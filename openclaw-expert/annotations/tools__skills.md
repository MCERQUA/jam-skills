---
upstream: https://docs.openclaw.ai/tools/skills.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: [11]
related_pages: [tools__skills-config, tools__creating-skills, tools__clawhub]
---

# Skills — JamBot annotation

## What docs say (TL;DR)

Skills = markdown-defined agent plugins with frontmatter, optional `requires.*` gating, `installer` specs. Three types: workspace (per-tenant), managed (system-wide), bundled (with openclaw). Distributed via ClawHub.

## Anchor #11 — `skills.entries` vs `plugins.entries` (dual-axis)

A bundled component like `memory-core` registers BOTH a plugin entry AND a skill entry. Disabling only one disables only that axis:

| Knob | Effect |
|------|--------|
| `skills.entries.<id>.enabled: false` | Removes from agent's prompt (TOOLS.md) |
| `plugins.entries.<id>.enabled: false` | Removes runtime/capabilities |

For memory specifically, the single-knob kill switch is `plugins.slots.memory: "none"` (anchor #2).

## v4.x skills changes

| Surface | Introduced | Source |
|---------|-----------|--------|
| `skills.entries.coding-agent.enabled` strictly required | v4.27 line 837 | Bundled coding-agent skill won't expose without this |
| Skills snapshot invalidates on `skills.allowBundled` / `skills.entries.<id>.enabled` / `skills.profile` writes | v4.15 line 2478 | Re-bootstrap on next turn |
| `metadata.clawdbot.requires` / `metadata.clawdbot.install` legacy compat | v4.25 line 1902 | Honor legacy when `metadata.openclaw` absent |
| Chokidar v5 hot-reload | v4.25 | New file-watcher behavior |
| TaskFlow / coding-agent bundled-skill enablement gating | v4.10 / v4.27 | strict gating |

## JamBot's skills setup

Shared skills master dir: `/mnt/system/base/skills/` — mounted into all client containers. Per-tenant local skills: `/mnt/clients/<user>/openclaw/workspace/local-skills/`.

Per CLAUDE.md: every JamBot skill MUST be routed in `TOOLS.md` (memory `feedback_tools_md_routing`) — skills invisible to agents without a routing row, even if mounted and API-reachable.

## TOOLS.md cap (anchor #5)

Per-file bootstrap cap ≈ 24K chars for TOOLS.md. As we add more JamBot skills, the routing table grows toward this cap. Audit per-client TOOLS.md sizes.

## Skills snapshot invalidation gotcha

If you toggle `skills.entries.X.enabled` while a session is live, the next turn re-bootstraps. Acceptable cost for changes; can be jarring mid-conversation. Plan toggles between sessions.

## ClawHub CLI

```bash
openclaw plugins install npm:@<author>/<skill>     # NEW v4.26 explicit prefix
openclaw plugins install git:<spec>                 # NEW v5.2
openclaw plugins inspect <id>                       # NEW v4.27
openclaw plugins registry --refresh                 # NEW v4.25
openclaw plugins deps                                # NEW v4.27/4.29
```

## Skill frontmatter — JamBot conventions

```yaml
---
name: my-skill
description: One-line description (Mike-AI host CLAUDE.md subset rules)
metadata: {"openclaw": {"emoji": "🧠"}}
requires:
  channels: [webchat, telegram]      # only loads on these
  agents: [main]                      # only this agent
installer:                              # for managed-skill install flows
  type: shell
  command: setup.sh
---
```

Per memory `feedback_research_latest_versions`: never trust cached version knowledge — query npm/pypi/`/v1/models` live before recommending versions in skill bodies.

## Related JamBot files

- `audit-anchors/anchor-{2,11}.md`
- `audit-anchors/anchor-05-per-file-bootstrap-caps.md` — TOOLS.md cap
- `feedback_tools_md_routing.md` (memory) — TOOLS.md routing rule
- `/maintain-skills` skill — JamBot-side skills audit tool
- `/setup-skills` skill — JamBot-side skill installer
