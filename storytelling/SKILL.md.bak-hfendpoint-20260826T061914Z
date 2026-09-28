---
name: storytelling
description: "Audio-visual story engine — combines FLUX images, Suno ambient/SFX audio, and Resemble character voices into canvas-based stories, created on demand (the user asks; no desktop icon). Modes: random, user-directed, self-generating with choices, storyboard (plays like a movie, no buttons), or scene-by-scene user influence. TRIGGER when the user asks for a story."
metadata: {"openclaw": {"emoji": "📖"}}
---

# Storytelling Skill

## What This Is

A **generation and creation capability** — not a fixed product. The agent assembles scene assets on demand and produces a canvas page tailored to what was asked for. The canvas page is created at request time and opened directly; it is never pinned to the desktop.

**The building blocks:**
- **Scene image** — FLUX.1-schnell via HuggingFace (~2.75s)
- **Ambient audio loop** — Suno sounds V5_5 (~20-26s, loops seamlessly)
- **SFX** — Suno sounds V5_5, triggered at precise script moments with play_count + volume control
- **Narration + character voices** — Resemble Chatterbox per character (~2-3s/line)
- **Canvas player** — image, audio, subtitles, and whatever interaction model fits the request

**What gets built depends entirely on what was asked:**

| Request | What the agent creates |
|---------|----------------------|
| "Tell me a random story" | Agent picks genre/tone, generates all scenes up front, canvas plays like a movie (no buttons) |
| "Create a story about pirates" | Agent generates scene 1, canvas shows choices, each choice generates the next scene live |
| "I want to influence the story" | After each scene the agent asks what should happen next, user responds, scene generates from that |
| "Make me a storyboard" | Agent generates scene images + narration text only, laid out as a visual planning document |
| "Make a choose-your-own-adventure" | Full interactive mode — branching choices, each path generates on demand, cached so no repeats |
| "Generate a bedtime story for kids" | Short linear story, soft ambient, gentle voices, auto-advances through all scenes |

---

## Trigger Examples

- "tell me a story" / "tell me a {genre} story about {X}"
- "create a story" / "make me an interactive story about {X}"
- "generate a choose-your-own-adventure about {X}"
- "make a storyboard for {X}"
- "I want to build a story together"
- "make something scary / funny / romantic / for kids"

---

## Delivery Modes

### Movie mode (no buttons)
All scenes pre-generated before the canvas opens. Canvas auto-advances through scenes with a timed pause between them. No choices. Just plays. Good for: bedtime stories, short films, random generation, atmospheric pieces.

```json
{ "mode": "movie", "auto_advance_ms": 1800 }
```
Canvas omits choice buttons. After final narration line: scene fades, next scene crossfades in automatically.

### Interactive mode (choices, generates on demand)
Scene 1 is pre-generated. Choices at the end of each scene trigger live generation of the next scene via `POST /api/story/generate-scene`. Generated scenes are cached by choice ID — same choice never regenerates.

```json
{ "mode": "interactive" }
```

### Storyboard mode (planning, no audio playback)
Generates scene images + script text only. Laid out as a visual grid — one card per scene. No audio plays. Good for planning a longer story before committing to full generation.

```json
{ "mode": "storyboard" }
```

### User-influenced mode
After each scene the canvas posts back to the agent asking what happens next. The agent takes user input (voice or text) and uses it as the `choice_text` for the next generation. The user co-writes the story in real time.

---

## Story Structure — Fully Variable

