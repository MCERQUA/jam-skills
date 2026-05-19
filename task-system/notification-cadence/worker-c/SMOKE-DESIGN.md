# worker-c — milestone-4 smoke scenario design

**Author:** worker-c@mesh (dispatched by josh-desktop@mesh, parent host@mesh).
**Due:** 2026-05-20 nightly synthesize.
**Status (2026-05-19):** worker-a/DONE.txt and worker-b/DONE.txt both
landed; this design is **verified** against the merged v0.1.4 validator
(see `SAMPLE-RUN.txt`, all 9 steps + 7 sub-assertions PASS).
**Extends:** `/agent-desk/snapshots/2026-05-19-bootstrap-smoke/smoke_test.py`
(8 PASS steps → 9 PASS steps).

## What this adds

One end-to-end step (step 9) on top of the existing bootstrap-smoke
harness, exercising **both** milestone-4 fields together as they actually
shipped:

- `notification_policy` (worker-a, v0.1.4) — **OBJECT**
  `{"mode": "...", "on_finding_threshold": <object|null>}`.
  Mode enum (snake_case): `inline | roll_up_daily | on_finding`.
  Field is **optional**; reader treats absence as `{"mode": "roll_up_daily"}`.
- `research_at` (worker-b, v0.1.4) — ISO-Z UTC sibling of `scheduled_at`.
  Field is **optional**; scheduler computes `scheduled_at − 60min` at
  fire-time when the value is null/absent. **Field stays null in the
  file** — defaults are never frozen in.

Key correction vs the worker-c draft posted before peers landed: the
brief described `notification_policy` as a flat string enum with values
like `roll-up-daily`. Worker-a chose an **object** shape with snake_case
enum (`roll_up_daily`) and the threshold nested inside (see
`worker-a/NOTIFICATION-POLICY.md` §1). The fixtures, assertions, and
default-resolution helpers below all match the shipped shape.

## Scenario shape

Two fixtures live alongside the design doc:

| File                                | State       | Purpose                                                              |
|-------------------------------------|-------------|----------------------------------------------------------------------|
| `milestone-4-scenario.json`         | `scheduled` | Valid task with **both** new fields explicitly set; baseline pass.   |
| `milestone-4-invalid.json`          | `scheduled` | Two intentional defects (bad mode enum + bad ISO-Z) — must be rejected. |

The valid fixture pins:
- `scheduled_at: 2026-05-20T15:00:00Z`
- `research_at:  2026-05-20T14:00:00Z`  (= `scheduled_at − 60min`)
- `notification_policy: {"mode": "on_finding", "on_finding_threshold": null}`
  (non-default mode; proves the field is honoured rather than coerced).

The invalid fixture sets `notification_policy.mode: "every_five_minutes"`
(not in enum) **and** `research_at: "2026-05-20 14:00"` (missing the
`T...Z` shape) — each defect alone is enough to fail validation; bundling
both proves the validator flags both. Verified emitted errors:
```
research_at: must be ISO-8601 UTC ending in Z or null; got '2026-05-20 14:00'
notification_policy: notification_policy.mode must be one of ('inline', 'roll_up_daily', 'on_finding'); got 'every_five_minutes'
```

## Defaults are READER-side and SCHEDULER-side, not schema-side

Critical to test correctness: **neither peer ships a
`task_schema.resolve_defaults` helper.** Both designs explicitly choose
to apply defaults outside the validator:

- worker-a (NOTIFICATION-POLICY.md §1): "Absent ⇒ reader treats as
  `{\"mode\": \"roll_up_daily\"}`." Default is applied by intake adapter
  / reader, not materialised into the record.
- worker-b (SCHEDULE-DESIGN.md §3): "the scheduler computes the
  effective research moment as `scheduled_at − 60min` at fire-time. The
  field in the file stays null — defaults are never frozen into the
  record."

The smoke therefore implements two local helpers
(`_effective_notification_policy`, `_effective_research_at`) that mirror
the reader/scheduler rule. These prove the **rule** holds; they would be
the production reader/scheduler's own implementation when those land.

## Assertions

Each sub-assertion logs `[smoke] (9.N) ...: PASS`; the umbrella step
prints `[smoke] (9) milestone-4 notification cadence + research_at: PASS`.

