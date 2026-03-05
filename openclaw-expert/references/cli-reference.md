# OpenClaw CLI Reference

## Global Flags

| Flag | Description |
|------|-------------|
| `--dev` | Isolate state under `~/.openclaw-dev`, shift default ports |
| `--profile <name>` | Isolate state under `~/.openclaw-<name>` |
| `--no-color` / `NO_COLOR=1` | Disable ANSI colors |
| `--update` | Shorthand for `openclaw update` |
| `-V`, `-v`, `--version` | Print version and exit |
| `--json` | Machine-readable output (disables styling/spinner) |

---

## Setup & First-Run

### `setup` — Initialize config + workspace
```bash
openclaw setup
openclaw setup --workspace ~/.openclaw/workspace
openclaw setup --wizard
openclaw setup --non-interactive --mode local
openclaw setup --mode remote --remote-url ws://gateway-host:18789 --remote-token <token>
```
- `--wizard` runs the full onboarding wizard
- Wizard auto-runs when any of `--non-interactive`, `--mode`, `--remote-url`, `--remote-token` are present

### `onboard` — Interactive wizard (gateway + workspace + channels + skills)
```bash
openclaw onboard
openclaw onboard --flow quickstart
openclaw onboard --flow manual
openclaw onboard --mode remote --remote-url ws://gateway-host:18789
```

**Non-interactive custom provider:**
```bash
openclaw onboard --non-interactive \
  --auth-choice custom-api-key \
  --custom-base-url "https://llm.example.com/v1" \
  --custom-model-id "foo-large" \
  --custom-api-key "$CUSTOM_API_KEY" \
  --custom-compatibility openai
```

**Key `--auth-choice` values:** `setup-token` | `token` | `anthropic-api-key` | `openai-api-key` | `openrouter-api-key` | `gemini-api-key` | `zai-api-key` | `custom-api-key` | `skip`

**Key flags:**
| Flag | Description |
|------|-------------|
| `--flow <quickstart\|manual\|advanced>` | Setup depth |
| `--gateway-port <port>` | Port to bind |
| `--gateway-bind <loopback\|lan\|tailnet\|auto\|custom>` | Bind mode |
| `--gateway-auth <token\|password>` | Auth mode |
| `--install-daemon` / `--no-install-daemon` | Install background service |
| `--daemon-runtime <node\|bun>` | Runtime (bun not recommended) |
| `--skip-channels` / `--skip-skills` / `--skip-health` | Skip wizard steps |
| `--non-interactive` | Script mode (suppress prompts) |

> Note: `--json` does NOT imply non-interactive. Use `--non-interactive` explicitly for scripts.

### `configure` — Interactive config wizard
```bash
openclaw configure
openclaw configure --section models --section channels
```
- Sections: models, channels, gateway, devices, agent defaults
- Same wizard as `openclaw config` (no subcommand)

---

## Config Management

### `config` — Non-interactive get/set/unset

```bash
openclaw config get browser.executablePath
openclaw config set browser.executablePath "/usr/bin/google-chrome"
openclaw config set agents.defaults.heartbeat.every "2h"
openclaw config set agents.list[0].tools.exec.node "node-id-or-name"
openclaw config set gateway.port 19001 --json
openclaw config set channels.whatsapp.groups '["*"]' --json
openclaw config unset tools.web.search.apiKey
openclaw config get agents.list
openclaw config set agents.list[1].tools.exec.node "node-id-or-name"
```
- Paths use dot or bracket notation
- Values parsed as JSON5; use `--string` to force string; use `--json` to require JSON5
- **Restart the gateway after edits**

---

## Diagnostics

### `doctor` — Health checks + guided repairs
```bash
openclaw doctor
openclaw doctor --repair
openclaw doctor --deep
openclaw doctor --yes            # headless, accept defaults
openclaw doctor --non-interactive
```
- `--repair` / `--fix`: writes backup to `~/.openclaw/openclaw.json.bak`, drops unknown keys
- `--deep`: scan system services for extra gateway installs
- Interactive prompts only run when stdin is a TTY and `--non-interactive` is not set

