---
name: suno-music
description: Generate AI music using Suno API — full songs, 10-15s vocal logo jingles, audio logos, extends, covers, vocal swaps, lyric pulls. Includes proven jingle recipe + endpoint catalog with credit costs.
metadata: {"openclaw": {"emoji": "🎵"}}
---

# Suno Music & Jingle Generation Skill

Generate AI songs and short branded jingles. **All generation is async.** Songs take 45–90s, jingles take 30–60s, and auto-appear in the player. **Default model: `V5_5`.**

---

## ⚠️ CRITICAL: How Generation Works

**NEVER call `https://api.sunoapi.org` directly.** Use the local `/api/suno` endpoint inside the container. That endpoint forwards to Suno, downloads the audio, saves it to `generated_music/`, and writes metadata.

There are **three correct methods**:

1. **`[JINGLE_GENERATE:]` voice tag** — for 10-15s branded vocal/instrumental logo jingles. **Use this for any "make a jingle / audio logo / phone intro / sting" request.**
2. **`[SUNO_GENERATE:]` voice tag** — for full songs (~3 minutes).
3. **Direct `/api/suno` API call** — for canvas pages and programmatic flows.

---

## ⚠️ Delivering a song to the user — DOWNLOAD LINKS (voice / SMS / email)

A real client asked "give me a link to download it" and the agent failed five times: it
invented `[CANVAS:song-download]` pages that render blank, and handed out
`https://DOMAIN/music/<slug>.mp3` URLs that return `{"error":"Track not found"}` (the
client saw a JSON "pretty print" page). Generated songs are **NOT** under `/music/`.
Fixed 2026-06-30 — follow these rules so it never recurs:

**The one correct download link (works from any phone browser, no login, texts/emails fine):**
```
https://DOMAIN/generated_music/FILENAME?download=1
```
- `DOMAIN` = this tenant's domain (e.g. `src.jam-bot.com`).
- `FILENAME` = the **EXACT** file name from the Generated track list (e.g. `shop-bay-wisdom.mp3`). Never invent or re-slug it.
- `?download=1` makes the browser **save** the file (sends `Content-Disposition: attachment` with a friendly name). Drop it if you just want it to play inline.
- `/generated_music/` is a **public** path — the link works with no Clerk login, so it's exactly what you text or email a client.

**"Play / link the LAST song you made":** there is one authoritative source — do not guess.
```bash
curl -s "http://localhost:5001/api/music?action=latest"
# → {"track":{"filename":"...","title":"...","download_url":"/generated_music/...?download=1"}}
```
The voice agent also receives this every turn as `[Latest generated song: '<title>' (file: <file>) — download link: ...]` in context. Use that filename; never alphabetically guess.

**"Link the song CALLED X" (a SPECIFIC named song, not the latest):** this is where the agent
burned a client for hours (2026-06-30/07-01) — they asked for "Shop Bay Wisdom" over and over,
it wasn't the newest track, and the agent kept guessing wrong `/music/` URLs. **Never guess a
filename from the title.** Resolve it against the real list:
```bash
# list every generated track with its EXACT filename + title
curl -s "http://localhost:5001/api/music?action=list&playlist=generated" \
  | python3 -c "import sys,json; [print(t['filename'],'::',t.get('name','')) for t in json.load(sys.stdin).get('files',[])]"
# → shop-bay-wisdom.mp3 :: Shop Bay Wisdom
#   by-the-shop-light.mp3 :: By The Shop Light   ...
```
Pick the row whose title matches what the client said, take its **exact `filename`**, and build
`https://DOMAIN/generated_music/<filename>?download=1`. If several match (e.g. `-2` variants), ask
which one or offer the newest by mtime — do NOT silently pick one and do NOT hand over three links.

**If the client says "the link doesn't work on my phone":** the link is fine (verified: `HTTP 200,
Content-Type audio/mpeg, Content-Disposition attachment`). The failure is almost always that you
sent a `/music/<slug>` URL or a `[CANVAS:...]` page, NOT the `/generated_music/<exact-file>?download=1`
link. Re-send the correct link above — do not invent a new delivery mechanism, do not attach it to a
video unless they explicitly ask for a video.

**Hard rules:**
- ❌ NEVER use `/music/<file>` for a generated song — that route serves the (usually empty) library dir → 404 JSON.
- ❌ NEVER emit a `[CANVAS:...]` page for a download — there is no download page; use the direct link.
- ❌ NEVER dump the entire track list of raw URLs at the user. Give the ONE link they asked for.
- ✅ For SMS/email, the same `https://DOMAIN/generated_music/<file>?download=1` link is the deliverable.

---

## Short-Form Audio Tools — One Tool Per Recipe

**Design principle:** Each short-form audio variant (vocal jingle, instrumental sting, phone hold greeting, podcast bumper, etc.) is its own discrete tool with its own template that gets iterated until reliable. **Don't try to make one tool do everything.** Each recipe has different prompt structure, different style needs, different ideal length, and different tuning history. Mixing them in one endpoint produces unreliable output.

