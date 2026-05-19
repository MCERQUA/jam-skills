"""
Dedupe library — Rule 8 dedupe contract for the JamBot task system v0.1.2.

Per the v0.1.1 spec amendment, channel adapters write `task.json` to `intake/`
with `dedup_hash` populated. Before promoting `intake/ → shop-floor/`, the
tenant agent runs `scan_for_duplicates` against the existing task tree.

Exports:

    compute_dedup_hash(tenant, source_ref, summary) -> str
        Stable, deterministic hash of the intake identity. Format:
        `sha1:<tenant>:<source_ref|NONE>:<summary-shingle>`.

    scan_for_duplicates(*, workspace, tenant, source_ref, summary, dedup_hash) -> dict
        Primary Rule 8 contract (worker-b adapter signature).
        Returns: {"verdict", "existing_task_id", "match_reason"}.
        Verdict ∈ {"accept", "reject", "escalate"}.

    scan(workspace, record) -> dict
        Compatibility wrapper used by worker-c's adapters. Delegates to
        scan_for_duplicates and translates the verdict for worker-c semantics
        (accept|reject only).
        Returns: {"verdict", "linked_to", "existing_id"}.

Both interfaces are deliberately supported so the two downstream snapshots
(intake-internal, intake-external) work unchanged against the real library.

Scan scope:
  - same-tenant source_ref collision  → verdict=reject (any state including done/)
  - same-tenant exact-summary match on an open-state task
      (shop-floor, planned, scheduled, today, in-flight, parked)
    → verdict=escalate
  - cross-tenant exact-summary match in any state
    → verdict=escalate
  - otherwise → verdict=accept

Malformed task.json files are skipped — they don't crash the scan.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable


ALL_STATES: frozenset[str] = frozenset({
    "intake", "shop-floor", "planned", "scheduled",
    "today", "done", "in-flight", "parked",
})

OPEN_STATES_FOR_SEMANTIC_MATCH: frozenset[str] = frozenset({
    "shop-floor", "planned", "scheduled", "today", "in-flight", "parked",
})

_SLUG_NONALNUM = re.compile(r"[^a-z0-9]+")


def _shingle(summary: str, max_words: int = 3) -> str:
    """First 3 alpha-tokens of summary, joined by '-'. Coarse on purpose —
    semantic-match path uses exact equality; the hash shingle is for identity
    bookkeeping only."""
    s = _SLUG_NONALNUM.sub("-", (summary or "").lower()).strip("-")
    if not s:
        return "task"
    words = [w for w in s.split("-") if w]
    if not words:
        return "task"
    return "-".join(words[:max_words])


def compute_dedup_hash(
    tenant: str, source_ref: str | None, summary: str
) -> str:
    """Format: `sha1:<tenant>:<source_ref|NONE>:<shingle>`. The `sha1:`
    prefix is a version label — future hash schemes can co-exist."""
    sref = source_ref if source_ref else "NONE"
    return f"sha1:{tenant}:{sref}:{_shingle(summary)}"


def _iter_task_files(workspace: Path) -> Iterable[Path]:
    tasks_root = workspace / "tasks"
    if not tasks_root.exists() or not tasks_root.is_dir():
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


def _load(tj: Path) -> dict | None:
    try:
        data = json.loads(tj.read_text())
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def _sibling_workspaces(workspace: Path) -> Iterable[Path]:
    """Sibling tenants live under workspace.parent (per scaffold layout)."""
    parent = workspace.parent
    if not parent.exists():
        return
    for child in parent.iterdir():
        if not child.is_dir() or child == workspace:
            continue
        if (child / "tasks").is_dir():
            yield child


def _normalised(summary: str) -> str:
    return (summary or "").strip().lower()


def scan_for_duplicates(
    *,
    workspace,
    tenant: str,
    source_ref: str | None,
    summary: str,
    dedup_hash: str | None = None,
) -> dict[str, Any]:
    """Rule 8 dedupe scan.

    Args:
        workspace: tenant workspace root (the dir containing `tasks/`).
        tenant: candidate tenant name.
        source_ref: candidate's source_ref (may be None / empty).
        summary: candidate's summary text.
        dedup_hash: unused for matching today; reserved for v0.2 fuzzy match.

    Returns:
        {"verdict", "existing_task_id", "match_reason"}
        verdict ∈ {"accept", "reject", "escalate"}.
    """
    workspace = Path(workspace)
    norm = _normalised(summary)

    if source_ref:
        for tj in _iter_task_files(workspace):
            r = _load(tj)
            if r is None:
                continue
            if r.get("tenant") == tenant and r.get("source_ref") == source_ref:
                return {
                    "verdict":          "reject",
                    "existing_task_id": r.get("id"),
                    "match_reason":     "source_ref_collision",
                }

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
                "existing_task_id": r.get("id"),
                "match_reason":     "same_tenant_semantic_match",
            }

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
                    "existing_task_id": r.get("id"),
                    "match_reason":     "cross_tenant_semantic_match",
                }

    return {
        "verdict":          "accept",
        "existing_task_id": None,
        "match_reason":     None,
    }


def scan(workspace, record: dict) -> dict[str, Any]:
    """Worker-c compat wrapper. Translates dict-record contract to kwargs
    contract. Worker-c semantics: both reject and escalate map to 'reject'
    (no duplicate write either way — the matched task_id surfaces via
    linked_to so the caller can populate the field on the new intake)."""
    result = scan_for_duplicates(
        workspace=workspace,
        tenant=record.get("tenant", ""),
        source_ref=record.get("source_ref"),
        summary=record.get("summary", ""),
        dedup_hash=record.get("dedup_hash"),
    )
    verdict = result["verdict"]
    existing = result.get("existing_task_id")
    linked = [existing] if existing else []
    norm_verdict = "accept" if verdict == "accept" else "reject"
    return {
        "verdict":     norm_verdict,
        "linked_to":   linked,
        "existing_id": existing,
    }


if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="Dedupe scan against a tenant workspace")
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--tenant", required=True)
    ap.add_argument("--source-ref", default=None)
    ap.add_argument("--summary", required=True)
    args = ap.parse_args()

    dedup_hash = compute_dedup_hash(args.tenant, args.source_ref, args.summary)
    result = scan_for_duplicates(
        workspace=args.workspace,
        tenant=args.tenant,
        source_ref=args.source_ref,
        summary=args.summary,
        dedup_hash=dedup_hash,
    )
    print(json.dumps({"dedup_hash": dedup_hash, **result}, indent=2))
    sys.exit(0)
