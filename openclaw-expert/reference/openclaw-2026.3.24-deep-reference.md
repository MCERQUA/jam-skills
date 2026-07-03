---
name: openclaw-expert
description: Comprehensive expert guide to OpenClaw 2026.3.24 architecture, configuration, skills, gateway, memory, sessions, channels, tools, providers, and all platform internals. Use for teaching, debugging, and building on OpenClaw.
metadata: {"openclaw": {"emoji": "🧠"}}
---

# OpenClaw Expert

**OpenClaw Version:** 2026.3.24
**Last Updated:** 2026-04-15

## What is OpenClaw

OpenClaw is a **self-hosted multi-channel AI gateway** that connects chat apps to coding agents. A single Gateway daemon (Node ≥ 22) manages all channels, sessions, routing, and agent runtime.

**Core components:**
- **Gateway daemon** — WS server on `127.0.0.1:18789` (default), owns all channel connections, sessions, and routing
- **Pi agent** — embedded coding agent in RPC mode with streaming LLM + tool execution. **Pi is the ONLY coding agent path** (Claude/Codex/Gemini/Opencode have been removed)
- **Skills** — Markdown-defined agent plugins (workspace / managed / bundled), published to ClawHub
- **Memory** — `MEMORY.md` (long-term) + `memory/YYYY-MM-DD.md` (daily logs) + optional QMD hybrid search
- **Canvas host** — served at `http://127.0.0.1:18793/__openclaw__/canvas/` and `/a2ui/` (same port as gateway)
- **Nodes** — macOS/iOS/Android devices for canvas, camera, screen recording, location

**Built-in channels:** WhatsApp (Baileys Web), Telegram (grammY), Discord, Slack, Signal, iMessage/BlueBubbles, WebChat
**Plugin channels (extensions):** Mattermost, Matrix, MS Teams, Google Chat, IRC, Nostr, LINE, Twitch, Zalo, Feishu, Synology Chat, Nextcloud Talk, Tlon — install via `openclaw plugins install`

**Config file:** `~/.openclaw/openclaw.json` (JSON5)
**Workspace:** `~/.openclaw/workspace/` (or `~/.openclaw/workspace-<agentId>` for multi-agent)
**State dir:** `~/.openclaw/` (or `OPENCLAW_STATE_DIR`)

## Architecture Mental Model

```
Chat apps (WhatsApp / Telegram / Discord / Slack / Signal / iMessage / WebChat...)
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│                    GATEWAY (Node daemon)                    │
│  Channels ─ Sessions ─ Agent Runtime ─ Skills ─ Tools      │
│  Memory / Workspace (bootstrap files injected each turn)    │
│  Canvas host at /__openclaw__/canvas/ and /a2ui/           │
└──────────────────────────────────────────────────────────────┘
        │
   ┌────┴────┬─────────────┬──────────────┐
   ▼         ▼             ▼              ▼
  CLI      Nodes         Canvas        HTTP APIs
(openclaw) (iOS/macOS/  (port 18793)  /v1/responses
           Android)                   /tools/invoke
                                     /v1/chat/completions
```

**Message flow:** Channel inbound → access control (allowFrom / dmPolicy / mention gate) → session key resolved → bootstrap files injected → agent runtime → LLM (streaming) → tool execution → response chunks → channel outbound.

**Key insight — sessions = prompt cache warmth:**
- Persistent session key (e.g., `agent:main:main`) = warm Z.AI/GLM prompt cache → 3-8s response
- New session key = cold cache → 15-30s first response
- Session key format: `agent:<agentId>:<scope>` (e.g., `agent:main:telegram:dm:123456`)
- Use `GATEWAY_SESSION_KEY=main` env var to always use the main session across all connections
- **Compaction** summarizes old conversation history; **session pruning** trims old tool results in-memory
- **Pre-compaction memory flush** silently prompts the model to write durable notes before compaction

