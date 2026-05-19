"""
Per-tenant scaffolder — creates the v0.1 task-system directory skeleton.

Spec: /mesh/BLACKBOARD/meetings/2026-05-18-task-system-redesign/v0.1-spec-host.md §2

Idempotent: rerunning on an existing tenant is a no-op (touches mtimes only).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# v0.1 spec §2 — directory list. Treat this as the schema; downstream tools
# (validator, brief reader, digest cron) import _STATES so adding a state
# here is a one-line surface change.
_STATES = [
    "intake",
    "shop-floor",
    "planned",
    "scheduled",
    "today",
    "done",
    "in-flight",
    "parked",
]


def tenant_root(workspace: str | os.PathLike) -> Path:
    """`<workspace>/tasks/` — the dir that contains the state subdirs."""
    return Path(workspace) / "tasks"


def scaffold(workspace: str | os.PathLike, dry_run: bool = False) -> dict:
    """
    Create tasks/<state>/ subdirs under the given workspace root.
    Returns a summary of what was created vs. what already existed.
    """
    root = tenant_root(workspace)
    created: list[str] = []
    existed: list[str] = []
    for state in _STATES:
        d = root / state
        if d.exists():
            existed.append(state)
        else:
            if not dry_run:
                d.mkdir(parents=True, exist_ok=True)
                # Drop a .gitkeep so empty states aren't lost by git
                (d / ".gitkeep").touch()
            created.append(state)

    schema_pointer = root / "SCHEMA.md"
    if not schema_pointer.exists() and not dry_run:
        schema_pointer.write_text(
            "# Task-system schema reference\n\n"
            "Spec: /mesh/BLACKBOARD/meetings/2026-05-18-task-system-redesign/v0.1-spec-host.md\n"
            "States in this tree: " + ", ".join(_STATES) + "\n"
            f"Scaffolded: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        )

    return {
        "workspace": str(workspace),
        "tasks_root": str(root),
        "created": created,
        "existed": existed,
        "dry_run": dry_run,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument(
        "--workspace",
        required=True,
        help="Tenant workspace root (e.g. /mnt/clients/josh/openclaw/workspace)",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true", help="Emit summary as JSON")
    args = ap.parse_args(argv)

    summary = scaffold(args.workspace, dry_run=args.dry_run)
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        action = "would create" if args.dry_run else "created"
        if summary["created"]:
            print(f"{action}: " + ", ".join(summary["created"]))
        if summary["existed"]:
            print(f"existed (no-op): " + ", ".join(summary["existed"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
