import streamlit as st
import httpx

st.set_page_config(
    page_title="Account | SignalBox",
    page_icon="👤",
    layout="wide",
)

# Config
API_URL = st.secrets.get("API_URL", "http://localhost:8000")


def fetch_account():
    """Fetch account info from API."""
    try:
        response = httpx.get(f"{API_URL}/api/auth/me", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def fetch_usage():
    """Fetch usage stats."""
    try:
        response = httpx.get(f"{API_URL}/api/feedback/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def create_checkout():
    """Create Stripe checkout session."""
    try:
        response = httpx.post(f"{API_URL}/api/billing/checkout", timeout=10)
        if response.status_code == 200:
            return response.json().get("checkout_url")
        return None
    except Exception:
        return None


def create_portal():
    """Create Stripe billing portal session."""
    try:
        response = httpx.post(f"{API_URL}/api/billing/portal", timeout=10)
        if response.status_code == 200:
            return response.json().get("portal_url")
        return None
    except Exception:
        return None


# Header
st.title("👤 Account")

# Handle checkout redirects
query_params = st.query_params
if query_params.get("success"):
    st.success("Payment successful! Your account has been upgraded to Pro.")
    st.query_params.clear()
elif query_params.get("cancelled"):
    st.info("Checkout cancelled. You can try again anytime.")
    st.query_params.clear()

# Fetch data
account = fetch_account()
usage = fetch_usage()

if account:
    # Profile section
    st.subheader("Profile")

    col1, col2 = st.columns([1, 3])

    with col1:
        # Avatar placeholder
        st.markdown("**X Account**")

    with col2:
        username = account.get("x_username", "Unknown")
        st.markdown(f"### @{username}")

        status = account.get("subscription_status", "trial")
        status_colors = {
            "trial": "🟡 Trial",
            "active": "🟢 Active",
            "cancelled": "🔴 Cancelled",
            "expired": "⚫ Expired",
        }
        st.markdown(f"Status: {status_colors.get(status, status)}")

        if status == "trial":
            trial_end = account.get("trial_ends_at")
            if trial_end:
                st.caption(f"Trial ends: {trial_end[:10]}")

    st.divider()

    # Usage section
    st.subheader("Usage")

    if usage:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Feedback", usage.get("total", 0))

        with col2:
            st.metric("This Week", usage.get("this_week", 0))

        with col3:
            st.metric("Handled", usage.get("handled", 0))

        with col4:
            handled = usage.get("handled", 0)
            total = usage.get("total", 1)
            rate = int((handled / total) * 100) if total > 0 else 0
            st.metric("Handle Rate", f"{rate}%")
    else:
        st.info("No usage data available yet.")

    st.divider()

    # Subscription section
    st.subheader("Subscription")

    tier = account.get("tier", "free")

    if tier == "free":
        st.info("You're on the Free plan.")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Free (Current)")
            st.markdown("""
            - Unlimited feedback collection
            - Keyword classification
            - 3 response templates
            - 30-day data retention
            """)

        with col2:
            st.markdown("### Pro - $29/month")
            st.markdown("""
            - AI-powered classification
            - AI summaries
            - Telegram alerts
            - Unlimited templates
            - 1-year data retention
            """)

            if st.button("Upgrade to Pro", use_container_width=True, type="primary"):
                checkout_url = create_checkout()
                if checkout_url:
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={checkout_url}">', unsafe_allow_html=True)
                else:
                    st.error("Failed to create checkout. Try again.")

    elif tier == "pro":
        st.success("You're on the Pro plan.")

        st.markdown("**Plan:** SignalBox Pro ($29/month)")

        next_billing = account.get("next_billing_date")
        if next_billing:
            st.caption(f"Next billing date: {next_billing[:10]}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Manage Billing", use_container_width=True):
                portal_url = create_portal()
                if portal_url:
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={portal_url}">', unsafe_allow_html=True)
                else:
                    st.error("Failed to open billing portal.")

        with col2:
            if st.button("Cancel Subscription", use_container_width=True):
                portal_url = create_portal()
                if portal_url:
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={portal_url}">', unsafe_allow_html=True)
                else:
                    st.warning("Go to Manage Billing to cancel.")

    st.divider()

    # Danger zone
    st.subheader("Danger Zone")

    with st.expander("Delete Account"):
        st.warning("This will permanently delete your account and all data. This action cannot be undone.")

        confirm = st.text_input(
            "Type your username to confirm",
            placeholder=account.get("x_username", ""),
        )

        if st.button("Delete My Account", type="primary"):
            if confirm == account.get("x_username"):
                st.error("Account deletion coming soon. Contact support@signalbox.app")
            else:
                st.error("Username doesn't match")

else:
    # Not logged in
    st.warning("Please log in to view your account.")

    st.markdown("### Get Started")
    st.markdown("Connect your X account to start collecting feedback.")

    if st.button("Login with X", use_container_width=True, type="primary"):
        # Redirect to OAuth
        st.markdown(f"[Click here to login]({API_URL}/api/auth/login)")
