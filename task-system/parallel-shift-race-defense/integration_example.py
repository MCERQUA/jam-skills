"""
integration_example — using ShiftLock to defend a snapshot writer.

Drop-in pattern any task-system writer can adopt before mutating
/agent-desk/snapshots/<name>/. Demonstrates:

  1. acquire-before-write (the minimum viable defense)
  2. heartbeat during long-running shifts so co-shift work doesn't sweep us
  3. swept-payload inspection — when we sweep a stale prior, we can read what
     the displaced shift was working on and emit a postmortem hint

Run: python3 integration_example.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shift_lock import ShiftLock, ShiftRaceError  # noqa: E402


def write_snapshot_artifact(snapshot_dir: Path, agent_uri: str) -> None:
    """Canonical writer pattern: lock, write, heartbeat, release."""
    lock = ShiftLock(snapshot_dir, agent_uri, stale_after_seconds=600)

    with lock.held() as held_lock:
        manifest = snapshot_dir / "manifest.json"
        manifest.write_text(json.dumps({
            "written_by": agent_uri,
            "files": ["spec.md", "schema.json"],
        }, indent=2))

        for chunk_id in range(3):
            (snapshot_dir / f"chunk-{chunk_id}.txt").write_text(f"chunk {chunk_id}\n")
            time.sleep(0.05)
            held_lock.heartbeat()

        (snapshot_dir / "DONE").touch()


def main() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)

        scenario_a = tmp / "scenario-a-happy-path"
        write_snapshot_artifact(scenario_a, "src-desktop@mesh")
        assert (scenario_a / "DONE").exists(), "happy path didn't complete"
        assert not (scenario_a / ".shift.lock").exists(), "lock not released"
        print("scenario A (happy path): OK")

        scenario_b = tmp / "scenario-b-second-shift-blocked"
        first = ShiftLock(scenario_b, "src-desktop@mesh", pid=99001)
        first.acquire()
        try:
            write_snapshot_artifact(scenario_b, "src-desktop@mesh")
            print("scenario B (contested write): FAIL — second shift should have raised")
            return 1
        except ShiftRaceError as e:
            print(f"scenario B (contested write): OK — second shift refused: {e}")
        finally:
            first.release()

        scenario_c = tmp / "scenario-c-swept-stale"
        scenario_c.mkdir()
        stale_payload = {
            "agent_uri": "src-desktop@mesh",
            "pid": 99002,
            "hostname": "ghost-shift",
            "acquired_at": "2020-01-01T00:00:00Z",
            "heartbeat_at": "2020-01-01T00:00:00Z",
            "stale_after_seconds": 600,
        }
        (scenario_c / ".shift.lock").write_text(json.dumps(stale_payload))
        write_snapshot_artifact(scenario_c, "src-desktop@mesh")
        swept = list(scenario_c.glob(".shift.lock.swept-*"))
        assert len(swept) == 1, f"expected 1 swept file, got {len(swept)}"
        swept_payload = json.loads(swept[0].read_text())
        print(f"scenario C (stale sweep): OK — preserved prior owner pid={swept_payload['pid']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
