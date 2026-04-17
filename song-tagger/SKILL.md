---
name: song-tagger
description: "Analyze an audio file and return structural tags — genre, mood, energy, tempo, vocals — using offline zero-shot classification. Use when the user asks what a song sounds like, what genre/mood it is, or wants to auto-tag a music library. No API cost per song."
metadata: {"openclaw": {"requires": {"anyBins": ["python3"], "files": ["/mnt/system/base/tools/song-tagger/.venv/bin/python"]}}}
---

# Song Tagger Skill

Offline tagger that labels an audio file with genre, mood, energy, tempo, and vocals. Backed by LAION's CLAP zero-shot model running locally — no HuggingFace API calls, no per-song cost. Intended for library organization and metadata backfill, not conversational music analysis.

## When to use

- User asks "what does this song sound like" / "what genre is this" / "what's the mood of X.mp3"
- User wants to auto-tag a folder of music for organizing / search
- Filling in metadata when the user generates or uploads a song
- Batch processing `/mnt/clients/*/openvoiceui/generated_music/` or similar

Do **not** use for speech recognition, lyrics extraction, or detailed music critique — that's Audio Flamingo territory.

## ⚠️ Where this tool can run

The tagger lives on the **host** at `/mnt/system/base/tools/song-tagger/`. It is **not mounted inside client openclaw containers today** — you (the agent) cannot invoke it from inside the container with `exec()`.

**What you CAN do from inside a container:**
- Reference this skill to explain capabilities to the user
- Read tag sidecars IF the admin has placed them inside the workspace (`/home/node/.openclaw/workspace/music-tags/` or similar path)
- Ask the admin (Mike) to run the tagger against a folder

**What must happen on the host (admin-operated):**
- All `run tag` / `run batch` invocations

### Admin commands (run from `mike@Mike-AI` shell)

```bash
# Single file
/mnt/system/base/tools/song-tagger/run tag "/mnt/clients/<user>/openvoiceui/generated_music/<song>.mp3"

# Whole client library
/mnt/system/base/tools/song-tagger/run batch /mnt/clients/<user>/openvoiceui/generated_music

# Everyone
/mnt/system/base/tools/song-tagger/run batch /mnt/clients
```

Default output location: `/mnt/system/base/tools/song-tagger/tags/<client>/<song>.json`.

To make results agent-visible, admin can either:
- Use `--inline` so tags land as `*.mp3.tags.json` next to the source files (visible via openvoiceui file APIs), or
- Rsync the `tags/` tree into each client's workspace: `cp -r tags/<user>/ /mnt/clients/<user>/openclaw/workspace/music-tags/`

## Flags reference (for admin commands)

**`run tag <audio>`**
- `--out result.json` — also write to file
- `--seconds 20` — clip length (use 30 for longer tracks)
- `--offset-pct 0.4` — start position as % of total duration (avoids intros/outros)

**`run batch <dir>`**
- `--inline` — write `*.mp3.tags.json` next to each source file
- `--force` — re-tag files that already have a sidecar
- `--limit 5` — stop after N files
- `--sleep 2` — seconds to sleep between songs (default 2; set 0 to go faster)

## Output schema

```json
{
  "audio": "/abs/path/to/song.mp3",
  "total_duration_sec": 168.2,
  "clip_offset_sec": 67.28,
  "clip_duration_sec": 20.0,
  "axes": {
    "genre":      [{"label": "house music", "score": 0.18}, ...up to 5],
    "mood":       [{"label": "epic",        "score": 0.23}, ...up to 5],
    "energy":     [{"label": "very high energy",  "score": 0.64}],
    "tempo_feel": [{"label": "very fast tempo",   "score": 0.82}],
    "vocals":     [{"label": "has both male and female vocals", "score": 0.90}]
  },
  "top":  { "genre": "...", "mood": "...", "energy": "...", "tempo_feel": "...", "vocals": "..." },
  "inference_sec": 7.6,
  "model_load_sec": 0.26
}
```

- `axes.*` are **ranked lists** with softmax scores.
- `top` is the convenience flat-pick of #1 per axis.
- Scores are relative within an axis — treat them as a ranking, not an absolute confidence.

## Presenting results to the user

Summarize naturally from `top` — don't dump raw JSON:

> That track reads as **house music** with an **epic** mood, very high energy and fast tempo, with mixed male + female vocals.

Include top-3 genre/mood when the user asks "what else could it be" since scores are often close.

## Performance expectations

The tool is **intentionally throttled** — single-threaded torch + `nice -n 19` + `ionice -c 3` (idle class) + 2s sleep between songs in batch mode. It's a background organization job, not user-facing, and shouldn't impact live traffic on the VPS.

- **~13–16 seconds per song** on CPU (including the 2s polite-sleep in batch mode)
- Uses 1 CPU core, yields to anything else that wants the CPU
- $0 cost per song — all local, no HuggingFace API calls, no quota

If you ever need it faster (e.g. tagging one song for an active user request), override with env vars:
```bash
SONG_TAGGER_THREADS=4 SONG_TAGGER_NICE=10 /mnt/system/base/tools/song-tagger/run tag <file>
```
Or skip the sleep in batch mode:
```bash
/mnt/system/base/tools/song-tagger/run batch <dir> --sleep 0
```

## Vocabulary tuning

Label lists and prompt templates live in `vocabularies.json`. Five axes: `genre`, `mood`, `energy`, `tempo_feel`, `vocals`. Each axis has:
- `templates` — prompt formats with `{label}` — multiple templates averaged (ensemble) to reduce wording bias
- `labels` — candidate tags; keep them specific
- `top_k` — how many to keep in the ranked output

**Known trap labels** already removed because CLAP over-indexes them:
- `sensual`, `passionate` (mood)
- bare `soul` (genre — replaced with `neo soul` / `classic soul`)

If the user wants to add custom labels (e.g. branded moods like "foam-ready", "chill work"), edit `vocabularies.json` and re-tag.

## Common tasks

**User: "What does this song sound like?"**
1. Run `run tag "<path>"`
2. Summarize from `top` with top-3 genre + top-3 mood

**User: "Tag all my songs"**
1. Identify their music folder (usually `/mnt/clients/<user>/openvoiceui/generated_music/`)
2. Run `run batch <folder>`
3. Report count, total time, and summary of most common tags

**User: "Re-tag the library with my custom labels"**
1. Edit `/mnt/system/base/tools/song-tagger/vocabularies.json` per their vocabulary
2. Run `run batch <folder> --force`

## Troubleshooting

- **"No module named 'torch'"** — venv missing. Rebuild: `cd /mnt/system/base/tools/song-tagger && python3 -m venv .venv && .venv/bin/pip install --index-url https://download.pytorch.org/whl/cpu torch && .venv/bin/pip install transformers librosa soundfile`
- **First-run model download fails** — needs network to download ~600MB from HF the first time. Subsequent runs are offline.
- **Audio file unreadable** — librosa supports mp3/wav/m4a/ogg/flac/opus. For weird formats, convert with `ffmpeg -i input.x output.mp3` first.
- **All results look the same** — rare CLAP quirk. Lengthen clip (`--seconds 30`), shift offset (`--offset-pct 0.5`), or tune `vocabularies.json` to remove dominant labels.

## Files

| File | Purpose |
|------|---------|
| `tag_song.py` | Single-file tagger |
| `batch_tag.py` | Directory walker |
| `vocabularies.json` | Label lists + templates (edit to customize) |
| `run` | Shell wrapper that activates the venv |
| `README.md` | Full docs |
| `tags/<client>/<song>.json` | Default output location |
