# OpenClaw Gateway Protocol Reference

## Network Model

- One Gateway process per host (recommended); owns channel connections + WS control plane
- Single multiplexed port: WS RPC + HTTP APIs + Control UI + Hooks
- Default: `ws://127.0.0.1:18789` (loopback)
- Canvas host: HTTP file server on port `18793` → `/__openclaw__/canvas/`
- Legacy TCP bridge (port 18790): **deprecated/removed** — use Gateway WS

### Port/Bind Resolution

| Setting      | Precedence |
|---|---|
| Port | `--port` → `OPENCLAW_GATEWAY_PORT` → `gateway.port` → `18789` |
| Bind | CLI → `gateway.bind` → `loopback` |

### Bind Modes
- `loopback` (default) — localhost only
- `lan` — `0.0.0.0`
- `tailnet` — Tailscale IP only
- `custom` — explicit address
- **Non-loopback binds require auth (token or password)**

---

## Wire Protocol

- **Transport**: WebSocket, text frames, JSON payloads
- **First frame MUST be** `connect` request
- Three frame types:

```json
// Request
{ "type": "req", "id": "...", "method": "...", "params": {} }

// Response
{ "type": "res", "id": "...", "ok": true, "payload": {} }
// or on error:
{ "type": "res", "id": "...", "ok": false, "error": {} }

// Event
{ "type": "event", "event": "...", "payload": {}, "seq": 0, "stateVersion": 0 }
```

- Side-effecting methods require **idempotency keys**
- Protocol version: `PROTOCOL_VERSION` in `src/gateway/protocol/schema.ts`
- Clients send `minProtocol` + `maxProtocol`; server rejects mismatches (currently v3)

---

## Handshake Sequence (3-step)

### Step 1 — Gateway → Client (pre-connect challenge)
```json
{
  "type": "event",
  "event": "connect.challenge",
  "payload": { "nonce": "...", "ts": 1737264000000 }
}
```

### Step 2 — Client → Gateway (connect request)

**Operator example:**
```json
{
  "type": "req",
  "id": "...",
  "method": "connect",
  "params": {
    "minProtocol": 3,
    "maxProtocol": 3,
    "client": {
      "id": "cli",
      "version": "1.2.3",
      "platform": "macos",
      "mode": "operator"
    },
    "role": "operator",
    "scopes": ["operator.read", "operator.write"],
    "caps": [],
    "commands": [],
    "permissions": {},
    "auth": { "token": "..." },
    "locale": "en-US",
    "userAgent": "openclaw-cli/1.2.3",
    "device": {
      "id": "device_fingerprint",
      "publicKey": "...",
      "signature": "...",
      "signedAt": 1737264000000,
      "nonce": "..."
    }
  }
}
```

**Node example:**
```json
{
  "type": "req",
  "id": "...",
  "method": "connect",
  "params": {
    "minProtocol": 3, "maxProtocol": 3,
    "client": { "id": "ios-node", "version": "1.2.3", "platform": "ios", "mode": "node" },
    "role": "node",
    "scopes": [],
    "caps": ["camera", "canvas", "screen", "location", "voice"],
    "commands": ["camera.snap", "canvas.navigate", "screen.record", "location.get"],
    "permissions": { "camera.capture": true, "screen.record": false },
    "auth": { "token": "..." },
    "locale": "en-US",
    "userAgent": "openclaw-ios/1.2.3",
    "device": { "id": "device_fingerprint", "publicKey": "...", "signature": "...", "signedAt": 1737264000000, "nonce": "..." }
  }
}
```

### Step 3 — Gateway → Client (hello-ok)
```json
{
  "type": "res",
  "id": "...",
  "ok": true,
  "payload": {
    "type": "hello-ok",
    "protocol": 3,
    "policy": { "tickIntervalMs": 15000 }
  }
}
```

When a device token is issued, `hello-ok` also includes:
```json
{
  "auth": {
    "deviceToken": "...",
    "role": "operator",
    "scopes": ["operator.read", "operator.write"]
  }
}
```

- `hello-ok` also returns: `presence`, `health`, `stateVersion`, `uptimeMs`, limits/policy

---

## Roles

| Role | Description |
|---|---|
| `operator` | Control plane client (CLI, UI, automation) |
| `node` | Capability host (camera, screen, canvas, location, voice) |

