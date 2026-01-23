import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
import tweepy

from app.config import config
from app.services.encryption import decrypt

logger = logging.getLogger(__name__)

# Signal tags mapping
SIGNAL_TAGS = {
    "$bug": "bug",
    "$feature": "feature_request",
    "$question": "question",
    "$praise": "praise",
    "$complaint": "complaint",
    "$feedback": None,  # Generic - use AI classification
}

SIGNAL_PATTERN = re.compile(
    r"\$(?:bug|feature|question|praise|complaint|feedback)\b", re.IGNORECASE
)



def get_bot_client() -> tweepy.Client:
    """Get Twitter client for @SignalBoxHQ bot account."""
    return tweepy.Client(
        bearer_token=config.X_BOT_BEARER_TOKEN,
        consumer_key=config.X_CLIENT_ID,
        consumer_secret=config.X_CLIENT_SECRET,
        access_token=config.X_BOT_ACCESS_TOKEN,
        access_token_secret=config.X_BOT_ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=True,
    )


def get_user_client(access_token: str) -> tweepy.Client:
    """Get Twitter client for a user's account."""
    return tweepy.Client(
        bearer_token=access_token,
        wait_on_rate_limit=True,
    )


def parse_signal_tag(text: str) -> tuple[Optional[str], Optional[str]]:
    """Extract signal tag and category from tweet text.

    Returns (signal_tag, category) or (None, None) if no tag found.
    """
    match = SIGNAL_PATTERN.search(text)
    if match:
        tag = match.group(0).lower()
        category = SIGNAL_TAGS.get(tag)
        return tag, category
    return None, None


def detect_source(text: str) -> str:
    """Determine the source of feedback based on tweet content."""
    text_lower = text.lower()

    # Check for @SignalBoxHQ tag
    if "@signalboxhq" in text_lower:
        return "bot_tag"

    # Check for $ signal tags
    if SIGNAL_PATTERN.search(text):
        return "signal_tag"

    return "passive"


def calculate_priority(
    source: str,
    signal_tag: Optional[str],
    category: str,
    likes: int,
    retweets: int,
    followers: int,
) -> str:
    """Calculate priority level for a feedback item."""
    engagement = likes + retweets

    # High priority
    if source in ("bot_tag", "signal_tag"):
        return "high"
    if signal_tag and signal_tag != "$feedback":
        return "high"
    if engagement >= 5:
        return "high"
    if category in ("bug", "complaint") and followers >= 1000:
        return "high"

    # Medium priority
    if category in ("bug", "complaint", "feature_request"):
        return "medium"
    if followers >= 500:
        return "medium"

    # Low priority
    return "low"


def extract_mentioned_handles(text: str) -> list[str]:
    """Extract all @handles from tweet text."""
    pattern = r"@(\w+)"
    matches = re.findall(pattern, text)
    # Exclude signalboxhq
    return [h.lower() for h in matches if h.lower() != "signalboxhq"]


async def send_bot_confirmation(tweet_id: str, product_handle: str) -> bool:
    """Send confirmation reply from @SignalBoxHQ bot."""
    try:
        client = get_bot_client()
        reply_text = f"Forwarded to @{product_handle}. They'll see this."

        client.create_tweet(
            text=reply_text,
            in_reply_to_tweet_id=tweet_id,
        )
        logger.info(f"Sent confirmation reply for tweet {tweet_id}")
        return True
    except Exception as e:
        logger.warning(f"Failed to send bot confirmation: {e}")
        return False


async def search_mentions(
    query: str,
    since_minutes: int = 15,
    max_results: int = 100,
) -> list[dict]:
    """Search for recent tweets matching query."""
    client = get_bot_client()

    start_time = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)

    try:
        response = client.search_recent_tweets(
            query=query,
            max_results=max_results,
            start_time=start_time,
            tweet_fields=["created_at", "public_metrics", "author_id"],
            user_fields=["username", "public_metrics"],
            expansions=["author_id"],
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []

    if not response.data:
        return []

    # Build user lookup
    users = {}
    if response.includes and "users" in response.includes:
        for user in response.includes["users"]:
            users[user.id] = user

    results = []
    for tweet in response.data:
        author = users.get(tweet.author_id)

        results.append({
            "tweet_id": str(tweet.id),
            "text": tweet.text,
            "author_id": str(tweet.author_id),
            "author_username": author.username if author else None,
            "author_followers": author.public_metrics["followers_count"] if author else 0,
            "likes": tweet.public_metrics["like_count"],
            "retweets": tweet.public_metrics["retweet_count"],
            "created_at": tweet.created_at,
        })

    return results
