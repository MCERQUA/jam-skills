"""
Shared helpers for the three internal intake adapters (mesh, manual, brief).

The intake adapters are tools called by the tenant agent runtime. They:
  1. Build a v0.1.2-valid task.json record from a channel-specific input.
  2. Compute the dedup_hash per Rule 8.
  3. Call dedupe.scan_for_duplicates to get a verdict.
  4. Write tasks/intake/<task-id>/task.json (accept | merge | escalate),
     or skip the write entirely (reject).

All Rule 8 fields (dedup_hash, recipient_role, linked_to) are populated
here — schema is v0.1.2, post-flip, no PENDING markers.

Layout under the snapshot dir:
  intake_common.py     ← this file (helpers + finalize_intake)
  mesh_intake.py       ← channel: mesh inbox kind=task
  manual_intake.py     ← channel: CLI manual entry
  brief_intake.py      ← channel: morning-brief item
  _mock_dedupe.py      ← fallback used when real dedupe not yet landed
"""

from __future__ import annotations

import importlib
import json
import re
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

_SCHEMA_DIR = Path("/agent-desk/snapshots/2026-05-18-canonical-schema-v0.1.2")
_DEDUPE_DIR = Path("/agent-desk/snapshots/2026-05-18-intake-dedupe")

if str(_SCHEMA_DIR) not in sys.path:
    sys.path.insert(0, str(_SCHEMA_DIR))

from task_schema import validate_task_record  # noqa: E402


ADAPTER_BY_CHANNEL = {
    "mesh":   "mesh-intake-adapter@mesh",
    "manual": "manual-intake-adapter@mesh",
    "brief":  "brief-intake-adapter@mesh",
}


