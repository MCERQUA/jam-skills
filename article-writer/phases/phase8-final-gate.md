# Phase 8 — Final Quality Gate (automated, no human review)

Route the final review through the **`quality-review`** skill plus an article-final-review-agent
for content parity. Keep the score-9+ auto-proceed behavior.

## Run the gate
```bash
# Functional: routes/images/internal links/required sections/fabrication markers
python3 /mnt/shared-skills/quality-review/check.py --dir <work_dir>/<slug> \
  --routes "/article-final.html" \
  --require "Frequently Asked Questions,Conclusion" --out /tmp/qr-<slug>-final

# Visual: contrast (no light-on-light), mobile overflow, broken images — at 390 + 1440
python3 /mnt/shared-skills/quality-review/visual-check.py --url <served-html-url> \
  --viewports 390,1440 --out /tmp/qr-<slug>-visual
```
(If the HTML isn't reachable over HTTP, point `check.py` at the file/dir and run the visual check
against the served file.)

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
