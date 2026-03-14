---
name: suno-music
description: Generate AI music using Suno API - create songs from text, custom lyrics, extend tracks, and more
metadata: {"openclaw": {"emoji": "🎵"}}
---

# Suno Music Generation Skill

Generate AI songs for the user. Songs take **45–90 seconds** to generate and auto-appear in the music player.

---

## ⚠️ CRITICAL: How Generation Works

**NEVER call `https://api.sunoapi.org` directly. NEVER call `/api/suno/generate`. NEVER call `/api/music/suno/generate`.** Those are wrong.

There are **two correct methods** — pick one:

---

## Method 1: Voice Tag (ALWAYS USE THIS)

Include one or more `[SUNO_GENERATE:]` tags anywhere in your response:

```
[SUNO_GENERATE:upbeat corporate background music for an insurance office, professional and energizing, no vocals, 120 BPM]
```

**Rules:**
- The tag is stripped before TTS — the user won't hear you say it, they'll just hear your words
- You will NOT get a confirmation back — **this is normal**. The song IS being generated.
- Generation takes **45–90 seconds**. Tell the user to wait, then it'll appear in the player.
- To generate **3 songs at once**: put **3 tags** in your response — they all start simultaneously

**Example response making 3 songs:**
```
I'm cooking up three tracks for your office! Give me about a minute and they'll all be ready.

[SUNO_GENERATE:upbeat professional corporate background music, no vocals, warm piano and soft strings, 110 BPM]
[SUNO_GENERATE:lo-fi hip hop beats for focus and productivity, chill instrumental, soft drums and warm piano, 85 BPM]
[SUNO_GENERATE:smooth jazz background for a relaxed professional office vibe, saxophone and piano, no vocals]
```

**IMPORTANT: After emitting the tags, move on. Do NOT try to poll, check status, or verify. Just tell the user the songs will appear in ~60 seconds.**

---

## Method 2: Direct API Call (for advanced/programmatic use)

Use this when you need the `job_id` to check status later, or when building a canvas page.

```bash
curl -s -X POST http://openvoiceui:5001/api/suno \
  -H "Content-Type: application/json" \
  -H "X-Agent-Key: $AGENT_API_KEY" \
  -d '{
    "action": "generate",
    "prompt": "upbeat corporate background music, no vocals",
    "title": "Office Vibes",
    "style": "corporate, instrumental",
    "instrumental": true
  }'
```

Response:
```json
{
  "action": "generating",
  "job_id": "abc-123",
  "task_id": "suno-task-xyz",
  "response": "Cooking! 'Office Vibes' is being generated — check back in 30-60 seconds.",
  "estimated_seconds": 45
}
```

**Save the `job_id` — you'll need it to check status.**

---

## Checking Status

Only check status if the **user explicitly asks** "is my song done?" or similar.

```bash
curl -s -X POST http://openvoiceui:5001/api/suno \
  -H "Content-Type: application/json" \
  -H "X-Agent-Key: $AGENT_API_KEY" \
  -d '{"action": "status", "job_id": "abc-123"}'
```

Status values: `generating` | `complete` | `failed`

When `complete`, the song is already saved and in the player — no further action needed.

---

## Listing Songs

```bash
curl -s http://openvoiceui:5001/api/suno?action=list \
  -H "X-Agent-Key: $AGENT_API_KEY"
```

Returns all generated songs with titles, URLs, and metadata.

---

## Generate Params

| Field | Type | Description |
|-------|------|-------------|
| `prompt` | string | Music description (style, mood, instruments, BPM) |
| `title` | string | Song title (optional) |
| `style` | string | Genre/style tags (optional, e.g. "lo-fi, chill, instrumental") |
| `lyrics` | string | Custom lyrics — use `[Verse]`/`[Chorus]` tags (omit for auto-lyrics) |
| `instrumental` | bool | `true` = no vocals (default false) |
| `vocal_gender` | string | `"m"` or `"f"` (default "m") |

---

## Good Prompt Examples

- `"upbeat professional corporate background music, no vocals, warm piano and strings, 110 BPM"`
- `"lo-fi hip hop beats for focus and productivity, chill instrumental, soft drums, 85 BPM"`
- `"smooth jazz for a relaxed professional office, saxophone and piano, instrumental"`
- `"epic cinematic orchestral music with heavy strings and percussion, no vocals"`
- `"fun energetic pop song about a contractor who became an insurance expert"`

**Be descriptive**: include genre, instruments, mood, tempo, and vocal preference.

---

## Custom Lyrics Example

Via tag (put lyrics inside the tag):
```
[SUNO_GENERATE:From Rooftops to Results — country pop, upbeat, [Verse 1] Started on a roof with hammer in hand / Twenty years building across this land [Chorus] From rooftops to results that's how I roll / From the job site to policies heart and soul]
```

Or via direct API:
```json
{
  "action": "generate",
  "title": "From Rooftops to Results",
  "style": "country pop, upbeat",
  "lyrics": "[Verse 1]\nStarted on a roof with hammer in hand\n[Chorus]\nFrom rooftops to results that's how I roll"
}
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Song not appearing after 90s | Ask user to refresh the music panel |
| Agent says "not working" | Wrong — tags ARE working. Agent just doesn't get confirmation. Trust the tag. |
| 401 error on `/api/suno/generate` | That URL doesn't exist. Use `POST /api/suno` with `{"action":"generate"}` |
| 404 on `/api/music/suno/generate` | That URL doesn't exist. Use `POST /api/suno` |
| Want 3 songs | Put 3 `[SUNO_GENERATE:]` tags in ONE response |

---

## What NOT To Do

- ❌ `curl https://api.sunoapi.org/...` — wrong, don't call external API directly
- ❌ `/api/suno/generate` — wrong path
- ❌ `/api/music/suno/generate` — wrong path
- ❌ Saving files to `/home/mike/WEBSITES/...` — wrong path, system handles saves automatically
- ❌ Polling for status after emitting a tag — unnecessary, just tell user to wait
- ❌ Telling the user generation failed when you used the tag — it didn't fail, it's async
