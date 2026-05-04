---
upstream: https://docs.openclaw.ai/concepts/system-prompt.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: [5]
related_pages: [concepts__agent-workspace, reference__templates__AGENTS]
---

# System prompt — JamBot annotation

## What docs say (TL;DR)

Prompt assembled from ~26 sections at session start. Bootstrap files (`AGENTS.md`, `TOOLS.md`, `MEMORY.md`, `HEARTBEAT.md`, `SOUL.md`, `IDENTITY.md`, `BOOT.md`, `BOOTSTRAP.md`, `USER.md`) injected with caps. `/context list` shows what's consuming tokens.

## Anchor #5 — Per-file bootstrap caps (v5.2 production-observed)

v4.20 line 2393 introduced **per-file caps** (vs. flat `bootstrapMaxChars: 20000`). Specific values are NOT in changelog — production-observed against 5.2:

| File | Cap (chars) | Auto-truncated? |
|------|-------------|-----------------|
| TOOLS.md | ≈ 24,000 | Yes, with marker |
| MEMORY.md | ≈ 10,500 | Yes, with marker |
| Other workspace bootstrap files | ≈ 20,000 | Yes, with marker |

**JamBot's MEMORY.md is currently 56KB / 561 lines.** Most index entries past ~150 lines are NOT visible at runtime. Trim aggressively.

## New v4.x knobs (audit doc §2.1)

| Key | Default | Introduced |
|-----|---------|-----------|
| `agents.defaults.skipOptionalBootstrapFiles` | false | v5.2 line 35 |
| `agents.defaults.contextInjection: "never"` | enabled | v4.24 line 1792 |
| `agents.defaults.systemPromptOverride` | unset | v4.7 |

`contextInjection: "never"` is for agents that fully own their prompt lifecycle (skip workspace injection entirely).

## v4.7 heartbeat prompt-section controls

Heartbeat runtime behavior can stay enabled WITHOUT injecting heartbeat instructions every turn. Saves tokens.

## Bootstrap file load order

1. `AGENTS.md` — agent role + standing orders
2. `IDENTITY.md` — name, persona
3. `SOUL.md` — personality + hard blocks
4. `TOOLS.md` — tool routing for skills
5. `BOOT.md` / `BOOTSTRAP.md` — first-turn context
6. `USER.md` — principal info (delegate model, anchor #N — delegate-architecture)
7. `MEMORY.md` — long-term memory index
8. `HEARTBEAT.md` — periodic injection (controlled separately v4.7)

Order matters when caps bite — files later in the order may be more truncated.

## Skills snapshot invalidation (v4.15)

Session `skillsSnapshot` invalidates when ANY of these write:
- `skills.allowBundled`
- `skills.entries.<id>.enabled`
- `skills.profile`

Forces a re-bootstrap on next turn.

## /context commands

- `/context list` — what's consuming tokens
- `/context show <section>` — full section text
- `/context skills` — current skills snapshot

## JamBot impact

- MEMORY.md heavily truncated (anchor #5) — 75%+ of content unseen at runtime
- TOOLS.md is a bigger file across all clients now (ovui-desktop, mesh tools, custom skills) — at risk of cap
- Action item: per-client TOOLS.md audit, especially for clients with many skills

## Related JamBot files

- `audit-anchors/anchor-05-per-file-bootstrap-caps.md`
- `/home/mike/.claude/projects/-home-mike-MIKE-AI/memory/MEMORY.md` (the file getting truncated)
- `docs/jambot/openvoiceui-system-prompt.md`
- `annotations/concepts__memory.md`
