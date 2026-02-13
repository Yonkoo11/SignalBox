"""Minimal test server for CRE workflow e2e testing.
Serves demo sentiment data without needing the full app stack.
"""
import random
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

STATIC_DIR = Path(__file__).parent / "src" / "app" / "static"
PROPOSALS_DIR = Path(__file__).parent / "proposals"

app = FastAPI(title="SignalBox Test Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/proposals", StaticFiles(directory=PROPOSALS_DIR), name="proposals")

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

DEMO_ITEMS = {
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
    "uniswap": [
        {"text": "V4 hooks are going to unlock insane customization for pools.", "category": "praise", "priority": "medium", "engagement": 312, "author": "defi_whale", "followers": 25000},
        {"text": "Gas fees on mainnet are still brutal. Please optimize.", "category": "complaint", "priority": "high", "engagement": 178, "author": "gas_watcher", "followers": 4200},
        {"text": "Would love native limit orders without needing a third-party plugin.", "category": "feature_request", "priority": "medium", "engagement": 95, "author": "trader_joe", "followers": 6700},
        {"text": "The mobile wallet experience is top-tier. Smooth swaps every time.", "category": "praise", "priority": "low", "engagement": 67, "author": "mobile_user", "followers": 1800},
        {"text": "Getting slippage errors on large trades even with 5% tolerance.", "category": "bug", "priority": "high", "engagement": 45, "author": "whale_problems", "followers": 9500},
        {"text": "How does concentrated liquidity actually work in V3?", "category": "question", "priority": "low", "engagement": 34, "author": "lp_newbie", "followers": 320},
    ],
    "aave": [
        {"text": "GHO is the stablecoin we actually needed. Fully decentralized and stable.", "category": "praise", "priority": "medium", "engagement": 198, "author": "stablecoin_fan", "followers": 11000},
        {"text": "V3 efficiency mode is a game changer for correlated assets.", "category": "praise", "priority": "medium", "engagement": 156, "author": "yield_farmer", "followers": 7800},
        {"text": "Governance participation is really healthy. Love the transparent process.", "category": "praise", "priority": "low", "engagement": 89, "author": "gov_voter", "followers": 3400},
        {"text": "Liquidation UX could be much better. Hard to track health factor.", "category": "complaint", "priority": "high", "engagement": 67, "author": "risk_mgr", "followers": 5200},
        {"text": "Need better docs for new integrators. Took 3 days to figure out flash loans.", "category": "feature_request", "priority": "medium", "engagement": 45, "author": "new_integrator", "followers": 1200},
        {"text": "Safety module yields keep attracting people. Smart incentive design.", "category": "praise", "priority": "low", "engagement": 78, "author": "yield_seeker", "followers": 4100},
    ],
    "base": [
        {"text": "Fees are SO low on Base. This is what Ethereum should feel like.", "category": "praise", "priority": "medium", "engagement": 267, "author": "l2_lover", "followers": 8900},
        {"text": "Coinbase integration makes onboarding trivial. My mom could use this.", "category": "praise", "priority": "low", "engagement": 145, "author": "onboarding_fan", "followers": 3200},
        {"text": "Worried about centralization. Single sequencer is a real concern.", "category": "complaint", "priority": "high", "engagement": 198, "author": "decentralist", "followers": 15000},
        {"text": "Bridge reliability has been sketchy. Had a tx stuck for 6 hours.", "category": "bug", "priority": "high", "engagement": 89, "author": "bridge_user", "followers": 4500},
        {"text": "Developer experience is honestly the best of any L2 right now.", "category": "praise", "priority": "medium", "engagement": 112, "author": "base_builder", "followers": 6200},
        {"text": "NFT community on Base is exploding. Friends on Chain is addictive.", "category": "praise", "priority": "low", "engagement": 78, "author": "nft_collector", "followers": 2100},
    ],
    "arbitrum": [
        {"text": "Stylus is going to bring so many Rust devs to crypto.", "category": "praise", "priority": "medium", "engagement": 178, "author": "rust_dev", "followers": 7200},
        {"text": "BOLD upgrade makes fraud proofs actually permissionless. Huge.", "category": "praise", "priority": "high", "engagement": 234, "author": "l2_researcher", "followers": 12000},
        {"text": "ARB token governance is a mess. Too much whale control.", "category": "complaint", "priority": "high", "engagement": 312, "author": "small_holder", "followers": 2800},
        {"text": "Sequencer is still centralized. When decentralized sequencing?", "category": "complaint", "priority": "high", "engagement": 267, "author": "decentralist_2", "followers": 9500},
        {"text": "DeFi ecosystem on Arbitrum is deep. GMX, Camelot, Radiant all solid.", "category": "praise", "priority": "medium", "engagement": 89, "author": "arb_user", "followers": 5400},
        {"text": "UX on most Arbitrum dapps is rough. Feels like 2020 Ethereum.", "category": "complaint", "priority": "medium", "engagement": 56, "author": "ux_critic", "followers": 3400},
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
    {"id": "run-0047", "timestamp": "2026-02-12 22:09:03", "projects": 5, "avg_score": 71, "status": "success", "duration": "4.2s", "tx": "0xdb3d2cf8213f0f33e85ac6073b17422ffc2743ae94c18287e5dda3d967d9fb1b", "gas": 47283},
    {"id": "run-0046", "timestamp": "2026-02-12 21:49:01", "projects": 5, "avg_score": 70, "status": "success", "duration": "3.8s", "tx": "0xa1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2", "gas": 46891},
    {"id": "run-0045", "timestamp": "2026-02-12 21:29:00", "projects": 5, "avg_score": 72, "status": "success", "duration": "4.1s", "tx": "0xf6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5", "gas": 47102},
    {"id": "run-0044", "timestamp": "2026-02-12 21:08:58", "projects": 5, "avg_score": 69, "status": "failed", "duration": "2.1s", "tx": None, "gas": 0},
    {"id": "run-0043", "timestamp": "2026-02-12 20:49:02", "projects": 5, "avg_score": 71, "status": "success", "duration": "3.9s", "tx": "0x1234abcd5678ef901234abcd5678ef901234abcd5678ef901234abcd5678ef90", "gas": 47050},
]


@app.get("/api/v1/sentiment/{project}")
async def get_sentiment(project: str, period: str = Query("1h")):
    items = DEMO_ITEMS.get(project, DEMO_ITEMS["chainlink"])
    breakdown = {}
    for item in items:
        cat = item["category"]
        breakdown[cat] = breakdown.get(cat, 0) + 1
    return {
        "project": project,
        "period": period,
        "is_demo": True,
        "score": DEMO_SCORES.get(project, 50),
        "total_mentions": len(items),
        "breakdown": {
            "praise": breakdown.get("praise", 0),
            "feature_request": breakdown.get("feature_request", 0),
            "question": breakdown.get("question", 0),
            "bug": breakdown.get("bug", 0),
            "complaint": breakdown.get("complaint", 0),
        },
        "ai_summary": AI_SUMMARIES.get(project, "No analysis available."),
        "key_themes": KEY_THEMES.get(project, []),
        "items": items,
    }


@app.get("/api/v1/sentiment")
async def list_projects():
    return {
        "projects": [
            {
                "project": p,
                "score": DEMO_SCORES[p],
                "total_mentions": len(DEMO_ITEMS.get(p, [])),
                "trend": DEMO_TRENDS[p],
            }
            for p in DEMO_SCORES
        ]
    }


@app.get("/api/v1/history/{project}")
async def score_history(project: str, days: int = Query(7)):
    base = DEMO_SCORES.get(project, 50)
    trend = DEMO_TRENDS.get(project, [base] * 7)
    if days <= 7:
        history = trend[-days:]
    else:
        history = []
        for i in range(days):
            jitter = random.randint(-3, 3)
            val = max(0, min(100, base + jitter - (days - i)))
            history.append(val)
        history[-7:] = trend
    return {
        "project": project,
        "days": days,
        "history": history,
    }


@app.get("/api/v1/comparison")
async def project_comparison():
    ranked = sorted(DEMO_SCORES.items(), key=lambda x: x[1], reverse=True)
    return {
        "rankings": [
            {"rank": i + 1, "project": p, "score": s, "trend": DEMO_TRENDS[p]}
            for i, (p, s) in enumerate(ranked)
        ],
        "avg_score": round(sum(DEMO_SCORES.values()) / len(DEMO_SCORES)),
        "total_projects": len(DEMO_SCORES),
        "total_mentions": sum(len(DEMO_ITEMS.get(p, [])) for p in DEMO_SCORES),
    }


@app.get("/api/v1/pipeline/runs")
async def pipeline_runs():
    return {"runs": PIPELINE_RUNS}


@app.get("/api/v1/pipeline/status")
async def pipeline_status():
    return {
        "status": "idle",
        "last_run": PIPELINE_RUNS[0]["timestamp"],
        "last_duration": PIPELINE_RUNS[0]["duration"],
        "next_run_in": 247,
        "total_runs": 47,
        "success_rate": 0.957,
    }


@app.get("/dashboard")
async def dashboard():
    return FileResponse(STATIC_DIR / "dashboard.html")


@app.get("/redesign")
async def redesign():
    return FileResponse(PROPOSALS_DIR / "index.html")


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
