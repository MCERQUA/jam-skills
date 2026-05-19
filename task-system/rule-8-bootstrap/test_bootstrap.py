"""
Smoke tests for the Rule 8 bootstrap context loader.

Mirrors the scaffold + tempfile pattern from
/agent-desk/snapshots/2026-05-19-canonical-schema-v0.1.3/test_canonical_schema.py:
each assertion builds disposable workspace state, exercises load_context, and
asserts the returned dict's shape.

Run with:

    python3 test_bootstrap.py
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import task_bootstrap  # noqa: E402

_TENANT = "cca"
_OPEN_STATES = {
    "intake", "shop-floor", "planned", "scheduled",
    "today", "in-flight", "parked",
}
_ALL_STATES = _OPEN_STATES | {"done"}


def _now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _scaffold_workspace(work: Path) -> Path:
    tasks_root = work / "tasks"
    for state in _ALL_STATES:
        (tasks_root / state).mkdir(parents=True, exist_ok=True)
    return tasks_root


def _make_task(
    tasks_root: Path,
    state: str,
    task_id: str,
    tenant: str = _TENANT,
    **extra,
) -> Path:
    d = tasks_root / state / task_id
    d.mkdir(parents=True, exist_ok=True)
    record = {
        "id": task_id,
        "state": state,
        "raised_at": _now_z(),
        "raised_by": "mesh",
        "source_ref": None,
        "summary": "test task",
        "tenant": tenant,
        "operator_phone": None,
        "email_authorized_by_mike": None,
        "recipient": None,
        "state_history": [{"state": state, "at": _now_z(), "by": "test@mesh"}],
        "clerk_session_id": None,
        "lock_required": True,
        "defer_count": 0,
        "failure_modes": [],
        "dedup_hash": None,
        "recipient_role": None,
        "linked_to": [],
    }
    record.update(extra)
    (d / "task.json").write_text(json.dumps(record, indent=2))
    return d / "task.json"


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="rule8-bootstrap-test-"))
    try:
        tasks_root = _scaffold_workspace(work)

        # [1] all required top-level keys present.
        ctx = task_bootstrap.load_context(_TENANT, work)
        expected_keys = {
            "tenant", "workspace", "loaded_at", "today",
            "open_tasks", "open_task_count",
            "ledger_recent", "gmail_threads", "sms_threads",
            "voice_transcript", "reflections_recent",
        }
        missing = expected_keys - set(ctx.keys())
        assert not missing, f"missing top-level keys: {sorted(missing)}"
        assert ctx["tenant"] == _TENANT
        assert ctx["workspace"] == str(work.resolve())
        assert isinstance(ctx["loaded_at"], str)
        assert isinstance(ctx["today"], str) and len(ctx["today"]) == 10
        print(f"[1] load_context returns all {len(expected_keys)} required top-level keys: OK")

        # [2] open_tasks dict has all 7 scanned open states as keys (even when empty).
        assert set(ctx["open_tasks"].keys()) == _OPEN_STATES
        for state in _OPEN_STATES:
            assert ctx["open_tasks"][state] == [], f"{state} should be empty list"
        print("[2] open_tasks has all 7 open states as keys (empty workspace): OK")

        # [3] done/ tasks NOT included in open_tasks.
        _make_task(tasks_root, "done", "2026-05-19-0900-done-task")
        _make_task(tasks_root, "in-flight", "2026-05-19-0901-flight-task")
        ctx = task_bootstrap.load_context(_TENANT, work)
        assert "done" not in ctx["open_tasks"], "done must NOT be a key in open_tasks"
        all_ids = [t["id"] for tl in ctx["open_tasks"].values() for t in tl]
        assert "2026-05-19-0900-done-task" not in all_ids
        assert "2026-05-19-0901-flight-task" in all_ids
        print("[3] done/ tasks excluded from open_tasks: OK")

        # [4] open_task_count matches the sum across states.
        _make_task(tasks_root, "intake", "2026-05-19-0902-intake-a")
        _make_task(tasks_root, "intake", "2026-05-19-0903-intake-b")
        _make_task(tasks_root, "today", "2026-05-19-0904-today-a")
        ctx = task_bootstrap.load_context(_TENANT, work)
        manual_sum = sum(len(v) for v in ctx["open_tasks"].values())
        assert ctx["open_task_count"] == manual_sum
        # in-flight×1 + intake×2 + today×1 = 4 open; done×1 excluded.
        assert ctx["open_task_count"] == 4, ctx["open_task_count"]
        print(f"[4] open_task_count == sum across states ({manual_sum}): OK")

        # [5] missing optional inputs degrade gracefully on a bare workspace.
        bare = Path(tempfile.mkdtemp(prefix="rule8-bootstrap-bare-"))
        try:
            (bare / "tasks").mkdir()
            ctx_bare = task_bootstrap.load_context(_TENANT, bare)
            assert ctx_bare["open_task_count"] == 0
            assert ctx_bare["ledger_recent"] == []
            assert ctx_bare["gmail_threads"] == {}
            assert ctx_bare["sms_threads"] == {}
            assert ctx_bare["voice_transcript"] is None
            assert ctx_bare["reflections_recent"] == []
            # Also valid with no tasks/ dir at all:
            barer = Path(tempfile.mkdtemp(prefix="rule8-bootstrap-barer-"))
            try:
                ctx_barer = task_bootstrap.load_context(_TENANT, barer)
                assert ctx_barer["open_task_count"] == 0
                assert set(ctx_barer["open_tasks"].keys()) == _OPEN_STATES
            finally:
                shutil.rmtree(barer)
        finally:
            shutil.rmtree(bare)
        print("[5] missing optional inputs degrade gracefully: OK")

        # [6] gmail_threads only includes threads referenced by an open task.
        gmail_dir = work / "gmail" / "threads"
        gmail_dir.mkdir(parents=True, exist_ok=True)
        (gmail_dir / "gmail-thread-referenced.json").write_text(
            json.dumps([{"id": "m1", "body": "hi"}])
        )
        (gmail_dir / "gmail-thread-orphan.json").write_text(
            json.dumps([{"id": "m99", "body": "should not load"}])
        )
        _make_task(
            tasks_root, "intake", "2026-05-19-0905-email-task",
            raised_by="email", source_ref="gmail-thread-referenced",
        )
        ctx = task_bootstrap.load_context(_TENANT, work)
        assert "gmail-thread-referenced" in ctx["gmail_threads"]
        assert "gmail-thread-orphan" not in ctx["gmail_threads"]
        loaded = ctx["gmail_threads"]["gmail-thread-referenced"]
        assert isinstance(loaded, list) and loaded[0]["id"] == "m1"
        print("[6] gmail_threads filtered to referenced source_refs only: OK")

        # [7] voice_transcript loads when memory/<today>-conversation.md exists.
        today_d = date(2026, 5, 19)
        memory_dir = work / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        (memory_dir / f"{today_d.isoformat()}-conversation.md").write_text(
            "# 2026-05-19 voice transcript\nhello"
        )
        ctx_today = task_bootstrap.load_context(_TENANT, work, today=today_d)
        assert ctx_today["voice_transcript"] is not None
        assert "voice transcript" in ctx_today["voice_transcript"]
        # A day with no transcript file → None.
        other_day = date(2026, 1, 1)
        ctx_other = task_bootstrap.load_context(_TENANT, work, today=other_day)
        assert ctx_other["voice_transcript"] is None
        print("[7] voice_transcript loads when present, None otherwise: OK")

        # [8] ledger_recent filters to last 7 days; --today override demonstrates.
        ledger_dir = work / "ledger"
        ledger_dir.mkdir(parents=True, exist_ok=True)
        anchor = date(2026, 5, 19)
        for offset, label in [(0, "today"), (3, "three-back"), (10, "ten-back")]:
            d_str = (anchor - timedelta(days=offset)).isoformat()
            (ledger_dir / f"{d_str}.json").write_text(
                json.dumps([{"at": d_str, "label": label}])
            )
        ctx_anchor = task_bootstrap.load_context(_TENANT, work, today=anchor)
        labels = sorted(e["label"] for e in ctx_anchor["ledger_recent"])
        assert "today" in labels
        assert "three-back" in labels
        assert "ten-back" not in labels, f"10-day-old entry must be filtered; got {labels}"
        # Override to a future anchor → all ledger entries fall in-window:
        future_anchor = date(2026, 5, 27)  # 8d after newest, 17d after oldest
        ctx_future = task_bootstrap.load_context(_TENANT, work, today=future_anchor)
        future_labels = sorted(e["label"] for e in ctx_future["ledger_recent"])
        # newest is 0d-from-anchor, but anchor moved → it's 8d-old now, also out
        assert "today" not in future_labels
        assert "three-back" not in future_labels
        # Override to an EARLIER anchor that includes only the "three-back" entry:
        earlier_anchor = date(2026, 5, 16)  # = anchor - 3d
        ctx_earlier = task_bootstrap.load_context(_TENANT, work, today=earlier_anchor)
        earlier_labels = sorted(e["label"] for e in ctx_earlier["ledger_recent"])
        assert "three-back" in earlier_labels  # 5/16 == anchor, in-window
        assert "today" not in earlier_labels   # 5/19 > earlier_anchor → out (future)
        print(f"[8] ledger_recent 7-day window honors --today override (anchor={anchor}: {labels}): OK")

        # [9] malformed task.json files skipped, not crash.
        bad_dir = tasks_root / "intake" / "2026-05-19-0906-bad-json"
        bad_dir.mkdir(parents=True, exist_ok=True)
        (bad_dir / "task.json").write_text("{not valid json")
        ctx = task_bootstrap.load_context(_TENANT, work, today=today_d)
        all_ids = [t["id"] for tl in ctx["open_tasks"].values() for t in tl]
        assert "2026-05-19-0906-bad-json" not in all_ids
        # Good tasks from earlier still present:
        assert "2026-05-19-0902-intake-a" in all_ids
        assert "2026-05-19-0903-intake-b" in all_ids
        print("[9] malformed task.json skipped, no crash: OK")

        # [10] return value is a plain dict (JSON-serializable for mesh transmission).
        ctx = task_bootstrap.load_context(_TENANT, work, today=today_d)
        assert type(ctx) is dict, f"expected plain dict, got {type(ctx).__name__}"
        serialized = json.dumps(ctx)
        roundtrip = json.loads(serialized)
        assert roundtrip["tenant"] == _TENANT
        assert roundtrip["open_task_count"] == ctx["open_task_count"]
        assert set(roundtrip["open_tasks"].keys()) == _OPEN_STATES
        print("[10] return value is JSON-serializable plain dict: OK")

        print("\nALL RULE 8 BOOTSTRAP ASSERTIONS PASSED")
        return 0
    finally:
        shutil.rmtree(work)


if __name__ == "__main__":
    sys.exit(main())
