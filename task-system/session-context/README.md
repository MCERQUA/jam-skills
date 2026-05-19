# session-context — Rule 8 SessionContext wrapper

Higher-level, read-only view over the Rule 8 bootstrap bundle. Sits on top of
worker-a's `task_bootstrap.load_context()` raw loader and exposes friendly
helpers the **single tenant agent** (per Rule 8) calls during its task-execution
session.

- Worker-b snapshot: this directory.
- Worker-a snapshot (raw loader): `/agent-desk/snapshots/2026-05-19-rule-8-bootstrap/`
- Spec: `/mesh/BLACKBOARD/task-system/v0.1.1-spec-amendment.md` §Rule 8.

## Class contract

`SessionContext(tenant, workspace, *, today=None)` — calls
`task_bootstrap.load_context()` exactly once at init and freezes itself.
After init, the wrapper is read-only: attribute assignment, attribute
deletion, and any addition of new attributes all raise `AttributeError`. To
refresh state (a new ledger entry has landed, a parked task was promoted,
etc.), discard the instance and call `start_task_session(...)` again.

| Surface | Returns | Description |
|---|---|---|
| `loaded_at` *(property)* | `str` | ISO-8601 UTC `Z` timestamp of the bootstrap call. |
| `tenant` *(property)* | `str` | Tenant the bundle was loaded for. |
| `all_open_tasks` *(property)* | `list[dict]` | Flat list of every open task, ordered `intake → shop-floor → planned → scheduled → today → in-flight → parked`. `done/` is excluded — Rule 8 bootstrap loads open context only. |
| `open_tasks_in_state(state)` | `list[dict]` | Just that state's tasks. Unknown states (or `"done"`) return `[]`. |
| `find_task_by_id(task_id)` | `dict \| None` | First open task with that id, or `None`. |
| `find_tasks_by_source_ref(source_ref)` | `list[dict]` | All open tasks where `source_ref == source_ref`. Multiple matches across states are expected during the intake → shop-floor dedupe window — return them all. `None` query → `[]`. |
| `thread_history_for(gmail_thread_id)` | `list[dict]` | Loaded Gmail thread messages, or `[]` if not in the bundle. |
| `sms_history_for(operator_phone)` | `list[dict]` | Loaded SMS conversation for that phone, or `[]`. |
| `has_open_blocker_on(summary_text)` | `bool` | `True` iff a `parked/` task has an **exact** matching `summary` string. |
| `recent_blockers()` | `list[dict]` | All `parked/` tasks (the open-blocker set). |
| `to_dict()` | `dict` | Full underlying bootstrap context. JSON-serializable; for logging / mesh transmission. |

Module-level convenience constructor:

```python
def start_task_session(tenant, workspace, *, today=None) -> SessionContext
```

## Integration with intake adapters (Rule 8 dedupe pre-check)

Intake adapters write `task.json` to `tasks/intake/` per Rule 7. Before any
adapter calls the full dedupe pass on `intake/ → shop-floor/`, it can use the
SessionContext to short-circuit obvious `source_ref` collisions:

```python
from session_context import start_task_session

sess = start_task_session(tenant="cca", workspace="/mnt/clients/josh/openclaw/workspace")

# Channel adapter has computed a candidate task and its source_ref.
existing = sess.find_tasks_by_source_ref(candidate["source_ref"])
if existing:
    # Rule 8: reject as duplicate, link via `linked_to`. Skip the
    # heavier semantic-shingle dedupe; the source_ref collision is decisive.
    reject_as_duplicate(candidate, linked_to=[e["id"] for e in existing])
    return
```

The wrapper never *writes* — adapters use it to **read** the open-state
inventory and choose what to do, then perform any write via the canonical
dedupe / state-transition path.

## Example: tenant agent startup flow

```python
# At task-session start. Per Rule 8 this is ONE call from THE tenant agent
# regardless of which channel (email / SMS / voice / mesh / manual) opened
# the session.
from session_context import start_task_session

sess = start_task_session(
    tenant="cca",
    workspace="/mnt/clients/josh/openclaw/workspace",
)

# Headline triage — what's parked behind a blocker?
for blocker in sess.recent_blockers():
    log(f"PARKED: {blocker['id']} — {blocker['summary']}")

# What's on the plate for today?
for t in sess.open_tasks_in_state("today"):
    log(f"TODAY: {t['id']} — {t['summary']}")

# When a Gmail webhook fires mid-session, the adapter that woke us up
# can verify the thread isn't already represented:
new_thread_id = webhook["thread_id"]
already_open = sess.find_tasks_by_source_ref(new_thread_id)
prior_messages = sess.thread_history_for(new_thread_id)

# When the agent finishes its first decision and needs fresh state
# (a new parked-task may have appeared, or another adapter wrote intake),
# DISCARD this SessionContext and start a new session — the wrapper is
# read-only by design.
sess = start_task_session(tenant="cca", workspace="...")
```

## Why read-only?

Rule 8 says **one** tenant agent owns task execution across all channels. The
bootstrap bundle is a **snapshot at session start**. Letting the agent mutate
the snapshot in-place would:

1. Drift the in-memory view away from disk state without the canonical
   state-transition machinery (`state_history` append, file move, ledger
   write) running.
2. Mask the cost of a refresh — the agent should *know* it's re-bootstrapping.

Re-init makes the cost visible and keeps the file system as source of truth.

## Constraints honored

- **Pure stdlib** — no third-party imports.
- **`task_bootstrap` imported via `sys.path`** — `session_context.py` injects
  worker-a's snapshot dir at import time. No copy, no install.
- **Output scope** — every file in this run lives in
  `/agent-desk/snapshots/2026-05-19-session-context/`.

## Files

- `session_context.py` — module (class + constructor).
- `test_session_context.py` — 10 assertions, exits 0 on pass.
- `README.md` — this file.
- `COMPLETION-NOTICE.md` — single-line landed-marker (written last).

## Running tests

```
python3 test_session_context.py
```

Exits `0` on full pass.
