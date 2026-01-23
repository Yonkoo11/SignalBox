import logging
from datetime import datetime, timezone, timedelta
from telegram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import config
from app.models import User, UserSettings, FeedbackItem, AlertLog

logger = logging.getLogger(__name__)

CATEGORY_LABELS = {
    "bug": "Bug Report",
    "complaint": "Complaint",
    "feature_request": "Feature Request",
    "question": "Question",
    "praise": "Praise",
    "noise": "Other",
}


def get_bot() -> Bot | None:
    if not config.TELEGRAM_BOT_TOKEN:
        return None
    return Bot(token=config.TELEGRAM_BOT_TOKEN)


async def should_alert(
    db: AsyncSession,
    user_id: int,
    item: FeedbackItem,
    settings: UserSettings,
) -> list[str]:
    """Check if we should send an alert. Returns list of reasons."""
    reasons = []

    # Always alert for direct tags
    if item.source in ("bot_tag", "signal_tag"):
        reasons.append("direct_tag")

    # Alert on bugs if enabled
    if settings.alert_on_bugs and item.category == "bug":
        reasons.append("bug_detected")

    # Alert on complaints if enabled
    if settings.alert_on_complaints and item.category == "complaint":
        reasons.append("complaint_detected")

    # Alert on high-reach authors
    if settings.alert_on_high_reach and item.author_followers and item.author_followers >= 1000:
        reasons.append("high_reach")

    # Alert on high engagement
    engagement = (item.likes or 0) + (item.retweets or 0)
    if engagement >= settings.alert_min_engagement:
        reasons.append("high_engagement")

    return reasons


async def check_cooldown(db: AsyncSession, user_id: int, minutes: int = 5) -> bool:
    """Check if we're in cooldown period. Returns True if we can send."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    result = await db.execute(
        select(AlertLog)
        .where(
            AlertLog.user_id == user_id,
            AlertLog.sent_at > cutoff,
        )
        .order_by(AlertLog.sent_at.desc())
        .limit(1)
    )
    last_alert = result.scalar_one_or_none()

    return last_alert is None


async def log_alert(
    db: AsyncSession,
    user_id: int,
    feedback_item_id: int,
    reason: str,
):
    """Log that we sent an alert."""
    alert = AlertLog(
        user_id=user_id,
        feedback_item_id=feedback_item_id,
        alert_reason=reason,
    )
    db.add(alert)
    await db.flush()


async def send_telegram_alert(
    user: User,
    item: FeedbackItem,
    reasons: list[str],
) -> bool:
    """Send a Telegram alert for a feedback item."""
    if not user.telegram_chat_id:
        return False

    bot = get_bot()
    if not bot:
        logger.warning("Telegram bot not configured")
        return False

    # Build message
    category_label = CATEGORY_LABELS.get(item.category, item.category)
    reason_text = ", ".join(r.replace("_", " ").title() for r in reasons)

    # Truncate text if needed
    text = item.tweet_text
    if len(text) > 200:
        text = text[:197] + "..."

    message = f"""NEW FEEDBACK

Type: {category_label}
From: @{item.author_username} ({item.author_followers:,} followers)
Priority: {item.priority.upper()}

"{text}"

Why alerted: {reason_text}

View: {config.APP_URL}/dashboard?id={item.id}
X: {item.tweet_url}"""

    try:
        await bot.send_message(
            chat_id=user.telegram_chat_id,
            text=message,
            disable_web_page_preview=True,
        )
        logger.info(f"Sent Telegram alert to user {user.id} for item {item.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False


async def maybe_send_alert(
    db: AsyncSession,
    user_id: int,
    item: FeedbackItem,
) -> bool:
    """Check if we should alert and send if so."""
    # Get user and settings
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.telegram_chat_id:
        return False

    # Free tier users don't get alerts
    if user.tier != "pro":
        return False

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        return False

    # Check if we should alert
    reasons = await should_alert(db, user_id, item, settings)
    if not reasons:
        return False

    # Check cooldown
    if not await check_cooldown(db, user_id):
        logger.debug(f"Skipping alert for user {user_id} - in cooldown")
        return False

    # Send alert
    sent = await send_telegram_alert(user, item, reasons)

    if sent:
        await log_alert(db, user_id, item.id, reasons[0])
        await db.commit()

    return sent
