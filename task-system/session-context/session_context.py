"""
SessionContext — read-only friendly wrapper around the Rule 8 bootstrap loader.

The tenant agent constructs ONE SessionContext at task-session start. It calls
task_bootstrap.load_context() once and exposes typed helpers the agent (and
intake adapters running under the agent's identity) use during execution.

Read-only after init: the wrapper raises AttributeError on attribute mutation
after construction. To refresh state (e.g. a new ledger entry landed), discard
and re-construct via start_task_session().

Spec refs:
  - /mesh/BLACKBOARD/task-system/v0.1.1-spec-amendment.md §Rule 8
  - worker-a loader: /agent-desk/snapshots/2026-05-19-rule-8-bootstrap/task_bootstrap.py

Constraints (per worker-b brief):
  - Pure stdlib.
  - Imports task_bootstrap via sys.path injection (no install / no copy).
  - No mutation surface — re-init to refresh.
"""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

# Import worker-a's loader via sys.path, per brief.
_BOOTSTRAP_DIR = Path("/agent-desk/snapshots/2026-05-19-rule-8-bootstrap")
if str(_BOOTSTRAP_DIR) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_DIR))

import task_bootstrap  # noqa: E402

# Match worker-a's open-state ordering (intake → parked). The all_open_tasks
# property iterates in this order so callers get a deterministic flat list.
_OPEN_STATES_ORDER = (
    "intake",
    "shop-floor",
    "planned",
    "scheduled",
    "today",
    "in-flight",
    "parked",
)


class SessionContext:
    """Read-only view over a Rule 8 bootstrap snapshot."""

    __slots__ = ("_ctx", "_frozen")

    def __init__(
        self,
        tenant: str,
        workspace: str | os.PathLike,
        *,
        today: date | None = None,
    ) -> None:
        # Single bootstrap call — the whole point of the wrapper is that the
        # tenant agent pays this cost once at session start.
        ctx = task_bootstrap.load_context(tenant, workspace, today=today)
        object.__setattr__(self, "_ctx", ctx)
        object.__setattr__(self, "_frozen", True)

    def __setattr__(self, name, value):
        if getattr(self, "_frozen", False):
            raise AttributeError(
                f"SessionContext is read-only after init; "
                f"refused to set {name!r}. Re-init to refresh."
            )
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        raise AttributeError(
            f"SessionContext is read-only after init; "
            f"refused to delete {name!r}. Re-init to refresh."
        )

    @property
    def loaded_at(self) -> str:
        return self._ctx["loaded_at"]

    @property
    def tenant(self) -> str:
        return self._ctx["tenant"]

    @property
    def all_open_tasks(self) -> list[dict]:
        """Flat list of open tasks, ordered intake → parked."""
        open_tasks = self._ctx["open_tasks"]
        flat: list[dict] = []
        for state in _OPEN_STATES_ORDER:
            flat.extend(open_tasks.get(state, []))
        return flat

    def open_tasks_in_state(self, state: str) -> list[dict]:
        """Tasks filed under the given open state. [] for unknown states."""
        return list(self._ctx["open_tasks"].get(state, []))

    def find_task_by_id(self, task_id: str) -> dict | None:
        for task in self.all_open_tasks:
            if task.get("id") == task_id:
                return task
        return None

    def find_tasks_by_source_ref(self, source_ref: str) -> list[dict]:
        """All open tasks whose source_ref matches. For Rule 8 dedupe pre-check.

        Multiple matches across states are possible during the window between
        intake-adapter write and the dedupe pass — return them all.
        """
        if source_ref is None:
            return []
        return [
            t for t in self.all_open_tasks
            if t.get("source_ref") == source_ref
        ]

    def thread_history_for(self, gmail_thread_id: str) -> list[dict]:
        """Loaded Gmail thread messages, or [] if not in the bootstrap bundle."""
        return list(self._ctx["gmail_threads"].get(gmail_thread_id, []))

    def sms_history_for(self, operator_phone: str) -> list[dict]:
        """Loaded SMS conversation for the operator's phone, or []."""
        return list(self._ctx["sms_threads"].get(operator_phone, []))

    def has_open_blocker_on(self, summary_text: str) -> bool:
        """True iff a parked/ task has an exact-matching summary string."""
        for task in self._ctx["open_tasks"].get("parked", []):
            if task.get("summary") == summary_text:
                return True
        return False

    def recent_blockers(self) -> list[dict]:
        """Parked-state tasks only (the Rule 8 'open blocker' set)."""
        return list(self._ctx["open_tasks"].get("parked", []))

    def to_dict(self) -> dict:
        """Full underlying context dict. JSON-serializable for logging / mesh."""
        return self._ctx


def start_task_session(
    tenant: str,
    workspace: str | os.PathLike,
    *,
    today: date | None = None,
) -> SessionContext:
    """Module-level convenience constructor for the tenant agent's startup."""
    return SessionContext(tenant, workspace, today=today)
