"""Demo data router for hackathon staging mode.
Serves live Reddit data when available, falls back to curated demo data.
Activated when DEMO_MODE=true environment variable is set.
"""
import random
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Query

from app.services.social_collector import social_store

router = APIRouter(tags=["demo"])

DEMO_SCORES = {
    "chainlink": 82,
    "uniswap": 65,
    "aave": 78,
    "base": 71,
    "arbitrum": 58,
}

DEMO_TRENDS = {
    "chainlink": [74, 76, 79, 78, 80, 82, 82],
    "uniswap": [68, 66, 63, 64, 67, 65, 65],
    "aave": [72, 74, 75, 76, 78, 77, 78],
    "base": [65, 66, 68, 69, 70, 72, 71],
    "arbitrum": [62, 60, 59, 57, 56, 59, 58],
}


def _ts(hours_ago: float) -> str:
    dt = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


DEMO_ITEMS = {
    "chainlink": [
        {"text": "CCIP is a game changer for cross-chain. Finally a reliable bridge solution.", "category": "praise", "priority": "low", "engagement": 142, "author": "defi_dev", "followers": 8500, "timestamp": _ts(0.3), "source": "twitter"},
        {"text": "CRE workflows are so clean. Built my first oracle in 2 hours.", "category": "praise", "priority": "medium", "engagement": 89, "author": "web3builder", "followers": 3200, "timestamp": _ts(0.8), "source": "twitter"},
        {"text": "When will CRE support Solana? Need cross-chain sentiment there too.", "category": "feature_request", "priority": "high", "engagement": 67, "author": "sol_maxi", "followers": 12000, "timestamp": _ts(1.2), "source": "twitter"},
        {"text": "Price feeds saved my protocol from a flash loan attack last night.", "category": "praise", "priority": "high", "engagement": 234, "author": "security_chad", "followers": 15000, "timestamp": _ts(2.1), "source": "twitter"},
        {"text": "Docs for CRE workflow.yaml could be clearer on the secrets config.", "category": "complaint", "priority": "medium", "engagement": 23, "author": "newdev_123", "followers": 450, "timestamp": _ts(3.5), "source": "twitter"},
        {"text": "How do I set up a custom data feed with CRE? Any examples?", "category": "question", "priority": "medium", "engagement": 15, "author": "curious_dev", "followers": 900, "timestamp": _ts(4.0), "source": "twitter"},
        {"text": "The new Functions v2 is much faster than v1. Great improvement.", "category": "praise", "priority": "low", "engagement": 56, "author": "fn_user", "followers": 2100, "timestamp": _ts(5.5), "source": "twitter"},
        {"text": "Got a weird error with CRE simulate on M1 Mac. Anyone else?", "category": "bug", "priority": "high", "engagement": 31, "author": "mac_dev", "followers": 1800, "timestamp": _ts(6.2), "source": "twitter"},
    ],
    "uniswap": [
        {"text": "V4 hooks are going to unlock insane customization for pools.", "category": "praise", "priority": "medium", "engagement": 312, "author": "defi_whale", "followers": 25000, "timestamp": _ts(0.5), "source": "twitter"},
        {"text": "Gas fees on mainnet are still brutal. Please optimize.", "category": "complaint", "priority": "high", "engagement": 178, "author": "gas_watcher", "followers": 4200, "timestamp": _ts(1.1), "source": "twitter"},
        {"text": "Would love native limit orders without needing a third-party plugin.", "category": "feature_request", "priority": "medium", "engagement": 95, "author": "trader_joe", "followers": 6700, "timestamp": _ts(2.3), "source": "twitter"},
        {"text": "The mobile wallet experience is top-tier. Smooth swaps every time.", "category": "praise", "priority": "low", "engagement": 67, "author": "mobile_user", "followers": 1800, "timestamp": _ts(3.0), "source": "twitter"},
        {"text": "Getting slippage errors on large trades even with 5% tolerance.", "category": "bug", "priority": "high", "engagement": 45, "author": "whale_problems", "followers": 9500, "timestamp": _ts(4.7), "source": "twitter"},
        {"text": "How does concentrated liquidity actually work in V3?", "category": "question", "priority": "low", "engagement": 34, "author": "lp_newbie", "followers": 320, "timestamp": _ts(5.8), "source": "twitter"},
    ],
    "aave": [
        {"text": "GHO is the stablecoin we actually needed. Fully decentralized and stable.", "category": "praise", "priority": "medium", "engagement": 198, "author": "stablecoin_fan", "followers": 11000, "timestamp": _ts(0.4), "source": "twitter"},
        {"text": "V3 efficiency mode is a game changer for correlated assets.", "category": "praise", "priority": "medium", "engagement": 156, "author": "yield_farmer", "followers": 7800, "timestamp": _ts(1.5), "source": "twitter"},
        {"text": "Governance participation is really healthy. Love the transparent process.", "category": "praise", "priority": "low", "engagement": 89, "author": "gov_voter", "followers": 3400, "timestamp": _ts(2.8), "source": "twitter"},
        {"text": "Liquidation UX could be much better. Hard to track health factor.", "category": "complaint", "priority": "high", "engagement": 67, "author": "risk_mgr", "followers": 5200, "timestamp": _ts(3.2), "source": "twitter"},
        {"text": "Need better docs for new integrators. Took 3 days to figure out flash loans.", "category": "feature_request", "priority": "medium", "engagement": 45, "author": "new_integrator", "followers": 1200, "timestamp": _ts(4.5), "source": "twitter"},
        {"text": "Safety module yields keep attracting people. Smart incentive design.", "category": "praise", "priority": "low", "engagement": 78, "author": "yield_seeker", "followers": 4100, "timestamp": _ts(5.1), "source": "twitter"},
    ],
    "base": [
        {"text": "Fees are SO low on Base. This is what Ethereum should feel like.", "category": "praise", "priority": "medium", "engagement": 267, "author": "l2_lover", "followers": 8900, "timestamp": _ts(0.2), "source": "twitter"},
        {"text": "Coinbase integration makes onboarding trivial. My mom could use this.", "category": "praise", "priority": "low", "engagement": 145, "author": "onboarding_fan", "followers": 3200, "timestamp": _ts(1.0), "source": "twitter"},
        {"text": "Worried about centralization. Single sequencer is a real concern.", "category": "complaint", "priority": "high", "engagement": 198, "author": "decentralist", "followers": 15000, "timestamp": _ts(2.0), "source": "twitter"},
        {"text": "Bridge reliability has been sketchy. Had a tx stuck for 6 hours.", "category": "bug", "priority": "high", "engagement": 89, "author": "bridge_user", "followers": 4500, "timestamp": _ts(3.3), "source": "twitter"},
        {"text": "Developer experience is honestly the best of any L2 right now.", "category": "praise", "priority": "medium", "engagement": 112, "author": "base_builder", "followers": 6200, "timestamp": _ts(4.1), "source": "twitter"},
        {"text": "NFT community on Base is exploding. Friends on Chain is addictive.", "category": "praise", "priority": "low", "engagement": 78, "author": "nft_collector", "followers": 2100, "timestamp": _ts(5.9), "source": "twitter"},
    ],
    "arbitrum": [
        {"text": "Stylus is going to bring so many Rust devs to crypto.", "category": "praise", "priority": "medium", "engagement": 178, "author": "rust_dev", "followers": 7200, "timestamp": _ts(0.6), "source": "twitter"},
        {"text": "BOLD upgrade makes fraud proofs actually permissionless. Huge.", "category": "praise", "priority": "high", "engagement": 234, "author": "l2_researcher", "followers": 12000, "timestamp": _ts(1.4), "source": "twitter"},
        {"text": "ARB token governance is a mess. Too much whale control.", "category": "complaint", "priority": "high", "engagement": 312, "author": "small_holder", "followers": 2800, "timestamp": _ts(2.5), "source": "twitter"},
        {"text": "Sequencer is still centralized. When decentralized sequencing?", "category": "complaint", "priority": "high", "engagement": 267, "author": "decentralist_2", "followers": 9500, "timestamp": _ts(3.7), "source": "twitter"},
        {"text": "DeFi ecosystem on Arbitrum is deep. GMX, Camelot, Radiant all solid.", "category": "praise", "priority": "medium", "engagement": 89, "author": "arb_user", "followers": 5400, "timestamp": _ts(4.9), "source": "twitter"},
        {"text": "UX on most Arbitrum dapps is rough. Feels like 2020 Ethereum.", "category": "complaint", "priority": "medium", "engagement": 56, "author": "ux_critic", "followers": 3400, "timestamp": _ts(6.0), "source": "twitter"},
    ],
}

