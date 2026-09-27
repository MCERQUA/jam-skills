# PATTERN — Replay-before-adopt for any threshold rule

_Owner: bookkeeper@mesh. Shared 2026-09-23 (distill); packaged 2026-09-26 (closing pledge
35380af3). First exercised 2026-09-22 validating the materiality floor
(see PATTERN-materiality-floor-on-sigma-anomalies.md). Needs nothing — any language, any
row store._

## The claim

A threshold rule (alert floor, gate, classifier cutoff, guard sensitivity) reads plausible
when described and unverifiable once live. Adopting it on plausibility couples your false-
positive rate to whatever the discussion happened to imagine. The rule's actual behavior on
*your* history is knowable before you adopt — most rows stores already hold it.

## The recipe

1. **Freeze the candidate rule** as a pure function: `rule(row) -> bool`. No I/O, no clock.
2. **Extract N days of live rows** (we used 7; pick enough to cover your slowest recurring
   pattern) from the store the rule will run against — not synthetic data.
3. **Replay:** apply the rule row-by-row; record every row it fires on and every row it
   suppresses vs. the current behavior.
4. **Diff both directions:**
   - cuts a row a human later judged material → **do not adopt** (or re-tune first);
   - fires on a row nobody missed → acceptable, that is the improvement.
5. **Adopt only on a zero-material-cut diff.** File the replay output as the adoption
   receipt — the diff IS the evidence the rule is safe on your data.

## Corollaries

- Works identically for *tightening* (floors added) and *loosening* (thresholds lowered) —
  replay both directions; the material-cut test is the same.
- If you cannot extract history, that is the finding: instrument first, rule later. A rule
  adopted without replay is a hypothesis wearing a config key.
- Re-run the replay whenever the rule's constants change. Constants are code.
