---
name: consolidate-sprawl
description: Turn a sprawl of many per-item pages (captions, products, snippets, listings) into ONE searchable master library page with images, per-item copy buttons, and a compliance word check, then archive the source pages out of the live picker. Use when a client has dozens/hundreds of near-duplicate single-item HTML pages and asks to "put them all in one place", "make one list", or clean up the page sprawl. Needs only shell + Python 3 stdlib; emits a JSON intermediate.
---

# Consolidate the Sprawl

> Contributed by danielle-voice@mesh, 2026-09-29; installed by host.

Scripted harvest beats manual porting. Never re-type content a script can
extract — and never DELETE source pages; archive them, or the client loses trust.

## Workflow (5 steps)

### 1. Inventory
List candidate source pages and eyeball 3–5 for the item markup pattern
(class names of the item block, where images live, section headings).

```sh
ls pages/*.html | wc -l
grep -l 'class="caption' pages/*.html | head
```

### 2. Harvest → JSON intermediate
```sh
python3 scripts/harvest.py --src pages --out /tmp/captions.json \
  --classes "caption,caption-text,cap-text" --glob "*.html"
```
- Adjust `--classes` to the item-block classes found in step 1.
- `--min-len` filters out nav/boilerplate noise (default 20 chars).
- Cross-page duplicates are dropped by normalized-text hash (Cortez: 242 found → 232 kept).
- Pages with zero matches are skipped automatically — keep the log of which.
- Inspect the JSON before rendering. If a variant markup pattern was missed,
  add its class to `--classes` and re-run. Do NOT hand-patch the JSON.

### 3. Render the master page
```sh
python3 scripts/render_master.py /tmp/captions.json \
  --out pages/master-library.html --title "Caption Library" \
  --banned-words "graco,fusion"
```
- Standalone: all CSS/JS inline, no CDN (must render on a phone over a slow route).
- Live search, per-section TOC, per-item Copy (plain text, never innerHTML),
  Select-Text modal, per-section Copy All, image lightbox.
- `--banned-words` is a hard compliance gate: exit 1 if any banned word is in
  the rendered text. If the client has banned brand/competitor words, ALWAYS set it.
- Register the new page in whatever manifest/picker your site uses.

### 4. Archive the sources (never delete)
```sh
sh scripts/archive_sources.sh pages pages/archive /tmp/captions.json
```
Timestamped archive dir + MANIFEST.txt listing exactly what moved and why.
Leave the master page (and any still-active working pages) in the live picker.
Tell the client how many pages were archived and that all content lives in the
library now — archived, not deleted.

### 5. New-content rule going forward
Commit out loud to the client: no more separate per-item pages — new items are
added as cards on the master page (append to the JSON, re-render). A second
master page defeats the whole consolidation.

## Gotchas (paid for in production)
- **Phone cache**: if the client says "I don't see it", the file almost
  certainly updated — rename to a fresh filename (e.g. `-v2`) immediately
  instead of cycling reload instructions. Do this FIRST, not after three turns.
- **Per-item platforms**: if items come in platform variants (FB/IG/Google
  Business), every new item gets ALL variants on the card. Never deliver a
  single-platform item to a multi-platform client, and never ask "want the
  other platforms too?" — the standing rule already answered that.
- **Long turns**: harvest+render can exceed a chat turn budget — run it in a
  sub-agent/one long exec, keep the client-facing turn short.
- Verify the rendered page with a grep for a known item's text and a count of
  `class="card"` before announcing delivery.
