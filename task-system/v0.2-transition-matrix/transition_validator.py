"""
transition_validator — validate task state transitions against the v0.2 transition matrix.

Loaded by the state_history writer before appending any new state entry.
Refuses illegal transitions, missing required artifacts, missing required preconditions,
and writer-role violations (e.g. mesh-side scheduler attempting intake→in-flight).

Author: src-desktop@mesh
Spec ref: v0.1.1 §5 transition table → v0.2 machine-readable matrix
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ValidationResult:
    """Result of a transition check.

    ok: True if transition is allowed.
    reasons: empty if ok; otherwise one or more rejection reasons.
    """

    ok: bool
    reasons: tuple[str, ...]

    @classmethod
    def allow(cls) -> "ValidationResult":
        return cls(True, ())

    @classmethod
    def reject(cls, *reasons: str) -> "ValidationResult":
        return cls(False, tuple(reasons))


class TransitionValidator:
    def __init__(self, matrix_path: str | Path):
        with open(matrix_path) as f:
            self._matrix: dict[str, Any] = json.load(f)
        self._states: set[str] = set(self._matrix["states"])
        self._writer_roles: set[str] = set(self._matrix["writer_roles"])
        self._terminal: set[str] = set(self._matrix["terminal_states"])
        # index transitions by (from, to) for O(1) lookup
        self._by_pair: dict[tuple[str, str], dict[str, Any]] = {
            (t["from"], t["to"]): t for t in self._matrix["transitions"]
        }

    def validate(
        self,
        *,
        from_state: str,
        to_state: str,
        writer_role: str,
        present_artifacts: set[str] | None = None,
        precondition_values: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """Check whether a from→to transition is allowed.

        present_artifacts: filenames present in the task dir at the time of transition
                           (e.g. {"task.json", "plan.md", "schedule.json"})
        precondition_values: dict of values for precondition keys, e.g.
                             {"blocker.json.resolved": True, "blocker.json.parked_until": "2026-05-18T10:00:00Z"}
        """
        present = present_artifacts or set()
        preconds = precondition_values or {}
        reasons: list[str] = []

        # 1. State name sanity
        if from_state not in self._states:
            reasons.append(f"unknown from_state: {from_state!r}")
        if to_state not in self._states:
            reasons.append(f"unknown to_state: {to_state!r}")
        if reasons:
            return ValidationResult.reject(*reasons)

        # 2. Terminal state is sticky
        if from_state in self._terminal:
            return ValidationResult.reject(
                f"{from_state!r} is terminal — rework requires a new task with linked_to"
            )

        # 3. Writer role registered
        if writer_role not in self._writer_roles:
            reasons.append(f"unknown writer_role: {writer_role!r}")

        # 4. Transition exists in matrix
        spec = self._by_pair.get((from_state, to_state))
        if spec is None:
            reasons.append(
                f"illegal transition {from_state!r} → {to_state!r} (not in v0.2 matrix)"
            )
            return ValidationResult.reject(*reasons)

        # 5. Writer role is allowed for this specific transition
        allowed_roles: list[str] = spec["writer_roles"]
        if writer_role not in allowed_roles:
            reasons.append(
                f"writer_role {writer_role!r} not permitted for {from_state}→{to_state}; "
                f"allowed: {allowed_roles}"
            )

        # 6. Required artifacts present
        required: list[str] = spec.get("required_artifacts", [])
        missing = [a for a in required if a not in present]
        if missing:
            reasons.append(
                f"missing required artifacts for {from_state}→{to_state}: {missing}"
            )

        # 7. Preconditions satisfied (presence-only check; caller resolves values)
        preconds_spec: list[str] = spec.get("preconditions", [])
        for p in preconds_spec:
            # parse "key == value" or "key < now"
            if "==" in p:
                key, expected = (x.strip() for x in p.split("==", 1))
                actual = preconds.get(key)
                # tolerate string-cast comparison
                if str(actual).lower() != expected.lower():
                    reasons.append(
                        f"precondition failed: {key!r} expected {expected!r}, got {actual!r}"
                    )
            elif "< now" in p:
                key = p.split("<")[0].strip()
                if key not in preconds:
                    reasons.append(f"precondition unchecked: {p!r} (no value supplied)")
                # actual now-comparison left to caller (locale + timezone concerns)
            else:
                # unrecognized precondition shape — surface, do not silently pass
                reasons.append(f"precondition shape unrecognized: {p!r}")

        if reasons:
            return ValidationResult.reject(*reasons)
        return ValidationResult.allow()

    def legal_transitions_from(self, state: str) -> list[dict[str, Any]]:
        """For diagnostics: list every legal transition out of `state`."""
        return [t for t in self._matrix["transitions"] if t["from"] == state]


# ---------- self-tests ----------

def _run_tests(matrix_path: str | Path) -> None:
    v = TransitionValidator(matrix_path)

    # Legal: full happy path
    assert v.validate(
        from_state="_new", to_state="intake",
        writer_role="task-agent", present_artifacts={"task.json"},
    ).ok, "test 1 — happy path _new→intake"

    assert v.validate(
        from_state="intake", to_state="shop-floor",
        writer_role="task-agent",
    ).ok, "test 2 — intake→shop-floor"

    assert v.validate(
        from_state="shop-floor", to_state="planned",
        writer_role="task-agent", present_artifacts={"task.json", "plan.md"},
    ).ok, "test 3 — shop-floor→planned with plan.md"

    assert v.validate(
        from_state="planned", to_state="scheduled",
        writer_role="task-agent", present_artifacts={"task.json", "plan.md", "schedule.json"},
    ).ok, "test 4 — planned→scheduled with schedule.json"

    assert v.validate(
        from_state="scheduled", to_state="today",
        writer_role="brief-reader",
    ).ok, "test 5 — scheduled→today by brief-reader"

    assert v.validate(
        from_state="today", to_state="done",
        writer_role="task-agent", present_artifacts={"task.json", "plan.md", "schedule.json", "postmortem.md"},
    ).ok, "test 6 — today→done with postmortem"

    # Illegal: writer-role violation on the voice-only intake→in-flight
    r = v.validate(
        from_state="intake", to_state="in-flight",
        writer_role="task-agent", present_artifacts={"task.json", "upload-task.md"},
    )
    assert not r.ok and any("not permitted" in s for s in r.reasons), \
        f"test 7 — intake→in-flight by task-agent must be rejected, got {r}"

    # Legal: intake→in-flight by voice-agent
    assert v.validate(
        from_state="intake", to_state="in-flight",
        writer_role="voice-agent", present_artifacts={"task.json", "upload-task.md"},
    ).ok, "test 8 — intake→in-flight by voice-agent (with upload-task.md)"

    # Illegal: skip-state intake→planned
    r = v.validate(
        from_state="intake", to_state="planned",
        writer_role="task-agent", present_artifacts={"task.json", "plan.md"},
    )
    assert not r.ok and any("illegal transition" in s for s in r.reasons), \
        f"test 9 — intake→planned must be rejected (skips shop-floor), got {r}"

    # Illegal: done is terminal
    r = v.validate(
        from_state="done", to_state="today",
        writer_role="task-agent",
    )
    assert not r.ok and any("terminal" in s for s in r.reasons), \
        f"test 10 — done→anything must be rejected, got {r}"

    # Illegal: shop-floor→planned without plan.md
    r = v.validate(
        from_state="shop-floor", to_state="planned",
        writer_role="task-agent", present_artifacts={"task.json"},
    )
    assert not r.ok and any("missing required artifacts" in s for s in r.reasons), \
        f"test 11 — shop-floor→planned without plan.md must reject, got {r}"

    # Illegal: shop-floor→parked needs BOTH blocker.json and blockers.md
    r = v.validate(
        from_state="shop-floor", to_state="parked",
        writer_role="task-agent", present_artifacts={"task.json", "blocker.json"},
    )
    assert not r.ok and any("blockers.md" in s for s in r.reasons), \
        f"test 12 — parked needs both blocker files, got {r}"

    # Legal: parked→today with resolved blocker
    assert v.validate(
        from_state="parked", to_state="today",
        writer_role="check-and-promote-cron",
        present_artifacts={"task.json", "schedule.json", "blocker.json", "blockers.md"},
        precondition_values={"blocker.json.resolved": True, "blocker.json.parked_until": "2026-05-18T00:00:00Z"},
    ).ok, "test 13 — parked→today by cron with resolved blocker"

    # Illegal: parked→today without resolved blocker
    r = v.validate(
        from_state="parked", to_state="today",
        writer_role="check-and-promote-cron",
        present_artifacts={"task.json", "schedule.json", "blocker.json", "blockers.md"},
        precondition_values={"blocker.json.resolved": False, "blocker.json.parked_until": "2026-05-18T00:00:00Z"},
    )
    assert not r.ok and any("precondition failed" in s for s in r.reasons), \
        f"test 14 — parked→today with unresolved blocker must reject, got {r}"

    # Illegal: in-flight→shop-floor (no demote path)
    r = v.validate(
        from_state="in-flight", to_state="shop-floor",
        writer_role="voice-agent",
    )
    assert not r.ok and any("illegal transition" in s for s in r.reasons), \
        f"test 15 — in-flight→shop-floor must reject, got {r}"

    # Diagnostics: legal_transitions_from
    out = v.legal_transitions_from("shop-floor")
    targets = {t["to"] for t in out}
    assert targets == {"planned", "parked"}, f"test 16 — shop-floor exits, got {targets}"

    print("transition_validator: 16/16 assertions PASS")


if __name__ == "__main__":
    import sys
    matrix = sys.argv[1] if len(sys.argv) > 1 else "transition-matrix.json"
    _run_tests(matrix)
