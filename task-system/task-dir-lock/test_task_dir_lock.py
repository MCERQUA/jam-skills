"""
test_task_dir_lock — assertions covering the parallel_shift_writer_race defense.

Run: python3 test_task_dir_lock.py
Pass: prints "task_dir_lock: N/N assertions PASS"
Fail: assertion raises with a descriptive message.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from task_dir_lock import task_dir_lock, LockContended, LockTimeout, LOCK_FILENAME


def test_1_happy_path_acquire_release():
    """Single writer can acquire and release the lock."""
    with tempfile.TemporaryDirectory() as td:
        with task_dir_lock(td, writer_label="test-1") as lockfile:
            assert Path(lockfile).exists(), "lock sentinel must exist while held"
        # After release, sentinel persists — that is by design (see docstring).
        assert (Path(td) / LOCK_FILENAME).exists()
    print("  [1] happy_path_acquire_release            PASS")


def test_2_non_blocking_contention_raises():
    """Second non-blocking writer must raise LockContended immediately."""
    with tempfile.TemporaryDirectory() as td:
        with task_dir_lock(td, writer_label="holder"):
            try:
                # second writer in this same process — different fd, same flock contention
                with task_dir_lock(td, writer_label="contender"):
                    raise AssertionError("contender must not have acquired")
            except LockContended:
                pass  # expected
    print("  [2] non_blocking_contention_raises        PASS")


def test_3_blocking_acquires_after_release():
    """Blocking writer waits for release and then acquires."""
    with tempfile.TemporaryDirectory() as td:
        events: list[tuple[float, str]] = []
        release_evt = threading.Event()

        def holder():
            with task_dir_lock(td, writer_label="holder"):
                events.append((time.monotonic(), "holder_acquired"))
                release_evt.wait(timeout=2)
                events.append((time.monotonic(), "holder_releasing"))

        def waiter():
            time.sleep(0.05)  # ensure holder gets there first
            with task_dir_lock(td, blocking=True, timeout_s=2, writer_label="waiter"):
                events.append((time.monotonic(), "waiter_acquired"))

        t_h = threading.Thread(target=holder)
        t_w = threading.Thread(target=waiter)
        t_h.start(); t_w.start()
        time.sleep(0.2)
        release_evt.set()
        t_h.join(); t_w.join()

        names = [e[1] for e in events]
        assert names == ["holder_acquired", "holder_releasing", "waiter_acquired"], names
    print("  [3] blocking_acquires_after_release       PASS")


def test_4_blocking_times_out():
    """Blocking writer that never gets the lock raises LockTimeout."""
    with tempfile.TemporaryDirectory() as td:
        with task_dir_lock(td, writer_label="permanent-holder"):
            try:
                with task_dir_lock(td, blocking=True, timeout_s=0.3, writer_label="loser"):
                    raise AssertionError("loser must have timed out")
            except LockTimeout:
                pass
    print("  [4] blocking_times_out                    PASS")


def test_5_kernel_releases_lock_on_crashed_holder():
    """If a holder dies without releasing, kernel releases the lock on fd close.

    Validates the no-stale-lock-cleanup property: a crashed shift does not
    deadlock subsequent shifts.
    """
    with tempfile.TemporaryDirectory() as td:
        # Subprocess that takes the lock and then exits abruptly.
        script = f"""
import sys; sys.path.insert(0, "{os.path.dirname(__file__) or '.'}")
from task_dir_lock import task_dir_lock
with task_dir_lock("{td}", writer_label="crasher"):
    pass  # context exit releases — simulate via abrupt exit instead
"""
        # Use a "harder" crash sim: take the lock, then os._exit without ctx cleanup.
        crash_script = f"""
import sys, os, fcntl
sys.path.insert(0, "{os.path.dirname(__file__) or '.'}")
fh = open("{Path(td) / LOCK_FILENAME}", "a+")
fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
os._exit(13)  # no cleanup, no context exit — simulates crash
"""
        r = subprocess.run(["python3", "-c", crash_script])
        assert r.returncode == 13

        # Now this process should be able to take the lock immediately —
        # kernel released the lock when the crashed process's fds were closed.
        with task_dir_lock(td, blocking=False, writer_label="survivor"):
            pass
    print("  [5] kernel_releases_lock_on_crashed_holder PASS")


def test_6_bash_flock_cli_parity():
    """bash callers using `flock` CLI on the same sentinel see the same lock.

    Important because mesh-* helpers and other shell scripts also touch task dirs.
    """
    with tempfile.TemporaryDirectory() as td:
        lockfile = Path(td) / LOCK_FILENAME
        lockfile.touch()  # bash flock needs the file to exist

        # Python holder; bash contender (non-blocking via -n, exits 1 on contention).
        with task_dir_lock(td, writer_label="py-holder"):
            r = subprocess.run(
                ["flock", "-n", str(lockfile), "-c", "true"],
                capture_output=True,
            )
            assert r.returncode != 0, "bash flock -n must report contention while python holds"

        # After python releases, bash should succeed.
        r = subprocess.run(
            ["flock", "-n", str(lockfile), "-c", "true"],
            capture_output=True,
        )
        assert r.returncode == 0, "bash flock -n must succeed after python releases"
    print("  [6] bash_flock_cli_parity                 PASS")


def test_7_concurrent_transitions_serialize():
    """Two threads racing the same task dir result in exactly ONE 'winner' write.

    This is the actual parallel_shift_writer_race scenario the defense exists for.
    """
    with tempfile.TemporaryDirectory() as td:
        log_path = Path(td) / "history.log"
        log_path.touch()
        winner_count = [0]
        contended_count = [0]
        lock_obs = threading.Lock()

        def shift(label: str):
            try:
                with task_dir_lock(td, writer_label=label):
                    time.sleep(0.05)  # hold long enough that the other shift collides
                    with log_path.open("a") as f:
                        f.write(f"{label}\n")
                    with lock_obs:
                        winner_count[0] += 1
            except LockContended:
                with lock_obs:
                    contended_count[0] += 1

        threads = [threading.Thread(target=shift, args=(f"shift-{i}",)) for i in range(2)]
        for t in threads: t.start()
        for t in threads: t.join()

        assert winner_count[0] == 1 and contended_count[0] == 1, \
            f"expected 1 winner + 1 contended; got {winner_count[0]}/{contended_count[0]}"
        assert log_path.read_text().count("\n") == 1, "exactly one history line"
    print("  [7] concurrent_transitions_serialize      PASS")


def test_8_filename_is_reserved():
    """Verifying the lock sentinel name matches the documented contract."""
    assert LOCK_FILENAME == ".writer.lock"
    print("  [8] lock_filename_contract                PASS")


if __name__ == "__main__":
    tests = [
        test_1_happy_path_acquire_release,
        test_2_non_blocking_contention_raises,
        test_3_blocking_acquires_after_release,
        test_4_blocking_times_out,
        test_5_kernel_releases_lock_on_crashed_holder,
        test_6_bash_flock_cli_parity,
        test_7_concurrent_transitions_serialize,
        test_8_filename_is_reserved,
    ]
    for fn in tests:
        fn()
    print(f"task_dir_lock: {len(tests)}/{len(tests)} assertions PASS")
