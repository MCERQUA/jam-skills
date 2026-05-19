# Milestone-4 SYNTHESIS

**Synthesizer:** josh-desktop@mesh
**Source dispatches:** host msg 2026-05-19-001 (parent) + 3 sub-task briefs to worker-a/b/c.
**Status:** ready for host review + deploy.

---

## 1. Per-worker status

| Worker   | Field added            | Deliverable count | Self-verification                        |
|----------|------------------------|-------------------|------------------------------------------|
| worker-a | `notification_policy`  | 4 files (design + 3 patches) | patches apply clean; 3/3 mode examples valid; negatives reject |
| worker-b | `research_at`          | 5 files (design + 3 patches + cron-template) | patches apply clean; 25/25 canonical tests PASS; 5/5 examples valid; 3/3 v0.1.3 originals still validate |
| worker-c | smoke step 9 (e2e)     | 5 files (design + 2 fixtures + patch + sample-run + DONE) | smoke_test.patch parses; steps 1–8 still PASS on v0.1.3; step 9 fails-as-designed pre-peer-merge |

All three workers wrote DONE.txt to their dir.

---

## 2. Schema header conflict (mechanical)

Both worker-a and worker-b independently bump `$id`/`title`/`description` to v0.1.4. Property additions are non-conflicting (different keys at different lines), but the header diff is at the same 3 lines in both patches, so applying both serially produces a reject on the second.

**Resolution:** apply property additions only from each patch and ship a single merged header — recommended:

```json
"$id": "https://jam-bot.com/schemas/task-json/v0.1.4.json",
"title": "JamBot task.json (canonical v0.1.4 — milestone-4)",
"description": "v0.1.3 + notification_policy (delivery cadence) + research_at (two-phase schedule). Both additive; both optional with sensible defaults. v0.1.3 records validate clean under v0.1.4."
```

---

## 3. Cross-worker drifts (REAL — flagged before deploy)

### 3a. Enum casing — worker-a snake_case vs worker-c kebab-case

- **worker-a** chose `"inline" | "roll_up_daily" | "on_finding"` (snake_case) — explicitly justified to match the v0.2 `failure_modes` enum convention rather than the kebab-case `state` field. Reasonable principle: high-cardinality enums lock as snake_case.
- **worker-c** smoke fixtures + assertions use `"roll-up-daily" | "on-finding"` (kebab-case) — followed the brief and host msg verbatim.

**Recommendation:** **snake_case wins.** Worker-a's reasoning is principled and matches the most recent locked enum (failure_modes v0.2). The host msg's kebab-case was informal phrasing, not a normative declaration.

**Action required for worker-c:**
- `milestone-4-scenario.json`: change `notification_policy: "on-finding"` to `{"mode": "on_finding", "on_finding_threshold": {...}}` — note also the **shape change**: worker-a made the field a nested object with `mode` subkey, not a flat enum (see §3c).
- `milestone-4-invalid.json`: change `"every-5-minutes"` to `"every_5_minutes"` (or similar snake_case invalid).
- Assertion text in `smoke_test.patch`: replace `"roll-up-daily"`/`"on-finding"` with snake_case + nested-object access.

This is a cosmetic fixup — structural patch shape unchanged. Worker-c already flagged 4 TODO markers anticipating peer alignment.

### 3b. Default-resolver location — worker-b scheduler-side vs worker-c expects `task_schema` helper

- **worker-b** put the 60-min default-resolution rule **in the cron template (scheduler-side)**, NOT in `task_schema.py`. The field stays `null` in the record; the scheduler computes effective `research_at = scheduled_at - 60min` at fire-time. Principled reason: avoids forcing every intake adapter to know the rule.
- **worker-c** assertion 9.4 calls `task_schema.resolve_defaults(record)` and expects `record["research_at"]` to be populated. **No such function exists** in worker-b's patch.

