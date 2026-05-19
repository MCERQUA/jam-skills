"""
Email-channel intake adapter — Rule 7 (`raised_by="email"`).

NO real Gmail API calls. The runtime supplies a payload dict already
extracted by the tenant agent's Gmail channel reader; this adapter
converts that payload into a v0.1.2 `task.json` and files it under
`<workspace>/tasks/intake/<task-id>/`.

Payload shape:
    {
      "gmail_thread_id":  str,           # Gmail thread id (source_ref)
      "gmail_message_id": str,           # id of the message that triggered intake
      "from_addr":        str,           # "Acme Roofing <ops@acme.example>"
      "to_addrs":         list[str],     # inbox(es) the message was delivered to
      "subject":          str,           # used to derive summary (clamped to 120)
      "snippet":          str,           # short Gmail preview
      "body_text":        str,           # full text body
    }

Returns: {"verdict": "accept"|"reject", "task_id": str, "path_written": str|None}
"""

from __future__ import annotations

from pathlib import Path

from intake_common import build_and_file


def _agent_uri(tenant: str) -> str:
    return f"{tenant}-email-intake@mesh"


def intake(payload: dict, tenant: str, workspace: Path | str) -> dict:
    """Build & file a v0.1.2 intake task from a Gmail-origin payload."""
    required = ("gmail_thread_id", "subject")
    missing = [k for k in required if k not in payload]
    if missing:
        raise ValueError(f"email intake payload missing fields: {missing}")

    return build_and_file(
        workspace=workspace,
        tenant=tenant,
        raised_by="email",
        source_ref=payload["gmail_thread_id"],
        summary=payload.get("subject", ""),
        by_uri=_agent_uri(tenant),
        operator_phone=None,
        clerk_session_id=None,
    )
