# SignalBox Progress

## Current Focus: Production UI Redesign (Proposal 3 selected)

## What's Done

### CRE Dev Environment
- CRE CLI v1.0.10 installed at `~/.local/bin/cre`
- Bun v1.3.9 at `~/.bun/bin/bun`
- Node v20.19.5 (was already installed)
- Foundry v1.4.4 (was already installed)
- **NOTE:** bun/cre not in default PATH for shell scripts, use full paths
- Python venv at `.venv/` with FastAPI, uvicorn, etc. (greenlet incompatible with Python 3.14)

### Smart Contract: SentimentOracle
- `contracts/src/SentimentOracle.sol` - extends CRE ReceiverTemplate
- Accepts CRE reports via `onReport` -> `_processReport`
- Stores: score (0-100), totalMentions, positive, negative, neutral, summary
- Tracks projects, maintains history
- `contracts/test/SentimentOracle.t.sol` - 8 tests, all passing (includes RiskAlert tests)
- `contracts/script/Deploy.s.sol` - deploy script ready
- OpenZeppelin v5.5.0 installed
- CRE interfaces (IReceiver, ReceiverTemplate) copied from bootcamp
- **v2 DEPLOYED to Sepolia**: `0xcA374e8bba8bd2BA0Aed26c4d425aA9aa7E058D0` (with RiskAlert event)
- v1 (deprecated): `0x8e39631FBfAB68Ff5739F576847Ba7795f5b3AcE`
- Owner: `0x043117bb026a4F8F4b3eC259511748208243B59a`
- Forwarder: `0x15fC6ae953E024d975e77382eEeC56A9101f9F88`
- RiskAlert: emits when score drops >= 15 points between updates

### CRE Workflow (TypeScript)
- `workflow/main.ts` - entry point, HTTP trigger
- `workflow/httpCallback.ts` - fetches SignalBox API, scores with Claude, writes on-chain
- `workflow/claude.ts` - Claude AI sentiment scoring via CRE HTTP capability
- `workflow/workflow.yaml` - staging/production config
- `workflow/config.staging.json` - updated with deployed contract address
- CRE SDK v1.0.9 installed, Javy runtime ready

### E2E Test: PASSED
- Full pipeline: HTTP trigger -> fetch API -> Claude AI score (82/100) -> ABI encode -> write on-chain
- On-chain data confirmed: `cast call` returns score=82, summary, tracked projects
- Tx: `0xdb3d2cf8213f0f33e85ac6073b17422ffc2743ae94c18287e5dda3d967d9fb1b`

### Test Server (EXPANDED)
- `test_server.py` - FastAPI with full demo API suite
- Endpoints: sentiment, history, comparison, pipeline runs/status
- Rich demo data for all 5 projects with unique feed items
- AI summaries, key themes, trend data per project
- CORS enabled for local dev

### Frontend Redesign: DONE
- **Selected**: Proposal 3 (DNA-G-H-S-N-S, Mission Control, orange accent)
- **Built**: Production multi-page dashboard at `src/app/static/dashboard.html`
- **Pages**: Dashboard (report-first with sidebar), Project Detail (research report), Workflow (Vercel-style pipeline), Settings
- **Features**: Cmd+K palette (fuzzy search, keyboard nav), floating nav pill, responsive breakpoints (1280/1024/768), accessible (skip-link, aria-labels, keyboard nav, prefers-reduced-motion)
- **Dashboard**: Hero metrics bar, featured project card (score ring with color thresholds, stacked category bar, AI summary), project sidebar (sort by score/trend/alpha), live signal feed with category filters
- **Detail**: Score ring + trend chart (7d/30d), AI analysis card with metadata, category breakdown bars, key themes list, on-chain oracle card, signal feed
- **Workflow**: 5-step pipeline visualization (Collect/Classify/Score/Aggregate/Publish) with animated connectors, run history table with status pills and tx links, trigger button
- **Settings**: Project tags with scores, oracle config (contract/network/frequency/gas), alert toggles, API key management
- **Bugs fixed**: Duplicate HTML id, grid overflow pushing sidebar off-screen (minmax(0,1fr)), sidebar active state not updating on project select
- **Animations**: Score ring fill (conic-gradient), count-up numbers, staggered hero stats/feed/sidebar/pipeline, sparkline draw-in, status bar fresh glow, LIVE pulse, loading skeletons, page transitions
- **Production Polish Pass (30-issue audit)**:
  - Replaced 8 `transition:all` with specific properties (transform, opacity, color, background, border-color)
  - Bumped body text from 13px to 14px across all pages
  - Replaced `#fff` with `--text-on-accent` CSS token
  - Lightened `--text-3` from `#55555F` to `#6B6B76` for WCAG contrast
  - Added `--text-on-accent` and `--radius-lg` design tokens
  - Increased card padding from 20px to 28px for breathing room
  - Consolidated border-radius to 2 token values (`--radius:4px`, `--radius-lg:12px`)
  - Created CSS utility classes for score colors (`.score-green/.score-orange/.score-red`, `.bg-score-*`, `.trend-up/.trend-down/.trend-flat`) replacing inline styles
  - Added heading line-heights (1.15-1.2) for display fonts
  - Made grid background subtler with radial mask fade
  - Increased section gaps to 24px

