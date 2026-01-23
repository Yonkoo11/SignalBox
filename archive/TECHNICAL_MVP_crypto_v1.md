# FUDShield - Technical MVP Specification

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FUDSHIELD MVP                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   Streamlit  │────▶│   FastAPI    │────▶│  PostgreSQL  │    │
│  │  Dashboard   │     │   Backend    │     │   (Render)   │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│         │                    │                    │             │
│         │                    ▼                    │             │
│         │            ┌──────────────┐             │             │
│         │            │  Background  │             │             │
│         │            │   Scheduler  │             │             │
│         │            │ (APScheduler)│             │             │
│         │            └──────────────┘             │             │
│         │                    │                    │             │
│         ▼                    ▼                    ▼             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    External Services                      │  │
│  │  ┌────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │  │
│  │  │ X API  │  │ Telegram │  │  Stripe  │  │ Claude API │  │  │
│  │  │  v2    │  │   Bot    │  │ Checkout │  │ (replies)  │  │  │
│  │  └────────┘  └──────────┘  └──────────┘  └────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Reason |
|-------|------------|--------|
| Backend | FastAPI (Python 3.11+) | Async, fast, great for APIs, Claude-friendly |
| Frontend | Streamlit | Rapid prototyping, Python-native, good enough for MVP |
| Database | PostgreSQL (Render free tier) | Reliable, free, easy migration path |
| X API | tweepy v4.x | Battle-tested, v2 support, handles OAuth/pagination |
| Alerts | python-telegram-bot | Async, well-documented, reliable |
| Sentiment | VADER + custom crypto lexicon | Fast, no API costs, customizable |
| Payments | stripe-python | Standard, well-documented |
| Scheduler | APScheduler | In-process, simple, no Redis needed for MVP |
| Hosting | Render | Free tier, good Python support, easy deploys |

---

## Project Structure

```
FUDShield/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Environment config
│   ├── models.py               # SQLAlchemy models
│   ├── database.py             # DB connection
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py             # X OAuth endpoints
│   │   ├── mentions.py         # Threat feed API
│   │   ├── settings.py         # User settings API
│   │   └── webhooks.py         # Stripe webhooks
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── twitter.py          # X API wrapper (tweepy)
│   │   ├── sentiment.py        # Sentiment analysis
│   │   ├── alerts.py           # Telegram notifications
│   │   ├── replies.py          # Auto-reply logic
│   │   └── billing.py          # Stripe integration
│   │
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── scheduler.py        # APScheduler setup
│   │   ├── monitor.py          # Mention polling job
│   │   └── spike_detector.py   # FUD spike detection
│   │
│   └── utils/
│       ├── __init__.py
│       └── crypto_lexicon.py   # Crypto sentiment words
│
├── dashboard/
│   ├── app.py                  # Streamlit entry
│   ├── pages/
│   │   ├── threat_feed.py      # Main threat feed view
│   │   ├── settings.py         # Settings page
│   │   └── account.py          # Billing/account page
│   └── components/
│       └── mention_card.py     # Tweet card component
│
├── tests/
│   ├── test_sentiment.py
│   ├── test_spike_detection.py
│   └── test_auth.py
│
├── requirements.txt
├── render.yaml                 # Render deployment config
├── .env.example
└── README.md
```

---

## Database Schema

### users

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    x_user_id VARCHAR(255) UNIQUE NOT NULL,
    x_username VARCHAR(255) NOT NULL,
    x_access_token TEXT NOT NULL,           -- encrypted
    x_refresh_token TEXT NOT NULL,          -- encrypted
    telegram_chat_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    subscription_status VARCHAR(50) DEFAULT 'trial',  -- trial, active, cancelled, past_due
    trial_ends_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### user_settings

