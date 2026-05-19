"""
Smoke tests for the canonical v0.1.3 schema validator (failure_modes enum).

Extends v0.1.1 test suite at
/mesh/BLACKBOARD/task-system/v0.1.1-verified/canonical-schema/test_canonical_schema.py
with:
  - Updated test [17] (failure_modes type-check error message changed from
    "list[str]" to "not in v0.2 enum").
  - Three new assertions per v0.2-spec-amendment.md §12 step 3:
      [26] reject failure_modes containing a value not in the 21-value enum
      [27] accept failure_modes: [] (empty list permitted but discouraged)
      [28] accept failure_modes: ["orphan_after_crash", "interleave_corruption"]
           (multi-value enum list)

Run with:
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
# This snapshot's task_schema lives next to the test file.
# scaffold_tenant is reused from the v0.1.1-verified bundle (tenant-scaffolder).
_BASELINE = Path("/mesh/BLACKBOARD/task-system/v0.1.1-verified/tenant-scaffolder")

sys.path.insert(0, str(_BASELINE))
sys.path.insert(0, str(_HERE))

import scaffold_tenant  # noqa: E402 — from baseline
import task_schema      # noqa: E402 — from this snapshot


def _now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_valid_intake(tasks_root: Path, task_id: str) -> Path:
    """Build a v0.1.3-canonical intake task on disk and return its path."""
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
        "failure_modes": [],  # valid: empty list permitted (discouraged but accepted)
    }
    (d / "task.json").write_text(json.dumps(record, indent=2))
    return d / "task.json"


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="canonical-schema-v0.1.3-test-"))
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

        # ---- validator: valid task ----
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
        (parked_dir / "task.json").write_text(json.dumps(parked_record))
        errors = task_schema.validate_task_file(parked_dir / "task.json")
        assert any("missing required field: parked_until" in e for e in errors), errors
        print("[7] parked state requires parked_until: OK")

        # ---- escalate_count is no longer a task field ----
        elsewhere_path = make_valid_intake(tasks_root, "2026-05-18-2014-escalate-on-task")
        rec = json.loads(elsewhere_path.read_text())
        rec["escalate_count"] = 0
        elsewhere_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(elsewhere_path)
        assert any("unknown field" in e and "escalate_count" in e for e in errors), errors
        print("[8] escalate_count on task.json rejected as unknown field: OK")

        # ---- parked-task example carries blocker.json with escalate_count ----
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

        # ---- state_history required ----
        no_hist_path = make_valid_intake(tasks_root, "2026-05-18-2016-no-history")
        rec = json.loads(no_hist_path.read_text())
        del rec["state_history"]
        no_hist_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(no_hist_path)
        assert any("missing required field: state_history" in e for e in errors), errors
        print("[10] state_history required: OK")

        # ---- state_history entry shape ----
        bad_hist_path = make_valid_intake(tasks_root, "2026-05-18-2017-bad-history")
        rec = json.loads(bad_hist_path.read_text())
        rec["state_history"] = [{"state": "intake", "at": _now_z()}]  # missing 'by'
        bad_hist_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bad_hist_path)
        assert any("state_history" in e and "by" in e for e in errors), errors
        print("[11] state_history entry shape enforced: OK")

        # ---- state_history.at must be ISO-Z ----
        bad_hist2_path = make_valid_intake(tasks_root, "2026-05-18-2018-bad-history-ts")
        rec = json.loads(bad_hist2_path.read_text())
        rec["state_history"] = [
            {"state": "intake", "at": "not-an-iso-timestamp", "by": "josh-desktop@mesh"},
        ]
        bad_hist2_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bad_hist2_path)
        assert any("state_history" in e and "ISO" in e for e in errors), errors
        print("[12] state_history.at must be ISO-Z: OK")

        # ---- clerk_session_id required (nullable) ----
        no_clerk_path = make_valid_intake(tasks_root, "2026-05-18-2019-no-clerk")
        rec = json.loads(no_clerk_path.read_text())
        del rec["clerk_session_id"]
        no_clerk_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(no_clerk_path)
        assert any("missing required field: clerk_session_id" in e for e in errors), errors
        print("[13] clerk_session_id required (nullable): OK")

        # ---- lock_required must be bool ----
        bad_lock_path = make_valid_intake(tasks_root, "2026-05-18-2020-bad-lock")
        rec = json.loads(bad_lock_path.read_text())
        rec["lock_required"] = "yes"
        bad_lock_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bad_lock_path)
        assert any("lock_required" in e and "bool" in e for e in errors), errors
        print("[14] lock_required must be bool: OK")

        # ---- lock_required=false accepted ----
        bg_path = make_valid_intake(tasks_root, "2026-05-18-2021-background-task")
        rec = json.loads(bg_path.read_text())
        rec["lock_required"] = False
        bg_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bg_path)
        assert not errors, f"background task should validate; got {errors}"
        print("[15] lock_required=false accepted for background tasks: OK")

        # ---- defer_count non-neg int ----
        bad_defer_path = make_valid_intake(tasks_root, "2026-05-18-2022-bad-defer")
        rec = json.loads(bad_defer_path.read_text())
        rec["defer_count"] = -1
        bad_defer_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bad_defer_path)
        assert any("defer_count" in e and "non-negative" in e for e in errors), errors
        print("[16] defer_count must be non-negative int: OK")

        # ---- failure_modes must be a list (UPDATED for v0.1.3) ----
        # v0.1.1 rejected ["timeout", 42] with "list[str]" in the error.
        # v0.1.3 rejects on enum membership: the string "timeout" itself is not
        # in the 21-value enum (nor is int 42), so the new error mentions enum.
        bad_fm_path = make_valid_intake(tasks_root, "2026-05-18-2023-bad-failure-modes")
        rec = json.loads(bad_fm_path.read_text())
        rec["failure_modes"] = ["timeout", 42]
        bad_fm_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bad_fm_path)
        assert any(
            "failure_modes" in e and "not in v0.2 enum" in e
            for e in errors
        ), errors
        print("[17] failure_modes rejects non-enum value (v0.1.3 enum check): OK")

        # ---- email-origin task validates ----
        email_path = make_valid_intake(tasks_root, "2026-05-18-2024-email-origin")
        rec = json.loads(email_path.read_text())
        rec["raised_by"] = "email"
        rec["source_ref"] = "gmail-thread-abc123"
        email_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(email_path)
        assert not errors, f"email-origin task should validate; got {errors}"
        print("[18] email-origin task accepted (Rule 7 channel): OK")

        # ---- Rule-8 fields optional pre-confirm ----
        rule8_omitted = make_valid_intake(tasks_root, "2026-05-18-2025-rule8-omitted")
        errors = task_schema.validate_task_file(rule8_omitted)
        assert not errors, f"task omitting Rule-8 fields must validate (PENDING); got {errors}"
        print("[19] Rule-8 fields optional pre-confirm: OK")

        # ---- Rule-8 fields type-checked when present ----
        rule8_path = make_valid_intake(tasks_root, "2026-05-18-2026-rule8-typed")
        rec = json.loads(rule8_path.read_text())
        rec["dedup_hash"] = "sha1:abcd1234"
        rec["recipient_role"] = "mike"
        rec["linked_to"] = ["2026-05-17-0900-other-task"]
        rule8_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(rule8_path)
        assert not errors, f"valid Rule-8 fields should pass; got {errors}"
        print("[20] Rule-8 fields type-checked when present: OK")

        # ---- recipient_role enum enforced ----
        bad_role_path = make_valid_intake(tasks_root, "2026-05-18-2027-bad-role")
        rec = json.loads(bad_role_path.read_text())
        rec["recipient_role"] = "stranger"
        bad_role_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bad_role_path)
        assert any("recipient_role" in e for e in errors), errors
        print("[21] recipient_role enum enforced: OK")

        # ---- linked_to list[str] ----
        bad_linked_path = make_valid_intake(tasks_root, "2026-05-18-2028-bad-linked")
        rec = json.loads(bad_linked_path.read_text())
        rec["linked_to"] = "single-string-not-list"
        bad_linked_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bad_linked_path)
        assert any("linked_to" in e and "list[str]" in e for e in errors), errors
        print("[22] linked_to must be list[str]: OK")

        # ---- dedup_hash str|null ----
        bad_hash_path = make_valid_intake(tasks_root, "2026-05-18-2029-bad-hash")
        rec = json.loads(bad_hash_path.read_text())
        rec["dedup_hash"] = 12345
        bad_hash_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(bad_hash_path)
        assert any("dedup_hash" in e for e in errors), errors
        print("[23] dedup_hash must be string-or-null: OK")

        # ---- bundled examples validate / fail as advertised ----
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

        # ============================================================
        # v0.1.3 NEW ASSERTIONS — failure_modes enum migration
        # Per v0.2-spec-amendment.md §12 step 3.
        # ============================================================

        # ---- [26] reject arbitrary string in failure_modes ----
        arb_path = make_valid_intake(tasks_root, "2026-05-19-1100-arbitrary-fm")
        rec = json.loads(arb_path.read_text())
        rec["failure_modes"] = ["arbitrary_string"]
        arb_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(arb_path)
        assert any(
            "failure_modes" in e and "not in v0.2 enum" in e and "'arbitrary_string'" in e
            for e in errors
        ), errors
        print("[26] failure_modes rejects arbitrary string (not in v0.2 enum): OK")

        # ---- [27] accept failure_modes: [] (empty list permitted) ----
        empty_path = make_valid_intake(tasks_root, "2026-05-19-1101-empty-fm")
        rec = json.loads(empty_path.read_text())
        rec["failure_modes"] = []
        empty_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(empty_path)
        assert not errors, f"empty failure_modes must be accepted; got {errors}"
        print("[27] failure_modes: [] accepted (empty list permitted, discouraged): OK")

        # ---- [28] accept multi-value enum list ----
        multi_path = make_valid_intake(tasks_root, "2026-05-19-1102-multi-fm")
        rec = json.loads(multi_path.read_text())
        rec["failure_modes"] = ["orphan_after_crash", "interleave_corruption"]
        multi_path.write_text(json.dumps(rec))
        errors = task_schema.validate_task_file(multi_path)
        assert not errors, f"multi-value enum should pass; got {errors}"
        print("[28] failure_modes accepts multi-value enum list: OK")

        # ---- [29] bonus: every single enum value validates in isolation ----
        # Catches a class-of-21 regression in one assertion.
        for i, fm in enumerate(task_schema.FAILURE_MODES):
            iso_path = make_valid_intake(tasks_root, f"2026-05-19-12{i:02d}-fm-iso")
            rec = json.loads(iso_path.read_text())
            rec["failure_modes"] = [fm]
            iso_path.write_text(json.dumps(rec))
            errors = task_schema.validate_task_file(iso_path)
            assert not errors, f"enum value {fm!r} should validate; got {errors}"
        print(f"[29] all {len(task_schema.FAILURE_MODES)} enum values validate in isolation: OK")

        print("\nALL CANONICAL SCHEMA v0.1.3 ASSERTIONS PASSED")
        return 0
    finally:
        shutil.rmtree(work)


if __name__ == "__main__":
    sys.exit(main())
