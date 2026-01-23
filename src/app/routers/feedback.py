from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models import User, FeedbackItem

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


def get_current_user_id(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


@router.get("")
async def list_feedback(
    request: Request,
    db: AsyncSession = Depends(get_db),
    category: Optional[str] = Query(None, description="Filter by category (comma-separated)"),
    priority: Optional[str] = Query(None, description="Filter by priority (comma-separated)"),
    handled: Optional[bool] = Query(None, description="Filter by handled status"),
    hours: int = Query(168, description="Limit to last N hours"),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
):
    """List feedback items for the current user."""
    user_id = get_current_user_id(request)

    # Base query
    query = select(FeedbackItem).where(
        FeedbackItem.user_id == user_id,
        FeedbackItem.is_hidden == False,
    )

    # Filter by category
    if category:
        categories = [c.strip() for c in category.split(",")]
        query = query.where(FeedbackItem.category.in_(categories))

    # Filter by priority
    if priority:
        priorities = [p.strip() for p in priority.split(",")]
        query = query.where(FeedbackItem.priority.in_(priorities))

    # Filter by handled
    if handled is not None:
        query = query.where(FeedbackItem.is_handled == handled)

    # Default: show high + medium priority only
    if priority is None:
        query = query.where(FeedbackItem.priority.in_(["high", "medium"]))

    # Order by fetched_at desc
    query = query.order_by(FeedbackItem.fetched_at.desc())

    # Pagination
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": item.id,
                "tweet_id": item.tweet_id,
                "tweet_text": item.tweet_text,
                "tweet_url": item.tweet_url,
                "author_username": item.author_username,
                "author_followers": item.author_followers,
                "source": item.source,
                "signal_tag": item.signal_tag,
                "category": item.category,
                "sentiment": item.sentiment,
                "confidence": item.confidence,
                "summary": item.summary,
                "priority": item.priority,
                "likes": item.likes,
                "retweets": item.retweets,
                "is_handled": item.is_handled,
                "handled_at": item.handled_at.isoformat() if item.handled_at else None,
                "tweet_created_at": item.tweet_created_at.isoformat() if item.tweet_created_at else None,
                "fetched_at": item.fetched_at.isoformat() if item.fetched_at else None,
            }
            for item in items
        ],
        "limit": limit,
        "offset": offset,
    }


@router.get("/stats")
async def get_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get feedback stats for current user."""
    user_id = get_current_user_id(request)

    # Count by category
    result = await db.execute(
        select(FeedbackItem.category, func.count(FeedbackItem.id))
        .where(
            FeedbackItem.user_id == user_id,
            FeedbackItem.is_hidden == False,
        )
        .group_by(FeedbackItem.category)
    )
    by_category = {row[0]: row[1] for row in result.all()}

    # Count by priority
    result = await db.execute(
        select(FeedbackItem.priority, func.count(FeedbackItem.id))
        .where(
            FeedbackItem.user_id == user_id,
            FeedbackItem.is_hidden == False,
        )
        .group_by(FeedbackItem.priority)
    )
    by_priority = {row[0]: row[1] for row in result.all()}

    # Unhandled count
    result = await db.execute(
        select(func.count(FeedbackItem.id))
        .where(
            FeedbackItem.user_id == user_id,
            FeedbackItem.is_hidden == False,
            FeedbackItem.is_handled == False,
        )
    )
    unhandled = result.scalar() or 0

    # Total count
    result = await db.execute(
        select(func.count(FeedbackItem.id))
        .where(
            FeedbackItem.user_id == user_id,
            FeedbackItem.is_hidden == False,
        )
    )
    total = result.scalar() or 0

    return {
        "total": total,
        "unhandled": unhandled,
        "by_category": by_category,
        "by_priority": by_priority,
    }


@router.get("/{item_id}")
async def get_feedback_item(
    item_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get a single feedback item."""
    user_id = get_current_user_id(request)

    result = await db.execute(
        select(FeedbackItem).where(
            FeedbackItem.id == item_id,
            FeedbackItem.user_id == user_id,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Feedback item not found")

    return {
        "id": item.id,
        "tweet_id": item.tweet_id,
        "tweet_text": item.tweet_text,
        "tweet_url": item.tweet_url,
        "author_username": item.author_username,
        "author_followers": item.author_followers,
        "source": item.source,
        "signal_tag": item.signal_tag,
        "category": item.category,
        "sentiment": item.sentiment,
        "confidence": item.confidence,
        "summary": item.summary,
        "priority": item.priority,
        "likes": item.likes,
        "retweets": item.retweets,
        "is_handled": item.is_handled,
        "handled_at": item.handled_at.isoformat() if item.handled_at else None,
        "tweet_created_at": item.tweet_created_at.isoformat() if item.tweet_created_at else None,
        "fetched_at": item.fetched_at.isoformat() if item.fetched_at else None,
    }


@router.post("/{item_id}/handle")
async def mark_handled(
    item_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Mark a feedback item as handled."""
    user_id = get_current_user_id(request)

    result = await db.execute(
        select(FeedbackItem).where(
            FeedbackItem.id == item_id,
            FeedbackItem.user_id == user_id,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Feedback item not found")

    item.is_handled = True
    item.handled_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Marked as handled", "id": item_id}


@router.post("/{item_id}/hide")
async def hide_item(
    item_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Hide a feedback item (mark as noise)."""
    user_id = get_current_user_id(request)

    result = await db.execute(
        select(FeedbackItem).where(
            FeedbackItem.id == item_id,
            FeedbackItem.user_id == user_id,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Feedback item not found")

    item.is_hidden = True
    await db.commit()

    return {"message": "Item hidden", "id": item_id}