### Operator Scopes
- `operator.read`
- `operator.write`
- `operator.admin`
- `operator.approvals`
- `operator.pairing`

### Node Caps/Commands/Permissions
- `caps`: high-level capability categories declared at connect
- `commands`: allowlist for invoke (e.g. `camera.snap`, `canvas.navigate`, `screen.record`, `location.get`)
- `permissions`: granular toggles (e.g. `camera.capture`, `screen.record`)
- Gateway treats these as **claims** and enforces server-side allowlists

---

## RPC Method Categories

### Connection / System
- `connect` — handshake (first frame)
- `health` — gateway health snapshot
- `system-presence` — device presence (keyed by device identity; includes `deviceId`, `roles`, `scopes`)
- `skills.bins` — fetch skill executables list (nodes use for auto-allow checks)

### Chat / Sessions
- `chat.send` — send a message to an agent session
- `sessions_list` — list active sessions
- `sessions_history` — fetch session history
- `sessions_send` — send to an existing session
- `sessions_spawn` — spawn a sub-agent session
- `session_status` — check session state

### Agent
- Agent runs are two-stage:
  1. Immediate accepted ack (`status: "accepted"`)
  2. Final completion (`status: "ok" | "error"`) with streamed `agent` events in between

### Node Pairing (`node.pair.*`)
- `node.pair.request` — create/reuse a pending pairing request (idempotent per node; `silent: true` hint for auto-approval)
- `node.pair.list` — list pending + paired nodes
- `node.pair.approve` — approve a pending request (issues fresh token; rotates on re-pair)
- `node.pair.reject` — reject a pending request
- `node.pair.verify` — verify `{ nodeId, token }`

### Device Tokens
- `device.token.rotate` — rotate device token (requires `operator.pairing` scope)
- `device.token.revoke` — revoke device token (requires `operator.pairing` scope)

### Exec Approvals
- `exec.approval.resolve` — resolve an exec approval request (requires `operator.approvals` scope)

### Node Invoke (Gateway → Node)
- `invoke` / `invoke-res` — gateway sends node commands:
  - `canvas.*` — canvas navigation
  - `camera.*` — camera operations
  - `screen.record` — screen recording
  - `location.get` — get location
  - `sms.send` — send SMS

---

## Event Types

| Event | Direction | Meaning |
|---|---|---|
| `connect.challenge` | GW → Client | Pre-connect nonce challenge |
| `agent` | GW → Client | Streaming agent output |
| `chat` | GW → Client | Chat state updates for subscribed sessions |
| `presence` | GW → Client | User/device presence update |
| `tick` | GW → Client | Periodic keepalive (~every 15s per policy) |
| `health` | GW → Client | Periodic health snapshot |
| `heartbeat` | GW → Client | Heartbeat notification |
| `shutdown` | GW → Client | Graceful shutdown (emitted before socket close) |
| `node.pair.requested` | GW → Operator | New pairing request created |
| `node.pair.resolved` | GW → Operator | Pairing request approved/rejected/expired |
| `exec.approval.requested` | GW → Operator | Exec needs approval |

### Agent Streaming Events (after `chat.send`)
| Event | Meaning |
|---|---|
| `agent` + `stream=lifecycle` + `phase=start` | Agent started |
| `agent` + `stream=assistant` | Streaming text (cumulative, not delta) |
| `chat` + `state=delta` | State update during streaming |
| `agent` + `stream=lifecycle` + `phase=end` | LLM generation complete |
| `chat` + `state=final` | Definitive response with full content |

---

## Authentication

### Gateway Auth (client → gateway)
- Token: `OPENCLAW_GATEWAY_TOKEN` or `--token` or `gateway.auth.token`
- Password: `OPENCLAW_GATEWAY_PASSWORD` or `gateway.auth.password`
- Non-loopback binds **require** auth configured
- `connect.params.auth.token` must match or socket is closed

### Device Identity + Pairing
- All WS clients (operator + node) must include `device` identity during `connect`
- Non-local connections must **sign** the server `connect.challenge` nonce
- Control UI can omit device identity only when `gateway.controlUi.allowInsecureAuth: true`
  (or `dangerouslyDisableDeviceAuth` for break-glass)
