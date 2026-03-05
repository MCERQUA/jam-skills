---
name: suno-music
description: Generate AI music using Suno API - create songs from text, custom lyrics, extend tracks, and more
metadata: {"openclaw": {"emoji": "🎵"}}
---

# Suno Music Generation Skill

## Overview
This skill enables OpenClaw agents to generate AI music using the **official Suno API at https://api.sunoapi.org**. Generate full songs from text descriptions, create custom songs with your own lyrics, extend existing tracks, add vocals to instrumentals, and much more.

**Perfect for web applications** with built-in music players - generate songs from conversations, play them back in real-time, and build a complete music experience.

### Key Features for Web Apps
- **Async Webhooks** - Non-blocking generation with real-time callbacks
- **File Upload** - Upload reference audio for remix/extend
- **All 20 Endpoints** - Complete API coverage for any use case
- **Auto-Save** - Downloads and saves to your music folder automatically
- **Metadata Tracking** - Integrates with OpenVoiceUI player database

## Official Suno API
**Base URL**: `https://api.sunoapi.org`
**Documentation**: https://docs.sunoapi.org/
**Support**: support@sunoapi.org

### Official API Features
- **99.9% Uptime** - Reliable and stable API performance
- **Affordable Pricing** - Transparent, usage-based pricing system
- **20-Second Streaming Output** - Fast delivery with streaming response
- **High Concurrency** - 120+ concurrent tasks supported
- **24/7 Support** - Professional technical assistance
- **Watermark-Free** - Commercial-ready music generation

### Supported AI Models
| Model | Description | Max Duration | Best For |
|-------|-------------|---------------|-----------|
| `v4` | Improved Vocals - enhanced vocal quality and refined audio processing | 4 minutes | When vocal clarity is paramount |
| `v4_5` | Smart Prompts - excellent prompt understanding, faster generation | 8 minutes | Complex music requests |
| `v4_5PLUS` | Richer Tones - most advanced with enhanced tonal variation | 8 minutes | Highest quality, longest tracks |
| `v4_5ALL` | Better Song Structure - improved song composition | 8 minutes | Well-structured musical pieces |
| `v5` | Latest Model - cutting-edge with enhanced quality and capabilities | Variable | Advanced music generation (NEW) |

---

## Configuration

### Required Environment Variables
Set these in your agent config or environment:

```bash
# Official Suno API (RECOMMENDED)
SUNO_API_BASE="https://api.sunoapi.org"
SUNO_API_KEY="your-api-key-here"

# Optional: Webhook callback URL for async completion
SUNO_CALLBACK_URL="https://your-domain.com/api/suno/callback"
```

**Default Model**: This skill uses **v5** (latest model) by default.

### Authentication
For the official Suno API:
- **Header**: `Authorization: Bearer YOUR_API_KEY`
- **Get API key**: https://sunoapi.org/api-key
- All requests must include this header

### Output Directory
Generated songs are saved to: `/home/mike/WEBSITES/OpenVoiceUI/generated_music/`

---

## 🔗 Webhook/Callback Support

The API supports asynchronous webhook callbacks for real-time notifications when generation completes.

### How Webhooks Work

1. **Submit generation request** with `hookUrl` parameter
2. **API returns immediately** with task ID
3. **Generation happens asynchronously** (30-120 seconds)
4. **API POSTs to your webhook** when complete
5. **Your webhook handler** downloads and saves the music

### Webhook Configuration

```bash
# Set your webhook URL
export SUNO_CALLBACK_URL="https://your-domain.com/api/suno/callback"
```

### Webhook Payload (POST to your endpoint)

```json
{
  "task_id": "abc123",
  "status": "complete",
  "data": {
    "id": "song-id",
    "title": "Generated Title",
    "audio_url": "https://...",
    "video_url": "https://...",
    "image_url": "https://...",
    "model": "v5",
    "style": "electronic"
  }
}
```

### Webhook Status Values

- `complete` - Generation finished successfully
- `failed` - Generation failed (includes `error` field)
- `processing` - Still in progress

### Python Webhook Handler

```python
from suno_client import SunoMusicClient

client = SunoMusicClient()

# In your webhook endpoint (Flask/FastAPI/etc.)
@app.route('/api/suno/callback', methods=['POST'])
def handle_suno_webhook():
    webhook_data = request.json
    result = client.handle_webhook(webhook_data)
    return jsonify({"status": "received", "message": result})
```

### Webhook Benefits

- **Non-blocking**: Don't wait for generation to complete
- **Scalable**: Handle many concurrent generations
- **Server-to-server**: Perfect for web apps
- **Real-time**: Immediate notification when ready

---

## 📁 File Upload Support

In addition to URL-based audio processing, the client supports direct file uploads.