```sql
CREATE TABLE user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    monitored_handle VARCHAR(255) NOT NULL,   -- default: their @handle
    extra_keywords TEXT[],                     -- up to 3 additional
    alert_threshold_count INTEGER DEFAULT 10, -- mentions per window
    alert_threshold_sentiment INTEGER DEFAULT -60,
    alert_window_minutes INTEGER DEFAULT 15,
    auto_reply_enabled BOOLEAN DEFAULT false,
    auto_reply_positive_only BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### reply_templates

```sql
CREATE TABLE reply_templates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    template_text TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### mentions (cached for threat feed)

```sql
CREATE TABLE mentions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    tweet_id VARCHAR(255) UNIQUE NOT NULL,
    tweet_text TEXT NOT NULL,
    tweet_author VARCHAR(255),
    tweet_author_followers INTEGER,
    sentiment_score FLOAT,                    -- -100 to +100
    risk_level VARCHAR(20),                   -- high, medium, low
    matched_keywords TEXT[],
    tweet_created_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast threat feed queries
CREATE INDEX idx_mentions_user_sentiment ON mentions(user_id, sentiment_score, fetched_at DESC);
```

### alert_log

```sql
CREATE TABLE alert_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    alert_type VARCHAR(50),                   -- spike, keyword, threshold
    mention_count INTEGER,
    avg_sentiment FLOAT,
    top_keywords TEXT[],
    sent_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints

### Authentication

```
GET  /auth/login           → Redirect to X OAuth
GET  /auth/callback        → Handle OAuth callback, create user, redirect to dashboard
POST /auth/logout          → Revoke tokens, clear session
GET  /auth/me              → Get current user info
```

### Mentions / Threat Feed

```
GET  /api/mentions         → Get threat feed (paginated)
     ?severity=high,medium
     &hours=24
     &limit=50
     &offset=0

GET  /api/mentions/stats   → Get current stats (count, avg sentiment, spike status)
```

### Settings

```
GET  /api/settings                → Get user settings
PUT  /api/settings                → Update settings
POST /api/settings/telegram       → Initiate Telegram connection
GET  /api/settings/telegram/verify → Verify Telegram connection
GET  /api/templates               → Get reply templates
PUT  /api/templates               → Update templates
```

### Billing

```
POST /api/billing/checkout        → Create Stripe checkout session
POST /api/billing/portal          → Create Stripe billing portal session
POST /webhooks/stripe             → Handle Stripe events
```

---

## Core Logic

### X API Polling (monitor.py)

```python
# Runs every 2 minutes for each active user
async def poll_mentions(user_id: int):
    user = await get_user(user_id)
    settings = await get_settings(user_id)

    # Build search query
    query = f"@{settings.monitored_handle} OR #{settings.monitored_handle}"
    for keyword in settings.extra_keywords:
        query += f" OR {keyword}"

    # Fetch recent mentions (last 15 min to avoid duplicates)
    client = get_twitter_client(user.x_access_token)
    tweets = client.search_recent_tweets(
        query=query,
        max_results=100,
        tweet_fields=['created_at', 'author_id', 'public_metrics'],
        user_fields=['username', 'public_metrics'],
        expansions=['author_id'],
        start_time=datetime.utcnow() - timedelta(minutes=15)
    )

    for tweet in tweets.data or []:
        # Skip if already processed
        if await mention_exists(tweet.id):
            continue

        # Analyze sentiment
        score, keywords = analyze_sentiment(tweet.text)
        risk = 'high' if score < -60 else 'medium' if score < -30 else 'low'

        # Store
        await save_mention(
            user_id=user_id,
            tweet_id=tweet.id,
            tweet_text=tweet.text,
            sentiment_score=score,
            risk_level=risk,
            matched_keywords=keywords
        )
