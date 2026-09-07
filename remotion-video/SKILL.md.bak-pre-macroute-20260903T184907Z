---
name: remotion-video
description: "Create professional videos using Remotion, React, and TransitionSeries. Full workflow from planning to delivery."
metadata:
  version: 3.0.0
---

# Remotion Video Production

## CRITICAL RULES

- **Use `exec` tool for ALL commands.** Remotion, Chromium, FFmpeg are pre-installed.
- **Use `npx remotion`** (NOT global `remotion`). Global CLI has React 19 which crashes. Use `pnpm` (NOT `npm`).
- **EVERY video MUST have voiceover** unless user explicitly asks for silent.
- **ALWAYS render with `--crf 18`.** Default CRF produces unwatchable quality.
- **ALWAYS run faststart** (`ffmpeg -movflags +faststart`) before serving.
- **Use TransitionSeries** for scene transitions — NOT manual opacity fades.
- **Use `<Img>` from remotion** for images — NOT HTML `<img>`.
- **Use `<Audio>` from `@remotion/media`** for audio.
- **Use Google Fonts** via `@remotion/google-fonts` — NEVER use system font defaults.

## BANNED — Never Use These

- Purple, pink, magenta colors (`#764ba2`, `#667eea`, purple gradients)
- Emoji as visual elements (no emoji icons in scenes, headers, or UI)
- `linear-gradient(135deg, #667eea, #764ba2)` — generic AI gradient
- CSS animations or Tailwind animation classes
- HTML `<img>` elements (use Remotion `<Img>`)
- External CDN scripts
- System default fonts (DejaVu, Arial fallbacks) — always load a Google Font

## Professional Color Palette

- Backgrounds: `#0a0a0a`, `#0d1117`, `#1a1a2e`, `#111827`
- Primary accent: `#3b82f6` (blue), `#06b6d4` (cyan)
- Secondary: `#10b981` (emerald), `#f59e0b` (amber)
- Text: `#ffffff`, `#e2e8f0`, `#94a3b8`
- Gradients: `linear-gradient(135deg, #0d1117, #1a1a2e)`, `linear-gradient(135deg, #1e3a5f, #0d1117)`

## Template & Project Setup

Template: `~/remotion-project/` (pre-installed with node_modules)

```bash
# Template is pre-installed. If missing or broken, restore from shared:
cp -r /mnt/shared-skills/remotion-video/template/* ~/remotion-project/
cd ~/remotion-project && pnpm install
```

> **Browser is pre-configured.** `PUPPETEER_EXECUTABLE_PATH` is set in the container environment. Do NOT run `remotion browser ensure` or `npx puppeteer browsers install`.

### Installed Packages

**Core:** `remotion`, `@remotion/cli`, `@remotion/renderer`, `@remotion/media`
**Transitions:** `@remotion/transitions` (fade, slide, wipe, flip, clockWipe), `@remotion/light-leaks`
**Typography:** `@remotion/google-fonts` (1500+ fonts), `@remotion/layout-utils` (measureText)
**Graphics:** `@remotion/shapes` (SVG shapes), `@remotion/paths` (path animation/morphing)
**Effects:** `@remotion/noise` (Perlin noise), `@remotion/motion-blur` (Trail, CameraMotionBlur)
**Media:** `@remotion/lottie` + `lottie-web` (Lottie animations), `@remotion/gif` (animated GIFs)
**Captions:** `@remotion/captions` (TikTok-style word-by-word subtitles)

---

## Google Fonts (ALWAYS USE)

Every video must use proper typography. Never rely on system fonts.

```tsx
// Import at top of your composition file:
import { loadFont } from "@remotion/google-fonts/Inter";
import { loadFont as loadDisplay } from "@remotion/google-fonts/Montserrat";

// Call once at module level:
const { fontFamily: inter } = loadFont("normal", { weights: ["400", "600"], subsets: ["latin"] });
const { fontFamily: montserrat } = loadDisplay("normal", { weights: ["700", "800", "900"], subsets: ["latin"] });

// Use in styles:
<h1 style={{ fontFamily: montserrat, fontSize: 96, fontWeight: 800 }}>Title</h1>
<p style={{ fontFamily: inter, fontSize: 28, fontWeight: 400 }}>Body text</p>
```

