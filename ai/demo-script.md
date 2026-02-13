# SignalBox Demo Video Script (3-5 min)

## Intro (0:00 - 0:30)

**Show: Dashboard landing**

"SignalBox is an on-chain social sentiment oracle powered by Chainlink CRE. Think of it as Chainlink price feeds, but for community sentiment. Instead of ETH/USD, you get a verified score of how the community actually feels about a project -- bugs, praise, feature requests -- all classified by AI and published on-chain."

## The Problem (0:30 - 1:00)

**Show: Twitter feed / X mentions**

"Right now, crypto projects have no standardized way to measure community sentiment on-chain. DAOs vote on proposals without knowing if users are frustrated. Prediction markets can't factor in social consensus. DeFi protocols can't detect when bug reports spike. The data exists on Twitter/X, but it's not accessible to smart contracts."

## Architecture (1:00 - 1:45)

**Show: Architecture diagram from README (or draw in Excalidraw)**

"Here's how SignalBox works:

1. We monitor Twitter/X for mentions of crypto projects and classify them using Claude AI into categories -- praise, bugs, feature requests, complaints, questions.

2. The SignalBox API exposes this aggregated data at a public endpoint.

3. A Chainlink CRE workflow, written in TypeScript, runs on the DON. It fetches the data, sends it to Claude for scoring, reaches consensus across nodes, and writes the verified score to our SentimentOracle smart contract on Sepolia.

4. Any protocol can then read `getSentiment('chainlink')` and get back a score, breakdown, and AI summary -- all verified by the Chainlink DON."

## Live Demo - Dashboard (1:45 - 2:30)

**Show: http://localhost:8000/dashboard**

"Here's our dashboard. You can see sentiment scores for multiple projects. Chainlink is at 82 out of 100 -- Very Positive. The doughnut chart shows the category breakdown. The AI Analysis panel shows Claude's summary. On the right, the recent feedback feed with color-coded categories.

Down here, the On-chain Oracle panel shows our deployed contract on Sepolia with the verified score. And the CRE Workflow panel shows the full pipeline: Fetch API, AI Score, DON Consensus, Write EVM."

**Click different project cards to show switching**

## Live Demo - CRE Simulation (2:30 - 3:30)

**Show: Terminal**

"Let me show the CRE workflow running. First, our API server is serving sentiment data."

```bash
curl localhost:8000/api/v1/sentiment/chainlink | jq .score
# Shows: 82
```

"Now let's run the CRE workflow simulation:"

```bash
cd workflow
cre workflow simulate . --broadcast
```

"Watch the output -- Step 1 fetches from our API, Step 2 sends the feedback to Claude for scoring, Step 3 reaches DON consensus, Step 4 writes to the SentimentOracle contract on Sepolia."

**Show: successful output with score and tx hash**

## On-Chain Verification (3:30 - 4:00)

**Show: Terminal**

"Let's verify the data landed on-chain:"

```bash
cast call 0x8e39631FBfAB68Ff5739F576847Ba7795f5b3AcE \
  "getSentiment(string)(uint8,uint32,uint32,uint32,uint32,string,uint256)" \
  "chainlink" --rpc-url https://ethereum-sepolia-rpc.publicnode.com
```

"Score 82, 8 mentions, 5 positive, 2 negative, 1 neutral, and Claude's summary. All on-chain, verified by the Chainlink DON."

**Show: Etherscan link to the transaction**

## Use Cases & Wrap Up (4:00 - 4:30)

**Show: Dashboard or slides**

"Any smart contract can now call `getSentiment` and get verified community sentiment. DAOs can weight governance decisions. Prediction markets can create sentiment-based markets. Risk protocols can trigger alerts when sentiment drops.

SignalBox turns social noise into on-chain signal. Thanks for watching."

---

## Recording Notes

- Record terminal and browser in split screen, or switch between them
- Use a clean terminal with large font (16px+)
- Pre-load the dashboard before recording
- Have the test server running before the demo
- Keep the CRE simulation output scrolling visible
- Total target: 4-4.5 minutes
