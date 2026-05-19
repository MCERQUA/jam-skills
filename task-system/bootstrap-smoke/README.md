# bootstrap-smoke — end-to-end Rule 8 milestone smoke test

Walks a mock tenant (`acme`) through scaffold → seed prior state →
`load_context` → `SessionContext` helpers → intake adapter (accept) →
intake adapter (reject via `source_ref` collision) → re-bootstrap. Proves
the full stack works together — final piece of the Rule 8 bootstrap
milestone.

## Run

```bash
# tear down /tmp workspace on exit
python3 smoke_test.py

# keep the workspace for inspection
python3 smoke_test.py --no-cleanup
```

Exits **0 on PASS**, **non-zero on FAIL**. PASS line is
`PASS: 8 scenarios`. On failure, `FAIL: scenario <name>: <reason>` lands
on stderr.

## What it exercises

Each numbered step here lines up with a `[smoke] (N) ... PASS` line in
the runner output, so the trailing log reads as a checklist.

| #  | Step                                       | What it proves                                                                                                                                   |
|----|--------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| 1  | `scaffold`                                 | `scaffold_tenant.scaffold` creates all 8 state subdirs + `manifest.json` for the `acme` tenant.                                                  |
| 2  | seed prior task state                      | Drops 4 fixtures (shop-floor, parked + blocker, scheduled, done) into the scaffolded tree. Each one round-trip validates under v0.1.3.           |
| 3  | seed history                               | Voice transcript, gmail thread, sms thread, reflection (today-3), ledger (yesterday) — all in the layout `task_bootstrap.load_context` reads.    |
| 4  | `load_context`                             | All documented keys present; `open_task_count == 3` (done/ excluded); 1 gmail + 1 sms thread loaded (only for source_refs of open tasks); voice non-None. |
| 5  | `SessionContext` helpers                   | `all_open_tasks == 3`, `find_tasks_by_source_ref(<scheduled>)` returns 1, `thread_history_for(<gmail-id>)` returns the loaded messages, `recent_blockers()` returns just the parked task. |
| 6  | intake adapter — accept                    | `manual_intake.intake_manual` with a fresh summary + unique source_ref returns `verdict=accept` and writes `tasks/intake/<id>/task.json` that validates under v0.1.3. |
| 7  | intake adapter — reject via source_ref     | Re-running with the SAME `source_ref` as the seeded scheduled task fires `source_ref_collision` → `verdict=reject`, no new file, surfaces the existing task id. |
| 8  | re-bootstrap                               | Fresh `load_context` after the accept sees the new task under `open_tasks["intake"]` and `open_task_count == 4`.                                  |

## Scenarios (`scenarios/`)

| File                          | Purpose                                                                                                |
|-------------------------------|--------------------------------------------------------------------------------------------------------|
| `shop-floor-task.json`        | Email-origin task seeded into `tasks/shop-floor/`. Its `source_ref` is the gmail-thread id; loader uses it to find the gmail thread file. |
| `parked-task.json`            | SMS-origin parked task. `parked_until` is in the past so the resurface-clock has already fired.        |
| `parked-blocker.json`         | Sibling `blocker.json` for the parked task. Drives the seam-A digest cron contract.                    |
| `scheduled-task.json`         | SMS-origin scheduled task. Its `source_ref` is the trigger for step 7's source_ref-collision reject.   |
| `done-task.json`              | Completed task. MUST NOT appear in `open_tasks` (step 4's done-exclusion assertion).                    |
| `voice-transcript.md`         | Synthetic morning standup transcript. Loader picks up `<workspace>/memory/<today>-conversation.md`.    |
| `gmail-thread.json`           | Synthetic email thread. Loader keys these by source_ref; only loaded if an open email-origin task references the same id. |
| `sms-thread.json`             | Synthetic SMS conversation. Loader keys these by `operator_phone`.                                      |
| `reflection.md`               | Synthetic daily reflection at today-3.                                                                  |
| `ledger.jsonl`                | 3 ledger entries. Smoke test seeds both `2026-05-18.json` (loader contract — `.json` array) and `2026-05-18.jsonl` (line-per-entry, the brief's filename). |

## Dependency wiring

`smoke_test.py` uses `sys.path` inserts to import all upstream modules —
the pattern matches `/agent-desk/snapshots/2026-05-18-smoke-test/smoke_test.py`.
The deployed v0.1.3 schema is pinned via the `TASK_SYSTEM_SCHEMA_DIR` env
var BEFORE `intake_common` is imported, so adapter writes validate against
v0.1.3 (failure_modes enum locked, all Rule 8 fields required).

| Snapshot                                                  | Role                                |
|-----------------------------------------------------------|-------------------------------------|
| `2026-05-19-canonical-schema-v0.1.3/`                     | Schema validator + enum reference   |
| `2026-05-18-tenant-scaffolder/`                           | Workspace directory creation        |
| `2026-05-18-intake-dedupe/`                               | `dedupe.scan_for_duplicates`        |
| `2026-05-18-intake-internal/`                             | `manual_intake.intake_manual` (+ `intake_common`) |
| `2026-05-19-rule-8-bootstrap/`                            | `task_bootstrap.load_context`       |
| `2026-05-19-session-context/`                             | `session_context.start_task_session`|

## Constraints honoured

- **No external I/O.** Zero mesh sends, zero emails, zero SMS, zero
  network. All reads/writes stay under
  `/tmp/bootstrap-smoke-<random>/<tenant>/`.
- **Determinism.** Mock data is checked into `scenarios/`; the mock
  workspace is built fresh per run from those fixtures; `today` is pinned
  to `date(2026, 5, 19)` so reflection/ledger windows resolve the same
  way every run.
- **Teardown.** `/tmp/bootstrap-smoke-<random>/` is removed in the
  `finally` block unless `--no-cleanup` is passed.
- **Output scope.** This snapshot writes nothing outside
  `/agent-desk/snapshots/2026-05-19-bootstrap-smoke/`.

## Expected output

```
[smoke] workspace: /tmp/bootstrap-smoke-XXXXXXXX/acme
[smoke] scaffold created: ['intake', 'shop-floor', 'planned', 'scheduled', 'today', 'done', 'in-flight', 'parked']
[smoke] (1) scaffold: PASS
[smoke] (2) seed prior task state: PASS
[smoke] (3) seed history (voice/gmail/sms/reflection/ledger): PASS
[smoke] (4) load_context — keys + counts + threads + transcript: PASS
[smoke] (5) SessionContext helpers: PASS
[smoke] (6) intake adapter — accept new summary: PASS
[smoke] (7) intake adapter — reject on source_ref collision: PASS
[smoke] (8) re-bootstrap — new intake task visible, count==4: PASS
PASS: 8 scenarios
```

## References

- Spec: `/mesh/BLACKBOARD/task-system/v0.1.1-spec-amendment.md` §Rule 8
- Prior smoke test (worker-c, 2026-05-18 lifecycle):
  `/agent-desk/snapshots/2026-05-18-smoke-test/`
