# canonical-schema v0.1.4 — Changelog vs v0.1.3

**Trigger:** host msg 2026-05-19-001 ratified milestone-4 (notification_policy + two-phase schedule) → pivoted to milestone-5 (this deployment-ready bundle).
**Date:** 2026-05-19
**Author:** worker-a@mesh (synthesis of worker-a + worker-b patches; conflict resolution per `/agent-desk/snapshots/2026-05-19-milestone-4-notification-cadence/MERGE-NOTES.md` §"Proposed unified header" — applied verbatim).

---

## What changed

### `task-json-schema.json`

- **Header** — replaced verbatim from MERGE-NOTES.md §"Proposed unified header":
  - `$id`: `…/task-json/v0.1.3.json` → `…/task-json/v0.1.4.json`
  - `title`: "JamBot task.json (canonical v0.1.4 — notification_policy + two-phase schedule)"
  - `description`: rewritten to mention both additive features + back-compat guarantee
- **New optional field `research_at`** (worker-b) — inserted between `recipient` and `scheduled_at` in `properties`. Pattern-validated ISO-Z, nullable, NOT in `required[]`.
- **New optional field `notification_policy`** (worker-a) — appended after `linked_to` in `properties`. Object with `mode` enum (`inline` | `roll_up_daily` | `on_finding`, default `roll_up_daily`) + nullable `on_finding_threshold` sub-object. `additionalProperties: false` on the policy object. NOT in `required[]`.
- **`additionalProperties: false`** on the root object is unchanged — old v0.1.3 readers will reject any record carrying either new field (this is the expected forward-incompatible side of additive schema evolution; readers update lockstep at this ratchet).

### `task_schema.py`

- **Module docstring** v0.1.3 → v0.1.4 (verbatim per MERGE-NOTES.md `task_schema.py` line 2). Body extended with milestone-4 paragraph describing both new fields.
- **New constant `NOTIFICATION_MODES`** (worker-a) — `("inline", "roll_up_daily", "on_finding")` — module-level tuple, exported for downstream consumers.
- **New `TASK_FIELDS` entries:**
  - `"research_at": ("optional", "iso_z_or_null")` (worker-b)
  - `"notification_policy": ("optional", "notification_policy")` (worker-a)
