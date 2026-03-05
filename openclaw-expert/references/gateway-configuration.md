# OpenClaw Gateway Configuration Reference

## Config File & Editing

- **Location**: `~/.openclaw/openclaw.json` · Format: JSON5 (comments + trailing commas OK)
- **If missing**: Safe defaults used · **Validation**: Strict — bad keys/types prevent startup
- **On failure**: Only `openclaw doctor/logs/health/status` work

| Edit Method | How |
|-------------|-----|
| Wizard | `openclaw onboard` · `openclaw configure` |
| CLI | `openclaw config get/set/unset <key>` |
| Control UI | http://127.0.0.1:18789 → Config tab |
| Direct | Edit file — hot-reloads automatically |

Repair: `openclaw doctor` · `openclaw doctor --fix`

---

## Hot Reload

```json5
{ gateway: { reload: { mode: "hybrid", debounceMs: 300 } } }
```

| Mode | Behavior |
|------|----------|
| `hybrid` (default) | Hot-applies safe changes; auto-restarts for critical ones |
| `hot` | Hot-applies only; warns when restart needed |
| `restart` | Restarts on any change |
| `off` | Manual restart required |

- **Needs restart**: `gateway.*` (port/bind/auth/TLS), `discovery`, `canvasHost`, `plugins`
- **Hot-applies**: channels, agents, tools, session, hooks, cron, skills, ui, logging, bindings

---

## Minimal Configs

```json5
// Absolute minimum
{ agent: { workspace: "~/.openclaw/workspace" }, channels: { whatsapp: { allowFrom: ["+15555550123"] } } }
```

```json5
// Recommended starter
{
  identity: { name: "Clawd", theme: "helpful assistant", emoji: "🦞" },
  agent: { workspace: "~/.openclaw/workspace", model: { primary: "anthropic/claude-sonnet-4-5" } },
  channels: { whatsapp: { allowFrom: ["+15555550123"], groups: { "*": { requireMention: true } } } },
}
```

---

## `agents`

### `agents.defaults` Key Fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `workspace` | string | `~/.openclaw/workspace` | Agent working dir |
| `skipBootstrap` | bool | false | Skip AGENTS.md/SOUL.md/etc. creation |
| `bootstrapMaxChars` | int | 20000 | Max chars per bootstrap file |
| `userTimezone` | string | host TZ | System prompt timezone |
| `timeFormat` | `auto\|12\|24` | `auto` | — |
| `thinkingDefault` | string | — | `low\|high\|off` |
| `timeoutSeconds` | int | 600 | LLM request timeout |
| `mediaMaxMb` | int | 5 | Max inbound media size |
| `maxConcurrent` | int | 1 | Max parallel agent runs |
| `blockStreamingDefault` | `on\|off` | `off` | Block reply mode |

### Model Config

```json5
{
  agents: {
    defaults: {
      models: {
        "anthropic/claude-opus-4-6": { alias: "opus" },
        "openai/gpt-5.2": { alias: "gpt" },
      },
      model: { primary: "anthropic/claude-opus-4-6", fallbacks: ["openai/gpt-5.2"] },
      imageModel: { primary: "openrouter/qwen/qwen-2.5-vl-72b-instruct:free" },
    },
  },
}
```

Built-in aliases (only if in `agents.defaults.models`): `opus` · `sonnet` · `gpt` · `gpt-mini` · `gemini` · `gemini-flash`
> Z.AI GLM-4.x auto-enables thinking unless `--thinking off` or `params.thinking` is set.

### Heartbeat

```json5
{
  agents: { defaults: { heartbeat: {
    every: "30m",      // 0m disables
    model: "openai/gpt-5.2-mini",
    target: "last",    // last | whatsapp | telegram | discord | none
    to: "+15555550123",
    prompt: "Read HEARTBEAT.md if it exists...",
    ackMaxChars: 300,
  } } },
}
```

### Compaction & Context Pruning

```json5
{
  agents: { defaults: {
    compaction: {
      mode: "safeguard",  // default | safeguard
      reserveTokensFloor: 24000,
      memoryFlush: { enabled: true, softThresholdTokens: 6000 },
    },
    contextPruning: {
      mode: "cache-ttl",  // off | cache-ttl
      ttl: "1h",
      keepLastAssistants: 3,
      softTrimRatio: 0.3, hardClearRatio: 0.5,
      minPrunableToolChars: 50000,
      softTrim: { maxChars: 4000, headChars: 1500, tailChars: 1500 },
      hardClear: { enabled: true, placeholder: "[Old tool result content cleared]" },
      tools: { deny: ["browser", "canvas"] },
    },
  } },
}
```

