---
name: hyperframes
description: "HTML-to-video rendering via HyperFrames CLI — plain HTML + CSS + GSAP into frame-accurate MP4/MOV/WebM; built for agents, no React required. TRIGGER: 'hyperframes' or rendering a video composition from HTML. React-based video → remotion-video; animating a still image → wan-video."
metadata:
  version: 1.0.0
---

# HyperFrames — HTML to Video Rendering

HyperFrames turns plain HTML compositions into frame-accurate video (MP4, MOV, WebM). It uses headless Chrome's `beginFrame` API to seek to each frame precisely, then pipes the PNG sequence through FFmpeg. **No React. No DSL. Just HTML.**

`hyperframes` is installed globally on this system. Run it directly:
```bash
hyperframes render --output output.mp4
hyperframes preview
hyperframes lint
```

---

## THE GOLDEN RULE FOR GOOD VIDEOS

**1. Use GSAP for all animations — paused timeline, registered on `window.__timelines`.**  
**2. Always set `data-composition-id`, `data-width`, `data-height` on the root div.**  
**3. Every animated element needs `class="clip"`, `data-start`, `data-duration`, `data-track-index`.**  
**4. Render at `--quality standard` (CRF 18) — never ship draft quality.**  
**5. Run `hyperframes lint` before every render.**  

---

## CLI COMMANDS

```bash
# Init a new project
hyperframes init my-video                        # blank scaffold
hyperframes init my-video --example warm-grain   # from template

# Development
hyperframes preview                              # hot-reload at localhost:3002
hyperframes preview --port 3002

# Validate before rendering
hyperframes lint                                 # check composition structure
hyperframes inspect                              # audit text overflow / clipping
hyperframes snapshot --frame-number 45           # capture frame 45 as PNG

# Render
hyperframes render --output output.mp4
hyperframes render --output output.mp4 --quality standard   # DEFAULT — use this
hyperframes render --output draft.mp4 --quality draft       # fast dev check only
hyperframes render --output final.mp4 --quality high        # archival
hyperframes render --output output.mp4 --fps 30             # 24 | 30 | 60
hyperframes render --output output.mp4 --workers 2          # parallel Chrome instances
hyperframes render --output transparent.mov --format mov    # ProRes 4444 with alpha
hyperframes render --output web.webm --format webm          # VP9 for web

# Audio / TTS utilities
hyperframes tts "Hello world, this is your AI narrator."    # on-device TTS (Kokoro-82M, no API key)
hyperframes transcribe audio.mp3                            # word-level timestamps → SRT/VTT

# System check
hyperframes doctor                               # verify Node, FFmpeg, Chrome
hyperframes --version
```

### Quality Settings (pick one)

| Flag | CRF | Use For |
|------|-----|---------|
| `--quality draft` | 28 | Fast iteration, not for delivery |
| `--quality standard` | 18 | **Production default — use this** |
| `--quality high` | 15 | Final archival delivery |
| `--crf 18` | custom | Fine-grained control |

### Approximate File Sizes (1080p 30fps)
- Draft: ~30 MB/min
- Standard: ~100 MB/min
- High: ~150 MB/min
- ProRes MOV (alpha): ~500 MB+/min

---

## COMPOSITION STRUCTURE

Every composition is a single HTML file. Structure:

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #000; overflow: hidden; }
  </style>
</head>
<body>

  <!-- ROOT: required, sets video dimensions -->
  <div
    id="root"
    data-composition-id="my-video"
    data-width="1920"
    data-height="1080"
  >

    <!-- CLIP: every timed element needs these 4 attributes -->
    <div
      class="clip"
      data-start="0"
      data-duration="3"
      data-track-index="0"
      style="position:absolute; width:100%; height:100%; background:#1a1a2e;"
    ></div>

    <!-- Text appearing at 1s, lasting 2s, on layer 1 -->
    <h1
      class="clip"
      data-start="1"
      data-duration="2"
      data-track-index="1"
      style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
             font-size:72px; color:#fff; opacity:0;"
    >Hello World</h1>

    <!-- Video clip -->
    <video
      class="clip"
      data-start="3"
      data-duration="5"
      data-track-index="0"
      style="position:absolute; width:100%; height:100%; object-fit:cover;"
      muted
    >
      <source src="./assets/intro.mp4" type="video/mp4">
    </video>

    <!-- Audio track (background music) -->
    <audio
      class="clip"
      data-start="0"
      data-duration="10"
      data-track-index="0"
      data-volume="0.6"
    >
      <source src="./assets/music.mp3" type="audio/mpeg">
    </audio>

  </div><!-- end #root -->

  <!-- GSAP (load from CDN or local) -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
  <script>
    // CRITICAL: timeline MUST be paused: true
    const tl = gsap.timeline({ paused: true });

    tl.to('h1', { duration: 0.5, opacity: 1, y: 0 }, 1.0)
      .to('h1', { duration: 0.3, opacity: 0 }, 2.7);

    // CRITICAL: register on window.__timelines with the composition ID
    window.__timelines = window.__timelines || {};
    window.__timelines['my-video'] = tl;
  </script>

