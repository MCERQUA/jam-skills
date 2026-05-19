"""
shift_lock_smoke — 12 assertions covering the parallel_shift_writer_race defense.

Race scenarios exercised:
- T1: fresh acquire on empty dir
- T2: re-entry from same PID/URI is idempotent
- T3: same URI, different PID → DENIED with reason `parallel_shift_writer_race`
- T4: different URI → DENIED with reason `cross-agent-collision`
- T5: stale lock auto-swept; prior payload preserved at `.shift.lock.swept-<ts>`
- T6: release-then-acquire-by-second-writer works
- T7: heartbeat updates heartbeat_at; release after heartbeat OK
- T8: context manager releases on normal exit
- T9: context manager releases on exception
- T10: context manager raises ShiftRaceError when contested
- T11: corrupt lock file (non-JSON) → recovered cleanly
- T12: two subprocess writers race; exactly one wins, other gets parallel_shift_writer_race
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Make sibling import work
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shift_lock import LOCK_FILENAME, SWEPT_PREFIX, ShiftLock, ShiftRaceError  # noqa: E402


PASSED = 0
FAILED = 0


def check(label: str, cond: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  OK   {label}")
    else:
        FAILED += 1
        print(f"  FAIL {label} :: {detail}")


def t1_fresh_acquire(tmp: Path) -> None:
    d = tmp / "t1"
    lock = ShiftLock(d, "src-desktop@mesh", pid=1001)
    result = lock.acquire()
    check("T1.granted", result.granted, str(result))
    check("T1.lockfile_present", (d / LOCK_FILENAME).exists())
    payload = json.loads((d / LOCK_FILENAME).read_text())
    check("T1.payload_agent_uri", payload["agent_uri"] == "src-desktop@mesh")
    check("T1.payload_pid", payload["pid"] == 1001)
    lock.release()


def t2_re_entry(tmp: Path) -> None:
    d = tmp / "t2"
    lock1 = ShiftLock(d, "src-desktop@mesh", pid=2001)
    lock1.acquire()
    lock2 = ShiftLock(d, "src-desktop@mesh", pid=2001)
    result = lock2.acquire()
    check("T2.re_entry_granted", result.granted, str(result))
    check("T2.reason_is_re_entry", result.reason == "re-entry")
    lock1.release()


def t3_same_uri_different_pid(tmp: Path) -> None:
    d = tmp / "t3"
    held = ShiftLock(d, "src-desktop@mesh", pid=3001)
    held.acquire()
    contender = ShiftLock(d, "src-desktop@mesh", pid=3002)
    result = contender.acquire()
    check("T3.denied", not result.granted)
    check("T3.reason_is_named_failure_mode",
          result.reason == "parallel_shift_writer_race", result.reason)
    held.release()


def t4_cross_agent(tmp: Path) -> None:
    d = tmp / "t4"
    held = ShiftLock(d, "src-desktop@mesh", pid=4001)
    held.acquire()
    contender = ShiftLock(d, "bun-desktop@mesh", pid=4002)
    result = contender.acquire()
    check("T4.denied", not result.granted)
    check("T4.reason_is_cross_agent",
          result.reason == "cross-agent-collision", result.reason)
    held.release()


def t5_stale_sweep(tmp: Path) -> None:
    d = tmp / "t5"
    d.mkdir()
    stale_payload = {
        "agent_uri": "src-desktop@mesh",
        "pid": 5001,
        "hostname": "ghost",
        "acquired_at": "2020-01-01T00:00:00Z",
        "heartbeat_at": "2020-01-01T00:00:00Z",
        "stale_after_seconds": 600,
    }
    (d / LOCK_FILENAME).write_text(json.dumps(stale_payload))
    fresh = ShiftLock(d, "src-desktop@mesh", pid=5002, stale_after_seconds=600)
    result = fresh.acquire()
    check("T5.granted_after_sweep", result.granted, str(result))
    check("T5.reason_is_swept", result.reason == "swept-stale")
    check("T5.swept_path_preserved",
          result.swept_path is not None and Path(result.swept_path).exists())
    swept_files = list(d.glob(f"{SWEPT_PREFIX}*"))
    check("T5.exactly_one_swept_file", len(swept_files) == 1, f"got {len(swept_files)}")
    fresh.release()


def t6_release_then_other_writer(tmp: Path) -> None:
    d = tmp / "t6"
    first = ShiftLock(d, "src-desktop@mesh", pid=6001)
    first.acquire()
    first.release()
    second = ShiftLock(d, "bun-desktop@mesh", pid=6002)
    result = second.acquire()
    check("T6.second_writer_granted_after_release", result.granted, str(result))
    second.release()


def t7_heartbeat(tmp: Path) -> None:
    d = tmp / "t7"
    lock = ShiftLock(d, "src-desktop@mesh", pid=7001)
    lock.acquire()
    original = json.loads((d / LOCK_FILENAME).read_text())["heartbeat_at"]
    time.sleep(1.1)
    lock.heartbeat()
    updated = json.loads((d / LOCK_FILENAME).read_text())["heartbeat_at"]
    check("T7.heartbeat_advanced", updated > original, f"{original} → {updated}")
    check("T7.release_succeeds", lock.release())


def t8_context_manager_normal(tmp: Path) -> None:
    d = tmp / "t8"
    lock = ShiftLock(d, "src-desktop@mesh", pid=8001)
    with lock.held():
        check("T8.lockfile_present_inside_ctx", (d / LOCK_FILENAME).exists())
    check("T8.lockfile_removed_after_ctx", not (d / LOCK_FILENAME).exists())


def t9_context_manager_exception(tmp: Path) -> None:
    d = tmp / "t9"
    lock = ShiftLock(d, "src-desktop@mesh", pid=9001)
    try:
        with lock.held():
            raise RuntimeError("simulated failure")
    except RuntimeError:
        pass
    check("T9.lockfile_removed_after_exception", not (d / LOCK_FILENAME).exists())


def t10_context_manager_contested(tmp: Path) -> None:
    d = tmp / "t10"
    held = ShiftLock(d, "src-desktop@mesh", pid=10001)
    held.acquire()
    contender = ShiftLock(d, "src-desktop@mesh", pid=10002)
    raised = False
    try:
        with contender.held():
            pass
    except ShiftRaceError:
        raised = True
    check("T10.contested_raises_ShiftRaceError", raised)
    held.release()


def t11_corrupt_lock_recovered(tmp: Path) -> None:
    d = tmp / "t11"
    d.mkdir()
    (d / LOCK_FILENAME).write_text("not-valid-json {{{")
    lock = ShiftLock(d, "src-desktop@mesh", pid=11001)
    result = lock.acquire()
    check("T11.corrupt_lock_recovered",
          result.granted and result.reason == "recovered-corrupt-lock",
          f"reason={result.reason}")
    lock.release()


def t12_subprocess_race(tmp: Path) -> None:
    """Spawn two subprocess workers that try to acquire simultaneously."""
    d = tmp / "t12"
    d.mkdir()
    script = Path(__file__).resolve().parent / "shift_lock.py"
    worker_code = f"""
