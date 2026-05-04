---
upstream: https://docs.openclaw.ai/concepts/memory.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: [2, 11]
related_pages: [concepts__active-memory, concepts__memory-builtin, concepts__memory-search]
---

# Memory subsystem — JamBot annotation

## What docs say (TL;DR)

Memory has multiple engines: `memory-core` (builtin), `active-memory` (sub-agent recall plugin), `memory-wiki` (bundled separate plugin), `memory-lancedb` (cloud), `memory-honcho`, `memory-qmd` (quick markdown). Hybrid BM25+vector search. `MEMORY.md` injected at session start; daily `memory/YYYY-MM-DD.md` files.

## Audit anchors that apply

### Anchor #2 — `memory-core` auto-activates + active-memory sub-agent runs before every reply

- `plugins.slots.memory: "memory-core"` is the AUTO default (only `"none"` disables)
- `agents.defaults.memorySearch.enabled: true` (default true) — drives the recall sub-agent
- Active-memory plugin (v4.10) adds a memory sub-agent that runs **right before every main reply** — explains the production-observed "blocking memory sub-agent" latency

### Anchor #11 — Dual-axis disable

`plugins.entries.memory-core.enabled: false` disables runtime ONLY — skill (prompt-level) still exposed. The single-knob kill switch is `plugins.slots.memory: "none"`. To fully disable both axes, set BOTH keys, OR just use the slot kill switch.

## Anchor #5 reminder — MEMORY.md is auto-truncated at ~10.5K chars

JamBot's `MEMORY.md` is currently 56KB / 561 lines (system reminder warned). Most index entries past ~150 lines are NOT visible to the agent at runtime. Trim aggressively.

## Engine choices (per docs but not in current skill)

| Engine | Role | When to choose |
|--------|------|----------------|
| `memory-core` | Builtin BM25 + vector | Default for all clients |
| `memory-wiki` | Article-style memory | Long-form notes & research |
| `memory-lancedb` | Cloud LanceDB | Multi-host shared memory (not used in JamBot) |
| `memory-honcho` | Honcho protocol | Research; not used |
| `memory-qmd` | Quick markdown | Lightweight, no vector |

## Other v4.x memory changes (audit doc)

- v4.24 line 1422: hybrid search `vectorScore` / `textScore` raw return
- v4.26 line 1058: `recallMaxChars`, `inputType` / `queryInputType` / `documentInputType` knobs
- v4.15 line 2466: `dreaming.storage.mode: "separate"` is the new default → writes to `memory/dreaming/{phase}/YYYY-MM-DD.md`
- v4.15 line 2443: GitHub Copilot embedding provider

## JamBot tuning (what we do)

```json5
{
  agents: { defaults: { memorySearch: { enabled: true } } },
  plugins: {
    slots: { memory: "memory-core" },
    entries: {
      "active-memory": { enabled: true },
      "memory-wiki": { enabled: false }   // we use Office system instead
    }
  }
}
```

JamBot doesn't use `memory-wiki` — we have the Office filing-cabinet system (`docs/jambot/office-system-overview.md`) that serves the same purpose with Clerk-driven per-tenant scoping.

## Burns / incidents

- 2026-04-18 → 2026-05-03: blocking memory sub-agent before every reply contributed to perceived latency. Documented; trade-off accepted (recall quality > speed).
- 2026-05-04: MEMORY.md truncation discovered (anchor #5). Trim plan TBD.

## Related JamBot files

- `audit-anchors/anchor-{2,5,11}.md`
- `docs/jambot/office-system-overview.md` — Office filing cabinet (replaces memory-wiki use case)
- `/jambot-performance` skill — memory perf tuning
- `/home/mike/.claude/projects/-home-mike-MIKE-AI/memory/MEMORY.md` — the file in question
