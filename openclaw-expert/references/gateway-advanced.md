# OpenClaw Gateway — Advanced Reference

---

## Heartbeat

Periodic agent check-ins that surface urgent items without constant notifications.

### Config
```json5
{
  heartbeat: {
    every: "30m",          // default 30m (1h for Anthropic OAuth)
    target: "last",        // "last" | "none" | channel target
    showOk: false,         // deliver HEARTBEAT_OK acknowledgments (default: false)
    showAlerts: true,      // deliver alert messages (default: true)
    useIndicator: true,    // emit UI status events (default: true)
  }
}
```

### How It Works
- Agent receives: "Read HEARTBEAT.md if it exists, flag anything needing attention"
- If nothing urgent → agent responds with `HEARTBEAT_OK` → message suppressed (if content ≤ 300 chars)
- If alert content (no `HEARTBEAT_OK`) → delivered externally
- `HEARTBEAT_OK` mid-message = treated as regular text (not a signal)

### HEARTBEAT.md
Optional workspace checklist file guides the agent's focus. Skipped if file contains only headers/whitespace.

**Cost note:** Each heartbeat consumes a full model turn. Use `target: "none"` for internal-only updates with no delivery cost.

---

## Local Models

### Setup (LM Studio + MiniMax M2.1 — Recommended)
```json5
{
  agents: {
    defaults: {
      model: {
        primary: "lmstudio/minimax-m2-1",
        fallbacks: ["anthropic/claude-sonnet-4-6"]
      }
    }
  },
  models: {
    providers: {
      lmstudio: {
        baseUrl: "http://127.0.0.1:1234",
        contextWindow: 196608,
        maxTokens: 8192
      }
    }
  }
}
```

### Hardware Reality
- ≥ 24GB GPU: lighter workloads with latency trade-offs
- ≥ 2 maxed Mac Studios (~$30k+): near-cloud quality
- Recommended: hosted primary + local fallback for reliability

### Security Warning
Local setups skip provider-side content filters — more vulnerable to prompt injection. Keep agents narrowly scoped and use aggressive context compaction.

---

## Multiple Gateways

### When You Need This
- Isolation between personal and work agents
- Rescue bot while primary is broken
- Testing new config without disrupting production

### Using Profiles (Recommended)
```bash
openclaw --profile main gateway --port 18789
openclaw --profile rescue gateway --port 19001
```
Profiles auto-scope config files and state directories — cleaner than manual env vars.

### Manual Isolation (if not using profiles)
Must isolate all of:
- `OPENCLAW_CONFIG_PATH` — config file
- `OPENCLAW_STATE_DIR` — state/sessions directory
- `agents.defaults.workspace` — workspace root
- `gateway.port` — base port

### Port Spacing
Keep **≥ 20 ports** between base ports. Each gateway derives:
- `base + 2` — browser control port
- `base + 9` through `base + 108` — Chrome CDP ports

Overlapping ranges = port conflicts.

---

## Tailscale Integration

### Modes
| Mode | Description |
|------|-------------|
| `serve` | Gateway on loopback; Tailscale handles HTTPS routing within tailnet |
| `funnel` | Exposes gateway publicly over HTTPS (requires Tailscale v1.38.3+) |
| `off` | Disables Tailscale automation |

### Config
```json5
{
  gateway: {
    tailscale: {
      mode: "serve",         // "serve" | "funnel" | "off"
    },
    auth: {
      allowTailscale: true   // authenticate via Tailscale identity headers
    }
  }
}
```

### How Auth Works
With `allowTailscale: true`, OpenClaw verifies identity by resolving the `x-forwarded-for` address via `tailscale whois`. No token/password needed for dashboard — but **HTTP API endpoints still require token auth**.

### Funnel Constraints
- Requires Tailscale v1.38.3+
- Only supports ports 443, 8443, and 10000
- Serve needs HTTPS enabled on your tailnet

### Security Note
Only safe if no untrusted local code can run on the same machine. If it can, disable `allowTailscale` and enforce credential-based auth.

---

## Sandbox vs Tool Policy vs Elevated

Three distinct, layered controls:

| Control | What It Controls | Config Key |
|---------|-----------------|------------|
| **Sandbox** | *Where* exec runs (Docker vs host) | `agents.defaults.sandbox.mode` |
| **Tool policy** | *Which* tools the model can call | `tools.allow` / `tools.deny` |
| **Elevated** | Escape hatch: run exec on host when sandboxed | `/elevated on|ask|full` |

