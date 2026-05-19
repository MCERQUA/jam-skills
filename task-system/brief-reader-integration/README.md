---
author: src-desktop@mesh
status: DELIVERED v0.3 (REVISION 2, replacing 2026-05-19-brief-aggregate-reader/)
delivered_at: 2026-05-19T03:40:00Z
spec_ref: v0.2 spec amendment Rule 9 — consumer-side render contract
host_backlog: option #3 v2 from 2026-05-19-001-host-morning-brief-shape-option-1-file-exists.md
target_files: /home/mike/MIKE-AI/scripts/email-processor/{morning_brief.py, morning-brief-src.py}
upstream: /agent-desk/snapshots/2026-05-19-patterns-aggregator/
supersedes: /agent-desk/snapshots/2026-05-19-brief-aggregate-reader/ (initial pre-spec build)
---

# brief-reader-integration — patterns aggregate → morning brief (v0.3 R2)

Production-ready integration package for `morning_brief.py` per host's option-#3 spec (inbox 2026-05-19-001-host-morning-brief-shape-option-1-file-exists.md).

**Differences from R1 (`2026-05-19-brief-aggregate-reader/`):**
- Renamed module: `aggregate_summarizer.py` (host-suggested name, replaces `brief_aggregate_reader.py`)
- Primary entry: `gather_patterns_aggregate()` per host spec (replaces `render_for_brief()`)
- **Yesterday-by-calendar primary path** per host spec (with fallback to most recent + warning, defending `silent_drift`)
- **Tie-case surfacing**: ≥2 failure_modes or blocker_patterns sharing top count are all surfaced alphabetically, with explicit "tied" labeling
- Concrete `MERGE-INSTRUCTIONS.md` anchored on the BLACKBOARD-read code pattern the host disclosed (lines anchored on `distilled` variable + `nightly-reflections` read block)
- Test count: 14 assertions (down from 18) — tighter, all required-by-spec scenarios covered

## Files

| File | Purpose | Verification |
|---|---|---|
| `aggregate_summarizer.py` | Library + CLI. `gather_patterns_aggregate()` one-call helper for the brief. | 14-assertion test |
| `test_aggregate_summarizer.py` | Round-trip via real `patterns_aggregator`; ties / empty / malformed / fallback / staleness | **14/14 PASS** |
| `MERGE-INSTRUCTIONS.md` | 3-edit patch with code anchors (host disclosed file shape but not full source) | — |
| `COMPLETION-NOTICE.md` | Delivery marker | — |

## Verification

```
$ python3 test_aggregate_summarizer.py
aggregate_summarizer: 14/14 assertions PASS
```

Test coverage (per host spec "12-15 assertions covering ties + empty + malformed"):

| # | Scenario |
|---|---|
| 1 | Yesterday file found (no fallback path taken) |
| 2 | Tied failure_modes — both members surfaced alphabetically |
| 3 | Tied failure_modes — count semantics correct |
| 4 | Tied recurring patterns — both members surfaced alphabetically |
| 5 | Tied brief block contains "tied at N occurrences each" label |
| 6 | Tied recurring blocker block surfaces both patterns |
| 7 | Empty cycle → reviewer nudge ("rarely accurate") |
| 8 | Empty cycle still reports zero counts cleanly |
| 9 | No-aggregates directory → fallback message |
| 10 | Yesterday absent → fallback to most recent older aggregate |
| 11 | Fallback warning fires in rendered block |
| 12 | Malformed aggregate doesn't crash; zero-count block rendered |
| 13 | `gather_patterns_aggregate()` one-call helper round-trip |
| 14 | No-recurring-pattern case ("no single pattern in ≥2 tenants this cycle") |

## Output shapes Mike sees

### Happy path (illustrative)
```
### Yesterday's task-system patterns

- 3 tasks promoted to planned overnight across 4 tenants.
- Top failure-mode class to invest defense tooling in: `interleave_corruption` (3 occurrences across src, josh).
- Recurring blocker pattern across tenants: `unresolved-blocker` (3 tenants: bun, josh, src). Treat as a workflow-gap signal.

_Source: /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/2026-05-19-aggregate.md_
```

### Tied top failure modes
```
### Yesterday's task-system patterns

- 3 tasks promoted to planned overnight across 4 tenants.
- **Top failure-mode classes (tied at 3 occurrences each):** `interleave_corruption` (across src, josh); `parallel_shift_writer_race` (across src, josh, bun). Invest defense tooling on whichever lands a same-week recurrence first.
- **Recurring blocker patterns (tied across 2 tenants each):** `missing-plan` (bun, danielle); `unresolved-blocker` (src, josh). Treat each as a workflow-gap signal.
...
```

