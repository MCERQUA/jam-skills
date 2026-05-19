"""
Rule 8 bootstrap context loader.

Per v0.1.1 spec amendment §Rule 8 bootstrap contract — before working ANY task
the tenant agent MUST load full open-state task inventory + thread/conversation
history + voice transcript + reflection summaries. This module is the LOAD
half: returns a structured dict the agent introspects.

It is the BOTTOM of the stack — it does not import dedupe or any state-machine
layer; those import this. Reads are filesystem-only (no mesh I/O), restricted
to paths inside the passed workspace.

Usage:
    from task_bootstrap import load_context

    ctx = load_context(
        tenant="cca",
        workspace="/mnt/clients/josh/openclaw/workspace",
        # optional override for tests / replay:
        # today=date(2026, 5, 19),
    )

Spec refs:
  - /mesh/BLACKBOARD/task-system/v0.1.1-spec-amendment.md §Rule 8
  - /agent-desk/snapshots/2026-05-19-canonical-schema-v0.1.3/task_schema.py
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Tasks worth loading for active execution. `done/` is intentionally
# excluded — completed work is not open context (it's audit history).
_OPEN_STATES = (
    "intake",
    "shop-floor",
    "planned",
    "scheduled",
    "today",
    "in-flight",
    "parked",
)

_LEDGER_WINDOW_DAYS = 7
_REFLECTION_WINDOW_DAYS = 7


def _now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_within(workspace: Path, candidate: Path) -> bool:
    """True iff candidate resolves to a path inside workspace."""
    try:
        return candidate.resolve().is_relative_to(workspace.resolve())
    except (OSError, ValueError):
        return False


def _read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None


def _parse_date_prefix(stem: str) -> date | None:
    """Parse leading YYYY-MM-DD from a filename stem; return None if absent."""
    if len(stem) < 10:
        return None
    try:
        return date.fromisoformat(stem[:10])
    except ValueError:
        return None


def _load_open_tasks(workspace: Path, tenant: str) -> dict[str, list[dict]]:
    open_tasks: dict[str, list[dict]] = {s: [] for s in _OPEN_STATES}
    tasks_root = workspace / "tasks"
    if not tasks_root.is_dir():
        return open_tasks
    for state in _OPEN_STATES:
        state_dir = tasks_root / state
        if not state_dir.is_dir():
            continue
        for task_dir in sorted(state_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            task_json = task_dir / "task.json"
            if not task_json.is_file() or not _safe_within(workspace, task_json):
                continue
            record = _read_json(task_json)
            if not isinstance(record, dict):
                continue
            if record.get("tenant") != tenant:
                continue
            open_tasks[state].append(record)
    return open_tasks


def _load_ledger(workspace: Path, today_d: date) -> list[dict]:
    ledger_dir = workspace / "ledger"
    if not ledger_dir.is_dir():
        return []
    cutoff = today_d - timedelta(days=_LEDGER_WINDOW_DAYS)
    entries: list[dict] = []
    for entry_file in sorted(ledger_dir.iterdir()):
        if not entry_file.is_file() or entry_file.suffix != ".json":
            continue
        if not _safe_within(workspace, entry_file):
            continue
        entry_date = _parse_date_prefix(entry_file.stem)
        if entry_date is None:
            continue
        if entry_date < cutoff or entry_date > today_d:
            continue
        loaded = _read_json(entry_file)
        if isinstance(loaded, list):
            entries.extend(x for x in loaded if isinstance(x, dict))
        elif isinstance(loaded, dict):
            entries.append(loaded)
    return entries


def _extract_messages(loaded) -> list | None:
    """Accept either a list of messages or {"messages": [...]}; reject others."""
    if isinstance(loaded, list):
        return loaded
    if isinstance(loaded, dict):
        messages = loaded.get("messages")
        if isinstance(messages, list):
            return messages
    return None


def _load_gmail_threads(
    workspace: Path, open_tasks: dict[str, list[dict]]
) -> dict[str, list]:
    threads: dict[str, list] = {}
    threads_dir = workspace / "gmail" / "threads"
    if not threads_dir.is_dir():
        return threads
    referenced: set[str] = set()
    for task_list in open_tasks.values():
        for t in task_list:
            if t.get("raised_by") != "email":
                continue
            ref = t.get("source_ref")
            if isinstance(ref, str) and ref:
                referenced.add(ref)
    for ref in referenced:
        # Guard against path traversal via crafted source_ref.
        if "/" in ref or "\\" in ref or ".." in ref:
            continue
        thread_file = threads_dir / f"{ref}.json"
        if not thread_file.is_file() or not _safe_within(workspace, thread_file):
            continue
        messages = _extract_messages(_read_json(thread_file))
        if messages is not None:
            threads[ref] = messages
    return threads


def _load_sms_threads(
    workspace: Path, open_tasks: dict[str, list[dict]]
) -> dict[str, list]:
    threads: dict[str, list] = {}
    conv_dir = workspace / "sms" / "conversations"
    if not conv_dir.is_dir():
        return threads
    referenced: set[str] = set()
    for task_list in open_tasks.values():
        for t in task_list:
            phone = t.get("operator_phone")
            if isinstance(phone, str) and phone:
                referenced.add(phone)
    for phone in referenced:
        if "/" in phone or "\\" in phone or ".." in phone:
            continue
        conv_file = conv_dir / f"{phone}.json"
        if not conv_file.is_file() or not _safe_within(workspace, conv_file):
            continue
        messages = _extract_messages(_read_json(conv_file))
        if messages is not None:
            threads[phone] = messages
    return threads


def _load_voice_transcript(workspace: Path, today_d: date) -> str | None:
    transcript_path = workspace / "memory" / f"{today_d.isoformat()}-conversation.md"
    if not transcript_path.is_file() or not _safe_within(workspace, transcript_path):
        return None
    try:
        return transcript_path.read_text()
    except (OSError, UnicodeDecodeError):
        return None


def _load_reflections(workspace: Path, today_d: date) -> list[dict]:
    refl_dir = workspace / "reflections"
    if not refl_dir.is_dir():
        return []
    cutoff = today_d - timedelta(days=_REFLECTION_WINDOW_DAYS)
    entries: list[dict] = []
    for refl_file in sorted(refl_dir.iterdir()):
        if not refl_file.is_file() or refl_file.suffix != ".md":
            continue
        if not _safe_within(workspace, refl_file):
            continue
        entry_date = _parse_date_prefix(refl_file.stem)
        if entry_date is None:
            continue
        if entry_date < cutoff or entry_date > today_d:
            continue
        try:
            content = refl_file.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        entries.append({
            "date": entry_date.isoformat(),
            "filename": refl_file.name,
            "content": content,
        })
    return entries


def load_context(
    tenant: str,
    workspace: str | os.PathLike,
    *,
    today: date | None = None,
) -> dict:
    """
    Load the Rule 8 bootstrap context bundle for a tenant.

    Returns a JSON-serializable plain dict with the keys:
        tenant, workspace, loaded_at, today,
        open_tasks, open_task_count,
        ledger_recent, gmail_threads, sms_threads,
        voice_transcript, reflections_recent.

    All filesystem reads are restricted to within the resolved `workspace`
    path. Missing optional subdirectories yield empty values, never crash.
    """
    if not isinstance(tenant, str) or not tenant:
        raise ValueError("tenant must be a non-empty string")

    workspace_path = Path(workspace).resolve()
    if not workspace_path.is_dir():
        raise FileNotFoundError(
            f"workspace not found or not a directory: {workspace_path}"
        )

    today_d = today if today is not None else datetime.now(timezone.utc).date()
    if not isinstance(today_d, date):
        raise TypeError("today must be a datetime.date or None")

    open_tasks = _load_open_tasks(workspace_path, tenant)
    open_task_count = sum(len(v) for v in open_tasks.values())

    return {
        "tenant": tenant,
        "workspace": str(workspace_path),
        "loaded_at": _now_z(),
        "today": today_d.isoformat(),
        "open_tasks": open_tasks,
        "open_task_count": open_task_count,
        "ledger_recent": _load_ledger(workspace_path, today_d),
        "gmail_threads": _load_gmail_threads(workspace_path, open_tasks),
        "sms_threads": _load_sms_threads(workspace_path, open_tasks),
        "voice_transcript": _load_voice_transcript(workspace_path, today_d),
        "reflections_recent": _load_reflections(workspace_path, today_d),
    }
