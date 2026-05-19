"""
Tests for the three internal intake adapters.

Coverage map:
    (1)  each adapter writes a v0.1.2-valid task.json
    (2)  each adapter populates dedup_hash deterministically
    (3)  same mesh payload twice → second verdict=reject + no second write
    (4)  same summary across two tenants → verdict=escalate, linked_to set

Dedupe selection:
    Imports the real `dedupe` module from intake-dedupe snapshot if its
    COMPLETION-NOTICE.md has landed, else falls back to bundled _mock_dedupe.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
SCHEMA_DIR = Path("/agent-desk/snapshots/2026-05-18-canonical-schema-v0.1.2")
SCAFFOLDER_DIR = Path("/agent-desk/snapshots/2026-05-18-tenant-scaffolder")
DEDUPE_DIR = Path("/agent-desk/snapshots/2026-05-18-intake-dedupe")

for p in (HERE, SCHEMA_DIR, SCAFFOLDER_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from task_schema import validate_task_record, validate_task_file  # noqa: E402
from scaffold_tenant import scaffold  # noqa: E402

USING_REAL_DEDUPE = (
    (DEDUPE_DIR / "COMPLETION-NOTICE.md").exists()
    and (DEDUPE_DIR / "dedupe.py").exists()
)

if USING_REAL_DEDUPE:
    if str(DEDUPE_DIR) not in sys.path:
        sys.path.insert(0, str(DEDUPE_DIR))
    import dedupe as DEDUPE_MOD  # noqa: E402
else:
    import _mock_dedupe as DEDUPE_MOD  # noqa: E402

from mesh_intake import intake_from_mesh_message  # noqa: E402
from manual_intake import intake_manual  # noqa: E402
from brief_intake import intake_from_brief_item  # noqa: E402
from intake_common import compute_dedup_hash  # noqa: E402


def _scaffold(parent: Path, tenant: str) -> Path:
    ws = parent / tenant
    ws.mkdir()
    summary = scaffold(ws, tenant=tenant)
    assert summary.get("manifest") in ("created", "preserved"), summary
    return ws


class IntakeAdapterTests(unittest.TestCase):

    def setUp(self):
        self.parent = Path(tempfile.mkdtemp(prefix="intake-test-"))
        self.ws = _scaffold(self.parent, "cca")

    def tearDown(self):
        shutil.rmtree(self.parent, ignore_errors=True)

    # ---- (1) and (2): each adapter, valid task + correct dedup_hash ----

    def test_mesh_intake_writes_valid_task_with_correct_hash(self):
        message = {
            "tenant":     "cca",
            "subject":    "Mesh handoff: domain quote for Acme Roofing",
            "from":       "host@mesh",
            "at":         "2026-05-18T15:00:00Z",
            "message_id": "msg-001",
        }
        result = intake_from_mesh_message(message, self.ws, dedupe_module=DEDUPE_MOD)
        self.assertEqual(result["verdict"], "accept", result)
        path = Path(result["task_path"])
        self.assertTrue(path.exists())
        errors = validate_task_file(path)
        self.assertEqual(errors, [], f"task.json invalid: {errors}")

        record = json.loads(path.read_text())
        self.assertEqual(record["raised_by"], "mesh")
        self.assertEqual(record["tenant"], "cca")
        self.assertEqual(record["source_ref"], "msg-001")
        self.assertEqual(record["state"], "intake")
        self.assertEqual(
            record["dedup_hash"],
            compute_dedup_hash("cca", "msg-001", record["summary"]),
        )
        # state_history seeded with intake by mesh adapter.
        self.assertEqual(len(record["state_history"]), 1)
        self.assertEqual(record["state_history"][0]["state"], "intake")
        self.assertEqual(
            record["state_history"][0]["by"], "mesh-intake-adapter@mesh"
        )
        # Rule 8 fields populated (no PENDING markers).
        self.assertIsNone(record["recipient_role"])
        self.assertEqual(record["linked_to"], [])

    def test_manual_intake_writes_valid_task_with_correct_hash(self):
        result = intake_manual(
            tenant="cca",
            workspace=self.ws,
            summary="Email Acme about decking install timing",
            source_ref="josh-pad:2026-05-18-line-12",
            dedupe_module=DEDUPE_MOD,
        )
        self.assertEqual(result["verdict"], "accept", result)
        path = Path(result["task_path"])
        errors = validate_task_file(path)
        self.assertEqual(errors, [], f"task.json invalid: {errors}")

        record = json.loads(path.read_text())
        self.assertEqual(record["raised_by"], "manual")
        self.assertEqual(record["source_ref"], "josh-pad:2026-05-18-line-12")
        self.assertEqual(
            record["dedup_hash"],
            compute_dedup_hash(
                "cca", "josh-pad:2026-05-18-line-12", record["summary"]
            ),
        )
        self.assertEqual(
            record["state_history"][0]["by"], "manual-intake-adapter@mesh"
        )

    def test_manual_intake_carries_operator_phone(self):
        result = intake_manual(
            tenant="cca",
            workspace=self.ws,
            summary="Operator escalation: missed call from Stephen",
            source_ref="josh-pad:2026-05-18-line-13",
            operator_phone="+14374559131",
            dedupe_module=DEDUPE_MOD,
        )
        self.assertEqual(result["verdict"], "accept", result)
        record = json.loads(Path(result["task_path"]).read_text())
        self.assertEqual(record["operator_phone"], "+14374559131")
        # operator_phone presence must not break Rule 1 (auth+recipient pair).
        self.assertIsNone(record["email_authorized_by_mike"])
        self.assertIsNone(record["recipient"])
        self.assertEqual(validate_task_record(record), [])

    def test_brief_intake_writes_valid_task_with_correct_hash(self):
        item = {
            "subject":         "Acme Roofing follow-up on Q3 invoice",
            "snippet":         "Acme writes asking when Q3 invoice settles.",
            "gmail-thread-id": "gmail-thread-189f3b7ac2",
        }
        result = intake_from_brief_item(item, "cca", self.ws, dedupe_module=DEDUPE_MOD)
        self.assertEqual(result["verdict"], "accept", result)
        path = Path(result["task_path"])
        errors = validate_task_file(path)
        self.assertEqual(errors, [], f"task.json invalid: {errors}")

        record = json.loads(path.read_text())
        self.assertEqual(record["raised_by"], "brief")
        self.assertEqual(record["source_ref"], "gmail-thread-189f3b7ac2")
        self.assertEqual(
            record["dedup_hash"],
            compute_dedup_hash(
                "cca", "gmail-thread-189f3b7ac2", record["summary"]
            ),
        )
        self.assertEqual(
            record["state_history"][0]["by"], "brief-intake-adapter@mesh"
        )

    def test_brief_intake_accepts_underscore_key_form(self):
        item = {
            "subject":         "Roofing crew availability for next week",
            "snippet":         "...",
            "gmail_thread_id": "gmail-thread-abc",
        }
        result = intake_from_brief_item(item, "cca", self.ws, dedupe_module=DEDUPE_MOD)
        self.assertEqual(result["verdict"], "accept", result)
        record = json.loads(Path(result["task_path"]).read_text())
        self.assertEqual(record["source_ref"], "gmail-thread-abc")

    # ---- (3) duplicate via mesh_intake → reject ----

    def test_mesh_intake_duplicate_payload_rejects_and_does_not_write(self):
        message = {
            "tenant":     "cca",
            "subject":    "Mesh handoff: domain quote for Acme Roofing",
            "from":       "host@mesh",
            "at":         "2026-05-18T15:00:00Z",
            "message_id": "msg-dup-001",
        }
        first = intake_from_mesh_message(message, self.ws, dedupe_module=DEDUPE_MOD)
        self.assertEqual(first["verdict"], "accept", first)
        first_id = first["task_id"]
        first_path = Path(first["task_path"])
        self.assertTrue(first_path.exists())

        second = intake_from_mesh_message(message, self.ws, dedupe_module=DEDUPE_MOD)
        self.assertEqual(second["verdict"], "reject", second)
        self.assertEqual(second["task_id"], first_id)
        self.assertIsNone(second["task_path"])

        intake_dir = self.ws / "tasks" / "intake"
        task_dirs = [p for p in intake_dir.iterdir() if p.is_dir()]
        self.assertEqual(
            len(task_dirs), 1,
            f"duplicate must not write a second file; found {task_dirs}",
        )

    # ---- (4) same summary across two tenants → escalate ----

    def test_cross_tenant_same_summary_escalates(self):
        ws_other = _scaffold(self.parent, "danielle")

        first = intake_manual(
            tenant="cca",
            workspace=self.ws,
            summary="Kitchen cabinet photo walkthrough upload",
            source_ref="josh-pad:2026-05-18-cca-1",
            dedupe_module=DEDUPE_MOD,
        )
        self.assertEqual(first["verdict"], "accept", first)

        second = intake_manual(
            tenant="danielle",
            workspace=ws_other,
            summary="Kitchen cabinet photo walkthrough upload",
            source_ref="josh-pad:2026-05-18-danielle-1",
            dedupe_module=DEDUPE_MOD,
        )
        self.assertEqual(second["verdict"], "escalate", second)
        path = Path(second["task_path"])
        self.assertTrue(path.exists())

        record = json.loads(path.read_text())
        self.assertEqual(record["linked_to"], [first["task_id"]])
        self.assertEqual(validate_task_record(record), [])

        marker = path.parent / "host-question.md"
        self.assertTrue(marker.exists(), "escalate must write host-question.md")
        body = marker.read_text()
        self.assertIn(first["task_id"], body)
        self.assertIn("escalate", body)


if __name__ == "__main__":
    print(f"# using real dedupe: {USING_REAL_DEDUPE} "
          f"(from {DEDUPE_DIR if USING_REAL_DEDUPE else '_mock_dedupe'})")
    unittest.main(verbosity=2)