**Recommendation:** **add a thin `task_schema.apply_defaults(record)` helper.** Worker-b's scheduler-side computation stays canonical, but expose a pure-Python helper at the schema layer so:
- (i) downstream tools (briefs, displays) can compute the effective time without reimplementing the rule
- (ii) worker-c's smoke assertions work without faking a cron tick
- (iii) the 60-min constant lives next to the field definition (addresses worker-b's Q3)

Proposed helper (single function, snake_case naming):

```python
DEFAULT_RESEARCH_LEAD_SECONDS = 3600

def apply_defaults(record):
    """Returns a shallow copy with research_at and notification_policy
    materialized to their effective values. Does NOT mutate input.
    Does NOT write to file."""
    out = dict(record)
    if out.get("research_at") is None and out.get("scheduled_at"):
        sched = _parse_iso_z(out["scheduled_at"])
        out["research_at"] = _format_iso_z(sched - timedelta(seconds=DEFAULT_RESEARCH_LEAD_SECONDS))
    if "notification_policy" not in out:
        out["notification_policy"] = {"mode": "roll_up_daily"}
    return out
```

**Owner:** either worker-a or worker-b — small enough that the synthesizer (me) can write it inline if host approves the merge.

### 3c. Field SHAPE drift for `notification_policy` (worker-c blast radius)

Worker-a's final shape is a **nested object** with a `mode` subkey (justified for forward-compat with `on_finding_threshold`). Worker-c's fixtures + assertions treat `notification_policy` as a **flat string enum**. This is a bigger fixup than §3a casing — assertion 9.2 (`record["notification_policy"] == "on-finding"`) becomes `record["notification_policy"]["mode"] == "on_finding"`.

**Action required for worker-c (rolled into the same fixup pass as §3a):**
- Fixtures: nest the value under `{"mode": ...}`.
- Assertions: access via `.["mode"]` subkey.
- Error-message substring 9.6: still works (validator names the field path).

---

## 4. Recommended deploy order

1. **Host pick:** ratify snake_case vs kebab-case (recommend snake_case per §3a).
2. **Host pick:** ratify the `apply_defaults` helper location (recommend `task_schema.py` per §3b).
3. Apply worker-a property addition + worker-b property addition + single merged header bump → `task-json-schema.json` v0.1.4.
4. Apply worker-a `task_schema.patch` + worker-b `task_schema.patch` + new `apply_defaults` helper → `task_schema.py`.
5. Apply both `canonical-task.examples.patch` (non-overlapping).
6. **Worker-c fixup pass** (§3a + §3c): align casing + nest shape + swap `resolve_defaults` → `apply_defaults`.
7. Apply worker-c `smoke_test.patch` + add fixtures to `scenarios/`.
8. Run `python smoke_test.py` → expect step 9 PASS.
9. Run `python test_canonical_schema.py` → expect 25/25 still PASS (worker-b verified) + new milestone-4 assertions if added.
10. Host bumps schema reference in 7 downstream deployed snapshots to v0.1.4 (worker-b §5 warning).
11. Cron template installed via two-line crontab pattern (worker-b §7 example).

---

## 5. Open questions

Collated in `OPEN-QUESTIONS.md` — 9 total, 3 per worker, grouped by theme:
- **Notification cadence** (worker-a Q1/Q2/Q3): inline firing scope, threshold enum lock timing, per-recipient-role override.
- **Schedule semantics** (worker-b Q1/Q2/Q3): overdue-research behavior, research_completed_at field, default-constant location.
- **Synthesis-level** (added by me): snake_case-vs-kebab ratification, apply_defaults helper location, worker-c fixup ownership.

---

## 6. Mike-input dependencies

Items that can ship NOW without Mike-input:
- v0.1.4 schema with both new fields, defaults applied.
- All 3 worker patches (modulo §3 fixups).
- Cron template + worker-c smoke (modulo §3 fixups).

Items blocked on Mike-input (NON-blocking for v0.1.4 schema ship):
- `on_finding_threshold` inner shape (worker-a §3) — schema accepts any object, evaluator service is downstream.
- "inline firing scope" (worker-a Q1) — current default is `done`-only.
- Per-recipient-role override (worker-a Q3) — current default is "policy honored as-written."

Per Mike's standing rule (host msg 2026-05-19-001 §6): ship the schema, surface the open questions, don't idle waiting.
