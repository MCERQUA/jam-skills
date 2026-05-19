---
author: src-desktop@mesh
status: LOCKED v0.3
locked_at: 2026-05-19T00:55:00Z
spec_ref: v0.2 failure_modes enum → `parallel_shift_writer_race`
filed_under: v0.3 (per v0.2 state-transition-matrix README "out of scope for v0.2")
defends: parallel_shift_writer_race (two same-URI agent shifts mutating one task dir)
---

# task_dir_lock — parallel_shift_writer_race defense (v0.3)

POSIX file-lock primitive that serializes concurrent writers on a single task directory. Combined with the v0.2 transition_validator, it closes the failure mode the v0.2 enum names: two shifts of the same agent URI both trying to advance the same task at the same time, with last-writer-wins on the dir move and duplicate state_history entries.

## Why a flock and not a sentinel-with-CAS

| Candidate | Why rejected |
|---|---|
| Sentinel-file CAS | The write of the sentinel is itself racy unless protected; need a primitive to protect the primitive. |
| Atomic rename | Doesn't help when both writers race the rename — last one wins. |
| Append-only journal with token claim | Requires a separate ledger to serialize the token writes. Cost > benefit. |
| Mesh-wide semaphore | Crosses agent boundaries unnecessarily — race is within one URI's parallel shifts, not cross-URI. |
| **POSIX flock (chosen)** | Kernel-level, well-understood semantics, cross-language (bash CLI, python module), zero stale-lock cleanup (kernel auto-releases on fd close), works for same-host parallel processes which is the actual contention domain. |

## Files

| File | Purpose | Verification |
|---|---|---|
| `task_dir_lock.py` | Defense primitive: `task_dir_lock()` context manager + `transition_under_lock()` integration helper | self-contained |
| `test_task_dir_lock.py` | Defense-only tests | **8/8 PASS** |
| `transition_validator.py` | v0.2 validator (copied for self-contained integration test) | (v0.2 deliverable) |
| `transition-matrix.json` | v0.2 matrix (copied for self-contained integration test) | (v0.2 deliverable) |
| `test_integration_validator_plus_lock.py` | End-to-end demonstration: parallel_shift_writer_race scenario closed | **PASS — 1 winner, 1 contended, 1 history row** |

## Verification

```
$ cd 2026-05-19-task-dir-lock/
$ python3 test_task_dir_lock.py
  [1] happy_path_acquire_release            PASS
  [2] non_blocking_contention_raises        PASS
  [3] blocking_acquires_after_release       PASS
  [4] blocking_times_out                    PASS
  [5] kernel_releases_lock_on_crashed_holder PASS
  [6] bash_flock_cli_parity                 PASS
  [7] concurrent_transitions_serialize      PASS
  [8] lock_filename_contract                PASS
task_dir_lock: 8/8 assertions PASS

$ python3 test_integration_validator_plus_lock.py
  integration: 1 winner, 1 contended (clean rejection, no race)
  integration: state_history has exactly 1 row: state=planned by=task-agent
  integration: dir moved cleanly to planned/
test_integration_validator_plus_lock: ALL ASSERTIONS PASS
```

## API

### `task_dir_lock(task_dir, *, blocking=False, timeout_s=5.0, writer_label=None)`

Context manager. Acquires an exclusive lock on `<task_dir>/.writer.lock`. The lock filename is reserved — transition_validator MUST NOT count it among `required_artifacts`.

- `blocking=False` (default): one-shot acquire. On contention, raises `LockContended` immediately. This is the right mode for the task-agent execution loop — contention means another shift is already advancing this task, so the second writer should defer rather than wait.
- `blocking=True`: poll every `poll_s` (default 0.05s) for up to `timeout_s` (default 5s). On timeout, raises `LockTimeout`. Use for one-shot manual operations where waiting is acceptable.

### `transition_under_lock(task_dir, *, from_state, to_state, writer_role, validator, state_history_append, move_dir, present_artifacts=None, precondition_values=None, writer_label=None)`

Integration helper that composes lock + v0.2 validator + state_history append + dir move. Hold order:
1. Acquire `task_dir_lock` (non-blocking — contention raises `LockContended`).
2. Validate transition against v0.2 matrix (illegal raises `PermissionError`).
3. Append `state_history` row (ISO-Z timestamp stamped here).
4. Move dir to new state path.

If step 4 raises, state_history is one step ahead — caller MUST treat as a hard error and recover. This is intentional: the writer commits to the transition before the move, so a failed move is a system bug, not a user error.

## Production caveats

1. **Loser-sees-dir-gone is a separate, benign failure shape.** If shift A is fast enough to acquire-validate-append-move before shift B even calls `open()` on the lockfile, shift B raises `FileNotFoundError` instead of `LockContended`. Both are correct dispositions ("the world moved on"); callers SHOULD handle both as "retry from current state if still relevant." The integration test exercises the `LockContended` path specifically; the `FileNotFoundError` path is covered by the same caller-side retry logic.

2. **Same-host only.** flock is kernel-local. Cross-container races (e.g. host@mesh and src-desktop@mesh both touching `/mnt/shared/tasks/<id>/`) are NOT defended — would need NFS-aware locking (e.g. fcntl on the shared mount) or a mesh-level semaphore. Out of scope for v0.3; the parallel_shift_writer_race scenario as defined was within-URI parallel shifts, all same-host.

3. **No lock TTL.** A wedged holder (mid-execution, never returns) holds the lock forever from the perspective of subsequent shifts. Mitigation: blocking-mode callers SHOULD use a short timeout (e.g. 30s) and surface LockTimeout to operator. Hard TTL inside the primitive would let lifecycle bugs masquerade as lock contention — explicit timeout at call sites is more honest.

## Anti-failure-mode mapping (v0.2 enum coverage)

This primitive primarily defends `parallel_shift_writer_race`. It also incidentally helps:
- `interleave_corruption` — single-writer guarantee on dir contents during the lock window.
- `silent_drift` — `LockContended` is a loud signal; the alternative (silent overwrite) was the failure being defended.

It does NOT defend:
- `cross_session_artifact_handoff_blindness` — that's a discovery problem, not a serialization problem. A separate "scan workspace on session start" mechanism is needed.
- `orphan_after_crash` / `in_flight_orphan` — those are about state outliving the writer, not concurrent writers. flock auto-release on fd close helps a little (no stale lock) but doesn't repair the orphaned state itself.

## Integration recipe for worker-a substrate

```python
from task_dir_lock import LockContended, transition_under_lock
from transition_validator import TransitionValidator

validator = TransitionValidator("/path/to/transition-matrix.json")

def advance(task_dir, from_state, to_state, writer_role):
    try:
        transition_under_lock(
            task_dir,
            from_state=from_state, to_state=to_state,
            writer_role=writer_role,
            validator=validator,
            state_history_append=my_history_writer,
            move_dir=my_dir_mover,
            present_artifacts={p.name for p in Path(task_dir).iterdir() if p.name != ".writer.lock"},
        )
    except LockContended:
        # another shift is already advancing this task; back off
        defer_until_next_poll()
    except PermissionError as e:
        # validator rejected the transition; log and surface
        log_validator_rejection(e)
    except FileNotFoundError:
        # the world moved on between our task scan and lock attempt
        rescan_workspace()
```

## v0.4 follow-ups (out of scope here)

- Cross-host lock (NFS / shared-mount races between containers).
- Lock observability — expose current holder via `cat .writer.lock` (already works for diagnostics, but no UI surface).
- Lock metrics — count contention events per task per day, feed `patterns.json` so high-contention tasks surface for splitting.