| Tool | Status | Tag | Endpoint | Target length |
|---|---|---|---|---|
| **Vocal Logo Jingle** (sings the brand) | LIVE — recipe v2 (2026-05-05) | `[JINGLE_GENERATE:]` | `?action=jingle` | 10-15s |
| Instrumental Audio Logo / Stinger | LIVE — recipe v1 untested | `[JINGLE_GENERATE:...|...|...|true]` | `?action=jingle` (instrumental flag) | 5-10s |
| **Sound Effect / Stinger (non-vocal SFX)** | LIVE (2026-05-29) | — | `?action=sfx` | ~3-20s |
| Phone Hold / IVR Greeting | PLANNED | `[PHONE_HOLD:]` | `?action=phone_hold` | 8-15s |
| Podcast Intro Sting | PLANNED | `[PODCAST_INTRO:]` | `?action=podcast_intro` | 10-15s |
| Social Media Bumper | PLANNED | `[BUMPER:]` | `?action=bumper` | 5-10s |
| Brand Sting (very short) | PLANNED | `[STING:]` | `?action=sting` | 3-5s |

Each of those will get its own subsection in this skill once its recipe is tuned. Don't extrapolate from the vocal jingle's recipe to invent prompts for the others — they need their own iteration cycle.

---

## BEFORE generating an SFX — search the global sound library

Every generation costs credits. There is a shared, reusable library of sounds
across all clients at `/mnt/agent-mesh/shared/sound-library/` (mounted in every
container). **Search it first; only generate if nothing fits.**

```
sound-lib search coin            # /mnt/agent-mesh/shared/sound-library/bin/sound-lib
sound-lib path coin-pickup-blip  # → abs path to copy into your game
cp "$(/mnt/agent-mesh/shared/sound-library/bin/sound-lib path coin-pickup-blip)" \
   ~/openvoiceui/canvas-pages/_data/coin.mp3
```

After you generate a NEW keeper with `action=sfx`, **promote it back** so the
next game/client reuses it free:
```
/mnt/agent-mesh/shared/sound-library/bin/sound-lib promote \
  ~/openvoiceui/generated_music/<file>.mp3 --category impacts --name <clean-name> \
  --desc "what it is" --tags hit,wood --client <you> --prompt "<the prompt>" --approved
```
Full guide: `/mnt/agent-mesh/shared/sound-library/README.md`.

---

## Tool: Sound Effect / Stinger — `?action=sfx` (non-vocal SFX, ~3-20s)

**LIVE 2026-05-29.** Wraps sunoapi.org's `POST /api/v1/generate/sounds` (2.5 credits, model `V5_5`). Produces **non-vocal** game SFX, UI blips, stingers, ambient beds — NOT songs or vocal jingles. This is the right tool for game soundboards (e.g. coin pickups, impacts, game-over stings) instead of synthesized/WebAudio sounds.

**Submit:**
```
POST /api/suno   { "action": "sfx", "prompt": "<what the sound is>", "title": "<label>" }
```
| Field | Required | Notes |
|---|---|---|
| `prompt` | ✅ | What the sound should be (≤500 chars). e.g. `"retro 8-bit coin pickup blip"`, `"wooden mallet thwack impact"`, `"ominous low brass sting, no vocals"` |
| `title` | — | Label for the saved filename + metadata |
| `loop` | — | `true` for a seamless looping bed (ambient). Default false. → `soundLoop` |
| `tempo` | — | BPM 1-300. Omit for auto. → `soundTempo` |
| `key` | — | Musical key (`Any`,`Cm`,`Am`,`C`,…). Omit for Any. → `soundKey` |

**Response:** `{"action":"generating","job_id":"…","task_id":"…","kind":"sfx"}`. Then poll `?action=status&job_id=<job_id>` (same poller as songs/jingles). On completion the clip is **saved to the server** (`generated_music/<slug>.mp3`) and returned as `url` — never in-memory only. Takes ~20-70s.

**Tip — keep SFX short & literal.** Describe the sound, not a song ("twig snap", "arcade game-over jingle no vocals"). For game soundboards, generate once and reuse the saved file; don't regenerate per play (each gen costs 2.5 credits).

> Note: `routes/story.py` (storytelling skill) calls `/api/v1/generate/sounds` directly for its per-scene ambient+SFX. `?action=sfx` is the same endpoint exposed through the shared `/api/suno` wrapper so any agent/canvas can use it without bespoke httpx code.

---

## Tool 1: Vocal Logo Jingle — `[JINGLE_GENERATE:]` (10-15 seconds, sings the brand)

This is the **most practical generator for business clients**. The agent picks a brand and a style — the server assembles the proven prompt template (no recall required).

### Recipe iteration history

| Version | Date | Recipe | Result | Status |
|---|---|---|---|---|
| **v1** | 2026-05-05 | `customMode:false`, prompt ends with literal `, [Intro` (truncated) | Produced 30s and 141s outputs — too long, unreliable | DEPRECATED |
| **v2** | 2026-05-05 | `customMode:true`, prompt = `[Intro] {brand}*N [End] — no other lyrics`, style includes `short and sweet, 10 to 15 seconds, one shot` | Rejected by Suno: "lyrics empty, too short, or malformed" — credits refunded. customMode requires real song-shaped lyrics, skeleton + meta-instruction is invalid | DEPRECATED |
| **v3** | 2026-05-05 | `customMode:false`, single freeform prompt with inline `[Intro]...[End]` block, multi-clause style + length signals | Suno returned `400 Prompt likely malformed` — bracket syntax inside customMode-false prompt confuses parser | DEPRECATED |
| **v4** | 2026-05-05 | Same as v5 but `model: V5_5` | Worked but produced 21.3s — V5.5 renders longer than V5 | DEPRECATED |
| **v5 (current)** | 2026-05-05 | Identical to v4 but `model: V5` (not V5.5). Reasoning: V5.5 is tuned for fuller production; V5 hits short-form better with the truncated `, [Intro` trick. Confirmed by test-dev 2026-05-05: vocal jingle produced ~15s clip. | CONFIRMED | ACTIVE |

