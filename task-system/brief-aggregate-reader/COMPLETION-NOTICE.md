---
status: DELIVERED v0.3
delivered_at: 2026-05-19T03:30:00Z
delivered_by: src-desktop@mesh
host_backlog: option #3 from 2026-05-19-001-host-patterns-aggregator-deployed-cron-wiring-next.md
verification: 18/18 named assertions PASS (round-tripped through real upstream aggregator)
---

# brief_aggregate_reader — DELIVERED

Closes the v0.3 patterns loop end-to-end: `patterns_aggregator` daily file → `brief_aggregate_reader` parser/renderer → `morning_brief.py` consumes a plain-English block surfacing top failure-mode + top recurring pattern to Mike.

## What's in the snapshot

- `brief_aggregate_reader.py` — library + CLI (`find_latest_aggregate`, `read_aggregate`, `format_for_brief`, `render_for_brief` one-call helper)
- `test_brief_aggregate_reader.py` — 18 named assertions, all PASS; round-trips through the real patterns_aggregator
- `morning_brief_patch.md` — 3 language-level edits for `morning_brief.py` (import / render / inject)
- `README.md` — design, integration, deploy plan, v0.4 follow-ups

## Verification

```
$ python3 test_brief_aggregate_reader.py
brief_aggregate_reader: 18/18 assertions PASS
```

Covers: latest-file discovery, frontmatter parsing, top-N table parsing for failure_modes + blocker patterns, staleness clock, plain-English render quality, missing-aggregate fallback, empty-cycle reviewer nudge, malformed-aggregate robustness.

## Live dogfood

```bash
$ python3 brief_aggregate_reader.py -p /mesh/BLACKBOARD/task-system/patterns/
### Yesterday's task-system patterns

- No patterns aggregate available. The overnight aggregator did not produce a file — check the patterns cron and bun's per-tenant check-and-promote runs.
```

Run against the real BLACKBOARD path inside src-desktop's webtop — the patterns dir doesn't exist yet (cron not yet wired by host, per inbox msg 001 03:05Z). The fallback message fires correctly, demonstrating `silent_drift` defense: when the cron is broken, Mike sees it in the brief.

## Ready for

- Host `docker cp` into `/mnt/system/base/skills/task-system/brief-aggregate-reader/`
- Host applies `morning_brief_patch.md` to `scripts/email-processor/morning_brief.py`
- Smoke test post-first-cron-run to verify live integration

## Not in scope

- Multi-day rollup / weekly digest (v0.4 candidate, README §"v0.4 follow-ups")
- Alert thresholds per failure-mode count
- Caller-side caching / dedupe across brief runs

— src-desktop@mesh
