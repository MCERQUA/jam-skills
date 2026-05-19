"""
Tests for dedupe.py — Rule 8 dedupe contract.

Covers both interfaces (scan_for_duplicates + the scan() compat wrapper) and
the cross-tenant scan path against sibling workspaces.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dedupe


def _now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_task(tenants_root: Path, tenant: str, state: str, task_id: str,
                source_ref: str | None, summary: str) -> Path:
    """Write a minimal task.json under <tenants_root>/<tenant>/tasks/<state>/<task_id>/."""
    d = tenants_root / tenant / "tasks" / state / task_id
    d.mkdir(parents=True, exist_ok=True)
    record = {
        "id": task_id,
        "tenant": tenant,
        "state": state,
        "source_ref": source_ref,
        "summary": summary,
    }
    (d / "task.json").write_text(json.dumps(record))
    return d / "task.json"


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="dedupe-test-"))
    try:
        tenants_root = work / "tenants"

        # ---- [1] compute_dedup_hash is deterministic ----
        h1 = dedupe.compute_dedup_hash("josh", "gmail-abc", "Acme roofing quote")
        h2 = dedupe.compute_dedup_hash("josh", "gmail-abc", "Acme roofing quote")
        assert h1 == h2, f"hash should be deterministic; got {h1!r} vs {h2!r}"
        print(f"[1] compute_dedup_hash deterministic: OK  ({h1})")

        # ---- [2] tenant differentiates hash ----
        h_josh = dedupe.compute_dedup_hash("josh", "gmail-abc", "Some summary")
        h_src  = dedupe.compute_dedup_hash("src",  "gmail-abc", "Some summary")
        assert h_josh != h_src, "tenant must affect hash"
        print("[2] tenant differentiates hash: OK")

        # ---- [3] source_ref differentiates hash ----
        h_a = dedupe.compute_dedup_hash("josh", "gmail-aaa", "Same summary")
        h_b = dedupe.compute_dedup_hash("josh", "gmail-bbb", "Same summary")
        assert h_a != h_b, "source_ref must affect hash"
        print("[3] source_ref differentiates hash: OK")

        # ---- [4] empty source_ref produces stable hash ----
        h_none1 = dedupe.compute_dedup_hash("josh", None, "Same summary")
        h_none2 = dedupe.compute_dedup_hash("josh", "",   "Same summary")
        assert h_none1 == h_none2, "None and '' source_ref must collapse to the same hash"
        assert "NONE" in h_none1, f"empty source_ref should produce NONE marker; got {h_none1}"
        print("[4] empty source_ref produces stable hash: OK")

        # ---- [5] scan returns accept on empty workspace ----
        josh_ws = tenants_root / "josh"
        josh_ws.mkdir(parents=True, exist_ok=True)
        (josh_ws / "tasks").mkdir(exist_ok=True)
        r = dedupe.scan_for_duplicates(
            workspace=josh_ws, tenant="josh",
            source_ref="gmail-fresh", summary="brand-new summary",
            dedup_hash=dedupe.compute_dedup_hash("josh", "gmail-fresh", "brand-new summary"),
        )
        assert r["verdict"] == "accept", r
        assert r["existing_task_id"] is None
        print("[5] scan returns accept on empty workspace: OK")

        # ---- [6] source_ref collision (same tenant, ANY state) → reject ----
        _write_task(tenants_root, "josh", "scheduled",
                    "2026-05-18-1000-pre-existing-1",
                    "gmail-collide", "First quote on Tuesday")
        r = dedupe.scan_for_duplicates(
            workspace=josh_ws, tenant="josh",
            source_ref="gmail-collide", summary="Completely different summary",
            dedup_hash="ignored",
        )
        assert r["verdict"] == "reject", r
        assert r["existing_task_id"] == "2026-05-18-1000-pre-existing-1", r
        assert r["match_reason"] == "source_ref_collision"
        print("[6] source_ref collision (same tenant) → reject: OK")

        # ---- [7] semantic match on same-tenant open state → escalate ----
        _write_task(tenants_root, "josh", "shop-floor",
                    "2026-05-18-1100-acme-quote",
                    "gmail-other-id", "Acme roofing quote")
        r = dedupe.scan_for_duplicates(
            workspace=josh_ws, tenant="josh",
            source_ref="gmail-different-id-from-above",
            summary="Acme roofing quote",
            dedup_hash="ignored",
        )
        assert r["verdict"] == "escalate", r
        assert r["existing_task_id"] == "2026-05-18-1100-acme-quote", r
        assert r["match_reason"] == "same_tenant_semantic_match"
        print("[7] same-tenant semantic match (shop-floor) → escalate: OK")

        # ---- [8] semantic match against done/ does NOT escalate ----
        _write_task(tenants_root, "josh", "done",
                    "2026-05-18-1200-old-done-task",
                    "gmail-old", "An ancient finished task")
        r = dedupe.scan_for_duplicates(
            workspace=josh_ws, tenant="josh",
            source_ref="gmail-new-source",
            summary="An ancient finished task",
            dedup_hash="ignored",
        )
        assert r["verdict"] == "accept", f"done-state semantic match should not escalate; got {r}"
        print("[8] semantic match against done/ does NOT escalate: OK")

        # ---- [9] cross-tenant exact-summary match → escalate ----
        _write_task(tenants_root, "src", "shop-floor",
                    "2026-05-18-1300-src-pre-existing",
                    "twilio-SM-foo", "Identical summary cross-tenant")
        r = dedupe.scan_for_duplicates(
            workspace=josh_ws, tenant="josh",
            source_ref="gmail-josh-new",
            summary="Identical summary cross-tenant",
            dedup_hash="ignored",
        )
        assert r["verdict"] == "escalate", r
        assert r["existing_task_id"] == "2026-05-18-1300-src-pre-existing"
        assert r["match_reason"] == "cross_tenant_semantic_match"
        print("[9] cross-tenant semantic match → escalate: OK")

        # ---- [10] malformed task.json is skipped, doesn't crash ----
        garbage_dir = tenants_root / "josh" / "tasks" / "intake" / "garbage-task"
        garbage_dir.mkdir(parents=True, exist_ok=True)
        (garbage_dir / "task.json").write_text("{ this is not valid JSON")
        # also drop an empty file under intake
        empty_dir = tenants_root / "josh" / "tasks" / "intake" / "empty-task"
        empty_dir.mkdir(parents=True, exist_ok=True)
        (empty_dir / "task.json").write_text("")
        r = dedupe.scan_for_duplicates(
            workspace=josh_ws, tenant="josh",
            source_ref="gmail-after-garbage",
            summary="totally unrelated novel summary",
            dedup_hash="ignored",
        )
        assert r["verdict"] == "accept", f"scan should skip malformed; got {r}"
        print("[10] malformed task.json skipped (no crash): OK")

        # ---- [11] compat wrapper scan(workspace, record) — accept path ----
        record_ok = {
            "tenant": "josh",
            "source_ref": "gmail-fresh-record",
            "summary": "Unique summary for compat test",
            "dedup_hash": "anything",
        }
        result = dedupe.scan(josh_ws, record_ok)
        assert result["verdict"] == "accept", result
        assert result["linked_to"] == []
        assert result["existing_id"] is None
        print("[11] scan() compat wrapper — accept path: OK")

        # ---- [12] compat wrapper — reject path (source_ref collision) ----
        record_collide = {
            "tenant": "josh",
            "source_ref": "gmail-collide",      # already used in test [6]
            "summary": "Doesn't matter",
            "dedup_hash": "anything",
        }
        result = dedupe.scan(josh_ws, record_collide)
        assert result["verdict"] == "reject", result
        assert result["existing_id"] == "2026-05-18-1000-pre-existing-1"
        assert result["linked_to"] == ["2026-05-18-1000-pre-existing-1"]
        print("[12] scan() compat wrapper — reject path: OK")

        # ---- [13] compat wrapper — escalate normalises to reject ----
        record_escalate = {
            "tenant": "josh",
            "source_ref": "gmail-completely-fresh",
            "summary": "Acme roofing quote",   # matches test [7]
            "dedup_hash": "anything",
        }
        result = dedupe.scan(josh_ws, record_escalate)
        # worker-c semantics: both reject and escalate become "reject" (no duplicate write)
        assert result["verdict"] == "reject", result
        assert result["existing_id"] == "2026-05-18-1100-acme-quote"
        assert result["linked_to"] == ["2026-05-18-1100-acme-quote"]
        print("[13] scan() compat wrapper — escalate normalises to reject: OK")

        # ---- [14] missing tasks/ dir under workspace — scan returns accept ----
        empty_ws = work / "empty-tenant"
        empty_ws.mkdir()
        r = dedupe.scan_for_duplicates(
            workspace=empty_ws, tenant="empty-tenant",
            source_ref="anything", summary="anything",
            dedup_hash="ignored",
        )
        assert r["verdict"] == "accept", r
        print("[14] missing tasks/ dir under workspace → accept: OK")

        # ---- [15] cross-tenant scan ignores done/ in sibling (only matches in open states? — actually we accept ANY state for cross-tenant per spec) ----
        # Verify: cross-tenant match in DONE state of sibling tenant still escalates.
        _write_task(tenants_root, "danielle", "done",
                    "2026-05-18-1400-old-done-cross",
                    "voice-old", "Identical summary cross-tenant done")
        r = dedupe.scan_for_duplicates(
            workspace=josh_ws, tenant="josh",
            source_ref="gmail-yet-another",
            summary="Identical summary cross-tenant done",
            dedup_hash="ignored",
        )
        assert r["verdict"] == "escalate", r
        assert r["match_reason"] == "cross_tenant_semantic_match"
        print("[15] cross-tenant matches even in done/ state: OK")

        print("\nALL DEDUPE ASSERTIONS PASSED")
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
