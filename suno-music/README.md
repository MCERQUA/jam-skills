# Suno Music Generation Skill

Official Suno API skill for OpenClaw agents. Generate AI music with full support for all 20 endpoints.

**Official API**: https://api.sunoapi.org
**Documentation**: https://docs.sunoapi.org/

## Features

- **20 API Endpoints**: Complete coverage of all Suno API capabilities
- **5 AI Models**: V4, V4.5, V4.5 Plus, V4.5 All, V5
- **Music Generation**: From text prompts, custom lyrics, extend, cover, add vocals
- **Lyrics Generation**: AI lyrics with timestamps
- **Audio Processing**: Vocal separation, WAV conversion, style boost
- **Video Generation**: AI music videos from audio
- **All generated music saves to**: `/home/mike/WEBSITES/OpenVoiceUI/generated_music/`

## Quick Start

### Set API Key and Callback URL
```bash
export SUNO_API_KEY="your-api-key-here"
export SUNO_CALLBACK_URL="https://your-domain.com/api/suno/callback"
```

Get your API key at: https://sunoapi.org/api-key

**Note**: Callback URL is optional. If set, the API will send webhooks to this URL when generation completes.

### Generate music from description
```bash
./suno-generate.sh "dark trap beat with heavy 808s and ominous piano"
```

### Generate instrumental
```bash
./suno-generate.sh --instrumental "epic cinematic orchestral music for battle scene"
```

### Generate custom song with lyrics
```bash
./suno-generate.sh --custom --title "Code Dreams" --tags "electronic, synthwave" "my lyrics here"
```

### List local songs
```bash
./suno-generate.sh --list
```

## AI Models

| Model | Description | Max Duration | Best For |
|--------|-------------|---------------|-----------|
| `v4` | Improved Vocals | 4 min | Vocal clarity |
| `v4_5` | Smart Prompts | 8 min | Complex requests |
| `v4_5PLUS` | Richer Tones | 8 min | Highest quality |
| `v4_5ALL` | Better Structure | 8 min | Structured pieces |
| `v5` | Latest Model | Variable | Advanced generation |

## All 20 API Endpoints

### Music Generation (6)
1. `generate` - Create music from text
2. `extend` - Extend existing tracks
3. `upload_and_cover` - Transform audio styles
4. `upload_and_extend` - Upload and extend audio
5. `add_vocals` - Add AI vocals to instrumentals
6. `cover` - Reinterpret music in new styles
7. `add_instrumental` - Add backing music to vocals

### Lyrics Creation (2)
8. `generate_lyrics` - AI lyrics
9. `get_lyrics_timeline` - Timestamped lyrics

### Audio Processing (4)
10. `separate_vocals` - Split vocals/instrumental
11. `convert_wav` - Convert to WAV
12. `boost_style` - Enhance music style

### Music Video (1)
13. `create_video` - Generate video from audio

### Utility (7)
14. `get_music_details` - Task status
15. `get_credits` - Account balance
16. `get_lyrics_details` - Lyrics task status
17. `get_wav_details` - WAV conversion status
18. `get_separation_details` - Separation task status
19. `get_video_details` - Video task status
20. `get_cover_details` - Cover task status

## Python API Usage

```python
from suno_client import SunoMusicClient

# Initialize with official API
client = SunoMusicClient(
    api_base="https://api.sunoapi.org",
    api_key="your-api-key"
)

# Generate from prompt
result = client.generate_from_prompt(
    prompt="heavy metal track with aggressive guitar riffs",
    instrumental=False,
    model="v4_5"
)

# Access results
print(f"Saved to: {result['path']}")
print(f"Title: {result['song']['title']}")
print(f"Audio URL: {result['song']['audio_url']}")
```

## Command-Line Options

```
Usage: suno-generate.sh [OPTIONS] PROMPT

Arguments:
  PROMPT                  Music description or lyrics

Options:
  -m, --model MODEL       Model: v4, v4_5, v4_5PLUS, v4_5ALL, v5 (default: v4_5)
  -t, --title TITLE       Song title (for custom mode)
  -g, --tags TAGS         Style tags (for custom mode)
  -i, --instrumental      Generate instrumental only
  -c, --custom            Custom mode with lyrics
  -l, --lyrics-only       Generate lyrics only (no music)
  --credits               Show account credits
  --list                  List local songs
  -h, --help              Show this help

Environment Variables:
  SUNO_API_KEY            API key (required)
  SUNO_API_BASE           API base URL (default: https://api.sunoapi.org)
  SUNO_OUTPUT_DIR         Output directory
```

## Environment Variables

```bash
# Required
export SUNO_API_KEY="your-api-key-here"

# Optional
export SUNO_API_BASE="https://api.sunoapi.org"
export SUNO_OUTPUT_DIR="/home/mike/WEBSITES/OpenVoiceUI/generated_music"
```

## Output

All generated songs are saved to:
```
/home/mike/WEBSITES/OpenVoiceUI/generated_music/
```

Metadata is tracked in:
```
generated_metadata.json
```

Format uses filename as key for OpenVoiceUI compatibility.

## Style Tags

Electronic: edm, techno, house, trap, lo-fi, synthwave, vaporwave
Rock/Metal: rock, metal, punk, heavy-metal, progressive-rock
Hip-Hop: hip-hop, rap, trap, drill, boom-bap
Pop: pop, indie-pop, synth-pop, dance-pop
Jazz/Blues: jazz, blues, swing, bebop, smooth-jazz
Classical: classical, orchestral, piano, string-quartet
World: reggae, afrobeat, latin, salsa, k-pop

## Troubleshooting

**API returns 401?** - Check API key
**No audio_url?** - Generation still processing, poll details endpoint
**Download fails?** - URL may be expired
**Rate limited?** - Check credits, wait before retry
**Quality poor?** - Try v5 or v4_5PLUS model

## Official API Features

- 99.9% Uptime
- 20-Second Streaming Output
- High-Concurrency (120+ tasks)
- Watermark-Free Commercial Use
- 24/7 Support (support@sunoapi.org)
- Transparent Pricing

## Full Documentation

See `SKILL.md` for complete API documentation with all 20 endpoints.

## Sources

- [Official Suno API Documentation](https://docs.sunoapi.org/)
- [API Key Management](https://sunoapi.org/api-key)
