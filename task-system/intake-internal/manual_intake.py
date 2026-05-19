"""
Manual-channel intake adapter (Rule 7 raised_by="manual").

CLI tool — for operator / Mike / build-owner ad-hoc task entry that
doesn't originate from any other channel.

Usage:
    python3 manual_intake.py \
        --tenant cca \
        --workspace /mnt/clients/josh/openclaw/workspace \
        --summary "Email Acme about decking install timing" \
        --raised-by manual \
        --source-ref "josh-pad:2026-05-18-line-12" \
        [--operator-phone "+14374559131"]

`--source-ref` is required (not nullable here) because Rule 8 dedupe needs
a stable identifier to short-circuit identical re-submissions. Pass any
unique string — a notebook line, a Slack permalink, "operator-typed-2026-05-18T15:00",
etc. — the dedupe library only cares about equality.

Library entry point: `intake_manual(**kwargs)`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from intake_common import (
    ADAPTER_BY_CHANNEL,
    finalize_intake,
    now_z,
)

RAISED_BY_ALLOWED = ("manual",)


def intake_manual(
    *,
    tenant: str,
    workspace,
    summary: str,
    source_ref: str,
    raised_by: str = "manual",
    operator_phone: str | None = None,
    dedupe_module=None,
    now=None,
) -> dict:
    if raised_by not in RAISED_BY_ALLOWED:
        raise ValueError(
            f"manual intake: raised_by must be one of {RAISED_BY_ALLOWED}; "
            f"got {raised_by!r}"
        )
    if not source_ref:
        raise ValueError("manual intake: --source-ref is required")

    raised_at = now_z(now)
    return finalize_intake(
        workspace=workspace,
        tenant=tenant,
        raised_by=raised_by,
        source_ref=source_ref,
        summary=summary,
        raised_at=raised_at,
        by_actor=ADAPTER_BY_CHANNEL["manual"],
        operator_phone=operator_phone,
        dedupe_module=dedupe_module,
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--tenant", required=True)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument(
        "--raised-by", default="manual", choices=list(RAISED_BY_ALLOWED),
        help="must be 'manual' (other channels use their own adapter)",
    )
    ap.add_argument("--source-ref", required=True)
    ap.add_argument("--operator-phone", default=None)
    ap.add_argument("--json", action="store_true", help="emit result JSON")
    args = ap.parse_args(argv)

    try:
        result = intake_manual(
            tenant=args.tenant,
            workspace=args.workspace,
            summary=args.summary,
            source_ref=args.source_ref,
            raised_by=args.raised_by,
            operator_phone=args.operator_phone,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"verdict:  {result['verdict']}")
        print(f"task_id:  {result['task_id']}")
        if result.get("task_path"):
            print(f"task_path: {result['task_path']}")
        if result.get("linked_to"):
            print(f"linked_to: {', '.join(result['linked_to'])}")
    # Reject is a normal-flow outcome (idempotency), not an error.
    return 0


if __name__ == "__main__":
    sys.exit(main())