| #    | Assertion                                                                                                                                              | Why it covers e2e                                                                       |
|------|--------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| 9.1  | `task_schema.validate_task_record(valid)` returns `[]`.                                                                                                | v0.1.4 schema (worker-a + worker-b merged) accepts the canonical record.                |
| 9.2  | Loaded record has `notification_policy == {"mode": "on_finding", "on_finding_threshold": None}` and `research_at == "2026-05-20T14:00:00Z"`.            | Object-shape policy and ISO-Z research_at both round-trip through file → loader.        |
| 9.3  | Drop fixture into `tasks/scheduled/<id>/`, run `task_bootstrap.load_context`, assert task surfaces under `open_tasks["scheduled"]` and **both** fields are preserved on the in-memory record. | Loader (worker-a-bootstrap snapshot, predates milestone-4) is field-agnostic; this confirms it doesn't strip unknown-to-it keys. |
| 9.4  | **Scheduler-side default:** set `research_at = null`, assert record still validates (optional), then compute `_effective_research_at(record)` and assert it equals `scheduled_at − 60min`. | Worker-b's scheduler-side default rule is enforced.                                     |
| 9.5  | **Reader-side default:** delete `notification_policy`, assert record still validates (optional), then compute `_effective_notification_policy(record)` and assert it equals `{"mode": "roll_up_daily"}`. | Worker-a's reader-side default rule is enforced.                                        |
| 9.6  | `task_schema.validate_task_record(invalid)` returns errors mentioning `notification_policy` AND errors mentioning `research_at`.                        | Schema rejects malformed inputs for **both** new fields (not just one).                 |
| 9.7  | After seed: `open_task_count == 5` (3 originally seeded + 1 step-6 intake + 1 milestone-4 scheduled).                                                  | End-to-end stitch: fixture is visible across the full bootstrap-smoke chain.            |

## Coverage justification

The brief asks for one scenario that "covers BOTH new fields together
(e2e, not isolated)". This step:

- **Co-locates both fields in one fixture** (9.1, 9.2) — a tenant agent
  reading the record sees them as a unit, not as two independent knobs.
- **Exercises the loader path** (9.3, 9.7) — the existing
  `task_bootstrap.load_context` predates milestone-4, so this proves the
  v0.1.4 fields ride through an unchanged loader rather than getting
  filtered out.
- **Exercises BOTH default-resolution rules** (9.4, 9.5) — required by
  the brief. Each test names the expected value explicitly; if a peer
  ships a different default, the assertion message says which one drifted.
- **Exercises the validator's rejection path** (9.6) — covers the "1
  invalid example" requirement and proves both fields participate in
  schema error reporting (not just one).

## Coordination notes (for host@mesh nightly synthesize)

Both peer patches collide on **one** identical-line hunk: the
`task_schema.py` module docstring AND the `task-json-schema.json` title
/ description. Both peers independently rewrite v0.1.3 → v0.1.4 with
their feature's title. Resolution is mechanical — merge both descriptions
into one combined title:

> task.json schema validator — v0.1.4 (notification_policy + research_at
> added; v0.1.3 fields unchanged).

Worker-c verified the smoke against a hand-merged v0.1.4 with this combined
header; all 9 steps PASS. No semantic conflict in either peer patch
beyond the version-bump line.

## Out of scope

- **Cron behaviour.** The two-cron design (research worker + scheduler
  worker) is documented in worker-b's `cron-template.sh`. This smoke
  asserts schema + defaults only — running the cron is post-merge.
- **`on_finding_threshold` ratchet.** Worker-a flagged this as v0.2
  follow-up; current schema accepts any object. Smoke asserts only that
  the field is allowed (null in the valid fixture).
- **State transitions.** Milestone-4 fields don't alter the state
  machine; existing state_history assertions cover transitions.
- **Mesh I/O.** Honours bootstrap-smoke's "no external I/O" constraint —
  all work stays under `/tmp/bootstrap-smoke-*/`.

## References

- Bootstrap smoke harness: `/agent-desk/snapshots/2026-05-19-bootstrap-smoke/`
- Canonical schema v0.1.3 baseline: `/agent-desk/snapshots/2026-05-19-canonical-schema-v0.1.3/`
- Peer deliverables (verified landed 2026-05-19):
  - `worker-a/NOTIFICATION-POLICY.md`, `worker-a/task-json-schema.patch`, `worker-a/task_schema.patch`
  - `worker-b/SCHEDULE-DESIGN.md`, `worker-b/task-json-schema.patch`, `worker-b/task_schema.patch`, `worker-b/cron-template.sh`
- Spec context: `/mesh/BLACKBOARD/task-system/v0.2-spec-amendment.md:209-211`.
