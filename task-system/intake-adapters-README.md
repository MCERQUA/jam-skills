# Task System — Intake Adapters Milestone (v0.1.2 substrate)

**Status:** verified locally on josh-desktop@mesh, awaiting host docker-cp.
**Predecessor:** v0.1.2 canonical schema bundle (deployed earlier 2026-05-18 at `/mnt/system/base/skills/task-system/`).
**Spec:** v0.1.1 amendment Rule 7 + Rule 8 (`/mesh/BLACKBOARD/task-system/v0.1.1-spec-amendment.md`).

Three sealed snapshots — each with `COMPLETION-NOTICE.md` and a passing test suite. Together they implement the intake-adapter side of Rule 7 ("all channels feed one pipeline") and the dedupe-scanner side of Rule 8 ("scan before promoting intake→shop-floor").

## Snapshots in this bundle

| Snapshot | Owner | Role | Tests |
|---|---|---|---|
| `2026-05-18-intake-dedupe/` | josh-desktop@mesh (completed worker-a's role after interrupt) | `compute_dedup_hash` + `scan_for_duplicates` (Rule 8 contract). Exposes both worker-b kwargs interface and worker-c record-dict compat wrapper. | 15 assertions PASS |
| `2026-05-18-intake-internal/` | worker-b@mesh | mesh + manual + brief intake adapters. Uses `intake_common.finalize_intake()` shared pipeline. | 7 unittest tests PASS |
| `2026-05-18-intake-external/` | worker-c@mesh | email + SMS + voice intake adapters. Uses `intake_common.build_and_file()` shared pipeline. | 12 named assertions PASS |

**Combined: 34 named assertions PASS, all integration-tested against the real (not mocked) dedupe library.**

## Why two intake-common modules

Workers b and c each authored their own `intake_common.py` — different return shapes, different agent-URI conventions for state_history, different dedupe interfaces. Rather than force a refactor of one to match the other, the dedupe library exposes BOTH interfaces:

- **`scan_for_duplicates(*, workspace, tenant, source_ref, summary, dedup_hash)`** — worker-b's explicit-kwarg contract. Returns `{verdict, existing_task_id, match_reason}`. Verdict ∈ `{accept, reject, escalate}`.
- **`scan(workspace, record)`** — worker-c's record-dict compat wrapper. Returns `{verdict, linked_to, existing_id}`. Verdict ∈ `{accept, reject}` (escalate normalizes to reject).

Both interfaces share the same scan logic underneath. No correctness drift; minimal cosmetic drift documented below.

## Cosmetic drift (intentional, no correctness impact)

| Aspect | worker-b | worker-c | Notes |
|---|---|---|---|
| Return shape | `{verdict, task_id, task_path, linked_to, match_reason, dedup_hash}` | `{verdict, task_id, path_written}` | Both work; consumers adapt |
| `recipient_role` default at intake | `None` | `"mike"` | Both valid per schema (`["string", "null"]`). worker-c is more aligned with the spec default for status/digest. |
| State_history `by` field | `mesh-intake-adapter@mesh` (static) | `{tenant}-email-intake@mesh` (tenant-prefixed) | worker-c's is more informative for forensics |
| Helper name | `finalize_intake()` | `build_and_file()` | Functionally equivalent |

If host wants alignment, easiest is to standardize on worker-c's `recipient_role="mike"` default in worker-b's `build_intake_record()` (one-line edit in `intake_common.py`). Flagging not blocking.

## Rule 7 channel coverage (6 adapters across 6 channels)

| `raised_by` | Adapter | Owner | Source ref form |
|---|---|---|---|
| `mesh` | `mesh_intake.intake_from_mesh_message` | worker-b | `<source_ref>` or `mesh:<sender>:<at>` fallback |
| `manual` | `manual_intake.intake_manual` (also CLI) | worker-b | required user-supplied string |
| `brief` | `brief_intake.intake_from_brief_item` | worker-b | `<gmail-thread-id>` |
| `email` | `email_intake.intake` | worker-c | `<gmail_thread_id>` |
| `sms` | `sms_intake.intake` | worker-c | `<twilio-sid>` |
| `voice` | `voice_intake.intake` | worker-c | `<session_id>:line:<line_index>` |

All 6 adapters:
- Populate every required v0.1.2 field including `dedup_hash`, `recipient_role`, `linked_to`
- Initialize `state_history` with one entry tagged by their per-channel agent URI
- Call dedupe before writing — verdict=reject path does NOT touch disk
- Return a dict the tenant agent runtime can introspect

## Rule 8 dedupe contract — what fires what

| Scan finding | Verdict | Action by adapter |
|---|---|---|
| Same-tenant `source_ref` collision (any state, incl `done/`) | `reject` | No disk write; returns existing task_id |
| Same-tenant exact-summary match on open-state task | `escalate` | Worker-b: writes with `linked_to` + drops `host-question.md`. Worker-c: normalizes to reject (no write). |
| Cross-tenant exact-summary match (any state) | `escalate` | Same as above |
| No match | `accept` | Normal write |

`done/` is intentionally excluded from same-tenant semantic match because completed tasks don't preclude re-intake of the same intent. Cross-tenant `done/` IS still scanned because cross-tenant matches are rare and worth flagging regardless.

## Verification matrix run on this bundle (2026-05-18)

```
intake-dedupe        test_dedupe.py              15 assertions  PASS
intake-internal      test_intake_internal.py      7 unittest     PASS  (using real dedupe: True)
intake-external      test_intake_external.py     12 assertions  PASS
                                                  ─────────────────────
                                                  34 assertions, all green
```

Round-trip integration:
- Every adapter output validates against the deployed v0.1.2 schema (`/mnt/system/base/skills/task-system/schema/task_schema.py`)
- Both interfaces resolve to the same scan logic — confirmed by test_dedupe.py [11-13] (compat wrapper round-trip)
- Cross-tenant dedupe scan walks `workspace.parent` to find sibling tenants — works under the per-tenant scaffold layout

## Deploy order (recommended)

1. `intake-dedupe/` → `/mnt/system/base/skills/task-system/dedupe/` (shared mount)
2. `intake-internal/` → `/mnt/system/base/skills/task-system/intake/internal/`
3. `intake-external/` → `/mnt/system/base/skills/task-system/intake/external/`

The two intake-common modules import dedupe via `sys.path` insertion — if deploy paths differ from the snapshot layout, update each module's `_DEDUPE_DIR` constant accordingly. (Same pattern as the schema bundle: the run-smoke wrapper host wrote earlier handles this.)

## Known v0.2 surface (not in this bundle)

- **No real external connections** — adapters accept payload dicts. Tenant agent runtime is responsible for the gmail OAuth / Twilio webhook / OVU SDK fetch and parse into a payload dict before invoking the adapter. This is intentional per the "no external I/O" constraint and matches the existing seam-A pattern.
- **`recipient_role` default alignment** — worker-b sets `None`, worker-c sets `"mike"`. v0.2 to pick one (recommendation: worker-c's `"mike"` matches spec default).
- **State_history `by` agent URI form** — worker-b static, worker-c tenant-prefixed. v0.2 standardize.
- **Fuzzy-hash matching** — `dedup_hash` is currently a coarse `sha1:<tenant>:<source-ref>:<shingle>` label, not a true hash. v0.2 to add proper hashing + similarity scoring (the `dedup_hash` arg is already accepted by `scan_for_duplicates` for forward compatibility).
- **`failure_modes` enum** — src-desktop locked the v0.2 enum at 21:24Z (21 values). Absorbs at the next canonical-schema ratchet, not this bundle.
- **danielle's upload-specific fields** (`upload_filename`, `upload_size_bytes`, `upload_status`) — flagged in her schema-shape reply for v0.3.

## References

- v0.1.1 spec amendment: `/mesh/BLACKBOARD/task-system/v0.1.1-spec-amendment.md`
- Canonical schema (deployed): `/mnt/system/base/skills/task-system/schema/`
- Tenant scaffolder (deployed): `/mnt/system/base/skills/task-system/scaffold/`
- voice-active (deployed, Rule 5 AND-gate): `/mnt/system/base/skills/task-system/voice-active/`
- failure_modes enum lock: `/agent-desk/inbox/.read/2026-05-18-001-src-desktop-v0-2-failure-modes-enum-locked-schema-patch-ready-for-worker.md`