```

### Sentiment Analysis (sentiment.py)

```python
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Crypto-specific lexicon additions
CRYPTO_LEXICON = {
    # High negative
    'scam': -4.0,
    'rug': -4.0,
    'rugpull': -4.0,
    'rug pull': -4.0,
    'exit scam': -4.0,
    'honeypot': -3.5,
    'ponzi': -3.5,
    'fraud': -3.5,
    'hacked': -3.0,
    'drained': -3.0,
    'exploit': -2.5,

    # Medium negative
    'fud': -2.0,
    'dump': -2.0,
    'dumping': -2.0,
    'bearish': -1.5,
    'sus': -1.5,
    'sketchy': -1.5,
    'shady': -1.5,

    # Positive
    'moon': 3.0,
    'mooning': 3.0,
    'bullish': 2.5,
    'lfg': 2.5,
    'wagmi': 2.0,
    'gm': 1.0,
    'based': 2.0,
    'alpha': 1.5,
    'gem': 2.0,
    'diamond hands': 2.0,
}

analyzer = SentimentIntensityAnalyzer()
analyzer.lexicon.update(CRYPTO_LEXICON)

def analyze_sentiment(text: str) -> tuple[float, list[str]]:
    """Returns sentiment score (-100 to +100) and matched keywords."""
    scores = analyzer.polarity_scores(text)

    # Convert compound (-1 to 1) to our scale (-100 to +100)
    sentiment_score = scores['compound'] * 100

    # Find matched high-risk keywords
    text_lower = text.lower()
    matched = [kw for kw in CRYPTO_LEXICON if kw in text_lower and CRYPTO_LEXICON[kw] < -2]

    return sentiment_score, matched
```

### FUD Spike Detection (spike_detector.py)

```python
# Runs every 5 minutes
async def check_for_spikes(user_id: int):
    settings = await get_settings(user_id)
    window_start = datetime.utcnow() - timedelta(minutes=settings.alert_window_minutes)

    # Get recent mentions
    mentions = await get_mentions_since(user_id, window_start)

    if not mentions:
        return

    # Calculate metrics
    negative_mentions = [m for m in mentions if m.sentiment_score < 0]
    count = len(negative_mentions)
    avg_sentiment = sum(m.sentiment_score for m in negative_mentions) / count if count else 0

    # Check thresholds
    is_spike = (
        count >= settings.alert_threshold_count or
        avg_sentiment <= settings.alert_threshold_sentiment
    )

    if is_spike:
        # Check cooldown (no duplicate alerts within 30 min)
        last_alert = await get_last_alert(user_id)
        if last_alert and (datetime.utcnow() - last_alert.sent_at).seconds < 1800:
            return

        # Get top keywords
        all_keywords = []
        for m in negative_mentions:
            all_keywords.extend(m.matched_keywords)
        top_keywords = Counter(all_keywords).most_common(3)

        # Send alert
        await send_telegram_alert(
            user_id=user_id,
            mention_count=count,
            avg_sentiment=avg_sentiment,
            top_keywords=[kw for kw, _ in top_keywords],
            window_minutes=settings.alert_window_minutes
        )

        # Log alert
        await log_alert(user_id, 'spike', count, avg_sentiment, top_keywords)
```

### Telegram Alert (alerts.py)

```python
from telegram import Bot
from telegram.constants import ParseMode

bot = Bot(token=config.TELEGRAM_BOT_TOKEN)

async def send_telegram_alert(
    user_id: int,
    mention_count: int,
    avg_sentiment: float,
    top_keywords: list[str],
    window_minutes: int
):
    user = await get_user(user_id)
    if not user.telegram_chat_id:
        return

    severity = "HIGH" if avg_sentiment < -60 else "MEDIUM"
    emoji = "🚨" if severity == "HIGH" else "⚠️"

    message = f"""
{emoji} *FUD SPIKE DETECTED* {emoji}

*Severity:* {severity}
*Mentions:* {mention_count} in {window_minutes}min
*Avg Sentiment:* {avg_sentiment:.0f}
*Top Keywords:* {', '.join(top_keywords) or 'N/A'}

[View Threat Feed]({config.APP_URL}/threat-feed?spike=true)
"""

    await bot.send_message(
        chat_id=user.telegram_chat_id,
        text=message,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )
```

### Auto-Reply (replies.py)

```python
import anthropic
import random

client = anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)

