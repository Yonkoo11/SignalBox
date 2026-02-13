# SignalBox: Product Requirements Document

## Document Info
- **Version**: 2.1 (data strategy updated)
- **Date**: February 13, 2026
- **Hackathon**: Chainlink Convergence (Feb 6 - Mar 1, 2026)
- **Target Tracks**: CRE & AI (primary), Risk & Compliance, Prediction Markets, World ID, Tenderly, Top 10

---

## 1. Problem

Crypto projects are blind to user feedback outside their Discord.

Users report bugs in quote tweets. They complain in threads. They request features in replies. They praise in posts nobody on the team sees. All of this signal is scattered across X/Twitter with no collection, no classification, and no accountability.

**Current state**: Projects rely on Discord tickets and support channels. This captures maybe 10-20% of real user sentiment. The rest evaporates.

**What's lost**:
- Bug reports that never reach engineering ("bridge tx stuck for 6 hours")
- Complaints that fester into community anger ("sequencer still centralized")
- Feature requests that would inform roadmap ("when Solana support?")
- Praise that could be amplified for marketing ("CCIP is a game changer")

**Why blockchain matters**: Centralized feedback tools (Zendesk, Intercom) let projects suppress negative feedback. A project could receive 50 bug reports and pretend they don't exist. On-chain publication makes feedback permanent, transparent, and verifiable. DAOs can see real community health before governance votes. Investors can verify sentiment independently. Projects can't cherry-pick.

**Why CRE matters**: Feedback aggregation and AI classification running on a single server is a trust problem. Who controls the classification prompt? Who decides what's "negative"? Running the pipeline as a CRE workflow on Chainlink's DON means the execution is decentralized and verifiable. The data aggregation and on-chain publication happen in a trustless environment. **Caveat (acknowledged)**: The AI classification logic is still centralized -- one Claude prompt authored by us. In production, this would be mitigated by querying multiple AI providers (Claude + GPT + Gemini) and aggregating their results via DON consensus, so no single model or prompt controls the output. For the hackathon MVP, we use a single AI provider and acknowledge this limitation.

---

## 2. Solution

**SignalBox**: An on-chain social intelligence layer that aggregates crypto community feedback from social platforms, classifies every signal with AI, and publishes structured data on-chain via Chainlink CRE.

**One-line pitch**: "The accountability layer between crypto projects and their users."

**How it works**:
1. CRE workflow triggers (cron or HTTP)
2. Fetches aggregated social data from SignalBox API (hackathon: curated staging data; production: LunarCrush + X API + Reddit)
3. AI (Claude) classifies each item: bug, feature request, complaint, praise, question
4. AI scores overall sentiment and generates risk assessment
5. Structured data published on-chain: category counts, score, top issues, AI summary
6. Dashboard shows classified feedback
7. DeFi protocols, DAOs, and prediction markets consume the on-chain data

---

## 3. Target Users

### Primary: Crypto Project Teams
- **Pain**: Missing 80% of user feedback scattered across X/Twitter
- **Value**: Automated collection, AI classification, priority scoring, actionable alerts
- **Willingness to pay**: $29-99/month (SaaS model post-hackathon)

### Secondary: DeFi Protocols & DAOs
- **Pain**: No reliable way to gauge community sentiment before decisions
- **Value**: On-chain sentiment data consumable by smart contracts
- **Use case**: Governance votes weighted by community health, risk triggers based on sentiment crashes

### Tertiary: Prediction Market Platforms
- **Pain**: Need verifiable data sources for market resolution
- **Value**: On-chain sentiment scores as settlement data for sentiment-based markets
- **Use case**: "Will Chainlink sentiment stay above 70?" markets that auto-settle from oracle data

---

## 4. Product Requirements

### P0 (Must Have for Submission)

| ID | Requirement | Status |
|----|-------------|--------|
| P0-1 | CRE workflow that fetches social data, classifies with AI, writes on-chain | DONE |
| P0-2 | SentimentOracle.sol deployed on Sepolia | DONE |
| P0-3 | Successful CRE simulation (CLI) | DONE |
| P0-4 | SignalBox API serving structured sentiment data | DONE |
| P0-5 | Production dashboard showing classified feedback | DONE |
| P0-6 | 3-5 minute demo video | TODO |
| P0-7 | Public GitHub repo with README | TODO |
| P0-8 | README linking all Chainlink-related files | TODO |

