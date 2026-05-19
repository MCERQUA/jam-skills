"""
Tests for the three external-channel intake adapters (email/sms/voice).

Coverage (named assertions, all printed [n]/...):

  [1]  email adapter: builds a v0.1.2-valid task.json (round-trips schema validator).
  [2]  sms   adapter: builds a v0.1.2-valid task.json.
  [3]  voice adapter: builds a v0.1.2-valid task.json.
  [4]  raised_by per spec enum: email→"email", sms→"sms", voice→"voice".
  [5]  source_ref per spec:     gmail_thread_id / sid / "<session>:line:<n>".
  [6]  email adapter clamps a 200-char subject to summary length 120 (schema max).
  [7]  sms   adapter sets operator_phone to the E.164 from_number.
  [8]  voice adapter sets clerk_session_id from the payload.
  [9]  re-running identical email payload → second verdict=reject, no second file.
  [10] re-running identical sms   payload → second verdict=reject, no second file.
  [11] re-running identical voice payload → second verdict=reject, no second file.
  [12] every accepted task.json was filed under tasks/intake/<task-id>/.

Run:  python3 test_intake_external.py     (exit 0 = pass)
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SCHEMA_DIR = _HERE.parent / "2026-05-18-canonical-schema-v0.1.2"
_SCAFFOLD_DIR = _HERE.parent / "2026-05-18-tenant-scaffolder"
_DEDUPE_DIR = _HERE.parent / "2026-05-18-intake-dedupe"

for p in (_SCHEMA_DIR, _SCAFFOLD_DIR, _DEDUPE_DIR, _HERE):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import task_schema       # noqa: E402
import scaffold_tenant   # noqa: E402
import email_intake      # noqa: E402
import sms_intake        # noqa: E402
import voice_intake      # noqa: E402


def _scaffold(tenant: str) -> Path:
    """Create a fresh workspace with tasks/<state>/ subdirs."""
    work = Path(tempfile.mkdtemp(prefix=f"intake-{tenant}-"))
    scaffold_tenant.scaffold(work, tenant=tenant)
    return work


def _email_payload() -> dict:
    return {
        "gmail_thread_id":  "gmail-thread-189f3b7ac2",
        "gmail_message_id": "gmail-msg-aa11bb22",
        "from_addr":        "Acme Roofing <ops@acme.example>",
        "to_addrs":         ["cca-inbox@mike.example"],
        "subject":          "Acme Roofing asked for an updated domain + hosting quote",
        "snippet":          "Hi Mike, can you send us a fresh quote …",
        "body_text":        "Hi Mike,\n\nWe'd like a fresh quote on domain + hosting. Thanks.",
    }


def _sms_payload() -> dict:
    return {
        "sid":         "SM7c2a9f1e88b4d40a91ab0a3a2f1b8c01",
        "from_number": "+14374559131",
        "to_number":   "+18005551212",
        "body":        "Operator asked for callback re Seattle decking install timing",
    }


def _voice_payload() -> dict:
    return {
        "session_id":          "voice-session-7e2dd8a4",
        "clerk_session_id":    "sess_2nWqLk9rTfBy",
        "transcript_line":     "Upload the kitchen-cabinets MP4 walkthrough to canvas",
        "line_index":          42,
        "turn_intent_summary": "MP4 walkthrough of kitchen-cabinets job — Danielle canvas upload",
    }


def _assert_v0_1_2_valid(path: Path, label: str) -> dict:
    assert path.exists(), f"{label}: expected {path} on disk"
    rec = json.loads(path.read_text())
    errs = task_schema.validate_task_record(rec)
    assert not errs, f"{label}: schema errors {errs}"
    return rec


def _count_intake_tasks(workspace: Path) -> int:
    return sum(1 for _ in (workspace / "tasks" / "intake").glob("*/task.json"))


def main() -> int:
    workspaces: list[Path] = []
    try:
        # ---- [1] email adapter produces a v0.1.2-valid task.json ----
        w_email = _scaffold("cca"); workspaces.append(w_email)
        r1 = email_intake.intake(_email_payload(), tenant="cca", workspace=w_email)
        assert r1["verdict"] == "accept", r1
        rec_e = _assert_v0_1_2_valid(Path(r1["path_written"]), "email")
        print("[1] email adapter: builds a v0.1.2-valid task.json: OK")

        # ---- [2] sms adapter ----
        w_sms = _scaffold("cca"); workspaces.append(w_sms)
        r2 = sms_intake.intake(_sms_payload(), tenant="cca", workspace=w_sms)
        assert r2["verdict"] == "accept", r2
        rec_s = _assert_v0_1_2_valid(Path(r2["path_written"]), "sms")
        print("[2] sms adapter: builds a v0.1.2-valid task.json: OK")

        # ---- [3] voice adapter ----
        w_voice = _scaffold("danielle"); workspaces.append(w_voice)
        r3 = voice_intake.intake(_voice_payload(), tenant="danielle", workspace=w_voice)
        assert r3["verdict"] == "accept", r3
        rec_v = _assert_v0_1_2_valid(Path(r3["path_written"]), "voice")
        print("[3] voice adapter: builds a v0.1.2-valid task.json: OK")

        # ---- [4] raised_by per Rule 7 enum ----
        assert rec_e["raised_by"] == "email", rec_e["raised_by"]
        assert rec_s["raised_by"] == "sms",   rec_s["raised_by"]
        assert rec_v["raised_by"] == "voice", rec_v["raised_by"]
        print("[4] raised_by per spec enum (email/sms/voice): OK")

        # ---- [5] source_ref per spec ----
        assert rec_e["source_ref"] == "gmail-thread-189f3b7ac2", rec_e["source_ref"]
        assert rec_s["source_ref"] == "SM7c2a9f1e88b4d40a91ab0a3a2f1b8c01", rec_s["source_ref"]
        assert rec_v["source_ref"] == "voice-session-7e2dd8a4:line:42", rec_v["source_ref"]
        print("[5] source_ref per spec (gmail-thread / Twilio SID / session:line:n): OK")

        # ---- [6] email adapter clamps long subject to 120 chars ----
        w_long = _scaffold("cca"); workspaces.append(w_long)
        long_subj = "X" * 200
        long_payload = _email_payload()
        long_payload["gmail_thread_id"] = "gmail-thread-LONG-SUBJ"
        long_payload["subject"] = long_subj
        r6 = email_intake.intake(long_payload, tenant="cca", workspace=w_long)
        assert r6["verdict"] == "accept", r6
        rec_long = _assert_v0_1_2_valid(Path(r6["path_written"]), "email-long")
        assert len(rec_long["summary"]) == 120, len(rec_long["summary"])
        assert rec_long["summary"] == "X" * 120
        print("[6] email adapter clamps 200-char subject → summary length 120: OK")

        # ---- [7] sms adapter sets operator_phone ----
        assert rec_s["operator_phone"] == "+14374559131", rec_s["operator_phone"]
        print("[7] sms adapter sets operator_phone to E.164 from_number: OK")

        # ---- [8] voice adapter sets clerk_session_id ----
        assert rec_v["clerk_session_id"] == "sess_2nWqLk9rTfBy", rec_v["clerk_session_id"]
        print("[8] voice adapter sets clerk_session_id from payload: OK")

        # ---- [9] re-running email payload → reject, no second file ----
        before = _count_intake_tasks(w_email)
        r9 = email_intake.intake(_email_payload(), tenant="cca", workspace=w_email)
        after = _count_intake_tasks(w_email)
        assert r9["verdict"] == "reject", r9
        assert r9["path_written"] is None, r9
        assert before == after, f"email re-intake wrote to disk ({before} → {after})"
        print("[9] email re-intake → verdict=reject, no second file on disk: OK")

        # ---- [10] re-running sms payload → reject, no second file ----
        before = _count_intake_tasks(w_sms)
        r10 = sms_intake.intake(_sms_payload(), tenant="cca", workspace=w_sms)
        after = _count_intake_tasks(w_sms)
        assert r10["verdict"] == "reject", r10
        assert r10["path_written"] is None, r10
        assert before == after, f"sms re-intake wrote to disk ({before} → {after})"
        print("[10] sms re-intake → verdict=reject, no second file on disk: OK")

        # ---- [11] re-running voice payload → reject, no second file ----
        before = _count_intake_tasks(w_voice)
        r11 = voice_intake.intake(_voice_payload(), tenant="danielle", workspace=w_voice)
        after = _count_intake_tasks(w_voice)
        assert r11["verdict"] == "reject", r11
        assert r11["path_written"] is None, r11
        assert before == after, f"voice re-intake wrote to disk ({before} → {after})"
        print("[11] voice re-intake → verdict=reject, no second file on disk: OK")

        # ---- [12] every accepted task.json lives under tasks/intake/<task-id>/ ----
        for label, work, res in (
            ("email",      w_email, r1),
            ("sms",        w_sms,   r2),
            ("voice",      w_voice, r3),
            ("email-long", w_long,  r6),
        ):
            p = Path(res["path_written"])
            assert p.parent.parent.name == "intake", f"{label} not under tasks/intake/"
            assert p.parent.name == res["task_id"], (
                f"{label}: dir name {p.parent.name} != task_id {res['task_id']}"
            )
        print("[12] every accepted task lives under tasks/intake/<task-id>/task.json: OK")

        print("\nALL INTAKE-EXTERNAL ASSERTIONS PASSED")
        return 0
    finally:
        for w in workspaces:
            shutil.rmtree(w, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
