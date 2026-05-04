---
upstream: https://docs.openclaw.ai/concepts/active-memory.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: [2, 11]
related_pages: [concepts__memory, concepts__memory-search, concepts__memory-builtin]
---

# Active Memory — JamBot annotation

## What docs say (TL;DR)

Active Memory is a bundled plugin that runs a memory-recall sub-agent **right before every main reply**. It calls `memory_search` and `memory_get` against the configured memory engine (default `memory-core`) and prepends results to the main agent's context.

## Anchor #2 — auto-activation

- `plugins.slots.memory` defaults to `"memory-core"` — only `"none"` disables the slot
- `agents.defaults.memorySearch.enabled: true` (default) — drives the sub-agent recall
- `plugins.entries.active-memory.enabled` — disables runtime only (NOT skill exposure — anchor #11)

The "blocking memory sub-agent before every reply" latency Mike observed in production is structural — it's this sub-agent doing recall.

## Anchor #11 — Dual-axis disable

To fully disable active-memory:
- Easy: `plugins.slots.memory: "none"` (single knob)
- Manual: BOTH `plugins.entries.active-memory.enabled: false` AND `skills.entries.active-memory.enabled: false`

Setting only one disables only that axis.

## Cost / benefit

| Benefit | Cost |
|---------|------|
| Better recall — agent sees relevant memory entries inline | Adds 1-3s latency per reply (the sub-agent run) |
| No manual `/memory search` calls needed | Costs sub-agent tokens (small model recommended via `memoryFlush.model`) |
| Hybrid BM25+vector finds entries by semantic + keyword | Can over-fetch; tune `recallMaxChars` (v4.26) |

## JamBot's stance

Keep enabled. Recall quality > latency for our use case. Memory-core's sub-agent uses the active session model unless overridden — for cost control, consider:

```json5
{ agents: { defaults: { compaction: { memoryFlush: { model: "ollama/qwen3:8b" } } } } }
```

(Note: `memoryFlush.model` is for pre-compaction flush, not recall — separate but related.)

## Recall vs. flush

| Operation | When | Model used |
|-----------|------|-----------|
| Active memory recall | Before every reply | Active session model (or active-memory plugin override) |
| Pre-compaction memory flush | Before compaction | `agents.defaults.compaction.memoryFlush.model` (v4.27) |

## Related JamBot files

- `audit-anchors/anchor-{2,11}.md`
- `annotations/concepts__memory.md`
- `annotations/concepts__compaction.md`
- `/jambot-performance` skill — perf tuning
- `docs/jambot/office-system-overview.md` — Office filing-cabinet (replaces some memory-wiki use cases)
