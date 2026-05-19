"""
Smoke tests for the substrate: scaffolder + task.json validator.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import scaffold_tenant
import task_schema


def _now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_valid_intake(tasks_root: Path, task_id: str) -> Path:
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
        "escalate_count": 0,
    }
    (d / "task.json").write_text(json.dumps(record, indent=2))
    return d / "task.json"


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="substrate-test-"))
    try:
        # ---- scaffolder ----
        summary = scaffold_tenant.scaffold(work)
        assert set(summary["created"]) == set(scaffold_tenant._STATES)
        assert (work / "tasks" / "SCHEMA.md").exists()
        print("[1] scaffolder creates all 8 states + SCHEMA.md: OK")

        # idempotent
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
        # leave recipient = None → must fail
        rule1_path.write_text(json.dumps(rule1_record))
        errors = task_schema.validate_task_file(rule1_path)
        assert any("rule-1 violation" in e for e in errors), errors
        print("[5] rule-1 cross-field check fires when only one of (auth, recipient) is set: OK")

        # ---- validator: state/location mismatch ----
        # Move valid task's task.json into shop-floor/ but leave its state=intake
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

        print("\nALL SUBSTRATE ASSERTIONS PASSED")
        return 0
    finally:
        shutil.rmtree(work)


if __name__ == "__main__":
    sys.exit(main())
