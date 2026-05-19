"""
Internal helpers shared by the three external-channel intake adapters
(email_intake.py, sms_intake.py, voice_intake.py).

Not listed as a top-level deliverable; isolated here so each adapter stays
small and the dedupe / schema integration lives in one place.

Imports task_schema (v0.1.2) and dedupe from sibling snapshots via sys.path
manipulation rather than as packaged modules — matches the convention used
by /agent-desk/snapshots/2026-05-18-canonical-schema-v0.1.2/test_canonical_schema.py.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SCHEMA_DIR = _HERE.parent / "2026-05-18-canonical-schema-v0.1.2"
_DEDUPE_DIR = _HERE.parent / "2026-05-18-intake-dedupe"

for p in (_SCHEMA_DIR, _DEDUPE_DIR):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import task_schema  # noqa: E402  — sibling snapshot
import dedupe       # noqa: E402  — sibling snapshot

SUMMARY_MAX = 120                                   # schema §summary
_SLUG_NONALNUM = re.compile(r"[^a-z0-9]+")


def now_z() -> str:
    """UTC now in the schema's ISO-Z form (`YYYY-MM-DDTHH:MM:SSZ`)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clamp_summary(text: str | None, limit: int = SUMMARY_MAX) -> str:
    """Clamp to 1..limit chars. Empty/None becomes a single-char placeholder
    so the resulting task.json still passes the 1-char minimum."""
    s = (text or "").strip()
    if not s:
        return "(no summary)"
    return s[:limit]


def slugify(text: str | None, max_len: int = 40) -> str:
    """Lowercase + non-alnum to hyphen + trim. Never empty."""
    s = _SLUG_NONALNUM.sub("-", (text or "").lower()).strip("-")
    if not s:
        s = "task"
    return s[:max_len].rstrip("-") or "task"


def make_task_id(raised_at: str, summary: str) -> str:
    """`<YYYY-MM-DD>-<HHMM>-<slug>` per schema §id."""
    date = raised_at[:10]                           # YYYY-MM-DD
    hhmm = raised_at[11:13] + raised_at[14:16]      # HHMM
    return f"{date}-{hhmm}-{slugify(summary)}"


def intake_dir(workspace: Path, task_id: str) -> Path:
    return Path(workspace) / "tasks" / "intake" / task_id


def write_task(workspace: Path, record: dict) -> Path:
    """Write task.json under tasks/intake/<id>/. Returns the written path."""
    d = intake_dir(workspace, record["id"])
    d.mkdir(parents=True, exist_ok=True)
    p = d / "task.json"
    p.write_text(json.dumps(record, indent=2) + "\n")
    return p


def _resolve_dedupe_verdict(scan: dict) -> tuple[str, list[str], str | None]:
    """
    Normalize whatever dedupe.scan returns into (verdict, linked_to, existing_id).

    The dedupe library may return either:
      - {"verdict": "accept" | "reject", "linked_to": [...]}
      - {"verdict": ..., "linked_to": [...], "existing_id": "..."}
      - {"is_duplicate": bool, "matches": [task_id, ...]}
    Adapter is tolerant of all three shapes.
    """
    verdict = scan.get("verdict")
    if verdict is None and "is_duplicate" in scan:
        verdict = "reject" if scan["is_duplicate"] else "accept"
    if verdict not in ("accept", "reject"):
        verdict = "accept"
    linked = scan.get("linked_to") or scan.get("matches") or []
    existing_id = scan.get("existing_id")
    if existing_id is None and linked:
        existing_id = linked[0]
    return verdict, list(linked), existing_id


def build_and_file(
    *,
    workspace: Path | str,
    tenant: str,
    raised_by: str,
    source_ref: str,
    summary: str,
    by_uri: str,
    operator_phone: str | None = None,
    clerk_session_id: str | None = None,
) -> dict:
    """
    Common path used by all three adapters:

      1. Build a v0.1.2 task.json record (clamped summary, ISO-Z timestamp,
         id derived from raised_at + summary slug).
      2. Validate it against task_schema.
      3. Ask dedupe.scan whether to accept or reject.
      4. On accept: write to disk and return path.
         On reject:  return verdict only — no disk write (Rule 8 dedupe).

    Returns {verdict, task_id, path_written}. path_written is None on reject.
    """
    workspace = Path(workspace)
    raised_at = now_z()
    clamped = clamp_summary(summary)
    task_id = make_task_id(raised_at, clamped)
    dedup_hash = dedupe.compute_dedup_hash(tenant, source_ref, clamped)

    record = {
        "id": task_id,
        "state": "intake",
        "raised_at": raised_at,
        "raised_by": raised_by,
        "source_ref": source_ref,
        "summary": clamped,
        "tenant": tenant,
        "operator_phone": operator_phone,
        "email_authorized_by_mike": None,
        "recipient": None,
        "state_history": [
            {"state": "intake", "at": raised_at, "by": by_uri},
        ],
        "clerk_session_id": clerk_session_id,
        "lock_required": True,
        "defer_count": 0,
        "failure_modes": [],
        "dedup_hash": dedup_hash,
        "recipient_role": "mike",                   # Rule 7 default
        "linked_to": [],
    }

    errors = task_schema.validate_task_record(record)
    if errors:
        raise ValueError(
            f"intake adapter produced invalid v0.1.2 task.json: {errors}"
        )

    scan = dedupe.scan(workspace, record)
    verdict, linked, existing_id = _resolve_dedupe_verdict(scan)

    if verdict == "reject":
        # Rule 8: surface the link, do NOT write the duplicate.
        return {
            "verdict": "reject",
            "task_id": existing_id or task_id,
            "path_written": None,
        }

    if linked:
        record["linked_to"] = linked

    path = write_task(workspace, record)
    return {
        "verdict": "accept",
        "task_id": task_id,
        "path_written": str(path),
    }
