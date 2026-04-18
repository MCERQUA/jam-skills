---
name: soundcloud
description: "Find public SoundCloud tracks by artist/title and return a shareable URL + metadata. No auth, no API key, uses SoundCloud's public oEmbed endpoint. Use when the user mentions 'soundcloud', 'SC track', 'play from soundcloud', 'find on soundcloud', or wants to share/listen to a track that lives on SoundCloud."
metadata:
  version: 1.0.0
  openclaw:
    requires:
      env: ["SERPER_API_KEY"]
      anyBins: ["python3"]
---

# SoundCloud Track Finder

Find public SoundCloud tracks and share them. No auth required for discovery or embedding — SoundCloud's oEmbed endpoint is public. Uses the `serper-search` API key (already configured) to locate the track URL via Google, then validates via oEmbed.

## When to Use

- User asks to find / share / play a SoundCloud track
- User mentions a track they know is on SoundCloud
- Agent wants to surface a public SC track in conversation

## Tool

```bash
python3 /mnt/shared-skills/soundcloud/scripts/find_track.py "ARTIST - TRACK"
```

**Arguments:**
| Arg | Description |
|-----|-------------|
| query (positional) | Free-text search — `"artist - track"`, `"artist track remix"`, etc. |
| `--limit N` | Max candidates to evaluate (default 3, max 10) |
| `--json` | Raw JSON output (default: pretty text) |

**Returns (JSON):**
```json
{
  "ok": true,
  "url": "https://soundcloud.com/artist/track-name",
  "title": "Track Title",
  "author": "Artist Name",
  "artwork": "https://i1.sndcdn.com/…-t500x500.jpg",
  "embed_html": "<iframe …></iframe>",
  "provider": "SoundCloud"
}
```

If no match is found:
```json
{ "ok": false, "error": "no soundcloud track found for <query>" }
```

## Usage Patterns

### A — Share link only (always works)

1. Run `find_track.py` with the artist/track.
2. Include the URL in your voice reply:
   > "Found it — here's *Track Title* by Artist on SoundCloud: https://soundcloud.com/…"

### B — Play in the music player (`[SOUNDCLOUD:url]`)

Once you have a validated URL from `find_track.py`, emit the action tag in your reply. The music player panel will switch to SoundCloud mode and embed the iframe. User doesn't have to click out.

Example reply:
> "Playing *Strobe* by deadmau5 now. [SOUNDCLOUD:https://soundcloud.com/deadmau5/strobe]"

The tag is stripped from TTS output — only the conversational text is spoken.

### C — Full canvas page (`[SOUNDCLOUD_PAGE:url]`)

For a full-screen "now playing" view with artwork + embed, emit `[SOUNDCLOUD_PAGE:url]` instead. A new canvas page opens automatically.

Use when:
- User says "show me this track" / "put it on screen" / "open the page for it"
- You want to give the track visual prominence (vs. just background playback)

### Decision hints

- "play X" → use `[SOUNDCLOUD:url]` (B)
- "show me X" / "open X" → use `[SOUNDCLOUD_PAGE:url]` (C)
- Just answering a question ("is X on SoundCloud?") → plain link (A)
- Never emit both `[SOUNDCLOUD:...]` and `[SOUNDCLOUD_PAGE:...]` in the same reply.

## Budget & Etiquette

- 1 serper call + 1 oEmbed fetch per find. Negligible cost.
- Do NOT run this on auto-loop / in a scraper. One call per user request.
- If the user is asking you to play their OWN tracks from their AI-Radio catalog, use the `airadio` skill instead — this skill is for public SoundCloud links.

## Platform Notes

- Only **public** tracks are discoverable (private/unlisted return no results).
- Geo-blocked tracks may 403 on oEmbed — the script flags `region_blocked: true` if so.
- SoundCloud's oEmbed endpoint is documented + stable: `https://soundcloud.com/oembed?format=json&url=<track-url>`.