**Key insight — bootstrap files:**
- Every new session turn injects workspace root `.md` files into context
- Only these files belong in workspace root: `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `IDENTITY.md`, `USER.md`, `MEMORY.md`, `AGENT.md`, `BOOTSTRAP.md`
- Keep bootstrap total under ~50K chars; use `docs/` subdirectory for non-essential docs

## Quick Reference — All Docs

| Topic | Official Doc Path |
|-------|------------------|
| Architecture & components | `docs/concepts/architecture.md` |
| Gateway WS protocol & handshake | `docs/gateway/protocol.md` |
| Full config schema (`openclaw.json`) | `docs/gateway/configuration-reference.md` |
| Task-oriented config guide | `docs/gateway/configuration.md` |
| Gateway runbook (5-min startup) | `docs/gateway/index.md` |
| Heartbeat, local models, multiple gateways | `docs/gateway/heartbeat.md`, `docs/gateway/local-models.md`, `docs/gateway/multiple-gateways.md` |
| Trusted proxy auth | `docs/gateway/trusted-proxy-auth.md` |
| OpenAI-compatible HTTP API | `docs/gateway/openai-http-api.md` |
| OpenResponses API (`/v1/responses`) | `docs/gateway/openresponses-http-api.md` |
| Tools Invoke API (`/tools/invoke`) | `docs/gateway/tools-invoke-http-api.md` |
| Agent runtime, bootstrap, workspace | `docs/concepts/agent.md`, `docs/concepts/agent-workspace.md` |
| Sessions, dmScope, maintenance, reset | `docs/concepts/session.md` |
| Compaction (auto + manual + identifier policies) | `docs/concepts/compaction.md` |
| Session pruning (replaces contextPruning) | `docs/concepts/session-pruning.md` |
| Memory files, QMD backend, hybrid search, MMR, temporal decay | `docs/concepts/memory.md` |
| System prompt assembly | `docs/concepts/system-prompt.md` |
| Skills format, gating, ClawHub CLI | `docs/tools/skills.md` |
| Creating skills | `docs/tools/creating-skills.md` |
| ClawHub CLI | `docs/tools/clawhub.md` |
| Models, providers list, auth, fallbacks | `docs/providers/index.md` |
| Z.AI provider (GLM models) | `docs/providers/zai.md` |
| MiniMax provider | `docs/providers/minimax.md` |
| Per-channel setup | `docs/channels/` (per-channel files) |
| Tools: exec, process, browser, elevated, llm-task, lobster, subagents | `docs/tools/` (many files) |
| Web tools: web_search, web_fetch | `docs/tools/web.md` |
| Firecrawl scraping | `docs/tools/firecrawl.md` |
| ACP agents (Pi only) | `docs/concepts/acp-agents.md` |
| Plugins/extensions | `docs/tools/plugin.md` |
| Cron jobs, heartbeat, webhooks, hooks | `docs/automation/` |
| Auth monitoring, cron vs heartbeat | `docs/automation/auth-monitoring.md`, `docs/automation/cron-vs-heartbeat.md` |
| Security model, sandboxing | `docs/gateway/security/`, `docs/gateway/sandboxing.md` |
| Secrets management | `docs/gateway/secrets.md`, `docs/gateway/secrets-plan-contract.md` |
| CLI reference | `docs/cli/` (run `openclaw --help`) |
| Multi-agent routing, isolation | `docs/concepts/multi-agent.md` |
| Canvas, nodes, voice wake | `docs/nodes/index.md` |
| Troubleshooting | `docs/gateway/troubleshooting.md` |

## Sessions — Complete Reference

**Session key format:** `agent:<agentId>:<scope>`

| Scope Type | Key Format | When Used |
|------------|------------|-----------|
| Direct (main) | `agent:<agentId>:main` | All DMs share one session (default) |
| Direct (per-peer) | `agent:<agentId>:dm:<peerId>` | DMs isolated by sender |
| Direct (per-channel-peer) | `agent:<agentId>:<channel>:dm:<peerId>` | DMs isolated by channel+sender |
| Direct (per-account-channel-peer) | `agent:<agentId>:<channel>:<accountId>:dm:<peerId>` | Multi-account DMs |
| Group | `agent:<agentId>:<channel>:group:<id>` | Group chats |
| Thread/Topic | `agent:<agentId>:<channel>:group:<id>:topic:<threadId>` | Telegram forum topics |
| Cron | `cron:<jobId>` | Cron job sessions (always fresh) |
| Webhook | `hook:<uuid>` | Webhook-triggered sessions |
| Node | `node-<nodeId>` | Node-initiated runs |

**dmScope** — controls direct message session isolation:
```json5
{
  session: {
    dmScope: "main",                      // Default: all DMs share one session
    // dmScope: "per-peer",               // All channels: isolate by sender ID
    // dmScope: "per-channel-peer",       // Per channel+ sender (recommended multi-user)
    // dmScope: "per-account-channel-peer" // Per account+ channel+ sender
  }
}
```

**identityLinks** — map same person across channels to one session:
```json5
{
  session: {
    identityLinks: {
      "alice": ["telegram:123456789", "discord:987654321"],  // Same person
    }
  }
}
```

### Secure DM Mode (CRITICAL for multi-user)

> **WARNING:** If your agent receives DMs from multiple people, you MUST enable secure DM mode. Without it, all users share the same conversation context — Alice's private medical appointment is visible to Bob.

```json5
{
  session: {
    dmScope: "per-channel-peer",  // Isolate DMs per channel + sender
    // For multi-account: "per-account-channel-peer"
  }
}
```

### Session Maintenance (disk management)

```json5
{
  session: {
    maintenance: {
      mode: "enforce",           // "warn" (default) or "enforce"
      pruneAfter: "30d",         // Evict entries older than 30 days
      maxEntries: 500,           // Cap session store entries
      rotateBytes: "10mb",        // Rotate sessions.json when exceeded
      resetArchiveRetention: "14d", // Keep archives for 14 days
      maxDiskBytes: "1gb",       // HARD LIMIT: stop at 1GB
      highWaterBytes: "800mb",   // Start enforcing at 800MB (80% of max)
    }
  }
}
```
Run cleanup: `openclaw sessions cleanup --dry-run` / `openclaw sessions cleanup --enforce`

### Session Reset Policy

```json5
{
  session: {
    reset: {
      mode: "daily",        // "daily" or "idle" or "never"
      atHour: 4,            // Daily reset at 4 AM (gateway host local time)
      idleMinutes: 180,     // Idle timeout (whichever fires first resets)
    },
    // Per-type override
    resetByType: {
      direct: { mode: "idle", idleMinutes: 240 },
      group:  { mode: "idle", idleMinutes: 120 },
      thread: { mode: "daily", atHour: 4 },
    },
    // Per-channel override (takes precedence over resetByType)
    resetByChannel: {
      discord: { mode: "idle", idleMinutes: 10080 },  // 1 week
    },
    resetTriggers: ["/new", "/reset"],   // Manual reset commands
    mainKey: "main",                     // Key for main session
  }
}
```

### Send Policy (block delivery by rule)

```json5
{
  session: {
    sendPolicy: {
      rules: [
        { action: "deny", match: { channel: "discord", chatType: "group" } },
        { action: "deny", match: { keyPrefix: "cron:" } },
      ],
      default: "allow",
    }
  }
}
```
Runtime override: `/send on` / `/send off` / `/send inherit`

### Compaction

Compaction **summarizes older conversation** and persists to JSONL. Unlike pruning (in-memory tool result trim), compaction is durable.

```json5
{
  agents: {
    defaults: {
      compaction: {
        reserveTokens: 80000,        // Target: keep 80K tokens free
        keepRecentTokens: 8000,      // Keep last 8K tokens uncompressed
        reserveTokensFloor: 80000,  // Minimum free tokens before auto-compaction
        // identifierPolicy: "strict" (default) — preserves opaque identifiers
        // identifierPolicy: "off" or "custom"
        memoryFlush: {
          enabled: true,
          softThresholdTokens: 6000,  // Flush memories 6K before compaction
          systemPrompt: "Session nearing compaction. Store durable memories now.",
          prompt: "Write any lasting notes to memory/YYYY-MM-DD.md; reply NO_REPLY if nothing to store.",
        }
      }
    }
  }
}
```

**Manual:** `/compact [instructions]`
**Auto-compaction trigger:** When session exceeds ~124K tokens (204K context - 80K floor)
**Pre-compaction flush:** Silent memory write turn before compaction (~118K tokens)

### Session Pruning (NEW — replaces contextPruning)

> **NOTE:** `contextPruning` from older configs is deprecated. Use session pruning instead.

Session pruning trims **old tool results** from in-memory context before LLM calls. This does NOT rewrite JSONL history.

```json5
{
  agents: {
    defaults: {
      sessionPruning: {
        mode: "eager",         // "eager" (default) or "lazy"
        keepLastTools: 3,      // Keep last 3 tool results
        softTrimRatio: 0.3,    // Trim to 30% when hitting limits
        hardClearRatio: 0.5,   // Force clear at 50%
      }
    }
  }
}
```

## Memory — Complete Reference

**Memory is plain Markdown in the workspace.** Model only remembers what gets written to disk.

### Memory Files

- `memory/YYYY-MM-DD.md` — daily log, append-only. Read today + yesterday at session start.
- `MEMORY.md` — curated long-term memory. **Only loaded in main, private session (never groups).**
- `memory_search` — semantic recall over indexed snippets
- `memory_get` — targeted read of specific file/line range

### QMD Backend (experimental — local-first search)

QMD combines **BM25 full-text + vector embeddings + reranking**. Markdown stays source of truth.

```json5
{
  memory: {
    backend: "qmd",           // Default: "builtin" (SQLite vector index)
    citations: "auto",        // "auto" / "on" / "off" — cite memory sources in responses
    qmd: {
      command: "qmd",         // Override: path to qmd binary
      searchMode: "search",   // "search", "vsearch", or "query"
      includeDefaultMemory: true,
      paths: [
        { name: "docs", path: "~/notes", pattern: "**/*.md" }
      ],
      update: {
        interval: "5m",
        debounceMs: 15000,
        onBoot: true,
      },
      limits: {
        maxResults: 6,
        timeoutMs: 4000,
      },
      scope: {                // DM-only by default
        default: "deny",
        rules: [
          { action: "allow", match: { chatType: "direct" } },
        ]
      },
      sessions: {             // Index session transcripts
        enabled: false,      // Off by default
        retentionDays: 30,
      }
    }
  }
}
```

**Prereqs:** Install QMD: `bun install -g https://github.com/tobi/qmd` (or download release). Needs SQLite with extensions.

