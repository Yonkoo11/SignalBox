import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # App
    APP_URL = os.getenv("APP_URL", "http://localhost:8000")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")

    # Database (supports SQLite for dev, PostgreSQL for prod)
    _db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./signalbox.db")
    # Render uses postgres:// but SQLAlchemy needs postgresql://
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    DATABASE_URL = _db_url

    # X API
    X_CLIENT_ID = os.getenv("X_CLIENT_ID")
    X_CLIENT_SECRET = os.getenv("X_CLIENT_SECRET")

    # X Bot Account
    X_BOT_BEARER_TOKEN = os.getenv("X_BOT_BEARER_TOKEN")
    X_BOT_ACCESS_TOKEN = os.getenv("X_BOT_ACCESS_TOKEN")
    X_BOT_ACCESS_TOKEN_SECRET = os.getenv("X_BOT_ACCESS_TOKEN_SECRET")

    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    # Claude
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

    # Stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")

    # Encryption
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")


config = Config()
