---
name: suno-music
description: Generate AI music and sounds using Suno API - create songs, sounds, SFX, extend tracks, add vocals, mashups, and more
metadata: {"openclaw": {"emoji": "🎵"}}
---

# Suno Music Generation Skill

## Documentation Index
Fetch the complete documentation index at: https://docs.sunoapi.org/llms.txt
Use this file to discover all available pages before exploring further.

## Overview
This skill enables OpenClaw agents to generate AI music and sounds using the **official Suno API at https://api.sunoapi.org**. Generate full songs, sound effects, ambient loops, custom lyrics, extend tracks, add vocals, create mashups, and much more.

**Base URL**: `https://api.sunoapi.org`
**Documentation**: https://docs.sunoapi.org/
**Support**: support@sunoapi.org

### Supported AI Models
| Model | Description | Best For |
|-------|-------------|-----------|
| `V4` | Refined song structure | Structured pieces, up to 4 min |
| `V4_5` | Smart prompts, conversational style guidance | Complex music requests |
| `V4_5PLUS` | Richer tones, default for vocals/instrumental endpoints | Highest quality |
| `V4_5ALL` | Better song composition, 1-min max on upload endpoints | Well-structured pieces |
| `V5` | Superior musical expression, faster generation | Advanced music generation |
| `V5_5` | Custom models tailored to unique taste | Most expressive, latest |

**Default model for most generation endpoints**: `V5` or `V5_5`
**Sounds endpoint**: Supports `V5` and `V5_5` (docs say V5-only but V5_5 confirmed working via live test)
**Add Vocals / Add Instrumental default**: `V4_5PLUS`

---

## Configuration

### Required Environment Variables
```bash
SUNO_API_BASE="https://api.sunoapi.org"
SUNO_API_KEY="your-api-key-here"
SUNO_CALLBACK_URL="https://your-domain.com/api/suno/callback"  # optional
```

### Authentication
**Header**: `Authorization: Bearer YOUR_API_KEY`
**Get API key**: https://sunoapi.org/api-key

---

## Status Polling

All generation endpoints return a `taskId`. Poll for results with:

**Endpoint**: `GET https://api.sunoapi.org/api/v1/generate/record-info?taskId=<taskId>`

**Response**:
```json
{
  "code": 200,
  "data": {
    "taskId": "...",
    "status": "SUCCESS",
    "operationType": "sounds",
    "response": {
      "sunoData": [
        {
          "id": "audio-uuid",
          "audioUrl": "https://...",
          "sourceAudioUrl": "https://cdn1.suno.ai/...",
          "streamAudioUrl": "https://...",
          "imageUrl": "https://...",
          "title": "Track Title",
          "tags": "ambient, rain",
          "modelName": "chirp-fenix",
          "duration": 11.2,
          "createTime": 1780002218360
        }
      ]
    }
  }
}
```

**Status values**: `SUCCESS`, `FAILED`, `PROCESSING`

---

## 🎵 Music & Sound Generation APIs

### 1. Generate Music
**Endpoint**: `POST https://api.sunoapi.org/api/v1/generate`

```json
{
  "model": "V5_5",
  "custom": false,
  "instrumental": false,
  "prompt": "A heavy metal track with aggressive guitar riffs and thundering drums",
  "callBackUrl": "https://your-domain.com/callback"
}
```

**Fields**:
- `model` (str, required): `V4`, `V4_5`, `V4_5PLUS`, `V4_5ALL`, `V5`, `V5_5`
- `custom` (bool): `false` = prompt mode, `true` = custom mode with lyrics
- `instrumental` (bool): `true` = no vocals
- `prompt` (str): Music description (prompt mode) or custom lyrics (custom mode)
- `style` (str): Genre/style tags — required in custom mode
- `title` (str): Song title — required in custom mode
- `negativeTags` (str): Styles to exclude
- `vocalGender` (str): `m` or `f`
- `callBackUrl` (str): Webhook URL

---

### 2. Generate Sounds
Create sound effects, ambient loops, game audio, and background sounds.

**Endpoint**: `POST https://api.sunoapi.org/api/v1/generate/sounds`

```json
{
  "prompt": "A soft rain ambience with distant thunder and gentle wind",
  "model": "V5_5",
  "soundLoop": true,
  "soundTempo": 120,
  "soundKey": "Any",
  "grabLyrics": false,
  "callBackUrl": "https://your-domain.com/callback"
}
```