**Recommended font pairings:**
- **Bold headers + clean body:** Montserrat (800) + Inter (400/600)
- **Modern tech:** Space Grotesk (700) + DM Sans (400)
- **Premium/luxury:** Playfair Display (700) + Lato (300/400)
- **Startup/SaaS:** Plus Jakarta Sans (700) + Inter (400)
- **Bold statement:** Bebas Neue (400) + Source Sans 3 (400)

---

## Voiceover Generation (Groq Orpheus TTS)

```bash
mkdir -p ~/remotion-project/public/voiceover

# Generate narration for each scene (wav only, then convert to mp3):
curl -s https://api.groq.com/openai/v1/audio/speech \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"canopylabs/orpheus-v1-english","voice":"troy","input":"[professionally] Narration text here","response_format":"wav"}' \
  -o /tmp/scene01.wav

# Convert to mp3 (Orpheus only outputs wav):
ffmpeg -y -i /tmp/scene01.wav -codec:a libmp3lame -q:a 2 ~/remotion-project/public/voiceover/scene01.mp3

# Measure duration (REQUIRED for frame calculations):
ffprobe -v error -show_entries format=duration -of csv=p=0 ~/remotion-project/public/voiceover/scene01.mp3
# Output: 5.28 → frames = ceil(5.28 * 30) + 30 = 189 (30 extra for transition overlap)
```

**Voices:** `troy` (male), `austin` (male), `daniel` (male), `autumn` (female), `diana` (female), `hannah` (female)

**Vocal directions** — add `[tag]` in the input text to control expression:
- Tone: `[cheerful]`, `[friendly]`, `[warm]`, `[sarcastic]`, `[deadpan]`
- Professional: `[professionally]`, `[authoritatively]`, `[confidently]`
- Performance: `[whisper]`, `[excited]`, `[dramatic]`, `[breathy]`, `[singsong]`
- Use 1-2 word descriptors. Fewer = natural, more = expressive/acted.

---

## SVG Shapes & Path Animation

### Shapes — badges, icons, decorative elements

```tsx
import { Triangle, Star, Circle, Rect, Pie, Polygon, Ellipse } from "@remotion/shapes";

// Animated star badge
<Star points={5} innerRadius={40} outerRadius={80}
  fill="#f59e0b" stroke="#ffffff" strokeWidth={2}
  style={{ transform: `scale(${spring({ frame, fps })})` }} />

// Progress pie chart
<Pie radius={60} progress={interpolate(frame, [0, 90], [0, 0.75], { extrapolateRight: "clamp" })}
  fill="#3b82f6" />
```

### Path Animation — logo reveals, line draws, morphing

```tsx
import { evolvePath, interpolatePath, getLength } from "@remotion/paths";

// Draw-on animation (line drawing itself)
const pathData = "M 10 10 L 200 10 L 200 200"; // any SVG path
const evolution = interpolate(frame, [0, 60], [0, 1], { extrapolateRight: "clamp" });
const partialPath = evolvePath(evolution, pathData);

<svg viewBox="0 0 220 220">
  <path d={partialPath} stroke="#3b82f6" strokeWidth={3} fill="none" />
</svg>

// Morph between two shapes
const morphed = interpolatePath(
  interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" }),
  circlePath,
  starPath,
);
<svg><path d={morphed} fill="#06b6d4" /></svg>
```

---

## Perlin Noise — Organic Animations

