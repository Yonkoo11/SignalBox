# SignalBox - Product Requirements Document

## Overview

**Product**: SignalBox
**Tagline**: Catch the feedback that matters
**Version**: MVP v1
**Timeline**: 4 weeks
**Success Metric**: 1 actionable feedback item caught that would've been missed

---

## Problem Statement

Your users are telling you exactly what to build, what's broken, and why they love you. You're just not hearing it.

**The feedback void:**
- User tweets about a bug. You never see it. It festers.
- Someone requests a feature. Lost in your mentions. They churn.
- A power user praises you publicly. You miss the testimonial opportunity.
- A frustrated user explains exactly why they're leaving. To no one.

**Why this happens:**
- X notifications are noisy and unreliable
- Teams don't have time to monitor mentions manually
- Existing tools (Hootsuite, Mention) are bloated, expensive, and not built for product teams
- Feedback falls through the cracks between support, product, and engineering

**The cost:**
- Bugs stay unfixed because no one knew
- Features get deprioritized because "no one asked for it" (they did)
- Churn that could've been prevented
- Praise that could've been amplified

---

## Target User

### Primary: Product Teams at Growing Startups

**Who they are:**
- Founders, product managers, developer advocates, community managers
- Teams of 5-50 at startups or scale-ups
- Building dev tools, consumer apps, SaaS products
- Users are vocal on X (tech-savvy audience)

**Examples:**
- Dev tools: Vercel, Supabase, Raycast, Cursor, Railway
- Consumer: Notion, Arc, Linear, Superhuman
- Open source: maintainers who can't monitor every mention
- Early-stage: any startup that can't afford to miss signal

**Their day:**
- Ship features, fight fires, talk to users
- Check X sporadically, miss most mentions
- Hear about issues secondhand ("Did you see that thread?")
- Reactive instead of proactive on feedback

**What they need:**
- One place to see all feedback that matters
- Categorized: bugs, feature requests, complaints, praise
- Alerts for high-signal items
- Easy way to respond or route to the right person

---

## Solution

SignalBox monitors your product's X presence, categorizes feedback by type, surfaces what matters, and helps you respond before users give up.

### Value Proposition

"Your users are already telling you what to build. SignalBox makes sure you hear them."

---

## MVP Features (v1)

### 1. Feedback Inbox (Core Feature)

**What**: Unified feed of all mentions, categorized and prioritized.

**Categories:**
| Type | Description | Priority |
|------|-------------|----------|
| Bug | User reporting something broken | High |
| Complaint | Frustration, negative experience | High |
| Feature Request | User asking for something new | Medium |
| Question | User needs help or clarification | Medium |
| Praise | Positive feedback, testimonial material | Low |
| Noise | Unrelated mentions, spam | Hidden |

**User sees:**
- Reverse-chronological feed of mentions
- Each card: tweet embed, category badge, sentiment indicator, timestamp
- Filters: by category, time window, responded/unresponded
- Quick actions: mark as handled, respond, copy for testimonial

**Why it matters**: One view to triage all feedback. No more "did anyone see that tweet?"

### 2. Signal Alerts (Telegram)

**What**: Instant notification when high-signal feedback appears.

**Triggers:**
- Bug report detected
- Complaint with high engagement (5+ likes/retweets)
- Feature request from account with 1k+ followers
- Multiple mentions of same issue in short window

**Alert content:**
```
📬 NEW FEEDBACK

Type: Bug Report
From: @username (12k followers)
Sentiment: Frustrated

"Your auth is broken on mobile - been stuck for 20 min trying to login"

[View in SignalBox] [Reply on X]
```

**Why it matters**: Catch the important stuff in real-time, even at 3am.

### 3. Smart Categorization

**What**: AI-powered classification of each mention.

**How it works:**
1. Mention comes in
2. Claude (Haiku) analyzes: Is this a bug? Feature request? Praise? Noise?
3. Sentiment scored: frustrated, neutral, happy
4. Influence check: follower count, engagement metrics
5. Stored with metadata for filtering

**Why AI, not keywords:**
- "This would be so much better if..." = feature request (no keyword match)
- "I love X but Y is killing me" = complaint + praise
- Context matters more than keywords

### 4. Quick Response

**What**: Respond to feedback directly from SignalBox.

**Options:**
- One-click reply templates ("Thanks for reporting! Looking into it.")
- Custom reply (opens composer)
- Mark as handled (internal only)
- Route to team (copy link to Slack/Discord)

**Not auto-reply for MVP**: This is feedback, not marketing. Human responses only. Templates just speed you up.

### 5. Dashboard

**What**: Web-based control center.

**Views:**
- **Inbox** (primary) - All categorized feedback
- **Settings** - Keywords, alert preferences, Telegram connection
- **Account** - Subscription, billing

**Stats (simple):**
- Feedback received this week
- Breakdown by category
- Response rate

---

## Out of Scope (v1)

| Feature | Reason | When |
|---------|--------|------|
| Multi-platform (Discord, Reddit) | X first, validate, then expand | v2 |
| Team collaboration | Solo/small team MVP, add seats later | v2 |
| Analytics/trends | Focus on real-time triage first | v2 |
| Auto-responses | Feedback deserves human touch | Maybe never |
| CRM integration | Keep it simple | v2 |

---

## User Flows