**QMD state:** `~/.openclaw/agents/<agentId>/qmd/` (XDG dirs set automatically)

### Hybrid Search (BM25 + Vector)

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        query: {
          hybrid: {
            enabled: true,
            vectorWeight: 0.7,      // 70% semantic, 30% keyword
            textWeight: 0.3,
            candidateMultiplier: 4, // Pool 4x candidates from each
            mmr: {                  // Diversity — reduce near-duplicates
              enabled: true,
              lambda: 0.7,          // 1.0 = pure relevance, 0.0 = max diversity
            },
            temporalDecay: {         // Recency boost — older notes score lower
              enabled: true,
              halfLifeDays: 30,     // Score halves every 30 days
            }
          }
        }
      }
    }
  }
}
```

**MMR (Maximal Marginal Relevance):** When `memory_search` returns similar snippets (e.g., same router config from multiple daily notes), MMR re-ranks for diversity. Lambda 0.7 = balanced.

**Temporal Decay:** Recent memories score higher. `memory/YYYY-MM-DD.md` files decay by age. `MEMORY.md` and non-dated files are **evergreen** (never decayed).

### Embedding Providers

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        provider: "gemini",        // "openai", "gemini", "voyage", "mistral", "ollama", "local", "none"
        model: "gemini-embedding-001",
        fallback: "openai",        // Fallback if primary fails
        remote: {
          apiKey: "YOUR_KEY",
          baseUrl: "https://api.example.com/v1/",  // For OpenAI-compatible endpoints
          headers: { "X-Custom": "value" },
          batch: {                 // Async batch API for large backfills
            enabled: true,
            concurrency: 2,
          }
        },
        cache: {                   // Cache embeddings in SQLite
          enabled: true,
          maxEntries: 50000,
        },
        local: {
          modelPath: "hf:ggml-org/embeddinggemma-300m-qat-q8_0-GGUF",
        }
      }
    }
  }
}
```