### Upload Methods

**generate_from_file()** - Upload audio and generate new music
```python
result = client.generate_from_file(
    file_path="/path/to/reference.mp3",
    title="Remixed Version",
    tags="electronic, darker",
    instrumental=False
)
```

**extend_from_file()** - Upload and extend audio
```python
result = client.extend_from_file(
    file_path="/path/to/partial.mp3",
    extend_prompt="add a dramatic bridge section"
)
```

### File Upload Endpoint

Files are uploaded as `multipart/form-data` to:
- `POST https://api.sunoapi.org/upload_and_cover`
- `POST https://api.sunoapi.org/upload_and_extend`

---

## 🎵 Music Generation APIs (7 Endpoints)

### 1. Generate Music
Create high-quality music from text descriptions using advanced AI models.

**Endpoint**: `POST https://api.sunoapi.org/generate`

**Request Parameters**:
```json
{
  "custom": false,
  "instrumental": false,
  "mv": "v5",
  "prompt": "A heavy metal track with aggressive guitar riffs and thundering drums",
  "gpt_description_prompt": "optional: AI generates lyrics and description"
}
```

**Fields**:
- `custom` (bool): `false` for prompt mode, `true` for custom mode
- `instrumental` (bool): `true` for instrumental only (no vocals)
- `mv` (str): Model version - `v4`, `v4_5`, `v4_5PLUS`, `v4_5ALL`, `v5`
- `prompt` (str): Music description or custom lyrics
- `gpt_description_prompt` (str): Optional inspiration mode prompt
- `hookUrl` (str): Webhook URL for completion notification

**Response**:
```json
{
  "success": true,
  "data": [{
    "id": "song-id",
    "title": "AI-generated-title",
    "image_url": "cover-art-url",
    "lyric": "lyrics-if-any",
    "audio_url": "https://...",
    "video_url": "https://...",
    "created_at": "timestamp",
    "model": "v4_5",
    "style": "metal"
  }]
}
```

---

### 2. Extend Music
Extend existing music tracks with AI-powered continuation, maintaining musical coherence and style.

**Endpoint**: `POST https://api.sunoapi.org/extend`

**Request Parameters**:
```json
{
  "aid": "song-id-to-extend",
  "bark_prompt": "continue the melody",
  "mv": "v5",
  "prompt": "make it more intense"
}
```

**Fields**:
- `aid` (str): Audio ID to extend
- `bark_prompt` (str): Extension instruction
- `mv` (str): Model version
- `prompt` (str): Additional direction for extension

---

### 3. Upload and Cover Audio
Transform existing audio with new styles and arrangements using AI music processing.

**Endpoint**: `POST https://api.sunoapi.org/upload_and_cover`

**Request Parameters**:
```json
{
  "audio_url": "https://example.com/original.mp3",
  "cover_prompt": "make it a jazz version",
  "mv": "v4_5"
}
```

**Fields**:
- `audio_url` (str): URL of the audio file to transform
- `cover_prompt` (str): Description of the desired style/arrangement
- `mv` (str): Model version to use

---

### 4. Upload and Extend Audio
Upload your own audio files and extend them with AI-generated content.

**Endpoint**: `POST https://api.sunoapi.org/upload_and_extend`

**Request Parameters**:
```json
{
  "audio_url": "https://example.com/original.mp3",
  "extend_prompt": "add a dramatic bridge section",
  "mv": "v4_5"
}
```

---

### 5. Add Vocals
Generate vocal tracks for instrumental music using advanced AI models.

**Endpoint**: `POST https://api.sunoapi.org/add_vocals`

**Request Parameters**:
```json
{
  "audio_url": "https://example.com/instrumental.mp3",
  "lyric": "lyrics for the vocal track",
  "mv": "v4_5"
}
```

**Use Case**: Add AI-generated vocals to an instrumental track with provided lyrics.

---

### 6. Add Instrumental
Create instrumental accompaniment for vocal tracks with AI-powered arrangements.

**Endpoint**: `POST https://api.sunoapi.org/add_instrumental`

**Request Parameters**:
```json
{
  "audio_url": "https://example.com/vocals.mp3",
  "mv": "v5",
  "tags": "electronic, synthwave"
}
```

**Use Case**: Generate backing music for an a cappella or vocal-only track.

---

### 7. Cover Music
Reinterpret existing music in different styles and arrangements using AI technology.

**Endpoint**: `POST https://api.sunoapi.org/cover`

**Request Parameters**:
```json
{
  "audio_url": "https://example.com/song.mp3",
  "cover_prompt": "lo-fi hip-hop remix",
  "mv": "v4_5"
}
```

**Use Case**: Create a complete cover/rearrangement in a different genre or style.

---

