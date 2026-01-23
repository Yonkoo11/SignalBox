import streamlit as st
import httpx
from datetime import datetime

st.set_page_config(
    page_title="Inbox | SignalBox",
    page_icon="📬",
    layout="wide",
)

# Config
API_URL = st.secrets.get("API_URL", "http://localhost:8000")

# Session state
if "user" not in st.session_state:
    st.session_state.user = None


def fetch_user_tier():
    """Fetch user tier from API."""
    try:
        response = httpx.get(f"{API_URL}/api/auth/me", timeout=10)
        if response.status_code == 200:
            return response.json().get("tier", "free")
        return "free"
    except Exception:
        return "free"

# Category colors
CATEGORY_COLORS = {
    "bug": "🔴",
    "complaint": "🟠",
    "feature_request": "🔵",
    "question": "🟣",
    "praise": "🟢",
    "noise": "⚪",
}

CATEGORY_LABELS = {
    "bug": "Bug",
    "complaint": "Complaint",
    "feature_request": "Feature",
    "question": "Question",
    "praise": "Praise",
    "noise": "Noise",
}

PRIORITY_ICONS = {
    "high": "🔥",
    "medium": "📌",
    "low": "📎",
}


def fetch_feedback(category=None, priority=None, handled=None, limit=50):
    """Fetch feedback from API."""
    params = {"limit": limit}
    if category:
        params["category"] = category
    if priority:
        params["priority"] = priority
    if handled is not None:
        params["handled"] = str(handled).lower()

    try:
        # In production, include session cookie
        response = httpx.get(f"{API_URL}/api/feedback", params=params, timeout=10)
        if response.status_code == 200:
            return response.json().get("items", [])
        elif response.status_code == 401:
            st.warning("Please log in to view feedback.")
            return []
        else:
            st.error(f"Failed to fetch feedback: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Connection error: {e}")
        return []


def fetch_stats():
    """Fetch stats from API."""
    try:
        response = httpx.get(f"{API_URL}/api/feedback/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def mark_handled(item_id):
    """Mark item as handled."""
    try:
        response = httpx.post(f"{API_URL}/api/feedback/{item_id}/handle", timeout=10)
        return response.status_code == 200
    except Exception:
        return False


def hide_item(item_id):
    """Hide item."""
    try:
        response = httpx.post(f"{API_URL}/api/feedback/{item_id}/hide", timeout=10)
        return response.status_code == 200
    except Exception:
        return False


def format_time(iso_str):
    """Format ISO timestamp to relative time."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        diff = now - dt

        if diff.days > 7:
            return dt.strftime("%b %d")
        elif diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "just now"
    except Exception:
        return ""


# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📬 Inbox")
with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# Filters
col1, col2, col3, col4 = st.columns(4)

with col1:
    filter_category = st.multiselect(
        "Category",
        options=["bug", "complaint", "feature_request", "question", "praise"],
        default=["bug", "complaint", "feature_request"],
        format_func=lambda x: f"{CATEGORY_COLORS.get(x, '')} {CATEGORY_LABELS.get(x, x)}",
    )

with col2:
    filter_priority = st.multiselect(
        "Priority",
        options=["high", "medium", "low"],
        default=["high", "medium"],
        format_func=lambda x: f"{PRIORITY_ICONS.get(x, '')} {x.title()}",
    )

with col3:
    filter_handled = st.selectbox(
        "Status",
        options=[None, False, True],
        index=1,
        format_func=lambda x: "All" if x is None else ("Unhandled" if not x else "Handled"),
    )

with col4:
    show_hidden = st.checkbox("Show hidden", value=False)

st.divider()

# Fetch data
category_param = ",".join(filter_category) if filter_category else None
priority_param = ",".join(filter_priority) if filter_priority else None

items = fetch_feedback(
    category=category_param,
    priority=priority_param,
    handled=filter_handled,
)

# Stats bar
stats = fetch_stats()
if stats:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", stats.get("total", 0))
    with col2:
        st.metric("Unhandled", stats.get("unhandled", 0))
    with col3:
        bugs = stats.get("by_category", {}).get("bug", 0)
        complaints = stats.get("by_category", {}).get("complaint", 0)
        st.metric("Bugs + Complaints", bugs + complaints)
    with col4:
        high = stats.get("by_priority", {}).get("high", 0)
        st.metric("High Priority", high)

st.divider()

# Get user tier for upgrade prompts
user_tier = fetch_user_tier()

# Feedback list
if not items:
    st.info("No feedback items match your filters. Try adjusting the filters or check back later.")
else:
    for item in items:
        with st.container():
            # Card header
            col1, col2, col3 = st.columns([1, 6, 2])

            with col1:
                cat = item.get("category", "noise")
                priority = item.get("priority", "low")
                st.markdown(f"**{CATEGORY_COLORS.get(cat, '⚪')} {PRIORITY_ICONS.get(priority, '')}**")

            with col2:
                author = item.get("author_username", "unknown")
                followers = item.get("author_followers", 0)
                st.markdown(f"**@{author}** · {followers:,} followers")

            with col3:
                time_str = format_time(item.get("tweet_created_at"))
                st.caption(time_str)

            # Tweet text
            text = item.get("tweet_text", "")
            st.markdown(f"> {text}")

            # Summary (Pro only)
            summary = item.get("summary")
            if user_tier == "pro" and summary:
                st.caption(f"📝 {summary}")
            elif user_tier != "pro":
                st.caption("🔒 Upgrade to Pro for AI summaries")

            # Tags row
            col1, col2, col3, col4 = st.columns([2, 2, 2, 4])

            with col1:
                cat_label = CATEGORY_LABELS.get(cat, cat)
                st.caption(f"Category: **{cat_label}**")

            with col2:
                sentiment = item.get("sentiment", "neutral")
                sentiment_icon = {"frustrated": "😤", "neutral": "😐", "happy": "😊"}.get(sentiment, "")
                st.caption(f"Sentiment: {sentiment_icon} {sentiment}")

            with col3:
                source = item.get("source", "passive")
                signal_tag = item.get("signal_tag")
                source_text = signal_tag if signal_tag else source.replace("_", " ").title()
                st.caption(f"Source: {source_text}")

            with col4:
                likes = item.get("likes", 0)
                retweets = item.get("retweets", 0)
                st.caption(f"❤️ {likes} · 🔁 {retweets}")

            # Actions
            col1, col2, col3, col4 = st.columns(4)

            item_id = item.get("id")
            is_handled = item.get("is_handled", False)

            with col1:
                tweet_url = item.get("tweet_url", "")
                if tweet_url:
                    st.link_button("View on X", tweet_url, use_container_width=True)

            with col2:
                if not is_handled:
                    if st.button("✓ Mark Handled", key=f"handle_{item_id}", use_container_width=True):
                        if mark_handled(item_id):
                            st.success("Marked as handled")
                            st.rerun()
                        else:
                            st.error("Failed to mark as handled")
                else:
                    st.button("✓ Handled", key=f"handled_{item_id}", disabled=True, use_container_width=True)

            with col3:
                if st.button("🗑 Hide", key=f"hide_{item_id}", use_container_width=True):
                    if hide_item(item_id):
                        st.success("Hidden")
                        st.rerun()
                    else:
                        st.error("Failed to hide")

            with col4:
                # Copy reply template button (placeholder)
                st.button("💬 Reply", key=f"reply_{item_id}", use_container_width=True, disabled=True)

            st.divider()

# Footer
st.caption(f"Showing {len(items)} items")
