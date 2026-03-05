# OpenClaw Agent Runtime Reference

> Source: agent.md, agent-loop.md, agent-workspace.md, context.md, system-prompt.md, session.md, session-pruning.md, compaction.md, memory.md, models.md, queue.md, streaming.md, multi-agent.md, tools/index.md

---

## Agent Lifecycle (ordered)

1. **Workspace resolution** — `agents.defaults.workspace` (default `~/.openclaw/workspace`). Sandboxed sessions redirect to `agents.defaults.sandbox.workspaceRoot`.
2. **Session resolution** — `agent RPC` validates params, resolves sessionKey/sessionId, persists session metadata, returns `{ runId, acceptedAt }` immediately.
3. **Model selection** — in priority order:
   - `agents.defaults.model.primary` (or `agents.defaults.model`)
   - `agents.defaults.model.fallbacks` (in order)
   - Provider auth failover inside a provider before moving to next model
4. **Skills snapshot** — loads skills from workspace > managed (`~/.openclaw/skills`) > bundled.
5. **Session write lock acquired** — `SessionManager` opened and prepared.
6. **System prompt build** — assembled from base prompt + skills prompt + bootstrap context + per-run overrides. Model-specific limits and compaction reserve tokens enforced.
7. **Bootstrap injection** — workspace files injected into system prompt under **Project Context** (first turn of session). Large files truncated at `bootstrapMaxChars` (default 20000 chars).
8. **Attempt (embedded pi-agent run)** — `runEmbeddedPiAgent` serializes via per-session + global queues, enforces timeout, streams lifecycle/assistant/tool events.
9. **Tool execution loop** — tool start/update/end events emitted on `tool` stream. Steer-mode injects queued user messages after each tool boundary.
10. **Reply shaping** — assembles: assistant text + optional reasoning + inline tool summaries. `NO_REPLY` filtered. Messaging tool duplicates removed.
11. **Completion** — `chat.final` emitted on lifecycle `end/error`. Session transcript written as JSONL.

---

## Workspace Layout

| File | Purpose | Loaded |
|------|---------|--------|
| `AGENTS.md` | Operating instructions, rules, priorities, memory guidance | Every session |
| `SOUL.md` | Persona, tone, boundaries | Every session |
| `USER.md` | Who the user is, how to address them | Every session |
| `IDENTITY.md` | Agent name, vibe, emoji | Every session |
| `TOOLS.md` | Notes on local tools and conventions (guidance only, not access control) | Every session |
| `HEARTBEAT.md` | Short checklist for heartbeat runs (keep tiny) | Every session |
| `BOOT.md` | Startup checklist on gateway restart (internal hooks required) | On restart |
| `BOOTSTRAP.md` | One-time first-run ritual. Delete after completion. | First run only |
| `MEMORY.md` | Curated long-term memory (load in main/private sessions only) | Injected when present |
| `memory/YYYY-MM-DD.md` | Daily log. On-demand via `memory_search`/`memory_get` | NOT auto-injected |
| `skills/` | Workspace-specific skills (override managed/bundled on name conflict) | On demand |
| `canvas/` | Canvas UI files | On demand |

**What is NOT in workspace** (lives under `~/.openclaw/`):
- `openclaw.json` (config)
- `credentials/` (OAuth tokens, API keys)
- `agents/<agentId>/sessions/` (session transcripts)
- `skills/` (managed skills)

**Config location:**
```json5
{
  agent: {
    workspace: "~/.openclaw/workspace",
    skipBootstrap: true  // disable bootstrap file creation for pre-seeded workspaces
  }
}
```

---

## Bootstrap Injection