### Sandbox

```json5
{
  agents: { defaults: { sandbox: {
    mode: "non-main",        // off | non-main | all
    scope: "agent",          // session | agent | shared
    workspaceAccess: "none", // none | ro | rw
    workspaceRoot: "~/.openclaw/sandboxes",
    docker: {
      image: "openclaw-sandbox:bookworm-slim", network: "none",
      readOnlyRoot: true, tmpfs: ["/tmp"], user: "1000:1000",
      capDrop: ["ALL"], memory: "1g", cpus: 1, pidsLimit: 256,
      setupCommand: "apt-get update && apt-get install -y git curl jq",
    },
    browser: { enabled: false },
    prune: { idleHours: 24, maxAgeDays: 7 },
  } } },
}
```

Build images: `scripts/sandbox-setup.sh` · `scripts/sandbox-browser-setup.sh`

### `agents.list` (Per-Agent Overrides)

```json5
{
  agents: { list: [{
    id: "main", default: true, workspace: "~/.openclaw/workspace",
    model: "anthropic/claude-opus-4-6",  // or { primary, fallbacks }
    identity: { name: "Samantha", theme: "helpful sloth", emoji: "🦥" },
    groupChat: { mentionPatterns: ["@openclaw", "openclaw"] },
    sandbox: { mode: "off" }, subagents: { allowAgents: ["*"] },
    tools: { profile: "coding", allow: ["browser"], deny: ["canvas"] },
    heartbeat: { every: "30m" },
  }] },
}
```

---

## `channels`

### DM & Group Policies

| DM Policy | Behavior |
|-----------|----------|
| `pairing` (default) | Unknown senders get one-time pairing code |
| `allowlist` | Only senders in `allowFrom` |
| `open` | All DMs (requires `allowFrom: ["*"]`) |
| `disabled` | Ignore all DMs |

| Group Policy | Behavior |
|--------------|----------|
| `allowlist` (default) | Only groups matching allowlist |
| `open` | Bypass allowlists (mention-gating still applies) |
| `disabled` | Block all group messages |

### Channel Configs

```json5
// WhatsApp
{ channels: { whatsapp: {
  dmPolicy: "pairing", allowFrom: ["+15555550123"],
  textChunkLimit: 4000, mediaMaxMb: 50, sendReadReceipts: true,
  groups: { "*": { requireMention: true } },
  groupPolicy: "allowlist", groupAllowFrom: ["+15551234567"],
} } }

// Telegram
{ channels: { telegram: {
  enabled: true, botToken: "your-bot-token",
  dmPolicy: "pairing", allowFrom: ["tg:123456789"],
  groups: { "*": { requireMention: true },
    "-1001234567890": { allowFrom: ["@admin"], topics: { "99": { requireMention: false } } } },
  streamMode: "partial",  // off | partial | block
  replyToMode: "first",   // off | first | all
  historyLimit: 50, proxy: "socks5://localhost:9050",
} } }

// Discord
{ channels: { discord: {
  enabled: true, token: "your-bot-token",
  dm: { enabled: true, policy: "pairing", allowFrom: ["username"] },
  guilds: { "123456789012345678": { requireMention: false,
    channels: { general: { allow: true }, help: { allow: true, requireMention: true } } } },
  historyLimit: 20, textChunkLimit: 2000, maxLinesPerMessage: 17, allowBots: false,
  actions: { reactions: true, stickers: true, polls: true, threads: true, moderation: false },
} } }

// Slack
{ channels: { slack: {
  enabled: true, botToken: "xoxb-...", appToken: "xapp-...",
  dm: { enabled: true, policy: "pairing", allowFrom: ["U123"] },
  channels: { "#general": { allow: true, requireMention: true } },
  historyLimit: 50, thread: { historyScope: "thread" },
  slashCommand: { enabled: true, name: "openclaw", ephemeral: true },
  reactionNotifications: "own",  // off | own | all | allowlist
} } }

// Multi-account — use bindings[].match.accountId to route to different agents
{ channels: { telegram: { accounts: {
  default: { name: "Primary bot", botToken: "123456:ABC..." },
  alerts:  { name: "Alerts bot",  botToken: "987654:XYZ..." },
} } } }
```

