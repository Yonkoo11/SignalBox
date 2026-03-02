"""Reddit data fetcher for crypto project sentiment signals."""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Project -> subreddit mapping
PROJECT_SUBREDDITS = {
    "chainlink": ["chainlink", "cryptocurrency", "defi"],
    "aave": ["aave", "defi", "cryptocurrency"],
    "base": ["basechain", "cryptocurrency", "ethereum"],
    "uniswap": ["uniswap", "defi", "cryptocurrency"],
    "arbitrum": ["arbitrum", "cryptocurrency", "ethereum"],
}

# Search queries per project (used in subreddit search)
PROJECT_QUERIES = {
    "chainlink": "chainlink OR LINK OR CCIP OR CRE",
    "aave": "aave OR GHO OR aave v3",
    "base": "base chain OR base L2 OR coinbase L2",
    "uniswap": "uniswap OR UNI OR uniswap v4",
    "arbitrum": "arbitrum OR ARB OR arbitrum one",
}


def get_reddit_client():
    """Get authenticated PRAW Reddit client."""
    try:
        import praw
    except ImportError:
        logger.warning("praw not installed, Reddit collection disabled")
        return None

    from app.config import config

    if not config.REDDIT_CLIENT_ID or not config.REDDIT_CLIENT_SECRET:
        logger.info("Reddit credentials not set, collection disabled")
        return None

    try:
        reddit = praw.Reddit(
            client_id=config.REDDIT_CLIENT_ID,
            client_secret=config.REDDIT_CLIENT_SECRET,
            user_agent=config.REDDIT_USER_AGENT,
        )
        # Read-only mode (no username/password needed)
        reddit.read_only = True
        return reddit
    except Exception as e:
        logger.error(f"Failed to create Reddit client: {e}")
        return None


def fetch_project_signals(
    reddit,
    project: str,
    limit_per_sub: int = 10,
) -> list[dict]:
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
            subreddit = reddit.subreddit(sub_name)

            # Search for recent posts
            for post in subreddit.search(query, sort="new", time_filter="week", limit=limit_per_sub):
                if post.id in seen_ids:
                    continue
                seen_ids.add(post.id)

                # Skip removed/deleted posts
                if post.removed_by_category or post.selftext == "[removed]":
                    continue

                # Build text from title + body (truncate body)
                body = (post.selftext or "")[:300]
                text = post.title
                if body and body != "[removed]":
                    text = f"{post.title}. {body}"

                # Get author info safely
                author_name = "[deleted]"
                author_karma = 0
                if post.author:
                    try:
                        author_name = post.author.name
                        author_karma = post.author.link_karma or 0
                    except Exception:
                        pass

                signals.append({
                    "text": text[:500],
                    "category": "pending",
                    "priority": "medium",
                    "engagement": (post.score or 0) + (post.num_comments or 0),
                    "author": author_name,
                    "followers": author_karma,
                    "timestamp": datetime.fromtimestamp(post.created_utc, tz=timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "source": "reddit",
                    "source_id": post.id,
                    "url": f"https://reddit.com{post.permalink}",
                    "subreddit": sub_name,
                })

        except Exception as e:
            logger.warning(f"Failed to search r/{sub_name} for {project}: {e}")
            continue

    # Sort by engagement (highest first)
    signals.sort(key=lambda s: s["engagement"], reverse=True)

    logger.info(f"Fetched {len(signals)} Reddit signals for {project}")
    return signals
