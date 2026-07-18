---
name: social-image-picker
description: Pick and prepare client images for social posts BY DATA, never by fumbling — query the per-tenant image-intel index (quality/keywords/aspect), then fit the platform ratio (use-as-is, AI-outpaint for photos, crop for graphics). TRIGGER when choosing an image for a social post, ad, story, or link preview, or when an image is the wrong aspect ratio for a platform. DO NOT TRIGGER for generating brand-new images (social-media-designer) or posting/scheduling.
---

# Social Image Picker — pick by data, fit by rule

Every analyzed image in a tenant's workspace has a metadata record (Image
Intelligence system — `docs/jambot/image-intelligence-system.md`). NEVER
eyeball raw upload dirs or re-analyze images: query the index, apply the
fit rules, transform only when needed.

## 1. SELECT — query the index

On the VPS host:
```bash
python3 /home/mike/MIKE-AI/scripts/image-intel/social-image-pick.py \
  --tenant <t> --topic "spray foam attic job" --platform ig-feed [--top 5]
```
Remote nodes (mac-claude etc.): same script with `--url-base https://<t>.jam-bot.com`,
or fetch `https://<t>.jam-bot.com/uploads/image-intel-index.jsonl` and filter yourself.

Platforms: `ig-feed` (4:5) · `fb-feed`/`square` (1:1) · `story` (9:16) ·
`fb-link` (1.91:1) · `x-post`/`yt-thumb`/`wide` (16:9).

Output = ranked candidates each with a **verdict**:
- `use-as-is` — ratio already fits, quality ≥6: just use the `url`.
- `outpaint` — real photo, wrong ratio: run the included command (next section).
- `crop` — text/designed graphic, wrong ratio: center-crop or rebuild the layout. **NEVER AI-outpaint a graphic** — the model regenerates everything and garbles typography (proven 2026-07-18 on azrim's poster: duplicated layout + "CAWH RASH" gibberish).
- `reject` — quality/resolution below the platform bar; reason included. Don't argue with it; pick another or generate fresh.

## 2. TRANSFORM — ratio conversion for photos (VPS-side)

```bash
python3 /home/mike/MIKE-AI/scripts/image-intel/outpaint-to-ratio.py \
  --tenant <t> --file <filename> --ratio 16:9
```
- Engine: Qwen-Image-Edit-2509 via HF router (billed to HF_TOKEN). Winning recipe: raw original + pinned `image_size` at target ratio; the prompt is auto-grounded in the image's own sidecar description.
- Ratios: 16:9, 1.91:1, 9:16, 4:5, 1:1, 3:2, 2:3, 4:3, 3:4, 21:9.
- Guards itself: refuses text/graphic sources (`--force-transform` to override — don't).
- Saves the variant to the tenant uploads **immediately** with a sidecar (`derived_from` + `transform`) — variants are permanent and findable; NEVER regenerate one that exists (grep the index for `outpaint-<ratio>` first).
- Remote nodes without VPS shell: mesh-task `host@mesh` with tenant+file+ratio, or use your local on-screen ChatGPT browser (mac method) — but then you MUST upload the result to `https://<t>.jam-bot.com/api/upload` so it's server-saved.

## 3. VERIFY before posting (non-negotiable)

LOOK at the final image (vision call or your own eyes): subject intact, no
garbled text, no ghost/mirror artifacts at the edges, short side ≥1080px
(720px for 16:9 link cards). AI transforms fail ugly sometimes — a post with a
mangled image is worse than no post.

## 4. Record what you learn

Client says anything about an image ("that's our old truck", "never use this
one") → APPEND to `uploads/.image-intel/<file>.json` `client_context` list:
`{"at": "<iso>", "from": "<agent>", "note": "..."}`. Never overwrite fields.
