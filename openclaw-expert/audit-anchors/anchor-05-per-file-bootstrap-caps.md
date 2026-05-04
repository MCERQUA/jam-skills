---
anchor: 5
slug: per-file-bootstrap-caps
status: partially-confirmed
introduced: v2026.4.20 (per-file caps), values production-observed against v5.2
changelog_line: 2393
upstream_pages:
  - https://docs.openclaw.ai/concepts/system-prompt.md
  - https://docs.openclaw.ai/concepts/agent-workspace.md
old_behavior: "bootstrapMaxChars = 20000 (single value, all files)"
new_behavior: "per-file caps: TOOLS.md ≈ 24K, MEMORY.md ≈ 10.5K, others ≈ 20K"
skill_files_affected:
  - "references/system-prompt.md:195"
  - "references/system-prompt.md:293"
  - "references/agent-runtime.md:18"
---

# Anchor #5 — Per-file bootstrap-context truncation limits

## Status: PARTIALLY CONFIRMED

v4.20 line 2393: "Agents/bootstrap: budget truncation markers against per-file caps, preserve source content instead of silently wasting bootstrap bytes, and avoid marker-only output in tiny-budget truncation cases. (#69114)" — confirms per-file caps EXIST.

Specific values (TOOLS.md ≈ 24K, MEMORY.md ≈ 10.5K) NOT in changelog — production-observed during the 2026-05-04 session.

## Production evidence

- TOOLS.md hit 28K chars / 24K limit
- MEMORY.md hit 17K chars / 10.5K limit

Both auto-truncated with marker.

## JamBot impact

Critical. Mike's MEMORY.md is already 56KB / 561 lines (system reminder warned at session start). It's getting heavily truncated at 10.5K. Most of the index entries past the first ~150 lines are NOT visible to the agent at runtime.

## Action required

1. Trim MEMORY.md aggressively (already a known recurring task)
2. Verify the exact cap values by inspecting source or running `openclaw config get agents.defaults.bootstrapMaxChars` and a per-file equivalent on 5.2
3. Document override path

## Fix instruction (interim)

`annotations/concepts__system-prompt.md`: "Per-file caps (5.2): TOOLS.md ~24K chars, MEMORY.md ~10.5K chars (auto-truncated with marker), other workspace bootstrap files ~20K. Override via `agents.defaults.bootstrapMaxChars` (global ceiling); per-file override path TBD — see audit-anchors/anchor-05."
