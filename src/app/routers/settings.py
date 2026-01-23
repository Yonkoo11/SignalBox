import json
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, UserSettings, ResponseTemplate, TelegramLinkCode

router = APIRouter(prefix="/api/settings", tags=["settings"])


def get_current_user_id(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


# --- Settings ---

class SettingsUpdate(BaseModel):
    monitored_handle: Optional[str] = None
    extra_keywords: Optional[list[str]] = None
    alert_on_bugs: Optional[bool] = None
    alert_on_complaints: Optional[bool] = None
    alert_on_high_reach: Optional[bool] = None
    alert_min_engagement: Optional[int] = None


@router.get("")
async def get_settings(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get current user's settings."""
    user_id = get_current_user_id(request)

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    # Parse extra keywords
    extra_keywords = []
    if settings.extra_keywords:
        try:
            extra_keywords = json.loads(settings.extra_keywords)
        except json.JSONDecodeError:
            pass

    return {
        "monitored_handle": settings.monitored_handle,
        "extra_keywords": extra_keywords,
        "alert_on_bugs": settings.alert_on_bugs,
        "alert_on_complaints": settings.alert_on_complaints,
        "alert_on_high_reach": settings.alert_on_high_reach,
        "alert_min_engagement": settings.alert_min_engagement,
    }


@router.put("")
async def update_settings(
    request: Request,
    data: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update current user's settings."""
    user_id = get_current_user_id(request)

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    if data.monitored_handle is not None:
        # Remove @ if present
        handle = data.monitored_handle.lstrip("@")
        settings.monitored_handle = handle

    if data.extra_keywords is not None:
        # Limit to 5 keywords
        keywords = data.extra_keywords[:5]
        settings.extra_keywords = json.dumps(keywords)

    if data.alert_on_bugs is not None:
        settings.alert_on_bugs = data.alert_on_bugs

    if data.alert_on_complaints is not None:
        settings.alert_on_complaints = data.alert_on_complaints

    if data.alert_on_high_reach is not None:
        settings.alert_on_high_reach = data.alert_on_high_reach

    if data.alert_min_engagement is not None:
        settings.alert_min_engagement = max(1, min(100, data.alert_min_engagement))

    settings.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Settings updated"}


# --- Telegram Connection ---

@router.post("/telegram")
async def create_telegram_link(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Generate a Telegram link code for connecting."""
    user_id = get_current_user_id(request)

    # Generate unique code
    code = f"LINK-{secrets.token_urlsafe(8).upper()}"

    # Expire in 15 minutes
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    # Delete any existing codes for this user
    result = await db.execute(
        select(TelegramLinkCode).where(TelegramLinkCode.user_id == user_id)
    )
    existing = result.scalars().all()
    for old_code in existing:
        await db.delete(old_code)

    # Create new code
    link_code = TelegramLinkCode(
        user_id=user_id,
        code=code,
        expires_at=expires_at,
    )
    db.add(link_code)
    await db.commit()

    return {
        "code": code,
        "expires_at": expires_at.isoformat(),
        "instructions": f"Send /start {code} to @SignalBoxHQ on Telegram",
    }


@router.get("/telegram/status")
async def telegram_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Check if Telegram is connected."""
    user_id = get_current_user_id(request)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "connected": bool(user.telegram_chat_id),
    }


@router.delete("/telegram")
async def disconnect_telegram(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Disconnect Telegram."""
    user_id = get_current_user_id(request)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.telegram_chat_id = None
    await db.commit()

    return {"message": "Telegram disconnected"}


# --- Response Templates ---

class TemplateCreate(BaseModel):
    name: str
    template_text: str
    category: Optional[str] = None


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    template_text: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/templates")
async def list_templates(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """List all response templates."""
    user_id = get_current_user_id(request)

    result = await db.execute(
        select(ResponseTemplate)
        .where(ResponseTemplate.user_id == user_id)
        .order_by(ResponseTemplate.category, ResponseTemplate.name)
    )
    templates = result.scalars().all()

    return {
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "template_text": t.template_text,
                "category": t.category,
                "is_active": t.is_active,
            }
            for t in templates
        ]
    }


@router.post("/templates")
async def create_template(
    request: Request,
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new response template."""
    user_id = get_current_user_id(request)

    # Check user tier for template limit
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user and user.tier != "pro":
        # Free users limited to 3 templates
        result = await db.execute(
            select(ResponseTemplate).where(ResponseTemplate.user_id == user_id)
        )
        existing_count = len(result.scalars().all())
        if existing_count >= 3:
            raise HTTPException(
                status_code=403,
                detail="Free tier limited to 3 templates. Upgrade to Pro for unlimited.",
            )

    template = ResponseTemplate(
        user_id=user_id,
        name=data.name,
        template_text=data.template_text,
        category=data.category,
    )
    db.add(template)
    await db.commit()

    return {
        "id": template.id,
        "message": "Template created",
    }


@router.put("/templates/{template_id}")
async def update_template(
    template_id: int,
    request: Request,
    data: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a response template."""
    user_id = get_current_user_id(request)

    result = await db.execute(
        select(ResponseTemplate).where(
            ResponseTemplate.id == template_id,
            ResponseTemplate.user_id == user_id,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if data.name is not None:
        template.name = data.name
    if data.template_text is not None:
        template.template_text = data.template_text
    if data.category is not None:
        template.category = data.category
    if data.is_active is not None:
        template.is_active = data.is_active

    await db.commit()

    return {"message": "Template updated"}


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Delete a response template."""
    user_id = get_current_user_id(request)

    result = await db.execute(
        select(ResponseTemplate).where(
            ResponseTemplate.id == template_id,
            ResponseTemplate.user_id == user_id,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    await db.delete(template)
    await db.commit()

    return {"message": "Template deleted"}


# --- Bio/Promo Text ---

@router.get("/promo-text")
async def get_promo_text(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get recommended bio/promo text for user to add to their X profile."""
    user_id = get_current_user_id(request)

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    handle = settings.monitored_handle

    return {
        "bio_text": f"Feedback? @SignalBoxHQ @{handle} or $feedback @{handle}",
        "pinned_tweet": f"Got feedback for us? Tag @SignalBoxHQ @{handle} or use $bug/$feature/$question @{handle} and we'll see it instantly!",
    }
