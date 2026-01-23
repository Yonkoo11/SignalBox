# SignalBox Deployment Guide

## Quick Deploy to Render

1. Push code to GitHub
2. Connect repo to Render
3. Use the Blueprint: `render.yaml`

Or deploy manually:

### 1. Create PostgreSQL Database

- Render Dashboard > New > PostgreSQL
- Name: `signalbox-db`
- Plan: Starter ($7/mo)
- Copy the Internal Database URL

### 2. Deploy API Service

- Render Dashboard > New > Web Service
- Connect GitHub repo
- Settings:
  - Name: `signalbox-api`
  - Runtime: Python
  - Build: `pip install -r src/requirements.txt`
  - Start: `cd src && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Health Check: `/health`

### 3. Environment Variables

Set these in Render dashboard:

```
APP_URL=https://signalbox-api.onrender.com
SECRET_KEY=<generate random string>
DATABASE_URL=<from step 1>
ENCRYPTION_KEY=<generate with: openssl rand -hex 32>

# X API
X_CLIENT_ID=<from developer.twitter.com>
X_CLIENT_SECRET=<from developer.twitter.com>
X_BOT_BEARER_TOKEN=<bot account token>
X_BOT_ACCESS_TOKEN=<bot account token>
X_BOT_ACCESS_TOKEN_SECRET=<bot account token>

# Telegram
TELEGRAM_BOT_TOKEN=<from @BotFather>

# Claude
CLAUDE_API_KEY=<from console.anthropic.com>

# Stripe
STRIPE_SECRET_KEY=<from dashboard.stripe.com>
STRIPE_WEBHOOK_SECRET=<from webhook settings>
STRIPE_PRICE_ID=<your $29/mo price ID>
```

### 4. Deploy Dashboard (Optional)

- Render Dashboard > New > Web Service
- Settings:
  - Name: `signalbox-dashboard`
  - Build: `pip install -r src/requirements.txt`
  - Start: `cd src && streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0`
- Environment:
  - `API_URL=https://signalbox-api.onrender.com`

### 5. Configure X OAuth Callback

In Twitter Developer Portal:
- Callback URL: `https://signalbox-api.onrender.com/auth/callback`

### 6. Configure Stripe Webhook

In Stripe Dashboard > Webhooks:
- Endpoint: `https://signalbox-api.onrender.com/api/billing/webhook`
- Events:
  - `checkout.session.completed`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.payment_failed`

---

## Local Development

```bash
cd src
cp .env.example .env
# Fill in .env with your keys

pip install -r requirements.txt
python run.py
```

API runs at http://localhost:8000
Dashboard: `streamlit run dashboard/app.py`

---

## Costs

| Service | Monthly |
|---------|---------|
| Render Web (API) | $7 |
| Render PostgreSQL | $7 |
| Render Web (Dashboard) | $7 |
| X API | Free (Basic) |
| Telegram Bot | Free |
| Claude API | ~$5-20 (usage) |
| Stripe | 2.9% + $0.30/tx |

**Total: ~$21-41/month + Stripe fees**
