---
author: src-desktop@mesh
status: LOCKED v0.2
locked_at: 2026-05-18T21:05:00Z
locked_early: true (all peer input received ahead of 2026-05-19T10:00Z hard deadline)
canonical_field: task.json.failure_modes
canonical_change: v0.1.1 list[str] → v0.2 list[enum]
peer_contributors: src-desktop, josh-desktop, bun-desktop, danielle-desktop
target_publish: 2026-05-19T18:00Z nightly synthesize
schema_patch_target: josh-desktop@mesh worker-a (next canonical-schema ratchet)
---

# `failure_modes` enum — v0.2 (LOCKED)

Each enum value names a class of failure that a task plan should explicitly enumerate, so reviewers can confirm the plan defends against it (or knowingly accepts the risk). Postmortems back-fill failure_modes that occurred during execution but weren't anticipated — those feed the daily-improvement loop via patterns.json.

## Locked enum (21 values, alphabetized)

| Enum value | Definition | First observed in | Contributor |
|---|---|---|---|
| `blocker_source_split_brain` | blocker.json says `resolved: false` while blockers.md has `RESOLVED: true` (or vice-versa) due to operator editing one source and not the other; cron uses JSON as primary and silently ignores MD — task stuck with no signal. | seam-C check-and-promote.sh dual-source fallback design | bun-desktop |
| `completion_signal_ambiguous` | A "done" transition can fire from multiple potential sources (bridge response vs webhook vs poll) without one being defined as authoritative; risks double-write of postmortem.md or race between `done` and `failed`. | host's open question on uploading→done trigger (2026-05-18) | danielle-desktop |
| `cross_session_artifact_handoff_blindness` | A new agent session is unaware of prior-session artifacts in the same workspace; redoes done work or misses upstream dependencies that already shipped. | 2026-05-18T20:18Z discovering prior josh-desktop sessions had already shipped seam-A PoC + task-substrate snapshots only after starting sub-mesh worker briefing | josh-desktop |
| `deadlock_on_missing_signal` | Component waits indefinitely for a signal that the upstream writer never sends (writer not deployed, writer crashed, path misconfigured). | seam-B degraded-mode analysis (2026-05-18) | src-desktop |
| `decision_matrix_skipped_failure_mode_first_pass` | A multi-candidate decision was scored on performance axes (latency, throughput, cost) before failure-mode axes, leading to a "best on paper" choice that didn't survive failure-mode analysis on second pass. | seam-B AND-gate postmortem (2026-05-18) | src-desktop |
| `false_negative_active_state` | Predicate returns "inactive" when the target is actually active; downstream actions then run on live state and risk corruption. | seam-B AND-gate analysis (2026-05-18) | src-desktop |
| `false_positive_active_state` | Predicate returns "active" when the target is actually inactive; downstream actions stall or defer needlessly. | seam-B AND-gate analysis (2026-05-18) | src-desktop |
| `in_flight_orphan` | Task-record-level orphan: a task in `in-flight/` stays in that state forever because the lifecycle event that should advance it never fires (writer crash, missing parked_until clock). Distinct from `orphan_after_crash` which is session-level. | designing upload-task-complete.sh failure path (2026-05-18) | danielle-desktop |
| `interleave_corruption` | Two writers append concurrently to a shared stream (transcript, log, ledger) and produce a garbled merged record. | seam-B voice-agent + task-agent shared `memory/<date>-conversation.md` (2026-05-18) | src-desktop |
| `latency_budget_exceeded` | An operation that must complete within a hard time bound (UI tick, scheduler poll, lock predicate) takes longer; downstream timing assumptions break. | seam-B 100ms predicate bar (2026-05-18) | src-desktop |
| `orphan_after_crash` | A signal/file/state remains after the process that owns its lifecycle dies (Clerk cookie, session marker, lock file), leaving consumers stuck reading stale truth. Distinct from `in_flight_orphan` which is task-record-level. | seam-B Clerk cookie analysis (2026-05-18) | src-desktop |
| `outbound_recipient_drift` | An outbound channel with a parameterized recipient lets env/argv redirect the destination away from Mike (or any policy-locked recipient); env-injection or config-drift silently retargets. | seam-A blocker_digest_cron PoC test [5] env-injection hardening (2026-05-18) | josh-desktop |
| `parallel_shift_writer_race` | Two same-URI agent shifts edit the same `/agent-desk/snapshots/<name>/` directory; last-writer-wins overwrite drops one shift's work. | canonical-schema-v0.1.2/ dir at 2026-05-18T21:10Z | josh-desktop |
| `parked_without_clock` | blocker.json lacks `parked_until`; no cron resurfaces it (seam A skips it); no RESOLVED flag present (check-and-promote skips it). Task has no exit condition and dies silently. | seam-C check-and-promote.sh blocker.json structure check | bun-desktop |
| `permission_drift_breaks_protocol_channel` | A protocol channel becomes unwritable to some peers due to mount-permission drift (RO mount, missing bind-mount, EROFS, EACCES); messages silently fail or block. | mesh-chat EOFS on /mesh/EVENTS RO mount; worker AGENT_URI write attempts on RO paths | josh-desktop |
| `schema_field_unenforced` | A field declared required by spec is not validated at the writer or reader; bad data lands silently and surfaces as an obscure failure later. | bun's state_history shape enforcement during v0.1.1 reconciliation | bun-desktop (via reconciliation) |
| `sentinel_traps_silent_skip` | Idempotency sentinel (e.g. `.trigger-sent`) is written before confirming the consumer received the event; if consumer was down at fire time, the task sits with sentinel blocking re-fire indefinitely (no timeout, no re-arm). | task-scheduler.sh idempotency sentinel design | bun-desktop |
| `silent_drift` | A change to system state happens without any notification to interested parties, who continue acting on outdated assumptions. | "assume yes and proceed" anti-pattern (src ↔ host 2026-05-18, caught early by host before drift hardened) | src-desktop |
| `transition_illegal` | State machine moves between two states whose direct transition is not in the spec; resulting task state is undefined. | spec §5 transition table → state-machine validator (src 2026-05-19 v0.2) | src-desktop |
| `voice_agent_is_executor_but_no_task_record` | Upload or other voice-driven action completes (or fails) with no `task.json` / `upload-task.md` ever written; system has no audit trail for the work. | 2026-05-18 MP4 incident (5.7MB video processed, nothing in tasks/) | danielle-desktop |
| `worker_self_report_passed_but_unverified` | Handoff treats a worker's COMPLETION-NOTICE as sufficient without code review / verbose test rerun / cross-snapshot drift check; missing artifacts or unbroadcast handoffs surface only after Mike-side pushback. | 2026-05-18 v0.1.1 substrate handoff (msg 014) before Mike's pushback forced verification pass | josh-desktop |

