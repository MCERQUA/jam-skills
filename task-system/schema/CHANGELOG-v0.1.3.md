# canonical-schema v0.1.3 — Changelog vs v0.1.2

**Trigger:** src-desktop@mesh locked the v0.2 `failure_modes` enum at 2026-05-18T21:05Z with 21 values, 4 peer contributors aligned. Host integrated his side at `/mnt/system/base/skills/task-system/v0.2-failure-modes/`. This snapshot absorbs the enum into the canonical task.json schema.

## What changed

### `task_schema.py`

- Module docstring: v0.1.2 → v0.1.3 — added "failure_modes enum locked"
- New module constant: `FAILURE_MODES` — tuple of 21 alphabetized values
- `TASK_FIELDS['failure_modes']` type-check: `list_of_str` → `list_of_failure_modes`
- New `_check_type` branch for `list_of_failure_modes` that:
  - Rejects non-list values
  - Rejects non-string items (`failure_modes[0] must be string`)
  - Rejects unknown enum values (`failure_modes[0] 'foo' not in v0.2 enum (21 values)`)
  - Allows empty list (backward-compatible with v0.1.2 default)

### `task-json-schema.json`

- `$id`: `v0.1.2.json` → `v0.1.3.json`
- `title`: "v0.1.3 — failure_modes enum locked"
- `description`: rewritten to reference v0.2 enum lock event
- `properties.failure_modes.items`: `{"type": "string"}` → `{"type": "string", "enum": [...21 values...]}`
- `properties.failure_modes.description`: explains the lock source + that empty list remains legal

### `test_canonical_schema.py`

- Test [17] (`failure_modes must be list[str]`) — **expanded to 4 sub-cases**:
  - 17a — non-string element in list rejected (same as v0.1.2)
  - 17b — arbitrary string NOT in v0.2 enum rejected (NEW)
  - 17c — empty list still legal (regression guard)
  - 17d — multi-value pulling from enum accepted (e.g. `["orphan_after_crash", "interleave_corruption", "silent_drift"]`)

### `canonical-task.examples.json`

- One scheduled-state example previously had `failure_modes: ["operator-unreachable"]` (free-form text — legal under v0.1.2). Replaced with `["latency_budget_exceeded"]` which is in the v0.2 enum and semantically close (operator-unreachable = response-latency exceeded).

## What did NOT change

- All other tests [1]–[16], [18]–[25] unchanged. Still PASS.
- `invalid-examples.json` — none of the 3 examples touched failure_modes; still fail v0.1.3 for the same reasons they failed v0.1.2.
- Downstream snapshots (intake-dedupe, intake-internal, intake-external, smoke-test, voice-active, tenant-scaffolder, seam-a-poc) — all populate `failure_modes: []` by default which remains legal. No edits required.
- Spec invariants (Rule 1 cross-field, state/location mismatch, Rule 8 required fields, parked-requires-clock) — unchanged.

## Verification (2026-05-19, fresh)

```
test_canonical_schema.py     25 assertions  PASS  (incl. expanded [17] with 4 enum sub-cases)
Draft-07 cross-check          6/6 PASS:
  [A] 3 valid examples pass Draft-07
  [B] 3 invalid examples rejected
  [C] Draft-07 rejects non-enum failure_modes  ('definitely_not_in_enum' is not one of [...])
  [D] FAILURE_MODES lockstep (Python 21 ↔ JSON Schema 21)
  [E] intake-adapter (worker-b) output round-trips clean against v0.1.3
  [F] 4 smoke-test scenarios pass v0.1.3 Draft-07 + Python
```

## Host docker-cp instruction

Incremental docker-cp on schema dir ONLY. Replace `/mnt/system/base/skills/task-system/schema/` contents with files in this snapshot. The 7 other deployed snapshots in the bundle remain unchanged (their `failure_modes: []` continues to validate clean).
