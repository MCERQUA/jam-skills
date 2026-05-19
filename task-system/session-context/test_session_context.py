"""
Tests for session_context.SessionContext.

Mirrors worker-a's scaffold-and-tempdir pattern. Each numbered assertion
matches a deliverable from the worker-b brief.

Run with:

    python3 test_session_context.py
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import session_context  # noqa: E402
from session_context import (  # noqa: E402
    SessionContext,
    start_task_session,
    _OPEN_STATES_ORDER,
)

_TENANT = "cca"
_TODAY = date(2026, 5, 19)
_OPEN_STATES = set(_OPEN_STATES_ORDER)
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
    *,
    tenant: str = _TENANT,
    summary: str = "test task",
    source_ref: str | None = None,
    raised_by: str = "mesh",
    operator_phone: str | None = None,
) -> None:
    d = tasks_root / state / task_id
    d.mkdir(parents=True, exist_ok=True)
    record = {
        "id": task_id,
        "state": state,
        "raised_at": _now_z(),
        "raised_by": raised_by,
        "source_ref": source_ref,
        "summary": summary,
        "tenant": tenant,
        "operator_phone": operator_phone,
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
    (d / "task.json").write_text(json.dumps(record, indent=2))


def _build_workspace(work: Path) -> None:
    """Populate one task per open state plus a `done` task that must be hidden,
    plus a gmail thread + sms conversation referenced by the intake task."""
    tasks_root = _scaffold_workspace(work)

    # One task per open state; ids encode the state so flatten-order is testable.
    _make_task(
        tasks_root, "intake", "2026-05-19-0900-intake-email",
        raised_by="email", source_ref="gmail-thread-AAA",
        operator_phone="+15555550100",
        summary="intake: email arrived",
    )
    _make_task(tasks_root, "shop-floor", "2026-05-19-0901-shopfloor",
               summary="shop-floor: triaged")
    _make_task(tasks_root, "planned", "2026-05-19-0902-planned",
               summary="planned: queued")
    _make_task(tasks_root, "scheduled", "2026-05-19-0903-scheduled",
               summary="scheduled: later")
    _make_task(tasks_root, "today", "2026-05-19-0904-today",
               summary="today: work it")
    _make_task(tasks_root, "in-flight", "2026-05-19-0905-flight",
               summary="in-flight: doing")
    _make_task(tasks_root, "parked", "2026-05-19-0906-parked-blocker",
               summary="parked: waiting on Mike approval")
    _make_task(tasks_root, "parked", "2026-05-19-0907-parked-other",
               summary="parked: deps not landed")

    # `done` task must NOT appear anywhere in the SessionContext.
    _make_task(tasks_root, "done", "2026-05-19-0808-done-task",
               summary="done: shipped")

    # Two open tasks share a source_ref → dedupe pre-check should return both.
    _make_task(
        tasks_root, "intake", "2026-05-19-0908-dup-intake",
        raised_by="email", source_ref="gmail-thread-DUP",
        summary="duplicate-source intake",
    )
    _make_task(
        tasks_root, "shop-floor", "2026-05-19-0909-dup-shopfloor",
        raised_by="email", source_ref="gmail-thread-DUP",
        summary="duplicate-source shopfloor",
    )

    # Gmail thread that an open task references.
    gmail_dir = work / "gmail" / "threads"
    gmail_dir.mkdir(parents=True, exist_ok=True)
    (gmail_dir / "gmail-thread-AAA.json").write_text(
        json.dumps([
            {"id": "m1", "from": "client@x.com", "body": "first message"},
            {"id": "m2", "from": "operator@y.com", "body": "reply"},
        ])
    )

    # SMS conversation for the same intake task's operator phone.
    sms_dir = work / "sms" / "conversations"
    sms_dir.mkdir(parents=True, exist_ok=True)
    (sms_dir / "+15555550100.json").write_text(
        json.dumps([
            {"sid": "SM1", "direction": "in", "body": "hey"},
            {"sid": "SM2", "direction": "out", "body": "got it"},
        ])
    )


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="session-context-test-"))
    try:
        _build_workspace(work)

        # [1] start_task_session returns a SessionContext.
        sess = start_task_session(_TENANT, work, today=_TODAY)
        assert isinstance(sess, SessionContext), type(sess).__name__
        print("[1] start_task_session returns a SessionContext: OK")

        # [2] tenant + loaded_at + to_dict round-trip correctly.
        assert sess.tenant == _TENANT
        assert isinstance(sess.loaded_at, str) and sess.loaded_at.endswith("Z")
        d = sess.to_dict()
        assert d["tenant"] == _TENANT
        assert d["loaded_at"] == sess.loaded_at
        # to_dict is JSON-serializable for logging / mesh transmission.
        json.dumps(d)
        print("[2] tenant + loaded_at + to_dict round-trip: OK")

        # [3] all_open_tasks flattens across the 7 scanned states, ordered intake → parked.
        flat = sess.all_open_tasks
        states_in_order = [t["state"] for t in flat]
        # Check ordering: each scanned state's tasks appear contiguously and in the
        # spec's intake → parked order. We assert by finding each state's first
        # occurrence and verifying those first-occurrence indices are monotonic.
        first_idx = {}
        for i, st in enumerate(states_in_order):
            first_idx.setdefault(st, i)
        present_in_flat = [
            s for s in _OPEN_STATES_ORDER if s in first_idx
        ]
        indices = [first_idx[s] for s in present_in_flat]
        assert indices == sorted(indices), (
            f"flatten not in intake→parked order; got {states_in_order}"
        )
        # done/ must be hidden:
        assert "done" not in states_in_order
        # All 7 open states should have at least one task in our scaffold:
        assert set(present_in_flat) == _OPEN_STATES
        print(f"[3] all_open_tasks flattens 7 states in order ({len(flat)} tasks): OK")

        # [4] open_tasks_in_state returns just that state's tasks.
        intake_only = sess.open_tasks_in_state("intake")
        # intake has: intake-email + dup-intake = 2 tasks
        assert len(intake_only) == 2, [t["id"] for t in intake_only]
        assert all(t["state"] == "intake" for t in intake_only)
        # Unknown state returns [].
        assert sess.open_tasks_in_state("nonexistent") == []
        # done is not loaded → []
        assert sess.open_tasks_in_state("done") == []
        print("[4] open_tasks_in_state filters correctly: OK")

        # [5] find_task_by_id returns dict or None.
        found = sess.find_task_by_id("2026-05-19-0904-today")
        assert found is not None and found["state"] == "today"
        missing = sess.find_task_by_id("2026-05-19-9999-not-here")
        assert missing is None
        # done/ tasks are not findable (open-only):
        done_hidden = sess.find_task_by_id("2026-05-19-0808-done-task")
        assert done_hidden is None
        print("[5] find_task_by_id returns dict or None: OK")

        # [6] find_tasks_by_source_ref returns list — multiple across states.
        dups = sess.find_tasks_by_source_ref("gmail-thread-DUP")
        assert isinstance(dups, list)
        dup_states = sorted(t["state"] for t in dups)
        assert dup_states == ["intake", "shop-floor"], dup_states
        # Single-match path:
        singles = sess.find_tasks_by_source_ref("gmail-thread-AAA")
        assert len(singles) == 1 and singles[0]["state"] == "intake"
        # No-match path returns []:
        assert sess.find_tasks_by_source_ref("nope-no-such-ref") == []
        # Defensive: None source_ref query → []
        assert sess.find_tasks_by_source_ref(None) == []
        print("[6] find_tasks_by_source_ref returns list (incl. cross-state matches): OK")

        # [7] thread_history_for / sms_history_for return [] when no match.
        msgs = sess.thread_history_for("gmail-thread-AAA")
        assert isinstance(msgs, list) and len(msgs) == 2 and msgs[0]["id"] == "m1"
        assert sess.thread_history_for("gmail-thread-missing") == []
        sms = sess.sms_history_for("+15555550100")
        assert isinstance(sms, list) and len(sms) == 2 and sms[0]["sid"] == "SM1"
        assert sess.sms_history_for("+19999999999") == []
        print("[7] thread_history_for / sms_history_for return [] on miss: OK")

        # [8] has_open_blocker_on: exact summary match against parked tasks.
        assert sess.has_open_blocker_on("parked: waiting on Mike approval") is True
        # Non-parked summary string must NOT register as a blocker:
        assert sess.has_open_blocker_on("today: work it") is False
        # Unknown summary:
        assert sess.has_open_blocker_on("no such blocker") is False
        # Exact-match (not substring):
        assert sess.has_open_blocker_on("waiting on Mike") is False
        print("[8] has_open_blocker_on: exact match on parked summaries only: OK")

        # [9] recent_blockers returns only parked-state records.
        blockers = sess.recent_blockers()
        assert isinstance(blockers, list)
        assert len(blockers) == 2, [t["id"] for t in blockers]
        assert all(t["state"] == "parked" for t in blockers)
        blocker_ids = sorted(t["id"] for t in blockers)
        assert blocker_ids == [
            "2026-05-19-0906-parked-blocker",
            "2026-05-19-0907-parked-other",
        ]
        print("[9] recent_blockers: only parked records: OK")

        # [10] SessionContext is read-only after init — no mutator surface,
        # and direct attribute mutation is refused.
        before = json.dumps(sess.to_dict(), sort_keys=True)

        # Direct attribute set is blocked:
        try:
            sess.tenant = "evil-tenant"
        except AttributeError:
            pass
        else:
            raise AssertionError("expected AttributeError on attribute set")

        # New attribute is blocked:
        try:
            sess.injected_attr = 1
        except AttributeError:
            pass
        else:
            raise AssertionError("expected AttributeError on new attribute set")

        # Attribute delete is blocked:
        try:
            del sess._ctx
        except AttributeError:
            pass
        else:
            raise AssertionError("expected AttributeError on attribute delete")

        # Class surface check: no public methods that look like mutators.
        mutator_prefixes = (
            "set_", "add_", "remove_", "delete_", "update_", "insert_",
            "append_", "pop_", "clear_", "write_", "save_", "mutate_",
            "promote_", "demote_", "transition_", "reset_",
        )
        public = [
            n for n in dir(SessionContext)
            if not n.startswith("_") and callable(getattr(SessionContext, n))
        ]
        bad = [n for n in public if n.startswith(mutator_prefixes)]
        assert not bad, f"unexpected mutator-shaped methods: {bad}"

        # Repeated reads must return equal snapshots.
        _ = sess.all_open_tasks
        _ = sess.recent_blockers()
        _ = sess.find_tasks_by_source_ref("gmail-thread-DUP")
        after = json.dumps(sess.to_dict(), sort_keys=True)
        assert before == after, "to_dict() changed across reads"
        print("[10] SessionContext is read-only after init: OK")

        print("\nALL SESSION CONTEXT ASSERTIONS PASSED")
        return 0
    finally:
        shutil.rmtree(work)


if __name__ == "__main__":
    sys.exit(main())