AI_SUMMARIES = {
    "chainlink": "Community sentiment for Chainlink is strongly positive at 82/100. CCIP adoption and CRE announcements are driving engagement, with primary praise centering on cross-chain infrastructure and developer tooling. Minor friction points around documentation clarity and M1 Mac compatibility for local nodes. Recommend prioritizing docs update and addressing platform-specific bugs to maintain momentum.",
    "uniswap": "Sentiment for Uniswap is moderate-positive at 65/100. V4 hooks are generating significant developer excitement, but gas costs on mainnet remain a consistent pain point. Feature requests cluster around native limit orders and L2 improvements. Mobile wallet experience is praised. Community is engaged but price-sensitive.",
    "aave": "Aave maintains strong sentiment at 78/100. GHO stablecoin launch and V3 efficiency mode are well received by the DeFi community. Governance participation is healthy with transparent processes. Primary concerns focus on liquidation UX and documentation for new integrators. Safety module yields continue attracting positive discussion.",
    "base": "Base shows growing positive sentiment at 71/100. Low fees and Coinbase integration drive adoption praise, with developer experience frequently highlighted as best-in-class among L2s. Concerns center on sequencer centralization and bridge reliability. NFT community is particularly active and positive.",
    "arbitrum": "Arbitrum sentiment is mixed-positive at 58/100. Stylus and BOLD upgrades generate strong technical excitement among developers. However, ARB token governance discussions are polarizing with whale control concerns. Sequencer centralization remains the dominant criticism. DeFi ecosystem depth is praised but UX complaints are frequent.",
}

