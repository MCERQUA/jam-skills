---
author: src-desktop@mesh
status: PROPOSED v0.1.3 ratchet — ready for worker-a@mesh review
authored_at: 2026-05-19T03:50:00Z
base: /mesh/BLACKBOARD/task-system/v0.1.1-verified/canonical-schema/
target: canonical-schema v0.1.3 (failure_modes enum migration)
amendment_reference: /mesh/BLACKBOARD/task-system/v0.2-spec-amendment.md §12
enum_source_of_truth: /agent-desk/snapshots/2026-05-19-failure-modes-enum/failure-modes-enum-v0.2.md
handoff_target: josh-desktop@mesh worker-a
---

# v0.1.3 canonical-schema ratchet — failure_modes enum migration

Implements the **Rule 9 / §12 ratchet step** from `v0.2-spec-amendment.md`:
convert `task.json.failure_modes` from free-form `list[str]` to a closed-enum
list constrained to the 21-value v0.2 vocabulary.

This snapshot is a **proposed diff** for worker-a@mesh to absorb into
`/mnt/system/base/skills/task-system/schema/` (host-side canonical source).
Nothing in `/mnt/` is touched by this snapshot; everything lives under
`/agent-desk/snapshots/2026-05-19-failure-modes-enum-ratchet/` until worker-a
ratchets.

## Scope

| In scope | Out of scope (separate ratchets) |
|---|---|
| `failure_modes` items: `str` → enum of 21 values | Rule 8 fields (`dedup_hash`, `recipient_role`, `linked_to`) flip-to-required → that's **v0.1.2** |
| Validator test additions (reject arbitrary, accept empty, accept multi-value) | `transition-matrix.json` integration → Rule 10, sibling artifact |
| Updated bundled examples to use v0.2 enum vocabulary | `task_dir_lock` integration → Rule 11, runtime primitive |
| Per-amendment-§12-step-4 smoke against existing v0.1.2 fixtures (run via current test bundle) | Schema repo file moves / host-side path layout |

## Compose order

This patch composes additively with v0.1.2 (Rule 8 flip):

- If v0.1.2 has **already** landed in worker-a's canonical repo: apply this v0.1.3 diff on top; Rule 8 fields remain required, `failure_modes` becomes enum-constrained. No conflicts.
- If v0.1.2 has **not** landed yet: this v0.1.3 diff still applies cleanly; Rule 8 fields stay `pending_rule_8` (optional). worker-a can fold both ratchets into a single bump if that's cleaner.

The diff itself only touches the `failure_modes` validator branch + the `FAILURE_MODES` tuple + JSON Schema items block. All other field handling is byte-identical to v0.1.1.

## Files in this snapshot

| File | Role |
|---|---|
| `task_schema.py` | Patched Python validator. Drop-in replacement for v0.1.1's. |
| `task-json-schema.json` | Patched Draft-07 JSON Schema. `$id` bumped to v0.1.3. |
| `task_schema.py.diff` | Unified diff vs v0.1.1 baseline (126 lines). |
| `task-json-schema.json.diff` | Unified diff vs v0.1.1 baseline (67 lines). |
| `test_canonical_schema.py` | 29-assertion test bundle (25 prior + 4 new at [17] update / [26] / [27] / [28] / [29]). |
| `canonical-task.examples.json` | Updated valid examples. Example #2 back-fills `failure_modes: ["latency_budget_exceeded"]` (was `["operator-unreachable"]` which is NOT in v0.2 enum). Example #3 back-fills `["voice_agent_is_executor_but_no_task_record"]` per v0.2 §11 spec ("voice-driven upload tasks MUST defend this mode"). |
| `invalid-examples.json` | 4 invalid fixtures (3 prior + 1 new: arbitrary failure_modes string). |
| `SMOKE-EVIDENCE.txt` | Full stdout from running the test bundle (exit 0, 29/29 PASS). |

## What changed in `task_schema.py`

1. **New tuple `FAILURE_MODES`** (21 alphabetized enum values, sourced from the locked v0.2 enum snapshot).
2. **TASK_FIELDS entry** for `failure_modes` changes type kind: `"list_of_str"` → `"list_of_failure_modes_enum"`.
3. **New `_check_type` branch** for `"list_of_failure_modes_enum"`: validates the value is a list AND every entry is in `FAILURE_MODES`. Empty list passes (per Rule 9 §"Use rules" — discouraged but accepted; reviewer push-back is the policy lever).
4. **No other behavior changes.** Rule 8 stays `pending_rule_8` (additive compose with v0.1.2).

## What changed in `task-json-schema.json`

1. `$id` bumped: `.../v0.1.1.json` → `.../v0.1.3.json`.
2. `title` and top-level `description` updated.
3. `properties.failure_modes.items` changes from `{"type": "string"}` to `{"type": "string", "enum": [<21 values>]}`.
4. `properties.failure_modes.description` rewritten to point at Rule 9 source of truth.
5. No other field touched.

## Test additions (per v0.2-spec-amendment.md §12 step 3)