### P1 (Should Have - Competitive Edge)

| ID | Requirement | Status |
|----|-------------|--------|
| P1-1 | Multi-step CRE workflow (fetch multiple sources, conditional logic, risk alerts) | TODO |
| P1-2 | Polished curated data with timestamps, staging label, and consistent numbers | TODO |
| P1-3 | Cross-chain write (Sepolia + Base Sepolia or Arbitrum Sepolia) | TODO |
| P1-4 | Tenderly Virtual TestNet deployment | TODO |
| P1-5 | Live deployed API (not localhost) — FAQ says local is fine, so this is nice-to-have | TODO |

### P2 (Nice to Have - Bonus Tracks)

| ID | Requirement | Status |
|----|-------------|--------|
| P2-1 | World ID integration (sybil-resistant human sentiment) | TODO |
| P2-2 | Prediction market contract settling from oracle data | TODO |
| P2-3 | Risk alert system (sentiment crash triggers on-chain alert) | TODO |

### P3 (Post-Hackathon)

| ID | Requirement |
|----|-------------|
| P3-1 | Real X/Twitter monitoring (multi-channel: passive, @mention, $tags) |
| P3-2 | Telegram alerts for project teams |
| P3-3 | Multi-AI consensus (Claude + GPT + Gemini, aggregated via DON) |
| P3-4 | SaaS billing (Stripe, $29/month Pro tier) |
| P3-5 | User onboarding (X OAuth, project registration) |

---

## 5. Technical Architecture

```
                    ┌──────────────────────────────────┐
                    │         DATA SOURCES              │
                    │  LunarCrush  •  X/Twitter API     │
                    │  Reddit API  •  CryptoPanic       │
                    └──────────┬───────────────────────-─┘
                               │
                               ▼
                    ┌──────────────────────────────────┐
                    │      SIGNALBOX API (FastAPI)      │
                    │  /api/v1/sentiment/{project}      │
                    │  Aggregation • Caching • Auth     │
                    │  Deployed: Render / Railway        │
                    └──────────┬───────────────────────-─┘
                               │
                               ▼
              ┌────────────────────────────────────────────┐
              │        CHAINLINK CRE WORKFLOW               │
              │  ┌────────┐  ┌────────┐  ┌────────────┐    │
              │  │ Fetch  │→ │Classify│→ │ Risk Check │    │
              │  │ Multi- │  │ (AI)   │  │ (AI + On-  │    │
              │  │ Source  │  │ Claude │  │  chain)    │    │
              │  └────────┘  └────────┘  └─────┬──────┘    │
              │                                │           │
              │                     ┌──────────┴────┐      │
              │                     │  Conditional  │      │
              │                     │  Branching    │      │
              │                     └──┬─────────┬──┘      │
              │                        │         │         │
              │              ┌─────────┘    ┌────┘         │
              │              ▼              ▼              │
              │        ┌──────────┐   ┌──────────┐        │
              │        │  Write   │   │  Alert   │        │
              │        │  Oracle  │   │  (if     │        │
              │        │  (EVM)   │   │  crash)  │        │
              │        └──────────┘   └──────────┘        │
              │              │              │              │
              │         Sepolia      Base Sepolia          │
              └────────────────────────────────────────────┘
                               │
                               ▼
              ┌────────────────────────────────────────────┐
              │         ON-CHAIN CONTRACTS                  │
              │                                            │
              │  SentimentOracle.sol (per chain)            │
              │  └─ Category counts, score, summary        │
              │  └─ Historical data                        │
              │  └─ Risk alert events                      │
              │                                            │
              │  SentimentMarket.sol (optional)             │
              │  └─ Prediction market settling from oracle │
              └────────────────────────────────────────────┘
                               │
                               ▼
              ┌────────────────────────────────────────────┐
              │            DASHBOARD                        │
              │  Classified feed • Score rings • Trends     │
              │  Pipeline viz • On-chain cards • Alerts     │
              │  Served from: static HTML (self-contained)  │
              └────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Backend API | Python, FastAPI | Already built, battle-tested |
| CRE Workflow | TypeScript (CRE SDK v1.0.9) | Hackathon requirement |
| Smart Contracts | Solidity 0.8.24 (Foundry) | Standard, well-tested |
| AI Classification | Claude Haiku 4.5 via CRE HTTP | Fast, cheap, accurate |
| Testnet | Ethereum Sepolia + Base Sepolia | Multi-chain demo |
| Dashboard | Self-contained HTML/CSS/JS | Zero dependencies, instant load |
| API Deployment | Render or Railway | Free tier, auto-deploy from git |
| Contract Testing | Tenderly Virtual TestNet | Bonus prize track |

---

## 6. CRE Workflow Specification

### Current Workflow (v1 - DONE)

```
HTTP Trigger → Fetch SignalBox API → Claude AI Score → Write SentimentOracle (Sepolia)
```

3 steps. Functional but trivial.

### Target Workflow (v2 - TO BUILD)

```
HTTP Trigger
  │
  ├── Step 1: Parallel Fetch
  │   ├── SignalBox API (aggregated Twitter data)
  │   ├── (Optional) Reddit API or secondary source
  │   └── On-chain data (token price via existing feed, if available)
  │
  ├── Step 2: AI Classification
  │   └── Claude classifies EACH feedback item individually
  │       - Category: bug | feature_request | complaint | praise | question
  │       - Priority: high | medium | low
  │       - Bot probability: 0-100 (is this a bot or human?)
  │
  ├── Step 3: AI Aggregation + Risk Assessment
  │   └── Second Claude call:
  │       - Aggregate scores across items
  │       - Generate summary
  │       - Risk flag: has sentiment dropped >15pts vs last reading?
  │       - Highlight: top 3 issues by engagement
  │
  ├── Step 4: Conditional Branch
  │   ├── IF risk_flag == true:
  │   │   └── Emit RiskAlert event on-chain (separate function)
  │   └── ALWAYS:
  │       └── Write full sentiment data to SentimentOracle
  │
  └── Step 5: Multi-chain Write
      ├── Sepolia: SentimentOracle.onReport(data)
      └── Base Sepolia: SentimentOracle.onReport(data)