**Troubleshooting: macOS launchctl env overrides (persistent "unauthorized" errors):**
```bash
launchctl getenv OPENCLAW_GATEWAY_TOKEN
launchctl getenv OPENCLAW_GATEWAY_PASSWORD
launchctl unsetenv OPENCLAW_GATEWAY_TOKEN
launchctl unsetenv OPENCLAW_GATEWAY_PASSWORD
```

### `health` — Quick gateway health check
```bash
openclaw health
openclaw health --json
openclaw health --verbose
```
- `--verbose`: runs live probes, prints per-account timings

### `status` — Channel diagnostics + session overview
```bash
openclaw status
openclaw status --all
openclaw status --deep
openclaw status --usage
openclaw status --json
openclaw status --verbose
openclaw status --timeout <ms>
```
- `--deep`: live probes (WhatsApp, Telegram, Discord, Google Chat, Slack, Signal)
- `--all`: full read-only pasteable diagnosis
- `--usage`: show model provider usage/quota
- Includes Gateway + node host service status, update availability

---

## Gateway

### `gateway` — Run the WebSocket server

```bash
openclaw gateway
openclaw gateway run
```

**Options:**
| Flag | Description |
|------|-------------|
| `--port <port>` | WebSocket port (default ~18789) |
| `--bind <loopback\|lan\|tailnet\|auto\|custom>` | Listener bind mode |
| `--auth <token\|password>` | Auth mode override |
| `--token <token>` | Token override |
| `--password <password>` | Password override |
| `--tailscale <off\|serve\|funnel>` | Expose via Tailscale |
| `--tailscale-reset-on-exit` | Reset Tailscale config on shutdown |
| `--allow-unconfigured` | Skip `gateway.mode=local` requirement |
| `--dev` | Create dev config + workspace if missing |
| `--reset` | Reset dev config + creds + sessions (requires `--dev`) |
| `--force` | Kill existing listener on port before starting |
| `--verbose` | Verbose logs |
| `--ws-log <auto\|full\|compact>` | WebSocket log style |
| `--compact` | Alias for `--ws-log compact` |
| `--raw-stream` | Log raw model stream events to jsonl |

### `gateway` service management
```bash
openclaw gateway install
openclaw gateway start
openclaw gateway stop
openclaw gateway restart
openclaw gateway uninstall
```
- All lifecycle commands accept `--json`
- `gateway install` options: `--port`, `--runtime`, `--token`, `--force`, `--json`
- Default runtime: Node (bun **not recommended** — WhatsApp/Telegram bugs)

### `gateway health`
```bash
openclaw gateway health --url ws://127.0.0.1:18789
```

### `gateway status`
```bash
openclaw gateway status
openclaw gateway status --json
openclaw gateway status --no-probe
openclaw gateway status --deep
```
- `--no-probe`: skip RPC probe (service-only view)
- `--deep`: scan system-level services too

### `gateway probe` — Debug all reachable gateways
```bash
openclaw gateway probe
openclaw gateway probe --json
openclaw gateway probe --ssh user@gateway-host
openclaw gateway probe --ssh user@host:port --ssh-identity ~/.ssh/id_ed25519
openclaw gateway probe --ssh-auto
```
- Always probes configured remote AND localhost
- `--ssh-auto`: pick first discovered gateway host

### `gateway call` — Low-level RPC
```bash
openclaw gateway call status
openclaw gateway call logs.tail --params '{"sinceMs": 60000}'
```
**Common RPCs:** `config.apply` | `config.patch` | `update.run`

### `gateway discover` — Bonjour/mDNS scan
```bash
openclaw gateway discover
openclaw gateway discover --timeout 4000
openclaw gateway discover --json | jq '.beacons[].wsUrl'
```

