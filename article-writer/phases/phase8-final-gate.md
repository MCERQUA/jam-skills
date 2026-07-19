# Phase 8 — Final Quality Gate (automated, no human review)

Route the final review through the **`quality-review`** skill plus an article-final-review-agent
for content parity. Keep the score-9+ auto-proceed behavior.

## Run the gate
```bash
# Functional: routes/images/internal links/required sections/fabrication markers
python3 /mnt/shared-skills/quality-review/check.py --dir <work_dir>/<slug> \
  --routes "/article-final.html" \
  --require "Frequently Asked Questions,Conclusion" --out /tmp/qr-<slug>-final

# Visual gate — LIVES IN THIS SKILL (scripts/verify/visual-check.py), never skip it because
# an external quality-review path is missing. Renders 390px in DARK scheme + 1280px light,
# hard-fails on horizontal overflow / broken images / prefers-color-scheme:dark blocks,
# and writes JPEG strips of the whole page:
python3 <this-skill>/scripts/verify/visual-check.py \
  --serve-dir <built site root or article dir> --path /blog/<slug>/ --out /tmp/qr-<slug>-visual
```
(If `check.py` is missing on the host, self-apply its checks; the visual gate has NO such
fallback — it must actually run.)

**THEN LOOK AT THE STRIPS.** Open several `strip-*.jpg` with the Read tool (they're sized for
it) — the mobile-dark set especially. You are looking for what scripts can't score: light-grey
text on white, brand-purple headings on dark, muddy/dark overall cast, cramped or overlapping
components, clipped chart labels. An article is NOT publication-ready until a rendered
screenshot has been seen by the reviewing agent. (DSF 2026-07-19: three articles shipped with
half-baked dark-mode overrides — dark-on-dark H2s, grey-on-cream callouts on every dark-mode
phone — because this step was skipped when the old gate path didn't exist.)

## Agent review (content parity + standards)
- Content parity: every markdown section present in HTML and vice-versa (the Phase-7 design
  transform must not add or drop content — only style it).
- Word count hits `word_target`; natural keyword integration; FAQ complete (8-12); strong
  intro/conclusion; correct heading hierarchy; all images have alt text; links work.

## Design gate (verifies the Phase-7 "designed article, not a document" bar)
The HTML must be a **designed** page, not a prose wall. FAIL (→ AUTO-FIX in Phase 7) if any of:
- **Density:** fewer than ~1 non-prose visual block per 500 words (≥8 component blocks for a 4k article).
- **Variety:** fewer than **4 distinct** component types used (callout / stat cards / card grid /
  table / pros-cons / pull-quote / figure / **data chart** / FAQ accordion).
- **Visuals missing:** no embedded imagery/infographics, OR — when the article has quantitative
  content — **no real data visualization** (native SVG chart or a data infographic).
- **Required structure missing:** no gradient hero, OR no "Key Takeaways" block near the top, OR no
  CTA block at the end.
- **Fake data viz:** a chart rendered as a generated image instead of native SVG (image-model charts
  fabricate numbers — must be inline `<svg>` from the real figures, with `aria-label` + caption).
- **Self-contained broken:** no scoped `<style>` block, OR relies on a CDN/build (Tailwind classes
  with no embedded CSS, external icon font).
- **Rule violations:** any emoji in the UI, any purple, any light-on-light (visual-check contrast),
  any literal `{{placeholder}}`.
Quick check: `grep -c 'aw-callout\|aw-stat\|aw-card\|aw-table\|aw-quote\|aw-faq\|aw-figure\|aw-chart' <html>`
should comfortably exceed the density floor; `grep -c '<style' <html>` ≥ 1; `grep -c '<svg' <html>` ≥ 1.

## Autonomous decision
- **9+ AND quality-review PASS (exit 0) →** AUTO-PROCEED to Phase 9.
- **7-8 →** AUTO-FIX findings (missing links, alt text, contrast, structure), re-gate.
- **<7 →** AUTO-FIX, possibly re-draft sections, re-gate.
- `quality-review` exit 1 = FAIL = do NOT ship — fix and loop until PASS.
