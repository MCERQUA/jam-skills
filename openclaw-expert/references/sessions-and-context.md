# OpenClaw: Sessions & Context Reference

---

## SESSION MANAGEMENT

### Session Key Structure
- **Main DM session**: `agent:<agentId>:main`
- **Group/channel session**: `agent:<agentId>:<channel>:group:<id>`
- **Sub-agent session**: `agent:<agentId>:subagent:<uuid>`
- **Cron/hook sessions**: separate keys by type

### DM Scoping (`dmScope`)
Controls how DM conversations are grouped:

| `dmScope` Value | Behavior |
|-----------------|----------|
| `main` | All DMs share one session (default, single-user) |
| `per-peer` | One session per sender across all channels |
| `per-channel-peer` | One session per sender per channel (multi-user inbox) |
| `per-account-channel-peer` | One session per sender per channel per account |

- `identityLinks` maps provider-prefixed peer IDs to canonical identities (cross-channel sharing)
- **Secure DM mode**: use `per-channel-peer` for multi-user setups to prevent context leakage

### Session Storage (Files)
- **Session map**: `~/.openclaw/agents/<agentId>/sessions/sessions.json`
  - Maps `sessionKey → {sessionId, updatedAt, ...}`
- **Transcripts**: `~/.openclaw/agents/<agentId>/sessions/<SessionId>.jsonl`
  - Telegram topics: append `-topic-<threadId>` to filename

### Reset Policy
```json
{
  "reset": {
    "mode": "daily",        // "daily" | "idle"
    "atHour": 4,            // for daily: 4 AM local on gateway host
    "idleMinutes": 60       // for idle: sliding window
  }
}
```
- Both `daily` + `idleMinutes` can be set; whichever fires first wins
- Evaluated on **next inbound message** (not real-time)
- Manual reset: `/new` or `/reset` commands
- Per-type overrides via `resetByType`:
```json
{
  "resetByType": {
    "thread": { "mode": "daily", "atHour": 4 },
    "direct": { "mode": "idle", "idleMinutes": 240 },
    "group":  { "mode": "idle", "idleMinutes": 120 }
  }
}
```
- Per-channel overrides via `resetByChannel`

### Session Maintenance
```json
{
  "maintenance": {
    "mode": "warn",           // "warn" | "enforce"
    "pruneAfter": "30d",
    "maxEntries": 500,
    "rotateBytes": "10mb"
  }
}
```

---

## CONTEXT WINDOW

### What the Model Sees (per request)
- System prompt (all sections, fixed per run)
- Conversation history (from JSONL transcript)
- Tool calls + tool results
- Attachments (images, audio, files)
- Compaction summaries and pruning artifacts
- Provider-injected headers/wrappers

### System Prompt Components
- Tool list + short descriptions
- Skills list (metadata only — skill instructions NOT included by default)
- Workspace location
- Time (UTC + user time if configured)
- Runtime metadata (host/OS/model/thinking level)
- **Project Context**: injected workspace bootstrap files

### Injected Workspace Bootstrap Files (Project Context)
Loaded at session start; large files truncated per `bootstrapMaxChars` (default 20,000 chars):
- `AGENTS.md`
- `SOUL.md`
- `TOOLS.md`
- `IDENTITY.md`
- `USER.md`
- `HEARTBEAT.md`
- `BOOTSTRAP.md` (first-run only)
- `memory/YYYY-MM-DD.md` (today + yesterday)
- `MEMORY.md` (optional; main session only)

### Skills Context Cost
- Compact skills list (name + description + location) always in system prompt
- Full `SKILL.md` loaded on demand only when model needs to invoke the skill

### Tools Context Cost (Two Components)
1. **Tool list text** in system prompt
2. **Tool schemas** (JSON) sent to provider — count toward context even if invisible in UI

---

## TOKEN ACCOUNTING

### Inspect Commands
| Command | What It Shows |
|---------|---------------|
| `/status` | Quick context fill percentage + compaction count (`🧹 Compactions: N`) |
| `/context list` | What's injected + rough sizes per section |
| `/context detail` | Deep breakdown: per-file, per-tool, per-skill sizes |
| `/usage tokens` | Appends per-reply token usage footer |

---

## COMPACTION

### What It Does
- **Summarizes** older conversation turns into a compact summary entry
- Keeps recent messages intact
- **Persists** in session JSONL history (permanent, unlike pruning)
- Triggered when session nears or exceeds model's context window