**Auto-provider selection (when not set):** local (if `modelPath` configured + file exists) → openai → gemini → voyage → mistral → disabled.

**SQLite vector acceleration:** Uses `sqlite-vec` extension when available. `store.vector.enabled` defaults true, `extensionPath` overrides bundled path.

## Agents — Complete Reference

### Bootstrap Files (injected every session turn)

Workspace root `.md` files injected in this order:
1. `AGENTS.md` — operating instructions + memory
2. `SOUL.md` — persona, boundaries, tone
3. `TOOLS.md` — user-maintained tool notes
4. `IDENTITY.md` — agent name/vibe/emoji
5. `USER.md` — user profile + preferred address
6. `BOOTSTRAP.md` — first-run ritual (deleted after completion)
7. `MEMORY.md` — long-term memory
8. `AGENT.md` — agent-specific config

**Workspace root rules:**
- ONLY essential bootstrap files belong in root
- Non-essential docs → `docs/` subdirectory (not injected)
- Target: <50K chars total bootstrap
- Blank files are skipped; oversized files are trimmed with a marker

### skipBootstrap

```json5
{
  agent: {
    skipBootstrap: true  // NOTE: goes on "agent" not "agents.defaults"
  }
}
```
Disables ALL bootstrap file injection. Agent starts with zero context.

### Multi-Agent

Each agent has its own isolated workspace, auth profiles, sessions, and state:

```bash
# Create new isolated agent
openclaw agents add work

# List agents with bindings
openclaw agents list --bindings
```

**Auth profiles per-agent:** `~/.openclaw/agents/<agentId>/agent/auth-profiles.json`
**Sessions:** `~/.openclaw/agents/<agentId>/sessions/`
**Workspace:** `~/.openclaw/workspace-<agentId>/` (or `agents.defaults.workspace`)

**Shared skills:** `~/.openclaw/skills/` (visible to ALL agents)
**Per-agent skills:** `<workspace>/skills/`

### Sandbox

```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main",         // "main" (default), "non-main", "all"
        scope: "session",          // "session" or "agent"
        workspaceAccess: "ro",   // "rw" (default), "ro", "none"
      }
    }
  }
}
```

`sandbox.workspaceRoot` overrides per-session workspace in sandbox mode.

## Channels — Complete Reference

### DM Policy

