"""
Lock-and-defer "is voice channel active?" predicate — AND-gate reader.

Spec: /mesh/BLACKBOARD/meetings/2026-05-18-task-system-redesign/v0.1-spec-host.md §6
Source thread:
  - josh-desktop@mesh asked src-desktop@mesh to align before shipping the reader
  - src-desktop@mesh replied (2026-05-18-001-src-desktop-re-lock-and-defer-...):
      - Venue: shared substrate (here, not src-desktop's tenant)
      - AND-gate: BOTH signals must be present + fresh → voice IS active
      - Clerk cookie path: /config/.openvoiceui/clerk-session.cookie
      - OVU heartbeat path: /home/node/.openvoiceui/voice-active.flag
      - Heartbeat cadence: 2s (writer)
      - Reader stale window: 5s (2.5× cadence — covers one missed write + jitter)
      - Required helper: predicate_mode() distinguishing deployment states so
        callers fail-loud not fail-silent/fail-deadlock
      - Cookie writer is a v0.2 dep (not yet filed) — reader treats missing
        cookie path as Clerk-INACTIVE

Single stat() syscall per signal, sub-millisecond. No RPC, no subprocess.

CALLER CONTRACT:
    from voice_active import VoiceActivePredicate

    pred = VoiceActivePredicate()    # use canonical paths
    if pred.is_active():
        defer_task()
    else:
        run_task()

    # At scheduler startup, check what's deployed so we fail-loud:
    mode = pred.predicate_mode()
    if mode == "no-writers-deployed":
        warn_host("predicate has no writers — refusing to schedule lock-required tasks")

Constructor args let downstream callers override paths if v0.2 finalization
moves them. Default values are src-desktop's spec.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


# src-desktop spec defaults. Override via constructor args if v0.2 moves them.
DEFAULT_CLERK_COOKIE_PATH = "/config/.openvoiceui/clerk-session.cookie"
DEFAULT_HEARTBEAT_PATH = "/home/node/.openvoiceui/voice-active.flag"
DEFAULT_HEARTBEAT_STALE_SECONDS = 5.0  # 2.5× the 2s writer cadence

PredicateMode = Literal[
    "full",
    "degraded-cookie-only",
    "degraded-heartbeat-only",
    "no-writers-deployed",
]


@dataclass(frozen=True)
class VoiceActivePredicate:
    """
    Lock-and-defer reader. Both signals must be present-and-fresh for the
    predicate to fire active. Either signal absent or stale → inactive.

    AND-gate rationale (src-desktop): defense in depth.
      - Clerk cookie alone is stale-prone (no liveness signal)
      - Heartbeat alone has no identity binding (any process can touch the file)
      - Both together: identity AND liveness, no false-positive either way.
    """

    clerk_cookie_path: str = DEFAULT_CLERK_COOKIE_PATH
    heartbeat_path: str = DEFAULT_HEARTBEAT_PATH
    heartbeat_stale_seconds: float = DEFAULT_HEARTBEAT_STALE_SECONDS

    # ------------------------------------------------------------------ #
    # Per-signal readers — each ONE single stat() syscall + arithmetic.  #
    # ------------------------------------------------------------------ #

    def _clerk_active(self) -> bool:
        """True iff the Clerk session cookie file exists (no staleness check —
        Clerk session is OS-managed, OVU touches/removes it at connect/disconnect).

        If the cookie WRITER hasn't been deployed (file path missing), treat as
        clerk-INACTIVE (safer default — heartbeat alone never fires the AND-gate,
        so task work continues. False-positive "voice active" would corrupt
        transcripts; false-negative "inactive" just runs the task anyway).
        """
        try:
            return os.path.exists(self.clerk_cookie_path)
        except OSError:
            # Permission / mount errors → treat as inactive (fail-open for tasks).
            return False

    def _heartbeat_fresh(self) -> bool:
        """True iff the OVU heartbeat file's mtime is within stale window."""
        try:
            mtime = os.path.getmtime(self.heartbeat_path)
        except (FileNotFoundError, OSError):
            return False
        age = time.time() - mtime
        return 0 <= age <= self.heartbeat_stale_seconds

    # ------------------------------------------------------------------ #
    # Public predicate.                                                  #
    # ------------------------------------------------------------------ #

    def is_active(self) -> bool:
        """AND-gate: BOTH cookie present AND heartbeat fresh → voice active."""
        return self._clerk_active() and self._heartbeat_fresh()

    # ------------------------------------------------------------------ #
    # Deployment-mode introspection — call at scheduler startup so we    #
    # fail-LOUD when writers aren't installed, not silently corrupt.     #
    # ------------------------------------------------------------------ #

    def predicate_mode(self) -> PredicateMode:
        """
        Distinguish: are the writers actually deployed?

        A "no writers deployed" answer to is_active() looks identical to an
        "everyone is inactive" answer at the bit level — but the operational
        meaning is night-and-day. Callers that need the lock contract MUST
        check the mode at startup before trusting is_active().

        - 'full'                     — both writer paths exist (cookie file +
                                       heartbeat dir reachable). Trust is_active.
        - 'degraded-cookie-only'     — cookie writer deployed, heartbeat dir
                                       not present.
        - 'degraded-heartbeat-only'  — heartbeat dir present, cookie writer
                                       not deployed (the v0.2 dep that's filed
                                       but not yet implemented).
        - 'no-writers-deployed'      — neither path's container exists.
                                       Scheduler should refuse to schedule
                                       lock_required=True tasks and emit ONE
                                       startup warning to host@mesh.
        """
        cookie_dir = Path(self.clerk_cookie_path).parent
        heartbeat_dir = Path(self.heartbeat_path).parent
        cookie_writer = cookie_dir.is_dir()
        heartbeat_writer = heartbeat_dir.is_dir()
        if cookie_writer and heartbeat_writer:
            return "full"
        if cookie_writer:
            return "degraded-cookie-only"
        if heartbeat_writer:
            return "degraded-heartbeat-only"
        return "no-writers-deployed"


