---
upstream: https://docs.openclaw.ai/concepts/compaction.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: [6]
related_pages: [reference__session-management-compaction, concepts__session, concepts__session-pruning]
---

# Compaction — JamBot annotation

## What docs say (TL;DR)

Compaction summarizes older conversation turns when approaching context window limits. Default automatic; `/compact` is manual override. Tool-call/tool-result pairs stay paired during splits. Successor transcripts created from summaries; previous archived.

## Anchor #6 — new keys + behaviors

| Key | Default | Introduced | Effect |
|-----|---------|-----------|--------|
| `agents.defaults.compaction.midTurnPrecheck` | opt-in | v4.27 (line 378) | Detects tool-loop context pressure mid-turn, triggers compaction before next tool call |
| `agents.defaults.compaction.maxActiveTranscriptBytes` | opt-in | v4.26 (line 1058) | Preflight; runs normal local compaction when active JSONL grows too large. **Requires `truncateAfterCompaction: true`** |
| `agents.defaults.compaction.memoryFlush.model` | inherits | v4.27 (line 903) | Pre-compaction memory flush uses exact override (e.g. `ollama/qwen3:8b`) without inheriting fallback chain |
| `agents.defaults.compaction.provider` | unset | v4.7 | Pluggable compaction provider; registering forces `mode: "safeguard"` |
| `keepRecentTokens` | small | (existing) | Recent conversation tail preserved during manual compaction |
| `notifyUser` | false | (existing) | Show "🧹 Auto-compaction complete" — keep OFF for voice clients |
| `identifierPolicy` | `"strict"` | (existing) | Preserves opaque IDs |

Setting `compaction.provider` forces `mode: "safeguard"` automatically.

## Production observation (NOT in changelog)

- Default trigger ≈ 68% prompt usage (consistent with `reserveTokensFloor: 24000` + small `keepRecentTokens`)
- Auto-retry on failure via run-level retry loop

## v4.20 events renamed

- `compaction_start` / `compaction_end` (line 2395) — replaces older event names

## Compaction vs. Pruning vs. /new

| Operation | What it does | History on disk? |
|-----------|--------------|-------------------|
| Compaction | Summarize entire conversation; create successor | Archived |
| Pruning (context) | Trim tool results temporarily | Unchanged |
| `/new` | Start fresh session | Unchanged |
| `/compact <guidance>` | Manual compaction with focus hint | Archived |

## Memory flush before compaction

OpenClaw reminds the agent to save important notes to memory files BEFORE compacting. Optional housekeeping turn uses `memoryFlush.model` (v4.27) — useful for cheap-model flush even when primary is expensive.

## JamBot tuning

```json5
{
  agents: { defaults: { compaction: {
    maxActiveTranscriptBytes: 600000,    // empirically tuned
    truncateAfterCompaction: true,        // required with above
    midTurnPrecheck: true,                 // catch tool-loop pressure
    notifyUser: false,                     // voice clients hate the emoji
    memoryFlush: { model: null }           // inherits primary
  } } }
}
```

## Related JamBot files

- `audit-anchors/anchor-06-compaction-trigger-and-new-keys.md`
- `annotations/concepts__session.md`
- `annotations/concepts__memory.md` — memory flush hooks here
- `/jambot-performance` skill
