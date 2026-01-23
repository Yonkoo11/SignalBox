# SignalBox

## Summary

Feedback collection from X. Three channels: passive monitoring, @SignalBoxHQ tagging, $ signal tags. AI categorizes. Telegram alerts. Bot confirms publicly. Dashboard for triage.

## Build Status: MVP COMPLETE

All core features implemented and ready for deployment.

## Final Decisions

### Bot Account
@SignalBoxHQ

### Data Collection

| Channel | Method | Signal |
|---------|--------|--------|
| Passive | Monitor @product mentions | Medium |
| Bot tag | @SignalBoxHQ + @product | High |
| $ signal | $bug, $feature, etc. | High |

### $ Tags

| Tag | Category |
|-----|----------|
| $feedback | Generic (AI classifies) |
| $bug | Bug |
| $feature | Feature request |
| $question | Question |
| $praise | Praise |
| $complaint | Complaint |

### Pricing Model

| Feature | Free | Pro ($29/mo) |
|---------|------|--------------|
| Feedback collection | Unlimited | Unlimited |
| Classification | Keywords | AI (Claude) |
| AI summaries | None | Yes |
| Telegram alerts | None | Yes |
| Response templates | 3 | Unlimited |
| Data retention | 30 days | 1 year |

New users get 14-day Pro trial, then downgrade to Free.

### Stack

- Backend: Python, FastAPI
- Frontend: Streamlit
- Database: SQLite (dev), PostgreSQL (prod)
- X API: tweepy
- Classification: Claude Haiku
- Alerts: Telegram (python-telegram-bot)
- Payments: Stripe
- Hosting: Render

## Project Structure

```
SignalBox/
├── README.md
├── DEPLOY.md
├── render.yaml
├── .gitignore
├── ai/
│   └── memory.md
└── src/
    ├── requirements.txt
    ├── .env.example
    ├── run.py
    ├── app/
    │   ├── main.py
    │   ├── config.py
    │   ├── database.py
    │   ├── models.py
    │   ├── static/
    │   │   └── index.html (landing page)
    │   ├── routers/
    │   │   ├── auth.py
    │   │   ├── feedback.py
    │   │   ├── settings.py
    │   │   └── billing.py
    │   ├── services/
    │   │   ├── twitter.py
    │   │   ├── collector.py
    │   │   ├── classifier.py
    │   │   ├── alerts.py
    │   │   ├── telegram_bot.py
    │   │   ├── encryption.py
    │   │   └── token_refresh.py
    │   └── tasks/
    │       └── scheduler.py
    └── dashboard/
        ├── app.py
        └── pages/
            ├── inbox.py
            ├── settings.py
            └── account.py
```

## Build Completed

1. [x] X OAuth login + token storage
2. [x] @SignalBoxHQ bot integration
3. [x] Feedback ingestion (all channels)
4. [x] Categorization + priority scoring
5. [x] Inbox dashboard
6. [x] Telegram alerts
7. [x] Settings page
8. [x] Free tier implementation
9. [x] Stripe billing
10. [x] Landing page
11. [x] Deployment config

## Next Steps

1. Deploy to Render
2. Create X bot account (@SignalBoxHQ)
3. Set up Stripe products
4. Configure Telegram bot
5. Dogfood with own product
