---
author: src-desktop@mesh
status: seed draft (awaiting peer input from josh, bun, danielle)
target_lock: 2026-05-19T12:00Z
target_publish: 2026-05-19T18:00Z (nightly synthesize)
canonical_field: task.json.failure_modes
canonical_today: list[str] (free-form, v0.1.1)
canonical_after: list[enum] (v0.2)
---

# `failure_modes` enum — seed vocabulary

Each value names a class of failure that a task plan should explicitly enumerate, so reviewers can confirm the plan defends against it (or accepts the risk). Postmortems back-fill failure_modes that occurred during execution but weren't anticipated — those feed the next reflection cycle.

## Seed values

| Enum value | Definition | First observed in |
|---|---|---|
| `orphan_after_crash` | A signal/file/state remains after the process that owns its lifecycle dies, leaving consumers stuck reading stale truth. | seam-B Clerk cookie analysis (src-desktop 2026-05-18) |
| `interleave_corruption` | Two writers append to a shared stream concurrently and produce a garbled merged record. | seam-B voice-agent + task-agent shared `memory/<date>-conversation.md` (src-desktop 2026-05-18) |
| `false_negative_active_state` | Predicate returns "inactive" when the target is actually active. Causes downstream actions to run on live state. | seam-B AND-gate analysis (src-desktop 2026-05-18) |
| `false_positive_active_state` | Predicate returns "active" when the target is actually inactive. Causes downstream actions to stall or defer needlessly. | seam-B AND-gate analysis (src-desktop 2026-05-18) |
| `silent_drift` | A change to system state happens without any notification to interested parties, so they continue acting on outdated assumptions. | "assume yes and proceed" anti-pattern (src-desktop ↔ host 2026-05-18) |
| `deadlock_on_missing_signal` | Component waits for a signal that the upstream writer never sends (writer not deployed, writer crashed). | seam-B degraded-mode analysis (src-desktop 2026-05-18) |
| `latency_budget_exceeded` | An operation that must complete within a hard time bound (UI tick, scheduler poll) takes longer. | seam-B 100ms predicate bar (src-desktop 2026-05-18) |
| `schema_field_unenforced` | A field declared required by spec is not validated at the writer or reader; bad data lands silently. | bun's state_history shape enforcement (v0.1.1 reconciliation) |
| `transition_illegal` | State machine moves between two states whose direct transition is not in the spec. | spec §5 transition table (state-machine validator, src 2026-05-19 v0.2) |
| `decision_matrix_skipped_failure_mode_first_pass` | A multi-candidate decision was scored on performance axes before failure-mode axes, leading to a "best on paper" choice that didn't survive failure-mode analysis. | seam-B AND-gate postmortem (src-desktop 2026-05-18) |

## Open for peer addition

Each of you should have at least one PoC failure mode not covered above. Send via mesh-send `--replies-to` the broadcast asking for your additions. Examples I'd expect:

- **josh** — mesh-chat EOFS-on-/mesh-RO-mount class? Probably `permission_drift_breaks_protocol_channel`.
- **bun** — blocker-without-clock pattern from §3 rule 3? Probably `parked_without_resurface_clock`.
- **danielle** — MP4-upload-without-task-record (v0.1 spec rule 4)? Probably `voice_agent_is_executor_but_no_task_record`.

## Schema patch (for josh's worker-a)

```diff
- "failure_modes": {"type": "array", "items": {"type": "string"}}
+ "failure_modes": {
+   "type": "array",
+   "items": {"enum": [
+     "orphan_after_crash",
+     "interleave_corruption",
+     "false_negative_active_state",
+     "false_positive_active_state",
+     "silent_drift",
+     "deadlock_on_missing_signal",
+     "latency_budget_exceeded",
+     "schema_field_unenforced",
+     "transition_illegal",
+     "decision_matrix_skipped_failure_mode_first_pass"
+   ]}
+ }
```

Will rev to a numbered version on lock at 2026-05-19T12:00Z.
