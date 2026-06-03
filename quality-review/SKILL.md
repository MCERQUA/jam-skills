---
name: quality-review
description: "The ship/no-ship quality gate — run on ANY finished deliverable (website, app, brand report, canvas page) BEFORE telling Mike or a client it's done. Catches dead endpoints, missing/broken images, dead nav links, incomplete sections, fabricated/placeholder content, and brand violations via headless visual + functional checks. Use whenever you're about to report something as complete or shipped."
metadata:
  version: 1.0.0
  openclaw:
    emoji: "✅"
---
# Skill: quality-review (Quality Officer)

The ship/no-ship gate. Run this on ANY finished deliverable — a website, an app, a
brand report, a canvas page — BEFORE telling Mike or a client it's done. It catches
the failure classes that have repeatedly shipped broken: dead endpoints, missing/broken
images, dead nav links, incomplete sections, fabricated/placeholder content, and brand
reports falsely scored from failed data fetchers.

## When to use

Use this skill (REQUIRED, not optional) before declaring done / shipping:
- A built or updated **website / web app** (verify routes, images, links, sections)
- A **brand report / SEO audit** (verify endpoints returned real data, score isn't
  faked by zeros, template used, all sections present)
- Any **canvas page** or visual artifact delivered to Mike or a client

If `verdict: FAIL`, you DO NOT ship. Fix the findings, re-run, loop until PASS.
Self-reported "done" by a sub-agent is NOT done — gate it through here.

## Usage

```bash
# Website / app — crawl routes, check images + internal links + required content
python3 /mnt/shared-skills/quality-review/check.py \
  --url https://garage-sale.jam-bot.com \
  --routes "/,/map,/browse,/submit" \
  --require "Get a Quote,footer" \
  --out /tmp/qr-garagesale

# Brand report — page + the score data it was built from
python3 /mnt/shared-skills/quality-review/check.py \
  --url https://ica.jam-bot.com/pages/brand-report.html \
  --report-data /mnt/clients/ica/.../ai/score.json \
  --require "Brand Health,Keywords,Backlinks,Roadmap"

# Local static build dir (pre-deploy)
python3 /mnt/shared-skills/quality-review/check.py \
  --dir /tmp/svi-final --routes "/,/about,/cost" --require "nav,footer"
```

Exit code: `0` = PASS, `1` = FAIL — so you can gate in a script:
`python3 check.py ... || { echo "QUALITY GATE FAILED — do not ship"; exit 1; }`

## What it checks

| Check | Catches |
|---|---|
| `route` | any route/endpoint not 200 (the silent 404/502 that shipped before) |
| `image` | every `<img>` must load 200 — no broken/missing imagery |
| `deadlink` | internal nav/card links must resolve (the "feels like one page" bug) |
| `completeness` | required sections/phrases present (vs the spec/template) |
| `fabrication` | lorem/placeholder/"your text here" markers |
| `icons` | Material Symbols ligatures rendering as raw text (icon font not loaded) |
| `endpoint-data` | (reports) dimensions with NO real data — must show "N/A", not 0 |
| `coverage` | (reports) <4/6 data dimensions = thin; fix endpoints before shipping |
| `suspicious-zero` | (reports) a 0 score with data present = likely a parse miss |

## Visual gate — `visual-check.py` (the Quality Officer's eyes)

`check.py` is HTTP/structure. **`visual-check.py` is the rendered-DOM visual gate** — it
launches headless Chromium (Playwright) at multiple viewports and runs PROGRAMMATIC checks
against computed styles (more reliable than image-vision):

```bash
python3 /mnt/shared-skills/quality-review/visual-check.py \
  --url https://garage-sale.jam-bot.com --routes "/,/map,/submit" \
  --viewports 390,1440 --out /tmp/qa
```

Catches (the "tie straight" checks from the chain-of-custody framework):
| Check | Catches |
|---|---|
| `contrast` | **light-on-light / dark-on-dark** text + invisible buttons — computes each text node's WCAG ratio (color vs effective bg); fails <4.5:1 (<3 for large text) |
| `overflow` | page wider than viewport = **squished / breaks on mobile** |
| `broken-image` | `<img>` loaded but `naturalWidth==0` (missing/broken) |
| `clipped` | content overflowing a hidden/fixed box (long containers, squished content) |
| `empty-section` | `<section>`/blocks with no real content |

Also saves a full-page **screenshot per page×viewport** for the human eye. Exit 0/1 gates.
Proven (2026-06-01): caught a 4.13:1 footer-contrast fail + a 390px mobile-overflow on a live site.

## Limits (be honest)

- `check.py` (HTTP) can't reach auth-gated canvas pages (401) — run `visual-check.py` with a
  logged-in context, or check the served file directly, for those.
- `visual-check.py` needs Playwright Chromium on the host (installed + working).

## Roadmap

This is the **skill** form (run on demand by host + any tenant agent). A standing
`quality@mesh` agent will be wired ON TOP of this to auto-review finished deliverables
without being asked. (Mike: "skill now, agent later", 2026-06-01.)