- Injected on **first turn** of a new session into system prompt under **Project Context**
- Files injected: `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `IDENTITY.md`, `USER.md`, `HEARTBEAT.md`, `BOOTSTRAP.md` (brand-new only), `MEMORY.md`/`memory.md` (when present)
- **Sub-agent sessions**: only inject `AGENTS.md` and `TOOLS.md`
- Missing file → injects short "missing file" marker
- Blank file → skipped
- Large file → truncated with marker (per-file limit: `agents.defaults.bootstrapMaxChars`, default 20000)
- Hook point: `agent:bootstrap` (internal hook) to mutate/replace injected files before finalization
- Plugin hook: `before_agent_start` to inject context or override system prompt

**Inspect what's injected:**
```
/context list    — per-file raw vs injected sizes, truncation status
/context detail  — adds per-tool schema sizes, top skills entry sizes
/status          — quick context window usage + session settings
```

---

## System Prompt Structure

Sections (in order):
- **Tooling** — current tool list + short descriptions
- **Safety** — guardrail reminder (advisory, not enforced)
- **Skills** — compact list with file paths; model reads SKILL.md on demand
- **OpenClaw Self-Update** — how to run `config.apply` and `update.run`
- **Workspace** — working directory path
- **Documentation** — local docs path + public mirror
- **Workspace Files** — indicates bootstrap files follow
- **Sandbox** — (when enabled) sandbox paths and elevated exec availability
- **Current Date & Time** — timezone only (no dynamic clock, for cache stability)
- **Reply Tags** — optional syntax for supported providers
- **Heartbeats** — heartbeat prompt and ack behavior
- **Runtime** — host, OS, node, model, repo root, thinking level

**Prompt modes:**
| Mode | Used for | Omits |
|------|----------|-------|
| `full` | Default | — |
| `minimal` | Sub-agents | Skills, Memory Recall, Self-Update, Model Aliases, User Identity, Reply Tags, Messaging, Heartbeats |
| `none` | Base identity only | Everything |

---

## Built-in Tools

### Core (filesystem + runtime)
| Tool | Description |
|------|-------------|
| `read` | Read files |
| `write` | Write files |
| `edit` | Edit files |
| `apply_patch` | Multi-hunk patches (gated by `tools.exec.applyPatch.enabled`, OpenAI only) |
| `exec` | Shell commands in workspace. Params: `command`, `yieldMs`, `background`, `timeout`, `elevated`, `host`, `security`, `ask`, `pty` |
| `process` | Manage background exec sessions. Actions: `list`, `poll`, `log`, `write`, `kill`, `clear`, `remove` |

### Web
| Tool | Description |
|------|-------------|
| `web_search` | Brave Search API (requires `BRAVE_API_KEY`, `tools.web.search.enabled`) |
| `web_fetch` | HTML → markdown/text fetch. `maxChars` capped by `tools.web.fetch.maxCharsCap` (default 50000) |

### UI / Automation
| Tool | Description |
|------|-------------|
| `browser` | Managed browser. Actions: `status`, `start`, `stop`, `tabs`, `open`, `snapshot`, `screenshot`, `act`, `navigate`, `console`, `pdf`, `upload`, `dialog`, `profiles`, `create-profile`, `delete-profile` |
| `canvas` | Node Canvas. Actions: `present`, `hide`, `navigate`, `eval`, `snapshot`, `a2ui_push`, `a2ui_reset` |
| `nodes` | Paired node control. Actions: `status`, `describe`, `notify`, `run`, `camera_snap`, `camera_clip`, `screen_record`, `location_get` |
| `cron` | Gateway cron jobs. Actions: `status`, `list`, `add`, `update`, `remove`, `run`, `runs`, `wake` |
| `gateway` | Restart/update gateway. Actions: `restart`, `config.get`, `config.schema`, `config.apply`, `config.patch`, `update.run` |

### Sessions / Memory
| Tool | Description |
|------|-------------|
| `sessions_list` | List sessions. Params: `kinds?`, `limit?`, `activeMinutes?`, `messageLimit?` |
| `sessions_history` | Session transcript. Params: `sessionKey/sessionId`, `limit?`, `includeTools?` |
| `sessions_send` | Send to another session. Params: `sessionKey/sessionId`, `message`, `timeoutSeconds?` |
| `sessions_spawn` | Start sub-agent run (non-blocking). Params: `task`, `label?`, `agentId?`, `model?`, `runTimeoutSeconds?`, `cleanup?` |
| `session_status` | Status of session (default current). Params: `sessionKey?`, `model?` |
| `agents_list` | List agent IDs valid for `sessions_spawn` |
| `memory_search` | Semantic search over MEMORY.md + memory/*.md |
| `memory_get` | Read specific memory file by path |
| `image` | Analyze image with image model |
| `message` | Send/manage messages across Discord/Slack/Telegram/WhatsApp/Signal/iMessage/Teams |

### Tool Groups (for allow/deny policy)
| Group | Expands to |
|-------|-----------|
| `group:runtime` | `exec`, `bash`, `process` |
| `group:fs` | `read`, `write`, `edit`, `apply_patch` |
| `group:sessions` | `sessions_list`, `sessions_history`, `sessions_send`, `sessions_spawn`, `session_status` |
| `group:memory` | `memory_search`, `memory_get` |
| `group:web` | `web_search`, `web_fetch` |
| `group:ui` | `browser`, `canvas` |
| `group:automation` | `cron`, `gateway` |
| `group:messaging` | `message` |
| `group:nodes` | `nodes` |
| `group:openclaw` | All built-in OpenClaw tools |

### Tool Profiles
- `minimal` — `session_status` only
- `coding` — `group:fs`, `group:runtime`, `group:sessions`, `group:memory`, `image`
- `messaging` — `group:messaging`, `sessions_list`, `sessions_history`, `sessions_send`, `session_status`
- `full` — no restriction (default)

```json5
{ tools: { profile: "coding", allow: ["browser"], deny: ["group:runtime"],
    byProvider: { "google-antigravity": { profile: "minimal" } } } }
