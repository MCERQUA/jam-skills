---
name: remotion-best-practices
description: Complete Remotion video creation framework - React-based programmatic video. This contains FULL usage instructions, not just best practices.
metadata:
  tags: remotion, video, react, animation, composition, rendering
---

## What is Remotion

Remotion is a framework for creating videos programmatically using React. You write React components that are rendered frame-by-frame into MP4/WebM/GIF videos. Remotion is pre-installed at `~/remotion-project/`. Always use `npx remotion` from within that project directory (NOT global `remotion`). Use `pnpm` (not `npm`) for any package management.

## IMPORTANT: Loading Detailed Rules

This skill contains **37 detailed rule files** in the `./rules/` subdirectory with full code examples. **When working on Remotion code, you MUST read the relevant rule files** — they contain the actual API usage, code examples, and patterns.

To load a rule: read the file at `skills/remotion-best-practices/rules/<topic>.md`

## Quick Start — Core Patterns

### Project Structure
```
src/
  Root.tsx          ← Register all compositions here
  MyVideo.tsx       ← Your video component
  index.ts          ← Entry point
public/             ← Static assets (images, videos, audio, fonts)
```

### Define a Composition (src/Root.tsx)
```tsx
import { Composition } from "remotion";
import { MyVideo } from "./MyVideo";

export const RemotionRoot = () => {
  return (
    <Composition
      id="MyVideo"
      component={MyVideo}
      durationInFrames={150}  // 5 seconds at 30fps
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
```

### Animate with useCurrentFrame (NOT CSS animations)
```tsx
import { useCurrentFrame, useVideoConfig, interpolate, AbsoluteFill } from "remotion";

export const MyVideo = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame, [0, 2 * fps], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#000", opacity }}>
      <h1 style={{ color: "white", fontSize: 80 }}>Hello World</h1>
    </AbsoluteFill>
  );
};
```

**CRITICAL RULES:**
- ALL animations MUST use `useCurrentFrame()` — CSS transitions/animations are FORBIDDEN
- Tailwind animation classes are FORBIDDEN — they won't render correctly
- Use `interpolate()` for value mapping, `spring()` for physics-based motion
- Use `<AbsoluteFill>` as the root layout component
- Use `staticFile("filename")` to reference files in `public/`

### Render a Video
```bash
cd ~/remotion-project && npx remotion render src/index.ts MyVideo output.mp4
```

### Render a Still Image
```bash
cd ~/remotion-project && npx remotion still src/index.ts MyThumbnail output.png
```

**IMPORTANT:** Always use `npx remotion` from within `~/remotion-project/` — NEVER use global `remotion` directly. The global install has React 19 which conflicts with the project's React 18. Using `npx` runs the project-local CLI with the correct React version.

## ⚠️ CRITICAL: Working Directory & Rendering

### Working Directory (MANDATORY)

**You MUST set `workdir` to the project directory** when calling `remotion render` or `remotion still`. Remotion resolves the entry point (`src/index.ts`) relative to the current directory. If you run from the workspace root, Remotion will fail with "No entry point specified".

**WRONG** (fails — src/index.ts not found from workspace root, and global `remotion` has React 19 conflict):
```json
{"tool": "exec", "command": "remotion render src/index.ts MyVideo output.mp4"}
```

**CORRECT** (workdir set to ~/remotion-project, using npx):
```json
{"tool": "exec", "command": "npx remotion render src/index.ts MyVideo output.mp4", "workdir": "/home/node/.openclaw/workspace/remotion-project"}
```

You can also `cd` into the project directory first:
```json
{"tool": "exec", "command": "cd ~/remotion-project && npx remotion render src/index.ts MyVideo output.mp4"}
```

### Rendering is a Long-Running Process

**Video renders take 1-5+ minutes** depending on frame count and complexity. The `exec` tool auto-backgrounds commands after 10 seconds — **DO NOT retry the render command if you get an empty result**.

### Correct Rendering Pattern (MANDATORY)

**Step 1 — Start render with `background: true` and correct `workdir`:**
```json
{"tool": "exec", "command": "npx remotion render src/index.ts MyVideo output.mp4", "workdir": "/home/node/.openclaw/workspace/remotion-project", "background": true}
```
This returns immediately with a `sessionId`. Save it.

**Step 2 — Tell the user and WAIT:**
Tell the user "Your video is rendering — I'll let you know when it's done." Then **stop and wait**. The system has `notifyOnExit` enabled by default — you will automatically receive a system notification when the render process exits. Do NOT poll in a loop.

**Step 3 — On notification, check result:**
When the system notifies you that the background process exited, check `exitCode` (0 = success). If needed, use `process poll` or `process log` to see the final output. Then verify the output file exists and tell the user.

**Optional — Progress check (only if user asks):**
If the user asks for a progress update during rendering, you may poll once:
```json
{"tool": "process", "action": "poll", "sessionId": "<sessionId>"}
```
This shows lines like `Rendered 450/900 frames`. Do NOT poll in a loop — only poll when the user asks.

### Rules for Rendering
- **ALWAYS** set `workdir` to the project directory (where `src/index.ts` lives)
- **ALWAYS** use `background: true` for video renders
- **NEVER** retry a render because you got an empty result — it's running in the background
- **NEVER** poll in a loop — wait for the `notifyOnExit` system notification
- **Tell the user** the render is in progress and that you'll notify them when done
- A 30-second (900 frame) video at 30fps typically takes 2-3 minutes to render
- Still images (`remotion still`) are fast (seconds) and do NOT need background mode

### Output File Timing
The output MP4 file **does not exist until the render fully completes**. Remotion writes the file atomically at the very end after encoding. There are no temp files or partial outputs.

