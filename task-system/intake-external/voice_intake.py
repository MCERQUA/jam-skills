"""
Voice-channel intake adapter — Rule 7 (`raised_by="voice"`).

NO real OVU/OpenVoiceUI calls. The runtime supplies a payload dict already
extracted by the tenant agent's voice transcript reader; this adapter
converts that payload into a v0.1.2 `task.json` and files it under
`<workspace>/tasks/intake/<task-id>/`.

Payload shape:
    {
      "session_id":          str,    # OVU voice-session id
      "clerk_session_id":    str,    # Clerk session bound to the transcript
      "transcript_line":     str,    # raw text of the utterance
      "line_index":          int,    # zero-based line number within session
      "turn_intent_summary": str,    # tenant agent's distilled intent (summary)
    }

source_ref is composed as `<session_id>:line:<line_index>` so two utterances
in the same session don't collide on dedupe.

Returns: {"verdict": "accept"|"reject", "task_id": str, "path_written": str|None}
"""

from __future__ import annotations

from pathlib import Path

from intake_common import build_and_file


def _agent_uri(tenant: str) -> str:
    return f"{tenant}-voice@mesh"


def _source_ref(session_id: str, line_index: int) -> str:
    return f"{session_id}:line:{line_index}"


def intake(payload: dict, tenant: str, workspace: Path | str) -> dict:
    """Build & file a v0.1.2 intake task from a voice-origin payload."""
    required = ("session_id", "clerk_session_id", "line_index", "turn_intent_summary")
    missing = [k for k in required if k not in payload]
    if missing:
        raise ValueError(f"voice intake payload missing fields: {missing}")

    return build_and_file(
        workspace=workspace,
        tenant=tenant,
        raised_by="voice",
        source_ref=_source_ref(payload["session_id"], int(payload["line_index"])),
        summary=payload.get("turn_intent_summary", ""),
        by_uri=_agent_uri(tenant),
        operator_phone=None,
        clerk_session_id=payload["clerk_session_id"],
    )
