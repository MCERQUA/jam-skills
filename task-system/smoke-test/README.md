# 2026-05-18 — E2E task-system smoke test (worker-c)

End-to-end smoke harness for the JamBot task system v0.1.1. Wires together
worker-a's canonical schema validator and worker-b's tenant scaffolder and
walks four mock tasks through the full state machine defined in
`/mesh/BLACKBOARD/meetings/2026-05-18-task-system-redesign/v0.1-spec-host.md`.

The harness is the bridge artifact for the 2026-05-19 nightly synthesize:
it proves the two upstream PoCs compose into a working pipeline before any
real tenant workspace is migrated.

---

## Layout

```
2026-05-18-smoke-test/
  smoke_test.py            ← Python harness (exit 0 = PASS, nonzero = FAIL)
  scenarios/
    email-origin.json      ← raised_by=brief, gmail thread source_ref
    sms-origin.json        ← raised_by=sms, twilio SID source_ref
    voice-origin.json      ← raised_by=voice, clerk_session_id populated
    parked-with-blocker/
      task.json            ← state=parked, parked_until in the past
      blocker.json         ← all 6 spec §3 fields
  README.md
  COMPLETION-NOTICE.md     ← written last, only on green
```

`scenarios/` ships valid task.json fixtures with `state=intake` (or
`state=parked` for the blocker case). The harness owns the lifecycle —
fixtures are inert data.

---

## What each scenario tests

| Scenario | Asserts |
|---|---|
| `email-origin` | Email-origin task (raised_by=brief, gmail thread ref) validates cleanly through intake → shop-floor → planned → scheduled → today → done. Rule 8 `recipient_role=mike` field is accepted. |
| `sms-origin` | SMS-origin task (raised_by=sms, Twilio SID, operator_phone set) survives the same five transitions. Confirms `operator_phone` field is still honored despite bun-desktop's earlier push to cut it. |
| `voice-origin` | Voice-origin task with `clerk_session_id` populated (src-desktop's voice-lane binding field) survives the same five transitions. |
| `parked-with-blocker` | Validator accepts `state=parked + parked_until`. All six §3 `blocker.json` fields present and `parked_until` parses to a real datetime. Seam-A `blocker_digest_cron` dry-run finds ≥1 due item and includes the task_id in the digest body. |

The full transition path in the spec is
`intake → shop-floor → planned → scheduled → today → done` (5 transitions).
With the initial intake entry already in `state_history`, the final task ends
with **6 entries**, which the harness asserts explicitly.

`scheduled_at` is populated on entry to `scheduled/`; `completed_at` and
`outcome` are populated on entry to `done/`. Re-validation happens after
every move, so the lifecycle is exercised against the validator at every
step — not just at the endpoints.

---

## How to run

```bash
cd /agent-desk/snapshots/2026-05-18-smoke-test
python3 smoke_test.py            # exit 0 on PASS
python3 smoke_test.py --no-cleanup   # keep /tmp/smoke-*/ for inspection
```

Requires Python 3.10+ (uses PEP 604 unions transitively via worker-a's
`task_schema.py`). No third-party packages.

The harness imports the upstream modules directly via `sys.path.insert`:

- `task_schema` from `/agent-desk/snapshots/2026-05-18-canonical-schema/`
- `scaffold_tenant` from `/agent-desk/snapshots/2026-05-18-tenant-scaffolder/`
- `blocker_digest_cron` from `/agent-desk/snapshots/2026-05-18-seam-a-poc/`
  (imported only for the dry-run digest assertion — its mesh-send path is
  never invoked)

No real emails, SMS, voice, or mesh messages are sent. No `/mesh/`,
`/peer-inbox/`, or `/agent-desk/sent/` paths are touched.

---

## Expected pass output

```
[smoke] workspace: /tmp/smoke-XXXXXXX
[smoke] scaffold created: ['intake', 'shop-floor', 'planned', 'scheduled', 'today', 'done', 'in-flight', 'parked']
[smoke] email-origin: PASS
[smoke] sms-origin: PASS
[smoke] voice-origin: PASS
[digest] dry_run — not sending; snapshot at /tmp/smoke-XXXXXXX/blocker-digest-runs/blocker-digest-<ts>.md
[smoke] parked-with-blocker: PASS
PASS: 4 scenarios
```

Exit code: `0`.

## Failure output

On any assertion failure the harness prints one line to stderr and exits
nonzero:

```
FAIL: scenario <name>: <reason>
```

Exit codes: `1` for an assertion failure, `2` for an unexpected exception.

---

## What the harness does (mechanically)

1. Creates `/tmp/smoke-<random>/` as a mock tenant workspace.
2. Calls `scaffold_tenant.scaffold(workspace, tenant="smoke-test-tenant")`
   and asserts all eight state subdirs exist (matches `task_schema.STATES`).
3. For each non-parked scenario:
   a. Copies the scenario `task.json` into `mock/tasks/intake/<task-id>/`.
   b. Runs `task_schema.validate_task_file` — must return `[]`.
   c. Walks the dir through `shop-floor → planned → scheduled → today →
      done`, updating `state`, appending to `state_history`, populating
      `scheduled_at` / `completed_at` / `outcome` as state demands.
   d. Re-validates after every move.
   e. Asserts final state is `done`, history is 6 entries, completion
      fields populated.
4. For `parked-with-blocker`:
   a. Copies `task.json` + `blocker.json` into `mock/tasks/parked/<task-id>/`.
   b. Validates `task.json` — confirms `state=parked` with `parked_until`
      is accepted.
   c. Checks the six required `blocker.json` fields per spec §3.
   d. Parses `parked_until` to a real `datetime`.
   e. Invokes `blocker_digest_cron.run(..., dry_run=True)` and asserts
      the snapshot body names the task_id.
5. Tears down the workspace (unless `--no-cleanup`).

---

## Rollback

```bash
rm -rf /agent-desk/snapshots/2026-05-18-smoke-test/
```

Nothing else to undo. The harness writes only to `/tmp/smoke-*/` and that
gets cleaned at end of run regardless of pass/fail.

---

## Inputs consumed

- v0.1 spec §3 task.json shape, §3 blocker.json shape, §5 transitions
- worker-a `task_schema` (`STATES`, `validate_task_file`, `TASK_FIELDS`)
- worker-b `scaffold_tenant.scaffold`
- seam-A `blocker_digest_cron.run(dry_run=True)` for the digest assertion
