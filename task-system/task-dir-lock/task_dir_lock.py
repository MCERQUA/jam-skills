"""
task_dir_lock — per-task-dir exclusive lock that defends against
the `parallel_shift_writer_race` failure mode (v0.2 enum entry).

Two same-URI agent shifts may both try to advance the same task at the same
time. Without coordination, the dir move is last-writer-wins and state_history
may grow two entries for the same transition with conflicting metadata.

The defense is a POSIX file lock (`fcntl.flock`) on a sentinel file inside the
task dir. Hold the lock for: validator check → dir move → state_history append.
Release on context exit. The lock is held by the kernel against the *open file
descriptor*, so a crashed holder releases the lock automatically when the kernel
closes the fd — no manual stale-lock cleanup needed.

Author: src-desktop@mesh
Spec ref: v0.2 failure_modes enum → `parallel_shift_writer_race`
Filed-as: v0.3 defense (per state-transition-matrix README "out of scope for v0.2")
"""
from __future__ import annotations

import fcntl
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


LOCK_FILENAME = ".writer.lock"


class LockContended(RuntimeError):
    """Raised when a non-blocking acquire finds the lock held by another writer."""


class LockTimeout(RuntimeError):
    """Raised when a blocking acquire exceeds its timeout budget."""


@contextmanager
def task_dir_lock(
    task_dir: str | Path,
    *,
    blocking: bool = False,
    timeout_s: float = 5.0,
    poll_s: float = 0.05,
    writer_label: str | None = None,
) -> Iterator[Path]:
    """Acquire an exclusive lock on a task directory for the duration of the with-block.

    Yields the path to the sentinel lock file (useful for logging / debugging).

    Modes:
      blocking=False (default): try once. If contended, raise LockContended immediately.
                                This is the right mode for the task-agent execution loop —
                                contention means another shift is already advancing this
                                task, so the second writer should defer rather than wait.
      blocking=True: poll every `poll_s` for up to `timeout_s`. Raise LockTimeout if
                     the budget elapses without acquisition. Use this for one-shot
                     manual operations where waiting is acceptable.

    The lock file persists in the dir after release — that is intentional. The
    file's identity is what flock locks on; deleting it would race with the next
    acquirer. The .writer.lock filename is reserved; transition_validator should
    NOT count it among `required_artifacts`.

    writer_label is recorded in the lock file body for diagnostics (which shift
    holds the lock) but is NOT load-bearing for correctness — flock semantics are
    what enforce mutual exclusion.
    """
    task_dir = Path(task_dir)
    lockfile = task_dir / LOCK_FILENAME

    # Open (create if absent) the sentinel. Opening does NOT take the lock.
    fh = open(lockfile, "a+")
    try:
        if blocking:
            deadline = time.monotonic() + timeout_s
            while True:
                try:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise LockTimeout(
                            f"task_dir_lock: could not acquire {lockfile} within {timeout_s}s"
                        )
                    time.sleep(poll_s)
        else:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as e:
                raise LockContended(
                    f"task_dir_lock: {lockfile} is held by another writer"
                ) from e

        # We hold the lock. Stamp the body for diagnostics.
        fh.seek(0)
        fh.truncate()
        fh.write(f"pid={os.getpid()} label={writer_label or '-'} acquired_at={time.time():.3f}\n")
        fh.flush()

        try:
            yield lockfile
        finally:
            # Release the lock explicitly before closing the fd (defensive — kernel
            # would do it on close too).
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    finally:
        fh.close()


# ---------- integration helper ----------

def transition_under_lock(
    task_dir: str | Path,
    *,
    from_state: str,
    to_state: str,
    writer_role: str,
    validator,
    state_history_append,
    move_dir,
    present_artifacts: set[str] | None = None,
    precondition_values: dict | None = None,
    writer_label: str | None = None,
):
    """Advance a task through one state transition under the writer lock.

    Composes:
      1. acquire lock (non-blocking — contention means defer)
      2. validate transition with the v0.2 TransitionValidator
      3. append a state_history row
      4. move the task dir

    The validator's `present_artifacts` should NOT include the lock sentinel
    (`.writer.lock`). Filter it before passing in if you're using os.listdir.

    validator: instance of transition_validator.TransitionValidator
    state_history_append: callable(state, by, at_iso) → None
    move_dir: callable(from_path, to_path) → None
    """
    arts = set(present_artifacts or [])
    arts.discard(LOCK_FILENAME)

    with task_dir_lock(task_dir, blocking=False, writer_label=writer_label):
        result = validator.validate(
            from_state=from_state, to_state=to_state,
            writer_role=writer_role,
            present_artifacts=arts,
            precondition_values=precondition_values,
        )
        if not result.ok:
            from transition_validator import ValidationResult  # avoid hard import order
            raise PermissionError(f"transition rejected: {result.reasons}")

        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        state_history_append(to_state, writer_role, now_iso)

        # dir move is the last step inside the lock. If this raises, state_history
        # is one step ahead — caller should treat that as a hard error and recover.
        move_dir(task_dir, to_state)


if __name__ == "__main__":
    # quick smoke (real tests in test_task_dir_lock.py)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        with task_dir_lock(td) as lockfile:
            print(f"acquired {lockfile}")
        print("released")
