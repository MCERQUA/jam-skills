---
upstream: https://docs.openclaw.ai/tools/skills.md
relevance: jambot-critical
last-verified: 2026-07-25
audit_anchors: [11, 18]
related_pages: [tools__skills-config, tools__creating-skills, tools__clawhub, plugins__architecture]
---

# Skills — JamBot annotation

## What docs say (TL;DR)

Skills = markdown-defined agent plugins with frontmatter, optional `requires.*` gating, `installer` specs. Three types: workspace (per-tenant), managed (system-wide), bundled (with openclaw). Distributed via ClawHub.

## Anchor #18 — Supply-chain risk (added 2026-05-23)

**ALL ClawHub installs are untrusted code.** The ClawHavoc campaign caught 1,467 malicious skills; the flagship case `capability-evolver` (#1 on ClawHub, 35k installs) was exfiltrating to Chinese cloud storage before removal (github.com/openclaw/clawhub#95).

JamBot rule: `/mnt/system/base/skills/` is allowlist-only. New skills go through `playbooks/skill-install-vetting.md`. See `overrides/skill-allowlist.md` for the current allowlist + blocklist.

**Critical injection vector:** skill `DESCRIPTION.md` is injected verbatim into the agent system prompt — bypasses prompt-injection scanners. Treat skill `DESCRIPTION.md` as code-equivalent threat surface, not docs. See `annotations/security__prompt-injection.md`.

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
| Skills snapshot invalidates on `skills.allowBundled` / `skills.entries.<id>.enabled` writes (NOT `skills.profile` — see correction below) | v4.15 line 2478 | Re-bootstrap on next turn |
| `metadata.clawdbot.requires` / `metadata.clawdbot.install` legacy compat | v4.25 line 1902 | Honor legacy when `metadata.openclaw` absent |
| Chokidar v5 hot-reload | v4.25 | New file-watcher behavior |
| TaskFlow / coding-agent bundled-skill enablement gating | v4.10 / v4.27 | strict gating |

## JamBot's skills setup

Shared skills master dir: `/mnt/system/base/skills/` — mounted into all client containers. Per-tenant local skills: `/mnt/clients/<user>/openclaw/workspace/local-skills/`.

Per CLAUDE.md: every JamBot skill MUST be routed in `TOOLS.md` (memory `feedback_tools_md_routing`) — skills invisible to agents without a routing row, even if mounted and API-reachable.

**2026-05-23 addition:** the shared-skills directory is now also an allowlist (see `overrides/skill-allowlist.md`). Adding a skill to `/mnt/system/base/skills/` requires the full vetting playbook + Mike approval.

## TOOLS.md cap (anchor #5)

Per-file bootstrap cap ≈ 24K chars for TOOLS.md. As we add more JamBot skills, the routing table grows toward this cap. Audit per-client TOOLS.md sizes.

## Mandatory pre-install tool — Skill Vetter

Install **Skill Vetter** (`clawhub.ai/spclaudehome/skill-vetter`) on every new tenant. It's an agent-driven scanner that reviews ClawHub skill source before install. See `annotations/skills__skill-vetter.md` for setup; `playbooks/skill-install-vetting.md` for the full workflow.

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

**Always pin a version** when installing from ClawHub. Auto-update opens a re-vetting hole — the skill you vetted is NOT the skill you have three weeks later. Per r/openclaw 1ssuze9, OpenClaw auto-updates 2-3x/week, so upstream churn is fast.

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

- `audit-anchors/anchor-02-memory-core-auto-activates.md`
- `audit-anchors/anchor-11-plugins-entries-vs-skills-entries.md`
- `audit-anchors/anchor-18-clawhavoc-supply-chain.md`
- `audit-anchors/anchor-05-per-file-bootstrap-caps.md` — TOOLS.md cap
- `annotations/skills__skill-vetter.md` — mandatory pre-install tool
- `annotations/security__prompt-injection.md` — DESCRIPTION.md injection vector
- `overrides/skill-allowlist.md` — JamBot allowlist + blocklist
- `playbooks/skill-install-vetting.md` — full vetting workflow
- `feedback_tools_md_routing.md` (memory) — TOOLS.md routing rule
- `/maintain-skills` skill — JamBot-side skills audit tool
- `/setup-skills` skill — JamBot-side skill installer

---

> **⚠️ CORRECTED 2026-07-25 — `skills.profile` does not exist.** Verified absent from the live
> `2026.5.7` schema (`openclaw config schema`, 6,441 paths — the only `skills.*` keys are
> `allowBundled`, `entries.*`, `install.*`, `limits.*`, `load.*`) **and** absent from the 7.x
> config-reference docs. The snapshot-invalidation claim holds for `skills.allowBundled` and
> `skills.entries.<id>.enabled`; treat the third as an error in the original audit, not a key to set.

<!-- verification-stamp -->
## Verification — 2026-07-25

**Method (be precise about what this stamp does and does not mean):**

- Every config key this file asserts was checked against the **live schema of the version JamBot actually runs** — `openclaw config schema` inside `openclaw-test-dev` at `2026.5.7`, 6,441 schema paths.
- Upstream page re-fetched as Markdown on 2026-07-25 (`scripts/fetch-page.sh --no-cache`).
- **Not done:** the prose was not re-read line-by-line against the 7.x docs. Upstream is at `2026.7.1`; this file is verified for our pin, not for upstream HEAD.

**Config keys asserted here: 3/6 confirmed present in the 2026.5.7 schema.**

Not resolvable as schema paths (expected for RPC method names, plugin-manifest fields, OTel metric names, and shorthand references — confirm the kind before treating as drift):

- `skills.entries.X.enabled`
- `skills.entries.coding-agent.enabled`
- `skills.profile`

If you change this file, re-run `python3 scripts/sync-annotations.py` so `lastVerified` reaches `catalog.json`.
