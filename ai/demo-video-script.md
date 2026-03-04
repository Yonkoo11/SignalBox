# SignalBox Demo Video Script

**Style:** Faktory-style. Dashboard frames + ElevenLabs voiceover. No live recording.
**Duration:** ~71 seconds (67s content + 2s intro + 2s outro)
**Voice:** Male, calm, confident. ElevenLabs "Daniel" or "Josh". Speed 1.0x.

---

## Intro (2 seconds)

**Frame:** Black screen, white text fades in: "SignalBox"
**Audio:** Silence

---

## Frame 1: Hero Section (0:02 - 0:12)

**Frame:** `demo-frames/F1-hero.png` -- Dashboard overview top: title, score 71, HEALTHY, sparkline, stat grid
**Voiceover:**

> Every oracle in DeFi delivers price data. SignalBox delivers something new: a verified sentiment score for any crypto project, computed by AI and published on-chain through Chainlink CRE.

---

## Frame 2: Project Cards (0:12 - 0:22)

**Frame:** `demo-frames/F2-projects.png` -- Five project cards with scores, sparklines, summaries
**Voiceover:**

> We monitor five projects right now. Chainlink, Aave, Base, Uniswap, Arbitrum. Each gets a score from zero to a hundred, updated by a five-step pipeline running on the Chainlink Decentralized Oracle Network.

---

## Frame 3: Signals Feed (0:22 - 0:30)

**Frame:** `demo-frames/F3-signals.png` -- Live feed with classified mentions, categories, priorities
**Voiceover:**

> The pipeline starts with raw community feedback. Bug reports, praise, feature requests, complaints. Each one is classified by Claude AI with a category, priority, and bot probability score.

---

## Frame 4: Pipeline Runs (0:30 - 0:38)

**Frame:** `demo-frames/F4-pipeline.png` -- CRE workflow execution history
**Voiceover:**

> A second AI call aggregates everything into a single sentiment score, a natural language summary, and a risk flag. The full pipeline runs as a CRE workflow.

---

## Frame 5: Oracle Page (0:38 - 0:46)

**Frame:** `demo-frames/F5-oracle.png` -- Contract addresses, latest scores, tx links
**Voiceover:**

> The verified result is written to our SentimentOracle contract on Sepolia. Any smart contract can call getSentiment and read the latest score, mention counts, and AI summary directly on-chain.

---

## Frame 6: Etherscan Verified (0:46 - 0:54)

**Frame:** `demo-frames/F6-etherscan-verified.png` -- Green "Verified" badge, source code visible
**Voiceover:**

> All contracts are verified on Etherscan. The oracle, a governance gate that blocks proposals when sentiment is low, and a sentinel that uses Chainlink Automation to monitor data freshness.

---

## Frame 7: Etherscan Transaction (0:54 - 1:02)

**Frame:** `demo-frames/F7-etherscan-tx.png` -- Decoded SentimentUpdated event with score, mentions, AI summary
**Voiceover:**

> Here's a real SentimentUpdated event on Etherscan. Score 62 for Arbitrum, six mentions, and a full AI-generated summary stored on-chain. All verified by the DON.

---

## Frame 8: Automation Upkeep (1:02 - 1:09)

**Frame:** `demo-frames/F8-automation.png` -- Chainlink Automation upkeep page
**Voiceover:**

> Two Chainlink services working together. CRE pushes data in. Automation watches the oracle's health. SignalBox turns social noise into on-chain signal.

---

## Outro (2 seconds)

**Frame:** Black screen, white text fades in: "Built on Chainlink CRE | github.com/Yonkoo11/SignalBox"
**Audio:** Silence

---

## Assembly Instructions

### ElevenLabs Settings
- Voice: "Daniel" (British, calm) or "Josh" (American, natural)
- Model: Multilingual v2
- Stability: 0.50
- Similarity Boost: 0.75
- Style: 0.00 (neutral)
- Speed: 1.0x

### Video Editor (CapCut or DaVinci Resolve)
1. Import voiceover audio as single track
2. Import 8 frame PNGs as image clips
3. Set each frame duration to match the timing table above
4. Transition between frames: crossfade, 300ms
5. Intro: 2s black with "SignalBox" in white, fade in over 500ms
6. Outro: 2s black with "Built on Chainlink CRE | github.com/Yonkoo11/SignalBox", fade in 500ms
7. Optional: subtle 2% slow zoom (Ken Burns) on each frame to avoid static feeling
8. Export: 1920x1080, H.264, 30fps, <50MB

### Quality Checks
- [ ] Watch without sound: do frames tell a visual story?
- [ ] Listen without video: does voiceover stand alone?
- [ ] Together: does sync feel natural, not rushed?
- [ ] Zero "as you can see", "basically", "essentially"
- [ ] Feels like a product, not a student project
- [ ] Total duration under 75 seconds
