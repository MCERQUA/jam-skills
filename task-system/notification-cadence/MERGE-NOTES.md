# Milestone-4 merge notes — josh-desktop reconciliation

**Author:** josh-desktop@mesh (sub-mesh manager)
**Date:** 2026-05-19
**For:** host@mesh nightly synthesize (due 2026-05-20)

## Summary

All three workers shipped clean deliverables (see each `worker-{a,b,c}/DONE.txt`). When their patches are applied to a fresh v0.1.3 copy in series (a → b), there is **one 2-hunk conflict** — both worker-a and worker-b independently rewrite the same `$id` / `title` / `description` / module-docstring lines because both are bumping v0.1.3 → v0.1.4. The rest of the patches touch independent fields and apply cleanly.

Verified by dry-run merge in `/tmp/v014-merge-test/`:
- worker-a patches (both files) → CLEAN
- worker-b on top:
  - `task-json-schema.json` — 1 of 2 hunks failed (header rewrite collision)
  - `task_schema.py` — 1 of 4 hunks failed (module docstring), 3 succeeded with offsets

## Proposed unified header (for host to apply during synthesize)

### `task-json-schema.json` lines 1–8

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://jam-bot.com/schemas/task-json/v0.1.4.json",
  "title": "JamBot task.json (canonical v0.1.4 — notification_policy + two-phase schedule)",
  "description": "v0.1.3 (failure_modes enum locked) + notification_policy field (default mode 'roll_up_daily') + research_at sibling of scheduled_at for two-phase scheduling. Both additions are additive — v0.1.3 records without these fields validate clean under v0.1.4. Milestone-4 per host msg 2026-05-19-001.",
  "type": "object",
  "additionalProperties": false,
  "required": [
```

### `task_schema.py` line 2 (module docstring)

```python
task.json schema validator — v0.1.4 (notification_policy + two-phase schedule on top of v0.1.3).
```

## After header is resolved, the rest composes — EXCEPT one more

Patches that apply clean independently:

| File | worker-a hunk | worker-b hunk |
|---|---|---|
| `task-json-schema.json` | adds `notification_policy` property block | adds `research_at` property block |
| `task_schema.py` | adds `NOTIFICATION_MODES` const + `notification_policy` TASK_FIELDS entry + `_check_notification_policy` branch | adds `research_at` TASK_FIELDS entry + `optional` type-check branch |
| `canonical-task.examples.json` | adds 3 mode examples at line 70+ | hunk #1 extends decking-callback with `research_at` (clean) — **hunk #2 collides** with worker-a's additions at end-of-file |

### Third conflict — `canonical-task.examples.json` hunk #2

Worker-a appended 3 new mode-example records at end of the examples array (originally line 70+). Worker-b's hunk #2 also targets that region to append 2 new schedule-example records. Verified by dry-run apply in `/tmp/v014-build/` — worker-b hunk #2 fails because line numbers shifted.

**Resolution:** mechanical — append both sets concatenated. The 3 worker-a notification-mode examples and the 2 worker-b schedule examples are independent records; either ordering works. Recommend worker-a's records first (lower ID timestamps) then worker-b's records.

Worker-b's 2 new records to append after worker-a's set:
- `2026-05-19-0930-josh-brief-task-74-plan` (state=scheduled, both phases populated, 60-min delta)
- `2026-05-19-1015-cca-research-blocker-parked` (state=parked, demonstrates research-blocker flow)

## Worker-c smoke depends on both

`worker-c/smoke_test.patch` exercises **both** new fields together in one e2e scenario. Two TODO markers in the patch await the final symbol names from worker-b's resolver — minor and called out in worker-c's DONE.txt. Recommend host resolve those during synthesize (likely a 2-line search/replace).

## Open questions surfaced by workers (9 total — consolidate?)

worker-a:
- Q1 inline mode firing scope (done-only vs broader state transitions)
- Q2 `on_finding_threshold.metric` — ratchet to enum now or at v0.2?
- Q3 per-recipient-role override (force `roll_up_daily` for `recipient_role: client`?)

worker-b:
- Q1 overdue-research behavior (fire-immediately vs skip vs push `scheduled_at`?)
- Q2 add `research_completed_at` field, or scan `state_history`?
- Q3 60-min default — schema constant or scheduler-side only?

worker-c:
- (no open Qs; TODO markers are mechanical, not architectural)

josh-desktop note: Q3 from worker-a and Q1 from worker-b touch the same surface (what happens when planning surfaces a blocker that affects `recipient_role`-bound notification). Probably one consolidated answer covers both.

## What's NOT done

- No actual schema files written — patches only.
- Header conflict NOT pre-resolved in patches; host applies the unified version above during synthesize.
- The 9 open questions are surfaced, not answered — host or Mike-gate.

— josh-desktop@mesh
