# voice-active predicate (lock-and-defer reader)

Sub-millisecond AND-gate "is voice channel active?" predicate that the task agent calls before working any lock-required task.

## Files

| File | Purpose |
|---|---|
| `voice_active.py` | Module — `VoiceActivePredicate` class + module-level convenience |
| `test_voice_active.py` | 14-assertion test suite; latency probe; mode introspection |
| `COMPLETION-NOTICE.md` | Ready-for-deploy signal |

## Architecture (per src-desktop's 2026-05-18 alignment reply)

**AND-gate:** BOTH signals must be present-and-fresh for the predicate to fire active. Either signal absent or stale → inactive.

| Signal | Path | Liveness check |
|---|---|---|
| Clerk session cookie | `/config/.openvoiceui/clerk-session.cookie` | File exists (Clerk-managed, OVU touch/remove on connect/disconnect) |
| OVU heartbeat | `/home/node/.openvoiceui/voice-active.flag` | mtime within 5s (writer cadence 2s, reader stale window 2.5×) |

**Why AND, not OR:** Cookie alone is stale-prone (no liveness). Heartbeat alone has no identity (any process can touch). AND gives identity AND liveness with no false-positive either way.

## Deployment-mode introspection

The reader is functional even when its writers aren't deployed yet — `is_active()` returns `False` if either signal can't be read. But "no writers deployed" returns the same `False` as "everyone is genuinely inactive" — which is dangerous for callers that need the lock contract.

`predicate_mode()` distinguishes:

| Mode | Meaning | Scheduler behavior |
|---|---|---|
| `full` | Both writer dirs exist; trust `is_active()` | Run normally |
| `degraded-cookie-only` | Heartbeat dir missing | Refuse new lock_required=True work; warn host once |
| `degraded-heartbeat-only` | Cookie dir missing (cookie writer is the v0.2 dep that's filed but not yet implemented) | Same |
| `no-writers-deployed` | Neither writer present | Refuse all lock_required=True tasks; warn host once |

**Recommended pattern in task scheduler bootstrap:**

```python
from voice_active import VoiceActivePredicate

pred = VoiceActivePredicate()
mode = pred.predicate_mode()
if mode != "full":
    warn_host(f"voice predicate degraded: {mode}")
    if mode == "no-writers-deployed":
        refuse_lock_required_tasks()
```

## Usage

```python
from voice_active import VoiceActivePredicate

pred = VoiceActivePredicate()   # uses default paths above

if pred.is_active():
    # voice session active — defer the task
    record["defer_count"] += 1
    return
else:
    # voice idle — run the task
    do_work()
```

Constructor args override default paths (for tests or v0.2 path changes):

```python
pred = VoiceActivePredicate(
    clerk_cookie_path="/custom/cookie/path",
    heartbeat_path="/custom/heartbeat/path",
    heartbeat_stale_seconds=3.0,
)
```

Module-level convenience for the spec-default case:

```python
import voice_active
if voice_active.is_active(): ...
mode = voice_active.predicate_mode()
```

CLI for quick checks:

```bash
python3 voice_active.py            # prints "active" or "inactive"
python3 voice_active.py --mode     # prints deployment mode
python3 voice_active.py --json     # full structured output
```

## Performance

Single `os.path.exists()` + `os.path.getmtime()` call per `is_active()` — sub-millisecond. Test [12] measures 0.092ms per call on this container.

## Dependencies on other snapshots

This module integrates with:
- **task-system canonical schema** (`task.json` carries `lock_required` + `defer_count`)
- **task scheduler** (calls `is_active()` before promoting a task to `today/`)
- **OVU heartbeat writer** — bun-desktop + claude-direct, host-filed
- **Clerk cookie writer** — flagged in mesh thread as v0.2 dep, not yet filed

## Rollback

Delete the file. Callers that import `voice_active` will fail loudly — that's intentional (better than silently falling back to "always inactive" which would interleave task work with voice).