**Fields**:
- `prompt` (str, required): Sound description. Max 500 characters.
- `model` (str, required): `V5` or `V5_5` — sounds tasks only support these two. **V5_5 confirmed working.**
- `soundLoop` (bool): Enable loop playback. Default `false`. Ideal for ambient/background use.
- `soundTempo` (int): BPM (1–300). Omit for auto.
- `soundKey` (str): Pitch key. Default `Any`. Options: `Any`, `C`, `C#`, `D`, `D#`, `E`, `F`, `F#`, `G`, `G#`, `A`, `A#`, `B`, `Cm`, `C#m`, `Dm`, `D#m`, `Em`, `Fm`, `F#m`, `Gm`, `G#m`, `Am`, `A#m`, `Bm`
- `grabLyrics` (bool): Fetch lyric subtitle data after completion.
- `callBackUrl` (str): Webhook URL.

**Usage Scenarios**: Background music loops, game SFX, ambient sounds, audio platform integrations

---

### 3. Extend Music
**Endpoint**: `POST https://api.sunoapi.org/api/v1/generate/extend`

```json
{
  "audioId": "song-uuid",
  "model": "V5",
  "defaultParamFlag": true,
  "prompt": "add a dramatic bridge section",
  "style": "epic orchestral",
  "title": "My Extended Track",
  "continueAt": 90,
  "callBackUrl": "https://your-domain.com/callback"
}
```

**Fields**:
- `audioId` (str, required): ID of the track to extend
- `model` (str, required): Model version
- `defaultParamFlag` (bool, required): `true` = use custom params below; `false` = auto-extend from original audio settings
- `prompt` (str): Extension direction — required when `defaultParamFlag: true` and `instrumental: false`
- `style` (str): Genre/style — required when `defaultParamFlag: true`
- `title` (str): Track title — required when `defaultParamFlag: true`
- `continueAt` (number): Timestamp (seconds) to continue from
- `callBackUrl` (str): Webhook URL
- `personaId`, `personaModel`, `negativeTags`, `vocalGender`, `styleWeight`, `weirdnessConstraint`, `audioWeight` (optional)

---

### 4. Upload and Cover Audio
Transform existing audio in a new style.

**Endpoint**: `POST https://api.sunoapi.org/api/v1/generate/upload-cover`

```json
{
  "uploadUrl": "https://example.com/original.mp3",
  "model": "V5",
  "customMode": false,
  "instrumental": false,
  "prompt": "make it a lo-fi jazz version",
  "callBackUrl": "https://your-domain.com/callback"
}
```

**Fields**:
- `uploadUrl` (str, required): Audio file URL. Max 8 min (1 min for `V4_5ALL`)
- `model` (str, required): `V4`, `V4_5`, `V4_5PLUS`, `V4_5ALL`, `V5`, `V5_5`
- `customMode` (bool, required): `true` = custom mode (requires `style`, `title`); `false` = auto
- `instrumental` (bool, required): `true` = no vocals
- `prompt` (str): Auto-generated lyrics concept (non-custom) or exact lyrics (custom, non-instrumental)
- `style` (str): Genre — required when `customMode: true`
- `title` (str): Title — required when `customMode: true`
- `negativeTags`, `vocalGender`, `styleWeight`, `weirdnessConstraint`, `audioWeight`, `personaId`, `personaModel` (optional)

---

### 5. Upload and Extend Audio
Upload audio and extend it.

**Endpoint**: `POST https://api.sunoapi.org/api/v1/generate/upload-extend`

```json
{
  "uploadUrl": "https://example.com/partial.mp3",
  "model": "V5",
  "defaultParamFlag": false,
  "prompt": "continue with a high-energy chorus",
  "callBackUrl": "https://your-domain.com/callback"
}
```

**Fields**:
- `uploadUrl` (str, required): Audio URL. Max 8 min (1 min for `V4_5ALL`)
- `model` (str, required): `V4`, `V4_5`, `V4_5PLUS`, `V4_5ALL`, `V5`, `V5_5`
- `defaultParamFlag` (bool, required): `false` = only `prompt` needed; `true` = also requires `style`, `title`
- `prompt` (str): Extension direction
- `style`, `title`: Required when `defaultParamFlag: true`
- Prompt limit: 3,000 chars (V4) or 5,000 chars (V4_5+); Style limit: 200 (V4) or 1,000 (V4_5+)

---

### 6. Add Vocals
Add AI vocals to an instrumental track.

**Endpoint**: `POST https://api.sunoapi.org/api/v1/generate/add-vocals`

