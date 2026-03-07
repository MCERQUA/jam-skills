---
name: remotion-video
description: "Create professional videos using Remotion, React, and TransitionSeries. Full workflow from planning to delivery."
metadata:
  version: 2.0.0
---

# Remotion Video Production

## CRITICAL RULES

- **Use `exec` tool for ALL commands.** Remotion, Chromium, FFmpeg are pre-installed.
- **Use `remotion` directly** (NOT `npx remotion`). Use `pnpm` (NOT `npm`).
- **EVERY video MUST have voiceover** unless user explicitly asks for silent.
- **ALWAYS render with `--crf 18`.** Default CRF produces unwatchable quality.
- **ALWAYS run faststart** (`ffmpeg -movflags +faststart`) before serving.
- **Use TransitionSeries** for scene transitions — NOT manual opacity fades.
- **Use `<Img>` from remotion** for images — NOT HTML `<img>`.
- **Use `<Audio>` from `@remotion/media`** for audio.

## BANNED — Never Use These

- Purple, pink, magenta colors (`#764ba2`, `#667eea`, purple gradients)
- Emoji as visual elements (no emoji icons in scenes, headers, or UI)
- `linear-gradient(135deg, #667eea, #764ba2)` — generic AI gradient
- CSS animations or Tailwind animation classes
- HTML `<img>` elements (use Remotion `<Img>`)
- External CDN scripts

## Professional Color Palette

- Backgrounds: `#0a0a0a`, `#0d1117`, `#1a1a2e`, `#111827`
- Primary accent: `#3b82f6` (blue), `#06b6d4` (cyan)
- Secondary: `#10b981` (emerald), `#f59e0b` (amber)
- Text: `#ffffff`, `#e2e8f0`, `#94a3b8`
- Gradients: `linear-gradient(135deg, #0d1117, #1a1a2e)`, `linear-gradient(135deg, #1e3a5f, #0d1117)`

## Template & Project Setup

Template: `/mnt/shared-skills/remotion-video/template/`

```bash
# Fresh setup (skip if ~/remotion-project exists with node_modules)
cp -r /mnt/shared-skills/remotion-video/template/* ~/remotion-project/
cd ~/remotion-project && pnpm install
```

Required packages (included in template):
- `remotion`, `@remotion/cli`, `@remotion/renderer`
- `@remotion/transitions` — TransitionSeries, fade, slide, wipe
- `@remotion/light-leaks` — LightLeak overlay effects
- `@remotion/media` — Audio component

## Voiceover Generation (Groq TTS)

```bash
mkdir -p ~/remotion-project/public/voiceover

# Generate narration for each scene:
curl -s https://api.groq.com/openai/v1/audio/speech \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"playai-tts","voice":"Fritz-PlayAI","input":"Narration text","response_format":"mp3"}' \
  -o ~/remotion-project/public/voiceover/scene01.mp3

# Measure duration (REQUIRED for frame calculations):
ffprobe -v error -show_entries format=duration -of csv=p=0 ~/remotion-project/public/voiceover/scene01.mp3
# Output: 5.28 → frames = ceil(5.28 * 30) + 30 = 189 (30 extra for transition overlap)
```

**Voices:** Fritz-PlayAI, Arista-PlayAI, Atlas-PlayAI, Basil-PlayAI, Briggs-PlayAI, Calista-PlayAI, Celeste-PlayAI, Cheyenne-PlayAI, Chip-PlayAI, Cillian-PlayAI, Deedee-PlayAI, Eleanor-PlayAI, Gail-PlayAI, Indira-PlayAI, Jennifer-PlayAI, Mamaw-PlayAI, Mason-PlayAI, Mikail-PlayAI, Mitch-PlayAI, Nia-PlayAI, Quinn-PlayAI, Ruby-PlayAI, Thunder-PlayAI

## Composition with TransitionSeries

This is the CORRECT way to build multi-scene videos with transitions:

```tsx
import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { Audio } from "@remotion/media";

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
        <h1 style={{ color: "#ffffff", fontSize: 96, fontWeight: 800, margin: 0 }}>
          {title}
        </h1>
        <p style={{ color: "#94a3b8", fontSize: 32, opacity: subtitleOpacity, marginTop: 20 }}>
          Professional tagline here
        </p>
      </div>
    </AbsoluteFill>
  );
};

// ── Scene with image ────────────────────────────────────────
const ProductScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const imgScale = spring({ frame, fps, config: { damping: 200 } });

  return (
    <AbsoluteFill style={{ background: "#0a0a0a", justifyContent: "center", alignItems: "center" }}>
      <Audio src={staticFile("voiceover/scene02.mp3")} />
      <div style={{ transform: `scale(${imgScale})`, borderRadius: 16, overflow: "hidden", boxShadow: "0 20px 60px rgba(0,0,0,0.5)" }}>
        <Img src={staticFile("images/product-screenshot.png")} style={{ width: 1200, height: "auto" }} />
      </div>
    </AbsoluteFill>
  );
};

// ── Main composition with TransitionSeries ──────────────────
export const PromoVideo: React.FC = () => {
  // Frame counts from ffprobe audio durations: ceil(seconds * 30) + 30
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
<h1 style={{ color: "#fff", fontSize: 120 }}>{count.toLocaleString()}</h1>
```

**Typewriter text:**
```tsx
const text = "Full sentence here";
const chars = Math.floor(interpolate(frame, [0, 60], [0, text.length], { extrapolateRight: "clamp" }));
<p style={{ color: "#e2e8f0", fontSize: 28 }}>{text.slice(0, chars)}</p>
```

**Background music at low volume:**
```tsx
// Place at the composition root level (outside TransitionSeries)
<Audio src={staticFile("music/background.mp3")} volume={0.12} loop />
```

## Render + Optimize + Verify

```bash
# Render
cd ~/remotion-project && remotion render src/index.ts PromoVideo out/video.mp4 --codec h264 --crf 18

# Optimize for web (faststart)
ffmpeg -y -i out/video.mp4 -c copy -movflags +faststart out/video-web.mp4

# Verify
ffprobe -v error -show_entries format=duration,size,bit_rate -show_entries stream=codec_name,bit_rate -of json out/video-web.mp4
# Must show: 2 streams, video bitrate > 2Mbps, correct duration
```

## Deliver

```bash
cp ~/remotion-project/out/video-web.mp4 /app/runtime/canvas-pages/VIDEO_NAME.mp4
```

Create a canvas page with `<video controls autoplay>`, open with `[CANVAS:video-player]`, verify.

## Common Pitfalls

1. **No audio** — `<Audio>` must be INSIDE the `<Sequence>`/`<TransitionSeries.Sequence>` where it should play
2. **Wrong duration** — total composition frames = sum of scene frames MINUS sum of transition frames
3. **Low bitrate** — always use `--crf 18`, never default CRF
4. **Choppy in browser** — always run `ffmpeg -movflags +faststart`
5. **Blank frames** — use Remotion `<Img>` not HTML `<img>` (Img waits for load)
6. **Purple/emoji defaults** — BANNED. Use professional blue/cyan/white palette