import sys, json
sys.path.insert(0, {str(script.parent)!r})
from shift_lock import ShiftLock
lock = ShiftLock({str(d)!r}, "src-desktop@mesh", pid=int(sys.argv[1]), stale_after_seconds=600)
result = lock.acquire()
print(json.dumps({{"granted": result.granted, "reason": result.reason, "pid": int(sys.argv[1])}}))
if result.granted:
    import time; time.sleep(0.5); lock.release()
"""
    worker_path = tmp / "_worker.py"
    worker_path.write_text(worker_code)

    p1 = subprocess.Popen([sys.executable, str(worker_path), "12001"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    p2 = subprocess.Popen([sys.executable, str(worker_path), "12002"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out1, _ = p1.communicate(timeout=10)
    out2, _ = p2.communicate(timeout=10)

    try:
        r1 = json.loads(out1.strip())
        r2 = json.loads(out2.strip())
    except json.JSONDecodeError:
        check("T12.subprocess_race", False, f"unparsable: {out1!r} / {out2!r}")
        return

    granted_count = int(r1["granted"]) + int(r2["granted"])
    check("T12.exactly_one_winner", granted_count == 1,
          f"got {granted_count}: r1={r1} r2={r2}")
    loser = r1 if not r1["granted"] else r2
    check("T12.loser_reports_named_failure_mode",
          loser["reason"] == "parallel_shift_writer_race",
          f"loser reason: {loser['reason']}")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        for fn in (t1_fresh_acquire, t2_re_entry, t3_same_uri_different_pid,
                   t4_cross_agent, t5_stale_sweep, t6_release_then_other_writer,
                   t7_heartbeat, t8_context_manager_normal,
                   t9_context_manager_exception, t10_context_manager_contested,
                   t11_corrupt_lock_recovered, t12_subprocess_race):
            fn(tmp)
    total = PASSED + FAILED
    print(f"\nshift_lock_smoke: {PASSED}/{total} assertions PASS")
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