**Shared RPC flags (all query subcommands):**
| Flag | Default |
|------|---------|
| `--url <url>` | From config |
| `--token <token>` | From config |
| `--password <password>` | From config |
| `--timeout <ms>` | Varies |
| `--expect-final` | Wait for final response |

> When `--url` is set, config/env credentials are NOT applied automatically. Pass `--token` or `--password` explicitly.

---

## Messaging

### `message` — Unified outbound messaging

```bash
openclaw message <subcommand> [flags]
```

**Common flags:**
| Flag | Description |
|------|-------------|
| `--channel <name>` | Required if >1 channel configured |
| `--target <dest>` | Destination channel or user |
| `--account <id>` | Channel account id |
| `--json` | Machine output |
| `--dry-run` | Preview without sending |
| `--verbose` | Verbose output |

**Target format by provider:**
| Channel | Format |
|---------|--------|
| WhatsApp | E.164 or group JID |
| Telegram | chat id or `@username` |
| Discord | `channel:<id>` or `user:<id>` |
| Google Chat | `spaces/<spaceId>` or `users/<userId>` |
| Slack | `channel:<id>` or `user:<id>` |
| Signal | `+E.164`, `group:<id>`, `username:<name>` |
| iMessage | handle, `chat_id:<id>`, `chat_guid:<guid>` |
| MS Teams | `19:...@thread.tacv2` or `conversation:<id>` |

**Core actions:**
```bash
# Send
openclaw message send --channel discord --target channel:123 --message "hi" --reply-to 456

# Poll (WhatsApp/Discord/MS Teams)
openclaw message poll --channel discord \
  --target channel:123 \
  --poll-question "Snack?" \
  --poll-option Pizza --poll-option Sushi \
  --poll-multi --poll-duration-hours 48

# React
openclaw message react --channel slack --target C123 --message-id 456 --emoji "✅"
openclaw message react --channel signal \
  --target signal:group:abc123 --message-id 1737630212345 \
  --emoji "✅" --target-author-uuid 123e4567-e89b-12d3-a456-426614174000

# Read history (Discord/Slack)
openclaw message read --channel discord --target channel:123 --limit 50

# Edit / Delete
openclaw message edit --channel discord --target channel:123 --message-id 456 --message "updated"
openclaw message delete --channel discord --target channel:123 --message-id 456

# Telegram inline buttons
openclaw message send --channel telegram --target @mychat --message "Choose:" \
  --buttons '[ [{"text":"Yes","callback_data":"cmd:yes"}], [{"text":"No","callback_data":"cmd:no"}] ]'

# MS Teams proactive
openclaw message send --channel msteams \
  --target conversation:19:abc@thread.tacv2 --message "hi"

# Broadcast
openclaw message broadcast --channel all --targets "#general" --targets "@user1" --message "hi"
```

**Other actions:** `pin` | `unpin` | `pins` | `reactions` | `permissions` | `search` | `timeout` | `kick` | `ban`

**Thread actions (Discord):**
```bash
openclaw message thread create --target channel:123 --thread-name "New Thread" --message "first post"
openclaw message thread reply --target thread:456 --message "reply"
openclaw message thread list --guild-id 789
```

**Discord-specific:**
```bash
openclaw message role add --guild-id 123 --user-id 456 --role-id 789
openclaw message emoji list --guild-id 123
openclaw message event create --guild-id 123 --event-name "Meetup" --start-time "2026-03-01T18:00:00Z"
openclaw message voice status --guild-id 123 --user-id 456
```

---

## Agent

