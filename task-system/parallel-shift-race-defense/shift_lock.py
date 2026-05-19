"""
shift_lock — defense against parallel_shift_writer_race.

Two same-URI agent shifts editing the same /agent-desk/snapshots/<name>/ dir
race on file writes — last-writer-wins overwrites the first shift's work.

Defense: O_EXCL atomic-create a `.shift.lock` file inside the snapshot dir
with a JSON payload identifying the claimant. Writers MUST acquire before
mutating the directory. Stale locks (heartbeat_at older than stale_after_seconds)
are swept atomically; the swept payload is preserved at `.shift.lock.swept-<ts>`
so the displaced shift can post-hoc inspect what was lost.

Conflict matrix:
- same agent_uri + same PID  → re-entry granted (idempotent)
- same agent_uri + different PID → DENIED (the named failure mode)
- different agent_uri + any PID → DENIED (cross-agent collision)
- existing lock past stale threshold → swept + granted

Author: src-desktop@mesh
Spec: failure_modes enum v0.2 entry `parallel_shift_writer_race`
"""
from __future__ import annotations

import json
import os
import socket
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


LOCK_FILENAME = ".shift.lock"
SWEPT_PREFIX = ".shift.lock.swept-"
DEFAULT_STALE_AFTER_SECONDS = 600


class ShiftRaceError(Exception):
    """Raised when a shift lock cannot be acquired (parallel writer detected)."""


@dataclass(frozen=True)
class ClaimResult:
    granted: bool
    reason: str
    prior_owner: dict[str, Any] | None = None
    swept_path: str | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _payload(agent_uri: str, pid: int, stale_after: int) -> dict[str, Any]:
    now = _now_iso()
    return {
        "agent_uri": agent_uri,
        "pid": pid,
        "hostname": socket.gethostname(),
        "acquired_at": now,
        "heartbeat_at": now,
        "stale_after_seconds": stale_after,
    }


def _read_lock(path: Path) -> dict[str, Any] | None:
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _is_stale(payload: dict[str, Any]) -> bool:
    stale_after = payload.get("stale_after_seconds", DEFAULT_STALE_AFTER_SECONDS)
    heartbeat = payload.get("heartbeat_at", payload.get("acquired_at"))
    if not heartbeat:
        return True
    try:
        hb_dt = datetime.strptime(heartbeat, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return True
    age = (datetime.now(timezone.utc) - hb_dt).total_seconds()
    return age > stale_after


class ShiftLock:
    """Per-snapshot-dir advisory lock with stale-sweep semantics."""

    def __init__(
        self,
        snapshot_dir: str | Path,
        agent_uri: str,
        stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
        pid: int | None = None,
    ):
        self.dir = Path(snapshot_dir)
        self.path = self.dir / LOCK_FILENAME
        self.agent_uri = agent_uri
        self.stale_after = stale_after_seconds
        self._pid = pid if pid is not None else os.getpid()
        self._held = False

    def _sweep(self, prior: dict[str, Any]) -> str:
        """Atomic-rename existing lock to swept-<ts> for post-hoc inspection."""
        swept_name = f"{SWEPT_PREFIX}{int(time.time())}"
        swept_path = self.dir / swept_name
        os.replace(self.path, swept_path)
        return str(swept_path)

    def _write_atomic(self, payload: dict[str, Any]) -> None:
        """O_EXCL create. Raises FileExistsError if another writer beat us."""
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        try:
            os.write(fd, json.dumps(payload, indent=2).encode("utf-8"))
        finally:
            os.close(fd)

    def acquire(self) -> ClaimResult:
        """Attempt to claim the snapshot dir.

        Re-entry from same agent_uri+pid is granted idempotently.
        Stale locks (heartbeat older than stale_after_seconds) are swept.
        """
        self.dir.mkdir(parents=True, exist_ok=True)

        payload = _payload(self.agent_uri, self._pid, self.stale_after)

        try:
            self._write_atomic(payload)
            self._held = True
            return ClaimResult(granted=True, reason="fresh-acquire")
        except FileExistsError:
            pass

        existing = _read_lock(self.path)
        if existing is None:
            try:
                os.unlink(self.path)
            except FileNotFoundError:
                pass
            try:
                self._write_atomic(payload)
                self._held = True
                return ClaimResult(granted=True, reason="recovered-corrupt-lock")
            except FileExistsError:
                return ClaimResult(
                    granted=False,
                    reason="lock-flapping-unreadable",
                    prior_owner=None,
                )

        if (
            existing.get("agent_uri") == self.agent_uri
            and existing.get("pid") == self._pid
        ):
            self._held = True
            return ClaimResult(granted=True, reason="re-entry", prior_owner=existing)

        if _is_stale(existing):
            swept = self._sweep(existing)
            self._write_atomic(payload)
            self._held = True
            return ClaimResult(
                granted=True,
                reason="swept-stale",
                prior_owner=existing,
                swept_path=swept,
            )

        if existing.get("agent_uri") == self.agent_uri:
            return ClaimResult(
                granted=False,
                reason="parallel_shift_writer_race",
                prior_owner=existing,
            )

        return ClaimResult(
            granted=False,
            reason="cross-agent-collision",
            prior_owner=existing,
        )

    def heartbeat(self) -> None:
        """Refresh heartbeat_at. Call periodically during long shifts."""
        if not self._held:
            raise ShiftRaceError("heartbeat called without holding lock")
        existing = _read_lock(self.path)
        if existing is None or existing.get("pid") != self._pid:
            self._held = False
            raise ShiftRaceError("lock no longer ours — someone swept us")
        existing["heartbeat_at"] = _now_iso()
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(existing, f, indent=2)
        os.replace(tmp, self.path)

    def release(self) -> bool:
        """Remove lock if we still own it. Returns True if released."""
        if not self._held:
            return False
        existing = _read_lock(self.path)
        if existing and existing.get("pid") == self._pid and existing.get("agent_uri") == self.agent_uri:
            try:
                os.unlink(self.path)
            except FileNotFoundError:
                pass
            self._held = False
            return True
        self._held = False
        return False

    @contextmanager
    def held(self) -> Iterator["ShiftLock"]:
        """Context manager. Raises ShiftRaceError if not granted."""
        result = self.acquire()
        if not result.granted:
            raise ShiftRaceError(
                f"shift lock denied: {result.reason} "
                f"(prior_owner={result.prior_owner})"
            )
        try:
            yield self
        finally:
            self.release()
