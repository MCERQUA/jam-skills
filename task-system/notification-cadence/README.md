# Milestone-4 snapshot — notification cadence + two-phase schedule

**Dispatch:** host@mesh → josh-desktop@mesh msg `2026-05-19-001-host-milestone-4-notification-cadence-and-cron-split.md`
**Synthesizer:** josh-desktop@mesh (sub-mesh: worker-a, worker-b, worker-c)
**Date:** 2026-05-19
**Schema bump:** v0.1.3 → v0.1.4 (additive; backward-compatible)

## Contents

```
worker-a/   notification_policy field (NOTIFICATION-POLICY.md + 3 patches)
worker-b/   research_at field + cron template (SCHEDULE-DESIGN.md + 3 patches + cron-template.sh)
worker-c/   smoke harness extension (SMOKE-DESIGN.md + 2 fixtures + smoke_test.patch)
SYNTHESIS.md       cross-worker analysis, drift flags, recommended deploy order
OPEN-QUESTIONS.md  9 questions for host — 3 per worker, grouped
```

## TL;DR

- All 3 worker deliverables complete + self-verified.
- 2 cross-worker drifts surfaced — see SYNTHESIS.md §3:
  1. **Enum casing** (snake_case vs kebab-case)
  2. **Default-resolver location** (scheduler-side vs `task_schema.py` helper)
- Both schema patches bump header to v0.1.4 — header lines conflict if applied serially; property additions land at non-overlapping lines.
- Recommended deploy: apply property additions only, ship a single merged header bump.

See SYNTHESIS.md for the full report.
