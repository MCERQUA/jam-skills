"""
task.json schema validator — v0.1.3 (canonical, failure_modes enum ratchet).

Baseline:
  /mesh/BLACKBOARD/task-system/v0.1.1-verified/canonical-schema/task_schema.py

v0.1.3 delta (per v0.2-spec-amendment.md §12 + Rule 9):
  - failure_modes type: list[str] → list[<enum>] with the 21-value vocabulary
    locked in /agent-desk/snapshots/2026-05-19-failure-modes-enum/failure-modes-enum-v0.2.md
  - Schema rejects arbitrary strings; accepts empty list; accepts multi-value lists.
  - All other fields unchanged from v0.1.1.

v0.1.2 (Rule 8 flip-required) is NOT included in this patch. If worker-a@mesh
has already landed v0.1.2 downstream, this patch composes additively. If v0.1.2
has NOT landed yet, apply this patch on top of v0.1.1; the Rule-8 fields stay
"pending_rule_8" (optional pre-confirm) and the failure_modes enum migration is
independent of that flip.

Cross-agent lockstep: every agent that reads/writes a task.json imports
TASK_FIELDS / STATES / SOURCES / RECIPIENT_ROLES / FAILURE_MODES from this
module. Schema bumps land here first, all downstream tools follow.

Usage:
    from task_schema import validate_task_file, TASK_FIELDS, FAILURE_MODES

    errors = validate_task_file(Path("tasks/intake/.../task.json"))
    # → list[str], empty if valid

CLI:
    python3 task_schema.py /path/to/workspace/tasks
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

STATES = (
    "intake",
    "shop-floor",
    "planned",
    "scheduled",
    "today",
    "done",
    "in-flight",
    "parked",
)

# v0.1 §3 lists "voice|mesh|brief|manual|sms". Rule 7 (folded into the Rule 8
# amendment) explicitly names "email" as a first-class channel — included so
# email-origin tasks validate without a second schema bump.
SOURCES = ("voice", "mesh", "brief", "manual", "sms", "email")

RECIPIENT_ROLES = ("mike", "operator", "client", "other")

# v0.2 Rule 9 — failure_modes vocabulary (LOCKED 2026-05-18T21:05Z).
# Source of truth:
#   /agent-desk/snapshots/2026-05-19-failure-modes-enum/failure-modes-enum-v0.2.md
# Contributors: src-desktop, josh-desktop, bun-desktop, danielle-desktop.
# Closed at 21 values for v0.2. New values require kind: decision + Mike approval
# at the v0.3 ratchet.
FAILURE_MODES = (
    "blocker_source_split_brain",
    "completion_signal_ambiguous",
    "cross_session_artifact_handoff_blindness",
    "deadlock_on_missing_signal",
    "decision_matrix_skipped_failure_mode_first_pass",
    "false_negative_active_state",
    "false_positive_active_state",
    "in_flight_orphan",
    "interleave_corruption",
    "latency_budget_exceeded",
    "orphan_after_crash",
    "outbound_recipient_drift",
    "parallel_shift_writer_race",
    "parked_without_clock",
    "permission_drift_breaks_protocol_channel",
    "schema_field_unenforced",
    "sentinel_traps_silent_skip",
    "silent_drift",
    "transition_illegal",
    "voice_agent_is_executor_but_no_task_record",
    "worker_self_report_passed_but_unverified",
)

# id: <YYYY-MM-DD>-<HHMM>-<slug>
_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}-[a-z0-9][a-z0-9-]*$")
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

TASK_FIELDS = {
    # field_name: (required_when, type_check)
    "id":                       ("always",        "id"),
    "state":                    ("always",        "state"),
    "raised_at":                ("always",        "iso_z"),
    "raised_by":                ("always",        "source"),
    "source_ref":               ("always",        "str_or_null"),
    "summary":                  ("always",        "summary"),
    "tenant":                   ("always",        "str"),
    "operator_phone":           ("always",        "str_or_null"),
    "email_authorized_by_mike": ("always",        "iso_z_or_null"),
    "recipient":                ("always",        "str_or_null"),
    "scheduled_at":             ("if_scheduled",  "iso_z_or_null"),
    "parked_until":             ("if_parked",     "iso_z_or_null"),
    "completed_at":             ("if_done",       "iso_z_or_null"),
    "outcome":                  ("if_done",       "str_or_null"),
    # bun-desktop: append-only state-transition audit trail.
    "state_history":            ("always",        "state_history"),
    # src-desktop: voice-lane / scheduler fields.
    "clerk_session_id":         ("always",        "str_or_null"),
    "lock_required":            ("always",        "bool"),
    "defer_count":              ("always",        "non_neg_int"),
    # v0.1.3: failure_modes is now enum-constrained (was list_of_str at v0.1.1).
    "failure_modes":            ("always",        "list_of_failure_modes_enum"),
    # Rule 8 amendment — PENDING_HOST_CONFIRM at v0.1.1. The v0.1.2 ratchet
    # (worker-a@mesh, separate from this v0.1.3 ratchet) flips these to required.
    # This patch leaves them as "pending_rule_8" so it composes additively whether
    # v0.1.2 has landed yet or not.
    "dedup_hash":               ("pending_rule_8", "str_or_null"),
    "recipient_role":           ("pending_rule_8", "recipient_role_or_null"),
    "linked_to":                ("pending_rule_8", "list_of_str"),
}


def _check_type(value, kind: str) -> str | None:
    if kind == "id":
        if not isinstance(value, str) or not _ID_RE.match(value):
            return f"id must match <YYYY-MM-DD>-<HHMM>-<slug>; got {value!r}"
    elif kind == "state":
        if value not in STATES:
            return f"state must be one of {STATES}; got {value!r}"
    elif kind == "iso_z":
        if not isinstance(value, str) or not _ISO_Z_RE.match(value):
            return f"must be ISO-8601 UTC ending in Z; got {value!r}"
    elif kind == "iso_z_or_null":
        if value is None:
            return None
        if not isinstance(value, str) or not _ISO_Z_RE.match(value):
            return f"must be ISO-8601 UTC ending in Z or null; got {value!r}"
    elif kind == "source":
        if value not in SOURCES:
            return f"raised_by must be one of {SOURCES}; got {value!r}"
    elif kind == "summary":
        if not isinstance(value, str) or not (1 <= len(value) <= 120):
            return f"summary must be 1–120 chars; got len={len(value) if isinstance(value, str) else 'N/A'}"
    elif kind == "str":
        if not isinstance(value, str) or not value:
            return f"must be non-empty string; got {value!r}"
    elif kind == "str_or_null":
        if value is not None and not isinstance(value, str):
            return f"must be string or null; got {type(value).__name__}"
    elif kind == "non_neg_int":
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            return f"must be non-negative int; got {value!r}"
    elif kind == "bool":
        if not isinstance(value, bool):
            return f"must be bool; got {type(value).__name__}"
    elif kind == "list_of_str":
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            return f"must be list[str]; got {value!r}"
    elif kind == "list_of_failure_modes_enum":
        # v0.1.3 Rule 9: closed enum of 21 values.
        if not isinstance(value, list):
            return f"failure_modes must be list[<enum>]; got {type(value).__name__}"
        bad = [x for x in value if x not in FAILURE_MODES]
        if bad:
            return (
                f"failure_modes contains value(s) not in v0.2 enum: {bad!r}. "
                f"Allowed (21): {list(FAILURE_MODES)}"
            )
    elif kind == "state_history":
        if not isinstance(value, list):
            return f"state_history must be a list; got {type(value).__name__}"
        for i, entry in enumerate(value):
            if not isinstance(entry, dict):
                return f"state_history[{i}] must be an object; got {type(entry).__name__}"
            missing = {"state", "at", "by"} - set(entry)
            if missing:
                return f"state_history[{i}] missing fields: {sorted(missing)}"
            extra = set(entry) - {"state", "at", "by"}
            if extra:
                return f"state_history[{i}] unknown fields: {sorted(extra)}"
            if entry["state"] not in STATES:
                return f"state_history[{i}].state must be one of {STATES}; got {entry['state']!r}"
            if not isinstance(entry["at"], str) or not _ISO_Z_RE.match(entry["at"]):
                return f"state_history[{i}].at must be ISO-8601 UTC Z; got {entry['at']!r}"
            if not isinstance(entry["by"], str) or not entry["by"]:
                return f"state_history[{i}].by must be non-empty string; got {entry['by']!r}"
    elif kind == "recipient_role_or_null":
        if value is None:
            return None
        if value not in RECIPIENT_ROLES:
            return f"recipient_role must be one of {RECIPIENT_ROLES} or null; got {value!r}"
    return None


def _required(field: str, state: str) -> bool:
    when, _ = TASK_FIELDS[field]
    if when == "always":
        return True
    if when == "if_scheduled":
        return state in ("scheduled", "today", "done")
    if when == "if_parked":
        return state == "parked"
    if when == "if_done":
        return state == "done"
    if when == "pending_rule_8":
        return False
    return False


def validate_task_record(record: dict) -> list[str]:
    """Return a list of human-readable errors. Empty list = valid."""
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["task.json must be a JSON object"]
    state = record.get("state")

    unknown = set(record) - set(TASK_FIELDS)
    if unknown:
        errors.append(f"unknown field(s): {sorted(unknown)}")

    for field, (_, kind) in TASK_FIELDS.items():
        if field not in record:
            if _required(field, state):
                errors.append(f"missing required field: {field}")
            continue
        err = _check_type(record[field], kind)
        if err is not None:
            errors.append(f"{field}: {err}")

    # Rule 1 cross-field check: any outbound-bearing field requires both
    # email_authorized_by_mike AND recipient.
    auth = record.get("email_authorized_by_mike")
    rcpt = record.get("recipient")
    if (auth is None) != (rcpt is None):
        errors.append(
            "rule-1 violation: email_authorized_by_mike and recipient must "
            "BOTH be set or BOTH be null"
        )

    return errors


def validate_task_file(path: Path) -> list[str]:
    try:
        record = json.loads(path.read_text())
    except FileNotFoundError:
        return [f"file not found: {path}"]
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"]
    return validate_task_record(record)


def validate_tree(tasks_root: Path) -> dict:
    """
    Walk tasks/<state>/<task-id>/task.json under tasks_root.
    Return {file → [errors]} for invalid files only, plus counts.
    """
    invalid: dict[str, list[str]] = {}
    total = 0
    for task_json in tasks_root.rglob("task.json"):
        total += 1
        errors = validate_task_file(task_json)
        if errors:
            invalid[str(task_json)] = errors

        # Cross-check: task is filed under the directory matching its state
        try:
            record = json.loads(task_json.read_text())
        except Exception:
            continue
        declared_state = record.get("state")
        parent_state = task_json.parent.parent.name
        if declared_state and parent_state in STATES and declared_state != parent_state:
            invalid.setdefault(str(task_json), []).append(
                f"state/location mismatch: state={declared_state} "
                f"but filed under tasks/{parent_state}/"
            )

    return {
        "tasks_root": str(tasks_root),
        "total_tasks": total,
        "invalid_count": len(invalid),
        "invalid": invalid,
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument(
        "target",
        help="Path to a single task.json OR a tasks/ root directory",
    )
    ap.add_argument("--json", action="store_true", help="Emit report as JSON")
    args = ap.parse_args(argv)

    target = Path(args.target)
    if target.is_file():
        errors = validate_task_file(target)
        report = {
            "tasks_root": None,
            "total_tasks": 1,
            "invalid_count": 1 if errors else 0,
            "invalid": {str(target): errors} if errors else {},
        }
    else:
        report = validate_tree(target)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        if report["invalid_count"] == 0:
            print(f"{report['total_tasks']} task(s) checked — all valid.")
        else:
            print(
                f"{report['total_tasks']} task(s) checked — "
                f"{report['invalid_count']} invalid:"
            )
            for path, errs in report["invalid"].items():
                print(f"  {path}")
                for e in errs:
                    print(f"    - {e}")
    return 1 if report["invalid_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
