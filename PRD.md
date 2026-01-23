# SignalBox

Product requirements for MVP.

## Overview

| | |
|---|---|
| Product | SignalBox |
| Tagline | Catch feedback that matters |
| Timeline | 4 weeks |
| Success | 1 actionable feedback item caught that would have been missed |

## Problem

Users post feedback on X every day. Bug reports, feature requests, complaints, praise. Most of it never reaches the team. It disappears into the timeline. Teams miss signals that could prevent churn, fix bugs faster, or shape the roadmap.

Existing tools (Hootsuite, Mention, Brand24) are built for marketing teams tracking brand sentiment. They're expensive, noisy, and don't categorize feedback in ways that help product teams act.

## Solution

SignalBox collects feedback from X through three channels, categorizes it, and surfaces what matters. Product teams get a single inbox of actionable feedback with alerts for high-signal items.

## Target User

Product teams at startups (5-50 people) building software. Founders, product managers, developer advocates, community managers.

Examples: teams building dev tools, consumer SaaS, open source projects.

What they need:
- See all feedback in one place
- Know what type it is (bug, feature request, complaint, praise)
- Get alerted when something important comes in
- Respond without switching contexts

## Data Collection

### Three Channels

| Channel | How it works | Signal strength |
|---------|--------------|-----------------|
| Passive | Monitor @product mentions and keywords | Medium |
| Bot tag | User tags @SignalBox + @product | High |
| $ signal | User includes $feedback, $bug, etc. + @product | High |

### $ Tag System

Users can self-categorize their feedback using $ tags. When a $ tag is present, we skip AI classification and use the user's label.

| Tag | Category |
|-----|----------|
| $feedback | Generic (AI classifies) |
| $bug | Bug |
| $feature | Feature request |
| $question | Question |
| $praise | Praise |
| $complaint | Complaint |

### Examples

Passive (we find it):
```
@vercel auth is broken on mobile
```

Bot tag (user flags it):
```
@SignalBox @vercel auth is broken on mobile
```

$ signal (user categorizes it):
```
$bug @vercel auth is broken on mobile
```

### Bot Account

SignalBox needs an X account (@SignalBox or similar) to:
- Receive direct @mentions
- Confirm receipt publicly ("Forwarded to @vercel")
- Build brand presence

### Bot Routing

When someone tags @SignalBox, the bot needs to know where to route feedback.

| Scenario | Action |
|----------|--------|
| @SignalBox + tracked @product | Route to that customer, confirm |
| @SignalBox + unknown @product | Ignore |
| @SignalBox alone | Ignore |
| $ tag + tracked @product | Route to that customer, confirm |
| $ tag + unknown @product | Ignore |

The bot only responds when it can route to a paying customer.

### Bot Confirmation Replies

When feedback is routed, the bot replies publicly:

```
Forwarded to @vercel. They'll see this.
```

Why:
- Closes the loop for the user (they know it worked)
- Free marketing (public proof the system works)
- Trains users that $ tags and @SignalBox tagging work

## Features

### 1. Feedback Inbox

All feedback in one view. Each item shows:
- Tweet content and author
- Category (bug, complaint, feature request, question, praise)
- Sentiment (frustrated, neutral, happy)
- Author reach (follower count)
- Engagement (likes, retweets)

Filters: category, time range, handled/unhandled.

Actions: mark handled, hide, respond.

### 2. Classification

For passive mentions and $feedback tags, Claude Haiku categorizes the tweet:
- Category: bug, complaint, feature_request, question, praise, noise
- Sentiment: frustrated, neutral, happy
- Summary: one-line description

For specific $ tags ($bug, $feature, etc.), skip AI and use the tag directly.

### 3. Alerts

Telegram notifications for high-signal items.

Triggers:
- Bug or complaint detected
- Author has 1k+ followers
- Tweet has 5+ engagements
- @SignalBox was explicitly tagged

Alert format:
```
NEW FEEDBACK

Type: Bug
From: @username (12k followers)
Sentiment: Frustrated

"Your auth is broken on mobile"

[View in SignalBox] [View on X]
```

