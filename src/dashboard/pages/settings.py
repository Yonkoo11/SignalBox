import streamlit as st
import httpx

st.set_page_config(
    page_title="Settings | SignalBox",
    page_icon="⚙️",
    layout="wide",
)

# Config
API_URL = st.secrets.get("API_URL", "http://localhost:8000")


def fetch_settings():
    """Fetch settings from API."""
    try:
        response = httpx.get(f"{API_URL}/api/settings", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def update_settings(data):
    """Update settings."""
    try:
        response = httpx.put(f"{API_URL}/api/settings", json=data, timeout=10)
        return response.status_code == 200
    except Exception:
        return False


def fetch_telegram_status():
    """Check Telegram connection status."""
    try:
        response = httpx.get(f"{API_URL}/api/settings/telegram/status", timeout=10)
        if response.status_code == 200:
            return response.json().get("connected", False)
        return False
    except Exception:
        return False


def create_telegram_link():
    """Create Telegram link code."""
    try:
        response = httpx.post(f"{API_URL}/api/settings/telegram", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def disconnect_telegram():
    """Disconnect Telegram."""
    try:
        response = httpx.delete(f"{API_URL}/api/settings/telegram", timeout=10)
        return response.status_code == 200
    except Exception:
        return False


def fetch_templates():
    """Fetch response templates."""
    try:
        response = httpx.get(f"{API_URL}/api/settings/templates", timeout=10)
        if response.status_code == 200:
            return response.json().get("templates", [])
        return []
    except Exception:
        return []


def fetch_promo_text():
    """Fetch promo text."""
    try:
        response = httpx.get(f"{API_URL}/api/settings/promo-text", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def fetch_user_tier():
    """Fetch user tier from API."""
    try:
        response = httpx.get(f"{API_URL}/api/auth/me", timeout=10)
        if response.status_code == 200:
            return response.json().get("tier", "free")
        return "free"
    except Exception:
        return "free"


# Header
st.title("⚙️ Settings")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Monitoring", "Alerts", "Templates", "Promo Text"])

# --- Monitoring Tab ---
with tab1:
    st.subheader("Monitoring Settings")

    settings = fetch_settings()

    if settings:
        with st.form("monitoring_form"):
            monitored_handle = st.text_input(
                "Monitored Handle",
                value=settings.get("monitored_handle", ""),
                help="Your X handle to monitor (without @)",
            )

            keywords_str = ", ".join(settings.get("extra_keywords", []))
            extra_keywords = st.text_input(
                "Extra Keywords (comma-separated)",
                value=keywords_str,
                help="Additional keywords to monitor (max 5)",
            )

            submitted = st.form_submit_button("Save Changes", use_container_width=True)

            if submitted:
                keywords_list = [k.strip() for k in extra_keywords.split(",") if k.strip()][:5]
                data = {
                    "monitored_handle": monitored_handle.lstrip("@"),
                    "extra_keywords": keywords_list,
                }
                if update_settings(data):
                    st.success("Settings saved!")
                else:
                    st.error("Failed to save settings")
    else:
        st.warning("Could not load settings. Please log in.")

# --- Alerts Tab ---
with tab2:
    st.subheader("Alert Preferences")

    settings = fetch_settings()

    if settings:
        with st.form("alerts_form"):
            alert_on_bugs = st.checkbox(
                "Alert on bug reports",
                value=settings.get("alert_on_bugs", True),
            )
            alert_on_complaints = st.checkbox(
                "Alert on complaints",
                value=settings.get("alert_on_complaints", True),
            )
            alert_on_high_reach = st.checkbox(
                "Alert on high-reach accounts (1k+ followers)",
                value=settings.get("alert_on_high_reach", True),
            )
            alert_min_engagement = st.number_input(
                "Minimum engagement to alert",
                min_value=1,
                max_value=100,
                value=settings.get("alert_min_engagement", 5),
                help="Alert when likes + retweets >= this number",
            )

            submitted = st.form_submit_button("Save Alert Settings", use_container_width=True)

            if submitted:
                data = {
                    "alert_on_bugs": alert_on_bugs,
                    "alert_on_complaints": alert_on_complaints,
                    "alert_on_high_reach": alert_on_high_reach,
                    "alert_min_engagement": alert_min_engagement,
                }
                if update_settings(data):
                    st.success("Alert settings saved!")
                else:
                    st.error("Failed to save settings")

        st.divider()

        # Telegram connection
        st.subheader("Telegram Alerts")

        user_tier = fetch_user_tier()

        if user_tier != "pro":
            st.warning("🔒 Telegram alerts are a Pro feature. Upgrade to receive instant alerts.")
            st.button("Upgrade to Pro", use_container_width=True, disabled=True)
        else:
            telegram_connected = fetch_telegram_status()

            if telegram_connected:
                st.success("✓ Telegram connected")
                if st.button("Disconnect Telegram"):
                    if disconnect_telegram():
                        st.success("Disconnected")
                        st.rerun()
                    else:
                        st.error("Failed to disconnect")
            else:
                st.info("Connect Telegram to receive instant alerts")

                if st.button("Generate Link Code"):
                    link_data = create_telegram_link()
                    if link_data:
                        code = link_data.get("code", "")
                        st.code(f"/start {code}")
                        st.caption("Send this command to @SignalBoxHQ on Telegram")
                    else:
                        st.error("Failed to generate code")
    else:
        st.warning("Could not load settings. Please log in.")

# --- Templates Tab ---
with tab3:
    st.subheader("Response Templates")
    st.caption("Quick replies for common feedback types")

    user_tier_templates = fetch_user_tier()
    if user_tier_templates != "pro":
        st.info("Free tier: 3 templates max. Upgrade to Pro for unlimited templates.")

    templates = fetch_templates()

    if templates:
        for tmpl in templates:
            with st.expander(f"{tmpl.get('name', 'Template')} ({tmpl.get('category', 'any')})"):
                st.text_area(
                    "Template",
                    value=tmpl.get("template_text", ""),
                    key=f"tmpl_{tmpl.get('id')}",
                    disabled=True,
                    label_visibility="collapsed",
                )
                col1, col2 = st.columns(2)
                with col1:
                    st.button("Edit", key=f"edit_{tmpl.get('id')}", disabled=True)
                with col2:
                    st.button("Delete", key=f"delete_{tmpl.get('id')}", disabled=True)
    else:
        st.info("No templates found. Templates are created automatically on signup.")

    st.divider()
    st.caption("Template editing coming soon")

# --- Promo Text Tab ---
with tab4:
    st.subheader("Promo Text")
    st.caption("Add these to your X profile to help users send feedback")

    promo = fetch_promo_text()

    if promo:
        st.markdown("**Bio text:**")
        bio_text = promo.get("bio_text", "")
        st.code(bio_text)
        st.button("📋 Copy", key="copy_bio", disabled=True)

        st.markdown("**Pinned tweet:**")
        pinned_text = promo.get("pinned_tweet", "")
        st.code(pinned_text)
        st.button("📋 Copy", key="copy_pinned", disabled=True)
    else:
        st.warning("Could not load promo text. Please log in.")
