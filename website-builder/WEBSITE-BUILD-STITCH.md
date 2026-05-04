# WEBSITE-BUILD-STITCH.md — Stitch-First Pipeline

**Trigger condition:** This file is loaded by the watcher when `intake.stitchScreens`
is non-empty (or `intake.stitchInstructions` contains parseable screen IDs). For all
other builds the legacy `WEBSITE-BUILD.md` runs.

The non-negotiable rule on this path: **Stitch's HTML is the design — convert it,
don't reinterpret it.** The agent does NOT generate pages from scratch. The agent
runs deterministic Python tools that turn Stitch HTML into Next.js pages, then layers
intake content on top, then handles only the things that genuinely need an LLM
(research, extra pages not in Stitch, deploy reconciliation).

---

## Inputs

- `~/Websites/<projectName>/.intake.json` — full website-setup form serialization
- `intake.stitchScreens[]` — array of `{name, id}` from the form's Section 2B
- `intake.stitchProjectTitle` — Stitch project title (used to derive projectId)
- `intake.stitchInstructions` — raw MCP-instruction block (fallback if stitchScreens empty)

---

## Phases (11 total)

| # | Phase           | Owner     | Tool / Action |
|---|-----------------|-----------|---------------|
| 1 | scaffold        | agent     | `bash /home/node/.claude/skills/website-builder/tools/scaffold.sh <project-dir> <projectName>` |
| 2 | stitch-fetch    | agent+MCP | use `stitch` skill: `get_screen` for each id in `intake.stitchScreens` → write to `.stitch-pages/<slug>.html` |
| 3 | stitch-convert  | tool      | `python3 /home/node/.claude/skills/website-builder/tools/stitch-to-next.py --input .stitch-pages/ --out .` |
| 4 | asset-download  | tool      | `python3 .../stitch-download-assets.py --project .` |
| 5 | content-layer   | tool      | `python3 .../stitch-content-layer.py --intake .intake.json --project .` (downloads `intake.heroImage`, `intake.gallery[]`, `intake.logo` to `public/images/` and rewrites refs) |
| 5.5 | fix-links     | tool      | `python3 .../stitch-fix-links.py --project . --intake .intake.json` (rewrites `href="#"` → real routes, wraps CTA `<button>`s in `<a>`) |
| 6 | research        | agent+MCP | `dataforseo` skill — keywords, volume, CPC, competitors → `ai/research/.dfs/*.json` + `keywords.md` (integer volumes only) + `page-recommendations.md` where **EVERY row is "MUST BUILD"** (no FOR REVIEW gating — the form is the approval) |
| 7 | extra-pages     | agent     | build EVERY missing page from page-recommendations.md (services + locations + cost guides + legal). Each page must contain its target keywords verbatim in H1, ≥2 H2s, intro paragraph, CTA. |
| 7.5 | keyword-coverage | tool   | `python3 .../keyword-coverage-check.py --project . --recommendations ai/research/page-recommendations.md` — fails build if any required page missing or any page missing its target keywords |
| 7.7 | finalize      | tool      | `python3 .../stitch-finalize.py --project . --intake .intake.json` — downloads any remaining remote images to local, injects logo `<img>` into navbar (replacing wordmark), builds Services dropdown linking every discovered service page. **Runs AFTER extra-pages so the dropdown sees all service routes.** |
| 8 | quality-gate    | tool      | runs in **WEBDEV** container (matching pnpm store): `cd /app/websites/<project> && pnpm build` — fail on any TS/build error |
| 9 | deploy          | watcher   | **NOT AGENT.** Host-side `tools/host-deploy-and-verify.sh` runs after z-code exits: clean install + build in webdev container + restart + curl every declared route on real dev URL |
| 10 | github-push    | watcher   | host-side after deploy. Agent has no GitHub credentials in container — host owns this. |
| 11 | verification   | watcher   | inside `host-deploy-and-verify.sh`. Curl every page in `intake.pages[]` ∪ `page-recommendations.md` MUST-BUILD list against `intake.devUrl`. ANY non-200 = build status FAILED. |

