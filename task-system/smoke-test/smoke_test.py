"""
E2E smoke test for JamBot task system v0.1.1.

Exercises a mock tenant through the full task lifecycle using the upstream
canonical schema validator and tenant scaffolder. Validates four scenarios
(email-, sms-, voice-origin lifecycles + parked-with-blocker) end-to-end.

Spec: /mesh/BLACKBOARD/meetings/2026-05-18-task-system-redesign/v0.1-spec-host.md
Upstream:
  - /agent-desk/snapshots/2026-05-18-canonical-schema/  (worker-a)
  - /agent-desk/snapshots/2026-05-18-tenant-scaffolder/ (worker-b)
  - /agent-desk/snapshots/2026-05-18-seam-a-poc/        (dry-run digest cron)

Exits 0 on PASS, nonzero on FAIL. Workspace is torn down unless --no-cleanup.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEMA_DIR = Path("/agent-desk/snapshots/2026-05-18-canonical-schema")
SCAFFOLD_DIR = Path("/agent-desk/snapshots/2026-05-18-tenant-scaffolder")
SEAM_A_DIR = Path("/agent-desk/snapshots/2026-05-18-seam-a-poc")

for p in (SCHEMA_DIR, SCAFFOLD_DIR, SEAM_A_DIR):
    sys.path.insert(0, str(p))

import task_schema  # noqa: E402  worker-a
import scaffold_tenant  # noqa: E402  worker-b
import blocker_digest_cron  # noqa: E402  seam-A PoC

SCENARIOS = ROOT / "scenarios"
NON_PARKED = ("email-origin", "sms-origin", "voice-origin")
TRANSITIONS = ("shop-floor", "planned", "scheduled", "today", "done")
_ISO = "%Y-%m-%dT%H:%M:%SZ"


def _now_z() -> str:
    return datetime.now(timezone.utc).strftime(_ISO)


def _log(msg: str) -> None:
    print(msg, flush=True)


class SmokeFail(Exception):
    """Smoke test assertion failure. .scenario is the failing scenario name."""

    def __init__(self, scenario: str, reason: str) -> None:
        super().__init__(f"{scenario}: {reason}")
        self.scenario = scenario
        self.reason = reason


def _assert(cond: bool, scenario: str, reason: str) -> None:
    if not cond:
        raise SmokeFail(scenario, reason)


def _read_task(task_file: Path) -> dict:
    return json.loads(task_file.read_text())


def _write_task(task_file: Path, record: dict) -> None:
    task_file.write_text(json.dumps(record, indent=2) + "\n")


def _transition(workspace: Path, scenario: str, task_id: str,
                current_state: str, new_state: str) -> Path:
    """Move <task_id> from current_state/ to new_state/, update fields, validate."""
    tasks_root = workspace / "tasks"
    old_dir = tasks_root / current_state / task_id
    new_dir = tasks_root / new_state / task_id
    _assert(old_dir.exists(), scenario, f"missing task dir before move: {old_dir}")
    _assert(not new_dir.exists(), scenario, f"target dir already populated: {new_dir}")

    shutil.move(str(old_dir), str(new_dir))

    task_file = new_dir / "task.json"
    record = _read_task(task_file)
    record["state"] = new_state
    record["state_history"].append({
        "state": new_state,
        "at": _now_z(),
        "by": "smoke-test@worker-c",
    })
    if new_state == "scheduled" and not record.get("scheduled_at"):
        record["scheduled_at"] = _now_z()
    if new_state == "done":
        record["completed_at"] = _now_z()
        record["outcome"] = "smoke-test simulated completion"
    _write_task(task_file, record)

    errors = task_schema.validate_task_file(task_file)
    _assert(not errors, scenario,
            f"validation failed after move to {new_state}: {errors}")
    return new_dir


def _run_lifecycle(workspace: Path, scenario: str) -> None:
    """Walk a non-parked scenario from intake through done."""
    src = SCENARIOS / f"{scenario}.json"
    _assert(src.is_file(), scenario, f"scenario fixture missing: {src}")

    record = _read_task(src)
    task_id = record["id"]
    intake_dir = workspace / "tasks" / "intake" / task_id
    intake_dir.mkdir(parents=True, exist_ok=True)
    _write_task(intake_dir / "task.json", record)

    errors = task_schema.validate_task_file(intake_dir / "task.json")
    _assert(not errors, scenario, f"initial validation failed: {errors}")
    _assert(record["state"] == "intake", scenario,
            f"scenario file must start in state=intake; got {record['state']!r}")
    _assert(len(record["state_history"]) == 1, scenario,
            f"scenario state_history must start with 1 entry; got {len(record['state_history'])}")

    current = "intake"
    for nxt in TRANSITIONS:
        _transition(workspace, scenario, task_id, current, nxt)
        current = nxt

    final = _read_task(workspace / "tasks" / "done" / task_id / "task.json")
    _assert(final["state"] == "done", scenario,
            f"final state != done; got {final['state']!r}")
    _assert(len(final["state_history"]) == 6, scenario,
            f"state_history length != 6 (intake + 5 transitions); "
            f"got {len(final['state_history'])}")
    _assert(final.get("completed_at") is not None, scenario,
            "completed_at not populated at done")
    _assert(final.get("outcome"), scenario, "outcome not populated at done")


def _run_parked(workspace: Path) -> None:
    scenario = "parked-with-blocker"
    src_dir = SCENARIOS / scenario
    _assert(src_dir.is_dir(), scenario, f"scenario dir missing: {src_dir}")

    task_record = _read_task(src_dir / "task.json")
    blocker_record = json.loads((src_dir / "blocker.json").read_text())
    task_id = task_record["id"]

    parked_dir = workspace / "tasks" / "parked" / task_id
    parked_dir.mkdir(parents=True, exist_ok=True)
    _write_task(parked_dir / "task.json", task_record)
    (parked_dir / "blocker.json").write_text(
        json.dumps(blocker_record, indent=2) + "\n"
    )

    errors = task_schema.validate_task_file(parked_dir / "task.json")
    _assert(not errors, scenario, f"task.json validation failed: {errors}")
    _assert(task_record["state"] == "parked", scenario,
            f"expected state=parked; got {task_record['state']!r}")
    _assert(task_record.get("parked_until") is not None, scenario,
            "parked_until must be set when state=parked")

    required = {"raised_at", "blocker_text", "last_pinged",
                "parked_until", "escalate_count", "resurface_action"}
    missing = required - set(blocker_record)
    _assert(not missing, scenario, f"blocker.json missing fields: {sorted(missing)}")

    try:
        parked_until = datetime.strptime(
            blocker_record["parked_until"], _ISO
        ).replace(tzinfo=timezone.utc)
    except (TypeError, ValueError) as exc:
        raise SmokeFail(scenario, f"parked_until did not parse: {exc}") from exc
    _assert(isinstance(parked_until, datetime), scenario,
            "parked_until parse produced non-datetime")

    # Seam-A digest dry-run integration. Confirms the cron WOULD pick up our
    # parked blocker and include task_id in the snapshot — without dispatching.
    runs_dir = workspace / "blocker-digest-runs"
    result = blocker_digest_cron.run(
        parked_root=workspace / "tasks" / "parked",
        run_record_dir=runs_dir,
        bump_extend_hours=None,
        dry_run=True,
    )
    _assert(result["dispatched"] is False, scenario,
            "digest cron must not dispatch in dry_run")
    _assert(result["due_count"] >= 1, scenario,
            f"digest expected ≥1 due blocker; got {result['due_count']}")
    snapshot_body = Path(result["snapshot"]).read_text()
    _assert(task_id in snapshot_body, scenario,
            f"digest snapshot missing task_id {task_id!r}")


def _scaffold_and_check(workspace: Path) -> None:
    scenario = "scaffold"
    summary = scaffold_tenant.scaffold(workspace, tenant="smoke-test-tenant")
    _assert(summary.get("manifest") != "conflict", scenario,
            f"manifest conflict: {summary.get('manifest_conflict')}")
    tasks_root = workspace / "tasks"
    for state in task_schema.STATES:
        _assert((tasks_root / state).is_dir(), scenario,
                f"scaffold missing state subdir: tasks/{state}/")
    _log(f"[smoke] scaffold created: {summary.get('created', [])}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Keep /tmp/smoke-* workspace after run (for inspection).",
    )
    args = ap.parse_args(argv)

    workspace = Path(tempfile.mkdtemp(prefix="smoke-"))
    _log(f"[smoke] workspace: {workspace}")

    n_passed = 0
    try:
        _scaffold_and_check(workspace)

        for scenario in NON_PARKED:
            _run_lifecycle(workspace, scenario)
            n_passed += 1
            _log(f"[smoke] {scenario}: PASS")

        _run_parked(workspace)
        n_passed += 1
        _log("[smoke] parked-with-blocker: PASS")

    except SmokeFail as exc:
        print(f"FAIL: scenario {exc.scenario}: {exc.reason}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001  surface unexpected explicitly
        print(f"FAIL: unexpected {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    finally:
        if args.no_cleanup:
            _log(f"[smoke] workspace preserved: {workspace}")
        else:
            shutil.rmtree(workspace, ignore_errors=True)

    print(f"PASS: {n_passed} scenarios")
    return 0


if __name__ == "__main__":
    sys.exit(main())
