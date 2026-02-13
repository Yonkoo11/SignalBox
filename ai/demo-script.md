# SignalBox Demo Video Script (3-5 min)

## Pre-Recording Setup

```bash
# Terminal 1: API server
cd ~/Projects/SignalBox
python test_server.py
# Verify: curl localhost:8000/api/v1/sentiment/chainlink | jq .score

# Terminal 2: Ready for CRE commands
cd ~/Projects/SignalBox/workflow

# Browser: http://localhost:8000/proposals/proposal-hybrid.html (hybrid dashboard)
# Terminal: large font (16px+), clean prompt, dark theme
```

---

## Intro (0:00 - 0:30)

**Show: Hybrid dashboard landing page (http://localhost:8000/proposals/proposal-hybrid.html -> hybrid tab)**

"SignalBox is an on-chain social sentiment oracle built on Chainlink CRE. Think of it as Chainlink price feeds, but for community sentiment.

Instead of ETH/USD, smart contracts get a verified score of how the community actually feels about a project -- bugs, praise, feature requests -- all classified by AI and published on-chain across multiple networks."

---

## The Problem (0:30 - 1:00)

**Show: Scroll down to project grid on dashboard**

"Right now, crypto projects have no standardized way to measure community sentiment on-chain. DAOs vote on proposals without knowing if users are frustrated. DeFi protocols can't detect when bug reports spike. The data exists on Twitter, but it's locked out of smart contracts.

SignalBox fixes this by running a two-step AI pipeline on the Chainlink DON that classifies raw social data, scores overall sentiment, detects risk, and publishes verified results on-chain."

---

## Architecture (1:00 - 1:45)

**Show: Terminal with the architecture from README, or Excalidraw diagram**

"Here's the pipeline:

1. The SignalBox API aggregates social mentions for crypto projects -- praise, bugs, complaints, feature requests.

2. A CRE workflow written in TypeScript triggers via HTTP. It calls our API to fetch raw feedback.

3. Step 2: Claude AI classifies each item individually -- what category, what priority, is it a bot?

4. Step 3: A second Claude call takes the classified data and produces an overall score, summary, top issues, and a risk flag.

5. The DON reaches consensus, then writes the verified report to our SentimentOracle contract on Sepolia and Base Sepolia.

The two-step approach -- classify then aggregate -- produces better scores because the aggregation model works on structured data, not raw text."

---

## Live Demo - Dashboard (1:45 - 2:30)

**Show: http://localhost:8000/proposals/proposal-hybrid.html (hybrid dashboard)**

"Here's our dashboard monitoring 5 crypto projects. The hero shows the Global Sentiment Index.

**[Scroll to project grid]**

Each project has a live score, sparkline trend, and category breakdown. Chainlink is at 82 -- Very Positive. Arbitrum is at 62 -- Neutral, with more complaints.

**[Click on a project card to open slide-over]**

The slide-over shows the full report: score ring, AI analysis, category breakdown, and the live feed of classified signals.

**[Click 'Full Report' to navigate to project page]**

The full project page has trend charts, key themes, an influencer leaderboard, and the on-chain oracle card showing our deployed contract.

**[Scroll down to pipeline section]**

Down here, the CRE Pipeline shows recent workflow runs with status, duration, and transaction links."

---

## Live Demo - CRE Workflow v2 (2:30 - 3:30)

**Show: Terminal (split screen with browser if possible)**

"Let me run the actual CRE workflow. First, our API has data ready:"

```bash
curl -s localhost:8000/api/v1/sentiment/chainlink | jq '{score, total_mentions, breakdown}'
```

"8 mentions, 4 praise, 1 bug, 1 complaint. Now the CRE workflow:"

```bash
~/.local/bin/cre workflow simulate . -T staging-settings --broadcast \
  --non-interactive --trigger-index 0 --http-payload '{"project":"chainlink"}'
```

"Watch the output:
- Step 1 fetches from our API
- Step 2 sends each item to Claude for individual classification -- category, priority, bot probability
- Step 3 sends the classified batch to Claude for aggregation -- overall score, summary, risk assessment
- Step 5 writes the verified report to SentimentOracle on Sepolia

Score 82, risk flag false, transaction confirmed."

---

## On-Chain Verification (3:30 - 4:00)

**Show: Terminal**

"Let's verify on-chain. On Sepolia:"

```bash
cast call 0xcA374e8bba8bd2BA0Aed26c4d425aA9aa7E058D0 \
  "getSentiment(string)((uint8,uint32,uint32,uint32,uint32,string,uint256))" \
  "chainlink" --rpc-url https://1rpc.io/sepolia
```

"Score 82, 8 mentions, 5 positive, 1 negative, 1 neutral, and Claude's summary. All on-chain, verified by the Chainlink DON.

And on Base Sepolia -- same contract, same data, cross-chain:"

```bash
cast call 0x8e39631FBfAB68Ff5739F576847Ba7795f5b3AcE \
  "getSentiment(string)((uint8,uint32,uint32,uint32,uint32,string,uint256))" \
  "chainlink" --rpc-url https://base-sepolia-rpc.publicnode.com
```

"We also track 5 projects total:"

```bash
cast call 0xcA374e8bba8bd2BA0Aed26c4d425aA9aa7E058D0 \
  "getTrackedProjects()(string[])" --rpc-url https://1rpc.io/sepolia
```

**Show: Etherscan link to contract (open in browser)**

---

## Wrap Up (4:00 - 4:30)

**Show: Dashboard**

"Any smart contract can now call `getSentiment` and get verified community sentiment.

DAOs can weight governance votes by community health. Risk protocols can trigger alerts when sentiment crashes -- our contract emits a RiskAlert event when scores drop 15 or more points. Prediction markets can create sentiment-based positions.

SignalBox turns social noise into on-chain signal, powered by Chainlink CRE and Claude AI. Running in staging mode with curated data for this hackathon -- in production, it connects to LunarCrush, X API, and Reddit for real-time monitoring.

Thanks for watching."

---

## Recording Notes

- Record terminal and browser side-by-side (OBS or ScreenFlow)
- Terminal: large font (16px+), dark theme, clean prompt
- Browser: hybrid dashboard pre-loaded, full width
- Have test_server.py running BEFORE recording starts
- Pre-run the CRE simulate once to warm up (first run downloads Javy runtime)
- Total target: 4-4:30 minutes (leaves buffer under 5 min limit)
- Recording schedule per PRD: Thu Feb 27 record, Fri Feb 28 polish + upload
- Audio: speak slowly, pause between sections
- If CRE simulate takes >15s, edit out the wait or speed up footage
