"""
Morning-brief intake adapter (Rule 7 raised_by="brief").

Inputs:
    item     — parsed brief item with at least:
                 {"subject":         <str>,
                  "snippet":         <str>,
                  "gmail-thread-id": <str>}
               Either key form `gmail-thread-id` or `gmail_thread_id` works.
    tenant     — target tenant (string)
    workspace  — tenant workspace path (the dir that contains tasks/)

Distinct from a later email_intake.py (raised_by="email"):
    The morning brief is a digest-surface read of a Gmail thread, not the
    raw email itself. Both share the gmail-thread-id as source_ref, but
    the `raised_by` enum disambiguates origin so they don't collide:
    Rule 8 dedupe matches on (tenant, source_ref) regardless of raised_by,
    so a brief-origin task that subsequently gets a direct email-origin
    follow-up will dedupe correctly to the same task — which is the
    intended behaviour. The `raised_by` field then preserves the audit
    trail of which surface first raised it.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from intake_common import (
    ADAPTER_BY_CHANNEL,
    finalize_intake,
    now_z,
    truncate_summary,
)

RAISED_BY = "brief"


def _derive_summary(item: dict) -> str:
    subject = (item.get("subject") or "").strip()
    if subject:
        return truncate_summary(subject)
    snippet = (item.get("snippet") or "").strip()
    if snippet:
        return truncate_summary(snippet)
    raise ValueError(
        "brief intake: item has neither 'subject' nor 'snippet' — "
        "cannot derive task summary"
    )


def _gmail_thread_id(item: dict) -> str:
    tid = item.get("gmail-thread-id") or item.get("gmail_thread_id")
    if not tid:
        raise ValueError("brief intake: item missing 'gmail-thread-id'")
    return str(tid)


def intake_from_brief_item(
    item: dict,
    tenant: str,
    workspace,
    *,
    dedupe_module=None,
    now=None,
) -> dict:
    if not isinstance(item, dict):
        raise TypeError(
            f"brief intake: item must be a dict; got {type(item).__name__}"
        )
    if not tenant or not isinstance(tenant, str):
        raise ValueError("brief intake: 'tenant' is required")

    summary = _derive_summary(item)
    source_ref = _gmail_thread_id(item)
    raised_at = now_z(now)

    return finalize_intake(
        workspace=workspace,
        tenant=tenant,
        raised_by=RAISED_BY,
        source_ref=source_ref,
        summary=summary,
        raised_at=raised_at,
        by_actor=ADAPTER_BY_CHANNEL["brief"],
        dedupe_module=dedupe_module,
    )
