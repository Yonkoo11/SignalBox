# FUDShield - Product Requirements Document

## Overview

**Product**: FUDShield
**Tagline**: Real-time FUD defense for crypto projects
**Version**: MVP v1
**Timeline**: 4 weeks
**Success Metric**: 1 crisis caught and acted upon

---

## Problem Statement

Crypto projects operate in a 24/7, high-stakes environment where a single viral FUD thread can:
- Tank token prices within hours
- Trigger mass wallet drains
- Destroy community trust built over months
- Spread scam accusations that stick forever

Current solutions (Hootsuite, Mention, Brand24) fail crypto teams because:
- No crypto-specific sentiment tuning ("rug pull" reads as neutral)
- Expensive for bootstrapped projects ($99+/month)
- Cluttered UIs designed for enterprise marketing, not crisis defense
- Slow - not built for the speed crypto demands

**The gap**: No affordable, X-native tool that wakes you at 3am when FUD hits.

---

## Target User

### Primary: Crypto Project Leads

**Who they are**:
- Founders, community managers, growth leads for DeFi protocols, NFT collections, token launches
- 1-5 person teams, often bootstrapped or early-stage funded
- Live on X and Telegram 24/7
- Technical enough to use APIs but too busy to build monitoring tools

**Their day**:
- Wake up, check X for overnight drama
- Scan mentions manually (miss things constantly)
- React to FUD after it's already viral
- Spend hours in damage control instead of building

**What they need**:
- Instant alerts when negativity spikes
- Quick way to see all threats in one view
- Auto-engagement on positive mentions to build momentum
- Peace of mind to actually sleep

### Pain Point Ranking

1. **FUD/crisis blindsiding** - The killer. Unchecked negativity spirals before teams notice.
2. **Missing mentions** - X algorithm buries conversations; opportunities and threats slip by.
3. **Slow response time** - Manual monitoring means 6-12 hour delays.
4. **No actionable data** - Flying blind on sentiment trends.

---

## Solution

FUDShield monitors your project's X presence in real-time, detects FUD spikes, alerts you instantly via Telegram, and helps you respond fast.

### Value Proposition

"Set it and forget it FUD defense. Sleep knowing you'll wake up if something's wrong."

---

## MVP Features (v1)

### 1. Threat Feed (Core Feature)

**What**: Live stream of negative/risky mentions with sentiment scores.

**User sees**:
- Reverse-chronological list of concerning posts
- Each card shows: tweet embed, sentiment score (-100 to 0), risk badge (red/orange/yellow), timestamp
- Keywords highlighted ("scam", "rug", "exit liquidity")
- Filter by: time window (1h/6h/24h), severity threshold, keyword

**Why it matters**: The first thing a project lead opens every morning. "What's on fire?"

### 2. FUD Spike Alerts (Telegram)

**What**: Instant push notification when negativity crosses thresholds.

**Triggers**:
- >10 negative mentions in 15 minutes
- Average sentiment drops below -60
- Specific high-risk keywords appear 3+ times ("scam", "rug pull", "exit scam")

**Alert content**:
```
🚨 FUD SPIKE DETECTED

Time: 3:12 AM
Severity: HIGH
Mentions: 22 (↑300% vs baseline)
Sentiment: -78
Top keywords: scam, rug, fake team

[View Threat Feed] [Top Thread]
```

**Why it matters**: The 3am wake-up call that saves the project.

### 3. Positive Auto-Replies (Hybrid)

**What**: Automated responses to positive mentions using customizable templates + AI variation.

**How it works**:
1. We provide 5-7 starter templates (crypto-tuned)
2. User customizes tone/links
3. AI adds variation to avoid bot detection
4. Auto-reply to positive mentions only (medium risk setting)
5. Throttled: max 1 reply per 5 minutes

**Starter templates**:
- "Thanks for the support! We're just getting started. [link]"
- "Appreciate the shoutout! Join our Telegram for alpha: [link]"
- "LFG! More announcements coming soon. Stay tuned."
- "This is the energy we love. Welcome to the community!"

**Why it matters**: Amplifies positive momentum without manual effort.

### 4. Dashboard

**What**: Web-based control center.

**Views**:
- **Threat Feed** (primary) - Live negative mentions
- **Settings** - Keywords, thresholds, templates, Telegram connection
- **Account** - Subscription status, billing

**Not in v1**: Historical charts, analytics, multi-account switching.

### 5. X OAuth Login

**What**: One-click "Login with X" using OAuth 2.0 + PKCE.

**Flow**:
1. User clicks "Login with X"
2. Redirects to X authorization
3. Returns with tokens, auto-sets monitored account to their @handle
4. Lands on Threat Feed

**Why OAuth only**: Crypto users expect one-click. No email signup friction.

---

## Out of Scope (v1)

| Feature | Reason | When |
|---------|--------|------|
| X Ads integration | Different API, compliance overhead | v2 |
| Historical analytics | Requires expensive archive access | v2 |
| Discord/Slack alerts | Telegram covers 90% of crypto users | v2 |
| Full multi-account | Quota management complexity | v2 |
| Mobile app | Web-first, Telegram handles push | v3+ |

