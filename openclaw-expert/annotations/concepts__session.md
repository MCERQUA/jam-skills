---
upstream: https://docs.openclaw.ai/concepts/session.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: [6, 15]
related_pages: [reference__session-management-compaction, concepts__compaction, concepts__session-pruning]
---

# Sessions — JamBot annotation

## What docs say (TL;DR)

Sessions = per-channel/group state. Persistent session key = warm Z.AI prompt cache (3-8s). New session key = cold (15-30s). JSONL transcript on disk. Compaction summarizes older turns; pruning trims tool results temporarily.

## Audit anchors that apply

### Anchor #15 — `session.maintenance.rotateBytes` DEPRECATED (v4.27)

Doctor `--fix` removes the key. Rotation no longer happens automatically — log management is BYO. Replacement (different concept): `session.writeLock.acquireTimeoutMs` (default 60s, v5.2 line 71).

### Anchor #6 — Compaction has new keys

Pre-compaction triggers + memory flush + plugin provider — see `audit-anchors/anchor-06`. Production-observed trigger ≈ 68% prompt usage (consistent with `reserveTokensFloor: 24000` + small `keepRecentTokens` default; not hardcoded).

## Other v4.x session changes (audit doc)

- v4.7: persisted compaction checkpoints + Sessions UI branch/restore — multiple checkpoints navigable
- v4.7: `sessions_yield` paused-state semantics — pauses agent without ending session
- v4.20 line 2395: events renamed `compaction_start` / `compaction_end`
- v4.26: transcript-rotation on compaction (when `truncateAfterCompaction: true`)
- v5.2: `session.writeLock.acquireTimeoutMs` policy (default 60s, replaces removed rotation)

## JamBot tuning

```json5
{
  session: {
    writeLock: { acquireTimeoutMs: 60000 }      // anchor #15
  },
  agents: {
    defaults: {
      compaction: {
        maxActiveTranscriptBytes: 600000,        // anchor #6
        truncateAfterCompaction: true,            // REQUIRED above
        midTurnPrecheck: true                     // anchor #6
      },
      contextPruning: { mode: "cache-ttl", ttl: "30m" }
    }
  }
}
```

## /compact vs /new vs context

- `/compact [guidance]` — manual compaction summary, optional focus hint
- `/new` — start fresh session WITHOUT compacting, full history preserved on disk
- `/context list` — see what's consuming tokens

## JSONL transcript layout

```
~/.openclaw/agents/<agent>/sessions/<channel>/<session-key>.jsonl
~/.openclaw/agents/<agent>/sessions/<channel>/<session-key>.trajectory.jsonl  (NEW v4.x — see tools/trajectory)
~/.openclaw/agents/<agent>/sessions/<channel>/<session-key>.trajectory-path.json  (sidecar pointer)
```

## Burns / incidents

- 2026-04-18 → 2026-05-03: empty-final cascade caused session poisoning. Fix path: `playbooks/debug-empty-final.md`.

## Related JamBot files

- `audit-anchors/anchor-{6,15}.md`
- `playbooks/debug-empty-final.md`
- `annotations/gateway__configuration.md` — config-side
- `annotations/concepts__memory.md` — memory-core sub-agent runs every turn (anchor #2)
- `/jambot-performance` skill — full perf tuning