**Mark every generated jingle with its `recipe_version` in metadata** so we can compare durations as recipes evolve.

### Prompt engineering rules (for understanding what drives duration — confirmed 2026-05-05)

These are why the server's recipe works. Useful if you're debugging outputs or extending the recipe later:

| Technique | Effect |
|---|---|
| Minimal lyrics (`[Intro` truncated, no closing bracket) | Signals "intro only", prevents verse/chorus structure |
| Fewer words in the brand phrase | Directly correlates to shorter output — 4 words ≈ 15s |
| `negativeTags` excluding "verse, chorus, full song, long intro, padding" | Suppresses Suno's padding instinct |
| `model: V5` (not V5.5) | V5.5 renders longer by design; V5 produces tighter short-form |
| "one shot" / "audio logo" vocabulary | Model understands these as short-clip signals |
| Duration hint ("10 second") in prompt | Helps but Suno still tends to overshoot — accept 15-30s as realistic range |
| NO `[Verse]`/`[Chorus]` tags | Those trigger full song generation |

**Lesson from v2:** Suno's `customMode:true` enforces lyrics-shaped content. Don't put meta-instructions in the lyrics field. If you need length control via lyrics structure, use `customMode:false` and embed the `[Intro]...[End]` block inside the freeform prompt — Suno parses the brackets correctly without strict-shape validation.

### What this thing is called (agent must recognize ALL of these as the same request)

The user — and clients — will use many different names for the same 10-15 second branded audio clip. Treat all of these as requests for `[JINGLE_GENERATE:]`:

**Industry / professional terms:**
- **Audio logo** (most formal — Intel "bong," Netflix "ta-dum")
- **Sonic logo** (synonym, used in branding agencies)
- **Sonic branding asset** / **sonic identity** / **sonic signature**
- **Audio mnemonic** (academic / brand-strategy term)
- **Brand sting** / **station sting** / **brand sting cue** (radio/broadcast term)
- **Audio bumper** / **brand bumper**
- **Audio ID** / **audio idem** / **station ID** (radio term — short branded ID between segments)
- **Audio watermark** (less common, same idea)

