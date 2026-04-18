---
name: bandcamp
description: "Find public Bandcamp tracks/albums by artist + title and return a shareable URL + metadata. No auth, no API key. Use when the user mentions 'bandcamp', 'find on bandcamp', 'bandcamp embed', or wants to share/listen to an album or track hosted on Bandcamp."
metadata:
  version: 1.0.0
  openclaw:
    requires:
      env: ["SERPER_API_KEY"]
      anyBins: ["python3"]
---

# Bandcamp Track Finder

Find public Bandcamp tracks and albums. No auth, no API key — Bandcamp has no public API, so this skill uses `serper-search` to locate the artist's Bandcamp URL via Google, then scrapes OpenGraph metadata from the page to confirm the track/album exists.

## When to Use

- User asks to find / share a Bandcamp track or album
- Artist is known to sell/host on Bandcamp
- Agent wants to surface a purchasable or free Bandcamp link

## Tool

```bash
python3 /mnt/shared-skills/bandcamp/scripts/find_track.py "ARTIST - TRACK-OR-ALBUM"
```

**Arguments:**
| Arg | Description |
|-----|-------------|
| query (positional) | Free-text search — `"artist - album"`, `"artist track name"`, etc. |
| `--kind track\|album\|any` | Filter result type (default: any) |
| `--limit N` | Max candidates to evaluate (default 3, max 10) |
| `--json` | Raw JSON output (default: pretty text) |

**Returns (JSON):**
```json
{
  "ok": true,
  "url": "https://artist.bandcamp.com/album/album-name",
  "kind": "album",
  "title": "Album Title",
  "artist": "Artist Name",
  "artwork": "https://f4.bcbits.com/img/…_16.jpg",
  "description": "short album description if available",
  "embed_url": "https://bandcamp.com/EmbeddedPlayer/album=<id>/size=large/",
  "embed_html": "<iframe …></iframe>",
  "provider": "Bandcamp"
}
```

If no match:
```json
{ "ok": false, "error": "no bandcamp page found for <query>" }
```

## Usage Patterns

### A — Share link only

1. Run `find_track.py` with artist + track/album.
2. Include the URL in your reply:
   > "Found *Album Title* by Artist on Bandcamp: https://artist.bandcamp.com/album/…"
3. Mention that Bandcamp tracks often have free preview streams + optional purchase.

### B — Play in the music player (`[BANDCAMP:url]`)

Emit the tag after a successful `find_track.py`. The music panel embeds the Bandcamp player iframe (shows artwork + track list, click-to-play).

Example reply:
> "Playing *Another Life* by Amnesia Scanner now. [BANDCAMP:https://amnesiascanner.bandcamp.com/album/another-life]"

The tag is stripped from TTS output.

### C — Full canvas page (`[BANDCAMP_PAGE:url]`)

Full-screen page with hero artwork + embed — best for "show me this album" moments.

### Decision hints

- "play X" → `[BANDCAMP:url]` (B)
- "show me X" / "open X" → `[BANDCAMP_PAGE:url]` (C)
- Just mentioning ("is X on Bandcamp?") → plain link (A)
- Never emit both `[BANDCAMP:...]` and `[BANDCAMP_PAGE:...]` in the same reply.

## Platform Notes

- Bandcamp has no public API. This skill relies on Google search + OpenGraph meta tags from the page.
- Artists host on their own subdomain: `<artist>.bandcamp.com/album/...` or `.../track/...`.
- Many artists enable free streaming and name-your-price downloads — check the page before recommending a purchase.
- Embed URL structure is stable: `https://bandcamp.com/EmbeddedPlayer/album=<id>/size=large/bgcol=ffffff/linkcol=0687f5/tracklist=false/artwork=small/transparent=true/`.

## Budget & Etiquette

- 1 serper call + 1 page fetch per find.
- Do NOT scrape artist catalogs in a loop. One call per user request.