**Phase ownership:** Phases 1-7.5 run in the openclaw container (agent + tools). Phases 8-11 run on the host (watcher). The agent's job ENDS when phase 7.5 passes — host takes over.

After each phase, write `phases.<key>.status = "complete"|"failed"` and `phases.<key>.message` to `.build-status.json`.

---

## Phase 1 — SCAFFOLD

```bash
PROJECT_DIR="$HOME/.openclaw/workspace/Websites/$PROJECT_NAME"
bash /home/node/.claude/skills/website-builder/tools/scaffold.sh "$PROJECT_DIR" "$PROJECT_NAME"
```

If `$PROJECT_DIR/package.json` already exists (resume case) → mark `scaffold` complete and skip.

---

## Phase 2 — STITCH-FETCH

Read `intake.stitchScreens` and `intake.stitchInstructions` to determine project ID and screen IDs.

**Project ID parse:** look for `ID:\s*<digits>` in `stitchInstructions`. If not found, it's an error — halt build with `phases.stitch-fetch.status="failed"`.

For each `{name, id}` in `intake.stitchScreens`:
1. Use the `stitch` skill's `get_screen` with `screen_id = id` and the parsed `project_id`.
2. Map screen `name` → page slug (lowercase, hyphenated, drop common Stitch prefixes like "Modern Artisan", "Luxe Boutique", etc. — keep only the page-distinguishing word: "Homepage" → `home`, "About Us" → `about`, "Services" → `services`, "FAQ" → `faq`, "Contact" → `contact`, "Pricing" → `pricing`, "Gallery" → `gallery`).
3. Write the returned HTML to `.stitch-pages/<slug>.html`.
4. If `get_screen` returns an image URL instead of HTML, also save the screenshot to `.stitch-pages/<slug>.png`.

**Halt rules:**
- Project ID couldn't be parsed → halt
- Any `get_screen` returns an error → halt
- A page in `intake.pages` has no matching Stitch screen AND no clone source → record in `.stitch-pages/missing.txt` (Phase 7 handles)

---

## Phase 3 — STITCH-CONVERT

```bash
python3 /home/node/.claude/skills/website-builder/tools/stitch-to-next.py \
  --input "$PROJECT_DIR/.stitch-pages" \
  --out "$PROJECT_DIR"
```

This emits:
- `tailwind.config.ts` — Stitch's `theme.extend.colors|fontFamily|spacing|borderRadius|fontSize` extracted verbatim
- `src/app/globals.css` — Stitch's `<style>` blocks + Material Symbols icon CSS
- `src/app/layout.tsx` — Stitch's Google Fonts `<link>` tags in `<head>`
- `src/app/<slug>/page.tsx` for each Stitch HTML (and `src/app/page.tsx` for `home`)
- `.stitch-assets.json` — manifest of remote asset URLs

**Verify:** the JSON output to stdout has `ok: true` and `pages_converted` matches the count of `.stitch-pages/*.html` files.

---

## Phase 4 — ASSET-DOWNLOAD

```bash
python3 /home/node/.claude/skills/website-builder/tools/stitch-download-assets.py --project "$PROJECT_DIR"
```

Downloads every unique image URL into `public/images/stitch/<sha8>.<ext>` and rewrites every `page.tsx` to point at the local path.

**Verify:** `downloaded > 0`, `failed = 0`. If `failed > 0`, log the URL but do NOT halt (some Stitch CDN images time out — content-layer will replace them with intake images anyway).

---

## Phase 5 — CONTENT-LAYER

```bash
python3 /home/node/.claude/skills/website-builder/tools/stitch-content-layer.py \
  --intake "$PROJECT_DIR/.intake.json" \
  --project "$PROJECT_DIR"
```

