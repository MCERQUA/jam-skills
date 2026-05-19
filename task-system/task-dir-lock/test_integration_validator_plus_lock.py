"""
Integration test: parallel_shift_writer_race scenario, end-to-end.

Composes v0.2 transition_validator + v0.3 task_dir_lock to advance a real
task dir from shop-floor → planned. Spawns two threads racing the same
transition. Asserts:
  - exactly one of them succeeds
  - the other is rejected with LockContended (not validator-rejected, not silent)
  - state_history has exactly one row added
  - the task dir is in the expected new state

This is the canonical demonstration that the v0.3 defense closes the failure
mode v0.2 named.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import threading
from pathlib import Path

import time
from datetime import datetime, timezone
from task_dir_lock import LockContended, task_dir_lock
from transition_validator import TransitionValidator


def setup_task_dir(parent: Path) -> Path:
    """Create a task dir in shop-floor/<task-id>/ with task.json + plan.md ready
    for shop-floor → planned promotion."""
    task_dir = parent / "shop-floor" / "2026-05-19-1200-race-demo"
    task_dir.mkdir(parents=True)
    (task_dir / "task.json").write_text(json.dumps({"id": "race-demo", "state": "shop-floor"}))
    (task_dir / "plan.md").write_text("# plan\n")
    (task_dir / "state_history.jsonl").write_text("")
    return task_dir


def make_state_history_appender(history_path: Path):
    lock = threading.Lock()
    def append(state: str, by: str, at_iso: str):
        with lock, history_path.open("a") as f:
            f.write(json.dumps({"state": state, "by": by, "at": at_iso}) + "\n")
    return append


def make_move_dir(parent: Path):
    def move(task_dir: Path, to_state: str):
        new_path = parent / to_state / task_dir.name
        new_path.parent.mkdir(exist_ok=True)
        shutil.move(str(task_dir), str(new_path))
    return move


def main():
    matrix_path = Path(__file__).parent / "transition-matrix.json"
    validator = TransitionValidator(matrix_path)

    with tempfile.TemporaryDirectory() as td:
        parent = Path(td)
        task_dir = setup_task_dir(parent)
        history_path = task_dir / "state_history.jsonl"
        appender = make_state_history_appender(history_path)
        mover = make_move_dir(parent)

        results: list[tuple[str, str]] = []  # (label, outcome)
        results_lock = threading.Lock()

        # Snapshot the artifact list once at the start, BEFORE any shift moves the dir.
        # This mirrors the real race: both shifts captured the dir state at the same
        # moment, then race the lock. Without this, the sequentially-started loser
        # would FileNotFoundError on iterdir after the winner already moved the dir
        # — a different (and benign) failure mode, not the parallel_shift_writer_race
        # this test is meant to demonstrate.
        artifacts_at_start = {p.name for p in task_dir.iterdir()}

        # Barrier ensures both threads reach the transition_under_lock call together
        # so they actually race the lock instead of running sequentially.
        barrier = threading.Barrier(2)

        # Inline transition_under_lock with a HOLD inside the lock so both
        # threads' open() + flock() interleave correctly. In production the
        # validate-append-move work itself provides enough hold time; the test
        # just needs to be explicit about timing.
        def shift(label: str):
            barrier.wait()
            try:
                with task_dir_lock(task_dir, blocking=False, writer_label=label):
                    # Loser is currently parked in fh = open(...) or flock() of
                    # task_dir_lock — give it time to hit the flock contention.
                    time.sleep(0.05)
                    result = validator.validate(
                        from_state="shop-floor", to_state="planned",
                        writer_role="task-agent",
                        present_artifacts=artifacts_at_start,
                    )
                    if not result.ok:
                        raise PermissionError(result.reasons)
                    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
                    appender("planned", "task-agent", now_iso)
                    mover(task_dir, "planned")
                with results_lock:
                    results.append((label, "won"))
            except LockContended:
                with results_lock:
                    results.append((label, "contended"))
            except PermissionError as e:
                with results_lock:
                    results.append((label, f"validator-rejected: {e}"))

        threads = [threading.Thread(target=shift, args=(f"shift-{i}",)) for i in range(2)]
        for t in threads: t.start()
        for t in threads: t.join()

        # IMPORTANT: history_path moved with the dir if the winning shift relocated it.
        # Find the new history path.
        moved_task_dir = parent / "planned" / task_dir.name
        if moved_task_dir.exists():
            history_path = moved_task_dir / "state_history.jsonl"

        wins = [r for r in results if r[1] == "won"]
        contended = [r for r in results if r[1] == "contended"]

        assert len(wins) == 1, f"expected 1 win, got {wins}"
        assert len(contended) == 1, f"expected 1 contended, got {contended}"
        assert moved_task_dir.exists(), f"task dir should be in planned/, got {list(parent.iterdir())}"
        assert not (parent / "shop-floor" / task_dir.name).exists(), "old path should be gone"

        history_lines = history_path.read_text().strip().split("\n")
        assert len(history_lines) == 1, f"expected 1 state_history row, got {history_lines}"
        row = json.loads(history_lines[0])
        assert row["state"] == "planned"
        assert row["by"] == "task-agent"

        print("  integration: 1 winner, 1 contended (clean rejection, no race)")
        print(f"  integration: state_history has exactly 1 row: state={row['state']} by={row['by']}")
        print(f"  integration: dir moved cleanly to planned/")
        print("test_integration_validator_plus_lock: ALL ASSERTIONS PASS")


if __name__ == "__main__":
    main()