async def generate_reply_variation(template: str, tweet_context: str) -> str:
    """Use Claude to add natural variation to template."""
    response = client.messages.create(
        model="claude-3-haiku-20240307",  # Fast and cheap
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": f"""Rewrite this reply to be slightly different while keeping the same meaning and tone.
Keep it under 280 characters. Make it feel natural, not robotic.
Add relevant crypto enthusiasm if appropriate.

Original: {template}
Context (tweet we're replying to): {tweet_context}

Just output the rewritten reply, nothing else."""
        }]
    )
    return response.content[0].text.strip()

async def maybe_auto_reply(user_id: int, mention: Mention):
    settings = await get_settings(user_id)

    if not settings.auto_reply_enabled:
        return

    if settings.auto_reply_positive_only and mention.sentiment_score < 30:
        return

    # Check throttle (1 reply per 5 min)
    last_reply = await get_last_reply(user_id)
    if last_reply and (datetime.utcnow() - last_reply.sent_at).seconds < 300:
        return

    # Get random active template
    templates = await get_active_templates(user_id)
    if not templates:
        return

    template = random.choice(templates)

    # Generate variation
    reply_text = await generate_reply_variation(template.template_text, mention.tweet_text)

    # Post reply
    user = await get_user(user_id)
    twitter = get_twitter_client(user.x_access_token)
    twitter.create_tweet(
        text=reply_text,
        in_reply_to_tweet_id=mention.tweet_id
    )

    # Log
    await log_reply(user_id, mention.tweet_id, reply_text)
```

---

## X OAuth 2.0 Flow

### Login Endpoint

```python
from authlib.integrations.starlette_client import OAuth
import secrets

oauth = OAuth()
oauth.register(
    name='twitter',
    client_id=config.X_CLIENT_ID,
    client_secret=config.X_CLIENT_SECRET,
    authorize_url='https://twitter.com/i/oauth2/authorize',
    access_token_url='https://api.twitter.com/2/oauth2/token',
    client_kwargs={
        'scope': 'tweet.read users.read offline.access tweet.write',
        'code_challenge_method': 'S256'
    }
)

@router.get('/auth/login')
async def login(request: Request):
    redirect_uri = f"{config.APP_URL}/auth/callback"
    return await oauth.twitter.authorize_redirect(request, redirect_uri)

@router.get('/auth/callback')
async def callback(request: Request):
    token = await oauth.twitter.authorize_access_token(request)

    # Get user info
    client = tweepy.Client(bearer_token=token['access_token'])
    user_info = client.get_me(user_fields=['username'])

    # Create or update user
    user = await upsert_user(
        x_user_id=user_info.data.id,
        x_username=user_info.data.username,
        x_access_token=encrypt(token['access_token']),
        x_refresh_token=encrypt(token['refresh_token'])
    )

    # Create default settings
    await create_default_settings(user.id, user_info.data.username)

    # Set session
    request.session['user_id'] = user.id

    return RedirectResponse(url='/dashboard')
```

---

## Environment Variables

```bash
# App
APP_URL=https://fudshield.com
SECRET_KEY=<random-32-chars>

# Database
DATABASE_URL=postgresql://user:pass@host:5432/fudshield

# X API (from developer.twitter.com)
X_CLIENT_ID=<your-client-id>
X_CLIENT_SECRET=<your-client-secret>

# Telegram (from @BotFather)
TELEGRAM_BOT_TOKEN=<your-bot-token>

# Claude API (for reply variations)
CLAUDE_API_KEY=<your-api-key>

# Stripe
STRIPE_SECRET_KEY=<your-secret-key>
STRIPE_WEBHOOK_SECRET=<your-webhook-secret>
STRIPE_PRICE_ID=<your-price-id>  # $29/month product

# Encryption key for tokens
ENCRYPTION_KEY=<random-32-chars>
```

---

## Deployment (Render)

### render.yaml

```yaml
services:
  # FastAPI Backend
  - type: web
    name: fudshield-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: fudshield-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: X_CLIENT_ID
        sync: false
      - key: X_CLIENT_SECRET
        sync: false
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: CLAUDE_API_KEY
        sync: false
      - key: STRIPE_SECRET_KEY
        sync: false

  # Streamlit Dashboard
  - type: web
    name: fudshield-dashboard
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: API_URL
        value: https://fudshield-api.onrender.com

databases:
  - name: fudshield-db
    plan: free
```

---

## Rate Limits and Quotas

### X API (Pro Tier - $100/month)

| Endpoint | Limit | Our Usage |
|----------|-------|-----------|
| Search recent | 450 req/15min | ~20 users × 7 polls/15min = 140 |
| Post tweet | 50/3hr per user | Max 12 auto-replies/hr |
| User lookup | 900/15min | Minimal |

**Headroom**: Comfortable for 20-30 users. Scale to Enterprise at ~50+ users.

### Telegram Bot API

| Limit | Value |
|-------|-------|
| Messages per second | 30 |
| Messages per chat per minute | 20 |

**Headroom**: Plenty for alerts.

### Claude API (Haiku)

| Metric | Cost |
|--------|------|
| Input | $0.25/1M tokens |
| Output | $1.25/1M tokens |

**Estimate**: ~$5/month for 1000 reply variations.

---

## Security Considerations

1. **Token encryption**: X tokens encrypted at rest using Fernet (symmetric encryption)
2. **HTTPS only**: Render provides free SSL
3. **OAuth state validation**: Prevent CSRF on auth flow
4. **Stripe webhook verification**: Validate signatures
5. **Rate limiting**: FastAPI middleware to prevent abuse
6. **No secrets in logs**: Sanitize all logging

---

## Testing Strategy

### Unit Tests
- Sentiment analysis with crypto terms
- Spike detection thresholds
- Reply throttling logic

### Integration Tests
- X OAuth flow (mock)
- Telegram message sending (test bot)
- Stripe webhook handling

### Manual Testing
- Full signup flow
- FUD spike alert (trigger manually)
- Auto-reply posting (test account)

---

## Monitoring (MVP)

- **Render logs**: Built-in log streaming
- **Uptime**: Render health checks
- **Errors**: Basic try/catch logging to stdout
- **Alerts**: Manual check of alert_log table

Post-MVP: Add Sentry for error tracking, better metrics.

---

## Development Workflow

```bash
# Local setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in values

# Run locally
uvicorn app.main:app --reload  # API on :8000
streamlit run dashboard/app.py  # Dashboard on :8501

# Deploy
git push origin main  # Auto-deploys on Render
```

---

## Week-by-Week Build Plan

### Week 1: Foundation
- [ ] Project setup (FastAPI, Streamlit, PostgreSQL)
- [ ] Database models and migrations
- [ ] X OAuth 2.0 login flow
- [ ] Basic user creation and session
- [ ] Telegram bot setup (/start command)

### Week 2: Core Value
- [ ] Mention polling service
- [ ] Sentiment analysis with crypto lexicon
- [ ] Mention storage and threat feed API
- [ ] Threat feed UI (Streamlit)
- [ ] FUD spike detection
- [ ] Telegram alert sending

### Week 3: Engagement
- [ ] Reply templates CRUD
- [ ] Claude integration for variations
- [ ] Auto-reply service with throttling
- [ ] Settings page (keywords, thresholds, templates)
- [ ] Telegram connection flow in settings

### Week 4: Launch
- [ ] Stripe integration (checkout, webhooks, trial logic)
- [ ] Landing page
- [ ] Deploy to Render (API + Dashboard)
- [ ] Domain setup
- [ ] Beta invites
- [ ] Monitor and fix issues

---

## Future Enhancements (Post-MVP)

- Discord/Slack alert channels
- Historical sentiment charts
- Multi-account for agencies
- Mobile PWA with push
- Influencer tracking (who's talking about you)
- Competitor monitoring
- AI-generated crisis response suggestions
- Webhook integrations (Zapier, custom)