```

### Workflow Files

| File | Purpose |
|------|---------|
| `workflow/main.ts` | Entry point, HTTP trigger handler |
| `workflow/httpCallback.ts` | Orchestration: fetch → classify → score → write |
| `workflow/claude.ts` | AI classification and aggregation logic |
| `workflow/workflow.yaml` | Staging + production config |
| `workflow/config.staging.json` | API URL, model, projects, chain configs |
| `secrets.yaml` | ANTHROPIC_API_KEY, deployer private key |

### CRE Capabilities Used

| Capability | How Used |
|------------|----------|
| HTTPClient | Fetch social data from SignalBox API |
| HTTPClient | Call Claude API for classification |
| EVMClient | Write sentiment reports on-chain |
| Runtime.report() | ABI-encode reports for on-chain consumption |
| Runtime.getSecret() | Securely access API keys |
| consensusIdenticalAggregation | DON consensus on HTTP responses |

---

## 7. Smart Contract Specification

### SentimentOracle.sol (EXISTS - needs minor update)

**Deployed**: `0xcA374e8bba8bd2BA0Aed26c4d425aA9aa7E058D0` (Sepolia) — v2 with RiskAlert

```solidity
struct SentimentData {
    uint8 score;          // 0-100 overall sentiment
    uint32 totalMentions; // total items classified
    uint32 positive;      // praise + feature_request count
    uint32 negative;      // bug + complaint count
    uint32 neutral;       // question count
    string summary;       // AI-generated 1-2 sentence summary
    uint256 timestamp;    // block.timestamp of update
}
```

**Functions**:
- `_processReport(bytes report)` — CRE workflow writes here
- `getSentiment(string project)` — read latest data
- `getHistory(string project, uint256 count)` — historical readings
- `getTrackedProjects()` — list all tracked projects
- `getHistoryLength(string project)` — count of historical entries

**Events**:
- `SentimentUpdated(project, score, totalMentions, summary, timestamp)`
- `ProjectAdded(project)`

**RiskAlert**: DONE. Emits `RiskAlert(project, previousScore, newScore, dropSize, timestamp)` when score drops >= 15 points. Deployed to Sepolia as v2 contract.

### SentimentMarket.sol (NEW - P2-2, optional)

Simple prediction market that settles from SentimentOracle data.

```solidity
struct Market {
    string project;           // which project
    uint8 targetScore;        // threshold (e.g., 70)
    bool directionAbove;      // true = betting score stays above target
    uint256 deadline;         // when market resolves
    uint256 yesPool;          // ETH staked on YES
    uint256 noPool;           // ETH staked on NO
    bool resolved;
    bool outcome;             // true if condition met
}
```

**Functions**:
- `createMarket(project, targetScore, directionAbove, deadline)` — create a new market
- `bet(marketId, isYes)` payable — place a bet
- `resolve(marketId)` — called by CRE workflow, reads oracle, settles
- `claim(marketId)` — winners withdraw their share

**Resolves from**: `SentimentOracle.getSentiment(project).score` at deadline.

---

## 8. API Specification

### SignalBox API (FastAPI)

Base URL: `https://signalbox-api.onrender.com` (production) or `http://localhost:8000` (dev)

