from datetime import datetime, timedelta
from sqlalchemy import String, Integer, Boolean, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    x_user_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    x_username: Mapped[str] = mapped_column(String(255), nullable=False)
    x_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    x_refresh_token: Mapped[str] = mapped_column(Text, nullable=False)

    telegram_chat_id: Mapped[str | None] = mapped_column(String(255))
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    subscription_status: Mapped[str] = mapped_column(String(50), default="trial")
    tier: Mapped[str] = mapped_column(String(20), default="free")  # free, pro
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime)
    needs_reauth: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    monitoring_since: Mapped[datetime | None] = mapped_column(DateTime)

    settings: Mapped["UserSettings"] = relationship(back_populates="user", uselist=False)
    feedback_items: Mapped[list["FeedbackItem"]] = relationship(back_populates="user")
    templates: Mapped[list["ResponseTemplate"]] = relationship(back_populates="user")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    monitored_handle: Mapped[str] = mapped_column(String(255), nullable=False)
    extra_keywords: Mapped[str | None] = mapped_column(Text)  # JSON array stored as string

    alert_on_bugs: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_on_complaints: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_on_high_reach: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_min_engagement: Mapped[int] = mapped_column(Integer, default=5)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="settings")


class FeedbackItem(Base):
    __tablename__ = "feedback_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    tweet_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    tweet_text: Mapped[str] = mapped_column(Text, nullable=False)
    tweet_url: Mapped[str | None] = mapped_column(Text)
    author_username: Mapped[str | None] = mapped_column(String(255))
    author_followers: Mapped[int | None] = mapped_column(Integer)

    source: Mapped[str] = mapped_column(String(20), nullable=False)  # passive, bot_tag, signal_tag
    signal_tag: Mapped[str | None] = mapped_column(String(20))  # $bug, $feature, etc.

    category: Mapped[str] = mapped_column(String(50), nullable=False)
    sentiment: Mapped[str | None] = mapped_column(String(20))
    confidence: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str | None] = mapped_column(Text)

    priority: Mapped[str] = mapped_column(String(20), default="medium")  # high, medium, low
    likes: Mapped[int] = mapped_column(Integer, default=0)
    retweets: Mapped[int] = mapped_column(Integer, default=0)

    is_handled: Mapped[bool] = mapped_column(Boolean, default=False)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)

    tweet_created_at: Mapped[datetime | None] = mapped_column(DateTime)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="feedback_items")


class ResponseTemplate(Base):
    __tablename__ = "response_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    template_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="templates")


class TelegramLinkCode(Base):
    __tablename__ = "telegram_link_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class AlertLog(Base):
    __tablename__ = "alert_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    feedback_item_id: Mapped[int | None] = mapped_column(ForeignKey("feedback_items.id"))
    alert_reason: Mapped[str | None] = mapped_column(String(100))
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
