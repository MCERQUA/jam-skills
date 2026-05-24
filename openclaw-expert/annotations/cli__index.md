---
upstream: https://docs.openclaw.ai/cli/index.md
relevance: jambot-critical
last-verified: 2026-05-23
audit_anchors: [19]
related_pages: [cli__gateway, cli__doctor, cli__plugins, cli__sessions, cli__sandbox, help__troubleshooting]
---

# CLI reference — JamBot annotation

## Anchor #19 — `openclaw doctor` is destructive (added 2026-05-23)

Per anchor-19 + r/openclaw 1ri9nt0: `openclaw doctor --fix` overwrites custom config with defaults. Multiple gateway-won't-start incidents in the community trace to this command. JamBot rule: never run on a tenant without a fresh git-backup of `openclaw.json`. See `playbooks/safe-config-edit.md`.

The `openclaw doctor` (no `--fix`) diagnostic-only run is safer but still surfaces "fixes" suggestions you should not blindly accept. Read the output, change one thing at a time via `openclaw config set`, git-commit each change.

## Slash commands (canonical, added 2026-05-23)

| Command | Purpose | Source |
|---|---|---|
| `/new` | Clear conversation buffer (preserves SOUL.md/MEMORY.md/etc) | r/openclaw 1ssuze9 |
| `/compact` | Force compaction with optional focus hint: `/compact <guidance>` | docs + 1qzyibu |
| `/btw` | Fire a side conversation without polluting main context | 1ssuze9 |

**`/new` cost-cutting note (1rp8t9r):** can cut cost 40-60% on long-running sessions. **Caveat (u/EquivalentFactor7591 +11, 1rp8t9r):** prompt caching makes `/new` MORE expensive when used mid-topic because cache invalidates. Rule: `/new` at topic boundaries, not for short follow-ups.

## What docs say (TL;DR)

`openclaw <verb>` covers gateway, channels, agents, sessions, memory, models, nodes, cron, hooks, plugins, doctor, etc. Each verb has its own page.

## New CLI commands (v4.20 → v5.2; audit doc §2.2)

### Gateway / lifecycle

| Command | Introduced | Notes |
|---------|-----------|-------|
| `openclaw gateway restart --force --wait <duration>` | v5.2 | Replaces ad-hoc `--force` flag; wait honored |
| `openclaw doctor.memory.remHarness` (RPC) | v4.29 line 416 | Read-only memory diagnostics |

### Plugins (heavy v4.x activity)

| Command | Introduced |
|---------|-----------|
| `openclaw plugins registry [--refresh]` | v4.25 line 1385 |
| `openclaw plugins deps` | v4.27/4.29 line 518 |
| `openclaw plugins install --force` | v4.5 |
| `openclaw plugins install npm:<package>` (explicit prefix) | v4.26 line 1153 |
| `openclaw plugins install git:<spec>` | v5.2 line 38 |
| `openclaw plugins inspect <id>` | v4.27 line 844 |

### Migration / config

| Command | Introduced | Notes |
|---------|-----------|-------|
| `openclaw migrate plan --dry-run --json` | v4.26 line 1060 | Idempotent migration planner |
| `openclaw proxy validate` | v5.2 line 33 | Validates `proxy.*` config (anchor — proxy.enabled v4.27) |

### Channels / pairing

| Command | Introduced |
|---------|-----------|
| `openclaw nodes remove --node <id\|name\|ip>` | v4.26 line 1085 |
| `openclaw matrix encryption setup` | v4.26 line 1057 |
| `openclaw matrix verify self` / `verify confirm-sas` | v4.24/4.29 line 530 |

### Browser

| Command | Introduced |
|---------|-----------|
| `openclaw browser click-coords` | v4.24 |
| `openclaw browser doctor --deep` | v4.25 line 1369 |
| `openclaw browser start --headless` | v4.25 line 1373 |

### Inference (NEW hub v4.7)

| Command | Introduced |
|---------|-----------|
| `openclaw infer model run` | v4.7 line 2925 |
| `openclaw infer image generate` | v4.7 |
| `openclaw infer image describe` | v4.7 |
| `openclaw infer image edit` | v4.7 |
| `openclaw infer describe-many` | v4.7 |
| `openclaw infer model run --gateway` (skip transcript/bootstrap) | v4.27 line 864 |

### Other

| Command | Introduced |
|---------|-----------|
| `openclaw exec-policy show / preset / set` | v4.10 line 2747 |
| `openclaw cron add --thread-id` | v4.27 line 847 |
| `openclaw cron edit --failure-alert-include-skipped` | v4.26 line 1235 |
| `openclaw qa suite [--allow-failures]` | v4.10 line 2350 |
| `openclaw qa telegram` / `openclaw qa matrix` | v4.20 line 2744 |
| `openclaw memory lab character-vibes` | v4.9 |
| `voicecall setup` / `voicecall smoke` | v4.24 |
| `googlemeet doctor --oauth` / `recover-tab` / `end-active-conference` / `test-listen` | v4.24 / v5.2 line 18 |

## JamBot frequent-use cheat sheet

```bash
# Inside any client container
docker exec -it openclaw-<user> bash

# Then:
openclaw status                    # general health
openclaw doctor                    # config validation + 5.2 migrations
openclaw gateway restart --wait 60s  # NEW v5.2 — clean restart
openclaw plugins list --json       # what's loaded (anchor #12 audit)
openclaw plugins registry --refresh  # NEW v4.25 — force registry update
openclaw sandbox explain           # debug tool-policy layering
openclaw migrate plan --dry-run    # what would 5.2 doctor change?
openclaw config get agents.defaults.compaction  # check anchor #6 keys
openclaw infer model run --gateway "test prompt"  # test LLM without bootstrap
```

## Related JamBot files

- `annotations/help__troubleshooting.md` — triage ladder
- `audit-anchors/anchor-{3,7,12}.md`
- `/jambot-openclaw` skill — container UIDs, z-code wrapper, `jb` CLI