### Dashboard Redesign: Hybrid Selected + Polished
- Built 3 redesign proposals: A (slide-over), B (hash routing), Hybrid (best of both)
- All at `proposals/proposal-{a,b,hybrid}.html`, catalog at `proposals/index.html`
- **Hybrid selected** (2871 lines): slide-over quick-peek + hash-routed full pages + influencer leaderboard
- Test server updated: `/redesign` route serves catalog, `/proposals/` serves static files
- Fixed API data type bugs in all proposals: success_rate (decimal not %), duration (string not number)
- Committed and pushed: `438555b`
- **Production Polish Pass on Hybrid**:
  - Added 3 ambient gradient blobs (orange, green, purple) with staggered drift animations (25s/30s/22s)
  - Added radial ambient wash gradient behind hero area
  - Hero card: gradient background, wider accent line (500px, full opacity), radial orange glow ::after, stronger layered box-shadow with accent tint
  - Hero score number: text-shadow glow using currentColor
  - All cards (project, pipeline stats, oracle, AI analysis, deep dive, settings): layered box-shadows (2-layer: 4px + 16px depth)
  - Project cards: hover glow with accent-colored shadow, wrapped in @media(hover:hover)
  - #1 ranked project card: orange top accent border
  - Sparkline SVG: area fill gradient under line (linear gradient from color at 15% opacity to transparent)
  - Score ring on project page: color-matched drop-shadow glow (green/orange/red classes)
  - Pipeline circles: glow shadows for completed (green) and active (orange) states
  - Slide-over panel: deep left-edge shadow (-8px + -24px), "Full Report" button upgraded to filled accent with glow
  - Command palette: 4-layer box-shadow with accent tint
  - Status bar: increased blur (20px), added saturate(1.2), subtle box-shadow
  - Theme tags: hover adds background change + shadow
  - Feed items: hover adds background elevation
  - Influencer cards: hover adds shadow, #1 rank gets accent color
  - Footer: minimal centered row (SignalBox + Oracle + Chainlink CRE)
  - All hover states wrapped in @media(hover:hover) for mobile safety
  - Button press feedback: scale(0.97) on :active

## What's Next (PRD v2.1 priorities)

### P0 DONE
- ~~CRE workflow v1~~ | ~~Contract deployed~~ | ~~E2E test~~ | ~~Dashboard~~ | ~~Polish~~

### P1 STATUS (3/5 done, 2 not started)
1. **SentimentOracle.sol v2** - DEPLOYED + ALL 5 PROJECTS ON-CHAIN. RiskAlert event, RISK_THRESHOLD=15, 8 unit tests passing. Contract: `0xcA374e8bba8bd2BA0Aed26c4d425aA9aa7E058D0`. Chainlink has 2 history entries. **NOT tested**: RiskAlert trigger on-chain (would need a score drop of 15+ between runs), error recovery paths.
2. **CRE workflow v2** - ALL 5 PROJECTS TESTED + ON-CHAIN. Results:
   - chainlink: 82/100 (praise:4, feature_request:1, complaint:1, question:1, bug:1)
   - uniswap: 68/100 (praise:2, complaint:1, feature_request:1, bug:1, question:1)
   - aave: 82/100 (praise:4, complaint:1, feature_request:1)
   - base: 72/100 (praise:4, complaint:1, bug:1)
   - arbitrum: 62/100 (praise:3, complaint:2, question:1)
   **Known limitation**: CRE simulator has 5 HTTP calls/run limit. With v2's 3 HTTP calls per project (fetch + classify + aggregate), only 1 project fits per run. Each project must be triggered individually. This is a simulator constraint, not a code bug.
   **Unresolved tradeoff**: v2 takes ~5-20s per project (two Claude calls) vs v1's ~2s (one call). Added complexity may or may not impress judges.
3. **Demo data** - DONE + VERIFIED.
4. **Cross-chain write** - DONE. Bridged 0.02 ETH Sepolia->Base Sepolia via L1StandardBridge. Deployed SentimentOracle at `0x8e39631FBfAB68Ff5739F576847Ba7795f5b3AcE` (Base Sepolia). Manually wrote chainlink score=82 to verify contract works. Workflow updated to write to all configured EVMs. **Caveat**: CRE simulator doesn't support Base Sepolia chain selector (`no compatible capability found`), so cross-chain writes only work on a real DON. The Sepolia write succeeds, Base Sepolia fails gracefully in simulator. The contract and workflow code are correct but cannot be E2E tested via CRE simulate.
5. **Tenderly Virtual TestNet** - BLOCKED. No `TENDERLY_ACCESS_KEY` configured. Need to create Tenderly account and get API key.

### P2 IF TIME
6. World ID integration
7. SentimentMarket.sol (prediction market)

### P0 REMAINING
8. ~~README~~ - DONE (updated with v2 workflow, new contract, all endpoints)
9. Demo video (<5 min) - NOT STARTED
10. Submit by March 1 (16 days away)

## Blocked On
- Tenderly: no TENDERLY_ACCESS_KEY, need to create account
- Demo video: not started, must be <5 min per rules
- Submission form: not started

## Remaining Wallet
- Sepolia: ~0.088 ETH
- Base Sepolia: ~0.019 ETH

## Known Limitations (honest)
- CRE simulator 5 HTTP call limit: only 1 project per workflow run. Multi-project loop FAILED (4/5 errored). Refactored to single-project-per-trigger architecture.
- CRE simulator doesn't support Base Sepolia chain selector. Cross-chain write code exists but can only be proven via manual `cast send`, not CRE simulate.
- RiskAlert has not been triggered on-chain. Would need a score drop of 15+ between consecutive runs for the same project.
- v2 workflow (two AI calls) takes 5-20s vs v1's 2s. May or may not be viewed favorably by judges.

## Key Decisions (this session)
- Hackathon uses curated demo data (honest staging mode, not fake "live")
- Production data: LunarCrush ($30/mo) primary, X API Basic ($100/mo) when revenue justifies
- Farcaster killed (dying platform)
- Frontend NOT required per FAQ, local demo is fine
- PRD v2.1 at ai/PRD.md with full audit fixes