```json
{
  "story_id": "{story_id}",
  "title": "{title}",
  "genre": "{genre}",
  "tone": "{tone}",

  "characters": {
    "{character_key}": {
      "name": "{Display Name shown in subtitles}",
      "voice_uuid": "{resemble_voice_uuid}",
      "model": "chatterbox-turbo | chatterbox | chatterbox-multilingual",
      "exaggeration": 0.0,
      "prompt": "{acting direction, e.g. 'gruff old wizard, slow deliberate speech'}"
    }
  },

  "start": "{scene_id}",

  "scenes": {
    "{scene_id}": {
      "title": "{scene title}",
      "image_prompt": "{detailed cinematic description for FLUX — include style, lighting, mood}",

      "sounds": [
        {
          "id": "{sound_id}",
          "role": "ambient | sfx",
          "prompt": "{suno sound prompt}",
          "soundLoop": true,
          "soundKey": "Any | Am | C | Em | Dm | ...",
          "model": "V5_5",
          "trigger": "scene_start | after_line_{n}",
          "volume": 0.35,
          "play_count": 1,
          "gap_ms": 150,
          "delay_ms": 0
        }
      ],

      "script": [
        {
          "type": "narration | dialogue",
          "character": "{character_key}",
          "text": "{spoken text}",
          "audio": "{story_id}/scene_{id}_line_{nn}.wav"
        }
      ],

      "choices": [
        {
          "id": "{choice_id}",
          "text": "{Button label}",
          "next_scene": "{scene_id} | null"
        }
      ],

      "next_scene": "{scene_id} | null"
    }
  }
}
```

### Variable Rules
- `characters{}` — any number. Each key used in `script[].character`. Narrator key should be `"narrator"` with `name: ""`.
- `sounds[]` — any number of entries per scene. Use concurrency rules below — too many overlapping streams causes distortion/static.
- `script[]` — any number of lines, any mix of narration/dialogue.
- `choices[]` — 0 to N. Zero + `next_scene` = auto-advance. Zero + no `next_scene` = "The End."
- `sounds[].trigger` — `scene_start` for ambient on load; `after_line_{n}` fires as line n begins (0-indexed). `after_line_-1` fires as line 0 starts.

### Sound Concurrency Rules — IMPORTANT
Too many overlapping streams causes distortion/static. Hard cap: **3 SFX max simultaneously** (enforced by canvas engine).

**Volume hierarchy** — stay in these ranges to avoid clipping:
| Type | Volume | Notes |
|------|--------|-------|
| Ambient loop | 0.25–0.32 | Always quietest — bed under everything |
| Atmospheric SFX (wind, footsteps) | 0.35–0.45 | Long clips, keep soft |
| Movement SFX (rustling, distant) | 0.45–0.60 | Medium |
| Impact SFX (snaps, heartbeat, doors) | 0.65–0.82 | Short and punchy |
| Narration | 1.0 | Always full |

**`play_count`** — how many times to repeat the clip before stopping:
- Footsteps, walking: `play_count: 2`, `gap_ms: 200` (a few paces, then silence)
- Heartbeat/pulse: `play_count: 2`, `gap_ms: 650-800` (natural rhythm)
- Impact sounds (snap, crash, door): `play_count: 1` — always single hit
- Wind gusts, long atmospheric: `play_count: 1` — let it fade naturally

**`delay_ms`** — stagger SFX sharing the same trigger. E.g. twig snap at `delay_ms: 0` + rustling at `delay_ms: 500` = snap hits first, creature moves away after.

**Never**: two long atmospheric SFX on the same trigger slot. Space them across different `after_line_N` triggers.

---

## Asset Generation

All assets are pre-generated before the canvas page is served. Fire image and all Suno sounds in parallel first (Suno is the bottleneck at 20-30s), then TTS lines in parallel.

### Image — FLUX.1-schnell
```python
r = httpx.post(
    "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell",
    content=json.dumps({"inputs": scene["image_prompt"]}).encode(),
    headers={"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"},
    timeout=60.0
)
# r.content is JPEG bytes — save directly
```
- Time: ~2.75s
- Key: `HF_TOKEN` from `.platform-keys.env`
- Output: JPEG, any prompt accepted