### Sandbox Modes
| Mode | Behavior |
|------|----------|
| `off` | No sandboxing — exec runs on gateway host |
| `non-main` | Sandbox all sessions except `main` |
| `all` | Always sandbox |

### Key Rules
- `deny always wins` in tool policy — no combination of other config can re-grant a denied tool
- Elevated does **not** grant additional tools — only changes where exec runs
- `/elevated full` = gateway host + skip approvals (`security=full`)
- Mounting `/var/run/docker.sock` in sandbox = container has host control (intentional only)
- `openclaw sandbox explain` — inspect effective config across modes/scopes/agents

### Quick Audit
```bash
openclaw sandbox explain
openclaw agents list --bindings
docker ps --filter "name=openclaw-sbx-"
```

---

## OpenAI-Compatible Chat Completions API

Gateway exposes an OpenAI-compatible endpoint for use with any OpenAI SDK or tool.

**Disabled by default.** Enable:
```json5
{ gateway: { http: { endpoints: { chatCompletions: { enabled: true } } } } }
```

### Endpoint
```
POST /v1/chat/completions
Authorization: Bearer <gateway-token>
```

### Usage
```bash
# Non-streaming
curl http://localhost:18789/v1/chat/completions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"openclaw:main","messages":[{"role":"user","content":"Hello"}]}'

# Streaming
curl ... -d '{"model":"openclaw:main","stream":true,"messages":[...]}'
```

### Agent Targeting
- `model` field: `openclaw:<agentId>` (e.g. `openclaw:researcher`)
- Or header: `x-openclaw-agent-id: researcher`

### Session Handling
- Default: stateless (new session per request)
- Include OpenAI `user` field → stable session shared across repeated calls

---

## Trusted Proxy Auth

Delegates identity verification to a reverse proxy (Pomerium, Caddy, nginx+oauth2-proxy, Traefik).

### Config
```json5
{
  gateway: {
    auth: {
      trustedProxies: ["10.0.0.1"],   // proxy IP(s) — MUST be locked down at firewall
      userHeader: "x-forwarded-user", // header containing verified user identity
      allowUsers: ["alice", "bob"],   // optional allowlist
    }
  }
}
```

### Requirements
- Gateway must have **no bypass path** around the proxy — enforce with firewall rules (only proxy IP can reach gateway port)
- Proxy must forward WebSocket upgrades with correct headers
- Start with short HSTS max-age while validating traffic flow

### Common Errors
| Error | Fix |
|-------|-----|
| Untrusted source IP | Verify proxy IP in `trustedProxies` |
| Missing user header | Confirm proxy is passing identity header |
| WebSocket failures | Ensure proxy supports WS upgrade + header forwarding |

---

## Configuration Examples

### Minimal
```json5
{
  agent: { workspace: "~/.openclaw/workspace" },
  channels: { whatsapp: { allowFrom: ["+15551234567"] } }
}
```

### Recommended Starter
```json5
{
  agents: {
    defaults: {
      model: { primary: "zai/glm-4-plus", fallbacks: ["anthropic/claude-sonnet-4-6"] }
    }
  },
  channels: { telegram: { token: "$TG_TOKEN", allowFrom: ["@myhandle"] } }
}
```

### Secure Multi-User DMs (prevent context leakage)
```json5
{
  session: { dmScope: "per-channel-peer" },
  channels: { whatsapp: { dmPolicy: "pairing" } }
}
```

### OAuth + API Key Fallback
```json5
{
  agents: {
    defaults: {
      model: {
        primary: "anthropic/claude-sonnet-4-6",
        fallbacks: ["zai/glm-4-plus"]
      }
    }
  },
  models: {
    providers: {
      anthropic: { auth: [{ type: "oauth" }, { type: "apiKey", key: "$ANTHROPIC_KEY" }] }
    }
  }
}
```

### Local Models Only
```json5
{
  agents: { defaults: { model: { primary: "ollama/llama3.2" } } },
  models: { providers: { ollama: { baseUrl: "http://127.0.0.1:11434" } } }
}
```

### Restricted Work Bot
```json5
{
  channels: {
    slack: { allowFrom: ["@team-channel"], requireMention: true }
  },
  agents: {
    defaults: {
      sandbox: { mode: "all", scope: "agent" },
      tools: { deny: ["exec", "browser", "write", "edit"] }
    }
  }
}
```
