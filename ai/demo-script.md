# SignalBox Demo Video Script

**Target: 3:30 - 4:30 (hard max 5:00)**
**Hackathon: Chainlink Convergence (deadline March 8, 2026)**
**Tracks: CRE & AI ($33,500) | Risk & Compliance ($32,000) | Tenderly ($10,250)**

---

## Pre-Recording Checklist

Do all of this BEFORE you hit record.

```bash
# 1. API server running (Terminal 1)
cd ~/Projects/SignalBox/src
DEMO_MODE=true python -m uvicorn app.main:app --port 8000
# Verify: curl -s localhost:8000/api/v1/sentiment/chainlink | jq .score

# 2. CRE workflow directory ready (Terminal 2 - large font, dark theme)
cd ~/Projects/SignalBox/workflow

# 3. Pre-warm the CRE simulator (first run downloads Javy runtime, takes 30s)
cre workflow simulate . -T staging-settings --broadcast \
  --non-interactive --trigger-index 0 --http-payload '{"project":"chainlink"}'

# 4. Browser tabs pre-loaded:
#    Tab 1: https://signalbox-4bmb.onrender.com/dashboard (Overview page)
#    Tab 2: https://sepolia.etherscan.io/address/0xcA374e8bba8bd2BA0Aed26c4d425aA9aa7E058D0

# 5. Terminal: 18px font, dark theme, clean prompt (PS1="$ ")
# 6. Screen recording: 1920x1080, mic test done
# 7. Close Slack, Discord, notifications - nothing pops up mid-recording
```

---

## SECTION 1: Hook (0:00 - 0:15)

**On screen:** Dark background, just you talking (or a title card: "SignalBox: The On-Chain Social Oracle")

**Say:**

> "Every oracle in DeFi delivers price data. ETH is $3,200. BTC is $64,000. Great. But nobody's telling smart contracts what the community actually *thinks* about a project. Are users happy? Are they finding bugs? Is sentiment crashing before a governance vote? That data exists on Twitter -- but it's completely locked out of the blockchain. Until now."

**Delivery tip:** Start with energy. This is your one chance to hook them. Speak like you're pitching to a friend, not reading a script. Lean into "until now" with a slight pause before it.

**Timing:** 15 seconds. Don't rush. Let the problem land.

---

## SECTION 2: The Vision (0:15 - 0:45)

