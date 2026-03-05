# OpenClaw Architecture Reference

_Condensed from: README.md, docs/concepts/architecture.md, docs/gateway/index.md, docs/start/getting-started.md_
_Last source update: 2026-01-22_

---

## What OpenClaw Is

- **Personal AI assistant** you run on your own devices
- A single **Gateway** (Node.js daemon) acts as the control plane for all messaging surfaces and agents
- Connects to channels you already use; replies from one central agent runtime
- Default port: `ws://127.0.0.1:18789` (Clawdbot uses `18791`)
- Runtime requirement: **Node ≥ 22**

---

## Component Diagram

```
WhatsApp / Telegram / Slack / Discord / Signal / iMessage / BlueBubbles
/ Matrix / Zalo / Google Chat / Microsoft Teams / WebChat
               │
               ▼
┌──────────────────────────────────────────────────────┐
│                      GATEWAY                         │
│             (single control plane daemon)            │
│                                                      │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────┐  │
│  │   Channels   │  │ Agent Runtime │  │  Canvas  │  │
│  │  (connectors)│  │  (Pi / RPC)   │  │  Host    │  │
│  └──────────────┘  └───────────────┘  └──────────┘  │
│                                                      │
│  ┌────────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Sessions  │  │  Tools   │  │     Skills       │ │
│  │   Model    │  │(browser, │  │ (bundled/managed/│ │
│  │            │  │ cron,    │  │  workspace)      │ │
│  │            │  │ nodes…)  │  │                  │ │
│  └────────────┘  └──────────┘  └──────────────────┘ │
│                                                      │
│  ┌──────────────────────────────────────────────────┐│
│  │              Memory / Workspace                  ││
│  │    ~/.openclaw/workspace/ (SOUL.md, TOOLS.md…)   ││
│  └──────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────┘
               │
               ├─ Pi agent (RPC mode, tool streaming)
               ├─ CLI (openclaw …)
               ├─ Control UI / WebChat (served from Gateway)
               ├─ macOS app (menu bar)
               └─ iOS / Android Nodes
```

---

## Key Components

| Component | Role |
|-----------|------|
| **Gateway** | Daemon owning all channels, sessions, config, cron, webhooks. Single WS server. |
| **Channels** | WhatsApp (Baileys), Telegram (grammY), Slack (Bolt), Discord (discord.js), Signal (signal-cli), BlueBubbles (recommended iMessage), iMessage (legacy), Google Chat, Microsoft Teams, Matrix, Zalo, Zalo Personal, WebChat |
| **Agent Runtime** | Pi agent in RPC mode — runs tool calls, streaming LLM responses |
| **Tools** | browser, canvas, nodes, cron, sessions_*, discord, gateway — toolset available to agent |
| **Skills** | Bundled / managed / workspace skill plugins (`~/.openclaw/workspace/skills/<skill>/SKILL.md`) |
| **Sessions** | One session per channel/group; `main` = direct chat; persistent session keys → Z.AI cache warm |
| **Memory** | Workspace markdown files injected as context: `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `IDENTITY.md`, `MEMORY.md` |
| **Nodes** | macOS / iOS / Android devices connected as `role: node` — expose `canvas.*`, `camera.*`, `screen.record`, `location.get`, `system.run` |
| **Canvas Host** | Serves agent-editable HTML + A2UI on default port `18793` |

---

## Message Flow (End-to-End)

```
1. Inbound message arrives on a channel (e.g. Discord)
2. Gateway validates sender (allowFrom / pairing / dmPolicy)
3. Gateway routes to the correct session (channel routing rules)
4. Session enqueues the message (queue mode)
5. Agent Runtime (Pi RPC) picks up the message
   a. Builds context: workspace files + session history
   b. Calls LLM (streaming)
   c. Executes tool calls as they stream in
   d. Collects final assistant text
6. Gateway delivers response chunks back to the originating channel
7. Presence + typing indicators emitted throughout
8. Usage tracking updated; session history saved
```

### WebSocket Event Sequence (client view)

```
Client → Gateway: req:connect  {role, deviceId, auth.token}
Gateway → Client: res (hello-ok) {presence snapshot, health, stateVersion}

