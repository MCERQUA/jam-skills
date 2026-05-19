---
target_file_primary: /home/mike/MIKE-AI/scripts/email-processor/morning_brief.py
target_file_stretch: /home/mike/MIKE-AI/scripts/email-processor/morning-brief-src.py
library_install_path: /mnt/system/base/skills/task-system/brief-reader-integration/
review_owner: host@mesh
---

# Merge instructions — patterns aggregate → morning brief

Three required edits to `morning_brief.py`; same three edits to `morning-brief-src.py` (stretch).

I (src-desktop@mesh) can't read the host VPS file from my webtop, so the edits are anchored on **code patterns** the host already disclosed in inbox msg 001 03:14Z plus standard Python conventions. Host or worker-a applies the edits and verifies the line numbers match.

## Pre-merge: install the library

```bash
mkdir -p /mnt/system/base/skills/task-system/brief-reader-integration
cp /agent-desk/snapshots/2026-05-19-brief-reader-integration/aggregate_summarizer.py \
   /mnt/system/base/skills/task-system/brief-reader-integration/
# (test file optional in production)
```

The library is stdlib-only — no pip install, no venv changes.

## Edit 1 — Import (insert near existing imports)

**Anchor:** the existing import block at the top of the file (after the docstring).

**Patch:**

```python
import sys
sys.path.insert(0, "/mnt/system/base/skills/task-system/brief-reader-integration")
from aggregate_summarizer import gather_patterns_aggregate
```

If the brief reader's project structure already exposes `/mnt/system/base/skills/task-system/` on `PYTHONPATH`, drop the `sys.path.insert` line and use:

```python
from brief_reader_integration.aggregate_summarizer import gather_patterns_aggregate
```

## Edit 2 — Render the patterns block (insert in the brief-assembly section)

**Anchor:** the existing `nightly-reflections` read block. Host disclosed:

```python
p = Path(f"/mnt/agent-mesh/mesh/BLACKBOARD/nightly-reflections/{yesterday}/group-distilled.md")
if p.exists():
    distilled = p.read_text()
```

**Insert AFTER this block, BEFORE the open-tasks section.** Example shape after edit:

```python
# ─── existing nightly-reflections read ───
p = Path(f"/mnt/agent-mesh/mesh/BLACKBOARD/nightly-reflections/{yesterday}/group-distilled.md")
if p.exists():
    distilled = p.read_text()

# ─── NEW: patterns aggregate block ───
patterns_block = gather_patterns_aggregate(
    "/mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns",
)

# ─── existing open-tasks read continues ───
```

**Key contract for the brief author:**
- `gather_patterns_aggregate()` ALWAYS returns a non-empty string (missing aggregate → fallback message; stale → warning; empty cycle → reviewer nudge).
- No try/except needed.
- Stdlib-only, sub-10ms typical runtime.

## Edit 3 — Inject the block into the assembled brief body

**Anchor:** wherever the brief composes its final body. The reflection section's variable name (host disclosed `distilled`) is the most reliable anchor; the patterns block lands right after it.

**Patch (illustrative):**

```python
body_parts = [
    # ... existing header ...
    distilled,                          # nightly reflection (existing)
    patterns_block,                     # NEW — patterns aggregate
    open_tasks_block,                   # existing — open client tickets
    # ... existing footer ...
]
body = "\n\n".join(part for part in body_parts if part)
```

If the brief uses an f-string template instead of a parts-list:

```python
body = f"""
{header}

{distilled}

{patterns_block}

{open_tasks_block}

{footer}
""".strip()
```

## Output Mike sees (example, illustrative)

```
### Yesterday's task-system patterns

- 3 tasks promoted to planned overnight across 4 tenants.
- Top failure-mode class to invest defense tooling in: `interleave_corruption` (3 occurrences across src, josh).
- Recurring blocker pattern across tenants: `unresolved-blocker` (3 tenants: bun, josh, src). Treat as a workflow-gap signal.

_Source: /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/2026-05-19-aggregate.md_
```

When the aggregate is missing (e.g., cron didn't fire):

```
### Yesterday's task-system patterns

- No patterns aggregate available. The overnight aggregator did not produce a file — check the patterns cron and bun's per-tenant check-and-promote runs.
```

When ties exist (3+ failure modes at the same top count):

```
### Yesterday's task-system patterns

- 3 tasks promoted to planned overnight across 4 tenants.
- **Top failure-mode classes (tied at 3 occurrences each):** `interleave_corruption` (across src, josh); `parallel_shift_writer_race` (across src, josh, bun). Invest defense tooling on whichever lands a same-week recurrence first.
- **Recurring blocker patterns (tied across 2 tenants each):** `missing-plan` (bun, danielle); `unresolved-blocker` (src, josh). Treat each as a workflow-gap signal.

_Source: ..._
```

## Stretch: `morning-brief-src.py`

If/when host wires the same library in Stephen/Rory's brief, apply the same 3 edits with one substitution: the `gather_patterns_aggregate()` call's default `patterns_dir` is the same path (`/mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns`). Cross-tenant patterns are intentionally shared — the brief just renders the same daily aggregate.

If src tenant ever needs a per-tenant aggregate variant, the producer (`patterns_aggregator`) would need a `--scope tenant=src` filter, which is v0.4 work.

## Post-merge smoke test

```bash
# 1. Confirm the library is importable
python3 -c "from aggregate_summarizer import gather_patterns_aggregate; print('ok')" \
  || { echo "library not on PYTHONPATH"; exit 1; }

# 2. Render against the live BLACKBOARD path (pre-cron: expect fallback message)
python3 /mnt/system/base/skills/task-system/brief-reader-integration/aggregate_summarizer.py \
  -p /mnt/agent-mesh/mesh/BLACKBOARD/task-system/patterns/

# 3. Dry-run the brief composer to confirm the block appears (no email send)
python3 /home/mike/MIKE-AI/scripts/email-processor/morning_brief.py --dry-run
# (substitute whatever dry-run flag the existing brief composer supports)
```

## Tests included with this snapshot

```
$ python3 test_aggregate_summarizer.py
aggregate_summarizer: 14/14 assertions PASS
```

Covers:
1. Yesterday file found (happy path)
2. Tied failure_modes — both members surfaced alphabetically
3. Tied failure_modes — count semantics
4. Tied recurring patterns — both members surfaced alphabetically
5. Tied brief block contains the "tied" label
6. Tied recurring blocker label
7. Empty cycle → reviewer nudge
8. Empty cycle still reports zero counts cleanly
9. No-aggregates directory → fallback message
10. Yesterday absent → fallback to most recent older aggregate
11. Fallback warning in the rendered block
12. Malformed aggregate doesn't crash; defaults to zero counts
13. `gather_patterns_aggregate()` one-call helper matches direct API
14. No-recurring-pattern case ("no single pattern in ≥2 tenants this cycle")

## Rollback plan

If the patch breaks brief generation:

1. Comment out Edit 2's `patterns_block = gather_patterns_aggregate(...)` line.
2. Replace `patterns_block` in Edit 3 with `""`.
3. The brief returns to its pre-patch state with zero functional change.

The library itself doesn't need to be uninstalled — it has no side effects until called.
