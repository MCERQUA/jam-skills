"""
task.json schema validator — v0.1.

Spec: /mesh/BLACKBOARD/meetings/2026-05-18-task-system-redesign/v0.1-spec-host.md §3

Cross-agent lockstep: every agent that reads/writes a task.json imports
TASK_FIELDS / STATES / SOURCES from this module. Schema bumps land here
first, all downstream tools follow.

Usage:
    from task_schema import validate_task_file, TASK_FIELDS

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

SOURCES = ("voice", "mesh", "brief", "manual", "sms")

# id: <YYYY-MM-DD>-<HHMM>-<slug>
_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}-[a-z0-9][a-z0-9-]*$")
_ISO_Z_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)

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
    "escalate_count":           ("always",        "non_neg_int"),
    "completed_at":             ("if_done",       "iso_z_or_null"),
    "outcome":                  ("if_done",       "str_or_null"),
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
    return False


def validate_task_record(record: dict) -> list[str]:
    """Return a list of human-readable errors. Empty list = valid."""
    errors: list[str] = []
    state = record.get("state")
    if not isinstance(record, dict):
        return ["task.json must be a JSON object"]

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