#### GET /api/v1/sentiment/{project}

Returns classified feedback for a project.

```json
{
  "project": "chainlink",
  "period": "1h",
  "score": 82,
  "total_mentions": 8,
  "breakdown": {
    "praise": 4,
    "feature_request": 1,
    "question": 1,
    "bug": 1,
    "complaint": 1
  },
  "ai_summary": "Community sentiment strongly positive...",
  "key_themes": ["CCIP adoption", "CRE developer experience"],
  "items": [
    {
      "text": "CCIP is a game changer for cross-chain.",
      "category": "praise",
      "priority": "low",
      "engagement": 142,
      "author": "defi_dev",
      "followers": 8500
    }
  ]
}
```

#### GET /api/v1/sentiment

List all tracked projects with scores and trends.

#### GET /api/v1/history/{project}?days=7

Historical scores for trend charts.

#### GET /api/v1/comparison

All projects ranked by score with trends.

#### GET /api/v1/pipeline/runs

Recent CRE workflow execution history.

#### GET /api/v1/pipeline/status

Current pipeline status: last run, next run countdown, success rate.

---

## 9. Data Source Strategy

### Hackathon Phase: Curated Demo Data

The hackathon demo runs in **staging mode with curated data**. This is standard hackathon practice. The demo video states honestly: "Running in staging mode with curated data. In production, SignalBox connects to LunarCrush, X API, and Reddit for real-time monitoring."

**Current demo data** (test_server.py):
- 5 projects: Chainlink, Uniswap, Aave, Base, Arbitrum
- 6-8 realistic feed items per project with categories, priorities, engagement, authors
- AI summaries, key themes, trend data per project
- Pipeline run history with real tx hashes

**Improvements needed for convincing demo**:
- Add timestamps to feed items (currently missing — makes data feel static)
- Add "STAGING" indicator in dashboard status bar so it's honest
- Ensure internal numbers are consistent (mention counts match item arrays)

### Production Phase: Live Data Sources (Post-Hackathon)

#### Tier 1: Primary (Best bang for buck)

| Source | Cost | Data Quality | Notes |
|--------|------|-------------|-------|
| **LunarCrush API** | ~$30/month ($1/day credits) | HIGH | Already aggregates X, Reddit, YouTube, news for every crypto project. Pre-scored sentiment, social volume, top creators. Has an MCP server on GitHub. This is the cheat code — they solved the hard aggregation problem already. SignalBox adds value through AI classification (bug vs feature vs complaint), on-chain publication, and project alerting. |
| **X API Basic** | $100/month | HIGH | 10K tweet reads/month. Direct access to tweets. The gold standard when revenue justifies it. |

#### Tier 2: Free Supplements

| Source | Cost | Data Quality | Notes |
|--------|------|-------------|-------|
| **Xpoz** | Free 100K results/month | MEDIUM | Multi-platform including X data via natural language queries. Needs real-world testing to verify crypto coverage and data freshness. |
| **Reddit API** | Free (limited) | MEDIUM | r/cryptocurrency, r/chainlink, r/ethereum. Different tone than Twitter (longer discussions, more technical) but real signal. Rate limited after 2023 pricing changes. |
| **CryptoPanic API** | Free | MEDIUM | News aggregation, not social posts. Different signal type but useful context — news drives sentiment shifts. |