```json
{
  "uploadUrl": "https://example.com/instrumental.mp3",
  "prompt": "soulful, emotional lyrics about resilience",
  "title": "Resilient",
  "style": "Soul, R&B",
  "negativeTags": "rap",
  "model": "V5_5",
  "vocalGender": "f",
  "callBackUrl": "https://your-domain.com/callback"
}
```

**Fields**:
- `uploadUrl` (str, required): Instrumental audio URL
- `prompt` (str, required): Vocal content and style description
- `title` (str, required): Track title (max 100 chars)
- `negativeTags` (str, required): Styles/traits to exclude
- `style` (str, required): Music and vocal genre
- `model` (str): `V4_5PLUS` (default), `V5`, or `V5_5`
- `vocalGender` (str): `m` or `f`
- `styleWeight`, `weirdnessConstraint`, `audioWeight` (optional, 0.00–1.00)
- `callBackUrl` (str, required): Webhook URL

---

### 7. Add Instrumental
Generate backing music for a vocal track.

**Endpoint**: `POST https://api.sunoapi.org/api/v1/generate/add-instrumental`

```json
{
  "uploadUrl": "https://example.com/vocals.mp3",
  "title": "Electric Dreams",
  "tags": "electronic, synthwave",
  "negativeTags": "acoustic",
  "model": "V5_5",
  "callBackUrl": "https://your-domain.com/callback"
}
```

**Fields**:
- `uploadUrl` (str, required): Vocal audio URL
- `title` (str, required): Track title (max 100 chars)
- `tags` (str, required): Desired instrumental style
- `negativeTags` (str, required): Styles/instruments to exclude
- `model` (str): `V4_5PLUS` (default), `V5`, or `V5_5`
- `vocalGender`, `styleWeight`, `audioWeight`, `weirdnessConstraint` (optional)
- `callBackUrl` (str, required): Webhook URL

---

### 8. Generate Mashup
Blend two audio tracks together.

**Endpoint**: `POST https://api.sunoapi.org/api/v1/generate/mashup`

```json
{
  "uploadUrlList": ["https://example.com/track1.mp3", "https://example.com/track2.mp3"],
  "model": "V5",
  "customMode": false,
  "instrumental": false,
  "callBackUrl": "https://your-domain.com/callback"
}
```

**Fields**:
- `uploadUrlList` (array, required): Exactly 2 audio file URLs
- `model` (str, required): `V4`, `V4_5`, `V4_5PLUS`, `V4_5ALL`, `V5` (V5_5 not listed for mashup)
- `customMode` (bool, required): `true` = requires `style`, `title`, `prompt`
- `instrumental` (bool): No vocals if `true`
- `prompt`, `style`, `title`: Required in custom mode
- `vocalGender`, `styleWeight`, `weirdnessConstraint`, `audioWeight` (optional)
- `callBackUrl` (str, required): Webhook URL

---

## ✍️ Lyrics Creation APIs

### 9. Generate Lyrics
**Endpoint**: `POST https://api.sunoapi.org/api/v1/lyrics`

```json
{
  "prompt": "A song about a robot falling in love with a toaster",
  "callBackUrl": "https://your-domain.com/callback"
}
```

**Fields**:
- `prompt` (str, required): Desired lyrics content. Max 200 characters.
- `callBackUrl` (str, required): Webhook URL

Returns multiple lyric variations. Retained for 15 days.

---

### 10. Get Timestamped Lyrics
**Endpoint**: `GET https://api.sunoapi.org/get_lyrics_timeline?song_id=<song_id>`

Returns lyrics with per-line timestamps for karaoke/sync use.

---

## 🔊 Audio Processing APIs

### 11. Separate Vocals from Music
**Endpoint**: `POST https://api.sunoapi.org/separate_vocals`

```json
{ "audio_url": "https://example.com/song.mp3" }
```

Returns separate `vocals_url` and `instrumental_url`.

---

### 12. Convert to WAV Format
**Endpoint**: `POST https://api.sunoapi.org/api/v1/wav/generate`

```json
{
  "taskId": "music-generation-task-id",
  "audioId": "specific-track-id",
  "callBackUrl": "https://your-domain.com/callback"
}
```

**Fields**: `taskId` + `audioId` from a completed generation task.

---

### 13. Boost Music Style
Generate a refined style description for use in generation prompts.

**Endpoint**: `POST https://api.sunoapi.org/api/v1/style/generate`

```json
{ "content": "Pop, Mysterious, melancholic but uplifting" }
```

**Fields**:
- `content` (str, required): Concise style description. V4_5+ accepts conversational language.

Returns an enhanced style string to use in other generation endpoints.

---

## 🎬 Music Video API

