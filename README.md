# SignalBox: On-Chain Social Sentiment Oracle

**Chainlink price feeds, but for community sentiment.**

SignalBox monitors Twitter/X for mentions of crypto projects, scores sentiment using Claude AI, and publishes verified scores on-chain via Chainlink CRE. DAOs, prediction markets, and DeFi protocols can consume this data to make decisions based on real community signal.

**Chainlink Convergence Hackathon | CRE & AI Track**

## How It Works

```
Twitter/X mentions
       |
       v
  SignalBox API (FastAPI)
  Collects, classifies, aggregates
       |
       v
  /api/v1/sentiment/{project}
       |
       v
  Chainlink CRE Workflow (TypeScript)
  +------------------------------------+
  | 1. HTTP Fetch    - Pull sentiment  |
  | 2. Claude AI     - Score 0-100     |
  | 3. DON Consensus - Nodes agree     |
  | 4. Write EVM     - Publish score   |
  +------------------------------------+
       |
       v
  SentimentOracle.sol (Sepolia)
  On-chain sentiment feed
       |
       v
  Any protocol can read:
  getSentiment("chainlink") => {score: 82, mentions: 8, ...}
```

## Live Demo

- **Contract**: [`0x8e39631FBfAB68Ff5739F576847Ba7795f5b3AcE`](https://sepolia.etherscan.io/address/0x8e39631FBfAB68Ff5739F576847Ba7795f5b3AcE) (Sepolia)
- **E2E Transaction**: [`0xdb3d2cf8...`](https://sepolia.etherscan.io/tx/0xdb3d2cf8213f0f33e85ac6073b17422ffc2743ae94c18287e5dda3d967d9fb1b)
- **On-chain Score**: 82/100 for Chainlink (verified via `cast call`)
- **Dashboard**: Run locally at `http://localhost:8000/dashboard`

## What Makes This Different

Most oracles deliver price data. SignalBox delivers **sentiment data** -- a novel oracle type that captures what the community actually thinks about a project. This opens up use cases that price feeds can't address:

- **DAO governance**: Weight proposals by community sentiment
- **Prediction markets**: Trade on social consensus shifts
- **Risk assessment**: Detect community frustration before it becomes a sell event
- **Protocol health**: Monitor bug reports and complaints in real-time

## CRE Workflow

The CRE workflow (`workflow/`) runs on Chainlink's Decentralized Oracle Network:

1. **HTTP Trigger** -- on-demand or scheduled
2. **Fetch** -- pulls aggregated feedback from the SignalBox API
3. **AI Score** -- sends feedback to Claude AI via CRE's HTTP capability, gets a sentiment score (0-100), breakdown (positive/negative/neutral), and a natural language summary
4. **DON Consensus** -- CRE nodes reach agreement on the score using `consensusIdenticalAggregation`
5. **Write EVM** -- publishes the verified report to `SentimentOracle.sol` via `writeReport`

The workflow handles multiple projects in a single run, with per-project error isolation so one failure doesn't affect others.

### Workflow Files

| File | Purpose |
|------|---------|
| `workflow/main.ts` | Entry point, registers HTTP trigger |
| `workflow/httpCallback.ts` | Core pipeline: fetch -> score -> write |
| `workflow/claude.ts` | Claude AI integration with input validation |
| `workflow/workflow.yaml` | CRE staging/production config |
| `workflow/config.staging.json` | Chain config, contract address, API URL |

## Smart Contract

`SentimentOracle.sol` extends CRE's `ReceiverTemplate` to accept verified reports from the DON.

**Stores per project:**
- `score` (0-100) -- overall sentiment
- `totalMentions` -- feedback volume
- `positive` / `negative` / `neutral` -- category counts
- `summary` -- AI-generated natural language summary
- `timestamp` -- last update time

**Read functions:**
- `getSentiment(project)` -- latest data
- `getHistory(project, count)` -- historical scores
- `getTrackedProjects()` -- all monitored projects

**Events:**
- `SentimentUpdated(project, score, totalMentions, summary, timestamp)`
- `ProjectAdded(project)`

## Running Locally

### Prerequisites

- Node.js v20+
- Foundry (forge, cast)
- Bun v1.3+
- CRE CLI v1.0.10+
- Python 3.10+ (for API server)

### 1. Smart Contract

```bash
cd contracts
forge build
forge test  # 5 tests, all passing
```

### 2. API Server (demo mode)

```bash
# Uses test_server.py (no database needed)
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn
python test_server.py
# API: http://localhost:8000
# Dashboard: http://localhost:8000/dashboard
```

### 3. CRE Workflow Simulation

```bash
cd workflow
cp ../.env.example ../.env
# Set ANTHROPIC_API_KEY and CRE_ETH_PRIVATE_KEY in .env

# Simulate (dry run)
cre workflow simulate .

# Simulate with on-chain broadcast
cre workflow simulate . --broadcast
```

### 4. Verify On-Chain

```bash
cast call 0x8e39631FBfAB68Ff5739F576847Ba7795f5b3AcE \
  "getSentiment(string)(uint8,uint32,uint32,uint32,uint32,string,uint256)" \
  "chainlink" \
  --rpc-url https://ethereum-sepolia-rpc.publicnode.com
# Returns: 82, 8, 5, 2, 1, "Chainlink community sentiment is strongly positive...", 1739...
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| API Server | Python, FastAPI |
| CRE Workflow | TypeScript, Chainlink CRE SDK v1.0.9 |
| Smart Contract | Solidity ^0.8.24, Foundry |
| AI Scoring | Claude Haiku 4.5 (via CRE HTTP) |
| AI Classification | Claude Haiku (in SignalBox API) |
| Testnet | Ethereum Sepolia |
| ABI Encoding | viem (`encodeAbiParameters`) |
| Contract Base | CRE ReceiverTemplate, OpenZeppelin v5.5 |

## Project Structure

```
SignalBox/
+-- contracts/
|   +-- src/SentimentOracle.sol     # On-chain oracle contract
|   +-- test/SentimentOracle.t.sol  # Foundry tests
|   +-- script/Deploy.s.sol         # Deployment script
+-- workflow/
|   +-- main.ts                     # CRE entry point
|   +-- httpCallback.ts             # Fetch -> AI -> Write pipeline
|   +-- claude.ts                   # Claude AI scoring
|   +-- workflow.yaml               # CRE config
|   +-- config.staging.json         # Deployment config
+-- src/app/
|   +-- routers/sentiment.py        # Sentiment API endpoints
|   +-- static/dashboard.html       # Demo dashboard
+-- test_server.py                  # Lightweight demo server
```

## API Endpoints

### `GET /api/v1/sentiment/{project}?period=1h`

Returns aggregated sentiment data for a project.

```json
{
  "project": "chainlink",
  "period": "1h",
  "score": 82,
  "is_demo": true,
  "total_mentions": 8,
  "breakdown": {
    "praise": 4,
    "feature_request": 1,
    "question": 1,
    "bug": 1,
    "complaint": 1
  },
  "items": [...]
}
```

### `GET /api/v1/sentiment`

Lists all monitored projects.

## E2E Test Results

Full pipeline executed successfully:

```
=== SignalBox Sentiment Oracle: HTTP Trigger ===
[Step 1] Updating sentiment for: chainlink
[Step 2] Got 8 mentions
[Step 3] Claude AI score: 82/100
[Step 4] chainlink: score=82 tx=0xdb3d2cf8...
=== Sentiment Oracle Update Complete ===
```

On-chain data verified:
- Score: 82
- Total Mentions: 8
- Positive: 5, Negative: 2, Neutral: 1
- Summary: "Chainlink community sentiment is strongly positive..."

## Built For

Chainlink Convergence Hackathon 2026 -- CRE & AI Track
