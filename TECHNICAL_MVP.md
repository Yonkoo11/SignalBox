# SignalBox - Technical Specification

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                        SIGNALBOX                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐       │
│  │  Streamlit │───▶│  FastAPI   │───▶│ PostgreSQL │       │
│  │  Dashboard │    │  Backend   │    │            │       │
│  └────────────┘    └────────────┘    └────────────┘       │
│                          │                                 │
│                          ▼                                 │
│                   ┌────────────┐                          │
│                   │ APScheduler│                          │
│                   │  (polling) │                          │
│                   └────────────┘                          │
│                          │                                 │
│         ┌────────────────┼────────────────┐               │
│         ▼                ▼                ▼               │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐           │
│   │  X API   │    │  Claude  │    │ Telegram │           │
│   │          │    │  Haiku   │    │   Bot    │           │
│   └──────────┘    └──────────┘    └──────────┘           │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI |
| Frontend | Streamlit |
| Database | SQLite (initially), PostgreSQL later |
| X API | tweepy v4 |
| Classification | Claude Haiku |
| Alerts | python-telegram-bot |
| Payments | stripe-python |
| Scheduler | APScheduler |
| Hosting | Render |

## Project Structure

```
signalbox/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── database.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── feedback.py
│   │   ├── settings.py
│   │   └── webhooks.py
│   ├── services/
│   │   ├── twitter.py
│   │   ├── classifier.py
│   │   ├── alerts.py
│   │   └── billing.py
│   └── tasks/
│       ├── scheduler.py
│       └── collector.py
├── dashboard/
│   ├── app.py
│   └── pages/
│       ├── inbox.py
│       ├── settings.py
│       └── account.py
├── requirements.txt
├── render.yaml
└── .env.example
```

## Database Schema

### users

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    x_user_id VARCHAR(255) UNIQUE NOT NULL,
    x_username VARCHAR(255) NOT NULL,
    x_access_token TEXT NOT NULL,
    x_refresh_token TEXT NOT NULL,
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
    extra_keywords TEXT[],
    alert_on_bugs BOOLEAN DEFAULT true,
    alert_on_complaints BOOLEAN DEFAULT true,
    alert_on_high_reach BOOLEAN DEFAULT true,
    alert_min_engagement INTEGER DEFAULT 5,
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
    author_followers INTEGER,

    source VARCHAR(20) NOT NULL,          -- 'passive', 'bot_tag', 'signal_tag'
    signal_tag VARCHAR(20),               -- '$bug', '$feature', etc. if present

    category VARCHAR(50) NOT NULL,
    sentiment VARCHAR(20),
    confidence FLOAT,
    summary TEXT,

    likes INTEGER DEFAULT 0,
    retweets INTEGER DEFAULT 0,

    is_handled BOOLEAN DEFAULT false,
    is_hidden BOOLEAN DEFAULT false,

    tweet_created_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_feedback_user_category ON feedback_items(user_id, category, fetched_at DESC);
```

### response_templates

```sql
CREATE TABLE response_templates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100),
    template_text TEXT NOT NULL,
    category VARCHAR(50),
    is_active BOOLEAN DEFAULT true
);
```

## Data Collection

### Collector Logic

```python
import re

SIGNAL_TAGS = {
    '$bug': 'bug',
    '$feature': 'feature_request',
    '$question': 'question',
    '$praise': 'praise',
    '$complaint': 'complaint',
    '$feedback': None,  # Use AI classification
}

SIGNAL_PATTERN = re.compile(r'\$(?:bug|feature|question|praise|complaint|feedback)\b', re.IGNORECASE)

async def collect_mentions(user_id: int):
    user = await get_user(user_id)
    settings = await get_settings(user_id)

    # Build search query
    # Passive: @handle OR keywords
    # Bot tag: @SignalBoxHQ @handle
    # Signal tag: $tag @handle

    query_parts = [
        f"@{settings.monitored_handle}",
        "@SignalBoxHQ",
    ]
    for kw in settings.extra_keywords or []:
        query_parts.append(kw)

    query = " OR ".join(query_parts)
    query += f" -from:{settings.monitored_handle} -is:retweet"

    client = get_twitter_client(user.x_access_token)
    tweets = client.search_recent_tweets(
        query=query,
        max_results=100,
        tweet_fields=['created_at', 'public_metrics'],
        user_fields=['username', 'public_metrics'],
        expansions=['author_id'],
        start_time=datetime.utcnow() - timedelta(minutes=15)
    )

    for tweet in tweets.data or []:
        if await feedback_exists(tweet.id):
            continue

        await process_tweet(user_id, tweet, tweets.includes['users'])