### Flow 1: First-Time Setup (5 minutes)

```
Landing Page → "Login with X" → X OAuth consent → Dashboard
                                                      ↓
                                               Inbox (empty)
                                                      ↓
                                               Settings page
                                                      ↓
                                           Add product keywords
                                              (@handle, #hashtag)
                                                      ↓
                                           Connect Telegram (optional)
                                                      ↓
                                           "Start Monitoring"
                                                      ↓
                                            Inbox populates
```

### Flow 2: Daily Triage (2 minutes)

```
Open SignalBox → See new items since last visit
                        ↓
              Filter by "Bugs + Complaints"
                        ↓
              Review top items
                        ↓
         For each: respond / mark handled / route
                        ↓
              Check "Praise" for testimonials
                        ↓
                     Done
```

### Flow 3: Real-Time Alert

```
Bug report detected → Telegram push → You see it immediately
                                              ↓
                                      Tap "View in SignalBox"
                                              ↓
                                      See full context
                                              ↓
                                      Reply: "Looking into this now!"
                                              ↓
                                      Mark as handled
```

---

## Monetization

### Pricing

**$29/month** per product (1 monitored @handle + up to 5 keywords)

**14-day free trial** - Full access, no credit card required.

### Why $29

- Affordable for early-stage startups
- Sustainable with API costs (~$100/mo X API Pro)
- 10 customers = profitable
- Room to add team seats at $19/seat later

### Who Pays

- Startup founder who doesn't want to miss feedback
- Product manager who needs signal from noise
- DevRel who tracks community sentiment
- Open source maintainer (sponsored or personal budget)

---

## Success Criteria

### MVP Success (4 weeks)

**Primary**: 1 actionable feedback item caught that would've been missed

Example wins:
- Bug report seen and fixed before it went viral
- Feature request captured that influenced roadmap
- Frustrated user saved because you responded fast
- Testimonial captured for marketing

**Secondary:**
- 10-20 beta signups
- System stable for 7+ days
- <30 second categorization latency
- Users check inbox daily (retention signal)

---

## Competitive Landscape

| Tool | Price | AI Categorization | Real-time Alerts | Built for Product Teams |
|------|-------|-------------------|------------------|------------------------|
| Hootsuite | $99+/mo | No | Limited | No (marketing focus) |
| Mention | $29+/mo | No | Yes | No (PR/brand focus) |
| Brand24 | $79+/mo | Basic | Yes | No |
| Syften | $19+/mo | No | Yes | Closer, but keyword-only |
| **SignalBox** | $29/mo | Yes (Claude) | Telegram instant | Yes |

**Our edge**: AI categorization (bug vs feature vs praise) + built specifically for product teams who care about feedback, not marketing metrics.

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| AI miscategorizes | Wrong priority, missed items | Human can recategorize; improve prompts over time |
| X API rate limits | Gaps in monitoring | Smart polling, prioritize active hours |
| Low engagement | No one checks inbox | Telegram alerts for high-signal items |
| "I can just check X" | No perceived value | Categorization is the value - X doesn't do this |

---

## Timeline

### Week 1: Foundation
- X OAuth login flow
- Basic mention polling
- PostgreSQL storage (Render)
- Telegram bot setup

### Week 2: Core Value
- Claude integration for categorization
- Feedback inbox UI (Streamlit)
- Category filters
- Telegram alerts for high-signal

### Week 3: Polish
- Quick response templates
- Settings page (keywords, alert prefs)
- Mark as handled flow
- Basic stats

### Week 4: Launch
- Stripe integration
- Landing page
- Deploy to Render
- Beta invites
- Iterate on categorization accuracy

---

## Open Questions

1. **Categorization prompt**: How to tune Claude for best accuracy?
2. **Alert threshold**: What makes something "high-signal" enough to push?
3. **Historical backfill**: On signup, pull last 7 days or start fresh?
4. **Noise handling**: Auto-hide or let user dismiss?

---

## Appendix: Categorization Prompt (Draft)

```
Analyze this tweet mentioning a product and categorize it.

Tweet: "{tweet_text}"
Author: @{username} ({followers} followers)

Respond with JSON:
{
  "category": "bug" | "complaint" | "feature_request" | "question" | "praise" | "noise",
  "sentiment": "frustrated" | "neutral" | "happy",
  "confidence": 0.0-1.0,
  "summary": "One sentence summary of the feedback"
}

Guidelines:
- "bug": User reports something broken, not working as expected
- "complaint": Frustration without specific bug (slow, confusing, annoying)
- "feature_request": User wants something that doesn't exist
- "question": User asking how to do something
- "praise": Positive feedback, recommendation, testimonial
- "noise": Unrelated mention, spam, or just tagging without substance
```

---

## Appendix: Example Feedback Items

**Bug:**
> "@linear is showing duplicate notifications for the same issue. Anyone else seeing this?"

**Complaint:**
> "I love @notion but the mobile app is painfully slow. Please fix this."

**Feature Request:**
> "Would kill for @raycast to have a clipboard history built in"

**Question:**
> "How do I connect @supabase to my Next.js app? Docs are confusing"

**Praise:**
> "Just switched to @arcinternet and holy shit this is how browsers should work"

**Noise:**
> "Working on my side project today @vercel @tailwindcss @nextjs"
