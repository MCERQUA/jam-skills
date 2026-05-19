"""
Smoke tests for the canonical v0.1.4 schema validator.

Extends /agent-desk/snapshots/2026-05-18-task-substrate/test_substrate.py with
assertions for every field added in the v0.1.1 reconciliation. Run with:

    python3 test_canonical_schema.py
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BASELINE = _HERE.parent / "2026-05-18-task-substrate"

# Local task_schema is the canonical extension; scaffold_tenant is reused
# from the immutable v0.1 baseline. Order matters: _HERE must win over
# _BASELINE for the `task_schema` import.
sys.path.insert(0, str(_BASELINE))
sys.path.insert(0, str(_HERE))

import scaffold_tenant  # noqa: E402 — from baseline
import task_schema      # noqa: E402 — from this snapshot


def _now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_valid_intake(tasks_root: Path, task_id: str) -> Path:
    """Build a v0.1.2-canonical intake task on disk and return its path.

    v0.1.2 difference vs v0.1.1: Rule 8 fields (dedup_hash, recipient_role,
    linked_to) are now required-always (host@mesh confirmed 2026-05-18),
    so they MUST be present in the baseline valid record.
    """
    d = tasks_root / "intake" / task_id
    d.mkdir(parents=True, exist_ok=True)
    record = {
        "id": task_id,
        "state": "intake",
        "raised_at": _now_z(),
        "raised_by": "mesh",
        "source_ref": "2026-05-18-001-host-task-system-v0-1-spec-posted.md",
        "summary": "ship blocker.json writer in joshai-process.py",
        "tenant": "josh",
        "operator_phone": None,
        "email_authorized_by_mike": None,
        "recipient": None,
        "state_history": [
            {"state": "intake", "at": _now_z(), "by": "josh-desktop@mesh"},
        ],
        "clerk_session_id": None,
        "lock_required": True,
        "defer_count": 0,
        "failure_modes": [],
        "dedup_hash": "sha1:josh:fake-source-ref:test-baseline",
        "recipient_role": "mike",
        "linked_to": [],
    }
    (d / "task.json").write_text(json.dumps(record, indent=2))
    return d / "task.json"


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="canonical-schema-test-"))
    try:
        # ---- scaffolder (preserved from substrate) ----
        summary = scaffold_tenant.scaffold(work)
        assert set(summary["created"]) == set(scaffold_tenant._STATES)
        assert (work / "tasks" / "SCHEMA.md").exists()
        print("[1] scaffolder creates all 8 states + SCHEMA.md: OK")

        rerun = scaffold_tenant.scaffold(work)
        assert rerun["created"] == [] and set(rerun["existed"]) == set(scaffold_tenant._STATES)
        print("[2] scaffolder idempotent: OK")

        tasks_root = work / "tasks"

        # ---- validator: valid task (now with v0.1.1 fields) ----
        valid_path = make_valid_intake(tasks_root, "2026-05-18-2010-poc-followup")
        errors = task_schema.validate_task_file(valid_path)
        assert not errors, f"valid task should have no errors; got {errors}"
        print("[3] valid intake task: OK")

        # ---- validator: bad id format ----
        bad_id_path = make_valid_intake(tasks_root, "2026-05-18-2011-x")
        bad_record = json.loads(bad_id_path.read_text())
        bad_record["id"] = "not-a-valid-id"
        bad_id_path.write_text(json.dumps(bad_record))
        errors = task_schema.validate_task_file(bad_id_path)
        assert any("id must match" in e for e in errors), errors
        print("[4] bad id rejected: OK")

        # ---- validator: rule-1 cross-field check ----
        rule1_path = make_valid_intake(tasks_root, "2026-05-18-2012-rule1-check")
        rule1_record = json.loads(rule1_path.read_text())
        rule1_record["email_authorized_by_mike"] = _now_z()
        # leave recipient = None → must fail
        rule1_path.write_text(json.dumps(rule1_record))
        errors = task_schema.validate_task_file(rule1_path)
        assert any("rule-1 violation" in e for e in errors), errors
        print("[5] rule-1 cross-field check fires when only one of (auth, recipient) is set: OK")

        # ---- validator: state/location mismatch (tree-level) ----
        new_loc = tasks_root / "shop-floor" / "2026-05-18-2010-poc-followup"
        new_loc.mkdir(parents=True, exist_ok=True)
        (new_loc / "task.json").write_text(valid_path.read_text())
        report = task_schema.validate_tree(tasks_root)
        mismatch_hits = [
            errs for errs in report["invalid"].values()
            if any("state/location mismatch" in e for e in errs)
        ]
        assert mismatch_hits, f"expected mismatch error; got {report['invalid']}"
        print("[6] state/location mismatch detected: OK")

        # ---- validator: parked task missing parked_until ----
        parked_dir = tasks_root / "parked" / "2026-05-18-2013-parked-test"
        parked_dir.mkdir(parents=True, exist_ok=True)
        parked_record = json.loads(valid_path.read_text())
        parked_record["id"] = "2026-05-18-2013-parked-test"
        parked_record["state"] = "parked"
        # intentionally omit parked_until
        (parked_dir / "task.json").write_text(json.dumps(parked_record))
        errors = task_schema.validate_task_file(parked_dir / "task.json")
        assert any("missing required field: parked_until" in e for e in errors), errors
        print("[7] parked state requires parked_until: OK")

        # ---- NEW: escalate_count is no longer a task field ----
        # (Moved to blocker.json per src-desktop input.)
        elsewhere_path = make_valid_intake(tasks_root, "2026-05-18-2014-escalate-on-task")
        rec = json.loads(elsewhere_path.read_text())
        rec["escalate_count"] = 0
        elsewhere_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(elsewhere_path)
        assert any("unknown field" in e and "escalate_count" in e for e in errors), errors
        print("[8] escalate_count on task.json rejected as unknown field: OK")

        # ---- NEW: parked-task example carries blocker.json with escalate_count ----
        parked2_dir = tasks_root / "parked" / "2026-05-18-2015-blocker-example"
        parked2_dir.mkdir(parents=True, exist_ok=True)
        parked2_record = json.loads(valid_path.read_text())
        parked2_record["id"] = "2026-05-18-2015-blocker-example"
        parked2_record["state"] = "parked"
        parked2_record["parked_until"] = _now_z()
        parked2_record["state_history"].append(
            {"state": "parked", "at": _now_z(), "by": "josh-desktop@mesh"}
        )
        (parked2_dir / "task.json").write_text(json.dumps(parked2_record))
        blocker = {
            "raised_at": _now_z(),
            "blocker_text": "Waiting on Mike's approval for new domain DNS change",
            "last_pinged": _now_z(),
            "parked_until": _now_z(),
            "escalate_count": 0,
            "resurface_action": "email-mike-digest",
        }
        (parked2_dir / "blocker.json").write_text(json.dumps(blocker))
        errors = task_schema.validate_task_file(parked2_dir / "task.json")
        assert not errors, f"parked task with blocker.json should validate; got {errors}"
        assert (parked2_dir / "blocker.json").exists()
        loaded_blocker = json.loads((parked2_dir / "blocker.json").read_text())
        assert loaded_blocker["escalate_count"] == 0
        print("[9] parked task with sibling blocker.json (carrying escalate_count) valid: OK")

        # ---- NEW: state_history required ----
        no_hist_path = make_valid_intake(tasks_root, "2026-05-18-2016-no-history")
        rec = json.loads(no_hist_path.read_text())
        del rec["state_history"]
        no_hist_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(no_hist_path)
        assert any("missing required field: state_history" in e for e in errors), errors
        print("[10] state_history required: OK")

        # ---- NEW: state_history entry must have {state, at, by} ----
        bad_hist_path = make_valid_intake(tasks_root, "2026-05-18-2017-bad-history")
        rec = json.loads(bad_hist_path.read_text())
        rec["state_history"] = [{"state": "intake", "at": _now_z()}]  # missing 'by'
        bad_hist_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bad_hist_path)
        assert any("state_history" in e and "by" in e for e in errors), errors
        print("[11] state_history entry shape enforced: OK")

        # ---- NEW: state_history.at must be ISO-Z ----
        bad_hist2_path = make_valid_intake(tasks_root, "2026-05-18-2018-bad-history-ts")
        rec = json.loads(bad_hist2_path.read_text())
        rec["state_history"] = [
            {"state": "intake", "at": "not-an-iso-timestamp", "by": "josh-desktop@mesh"},
        ]
        bad_hist2_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bad_hist2_path)
        assert any("state_history" in e and "ISO" in e for e in errors), errors
        print("[12] state_history.at must be ISO-Z: OK")

        # ---- NEW: clerk_session_id required (but nullable) ----
        no_clerk_path = make_valid_intake(tasks_root, "2026-05-18-2019-no-clerk")
        rec = json.loads(no_clerk_path.read_text())
        del rec["clerk_session_id"]
        no_clerk_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(no_clerk_path)
        assert any("missing required field: clerk_session_id" in e for e in errors), errors
        print("[13] clerk_session_id required (nullable): OK")

        # ---- NEW: lock_required must be bool ----
        bad_lock_path = make_valid_intake(tasks_root, "2026-05-18-2020-bad-lock")
        rec = json.loads(bad_lock_path.read_text())
        rec["lock_required"] = "yes"
        bad_lock_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bad_lock_path)
        assert any("lock_required" in e and "bool" in e for e in errors), errors
        print("[14] lock_required must be bool: OK")

        # ---- NEW: lock_required = false accepted (background tasks) ----
        bg_path = make_valid_intake(tasks_root, "2026-05-18-2021-background-task")
        rec = json.loads(bg_path.read_text())
        rec["lock_required"] = False
        bg_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bg_path)
        assert not errors, f"background task should validate; got {errors}"
        print("[15] lock_required=false accepted for background tasks: OK")

        # ---- NEW: defer_count must be non-negative int ----
        bad_defer_path = make_valid_intake(tasks_root, "2026-05-18-2022-bad-defer")
        rec = json.loads(bad_defer_path.read_text())
        rec["defer_count"] = -1
        bad_defer_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bad_defer_path)
        assert any("defer_count" in e and "non-negative" in e for e in errors), errors
        print("[16] defer_count must be non-negative int: OK")

        # ---- v0.1.3 UPGRADE: failure_modes must be list of enum strings ----
        # (Previously v0.1.2 list[str]; now v0.2 enum of 21 values per src-desktop's lock.)
        # 17a — non-string element rejected
        bad_fm_path = make_valid_intake(tasks_root, "2026-05-18-2023-bad-failure-modes")
        rec = json.loads(bad_fm_path.read_text())
        rec["failure_modes"] = ["orphan_after_crash", 42]  # int in the list
        bad_fm_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bad_fm_path)
        assert any("failure_modes" in e and "must be string" in e for e in errors), errors
        # 17b — arbitrary string NOT in enum rejected
        bad_enum_path = make_valid_intake(tasks_root, "2026-05-18-2123-bad-enum")
        rec = json.loads(bad_enum_path.read_text())
        rec["failure_modes"] = ["arbitrary_string_not_in_enum"]
        bad_enum_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bad_enum_path)
        assert any("failure_modes" in e and "not in v0.2 enum" in e for e in errors), errors
        # 17c — empty list still legal (make_valid_intake's default is [])
        empty_fm_path = make_valid_intake(tasks_root, "2026-05-18-2223-empty-fm")
        errors = task_schema.validate_task_file(empty_fm_path)
        assert not errors, f"empty failure_modes must remain legal; got {errors}"
        # 17d — multi-value from enum accepted
        multi_fm_path = make_valid_intake(tasks_root, "2026-05-18-2323-multi-fm")
        rec = json.loads(multi_fm_path.read_text())
        rec["failure_modes"] = ["orphan_after_crash", "interleave_corruption", "silent_drift"]
        multi_fm_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(multi_fm_path)
        assert not errors, f"multi-value valid enum failure_modes must pass; got {errors}"
        print("[17] failure_modes v0.2 enum enforced (non-string + arbitrary + empty + multi all correct): OK")

        # ---- NEW: email-origin task validates ----
        email_path = make_valid_intake(tasks_root, "2026-05-18-2024-email-origin")
        rec = json.loads(email_path.read_text())
        rec["raised_by"] = "email"
        rec["source_ref"] = "gmail-thread-abc123"
        email_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(email_path)
        assert not errors, f"email-origin task should validate; got {errors}"
        print("[18] email-origin task accepted (Rule 7 channel): OK")

        # ---- INVERTED for v0.1.2: Rule-8 fields are now REQUIRED ----
        # host@mesh confirmed Rule 8 + Rule 7 on 2026-05-18. Tasks missing
        # any of {dedup_hash, recipient_role, linked_to} must now FAIL.
        for missing_field in ("dedup_hash", "recipient_role", "linked_to"):
            r8_path = make_valid_intake(tasks_root, f"2026-05-18-2025-r8-missing-{missing_field}")
            rec = json.loads(r8_path.read_text())
            del rec[missing_field]
            r8_path.write_text(json.dumps(rec))
            errors = task_schema.validate_task_file(r8_path)
            assert any(f"missing required field: {missing_field}" in e for e in errors), (
                f"task missing {missing_field} should be rejected post Rule-8 confirm; got {errors}"
            )
        print("[19] Rule-8 fields REQUIRED post host-confirm (dedup_hash/recipient_role/linked_to all rejected when missing): OK")

        # ---- NEW: Rule-8 fields, when present, are type-checked ----
        rule8_path = make_valid_intake(tasks_root, "2026-05-18-2026-rule8-typed")
        rec = json.loads(rule8_path.read_text())
        rec["dedup_hash"] = "sha1:abcd1234"
        rec["recipient_role"] = "mike"
        rec["linked_to"] = ["2026-05-17-0900-other-task"]
        rule8_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(rule8_path)
        assert not errors, f"valid Rule-8 fields should pass; got {errors}"
        print("[20] Rule-8 fields type-checked when present: OK")

        # ---- NEW: recipient_role enum enforced ----
        bad_role_path = make_valid_intake(tasks_root, "2026-05-18-2027-bad-role")
        rec = json.loads(bad_role_path.read_text())
        rec["recipient_role"] = "stranger"
        bad_role_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bad_role_path)
        assert any("recipient_role" in e for e in errors), errors
        print("[21] recipient_role enum enforced: OK")

        # ---- NEW: linked_to must be list[str] ----
        bad_linked_path = make_valid_intake(tasks_root, "2026-05-18-2028-bad-linked")
        rec = json.loads(bad_linked_path.read_text())
        rec["linked_to"] = "single-string-not-list"
        bad_linked_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bad_linked_path)
        assert any("linked_to" in e and "list[str]" in e for e in errors), errors
        print("[22] linked_to must be list[str]: OK")

        # ---- NEW: dedup_hash str|null ----
        bad_hash_path = make_valid_intake(tasks_root, "2026-05-18-2029-bad-hash")
        rec = json.loads(bad_hash_path.read_text())
        rec["dedup_hash"] = 12345  # int — must reject
        bad_hash_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bad_hash_path)
        assert any("dedup_hash" in e for e in errors), errors
        print("[23] dedup_hash must be string-or-null: OK")

        # ---- NEW: bundled examples files validate / fail as advertised ----
        examples_file = _HERE / "canonical-task.examples.json"
        invalid_file = _HERE / "invalid-examples.json"
        if examples_file.exists():
            examples = json.loads(examples_file.read_text())
            assert isinstance(examples, list) and len(examples) >= 3
            for i, ex in enumerate(examples):
                errs = task_schema.validate_task_record(ex)
                assert not errs, f"canonical example #{i} should validate; got {errs}"
            print(f"[24] bundled {len(examples)} valid examples all pass: OK")
        if invalid_file.exists():
            invalids = json.loads(invalid_file.read_text())
            assert isinstance(invalids, list) and len(invalids) >= 3
            for i, wrap in enumerate(invalids):
                errs = task_schema.validate_task_record(wrap["example"])
                assert errs, f"invalid example #{i} should fail; got no errors"
            print(f"[25] bundled {len(invalids)} invalid examples all fail: OK")


        # ====================================================================
        # Milestone-4 assertions — notification_policy + research_at + back-compat.
        # Target: lift total PASS count from 25 → ≥30.
        # ====================================================================

        # [26] notification_policy — valid object with mode='inline' validates.
        np_inline_path = make_valid_intake(tasks_root, "2026-05-19-2600-np-inline")
        rec = json.loads(np_inline_path.read_text())
        rec["notification_policy"] = {"mode": "inline"}
        np_inline_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(np_inline_path)
        assert not errors, f"notification_policy mode=inline should validate; got {errors}"
        print("[26] notification_policy with mode='inline' validates: OK")

        # [27] notification_policy — kebab-case mode rejected (must be snake_case).
        np_kebab_path = make_valid_intake(tasks_root, "2026-05-19-2701-np-kebab")
        rec = json.loads(np_kebab_path.read_text())
        rec["notification_policy"] = {"mode": "roll-up-daily"}  # kebab
        np_kebab_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(np_kebab_path)
        assert any("notification_policy" in e and "must be one of" in e for e in errors), errors
        print("[27] notification_policy kebab-case mode rejected (snake_case enforced): OK")

        # [28] notification_policy — missing 'mode' subkey rejected.
        np_no_mode_path = make_valid_intake(tasks_root, "2026-05-19-2802-np-no-mode")
        rec = json.loads(np_no_mode_path.read_text())
        rec["notification_policy"] = {"on_finding_threshold": None}  # mode missing
        np_no_mode_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(np_no_mode_path)
        assert any("notification_policy" in e and "missing required field: mode" in e
                   for e in errors), errors
        print("[28] notification_policy missing 'mode' rejected: OK")

        # [29] notification_policy — extra unknown subkey rejected.
        np_extra_path = make_valid_intake(tasks_root, "2026-05-19-2903-np-extra")
        rec = json.loads(np_extra_path.read_text())
        rec["notification_policy"] = {"mode": "inline", "unknown_field": "x"}
        np_extra_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(np_extra_path)
        assert any("notification_policy" in e and "unknown" in e for e in errors), errors
        print("[29] notification_policy unknown subkey rejected: OK")

        # [30] notification_policy — non-object (string) value rejected.
        np_str_path = make_valid_intake(tasks_root, "2026-05-19-3004-np-string")
        rec = json.loads(np_str_path.read_text())
        rec["notification_policy"] = "inline"  # bare string — must be object
        np_str_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(np_str_path)
        assert any("notification_policy" in e and "must be an object" in e for e in errors), errors
        print("[30] notification_policy non-object value rejected: OK")

        # [31] notification_policy — omitted (default-by-absence path) validates.
        np_absent_path = make_valid_intake(tasks_root, "2026-05-19-3105-np-absent")
        # make_valid_intake doesn't set notification_policy → absent by default.
        errors = task_schema.validate_task_file(np_absent_path)
        assert not errors, f"absent notification_policy must validate; got {errors}"
        print("[31] notification_policy absent (default-by-absence path) validates: OK")

        # [32] research_at — valid ISO-Z accepted.
        ra_ok_path = make_valid_intake(tasks_root, "2026-05-19-3206-ra-ok")
        rec = json.loads(ra_ok_path.read_text())
        rec["research_at"] = "2026-05-20T13:00:00Z"
        ra_ok_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(ra_ok_path)
        assert not errors, f"valid research_at ISO-Z must validate; got {errors}"
        print("[32] research_at valid ISO-Z accepted: OK")

        # [33] research_at — bad format rejected.
        ra_bad_path = make_valid_intake(tasks_root, "2026-05-19-3307-ra-bad")
        rec = json.loads(ra_bad_path.read_text())
        rec["research_at"] = "2026/05/20 13:00"  # wrong format
        ra_bad_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(ra_bad_path)
        assert any("research_at" in e and "ISO" in e for e in errors), errors
        print("[33] research_at bad format rejected: OK")

        # [34] research_at — null accepted (optional + nullable).
        ra_null_path = make_valid_intake(tasks_root, "2026-05-19-3408-ra-null")
        rec = json.loads(ra_null_path.read_text())
        rec["research_at"] = None
        ra_null_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(ra_null_path)
        assert not errors, f"research_at=null must validate (optional+nullable); got {errors}"
        print("[34] research_at=null accepted: OK")

        # [35] Backward compatibility — a synthetic v0.1.3 record (no new fields)
        # must still validate under v0.1.4.
        v013_path = make_valid_intake(tasks_root, "2026-05-19-3509-v013-backcompat")
        rec = json.loads(v013_path.read_text())
        # make_valid_intake does not set notification_policy or research_at → emulates v0.1.3.
        assert "notification_policy" not in rec
        assert "research_at" not in rec
        errors = task_schema.validate_task_file(v013_path)
        assert not errors, (
            f"v0.1.3-shape record (no new fields) must validate under v0.1.4; "
            f"got {errors}"
        )
        print("[35] backward compat — v0.1.3-shape record (no new fields) validates under v0.1.4: OK")

        # [36] notification_policy enum LOCKED — accepts all 3 valid modes.
        for mode in ("inline", "roll_up_daily", "on_finding"):
            np_mode_path = make_valid_intake(
                tasks_root, f"2026-05-19-3600-np-{mode.replace('_','-')}"
            )
            rec = json.loads(np_mode_path.read_text())
            rec["notification_policy"] = {"mode": mode}
            np_mode_path.write_text(json.dumps(rec))
            errors = task_schema.validate_task_file(np_mode_path)
            assert not errors, f"mode={mode} should validate; got {errors}"
        print("[36] notification_policy accepts all 3 enum modes: OK")

        # [37] NOTIFICATION_MODES module constant present + correct shape (lockstep contract).
        assert hasattr(task_schema, "NOTIFICATION_MODES"),             "task_schema must export NOTIFICATION_MODES tuple for downstream readers."
        assert task_schema.NOTIFICATION_MODES == ("inline", "roll_up_daily", "on_finding"),             f"NOTIFICATION_MODES drift: {task_schema.NOTIFICATION_MODES!r}"
        print("[37] NOTIFICATION_MODES module constant present + correct: OK")

        print("\nALL CANONICAL SCHEMA ASSERTIONS PASSED")
        return 0
    finally:
        shutil.rmtree(work)


if __name__ == "__main__":
    sys.exit(main())
