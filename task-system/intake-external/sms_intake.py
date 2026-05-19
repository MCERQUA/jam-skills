"""
SMS-channel intake adapter — Rule 7 (`raised_by="sms"`).

NO real Twilio calls. The runtime supplies a payload dict already extracted
by the tenant agent's SMS channel reader; this adapter converts that payload
into a v0.1.2 `task.json` and files it under
`<workspace>/tasks/intake/<task-id>/`.

Payload shape (Twilio-like):
    {
      "sid":         str,    # Twilio Message SID (source_ref)
      "from_number": str,    # operator E.164 ("+14374559131") — operator_phone
      "to_number":   str,    # tenant inbound number
      "body":        str,    # SMS text — used to derive summary (clamped to 120)
    }

Returns: {"verdict": "accept"|"reject", "task_id": str, "path_written": str|None}
"""

from __future__ import annotations

from pathlib import Path

from intake_common import build_and_file


def _agent_uri(tenant: str) -> str:
    return f"{tenant}-sms-intake@mesh"


def intake(payload: dict, tenant: str, workspace: Path | str) -> dict:
    """Build & file a v0.1.2 intake task from an SMS-origin payload."""
    required = ("sid", "from_number", "body")
    missing = [k for k in required if k not in payload]
    if missing:
        raise ValueError(f"sms intake payload missing fields: {missing}")

    return build_and_file(
        workspace=workspace,
        tenant=tenant,
        raised_by="sms",
        source_ref=payload["sid"],
        summary=payload.get("body", ""),
        by_uri=_agent_uri(tenant),
        operator_phone=payload["from_number"],   # E.164 string
        clerk_session_id=None,
    )