---

## `session`

```json5
{ session: {
  dmScope: "per-channel-peer",  // main | per-peer | per-channel-peer | per-account-channel-peer
  identityLinks: { alice: ["telegram:123456789", "discord:987654321012345678"] },
  reset: { mode: "daily", atHour: 4, idleMinutes: 60 },  // daily | idle
  resetByType: {
    thread: { mode: "daily", atHour: 4 },
    direct: { mode: "idle", idleMinutes: 240 },
    group:  { mode: "idle", idleMinutes: 120 },
  },
  resetTriggers: ["/new", "/reset"],
  maintenance: { mode: "warn", pruneAfter: "30d", maxEntries: 500, rotateBytes: "10mb" },
  sendPolicy: {
    rules: [{ action: "deny", match: { channel: "discord", chatType: "group" } }],
    default: "allow",
  },
} }
```

---

## `tools`

### Profiles & Groups

| Profile | Includes |
|---------|----------|
| `minimal` | `session_status` only |
| `coding` | `group:fs` + `group:runtime` + `group:sessions` + `group:memory` + `image` |
| `messaging` | `group:messaging` + sessions tools |
| `full` | No restriction |

| Group | Tools |
|-------|-------|
| `group:fs` | `read`, `write`, `edit`, `apply_patch` |
| `group:runtime` | `exec`, `process` |
| `group:sessions` | `sessions_list`, `sessions_history`, `sessions_send`, `sessions_spawn`, `session_status` |
| `group:web` | `web_search`, `web_fetch` |
| `group:ui` | `browser`, `canvas` |
| `group:automation` | `cron`, `gateway` |
| `group:memory` | `memory_search`, `memory_get` |

```json5
{
  tools: {
    profile: "coding",
    allow: ["exec", "read", "write", "edit"], deny: ["browser", "canvas"],
    elevated: { enabled: true, allowFrom: { whatsapp: ["+15555550123"], discord: ["username"] } },
    exec: { backgroundMs: 10000, timeoutSec: 1800, notifyOnExit: true },
    web: {
      search: { enabled: true, apiKey: "brave_api_key", maxResults: 5, cacheTtlMinutes: 15 },
      fetch:  { enabled: true, maxChars: 50000, timeoutSeconds: 30 },
    },
    media: {
      audio: { enabled: true, maxBytes: 20971520, models: [{ provider: "openai", model: "gpt-4o-mini-transcribe" }] },
      video: { enabled: true, maxBytes: 52428800, models: [{ provider: "google", model: "gemini-3-flash-preview" }] },
    },
    agentToAgent: { enabled: false, allow: ["home", "work"] },
    // Provider-specific tool restrictions (can only narrow, not expand)
    byProvider: {
      "google-antigravity": { profile: "minimal" },
      "openai/gpt-5.2": { allow: ["group:fs", "sessions_list"] },
    },
    // Safe additive (avoids restrictive allowlist mode)
    alsoAllow: ["lobster", "llm-task"],
    // Loop detection (default: disabled)
    loopDetection: {
      enabled: true, warningThreshold: 10, criticalThreshold: 20,
      globalCircuitBreakerThreshold: 30, historySize: 30,
      detectors: { genericRepeat: true, knownPollNoProgress: true, pingPong: true },
    },
    // Session visibility for session tools
    sessions: { visibility: "tree" },  // tree | self
    // Subagent tool config
    subagents: { tools: { deny: ["browser"], /* allow: [...] */ } },
    // sessions_spawn attachments config
    sessions_spawn: { attachments: { enabled: true, maxTotalBytes: 10485760, maxFiles: 10, maxFileBytes: 5242880 } },
  },
}
```

### ACP Config (Agent Client Protocol)

```json5
{
  acp: {
    enabled: true,
    dispatch: { enabled: true },
    backend: "acpx",
    defaultAgent: "codex",
    allowedAgents: ["pi", "claude", "codex", "opencode", "gemini", "kimi"],
    maxConcurrentSessions: 8,
    stream: { coalesceIdleMs: 300, maxChunkChars: 1200 },
    runtime: { ttlMinutes: 120 },
  },
}
```

