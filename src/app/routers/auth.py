import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import tweepy

from app.config import config
from app.database import get_db
from app.models import User, UserSettings, ResponseTemplate
from app.services.encryption import encrypt, decrypt

router = APIRouter(prefix="/auth", tags=["auth"])

# OAuth setup
oauth = OAuth()
oauth.register(
    name="twitter",
    client_id=config.X_CLIENT_ID,
    client_secret=config.X_CLIENT_SECRET,
    authorize_url="https://twitter.com/i/oauth2/authorize",
    access_token_url="https://api.twitter.com/2/oauth2/token",
    client_kwargs={
        "scope": "tweet.read users.read offline.access",
        "code_challenge_method": "S256",
    },
)

# Default templates for new users
DEFAULT_TEMPLATES = [
    {"name": "Bug ack", "category": "bug", "text": "Thanks for flagging. Looking into it."},
    {"name": "Feature noted", "category": "feature_request", "text": "Good idea. Added to our list."},
    {"name": "Help", "category": "question", "text": "Happy to help. Check our docs or DM us."},
    {"name": "Thanks", "category": "praise", "text": "Thanks for the kind words."},
    {"name": "Apology", "category": "complaint", "text": "Sorry about that. Can you DM us details?"},
]


@router.get("/login")
async def login(request: Request):
    redirect_uri = f"{config.APP_URL}/auth/callback"
    return await oauth.twitter.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def callback(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        token = await oauth.twitter.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth failed: {str(e)}")

    # Get user info from X
    client = tweepy.Client(bearer_token=token["access_token"])
    me = client.get_me(user_fields=["username"])

    if not me.data:
        raise HTTPException(status_code=400, detail="Could not fetch user info from X")

    x_user_id = str(me.data.id)
    x_username = me.data.username

    # Check if user exists
    result = await db.execute(select(User).where(User.x_user_id == x_user_id))
    user = result.scalar_one_or_none()

    if user:
        # Update tokens
        user.x_access_token = encrypt(token["access_token"])
        user.x_refresh_token = encrypt(token["refresh_token"])
        user.x_username = x_username
        user.needs_reauth = False
        user.updated_at = datetime.utcnow()
    else:
        # Create new user (trial users get Pro features)
        user = User(
            x_user_id=x_user_id,
            x_username=x_username,
            x_access_token=encrypt(token["access_token"]),
            x_refresh_token=encrypt(token["refresh_token"]),
            tier="pro",  # Trial users get Pro features
            trial_ends_at=datetime.utcnow() + timedelta(days=14),
            monitoring_since=datetime.utcnow(),
        )
        db.add(user)
        await db.flush()

        # Create default settings
        settings = UserSettings(
            user_id=user.id,
            monitored_handle=x_username,
        )
        db.add(settings)

        # Create default templates
        for tmpl in DEFAULT_TEMPLATES:
            template = ResponseTemplate(
                user_id=user.id,
                name=tmpl["name"],
                category=tmpl["category"],
                template_text=tmpl["text"],
            )
            db.add(template)

    await db.commit()

    # Set session
    request.session["user_id"] = user.id

    return RedirectResponse(url="/dashboard", status_code=302)


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}


@router.get("/me")
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "x_username": user.x_username,
        "tier": user.tier,
        "subscription_status": user.subscription_status,
        "trial_ends_at": user.trial_ends_at.isoformat() if user.trial_ends_at else None,
        "telegram_connected": bool(user.telegram_chat_id),
        "monitoring_since": user.monitoring_since.isoformat() if user.monitoring_since else None,
        "needs_reauth": user.needs_reauth,
    }