### `agent` — Run one agent turn
```bash
openclaw agent --to +15555550123 --message "status update" --deliver
openclaw agent --agent ops --message "Summarize logs"
openclaw agent --session-id 1234 --message "Summarize inbox" --thinking medium
openclaw agent --agent ops --message "Generate report" --deliver --reply-channel slack --reply-to "#reports"
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--message <text>` | **Required** |
| `--to <dest>` | Session key + optional delivery target |
| `--agent <id>` | Target a configured agent directly |
| `--session-id <id>` | Explicit session id |
| `--thinking <off\|minimal\|low\|medium\|high\|xhigh>` | Thinking level (GPT-5.2/Codex) |
| `--deliver` | Deliver reply to `--to` target |
| `--reply-channel <channel>` | Override delivery channel |
| `--reply-to <dest>` | Override delivery destination |
| `--local` | Use embedded agent (skip Gateway) |
| `--channel <name>` | Channel context |
| `--verbose <on\|full\|off>` | Verbosity |
| `--json` | Machine output |
| `--timeout <seconds>` | Request timeout |

### `agents` — Manage isolated agents
```bash
openclaw agents list
openclaw agents list --bindings
openclaw agents add work --workspace ~/.openclaw/workspace-work
openclaw agents add --workspace /path --model provider/model --bind discord:work --non-interactive
openclaw agents set-identity --workspace ~/.openclaw/workspace --from-identity
openclaw agents set-identity --agent main --name "OpenClaw" --emoji "🦞" --avatar avatars/openclaw.png
openclaw agents delete work
openclaw agents delete work --force
```

**Identity config:**
```json5
{
  agents: {
    list: [
      {
        id: "main",
        identity: {
          name: "OpenClaw",
          theme: "space lobster",
          emoji: "🦞",
          avatar: "avatars/openclaw.png",
        },
      },
    ],
  },
}
```

---

## Sessions & Memory

### `sessions` — List stored conversation sessions
```bash
openclaw sessions
openclaw sessions --active 120
openclaw sessions --json
openclaw sessions --verbose
openclaw sessions --store <path>
```

### `memory` — Semantic memory search & indexing
```bash
openclaw memory status
openclaw memory status --deep
openclaw memory status --deep --index
openclaw memory status --agent main
openclaw memory index
openclaw memory index --verbose
openclaw memory index --agent main --verbose
openclaw memory search "release checklist"
```
- Default plugin: `memory-core` (disable: set `plugins.slots.memory = "none"`)
- `--agent <id>`: scope to one agent (default: all)
- `--deep --index`: reindex if store is dirty
- Includes paths from `memorySearch.extraPaths`

---

## Channels

### `channels` — Manage chat channel accounts
```bash
openclaw channels list
openclaw channels list --json
openclaw channels status
openclaw channels status --probe
openclaw channels logs --channel discord --lines 100
openclaw channels add
openclaw channels add --channel telegram --account alerts --name "Alerts Bot" --token $TELEGRAM_BOT_TOKEN
openclaw channels add --channel discord --account work --name "Work Bot" --token $DISCORD_BOT_TOKEN
openclaw channels remove --channel discord --account work --delete
openclaw channels login --channel whatsapp
openclaw channels logout --channel whatsapp
```

**Supported channels:** `whatsapp` | `telegram` | `discord` | `googlechat` | `slack` | `mattermost` | `signal` | `imessage` | `msteams`

---

## Models

### `models` — Model discovery and auth
```bash
openclaw models status
openclaw models status --probe
openclaw models status --check          # exit 1=expired/missing, 2=expiring
openclaw models status --probe-provider anthropic
openclaw models list
openclaw models list --all
openclaw models list --provider openai
openclaw models set anthropic/claude-opus-4-5
openclaw models set openrouter/moonshotai/kimi-k2
openclaw models set-image provider/model
openclaw models scan
openclaw models scan --provider openai --set-default
```

**Auth setup (preferred: setup-token):**
```bash
claude setup-token
openclaw models auth setup-token --provider anthropic
openclaw models auth login --provider openai
openclaw models auth add
openclaw models auth paste-token --provider anthropic --expires-in 365d
openclaw models status
```

**Aliases & fallbacks:**
```bash
openclaw models aliases list
openclaw models fallbacks list
openclaw models fallbacks add anthropic/claude-haiku-4-5
openclaw models fallbacks clear
openclaw models image-fallbacks add provider/model
```