---

## User Flows

### Flow 1: First-Time Setup (5 minutes)

```
Landing Page → "Login with X" → X OAuth consent → Dashboard
                                                      ↓
                                               Settings page
                                                      ↓
                                           "Connect Telegram"
                                                      ↓
                                            Add keywords/hashtags
                                                      ↓
                                            Review auto-reply templates
                                                      ↓
                                              "Start Monitoring"
                                                      ↓
                                              Threat Feed (live)
```

### Flow 2: 3am FUD Alert

```
FUD spike detected → Telegram push sent → User wakes up
                                              ↓
                                        Opens alert link
                                              ↓
                                        Threat Feed (filtered to spike)
                                              ↓
                                        Reviews top threads
                                              ↓
                                        Drafts response / escalates to team
```

### Flow 3: Positive Mention Auto-Reply

```
Positive mention detected → Sentiment scored (+65) → Passes threshold
                                                          ↓
                                                  Select random template
                                                          ↓
                                                  AI generates variation
                                                          ↓
                                                  Check throttle (ok)
                                                          ↓
                                                  Post reply via X API
```

---

## Monetization

### Pricing

**$29/month** per monitored project (1 primary @handle + up to 3 extra keywords/hashtags)

**14-day free trial** - Full access, no credit card required to start.

### Why $29

- X API Pro costs ~$100/month base
- At 10 users: $290 revenue vs $100 cost = $190 margin
- Sweet spot: affordable for bootstrapped projects, sustainable for us
- Competitors charge $99+ for less crypto-specific value

### Payment

- Stripe Checkout for subscriptions
- Monthly billing (annual discount later)
- Grace period: 3 days after failed payment before feature lockout

---

## Success Criteria

### MVP Success (4 weeks)

**Primary**: 1 crisis caught and acted upon
- A real user receives a FUD spike alert
- They see the threat feed, understand the situation
- They take action (reply, escalate, post clarification)
- Crisis is mitigated or at least they knew before it went viral

**Secondary**:
- 10-20 beta signups from @soligxbt network
- System runs stable for 7+ days without manual intervention
- <5 second alert latency (spike to Telegram notification)

### Why "Crisis Caught" Over Revenue

Revenue validates price. But for a defense product, the proof is in the save. One testimonial of "FUDShield woke me up and saved our launch" is worth more than 50 signups who never faced a crisis.

---

## Competitive Landscape

| Tool | Price | Crypto Focus | Real-time Alerts | Auto-Reply |
|------|-------|--------------|------------------|------------|
| Hootsuite | $99+/mo | No | Limited | No |
| Mention | $29+/mo | No | Yes | No |
| Brand24 | $79+/mo | No | Yes | No |
| LunarCrush | Free-$99 | Yes | Basic | No |
| **FUDShield** | $29/mo | Yes | Telegram instant | Yes (hybrid) |

**Our edge**: Crypto-native sentiment + instant Telegram alerts + auto-engagement. Built by crypto people for crypto people.

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| X API rate limits | Monitoring gaps | Smart polling intervals, prioritize active hours |
| X bans auto-reply accounts | Feature breaks | Throttling, variation, human-approved templates |
| False positive FUD alerts | Alert fatigue | Tunable thresholds, crypto-specific sentiment model |
| Low trial conversion | Revenue miss | Focus on value demo during trial, onboarding flow |
| Competitor copies | Market share | Speed to market, community building, iterate fast |

---

## Timeline

### Week 1: Foundation
- X OAuth login flow
- Basic polling for mentions
- SQLite storage for users/tokens
- Telegram bot setup

### Week 2: Core Value
- Sentiment analysis integration
- Threat feed UI (Streamlit)
- FUD spike detection logic
- Telegram alert sending

### Week 3: Engagement
- Auto-reply system (templates + AI variation)
- Settings page (keywords, thresholds)
- Throttling and safety checks

### Week 4: Launch
- Stripe integration
- Landing page
- Deploy to Render
- Beta invites to crypto network
- Monitor and iterate

---

## Open Questions

1. **Sentiment model**: Use off-the-shelf (VADER/TextBlob) or fine-tune for crypto slang?
2. **Keyword defaults**: What starting keywords should we pre-populate? (scam, rug, exit, FUD, fake?)
3. **Alert frequency cap**: How many alerts per hour before it becomes spam?
4. **Trial-to-paid flow**: Require credit card at signup or after trial?

---

## Appendix: Crypto Sentiment Keywords

### High-Risk (Red)
scam, rug pull, exit liquidity, fake team, honeypot, ponzi, fraud, stolen, hack, exploit, drained

### Medium-Risk (Orange)
FUD, dump, sell, bearish, concern, warning, careful, sketchy, sus, shady

### Positive (for auto-reply triggers)
moon, bullish, LFG, gem, alpha, based, chad, wagmi, diamond hands, holding
