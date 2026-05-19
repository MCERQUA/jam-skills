---
purpose: integration patch for morning_brief.py to consume patterns aggregate
target: `scripts/email-processor/morning_brief.py` (host VPS — exact path per host's reference)
applies_to: any brief reader Python entrypoint that builds Mike's morning email
---

# Morning brief — patterns aggregate integration

This is a **language-level patch**, not a literal diff — I (src-desktop@mesh) cannot see `morning_brief.py` from inside my webtop. The host VPS or josh-desktop's worker-a applies these edits.

## Three required edits

### 1. Import the reader

```python
# top of morning_brief.py, with the rest of the imports
import sys
sys.path.insert(0, "/mnt/system/base/skills/task-system/brief-aggregate-reader")
from brief_aggregate_reader import render_for_brief as render_patterns_block
```

(If the brief reader is moved into the host venv or package-installed, drop the `sys.path.insert` and use a normal `from skills.task_system.brief_aggregate_reader import ...` form.)

### 2. Render the patterns block

Wherever the brief assembles its sections (typically a function like `build_brief()` or `compose_email()`), add ONE call to render the patterns block. It returns a markdown string that always non-empty — missing aggregate yields a clear fallback, stale aggregate yields a warning. No need to wrap in try/except.

```python
patterns_block = render_patterns_block("/mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/")
```

### 3. Inject between existing sections

Place `patterns_block` **after** the per-tenant task summary section and **before** the "today's schedule" section. Rationale:

- Patterns inform schedule choices — Mike sees signals before committing to today's slot allocation.
- Per-tenant detail establishes context first; cross-tenant signals are the synthesis layer.

Example shape after the patch:

```
# Morning brief — 2026-05-20

## Tenant status
...per-tenant lines...

### Yesterday's task-system patterns       ← patterns_block lands here

- 3 tasks promoted to planned overnight across 4 tenants.
- Top failure-mode class to invest defense tooling in: `interleave_corruption` (3 occurrences across src, josh).
- Recurring blocker pattern across tenants: `unresolved-blocker` (3 tenants: bun, josh, src). Treat as a workflow-gap signal.

_Source: /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/2026-05-20-aggregate.md_

## Today's schedule
...time-slot allocations...
```

## What the block guarantees (so the brief author can rely on it)

- **Always non-empty.** Missing aggregate yields a fallback message naming the cron as the suspect. Empty cycle yields a reviewer-nudge. Stale aggregate yields a lag warning. The brief never gets a blank.
- **Plain English.** Counts and tenant names are spelled out, not raw JSON. Mike reads `interleave_corruption` × 3 across src, josh — not `{"interleave_corruption": 3}`.
- **Glob-based latest-aggregate discovery.** If the cron skipped a day, the brief still finds the most recent aggregate AND warns. `silent_drift` defense — no quiet 404s.
- **No external dependencies.** Stdlib only. Same Python version as the brief reader.

## What the brief author SHOULD NOT do

- Don't parse the aggregate yourself. The aggregate's markdown format is a v0.3 contract; this reader insulates the brief from future format changes (e.g., the v0.4 "per-day diff" section will be additive — won't break this reader).
- Don't fall back to "skip patterns block on error." The fallback message is the signal Mike needs to know the cron is broken. Silencing it = `silent_drift` v0.2 enum entry.
- Don't combine the patterns block with the per-tenant summary into one section. They're different abstraction layers — per-tenant is "what each agent is doing"; patterns is "what's recurring across the system."

## Smoke test against host's real path

```bash
python3 /mnt/system/base/skills/task-system/brief-aggregate-reader/brief_aggregate_reader.py \
  -p /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/
```

Should print a brief block to stdout. Run after the first daily cron fires to verify the integration end-to-end.

## Override for testing

```bash
python3 brief_aggregate_reader.py -p /path/to/patterns/ --today 2026-05-25
```

`--today` overrides the staleness clock for golden-output testing without time-machine games.

## Failure-mode coverage (Rule 9 dogfood)

Plan-time defenses in this reader:

- `silent_drift` — fallback message on missing aggregate is loud, never silent.
- `latency_budget_exceeded` — single file read, no network calls, runs in <10ms on any reasonable FS.
- `schema_field_unenforced` — robust to malformed aggregate frontmatter (test [16-17]); defaults to zero counts and surfaces a parseable block anyway.

NOT defended:

- Multi-day aggregation (the reader is one-aggregate-per-call; future feature could combine N days).
- Custom failure-mode threshold alerts (just surfaces top-1 currently; tunable threshold is v0.4 work).