**Auth order:**
```bash
openclaw models auth order get --provider anthropic
openclaw models auth order set --provider anthropic profile1 profile2
openclaw models auth order clear --provider anthropic
```

---

## Skills & Plugins

### `skills` — Inspect available skills
```bash
openclaw skills list
openclaw skills list --eligible
openclaw skills info <name>
openclaw skills check
```
- `--eligible`: show only ready skills
- `--verbose`: include missing requirements detail

### `plugins` — Manage gateway extensions
```bash
openclaw plugins list
openclaw plugins list --json
openclaw plugins info <id>
openclaw plugins install <path|.tgz|npm-spec>
openclaw plugins enable <id>
openclaw plugins disable <id>
openclaw plugins doctor
```
- Most plugin changes require a gateway restart

---

## Pairing

### `pairing` — Approve DM pairing requests
```bash
openclaw pairing list whatsapp
openclaw pairing approve whatsapp <code> --notify
```

---

## Update

### `update` — Update OpenClaw
```bash
openclaw update
openclaw update status
openclaw update wizard
openclaw update --channel beta
openclaw update --channel dev
openclaw update --channel stable
openclaw update --tag beta
openclaw update --no-restart
openclaw update --json
openclaw --update                   # shorthand alias
```

**Options:**
| Flag | Description |
|------|-------------|
| `--channel <stable\|beta\|dev>` | Persistent channel switch |
| `--tag <dist-tag\|version>` | One-time version override |
| `--no-restart` | Skip Gateway restart after update |
| `--json` | Machine-readable `UpdateRunResult` |
| `--timeout <seconds>` | Per-step timeout (default 1200s) |

**`update status`:**
```bash
openclaw update status
openclaw update status --json
openclaw update status --timeout 10
```

**Channel behavior:**
- `dev` → git checkout of `main`, fetch + rebase, build locally
- `stable` / `beta` → install from npm matching dist-tag
- Downgrades require confirmation

**Git checkout flow:**
1. Requires clean worktree
2. Switches to selected channel (tag/branch)
3. Dev: preflight lint + TypeScript build; walks back up to 10 commits on failure
4. `pnpm install` (npm fallback)
5. Builds + builds Control UI
6. Runs `openclaw doctor` as final check
7. Syncs plugins to active channel

---

## Logs

### `logs` — Tail gateway logs via RPC
```bash
openclaw logs
openclaw logs --follow
openclaw logs --json
openclaw logs --limit 500
openclaw logs --local-time
openclaw logs --plain
openclaw logs --no-color
openclaw logs --follow --local-time
```
- Works in remote mode (over RPC, no SSH needed)
- `--local-time`: render timestamps in local timezone
- `--json`: line-delimited JSON (one event per line)

---

## Nodes

### `nodes` — Manage paired node devices
```bash
openclaw nodes list
openclaw nodes list --connected
openclaw nodes list --last-connected 24h
openclaw nodes pending
openclaw nodes approve <requestId>
openclaw nodes reject <requestId>
openclaw nodes status
openclaw nodes describe --node <id|name|ip>
openclaw nodes rename --node <id|name|ip> --name "My Mac"
```

**Exec on node:**
```bash
openclaw nodes run --node <id|name|ip> git status
openclaw nodes run --node <id|name|ip> --raw "git status"
openclaw nodes run --agent main --node <id|name|ip> --raw "git status"
openclaw nodes invoke --node <id|name|ip> --command system.run --params '{"cmd":"ls"}'
```

**Camera:**
```bash
openclaw nodes camera list --node <id>
openclaw nodes camera snap --node <id> --facing front --max-width 1280
openclaw nodes camera clip --node <id> --duration 10s --no-audio
```

**Canvas/screen:**
```bash
openclaw nodes canvas snapshot --node <id> --format png
openclaw nodes canvas present --node <id> --target https://example.com
openclaw nodes canvas navigate https://example.com --node <id>
openclaw nodes canvas hide --node <id>
openclaw nodes screen record --node <id> --duration 30s --fps 30
```