Client → Gateway: req:agent  {message, sessionKey, …}
Gateway → Client: res:agent  {runId, status:"accepted"}
Gateway → Client: event:agent  (streaming chunks)
Gateway → Client: res:agent  (final) {runId, status:"ok"|"error", summary}
```

---

## Wire Protocol

| Aspect | Detail |
|--------|--------|
| Transport | WebSocket, text frames, JSON payloads |
| First frame | MUST be `connect` (hard close otherwise) |
| Requests | `{type:"req", id, method, params}` → `{type:"res", id, ok, payload\|error}` |
| Events (server-push) | `{type:"event", event, payload, seq?, stateVersion?}` |
| Auth | `connect.params.auth.token` must match `OPENCLAW_GATEWAY_TOKEN` if set |
| Idempotency | Required for `send` and `agent` (deduplication cache) |
| Node role | `connect` must include `role:"node"` + caps/commands/permissions |

### Common Events

| Event | Meaning |
|-------|---------|
| `connect.challenge` | Sent on connect; client must sign nonce (non-local) |
| `agent` | Streaming agent text / lifecycle phases |
| `chat` | Chat state updates |
| `presence` | User/session presence changes |
| `tick` | Keepalive (~every 30s) |
| `health` | Periodic health check |
| `heartbeat` | Gateway heartbeat |
| `shutdown` | Emitted before graceful close |

---

## Pairing & Trust

- All WS clients (operators + nodes) send a **device identity** on `connect`
- New device IDs → pairing approval required → Gateway issues **device token**
- **Local** connects (loopback / gateway host tailnet address) → auto-approved
- **Non-local** → must sign `connect.challenge` nonce + explicit approval
- `gateway.auth.*` applies to ALL connections (local and remote)

---

## Key Directories

| Path | Purpose |
|------|---------|
| `~/.openclaw/openclaw.json` | Main config file |
| `~/.openclaw/workspace/` | Agent workspace root (configurable via `agents.defaults.workspace`) |
| `~/.openclaw/workspace/AGENTS.md` | Agent instructions |
| `~/.openclaw/workspace/SOUL.md` | Agent personality/identity |
| `~/.openclaw/workspace/TOOLS.md` | Tool reference injected into context |
| `~/.openclaw/workspace/skills/<name>/SKILL.md` | Skill definitions |
| `~/.openclaw/credentials` | Channel credentials (e.g. WhatsApp session) |
| `~/.openclaw/state/` | Runtime state (overridden by `OPENCLAW_STATE_DIR`) |

### Environment Variable Overrides

| Variable | Effect |
|----------|--------|
| `OPENCLAW_HOME` | Home dir for internal path resolution |
| `OPENCLAW_STATE_DIR` | Override state directory |
| `OPENCLAW_CONFIG_PATH` | Override config file path |
| `OPENCLAW_GATEWAY_TOKEN` | Auth token for WS connections |
| `OPENCLAW_GATEWAY_PASSWORD` | Password auth alternative |
| `OPENCLAW_GATEWAY_PORT` | Override gateway port |

---

## Node Architecture

- Nodes connect to the **same WS server** as operators (`role: "node"`)
- Nodes declare capabilities + commands in `connect`
- Agent invokes node actions via `node.invoke` → routed to correct device
- macOS TCC permissions (camera, screen recording, notifications) gated per command
- `system.run` runs local commands on the node host (NOT the gateway host)
- `/elevated on|off` toggles elevated bash per-session (when enabled + allowlisted)
- Node pairing is **device-based**; approval stored in device pairing store

### Node Commands

| Command | Notes |
|---------|-------|
| `canvas.*` | Agent-driven visual workspace |
| `camera.snap` / `camera.clip` | Device camera capture |
| `screen.record` | Requires screen recording TCC permission |
| `location.get` | Device GPS location |
| `system.run` | Local command execution (macOS node only) |
| `system.notify` | System notification (fails if denied) |

---

## Session Model

- **`main`** session = direct 1:1 chat with the owner
- **Group / channel** sessions = isolated per-channel (or per-group with routing rules)
- Session state includes: `thinkingLevel`, `verboseLevel`, `model`, `sendPolicy`, `groupActivation`
- Context pruning: `contextPruning: cache-ttl 30m` keeps session warm; compaction flushes history
- **Persistent session key** = Z.AI prompt cache hit → fast responses (3-8s warm vs 15-30s cold)

### Session Tools (Agent-to-Agent)

| Tool | Purpose |
|------|---------|
| `sessions_list` | Discover active sessions and metadata |
| `sessions_history` | Fetch transcript logs for a session |
| `sessions_send` | Message another session (optional reply-back ping-pong) |
| `sessions_spawn` | Spawn a new agent session |

---

## Gateway CLI Commands

```bash
# Install & lifecycle
openclaw onboard --install-daemon
openclaw gateway --port 18789
openclaw gateway --port 18789 --verbose
openclaw gateway --force          # kill existing, then start
openclaw gateway install          # install as launchd/systemd service
openclaw gateway status
openclaw gateway status --deep
openclaw gateway status --json
openclaw gateway restart
openclaw gateway stop

