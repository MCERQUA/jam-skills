# canonical-schema v0.1.4 — deployment-ready bundle

**Purpose:** the v0.1.4 ratchet of the canonical `task.json` schema. Host docker-cps the contents of this directory into `/mnt/system/base/skills/task-system/schema/` to deploy.

**Source-of-truth invariant:** the Python validator (`task_schema.py`) and JSON-Schema (`task-json-schema.json`) MUST agree. Cross-validation lives in `test_canonical_schema.py`; downstream readers import `task_schema.TASK_FIELDS / STATES / SOURCES / RECIPIENT_ROLES / FAILURE_MODES / NOTIFICATION_MODES` for lockstep.

---

## What's new in v0.1.4

Two additive, optional fields land on top of v0.1.3 (which locked the `failure_modes` 21-value enum). Both fields are absent-defaulted so v0.1.3 records validate clean under v0.1.4.

| Field | Owner | Shape | Default-when-absent |
|---|---|---|---|
| `notification_policy` | worker-a@mesh | `{mode: enum, on_finding_threshold: obj\|null}` — `mode` ∈ `inline` \| `roll_up_daily` \| `on_finding` (snake_case) | reader treats as `{"mode": "roll_up_daily"}` |
| `research_at` | worker-b@mesh | ISO-8601 UTC ending in `Z`, or `null` | scheduler computes `scheduled_at - 60min` (when `scheduled_at` is set) |

Defaults are applied **reader-side / scheduler-side**, NOT by the validator. The validator only checks the field's literal shape when present.

Full detail: `CHANGELOG-v0.1.4.md`.

---

## Quickstart

```bash
# Run all assertions
python3 test_canonical_schema.py
# → 37/37 PASS, "ALL CANONICAL SCHEMA ASSERTIONS PASSED"

# Validate a task.json against the schema
python3 task_schema.py /path/to/task.json

# Validate a whole tasks/<state>/ tree
python3 task_schema.py /path/to/workspace/tasks
```

---

## Files

| File | Purpose |
|---|---|
| `task-json-schema.json` | Draft-07 JSON Schema, source of truth for downstream JS/Draft-07 validators |
| `task_schema.py` | Hand-rolled Python validator + module exports (TASK_FIELDS, enums) |
| `canonical-task.examples.json` | 5 valid examples covering: 3 notification-policy modes + both schedule phases + 1 failure_modes entry (parked example) |
| `invalid-examples.json` | 7 invalid examples — must all be rejected. Covers Rule-1, legacy fields, missing state_history, bad notification_policy mode/shape, bad research_at format, non-enum failure_mode |
| `test_canonical_schema.py` | 37 named assertions. Run from this directory. Imports `scaffold_tenant` from sibling `2026-05-18-task-substrate/` |
| `CHANGELOG-v0.1.4.md` | What changed v0.1.3 → v0.1.4 |
| `DEPLOY-NOTES.md` | Host docker-cp instructions + downstream snapshots needing schema-ref bump |
| `DONE.txt` | Verification sentinel — josh-desktop@mesh polls for this |

---

## Deploy command (host VPS)

```bash
# Replace the deployed schema dir with this snapshot's contents.
docker cp /mnt/clients/<host>/agent-desk/snapshots/2026-05-19-canonical-schema-v0.1.4/. \
          <task-system-container>:/mnt/system/base/skills/task-system/schema/

# Verify in-container
docker exec <task-system-container> python3 /mnt/system/base/skills/task-system/schema/test_canonical_schema.py
```

Detailed deploy + downstream snapshot bumps: `DEPLOY-NOTES.md`.

---

## Lockstep contract

Every agent that reads/writes `task.json` MUST import from this module:

```python
from task_schema import (
    TASK_FIELDS,
    STATES,
    SOURCES,
    RECIPIENT_ROLES,
    FAILURE_MODES,        # 21-value enum locked 2026-05-18T21:05Z
    NOTIFICATION_MODES,   # 3-value enum locked at v0.1.4
)
```

Drift between any agent and this snapshot will surface as a `silent_drift` failure-mode entry per v0.2 spec amendment Rule 9. Schema bumps land here first; downstream tools follow lockstep.

---

## Open questions deferred to host nightly

9 open questions surfaced by milestone-4 workers, deliberately NOT pre-resolved at this ratchet (per host directive: "let broader mesh weigh in"). Documented at `/agent-desk/snapshots/2026-05-19-milestone-4-notification-cadence/OPEN-QUESTIONS.md`. Summary:
- worker-a Q1-3: inline firing scope, on_finding_threshold.metric enum-vs-free-form, recipient_role override
- worker-b Q1-3: overdue-research behavior, research_completed_at field, 60-min default location
- worker-c (none — TODO markers are mechanical)
