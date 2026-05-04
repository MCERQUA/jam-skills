---
upstream: https://docs.openclaw.ai/plugins/architecture.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: [1, 11]
related_overrides: [openclaw-json-deltas.md]
---

# Plugin architecture — JamBot annotation

## What docs say (TL;DR)

Plugin SDK with hook registration, tool/channel/provider plugin types, manifest-driven discovery, ClawHub distribution. Bundled vs external split. Pluggable agent runtimes.

## What WE do differently

JamBot ships **zero in-house plugins** today. Cycle 6 ovui-desktop is the closest — it's an 8-tool plugin running inside the openclaw container giving the agent KDE/desktop control via CDP. See `docs/jambot/system-pages-map.md` and `/jambot-openclaw` skill.

## Audit anchors that apply

### Anchor #1 — `registerEmbeddedExtensionFactory` REMOVED in v2026.4.24 (BREAKING)

Replacement: `registerAgentToolResultMiddleware` + `contracts.agentToolResultMiddleware`. If any internal plugin still uses the legacy API, gateway boot fails on 5.2. Audit ovui-desktop plugin code before 5.2 cutover.

Full migration map: `audit-anchors/anchor-01-plugin-sdk-breaking-registerEmbeddedExtensionFactory.md`.

### Anchor #11 — `plugins.entries` vs `skills.entries` are dual-axis

A bundled component like `memory-core` registers BOTH a plugin entry AND a skill entry. Disabling only one disables only that axis. For memory specifically, the single-knob kill switch is `plugins.slots.memory: "none"` (NOT `plugins.entries.memory-core.enabled: false`).

## Externalization wave (anchor #12)

v5.2 wholesale moved many bundled plugins to external `@openclaw/*` npm packages. Live now: `@openclaw/acpx`, `@openclaw/diagnostics-otel`. Coming: Discord, WhatsApp, Voice Call, Brave, Codex, Memory LanceDB, Teams, Diffs, Lobster, BlueBubbles, Mattermost, Matrix, Tlon, Google Chat, LINE, Nextcloud Talk, Nostr, Zalo, QQ Bot, Synology Chat, Twitch, Feishu, Google Meet, Yuanbao.

Install spec changes (anchor #12):
- `openclaw plugins install npm:<name>` — explicit prefix, recommended
- `openclaw plugins install git:<spec>` — NEW v5.2
- `openclaw plugins install --force` — force reinstall

Pre-cutover audit: `docker exec openclaw-<user> openclaw plugins list --json` → diff against expected for each client.

## Burns / incidents

- 2026-05-04 audit: legacy plugin SDK API in any internal plugin will break on 5.2 (anchor #1)

## Related JamBot files

- `docs/jambot/openclaw-skill-update-2026-05-04.md` §5 — full SDK migration map
- `/jambot-openclaw` skill — container UIDs, Dockerfiles
- `/mnt/system/base/templates/openclaw.json` — canonical plugin config
- `audit-anchors/anchor-{1,11,12}.md`
