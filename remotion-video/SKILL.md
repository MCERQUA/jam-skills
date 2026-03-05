---
name: remotion-video
description: "Create videos programmatically using Remotion and React. Use when the user wants to generate, render, or edit videos with code, create animated content, or build video templates."
metadata:
  version: 1.0.0
---

# Remotion Video Creation — End-to-End Workflow

This skill provides everything needed to create a video from scratch using Remotion inside the openclaw container.

## Quick Start

```bash
# 1. Copy the template into your workspace
cp -r /mnt/shared-skills/remotion-video/template ~/workspace/video-project

# 2. Install dependencies
cd ~/workspace/video-project && pnpm install

# 3. Edit the composition (src/Root.tsx, src/HelloWorld.tsx)

# 4. Generate voiceover (if needed)
GROQ_API_KEY=$GROQ_API_KEY node --strip-types generate-voiceover.ts

# 5. Render
npx remotion render src/index.ts HelloWorld out/video.mp4

# 6. Copy to canvas-pages for serving
cp out/video.mp4 ~/workspace/canvas-pages/my-video.mp4
```

## Template Location

The project template is at `/mnt/shared-skills/remotion-video/template/`. **Always copy it** — never modify the template in-place (it's read-only).

## Template Contents

```
template/
  package.json            ← Remotion + React deps
  tsconfig.json           ← TypeScript config
  src/
    index.ts              ← Entry point (registerRoot)
    Root.tsx               ← Composition registry
    HelloWorld.tsx         ← Working example composition
  public/
    voiceover/            ← TTS audio files go here
  generate-voiceover.ts   ← Groq TTS generation script
```

## Full Workflow

### Step 1: Copy Template
```bash
cp -r /mnt/shared-skills/remotion-video/template ~/workspace/video-project
cd ~/workspace/video-project
pnpm install
```

### Step 2: Design Your Composition

Edit `src/Root.tsx` to register your compositions and create component files in `src/`.

Key rules:
- **No CSS animations** — use Remotion's `interpolate()` and `useCurrentFrame()` for all motion
- **Use `staticFile()`** for all assets (images, audio, video) placed in `public/`
- **Set explicit dimensions** — `width: 1920, height: 1080` in composition config
- **All text must use inline styles** — no Tailwind, no external CSS frameworks

### Step 3: Generate Voiceover with Groq TTS

The template includes `generate-voiceover.ts`. Edit the `scenes` array with your script text:

```ts
const scenes = [
  { id: "intro", text: "Welcome to our video." },
  { id: "main", text: "Here's what we're about." },
  { id: "outro", text: "Thanks for watching!" },
];
```

Then run:
```bash
GROQ_API_KEY=$GROQ_API_KEY node --strip-types generate-voiceover.ts
```

This creates MP3 files in `public/voiceover/` that your composition reads via `staticFile()`.

**Available Groq TTS voices:** Fritz-PlayAI, Arista-PlayAI, Atlas-PlayAI, Basil-PlayAI, Briggs-PlayAI, Calista-PlayAI, Celeste-PlayAI, Cheyenne-PlayAI, Chip-PlayAI, Cillian-PlayAI, Deedee-PlayAI, Eleanor-PlayAI, Gail-PlayAI, Indira-PlayAI, Jennifer-PlayAI, Mamaw-PlayAI, Mason-PlayAI, Mikail-PlayAI, Mitch-PlayAI, Nia-PlayAI, Quinn-PlayAI, Ruby-PlayAI, Thunder-PlayAI

**Groq TTS API:**
```bash
curl -s https://api.groq.com/openai/v1/audio/speech \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"playai-tts","voice":"Fritz-PlayAI","input":"Hello world","response_format":"mp3"}' \
  -o output.mp3
```

### Step 4: Render

```bash
# Basic render (720p, fast)
npx remotion render src/index.ts HelloWorld out/video.mp4

# Higher quality
npx remotion render src/index.ts HelloWorld out/video.mp4 --scale=1

# Custom resolution is set in the composition config (Root.tsx)
```

**Render tips:**
- Rendering takes 1-5 minutes depending on duration and complexity
- Use `--log=verbose` to debug render failures
- If render hangs, check that all `staticFile()` references point to files that exist in `public/`
- The container has Chromium (via Playwright) — no need to install a browser

### Step 5: Serve via Canvas Pages

Copy the rendered video to canvas-pages so it's accessible via the web:

```bash
cp out/video.mp4 ~/workspace/canvas-pages/my-video.mp4
```

The video is then available at `https://<domain>/canvas/my-video.mp4`.

To embed in a canvas page:
```html
<video controls autoplay style="width:100%;max-width:800px;">
  <source src="/canvas/my-video.mp4" type="video/mp4">
</video>
```

Or show it with the canvas command tag: `[CANVAS_PAGE:my-video.mp4]`

## Common Pitfalls

1. **Don't use CSS animations** — they don't sync with Remotion's frame system. Use `interpolate()`.
2. **Don't use external CDN scripts** — the render environment is headless Chromium, external loads fail.
3. **Always use `staticFile()`** for assets — don't use relative paths or `require()`.
4. **Audio must be MP3 or WAV** — other formats may not decode correctly in the render.
5. **Don't forget `pnpm install`** — the template needs deps installed before render.
6. **Keep compositions under 5 minutes** — longer videos use significant memory during render.
7. **`registerRoot` must be in `src/index.ts`** — this is Remotion's expected entry point.

## Composition Patterns

### Simple text + voiceover scene
```tsx
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, interpolate } from "remotion";

export const Scene: React.FC<{ text: string; audioFile: string }> = ({ text, audioFile }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: "#1a1a2e", justifyContent: "center", alignItems: "center" }}>
      <Audio src={staticFile(audioFile)} />
      <h1 style={{ color: "white", fontSize: 64, opacity, textAlign: "center", padding: 40 }}>
        {text}
      </h1>
    </AbsoluteFill>
  );
};
```

### Background image + animated text
```tsx
import { AbsoluteFill, Img, staticFile, useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";

export const ImageScene: React.FC<{ title: string; image: string }> = ({ title, image }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = spring({ frame, fps, config: { damping: 200 } });

  return (
    <AbsoluteFill>
      <Img src={staticFile(image)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      <div style={{
        position: "absolute", bottom: 80, left: 0, right: 0,
        textAlign: "center", transform: `scale(${scale})`
      }}>
        <h1 style={{ color: "white", fontSize: 72, textShadow: "0 4px 20px rgba(0,0,0,0.8)" }}>
          {title}
        </h1>
      </div>
    </AbsoluteFill>
  );
};
```

### Multi-scene with Series
```tsx
import { Composition, Series } from "remotion";

export const RemotionRoot: React.FC = () => (
  <Composition
    id="PromoVideo"
    component={PromoVideo}
    durationInFrames={300}
    fps={30}
    width={1920}
    height={1080}
  />
);

const PromoVideo: React.FC = () => (
  <Series>
    <Series.Sequence durationInFrames={90}>
      <IntroScene />
    </Series.Sequence>
    <Series.Sequence durationInFrames={120}>
      <MainScene />
    </Series.Sequence>
    <Series.Sequence durationInFrames={90}>
      <OutroScene />
    </Series.Sequence>
  </Series>
);
```