### Sounds — Suno
```python
# Submit
r = httpx.post(
    "https://api.sunoapi.org/api/v1/generate/sounds",
    json={"prompt": sound["prompt"], "model": "V5_5",
          "soundLoop": sound["soundLoop"], "soundKey": sound["soundKey"]},
    headers={"Authorization": f"Bearer {SUNO_API_KEY}"},
)
task_id = r.json()["data"]["taskId"]

# Poll (every 5s)
poll = httpx.get(f"https://api.sunoapi.org/api/v1/generate/record-info?taskId={task_id}",
                 headers={"Authorization": f"Bearer {SUNO_API_KEY}"})
clips = poll.json()["data"]["response"]["sunoData"]
audio_url = clips[0]["sourceAudioUrl"]  # CDN direct — more stable than audioUrl
```
- Time: 20-30s typical (much faster than the 120s worst-case — V5_5 is fast)
- Generates 2 clips, use `clips[0]` (or let user pick)
- `soundLoop: true` for ambient, `false` for SFX

### Narration / Character Voice — Resemble
```python
text = f'<speak exaggeration="{char["exaggeration"]}" prompt="{char["prompt"]}">{line["text"]}</speak>'
r = httpx.post(
    "https://f.cluster.resemble.ai/stream",
    json={"voice_uuid": char["voice_uuid"], "data": text,
          "precision": "PCM_16", "sample_rate": 24000},
    headers={"Authorization": f"Bearer {RESEMBLE_API_KEY}"},
    timeout=30.0
)
# r.content is WAV bytes
```
- Time: 2-3s per line
- Run all lines in parallel threads — total ~3s regardless of line count
- `exaggeration` 0.0–1.0: higher = more emotional. Narrator ~0.3, characters 0.6-0.85
- `prompt` is the acting direction injected as SSML

---

## Available Resemble Voices (en-US)

| UUID | Name | Good for |
|------|------|----------|
| `819fcc57` | Luma | Narrator (calm, clear female) |
| `fb2d2858` | Lucy | Young female character |
| `a9fc5a41` | Nova | Warm female character |
| `6e37aa15` | Titan | Deep male narrator or villain |
| `316d5642` | Atlas | Calm male narrator |
| `31f74317` | Remy | Younger male character |
| `704cb696` | Kyle Valhalla | Character voice |
| `cabc1397` | Bryce BigHead | Character voice |

---

## File Storage

```
/mnt/clients/{tenant}/openvoiceui/canvas-pages/stories/{story_id}/
  manifest.json
  scene_{id}_image.jpg
  scene_{id}_{sound_id}.mp3       ← ambient or sfx
  scene_{id}_line_{nn}.wav        ← one per script line (00, 01, 02...)

/mnt/clients/{tenant}/openvoiceui/canvas-pages/
  story-{story_id}.html           ← the canvas player page
```

Served at: `https://{tenant}.jam-bot.com/pages/story-{story_id}.html`

---

## Canvas Manifest Registration

```python
manifest["pages"]["story-{story_id}"] = {
    "filename": "story-{story_id}.html",
    "display_name": "{title}",
    "description": "{one line description}",
    "category": "stories",
    "tags": ["story", "interactive", "audio"],
    "is_public": True,                          # REQUIRED — auth blocks page otherwise
    "voice_aliases": ["{title lower}", "story"],
    "starred": False,
    "access_count": 0
}
```

**Critical**: The manifest key MUST match `Path(filename).stem` exactly. The auth check does `manifest["pages"][Path(path).stem]` — a mismatch means `is_public` lookup returns `{}` → 401 even for public pages.

---

## Canvas Player HTML — Key Rules

The OVU app injects `padding: 25px !important` on `html, body` via its canvas base styles. Override it or the full-screen layout breaks:

```css
html, body {
  padding: 0 !important;
  margin: 0 !important;
}
```