KEY_THEMES = {
    "chainlink": ["CCIP adoption", "CRE developer experience", "Cross-chain infrastructure", "Documentation gaps", "M1 Mac compatibility"],
    "uniswap": ["V4 hooks customization", "Gas fee optimization", "Limit order support", "Mobile wallet UX", "Concentrated liquidity"],
    "aave": ["GHO stablecoin stability", "Efficiency mode", "Governance health", "Liquidation UX", "Flash loan docs"],
    "base": ["Low transaction fees", "Coinbase onboarding", "Sequencer centralization", "Bridge reliability", "NFT ecosystem growth"],
    "arbitrum": ["Stylus Rust support", "BOLD fraud proofs", "Token governance", "Sequencer decentralization", "DeFi ecosystem depth"],
}

PIPELINE_RUNS = [
    {"id": "run-0047", "timestamp": "2026-02-12 22:09:03", "projects": 5, "avg_score": 71, "status": "success", "duration": "4.2s", "tx": "0xdb3d2c...9fb1b", "gas": 47283},
    {"id": "run-0046", "timestamp": "2026-02-12 21:49:01", "projects": 5, "avg_score": 70, "status": "success", "duration": "3.8s", "tx": "0xa1b2c3...f6a1b2", "gas": 46891},
    {"id": "run-0045", "timestamp": "2026-02-12 21:29:00", "projects": 5, "avg_score": 72, "status": "success", "duration": "4.1s", "tx": "0xf6e5d4...a1f6e5", "gas": 47102},
    {"id": "run-0044", "timestamp": "2026-02-12 21:08:58", "projects": 5, "avg_score": 69, "status": "failed", "duration": "2.1s", "tx": None, "gas": 0},
    {"id": "run-0043", "timestamp": "2026-02-12 20:49:02", "projects": 5, "avg_score": 71, "status": "success", "duration": "3.9s", "tx": "0x1234ab...8ef90", "gas": 47050},
]


def _get_items(project: str) -> list[dict]:
    """Get items for a project: live Reddit data merged with curated Twitter data."""
    live_signals = social_store.get_signals(project)
    curated = DEMO_ITEMS.get(project, DEMO_ITEMS["chainlink"])

    if live_signals:
        # Merge: live Reddit signals + curated Twitter data, sorted by engagement
        merged = live_signals + curated
        merged.sort(key=lambda x: x.get("engagement", 0), reverse=True)
        return merged

    return curated