**On screen:** Switch to the dashboard Overview page (https://signalbox-4bmb.onrender.com/dashboard)

**Say:**

> "This is SignalBox -- the first on-chain social sentiment oracle, built on Chainlink CRE."
>
> "It works like a Chainlink price feed, but instead of ETH/USD, you get a verified sentiment score from 0 to 100 for any crypto project. The score is computed by an AI pipeline that runs *inside* the Chainlink Decentralized Oracle Network. Not on my server. On the DON."
>
> "Any smart contract can call `getSentiment('chainlink')` and get back a verified score, mention counts, category breakdowns, and an AI-generated summary -- all on-chain."

**Delivery tip:** Point at the hero score on the dashboard when you say "0 to 100." Emphasize "on the DON" -- that's what separates this from a centralized API.

**Timing:** 30 seconds.

---

## SECTION 3: Architecture (0:45 - 1:30)

**On screen:** Show the architecture diagram from the README (or the Pipeline page of the dashboard: navigate to #/pipeline)

**Navigate to:** Click the "Pipeline" tab in the dashboard nav

**Say:**

> "Here's how the pipeline works. Five steps, all orchestrated by CRE."
>
> "Step one: the CRE workflow fires an HTTP request to the SignalBox API, which aggregates community mentions from Twitter for a given project. Bug reports, feature requests, praise, complaints -- raw text."
>
> "Step two: that raw text goes to Claude AI for *individual classification*. Each post gets a category, a priority level, and a bot probability score. This filters out spam and gives structure to the noise."
>
> "Step three: a *second* Claude call takes the classified batch and produces an overall sentiment score, a natural language summary, the top three issues, and a risk flag. Two-step AI is key here -- the aggregation model works on structured data, not raw text, so the scores are significantly better."
>
> "Step four: if the risk flag triggers -- score below 40, majority bugs, or a high-priority security issue -- the workflow logs a risk alert."
>
> "Step five: the DON reaches consensus on the result, then writes the verified report to our SentimentOracle contract on Sepolia via `writeReport`. ABI-encoded, signed, on-chain."

**Delivery tip:** Count the steps on your fingers or use the Pipeline page visuals. Keep it moving -- this is the most technical section, so don't linger. The judges know CRE; they want to see you *used* it properly, not that you can explain what an oracle is.

**Timing:** 45 seconds. If you're hitting 50+, trim the risk flag explanation.

---

## SECTION 4: Live Demo - CRE Workflow (1:30 - 3:00)

**On screen:** Terminal (full screen or split with browser)

This is the heart of the demo. You're going to run the actual CRE pipeline live and show data flowing from API to AI to chain.

### 4a. Show the API data (15 seconds)

**Run:**

```bash
curl -s localhost:8000/api/v1/sentiment/chainlink | jq '{project, total_mentions, breakdown, items: [.items[0], .items[1]]}'
```

**Say:**

> "First, let's see what the API has. We're monitoring Chainlink. 8 mentions in the last hour -- 4 praise, 1 bug, 1 complaint, 1 feature request, 1 question. This is the raw data that feeds the pipeline."

**Delivery tip:** Don't read every field. Just call out the total and the breakdown. The jq filter keeps it clean.

### 4b. Run the CRE workflow (60-90 seconds)

**Run:**

```bash
cre workflow simulate . -T staging-settings --broadcast \
  --non-interactive --trigger-index 0 --http-payload '{"project":"chainlink"}'
```

**Say (as output streams):**

> "Now I'm running the actual CRE workflow. Watch the output."
>
> *[As Step 1 appears]* "Step 1 -- fetching from our API. Got 8 mentions."
>
> *[As Step 2 appears]* "Step 2 -- Claude is classifying each item individually. Categories, priorities, bot scores."
>
> *[As Step 3 appears]* "Step 3 -- second AI call. Aggregating into a single score."
>
> *[As Step 5 / tx hash appears]* "And there it is -- score 78, risk flag false, transaction confirmed on Sepolia. That entire pipeline just ran on the Chainlink DON simulator."

**Delivery tip:** If the CRE simulate takes more than 10 seconds to complete, narrate what's happening while you wait. Don't sit in silence. If it takes 20+, say "the simulator compiles to Wasm and runs in a sandboxed environment, so there's a brief compilation step." If it's painfully slow in recording, speed up the footage in post with a "x2" overlay.

**IMPORTANT:** The output will show log lines like:
```
[Step 1] Fetching from SignalBox API...
[Step 1] Got 8 mentions
[Step 2] Classifying feedback with Claude AI...
[Step 2] Classification: {"praise":4,"bug":1,"complaint":1,"feature_request":1,"question":1}
[Step 3] Aggregating sentiment + risk assessment...
[Claude] Score: 78/100 | +5 -2 ~1 | risk=false
[Step 5] Writing to 1 chain(s)...
[Step 5] chainlink -> ethereum_testnet_sepolia: tx=0x...
```

Point at each log line as you narrate. The judges need to see the 5-step flow clearly.

### 4c. Verify on-chain immediately (20 seconds)

**Run:**

```bash
cast call 0xcA374e8bba8bd2BA0Aed26c4d425aA9aa7E058D0 \
  "getSentiment(string)((uint8,uint32,uint32,uint32,uint32,string,uint256))" \
  "chainlink" --rpc-url https://1rpc.io/sepolia
```

**Say:**

> "Let's verify. Calling `getSentiment` on the oracle contract on Sepolia. Score 78, 8 mentions, 5 positive, 2 negative, 1 neutral, and Claude's summary -- all on-chain, verified by the DON."

**Delivery tip:** The cast output is a tuple. Know what each field maps to before recording so you can call them out quickly without fumbling.

**Timing:** Entire Section 4 should be 60-90 seconds. This is the meat. Don't rush it, but don't ramble either.

---

## SECTION 5: Live Demo - Dashboard (3:00 - 3:45)

**On screen:** Browser - dashboard at https://signalbox-4bmb.onrender.com/dashboard

### 5a. Overview page (15 seconds)

**Navigate to:** Overview tab (should already be there, or click it)

**Say:**

> "Here's the dashboard. The Overview page shows every project we're monitoring -- Chainlink, Uniswap, Aave, Base, Arbitrum. Each card has the live score, trend sparkline, and category breakdown. Chainlink at 78 -- positive. Arbitrum at 62 -- more mixed, with higher complaint volume."

### 5b. Signals page (10 seconds)

**Navigate to:** Click "Signals" tab

**Say:**

> "The Signals page shows the live feed -- every classified mention in real time. You can see the AI-assigned category, priority, and engagement metrics for each post."

### 5c. Pipeline page (10 seconds)

**Navigate to:** Click "Pipeline" tab

**Say:**

> "Pipeline shows recent CRE workflow runs -- status, duration, and the transaction hashes linking back to Etherscan."

### 5d. Oracle page (10 seconds)

**Navigate to:** Click "Oracle" tab

**Say:**

> "And the Oracle page shows the on-chain state -- contract addresses on Sepolia and Base Sepolia, the latest scores written to chain, and verified transaction history."

**Delivery tip:** Move through the dashboard with purpose. Click, say one sentence per page, move on. Don't explore or scroll aimlessly. The judges have short attention spans. They want to see that the UI exists, it's real, and it connects to the on-chain data. That's it.

**Timing:** 45 seconds total for all four tabs.

---

## SECTION 6: Consumer Contract - SentimentGate (3:45 - 4:15)

**On screen:** Split or switch between terminal and code

### 6a. Show the contract (15 seconds)

Show SentimentGate.sol briefly in your editor or terminal. Highlight the key function.

**Say:**

> "So who consumes this data? Here's SentimentGate -- a governance contract that won't let proposals execute unless community sentiment is healthy."
>
> "It reads from SentimentOracle, checks the score against a threshold, checks that the data is fresh, and only then lets the proposal go through. If sentiment is too low, it reverts with `SentimentTooLow`. Simple, but powerful -- imagine a DAO that literally cannot push a controversial upgrade when users are upset."

### 6b. Tests passing (15 seconds)

**Run:**

```bash
cd ~/Projects/SignalBox/contracts && forge test --summary
```

**Say:**

> "19 tests across both contracts -- 8 for the oracle, 11 for the gate. All green. The gate tests cover the happy path, stale data rejection, low sentiment blocking, cancellation, and threshold updates."

**Delivery tip:** Don't wait for compilation. Pre-build with `forge build` before recording. The `forge test --summary` output should be fast if already compiled. If it takes a few seconds, just let it run while you talk about the test coverage.

**Timing:** 30 seconds.

---

## SECTION 7: What's Next (4:15 - 4:30)

**On screen:** Dashboard Overview or a simple slide/title card

**Say:**

> "What's next for SignalBox? Multi-chain distribution via Chainlink CCIP -- one workflow update, every chain gets the data. Real social API integrations -- LunarCrush, X API, Reddit -- replacing our curated demo data with live feeds. And more consumer contracts: DeFi protocols gating liquidations by sentiment, prediction markets trading on social consensus shifts."
>
> "SignalBox turns social noise into on-chain signal. Thanks for watching."

**Delivery tip:** End strong. Don't trail off. "Thanks for watching" with a nod, then cut. No awkward silence.

**Timing:** 15 seconds. Keep it tight.

---

## Total Timing Breakdown

| Section | Duration | Cumulative |
|---------|----------|------------|
| 1. Hook | 0:15 | 0:15 |
| 2. Vision | 0:30 | 0:45 |
| 3. Architecture | 0:45 | 1:30 |
| 4. CRE Workflow Demo | 1:30 | 3:00 |
| 5. Dashboard Demo | 0:45 | 3:45 |
| 6. Consumer Contract | 0:30 | 4:15 |
| 7. What's Next | 0:15 | 4:30 |

**Total: ~4:30** (safe buffer under the 5:00 limit)

If you're running long, cut these first:
1. Dashboard walkthrough -- drop Signals and Pipeline tabs, just show Overview + Oracle (saves 20s)
2. Architecture step 4 (risk flag detail) -- mention it exists, don't explain the logic (saves 10s)
3. "What's Next" can be trimmed to one sentence (saves 10s)

If you're running short, expand these:
1. Run a second project through the CRE pipeline: `--http-payload '{"project":"aave"}'`
2. Show tracked projects: `cast call 0xcA374e8bba8bd2BA0Aed26c4d425aA9aa7E058D0 "getTrackedProjects()(string[])" --rpc-url https://1rpc.io/sepolia`
3. Open the Etherscan contract page and show the verified transactions

---

## Judge-Specific Beats

These are moments tailored to what each key judge values. Make sure you don't accidentally skip them.

**Harry Papacharissiou (Head of DevRel)** -- wants real Chainlink integration, not toy usage
- Beat: The 5-step CRE pipeline is real and runs end-to-end. Show the `writeReport` tx hash.
- Beat: SentimentGate as a consumer contract shows downstream utility.
- Beat: Two chains (Sepolia + Base Sepolia) shows cross-chain thinking.

**Dave Isbitski (ex-Amazon Alexa)** -- values polished demos and storytelling
- Beat: The opening hook. Problem-first, not feature-first.
- Beat: Dashboard walkthrough should feel smooth, not fumbling between tabs.
- Beat: End with a clear vision, not just "it works."

**Andrej Rakic (CRE Bootcamp leader)** -- deep CRE technical usage
- Beat: Show the actual CRE log output with step numbers. He wants to see you used capabilities correctly.
- Beat: Mention `consensusIdenticalAggregation`, `Runtime.report()`, `EVMClient.writeReport()`, `Runtime.getSecret()`.
- Beat: The two-step AI approach (classify then aggregate) is a non-trivial workflow pattern. Call it out.

**Richard Gottleber (teacher)** -- values clear, accessible explanations
- Beat: The "price feeds but for sentiment" analogy. He'll appreciate the framing.
- Beat: The SentimentGate use case makes the abstract concrete. "A DAO that can't push upgrades when users are upset."

---

## Recording Tips

1. **Energy level:** 7/10. Excited but not manic. You built something real; let the confidence show.
2. **Pacing:** Slightly slower than you think. Demo videos always sound rushed on playback.
3. **Mistakes:** If you fumble a command, just re-type it. Don't apologize or restart the whole section. Cut it in post.
4. **Silence:** Never let the screen sit idle for more than 3 seconds. If a command is running, narrate what's happening.
5. **Cursor:** Move your mouse deliberately. Don't jitter it around the screen.
6. **Font size:** 18px minimum in terminal. Judges watch on laptops, not monitors.
7. **Do NOT:** Say "as you can see" -- just describe what's there. Don't say "basically" or "essentially" -- they add nothing.
8. **Do NOT:** Read code line by line. Show the contract, highlight the key function, explain the concept.

## Post-Production

- Trim dead air and long compilation waits
- Add a 2-second title card at the start: "SignalBox - The On-Chain Social Oracle | Chainlink Convergence Hackathon 2026"
- Optional: speed up CRE simulate if it takes >15s (2x with timer overlay)
- Export at 1080p, H.264, <100MB
- Upload to YouTube (unlisted) or Loom, add link to README and submission form