See `acp-agents.md` for full ACP reference.

---

## `session` (Thread Bindings)

```json5
{
  session: {
    threadBindings: {
      enabled: true,
      idleHours: 24,
      maxAgeHours: 0,   // 0 = no max age
    },
  },
}
```

### Channel Model Overrides

```json5
{
  channels: {
    modelByChannel: {
      discord: { "123456789012345678": "anthropic/claude-opus-4-6" },
      slack: { "C1234567890": "openai/gpt-4.1" },
      telegram: { "-1001234567890": "openai/gpt-4.1-mini" },
    },
  },
}
```

---

## `skills`

```json5
{ skills: {
  allowBundled: ["gemini", "peekaboo"],
  load: { extraDirs: ["~/Projects/agent-scripts/skills"] },
  install: { preferBrew: true, nodeManager: "npm" },
  entries: {
    "nano-banana-pro": { enabled: true, apiKey: "GEMINI_KEY_HERE", env: { GEMINI_API_KEY: "GEMINI_KEY_HERE" } },
    peekaboo: { enabled: true }, sag: { enabled: false },
  },
} }
```

## `cron`

```json5
{ cron: { enabled: true, maxConcurrentRuns: 2, sessionRetention: "24h" } }
```

## `hooks`

```json5
{
  hooks: {
    enabled: true, token: "shared-secret", path: "/hooks",
    maxBodyBytes: 262144, allowedAgentIds: ["hooks", "main"],
    presets: ["gmail"], transformsDir: "~/.openclaw/hooks",
    mappings: [{
      match: { path: "gmail" }, action: "agent", agentId: "hooks",
      wakeMode: "now", name: "Gmail",
      sessionKey: "hook:gmail:{{messages[0].id}}",
      messageTemplate: "From: {{messages[0].from}}\nSubject: {{messages[0].subject}}",
      deliver: true, channel: "last", model: "openai/gpt-5.2-mini",
    }],
  },
}
```

- **Auth**: `Authorization: Bearer <token>` or `x-openclaw-token: <token>`
- **Endpoints**: `POST /hooks/wake` · `POST /hooks/agent` · `POST /hooks/<name>`

## `gateway`

```json5
{
  gateway: {
    mode: "local",    // local | remote
    port: 18789,      // precedence: --port > OPENCLAW_GATEWAY_PORT > config > 18789
    bind: "loopback", // auto | loopback | lan | tailnet | custom
    auth: { mode: "token", token: "your-token", allowTailscale: true },
    tailscale: { mode: "off" },  // off | serve | funnel
    controlUi: { enabled: true, basePath: "/openclaw" },
    remote: { url: "ws://gateway.tailnet:18789", transport: "ssh", token: "your-token" },
    reload: { mode: "hybrid", debounceMs: 300 },
    trustedProxies: ["10.0.0.1"],
    // HTTP API endpoints
    http: {
      endpoints: {
        responses: { enabled: false },  // OpenResponses API (/v1/responses)
        chat: { enabled: false },       // Chat Completions API (/v1/chat/completions)
      },
    },
    // HTTP tool invoke deny/allow overrides
    tools: {
      deny: ["sessions_spawn", "sessions_send", "gateway", "whatsapp_login"],  // default deny
      allow: [],  // remove from default deny
    },
  },
}
```

See `http-apis.md` for full OpenResponses / Tools Invoke / Chat Completions API reference.

```bash
# Multi-instance
OPENCLAW_CONFIG_PATH=~/.openclaw/a.json OPENCLAW_STATE_DIR=~/.openclaw-a openclaw gateway --port 19001
openclaw gateway --dev              # ~/.openclaw-dev + port 19001
openclaw gateway --profile myname   # ~/.openclaw-myname
```

## `models` (Custom Providers)

```json5
{
  models: {
    mode: "merge",  // merge | replace
    providers: {
      "custom-proxy": {
        baseUrl: "http://localhost:4000/v1", apiKey: "LITELLM_KEY",
        api: "openai-completions",  // openai-completions | openai-responses | anthropic-messages | google-generative-ai
        models: [{ id: "llama-3.1-8b", name: "Llama 3.1 8B", reasoning: false, input: ["text"],
                   cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 128000, maxTokens: 32000 }],
      },
    },
  },
}
```