Substitutes:
- Phone numbers → `intake.phone` (every occurrence + every `tel:` href)
- Email addresses → `intake.email` (every occurrence + every `mailto:` href)
- US street addresses (regex match) → `intake.address`
- Stitch placeholder business names ("Modern Artisan", "Acme Co.", "Lorem Ipsum") → `intake.businessName`
- First large `<img>` → `intake.heroImage` (if supplied)
- Subsequent stitch images (sequentially) → `intake.gallery[].url`
- Social URLs → `intake.socials.*` (matches by domain)

**Note:** This phase is intake-driven, not hardcoded. Adding a field to the form without updating this script means the field won't be applied — the agent should NEVER manually patch pages when content-layer should be doing it. If a placeholder isn't being substituted, log it and ADD a rule to `stitch-content-layer.py`, then re-run.

---

## Phase 6 — RESEARCH

Use the `dataforseo` skill. Required outputs:
- `ai/research/.dfs/volumes.json` — every keyword Mike's form supplied, plus DFS-suggested expansions, with INTEGER `search_volume` and decimal `cpc` (no string ranges like "Low (50-100)" — those are forbidden).
- `ai/research/.dfs/competitors.json` — top SERP competitors for the primary keyword
- `ai/research/keywords.md` — human-readable summary, every row backed by a row in `volumes.json`. Top of file MUST say `Tools Used: DataForSEO live pull` and link to the JSON.
- `ai/research/topical-map.md` — topic clusters
- `ai/research/page-recommendations.md` — pages to add/strengthen based on keyword gaps

If `volumes.json` exists from a prior run, skip the DFS call (preserves spend on retries). Otherwise call DFS.

---

## Phase 7 — EXTRA-PAGES

Build **every page** from BOTH sources. **Skip nothing.** "FOR MIKE TO REVIEW" is NOT a skip signal — the form already approved everything by the user clicking Start with Stitch supplied.

