# SignalBox Progress

## Current State: Demo video frames v2 captured + FFmpeg build script ready

## Session: Mar 4, 2026 - Demo Video Frame Re-capture

### Done This Session
- Re-captured 5 dashboard frames at 1920x1080 to `ai/demo-frames-v2/`:
  - F1-hero.png: Score 71, HEALTHY, 5 projects, 32 mentions, 95.7%, sparkline
  - F2-projects.png: 5 project cards + Trending Themes (varied counts) + start of signals
  - F3-signals.png: Signals feed with TWITTER badges, categories, engagement
  - F4-pipeline.png: CRE Pipeline (95.7%, 4:07, 4.2s), 5-step flow, runs table, Oracle header
  - F5-oracle.png: Pipeline runs + On-Chain Oracle (contract, Sepolia, CRE, 4/4 DON, 47 subs)
- Copied F6-F8 from v1 (Etherscan pages, 1280x800 - FFmpeg will upscale)
- Created `ai/build-demo-video.sh` - FFmpeg assembly script that:
  - Scales all frames to 1920x1080
  - Probes audio durations automatically
  - Applies Ken Burns 2% zoom
  - Adds 0.5s visual lead + 0.3s tail per segment
  - Creates intro/outro cards
  - Concatenates everything
- Created `ai/capture-frames.mjs` - Puppeteer script for re-capturing frames

### Note: Reddit blocked locally
- Reddit public JSON returns empty from this machine (rate limited or blocked)
- Dashboard shows curated Twitter data only (no Reddit badges)
- On Render, both Reddit + Twitter data worked correctly
- For demo frames, Twitter data is fine - voiceover doesn't mention Reddit specifically

### Note: Render service returning 404
- signalbox-demo.onrender.com returns 404 on all routes
- May need manual redeploy on Render dashboard
- Local server at port 8765 used for frame capture instead

### Remaining Tasks (USER action)
1. Generate 8 ElevenLabs audio clips from `ai/demo-video-production.md`
   - Voice: "Daniel" or "Josh"
   - Settings: Multilingual v2, Stability 0.50, Similarity 0.75, Speed 1.0x
   - Save to `ai/demo-audio/V1-hero.mp3` through `V8-automation.mp3`
2. Run `bash ai/build-demo-video.sh` to assemble video
3. Upload to YouTube (unlisted) or Loom
4. Update README with video URL
5. Submit on Devpost
6. Redeploy on Render if needed

### Key Files
- `ai/demo-video-production.md` - Voiceover script (8 clips, ~84s total)
- `ai/demo-frames-v2/` - 8 PNG frames (F1-F5 at 1920x1080, F6-F8 at 1280x800)
- `ai/build-demo-video.sh` - FFmpeg assembly script
- `ai/capture-frames.mjs` - Puppeteer capture script

### Key URLs
- GitHub Pages: https://yonkoo11.github.io/SignalBox/
- Render API: https://signalbox-demo.onrender.com (currently 404, needs redeploy)
- GitHub: https://github.com/Yonkoo11/SignalBox
- Automation Upkeep: https://automation.chain.link/sepolia/63951953480945797395994495867330998017254415204292776530584090000110353892946
