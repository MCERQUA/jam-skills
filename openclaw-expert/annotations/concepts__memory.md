---
upstream: https://docs.openclaw.ai/concepts/memory.md
relevance: jambot-critical
last-verified: 2026-05-23
audit_anchors: [2, 5, 11, 20]
related_pages: [concepts__active-memory, concepts__memory-builtin, concepts__memory-search, concepts__heartbeat]
---

# Memory subsystem — JamBot annotation

## What docs say (TL;DR)

Memory has multiple engines: `memory-core` (builtin), `active-memory` (sub-agent recall plugin), `memory-wiki` (bundled separate plugin), `memory-lancedb` (cloud), `memory-honcho`, `memory-qmd` (quick markdown). Hybrid BM25+vector search. `MEMORY.md` injected at session start; daily `memory/YYYY-MM-DD.md` files.

## Anchor #20 — Community shift toward hybrid retrieval (added 2026-05-23)

OpenClaw default `memory-core` is markdown + keyword search. Synonyms and rephrasings miss; agent re-asks for context it already has on disk. Community has converged on hybrid retrieval — either **QMD plugin** (~2-week-old standard per r/openclaw 1rkxr9g) or **memory-lancedb** via `plugins.slots.memory: "memory-lancedb"`.

JamBot tenants currently default to `memory-core`. Worth evaluating QMD on one tenant for 2 weeks; measure re-ask rate (agent asks for info already in MEMORY.md). See `audit-anchors/anchor-20-qmd-memory-default-shift.md`.

Heavier alternative (full architecture in `playbooks/hybrid-memory-sqlite-lance.md`): SQLite-FTS5 + LanceDB hybrid with TTL decay tiers (permanent / 90d / 14d / 24h / 4h) and decision-extraction regex patterns. Source: r/openclaw 1r49r9m.

## Canonical workspace layout (added 2026-05-23)

Per r/openclaw 1rqsg2a + 1r4t9q8 community consensus:

```
workspace/
├── AGENTS.md  SOUL.md  USER.md
├── MEMORY.md       # INDEX, not dump
├── TOOLS.md        # routed skills (anchor-05 cap = 24K chars)
├── HEARTBEAT.md    # cron-dispatched maintenance prompts
├── SECURITY.md     # security log + skill-vetting records
├── ACTIVE-TASK.md  # current work state
├── memory/
│   ├── people/        # one .md per person (entities)
│   ├── projects/      # one .md per project
│   ├── decisions/     # one .md per significant decision
│   └── YYYY-MM-DD.md  # daily append-only timeline
├── skills/   tools/   projects/   secrets/   agents/
```

**Key principle: `MEMORY.md` = INDEX, NOT DUMP.** Drill into `memory/people/`, `memory/projects/`, `memory/decisions/` on demand. The MEMORY.md cap (anchor-05, ~10.5K chars) forces this — overflow gets auto-truncated.

## 4-layer mental model (added 2026-05-23)

Per r/openclaw 1rqsg2a — files in different layers MUST NOT overlap:

| Layer | Files | Purpose |
|---|---|---|
| Identity / behavior | SOUL.md, AGENTS.md, USER.md | Who the agent is, who the user is, behavior boundaries |
| Memory | MEMORY.md (index), memory/* (drill-in) | What the agent knows |
| Tooling / ops | TOOLS.md, HEARTBEAT.md, SECURITY.md | How the agent does things + maintenance |
| Project work | ACTIVE-TASK.md, projects/* | Current work, separate from identity/memory |

Cross-layer leakage is a common bug: putting project status in MEMORY.md (wrong layer; should be ACTIVE-TASK.md + projects/) or putting behavior rules in TOOLS.md (wrong layer; SOUL.md/AGENTS.md). Audit per-tenant when reviewing system-prompt budget.

## Audit anchors that apply

### Anchor #2 — `memory-core` auto-activates + active-memory sub-agent runs before every reply

- `plugins.slots.memory: "memory-core"` is the AUTO default (only `"none"` disables)
- `agents.defaults.memorySearch.enabled: true` (default true) — drives the recall sub-agent
- Active-memory plugin (v4.10) adds a memory sub-agent that runs **right before every main reply** — explains the production-observed "blocking memory sub-agent" latency

### Anchor #11 — Dual-axis disable

`plugins.entries.memory-core.enabled: false` disables runtime ONLY — skill (prompt-level) still exposed. The single-knob kill switch is `plugins.slots.memory: "none"`. To fully disable both axes, set BOTH keys, OR just use the slot kill switch.

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
