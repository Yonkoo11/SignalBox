# SignalBox Demo Video - Production Guide

**Approach:** Audio-first editing. The voiceover dictates the timeline, not the frames.

---

## Step 1: Generate 8 Separate Audio Clips in ElevenLabs

Generate each segment as its own audio file. This gives precise control: if one segment sounds off, you re-generate only that one. The FFmpeg build script uses actual audio durations, not guesses.

### ElevenLabs Settings (use these for ALL 8 clips)

- **Voice:** "Daniel" (British, calm) or "Josh" (American, natural)
- **Model:** Multilingual v2
- **Stability:** 0.50
- **Similarity Boost:** 0.75
- **Style:** 0.00 (neutral)
- **Speed:** 1.0x

### Important: Copy-paste rules

- Copy EXACTLY what's in the text box below. No extra words.
- Each clip should have NO leading or trailing silence. ElevenLabs adds natural pauses between sentences already.
- After generating, LISTEN to each clip once. If any word sounds robotic or rushed, regenerate that clip.
- Save each file as the exact filename shown (the FFmpeg script depends on these names).

---

### Clip 1: `V1-hero.mp3`
**Frame:** F1 (hero section)
**Words:** 31 | **Est. duration:** ~11s at natural pace

```
Every oracle in DeFi delivers price data. SignalBox delivers something new: a verified sentiment score for any crypto project, computed by AI and published on-chain through Chainlink CRE.
```

---

### Clip 2: `V2-projects.mp3`
**Frame:** F2 (project cards)
**Words:** 36 | **Est. duration:** ~12s at natural pace

```
We monitor five projects right now. Chainlink, Aave, Base, Uniswap, Arbitrum. Each gets a score from zero to a hundred, updated by a five-step pipeline running on the Chainlink Decentralized Oracle Network.
```

---

### Clip 3: `V3-signals.mp3`
**Frame:** F3 (signals feed)
**Words:** 30 | **Est. duration:** ~10s at natural pace

```
The pipeline starts with raw community feedback. Bug reports, praise, feature requests, complaints. Each one is classified by Claude AI with a category, priority, and bot probability score.
```

---

### Clip 4: `V4-pipeline.mp3`
**Frame:** F4 (pipeline runs)
**Words:** 28 | **Est. duration:** ~9s at natural pace

```
A second AI call aggregates everything into a single sentiment score, a natural language summary, and a risk flag. The full pipeline runs as a CRE workflow.
```

---

### Clip 5: `V5-oracle.mp3`
**Frame:** F5 (oracle page)
**Words:** 30 | **Est. duration:** ~10s at natural pace

```
The verified result is written to our SentimentOracle contract on Sepolia. Any smart contract can call getSentiment and read the latest score, mention counts, and AI summary directly on-chain.
```

---

### Clip 6: `V6-etherscan.mp3`
**Frame:** F6 (etherscan verified)
**Words:** 28 | **Est. duration:** ~9s at natural pace

```
All contracts are verified on Etherscan. The oracle, a governance gate that blocks proposals when sentiment is low, and a sentinel that uses Chainlink Automation to monitor data freshness.
```

---

### Clip 7: `V7-event.mp3`
**Frame:** F7 (etherscan event)
**Words:** 26 | **Est. duration:** ~9s at natural pace

```
Here's a real SentimentUpdated event on Etherscan. Score 62 for Arbitrum, six mentions, and a full AI-generated summary stored on-chain. All verified by the DON.
```

---

### Clip 8: `V8-automation.mp3`
**Frame:** F8 (automation upkeep)
**Words:** 22 | **Est. duration:** ~8s at natural pace

```
Two Chainlink services working together. CRE pushes data in. Automation watches the oracle's health. SignalBox turns social noise into on-chain signal.
```

---

## Word Count Summary

| Clip | Words | Est. Duration | Frame |
|------|-------|---------------|-------|
| V1 | 31 | ~11s | F1 Hero |
| V2 | 36 | ~12s | F2 Projects |
| V3 | 30 | ~10s | F3 Signals |
| V4 | 28 | ~9s | F4 Pipeline |
| V5 | 30 | ~10s | F5 Oracle |
| V6 | 28 | ~9s | F6 Etherscan Verified |
| V7 | 26 | ~9s | F7 Etherscan Event |
| V8 | 22 | ~8s | F8 Automation |
| **Total** | **231** | **~78s voiceover** | |

**Plus:** 2s intro silence + 2s outro silence + ~0.5s breathing room per transition (8 transitions x 0.3s = 2.4s)

**Estimated total: ~84s** (1:24)

This is slightly longer than the original 71s estimate because I'm accounting for natural speech pace (ElevenLabs at 1.0x with stability 0.50 breathes between sentences). If the actual audio comes in shorter, the video will be tighter. If longer, we have room under any hackathon limit.

---

## Step 2: Save Audio Clips

After generating all 8 clips in ElevenLabs, save them to:

```
SignalBox/ai/demo-audio/
  V1-hero.mp3
  V2-projects.mp3
  V3-signals.mp3
  V4-pipeline.mp3
  V5-oracle.mp3
  V6-etherscan.mp3
  V7-event.mp3
  V8-automation.mp3
```

---

## Step 3: Run the Build Script

Once the audio files are saved, tell Claude to build the FFmpeg command. The script will:

1. **Probe each audio file** for exact duration (no guessing)
2. **Calculate frame hold times:** audio_duration + 0.5s visual lead (frame appears before voice) + 0.3s tail (frame lingers after voice ends)
3. **Generate intro/outro** as black frames with white text
4. **Apply Ken Burns** (subtle 2% slow zoom) on each frame to avoid static feeling
5. **Crossfade** between frames (300ms)
6. **Mix audio** with correct offsets per frame
7. **Export** 1920x1080, H.264, 30fps, AAC audio

The build script is deterministic: same inputs = same output. You can iterate on individual audio clips and re-run without touching anything else.

---

## Quality Checklist (run after first render)

### Audio-only test (close your eyes)
- [ ] Does the voiceover make sense without seeing anything?
- [ ] Is the pacing natural? Not rushed, not dragging?
- [ ] Are there natural pauses between sections?
- [ ] Zero: "as you can see", "basically", "essentially", "actually"
- [ ] Does it sound like a person, not a robot reading a script?

### Video-only test (mute the audio)
- [ ] Do the frames tell a visual progression? (dashboard -> details -> on-chain proof)
- [ ] Is each frame on screen long enough to parse the content?
- [ ] Do transitions feel smooth, not jarring?
- [ ] Does the Ken Burns zoom feel subtle, not distracting?

### Combined test
- [ ] Does voiceover start ~0.5s after each frame appears? (visual leads audio)
- [ ] Does each frame linger ~0.3s after its voiceover ends? (breathing room)
- [ ] Does the overall pace feel confident, like a product demo?
- [ ] Intro: "SignalBox" text appears clearly for 2s?
- [ ] Outro: GitHub link visible for 2s?
- [ ] Total under 90 seconds?

### Senior editor gut check
- [ ] Would you watch this if you weren't the one who made it?
- [ ] Does it feel like a product, not a hackathon project?
- [ ] Could a judge understand what SignalBox does after watching once?
- [ ] Zero cringe moments?
