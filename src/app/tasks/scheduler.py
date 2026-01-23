import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from app.database import async_session
from app.models import User
from app.services.collector import collect_all
from app.services.token_refresh import refresh_all_tokens

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_collection():
    """Scheduled job: collect feedback from X."""
    logger.info("Starting scheduled collection...")
    async with async_session() as db:
        try:
            stats = await collect_all(db)
            logger.info(f"Collection stats: {stats}")
        except Exception as e:
            logger.error(f"Collection failed: {e}")


async def run_token_refresh():
    """Scheduled job: refresh OAuth tokens."""
    logger.info("Starting scheduled token refresh...")
    async with async_session() as db:
        try:
            await refresh_all_tokens(db)
            logger.info("Token refresh complete")
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")


async def run_trial_expiry_check():
    """Scheduled job: downgrade expired trial users to free tier."""
    logger.info("Checking for expired trials...")
    async with async_session() as db:
        try:
            now = datetime.now(timezone.utc)

            # Find users with expired trials who are still on pro tier
            result = await db.execute(
                select(User).where(
                    User.subscription_status == "trial",
                    User.tier == "pro",
                    User.trial_ends_at < now,
                )
            )
            expired_users = result.scalars().all()

            for user in expired_users:
                user.tier = "free"
                user.subscription_status = "expired"
                logger.info(f"Downgraded user {user.id} ({user.x_username}) to free tier")

            if expired_users:
                await db.commit()
                logger.info(f"Downgraded {len(expired_users)} users to free tier")

        except Exception as e:
            logger.error(f"Trial expiry check failed: {e}")


def start_scheduler():
    """Start the background scheduler."""
    # Collection every 2 minutes
    scheduler.add_job(
        run_collection,
        trigger=IntervalTrigger(minutes=2),
        id="collect_feedback",
        replace_existing=True,
    )

    # Token refresh every hour
    scheduler.add_job(
        run_token_refresh,
        trigger=IntervalTrigger(hours=1),
        id="refresh_tokens",
        replace_existing=True,
    )

    # Trial expiry check every hour
    scheduler.add_job(
        run_trial_expiry_check,
        trigger=IntervalTrigger(hours=1),
        id="trial_expiry_check",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    """Stop the background scheduler."""
    scheduler.shutdown()
    logger.info("Scheduler stopped")