</body>
</html>
```

---

## DATA ATTRIBUTES REFERENCE

### Root Element (`#root`)
| Attribute | Required | Description |
|-----------|----------|-------------|
| `data-composition-id` | ✅ | Unique ID — must match `window.__timelines` key |
| `data-width` | ✅ | Output width in pixels |
| `data-height` | ✅ | Output height in pixels |

### Clip Elements (`.clip`)
| Attribute | Required | Description |
|-----------|----------|-------------|
| `class="clip"` | ✅ | Marks element as timed |
| `data-start` | ✅ | Start time in seconds (float OK: `2.5`) |
| `data-duration` | ✅ | Duration in seconds (float OK: `1.5`) |
| `data-track-index` | ✅ | Layer/z-index (0 = bottom, higher = on top) |
| `data-volume` | Audio only | Volume multiplier 0.0–1.0 |

---

## GSAP ANIMATION (CRITICAL RULES)

GSAP is the primary animation library. Follow these rules exactly or the render will be wrong:

```javascript
// ✅ CORRECT — paused: true is mandatory
const tl = gsap.timeline({ paused: true });

// ✅ CORRECT — second arg is the insertion time on the timeline
tl.to('.title', { duration: 0.6, opacity: 1, y: 0 }, 0)          // starts at t=0
  .to('.subtitle', { duration: 0.8, opacity: 1, x: 0 }, 0.3)     // starts at t=0.3s
  .to('.title', { duration: 0.4, opacity: 0 }, 2.5);              // fade out at t=2.5s

// ✅ CORRECT — register with composition ID
window.__timelines = window.__timelines || {};
window.__timelines['my-video'] = tl;

// ❌ WRONG — wall-clock based (setTimeout, requestAnimationFrame, Date.now())
// These do NOT work in frame-seek rendering. Only use GSAP timeline or frame adapters.

// ❌ WRONG — timeline not paused
const tl = gsap.timeline(); // plays immediately, renderer can't seek
```

### GSAP Eases for Good-Looking Video
```javascript
// Smooth entries
gsap.to(el, { duration: 0.5, opacity: 1, y: 0, ease: 'power2.out' })

// Bouncy
gsap.to(el, { duration: 0.8, scale: 1, ease: 'back.out(1.7)' })

// Smooth exits
gsap.to(el, { duration: 0.4, opacity: 0, y: -20, ease: 'power2.in' })

// Text letter stagger
gsap.from('.letter', { duration: 0.4, opacity: 0, y: 30, stagger: 0.05, ease: 'power2.out' })
```

---

## COMMON RESOLUTIONS

```
1920x1080  — Standard 16:9 landscape (YouTube, web, streaming)
1280x720   — HD 16:9 (smaller files, still good quality)
1080x1920  — Portrait 9:16 (TikTok, Instagram Reels, YouTube Shorts)
1080x1080  — Square (Instagram feed)
3840x2160  — 4K (only if needed — large files, slow render)
```

---

## WORKFLOW FOR PRODUCING A GOOD VIDEO

Follow this order every time:

### 1. Plan the composition
Before writing HTML, define:
- Total duration (seconds)
- Resolution + frame rate
- Scenes and timing (write it out: Scene 1: 0-3s, Scene 2: 3-8s, etc.)
- Audio: background music? voiceover? (use `hyperframes tts` for VO)

### 2. Init project
```bash
cd ~/workspace/Videos
hyperframes init my-project-name
cd my-project-name
```

### 3. Write the composition HTML
- Put all assets in `./assets/`
- One `#root` div with `data-composition-id`, `data-width`, `data-height`
- Every element that appears/disappears = `class="clip"` with timing attributes
- GSAP timeline for all motion — paused, registered on `window.__timelines`

### 4. Preview & iterate
```bash
hyperframes preview
# Opens at localhost:3002 with hot-reload
# Scrub through timeline to check timing
```

### 5. Lint before rendering
```bash
hyperframes lint
# Fix any warnings about overlapping clips, missing attributes, etc.
```

### 6. Snapshot key frames
```bash
hyperframes snapshot --frame-number 0 --output frame-0.png    # first frame
hyperframes snapshot --frame-number 30 --output frame-1s.png  # 1s in (at 30fps)
```

