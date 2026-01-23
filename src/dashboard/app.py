import streamlit as st

st.set_page_config(
    page_title="SignalBox",
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        max-width: 1400px;
        margin: 0 auto;
    }
    .feedback-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        background: white;
    }
    .priority-high {
        border-left: 4px solid #ef4444;
    }
    .priority-medium {
        border-left: 4px solid #f59e0b;
    }
    .priority-low {
        border-left: 4px solid #6b7280;
    }
    .category-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
    }
    .cat-bug { background: #fee2e2; color: #991b1b; }
    .cat-complaint { background: #fef3c7; color: #92400e; }
    .cat-feature_request { background: #dbeafe; color: #1e40af; }
    .cat-question { background: #f3e8ff; color: #6b21a8; }
    .cat-praise { background: #d1fae5; color: #065f46; }
    .cat-noise { background: #f3f4f6; color: #4b5563; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("📬 SignalBox")
    st.caption("Catch feedback that matters")

    st.divider()

    # Navigation
    page = st.radio(
        "Navigate",
        ["Inbox", "Settings", "Account"],
        label_visibility="collapsed",
    )

    st.divider()

    # Quick stats placeholder
    st.metric("Unhandled", "—")
    st.metric("This Week", "—")

# Main content
if page == "Inbox":
    st.switch_page("pages/inbox.py")
elif page == "Settings":
    st.switch_page("pages/settings.py")
elif page == "Account":
    st.switch_page("pages/account.py")
else:
    # Default to inbox
    st.switch_page("pages/inbox.py")