```json5
// Z.AI — set ZAI_API_KEY
{ agents: { defaults: { model: { primary: "zai/glm-4.7" }, models: { "zai/glm-4.7": {} } } } }

// LM Studio (local)
{ models: { mode: "merge", providers: { lmstudio: {
  baseUrl: "http://127.0.0.1:1234/v1", apiKey: "lmstudio", api: "openai-responses",
  models: [{ id: "minimax-m2.1-gs32", name: "MiniMax M2.1 GS32", reasoning: false, input: ["text"],
             cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 196608, maxTokens: 8192 }],
} } }, agent: { model: { primary: "lmstudio/minimax-m2.1-gs32" } } }
```

## `messages`

```json5
{ messages: {
  responsePrefix: "🦞",  // "auto" → [{identity.name}]; vars: {model} {modelFull} {provider} {thinkingLevel}
  ackReaction: "👀",
  ackReactionScope: "group-mentions",  // group-mentions | group-all | direct | all
  removeAckAfterReply: false,
  queue: { mode: "collect", debounceMs: 1000, cap: 20, drop: "summarize" },
  inbound: { debounceMs: 2000, byChannel: { whatsapp: 5000, slack: 1500 } },
  tts: { auto: "always",  // off | always | inbound | tagged
    provider: "elevenlabs",
    elevenlabs: { apiKey: "key", voiceId: "id", modelId: "eleven_multilingual_v2",
                  voiceSettings: { stability: 0.5, similarityBoost: 0.75, speed: 1.0 } },
  },
} }
```

## `env` & Substitution

```json5
{ env: { OPENROUTER_API_KEY: "sk-or-...", vars: { GROQ_API_KEY: "gsk-..." }, shellEnv: { enabled: true, timeoutMs: 15000 } } }
```

- Neither `.env` (CWD or `~/.openclaw/.env`) overrides existing env vars
- Substitution in config values: `"${VAR_NAME}"` (uppercase only; missing = load-time error; escape: `$${VAR}`)

## `logging`

```json5
{ logging: { level: "info", file: "/tmp/openclaw/openclaw.log", consoleStyle: "pretty", redactSensitive: "tools" } }
```

---

## Multi-Agent Routing

```json5
{
  agents: { list: [
    { id: "home", default: true, workspace: "~/.openclaw/workspace-home" },
    { id: "work", workspace: "~/.openclaw/workspace-work" },
  ] },
  bindings: [
    { agentId: "home", match: { channel: "whatsapp", accountId: "personal" } },
    { agentId: "work", match: { channel: "whatsapp", accountId: "biz" } },
  ],
}
```

**Precedence**: `match.peer` → `match.guildId` → `match.teamId` → `match.accountId` (exact) → `match.accountId: "*"` → default

```json5
// Read-only access profile (inside agents.list[])
{ sandbox: { mode: "all", workspaceAccess: "ro" }, tools: { allow: ["read", "sessions_list", "session_status"], deny: ["write", "exec", "browser"] } }
// Messaging-only
{ sandbox: { mode: "all", workspaceAccess: "none" }, tools: { allow: ["sessions_list", "whatsapp", "telegram"], deny: ["read", "write", "exec", "browser", "canvas"] } }
```

---

## Config Includes · Config RPC

```json5
// $include splits config across files
{ gateway: { port: 18789 }, agents: { $include: "./agents.json5" }, broadcast: { $include: ["./a.json5", "./b.json5"] } }
```
- Single file: replaces object · Array: deep-merged (later wins) · Max depth: 10

```bash
# Config RPC
openclaw gateway call config.get --params '{}'
openclaw gateway call config.apply --params '{ "raw": "{ agents: { defaults: { workspace: \"~/.openclaw/workspace\" } } }", "baseHash": "<hash>" }'
openclaw gateway call config.patch --params '{ "raw": "{ channels: { telegram: { groups: { \"*\": { requireMention: false } } } } }", "baseHash": "<hash>" }'
```

---

## Key CLI Commands

```bash
openclaw onboard                               # Full setup wizard
openclaw configure                             # Config wizard
openclaw config get agents.defaults.workspace
openclaw config set agents.defaults.heartbeat.every "2h"
openclaw config unset tools.web.search.apiKey
openclaw doctor                                # Diagnose config issues
openclaw doctor --fix                          # Auto-repair config issues
openclaw dns setup --apply                     # Setup DNS-SD discovery
```