#### Tier 3: Not Worth Pursuing

| Source | Why Skip |
|--------|----------|
| **Neynar/Farcaster** | Farcaster is dying. Neynar acquired it Jan 2026 because it was struggling. Tiny user base, minimal crypto project discussion. Data would be embarrassingly thin. |
| **Lens Protocol** | Minimal user base, minimal project discussion. Irrelevant volume. |
| **Santiment** | Unclear free tier limits, more of an analytics platform than raw data API. |

#### Recommended Production Stack
1. **LunarCrush** ($30/month) as primary — covers 80% of social data needs across platforms
2. **Reddit API** (free) for discussion-style feedback supplement
3. **X API Basic** ($100/month) when monthly revenue exceeds $500 — direct tweet access
4. **Total**: $30-130/month for comprehensive multi-source coverage

#### Why LunarCrush is the Play
LunarCrush already tracks social metrics for every major crypto project across Twitter, Reddit, YouTube, TikTok, and news. Their API returns social volume, sentiment scores, top posts, and creator rankings. Instead of building Twitter scraping infrastructure from scratch (months of work, $100+/month API costs, rate limit management), SignalBox consumes their aggregated data and adds value through:
- **AI classification** — LunarCrush doesn't classify bug vs feature vs complaint
- **On-chain publication** — their data stays off-chain and ephemeral
- **Accountability** — their data isn't permanent or verifiable
- **Project alerting** — they don't alert project teams about specific feedback
- **Risk signals** — they don't detect sentiment crashes as DeFi risk indicators

SignalBox is a value-add layer on top of existing data infrastructure, not a data collection tool.

---

## 10. Frontend Specification

### Dashboard Architecture

Self-contained HTML file: `src/app/static/dashboard.html` (~3056 lines)

