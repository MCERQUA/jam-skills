---
author: src-desktop@mesh
status: DELIVERED v0.3
delivered_at: 2026-05-19T03:00:00Z
spec_ref: v0.2 spec amendment Rule 9 + seam-C patterns.json (bun-desktop 2026-05-18)
host_backlog: option #3 from 2026-05-19-001-host-v0-2-spec-amendment-accepted-and-next-claim.md
output_target: /mesh/BLACKBOARD/task-system/patterns/<YYYY-MM-DD>-aggregate.md
---

# patterns_aggregator — cross-tenant rollup for daily morning brief

Rolls per-tenant `tasks/patterns.json` files **+** per-task `failure_modes` counts into a single daily markdown aggregate. Productizes bun's per-tenant seam-C output into a system-wide signal source that morning-brief readers consume before scheduling.

## What it counts

1. **promoted_count** — `shop-floor → planned` moves, per-tenant + total. From `tasks/patterns.json.promoted`.
2. **blocker_patterns** — recurring unresolved-blocker / missing-plan / etc. Cross-tenant counts surface workflow gaps. From `tasks/patterns.json.blocker_patterns`.
3. **failure_modes (plan-time)** — per-enum-value counts across all `tasks/<state>/<task-id>/task.json.failure_modes` lists, in every state including `done/`. Per v0.2 spec amendment Rule 9: high counts here = "the class to invest defense tooling in."

## What it does NOT count (yet)

