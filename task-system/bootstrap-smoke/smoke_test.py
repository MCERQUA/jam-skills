"""
End-to-end smoke test — bootstrap + intake + dedupe + session-context.

Walks a mock tenant ("acme") through the full Rule 8 bootstrap milestone:
scaffold → seed prior state → load_context → SessionContext helpers →
intake adapter (accept) → intake adapter (reject via source_ref collision) →
re-bootstrap. Exits 0 on PASS, non-zero on FAIL.

Upstream snapshots wired here:
  - /agent-desk/snapshots/2026-05-19-canonical-schema-v0.1.3/ (deployed schema)
  - /agent-desk/snapshots/2026-05-18-tenant-scaffolder/        (scaffolder)
  - /agent-desk/snapshots/2026-05-18-intake-dedupe/            (dedupe)
  - /agent-desk/snapshots/2026-05-18-intake-internal/          (intake adapters)
  - /agent-desk/snapshots/2026-05-19-rule-8-bootstrap/         (worker-a)
  - /agent-desk/snapshots/2026-05-19-session-context/          (worker-b)

Spec refs:
  /mesh/BLACKBOARD/task-system/v0.1.1-spec-amendment.md  §Rule 8

CLI:
    python3 smoke_test.py            # tear down tmp workspace at end
    python3 smoke_test.py --no-cleanup
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCENARIOS = ROOT / "scenarios"

SCHEMA_DIR     = Path("/agent-desk/snapshots/2026-05-19-canonical-schema-v0.1.3")
SCAFFOLD_DIR   = Path("/agent-desk/snapshots/2026-05-18-tenant-scaffolder")
DEDUPE_DIR     = Path("/agent-desk/snapshots/2026-05-18-intake-dedupe")
INTAKE_DIR     = Path("/agent-desk/snapshots/2026-05-18-intake-internal")
BOOTSTRAP_DIR  = Path("/agent-desk/snapshots/2026-05-19-rule-8-bootstrap")
SESSION_DIR    = Path("/agent-desk/snapshots/2026-05-19-session-context")

# Point intake_common's schema resolver at v0.1.3 BEFORE it imports task_schema.
os.environ["TASK_SYSTEM_SCHEMA_DIR"] = str(SCHEMA_DIR)
os.environ["TASK_SYSTEM_DEDUPE_DIR"] = str(DEDUPE_DIR)

for p in (SCHEMA_DIR, SCAFFOLD_DIR, DEDUPE_DIR, INTAKE_DIR, BOOTSTRAP_DIR, SESSION_DIR):
    sys.path.insert(0, str(p))

import task_schema       # noqa: E402  v0.1.3
import scaffold_tenant   # noqa: E402
import dedupe            # noqa: E402
import manual_intake     # noqa: E402
import task_bootstrap    # noqa: E402  worker-a
import session_context   # noqa: E402  worker-b


TENANT = "acme"
TODAY = date(2026, 5, 19)
ISO_Z = "%Y-%m-%dT%H:%M:%SZ"

BOOTSTRAP_KEYS = (
    "tenant", "workspace", "loaded_at", "today",
    "open_tasks", "open_task_count",
    "ledger_recent", "gmail_threads", "sms_threads",
    "voice_transcript", "reflections_recent",
)

# Sources we seed into prior state. (raised_by, fixture, target_state)
SEED_TASKS = (
    ("shop-floor", "shop-floor-task.json", "shop-floor"),
    ("parked",     "parked-task.json",     "parked"),
    ("scheduled",  "scheduled-task.json",  "scheduled"),
    ("done",       "done-task.json",       "done"),
)

# Scheduled task's source_ref — reused by step 7 to fire source_ref_collision.
SCHEDULED_SOURCE_REF = "SM7c2a9f1e88b4d40a91ab0a3a2f1b8c01"
SHOP_FLOOR_GMAIL_THREAD = "gmail-thread-abc123def456"
SMS_OPERATOR_PHONE = "+14165557788"


class SmokeFail(Exception):
    def __init__(self, scenario: str, reason: str) -> None:
        super().__init__(f"{scenario}: {reason}")
        self.scenario = scenario
        self.reason = reason


def _log(msg: str) -> None:
    print(msg, flush=True)


def _assert(cond: bool, scenario: str, reason: str) -> None:
    if not cond:
        raise SmokeFail(scenario, reason)


def _now_z() -> str:
    return datetime.now(timezone.utc).strftime(ISO_Z)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def scaffold(workspace: Path) -> None:
    scenario = "scaffold"
    summary = scaffold_tenant.scaffold(workspace, tenant=TENANT)
    _assert(summary.get("manifest") != "conflict", scenario,
            f"manifest conflict: {summary.get('manifest_conflict')}")
    tasks_root = workspace / "tasks"
    for state in task_schema.STATES:
        _assert((tasks_root / state).is_dir(), scenario,
                f"scaffold missing state subdir: tasks/{state}/")
    _log(f"[smoke] scaffold created: {summary.get('created', [])}")


def seed_tasks(workspace: Path) -> None:
    """Drop one task fixture into each of shop-floor/, parked/, scheduled/, done/.
    parked/ also gets its blocker.json sibling."""
    scenario = "seed-tasks"
    for tag, fixture, state in SEED_TASKS:
        record = _read_json(SCENARIOS / fixture)
        task_id = record["id"]
        task_dir = workspace / "tasks" / state / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        _write_json(task_dir / "task.json", record)
        errors = task_schema.validate_task_file(task_dir / "task.json")
        _assert(not errors, scenario,
                f"{tag} fixture failed v0.1.3 validation: {errors}")

    # parked task needs blocker.json with parked_until in the past.
    parked_record = _read_json(SCENARIOS / "parked-task.json")
    parked_dir = workspace / "tasks" / "parked" / parked_record["id"]
    blocker = _read_json(SCENARIOS / "parked-blocker.json")
    _write_json(parked_dir / "blocker.json", blocker)

    try:
        parked_until = datetime.strptime(blocker["parked_until"], ISO_Z).replace(
            tzinfo=timezone.utc
        )
    except (TypeError, ValueError) as exc:
        raise SmokeFail(scenario, f"blocker.parked_until did not parse: {exc}") from exc
    now = datetime.now(timezone.utc)
    _assert(parked_until < now, scenario,
            f"blocker.parked_until must be in the past for resurfacing; "
            f"got {parked_until.isoformat()} (now={now.isoformat()})")


def seed_history(workspace: Path) -> None:
    """Seed voice transcript, gmail thread, sms thread, reflection, ledger."""
    # Voice transcript — <workspace>/memory/<today>-conversation.md
    transcript_src = SCENARIOS / "voice-transcript.md"
    transcript_dst = workspace / "memory" / f"{TODAY.isoformat()}-conversation.md"
    transcript_dst.parent.mkdir(parents=True, exist_ok=True)
    transcript_dst.write_text(transcript_src.read_text())

    # Gmail thread — <workspace>/gmail/threads/<thread-id>.json
    gmail_src = SCENARIOS / "gmail-thread.json"
    gmail_dst = workspace / "gmail" / "threads" / f"{SHOP_FLOOR_GMAIL_THREAD}.json"
    gmail_dst.parent.mkdir(parents=True, exist_ok=True)
    gmail_dst.write_text(gmail_src.read_text())

    # SMS thread — <workspace>/sms/conversations/<phone>.json
    sms_src = SCENARIOS / "sms-thread.json"
    sms_dst = workspace / "sms" / "conversations" / f"{SMS_OPERATOR_PHONE}.json"
    sms_dst.parent.mkdir(parents=True, exist_ok=True)
    sms_dst.write_text(sms_src.read_text())

    # Reflection — <workspace>/reflections/<today-3>-daily.md  (2026-05-16)
    refl_src = SCENARIOS / "reflection.md"
    refl_dst = workspace / "reflections" / "2026-05-16-daily.md"
    refl_dst.parent.mkdir(parents=True, exist_ok=True)
    refl_dst.write_text(refl_src.read_text())

    # Ledger — worker-a reads `.json` only, brief said `.jsonl`. Seed both:
    # the .json (loader contract) holds the array; the .jsonl is a per-line
    # mirror for downstream tools that prefer streaming.
    ledger_src = SCENARIOS / "ledger.jsonl"
    ledger_dir = workspace / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    (ledger_dir / "2026-05-18.jsonl").write_text(ledger_src.read_text())
    entries = [json.loads(line) for line in ledger_src.read_text().splitlines() if line.strip()]
    _assert(len(entries) == 3, "seed-history",
            f"ledger fixture must have 3 entries; got {len(entries)}")
    (ledger_dir / "2026-05-18.json").write_text(json.dumps(entries, indent=2) + "\n")


def assert_bootstrap_initial(workspace: Path) -> dict:
    """Step 4 — load_context after seeding; verify keys / counts / threads."""
    scenario = "load_context"
    ctx = task_bootstrap.load_context(TENANT, workspace, today=TODAY)

    missing = [k for k in BOOTSTRAP_KEYS if k not in ctx]
    _assert(not missing, scenario, f"missing keys: {missing}")

    _assert(ctx["open_task_count"] == 3, scenario,
            f"expected open_task_count == 3 (excludes done/); got {ctx['open_task_count']}")

    # done/ MUST NOT appear in open_tasks
    open_states = ctx["open_tasks"]
    _assert("done" not in open_states or not open_states.get("done"), scenario,
            "done/ leaked into open_tasks")
    _assert(len(open_states.get("shop-floor", [])) == 1, scenario,
            "expected 1 shop-floor task")
    _assert(len(open_states.get("parked", [])) == 1, scenario,
            "expected 1 parked task")
    _assert(len(open_states.get("scheduled", [])) == 1, scenario,
            "expected 1 scheduled task")
    _assert(len(open_states.get("intake", [])) == 0, scenario,
            "intake/ must be empty before step 6")

    gmail = ctx["gmail_threads"]
    sms = ctx["sms_threads"]
    _assert(len(gmail) == 1, scenario,
            f"expected 1 gmail thread (only source_refs referenced by open tasks); got {len(gmail)}")
    _assert(len(sms) == 1, scenario,
            f"expected 1 sms thread; got {len(sms)}")
    _assert(SHOP_FLOOR_GMAIL_THREAD in gmail, scenario,
            f"gmail thread {SHOP_FLOOR_GMAIL_THREAD!r} not loaded")
    _assert(SMS_OPERATOR_PHONE in sms, scenario,
            f"sms thread for {SMS_OPERATOR_PHONE!r} not loaded")

    _assert(ctx["voice_transcript"] is not None, scenario,
            "voice_transcript must be non-None when memory/<today>-conversation.md exists")
    _assert("Mike" in ctx["voice_transcript"], scenario,
            "voice_transcript content mismatch — fixture not loaded?")

    return ctx


def assert_session_helpers(workspace: Path) -> None:
    """Step 5 — wrap context in SessionContext, exercise helper methods."""
    scenario = "session_context"
    sess = session_context.start_task_session(TENANT, workspace, today=TODAY)

    _assert(len(sess.all_open_tasks) == 3, scenario,
            f"all_open_tasks length != 3; got {len(sess.all_open_tasks)}")

    matches = sess.find_tasks_by_source_ref(SCHEDULED_SOURCE_REF)
    _assert(len(matches) == 1, scenario,
            f"find_tasks_by_source_ref({SCHEDULED_SOURCE_REF!r}) returned "
            f"{len(matches)} matches; expected 1")
    _assert(matches[0]["state"] == "scheduled", scenario,
            f"matched task is in state {matches[0]['state']!r}; expected scheduled")

    thread = sess.thread_history_for(SHOP_FLOOR_GMAIL_THREAD)
    _assert(len(thread) >= 1, scenario,
            f"thread_history_for({SHOP_FLOOR_GMAIL_THREAD!r}) returned empty list")
    _assert(any("Acme" in msg.get("body", "") for msg in thread), scenario,
            "thread_history_for content mismatch — fixture not present?")

    blockers = sess.recent_blockers()
    _assert(len(blockers) == 1, scenario,
            f"recent_blockers length != 1; got {len(blockers)}")
    _assert(blockers[0]["state"] == "parked", scenario,
            f"recent_blockers[0].state != parked; got {blockers[0]['state']!r}")


def intake_step_accept(workspace: Path) -> dict:
    """Step 6 — manual_intake with a NEW summary + unique source_ref."""
    scenario = "intake_accept"
    result = manual_intake.intake_manual(
        tenant=TENANT,
        workspace=workspace,
        summary="New intake: schedule site visit for Riverside fence install",
        source_ref="josh-pad:2026-05-19-smoke-unique-step-6",
        raised_by="manual",
        dedupe_module=dedupe,
    )
    _assert(result["verdict"] == "accept", scenario,
            f"expected verdict=accept; got {result['verdict']!r} "
            f"(match_reason={result.get('match_reason')!r})")
    _assert(result["task_path"] is not None, scenario,
            "verdict=accept but task_path is None")
    task_path = Path(result["task_path"])
    _assert(task_path.exists(), scenario,
            f"task.json was not written at {task_path}")
    _assert("tasks/intake/" in str(task_path), scenario,
            f"task.json not written under tasks/intake/: {task_path}")
    errors = task_schema.validate_task_file(task_path)
    _assert(not errors, scenario,
            f"new intake task.json failed v0.1.3 validation: {errors}")
    return result


def intake_step_reject(workspace: Path) -> dict:
    """Step 7 — manual_intake with SAME source_ref as the scheduled task.
    Dedupe should fire `source_ref_collision` and return verdict=reject."""
    scenario = "intake_reject"
    files_before = list((workspace / "tasks" / "intake").iterdir())
    result = manual_intake.intake_manual(
        tenant=TENANT,
        workspace=workspace,
        summary="Decking callback (would-be dupe via source_ref collision)",
        source_ref=SCHEDULED_SOURCE_REF,
        raised_by="manual",
        dedupe_module=dedupe,
    )
    _assert(result["verdict"] == "reject", scenario,
            f"expected verdict=reject (source_ref_collision against scheduled "
            f"task); got {result['verdict']!r}")
    _assert(result["task_path"] is None, scenario,
            f"verdict=reject must NOT write a new task; got task_path={result['task_path']!r}")
    scheduled_record = _read_json(SCENARIOS / "scheduled-task.json")
    _assert(result["task_id"] == scheduled_record["id"], scenario,
            f"reject must surface existing task id {scheduled_record['id']!r}; "
            f"got {result['task_id']!r}")
    files_after = list((workspace / "tasks" / "intake").iterdir())
    _assert(len(files_after) == len(files_before), scenario,
            f"intake/ dir changed on reject (was {len(files_before)}, "
            f"now {len(files_after)})")
    return result


def assert_bootstrap_after_intake(workspace: Path) -> None:
    """Step 8 — re-bootstrap; new accepted task must show in open_tasks.intake."""
    scenario = "re_bootstrap"
    ctx = task_bootstrap.load_context(TENANT, workspace, today=TODAY)
    _assert(ctx["open_task_count"] == 4, scenario,
            f"expected open_task_count == 4 (3 seeded + 1 accepted intake); "
            f"got {ctx['open_task_count']}")
    intake_tasks = ctx["open_tasks"].get("intake", [])
    _assert(len(intake_tasks) == 1, scenario,
            f"expected 1 intake task after step 6; got {len(intake_tasks)}")
    _assert(intake_tasks[0]["state"] == "intake", scenario,
            f"intake/ task has state {intake_tasks[0]['state']!r}; expected intake")
    _assert(intake_tasks[0]["raised_by"] == "manual", scenario,
            f"intake task raised_by != manual; got {intake_tasks[0]['raised_by']!r}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--no-cleanup", action="store_true",
                    help="Keep /tmp/bootstrap-smoke-* workspace after run")
    args = ap.parse_args(argv)

    tmp_root = Path(tempfile.mkdtemp(prefix="bootstrap-smoke-"))
    workspace = tmp_root / TENANT
    workspace.mkdir(parents=True, exist_ok=True)
    _log(f"[smoke] workspace: {workspace}")

    n_passed = 0
    try:
        scaffold(workspace)
        n_passed += 1
        _log("[smoke] (1) scaffold: PASS")

        seed_tasks(workspace)
        n_passed += 1
        _log("[smoke] (2) seed prior task state: PASS")

        seed_history(workspace)
        n_passed += 1
        _log("[smoke] (3) seed history (voice/gmail/sms/reflection/ledger): PASS")

        assert_bootstrap_initial(workspace)
        n_passed += 1
        _log("[smoke] (4) load_context — keys + counts + threads + transcript: PASS")

        assert_session_helpers(workspace)
        n_passed += 1
        _log("[smoke] (5) SessionContext helpers: PASS")

        intake_step_accept(workspace)
        n_passed += 1
        _log("[smoke] (6) intake adapter — accept new summary: PASS")

        intake_step_reject(workspace)
        n_passed += 1
        _log("[smoke] (7) intake adapter — reject on source_ref collision: PASS")

        assert_bootstrap_after_intake(workspace)
        n_passed += 1
        _log("[smoke] (8) re-bootstrap — new intake task visible, count==4: PASS")

    except SmokeFail as exc:
        print(f"FAIL: scenario {exc.scenario}: {exc.reason}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: unexpected {type(exc).__name__}: {exc}", file=sys.stderr)
        import traceback; traceback.print_exc()
        return 2
    finally:
        if args.no_cleanup:
            _log(f"[smoke] workspace preserved: {tmp_root}")
        else:
            shutil.rmtree(tmp_root, ignore_errors=True)

    print(f"PASS: {n_passed} scenarios")
    return 0


if __name__ == "__main__":
    sys.exit(main())
