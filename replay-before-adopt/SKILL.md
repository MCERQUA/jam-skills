---
name: replay-before-adopt
description: Before adopting any threshold rule, alert floor, or statistical anomaly flag, replay it as a pure function against N days of live historical rows and adopt only on a zero-material-cut diff. Pair every statistical flag with a two-part materiality floor. Use when adding/tightening/loosening any alert threshold, sigma/z-score gate, or classifier cutoff.
---

# Replay-before-adopt + materiality floor

**The rule, in one line:** *a threshold rule reads plausible when described and is
unverifiable once live — replay it against your own history before adopting, and never
let a statistical flag fire without a materiality floor beside it.*

Two full recipes live in this directory (copied verbatim from the blackboard bin, owner
bookkeeper@mesh):

1. **[PATTERN-replay-before-adopt.md](PATTERN-replay-before-adopt.md)** — freeze the rule
   as `rule(row) -> bool`, extract N days of live rows (7 is a working minimum) from the
   store the rule will run against, replay, diff both directions, adopt only on a
   zero-material-cut diff. The replay output IS the adoption receipt. If you cannot
   extract history, that is the finding: instrument first, rule later.

2. **[PATTERN-materiality-floor-on-sigma-anomalies.md](PATTERN-materiality-floor-on-sigma-anomalies.md)** —
   pair every sigma/z-score flag with a CONJUNCTION: `sigma > threshold AND value >=
   baseline*RELATIVE_FLOOR AND value >= ABSOLUTE_FLOOR`. The relative floor kills the
   low-variance wobble false positive; the absolute floor kills the tiny-denominator
   case. Constants are domain-owned — pick floors in your lane's units and re-run the
   replay for them.

## What you need

- A **row store**: the historical rows the rule will run against (jsonl ledger, report
  history, log dir — any queryable series). No row store = no replay = do not adopt.
- Nothing else. Any language; the reference implementation is bookkeeper's
  `_sigma_anomalies()` (path in the materiality PATTERN doc).

## Validated

First exercised 2026-09-22 (materiality floor adopted after a 7-day before/after replay:
floors cut the ±5%-wobble noise class entirely, kept both real spikes); packaged
2026-09-26 closing pledges 35380af3 / 9d94339b.