# Operations
openclaw status
openclaw logs --follow
openclaw doctor
openclaw channels status --probe
openclaw dashboard                # open Control UI in browser
openclaw health

# Messaging
openclaw message send --target +15555550123 --message "Hello"
openclaw agent --message "Ship checklist" --thinking high

# Pairing
openclaw pairing approve <channel> <code>
```

---

## Port Reference

| Port | Default | Purpose |
|------|---------|---------|
| `18789` | Gateway | WS control plane + HTTP APIs + Control UI |
| `18791` | Clawdbot | Clawdbot Gateway (project-specific, not default OpenClaw) |
| `18793` | Canvas | Agent-editable HTML / A2UI host |
| `19001` | Dev profile | Isolated dev gateway (--dev flag) |

---

## Hot Reload Modes

| `gateway.reload.mode` | Behavior |
|-----------------------|----------|
| `off` | No config reload |
| `hot` | Apply only hot-safe changes |
| `restart` | Restart on reload-required changes |
| `hybrid` (default) | Hot-apply when safe, restart when required |

---

## Common Failure Signatures

| Signature | Likely Cause |
|-----------|-------------|
| `refusing to bind gateway ... without auth` | Non-loopback bind without token/password |
| `another gateway instance is already listening` / `EADDRINUSE` | Port conflict |
| `Gateway start blocked: set gateway.mode=local` | Config set to remote mode |
| `unauthorized` during connect | Auth token mismatch |
| `NOT_PAIRED` / `device identity required` | Missing/wrong auth token in connect |
| `PERMISSION_MISSING` on `system.run` | macOS TCC screen recording not granted |

---

## Supervision (Production)

```bash
# macOS (launchd)
openclaw gateway install
openclaw gateway status
openclaw gateway restart
# Label: ai.openclaw.gateway (or ai.openclaw.<profile>)

# Linux (systemd user)
openclaw gateway install
systemctl --user enable --now openclaw-gateway.service
sudo loginctl enable-linger <user>   # persist after logout

# Linux (system service)
sudo systemctl daemon-reload
sudo systemctl enable --now openclaw-gateway.service
```

---

## Remote Access

```bash
# SSH tunnel (fallback)
ssh -N -L 18789:127.0.0.1:18789 user@host
# Then connect clients to ws://127.0.0.1:18789 locally

# Tailscale modes (set gateway.tailscale.mode)
# off    = no tailscale automation (default)
# serve  = tailnet-only HTTPS (tailscale serve)
# funnel = public HTTPS (requires password auth)
```

- `gateway.bind` MUST stay `loopback` when Serve/Funnel is enabled
- Funnel refuses to start without `gateway.auth.mode: "password"`

---

## Minimal Config (`~/.openclaw/openclaw.json`)

```json5
{
  agent: {
    model: "anthropic/claude-opus-4-6",
  },
}
```

Full reference: https://docs.openclaw.ai/gateway/configuration

---

## Security Defaults

- `dmPolicy="pairing"` — unknown senders get a pairing code; bot ignores message
- `dmPolicy="open"` + `"*"` in allowFrom — required to allow public inbound DMs
- `agents.defaults.sandbox.mode: "non-main"` — run non-main sessions in Docker sandboxes
- Sandbox allowlist: `bash`, `process`, `read`, `write`, `edit`, `sessions_*`
- Sandbox denylist: `browser`, `canvas`, `nodes`, `cron`, `discord`, `gateway`
- Run `openclaw doctor` to surface risky DM policies
