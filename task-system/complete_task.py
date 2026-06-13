#!/usr/bin/env python3
"""complete_task.py — the ONE canonical task-completion helper (fleet-wide).

This is the missing completion path that ties the existing task-system machinery
together into a single call. For ~3 weeks the schema/intake/transition/lock
machinery existed but nothing CLOSED tasks — the pipeline stayed empty. This
helper is what every tenant agent calls when it finishes a task. It does TWO
writes (per build-owner josh-desktop's rec; Mike's Path A 2026-06-13):

  WRITE 1 (structured — the v0.1.4 pipeline):
    move task.json  today|in-flight -> done/  with a postmortem.md artifact,
    state_history (completer + ts), validated by the transition matrix + schema.
  WRITE 2 (receipt — the convergence):
    append a kind:task-done receipt to the bookkeeper receipts ledger so the
    fleet roll-up (DONE.md) gets a REAL completion signal, distinct from the
    git-autocommit churn that dominates today.

  + BRIDGE: a `work-done` row into the tenant's daily ledger (the section that
    has had zero rows because this call never existed).

Builds ON existing components — reinvents nothing:
  - parallel-shift-race-defense/shift_lock.py        ShiftLock (dir lock)
  - v0.2-transition-matrix/transition_validator.py   TransitionValidator
  - schema/task_schema.py                            validate_task_record
  - scripts/ledger/ledger-append.sh                  work-done section
  - /mnt/agent-mesh/mesh/LEDGER/receipts/<date>.jsonl bookkeeper receipt schema

CLI:
  complete_task.py --workspace <ws> --task-id <id> --by <agent@uri> \
      --summary "<one line>" --postmortem "<what happened>" [--tenant <t>] \
      [--outcome success|partial|failed] [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
# existing components live in sibling dirs (hyphenated → add to path, import by name)
for _d in ("parallel-shift-race-defense", "v0.2-transition-matrix", "schema"):
    p = HERE / _d
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from shift_lock import ShiftLock  # noqa: E402
from transition_validator import TransitionValidator  # noqa: E402
from task_schema import validate_task_record  # noqa: E402

MATRIX = HERE / "v0.2-transition-matrix" / "transition-matrix.json"
LEDGER_APPEND = Path("/home/mike/MIKE-AI/scripts/ledger/ledger-append.sh")
RECEIPTS_DIR = Path("/mnt/agent-mesh/mesh/LEDGER/receipts")

# done is legal only from these pre-done states; writer role is implied by state
_DONE_FROM = {"today": "task-agent", "in-flight": "voice-agent"}
_PRE_DONE_SEARCH = ("today", "in-flight")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _find_task(tasks_root: Path, task_id: str) -> tuple[Path, str] | None:
    """Return (task_dir, state) for task_id in a pre-done state, else None."""
    for state in _PRE_DONE_SEARCH:
        d = tasks_root / state / task_id
        if (d / "task.json").is_file():
            return d, state
    return None


def complete_task(
    workspace: str | Path,
    task_id: str,
    by_uri: str,
    summary: str,
    postmortem: str,
    *,
    tenant: str | None = None,
    outcome: str = "success",
    dry_run: bool = False,
) -> dict:
    """Close one task: structured done-move + work-done ledger row + receipt."""
    ws = Path(workspace)
    tasks_root = ws / "tasks"
    tenant = tenant or _infer_tenant(ws)

    found = _find_task(tasks_root, task_id)
    if not found:
        return {"ok": False, "error": "task_not_found_in_pre_done_state",
                "detail": f"{task_id} not under tasks/{{{','.join(_PRE_DONE_SEARCH)}}}/. "
                          "Promote it to today/in-flight before completing (matrix rule)."}
    task_dir, from_state = found
    writer_role = _DONE_FROM[from_state]
    record = json.loads((task_dir / "task.json").read_text())

    # required artifact: postmortem.md (matrix requires it on every →done)
    postmortem_path = task_dir / "postmortem.md"
    if not dry_run:
        postmortem_path.write_text(
            f"# Postmortem — {record.get('summary', task_id)}\n\n"
            f"- completed_by: {by_uri}\n- at: {_now()}\n- outcome: {outcome}\n\n{postmortem}\n")
    present = {p.name for p in task_dir.iterdir()} | {"postmortem.md"}

    # precondition for the in-flight (upload) path; harmless for the today path
    precond = {"upload-task.md.status": "done"} if from_state == "in-flight" else {}

    v = TransitionValidator(MATRIX).validate(
        from_state=from_state, to_state="done", writer_role=writer_role,
        present_artifacts=present, precondition_values=precond)
    if not v.ok:
        return {"ok": False, "error": "transition_illegal", "from": from_state,
                "reasons": list(v.reasons)}

    # enrich the record for the terminal state
    now = _now()
    record["state"] = "done"
    record.setdefault("state_history", []).append(
        {"state": "done", "at": now, "by": by_uri})
    record["completed_at"] = now
    record["outcome"] = outcome  # completer is captured in state_history[].by

    errs = validate_task_record(record)
    if errs:
        return {"ok": False, "error": "schema_invalid", "schema_errors": errs}

    if dry_run:
        return {"ok": True, "dry_run": True, "from": from_state, "task_id": task_id,
                "would_write": ["tasks/done", "ledger:work-done", "receipt:task-done"]}

    # ── WRITE 1: relocate task → done/ under the dir lock (atomic-ish, race-safe)
    done_dir = tasks_root / "done" / task_id
    with ShiftLock(tasks_root, by_uri).held():
        done_dir.mkdir(parents=True, exist_ok=True)
        (done_dir / "task.json").write_text(json.dumps(record, indent=2) + "\n")
        # relocate artifacts (move, not delete — data preserved, just advanced state)
        for art in task_dir.iterdir():
            if art.name == "task.json":
                continue
            os.replace(art, done_dir / art.name)
        # leave a tombstone breadcrumb, then drop the now-empty source dir entry
        try:
            (task_dir / "task.json").unlink()
            task_dir.rmdir()
        except OSError:
            pass  # non-fatal — the done/ copy is authoritative

    # ── BRIDGE: work-done row into the tenant daily ledger
    ledger_file = ws / "ledger" / f"{_today()}.md"
    _ledger_work_done(ledger_file, by_uri, summary, done_dir / "task.json")

    # ── WRITE 2: kind:task-done receipt → bookkeeper roll-up (distinct from git)
    receipt = _emit_receipt(tenant, by_uri, summary, task_id)

    return {"ok": True, "task_id": task_id, "from": from_state,
            "done_path": str(done_dir / "task.json"),
            "ledger": str(ledger_file), "receipt_id": receipt}


def _ledger_work_done(ledger_file: Path, actor: str, summary: str, proof: Path) -> None:
    """Append a work-done row via the existing ledger-append.sh (the bridge)."""
    if not LEDGER_APPEND.is_file():
        return
    ledger_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["bash", str(LEDGER_APPEND), str(ledger_file), "work-done",
             "task-system", actor, summary],
            check=False, capture_output=True, timeout=15)
    except Exception:  # noqa: BLE001 — ledger bridge is best-effort, never blocks
        pass


def _emit_receipt(tenant: str, actor: str, summary: str, task_id: str) -> str:
    """Append a kind:task-done receipt (source=tasks, proof=task:<id>).

    Idempotent on dedupe_key (normalized-summary|tenant|day) the same way the
    aggregator dedupes — a re-run of the same completion won't double-count."""
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    day = _today()
    dedupe_key = f"{_norm(summary)}|{tenant}|{day}"
    rid = "rcpt-" + day.replace("-", "") + "-" + hashlib.sha1(
        (dedupe_key + task_id).encode()).hexdigest()[:10]
    row = {
        "id": rid, "ts": _now(), "actor": actor, "agent_type": "task-system",
        "tenant": tenant, "action": "task-done", "summary": summary,
        "proof": f"task:{task_id}", "source": "tasks", "tier": "deliverable",
        "dedupe_key": dedupe_key,
    }
    f = RECEIPTS_DIR / f"{day}.jsonl"
    existing = f.read_text().splitlines() if f.is_file() else []
    if any(rid in ln for ln in existing):
        return rid  # already recorded — idempotent
    with f.open("a") as fh:
        fh.write(json.dumps(row) + "\n")
    return rid


def _infer_tenant(ws: Path) -> str:
    # /mnt/clients/<tenant>/openclaw/workspace  → <tenant>
    parts = ws.parts
    if "clients" in parts:
        i = parts.index("clients")
        if i + 1 < len(parts):
            return parts[i + 1]
    return "host"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Close a task: done-move + work-done ledger row + receipt")
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--by", required=True, help="completer agent URI, e.g. joshai@voice")
    ap.add_argument("--summary", required=True)
    ap.add_argument("--postmortem", default="(no detail provided)")
    ap.add_argument("--tenant", default=None)
    ap.add_argument("--outcome", default="success", choices=["success", "partial", "failed"])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    res = complete_task(a.workspace, a.task_id, a.by, a.summary, a.postmortem,
                        tenant=a.tenant, outcome=a.outcome, dry_run=a.dry_run)
    print(json.dumps(res, indent=2))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