- **New `_required()` branch** — `"optional"` always returns `False` (worker-b's contribution; required by the new `"optional"` `required_when` key).
- **New `_check_type()` branch** for `kind="notification_policy"` — validates: must be a dict; only `mode` and `on_finding_threshold` allowed; `mode` required and in `NOTIFICATION_MODES`; `on_finding_threshold` if present must be dict-or-null. Inner shape of threshold deliberately NOT validated at v0.1.4 (mirrors the v0.1.x failure_modes → v0.2 enum ratchet pattern).

### `canonical-task.examples.json`

- **Existing 3 v0.1.3 records — minimally augmented** to demonstrate the new fields:
  - `2026-05-18-0915-cca-domain-quote-acme` (intake) → `notification_policy: {"mode": "roll_up_daily"}` (explicit default)
  - `2026-05-18-1830-cca-followup-decking` (scheduled) → adds `research_at: "2026-05-19T13:00:00Z"` + `notification_policy: {"mode": "inline"}`
  - `2026-05-18-1411-kitchen-cabinets-upload` (in-flight) → `notification_policy: {"mode": "on_finding", "on_finding_threshold": {...}}` with a sample threshold shape (TBD-pending-Mike-input)
- **Appended 2 worker-b schedule-demo records** (per MERGE-NOTES.md §"Third conflict" — worker-a's notification examples first, worker-b's schedule examples second):
  - `2026-05-19-0930-josh-brief-task-74-plan` (scheduled — both phases populated, default 60-min delta)
  - `2026-05-19-1015-cca-research-blocker-parked` (parked — demonstrates research-blocker flow + `permission_drift_breaks_protocol_channel` failure mode)
- Total examples: **5** (was 3).

### `invalid-examples.json`

- Existing 3 invalid records preserved (Rule-1, legacy `escalate_count`, missing `state_history`).
- Appended 4 new invalid records:
  - `2026-05-19-2200-bad-notif-mode` — `notification_policy.mode: "roll-up-daily"` (kebab — enum is snake_case)
  - `2026-05-19-2201-bad-research-at` — `research_at: "2026/05/19 13:00"` (wrong format — ISO-Z required)
  - `2026-05-19-2202-bad-failure-mode` — `failure_modes: ["arbitrary_string_not_in_enum"]` (re-affirms v0.1.3 enum lock)
  - `2026-05-19-2203-notif-extra` — `notification_policy: {"mode": "inline", "unknown_key": "x"}` (extra field rejected)
- Total invalid examples: **7** (was 3).

### `test_canonical_schema.py`

- Docstring v0.1.1 → v0.1.4.
- Existing tests `[1]`–`[25]` unchanged. All still PASS.
- Appended **12 new tests `[26]`–`[37]`** covering:
  - [26] valid `notification_policy.mode='inline'`
  - [27] kebab-case mode rejected (snake_case enforced)
  - [28] missing `mode` rejected
  - [29] extra subkey rejected
  - [30] non-object value rejected
  - [31] absent policy (default-by-absence) accepted
  - [32] valid `research_at` ISO-Z accepted
  - [33] bad `research_at` format rejected
  - [34] `research_at=null` accepted
  - [35] backward-compat: v0.1.3-shape record (no new fields) validates under v0.1.4
  - [36] all 3 enum modes accepted
  - [37] `NOTIFICATION_MODES` module constant present + correct shape
- **Total assertions: 37 PASS** (was 25 — exceeds the milestone-5 ≥30 target).

---

## What did NOT change

- All other tests `[1]`–`[25]` — unchanged. PASS.
- All other schema fields (`id`, `state`, `raised_at`, `raised_by`, `source_ref`, `summary`, `tenant`, `operator_phone`, `email_authorized_by_mike`, `recipient`, `scheduled_at`, `parked_until`, `completed_at`, `outcome`, `state_history`, `clerk_session_id`, `lock_required`, `defer_count`, `failure_modes`, `dedup_hash`, `recipient_role`, `linked_to`) — unchanged.
- Rule-1 cross-field invariant — unchanged.
- State-conditional required fields (`scheduled_at` if scheduled/today/done, `parked_until` if parked, `completed_at`+`outcome` if done) — unchanged.
- `failure_modes` 21-value enum — preserved from v0.1.3 lock (re-affirmed by new invalid-example `2026-05-19-2202-bad-failure-mode`).

## What was deliberately NOT done (per host directive)

- **NO `task_schema.apply_defaults` helper.** Host did not ratify worker-b's open question Q8 — apply patches verbatim. Reader-side / scheduler-side defaults are applied by downstream consumers (worker-c's smoke test exercises this), NOT by the validator.
- **NO pre-resolution of the 9 open questions** from milestone-4 worker designs (3 from worker-a, 3 from worker-b, 3 from worker-c). Host said "let broader mesh weigh in" at the nightly synthesize; documented in `/agent-desk/snapshots/2026-05-19-milestone-4-notification-cadence/OPEN-QUESTIONS.md`.
- **NO changes to worker-c's smoke-test patch TODO markers** — they're mechanical (await worker-b resolver symbol names) and host will resolve during synthesize.

---

## Verification (2026-05-19, fresh)

```
python3 test_canonical_schema.py    →  37/37 PASS
backward-compat check               →  3/3 v0.1.3 originals validate under v0.1.4
Draft-07 cross-check                →  schema is valid Draft-07
                                       5/5 v0.1.4 examples validate
                                       7/7 invalid examples rejected
JSON validity                       →  schema + examples + invalid examples parse clean
Python AST                          →  task_schema.py syntax OK
```

## failure_modes enum status (milestone-5 task 2)

Re-affirmed. The 21-value enum locked at v0.1.3 by src-desktop@mesh on 2026-05-18T21:05Z (per `/mesh/BLACKBOARD/task-system/v0.2-spec-amendment.md` §3 + §12) carries forward unchanged into v0.1.4. New invalid-example `2026-05-19-2202-bad-failure-mode` provides an additional negative-case guard against drift.

Enum values (lockstep contract with `task_schema.FAILURE_MODES`):
`blocker_source_split_brain`, `completion_signal_ambiguous`, `cross_session_artifact_handoff_blindness`, `deadlock_on_missing_signal`, `decision_matrix_skipped_failure_mode_first_pass`, `false_negative_active_state`, `false_positive_active_state`, `in_flight_orphan`, `interleave_corruption`, `latency_budget_exceeded`, `orphan_after_crash`, `outbound_recipient_drift`, `parallel_shift_writer_race`, `parked_without_clock`, `permission_drift_breaks_protocol_channel`, `schema_field_unenforced`, `sentinel_traps_silent_skip`, `silent_drift`, `transition_illegal`, `voice_agent_is_executor_but_no_task_record`, `worker_self_report_passed_but_unverified`.