### 14. Create Music Video
**Endpoint**: `POST https://api.sunoapi.org/api/v1/mp4/generate`

```json
{
  "taskId": "music-generation-task-id",
  "audioId": "specific-track-id",
  "author": "Artist Name",
  "domainName": "jam-bot.com",
  "callBackUrl": "https://your-domain.com/callback"
}
```

**Fields**:
- `taskId` + `audioId` (required): From a completed generation task
- `author` (str): Displayed on video (max 50 chars)
- `domainName` (str): Watermark at bottom (max 50 chars)
- `callBackUrl` (str, required): Webhook URL

---

## 🛠️ Utility APIs

### 15. Get Task Status / Music Details
**Endpoint**: `GET https://api.sunoapi.org/api/v1/generate/record-info?taskId=<taskId>`

Returns full task status and `sunoData` array with all track fields. See **Status Polling** section above for full response schema.

### 16. Get Remaining Credits
**Endpoint**: `GET https://api.sunoapi.org/api/v1/generate/credit`

```json
{ "code": 200, "msg": "success", "data": 100 }
```

Returns integer credit balance. Each operation consumes credits based on feature. Credit exhaustion returns error code 429.

### 17–21. Other Status Endpoints
Use `taskId` returned from each endpoint to poll these:
- Lyrics details: `GET /api/v1/lyrics/record-info?taskId=`
- WAV details: `GET /api/v1/wav/record-info?taskId=`
- Video details: `GET /api/v1/mp4/record-info?taskId=`
- Separation details: `GET /api/v1/separate/record-info?taskId=`

---

## Style Tags Reference

**Electronic**: `electronic, edm, techno, house, trance, drum-and-bass, dubstep, trap, lo-fi, synthwave, vaporwave`
**Rock/Metal**: `rock, metal, punk, alternative, grunge, heavy-metal, thrash-metal, progressive-rock`
**Hip-Hop/R&B**: `hip-hop, rap, r&b, soul, funk, trap, drill, boom-bap`
**Pop**: `pop, indie-pop, synth-pop, dance-pop, bubblegum-pop`
**Jazz/Blues**: `jazz, blues, swing, bebop, smooth-jazz, acid-jazz`
**Classical**: `classical, orchestral, piano, string-quartet, opera`
**World**: `reggae, afrobeat, latin, salsa, bossa-nova, k-pop`
**Moods**: `happy, sad, energetic, chill, dark, romantic, aggressive, mysterious, epic`

---

## Agent Implementation Guide

1. **Use `instrumental: true` for background music** — avoids copyright issues with generated lyrics
2. **Save all generated audio immediately** to server — never hold in memory. Download from `audioUrl` in `sunoData`.
3. **Sounds for SFX/ambient loops** → `/api/v1/generate/sounds` with `soundLoop: true`, model `V5_5`
4. **Poll with** `GET /api/v1/generate/record-info?taskId=<id>` — check `status === "SUCCESS"`
5. **Track metadata** in `generated_metadata.json` using filename as key for OpenVoiceUI compatibility
6. **Generation time**: 30–120 seconds typical. Use webhooks (`callBackUrl`) for non-blocking flow.
7. **Credits**: check `/api/v1/generate/credit` before bulk generation
8. **NEVER include real artist or band names in any prompt, style, or tags field** — Suno rejects prompts containing known artist names (e.g. "Taylor Swift style", "like The Beatles"). Describe the sound instead: use genre, mood, instrument, tempo, era (e.g. "upbeat 80s synth-pop with female vocals" instead of "like Madonna").

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Invalid parameters |
| 401 | Unauthorized |
| 404 | Invalid path/method |
| 405 | Rate limit exceeded |
| 413 | Prompt/theme too long |
| 429 | Insufficient credits |
| 430 | Call frequency too high |
| 455 | System maintenance |
| 500 | Server error |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 401 | Check API key and Bearer token format |
| No audio in record-info | Still processing — keep polling |
| 429 | Check `/api/v1/generate/credit` balance |
| 430 | Slow down requests, rate limited |
| Audio URL expired | Use `sourceAudioUrl` (CDN direct) as fallback |
| Sounds endpoint rejects model | Use `V5` or `V5_5` only — other models not supported |
| Prompt rejected / generation fails | Remove any real artist or band names — describe the style with genre/mood/instrument/era instead |

---

## Sources
- [Official Suno API Documentation](https://docs.sunoapi.org/)
- [Documentation Index](https://docs.sunoapi.org/llms.txt)
- [API Key Management](https://sunoapi.org/api-key)
- Support: support@sunoapi.org
