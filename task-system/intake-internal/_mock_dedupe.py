"""
Mock implementation of `dedupe.scan_for_duplicates` for development +
test_intake_internal.py before the real intake-dedupe snapshot lands.

Implements just enough of the Rule 8 dedupe contract to drive the four
test scenarios in `test_intake_internal.py`:

  - (tenant, source_ref) collision   → verdict=reject  (existing task_id)
  - (tenant, summary) semantic match on an open-state task
                                     → verdict=escalate
  - cross-tenant identical-summary match (sibling workspaces)
                                     → verdict=escalate
  - no match                         → verdict=accept

Scan scope:
  - <workspace>/tasks/                     (primary)
  - <workspace.parent>/*/tasks/            (sibling tenants → cross-tenant)

The real dedupe library at /agent-desk/snapshots/2026-05-18-intake-dedupe/
is expected to expose `scan_for_duplicates` with the same kwargs and a
compatible return shape. `intake_common.resolve_dedupe()` prefers the real
one when its COMPLETION-NOTICE.md is present.
"""

from __future__ import annotations

import json
from pathlib import Path

OPEN_STATES_FOR_SEMANTIC_MATCH = {
    "shop-floor", "planned", "scheduled", "today", "in-flight", "parked",
}

ALL_STATES = {
    "intake", "shop-floor", "planned", "scheduled",
    "today", "done", "in-flight", "parked",
}


def _iter_task_files(workspace: Path):
    tasks_root = workspace / "tasks"
    if not tasks_root.exists():
        return
    for state_dir in tasks_root.iterdir():
        if not state_dir.is_dir() or state_dir.name not in ALL_STATES:
            continue
        for task_dir in state_dir.iterdir():
            if not task_dir.is_dir():
                continue
            tj = task_dir / "task.json"
            if tj.exists():
                yield tj


def _load(tj: Path):
    try:
        return json.loads(tj.read_text())
    except Exception:
        return None


def _sibling_workspaces(workspace: Path):
    parent = workspace.parent
    if not parent.exists():
        return
    for child in parent.iterdir():
        if not child.is_dir() or child == workspace:
            continue
        if (child / "tasks").exists():
            yield child


def _normalised(summary: str) -> str:
    return (summary or "").strip().lower()


def scan_for_duplicates(*, workspace, tenant, source_ref, summary, dedup_hash):
    """
    Returns:
        {
          "verdict":          "accept" | "reject" | "escalate",
          "existing_task_id": str | None,
          "match_reason":     str | None,
        }
    """
    workspace = Path(workspace)
    norm = _normalised(summary)

    # (1) source_ref collision within same tenant → reject.
    if source_ref:
        for tj in _iter_task_files(workspace):
            r = _load(tj)
            if r is None:
                continue
            if r.get("tenant") == tenant and r.get("source_ref") == source_ref:
                return {
                    "verdict":          "reject",
                    "existing_task_id": r["id"],
                    "match_reason":     "source_ref_collision",
                }

    # (2) Same-tenant semantic (exact-summary) match on an open-state task.
    for tj in _iter_task_files(workspace):
        r = _load(tj)
        if r is None:
            continue
        if r.get("tenant") != tenant:
            continue
        if r.get("state") not in OPEN_STATES_FOR_SEMANTIC_MATCH:
            continue
        if _normalised(r.get("summary") or "") == norm:
            return {
                "verdict":          "escalate",
                "existing_task_id": r["id"],
                "match_reason":     "same_tenant_semantic_match",
            }

    # (3) Cross-tenant identical-summary match in any state.
    for sib in _sibling_workspaces(workspace):
        for tj in _iter_task_files(sib):
            r = _load(tj)
            if r is None:
                continue
            if r.get("tenant") == tenant:
                continue
            if _normalised(r.get("summary") or "") == norm:
                return {
                    "verdict":          "escalate",
                    "existing_task_id": r["id"],
                    "match_reason":     "cross_tenant_semantic_match",
                }

    return {
        "verdict":          "accept",
        "existing_task_id": None,
        "match_reason":     None,
    }