## Use rules

- Every `task.json` MUST have `failure_modes: [<enum>, ...]`. Empty list `[]` is permitted but discouraged — it asserts the task's plan has no defended-against failure modes, which is rarely true.
- Plan-time entries: failure modes the plan explicitly defends against. Reviewer asks "does the plan address each?"
- Postmortem-time entries (append-only via state_history): failure modes that occurred during execution but weren't on the plan. These are the patterns.json fuel.
- `patterns.json` aggregator MUST count per-enum-value occurrences across all tasks per day. High counts on plan-time entries = a class to invest defense tooling in. High counts on postmortem-time entries = a class to teach plan-time anticipation for.

## Draft-07 JSON Schema patch (for josh-desktop@mesh worker-a)

```diff
- "failure_modes": {
-   "type": "array",
-   "items": {"type": "string"}
- }
+ "failure_modes": {
+   "type": "array",
+   "items": {
+     "enum": [
+       "blocker_source_split_brain",
+       "completion_signal_ambiguous",
+       "cross_session_artifact_handoff_blindness",
+       "deadlock_on_missing_signal",
+       "decision_matrix_skipped_failure_mode_first_pass",
+       "false_negative_active_state",
+       "false_positive_active_state",
+       "in_flight_orphan",
+       "interleave_corruption",
+       "latency_budget_exceeded",
+       "orphan_after_crash",
+       "outbound_recipient_drift",
+       "parallel_shift_writer_race",
+       "parked_without_clock",
+       "permission_drift_breaks_protocol_channel",
+       "schema_field_unenforced",
+       "sentinel_traps_silent_skip",
+       "silent_drift",
+       "transition_illegal",
+       "voice_agent_is_executor_but_no_task_record",
+       "worker_self_report_passed_but_unverified"
+     ]
+   }
+ }
```

## Ratchet plan (for next canonical-schema snapshot)

1. josh-desktop@mesh worker-a absorbs the diff above into the canonical schema's `task.json` definition.
2. Bump canonical-schema → v0.1.2 (lockstep, per the existing reconciliation cadence).
3. Validator test additions:
   - Reject `failure_modes: ["arbitrary_string"]` (not in enum).
   - Accept `failure_modes: []` (empty allowed but discouraged).
   - Accept `failure_modes: ["orphan_after_crash", "interleave_corruption"]` (multi-value).
4. Smoke-test on a real migration: walk my done/ PoC task through the new validator and confirm its current `failure_modes: []` still passes (will be back-filled in v0.3 to include `interleave_corruption` and `deadlock_on_missing_signal` per the AND-gate analysis it contains).
