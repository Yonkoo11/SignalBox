import httpx
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import config
from app.models import User
from app.services.encryption import encrypt, decrypt

logger = logging.getLogger(__name__)


async def refresh_user_token(db: AsyncSession, user_id: int) -> bool:
    """Refresh X OAuth token for a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        logger.error(f"User {user_id} not found for token refresh")
        return False

    try:
        refresh_token = decrypt(user.x_refresh_token)
    except Exception as e:
        logger.error(f"Failed to decrypt refresh token for user {user_id}: {e}")
        user.needs_reauth = True
        await db.commit()
        return False

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.twitter.com/2/oauth2/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": config.X_CLIENT_ID,
            },
            auth=(config.X_CLIENT_ID, config.X_CLIENT_SECRET),
        )

    if response.status_code != 200:
        logger.error(f"Token refresh failed for user {user_id}: {response.text}")
        user.needs_reauth = True
        await db.commit()
        return False

    data = response.json()
    user.x_access_token = encrypt(data["access_token"])
    user.x_refresh_token = encrypt(data["refresh_token"])
    user.needs_reauth = False
    user.updated_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info(f"Token refreshed for user {user_id}")
    return True


async def refresh_all_tokens(db: AsyncSession):
    """Refresh tokens for all active users."""
    result = await db.execute(
        select(User).where(
            User.needs_reauth == False,
            User.subscription_status.in_(["trial", "active"]),
        )
    )
    users = result.scalars().all()

    for user in users:
        await refresh_user_token(db, user.id)