```json5
{
  channels: {
    <channel>: {
      dmPolicy: "pairing",    // Default: pairing code for unknown senders
      // dmPolicy: "allowlist"  // Only allowFrom list
      // dmPolicy: "open"       // Allow all (requires allowFrom: ["*"])
      // dmPolicy: "disabled"   // Ignore all DMs
      allowFrom: ["+15551234567", "123456789"],  // Phone numbers or sender IDs
    }
  }
}
```

**Pairing flow:** Unknown sender → gets one-time code → owner approves via dashboard or `openclaw pairing approve <channel> <code>`

### Group Policy

```json5
{
  channels: {
    <channel>: {
      groups: {
        "*": { requireMention: true },     // Default: mention required
        "group-id-123": { requireMention: false },  // Allow without mention
      }
    }
  }
}
```

```json5
{
  channels: {
    defaults: {
      groupPolicy: "allowlist",   // "allowlist" (default), "open", "disabled"
      heartbeat: {
        showOk: false,
        showAlerts: true,
        useIndicator: true,
      }
    }
  }
}
```

### Per-Channel Model Override

```json5
{
  channels: {
    modelByChannel: {
      discord: {
        "123456789012345678": "anthropic/claude-opus-4-6",
      },
      telegram: {
        "-1001234567890": "openai/gpt-4.1",
        "-1001234567890:topic:99": "anthropic/claude-sonnet-4-6",  // Topic-level
      }
    }
  }
}
```

### Channel List

**Built-in channels:** `whatsapp`, `telegram`, `discord`, `slack`, `signal`, `imessage` (macOS only via `imsg`), `bluebubbles`, `web`

**Plugin channels** (install via `openclaw plugins install`): `mattermost`, `matrix`, `msteams`, `googlechat`, `irc`, `nostr`, `line`, `twitch`, `zalo`, `feishu`, `synology-chat`, `nextcloud-talk`, `tlon`

## Tools — Complete Reference

### Core Tools (always available)

| Tool | Description |
|------|-------------|
| `read` | Read files |
| `write` | Write files |
| `edit` | Edit files (exact string replacement) |
| `glob` | File pattern matching |
| `grep` | Content search |
| `bash` / `exec` | Shell command execution |
| `process` | Background process management |
| `apply_patch` | Patch files (optional, gated by `tools.exec.applyPatch`) |
| `memory_search` | Semantic memory recall |
| `memory_get` | Read specific memory file |
| `llm-task` | Spawn sub-agent task |
| `subagents` | Manage sub-agents |
| `loop_detection` | Detect and prevent loops |
| `thinking` | Toggle thinking mode |
| `lobster` | Lobster tool |
| `browser` | Browser automation (Linux) |
| `agent-send` | Send to another agent session |

### Elevated Execution

For privileged operations (systemd, network changes, package installation):

```json5
{
  tools: {
    elevated: {
      enabled: true,           // Enable elevated tool
      requireApproval: true,   // Always require approval (default)
      allowWithoutApproval: false,
      approvalTimeout: "5m",  // Auto-deny after 5 min
    }
  }
}
```

Approve: `openclaw approvals get --node <id>` → `openclaw approvals approve <id>`

### Tool Profiles and Groups

```json5
{
  tools: {
    profiles: {
      readOnly: {
        allow: ["read", "glob", "grep", "memory_*"],
        deny: ["write", "edit", "bash", "exec", "process"],
      },
      coding: {
        allow: ["*"],
        deny: ["elevated"],
      }
    },
    groups: {
      safe: ["read", "glob", "grep", "memory_*", "llm-task"],
      dangerous: ["write", "edit", "bash", "exec", "process", "elevated"],
    },
    byProvider: {
      "openai/gpt-4.1": "readOnly",
    }
  }
}
```

### Web Tools

```json5
{
  tools: {
    web: {
      searchProvider: "perplexity",   // "perplexity", "brave", "gemini", "grok", "kimi"
      fetchProvider: "perplexity",    // "perplexity", "firecrawl", "brave"
      firecrawl: {
        apiKey: "YOUR_KEY",
        limit: 2,                      // Rate limit
      }
    }
  }
}
```

### exec Approvals

```json5
{
  tools: {
    exec: {
      approveNew: true,         // Auto-approve already-approved commands
      storeApproved: true,     // Store approved commands for future use
      approvalTimeout: "10m",   // Re-request approval after 10 min
    }
  }
}
```

## Skills — Complete Reference

Skills are Markdown files with YAML frontmatter that teach the agent how to use tools.

### Format

```markdown
---
name: my-skill
description: One-line description shown in skill list
metadata:
  openclaw:
    requires:
      tools: ["bash", "read"]     # Required tools
      env: ["OPENAI_API_KEY"]      # Required env vars
    rating: "★★★★☆"               # Optional quality rating
---

# My Skill

Instructions for the agent...
```