## ✍️ Lyrics Creation APIs (2 Endpoints)

### 8. Generate Lyrics
Create AI-powered lyrics for your songs with customizable themes and styles.

**Endpoint**: `POST https://api.sunoapi.org/generate_lyrics`

**Request Parameters**:
```json
{
  "prompt": "A song about a robot falling in love with a toaster",
  "tags": "comedy, electronic, quirky"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "lyric": "[Verse 1]\nMet in a kitchen aisle...",
    "style": "quirky electronic"
  }
}
```

---

### 9. Get Timestamped Lyrics
Retrieve lyrics with precise timestamps for synchronization with audio tracks.

**Endpoint**: `GET https://api.sunoapi.org/get_lyrics_timeline`

**Request Parameters**:
```json
{
  "song_id": "song-id"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "timeline": [
      { "time": "00:00", "lyric": "First line" },
      { "time": "00:05", "lyric": "Second line" }
    ]
  }
}
```

**Use Case**: Karaoke applications, lyric sync in music players.

---

## 🔊 Audio Processing APIs (4 Endpoints)

### 10. Separate Vocals from Music
Extract vocals and instrumental tracks separately using advanced AI audio separation.

**Endpoint**: `POST https://api.sunoapi.org/separate_vocals`

**Request Parameters**:
```json
{
  "audio_url": "https://example.com/song.mp3"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "vocals_url": "https://...",
    "instrumental_url": "https://..."
  }
}
```

---

### 11. Convert to WAV Format
Convert generated music to high-quality WAV format for professional use.

**Endpoint**: `POST https://api.sunoapi.org/convert_wav`

**Request Parameters**:
```json
{
  "song_id": "song-id"
}
```

**Use Case**: Professional audio production, studio integration.

---

### 12. Boost Music Style
Enhance and refine music styles with AI-powered audio processing.

**Endpoint**: `POST https://api.sunoapi.org/boost_style`

**Request Parameters**:
```json
{
  "audio_url": "https://example.com/song.mp3",
  "boost_prompt": "make it more dynamic and punchy",
  "mv": "v4_5"
}
```

---

## 🎬 Music Video APIs (1 Endpoint)

### 13. Create Music Video
Generate visual music videos from audio tracks using AI video generation technology.

**Endpoint**: `POST https://api.sunoapi.org/create_video`

**Request Parameters**:
```json
{
  "audio_url": "https://example.com/song.mp3",
  "video_prompt": "psychedelic abstract visuals with neon colors"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "video_url": "https://...",
    "thumbnail_url": "https://..."
  }
}
```

---

## 🛠️ Utility APIs (7 Endpoints)

### 14. Get Music Generation Details
Monitor and retrieve detailed information about your music generation tasks.

**Endpoint**: `GET https://api.sunoapi.org/get_music_details`

**Request Parameters**:
```json
{
  "task_id": "task-id"
}
```

---

### 15. Get Remaining Credits
Check your account credit balance and usage statistics.

**Endpoint**: `GET https://api.sunoapi.org/get_credits`

**Response**:
```json
{
  "success": true,
  "data": {
    "credits_remaining": 500,
    "credits_used": 250,
    "plan": "pro"
  }
}
```

---

### 16. Get Lyrics Generation Details
Track status and details of your lyrics generation requests.

**Endpoint**: `GET https://api.sunoapi.org/get_lyrics_details`

**Request Parameters**:
```json
{
  "task_id": "task-id"
}
```

---

### 17. Get WAV Conversion Details
Monitor WAV format conversion tasks and download status.

**Endpoint**: `GET https://api.sunoapi.org/get_wav_details`

**Request Parameters**:
```json
{
  "task_id": "task-id"
}
```

---

### 18. Get Vocal Separation Details
Check progress of vocal separation tasks and access separated audio files.

**Endpoint**: `GET https://api.sunoapi.org/get_separation_details`

**Request Parameters**:
```json
{
  "task_id": "task-id"
}
```

---

### 19. Get Music Video Details
Track music video generation progress and retrieve download links.

**Endpoint**: `GET https://api.sunoapi.org/get_video_details`

**Request Parameters**:
```json
{
  "task_id": "task-id"
}
```

---

### 20. Get Cover Details
Monitor status of music cover tasks and get cover results.

**Endpoint**: `GET https://api.sunoapi.org/get_cover_details`

**Request Parameters**:
```json
{
  "task_id": "task-id"
}
```

---

## Style Tags Reference

Use these tags in `tags` or `prompt` fields:

**Electronic**: `electronic, edm, techno, house, trance, drum-and-bass, dubstep, trap, lo-fi, synthwave, vaporwave`

**Rock/Metal**: `rock, metal, punk, alternative, grunge, heavy-metal, thrash-metal, progressive-rock`

