---
author: src-desktop@mesh
status: DELIVERED v0.3
delivered_at: 2026-05-19T03:30:00Z
spec_ref: v0.2 spec amendment Rule 9 — consumer side
host_backlog: option #3 from 2026-05-19-001-host-patterns-aggregator-deployed-cron-wiring-next.md
upstream: /agent-desk/snapshots/2026-05-19-patterns-aggregator/ (producer)
downstream: scripts/email-processor/morning_brief.py (host VPS — see morning_brief_patch.md)
---

# brief_aggregate_reader — patterns aggregate → morning brief block

Closes the v0.3 loop: the daily aggregate file produced by `patterns_aggregator` flows into Mike's morning brief as a plain-English block surfacing the top failure-mode class to invest defense tooling in + the top recurring blocker pattern across tenants.

## Files

| File | Purpose | Verification |
|---|---|---|
| `brief_aggregate_reader.py` | Library + CLI. `find_latest_aggregate()` / `read_aggregate()` / `format_for_brief()` / `render_for_brief()` one-call helper | 18-assertion fixture test |
| `test_brief_aggregate_reader.py` | Round-trip via real `patterns_aggregator`; happy path, stale, missing, empty cycle, malformed | **18/18 PASS** |
| `morning_brief_patch.md` | Language-level patch for `morning_brief.py` (3 edits: import, render, inject between sections) | — |
| `COMPLETION-NOTICE.md` | Delivery marker | — |

## Verification

```
$ python3 test_brief_aggregate_reader.py
brief_aggregate_reader: 18/18 assertions PASS
```

Tests round-trip through the real upstream aggregator (no mock). Covers:
- Latest-file discovery (1)
- Frontmatter parsing (2-3)
- Top-N table parsing for failure_modes + blocker patterns (4-6)
- Staleness clock (7, 11-12)
- Plain-English render quality (8-10)
- Missing-aggregate fallback (13-14)
- Empty-cycle reviewer nudge (15)
- Malformed-aggregate robustness (16-17)
- One-call helper (18)

## Plain-English output shape

```
### Yesterday's task-system patterns

- 3 tasks promoted to planned overnight across 4 tenants.
- Top failure-mode class to invest defense tooling in: `interleave_corruption` (3 occurrences across src, josh).
- Recurring blocker pattern across tenants: `unresolved-blocker` (3 tenants: bun, josh, src). Treat as a workflow-gap signal.

_Source: /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/2026-05-19-aggregate.md_
```

## When patterns aggregate is missing

```
### Yesterday's task-system patterns

- No patterns aggregate available. The overnight aggregator did not produce a file — check the patterns cron and bun's per-tenant check-and-promote runs.
```

Loud signal beats silent skip — Mike sees the cron is broken in the brief itself.

## When patterns aggregate is stale

```
### Yesterday's task-system patterns

- _Note: latest aggregate is from 2026-05-15 (4 days old). Patterns cron may be lagging._

- 2 tasks promoted to planned overnight across 4 tenants.
...
```

Aggregate is still rendered, but the staleness warning fires (default threshold: >2 days old).

## Design decisions

1. **Glob-based latest-aggregate discovery, not `<yesterday>-aggregate.md`.** Host's option #3 said "glob `<yesterday>-aggregate.md`" — taken as a direction, not a literal filename. If yesterday's cron failed, the brief still finds the last successful aggregate AND warns about staleness. Hard-coded yesterday-by-calendar would 404 silently when most needed. `silent_drift` defense.

2. **Robust to malformed aggregate.** Frontmatter parse failure → defaults to zero counts; section parse failure → returns None for top-N fields; render still produces a valid brief block. Reason: a broken aggregate is a real-world possibility (cron disk full, parsing bug in v0.4 upgrade); the brief should always ship.

3. **Always render a block, never raise.** The reader returns a populated `BriefAggregateBlock` even in the worst case (no file, no parse, no data). `format_for_brief()` always returns a non-empty string. Brief composer can call this unconditionally without try/except. Reduces foot-guns.

4. **Top-1 surfaced, not top-N.** Mike's brief is short. Top-1 failure-mode class + top-1 recurring blocker pattern + total counts is the right density. The full aggregate file is one link away if Mike wants the long version.

5. **`--today` override for staleness clock.** Tests need to control the clock without `freezegun` or monkey-patching. The CLI also exposes it for golden-output reproductions in postmortems.

6. **No dependency on `patterns_aggregator` at runtime.** This module reads markdown; doesn't import the producer module. Decouples deploy: brief reader can ship before/after patterns aggregator without version-lockstep. Tests DO import both to round-trip, but that's test-only.

## Failure-mode coverage (Rule 9 dogfood — closing the loop on my own work)

Plan-time defenses in this reader:

- `silent_drift` — fallback message on missing aggregate is loud, never silent (test [13-14]).
- `latency_budget_exceeded` — single file read, stdlib-only, sub-10ms. No threat to brief generation timing.
- `schema_field_unenforced` — robust to malformed aggregate frontmatter (test [16-17]).
- `worker_self_report_passed_but_unverified` — the brief block names the source path so Mike can spot-check the rendered summary against the raw aggregate file.

NOT defended (out of scope):

- Multi-day aggregation across N aggregate files (v0.4 candidate).
- Per-failure-mode alert thresholds ("alert me if `parallel_shift_writer_race` count > 5").
- Brief-side caching / dedupe (the brief reader is the right layer; this is a parser, not a workflow engine).

## Integration recipe

See `morning_brief_patch.md` — 3 language-level edits to `morning_brief.py`:

1. Import `render_for_brief as render_patterns_block` from this module.
2. Call `render_patterns_block(patterns_dir)` once per brief.
3. Inject the returned markdown between the per-tenant summary and today's schedule.

The patch is described at the language level (not as a literal diff) because the actual `morning_brief.py` lives on the host VPS and I can't see it from inside the webtop. Host or worker-a applies the patch.

## Deploy plan (host action)

1. `docker cp` this snapshot → `/mnt/system/base/skills/task-system/brief-aggregate-reader/`
2. Apply `morning_brief_patch.md` to `scripts/email-processor/morning_brief.py`
3. Smoke test:
   ```bash
   python3 /mnt/system/base/skills/task-system/brief-aggregate-reader/brief_aggregate_reader.py \
     -p /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/
   ```
   Expected: brief block printed to stdout. Pre-cron output: "fallback message" (correct). Post-first-cron output: real digest with counts.

## v0.4 follow-ups

- Multi-day rollup (e.g., "weekly patterns" section combining the last 7 aggregate files)
- Alert thresholds with per-tenant breakouts
- Mesh-event triggered re-render (when a new aggregate lands, push a fresh brief diff to Mike)
- Diff against previous brief's patterns block ("interleave_corruption count went 3 → 6 day-over-day")
- Integration into nightly reflection synthesizer (consumes same reader)

## References

- v0.2 spec amendment Rule 9: `/mesh/BLACKBOARD/task-system/v0.2-spec-amendment.md`
- patterns_aggregator (producer): `/agent-desk/snapshots/2026-05-19-patterns-aggregator/`
- patterns_aggregator BLACKBOARD entry: `/mesh/BLACKBOARD/task-system/2026-05-19/patterns-aggregator-v0.3.md`
- Host backlog option #3 (this work): inbox 2026-05-19-001-host-patterns-aggregator-deployed-cron-wiring-next.md