**Notifications (macOS):**
```bash
openclaw nodes notify --node <id> --title "Alert" --body "message" --priority active
```

### `node` — Run/manage headless node host service
```bash
openclaw node run --host <gateway-host> --port 18789
openclaw node status
openclaw node install --host <gateway-host> --port 18789
openclaw node install --tls --tls-fingerprint <sha256>
openclaw node uninstall
openclaw node stop
openclaw node restart
```

---

## Cron

```bash
openclaw cron status
openclaw cron list
openclaw cron list --all
openclaw cron add --name "daily-report" --every "24h" --message "Generate daily report"
openclaw cron add --name "morning" --at "08:00" --system-event "Good morning"
openclaw cron add --name "weekly" --cron "0 9 * * 1" --message "Weekly summary"
openclaw cron edit <id>
openclaw cron rm <id>
openclaw cron enable <id>
openclaw cron disable <id>
openclaw cron runs --id <id> --limit 20
openclaw cron run <id> --force
```
- All `cron` commands accept `--url`, `--token`, `--timeout`, `--expect-final`
- `--at` | `--every` | `--cron` are mutually exclusive
- `--system-event` | `--message` are mutually exclusive

---

## System

```bash
openclaw system event --text "Deploy complete" --mode now
openclaw system event --text "Check inbox" --mode next-heartbeat
openclaw system heartbeat last
openclaw system heartbeat enable
openclaw system heartbeat disable
openclaw system presence
```
- All accept `--url`, `--token`, `--timeout`, `--expect-final`, `--json`

---

## TUI & Dashboard

```bash
openclaw tui
openclaw tui --url ws://127.0.0.1:18789 --token <token>
openclaw tui --session <key>
openclaw tui --message "hello" --deliver
openclaw tui --thinking medium
openclaw tui --history-limit 50

openclaw dashboard              # Open Control UI in browser
```

---

## Security & Reset

```bash
openclaw security audit
openclaw security audit --deep
openclaw security audit --fix

openclaw reset
openclaw reset --scope config
openclaw reset --scope config+creds+sessions
openclaw reset --scope full --yes --non-interactive

openclaw uninstall --service
openclaw uninstall --state
openclaw uninstall --all --yes --non-interactive
openclaw uninstall --dry-run
```

---

## Browser Control

```bash
openclaw browser status
openclaw browser start
openclaw browser stop
openclaw browser tabs
openclaw browser open https://example.com
openclaw browser screenshot --full-page
openclaw browser snapshot --format aria
openclaw browser navigate https://example.com
openclaw browser click <ref>
openclaw browser type <ref> "search text" --submit
openclaw browser press "Enter"
openclaw browser fill --fields '{"#email":"user@example.com","#pass":"secret"}'
openclaw browser evaluate --fn "return document.title"
openclaw browser pdf
openclaw browser wait --text "Loading complete"
openclaw browser dialog --accept
```

---

## Other Utilities

```bash
# ACP bridge for IDEs
openclaw acp

# Docs search
openclaw docs "how to configure channels"

# DNS setup (CoreDNS + Tailscale wide-area discovery)
openclaw dns setup
openclaw dns setup --apply

# Sandbox management
openclaw sandbox list
openclaw sandbox recreate
openclaw sandbox explain

# Webhooks (Gmail Pub/Sub)
openclaw webhooks gmail setup --account user@gmail.com
openclaw webhooks gmail run

# Hooks (agent hooks)
openclaw hooks list
openclaw hooks info <name>
openclaw hooks enable <name>
openclaw hooks disable <name>
openclaw hooks install <path>
openclaw hooks update

# Approvals
openclaw approvals get
openclaw approvals set
openclaw approvals allowlist add <pattern>
openclaw approvals allowlist remove <pattern>

# Devices
openclaw devices        # Device pairing + token management
```