### Skill Locations (precedence high→low)

1. `<workspace>/skills/` — per-agent skills
2. `~/.openclaw/skills/` — shared across all agents on this machine
3. Bundled skills — shipped with OpenClaw install

### ClawHub CLI

```bash
# Install a skill
clawhub install <skill-slug>

# Update all installed skills
clawhub update --all

# Sync (scan + publish updates)
clawhub sync --all

# Browse available skills
# https://clawhub.com
```

## Providers — Complete Reference

### Z.AI (GLM models) — **PRIMARY for Jambot**

```json5
{
  env: { ZAI_API_KEY: "sk-..." },
  agents: { defaults: { model: { primary: "zai/glm-5" } } },
}
```

- Models: `zai/glm-5`, `zai/glm-4`, `zai/glm-3` (use subscription endpoint, NOT `open.bigmodel.cn`)
- Provider name in config: `zai` (NOT `glm`)
- Auth: Bearer token via `ZAI_API_KEY`
- `tool_stream` enabled by default for Z.AI

### MiniMax

```json5
{
  env: { MINIMAX_API_KEY: "..." },
  agents: { defaults: { model: { primary: "minimax/minimax-01" } } },
}
```

### Other Supported Providers

| Provider | Config Key | Auth |
|----------|-----------|------|
| Anthropic | `anthropic` | API key or OAuth |
| OpenAI | `openai` | API key or OAuth |
| OpenRouter | `openrouter` | API key |
| Ollama (local) | `ollama` | No key needed |
| vLLM (local) | `vllm` | No key needed |
| LiteLLM | `litellm` | API key |
| Bedrock | `bedrock` | AWS credentials |
| Together AI | `together` | API key |
| Groq | `groq` | API key (TTS only — NOT for LLM) |
| Gemini | `gemini` | API key |
| Mistral | `mistral` | API key |
| Moonshot/Kimi | `moonshot` | API key |
| Qianfan | `qianfan` | API key |
| Qwen | `qwen` | OAuth |
| Deepgram | `deepgram` | API key (transcription) |

```json5
{
  models: {
    providers: {
      <provider>: {
        apiKey: "...",
        // provider-specific options
      }
    },
    defaults: {
      primary: "zai/glm-5",
      fallback: ["minimax/minimax-01", "openai/gpt-4.1"],
    }
  }
}
```

## Automation — Complete Reference

### Cron Jobs

```bash
openclaw cron add \
  --name "daily-summary" \
  --cron "0 9 * * *" \
  --session isolated \
  --message "Morning summary" \
  --announce \
  --channel telegram \
  --to "@me"
```

### Heartbeat

Heartbeat is a periodic status message sent to channels. Use `channels.defaults.heartbeat` to configure.

> **NOTE:** For JamBot, heartbeat is **DISABLED** across all containers via `heartbeat: { every: "0m" }` in `agents.defaults`. Do NOT enable — all clients share one Z.AI API key and heartbeat cron calls eat from the same rate-limit bucket as user requests.

```json5
{
  heartbeat: {
    every: "0m",       // "0m" = disabled (JamBot standard)
    // every: "25m",   // Enable: every 25 minutes
    showOk: false,     // Include healthy status
    showAlerts: true,  // Include degraded/error status
    useIndicator: true,
  }
}
```

### Webhooks

```json5
{
  hooks: {
    wake: "/hooks/wake",      // GET when gateway starts
    agent: "/hooks/agent",    // POST after each agent turn
  }
}
```

### Auth Monitoring

Monitor authentication state changes (new logins, failures) via `docs/automation/auth-monitoring.md`.

## Troubleshooting Quick-Start

Run these in order:

```bash
openclaw status
openclaw gateway status
openclaw logs --follow
openclaw doctor
openclaw channels status --probe
openclaw sessions --json
```

**Healthy signals:**
- `gateway status` → `Runtime: running` and `RPC probe: ok`
- `doctor` → no blocking errors
- `channels status --probe` → `connected` or `ready`
- `sessions --json` → shows session keys and token counts

**Common errors:**

| Error | Fix |
|-------|-----|
| `Gateway start blocked: set gateway.mode=local` | `openclaw config set gateway.mode local` |
| `refusing to bind gateway ... without auth` | Set `gateway.auth.token` in config |
| `EADDRINUSE` / port conflict | `openclaw gateway --force` |
| `NOT_PAIRED` / `device identity required` | Auth token missing or wrong, or `dangerouslyDisableDeviceAuth` not set |
| `unauthorized` during connect | Token mismatch — check `OPENCLAW_GATEWAY_TOKEN` |
| No replies in group chat | Check `requireMention` + `openclaw pairing list <channel>` |
| Model auth failed | `openclaw models status` → re-run setup or set API key |
| Slow responses (15-30s) | Cold session — prompt cache miss. Use persistent session key. |
| `SESSION RESET` mid-conversation | Context exceeded, auto-compaction fired. Normal. |
| Empty responses / `NO_REPLY` | Compaction may have fired silently. Check `/status`. |