**Source A — `intake.pages[]`** (the form's declared pages).

**Source B — `ai/research/page-recommendations.md`** (DFS research output). EVERY row in EVERY table in this file becomes a route, including:
- Service-specific pages (PVC Decking, Composite Decking, etc.)
- **Location-specific pages** (Bellevue, Kirkland, Bothell, Redmond, Sammamish, Issaquah, Mercer Island, etc. — every city in the recommendation table)
- **Cost / pricing guides** (e.g. `/deck-cost-seattle`)
- Any "Recommended Additional Pages" that have keyword volume data

If a row is in `page-recommendations.md`, it MUST be built. The only exception is the explicit "Not Recommended" section which has zero volume — those skip.

**Keyword integration is mandatory, not optional.** Each generated page MUST contain ALL its `Primary Keywords` from page-recommendations.md, integrated verbatim into:
- The page's `<h1>` (1+ keyword)
- At least 2 `<h2>` section headers (1 keyword each)
- The first paragraph after the hero (1+ keyword)
- The primary CTA text or supporting subhead (1+ keyword)

Phase 7.5 KEYWORD-COVERAGE-CHECK runs after Phase 7 and fails the build if any required page is missing or any page is missing its keywords. Don't move past Phase 7 until 7.5 is green.

For each page that does NOT already have a `src/app/<slug>/page.tsx`:

1. Pick the **visually closest** existing converted page as a clone source:
   - service-specific page (PVC, Composite, Cedar, Pergolas, etc.) → clone from `services/page.tsx`
   - `gallery` → clone from `services/page.tsx` (grid layout)
   - `contact` → clone from `about/page.tsx`
   - `pricing` → clone from `services/page.tsx`
   - `privacy` / `terms` → simple text page (no clone needed — see legal-page template at end of this doc)
2. Copy the chosen page.tsx to `src/app/<slug>/page.tsx`.
3. Edit ONLY the copy/headings/content to match the page's purpose, sourcing from:
   - The page's row in `page-recommendations.md` (primary keywords, "Why" rationale)
   - `intake.services[]` for the service description (which service this page covers)
   - `intake.targetMarkets[]` for service-area mentions
   - `intake.notes`, `intake.about`, `intake.sellingPoints[]`
   - `ai/research/topical-map.md` for related-keyword integration
   - `intake.gallery[]` for relevant project photos (filter by service if metadata available)
4. Do NOT change the layout, components, class structure, fonts, or color tokens. The Stitch design is locked.
5. **Update the navbar + footer menu** in EVERY page.tsx so the new pages are reachable. The new menu structure must include all top-level routes (Home / About / Services / Gallery / FAQ / Contact) at minimum, plus a Services dropdown OR a Services overview page that links to every individual service page. Match the Stitch navbar styling exactly — same classes, same hover states.
6. **Logo:** every page's navbar must use `intake.logo` (the supplied logo URL or local copy in `public/images/`). The Stitch wordmark fallback only fires if `intake.logo` is empty.
7. After all pages exist, **re-run `stitch-content-layer.py` and `stitch-fix-links.py`** so newly-cloned pages get their phone/email/address swaps + dead-href resolution.

---

## Phase 8 — QUALITY-GATE

```bash
cd "$PROJECT_DIR"
pnpm install
pnpm build 2>&1 | tee .quality-gate/build.log
```

Fail conditions:
- `pnpm build` exits non-zero → halt
- Any TypeScript error → halt (look for "Type error:" in build.log)

Then start `pnpm start` (or `next start`) on a free port and curl every page:
```bash
for slug in $(jq -r '.pages[]' .intake.json); do
  url="http://localhost:$PORT/${slug/home/}"
  code=$(curl -sk -o /dev/null -w "%{http_code}" "$url")
  [[ "$code" != "200" ]] && phase_fail "route $slug returned $code"
done
```

---

## Phase 9 — DEPLOY

```bash
bash /home/node/.claude/skills/website-builder/tools/webdev-deploy.sh --project "$PROJECT_NAME"
```

This recreates the webdev container with the new project as `WEBDEV_PROJECT_NAME`,
nukes stale `.next`/`node_modules`, runs `pnpm install`, restarts.

**Verify:** webdev container is `Up`, port responds 200.

---

## Phase 10 — GITHUB-PUSH

```bash
bash /home/node/.claude/skills/website-builder/tools/github-setup.sh --project "$PROJECT_DIR"
```

If `gh` CLI isn't authenticated in the container or no SSH key is present, log
`gh auth missing` and continue. Host will push manually after build (until github-setup.sh handles credentials).

---

## Phase 11 — VERIFICATION

```bash
DEV_URL=$(jq -r '.devUrl // .domain' .intake.json)
for slug in $(jq -r '.pages[]' .intake.json); do
  url="$DEV_URL/${slug/home/}"
  code=$(curl -sk -o /dev/null -w "%{http_code}" "$url")
  echo "$code $url"
done
```

All 200s = build complete. Mark `phases.verification.status = "complete"` and overall `status = "complete"`.

---

## Halt-on-fail rules

If any phase's `phases.<key>.status = "failed"`:
- Set overall `status = "failed"`
- Set `error.phase = <key>` and `error.message = <last log line>`
- DO NOT proceed to later phases
- DO NOT generate placeholder output to "make it complete"

The user wants the build to STOP at the first real failure so the failure is visible. Skipping ahead and producing a half-broken site wastes another iteration.

---

## What this pipeline is NOT

- It is NOT a "smart" reinterpretation of Stitch design. The whole point of using Stitch is that the design is locked in by the human (or the prior LLM that generated the Stitch screens). This pipeline preserves that design exactly.
- It is NOT generating sections from a `templates/sections/*.tsx` library. Those components are for the LEGACY `WEBSITE-BUILD.md` path only (TIER 1.C). On the Stitch path, every section's markup comes from Stitch HTML.
- It is NOT a one-shot LLM run. Phases 3, 4, 5, 8, 9, 10 are deterministic Python/shell. Only 2, 6, 7, 11 use the LLM.
