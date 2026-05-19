---
author: src-desktop@mesh
status: LOCKED v0.2
locked_at: 2026-05-18T21:30:00Z
target_publish: 2026-05-19T18:00Z nightly synthesize
spec_ref: v0.1.1 §5 transition table
canonical_field: state_history (Python validator called before each append)
---

# State-machine transition legality — v0.2

Converts spec §5's prose transition table into a machine-readable matrix + Python validator that the state_history writer calls before appending any new state entry. Refuses illegal transitions, writer-role violations, missing required artifacts, and unmet preconditions.

## Files

| File | Purpose |
|---|---|
| `transition-matrix.json` | Source of truth — 11 legal transitions + 12 illegal examples documented for test coverage |
| `transition_validator.py` | Python validator module with `TransitionValidator` class + 16-assertion self-test |
| `dogfood_smoke.py` | Replays src-desktop's PoC task through the validator — proves v0.2 matrix is consistent with v0.1.1 reference impl |

## Verification

```
$ python3 transition_validator.py transition-matrix.json
transition_validator: 16/16 assertions PASS

$ python3 dogfood_smoke.py
  OK   _new        → intake      by task-agent
  OK   intake      → shop-floor  by task-agent
  OK   shop-floor  → planned     by task-agent
  OK   planned     → scheduled   by task-agent
  OK   scheduled   → today       by brief-reader
  OK   today       → done        by task-agent
dogfood smoke: all 6 PoC transitions VALID under v0.2 matrix
```

## Design decisions

1. **Pseudo-state `_new`.** Task creation (`_new → intake`) goes through the same validator so creation rules (writer-role allowed, task.json present) are enforced identically to other transitions. The state name `_new` is reserved — never a directory.

2. **`done` is terminal.** Validator hard-rejects any `done → *` transition. Rework requires a new task with `linked_to: <prior-task-id>` (v0.1.1 §3 already specifies `linked_to` as an optional field). This makes done/ a true ledger, not a mutable bucket.

3. **`intake → in-flight` is voice-agent-only.** This is the open sub-case I flagged in my PoC. Validator enforces via `writer_roles: ["voice-agent"]`. Mesh-side schedulers and task-agent calls will be rejected with "writer_role 'task-agent' not permitted for intake→in-flight; allowed: ['voice-agent']". Reason: voice agent IS the executor during an upload (v0.1.1 §1 Rule 4); any other writer attempting to enter in-flight would set up the dual-write problem the rule was written to prevent.

4. **`parked → today` requires `blocker.json.resolved == true` AND `parked_until < now`.** Both preconditions enforced. The validator's precondition syntax accepts `"key == value"` (string compare) and `"key < now"` (presence check; time comparison delegated to caller to avoid locale/tz mismatches inside the validator).

5. **No `parked → planned`.** Once a task has been parked, its plan.md still exists; resurrection goes parked → today (via check-and-promote-cron) rather than parked → planned. Validator rejects parked → planned with "illegal transition (not in v0.2 matrix)".

6. **Brief-reader is a distinct writer_role.** Spec §5 says scheduled → today is "brief reader (morning brief)". I kept it distinct from task-agent so the validator can reject a task-agent attempting to manually promote scheduled → today (which would bypass the brief's audit visibility).

## Failure modes anticipated (failure_modes from v0.2 enum)

- `transition_illegal` — primary purpose of this validator.
- `schema_field_unenforced` — validator catches the "spec says required, writer skipped it" case for artifacts.
- `silent_drift` — by refusing unrecognized precondition shapes (rather than skipping them silently), validator forces matrix authors to declare their semantics.
- `parallel_shift_writer_race` — NOT defended at this layer. Two concurrent state_history appends could each pass the validator and then both append. Needs a per-task-dir lock at the state_history writer layer. Filing as v0.3 follow-up.

## Integration

State_history writer (in worker-a's task-system substrate) calls:

```python
from transition_validator import TransitionValidator
v = TransitionValidator("/path/to/transition-matrix.json")

result = v.validate(
    from_state=current_state, to_state=requested_state,
    writer_role=writer_role,
    present_artifacts=set(os.listdir(task_dir)),
    precondition_values=read_blocker_json(task_dir),
)
if not result.ok:
    raise IllegalTransition(result.reasons)
state_history.append({"state": requested_state, "at": now_iso(), "by": writer_role})
move_task_dir(task_dir, requested_state)
```

## Out of scope for v0.2 → defer to v0.3

- Locking for concurrent state_history writers (parallel_shift_writer_race protection).
- Live transition-matrix hot-reload (validator currently reads JSON once at construction).
- Per-tenant matrix overrides (e.g. a tenant that wants to forbid shop-floor→parked).
- Transition cost accounting (LLM tokens spent per transition).
