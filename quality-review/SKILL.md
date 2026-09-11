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
  --url https://<tenant>.jam-bot.com/pages/brand-report.html \
  --report-data /mnt/clients/<tenant>/.../ai/score.json \
  --require "Brand Health,Keywords,Backlinks,Roadmap"

# Local static build dir (pre-deploy)
python3 /mnt/shared-skills/quality-review/check.py \
  --dir /tmp/svi-final --routes "/,/about,/cost" --require "nav,footer"
```

# Canvas page(s) — brand voice + revert + fabrication, straight off the served file
# (this is how a tenant agent reviews its own pages; the Clerk gate never gets in the way)
python3 /mnt/shared-skills/quality-review/check.py \
  --files ~/.openclaw/workspace/canvas-pages/home.html,~/.openclaw/workspace/canvas-pages/about.html
```

Exit code: `0` = PASS, `1` = FAIL — so you can gate in a script:
`python3 check.py ... || { echo "QUALITY GATE FAILED — do not ship"; exit 1; }`

## Brand voice + revert — the "agents are everyone's eyes" standard (2026-09-11)

**Origin.** Danielle C reviewed her rebuilt homepage: the agent caught spelling but MISSED
*"Boutique Digital Marketing & Brand Advisory Collective"* — corporate jargon on her own banned
list — and a line fixed earlier had silently REVERTED in the Stitch rebuild. She caught both.
Her words: *our agents are everyone's eyes.* Two mechanisms were missing, and both are now in
this gate, because a standard in the gate gets run and a standard in meeting minutes gets forgotten.

**The standard, four points:** (1) every content/page review = facts + spelling + brand voice,
every section; (2) banned words vs EVERY line; (3) approved fixes get a revert check;
(4) misses the client catches are logged for patterns, not blame.

**Mechanism 1 — the canonical file.** A banned list that lives only inside a brand-kit canvas HTML
cannot be loaded by a check, which is exactly why it was never run. Every tenant keeps
`business/brand-voice.json` (template: `jambot/templates/business/brand-voice.json`; live
example: danielle). The brand-kit page is the VIEW; this file is the SOURCE; `CLIENT.md`
"Brand Voice" points at it. Schema:

```json
{ "brands": { "<brand name>": {
    "banned_words":    ["synergy", "leverage"],          // mechanical: word-boundary, case-insensitive
    "banned_regex":    ["\\bboutique\\b.*\\b(collective|advisory)\\b"],  // mechanical: regex
    "banned_patterns": ["corporate-speak of any kind"],   // PROSE: echoed for the human/LLM pass, never claimed as checked
    "tone": "...", "words_used": [], "emojis": [], "emoji_rule": "..." } },
  "review_protocol": { "steps": [...], "pattern_notes": [] } }   // point 4 lives in pattern_notes
```
`--files` auto-finds it (`<workspace>/business/brand-voice.json` beside `canvas-pages/`; on the
host, `/mnt/clients/<t>/openclaw/workspace/business/`) or pass `--brand-voice <path>`. Hits are
**fail** (ship-blockers). Scripts, styles and comments are not "visible" and are not scanned.
No file found → `CANNOT-TELL` on the info line, never a PASS you can mistake for "clean".

**Mechanism 2 — the approved ref.** Canvas-pages dirs are git repos (auto-committed). When a
review is approved, tag that state: `git -C <canvas-pages> tag -f approved/<file>.html`. The
next run diffs the page's visible text against the tag and reports every approved line that is
no longer on the page as a **warn** `revert` — a rebuild that drops a fix shows up in one line.
No tag → `CANNOT-TELL`, with the exact tag command printed. Re-tag after each approved change;
until you do, intentional edits also show as warns (that is the point: someone looks).

**Known limits.** Copy rendered from JS strings or `_data/*.json` is not visible text and is not
scanned — say so in the review rather than reporting clean. The brand-kit page itself lists the
banned words and will trip the check; it is the one page you do not run it on.

**First-run friction (measured by danielle-sms 2026-09-11).** Pass the WORKSPACE path
(`~/.openclaw/workspace/canvas-pages/<page>`) — it is a symlink and the checker resolves it for
git while still finding `business/brand-voice.json` beside it. If git answers *dubious ownership*
(the repo is owned by another uid), the check prints the one-time fix:
`git config --global --add safe.directory <real canvas-pages path>`. `banned_regex` alternations
need parentheses: `boutique.*(collective|advisory)` — `boutique.*collective|advisory` matches
every line containing "advisory".

## What it checks

| Check | Catches |
|---|---|
| `route` | any route/endpoint not 200 (the silent 404/502 that shipped before) |
| `image` | every `<img>` must load 200 — no broken/missing imagery |
| `deadlink` | internal nav/card links must resolve (the "feels like one page" bug) |
| `completeness` | required sections/phrases present (vs the spec/template) |
| `fabrication` | lorem/placeholder/"your text here" markers |
| `brand-voice` | banned words / regex from `business/brand-voice.json` in any VISIBLE line (fail); prose patterns echoed for the human pass |
| `revert` | approved text (git tag `approved/<file>`) no longer on the page (warn) — the silent-rebuild class |
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