**Design System**:
- Fonts: Space Grotesk (display), DM Sans (body), JetBrains Mono (code)
- Colors: Dark theme with orange accent (#FF6B2B)
- Tokens: CSS custom properties for all values
- Radius: 2 values only (--radius: 4px, --radius-lg: 12px)
- Spacing: 4px base scale

**Pages** (hash-routed, single HTML file):
1. **Home** — hero metrics, project comparison grid, live feed, influencer leaderboard
2. **Project Detail** — score ring, trend chart, AI analysis, category bars, key themes, on-chain card
3. **Workflow** — 5-step pipeline visualization, run history table, trigger button
4. **Settings** — tracked projects, oracle config, alerts, API keys

**Interactions**:
- Cmd+K command palette (fuzzy search, keyboard navigation)
- Slide-over panel for quick project peek
- Hash routing for full project pages (#/project/chainlink)
- Responsive: 1280px / 1024px / 768px breakpoints

**Visual Effects**:
- 3 ambient gradient blobs (drift animation)
- Layered box-shadows on all cards
- Score ring with conic-gradient fill animation
- Sparkline SVGs with area fill gradients
- Skeleton loading states
- Staggered entrance animations

---

## 11. Hackathon Submission Strategy

### Track Targeting

| Track | Prize Pool | Our Angle | Strength |
|-------|-----------|-----------|----------|
| **CRE & AI** | $17K / $10.5K / $6.5K | AI-powered feedback classification pipeline | PRIMARY — core product |
| **Risk & Compliance** | $16K / $10K / $6K | Sentiment crash as DeFi risk signal | STRONG — unique angle |
| **Prediction Markets** | $16K / $10K / $6K | Sentiment-based markets with oracle settlement | MODERATE — needs market contract |
| **World ID** | $5K / $3K / $1.5K / $0.5K | Sybil-resistant human sentiment | STRONG — genuinely novel |
| **Tenderly** | $5K / $2.5K / $1.75K / $0.75K | Deploy on Virtual TestNet | EASY — just deploy there |
| **Top 10** | $1.5K | Fallback | LIKELY — working product |

**Maximum addressable**: $60.5K in first-place prizes across 6 tracks.

### Differentiation

**What 80% of teams will build**: Basic data feed (fetch API → AI → write chain). Generic CRE hello-world.

**What we build**: Multi-source feedback aggregation → individual item classification → risk assessment → conditional alerts → multi-chain publication. Plus: prediction market settlement, World ID sybil resistance.

**Why we're different**:
1. Real product solving a real problem (not a hackathon toy)
2. Dashboard that looks like a $50M fintech product (most hackathon UIs are ugly)
3. Multi-step CRE workflow with conditional logic (not fetch-score-write)
4. Unique angle: social sentiment as risk infrastructure for DeFi
5. Eligible for 6 tracks (most teams target 1-2)

### Eligibility Rules (from FAQ)

- **CRE is mandatory**: "Projects must meaningfully use the Chainlink Runtime Environment (CRE)"
- **Team size**: 1-5 participants
- **Pre-existing work**: "Projects built before the event aren't eligible unless meaningful onchain updates occur during the hackathon" -- our CRE integration, contracts, and dashboard are all post-Feb-6, so this is fine. README must make this clear.
- **Frontend NOT required**: "A frontend is not required" -- our dashboard is a bonus, not a requirement
- **Can run locally**: "You can run your application locally. You'll just need a working demo" -- deploying to Render is nice-to-have, not mandatory
- **Demo video mandatory**: "<5 minutes", must show working demo
- **Judging criteria**: Technical execution, blockchain technology application, effective CRE use, and originality
- **KYC for winners**: Standard KYC procedures required

### Submission Checklist

- [ ] CRE Workflow simulated successfully (CLI)
- [ ] Smart contracts deployed on Sepolia
- [ ] Tenderly Virtual TestNet deployment + explorer link
- [ ] 3-5 minute demo video (public URL, <5 min)
- [ ] Public GitHub repository
- [ ] README with:
  - [ ] Project description
  - [ ] Architecture diagram
  - [ ] Links to all Chainlink-related files (workflow/, contracts/)
  - [ ] Setup and run instructions
  - [ ] Tenderly explorer link
  - [ ] Demo video link
  - [ ] Clear statement that CRE/blockchain components built during hackathon
- [ ] Each team member registered individually via hackathon registration
- [ ] No code from before Feb 6 in Chainlink-specific components

---

## 12. Demo Video Script (3-5 minutes)

### Structure

**[0:00-0:30] The Problem**
"Every day, users report bugs, complain, and request features on Twitter. And project teams never see it. They only monitor Discord. 80% of real user sentiment is invisible."

**[0:30-1:30] SignalBox in Action**
- Show the dashboard with classified feedback (note: "running in staging mode with curated data")
- Click through project cards: Chainlink (82), Arbitrum (58)
- Show category breakdown: "Chainlink has 1 bug report and 1 complaint that their team hasn't addressed"
- Show AI summary and key themes

**[1:30-2:30] CRE Pipeline**
- Show the workflow page with 5-step pipeline
- Trigger a run (or show a pre-recorded run)
- Walk through: "CRE fetches social data, Claude classifies each item, scores sentiment, checks for risk conditions, then writes to Sepolia and Base"
- Show the transaction on Etherscan/Tenderly

**[2:30-3:30] On-Chain Verification**
- Show contract on Sepolia: `cast call` returns the data
- Show it on Tenderly Virtual TestNet
- "Any DeFi protocol can read this data. Any DAO can verify community health."

**[3:30-4:30] Why CRE**
- "This isn't just a data feed. CRE gives us decentralized execution — no single server controls the classification. Multi-chain publication — one workflow, multiple chains. Conditional logic — if sentiment crashes, the contract emits a risk alert."
- Show risk alert scenario
- Show prediction market (if built)

**[4:30-5:00] Vision**
- "Today: 5 projects on testnet. Tomorrow: every crypto project's accountability layer."
- "World ID integration means only verified humans contribute sentiment — no bots, no manipulation."
- "Chainlink CRE makes social intelligence trustless."

---

## 13. Build Timeline

### Week 1: Feb 13-18 (6 days)

| Day | Task | Deliverable |
|-----|------|-------------|
| Thu 13 | PRD finalization, data source decision | This document |
| Fri 14 | Upgrade CRE workflow: multi-step, conditional risk alerts | workflow/ v2 |
| Sat 15 | Polish demo data: add timestamps, staging label, consistency fixes | test_server.py v2 |
| Sun 16 | Cross-chain write (add Base Sepolia target) | config + contract deploy |
| Mon 17 | Tenderly Virtual TestNet deployment | Explorer link |
| Tue 18 | Dashboard updates: risk alerts, multi-chain status | dashboard.html v2 |

### Week 2: Feb 19-25 (7 days)

| Day | Task | Deliverable |
|-----|------|-------------|
| Wed 19 | Deploy API to Render (optional — FAQ says local is fine) OR buffer day | signalbox-api.onrender.com or catch-up |
| Thu 20 | World ID integration: CRE workflow + contract | Sybil-resistant sentiment |
| Fri 21 | World ID continued + testing | E2E with World ID proofs |
| Sat 22 | SentimentMarket.sol (if time permits) | Prediction market contract |
| Sun 23 | Full E2E test: all components working together | Green pipeline |
| Mon 24 | Polish: dashboard, error handling, edge cases | Production ready |
| Tue 25 | README, architecture docs, code cleanup | Submission-ready repo |

### Week 3: Feb 26 - Mar 1 (4 days)

| Day | Task | Deliverable |
|-----|------|-------------|
| Wed 26 | Demo script finalization | ai/demo-script.md |
| Thu 27 | Record demo video (takes + editing) | 3-5 min video |
| Fri 28 | Video polish, upload to YouTube/Loom | Public video URL |
| Sat Mar 1 | SUBMIT | Airtable form complete |

---

## 14. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Demo uses curated data, not live API | MEDIUM — judges may question credibility | HIGH (by design) | Be honest: label as "staging mode," explain production data path (LunarCrush + X API) in demo video and README. Judges respect honesty over fake "live" demos. |
| CRE SDK doesn't support conditional branching | MEDIUM — workflow stays simple | LOW | Implement branching in workflow logic, not SDK features |
| Confidential Compute not stable (early access Feb 16) | LOW — privacy track less viable | MEDIUM | Skip Privacy track, focus on other 5 tracks |
| World ID integration is complex | MEDIUM — lose $5K track | MEDIUM | Time-box to 2 days. If blocked, skip and focus on core |
| Scope creep (too many features, nothing finished) | HIGH — half-done = worse than nothing | HIGH | Hard priority stack: P0 → P1 → P2. Cut aggressively. |
| "Started before hackathon" disqualification | CRITICAL — no prizes | MEDIUM | SignalBox MVP (FastAPI, Twitter monitoring) predates Feb 6. ALL CRE/blockchain code (workflow, contracts, dashboard) is post-Feb-6. README must clearly state: "SignalBox core existed as a SaaS prototype. All Chainlink CRE integration, smart contracts, and dashboard were built during the hackathon." Git history proves this. |
| Demo video quality (bad audio, rushed) | HIGH — video is the primary judging artifact | MEDIUM | Write script first. Record multiple takes. Budget 2 full days. |
| API goes down during judging | HIGH — judges can't test | LOW | Deploy on Render with health check. Static dashboard works offline. |
| Contract redeployment breaks E2E proof | LOW — old tx still validates architecture | HIGH (if adding RiskAlert) | Deploy new contract, update all configs, run new E2E test to generate fresh tx proof. Document both old and new contracts. |
| Base Sepolia wallet unfunded | MEDIUM — cross-chain demo fails | MEDIUM | Check wallet balance on Base Sepolia before building cross-chain. Use faucet early. |
| Dashboard doesn't read on-chain data directly | LOW — demo uses API, not blockchain reads | HIGH (by design) | Acknowledge in README: "Dashboard reads from SignalBox API. On-chain data can be independently verified via Etherscan or cast call." Adding direct on-chain reads (via ethers.js) is a post-hackathon enhancement. |
| Submission form requires unknown fields | LOW — FAQ clarifies requirements | LOW | Submission via Airtable link (opens closer to deadline). Required: demo video (<5 min), GitHub repo, working demo. Frontend NOT required. Can run locally. Form fields likely: project name, description, video URL, GitHub URL, team info, track selection. |

---

## 15. Success Criteria

### Minimum Viable Submission
- [ ] Working CRE workflow with real (or curated-real) data
- [ ] Contract deployed on Sepolia
- [ ] Dashboard accessible via URL
- [ ] 3-5 minute demo video
- [ ] Public GitHub repo with README

### Competitive Submission
- [ ] Multi-step CRE workflow with conditional logic
- [ ] Cross-chain deployment (Sepolia + Base)
- [ ] Tenderly Virtual TestNet deployment
- [ ] World ID integration
- [ ] Live API (not localhost)
- [ ] Polished dashboard with real data

### Winning Submission
All of the above, plus:
- [ ] Prediction market auto-settling from oracle data
- [ ] Risk alert system with on-chain events
- [ ] Demo video that tells a story judges remember
- [ ] Clear post-hackathon roadmap showing this is a real product

---

## 16. Deployment Details

### What Gets Deployed Where

| Component | Target | URL | Notes |
|-----------|--------|-----|-------|
| **API Server** | Render (free tier) | signalbox-api.onrender.com | Deploy `test_server.py` (demo data), NOT `src/app/main.py` (real backend requires DB, Twitter API, etc.). The test server is self-contained with no dependencies beyond FastAPI. |
| **Dashboard** | Served by API server | /dashboard on the API | Static HTML served by FastAPI. Self-contained, no build step. |
| **SentimentOracle.sol** | Sepolia | 0xcA37...8D0 | v2 deployed with RiskAlert. |
| **SentimentOracle.sol** | Base Sepolia | TBD | Cross-chain deploy (P1-3). Needs Base Sepolia faucet ETH. |
| **SentimentOracle.sol** | Tenderly Virtual TestNet | TBD | For Tenderly bonus track (P1-4). |
| **CRE Workflow** | CRE CLI simulation | N/A | Simulated locally per hackathon rules. Live DON deployment is optional. |

### Config Files Needed

| File | Purpose | Status |
|------|---------|--------|
| `workflow/config.staging.json` | Local dev (localhost:8000) | EXISTS |
| `workflow/config.production.json` | Deployed API (Render URL) | NEEDED |
| `secrets.yaml` | API keys (gitignored) | EXISTS |

### Wallet Funding Checklist

- [ ] Sepolia ETH: check balance on `0x043117bb...` (deployer wallet)
- [ ] Base Sepolia ETH: fund deployer wallet via faucet
- [ ] Tenderly Virtual TestNet: no gas needed (virtual)

---

## Appendix A: Existing Codebase

### Repository Structure
```
SignalBox/
├── ai/
│   ├── PRD.md              ← this document
│   ├── plan.md             ← original hackathon plan
│   ├── progress.md         ← session state tracking
│   └── memory.md           ← product decisions log
├── contracts/
│   ├── src/
│   │   ├── SentimentOracle.sol     ← DEPLOYED (Sepolia)
│   │   └── interfaces/
│   │       ├── IReceiver.sol
│   │       └── ReceiverTemplate.sol
│   ├── test/
│   │   └── SentimentOracle.t.sol   ← 5 tests passing
│   ├── script/
│   │   └── Deploy.s.sol
│   └── foundry.toml
├── workflow/
│   ├── main.ts                     ← CRE entry point
│   ├── httpCallback.ts             ← orchestration logic
│   ├── claude.ts                   ← AI scoring
│   ├── workflow.yaml               ← CRE config
│   └── config.staging.json         ← staging params
├── src/app/
│   ├── main.py                     ← FastAPI backend
│   └── static/
│       └── dashboard.html          ← production dashboard (3056 lines)
├── proposals/
│   ├── index.html                  ← proposal catalog
│   ├── proposal-a.html
│   ├── proposal-b.html
│   └── proposal-hybrid.html
├── test_server.py                  ← demo API server
└── secrets.yaml                    ← (gitignored) API keys
```

### Deployed Contracts
- **SentimentOracle v2**: `0xcA374e8bba8bd2BA0Aed26c4d425aA9aa7E058D0` (Sepolia) — with RiskAlert
- **SentimentOracle v1** (deprecated): `0x8e39631FBfAB68Ff5739F576847Ba7795f5b3AcE` (Sepolia)
- **CRE Forwarder**: `0x15fC6ae953E024d975e77382eEeC56A9101f9F88`
- **Owner**: `0x043117bb026a4F8F4b3eC259511748208243B59a`

### Proven E2E Flow
```
HTTP Trigger → Fetch API → Claude Score (82/100) → ABI Encode → Write On-Chain
Tx: 0xdb3d2cf8213f0f33e85ac6073b17422ffc2743ae94c18287e5dda3d967d9fb1b
```
