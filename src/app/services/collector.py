import json
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, UserSettings, FeedbackItem
from app.services.twitter import (
    search_mentions,
    detect_source,
    parse_signal_tag,
    calculate_priority,
    extract_mentioned_handles,
    send_bot_confirmation,
)
from app.services.alerts import maybe_send_alert
from app.services.classifier import classify_feedback

logger = logging.getLogger(__name__)


async def feedback_exists(db: AsyncSession, tweet_id: str) -> bool:
    """Check if feedback item already exists."""
    result = await db.execute(
        select(FeedbackItem).where(FeedbackItem.tweet_id == tweet_id)
    )
    return result.scalar_one_or_none() is not None


async def get_all_tracked_handles(db: AsyncSession) -> dict[str, int]:
    """Get all monitored handles mapped to user IDs."""
    result = await db.execute(
        select(UserSettings.monitored_handle, UserSettings.user_id)
    )
    return {row[0].lower(): row[1] for row in result.all()}


async def save_feedback_item(
    db: AsyncSession,
    user_id: int,
    tweet_data: dict,
    source: str,
    signal_tag: str | None,
    category: str,
    sentiment: str | None,
    confidence: float,
    summary: str | None,
    priority: str,
) -> FeedbackItem:
    """Save a feedback item to the database."""
    item = FeedbackItem(
        user_id=user_id,
        tweet_id=tweet_data["tweet_id"],
        tweet_text=tweet_data["text"],
        tweet_url=f"https://x.com/{tweet_data['author_username']}/status/{tweet_data['tweet_id']}",
        author_username=tweet_data["author_username"],
        author_followers=tweet_data["author_followers"],
        source=source,
        signal_tag=signal_tag,
        category=category,
        sentiment=sentiment,
        confidence=confidence,
        summary=summary,
        priority=priority,
        likes=tweet_data["likes"],
        retweets=tweet_data["retweets"],
        tweet_created_at=tweet_data["created_at"],
    )
    db.add(item)
    await db.flush()
    return item


async def process_tweet(
    db: AsyncSession,
    user_id: int,
    tweet_data: dict,
    monitored_handle: str,
) -> FeedbackItem | None:
    """Process a single tweet and save as feedback item."""

    # Skip if already processed
    if await feedback_exists(db, tweet_data["tweet_id"]):
        return None

    # Get user tier for classification
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    use_ai = user.tier == "pro" if user else False

    text = tweet_data["text"]

    # Determine source
    source = detect_source(text)

    # Parse signal tag
    signal_tag, tag_category = parse_signal_tag(text)

    # Classify (AI for pro, keywords for free)
    classification = await classify_feedback(
        text=text,
        username=tweet_data["author_username"] or "unknown",
        followers=tweet_data["author_followers"] or 0,
        category_override=tag_category,  # Skip AI category if user provided $ tag
        use_ai=use_ai,
    )

    category = classification["category"]
    sentiment = classification["sentiment"]
    confidence = classification["confidence"]
    summary = classification["summary"]

    # Skip noise with high confidence
    if category == "noise" and confidence > 0.7:
        logger.debug(f"Skipping noise tweet {tweet_data['tweet_id']}")
        return None

    # Calculate priority
    priority = calculate_priority(
        source=source,
        signal_tag=signal_tag,
        category=category,
        likes=tweet_data["likes"],
        retweets=tweet_data["retweets"],
        followers=tweet_data["author_followers"],
    )

    # Save item
    item = await save_feedback_item(
        db=db,
        user_id=user_id,
        tweet_data=tweet_data,
        source=source,
        signal_tag=signal_tag,
        category=category,
        sentiment=sentiment,
        confidence=confidence,
        summary=summary,
        priority=priority,
    )

    logger.info(
        f"Saved feedback {item.id}: {category} ({priority}) from @{tweet_data['author_username']}"
    )

    # Send bot confirmation for direct tags
    if source in ("bot_tag", "signal_tag"):
        await send_bot_confirmation(tweet_data["tweet_id"], monitored_handle)

    # Send Telegram alert if warranted
    await maybe_send_alert(db, user_id, item)

    return item


async def collect_for_user(db: AsyncSession, user_id: int) -> int:
    """Collect feedback for a single user. Returns count of new items."""
    # Get user settings
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        logger.warning(f"No settings found for user {user_id}")
        return 0

    handle = settings.monitored_handle

    # Build search query
    # Passive: @handle mentions
    # Also catches @SignalBoxHQ @handle and $tag @handle
    query_parts = [f"@{handle}"]

    # Add extra keywords if any
    if settings.extra_keywords:
        try:
            keywords = json.loads(settings.extra_keywords)
            for kw in keywords[:5]:  # Max 5 keywords
                query_parts.append(kw)
        except json.JSONDecodeError:
            pass

    query = " OR ".join(query_parts)
    query += f" -from:{handle} -is:retweet"

    # Search
    tweets = await search_mentions(query, since_minutes=15, max_results=100)

    count = 0
    for tweet_data in tweets:
        item = await process_tweet(db, user_id, tweet_data, handle)
        if item:
            count += 1

    await db.commit()
    return count


async def collect_bot_mentions(db: AsyncSession) -> int:
    """Collect all @SignalBoxHQ mentions and route to correct users."""
    # Get all tracked handles
    tracked_handles = await get_all_tracked_handles(db)

    if not tracked_handles:
        return 0

    # Search for @SignalBoxHQ mentions
    query = "@SignalBoxHQ -is:retweet"
    tweets = await search_mentions(query, since_minutes=15, max_results=100)

    count = 0
    for tweet_data in tweets:
        # Skip if already processed
        if await feedback_exists(db, tweet_data["tweet_id"]):
            continue

        # Find which tracked product is mentioned
        mentioned = extract_mentioned_handles(tweet_data["text"])

        routed_to = None
        for handle in mentioned:
            if handle in tracked_handles:
                routed_to = (handle, tracked_handles[handle])
                break

        if not routed_to:
            # No tracked product mentioned, skip
            continue

        handle, user_id = routed_to
        item = await process_tweet(db, user_id, tweet_data, handle)
        if item:
            count += 1

    await db.commit()
    return count


async def collect_all(db: AsyncSession) -> dict:
    """Run collection for all active users. Returns stats."""
    # Get all active users
    result = await db.execute(
        select(User).where(
            User.needs_reauth == False,
            User.subscription_status.in_(["trial", "active"]),
        )
    )
    users = result.scalars().all()

    stats = {
        "users_processed": 0,
        "items_collected": 0,
        "bot_mentions": 0,
    }

    # Collect bot mentions first (routes to correct users)
    stats["bot_mentions"] = await collect_bot_mentions(db)
    stats["items_collected"] += stats["bot_mentions"]

    # Collect for each user
    for user in users:
        count = await collect_for_user(db, user.id)
        stats["items_collected"] += count
        stats["users_processed"] += 1

    logger.info(
        f"Collection complete: {stats['items_collected']} items from {stats['users_processed']} users"
    )

    return stats
