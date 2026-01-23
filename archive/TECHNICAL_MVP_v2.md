# SignalBox - Technical MVP Specification

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         SIGNALBOX MVP                           │
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
│  │  │  v2    │  │   Bot    │  │ Checkout │  │ (classify) │  │  │
│  │  └────────┘  └──────────┘  └──────────┘  └────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Reason |
|-------|------------|--------|
| Backend | FastAPI (Python 3.11+) | Async, fast, Claude-friendly |
| Frontend | Streamlit | Rapid MVP, Python-native |
| Database | PostgreSQL (Render free tier) | Reliable, free |
| X API | tweepy v4.x | Battle-tested, v2 support |
| Alerts | python-telegram-bot | Async, reliable |
| Classification | Claude Haiku | Fast, accurate categorization |
| Payments | stripe-python | Standard |
| Scheduler | APScheduler | Simple, no Redis needed |
| Hosting | Render | Free tier, easy deploys |

---

## Project Structure

```
signalbox/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry
│   ├── config.py               # Environment config
│   ├── models.py               # SQLAlchemy models
│   ├── database.py             # DB connection
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py             # X OAuth endpoints
│   │   ├── feedback.py         # Inbox API
│   │   ├── settings.py         # User settings API
│   │   └── webhooks.py         # Stripe webhooks
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── twitter.py          # X API wrapper
│   │   ├── classifier.py       # Claude categorization
│   │   ├── alerts.py           # Telegram notifications
│   │   └── billing.py          # Stripe integration
│   │
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── scheduler.py        # APScheduler setup
│   │   ├── monitor.py          # Mention polling
│   │   └── signal_detector.py  # High-signal detection
│   │
│   └── utils/
│       ├── __init__.py
│       └── prompts.py          # Classification prompts
│
├── dashboard/
│   ├── app.py                  # Streamlit entry
│   ├── pages/
│   │   ├── inbox.py            # Main feedback inbox
│   │   ├── settings.py         # Settings page
│   │   └── account.py          # Billing page
│   └── components/
│       └── feedback_card.py    # Tweet card component
│
├── tests/
│   ├── test_classifier.py
│   ├── test_signal_detection.py
│   └── test_auth.py
│
├── requirements.txt
├── render.yaml
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
    subscription_status VARCHAR(50) DEFAULT 'trial',
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
    monitored_handle VARCHAR(255) NOT NULL,
    extra_keywords TEXT[],                     -- up to 5
    alert_on_bugs BOOLEAN DEFAULT true,
    alert_on_complaints BOOLEAN DEFAULT true,
    alert_on_high_reach BOOLEAN DEFAULT true,  -- 1k+ followers
    alert_min_engagement INTEGER DEFAULT 5,    -- likes+RTs to alert
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### feedback_items

```sql
CREATE TABLE feedback_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    tweet_id VARCHAR(255) UNIQUE NOT NULL,
    tweet_text TEXT NOT NULL,
    tweet_url TEXT,
    author_username VARCHAR(255),
    author_display_name VARCHAR(255),
    author_followers INTEGER,
    author_avatar_url TEXT,

    -- Classification
    category VARCHAR(50) NOT NULL,            -- bug, complaint, feature_request, question, praise, noise
    sentiment VARCHAR(20),                     -- frustrated, neutral, happy
    confidence FLOAT,
    summary TEXT,                              -- AI-generated one-liner

    -- Metrics
    likes INTEGER DEFAULT 0,
    retweets INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,

    -- Status
    is_handled BOOLEAN DEFAULT false,
    handled_at TIMESTAMP,
    is_hidden BOOLEAN DEFAULT false,          -- user dismissed as noise

    tweet_created_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_feedback_user_category ON feedback_items(user_id, category, fetched_at DESC);
CREATE INDEX idx_feedback_unhandled ON feedback_items(user_id, is_handled, is_hidden, fetched_at DESC);
```

### response_templates

```sql
CREATE TABLE response_templates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100),                        -- "Bug acknowledged", "Thanks for feedback"
    template_text TEXT NOT NULL,
    category VARCHAR(50),                     -- Which category this template is for
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### alert_log