```

---

## Steering While Streaming (Queue Modes)

| Mode | Behavior |
|------|---------|
| `steer` | Inject inbound message into current run after next tool boundary; remaining tool calls skipped with error "Skipped due to queued user message." Falls back to `followup` if not streaming. |
| `followup` | Hold until current turn ends, then new agent turn with queued payloads |
| `collect` | Coalesce all queued into **single** followup turn (default) |
| `steer-backlog` | Steer now AND preserve for followup turn (can look like duplicate responses) |
| `interrupt` | Abort active run, run newest message (legacy) |

**Queue options** (apply to `followup`, `collect`, `steer-backlog`):
- `debounceMs` — wait for quiet before followup (default 1000)
- `cap` — max queued messages per session (default 20)
- `drop` — overflow policy: `old`, `new`, `summarize` (default `summarize`)

**Config:**
```json5
{
  messages: {
    queue: {
      mode: "collect",
      debounceMs: 1000,
      cap: 20,
      drop: "summarize",
      byChannel: { discord: "collect" }
    }
  }
}
```

**Per-session override (chat command):**
```
/queue collect
/queue steer debounce:2s cap:25 drop:summarize
/queue default    ← clear override
```

**Troubleshooting:** If commands stuck, enable verbose logs, look for "queued for …ms" lines.

---

## Session Management

**Session key formats:**
| Type | Key format |
|------|-----------|
| DM (main) | `agent:<agentId>:<mainKey>` |
| DM per-peer | `agent:<agentId>:dm:<peerId>` |
| DM per-channel-peer | `agent:<agentId>:<channel>:dm:<peerId>` |
| Group | `agent:<agentId>:<channel>:group:<id>` |
| Cron | `cron:<job.id>` |
| Webhook | `hook:<uuid>` |

**dmScope options:** `main` (default), `per-peer`, `per-channel-peer`, `per-account-channel-peer`

⚠️ **Security:** Use `dmScope: "per-channel-peer"` for multi-user setups — otherwise all DMs share context.

**Session files:**
- Store: `~/.openclaw/agents/<agentId>/sessions/sessions.json`
- Transcripts: `~/.openclaw/agents/<agentId>/sessions/<SessionId>.jsonl`

**Session reset config:**
```json5
{ session: {
    dmScope: "per-channel-peer",
    reset: { mode: "daily", atHour: 4, idleMinutes: 120 }, // whichever expires first
    resetByType: {
      thread: { mode: "daily", atHour: 4 },
      direct: { mode: "idle", idleMinutes: 240 },
      group:  { mode: "idle", idleMinutes: 120 }
    },
    resetByChannel: { discord: { mode: "idle", idleMinutes: 10080 } },
    mainKey: "main"
} }
```

**Manual reset triggers:** `/new`, `/reset` (or add extras in `resetTriggers`). **CLI inspection:**
```bash
openclaw status
openclaw sessions --json
openclaw sessions --active 60
openclaw gateway call sessions.list --params '{}'
```

**Chat commands:**
```
/status            — context window usage, thinking/verbose toggles
/context list      — injected files + sizes
/context detail    — per-tool schema sizes, per-skill sizes
/stop              — abort current run + clear queued followups
/compact           — manual compaction (optional instructions)
/new               — fresh session (resets sessionId)
/send on|off|inherit — override send policy for session
```

---

## Context Window & Compaction

**Compaction** — summarizes older conversation, persists in JSONL. Triggered when session nears context window limit.
- Auto: default on. Emits `🧹 Auto-compaction complete` in verbose mode.
- Manual: `/compact [optional instructions]`
- Pre-compaction **memory flush**: silent agentic turn that writes durable memory before context is compacted.

**Session pruning** — trims OLD TOOL RESULTS from in-memory context before LLM call. Does NOT rewrite JSONL.
- Only runs for Anthropic API calls (and OpenRouter Anthropic models)
- Only affects `toolResult` messages (user + assistant messages never modified)
- Protected: last `keepLastAssistants` (default 3) assistant messages + tool results after that cutoff

**Pruning defaults:** `ttl=5m`, `keepLastAssistants=3`, `softTrimRatio=0.3`, `hardClearRatio=0.5`, `minPrunableToolChars=50000`, `softTrim.maxChars=4000`

**Enable TTL-aware pruning:**
```json5
{
  agent: {
    contextPruning: {
      mode: "cache-ttl",
      ttl: "5m",
      tools: { allow: ["exec", "read"], deny: ["*image*"] }
    }
  }
}
```

**Memory flush config** (defaults shown, runs silently before compaction):
```json5
{ agents: { defaults: { compaction: { reserveTokensFloor: 20000,
    memoryFlush: { enabled: true, softThresholdTokens: 4000,
      prompt: "Write any lasting notes to memory/YYYY-MM-DD.md; reply with NO_REPLY if nothing to store." }
} } } }
```

---

## Model Selection

**Selection order:**
1. `agents.defaults.model.primary`
2. `agents.defaults.model.fallbacks` (in order)
3. Provider auth failover

**Model ref format:** `provider/model` (split on first `/`)
- OpenRouter: `openrouter/moonshotai/kimi-k2`
- Z.AI: `zai/glm-4.7-flash` (alias `z.ai/*` normalizes to `zai/*`)

**CLI commands:**
```bash
openclaw models list [--all] [--provider <name>] [--plain] [--json]
openclaw models status [--check]
openclaw models set <provider/model>
openclaw models set-image <provider/model>
openclaw models aliases list
openclaw models aliases add <alias> <provider/model>
openclaw models aliases remove <alias>
openclaw models fallbacks list
openclaw models fallbacks add <provider/model>
openclaw models fallbacks remove <provider/model>
openclaw models fallbacks clear
```

**Chat model switching:**
```
/model            — numbered picker
/model 3          — select by number
/model openai/gpt-5.2
/model status
```

**Allowlist config** (if set, model must be in list or replies stop):
```json5
{ agent: { model: { primary: "anthropic/claude-sonnet-4-5" },
    models: { "anthropic/claude-sonnet-4-5": { alias: "Sonnet" },
              "anthropic/claude-opus-4-6":   { alias: "Opus" } } } }
```

**Timeouts:**
- `agent.wait` default: 30s (wait only; `timeoutMs` overrides)
- Agent runtime: `agents.defaults.timeoutSeconds` default 600s

---

## Block Streaming

**Off by default** (`agents.defaults.blockStreamingDefault: "off"`). Non-Telegram channels need explicit `*.blockStreaming: true`.

| Config | Default | Description |
|--------|---------|-------------|
| `blockStreamingDefault` | `"off"` | Global on/off |
| `blockStreamingBreak` | `"text_end"` | `text_end` = emit as buffer grows; `message_end` = flush at end |
| `blockStreamingChunk` | 800–1200 chars | Min/max bounds + break preference |
| `blockStreamingCoalesce` | idle-based | Merge consecutive chunks before send (default minChars 1500 for Signal/Slack/Discord) |
| `humanDelay` | `off` | Randomized pause between blocks: `natural` (800–2500ms), `custom` (`minMs`/`maxMs`) |

**Telegram only:** draft streaming with `channels.telegram.streamMode: "partial" | "block" | "off"`.

---

## Multi-Agent Routing

Each agent is isolated with its own: workspace, `agentDir`, sessions, auth profiles.

**Default:** single agent, `agentId = "main"`.

**Binding priority (most-specific wins):**
1. `peer` match (exact DM/group/channel id)
2. `guildId` (Discord)
3. `teamId` (Slack)
4. `accountId` match for a channel
5. Channel-level match (`accountId: "*"`)
6. Default agent

**CLI:**
```bash
openclaw agents add work
openclaw agents list --bindings
```

**Two-agent example (two WhatsApp accounts):**
```json5
{
  agents: { list: [
    { id: "home", default: true, workspace: "~/.openclaw/workspace-home" },
    { id: "work",                workspace: "~/.openclaw/workspace-work" }
  ]},
  bindings: [
    { agentId: "home", match: { channel: "whatsapp", accountId: "personal" } },
    { agentId: "work", match: { channel: "whatsapp", accountId: "biz" } }
  ],
  // Agent-to-agent messaging — off by default
  tools: { agentToAgent: { enabled: false, allow: ["home", "work"] } }
}
```

---

## Hook Points

### Internal (Gateway) Hooks
| Hook | When |
|------|------|
| `agent:bootstrap` | While building bootstrap files, before system prompt finalized |
| `/new`, `/reset`, `/stop` | Command events |

### Plugin Hooks (agent lifecycle)
| Hook | When |
|------|------|
| `before_agent_start` | Inject context / override system prompt |
| `agent_end` | Inspect final message list + run metadata |
| `before_compaction` / `after_compaction` | Observe/annotate compaction |
| `before_tool_call` / `after_tool_call` | Intercept tool params/results |
| `tool_result_persist` | Transform tool results before JSONL write |
| `message_received` / `message_sending` / `message_sent` | Inbound + outbound |
| `session_start` / `session_end` | Session lifecycle |
| `gateway_start` / `gateway_stop` | Gateway lifecycle |

---

## Memory System

**Two layers:**
- `MEMORY.md` — curated long-term facts. Injected into context every session. Keep concise (grows → compaction).
- `memory/YYYY-MM-DD.md` — daily logs. NOT auto-injected. Accessed via `memory_search`/`memory_get` only.

**When to write:**
- Decisions, preferences, durable facts → `MEMORY.md`
- Day-to-day notes → `memory/YYYY-MM-DD.md`

**Vector search (default: enabled):**
- Provider auto-selection: local → openai → gemini → voyage → disabled
- Hybrid search (BM25 + vector) by default
- Index: `~/.openclaw/memory/<agentId>.sqlite`

**Disable memory plugin:** `{ plugins: { slots: { memory: "none" } } }`

**QMD backend** (experimental, local-first BM25+vector+reranking):
```json5
{ memory: { backend: "qmd", citations: "auto",
    qmd: { includeDefaultMemory: true, update: { interval: "5m" },
           limits: { maxResults: 6, timeoutMs: 4000 } } } }
```

---

## Gateway / Workspace CLI

```bash
openclaw setup                  # create openclaw.json + seed workspace
openclaw onboard                # full setup wizard
openclaw configure --section web
openclaw doctor                 # warns on extra workspace dirs
openclaw status
openclaw sessions --json
openclaw models status
# Workspace backup (private git repo)
cd ~/.openclaw/workspace && git init
git add AGENTS.md SOUL.md TOOLS.md IDENTITY.md USER.md HEARTBEAT.md memory/
git commit -m "Add agent workspace"
gh repo create openclaw-workspace --private --source . --remote origin --push
```

---

## Minimal Config (`~/.openclaw/openclaw.json`)

```json5
{
  agent: {
    workspace: "~/.openclaw/workspace",
    model: { primary: "zai/glm-4.7-flash" },
    timeoutSeconds: 600,
    bootstrapMaxChars: 20000,
    blockStreamingDefault: "off",
    contextPruning: { mode: "cache-ttl", ttl: "30m" }
  },
  session: {
    dmScope: "main",
    reset: { mode: "daily", atHour: 4 }
  },
  messages: {
    queue: { mode: "collect", debounceMs: 1000, cap: 20, drop: "summarize" }
  },
  channels: {
    whatsapp: { allowFrom: ["+1xxxxxxxxxx"] }
  }
}
```
