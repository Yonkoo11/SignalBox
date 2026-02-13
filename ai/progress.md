# SignalBox Progress

## Current State: P1 complete (3/5 done, 1 blocked, 1 dropped). Ready for demo prep.

## What's Done

### CRE Dev Environment
- CRE CLI v1.0.10 at `~/.local/bin/cre`, Bun v1.3.9, Node v20.19.5, Foundry v1.4.4
- Python venv at `.venv/` with FastAPI, uvicorn
- **NOTE:** bun/cre not in default PATH for shell scripts, use full paths

### Smart Contract: SentimentOracle v2
- `contracts/src/SentimentOracle.sol` - extends CRE ReceiverTemplate
- Stores: score (0-100), totalMentions, positive, negative, neutral, summary
- RiskAlert: emits when score drops >= 15 points between updates
- 8 tests passing (`contracts/test/SentimentOracle.t.sol`)
- **Sepolia**: `0xcA374e8bba8bd2BA0Aed26c4d425aA9aa7E058D0` (5 projects on-chain)
- **Base Sepolia**: `0x8e39631FBfAB68Ff5739F576847Ba7795f5b3AcE` (1 project, manual write)
- Owner: `0x043117bb026a4F8F4b3eC259511748208243B59a`

### CRE Workflow v2
- Two-step AI pipeline: classify (category/priority/botProbability) -> aggregate (score/summary/risk)
- All 5 projects tested individually via CRE simulate + broadcast:
  - chainlink: 82, uniswap: 68, aave: 82, base: 72, arbitrum: 62
- Writes to all configured EVMs (Sepolia works, Base Sepolia fails in simulator)
- **Limitation**: 1 project per invocation (CRE 5 HTTP call limit, v2 uses 3 per project)

### Frontend
- Production dashboard: `proposals/proposal-hybrid.html` (selected from 3 proposals)
- Hybrid: long-scroll + slide-over quick-peek + hash-routed full pages + influencer leaderboard
- Polish pass: ambient gradients, card shadows, glow effects, hover states
- URL: `http://localhost:8000/proposals/proposal-hybrid.html`

### Test Server
- `test_server.py` - FastAPI with full demo API suite
- Curated demo data for 5 projects with unique feed items, AI summaries, trends

### Git
- Latest commit: `463a628` (pushed to main)
- Includes: contracts, workflow v2, cross-chain, all proposals, README

## P1 Status (3/5 done)
1. **SentimentOracle v2** - DONE. Deployed both chains. NOT tested: RiskAlert trigger on-chain.
2. **CRE workflow v2** - DONE. All 5 projects tested. Known: 1 project/run, v2 slower than v1.
3. **Demo data** - DONE.
4. **Cross-chain** - DONE. Base Sepolia deployed + verified via manual cast send. CRE simulator can't write to Base Sepolia (chain selector not supported).
5. **Tenderly** - BLOCKED. No API key. Dropping -- not critical for submission.

## What's Left (Deadline: March 1)
- [ ] Demo video (<5 min) - Target: Feb 27-28 per schedule
- [ ] Submission form - Opens closer to deadline
- [ ] Optional: Deploy test_server.py to Render for judges to access remotely

## Remaining Wallet
- Sepolia: ~0.088 ETH
- Base Sepolia: ~0.019 ETH

## Known Limitations (honest)
- CRE simulator 5 HTTP call limit: 1 project per workflow run
- CRE simulator doesn't support Base Sepolia chain selector
- RiskAlert never triggered on-chain (needs 15+ point drop)
- v2 workflow takes 5-20s vs v1's 2s per project
- Dashboard reads API data, not on-chain data directly
