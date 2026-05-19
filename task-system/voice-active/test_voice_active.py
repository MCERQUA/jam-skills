"""
Tests for voice_active.py — AND-gate reader.

Uses tempfile for both signal paths so tests don't depend on the actual
deployed locations.
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import voice_active as va


def _fresh_heartbeat(path: Path) -> None:
    path.write_text("")
    # touch with current mtime
    now = time.time()
    os.utime(path, (now, now))


def _stale_heartbeat(path: Path, age_seconds: float) -> None:
    path.write_text("")
    past = time.time() - age_seconds
    os.utime(path, (past, past))


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="voice-active-test-"))
    try:
        cookie = work / "clerk-session.cookie"
        heartbeat = work / "voice-active.flag"

        pred = va.VoiceActivePredicate(
            clerk_cookie_path=str(cookie),
            heartbeat_path=str(heartbeat),
            heartbeat_stale_seconds=5.0,
        )

        # [1] No writers, no signals: inactive, mode=full (parent dirs DO exist)
        assert pred.is_active() is False, "no signals → must be inactive"
        # The cookie's parent (work dir) DOES exist here, so mode is 'full'.
        # We test 'no-writers-deployed' below with non-existent parent dirs.
        print("[1] both signals absent → is_active False: OK")

        # [2] Only cookie present, heartbeat missing → inactive (AND-gate)
        cookie.write_text("dummy session cookie")
        assert pred.is_active() is False, "cookie alone must not fire AND-gate"
        print("[2] cookie-only → is_active False (AND-gate enforced): OK")

        # [3] Only heartbeat fresh, cookie missing → inactive
        cookie.unlink()
        _fresh_heartbeat(heartbeat)
        assert pred.is_active() is False, "heartbeat alone must not fire AND-gate"
        print("[3] heartbeat-only → is_active False (AND-gate enforced): OK")

        # [4] Both present + fresh → ACTIVE
        cookie.write_text("dummy session cookie")
        _fresh_heartbeat(heartbeat)
        assert pred.is_active() is True, "both present + fresh must fire AND-gate"
        print("[4] cookie + fresh heartbeat → is_active True: OK")

        # [5] Both present, but heartbeat STALE → inactive
        _stale_heartbeat(heartbeat, age_seconds=7.0)  # >5s stale window
        assert pred.is_active() is False, "stale heartbeat must not fire AND-gate"
        print("[5] cookie + stale heartbeat (>5s) → is_active False: OK")

        # [6] heartbeat at exactly the stale boundary
        _stale_heartbeat(heartbeat, age_seconds=4.9)  # within window
        assert pred.is_active() is True, "heartbeat just inside window must fire"
        print("[6] heartbeat 4.9s old (inside 5s window) → is_active True: OK")

        # [7] custom stale window (constructor override)
        pred_short = va.VoiceActivePredicate(
            clerk_cookie_path=str(cookie),
            heartbeat_path=str(heartbeat),
            heartbeat_stale_seconds=2.0,
        )
        _stale_heartbeat(heartbeat, age_seconds=3.0)
        assert pred.is_active() is True, "default 5s window: 3s old is fresh"
        assert pred_short.is_active() is False, "custom 2s window: 3s old is stale"
        print("[7] custom heartbeat_stale_seconds respected: OK")

        # [8] predicate_mode = 'full' when both parent dirs exist
        # (cookie and heartbeat are both under `work` which exists)
        assert pred.predicate_mode() == "full", pred.predicate_mode()
        print("[8] both writer dirs present → mode='full': OK")

        # [9] mode='no-writers-deployed' when neither parent dir exists
        pred_none = va.VoiceActivePredicate(
            clerk_cookie_path="/nonexistent-cookie-dir/cookie",
            heartbeat_path="/nonexistent-heartbeat-dir/flag",
        )
        assert pred_none.predicate_mode() == "no-writers-deployed", pred_none.predicate_mode()
        assert pred_none.is_active() is False, "no writers → is_active False"
        print("[9] no writer dirs → mode='no-writers-deployed' + is_active False: OK")

        # [10] mode='degraded-heartbeat-only' (heartbeat dir present, cookie dir missing)
        pred_hb_only = va.VoiceActivePredicate(
            clerk_cookie_path="/nonexistent-cookie-dir/cookie",
            heartbeat_path=str(heartbeat),
        )
        assert pred_hb_only.predicate_mode() == "degraded-heartbeat-only", pred_hb_only.predicate_mode()
        print("[10] heartbeat dir only → mode='degraded-heartbeat-only': OK")

        # [11] mode='degraded-cookie-only' (cookie dir present, heartbeat dir missing)
        pred_ck_only = va.VoiceActivePredicate(
            clerk_cookie_path=str(cookie),
            heartbeat_path="/nonexistent-heartbeat-dir/flag",
        )
        assert pred_ck_only.predicate_mode() == "degraded-cookie-only", pred_ck_only.predicate_mode()
        print("[11] cookie dir only → mode='degraded-cookie-only': OK")

        # [12] Latency sanity: under 100ms per is_active() call (target: <1ms)
        # Re-prime signals so we measure the active path (more I/O than inactive).
        cookie.write_text("dummy session cookie")
        _fresh_heartbeat(heartbeat)
        N = 1000
        start = time.perf_counter()
        for _ in range(N):
            _ = pred.is_active()
        elapsed = time.perf_counter() - start
        per_call_ms = (elapsed / N) * 1000
        assert per_call_ms < 100.0, f"per-call latency {per_call_ms:.3f}ms exceeds 100ms target"
        print(f"[12] is_active() per-call latency: {per_call_ms:.3f}ms (target <100ms): OK")

        # [13] module-level convenience funcs work (with default paths,
        # they reflect real environment — just confirm they don't crash and
        # return the right types)
        assert isinstance(va.is_active(), bool)
        assert va.predicate_mode() in (
            "full", "degraded-cookie-only", "degraded-heartbeat-only", "no-writers-deployed"
        )
        print("[13] module-level convenience funcs return correct types: OK")

        # [14] OSError on cookie path (e.g. permission denied) treated as inactive
        # Hard to simulate portably; simulate by passing a path that triggers
        # ENOTDIR (cookie under a file, not a directory)
        regular_file = work / "regular.txt"
        regular_file.write_text("")
        pred_enotdir = va.VoiceActivePredicate(
            clerk_cookie_path=str(regular_file / "subpath"),  # path under a file
            heartbeat_path=str(heartbeat),
        )
        # _fresh_heartbeat already set
        assert pred_enotdir.is_active() is False, "ENOTDIR on cookie path must read as inactive"
        print("[14] cookie path OSError (ENOTDIR) → is_active False: OK")

        print("\nALL VOICE-ACTIVE ASSERTIONS PASSED")
        return 0
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