```sql
CREATE TABLE alert_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    feedback_item_id INTEGER REFERENCES feedback_items(id),
    alert_reason VARCHAR(100),                -- "bug_detected", "high_reach", "high_engagement"
    sent_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints

### Authentication

```
GET  /auth/login           → Redirect to X OAuth
GET  /auth/callback        → Handle callback, create user
POST /auth/logout          → Clear session
GET  /auth/me              → Current user info
```

### Feedback Inbox

```
GET  /api/feedback                  → Get inbox (paginated)
     ?category=bug,complaint,feature_request
     &handled=false
     &hours=168                      # 7 days default
     &limit=50
     &offset=0

GET  /api/feedback/{id}             → Get single item
POST /api/feedback/{id}/handle      → Mark as handled
POST /api/feedback/{id}/hide        → Hide from inbox
GET  /api/feedback/stats            → Counts by category
```

### Settings

```
GET  /api/settings                  → Get user settings
PUT  /api/settings                  → Update settings
POST /api/settings/telegram         → Start Telegram connection
GET  /api/settings/telegram/verify  → Verify connection
GET  /api/templates                 → Get response templates
PUT  /api/templates                 → Update templates
```

### Billing

```
POST /api/billing/checkout          → Create Stripe session
POST /api/billing/portal            → Billing portal
POST /webhooks/stripe               → Stripe events
```

---

## Core Logic

### Mention Polling (monitor.py)

```python
async def poll_mentions(user_id: int):
    user = await get_user(user_id)
    settings = await get_settings(user_id)

    # Build query
    query = f"@{settings.monitored_handle}"
    for keyword in settings.extra_keywords or []:
        query += f" OR {keyword}"

    # Exclude own tweets and retweets
    query += f" -from:{settings.monitored_handle} -is:retweet"

    client = get_twitter_client(user.x_access_token)
    tweets = client.search_recent_tweets(
        query=query,
        max_results=100,
        tweet_fields=['created_at', 'public_metrics', 'author_id'],
        user_fields=['username', 'name', 'public_metrics', 'profile_image_url'],
        expansions=['author_id'],
        start_time=datetime.utcnow() - timedelta(minutes=15)
    )

    for tweet in tweets.data or []:
        if await feedback_exists(tweet.id):
            continue

        author = get_author(tweets.includes['users'], tweet.author_id)

        # Classify with Claude
        classification = await classify_feedback(
            tweet_text=tweet.text,
            author_username=author.username,
            author_followers=author.public_metrics['followers_count']
        )

        # Skip noise unless low confidence
        if classification['category'] == 'noise' and classification['confidence'] > 0.8:
            continue

        # Save
        item = await save_feedback_item(
            user_id=user_id,
            tweet_id=tweet.id,
            tweet_text=tweet.text,
            tweet_url=f"https://x.com/{author.username}/status/{tweet.id}",
            author_username=author.username,
            author_display_name=author.name,
            author_followers=author.public_metrics['followers_count'],
            author_avatar_url=author.profile_image_url,
            category=classification['category'],
            sentiment=classification['sentiment'],
            confidence=classification['confidence'],
            summary=classification['summary'],
            likes=tweet.public_metrics['like_count'],
            retweets=tweet.public_metrics['retweet_count'],
            replies=tweet.public_metrics['reply_count'],
            tweet_created_at=tweet.created_at
        )

        # Check if alert-worthy
        await maybe_send_alert(user_id, item, settings)
```

### Classification (classifier.py)

```python
import anthropic

client = anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)