### Audio Playback Engine (simplified)
```javascript
async function playScene(sceneId) {
  const scene = manifest.scenes[sceneId];

  // 1. Show image (crossfade)
  bg.style.backgroundImage = `url(${scene.image_file})`;
  bg.classList.add('visible');

  // 2. Start ambient sounds (trigger: scene_start)
  for (const s of scene.sounds.filter(s => s.trigger === 'scene_start' && s.role === 'ambient')) {
    ambientAudio.src = s.file; ambientAudio.volume = s.volume; ambientAudio.play();
  }

  // 3. Play script lines sequentially
  for (let i = 0; i < scene.script.length; i++) {
    // Trigger SFX set for after_line_{i-1}
    for (const s of scene.sounds.filter(s => s.trigger === `after_line_${i-1}` && s.role === 'sfx')) {
      sfxAudio.src = s.file; sfxAudio.volume = s.volume; sfxAudio.play();
    }
    // Show subtitle, play audio, wait for end
    setSubtitle(scene.script[i]);
    await playAndWait(narrationAudio, scene.script[i].audio);
    await delay(220);
  }

  // 4. Show choices or end
  if (scene.choices?.length) showChoices(scene.choices);
  else if (scene.next_scene) { await delay(600); playScene(scene.next_scene); }
  else showEnd();
}
```

---

## Ambient + SFX Prompt Reference

**Ambient loops (soundLoop: true):**
| Setting | Prompt | soundKey |
|---------|--------|----------|
| Dark forest | `deep forest at night, crickets, distant owl, soft wind` | Am |
| Tavern | `lively medieval tavern, murmur, cups clinking, lute` | C |
| Ocean/ship | `ocean waves on ship hull, creaking wood, seagulls, wind` | Any |
| Cave/dungeon | `dark cave, dripping water, distant echo, low hum` | Dm |
| Haunted house | `eerie manor, floorboards creaking, moaning wind` | Bm |
| Battle nearby | `distant battle, clashing metal, marching drums` | Em |
| Spaceship | `spaceship bridge hum, soft beeps, distant machinery` | Any |
| Rainy night | `heavy rain on window, distant thunder, steady rhythm` | Any |

**SFX (soundLoop: false):**
| Event | Prompt |
|-------|--------|
| Twig snap | `single dry twig snapping in a silent forest, sharp crack` |
| Door creak | `old wooden door slowly creaking open` |
| Thunder | `single thunder clap, distant rumble fading` |
| Sword draw | `metal sword drawn from leather scabbard` |
| Magic/spell | `mystical energy whoosh, crystalline shimmer, sparkling` |
| Footsteps stone | `slow footsteps on stone floor, hollow echo` |
| Glass break | `glass shattering on hard floor` |

---

## Generation Timing (confirmed via live test)

| Asset | Time |
|-------|------|
| FLUX.1-schnell image | ~2.75s |
| Suno ambient (V5_5) | ~20-26s |
| Suno SFX (V5_5) | ~20s |
| Resemble TTS line | ~2-3s (run all in parallel) |
| **Full scene (parallel)** | **~26-29s total** |

Suno is always the bottleneck. For multi-scene stories: pre-generate scene N+1 sounds immediately when scene N starts playing (~30s of playback time covers the generation).

---

## Provider Keys

| Provider | Key Env Var | Notes |
|----------|------------|-------|
| HF FLUX.1-schnell | `HF_TOKEN` | `router.huggingface.co` resolves; `api-inference.huggingface.co` does NOT |
| Suno sounds | `SUNO_API_KEY` | V5_5 confirmed working on sounds endpoint |
| Resemble Chatterbox | `RESEMBLE_API_KEY` | Synthesis: `f.cluster.resemble.ai/stream`; API: `app.resemble.ai/api/v2` |

---

## Build Status

**Proven working on mm-test (2026-05-28):**
- [x] FLUX image generation
- [x] Suno ambient loop + SFX
- [x] Resemble per-character TTS with SSML emotion
- [x] Canvas player: image fade-in, ambient loop, sequential narration, SFX trigger, subtitles, choice buttons

**Next to build:**
- [ ] Multi-scene stories (scene 2, 3... with branching)
- [ ] Asset generation script as a proper OpenVoiceUI service (`services/story_engine.py`)
- [ ] `POST /api/story/create` route — agent calls it with a prompt, gets back a canvas URL
- [ ] OpenClaw skill hook so agent can generate and open stories from conversation
