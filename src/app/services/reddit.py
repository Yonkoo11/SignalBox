"""Reddit data fetcher using public JSON endpoints (no API key needed).

Reddit exposes JSON at any URL by appending .json. Rate limit: ~30 req/min
unauthenticated. We use httpx (already in requirements) with a proper User-Agent.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

REDDIT_BASE = "https://www.reddit.com"
USER_AGENT = "SignalBox/1.0 (crypto sentiment oracle; hackathon project)"
REQUEST_TIMEOUT = 15

# Project -> subreddit search mapping
PROJECT_SUBREDDITS = {
    "chainlink": ["chainlink", "cryptocurrency"],
    "aave": ["aave", "defi"],
    "base": ["CoinBase", "cryptocurrency"],
    "uniswap": ["uniswap", "defi"],
    "arbitrum": ["arbitrum", "cryptocurrency"],
}

PROJECT_QUERIES = {
    "chainlink": "chainlink OR LINK OR CCIP",
    "aave": "aave OR GHO",
    "base": "base chain OR base L2",
    "uniswap": "uniswap OR UNI",
    "arbitrum": "arbitrum OR ARB",
}


async def _fetch_json(url: str, params: Optional[dict] = None) -> Optional[dict]:
    """Fetch JSON from a Reddit URL."""
    headers = {"User-Agent": USER_AGENT}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url, params=params, headers=headers, timeout=REQUEST_TIMEOUT,
                follow_redirects=True,
            )
            if resp.status_code == 429:
                logger.warning("Reddit rate limit hit, backing off")
                return None
            if resp.status_code != 200:
                logger.warning(f"Reddit returned {resp.status_code} for {url}")
                return None
            return resp.json()
    except Exception as e:
        logger.error(f"Reddit fetch failed: {e}")
        return None


def _parse_post(post_data: dict) -> Optional[dict]:
    """Parse a Reddit post from JSON into our signal format."""
    data = post_data.get("data", {})

    # Skip removed/deleted
    if data.get("removed_by_category") or data.get("selftext") == "[removed]":
        return None

    # Skip stickied posts (usually mod announcements)
    if data.get("stickied"):
        return None

    title = data.get("title", "")
    body = (data.get("selftext") or "")[:300]
    text = title
    if body and body != "[removed]" and body != "[deleted]":
        text = f"{title}. {body}"

    author = data.get("author", "[deleted]")
    if author == "[deleted]":
        return None

    score = data.get("score", 0)
    num_comments = data.get("num_comments", 0)
    created_utc = data.get("created_utc", 0)

    return {
        "text": text[:500],
        "category": "pending",
        "priority": "medium",
        "engagement": score + num_comments,
        "author": author,
        "followers": 0,  # Not available from JSON endpoint
        "timestamp": datetime.fromtimestamp(created_utc, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "source": "reddit",
        "source_id": data.get("id", ""),
        "subreddit": data.get("subreddit", ""),
    }


async def search_subreddit(subreddit: str, query: str, limit: int = 10) -> list[dict]:
    """Search a subreddit for posts matching query."""
    url = f"{REDDIT_BASE}/r/{subreddit}/search.json"
    params = {
        "q": query,
        "sort": "new",
        "t": "week",
        "restrict_sr": "on",
        "limit": str(limit),
    }

    data = await _fetch_json(url, params)
    if not data:
        return []

    posts = []
    children = data.get("data", {}).get("children", [])
    for child in children:
        parsed = _parse_post(child)
        if parsed:
            posts.append(parsed)

    return posts


async def fetch_subreddit_new(subreddit: str, limit: int = 10) -> list[dict]:
    """Fetch newest posts from a subreddit."""
    url = f"{REDDIT_BASE}/r/{subreddit}/new.json"
    params = {"limit": str(limit)}

    data = await _fetch_json(url, params)
    if not data:
        return []

    posts = []
    children = data.get("data", {}).get("children", [])
    for child in children:
        parsed = _parse_post(child)
        if parsed:
            posts.append(parsed)

    return posts


async def fetch_project_signals(project: str, limit_per_sub: int = 8) -> list[dict]:
    """Fetch signals for a project from relevant subreddits.

    Returns normalized signal dicts matching the existing items schema.
    """
    query = PROJECT_QUERIES.get(project)
    subreddits = PROJECT_SUBREDDITS.get(project, ["cryptocurrency"])

    if not query:
        return []

    signals = []
    seen_ids = set()

    for sub_name in subreddits:
        try:
            # Search for project mentions
            posts = await search_subreddit(sub_name, query, limit=limit_per_sub)

            for post in posts:
                sid = post.get("source_id", "")
                if sid and sid not in seen_ids:
                    seen_ids.add(sid)
                    signals.append(post)

        except Exception as e:
            logger.warning(f"Failed to fetch r/{sub_name} for {project}: {e}")
            continue

    # Sort by engagement (highest first)
    signals.sort(key=lambda s: s["engagement"], reverse=True)

    logger.info(f"Fetched {len(signals)} Reddit signals for {project}")
    return signals