CLASSIFICATION_PROMPT = """Analyze this tweet mentioning a product and categorize the feedback.

Tweet: "{tweet_text}"
Author: @{author_username} ({author_followers} followers)

Respond with JSON only, no other text:
{{
  "category": "bug" | "complaint" | "feature_request" | "question" | "praise" | "noise",
  "sentiment": "frustrated" | "neutral" | "happy",
  "confidence": 0.0-1.0,
  "summary": "One sentence summary of the feedback"
}}

Category definitions:
- bug: User reports something broken or not working
- complaint: Frustration about experience (not a specific bug)
- feature_request: User wants something new or different
- question: User asking how to do something
- praise: Positive feedback, recommendation, love
- noise: Unrelated mention, spam, just tagging without substance

Be accurate. When uncertain between categories, choose the more actionable one (bug > complaint > feature_request > question > praise > noise)."""

async def classify_feedback(
    tweet_text: str,
    author_username: str,
    author_followers: int
) -> dict:
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": CLASSIFICATION_PROMPT.format(
                tweet_text=tweet_text,
                author_username=author_username,
                author_followers=author_followers
            )
        }]
    )

    # Parse JSON response
    import json
    try:
        return json.loads(response.content[0].text)
    except json.JSONDecodeError:
        # Fallback for malformed response
        return {
            "category": "noise",
            "sentiment": "neutral",
            "confidence": 0.5,
            "summary": "Could not classify"
        }
```

### Signal Detection (signal_detector.py)

```python
async def maybe_send_alert(user_id: int, item: FeedbackItem, settings: UserSettings):
    """Determine if feedback item warrants an alert."""

    reasons = []

    # Bug detected
    if settings.alert_on_bugs and item.category == 'bug':
        reasons.append('bug_detected')

    # Complaint detected
    if settings.alert_on_complaints and item.category == 'complaint':
        reasons.append('complaint_detected')

    # High-reach author
    if settings.alert_on_high_reach and item.author_followers >= 1000:
        reasons.append('high_reach')

    # High engagement
    total_engagement = item.likes + item.retweets
    if total_engagement >= settings.alert_min_engagement:
        reasons.append('high_engagement')

    if not reasons:
        return

    # Check cooldown (no spam)
    last_alert = await get_last_alert(user_id)
    if last_alert and (datetime.utcnow() - last_alert.sent_at).seconds < 300:
        return

    # Send alert
    await send_telegram_alert(user_id, item, reasons)
    await log_alert(user_id, item.id, reasons[0])
```

### Telegram Alerts (alerts.py)

```python
from telegram import Bot
from telegram.constants import ParseMode

bot = Bot(token=config.TELEGRAM_BOT_TOKEN)

CATEGORY_EMOJI = {
    'bug': '🐛',
    'complaint': '😤',
    'feature_request': '💡',
    'question': '❓',
    'praise': '🙌',
}

async def send_telegram_alert(user_id: int, item: FeedbackItem, reasons: list[str]):
    user = await get_user(user_id)
    if not user.telegram_chat_id:
        return

    emoji = CATEGORY_EMOJI.get(item.category, '📬')
    reason_text = ', '.join(reasons).replace('_', ' ').title()

    message = f"""
{emoji} *NEW FEEDBACK*

*Type:* {item.category.replace('_', ' ').title()}
*From:* @{item.author_username} ({item.author_followers:,} followers)
*Sentiment:* {item.sentiment}

"{item.tweet_text[:200]}{'...' if len(item.tweet_text) > 200 else ''}"

*Why alerted:* {reason_text}

[View in SignalBox]({config.APP_URL}/inbox?id={item.id}) | [View on X]({item.tweet_url})
"""

    await bot.send_message(
        chat_id=user.telegram_chat_id,
        text=message,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )
