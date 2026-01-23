import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from sqlalchemy import select

from app.config import config
from app.database import async_session
from app.models import User, TelegramLinkCode

logger = logging.getLogger(__name__)

# Global application instance
application: Application = None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - link Telegram account."""
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text(
            "Welcome to SignalBox!\n\n"
            "To connect your account:\n"
            "1. Go to your SignalBox dashboard\n"
            "2. Click 'Connect Telegram' in settings\n"
            "3. Copy the link code\n"
            "4. Send /start YOUR-CODE here\n\n"
            "Example: /start LINK-ABC123XY"
        )
        return

    code = args[0].upper()

    async with async_session() as db:
        # Find valid link code
        result = await db.execute(
            select(TelegramLinkCode).where(
                TelegramLinkCode.code == code,
                TelegramLinkCode.used == False,
                TelegramLinkCode.expires_at > datetime.now(timezone.utc),
            )
        )
        link = result.scalar_one_or_none()

        if not link:
            await update.message.reply_text(
                "Invalid or expired code.\n\n"
                "Please get a new code from your SignalBox dashboard."
            )
            return

        # Link the account
        result = await db.execute(
            select(User).where(User.id == link.user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await update.message.reply_text("User not found. Please try again.")
            return

        user.telegram_chat_id = str(chat_id)
        link.used = True
        await db.commit()

        await update.message.reply_text(
            f"Connected! You'll now receive alerts for @{user.x_username}.\n\n"
            "You'll be notified when:\n"
            "- Someone reports a bug\n"
            "- Someone posts a complaint\n"
            "- High-reach accounts mention you\n"
            "- Someone tags @SignalBoxHQ with your handle\n\n"
            "To disconnect, go to Settings in your dashboard."
        )

        logger.info(f"Telegram linked for user {user.id} ({user.x_username})")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    await update.message.reply_text(
        "SignalBox Telegram Bot\n\n"
        "Commands:\n"
        "/start CODE - Connect your SignalBox account\n"
        "/help - Show this help message\n"
        "/status - Check connection status\n\n"
        "Visit signalbox.app for more info."
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    chat_id = str(update.effective_chat.id)

    async with async_session() as db:
        result = await db.execute(
            select(User).where(User.telegram_chat_id == chat_id)
        )
        user = result.scalar_one_or_none()

        if user:
            await update.message.reply_text(
                f"Connected to @{user.x_username}\n"
                f"Status: {user.subscription_status}\n\n"
                "Alerts are active."
            )
        else:
            await update.message.reply_text(
                "Not connected to any SignalBox account.\n\n"
                "Use /start CODE to connect."
            )


def create_bot_application() -> Application:
    """Create the Telegram bot application."""
    global application

    if not config.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set, bot disabled")
        return None

    application = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))

    return application


async def start_bot():
    """Start the Telegram bot."""
    global application

    app = create_bot_application()
    if not app:
        return

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    logger.info("Telegram bot started")


async def stop_bot():
    """Stop the Telegram bot."""
    global application

    if application:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

        logger.info("Telegram bot stopped")
