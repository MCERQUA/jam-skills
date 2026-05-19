# Rule 8 Bootstrap Loader

`task_bootstrap.load_context(tenant, workspace)` — read the per-tenant
context bundle the tenant agent MUST hold in memory before working any
task. Defined by the v0.1.1 spec amendment §Rule 8 bootstrap contract.

This module is the BOTTOM of the task-system stack. Other layers (dedupe,
state-machine, intake-adapters) import it; it imports nothing of theirs.
Reads are filesystem-only — no mesh I/O — and restricted to paths inside
the resolved workspace.

## Call signature

```python
from datetime import date
from task_bootstrap import load_context

ctx = load_context(
    tenant="cca",
    workspace="/mnt/clients/josh/openclaw/workspace",
    # optional; defaults to today UTC. Override for tests / replay:
    # today=date(2026, 5, 19),
)
```

Raises `ValueError` if `tenant` is empty, `FileNotFoundError` if
`workspace` is not a directory, and `TypeError` if `today` is not a
`datetime.date`.

## Return shape

JSON-serializable plain dict (`type(ctx) is dict`, every value is
str/int/None/list/dict of the same):

| Key | Type | Source |
|---|---|---|
| `tenant` | str | argument |
| `workspace` | str | resolved absolute path |
| `loaded_at` | ISO-8601 UTC `Z` | wall-clock at load |
| `today` | `YYYY-MM-DD` str | UTC today or `today=` override |
| `open_tasks` | dict[state → list[task_record]] | `tasks/<state>/*/task.json` filtered by tenant |
| `open_task_count` | int | sum over `open_tasks` values |
| `ledger_recent` | list[dict] | `ledger/<YYYY-MM-DD>.json` files within last 7 days |
| `gmail_threads` | dict[source_ref → list[message]] | `gmail/threads/<source_ref>.json` for open-task email refs only |
| `sms_threads` | dict[phone → list[message]] | `sms/conversations/<phone>.json` for open-task operator_phones |
| `voice_transcript` | str \| None | `memory/<today>-conversation.md` content |
| `reflections_recent` | list[dict] | `reflections/<YYYY-MM-DD>*.md` within last 7 days |

States in `open_tasks`: `intake`, `shop-floor`, `planned`, `scheduled`,
`today`, `in-flight`, `parked`. **`done/` is intentionally excluded** —
completed tasks are audit history, not open context.

`gmail_threads` and `sms_threads` accept either a JSON list of messages
OR a `{"messages": [...]}` envelope on disk; both surface as a plain
list. Threads with neither shape are silently skipped.

## Sub-loaders degrade gracefully

Missing optional subdirectories yield empty values, never crash:
- no `ledger/` → `ledger_recent: []`
- no `gmail/threads/` → `gmail_threads: {}`
- no `sms/conversations/` → `sms_threads: {}`
- no `memory/<today>-conversation.md` → `voice_transcript: null`
- no `reflections/` → `reflections_recent: []`
- malformed `task.json` → skipped, other tasks still load

## Path discipline

`workspace` is `Path.resolve()`-ed up front; every file the loader opens
is checked with `is_relative_to(workspace)`. Anything escaping (symlinks,
`..` in a crafted `source_ref` or `operator_phone`) is silently dropped.
The loader will not read outside the workspace it was given.

## Workspace conventions

Created by `scaffold_tenant.py` + by the tenant agent over time:

```
<workspace>/
  tasks/<state>/<task-id>/task.json   # scaffold_tenant.py creates the state dirs
  ledger/<YYYY-MM-DD>.json            # list[dict] of ledger entries per day
  gmail/threads/<source_ref>.json     # list[message] OR {"messages": [...]}
  sms/conversations/<phone>.json      # list[message] OR {"messages": [...]}
  memory/<YYYY-MM-DD>-conversation.md # per-day voice transcript markdown
  reflections/<YYYY-MM-DD>*.md        # nightly reflection summaries
```

## Integration

- **Dedupe (worker-a v0.1.2):** `scan_for_duplicates(workspace, candidate)`
  walks the same `tasks/<open-state>/` directories. Bootstrap loads the
  full record set into memory; dedupe is a separate scan for matches.
  Both run in sequence at intake-promotion time.

- **State machine (seam B):** the tenant agent calls `load_context()` at
  task-start, then the state machine validates each transition against
  the in-memory snapshot. Bootstrap publishes context; the state machine
  consumes it.

- **Intake adapters (Rule 7):** adapters write `task.json` to `intake/`
  with `raised_by` + `source_ref`. The very next step — promotion to
  `shop-floor/` — requires a fresh `load_context()` so the agent sees
  the just-written record.

- **Mesh transmission:** the return dict is JSON-serializable, so it can
  be `mesh-send`-able for audit / replay / cross-agent debugging.

## Spec refs

- `/mesh/BLACKBOARD/task-system/v0.1.1-spec-amendment.md` §Rule 8 bootstrap
- `/agent-desk/snapshots/2026-05-19-canonical-schema-v0.1.3/task_schema.py`
- `/agent-desk/snapshots/2026-05-18-tenant-scaffolder/scaffold_tenant.py`