- Local = loopback + gateway host's own tailnet address (auto-approve eligible)
- New device IDs require pairing approval unless local auto-approval is enabled

### Device Token Lifecycle
- Issued in `hello-ok.auth.deviceToken` after successful pairing
- Persist on client for future `connect` calls
- Rotate: `device.token.rotate` (requires `operator.pairing` scope)
- Revoke: `device.token.revoke` (requires `operator.pairing` scope)
- Tokens are rotated on re-pair approval

### Model Auth (gateway → LLM providers)
```bash
export ANTHROPIC_API_KEY="..."        # or store in ~/.openclaw/.env
claude setup-token                    # subscription auth (interactive TTY required)
openclaw models auth setup-token --provider anthropic
openclaw models auth paste-token --provider anthropic   # paste token from another machine
openclaw models auth order set --provider anthropic anthropic:default
openclaw models status                # check auth status
openclaw models status --check        # exits 1=expired/missing, 2=expiring
```

---

## Node Pairing Flow

1. Node connects to Gateway WS, requests pairing (`node.pair.request`)
2. Gateway stores pending request, emits `node.pair.requested`
3. Operator approves/rejects (CLI or UI)
4. On approval: fresh token issued, node reconnects with token
5. Pending requests expire after **5 minutes**

### CLI Pairing Commands
```bash
openclaw nodes pending
openclaw nodes approve <requestId>
openclaw nodes reject <requestId>
openclaw nodes status
openclaw nodes rename --node <id|name|ip> --name "Living Room iPad"
```

### Node Exec Lifecycle Events (node → gateway)
- `exec.finished` — `sessionKey`*(req)*, `runId`, `command`, `exitCode`, `timedOut`, `success`, `output`
- `exec.denied` — `sessionKey`*(req)*, `runId`, `command`, `reason`

---

## Discovery

### Bonjour / mDNS (LAN only)
- Service type: `_openclaw-gw._tcp`
- TXT keys: `role=gateway`, `lanHost`, `gatewayPort=18789`, `gatewayTls=1`, `gatewayTlsSha256`, `canvasPort=18793`, `sshPort` (full mode), `cliPath` (full mode), `tailnetDns`
- `discovery.mdns.mode`: `minimal` (default, omits `cliPath`+`sshPort`) | `full` | `off`
- `OPENCLAW_DISABLE_BONJOUR=1` — disable; `OPENCLAW_MDNS_HOSTNAME` — override hostname
- Bonjour does NOT cross networks — LAN only

### Cross-Network (Tailnet)
- Use Tailscale MagicDNS name or stable tailnet IP
- Gateway publishes `tailnetDns` hint when Tailscale detected
- `OPENCLAW_TAILNET_DNS` — force publish tailnet hint

### Transport Selection (client priority order)
1. Paired direct endpoint (if configured + reachable)
2. Bonjour LAN discovery → save as direct endpoint
3. Tailnet DNS/IP direct
4. SSH tunnel fallback

### SSH Tunnel
```bash
ssh -N -L 18789:127.0.0.1:18789 user@host
# Connect clients to ws://127.0.0.1:18789; auth token still required
```

- TLS: supported; pin via `gateway.tls` + `gateway.remote.tlsFingerprint` / `--tls-fingerprint`

---

## Gateway Config Reference (`~/.openclaw/openclaw.json`)

```json5
{
  gateway: {
    mode: "local",        // local | remote
    port: 18789,
    bind: "loopback",     // loopback | lan | tailnet | custom
    auth: {
      mode: "token",      // token | password
      token: "your-token",
      allowTailscale: true,  // Tailscale Serve identity headers satisfy auth
    },
    tailscale: {
      mode: "off",        // off | serve | funnel
      resetOnExit: false,
    },
    controlUi: {
      enabled: true,
      basePath: "/openclaw",
      // allowInsecureAuth: false,
      // dangerouslyDisableDeviceAuth: false,
    },
    remote: {
      url: "ws://gateway.tailnet:18789",
      transport: "ssh",   // ssh | direct
      token: "your-token",
    },
    trustedProxies: ["10.0.0.1"],
  },
}
```