```tsx
import { noise2D, noise3D } from "@remotion/noise";

// Floating particles
const PARTICLES = Array.from({ length: 20 }, (_, i) => i);
{PARTICLES.map((i) => {
  const x = noise2D("x" + i, frame / 100, 0) * 960 + 960;
  const y = noise2D("y" + i, 0, frame / 100) * 540 + 540;
  const size = noise2D("s" + i, frame / 50, i) * 4 + 6;
  return <circle key={i} cx={x} cy={y} r={size} fill="rgba(59, 130, 246, 0.3)" />;
})}

// Wavy background line
const points = Array.from({ length: 100 }, (_, i) => {
  const x = (i / 99) * 1920;
  const y = 540 + noise2D("wave", i / 20, frame / 60) * 100;
  return `${x},${y}`;
}).join(" ");
<svg><polyline points={points} stroke="#06b6d4" strokeWidth={2} fill="none" /></svg>
```

---

## Motion Blur — Cinematic Feel

```tsx
import { Trail, CameraMotionBlur } from "@remotion/motion-blur";

// Trail effect (afterimage on moving elements)
<Trail layers={6} lagInFrames={0.2}>
  <MovingElement />  {/* useCurrentFrame() MUST be inside this component */}
</Trail>

// Camera motion blur (whole scene blur during fast movement)
<CameraMotionBlur samples={10} shutterAngle={180}>
  <FastMovingScene />
</CameraMotionBlur>
```

> `useCurrentFrame()` must be called INSIDE the wrapped component, not outside.

---

## Lottie Animations