### 4. Response Templates

Pre-written replies for common scenarios. User selects template, edits if needed, sends manually.

Default templates:
- Bug: "Thanks for flagging this. Looking into it."
- Feature: "Good idea. Added to our list."
- Question: "Happy to help. Check [link] or DM us."
- Praise: "Thanks for the kind words."
- Complaint: "Sorry about that. Can you DM us details?"

### 5. Settings

- Monitored handle and keywords
- Alert preferences (which categories trigger alerts)
- Telegram connection
- Response templates

## Out of Scope (v1)

| Feature | Reason |
|---------|--------|
| Multi-platform (Discord, Reddit) | X first, validate, then expand |
| Team seats | Single user MVP, add collaboration later |
| Historical analytics | Focus on real-time triage |
| Auto-responses to feedback | Feedback deserves human replies |

## User Flows

### Setup (5 min)

1. Land on signalbox.app
2. Click "Login with X"
3. Authorize via OAuth
4. Land on empty inbox
5. Go to settings
6. Confirm monitored @handle
7. Add extra keywords (optional)
8. Connect Telegram (optional)
9. Return to inbox, monitoring starts

### Daily Triage (2 min)

1. Open SignalBox
2. See new items since last visit
3. Filter by bugs + complaints
4. Review each: respond or mark handled
5. Check praise for testimonials
6. Done

### Alert Response

1. Receive Telegram alert
2. Tap "View in SignalBox"
3. See full context
4. Respond or escalate
5. Mark handled

### Telegram Connection

1. Go to settings, click "Connect Telegram"
2. See unique code (e.g., `LINK-ABC123`)
3. Open @SignalBoxBot on Telegram
4. Send `/start LINK-ABC123`
5. Bot confirms: "Connected! You'll receive alerts here."
6. Dashboard shows Telegram as connected

## Pricing

$29/month per product.

Includes:
- 1 monitored @handle
- 5 additional keywords
- Unlimited feedback items
- Telegram alerts

14-day free trial. No credit card required to start.

## Success Criteria

Primary: 1 actionable feedback item caught that would have been missed.

Examples:
- Bug report seen and fixed before it spread
- Feature request captured that influenced roadmap
- Frustrated user saved because team responded fast
- Testimonial captured for marketing

Secondary:
- 10-20 beta signups
- System stable for 7+ days
- Users check inbox daily

## Landing Page

Simple, single page. No features list, no testimonials (MVP).

**Content:**
- Headline: "Your users are telling you what to build"
- Subhead: "SignalBox catches feedback from X and puts it in one inbox."
- How it works: 3 icons showing passive monitoring, @SignalBox tagging, $ signals
- Pricing: "$29/month. 14-day free trial."
- CTA: "Login with X" button
- Footer: link to docs, contact

**No:**
- Feature comparison tables
- Screenshots (build them post-launch)
- Long copy

## Timeline

| Week | Focus |
|------|-------|
| 1 | Auth, polling, database, Telegram bot |
| 2 | Classification, inbox UI, alerts, bot confirmations |
| 3 | Templates, settings, mark-handled flow |
| 4 | Stripe, landing page, deploy, beta |

## Resolved Decisions

1. **Backfill**: No backfill for MVP. Monitoring starts fresh from signup. Dashboard shows "Monitoring active since [timestamp]".

2. **Noise handling**: Auto-priority with collapse.
   - High: @SignalBoxHQ tags, $specific tags, engagement >5, strong keywords
   - Medium: Passive mentions with relevant sentiment/keywords
   - Low/Noise: Neutral, low-engagement, auto-collapsed
   - Default view: High + Medium only. Toggle to show all.

3. **Rate limits**: Prefer filtered stream, fallback to polling with exponential backoff. Dashboard shows "Monitoring healthy" or "Delayed" status.

4. **Bot account**: @SignalBoxHQ
   - Bio: "Feedback helper – tag me + @yourproduct or use $feedback @yourproduct. Powered by SignalBox"
