"""
dogfood smoke test — replay the seam-B PoC task through the v0.2 transition validator.

Reproduces every transition recorded in src-desktop's PoC task transcript:
    /config/workspace/tasks/done/2026-05-18-2000-seam-b-lock-and-defer-signal/transcript.md

If the validator accepts every transition the PoC actually executed, the v0.2 matrix
is consistent with the v0.1.1 reference implementation. Any rejection here would mean
either the PoC did something the spec forbids, or the validator is over-strict.
"""
from transition_validator import TransitionValidator


def main() -> None:
    v = TransitionValidator("transition-matrix.json")

    # Replay the PoC. Artifacts present at each transition reflect the task dir
    # state at that point in the transcript.
    steps = [
        # (from, to, writer_role, artifacts_present_at_transition, preconditions)
        ("_new",        "intake",     "task-agent", {"task.json"},                                              {}),
        ("intake",      "shop-floor", "task-agent", {"task.json"},                                              {}),
        ("shop-floor",  "planned",    "task-agent", {"task.json", "plan.md"},                                   {}),
        ("planned",     "scheduled",  "task-agent", {"task.json", "plan.md", "schedule.json"},                  {}),
        ("scheduled",   "today",      "brief-reader", {"task.json", "plan.md", "schedule.json"},                {}),
        ("today",       "done",       "task-agent", {"task.json", "plan.md", "schedule.json", "transcript.md", "postmortem.md"}, {}),
    ]

    fails = 0
    for from_state, to_state, role, arts, preconds in steps:
        r = v.validate(
            from_state=from_state, to_state=to_state,
            writer_role=role, present_artifacts=arts,
            precondition_values=preconds,
        )
        status = "OK " if r.ok else "FAIL"
        print(f"  {status}  {from_state:11} → {to_state:11} by {role}")
        if not r.ok:
            for reason in r.reasons:
                print(f"       reason: {reason}")
            fails += 1

    if fails == 0:
        print(f"dogfood smoke: all {len(steps)} PoC transitions VALID under v0.2 matrix")
    else:
        print(f"dogfood smoke: {fails}/{len(steps)} transitions REJECTED — matrix or PoC inconsistent")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
