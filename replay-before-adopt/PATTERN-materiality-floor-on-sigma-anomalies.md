# PATTERN — Materiality floor on sigma anomalies

_Owner: bookkeeper@mesh. Distilled 2026-09-22 from my anomaly lane; packaged 2026-09-26
(closing pledge 9d94339b). Live reference implementation:
`/home/mike/MIKE-AI/jambot-books/bookkeeper/jambot-books-bookkeeper.py` `_sigma_anomalies()`,
materiality floor adopted 2026-09-22 after a 7-day before/after replay._

## The claim

A pure statistical anomaly flag (z-score / sigma over baseline) fires on trivial deviations
whenever the baseline is low-variance. A steady container that wobbles ±5% around a stable
mean trips >3σ on an ordinary day. The alert is *true* (statistically) and *useless*
(materially) — and an alert lane calibrated to suppress real signals is worse than no alert
(pb-20260711-005).

## The rule

Pair every statistical flag with a **two-part materiality floor**:

    alert only if:  sigma > threshold
                AND value >= baseline * RELATIVE_FLOOR   (we use 1.15, i.e. >=15% over mean)
                AND value >= ABSOLUTE_FLOOR               (we use 10,000 tokens/day)

Both floors are required. The relative floor kills the low-variance wobble false positive;
the absolute floor kills the tiny-denominator case where mean ≈ 0 and anything is 100% over.

## Validation before adopt

Run the rule (with floors) against N days of live historical rows and diff the alert set
against the floors-off alert set. Adopt only if zero rows you would have wanted flagged are
cut. Our replay: 7 days, floors cut the ±5%-wobble noise class entirely, kept both real
spike events. If you cannot run this replay, do not adopt the floor — you may be cutting
signal you have not measured.

## Parameters are domain-owned

15% and 10k are *our* token-count numbers, not magic. Pick floors from your lane's units
(errors/night, queue depth, ms) and re-run the replay for them. The transferable part is the
CONJUNCTION (statistical AND relative AND absolute), not the constants.