**Session debugging:**
- `/status` — show token count, compaction count, thinking mode
- `/context list` — show what's consuming context tokens
- `/context detail` — detailed breakdown
- `/compact` — manually trigger compaction

## ACP Agents (Pi Only)

**As of 2026.3.24: Pi is the ONLY coding agent path.** Claude, Codex, Gemini CLI, and OpenCode paths have been removed.

ACP (Agent Communication Protocol) agents run in isolated sessions. Pi is embedded in the OpenClaw gateway via `pi-mono`.

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "zai/glm-5",   // Pi uses Z.AI/GLM as its LLM backend
        // fallback: ["openai/gpt-4.1"],
      }
    }
  }
}
```

## Plugins — Complete Reference

Plugins add channels, tools, providers, or capabilities to OpenClaw.

```bash
# Install plugin
openclaw plugins install <plugin-name>

# List installed
openclaw plugins list

# Enable/disable
openclaw plugins enable <plugin-name>
openclaw plugins disable <plugin-name>
```

**Plugin structure:** `openclaw.plugin.json` in plugin root declares tools, channels, providers, and skills.

## Secrets Management

Store API keys and credentials securely:

```json5
{
  secrets: {
    apply: {
      "<target>": "<path>",   // e.g., "env:OPENAI_API_KEY": "providers:openai:apiKey"
    }
  }
}
```

See `docs/gateway/secrets.md` and `docs/gateway/secrets-plan-contract.md` for full SecretRef contract.

## Teaching Mode

When the user asks to **teach**, **explain**, or **present** OpenClaw topics:

1. Read the relevant doc(s) from the official paths above
2. Build an HTML slide deck using the `canvas` tool
3. Save to `~/.openclaw/workspace/canvas/teach-<topic>.html`
4. Present: `canvas present file:///home/mike/.openclaw/workspace/canvas/teach-<topic>.html`

```html
<!DOCTYPE html><html><head><style>
body{font-family:sans-serif;background:#111;color:#eee;padding:2rem}
h1{color:#7cf;} h2{color:#adf;} code{background:#333;padding:2px 6px;border-radius:3px}
.slide{max-width:800px;margin:0 auto}
</style></head><body><div class="slide">
<h1>Topic Title</h1>
<!-- bullet points, code blocks, tables -->
</div></body></html>
```

## Top 10 FAQ

**Q1: Why are responses slow (15-30s)?**
Cold session — Z.AI/GLM prompt cache miss. Use persistent `GATEWAY_SESSION_KEY=main` env var so all connections share the same session. First warm-up: 15-30s. Subsequent: 3-8s. Cache TTL is ~30 min idle.

**Q2: How do I add a new channel?**
Channels start automatically when their config section exists in `openclaw.json`. Install plugin channels via `openclaw plugins install <name>`. No `openclaw channels add` command needed in 2026.3.24.

**Q3: How do I create a skill?**
```bash
mkdir -p ~/.openclaw/workspace/skills/my-skill
# Create SKILL.md with frontmatter + instructions
```
See `docs/tools/creating-skills.md` and `docs/tools/skills.md`.

**Q4: How do I add a new AI model/provider?**
Set the API key env var and update `agents.defaults.model.primary`:
```json5
{ env: { ZAI_API_KEY: "sk-..." }, agents: { defaults: { model: { primary: "zai/glm-5" } } } }
```
Run `openclaw models list` to see available models.

**Q5: Bot not replying in group chat?**
1. Check `requireMention: true` in group config — bot must be @mentioned
2. Run `openclaw channels status --probe` to verify connection
3. Run `openclaw pairing list <channel>` to check pairing state
4. Check `groupPolicy: "allowlist"` isn't blocking the group

**Q6: How do sessions work? What's dmScope?**
`dmScope` controls DM session isolation. Default `"main"` = all DMs share one session (privacy risk for multi-user). Use `"per-channel-peer"` for secure multi-user isolation. Session keys determine Z.AI cache warmth. See `docs/concepts/session.md`.

**Q7: How do I run a cron job / scheduled task?**
```bash
openclaw cron add --name "daily" --cron "0 9 * * *" --session isolated \
  --message "Morning summary" --announce --channel telegram --to "@me"
```
> **JamBot note:** All clients share one Z.AI API key. Cron LLM calls eat from the same rate-limit bucket as user requests. For monitoring/watchdog tasks, use host-side scripts instead of openclaw cron.