def now_z(now: datetime | None = None) -> str:
    """ISO-8601 UTC Z timestamp."""
    if now is None:
        now = datetime.now(timezone.utc)
    return now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_z(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


_SLUG_RE = re.compile(r"[a-z0-9]+")


def slugify(text: str, max_words: int = 4) -> str:
    words = _SLUG_RE.findall(text.lower())
    if not words:
        return "task"
    return "-".join(words[:max_words])


def shingle(text: str, n: int = 3) -> str:
    """Short fingerprint of summary for dedup_hash."""
    return slugify(text, max_words=n)


def truncate_summary(s: str, n: int = 120) -> str:
    """Trim to schema's 1–120 char window."""
    s = (s or "").strip()
    if not s:
        raise ValueError("summary cannot be empty")
    return s[:n]


def compute_dedup_hash(tenant: str, source_ref: str | None, summary: str) -> str:
    """
    Per Rule 8: dedup_hash computed from tenant + source_ref + summary-shingle.

    Format: `sha1:<tenant>:<source_ref|NONE>:<shingle>` — matches the
    canonical-task examples in v0.1.2 (the `sha1:` prefix is a versioning
    label, not an actual hex digest; downstream dedupe does fuzzy matching).
    """
    sref = source_ref if source_ref else "NONE"
    return f"sha1:{tenant}:{sref}:{shingle(summary)}"


def _task_id_exists(tasks_root: Path, task_id: str) -> bool:
    if not tasks_root.exists():
        return False
    for state_dir in tasks_root.iterdir():
        if state_dir.is_dir() and (state_dir / task_id).exists():
            return True
    return False


def make_task_id(tenant: str, summary: str, raised_at: str,
                 tasks_root: Path) -> str:
    """
    `<YYYY-MM-DD>-<HHMM>-<tenant>-<summary-slug>`; collisions get -2, -3, ...
    Matches the schema regex `^\\d{4}-\\d{2}-\\d{2}-\\d{4}-[a-z0-9][a-z0-9-]*$`.
    """
    dt = parse_z(raised_at)
    date_part = dt.strftime("%Y-%m-%d")
    time_part = dt.strftime("%H%M")
    tenant_slug = slugify(tenant, max_words=1)
    summary_slug = slugify(summary, max_words=4)
    base = f"{date_part}-{time_part}-{tenant_slug}-{summary_slug}"

    candidate = base
    seq = 2
    while _task_id_exists(tasks_root, candidate):
        candidate = f"{base}-{seq}"
        seq += 1
    return candidate


def build_intake_record(
    *,
    tenant: str,
    raised_by: str,
    source_ref: str | None,
    summary: str,
    raised_at: str,
    by_actor: str,
    task_id: str,
    operator_phone: str | None = None,
    clerk_session_id: str | None = None,
    linked_to: list[str] | None = None,
) -> dict:
    """Build a v0.1.2 task.json record for state=intake."""
    return {
        "id":                       task_id,
        "state":                    "intake",
        "raised_at":                raised_at,
        "raised_by":                raised_by,
        "source_ref":               source_ref,
        "summary":                  summary,
        "tenant":                   tenant,
        "operator_phone":           operator_phone,
        "email_authorized_by_mike": None,
        "recipient":                None,
        "state_history": [
            {"state": "intake", "at": raised_at, "by": by_actor},
        ],
        "clerk_session_id":         clerk_session_id,
        "lock_required":            True,
        "defer_count":              0,
        "failure_modes":            [],
        "dedup_hash":               compute_dedup_hash(tenant, source_ref, summary),
        "recipient_role":           None,
        "linked_to":                list(linked_to or []),
    }


def write_task_file(workspace: Path, record: dict) -> Path:
    """Write tasks/intake/<task-id>/task.json. Validates before writing."""
    errors = validate_task_record(record)
    if errors:
        raise ValueError(f"refusing to write invalid task.json: {errors}")
    task_dir = workspace / "tasks" / "intake" / record["id"]
    task_dir.mkdir(parents=True, exist_ok=True)
    path = task_dir / "task.json"
    path.write_text(json.dumps(record, indent=2) + "\n")
    return path


def write_host_question_marker(
    workspace: Path,
    task_id: str,
    verdict: str,
    matched_task_id: str | None,
    reason: str | None,
) -> Path:
    """
    On verdict=merge or escalate, drop a sibling marker so a human can see
    why this task entered intake with a `linked_to`. We do NOT mesh-send
    (per the no-external-I/O constraint) — the marker is filesystem-only.

    The tenant agent's runtime is expected to surface this marker as a
    `kind: question` mesh message to host@mesh during its next bootstrap.
    """
    task_dir = workspace / "tasks" / "intake" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    path = task_dir / "host-question.md"
    body = (
        f"# Host question — verdict={verdict}\n\n"
        f"- task_id: `{task_id}`\n"
        f"- matched_task_id: `{matched_task_id}`\n"
        f"- match_reason: {reason}\n"
        f"- written_at: {now_z()}\n\n"
        f"Per Rule 8 dedupe contract, this task is provisionally linked to "
        f"`{matched_task_id}`. The tenant agent MUST NOT promote this task "
        f"out of intake/ until host@mesh resolves the question.\n"
    )
    path.write_text(body)
    return path


def resolve_dedupe(explicit=None):
    """
    Pick a dedupe module:
      - explicit argument wins (tests inject the chosen module)
      - real `/agent-desk/snapshots/2026-05-18-intake-dedupe/dedupe.py` if
        its COMPLETION-NOTICE.md is present
      - fallback: bundled `_mock_dedupe` in this snapshot
    """
    if explicit is not None:
        return explicit
    notice = _DEDUPE_DIR / "COMPLETION-NOTICE.md"
    dedupe_py = _DEDUPE_DIR / "dedupe.py"
    if notice.exists() and dedupe_py.exists():
        if str(_DEDUPE_DIR) not in sys.path:
            sys.path.insert(0, str(_DEDUPE_DIR))
        return importlib.import_module("dedupe")
    here = Path(__file__).parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    return importlib.import_module("_mock_dedupe")


def _normalise_verdict(v) -> dict:
    """
    Accept either a dict {"verdict": str, "existing_task_id": str|None, ...}
    or an object with .verdict / .existing_task_id attributes. Returns dict.
    """
    if isinstance(v, dict):
        return {
            "verdict": v["verdict"],
            "existing_task_id": v.get("existing_task_id"),
            "match_reason": v.get("match_reason"),
        }
    return {
        "verdict": getattr(v, "verdict"),
        "existing_task_id": getattr(v, "existing_task_id", None),
        "match_reason": getattr(v, "match_reason", None),
    }


def finalize_intake(
    *,
    workspace,
    tenant: str,
    raised_by: str,
    source_ref: str | None,
    summary: str,
    raised_at: str,
    by_actor: str,
    operator_phone: str | None = None,
    clerk_session_id: str | None = None,
    dedupe_module=None,
) -> dict:
    """
    Shared post-parse path used by all three intake adapters:
        dedupe.scan_for_duplicates → write|link|skip → result dict.

    Returns:
        {
          "verdict":       "accept" | "reject" | "merge" | "escalate",
          "task_id":       str,                  # new id, or existing on reject
          "task_path":     str | None,           # None when verdict=reject
          "linked_to":     list[str],            # non-empty on merge/escalate
          "match_reason":  str | None,
          "dedup_hash":    str,                  # always populated
        }
    """
    workspace = Path(workspace)
    summary = truncate_summary(summary)
    dedupe = resolve_dedupe(dedupe_module)
    dedup_hash = compute_dedup_hash(tenant, source_ref, summary)

    raw_verdict = dedupe.scan_for_duplicates(
        workspace=workspace,
        tenant=tenant,
        source_ref=source_ref,
        summary=summary,
        dedup_hash=dedup_hash,
    )
    v = _normalise_verdict(raw_verdict)
    verdict = v["verdict"]
    existing_id = v["existing_task_id"]
    match_reason = v["match_reason"]

    if verdict == "reject":
        return {
            "verdict":      verdict,
            "task_id":      existing_id,
            "task_path":    None,
            "linked_to":    [],
            "match_reason": match_reason,
            "dedup_hash":   dedup_hash,
        }

    if verdict not in ("accept", "merge", "escalate"):
        raise ValueError(
            f"dedupe returned unknown verdict {verdict!r}; expected one of "
            "accept | reject | merge | escalate"
        )

    task_id = make_task_id(tenant, summary, raised_at, workspace / "tasks")
    linked_to = (
        [existing_id] if verdict in ("merge", "escalate") and existing_id else []
    )
    record = build_intake_record(
        tenant=tenant,
        raised_by=raised_by,
        source_ref=source_ref,
        summary=summary,
        raised_at=raised_at,
        by_actor=by_actor,
        task_id=task_id,
        operator_phone=operator_phone,
        clerk_session_id=clerk_session_id,
        linked_to=linked_to,
    )
    path = write_task_file(workspace, record)
    if verdict in ("merge", "escalate"):
        write_host_question_marker(
            workspace, task_id, verdict, existing_id, match_reason or verdict
        )
    return {
        "verdict":      verdict,
        "task_id":      task_id,
        "task_path":    str(path),
        "linked_to":    linked_to,
        "match_reason": match_reason,
        "dedup_hash":   dedup_hash,
    }