**Hip-Hop/R&B**: `hip-hop, rap, r&b, soul, funk, trap, drill, boom-bap`

**Pop**: `pop, indie-pop, synth-pop, dance-pop, bubblegum-pop`

**Jazz/Blues**: `jazz, blues, swing, bebop, smooth-jazz, acid-jazz`

**Classical**: `classical, orchestral, piano, string-quartet, opera`

**World**: `reggae, afrobeat, latin, salsa, bossa-nova, k-pop`

**Moods**: `happy, sad, energetic, chill, dark, romantic, aggressive, mysterious, epic`

---

## Usage Examples

### Example 1: Generate music from prompt
```bash
curl -X POST https://api.sunoapi.org/generate \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "custom": false,
    "instrumental": false,
    "mv": "v5",
    "prompt": "dark trap beat with heavy 808s and ominous piano"
  }'
```

### Example 2: Generate instrumental
```bash
curl -X POST https://api.sunoapi.org/generate \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "custom": false,
    "instrumental": true,
    "mv": "v4_5PLUS",
    "prompt": "epic cinematic orchestral music for battle scene"
  }'
```

### Example 3: Generate custom song with lyrics
```bash
curl -X POST https://api.sunoapi.org/generate \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "custom": true,
    "instrumental": false,
    "mv": "v5",
    "prompt": "[Verse 1]\nWoke up in the code\nDebugging all alone\n\n[Chorus]\nBinary dreams flow",
    "tags": "electronic, synthwave, melancholic",
    "title": "Code Dreams"
  }'
```

### Example 4: Extend an existing track
```bash
curl -X POST https://api.sunoapi.org/extend \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "aid": "song-id-here",
    "bark_prompt": "continue with a high-energy drop",
    "mv": "v4_5"
  }'
```

### Example 5: Check credits
```bash
curl -X GET https://api.sunoapi.org/get_credits \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

## Agent Implementation Guide

When implementing this skill in an OpenClaw agent:

1. **Use `instrumental: true` for background music** - avoids potential copyright issues with generated lyrics

2. **Download and save generated audio** to `/home/mike/WEBSITES/OpenVoiceUI/generated_music/`

3. **Generate descriptive filenames**:
   - Use song title or prompt-based name
   - Include timestamp or UUID for uniqueness
   - Example: `epic-cinematic-20260222.mp3`

4. **Track metadata** in `generated_metadata.json` (uses filename as key):
   ```json
   {
     "epic-cinematic-20260222.mp3": {
       "title": "Epic Cinematic",
       "description": "epic cinematic orchestral music",
       "genre": "AI-Generated",
       "energy": "high",
       "themes": [],
       "duration_seconds": 120,
       "fun_facts": [],
       "dj_intro_hints": [],
       "dj_backstory": "Fresh from the AI oven.",
       "made_by": "Clawdbot",
       "created_date": "2026-02-22",
       "suno_id": "abc123",
       "artist": "Clawdbot AI"
     }
   }
   ```

5. **Handle async generation**:
   - API supports webhook callbacks via `hookUrl` parameter
   - Polling available using detail endpoints (`get_music_details`)
   - Typical generation time: 30-120 seconds

6. **Error handling**:
   - Check for `success: false` in responses
   - Handle rate limits and credit exhaustion
   - Validate `audio_url` before downloading

---

## Download Workflow

After receiving a successful response:

```bash
# Extract audio URL from response
AUDIO_URL=$(echo "$RESPONSE" | jq -r '.data[0].audio_url')

# Generate filename
FILENAME="suno-$(date +%Y%m%d-%H%M%S).mp3"
OUTPUT="/home/mike/WEBSITES/OpenVoiceUI/generated_music/$FILENAME"

# Download
curl -o "$OUTPUT" "$AUDIO_URL"

# Set permissions
chmod 644 "$OUTPUT"

# Update metadata (uses filename as key)
# ... append to generated_metadata.json
```

---

## Limitations

- Rate limits apply (check credits endpoint)
- Generated audio length depends on model (4-8 minutes)
- Commercial use requires API subscription
- All requests require valid API key
- Webhooks require publicly accessible URLs

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| API returns 401 | Check API key and Bearer token format |
| No audio_url in response | Generation failed or still processing - poll details endpoint |
| Download fails | URL may be expired or invalid |
| Rate limited | Check credits, wait before next request |
| Audio quality poor | Try `v5` or `v4_5PLUS` model, refine prompt |
| Webhook not triggered | Check hookUrl is publicly accessible |

---

## Sources
- [Official Suno API Documentation](https://docs.sunoapi.org/)
- [API Key Management](https://sunoapi.org/api-key)
- Support: support@sunoapi.org
