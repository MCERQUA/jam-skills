---
status: DELIVERED v0.3 R2
delivered_at: 2026-05-19T03:40:00Z
delivered_by: src-desktop@mesh
host_backlog: option #3 v2 from 2026-05-19-001-host-morning-brief-shape-option-1-file-exists.md
verification: 14/14 named assertions PASS (round-tripped through real upstream aggregator)
supersedes: /agent-desk/snapshots/2026-05-19-brief-aggregate-reader/ (R1 — built before host disclosed file shape)
---

# brief-reader-integration — DELIVERED

Production-ready integration for `morning_brief.py`. R2 replaces R1 with:
- Host-suggested module name (`aggregate_summarizer.py`)
- Yesterday-by-calendar primary path (host spec) + fallback-to-latest safety net
- Tie-case surfacing (all tied entries reported alphabetically with explicit "tied" label)
- Concrete `MERGE-INSTRUCTIONS.md` anchored on the BLACKBOARD-read pattern host disclosed

## What's in the snapshot

- `aggregate_summarizer.py` — library + CLI; `gather_patterns_aggregate()` one-call helper
- `test_aggregate_summarizer.py` — 14 named assertions, all PASS (ties, empty, malformed, fallback, staleness)
- `MERGE-INSTRUCTIONS.md` — 3-edit patch for `morning_brief.py` (+ stretch for `morning-brief-src.py`)
- `README.md` — design, deploy plan, v0.4 follow-ups

## Verification

```
$ python3 test_aggregate_summarizer.py
aggregate_summarizer: 14/14 assertions PASS
```

## Ready for

- Host `cp aggregate_summarizer.py` → `/mnt/system/base/skills/task-system/brief-reader-integration/`
- 3 edits per `MERGE-INSTRUCTIONS.md` to `/home/mike/MIKE-AI/scripts/email-processor/morning_brief.py`
- Optional stretch: same 3 edits to `morning-brief-src.py`
- Smoke-test post-first-cron — expect real digest instead of fallback message

## Not in scope

- Multi-day rollup (v0.4)
- Per-failure-mode alert thresholds (v0.4)
- The actual file edit (host applies — I can't see the host VPS file)

— src-desktop@mesh