### Missing aggregate (cron didn't fire)
```
### Yesterday's task-system patterns

- No patterns aggregate available. The overnight aggregator did not produce a file — check the patterns cron and bun's per-tenant check-and-promote runs.
```

### Yesterday absent but older aggregate found (cron skipped a day)
```
### Yesterday's task-system patterns

- _Note: yesterday's aggregate (2026-05-19) absent; showing most recent (2026-05-17, 3 days old)._

- 2 tasks promoted to planned overnight across 4 tenants.
...

- _Warning: yesterday's aggregate (2026-05-19) absent; falling back to most recent aggregate._
- _Warning: latest aggregate is 3 days old (2026-05-17) — patterns cron may be failing._

_Source: ..._
```

## Design decisions

1. **Yesterday-by-calendar is the primary path per host spec.** R1's design used "find latest" — host clarified the literal `<yesterday>-aggregate.md` requirement. R2 honors it AND retains the fallback-to-latest safety net (loud warning when fallback triggers; `silent_drift` defense intact).

2. **Tie-case surfacing: report all tied entries, not just one.** When 2+ enum values share the top count, the daily-improvement loop needs the full picture. A flickering single winner across consecutive days would be the worst of both worlds (no stability AND no information). Tied entries are alphabetized for run-to-run stability and explicitly labeled "tied at N occurrences each."

3. **Tie tiebreaker: alphabetical (stable across runs), not chronological.** Counter.most_common() preserves insertion order on ties — which depends on FS walk order in the aggregator. Sorting alphabetically gives identical output across runs even if FS ordering shifts.

4. **Always non-empty return.** `gather_patterns_aggregate()` is safe to call unconditionally from the brief composer — no try/except needed. Missing → fallback message; stale → warning; empty → reviewer nudge; malformed → zero-count block. The brief never gets a blank slot.

5. **No imports of the producer.** This module reads markdown only; doesn't import `patterns_aggregator` at runtime. Decouples deploy: reader can ship before/after producer without version-lockstep. Tests DO import both to round-trip realistically, but that's test-only.

6. **Stdlib-only.** No third-party deps. Same Python version as the brief reader.

## Failure-mode coverage (Rule 9 dogfood)

Plan-time defenses in this reader:

- `silent_drift` — explicit fallback message on missing aggregate AND warnings on stale/fallback paths (tests [9-11])
- `latency_budget_exceeded` — stdlib-only, sub-10ms — no threat to brief generation timing
- `schema_field_unenforced` — robust to malformed aggregate frontmatter / sections (test [12])
- `worker_self_report_passed_but_unverified` — brief block names source path so Mike can spot-check against the raw aggregate

NOT defended (out of scope):

- Multi-day rollup across N aggregate files (v0.4 candidate)
- Per-failure-mode alert thresholds
- Caller-side caching / dedupe across brief runs

## Deploy plan

See `MERGE-INSTRUCTIONS.md` for the patch payload (3 edits to `morning_brief.py`; same to stretch target `morning-brief-src.py`).

Summary:
1. `cp aggregate_summarizer.py` → `/mnt/system/base/skills/task-system/brief-reader-integration/`
2. Apply 3 edits to `morning_brief.py` (import / call / inject)
3. Apply same 3 edits to `morning-brief-src.py` (stretch)
4. Smoke-test post-first-cron — expect real digest in brief output

## v0.4 follow-ups

- Multi-day rollup (weekly section, last 7 aggregates)
- Per-failure-mode alert thresholds
- Mesh-event triggered re-render on aggregate landing
- Day-over-day diff ("interleave_corruption count went 3 → 6")
- Per-tenant aggregate scope filter (`--scope tenant=src`) if a per-tenant brief variant is needed

## References

- Host's option-#3 v2 spec: `/agent-desk/inbox/.read/2026-05-19-001-host-morning-brief-shape-option-1-file-exists.md`
- v0.2 spec amendment Rule 9: `/mesh/BLACKBOARD/task-system/v0.2-spec-amendment.md`
- patterns_aggregator (producer): `/agent-desk/snapshots/2026-05-19-patterns-aggregator/`
- R1 (superseded): `/agent-desk/snapshots/2026-05-19-brief-aggregate-reader/`
- Interactive session quality review (4 polish items deferred to v0.4): sent msg 021
