# canonical-schema v0.1.2 — Changelog vs v0.1.1

**Trigger:** host@mesh decision 2026-05-18 (`2026-05-18-001-host-rule-8-7-baked-into-v0-1-1-flip-pending-to-required.md`) — Rule 8 + Rule 7 accepted as v0.1.1 invariants per Mike's direct call. v0.1.2 implements the flip.

## What changed

### `task_schema.py`

- Module docstring: re-marked from "Rule 8 amendment (PENDING host@mesh confirm)" to "Rule 8 + Rule 7 (host@mesh CONFIRMED 2026-05-18)"
- `TASK_FIELDS` entries for `dedup_hash`, `recipient_role`, `linked_to`: `"pending_rule_8"` → `"always"`
- `_required()` helper: dropped the `pending_rule_8` branch (no longer reachable)

### `task-json-schema.json`

- `$id`: `v0.1.1.json` → `v0.1.2.json`
- `title`: appended "(Rule 8 + Rule 7 confirmed)"
- `description`: rewritten to reflect host's confirmation
- `required[]`: added `dedup_hash`, `recipient_role`, `linked_to` (was 15 fields, now 18)
- Per-field `description` for the three: removed "PENDING_HOST_CONFIRM. Required once host@mesh confirms; until then optional." and replaced with "Required-always."

### `test_canonical_schema.py`

- `make_valid_intake` baseline record: added `dedup_hash`, `recipient_role: "mike"`, `linked_to: []` so the default valid task carries all required fields
- Test [19] **inverted**: was "Rule-8 fields optional pre-confirm: OK" → now "Rule-8 fields REQUIRED post host-confirm" — loops through all three fields, deletes each in turn, asserts the task is rejected with the expected missing-field error

## What did NOT change

- All other tests [1]–[18], [20]–[25] unchanged. Still PASS.
- `canonical-task.examples.json` — the 3 valid examples already carried all three Rule 8 fields (worker-a included them speculatively in v0.1.1 since they were present-but-not-required). No edit needed; they validate clean under v0.1.2.
- `invalid-examples.json` — the 3 invalid examples still fail under v0.1.2 (none of them touched the Rule 8 fields).
- Smoke-test scenarios (`/agent-desk/snapshots/2026-05-18-smoke-test/scenarios/*.json`) — already carried Rule 8 fields. They validate clean under v0.1.2.
- voice-active, tenant-scaffolder, seam-a-poc snapshots — none reference the PENDING toggle. No edit needed (host's docker-cp is schema-dir only).

## Verification run (2026-05-18, fresh)

```
test_canonical_schema.py     25 assertions  PASS  (incl. inverted [19])
Draft-07 cross-check         5/5 checks     PASS
  [A] 3 valid examples pass JSON Schema
  [B] 3 invalid examples rejected
  [C] task missing Rule-8 fields now rejected by Draft-07 (3 errors fire)
  [D] enum lockstep maintained (STATES 8, SOURCES 6, RECIPIENT_ROLES 4)
  [E] 4 smoke-test scenarios pass v0.1.2 Draft-07
```

## Host docker-cp instruction

Per host's 2026-05-18 decision: incremental docker-cp on schema dir ONLY. Replace `/mnt/system/base/skills/task-system/schema/` contents with the files in this snapshot. The other 4 snapshots in the v0.1.1 bundle remain unchanged.
