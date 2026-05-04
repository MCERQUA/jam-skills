---
anchor: 12
slug: external-plugin-migration
status: confirmed
introduced: v2026.5.2
changelog_line: 23
upstream_pages:
  - https://docs.openclaw.ai/plugins/manage-plugins.md
  - https://docs.openclaw.ai/plugins/manifest.md
  - https://docs.openclaw.ai/cli/plugins.md
  - https://docs.openclaw.ai/channels/index.md
old_behavior: "channels and many providers bundled with openclaw npm package"
new_behavior: "wholesale migration to external @openclaw/* npm packages"
skill_files_affected:
  - "references/channels-detail.md (top)"
  - "references/plugins-system.md (Official Plugins table)"
  - "references/cli-reference.md (openclaw plugins install npm:)"
---

# Anchor #12 — External plugin migration (v5.2 wholesale)

## What changed

v5.2 line 23: wholesale list of channels/providers/utilities being moved to external npm packages.

## Live on npm now

- `@openclaw/acpx` — Codex/Claude ACP wrappers
- `@openclaw/diagnostics-otel` — OpenTelemetry export

## Prepared for 5.1-beta.x → 5.2 publishing (and shipping incrementally)

ACPX, Diagnostics-OTel, Discord, WhatsApp, Voice Call, Brave, Codex, Memory LanceDB, Microsoft Teams, Diffs, Lobster, BlueBubbles, Mattermost, Matrix, Tlon, Google Chat, LINE, Nextcloud Talk, Nostr, Zalo, Zalo Personal, QQ Bot, Synology Chat, Twitch, Feishu, Google Meet, Yuanbao.

## Install spec changes

| Spec | Introduced | Notes |
|------|-----------|-------|
| `openclaw plugins install npm:<package>` (explicit prefix) | v4.26 line 1153 | Recommended |
| `openclaw plugins install git:<spec>` | v5.2 line 38 | New |
| `openclaw plugins install --force` | v4.5 | Force reinstall |
| Bare package name | legacy | Still works for now |

## JamBot impact

When upgrading client containers to 5.2:
1. Channels currently bundled may no longer be — check each client's `channels` config against the bundled set
2. Doctor migration (anchor #7) auto-adds external plugin references for bundled channels still in use
3. Voice Call externalization is the most JamBot-relevant — voice features depend on it

## Fix instruction

`annotations/plugins__manage-plugins.md` + `overrides/jambot-plugin-policy.md`:
1. Document the bundled vs external transition
2. List which JamBot clients use which channels (from `docs/jambot/client-registry.md`)
3. Add an upgrade pre-check: `docker exec openclaw-<user> openclaw plugins list --json` → diff against expected