Free animations from [LottieFiles.com](https://lottiefiles.com). Download `.json` files to `public/lottie/`.

```tsx
import { Lottie, getLottieMetadata } from "@remotion/lottie";
import { staticFile } from "remotion";
import animationData from "../public/lottie/checkmark.json";

// Get duration info
const metadata = getLottieMetadata(animationData);
// metadata.durationInSeconds, metadata.fps

<Lottie
  animationData={animationData}
  style={{ width: 300, height: 300 }}
  playbackRate={1}
/>
```

Good for: animated icons, loading spinners, success checkmarks, decorative flourishes.

---

## Animated GIFs

```tsx
import { Gif } from "@remotion/gif";
import { staticFile } from "remotion";

<Gif src={staticFile("gifs/reaction.gif")} width={400} height={400} fit="contain" />
```

---

## Captions — TikTok-Style Subtitles

```tsx
import { createTikTokStyleCaptions } from "@remotion/captions";

// Word-level transcript (from voiceover generation or manual)
const transcript = [
  { text: "Welcome", startMs: 0, endMs: 500 },
  { text: "to", startMs: 500, endMs: 650 },
  { text: "our", startMs: 650, endMs: 800 },
  { text: "business", startMs: 800, endMs: 1400 },
];

// Generate pages of highlighted captions
const { pages } = createTikTokStyleCaptions({ combineTokensWithinMilliseconds: 800 });

// Render current page with highlighted active word
const currentPage = pages.find(p => p.startMs <= currentTimeMs && currentTimeMs < p.endMs);
```

Captions make videos accessible and perform better on social media (85% of Facebook videos watched without sound).

---

## Layout Utils — Dynamic Text Sizing

```tsx
import { measureText, fitText } from "@remotion/layout-utils";

// Measure text to prevent overflow
const { width, height } = measureText({
  text: "Dynamic Title Here",
  fontFamily: montserrat,
  fontSize: 96,
  fontWeight: "800",
});
// Use width/height to size containers or decide line breaks

// Auto-fit text to container width
const fitted = fitText({
  text: "This title adapts to fit",
  withinWidth: 1600,
  fontFamily: montserrat,
  fontWeight: "800",
});
<h1 style={{ fontFamily: montserrat, fontSize: fitted.fontSize }}>This title adapts to fit</h1>
```

---

## Composition with TransitionSeries

This is the CORRECT way to build multi-scene videos with transitions:

```tsx
import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { Audio } from "@remotion/media";
import { loadFont } from "@remotion/google-fonts/Montserrat";
import { loadFont as loadBody } from "@remotion/google-fonts/Inter";

const { fontFamily: heading } = loadFont("normal", { weights: ["800"], subsets: ["latin"] });
const { fontFamily: body } = loadBody("normal", { weights: ["400", "600"], subsets: ["latin"] });

// ── Scene component pattern ─────────────────────────────────
const IntroScene: React.FC<{title: string}> = ({ title }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleScale = spring({ frame, fps, config: { damping: 200, stiffness: 100, mass: 0.5 } });
  const subtitleOpacity = interpolate(frame, [20, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{
      background: "linear-gradient(135deg, #0d1117 0%, #1a1a2e 100%)",
      justifyContent: "center",
      alignItems: "center",
    }}>
      <Audio src={staticFile("voiceover/scene01.mp3")} />
      <div style={{ textAlign: "center", transform: `scale(${titleScale})` }}>
        <h1 style={{ fontFamily: heading, color: "#ffffff", fontSize: 96, fontWeight: 800, margin: 0 }}>
          {title}
        </h1>
        <p style={{ fontFamily: body, color: "#94a3b8", fontSize: 32, opacity: subtitleOpacity, marginTop: 20 }}>
          Professional tagline here
        </p>
      </div>
    </AbsoluteFill>
  );
};

// ── Main composition with TransitionSeries ──────────────────
export const PromoVideo: React.FC = () => {
  const TRANSITION_FRAMES = 15;

  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0a0a" }}>
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={189}>
          <IntroScene title="Product Name" />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: TRANSITION_FRAMES })}
        />

        <TransitionSeries.Sequence durationInFrames={210}>
          <ProductScene />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={slide({ direction: "from-right" })}
          timing={linearTiming({ durationInFrames: TRANSITION_FRAMES })}
        />

        <TransitionSeries.Sequence durationInFrames={150}>
          <OutroScene />
        </TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
```

**Root.tsx — register composition with CORRECT total duration:**
```tsx
import { Composition } from "remotion";
import { PromoVideo } from "./PromoVideo";

// Total = sum of scene frames - sum of transition frames
// (189 + 210 + 150) - (15 + 15) = 519
export const RemotionRoot: React.FC = () => (
  <Composition
    id="PromoVideo"
    component={PromoVideo}
    durationInFrames={519}
    fps={30}
    width={1920}
    height={1080}
  />
);
```

## Available Transitions

```tsx
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";       // directions: "from-left", "from-right", "from-top", "from-bottom"
import { wipe } from "@remotion/transitions/wipe";
import { flip } from "@remotion/transitions/flip";
import { clockWipe } from "@remotion/transitions/clock-wipe";
```

## Light Leak Overlays

Add cinematic light leak effects between scenes:

```tsx
import { LightLeak } from "@remotion/light-leaks";

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={150}>
    <SceneA />
  </TransitionSeries.Sequence>
  <TransitionSeries.Overlay durationInFrames={30}>
    <LightLeak seed={3} hueShift={200} />  {/* Blue-ish tint */}
  </TransitionSeries.Overlay>
  <TransitionSeries.Sequence durationInFrames={150}>
    <SceneB />
  </TransitionSeries.Sequence>
</TransitionSeries>
```

Note: An overlay cannot be adjacent to a transition or another overlay.

## Animation Patterns

**Slide in from left:**
```tsx
const x = interpolate(frame, [0, 20], [-1920, 0], { extrapolateRight: "clamp" });
<div style={{ transform: `translateX(${x}px)` }}>Content</div>
```

**Scale bounce:**
```tsx
const scale = spring({ frame, fps, config: { damping: 10, stiffness: 100, mass: 0.5 } });
<div style={{ transform: `scale(${scale})` }}>Content</div>
```

**Animated counter:**
```tsx
const count = Math.round(interpolate(frame, [0, 60], [0, 1000], { extrapolateRight: "clamp" }));
<h1 style={{ fontFamily: heading, color: "#fff", fontSize: 120 }}>{count.toLocaleString()}</h1>
```

**Typewriter text:**
```tsx
const text = "Full sentence here";
const chars = Math.floor(interpolate(frame, [0, 60], [0, text.length], { extrapolateRight: "clamp" }));
<p style={{ fontFamily: body, color: "#e2e8f0", fontSize: 28 }}>{text.slice(0, chars)}</p>
```

**Background music at low volume:**
```tsx
// Place at the composition root level (outside TransitionSeries)
<Audio src={staticFile("music/background.mp3")} volume={0.12} loop />
```

---

## Render + Post-Process + Deliver

### Basic Render
```bash
cd ~/remotion-project && npx remotion render src/index.ts PromoVideo out/video.mp4 --codec h264 --crf 18
```

### Post-Processing (FFmpeg filters — pick what fits)

```bash
# REQUIRED: Web optimization (faststart for streaming)
ffmpeg -y -i out/video.mp4 -c copy -movflags +faststart out/video-web.mp4

# Cinematic letterbox (2.35:1 aspect ratio — black bars top/bottom)
ffmpeg -y -i out/video.mp4 -vf "pad=iw:iw/2.35:0:(oh-ih)/2:black" -c:a copy out/video-letterbox.mp4

# Subtle film grain (organic, professional feel)
ffmpeg -y -i out/video.mp4 -vf "noise=c0s=8:c0f=t+u" -c:a copy out/video-grain.mp4

# Vignette (dark edges, draws eye to center)
ffmpeg -y -i out/video.mp4 -vf "vignette=PI/4" -c:a copy out/video-vignette.mp4

# Boost saturation + slight contrast (punchier colors)
ffmpeg -y -i out/video.mp4 -vf "eq=saturation=1.2:contrast=1.05" -c:a copy out/video-vivid.mp4

# FULL CINEMATIC CHAIN (grain + vignette + slight desat + faststart)
ffmpeg -y -i out/video.mp4 \
  -vf "noise=c0s=8:c0f=t+u,vignette=PI/5,eq=saturation=0.95:contrast=1.05" \
  -c:a copy -movflags +faststart out/video-cinema.mp4
```

### Verify Quality
```bash
ffprobe -v error -show_entries format=duration,size,bit_rate -show_entries stream=codec_name,bit_rate -of json out/video-web.mp4
# Must show: 2 streams, video bitrate > 2Mbps, correct duration
```

### Deliver
```bash
cp ~/remotion-project/out/video-web.mp4 /app/runtime/canvas-pages/VIDEO_NAME.mp4
```

Create a canvas page with `<video controls autoplay>`, open with `[CANVAS:video-player]`, verify.

---

## Common Pitfalls

1. **No audio** — `<Audio>` must be INSIDE the `<Sequence>`/`<TransitionSeries.Sequence>` where it should play
2. **Wrong duration** — total composition frames = sum of scene frames MINUS sum of transition frames
3. **Low bitrate** — always use `--crf 18`, never default CRF
4. **Choppy in browser** — always run `ffmpeg -movflags +faststart`
5. **Blank frames** — use Remotion `<Img>` not HTML `<img>` (Img waits for load)
6. **HTML `<video>` tag** — use Remotion `<Video>` from `remotion` (`import { Video } from "remotion"`). HTML video tags do NOT render in Remotion.
7. **Purple/emoji defaults** — BANNED. Use professional blue/cyan/white palette
8. **System fonts** — BANNED. Always `import { loadFont } from "@remotion/google-fonts/FontName"`
9. **Motion blur outside** — `useCurrentFrame()` must be INSIDE `<Trail>` or `<CameraMotionBlur>` children
10. **Framer Motion** — DO NOT use `motion.dev` or `framer-motion`. Incompatible with Remotion's frame system. Use `spring()` and `interpolate()` instead.
11. **Duplicate `<Audio>`** — place `<Audio>` in ONE scene only (usually the root composition), NOT in every scene. Multiple `<Audio>` tags = overlapping playback.

---

## Downloading Media from Slack

When the user shares files (images, videos, logos) in Slack, download them using the bot token:

```bash
# List recent files shared in a channel:
curl -s -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  "https://slack.com/api/files.list?channel=$SLACK_CHANNEL_COMPANY&count=20" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
for f in data.get('files', []):
    print(f'{f[\"name\"]}|{f[\"mimetype\"]}|{f[\"url_private_download\"]}')
"

# Download a file:
curl -s -o ~/remotion-project/public/FILENAME \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  "FILE_URL_FROM_ABOVE"
```

**Rules:**
- Download directly to `~/remotion-project/public/` so Remotion can access via `staticFile()`
- Convert HEIC to JPG: `convert input.heic -quality 90 -auto-orient output.jpg`
- Check video specs: `ffprobe -v quiet -print_format json -show_streams INPUT.mp4`
- Match video dimensions in your Remotion composition (common: 1920x1080 or 720x720)

---

## End-to-End Video Workflow (Slack → Render → Deliver → Post)

When a user asks you to make a video from Slack content, follow these steps IN ORDER:

### Step 1: Gather assets
- Download all images/videos/logos from Slack (see above)
- Save to `~/remotion-project/public/` with descriptive names
- Check dimensions: `identify image.png` or `ffprobe video.mp4`

### Step 2: Generate voiceover
```bash
mkdir -p ~/remotion-project/public/voiceover
curl -s https://api.groq.com/openai/v1/audio/speech \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"canopylabs/orpheus-v1-english","voice":"troy","input":"[professionally] Your narration text","response_format":"wav"}' \
  -o /tmp/narration.wav
ffmpeg -y -i /tmp/narration.wav -codec:a libmp3lame -q:a 2 ~/remotion-project/public/voiceover/narration.mp3
# Measure duration for frame calculations:
ffprobe -v error -show_entries format=duration -of csv=p=0 ~/remotion-project/public/voiceover/narration.mp3
```

### Step 3: Write composition
- Create `~/remotion-project/src/MyVideo.tsx` with your scenes
- Update `~/remotion-project/src/Root.tsx` to register it (keep HelloWorld as fallback)
- Use `<Img>` for images, `<Video>` for video, `<Audio>` for audio (all from `remotion`)
- Use TransitionSeries for scene transitions
- Calculate total frames: sum of scene frames minus transition frames

### Step 4: Render (BACKGROUND — takes 2-5 minutes)
```bash
cd ~/remotion-project && npx remotion render src/index.ts MyVideo out/video.mp4 --codec h264 --crf 18
```
Run with `background: true`. Tell the user "Video is rendering, I'll let you know when it's done." Wait for the `notifyOnExit` notification.

### Step 5: Post-process + deliver
```bash
cd ~/remotion-project
# Web optimize:
ffmpeg -y -i out/video.mp4 -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 128k out/video-web.mp4
# Copy to canvas:
mkdir -p /app/runtime/canvas-pages/video
cp out/video-web.mp4 /app/runtime/canvas-pages/video/my-video.mp4
```

### Step 6: Show on canvas page
Write an HTML page to `/app/runtime/canvas-pages/video-player.html`:
```html
<video controls autoplay playsinline preload="auto" style="width:100%;max-height:80vh;">
  <source src="/pages/video/my-video.mp4" type="video/mp4">
</video>
<a href="/pages/video/my-video.mp4" download style="...">Download Video</a>
```
Open with `[CANVAS:video-player]`. ALSO copy to uploads for a shareable URL:
```bash
curl -s -X POST http://openvoiceui:5001/api/upload -F "file=@/home/node/remotion-project/out/video-web.mp4"
```
The upload API returns a `/uploads/<uuid>.mp4` URL that works outside the canvas.

### Step 7: Post to Slack (if requested)
```bash
curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"channel\": \"$SLACK_CHANNEL_COMPANY\", \"text\": \"Here's the video: https://DOMAIN/uploads/UUID.mp4\"}"
```
Use the domain from your `$DOMAIN` environment variable and the upload URL from Step 6.
