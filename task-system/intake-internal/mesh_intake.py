"""
Mesh-channel intake adapter (Rule 7 raised_by="mesh").

Accepts a parsed mesh-inbox file: the dict produced by reading frontmatter
+ body of a `kind=task` mesh message (sender's responsibility — we do NOT
parse the file ourselves, the tenant agent's runtime does).

Required keys in the input dict:
    tenant              — target tenant (string, slug-safe)
    subject  OR body    — at least one, used to derive summary

Optional keys (all best-effort, sensible fallbacks):
    source_ref / message_id / msg_id    — if missing, derived from from+at
    from / sender                        — used in fallback source_ref
    at / sent_at / raised_at             — ISO-8601 Z; defaults to now()
    operator_phone                       — E.164, only when SMS-relayed
    clerk_session_id                     — set when bridged from voice

Behaviour:
    accept              → writes tasks/intake/<task-id>/task.json
    reject              → does NOT write; task_id is the existing dupe
    merge | escalate    → writes the new record with `linked_to` set, plus
                          a sibling host-question.md marker (no mesh-send)

Returns a dict (see intake_common.finalize_intake docstring).

This module is a tool, not an autonomous service. It does not send mesh
messages, does not poll, does not mutate state beyond the candidate
tasks/ tree of the supplied workspace.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from intake_common import (
    ADAPTER_BY_CHANNEL,
    finalize_intake,
    now_z,
    truncate_summary,
)

RAISED_BY = "mesh"


def _first(d: dict, *keys):
    for k in keys:
        v = d.get(k)
        if v is not None and v != "":
            return v
    return None


def _normalise_iso_z(value, fallback_now=None) -> str:
    if not value:
        return now_z(fallback_now)
    if isinstance(value, str) and value.endswith("Z") and "T" in value:
        return value
    try:
        text = value.replace("Z", "+00:00") if isinstance(value, str) else value
        dt = datetime.fromisoformat(text) if isinstance(text, str) else text
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, AttributeError):
        return now_z(fallback_now)


def _derive_summary(message: dict) -> str:
    subject = _first(message, "subject", "title", "summary")
    if subject:
        return truncate_summary(subject)
    body = _first(message, "body", "message", "text") or ""
    for line in body.splitlines():
        line = line.strip()
        if line:
            return truncate_summary(line)
    raise ValueError(
        "mesh intake: message has neither 'subject' nor non-empty body — "
        "cannot derive task summary"
    )


def _derive_source_ref(message: dict) -> str:
    sref = _first(message, "source_ref", "message_id", "msg_id")
    if sref:
        return str(sref)
    sender = _first(message, "from", "sender") or "unknown"
    at = _first(message, "at", "sent_at", "raised_at")
    return f"mesh:{sender}:{at}" if at else f"mesh:{sender}"


def intake_from_mesh_message(
    message: dict,
    tenant_workspace_path,
    *,
    dedupe_module=None,
    now=None,
) -> dict:
    if not isinstance(message, dict):
        raise TypeError(
            f"mesh intake: message must be a dict; got {type(message).__name__}"
        )

    tenant = message.get("tenant")
    if not tenant or not isinstance(tenant, str):
        raise ValueError("mesh intake: message missing required 'tenant' field")

    summary = _derive_summary(message)
    source_ref = _derive_source_ref(message)
    raised_at = _normalise_iso_z(
        _first(message, "at", "sent_at", "raised_at"),
        fallback_now=now,
    )

    return finalize_intake(
        workspace=tenant_workspace_path,
        tenant=tenant,
        raised_by=RAISED_BY,
        source_ref=source_ref,
        summary=summary,
        raised_at=raised_at,
        by_actor=ADAPTER_BY_CHANNEL["mesh"],
        operator_phone=_first(message, "operator_phone"),
        clerk_session_id=_first(message, "clerk_session_id"),
        dedupe_module=dedupe_module,
    )