### Hot Reload Modes
| `gateway.reload.mode` | Behavior |
|---|---|
| `off` | No config reload |
| `hot` | Apply only hot-safe changes |
| `restart` | Restart on reload-required changes |
| `hybrid` (default) | Hot-apply when safe, restart when required |

---

## Gateway CLI Commands

```bash
# Startup
openclaw gateway --port 18789
openclaw gateway --port 18789 --verbose
openclaw gateway --force            # kill listener on port first

# Status / health
openclaw gateway status
openclaw gateway status --deep
openclaw gateway status --json
openclaw status
openclaw status --all
openclaw status --deep
openclaw health --json              # full health snapshot (WS-only), exits non-zero on failure
openclaw health --timeout 10000     # override default 10s timeout
openclaw doctor

# Service lifecycle
openclaw gateway install
openclaw gateway install --force
openclaw gateway restart
openclaw gateway stop
openclaw logs --follow

# Channel / pairing
openclaw channels status --probe
openclaw channels logout && openclaw channels login --verbose
openclaw pairing list <channel>

# Nodes
openclaw nodes status
openclaw nodes pending
openclaw nodes approve <requestId>
openclaw nodes reject <requestId>
openclaw nodes rename --node <id|name|ip> --name "Name"
openclaw nodes describe --node <idOrNameOrIp>
openclaw approvals get --node <idOrNameOrIp>

# Multiple instances
OPENCLAW_CONFIG_PATH=~/.openclaw/a.json OPENCLAW_STATE_DIR=~/.openclaw-a openclaw gateway --port 19001
openclaw --dev gateway --allow-unconfigured   # dev profile (port 19001, ~/.openclaw-dev)

# Protocol codegen
pnpm protocol:gen
pnpm protocol:gen:swift
pnpm protocol:check
```

---

## Troubleshooting

### Command Ladder (run in order)
```bash
openclaw status
openclaw gateway status
openclaw logs --follow
openclaw doctor
openclaw channels status --probe
```

### Common Failure Signatures

| Signature | Issue |
|---|---|
| `refusing to bind gateway ... without auth` | Non-loopback bind without token/password |
| `another gateway instance is already listening` / `EADDRINUSE` | Port conflict |
| `Gateway start blocked: set gateway.mode=local` | Config set to remote mode |
| `unauthorized` during connect | Auth token/password mismatch |
| `device identity required` | Missing device auth; non-secure context |
| `NOT_PAIRED` / `device identity required` (hello.error.code) | Auth token missing or invalid |
| `NODE_BACKGROUND_UNAVAILABLE` | Node app must be in foreground |
| `*_PERMISSION_REQUIRED` | Missing OS permission on node |
| `SYSTEM_RUN_DENIED: approval required` | Exec approval pending |
| `SYSTEM_RUN_DENIED: allowlist miss` | Command blocked by allowlist |
| `drop guild message (mention required)` | Group message needs @mention |
| `RPC probe: failed` (runtime running) | Gateway alive but wrong auth/url |

### No Replies Diagnosis
```bash
openclaw pairing list <channel>
openclaw config get channels
openclaw logs --follow
```
- Check: pairing pending, mention gating, allowlist mismatches

### Dashboard Won't Connect
```bash
openclaw gateway status --json
openclaw doctor
```
- Check: auth mode/token match, device identity required, correct host:port

### After Upgrade Breakage
```bash
openclaw gateway install --force
openclaw gateway restart
openclaw devices list
openclaw doctor
```

### WhatsApp Relink
```bash
openclaw channels logout
openclaw channels login --verbose
```
- Trigger: status codes 409–515 or `loggedOut` in logs

### State Files
- `~/.openclaw/nodes/paired.json` — paired nodes (treat as sensitive)
- `~/.openclaw/nodes/pending.json` — pending pairing requests
- `~/.openclaw/agents/<agentId>/sessions/sessions.json` — session store

---

## Legacy Bridge Protocol (Historical — Removed)

- TCP JSONL on port `18790` — **no longer started in current builds**
- `bridge.*` config keys now fail validation — run `openclaw doctor --fix` to strip
- Nodes connect via Gateway WS instead
- Handshake was: `hello` → (if unpaired) `pair-request` → `pair-ok` → `hello-ok`
- `hello-ok` returned `serverName`, optional `canvasHostUrl`