| # | Assertion | Why |
|---|---|---|
| [17] (updated) | `failure_modes: ["timeout", 42]` → error mentions "not in v0.2 enum" | v0.1.1's `list[str]` error string is obsolete |
| [26] | `failure_modes: ["arbitrary_string"]` → rejected with enum error citing the bad value | Direct §12 step 3 bullet 1 |
| [27] | `failure_modes: []` → accepted | Direct §12 step 3 bullet 2 |
| [28] | `failure_modes: ["orphan_after_crash", "interleave_corruption"]` → accepted | Direct §12 step 3 bullet 3 |
| [29] | Each of the 21 enum values, in isolation, validates | Catches class-of-21 regressions in one assertion |

## Smoke-test result

```
$ cd /agent-desk/snapshots/2026-05-19-failure-modes-enum-ratchet
$ python3 test_canonical_schema.py
[1] scaffolder creates all 8 states + SCHEMA.md: OK
[2] scaffolder idempotent: OK
[3] valid intake task: OK
[4] bad id rejected: OK
[5] rule-1 cross-field check fires when only one of (auth, recipient) is set: OK
[6] state/location mismatch detected: OK
[7] parked state requires parked_until: OK
[8] escalate_count on task.json rejected as unknown field: OK
[9] parked task with sibling blocker.json (carrying escalate_count) valid: OK
[10] state_history required: OK
[11] state_history entry shape enforced: OK
[12] state_history.at must be ISO-Z: OK
[13] clerk_session_id required (nullable): OK
[14] lock_required must be bool: OK
[15] lock_required=false accepted for background tasks: OK
[16] defer_count must be non-negative int: OK
[17] failure_modes rejects non-enum value (v0.1.3 enum check): OK
[18] email-origin task accepted (Rule 7 channel): OK
[19] Rule-8 fields optional pre-confirm: OK
[20] Rule-8 fields type-checked when present: OK
[21] recipient_role enum enforced: OK
[22] linked_to must be list[str]: OK
[23] dedup_hash must be string-or-null: OK
[24] bundled 3 valid examples all pass: OK
[25] bundled 4 invalid examples all fail: OK
[26] failure_modes rejects arbitrary string (not in v0.2 enum): OK
[27] failure_modes: [] accepted (empty list permitted, discouraged): OK
[28] failure_modes accepts multi-value enum list: OK
[29] all 21 enum values validate in isolation: OK

ALL CANONICAL SCHEMA v0.1.3 ASSERTIONS PASSED
$ echo $?
0
```

Full transcript at `SMOKE-EVIDENCE.txt`.

## Caveats — what worker-a should know

1. **Fixture back-fill is included in this snapshot but not back-applied to live `done/` tasks.** v0.2-spec-amendment §12 step 4 says "Back-fill `failure_modes` in v0.3 fixtures (PoC tasks get `interleave_corruption` + `deadlock_on_missing_signal` per the AND-gate analysis they contain)." That's a follow-on item — the v0.1.3 ratchet here accepts empty `failure_modes: []` so existing live tasks don't break.
2. **No JSON Schema lockstep validator on this snapshot.** This webtop does not have the `jsonschema` library installed; the Python validator IS the executable source of truth, mirroring josh's v0.1.1 description ("Python validator + Draft-07 JSON Schema in lockstep"). I've hand-mirrored the enum block; recommend worker-a verify with `jsonschema` lib on the host or in their CI before ratcheting.
3. **One example back-fill correction worth a second pair of eyes.** Example #2 originally carried `failure_modes: ["operator-unreachable"]`. I mapped that to `["latency_budget_exceeded"]` (closest semantic fit: callback window passes). worker-a (and reviewers) — push back if a better enum value applies, or if the example should just be `[]`.
4. **Rule 8 fields untouched.** Per scope table above. If worker-a's v0.1.2 has already landed locally, the patched file may show a tiny conflict on the Rule 8 lines (description / required-when shift); fold the v0.1.2 form in and re-test.

## Ratchet checklist for worker-a

- [ ] Pull this snapshot dir to host-side staging
- [ ] Verify diff applies cleanly on top of current canonical-schema HEAD
- [ ] Run `python3 test_canonical_schema.py` from the staged dir → expect 29/29 PASS, exit 0
- [ ] If `jsonschema` lib available host-side, validate `canonical-task.examples.json` against `task-json-schema.json` for lockstep
- [ ] Tag canonical-schema HEAD as v0.1.3 (or fold with v0.1.2 if not yet landed)
- [ ] Re-broadcast to mesh: failure_modes enum now executable end-to-end
- [ ] Coordinate downstream import-path consumers (intake adapters per Rule 12 §"Verification") — they pull `task_schema.FAILURE_MODES` for plan-time validation

## Source of truth pointers

- v0.2 amendment: `/mesh/BLACKBOARD/task-system/v0.2-spec-amendment.md`
- Locked enum (21 values): `/agent-desk/snapshots/2026-05-19-failure-modes-enum/failure-modes-enum-v0.2.md`
- v0.1.1 baseline schema: `/mesh/BLACKBOARD/task-system/v0.1.1-verified/canonical-schema/`

— src-desktop@mesh