async def process_tweet(user_id: int, tweet, users):
    author = get_author(users, tweet.author_id)

    # Determine source and check for signal tags
    source = 'passive'
    signal_tag = None
    category = None

    text_lower = tweet.text.lower()

    # Check for @SignalBoxHQ tag
    if '@signalbox' in text_lower:
        source = 'bot_tag'

    # Check for $ signal tags
    match = SIGNAL_PATTERN.search(tweet.text)
    if match:
        signal_tag = match.group(0).lower()
        source = 'signal_tag'
        category = SIGNAL_TAGS.get(signal_tag)

    # Classify with AI if no category from signal tag
    if category is None:
        result = await classify_feedback(tweet.text, author.username, author.public_metrics['followers_count'])
        category = result['category']
        sentiment = result['sentiment']
        confidence = result['confidence']
        summary = result['summary']
    else:
        # Signal tag provided category, still get sentiment
        result = await classify_feedback(tweet.text, author.username, author.public_metrics['followers_count'], category_override=category)
        sentiment = result['sentiment']
        confidence = 1.0
        summary = result['summary']

    # Skip noise unless low confidence
    if category == 'noise' and confidence > 0.8:
        return

    item = await save_feedback_item(
        user_id=user_id,
        tweet_id=tweet.id,
        tweet_text=tweet.text,
        tweet_url=f"https://x.com/{author.username}/status/{tweet.id}",
        author_username=author.username,
        author_followers=author.public_metrics['followers_count'],
        source=source,
        signal_tag=signal_tag,
        category=category,
        sentiment=sentiment,
        confidence=confidence,
        summary=summary,
        likes=tweet.public_metrics['like_count'],
        retweets=tweet.public_metrics['retweet_count'],
        tweet_created_at=tweet.created_at
    )

    await maybe_send_alert(user_id, item)

    # Send bot confirmation if tagged directly
    if item.source in ('bot_tag', 'signal_tag'):
        await send_bot_confirmation(item, settings.monitored_handle)


async def send_bot_confirmation(item, product_handle: str):
    """Reply publicly confirming feedback was forwarded."""
    bot_client = get_bot_twitter_client()  # Uses @SignalBoxHQ credentials

    reply_text = f"Forwarded to @{product_handle}. They'll see this."

    try:
        bot_client.create_tweet(
            text=reply_text,
            in_reply_to_tweet_id=item.tweet_id
        )
    except Exception as e:
        # Log but don't fail - confirmation is nice-to-have
        logger.warning(f"Failed to send bot confirmation: {e}")
```

## Bot Routing

The collector runs a central query for @SignalBoxHQ mentions across all tracked products.

```python
async def collect_bot_mentions():
    """Collect all @SignalBoxHQ mentions and route to correct customers."""
    bot_client = get_bot_twitter_client()

    tweets = bot_client.search_recent_tweets(
        query="@SignalBoxHQ -is:retweet",
        max_results=100,
        tweet_fields=['created_at', 'public_metrics'],
        user_fields=['username', 'public_metrics'],
        expansions=['author_id'],
        start_time=datetime.utcnow() - timedelta(minutes=15)
    )

    # Get all tracked handles
    tracked_handles = await get_all_tracked_handles()  # Returns {handle: user_id}

    for tweet in tweets.data or []:
        if await feedback_exists(tweet.id):
            continue

        # Find which tracked product is mentioned
        text_lower = tweet.text.lower()
        routed_to = None

        for handle, user_id in tracked_handles.items():
            if f"@{handle.lower()}" in text_lower:
                routed_to = (handle, user_id)
                break

        if not routed_to:
            # No tracked product mentioned, ignore
            continue

        handle, user_id = routed_to
        await process_tweet(user_id, tweet, tweets.includes['users'])
```

## Classification

### Prompt

```python
CLASSIFY_PROMPT = """Categorize this tweet about a product.

Tweet: "{text}"
Author: @{username} ({followers} followers)

Return JSON only:
{{
  "category": "bug|complaint|feature_request|question|praise|noise",
  "sentiment": "frustrated|neutral|happy",
  "confidence": 0.0-1.0,
  "summary": "One sentence description"
}}

Categories:
- bug: Something is broken or not working
- complaint: Frustration about experience (not a specific bug)
- feature_request: Wants something new
- question: Asking how to do something
- praise: Positive feedback
- noise: Unrelated, spam, just tagging"""


CLASSIFY_WITH_OVERRIDE_PROMPT = """Analyze sentiment for this tweet. Category is already known: {category}

Tweet: "{text}"

Return JSON only:
{{
  "sentiment": "frustrated|neutral|happy",
  "summary": "One sentence description"
}}"""
```

### Implementation

```python
import anthropic
import json

client = anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)

