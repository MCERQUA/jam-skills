# Phase 3 — Research Quality Gate (automated, no human review)

Gate the research through the **`quality-review`** skill plus a research-quality-reviewer-agent for
the qualitative score. This replaces the original's ad-hoc agent rubric while keeping the
score-8+ auto-proceed behavior.

## Do
1. Run the qualitative review: score each research area (topic, keyword, authority, FAQ) 1-10 on
   **Completeness, Quality, Depth** (enough for `word_target`), **Actionability**. List gaps.
2. Run `quality-review`'s completeness/coverage check over the staged research dir so the gate is
   data-backed, not vibes:
   ```bash
   python3 /mnt/shared-skills/quality-review/check.py --dir <work_dir>/<slug> \
     --require "topic-research,keyword-research,authority-link-research,faq-research" \
     --out /tmp/qr-<slug>-research
   ```
3. Write the combined `research-summary.md` (per-area scores, gaps, decision).

## Autonomous decision (score-driven)
- **8+ and quality-review PASS →** AUTO-PROCEED to Phase 4.
- **6-7 →** AUTO-FIX: re-run only the weak agent(s) with enhanced gap-filling prompts; re-gate.
- **<6 →** AUTO-FIX: re-run ALL research agents with detailed instructions; re-gate.
- Loop until PASS. No caller notification, no pause. This is an agent gate, not a human gate.