**Therefore:** Do NOT link to, embed, or reference the output file until after you receive the `notifyOnExit` completion notification and confirm the file exists. If you need to show the user something while rendering, create a "rendering in progress" placeholder page first, then update it with the video embed after the render completes.

### Web Optimization (MANDATORY)

Raw Remotion output is NOT web-ready. It lacks faststart metadata, has oversized audio, and may use incompatible pixel formats. **You MUST optimize every rendered video with ffmpeg before using it anywhere.**

After the render completes, run this ffmpeg command:
```json
{"tool": "exec", "command": "ffmpeg -y -i out.mp4 -vf scale=1280:720 -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -profile:v main -level 4.0 -g 60 -keyint_min 30 -tune animation -c:a aac -b:a 128k -movflags +faststart -f mp4 out-web.mp4", "workdir": "/home/node/.openclaw/workspace/remotion-project"}
```

What this does:
- `-vf scale=1280:720` — downscale to 720p (ideal for web/canvas playback)
- `-crf 18 -preset medium` — high quality encoding
- `-pix_fmt yuv420p` — universal browser compatibility
- `-profile:v main -level 4.0` — broad device/browser support
- `-g 60 -keyint_min 30` — keyframe every 2 seconds (prevents decoder stutter at scene transitions)
- `-tune animation` — optimized for synthetic/animated content (Remotion output has flat colors, sharp text, clean edges)
- `-b:a 128k` — web-appropriate audio bitrate
- `-movflags +faststart` — metadata at front for instant streaming

This runs in ~10-20 seconds and is NOT a long-running process — no need for background mode.

**The raw `out.mp4` is the high-res backup. The optimized `out-web.mp4` is what you use for everything** — canvas pages, embeds, links, downloads.

### Serving Rendered Videos on Canvas Pages

To display a rendered video on a canvas page:

1. **Optimize the video first** (see above)

2. **Copy the optimized file to the canvas-pages directory** (inside a `video/` subdirectory):
   ```json
   {"tool": "exec", "command": "mkdir -p /app/runtime/canvas-pages/video && cp out-web.mp4 /app/runtime/canvas-pages/video/my-video.mp4", "workdir": "/home/node/.openclaw/workspace/remotion-project"}
   ```

3. **Use the `/pages/` URL prefix** in the HTML video tag. All canvas content is served from `/pages/`:
   ```html
   <video controls preload="auto" playsinline>
     <source src="/pages/video/my-video.mp4" type="video/mp4">
   </video>
   ```
   Always use `preload="auto"` (NOT `preload="metadata"`) — optimized videos are small enough to fully preload, which prevents playback stuttering from streaming latency.

**WRONG** (404 — no `/video/` route exists):
```html
<source src="/video/my-video.mp4" type="video/mp4">
```

**CORRECT** (served by the `/pages/` route):
```html
<source src="/pages/video/my-video.mp4" type="video/mp4">
```

## Rule Files Reference

**When doing Remotion work, read these files for detailed code and examples:**

### Core (read these first)
- `rules/compositions.md` — Compositions, stills, folders, default props, dynamic metadata
- `rules/animations.md` — Frame-based animation fundamentals
- `rules/timing.md` — Interpolation curves: linear, easing, spring animations
- `rules/sequencing.md` — Delay, trim, limit duration of items with `<Sequence>`
- `rules/transitions.md` — Scene transition patterns
- `rules/parameters.md` — Make videos parametrizable with Zod schemas

### Media
- `rules/videos.md` — Embed videos: trimming, volume, speed, looping, pitch
- `rules/audio.md` — Audio: import, trim, volume, speed, pitch
- `rules/images.md` — Embed images with `<Img>` component
- `rules/gifs.md` — Display GIFs synchronized with timeline
- `rules/fonts.md` — Load Google Fonts and local fonts
- `rules/assets.md` — Import images, videos, audio, and fonts

### Advanced
- `rules/text-animations.md` — Typography and text animation patterns
- `rules/charts.md` — Bar, pie, line, stock chart patterns
- `rules/3d.md` — 3D content with Three.js and React Three Fiber
- `rules/lottie.md` — Embed Lottie animations
- `rules/light-leaks.md` — Light leak overlay effects
- `rules/maps.md` — Mapbox maps with animation
- `rules/audio-visualization.md` — Spectrum bars, waveforms, bass-reactive effects
- `rules/tailwind.md` — Using TailwindCSS in Remotion

### Captions & Voiceover
- `rules/subtitles.md` — Subtitle/caption system overview
- `rules/display-captions.md` — Render captions on screen
- `rules/import-srt-captions.md` — Import SRT caption files
- `rules/transcribe-captions.md` — Generate captions from audio
- `rules/voiceover.md` — AI voiceover with ElevenLabs TTS

### Utilities
- `rules/ffmpeg.md` — FFmpeg operations (trim, silence detection)
- `rules/trimming.md` — Cut beginning/end of animations
- `rules/calculate-metadata.md` — Dynamic composition duration/dimensions
- `rules/measuring-dom-nodes.md` — Measure DOM element dimensions
- `rules/measuring-text.md` — Measure text, fit to containers
- `rules/get-video-duration.md` — Get video duration with Mediabunny
- `rules/get-video-dimensions.md` — Get video width/height
- `rules/get-audio-duration.md` — Get audio duration
- `rules/extract-frames.md` — Extract frames at specific timestamps
- `rules/can-decode.md` — Check if browser can decode a video
- `rules/transparent-videos.md` — Render video with transparency
- `rules/sfx.md` — Sound effects