### Auto-Compaction
- Enabled by default
- OpenClaw triggers automatically when context window nearing full
- May retry original request using compacted context
- Shows `🧹 Auto-compaction complete` (verbose mode)
- Track count via `/status` → `🧹 Compactions: <N>`

### Manual Compaction
```
/compact
/compact <optional instructions>
```

### Compaction Config
```json
{
  "compaction": {
    "mode": "safeguard",         // "default" | "safeguard" (chunked summarization)
    "reserveTokensFloor": 24000,
    "memoryFlush": {
      "enabled": true,
      "softThresholdTokens": 6000,
      "systemPrompt": "Session nearing compaction. Store durable memories now.",
      "prompt": "Write any lasting notes to memory/YYYY-MM-DD.md; reply with NO_REPLY if nothing to store."
    }
  }
}
```

### Pre-Compaction Memory Flush
- Silent agentic turn runs **before** auto-compaction
- Reminds model to write durable notes to disk before history is summarized
- Only runs when workspace is writable (`workspaceAccess` ≠ `"ro"` or `"none"`)
- Reply `NO_REPLY` → user never sees this turn
- Flush triggers when session tokens cross: `contextWindow - reserveTokensFloor - softThresholdTokens`
- One flush per compaction cycle (tracked in `sessions.json`)

---

## CONTEXT PRUNING

### What It Does
- Trims **old tool results** from in-memory context right before LLM calls
- Does **NOT** rewrite on-disk session history (`*.jsonl`) — transcript unchanged
- Only affects the prompt sent to the model for that one request

### Pruning Modes
| Mode | Behavior |
|------|----------|
| `off` | No pruning (default for some profiles) |
| `cache-ttl` | Prune when TTL since last provider call has elapsed |

### When Pruning Runs (`cache-ttl` mode)
- Only triggers when last provider API call is older than `ttl`
- After prune, TTL window resets
- Match `ttl` to model's `cacheControlTtl` for best cache efficiency

### What Can (and Can't) Be Pruned
- ✅ **Can prune**: `toolResult` messages
- ❌ **Never pruned**: user messages, assistant messages, tool results with image blocks
- ❌ **Protected**: last `keepLastAssistants` assistant messages

### Pruning Operations
| Operation | When | Effect |
|-----------|------|--------|
| **Soft-trim** | Tool result > `softTrimRatio` of context | Keeps head + tail, inserts `...`, appends original size note |
| **Hard-clear** | Tool result > `hardClearRatio` of context | Replaces entire result with placeholder text |

### Pruning Config
```json
{
  "contextPruning": {
    "mode": "cache-ttl",
    "ttl": "1h",
    "keepLastAssistants": 3,
    "softTrimRatio": 0.3,
    "hardClearRatio": 0.5,
    "minPrunableToolChars": 50000,
    "softTrim": {
      "maxChars": 4000,
      "headChars": 1500,
      "tailChars": 1500
    },
    "hardClear": {
      "enabled": true,
      "placeholder": "[Old tool result content cleared]"
    },
    "tools": {
      "allow": [],
      "deny": ["browser", "canvas"]
    }
  }
}
```

### Tool Filter Rules
- `tools.allow` / `tools.deny` support `*` wildcards
- **Deny wins** over allow
- Matching is case-insensitive
- Empty `allow` list = all tools allowed (pruned by size rules)

### Smart Defaults by Profile Type
| Profile Type | Pruning Mode | TTL | `cacheControlTtl` |
|-------------|-------------|-----|-------------------|
| OAuth/setup-token | `cache-ttl` | `1h` heartbeat | — |
| API key | `cache-ttl` | `30m` heartbeat | `1h` |

---

## COMPACTION vs PRUNING (Quick Reference)

| Aspect | Compaction | Pruning |
|--------|-----------|---------|
| **What** | Summarizes full conversation | Trims tool results only |
| **Persists to disk** | Yes — JSONL updated | No — in-memory only |
| **Trigger** | Context window nearing full | TTL elapsed since last provider call |
| **Impact** | Reduces future + current token usage | Reduces current request size only |
| **Manual** | `/compact` command | Not manually triggered |
| **Scope** | Whole session history | Only tool result messages |

---

## SESSION PERSISTENCE (JSONL Files)

### File Layout
```
~/.openclaw/agents/<agentId>/
  sessions/
    sessions.json          # key → {sessionId, updatedAt, model, contextTokens, ...}
    <SessionId>.jsonl      # append-only transcript of all turns
    <SessionId>-topic-<threadId>.jsonl  # Telegram topics
```