**Casual / colloquial terms:**
- **Jingle** (catch-all — historically longer, but most people now use this for short brand audio too)
- **Logo jingle** / **vocal logo jingle** (Mike's preferred term)
- **Brand jingle**
- **Theme jingle** / **little theme** / **theme song** (when they mean ~10s)
- **Hook** / **earworm** / **catchy bit**
- **Sting** / **stinger** (used by podcasters — but technically "stinger" = no vocals)
- **Tag** / **tagline jingle** (when it sings the slogan)

**Format-specific synonyms:**
- **Phone hold intro** / **on-hold greeting** / **IVR intro** (use vocal jingle with brand name)
- **Podcast intro sting** / **podcast bumper**
- **YouTube/TikTok/Reels intro** / **content creator intro** / **channel intro**
- **Trade show booth audio** / **booth loop**
- **Email signature audio** / **inbox sound**
- **Notification chime with branding** (instrumental variant)

**When the user says any of these, ask only for: brand name, style preference (or "surprise me"), and male/female (or instrumental).** Don't make them define the term — silently route to `[JINGLE_GENERATE:]`.

### Pitch language for clients (when explaining what you can make)

When introducing this capability to a business client, pick the term that fits their world:
- B2B / corporate → "audio logo" or "sonic identity"
- Restaurants, contractors, local services → "jingle" or "logo jingle"
- Podcasters / creators → "intro sting" or "bumper"
- Radio / broadcast / station ops → "station ID" or "brand sting"
- Marketing agencies → "sonic branding asset"

Same product, different language. The asset is identical — pick the word the client already uses.


### Tag syntax

```
[JINGLE_GENERATE:brand|style|gender|instrumental|repeat]
```

| Field | Required | Values | Default |
|---|---|---|---|
| `brand` | yes | The brand/company name to be sung. Spell it phonetically if it's an acronym (e.g. "OpenVoice U-I", "B-M-W"). **Translate intent, never literal text** — see brand-name rule below | — |
| `style` | no | One of the preset keys (see list below), OR freetext descriptor, OR empty = random preset | random |
| `gender` | no | `m` or `f` | `m` |
| `instrumental` | no | `true` for an instrumental audio logo (no vocals), `false` for a vocal jingle that sings the brand | `false` |
| `repeat` | no | `1` (brand sung once, ~8-12s, shortest), `2` (twice, ~12-15s), `3` (three times, ~15s+) | `2` |

### Style presets (15 styles, kept fresh — pick one or let it randomize)

`rock`, `country`, `cinematic`, `gospel`, `lofi-hiphop`, `jazz`, `edm`, `bluegrass`, `synthwave`, `latin`, `reggae`, `gritty-blues`, `orchestral`, `punk`, `rnb`

If the user says "make me a jingle" with no style, **leave style empty** (the server picks a random preset) — this is the right move because Suno otherwise drifts toward teenage pop.

If the user names a style not in the list, pass it as freetext (e.g. `salsa with brass and timbales`).

### Brand-name rule — TRANSLATE INTENT, NEVER PASS LITERAL TEXT

When the user types something like `OOOOhhhPIN-VoIcE- UUUUUIIIIII` or `aaakmee PLUM-bing` or `BEEEEM-DOUBLE-YOUUU`, they are **showing you how the hook should be SUNG** — they're describing vocal delivery through typography because most people don't know the music-industry vocabulary for it. Your job is to do TWO things:

**Step 1 — Clean the brand string.** Strip the theatrical typography and submit the standard phonetic spelling:

| User typed | Brand to submit |
|---|---|
| `OOOOhhhPIN-VoIcE- UUUUUIIIIII` | `OpenVoice U-I` |
| `aaakmee PLUM-bing` | `Acme Plumbing` |
| `BEEEEM-DOUBLE-YOUUU` | `B-M-W` |
| `mmm-MAC-DON-aaaaalds` | `McDonald's` |
| `coooooooooke!` | `Coke` |

**Step 2 — Translate the typography into Suno-friendly delivery vocabulary** and append it to the `style` field as a freetext descriptor (NOT a preset key). This is the part that makes the jingle actually sound the way the user pictured it.

#### Typography → Suno delivery vocabulary cheat sheet

| User typed | What they're showing | Suno delivery descriptor to add to `style` |
|---|---|---|
| `OOOOhhh` / `UUUUU` / `aaaaa` (stretched vowels) | A long, sustained note | `sustained drawn-out vowel, long-held note, operatic sustain` |
| `BEEEEM-DOUBLE-YOUUU` (hyphens between letters) | Each letter sung distinctly with emphasis | `letter-by-letter spell-out, punctuated syllabic phrasing, each letter held` |
| `OPEN-VOICE-U-I` (hyphens between words) | Staccato, deliberate cadence | `staccato deliberate phrasing, slight pause between each word` |
| `OPEN VOICE U I!!!` (ALL CAPS + bangs) | Shouted, anthemic | `shouty anthemic belt, full-chest delivery, stadium-style chant` |
| `open voice u i...` (all lowercase + ellipsis) | Soft, intimate, breathy | `breathy intimate delivery, ASMR-soft, almost-whispered` |
| `oooOOOPpenVOICE` (mixed case wave) | Playful, bouncy, swooping | `playful pitch-bending vocal, bouncy melodic swoops` |
| `OPeN VoIcE U-I` (alternating case) | Sing-song, nursery-rhyme cadence | `sing-song melodic cadence, nursery-rhyme bounce` |
| `o-p-e-n   v-o-i-c-e` (spaced letters) | Slow, deliberate, chant | `slow deliberate chant, monk-like cadence, half-time delivery` |
| `OPEN—VOICE—UUUI` (em-dash + final stretch) | Builds to a held finale | `builds to a sustained finale on the last syllable, climactic hold` |
| `🎵 OpenVoice 🎵` (with emojis/notes) | Melodic, "this is the hook" | `clear melodic hook, instantly memorable singalong` |
| `OPEN!!! VOICE!!! YOOOOO` | Hype, drop-style | `hype crowd-style chant with drops, festival energy` |
| `sshh oh-pen voice` (with shush/quiet) | Whispered intro then build | `whispered intro that opens into the hook` |

#### Worked examples (full submission)

User: *"do a jingle for OOOOhhhPIN-VoIcE- UUUUUIIIIII"*
→ Clean brand: `OpenVoice U-I`
→ Style hint from typography: stretched vowels = `sustained drawn-out vowels on Open and U-I, long-held notes, operatic sustain`
→ Combined with a base style choice (or random preset): `, sustained drawn-out vowels on the brand name, long-held notes` appended.

User: *"make me a jingle for BEEEEM-DOUBLE-YOUUU rock style"*
→ Clean brand: `B-M-W`
→ Style: `rock` preset + delivery: `letter-by-letter spell-out with each letter held, anthemic rock belt`

User: *"jingle for coooooooooke! shouty"*
→ Clean brand: `Coke`
→ Delivery: `shouty anthemic chant, stadium-style, drawn-out final vowel`

**Rule of thumb:** The clean brand goes in the `brand` field. The vibe-from-typography goes appended to `style`. If the user names a preset (`rock`, `gospel`, etc.), pass that as `style` AND append a freetext delivery hint after — it'll combine. If you're unsure how to translate, **ask one short question** before firing the paid generation: *"You want it sung with long stretched-out vowels on the brand name?"*

### Examples

```
[JINGLE_GENERATE:Acme Plumbing|country|m]
[JINGLE_GENERATE:OpenVoice U-I||f]
[JINGLE_GENERATE:Stark Industries|cinematic|m|true]
[JINGLE_GENERATE:Sunset Yoga Studio|jazz|f]
```

### What the server actually sends to Suno (recipe v4 — current)

The agent does **not** need to construct this — but for understanding:

```json
{
  "prompt": "OpenVoice U-I 80s synthwave vocal logo jingle, [Intro",
  "customMode": false,
  "instrumental": false,
  "model": "V5_5",
  "vocalGender": "m",
  "negativeTags": "verse, chorus, full song, long intro, padding, extended outro, lengthy, repeat hook, second verse"
}
```

**Why it works (hypothesis):** The trick is the truncated `, [Intro` (no closing bracket) — Suno reads "this is just an intro, nothing more" and stops at ~10-15s. The prompt MUST stay minimal: brand + 1-3-word style adjective + "vocal logo jingle" + the truncated tag. Every extra clause lengthens the rendered output. v1 used a multi-clause style descriptor (`gospel piano with hand-claps, soulful male vocal`) and got 30-141s outputs. v4 uses just the keyword (`gospel`) and should keep things tight.

**Instrumental variant:** `{brand} {keyword} instrumental audio logo, [Intro` with `customMode:false, instrumental:true`.

### Listing existing jingles

```bash
curl -s "http://openvoiceui:5001/api/suno?action=list_jingles" -H "X-Agent-Key: $AGENT_API_KEY"
```

Returns `{ jingles: [{ filename, title, brand, style_key, vocal_gender, instrumental, duration_seconds, url, ... }] }`.

The user-facing canvas page is at **`/pages/jingle-maker.html`** — show it with `[CANVAS:jingle-maker]` when the user wants a UI to make/manage jingles.

---

## Method 2: Full Song — `[SUNO_GENERATE:]` (~3 minutes)

Include one or more `[SUNO_GENERATE:]` tags anywhere in your response:

```
[SUNO_GENERATE:upbeat corporate background music for an insurance office, professional and energizing, no vocals, 120 BPM]
```

Rules:
- Tag is stripped before TTS — user won't hear you say it.
- You will NOT get a confirmation back — **this is normal**. The song IS generating.
- Generation takes 45–90 seconds.
- Multiple tags in one response start in parallel — three tags = three songs cooking at once.

**3-song example:**
```
[SUNO_GENERATE:upbeat professional corporate background music, no vocals, warm piano and soft strings, 110 BPM]
[SUNO_GENERATE:lo-fi hip hop beats for focus and productivity, chill instrumental, 85 BPM]
[SUNO_GENERATE:smooth jazz background, saxophone and piano, no vocals]
```

Custom lyrics: include `[Verse]` / `[Chorus]` / `[Bridge]` tags inside the prompt. Suno auto-detects custom-mode and uses your lyrics verbatim.

```
[SUNO_GENERATE:From Rooftops to Results — country pop, upbeat, [Verse 1] Started on a roof with hammer in hand / Twenty years building across this land [Chorus] From rooftops to results that's how I roll]
```

---

## Method 3: Direct API Call

Use when you need the `job_id` (for status polling) or building a canvas page.

### Generate a full song
```bash
curl -s -X POST http://openvoiceui:5001/api/suno \
  -H "Content-Type: application/json" \
  -H "X-Agent-Key: $AGENT_API_KEY" \
  -d '{"action":"generate","prompt":"upbeat corporate background music, no vocals","title":"Office Vibes","style":"corporate, instrumental","instrumental":true}'
```

### Generate a jingle
```bash
curl -s -X POST http://openvoiceui:5001/api/suno \
  -H "Content-Type: application/json" \
  -H "X-Agent-Key: $AGENT_API_KEY" \
  -d '{"action":"jingle","brand":"Acme Plumbing","style":"country","vocal_gender":"m","instrumental":false}'
```

### Check status
```bash
curl -s "http://openvoiceui:5001/api/suno?action=status&job_id=$JOB_ID"
```
Returns `{action: "generating" | "complete" | "failed", ...}`. Only check status if the user explicitly asks "is it done?".

### List songs / jingles / styles
```bash
curl -s "http://openvoiceui:5001/api/suno?action=list"            # all generated tracks
curl -s "http://openvoiceui:5001/api/suno?action=list_jingles"    # only jingles
curl -s "http://openvoiceui:5001/api/suno?action=jingle_styles"   # available preset keys
curl -s "http://openvoiceui:5001/api/suno?action=credits"         # remaining Suno credits
```

### Files on disk

Generated audio is saved to **`/home/node/.openclaw/workspace/generated_music/<filename>.mp3`** — agent has read-write access. Metadata at `generated_music/generated_metadata.json` with `kind: "song" | "jingle"`, `brand`, `style_key`, `vocal_gender`, `instrumental`, `duration_seconds`, `lyrics`, `created_date`.

To read lyrics for a generated track:
```bash
jq -r '.[$file].lyrics // empty' --arg file 'acme-plumbing-jingle.mp3' /home/node/.openclaw/workspace/generated_music/generated_metadata.json
```

---

## When Things Fail

If generation fails (Suno API error, quota exceeded, content rejected), the system pushes to `failed_songs_queue`. On the **next user turn**, the agent's context will include:

```
[Suno generation FAILED: 'Acme Plumbing' — content policy violation — apologize to user and offer to try again]
```

When you see this, **tell the user it failed** with the reason in plain English, and offer to try a different style/brand. Do NOT silently swallow the failure.

The voice user also sees an error banner in the actions panel — but the agent owning the conversation is responsible for explaining what happened.

---

## Full Endpoint Catalog (sunoapi.org — credit costs)

**Each credit = $0.005 USD.** The local `/api/suno` endpoint wraps the most common operations. For others, you'd extend `routes/suno.py`.

### Music generation
| Endpoint | Credits | Cost | Local action |
|---|---|---|---|
| Generate Music (V5.5 / V5 / V4.5+ / V4.5 / V4 / V4.5ALL) | 12 | $0.060 | `?action=generate` |
| **Sounds Generation (V5_5)** — short SFX/stingers, NOT vocal jingles | **2.5** | **$0.0125** | `?action=sfx` ✅ |
| Extend Music (V5 / V4.5+ / V4.5 / V4 / V4.5ALL) | 12 | $0.060 | not yet wrapped |
| Upload And Cover Audio | 12 | $0.060 | not yet wrapped |
| Upload And Extend Audio | 12 | $0.060 | not yet wrapped |
| Add Instrumental | 12 | $0.060 | not yet wrapped |
| Add Vocals | 12 | $0.060 | not yet wrapped |
| Replace Music Section | 5 | $0.025 | not yet wrapped |
| Generate Music Cover | 0 | free | not yet wrapped |

### Lyrics
| Endpoint | Credits | Cost | Notes |
|---|---|---|---|
| Generate Lyrics (creates new lyrics from a prompt) | 0.4 | $0.002 | not yet wrapped |
| Get Timestamped Lyrics (per-syllable timing for an existing track) | 0.5 | $0.0025 | not yet wrapped |

**For pulling the lyrics OF an already-generated song:** the lyrics are already returned in the original `/api/v1/generate` response and stored locally in `generated_metadata.json` under `lyrics`. **No extra API call required** unless you need timestamped per-syllable timing for karaoke-style display.

### Audio post-processing
| Endpoint | Credits | Cost |
|---|---|---|
| Convert to WAV Format | 0.4 | $0.002 |
| Separate Vocals from Music (acapella + instrumental tracks) | 10 | $0.050 |
| Split Stem (drums/bass/vocals/other separation) | 50 | $0.250 |
| Boost Music Style (style-prompt enhancer) | 0.4 | $0.002 |

### Video
| Endpoint | Credits | Cost |
|---|---|---|
| Create Music Video | 2 | $0.010 |

### Polling / metadata (free)
- Get Music Generation Details — `/api/v1/generate/record-info?taskId=…`
- Get Remaining Credits — `?action=credits` locally
- Get Music Cover Details, Get Lyrics Generation Details, Get WAV Conversion Details, Get Vocal Separation Details, Get Music Video Details — all 0 credits
- Generate Persona — 0 credits (creates a reusable voice/style persona)

### Cost rules of thumb
- **Jingle (default tool here):** 12 credits = $0.06. Same cost as a full song. The Suno "Sounds Generation" endpoint at 2.5 credits is for SFX/ambient stingers, NOT vocal jingles — don't confuse them.
- A jingle-maker session of 5 attempts = ~$0.30. Quote that to clients pricing this as a service.
- Suno returns 2 clips per generation; we already keep only the first. (No way to suppress the 2nd; you pay for both.)

---

## Good Prompt Examples (Full Songs)

- `"upbeat professional corporate background music, no vocals, warm piano and strings, 110 BPM"`
- `"lo-fi hip hop beats for focus and productivity, chill instrumental, soft drums, 85 BPM"`
- `"smooth jazz for a relaxed professional office, saxophone and piano, instrumental"`
- `"epic cinematic orchestral music with heavy strings and percussion, no vocals"`
- `"fun energetic pop song about a contractor who became an insurance expert"`

**Be descriptive:** include genre, instruments, mood, tempo, and vocal preference.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Jingle came out long (full song instead of 10-15s) | The recipe truncated `, [Intro` was missing — verify you used `[JINGLE_GENERATE:]` (server forces it), not raw `[SUNO_GENERATE:]` |
| Jingle is always teenage pop | You left `style` empty AND it picked a stale preset — pass an explicit style key |
| Brand pronounced as one word ("openvoiceui") | Spell phonetically: `Open Voice U-I` |
| Vocal style mismatched with gender | Some preset descriptors have a fixed gender feel (e.g. orchestral choir is mixed). Force with `gender=f` if you want a female lead. |
| Song failed silently | Now surfaces — agent gets `[Suno generation FAILED: ...]` on next turn. Tell the user. |
| `/api/suno/generate` returns 404 | Wrong path. Use `POST /api/suno` with `{"action":"generate"}` or `{"action":"jingle"}`. |
| Lyrics not showing | They're in `generated_metadata.json` under `lyrics`. If empty, Suno didn't return them (rare for vocal generations). |

---

## What NOT To Do

- ❌ Call `https://api.sunoapi.org/...` directly — wrong, use local endpoint
- ❌ Use `[SUNO_GENERATE:]` for short jingles — won't be short, will cost the same. Use `[JINGLE_GENERATE:]`.
- ❌ Use the Suno "Sounds Generation (V5)" endpoint thinking it makes vocal jingles — it doesn't, that endpoint is for SFX/ambient stingers without vocals
- ❌ Save audio files to `/home/mike/...` or anywhere outside `generated_music/` — system handles saves
- ❌ Poll for status after firing a tag — async, just tell the user to wait
- ❌ Tell the user "I made a jingle" before the system has confirmed completion — wait for the queue notification on next turn, OR check the canvas at `/pages/jingle-maker.html`
- ❌ Silently ignore a failure — when `[Suno generation FAILED: ...]` appears in your context, ALWAYS tell the user
- ❌ **Include real artist or band names in any prompt, style, or tags** — Suno rejects prompts containing known artist names (e.g. "Taylor Swift style", "like The Beatles", "Metallica-inspired"). Describe the sound instead using genre, mood, instruments, tempo, and era (e.g. "heavy distorted guitar riffs, double kick drums, aggressive thrash metal" instead of "like Metallica").

---

## Suno Website Subscription vs. API — Capability & Commercial-License Comparison (2026-07-05)

**Why this exists:** Theme 5b of the 2026-07-02 admin-research meeting agenda asked whether JamBot should buy a Suno **website** subscription (suno.com Pro/Premier) *alongside* our existing **API** integration (`api.sunoapi.org`, documented above). Researched live 2026-07-05 — do not treat as cached, Suno's plans/models/legal posture change fast.

### ⚠️ Headline finding — read this before the table

**`api.sunoapi.org` is NOT an official Suno product, and it is not a reseller of Suno's commercial license.** Suno itself has no public official API as of 2026-07-05 — third-party developers reverse-engineered Suno's private web-app API and wrap it as a paid service. Per independent legal analysis: *"Unofficial API access violates Suno's ToS regardless of the commercial rights situation"* and third-party providers *"cannot guarantee those promises legally, since they operate outside Suno's authorized ecosystem"* ([aimlapi.com](https://aimlapi.com/blog/the-suno-api-reality)). `sunoapi.org`'s own marketing claims ("watermark-free," "unlimited commercial use rights") are the reseller's language, not a license Suno has granted.

**This is JamBot's current — and only — Suno generation path**, used commercially across every tenant (AI-Radio public catalog, client jingles/audio-logos, voice-agent songs). This is a compliance/legal-exposure item, not just a feature gap. Flagging per `feedback_every_system_needs_monitoring` / deferred-work-must-be-owned discipline — this needs an explicit Mike decision, not silent continuation.

**Timing note:** On 2026-07-03 — two days before this research — Suno's CPO publicly announced the company is *exploring* a curated, partner-only developer API ahead of a "partner-powered model" ([Music Business Worldwide](https://www.musicbusinessworldwide.com/suno-explores-developer-api-seeking-apps-that-unlock-experiences-generative-music-makes-possible-for-the-first-time/), [Digital Music News](https://www.digitalmusicnews.com/2026/07/03/suno-is-opening-an-api-partner-program/)). No public timeline, no pricing, application via intake form only. **This is the one thing that would change the recommendation below** — see Verdict.

### Comparison table

| Feature / Term | Website Subscription (suno.com) | API (`api.sunoapi.org` — what we use today) |
|---|---|---|
| **Official / authorized** | Yes — Suno's own first-party product | **No** — unofficial reverse-engineered wrapper of Suno's private web API; Suno has no public official API (Suno partner-API program only just announced, not live) |
| **Cost** | Free $0/mo · **Pro** $8/mo (billed annually, $10 month-to-month) · **Premier** $24/mo (billed annually, $30 month-to-month) — [suno.com/pricing](https://suno.com/pricing) | Subscription-only fixed-credit tiers, third-party estimates put the range at **$19–$199/mo** ([sunor.cc](https://sunor.cc/blog/suno-api-pricing-2026)) — **UNVERIFIED**: no authoritative price sheet found; sunoapi.org's own pricing page returned HTTP 403 to automated fetch, could not confirm exact figures live |
| **Credits** | Free: 50/day (~10 songs/day). Pro: 2,500/mo (~500 songs). Premier: 10,000/mo (~2,000 songs). [suno.com/pricing](https://suno.com/pricing) | Per-operation credit costs documented in `reference/endpoint-catalog-full-api.md` (e.g. SFX = 2.5 credits); plan-level credit *allotments* not independently verified live |
| **Models exposed** | Free: v4.5-all only. Pro/Premier: **v5.5** (latest, voice-personalized) — [suno.com/pricing](https://suno.com/pricing) | v4, v4.5, v4.5 Plus, v4.5 All, **v5**, **v5.5** all exposed ([docs.sunoapi.org](https://docs.sunoapi.org/)) — matches or exceeds website tier access; this skill already defaults to `V5_5` |
| **Stems / multitrack** | Pro: "2 stem separation types." Premier: "3 stem separation types" + Suno Studio. [suno.com/pricing](https://suno.com/pricing) | Two endpoints exist: `separate_vocals` (2-way vocals+instrumental — the ONLY one wired into this skill/reference catalog today) and `split_stem` (up to **12** discrete stems: vocals, backing vocals, drums, bass, guitar, keys, strings, brass, woodwinds, percussion, synth, FX — [docs.sunoapi.org](https://docs.sunoapi.org/suno-api/separate-vocals-from-music)). API's underlying capability exceeds the website tiers; **we just haven't implemented `split_stem` yet** — an "add later" opportunity, not a gap that needs a subscription. |
| **Editing / inpainting** | Pro: "advanced editing capabilities." Premier: full "Suno Studio" DAW-style editor + custom model tuning. [suno.com/pricing](https://suno.com/pricing) | No interactive editor — `extend`, `cover`, `add_vocals`, `add_instrumental` cover overlapping ground programmatically, but there's no human-driven DAW UI (not usable by our automated agent pipeline anyway) |
| **Personas** (reusable voice/style identity across songs) | Pro + Premier, early-access beta: 200 free Persona songs, then 10 credits/song — [suno.com/blog/personas](https://suno.com/blog/personas) | **Not exposed** by `api.sunoapi.org`; no equivalent in our integration — this is the one genuine capability gap for consistent per-tenant "artist voice" across a catalog (relevant to AI-Radio) |
| **Commercial use rights** | Granted **only** for songs generated on suno.com **while actively subscribed** to Pro or Premier — Suno "assigns all right, title and interest" in that output ([help.suno.com/9601665](https://help.suno.com/en/articles/9601665)). Free tier = personal/non-commercial only, Suno attribution required, and upgrading later is **NOT retroactive**. | Marketed by the reseller as unrestricted commercial use, but this is **not a license Suno has authorized** — see headline finding. No tier of Suno's own ToS extends rights to third-party-wrapper output. |
| **Legal exposure** | Governed directly by Suno's own ToS/EULA as a paying, in-good-standing customer — the most defensible position available today | Two stacked risks: (1) ToS violation for automated/unauthorized access regardless of reseller claims, (2) unresolved RIAA copyright litigation against Suno (filed by Sony/Universal/Warner) affects outputs "regardless of access method" ([aimlapi.com](https://aimlapi.com/blog/the-suno-api-reality)) |
| **Service stability** | Suno's own production surface, SLA-backed as a paid product | Reverse-engineered — "any change Suno makes to its web interface can break these tools overnight, with no notice and no recourse" (per third-party developer-guide analysis, [aimlapi.com](https://aimlapi.com/blog/the-suno-api-reality)) |
| **What JamBot uses today** | Not subscribed | `api.sunoapi.org` — the only Suno generation path in production, across every tenant |

### Verdict

**On features alone: no, a website subscription is not worth buying alongside the API.** Model access (v5.5) is already matched, and the API's stem-separation ceiling (`split_stem`, 12 tracks) technically exceeds what any website tier offers — we simply haven't wired it into this skill yet (candidate follow-up, not a subscription justification). Personas is the one real capability gap, and it's a nice-to-have (per-tenant "artist voice" consistency for AI-Radio), not a blocker.

**On commercial license: this is not a "buy a subscription too" decision — it's a standing legal-exposure item that a subscription does NOT fix.** Commercial rights attach *only* to output generated on suno.com itself by an active Pro/Premier subscriber ("Output generated from their submissions during the term of their paid-tier subscription"). That is a legally separate generation path from `api.sunoapi.org` output. **Subscribing to Pro/Premier alongside the API does not retroactively or prospectively license anything the API generates.** The two paths don't touch. JamBot's current commercial generation (AI-Radio catalog, client jingles, voice-agent songs) runs entirely on the unlicensed path today.

**Recommendation:**
1. Do not buy a website subscription as a feature workaround — nothing on it is worth paying for given current API capability.
2. **Do** treat the commercial-license gap on `api.sunoapi.org` as an owned, tracked risk (not a "someday" item) — it has run since this skill's inception with no Mike sign-off on the exposure, because the original assumption ("commercial license attaches to the paid tier in both cases," per the 2026-07-02 admin-research first-pass) was incorrect.
3. **Apply now** for Suno's newly-announced curated developer-partner API (intake form via [Jack Brody's announcement](https://www.musicbusinessworldwide.com/suno-explores-developer-api-seeking-apps-that-unlock-experiences-generative-music-makes-possible-for-the-first-time/), CPO, 2026-07-03) — this is the one thing that would flip the recommendation: if JamBot is accepted, that becomes the sanctioned, licensed replacement for `api.sunoapi.org`, at whatever price/credit terms Suno sets, and the whole comparison above resets around it.

**Could not verify from a live source (flagged, not guessed):**
- `sunoapi.org`'s exact pricing tiers/credit allotments — their own pricing page returned HTTP 403 to automated fetch; the $19–$199/mo figure is a third-party estimate, not sunoapi.org's own published number.
- Whether Pro vs. Premier differ in commercial-rights *scope* (e.g. sync licensing, distribution) beyond both simply being "granted" — help.suno.com's rights article did not distinguish between the two tiers.
- Suno's partner-API program pricing, timeline, or acceptance criteria — announcement was an intake form only as of 2026-07-03, no further detail published.

**Sources:** [suno.com/pricing](https://suno.com/pricing) · [suno.com/terms-of-service](https://suno.com/terms-of-service) · [help.suno.com/9601665 — paid subscriber rights](https://help.suno.com/en/articles/9601665) · [suno.com/blog/personas](https://suno.com/blog/personas) · [docs.sunoapi.org](https://docs.sunoapi.org/) · [docs.sunoapi.org — stem separation](https://docs.sunoapi.org/suno-api/separate-vocals-from-music) · [aimlapi.com — Suno API Reality (legal risk analysis)](https://aimlapi.com/blog/the-suno-api-reality) · [evolink.ai — Suno API Review](https://evolink.ai/blog/suno-api-review-complete-guide-ai-music-generation-integration) · [Music Business Worldwide — Suno explores developer API](https://www.musicbusinessworldwide.com/suno-explores-developer-api-seeking-apps-that-unlock-experiences-generative-music-makes-possible-for-the-first-time/) · [Digital Music News — Suno API Partner Program](https://www.digitalmusicnews.com/2026/07/03/suno-is-opening-an-api-partner-program/)