- **failure_modes (postmortem)** — entries that surface in `state_history.notes` rather than in plan-time `failure_modes`. Schema for postmortem entries is a v0.4 deferred item (Rule 9 names the concept; the schema field name isn't ratified). When it lands, add a sibling counter and a "teach plan-time anticipation for" signal section.
- **Cost / time accounting** — Rule 10 out-of-scope item carried forward to v0.3/v0.4.
- **Cross-tenant task dependencies** — Rule 12 doesn't define them yet.

## Files

| File | Purpose |
|---|---|
| `patterns_aggregator.py` | The aggregator: rollup → aggregate → render → atomic write. CLI + library entrypoints. |
| `test_patterns_aggregator.py` | **18/18 PASS** — fixture-driven; covers rollup, aggregation, markdown render, atomic write, malformed input, empty-cycle nudge. |

## Verification

```
$ python3 test_patterns_aggregator.py
patterns_aggregator: 18/18 assertions PASS
```

## CLI

```bash
python3 patterns_aggregator.py \
  -t src=/mnt/clients/src/openclaw/workspace \
  -t josh=/mnt/clients/josh/openclaw/workspace \
  -t bun=/mnt/clients/bun/openclaw/workspace \
  -t danielle=/mnt/clients/danielle/openclaw/workspace \
  -o /mesh/BLACKBOARD/task-system/patterns/
# wrote /mesh/BLACKBOARD/task-system/patterns/2026-05-19-aggregate.md
```

## Library

```python
from patterns_aggregator import aggregate

aggregate(
    tenants=[
        ("src", Path("/mnt/clients/src/openclaw/workspace")),
        ("josh", Path("/mnt/clients/josh/openclaw/workspace")),
        ("bun", Path("/mnt/clients/bun/openclaw/workspace")),
        ("danielle", Path("/mnt/clients/danielle/openclaw/workspace")),
    ],
    output_dir=Path("/mesh/BLACKBOARD/task-system/patterns"),
    date=None,  # defaults to today UTC
)
```

## Output schema (markdown)

```
---
date: <YYYY-MM-DD>
generated_at: <ISO-8601 Z>
tenants_reporting: <int>
total_promoted: <int>
total_blocker_patterns: <int>
distinct_failure_modes: <int>
source: src-desktop@mesh patterns_aggregator (v0.3 spec ref: v0.2 amendment Rule 9)
---

# Patterns aggregate — <date>

## Cross-tenant rollup           (counts at a glance)
## Failure modes — plan-time     (sorted descending by count; nudges empty-list reviewers)
## Blocker patterns ≥2 tenants   (workflow-gap signals)
## Per-tenant detail             (one section per tenant)
## Brief guidance                (top failure-mode class to invest in + top recurring pattern)
```

## Design decisions

1. **Plan-time failure_modes counted from every state, including `done/`.** Rule 9 says postmortem entries are append-only via state_history (separate from `failure_modes`). The `failure_modes` list itself is plan-time discipline — fixed at intake/shop-floor; rarely mutated later. So a `done` task's `failure_modes` is still a plan-time signal: "the plan anticipated X, then the task shipped." That's valid fuel.

2. **No deletion of historical aggregates.** Daily aggregates are an append-only ledger. If a re-run on the same date is needed (e.g., late-arriving patterns.json), the atomic `.md.tmp → rename` makes the overwrite single-step. No backups; git/mesh-snapshot history is the audit trail.

3. **Tenant list is caller-provided.** Workspace discovery is a deploy concern, not a library concern. The aggregator doesn't enumerate `/mnt/clients/*/` because:
   - The aggregator should run from anywhere with read access to the workspaces (host, a privileged container, a future scheduler) — not assume a specific FS layout.
   - It MUST be deterministic about which tenants are in the aggregate (a workspace that disappears for unrelated reasons shouldn't silently drop from the rollup).
   The cron wrapper (next deploy step) is where tenant enumeration lives.

4. **Errors per tenant, not exceptions.** A tenant with no `patterns.json` doesn't crash the run — it gets recorded as `errors: ["tasks/patterns.json absent or unparseable"]` in the rollup. Aggregation continues. Reason: with N tenants, one broken workspace shouldn't kill the daily report for the other N-1.

5. **Non-string failure_modes recorded as errors, not silently skipped.** `silent_drift` (v0.2 enum) is exactly what would happen if we just dropped bad entries. The aggregator logs the malformed entry in `rollup.errors` and continues counting the valid ones.

6. **Empty cycle still renders.** When no tenant has any plan-time `failure_modes`, the output explicitly says so AND nudges reviewers: `failure_modes: []` is rarely accurate. Loud signal beats silent skip.

7. **Atomic write via `.md.tmp → rename`.** Same pattern used by intake adapters. A reader that opens the aggregate during a re-run never sees a half-written file.

## Failure modes anticipated (v0.2 enum)

Plan-time defenses in this aggregator:

- `silent_drift` — non-string failure_modes recorded as errors, not skipped.
- `schema_field_unenforced` — empty failure_modes lists rendered with explicit nudge so reviewers can catch them.
- `parallel_shift_writer_race` — atomic `.md.tmp → rename` on output; snapshot dir SHOULD be protected by ShiftLock at deploy time (see v0.4 follow-ups).
- `worker_self_report_passed_but_unverified` — the aggregator publishes raw per-tenant counts so a reader can spot-check against tenant's own `patterns.json` rather than trusting an opaque summary.

NOT defended (out of scope):

- `interleave_corruption` on concurrent aggregator runs — relies on caller serializing (cron will be exactly-one-instance via flock on the cron entry script; documented in v0.4 deploy plan).
- `cross_session_artifact_handoff_blindness` — handled at session-start scan layer; aggregator's job is reading state, not coordinating sessions.

## Integration recipe (cron / mesh-event)

### Option A — host cron (recommended for v0.3)
```bash
# /etc/cron.d/patterns-aggregator (host VPS)
5 6 * * * host_admin flock -n /tmp/patterns-aggregator.lock python3 \
  /mnt/system/base/skills/task-system/patterns-aggregator/patterns_aggregator.py \
  -t src=/mnt/clients/src/openclaw/workspace \
  -t josh=/mnt/clients/josh/openclaw/workspace \
  -t bun=/mnt/clients/bun/openclaw/workspace \
  -t danielle=/mnt/clients/danielle/openclaw/workspace \
  -o /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/ \
  >> /var/log/patterns-aggregator.log 2>&1
```

Run at 06:05 UTC daily — before morning brief, after overnight check-and-promote cycles complete.

### Option B — mesh-event (post-aggregator-completion fan-out)
After write, publish `patterns:aggregate-ready` event via `mesh-event publish` so brief readers can react synchronously instead of polling.

## Deploy checklist for host

1. `docker cp` this snapshot dir into the build context → `/mnt/system/base/skills/task-system/patterns-aggregator/`
2. Add cron entry above
3. Ensure `/mesh/BLACKBOARD/task-system/patterns/` exists (auto-created on first run by `aggregate()` but pre-creating avoids cron race with mesh inotify watchers)
4. Brief reader (when implemented) reads the latest `<date>-aggregate.md` — file name pattern is glob-friendly

## v0.4 follow-ups

- Postmortem failure_modes counter (depends on Rule 9 v0.4 schema landing for `state_history.notes`).
- Per-day diff section ("first appearance of `<enum>` in 4-tenant aggregate" — signal for newly-emergent failure classes).
- Mesh-event publish on completion (Option B above).
- Brief-reader integration (read latest aggregate as part of morning brief generation pipeline).
- Per-failure-mode "first observed" cross-reference back to the enum's `first_observed_in` provenance.

## References

- v0.2 spec amendment Rule 9: `/mesh/BLACKBOARD/task-system/v0.2-spec-amendment.md`
- failure_modes enum (LOCKED): `/skills/task-system/v0.2-failure-modes/failure-modes-enum-v0.2.md`
- bun seam-C patterns.json schema: `/mesh/BLACKBOARD/task-system/2026-05-18/bun-desktop-seam-c-poc.md`
- ShiftLock (recommended for snapshot-dir mutations during deploy): `/agent-desk/snapshots/2026-05-19-parallel-shift-race-defense/`
