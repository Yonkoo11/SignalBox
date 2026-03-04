#!/bin/bash
# SignalBox Demo Video Builder
# Requires: ffmpeg, 8 audio clips in ai/demo-audio/, 8 frames in ai/demo-frames-v2/
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRAMES_DIR="$SCRIPT_DIR/demo-frames-v2"
AUDIO_DIR="$SCRIPT_DIR/demo-audio"
OUTPUT="$SCRIPT_DIR/demo-video.mp4"
TEMP_DIR="$SCRIPT_DIR/.video-tmp"

mkdir -p "$TEMP_DIR"

# Frame-to-audio mapping
FRAMES=(F1-hero F2-projects F3-signals F4-pipeline F5-oracle F6-etherscan-verified F7-etherscan-tx F8-automation)
AUDIOS=(V1-hero V2-projects V3-signals V4-pipeline V5-oracle V6-etherscan V7-event V8-automation)

echo "=== SignalBox Demo Video Builder ==="

# Check all files exist
for i in "${!FRAMES[@]}"; do
    frame="$FRAMES_DIR/${FRAMES[$i]}.png"
    audio="$AUDIO_DIR/${AUDIOS[$i]}.mp3"
    if [ ! -f "$frame" ]; then echo "MISSING: $frame"; exit 1; fi
    if [ ! -f "$audio" ]; then echo "MISSING: $audio"; exit 1; fi
done
echo "All 8 frames and 8 audio clips found."

# Step 1: Scale all frames to 1920x1080 (some may be different sizes)
echo "Scaling frames to 1920x1080..."
for i in "${!FRAMES[@]}"; do
    ffmpeg -y -i "$FRAMES_DIR/${FRAMES[$i]}.png" \
        -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black" \
        "$TEMP_DIR/frame_${i}.png" 2>/dev/null
done

# Step 2: Get audio durations and build segments
echo "Probing audio durations..."
DURATIONS=()
for i in "${!AUDIOS[@]}"; do
    dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$AUDIO_DIR/${AUDIOS[$i]}.mp3")
    DURATIONS+=("$dur")
    echo "  ${AUDIOS[$i]}: ${dur}s"
done

# Step 3: Create video segments (frame + Ken Burns zoom + audio)
echo "Building video segments..."
SEGMENTS=()
for i in "${!FRAMES[@]}"; do
    dur=${DURATIONS[$i]}
    # Add 0.5s visual lead + 0.3s tail
    total_dur=$(echo "$dur + 0.8" | bc)
    segment="$TEMP_DIR/segment_${i}.mp4"

    # Ken Burns: subtle 2% zoom over duration
    ffmpeg -y -loop 1 -i "$TEMP_DIR/frame_${i}.png" \
        -i "$AUDIO_DIR/${AUDIOS[$i]}.mp3" \
        -vf "zoompan=z='min(zoom+0.0002,1.02)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30" \
        -t "$total_dur" \
        -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
        -c:a aac -b:a 192k \
        -af "adelay=500|500" \
        -shortest \
        "$segment" 2>/dev/null

    SEGMENTS+=("$segment")
    echo "  Segment $i: ${total_dur}s (audio ${dur}s + 0.8s padding)"
done

# Step 4: Create intro (2s black with white text)
echo "Creating intro..."
ffmpeg -y -f lavfi -i "color=c=black:s=1920x1080:d=2" \
    -vf "drawtext=text='SignalBox':fontsize=72:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2-30,drawtext=text='The On-Chain Social Oracle':fontsize=28:fontcolor=gray:x=(w-text_w)/2:y=(h-text_h)/2+40" \
    -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
    "$TEMP_DIR/intro.mp4" 2>/dev/null

# Step 5: Create outro (2s black with GitHub link)
echo "Creating outro..."
ffmpeg -y -f lavfi -i "color=c=black:s=1920x1080:d=2" \
    -vf "drawtext=text='github.com/yonko/SignalBox':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2-15,drawtext=text='Powered by Chainlink CRE':fontsize=22:fontcolor=gray:x=(w-text_w)/2:y=(h-text_h)/2+35" \
    -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
    "$TEMP_DIR/outro.mp4" 2>/dev/null

# Step 6: Build concat file
echo "Concatenating all segments..."
CONCAT_FILE="$TEMP_DIR/concat.txt"
echo "file 'intro.mp4'" > "$CONCAT_FILE"
for i in "${!SEGMENTS[@]}"; do
    echo "file 'segment_${i}.mp4'" >> "$CONCAT_FILE"
done
echo "file 'outro.mp4'" >> "$CONCAT_FILE"

# Step 7: Concatenate with crossfade (simple concat for reliability)
ffmpeg -y -f concat -safe 0 -i "$CONCAT_FILE" \
    -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
    -c:a aac -b:a 192k \
    "$OUTPUT" 2>/dev/null

# Get final duration
FINAL_DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUTPUT")
echo ""
echo "=== BUILD COMPLETE ==="
echo "Output: $OUTPUT"
echo "Duration: ${FINAL_DUR}s"
echo "Size: $(du -h "$OUTPUT" | cut -f1)"

# Cleanup
rm -rf "$TEMP_DIR"
echo "Temp files cleaned."
