"""Public sentiment API for Chainlink CRE workflow consumption."""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models import FeedbackItem, UserSettings

router = APIRouter(prefix="/api/v1/sentiment", tags=["sentiment"])


@router.get("/{project}")
async def get_sentiment(
    project: str,
    db: AsyncSession = Depends(get_db),
    period: str = Query("1h", description="Time window: 1h, 6h, 24h, 7d"),
):
    """
    Aggregated sentiment data for a project.
    Called by the Chainlink CRE workflow to feed the SentimentOracle contract.
    """
    # Parse period into timedelta
    cutoff = _parse_period(period)

    # Find users monitoring this project handle
    users_result = await db.execute(
        select(UserSettings.user_id).where(
            func.lower(UserSettings.monitored_handle) == project.lower()
        )
    )
    user_ids = [row[0] for row in users_result.all()]

    # Base filter: feedback for these users within the time window
    base_filter = and_(
        FeedbackItem.is_hidden == False,
        FeedbackItem.fetched_at >= cutoff,
    )
    if user_ids:
        base_filter = and_(base_filter, FeedbackItem.user_id.in_(user_ids))

    # Count by category
    cat_result = await db.execute(
        select(FeedbackItem.category, func.count(FeedbackItem.id))
        .where(base_filter)
        .group_by(FeedbackItem.category)
    )
    breakdown = {}
    total = 0
    for cat, count in cat_result.all():
        breakdown[cat] = count
        total += count

    # Get recent items for AI scoring (most engaged first)
    items_result = await db.execute(
        select(FeedbackItem)
        .where(base_filter)
        .order_by(
            (FeedbackItem.likes + FeedbackItem.retweets).desc()
        )
        .limit(30)
    )
    items = items_result.scalars().all()

    # Compute sentiment score server-side (single source of truth)
    pos = breakdown.get("praise", 0) + breakdown.get("feature_request", 0)
    neg = breakdown.get("bug", 0) + breakdown.get("complaint", 0)
    neu = breakdown.get("question", 0)
    score = round(((pos * 1.0 + neu * 0.5) / max(total, 1)) * 100) if total > 0 else 0

    # Build response matching what CRE workflow expects
    response = {
        "project": project,
        "period": period,
        "score": score,
        "total_mentions": total,
        "breakdown": {
            "praise": breakdown.get("praise", 0),
            "feature_request": breakdown.get("feature_request", 0),
            "question": breakdown.get("question", 0),
            "bug": breakdown.get("bug", 0),
            "complaint": breakdown.get("complaint", 0),
        },
        "items": [
            {
                "text": item.tweet_text,
                "category": item.category,
                "priority": item.priority,
                "engagement": (item.likes or 0) + (item.retweets or 0),
                "author": item.author_username,
                "followers": item.author_followers or 0,
            }
            for item in items
        ],
    }

    # Fallback: return demo data when DB is empty (for hackathon demo/testing)
    if total == 0:
        response = _demo_data(project, period)
    else:
        response["is_demo"] = False

    return response


@router.get("")
async def list_projects(
    db: AsyncSession = Depends(get_db),
):
    """List all monitored projects with their latest mention counts."""
    result = await db.execute(
        select(
            UserSettings.monitored_handle,
            func.count(FeedbackItem.id),
        )
        .join(FeedbackItem, FeedbackItem.user_id == UserSettings.user_id, isouter=True)
        .where(FeedbackItem.is_hidden == False)
        .group_by(UserSettings.monitored_handle)
    )

    projects = []
    for handle, count in result.all():
        projects.append({"project": handle, "total_feedback": count})

    return {"projects": projects}


def _parse_period(period: str) -> datetime:
    """Convert period string to cutoff datetime."""
    now = datetime.now(timezone.utc)
    mapping = {
        "1h": timedelta(hours=1),
        "6h": timedelta(hours=6),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
    }
    delta = mapping.get(period, timedelta(hours=1))
    return now - delta


# Demo data for testing and hackathon demos
_DEMO_ITEMS = {
    "chainlink": [
        {"text": "CCIP is a game changer for cross-chain. Finally a reliable bridge solution.", "category": "praise", "priority": "low", "engagement": 142, "author": "defi_dev", "followers": 8500},
        {"text": "CRE workflows are so clean. Built my first oracle in 2 hours.", "category": "praise", "priority": "medium", "engagement": 89, "author": "web3builder", "followers": 3200},
        {"text": "When will CRE support Solana? Need cross-chain sentiment there too.", "category": "feature_request", "priority": "high", "engagement": 67, "author": "sol_maxi", "followers": 12000},
        {"text": "Price feeds saved my protocol from a flash loan attack last night.", "category": "praise", "priority": "high", "engagement": 234, "author": "security_chad", "followers": 15000},
        {"text": "Docs for CRE workflow.yaml could be clearer on the secrets config.", "category": "complaint", "priority": "medium", "engagement": 23, "author": "newdev_123", "followers": 450},
        {"text": "How do I set up a custom data feed with CRE? Any examples?", "category": "question", "priority": "medium", "engagement": 15, "author": "curious_dev", "followers": 900},
        {"text": "The new Functions v2 is much faster than v1. Great improvement.", "category": "praise", "priority": "low", "engagement": 56, "author": "fn_user", "followers": 2100},
        {"text": "Got a weird error with CRE simulate on M1 Mac. Anyone else?", "category": "bug", "priority": "high", "engagement": 31, "author": "mac_dev", "followers": 1800},
    ],
    "default": [
        {"text": "Really impressed with the latest release. Performance is way better.", "category": "praise", "priority": "medium", "engagement": 78, "author": "crypto_fan", "followers": 5000},
        {"text": "Would love to see L2 support added soon.", "category": "feature_request", "priority": "high", "engagement": 45, "author": "l2_enthusiast", "followers": 7200},
        {"text": "The UI is confusing for new users. Needs better onboarding.", "category": "complaint", "priority": "medium", "engagement": 34, "author": "ux_critic", "followers": 3400},
        {"text": "Great team, great tech. Bullish long term.", "category": "praise", "priority": "low", "engagement": 120, "author": "hodler99", "followers": 11000},
        {"text": "Transaction failed twice today. Is the RPC down?", "category": "bug", "priority": "high", "engagement": 52, "author": "frustrated_user", "followers": 2800},
        {"text": "How does staking work with the new tokenomics?", "category": "question", "priority": "medium", "engagement": 19, "author": "staker_q", "followers": 600},
    ],
}


_DEMO_SCORES = {
    "chainlink": 82,
    "default": 65,
}


def _demo_data(project: str, period: str) -> dict:
    items = _DEMO_ITEMS.get(project, _DEMO_ITEMS["default"])
    breakdown = {}
    for item in items:
        cat = item["category"]
        breakdown[cat] = breakdown.get(cat, 0) + 1
    return {
        "project": project,
        "period": period,
        "is_demo": True,
        "score": _DEMO_SCORES.get(project, _DEMO_SCORES["default"]),
        "total_mentions": len(items),
        "breakdown": {
            "praise": breakdown.get("praise", 0),
            "feature_request": breakdown.get("feature_request", 0),
            "question": breakdown.get("question", 0),
            "bug": breakdown.get("bug", 0),
            "complaint": breakdown.get("complaint", 0),
        },
        "items": items,
    }