### JSONL Entry Types
- User messages, assistant messages
- `toolCall` + `toolResult` pairs
- Compaction summary entries (persisted)
- Pruning does NOT write to JSONL

### Session Metadata in `sessions.json`
Row fields include: `key`, `kind`, `channel`, `displayName`, `updatedAt`, `sessionId`, `model`, `contextTokens`, `totalTokens`, `thinkingLevel`, `verboseLevel`, `systemSent`, `abortedLastRun`, `sendPolicy`, `lastChannel`, `lastTo`, `deliveryContext`, `transcriptPath`

---

## INSPECT: /status & /context

### `/status`
Quick snapshot of current session:
- Context window fill percentage
- `🧹 Compactions: <N>` (how many times compaction has run)
- Model in use, thinking level

### `/context list`
- Lists all injected sections + rough token/char sizes
- Shows which workspace files are loaded under Project Context

### `/context detail`
- Deep breakdown: per-file sizes, per-tool schema sizes, per-skill sizes
- Use when diagnosing why context window is filling fast

### `/usage tokens`
- Appends input/output token counts to each reply
- Useful for monitoring token burn rate

---

## MULTI-SESSION PATTERNS

### Agent-to-Agent Communication
```json
{
  "agentToAgent": {
    "maxPingPongTurns": 5   // 0–5; alternating turns between sessions
  }
}
```
- Agent calls `sessions_send` → target runs → reply comes back
- Reply `REPLY_SKIP` to stop ping-pong early
- Announce step: runs after loop, target posts result to requester's chat channel
- Reply `ANNOUNCE_SKIP` to stay silent on announce

### Sub-Agent Sessions (`sessions_spawn`)
- Creates isolated `agent:<agentId>:subagent:<uuid>` session
- `deliver: false` — results not sent to chat unless announced
- Sub-agents default to full tool set **minus session tools** (no spawning sub-sub-agents)
- Always non-blocking → returns `{status: "accepted", runId, childSessionKey}`
- Auto-archived after `subagents.archiveAfterMinutes` (default 60 min)

### Send Policy (Security)
```json
{
  "sendPolicy": {
    "rules": [
      { "action": "deny",  "match": { "channel": "discord", "chatType": "group" } },
      { "action": "allow", "match": { "keyPrefix": "trusted-" } }
    ],
    "default": "allow"
  }
}
```
- Deny wins over allow
- Runtime override: `sendPolicy: "allow" | "deny"` per session
- Owner command: `/send on|off|inherit`

### Sandbox Session Visibility
```json
{ "sandbox": { "sessionToolsVisibility": "spawned" } }  // "spawned" | "all"
```

---

## MEMORY SYSTEM (Context Persistence)

### Memory File Types
| File | Loaded When | Purpose |
|------|------------|---------|
| `memory/YYYY-MM-DD.md` | Today + yesterday at session start | Daily append-only log |
| `MEMORY.md` | Main session only | Curated long-term memory |

### When Model Should Write Memory
- Decisions, preferences, durable facts → `MEMORY.md`
- Day-to-day notes, running context → `memory/YYYY-MM-DD.md`
- Anything that shouldn't be lost to compaction → write to disk

### Memory Search (`memory_search` tool)
- Semantic search over memory chunks (~400 token target, 80-token overlap)
- Hybrid: BM25 (exact tokens) + vector (semantic) search
- Default backend: remote embeddings (OpenAI/Gemini/Voyage)
- Local backend: `node-llama-cpp` (requires `pnpm approve-builds`)
- QMD backend (experimental): `memory.backend = "qmd"` — local BM25 + vector + reranking

---

## FULL CONTEXT LIFECYCLE (Summary)

```
Inbound message arrives
  ↓
Check reset policy (daily/idle) → reset session if expired
  ↓
Build context: system prompt + JSONL history + tool schemas
  ↓
[If cache-ttl pruning enabled AND TTL elapsed]
  → Trim oversized tool results in-memory (JSONL unchanged)
  ↓
[If context nearing window limit]
  → Pre-compaction memory flush (silent agentic turn → write to disk)
  → Auto-compaction (summarize → persist summary to JSONL)
  ↓
Send context to model
  ↓
Model responds → tool calls → tool results → append to JSONL
  ↓
Session persists until next reset trigger
```
