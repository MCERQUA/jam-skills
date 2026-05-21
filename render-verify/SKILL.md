---
name: render-verify
description: "Universal video-render verification gate. Use after producing an MP4 to confirm it's not just metadata-valid but actually plays. Catches h264 NAL corruption, solid-color frames, missing audio, duration drift. ALWAYS run before shipping a V*_DONE signal or moving to the next iteration."
metadata:
  version: 1.0.0
---

# render-verify — did the video actually work?

The verification gap that let broken-v3 ship: ffprobe metadata passed (h264 header looked fine, duration was right), but the actual h264 stream had Invalid NAL units everywhere and Chrome could only decode the first I-frame. The manager shipped `V3_DONE · §9-pass-rate: 5/5` because §9 only checked metadata. This skill closes that gap.

**Rule: no agent ships a render result without `render-verify` returning PASS.**

## When to use

- After any `hyperframes render`, Remotion build, ffmpeg encode, or other MP4 production
- Before sending `V*_DONE`, `task-result`, or iteration-ready signals to the mesh
- Before adding to a client deliverables folder
- In CI / cron pipelines that auto-process video

## How to invoke

```bash
# Basic — read PASS/FAIL/WARN from exit code (0/1/2)
render-verify /path/to/output.mp4

# Strict — declare your expectations, fail hard on drift
render-verify /path/to/output.mp4 \
  --expected-duration 21.0 \
  --expected-audio yes \
  --frame-samples 12 \
  --min-audio-db -40

# CI / scripting — JSON-only, sidecar report written automatically
render-verify /path/to/output.mp4 --json-only > /tmp/verify.json
```

Report sidecar is always written to `<file>.verify.json` next to the MP4 (so the next agent in the pipeline can read it without re-running ffmpeg).

## What it checks

| Check | What it catches | How |
|-|-|-|
| **Container / metadata sanity** | Truncated file, missing moov, no streams | ffprobe |
| **Full-decode integrity** | h264 NAL corruption (the v3 failure mode) | `ffmpeg -v error -i <f> -f null -` — any error line = FAIL |
| **Frame samples (N=10)** | Solid-color "rendered black", broken transitions | Extract N frames + ImageMagick standard-deviation; std<0.005 = solid |
| **Audio peak** | Shipped without VO, muted track, dead audio | `volumedetect` mean_volume must be > −45 dB |
| **Duration sanity** | Composition truncated, encoded only partial timeline | duration must be within ±0.5s of `--expected-duration` |

## Verdict levels

- **PASS (exit 0)** — every check passes, file is shippable
- **WARN (exit 2)** — minor anomaly: 1 suspicious frame, audio slightly quiet but present, etc. Review before shipping.
- **FAIL (exit 1)** — disqualifying problem: stream corrupt, half the frames solid, expected audio missing, duration off. **DO NOT SHIP.**

## Pipeline integration pattern

```bash
hyperframes render --output out.mp4
if ! render-verify out.mp4 --expected-duration "$DUR" --expected-audio yes; then
  # Don't ship. Don't mesh-send V*_DONE. Surface the report.
  cat out.verify.json
  exit 1
fi
# Only NOW can the agent declare success.
mesh-send --to host@mesh --kind task --subject "render-done:$ID" < ...
```

## Common failure modes + diagnostic flow

1. **decode_ok=false with hundreds of error lines** → composition pipeline (hyperframes/Remotion) produced an invalid h264 stream. Likely culprits: headless Chrome crashed mid-render, ffmpeg buffer overflow, font/asset missing causing a hang.
2. **frames_solid >= 5/10** → most frames are single-color. Either the composition CSS broke (all elements off-screen) OR the encoder lost track of the source.
3. **expected-audio-missing or audio-too-quiet** → VO file failed to mux in, music ducking went too aggressive, or audio stream got dropped during encode.
4. **duration-mismatch** → ffmpeg encoded fewer frames than the composition timeline expected. Often means the render hit a per-frame timeout and bailed early.

## Updating this skill

If you discover a new failure mode that slipped past the current checks, ADD a check here. Don't write a one-off ad-hoc verifier. This skill is the single source of truth for "is this video shippable."

## Related

- `render-preflight` — run BEFORE the render to catch failures before burning render time
- `hyperframes` — the renderer this most commonly gates
- `video-task` — the higher-level pipeline that should always end in a `render-verify` call
