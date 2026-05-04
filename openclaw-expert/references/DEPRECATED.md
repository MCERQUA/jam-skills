# `references/` is DEPRECATED — superseded 2026-05-04

Pre-redesign prose snapshots from 2026-03-04 / 2026-03-18 / 2026-04-01. **Do not extend.** Most content is stale (see `docs/jambot/openclaw-skill-update-2026-05-04.md` for ~6.5 weeks of drift across 23 OpenClaw releases v4.20→v5.2).

## Where things moved

| Old reference file | New location |
|--------------------|--------------|
| Upstream prose copies (architecture, gateway, channels, etc.) | Lazy-fetch via `scripts/fetch-page.sh <page-id>` from `catalog.json` (464 indexed pages) |
| JamBot-specific deltas | `annotations/<page-id>.md` — keyed by upstream URL |
| What JamBot does differently than docs | `overrides/*.md` |
| Multi-page workflows | `playbooks/*.md` |
| Version-specific corrections (v4.20→v5.2 drift) | `audit-anchors/anchor-NN-*.md` (15 confirmed) |

## Specific migrations

| Old file | Successor |
|----------|-----------|
| `session-recovery-and-empty-finals.md` | `playbooks/debug-empty-final.md` (copied; canonical lives there now) |
| `architecture-overview.md` | `cache/concepts__architecture.md` (lazy) + `annotations/concepts__architecture.md` (TODO) |
| `gateway-configuration.md` | `annotations/gateway__configuration.md` (P0 ✅) |
| `agent-runtime.md` | `annotations/concepts__agent.md` (P0 ✅) |
| `memory-system.md` | `annotations/concepts__memory.md` (P0 ✅) |
| `plugins-system.md` | `annotations/plugins__architecture.md` (P0 ✅) |
| `tools-and-exec.md` | `annotations/tools__exec.md` (P0 ✅) |
| `channels-detail.md` / `channels-overview.md` | `annotations/channels__*.md` (Phase 2 — TODO) |
| `cli-reference.md` | `annotations/cli__*.md` (Phase 2 — TODO) |
| `models-and-providers.md` | `annotations/providers__*.md` (Phase 2 — TODO) |
| `system-prompt.md` | `annotations/concepts__system-prompt.md` (Phase 2 — TODO) |
| `sessions-and-context.md` | `annotations/concepts__session.md` + `annotations/reference__session-management-compaction.md` (Phase 2 — TODO) |
| `automation.md` | `annotations/automation__*.md` (Phase 2 — TODO) |
| `multi-agent.md` | `annotations/concepts__multi-agent.md` (Phase 2 — TODO) |
| `web-tools.md` | `annotations/tools__web*.md` (Phase 2 — TODO) |
| `acp-agents.md` | `annotations/tools__acp-agents.md` (Phase 2 — TODO) |
| `canvas-and-nodes.md` | `annotations/nodes__*.md` (Phase 2 — TODO) |
| `gateway-protocol.md` / `gateway-advanced.md` / `http-apis.md` | `annotations/gateway__*.md` (Phase 2 — TODO) |
| `security.md` | `annotations/security__*.md` + `overrides/jambot-exec-policy.md` (Phase 2/3 — TODO) |
| `troubleshooting.md` | `annotations/help__troubleshooting.md` + `playbooks/*.md` (Phase 2 — TODO) |
| `skills-system.md` | `annotations/tools__skills*.md` (Phase 2 — TODO) |
| `glossary.md` | folded into SKILL.md or kept as-is (decision pending) |
| `install-hetzner.md` | `annotations/install__hetzner.md` + `overrides/docker-deployment.md` ✅ |
| `teaching-presentations.md` | LARGELY EVERGREEN — keep as-is for now |

## When will the rest migrate?

Phase 2 (P1 corrections) and Phase 3 (full sweep) per the audit doc's recommended P0 sequence. Until then, references in this directory still LOAD on skill use but should NOT be extended.

If you find yourself about to edit a file in `references/`, stop and instead:
1. Run `bash scripts/lookup.sh <topic>` to find the upstream page
2. Run `bash scripts/fetch-page.sh <page-id>` to cache the current upstream content
3. Write your delta into `annotations/<page-id>.md`
4. Add a `lastVerified` date in frontmatter
