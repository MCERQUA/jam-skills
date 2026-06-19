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
- Content parity: every markdown section present in HTML and vice-versa.
- Word count hits `word_target`; natural keyword integration; FAQ complete (8-12); strong
  intro/conclusion; correct heading hierarchy; all images have alt text; links work.

## Autonomous decision
- **9+ AND quality-review PASS (exit 0) →** AUTO-PROCEED to Phase 9.
- **7-8 →** AUTO-FIX findings (missing links, alt text, contrast, structure), re-gate.
- **<7 →** AUTO-FIX, possibly re-draft sections, re-gate.
- `quality-review` exit 1 = FAIL = do NOT ship — fix and loop until PASS.
