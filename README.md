# SignalBox

Catch feedback that matters. SignalBox monitors X for mentions of your product and delivers actionable feedback to your inbox.

## Features

- **Three input channels**: Passive monitoring, @SignalBoxHQ tags, $ signals
- **AI classification**: Automatically categorize bugs, complaints, features, questions, praise
- **Telegram alerts**: Instant notifications for high-priority feedback
- **Priority scoring**: Focus on what matters based on reach,engagement, urgency
- **Response templates**: Reply quickly with pre-written responses

## Quick Start

```bash
cd src
cp .env.example .env
# Fill in API keys

pip install -r requirements.txt
python run.py
```

API: http://localhost:8000
Dashboard: `streamlit run dashboard/app.py`

## Deploy

See [DEPLOY.md](DEPLOY.md) for Render deployment guide.

## Stack

- FastAPI + SQLAlchemy
- PostgreSQL (prod) / SQLite (dev)
- Claude Haiku for AI
- Telegram Bot API
- Stripe for payments
- Streamlit dashboard

## Pricing

- **Free**: Unlimited collection, keyword classification, 3 templates
- **Pro ($29/mo)**: AI classification, summaries, Telegram alerts, unlimited templates
