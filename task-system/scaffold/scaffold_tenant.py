"""
Per-tenant scaffolder — creates the v0.1 task-system directory skeleton.

Spec: /mesh/BLACKBOARD/meetings/2026-05-18-task-system-redesign/v0.1-spec-host.md §2

Idempotent: rerunning on an existing tenant is a no-op for the directory tree.
Manifest is written once and preserved on rerun. A rerun with a conflicting
--tenant exits with code 2 (no-clobber).
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

_SCAFFOLDED_BY = "worker-b@mesh"
_SCHEMA_VERSION = "0.1-pending-rule-8"
_RULE_8_STATUS = "PENDING"


def tenant_root(workspace: str | os.PathLike) -> Path:
    """`<workspace>/tasks/` — the dir that contains the state subdirs."""
    return Path(workspace) / "tasks"


def _now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_manifest(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def scaffold(
    workspace: str | os.PathLike,
    dry_run: bool = False,
    tenant: str | None = None,
) -> dict:
    """
    Create tasks/<state>/ subdirs under the given workspace root and a
    structured manifest.json. Returns a summary dict.

    On a tenant conflict (manifest.json exists with a different tenant
    than the one passed), returns a summary with `manifest_conflict`
    set to a (existing_tenant, requested_tenant) tuple and performs no
    writes.
    """
    root = tenant_root(workspace)
    manifest_path = root / "manifest.json"

    # No-clobber: detect tenant conflict before doing anything else.
    existing_manifest = _read_manifest(manifest_path)
    if existing_manifest is not None and tenant is not None:
        existing_tenant = existing_manifest.get("tenant")
        if existing_tenant != tenant:
            return {
                "workspace": str(workspace),
                "tasks_root": str(root),
                "created": [],
                "existed": [],
                "dry_run": dry_run,
                "manifest": "conflict",
                "manifest_conflict": (existing_tenant, tenant),
            }

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

    if existing_manifest is not None:
        manifest_result = "preserved"
    elif dry_run:
        manifest_result = "would-create"
    else:
        manifest_data = {
            "tenant": tenant,
            "scaffolded_at": _now_z(),
            "scaffolded_by": _SCAFFOLDED_BY,
            "schema_version": _SCHEMA_VERSION,
            "subdirs": list(_STATES),
            "rule_8_status": _RULE_8_STATUS,
        }
        manifest_path.write_text(json.dumps(manifest_data, indent=2) + "\n")
        manifest_result = "created"

    return {
        "workspace": str(workspace),
        "tasks_root": str(root),
        "created": created,
        "existed": existed,
        "dry_run": dry_run,
        "manifest": manifest_result,
        "tenant": tenant,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument(
        "--workspace",
        required=True,
        help="Tenant workspace root (e.g. /mnt/clients/josh/openclaw/workspace)",
    )
    ap.add_argument(
        "--tenant",
        default=None,
        help="Tenant name recorded in manifest.json (no-clobber on rerun)",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true", help="Emit summary as JSON")
    args = ap.parse_args(argv)

    summary = scaffold(args.workspace, dry_run=args.dry_run, tenant=args.tenant)

    if summary.get("manifest") == "conflict":
        existing, requested = summary["manifest_conflict"]
        print(
            f"manifest mismatch: {existing} vs {requested}",
            file=sys.stderr,
        )
        return 2

    if args.json:
        # Drop tuple-only debug field for JSON output.
        printable = {k: v for k, v in summary.items() if k != "manifest_conflict"}
        print(json.dumps(printable, indent=2))
    else:
        action = "would create" if args.dry_run else "created"
        if summary["created"]:
            print(f"{action}: " + ", ".join(summary["created"]))
        if summary["existed"]:
            print("existed (no-op): " + ", ".join(summary["existed"]))
        print(f"manifest: {summary['manifest']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
