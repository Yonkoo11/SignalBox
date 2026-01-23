import stripe
import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import config
from app.database import get_db
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])

# Initialize Stripe
stripe.api_key = config.STRIPE_SECRET_KEY


def get_current_user_id(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


@router.post("/checkout")
async def create_checkout_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe checkout session for Pro subscription."""
    user_id = get_current_user_id(request)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.tier == "pro" and user.subscription_status == "active":
        raise HTTPException(status_code=400, detail="Already subscribed to Pro")

    try:
        # Create or get Stripe customer
        if user.stripe_customer_id:
            customer_id = user.stripe_customer_id
        else:
            customer = stripe.Customer.create(
                metadata={"user_id": str(user.id), "x_username": user.x_username},
            )
            customer_id = customer.id
            user.stripe_customer_id = customer_id
            await db.commit()

        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": config.STRIPE_PRICE_ID,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=f"{config.APP_URL}/dashboard/account?success=true",
            cancel_url=f"{config.APP_URL}/dashboard/account?cancelled=true",
            metadata={"user_id": str(user.id)},
        )

        return {"checkout_url": session.url}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/portal")
async def create_portal_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe customer portal session for managing subscription."""
    user_id = get_current_user_id(request)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing history found")

    try:
        session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=f"{config.APP_URL}/dashboard/account",
        )

        return {"portal_url": session.url}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Stripe webhooks."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, config.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data = event["data"]["object"]

    logger.info(f"Stripe webhook: {event_type}")

    if event_type == "checkout.session.completed":
        await handle_checkout_completed(db, data)

    elif event_type == "customer.subscription.updated":
        await handle_subscription_updated(db, data)

    elif event_type == "customer.subscription.deleted":
        await handle_subscription_deleted(db, data)

    elif event_type == "invoice.payment_failed":
        await handle_payment_failed(db, data)

    return {"status": "ok"}


async def handle_checkout_completed(db: AsyncSession, session: dict):
    """Handle successful checkout."""
    customer_id = session.get("customer")

    result = await db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    user = result.scalar_one_or_none()

    if user:
        user.tier = "pro"
        user.subscription_status = "active"
        await db.commit()
        logger.info(f"User {user.id} upgraded to Pro")


async def handle_subscription_updated(db: AsyncSession, subscription: dict):
    """Handle subscription status changes."""
    customer_id = subscription.get("customer")
    status = subscription.get("status")

    result = await db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        return

    if status == "active":
        user.tier = "pro"
        user.subscription_status = "active"
    elif status == "past_due":
        user.subscription_status = "past_due"
    elif status in ("canceled", "unpaid"):
        user.tier = "free"
        user.subscription_status = "cancelled"

    await db.commit()
    logger.info(f"User {user.id} subscription updated: {status}")


async def handle_subscription_deleted(db: AsyncSession, subscription: dict):
    """Handle subscription cancellation."""
    customer_id = subscription.get("customer")

    result = await db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    user = result.scalar_one_or_none()

    if user:
        user.tier = "free"
        user.subscription_status = "cancelled"
        await db.commit()
        logger.info(f"User {user.id} subscription cancelled")


async def handle_payment_failed(db: AsyncSession, invoice: dict):
    """Handle failed payment."""
    customer_id = invoice.get("customer")

    result = await db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    user = result.scalar_one_or_none()

    if user:
        user.subscription_status = "past_due"
        await db.commit()
        logger.info(f"User {user.id} payment failed")