**Q8: How do I sandbox the agent for untrusted users?**
```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main",
        scope: "session",
        workspaceAccess: "none"
      }
    }
  }
}
```
Also set `dmPolicy: "pairing"` and tool deny lists.

**Q9: Context window filling up? Slow compaction?**
- Run `/context list` to see token consumers
- Run `/compact` to manually summarize
- Session pruning trims old tool results in-memory (see `docs/concepts/session-pruning.md`)
- Compaction summarizes and persists old conversation to JSONL
- Enable `memoryFlush` to write memories before compaction fires
- For QMD/hybrid search config, see `docs/concepts/memory.md`

**Q10: How do I use the canvas / show something visually?**
Agent uses `canvas` tool: `present`, `hide`, `navigate`, `eval`, `snapshot`. Nodes (macOS/iOS/Android) must be paired via the control UI. Canvas files live at `~/.openclaw/workspace/canvas/`. For A2UI push: v0.8 format only.

## Reference File Index

| Official Doc | 1-line Description |
|-------------|-------------------|
| `docs/concepts/architecture.md` | Component diagram, message flow, ports, wire protocol |
| `docs/gateway/protocol.md` | WebSocket handshake, frame formats, RPC methods, events |
| `docs/gateway/configuration-reference.md` | Full `openclaw.json` schema — every field |
| `docs/gateway/configuration.md` | Task-oriented config guide |
| `docs/gateway/index.md` | Gateway runbook, 5-min startup |
| `docs/gateway/heartbeat.md` | Heartbeat configuration |
| `docs/gateway/local-models.md` | Ollama, vLLM local model setup |
| `docs/gateway/multiple-gateways.md` | Multiple gateway processes |
| `docs/gateway/trusted-proxy-auth.md` | trustedProxies config |
| `docs/gateway/openai-http-api.md` | OpenAI-compatible HTTP endpoint |
| `docs/gateway/openresponses-http-api.md` | /v1/responses API |
| `docs/gateway/tools-invoke-http-api.md` | /tools/invoke API |
| `docs/concepts/agent.md` | Agent runtime, bootstrap files, workspace layout |
| `docs/concepts/agent-workspace.md` | Full workspace file layout |
| `docs/concepts/session.md` | Session keys, dmScope, maintenance, reset policies |
| `docs/concepts/compaction.md` | Auto + manual compaction, identifier policies |
| `docs/concepts/session-pruning.md` | Session pruning (replaces contextPruning) |
| `docs/concepts/memory.md` | Memory files, QMD, hybrid search, MMR, temporal decay |
| `docs/concepts/system-prompt.md` | Prompt assembly order, bootstrap injection |
| `docs/tools/skills.md` | SKILL.md format, gating, precedence |
| `docs/tools/creating-skills.md` | How to create skills |
| `docs/tools/clawhub.md` | ClawHub CLI full reference |
| `docs/tools/elevated.md` | Elevated execution mode |
| `docs/tools/exec.md` | exec tool |
| `docs/tools/browser.md` | Browser automation |
| `docs/tools/web.md` | web_search + web_fetch |
| `docs/tools/llm-task.md` | llm-task sub-agent tool |
| `docs/tools/subagents.md` | Sub-agent spawning |
| `docs/tools/lobster.md` | Lobster tool |
| `docs/tools/loop-detection.md` | Loop detection |
| `docs/tools/apply-patch.md` | apply_patch tool |
| `docs/tools/agent-send.md` | agent-send tool |
| `docs/tools/plugin.md` | Plugin architecture |
| `docs/providers/index.md` | All supported providers |
| `docs/providers/zai.md` | Z.AI / GLM provider |
| `docs/providers/minimax.md` | MiniMax provider |
| `docs/channels/index.md` | Channels overview |
| `docs/channels/telegram.md` | Telegram setup |
| `docs/channels/discord.md` | Discord setup |
| `docs/channels/whatsapp.md` | WhatsApp setup |
| `docs/channels/slack.md` | Slack setup |
| `docs/channels/signal.md` | Signal setup |
| `docs/channels/imessage.md` | iMessage setup |
| `docs/automation/cron.md` | Cron jobs |
| `docs/automation/webhook.md` | Webhooks |
| `docs/automation/cron-vs-heartbeat.md` | When to use cron vs heartbeat |
| `docs/gateway/security/` | Security model |
| `docs/gateway/sandboxing.md` | Sandbox configuration |
| `docs/gateway/secrets.md` | Secrets management |
| `docs/gateway/troubleshooting.md` | Troubleshooting ladder |
| `docs/concepts/multi-agent.md` | Multi-agent routing |
| `docs/nodes/index.md` | Nodes overview |
| `docs/cli/` | CLI commands |
