---
anchor: 2
slug: memory-core-auto-activates
status: confirmed
introduced: v2026.4.10 (active-memory) + v2026.4.10/4.15 (memory-core auto-load)
changelog_lines: [1022, 1315, 1447, 2740]
upstream_pages:
  - https://docs.openclaw.ai/concepts/memory.md
  - https://docs.openclaw.ai/concepts/memory-builtin.md
  - https://docs.openclaw.ai/concepts/active-memory.md
  - https://docs.openclaw.ai/concepts/memory-search.md
old_behavior: "memory disabled unless explicitly enabled"
new_behavior: "memory-core auto-loads at gateway startup; active-memory sub-agent runs before every reply"
skill_files_affected:
  - "references/memory-system.md:420-424"
---

# Anchor #2 — `memory-core` auto-activates on bundled distributions

## What changed

- v4.10 line 2740: bundled `active-memory` plugin added — runs a dedicated memory sub-agent right before the main reply
- v4.10/4.15 lines 1022/1315/1447: "load the default `memory-core` slot during Gateway startup when permitted so active-memory recall can call `memory_search` and `memory_get` without requiring an explicit `plugins.slots.memory` entry, while preserving `plugins.slots.memory: "none"`"

## Exact config keys

| Key | Default | Effect |
|-----|---------|--------|
| `plugins.slots.memory` | `"memory-core"` (auto) | Only `"none"` disables — single-knob kill switch |
| `agents.defaults.memorySearch.enabled` | `true` | Enables sub-agent recall at turn start |
| `plugins.entries.active-memory.enabled` | depends on bundled dist | Disables runtime only |
| `skills.entries.active-memory.enabled` | depends | Disables prompt-level exposure only |
| `plugins.entries.memory-wiki.enabled` | bundled separately | Re-shipped v4.7 line 2927 |

## Production observation

The "blocking memory sub-agent before every reply" behavior Mike noticed is real and structural — it's the active-memory plugin doing recall before main reply.

## JamBot impact

If memory feels slow, the kill switch is `plugins.slots.memory: "none"`, NOT `plugins.entries.memory-core.enabled: false` (anchor #11 territory).

## Fix instruction

`annotations/concepts__memory.md` and `annotations/concepts__active-memory.md` must both call out:
1. memory-core auto-loads — slot kill switch is `"none"`
2. active-memory adds a sub-agent before every reply (cost: latency)
3. plugins.entries / skills.entries are dual-axis (anchor #11)