# ---------------------------------------------------------------------------- #
# Module-level convenience for the common case (default paths).                #
# ---------------------------------------------------------------------------- #

_default = VoiceActivePredicate()


def is_active() -> bool:
    """Convenience: AND-gate on the spec-default paths."""
    return _default.is_active()


def predicate_mode() -> PredicateMode:
    """Convenience: deployment-mode on the spec-default paths."""
    return _default.predicate_mode()


if __name__ == "__main__":
    import argparse
    import json
    import sys

    ap = argparse.ArgumentParser(description="Voice-active predicate (AND-gate reader)")
    ap.add_argument("--cookie", default=DEFAULT_CLERK_COOKIE_PATH)
    ap.add_argument("--heartbeat", default=DEFAULT_HEARTBEAT_PATH)
    ap.add_argument("--stale-seconds", type=float, default=DEFAULT_HEARTBEAT_STALE_SECONDS)
    ap.add_argument("--mode", action="store_true", help="emit predicate_mode() instead of is_active()")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    pred = VoiceActivePredicate(
        clerk_cookie_path=args.cookie,
        heartbeat_path=args.heartbeat,
        heartbeat_stale_seconds=args.stale_seconds,
    )

    out = {
        "is_active": pred.is_active(),
        "predicate_mode": pred.predicate_mode(),
        "clerk_cookie_path": pred.clerk_cookie_path,
        "heartbeat_path": pred.heartbeat_path,
        "heartbeat_stale_seconds": pred.heartbeat_stale_seconds,
    }
    if args.json:
        print(json.dumps(out, indent=2))
    elif args.mode:
        print(out["predicate_mode"])
    else:
        print("active" if out["is_active"] else "inactive")
    sys.exit(0)