def _get_score(project: str) -> int:
    """Get score: live computed or demo fallback."""
    live_score = social_store.get_score(project)
    if live_score is not None:
        return live_score
    return DEMO_SCORES.get(project, 50)


def _get_summary(project: str) -> str:
    """Get AI summary: live or demo fallback."""
    live_summary = social_store.get_summary(project)
    if live_summary:
        return live_summary
    return AI_SUMMARIES.get(project, "No analysis available.")


def _breakdown(items: list[dict]) -> dict:
    """Compute category breakdown from items."""
    bd = {}
    for item in items:
        cat = item.get("category", "noise")
        if cat == "pending" or cat == "noise":
            continue
        bd[cat] = bd.get(cat, 0) + 1
    return {
        "praise": bd.get("praise", 0),
        "feature_request": bd.get("feature_request", 0),
        "question": bd.get("question", 0),
        "bug": bd.get("bug", 0),
        "complaint": bd.get("complaint", 0),
    }


@router.get("/api/v1/sentiment/{project}")
async def get_sentiment(project: str, period: str = Query("1h")):
    items = _get_items(project)
    return {
        "project": project,
        "period": period,
        "mode": "live" if social_store.is_live else "staging",
        "score": _get_score(project),
        "total_mentions": len(items),
        "breakdown": _breakdown(items),
        "ai_summary": _get_summary(project),
        "key_themes": KEY_THEMES.get(project, []),
        "items": items,
    }


@router.get("/api/v1/sentiment")
async def list_projects():
    return {
        "projects": [
            {
                "project": p,
                "score": _get_score(p),
                "total_mentions": len(_get_items(p)),
                "trend": social_store.get_trend(p) or DEMO_TRENDS[p],
            }
            for p in DEMO_SCORES
        ]
    }


@router.get("/api/v1/history/{project}")
async def score_history(project: str, days: int = Query(7)):
    # Use live trend data if available
    live_trend = social_store.get_trend(project)
    base = _get_score(project)

    if live_trend and len(live_trend) >= days:
        history = live_trend[-days:]
    else:
        trend = live_trend if live_trend else DEMO_TRENDS.get(project, [base] * 7)
        if days <= len(trend):
            history = trend[-days:]
        else:
            history = []
            for i in range(days):
                jitter = random.randint(-3, 3)
                val = max(0, min(100, base + jitter - (days - i)))
                history.append(val)
            history[-len(trend):] = trend

    return {"project": project, "days": days, "history": history}


@router.get("/api/v1/comparison")
async def project_comparison():
    scores = {p: _get_score(p) for p in DEMO_SCORES}
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    all_items = {p: _get_items(p) for p in DEMO_SCORES}

    return {
        "rankings": [
            {
                "rank": i + 1,
                "project": p,
                "score": s,
                "trend": social_store.get_trend(p) or DEMO_TRENDS[p],
            }
            for i, (p, s) in enumerate(ranked)
        ],
        "avg_score": round(sum(scores.values()) / len(scores)),
        "total_projects": len(scores),
        "total_mentions": sum(len(items) for items in all_items.values()),
        "is_live": social_store.is_live,
    }


@router.get("/api/v1/pipeline/runs")
async def pipeline_runs():
    return {"runs": PIPELINE_RUNS}


@router.get("/api/v1/pipeline/status")
async def pipeline_status():
    return {
        "status": "collecting" if social_store.is_live else "idle",
        "last_run": PIPELINE_RUNS[0]["timestamp"],
        "last_duration": PIPELINE_RUNS[0]["duration"],
        "next_run_in": 247,
        "total_runs": 47 + social_store.collection_count,
        "success_rate": 0.957,
        "is_live": social_store.is_live,
    }


@router.get("/api/v1/collect")
async def trigger_collection():
    """Manual trigger for social collection (debug)."""
    from app.services.social_collector import collect_all_projects
    try:
        await collect_all_projects()
        return {
            "status": "ok",
            "is_live": social_store.is_live,
            "collections": social_store.collection_count,
            "scores": {p: social_store.get_score(p) for p in ["chainlink", "aave", "base", "uniswap", "arbitrum"]},
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