async def classify_feedback(text: str, username: str, followers: int, category_override: str = None) -> dict:
    if category_override:
        prompt = CLASSIFY_WITH_OVERRIDE_PROMPT.format(
            category=category_override,
            text=text
        )
    else:
        prompt = CLASSIFY_PROMPT.format(
            text=text,
            username=username,
            followers=followers
        )

    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        result = json.loads(response.content[0].text)
        if category_override:
            result['category'] = category_override
            result['confidence'] = 1.0
        return result
    except json.JSONDecodeError:
        return {
            "category": category_override or "noise",
            "sentiment": "neutral",
            "confidence": 0.5,
            "summary": "Could not classify"
        }
```

## Alerts

```python
from telegram import Bot

bot = Bot(token=config.TELEGRAM_BOT_TOKEN)

CATEGORY_LABEL = {
    'bug': 'Bug',
    'complaint': 'Complaint',
    'feature_request': 'Feature Request',
    'question': 'Question',
    'praise': 'Praise',
}

async def maybe_send_alert(user_id: int, item):
    settings = await get_settings(user_id)
    user = await get_user(user_id)

    if not user.telegram_chat_id:
        return

    should_alert = False

    if settings.alert_on_bugs and item.category == 'bug':
        should_alert = True
    if settings.alert_on_complaints and item.category == 'complaint':
        should_alert = True
    if settings.alert_on_high_reach and item.author_followers >= 1000:
        should_alert = True
    if item.source in ('bot_tag', 'signal_tag'):
        should_alert = True
    if (item.likes + item.retweets) >= settings.alert_min_engagement:
        should_alert = True

    if not should_alert:
        return

    # Cooldown check
    last = await get_last_alert(user_id)
    if last and (datetime.utcnow() - last.sent_at).seconds < 300:
        return

    await send_alert(user, item)
    await log_alert(user_id, item.id)


async def send_alert(user, item):
    label = CATEGORY_LABEL.get(item.category, item.category)

    message = f"""NEW FEEDBACK

Type: {label}
From: @{item.author_username} ({item.author_followers:,} followers)
Sentiment: {item.sentiment.title()}

"{item.tweet_text[:200]}"

View: {config.APP_URL}/inbox?id={item.id}
X: {item.tweet_url}"""

    await bot.send_message(
        chat_id=user.telegram_chat_id,
        text=message,
        disable_web_page_preview=True
    )
```

## Telegram Connection

### Flow

1. User clicks "Connect Telegram" in dashboard
2. Backend generates unique link code, stores with user_id and expiry (15 min)
3. Dashboard shows: "Send `/start LINK-ABC123` to @SignalBoxHQBot on Telegram"
4. User sends message to bot
5. Bot validates code, extracts user_id, stores chat_id
6. Bot replies: "Connected! You'll receive alerts here."
7. Dashboard polls or uses websocket to show connected state

### Database

```sql
CREATE TABLE telegram_link_codes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    code VARCHAR(50) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT false
);
```

### Bot Handler

```python
from telegram import Update
from telegram.ext import CommandHandler, Application

async def start_command(update: Update, context):
    args = context.args
    chat_id = update.effective_chat.id

    if not args:
        await update.message.reply_text(
            "To connect your SignalBox account, use the link code from your dashboard.\n"
            "Example: /start LINK-ABC123"
        )
        return

    code = args[0]

    # Validate code
    link = await get_valid_link_code(code)
    if not link:
        await update.message.reply_text("Invalid or expired code. Get a new one from your dashboard.")
        return

    # Link account
    await update_user_telegram(link.user_id, chat_id)
    await mark_code_used(code)

    await update.message.reply_text("Connected! You'll receive feedback alerts here.")
```

## API Endpoints

### Auth

```
GET  /auth/login      Redirect to X OAuth
GET  /auth/callback   Handle callback, create session
POST /auth/logout     Clear session
GET  /auth/me         Current user
```

### Feedback

```
GET  /api/feedback              List items (paginated, filtered)
GET  /api/feedback/{id}         Single item
POST /api/feedback/{id}/handle  Mark handled
POST /api/feedback/{id}/hide    Hide from inbox
GET  /api/feedback/stats        Counts by category
```

### Settings

```
GET  /api/settings              Get settings
PUT  /api/settings              Update settings
POST /api/settings/telegram     Start Telegram connection
GET  /api/templates             Get templates
PUT  /api/templates             Update templates
```

### Billing

```
POST /api/billing/checkout      Create Stripe session
POST /api/billing/portal        Billing portal
POST /webhooks/stripe           Stripe events
```

## X OAuth Flow

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
    return await oauth.twitter.authorize_redirect(
        request,
        f"{config.APP_URL}/auth/callback"
    )

@router.get('/auth/callback')
async def callback(request: Request):
    token = await oauth.twitter.authorize_access_token(request)

    client = tweepy.Client(bearer_token=token['access_token'])
    me = client.get_me(user_fields=['username'])

    user = await upsert_user(
        x_user_id=me.data.id,
        x_username=me.data.username,
        x_access_token=encrypt(token['access_token']),
        x_refresh_token=encrypt(token['refresh_token'])
    )

    await create_default_settings(user.id, me.data.username)
    request.session['user_id'] = user.id

    return RedirectResponse(url='/dashboard')
```