### 7. Draft render (quick check)
```bash
hyperframes render --output draft.mp4 --quality draft --workers 1
# Review draft.mp4 before committing to full render
```

### 8. Final render
```bash
hyperframes render --output final.mp4 --quality standard --fps 30
# Save output to user's uploads directory
cp final.mp4 /home/node/.openclaw/workspace/uploads/$(date +%Y%m%d-%H%M%S)-video.mp4
```

---

## SAVING OUTPUT (IMPORTANT)

All rendered video is valuable. Save immediately after render:

```bash
# Save to workspace uploads (accessible via canvas)
OUTPUT_PATH="/home/node/.openclaw/workspace/uploads/$(date +%Y%m%d-%H%M%S)-${SLUG}.mp4"
hyperframes render --output "$OUTPUT_PATH" --quality standard

# Notify user of the saved path
echo "Video saved: $OUTPUT_PATH"
```

Never leave rendered video only in the project temp directory — it may get cleaned up.

---

## AUDIO & TTS

### Built-in TTS (no API key needed)
```bash
# Generate voiceover audio
hyperframes tts "Welcome to the product demo. Here's what we built." --output voiceover.mp3

# Then reference in composition:
# <audio class="clip" data-start="0" data-duration="15" data-track-index="0" data-volume="1.0">
#   <source src="./assets/voiceover.mp3">
# </audio>
```

### Audio Mixing Tips
- Background music: `data-volume="0.3"` to `data-volume="0.5"`
- Voiceover: `data-volume="1.0"`
- SFX: `data-volume="0.6"` to `data-volume="0.8"`
- Only `data-volume` attribute for mixing — advanced EQ requires FFmpeg post-processing
- Use `.mp3` or `.wav` — avoid `.ogg` (inconsistent Chrome support)

### Transcription → Captions
```bash
hyperframes transcribe voiceover.mp3 --output captions.srt
# Use SRT to drive word-by-word text animations in the composition
```

---

## BUILT-IN TEMPLATES

Use `--example` to scaffold from a production-quality starting point:

```bash
hyperframes init my-video --example warm-grain      # lifestyle, cream aesthetic
hyperframes init my-video --example play-mode       # elastic social media style
hyperframes init my-video --example swiss-grid      # clean corporate
hyperframes init my-video --example kinetic-type    # dramatic typography for promos
hyperframes init my-video --example decision-tree   # flowchart/tutorial style
hyperframes init my-video --example product-promo   # multi-scene product showcase
hyperframes init my-video --example nyt-graph       # editorial data visualization
hyperframes init my-video --example vignelli        # bold typography, 1080x1920 portrait
```

These templates include working GSAP animations and proper structure. Start from one when the style fits the brief rather than building from scratch.

---

## MULTI-SCENE ARCHITECTURE (LONG VIDEOS)

For videos over 30 seconds, split into sub-compositions:

```
my-video/
├── index.html          ← root, stitches scenes together
├── scenes/
│   ├── scene-01.html   ← 0-8s: intro
│   ├── scene-02.html   ← 8-20s: demo
│   ├── scene-03.html   ← 20-30s: CTA
├── assets/
│   ├── music.mp3
│   ├── voiceover.mp3
│   └── logo.svg
└── package.json
```

Each scene is a standalone composition. Root composition stitches them by referencing sub-compositions as clips with appropriate `data-start` offsets.

---

## TROUBLESHOOTING

**Preview not updating:** Check file paths — assets must be relative to the HTML file, not absolute.

**Audio not playing in render:** Ensure `<audio>` has `class="clip"` and timing attributes. Use `.mp3` format.

**Animation not working:** GSAP timeline must have `{ paused: true }` and be registered on `window.__timelines['composition-id']`.

**Black frames at start/end:** Add a 0.1s buffer — start clip at `data-start="0.1"` instead of `0`.

**Render crashes with many workers:** Drop to `--workers 1` for stability. Useful on video-heavy compositions.

**Text looks wrong:** Add `font-display: block` and load fonts before rendering. System fonts are safest; web fonts may not load in headless Chrome.

**FFmpeg not found:** Run `hyperframes doctor` to diagnose. FFmpeg is pre-installed on this system at `/usr/bin/ffmpeg`.

---

## ENVIRONMENT

On this JamBot system:
- `hyperframes` binary: `/usr/local/share/pnpm/hyperframes`
- FFmpeg: `/usr/bin/ffmpeg` (v5.1.8)
- Chrome: bundled via puppeteer at `/usr/local/share/pnpm/global/5/node_modules/puppeteer/.local-chromium/`
- Working dir for video projects: `~/workspace/Videos/`
- Upload output to: `~/workspace/uploads/` (served at `/uploads/` on user's domain)

Run `hyperframes doctor` first if anything seems off.