```

---

## X OAuth 2.0 Flow

```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name='twitter',
    client_id=config.X_CLIENT_ID,
    client_secret=config.X_CLIENT_SECRET,
    authorize_url='https://twitter.com/i/oauth2/authorize',
    access_token_url='https://api.twitter.com/2/oauth2/token',
    client_kwargs={
        'scope': 'tweet.read users.read offline.access',
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

    client = tweepy.Client(bearer_token=token['access_token'])
    user_info = client.get_me(user_fields=['username'])

    user = await upsert_user(
        x_user_id=user_info.data.id,
        x_username=user_info.data.username,
        x_access_token=encrypt(token['access_token']),
        x_refresh_token=encrypt(token['refresh_token'])
    )

    await create_default_settings(user.id, user_info.data.username)
    request.session['user_id'] = user.id

    return RedirectResponse(url='/dashboard')
```

---

## Environment Variables

```bash
# App
APP_URL=https://signalbox.app
SECRET_KEY=<random-32-chars>

# Database
DATABASE_URL=postgresql://user:pass@host:5432/signalbox

# X API
X_CLIENT_ID=<your-client-id>
X_CLIENT_SECRET=<your-client-secret>

# Telegram
TELEGRAM_BOT_TOKEN=<your-bot-token>

# Claude API
CLAUDE_API_KEY=<your-api-key>

# Stripe
STRIPE_SECRET_KEY=<your-secret-key>
STRIPE_WEBHOOK_SECRET=<your-webhook-secret>
STRIPE_PRICE_ID=<your-price-id>

# Encryption
ENCRYPTION_KEY=<random-32-chars>
```

---

## Deployment (Render)

### render.yaml

```yaml
services:
  - type: web
    name: signalbox-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: signalbox-db
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

  - type: web
    name: signalbox-dashboard
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: API_URL
        value: https://signalbox-api.onrender.com

databases:
  - name: signalbox-db
    plan: free
```

---

## Rate Limits

### X API (Pro - $100/month)

| Endpoint | Limit | Our Usage |
|----------|-------|-----------|
| Search recent | 450/15min | ~20 users × 7 polls = 140 |
| User lookup | 900/15min | Minimal |

### Claude API (Haiku)

| Metric | Cost |
|--------|------|
| Input | $0.25/1M tokens |
| Output | $1.25/1M tokens |

**Estimate**: ~500 classifications/day × 500 tokens = 250k tokens/day = ~$10/month

### Telegram

30 messages/second - plenty of headroom.

---

## Week-by-Week Build Plan

### Week 1: Foundation
- [ ] Project setup (FastAPI, Streamlit, PostgreSQL)
- [ ] Database models and migrations
- [ ] X OAuth 2.0 login
- [ ] User creation and session
- [ ] Telegram bot /start command

### Week 2: Core Value
- [ ] Mention polling service
- [ ] Claude classification integration
- [ ] Feedback item storage
- [ ] Inbox UI (Streamlit) with filters
- [ ] Telegram alerts

### Week 3: Polish
- [ ] Response templates
- [ ] Mark as handled flow
- [ ] Settings page
- [ ] Basic stats (counts by category)
- [ ] Hide/dismiss noise

### Week 4: Launch
- [ ] Stripe integration
- [ ] Landing page
- [ ] Deploy to Render
- [ ] Domain setup (signalbox.app)
- [ ] Beta invites
- [ ] Iterate on classification accuracy

---

## Default Response Templates

```python
DEFAULT_TEMPLATES = [
    {
        "name": "Bug acknowledged",
        "category": "bug",
        "text": "Thanks for flagging this! We're looking into it now."
    },
    {
        "name": "Feature noted",
        "category": "feature_request",
        "text": "Love this idea - adding it to our list. Thanks for the suggestion!"
    },
    {
        "name": "Question help",
        "category": "question",
        "text": "Happy to help! Check out [link] or DM us for more details."
    },
    {
        "name": "Praise thanks",
        "category": "praise",
        "text": "This made our day! Thanks for the kind words 🙏"
    },
    {
        "name": "Complaint response",
        "category": "complaint",
        "text": "Sorry to hear that. Can you DM us more details? We want to make this right."
    }
]
```

---

## Future Enhancements (Post-MVP)

- Slack/Discord alert channels
- Team seats and collaboration
- Trend detection (same issue mentioned 5x)
- Competitor monitoring
- Testimonial export (praise → marketing copy)
- Webhook integrations
- Mobile PWA
- Historical analytics