## Token Refresh

X OAuth tokens expire after 2 hours. Refresh tokens are valid for 6 months.

```python
async def refresh_user_token(user_id: int):
    """Refresh X OAuth token before it expires."""
    user = await get_user(user_id)

    response = requests.post(
        'https://api.twitter.com/2/oauth2/token',
        data={
            'grant_type': 'refresh_token',
            'refresh_token': decrypt(user.x_refresh_token),
            'client_id': config.X_CLIENT_ID,
        },
        auth=(config.X_CLIENT_ID, config.X_CLIENT_SECRET)
    )

    if response.status_code != 200:
        logger.error(f"Token refresh failed for user {user_id}: {response.text}")
        # Mark user as needing re-auth
        await mark_user_needs_reauth(user_id)
        return False

    data = response.json()
    await update_user_tokens(
        user_id,
        encrypt(data['access_token']),
        encrypt(data['refresh_token'])
    )
    return True


# Run token refresh every hour for all active users
@scheduler.scheduled_job('interval', hours=1)
async def refresh_all_tokens():
    users = await get_active_users()
    for user in users:
        await refresh_user_token(user.id)
```

## Error Handling

### X API Failures

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def search_tweets_with_retry(client, query, **kwargs):
    return client.search_recent_tweets(query=query, **kwargs)
```

### Claude API Failures

```python
async def classify_feedback_safe(text: str, username: str, followers: int, category_override: str = None) -> dict:
    try:
        return await classify_feedback(text, username, followers, category_override)
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        # Return safe default - don't lose the feedback
        return {
            "category": category_override or "noise",
            "sentiment": "neutral",
            "confidence": 0.0,
            "summary": "Classification failed"
        }
```

### Telegram Failures

```python
async def send_alert_safe(user, item):
    try:
        await send_alert(user, item)
    except Exception as e:
        logger.error(f"Telegram alert failed for user {user.id}: {e}")
        # Don't retry immediately - will catch on next alert
```

### Principles

1. Never lose feedback items due to transient errors
2. Retry external API calls with exponential backoff
3. Log all failures for debugging
4. Degrade gracefully (skip classification, skip alerts, but save the item)

## Environment Variables

```bash
APP_URL=https://signalbox.app
SECRET_KEY=

DATABASE_URL=postgresql://...

X_CLIENT_ID=
X_CLIENT_SECRET=

TELEGRAM_BOT_TOKEN=

CLAUDE_API_KEY=

STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_ID=

ENCRYPTION_KEY=
```

## Deployment

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

  - type: web
    name: signalbox-dashboard
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0

databases:
  - name: signalbox-db
    plan: free
```

## Rate Limits

| Service | Limit | Usage |
|---------|-------|-------|
| X API Pro | 450 req/15min | ~20 users x 7 polls = 140 |
| Claude Haiku | $0.25/1M input | ~$10/month at 500/day |
| Telegram | 30 msg/sec | No concern |

## Build Plan

### Week 1
- [ ] FastAPI project setup
- [ ] PostgreSQL models, migrations
- [ ] X OAuth login/callback
- [ ] Token refresh service
- [ ] User creation, session
- [ ] Telegram bot /start and link flow

### Week 2
- [ ] Collector service (passive + bot tag + signal tag)
- [ ] Bot routing logic
- [ ] Bot confirmation replies
- [ ] Signal tag parsing
- [ ] Claude classification
- [ ] Feedback storage
- [ ] Inbox UI (Streamlit)
- [ ] Telegram alerts

### Week 3
- [ ] Response templates CRUD
- [ ] Mark handled flow
- [ ] Settings page
- [ ] Hide/dismiss
- [ ] Basic stats
- [ ] Error handling and retries

### Week 4
- [ ] Stripe checkout, webhooks
- [ ] Trial logic
- [ ] Landing page
- [ ] Deploy to Render
- [ ] Domain setup
- [ ] Beta invites

## Default Templates

```python
DEFAULT_TEMPLATES = [
    {"name": "Bug ack", "category": "bug", "text": "Thanks for flagging. Looking into it."},
    {"name": "Feature noted", "category": "feature_request", "text": "Good idea. Added to our list."},
    {"name": "Help", "category": "question", "text": "Happy to help. Check [link] or DM us."},
    {"name": "Thanks", "category": "praise", "text": "Thanks for the kind words."},
    {"name": "Apology", "category": "complaint", "text": "Sorry about that. Can you DM us details?"},
]
```
