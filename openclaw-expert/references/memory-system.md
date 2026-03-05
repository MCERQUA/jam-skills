# OpenClaw Memory System Reference

---

## Memory Files (Markdown on disk)

- `memory/YYYY-MM-DD.md` — Daily log, append-only. Read today + yesterday at session start.
- `MEMORY.md` — Curated long-term memory. Load in main private session only (never group contexts).
- Files live under workspace (`agents.defaults.workspace`, default `~/.openclaw/workspace`).
- Index stored at `~/.openclaw/memory/<agentId>.sqlite`

## When to Write Memory

| What | Where |
|------|-------|
| Decisions, preferences, durable facts | `MEMORY.md` |
| Day-to-day notes, running context | `memory/YYYY-MM-DD.md` |
| User says "remember this" | Write immediately — do not keep in RAM |

---

## Automatic Pre-Compaction Memory Flush

- When session nears auto-compaction → OpenClaw triggers a **silent agentic turn**
- Agent writes durable memory **before** context is compacted
- Convention: agent replies with `NO_REPLY` → user sees nothing
- Flush runs **once per compaction cycle** (tracked in `sessions.json` via `memoryFlushAt`, `memoryFlushCompactionCount`)
- Skipped if workspace is read-only (`workspaceAccess: "ro"` or `"none"`)
- Only runs for embedded Pi sessions (CLI backends skip)

### Config

```json5
{
  agents: {
    defaults: {
      compaction: {
        reserveTokensFloor: 20000,
        memoryFlush: {
          enabled: true,
          softThresholdTokens: 4000,
          systemPrompt: "Session nearing compaction. Store durable memories now.",
          prompt: "Write any lasting notes to memory/YYYY-MM-DD.md; reply with NO_REPLY if nothing to store.",
        },
      },
    },
  },
}
```

- **Soft threshold**: flush triggers when `contextWindow - reserveTokensFloor - softThresholdTokens` is crossed
- `softThresholdTokens: 4000` = fires 4000 tokens before compaction would occur

---

## Compaction vs Pruning

| | Compaction | Session Pruning |
|---|---|---|
| What | Summarizes older conversation | Trims old tool results |
| Persistence | **Persists** in JSONL transcript | **In-memory only** — does not rewrite JSONL |
| Trigger | Context overflow or threshold | Cache-TTL expiry |
| Scope | Full history summary | Tool result messages only |
| Manual | `/compact [instructions]` | N/A |

### Compaction Config

```json5
{
  compaction: {
    enabled: true,
    reserveTokens: 16384,   // headroom for output + housekeeping
    keepRecentTokens: 20000,
  },
}
```

- OpenClaw enforces a `reserveTokensFloor: 20000` minimum (set to `0` to disable)
- `/compact Focus on decisions and open questions` — manual compact with instructions

---

## Session Pruning (contextPruning)

- Trims **tool result** messages only — user/assistant messages never touched
- Only active for Anthropic API calls (and OpenRouter Anthropic models)
- Last `keepLastAssistants: 3` assistant messages are protected

### Pruning Modes

| Mode | Behavior |
|------|----------|
| `off` | Disabled (default) |
| `cache-ttl` | Runs only when last Anthropic call is older than `ttl` |

### Pruning Defaults (when enabled)

| Field | Default |
|-------|---------|
| `ttl` | `"5m"` |
| `keepLastAssistants` | `3` |
| `softTrimRatio` | `0.3` |
| `hardClearRatio` | `0.5` |
| `minPrunableToolChars` | `50000` |
| `softTrim.maxChars` | `4000` |
| `softTrim.headChars` | `1500` |
| `softTrim.tailChars` | `1500` |
| `hardClear.placeholder` | `"[Old tool result content cleared]"` |

### Config Examples

```json5
// Enable TTL-aware pruning
{
  agent: {
    contextPruning: { mode: "cache-ttl", ttl: "5m" },
  },
}
```

```json5
// Restrict to specific tools
{
  agent: {
    contextPruning: {
      mode: "cache-ttl",
      tools: { allow: ["exec", "read"], deny: ["*image*"] },
    },
  },
}
```

---

## Vector Memory Search

- Enabled by default
- Watches memory files for changes (debounced 1.5s)
- Config lives under `agents.defaults.memorySearch` (not top-level)
- Index stores embedding **provider/model + endpoint fingerprint + chunking params** — any change triggers full reindex
- Chunks: ~400 token target, 80-token overlap
- `memory_search` returns snippets (capped ~700 chars), file path, line range, score, provider/model
- `memory_get` reads specific memory file by path (workspace-relative only; rejects paths outside `MEMORY.md` / `memory/`)

### Provider Auto-Selection Order

1. `local` — if `memorySearch.local.modelPath` configured and file exists
2. `openai` — if OpenAI key resolvable
3. `gemini` — if Gemini key resolvable
4. `voyage` — if Voyage key resolvable
5. Otherwise: disabled until configured

### Key Resolution

| Provider | Env Var | Config Key |
|----------|---------|------------|
| Gemini | `GEMINI_API_KEY` | `models.providers.google.apiKey` |
| Voyage | `VOYAGE_API_KEY` | `models.providers.voyage.apiKey` |
| Custom OpenAI-compat | — | `memorySearch.remote.apiKey` |

### Embedding Provider Configs

**Gemini:**
```json5
agents: {
  defaults: {
    memorySearch: {
      provider: "gemini",
      model: "gemini-embedding-001",
      remote: { apiKey: "YOUR_GEMINI_API_KEY" }
    }
  }
}
```

**Custom OpenAI-compatible endpoint:**
```json5
agents: {
  defaults: {
    memorySearch: {
      provider: "openai",
      model: "text-embedding-3-small",
      remote: {
        baseUrl: "https://api.example.com/v1/",
        apiKey: "YOUR_REMOTE_API_KEY",
        headers: { "X-Organization": "org-id" }
      }
    }
  }
}
```

**Local (node-llama-cpp):**
```json5
agents: {
  defaults: {
    memorySearch: {
      provider: "local",
      local: { modelPath: "/path/to/model.gguf" },
      fallback: "none"
    }
  }
}
```
- Default local model: `hf:ggml-org/embeddinggemma-300M-GGUF/embeddinggemma-300M-Q8_0.gguf` (~0.6 GB)
- Requires: `pnpm approve-builds` → pick `node-llama-cpp` → `pnpm rebuild node-llama-cpp`

**Fallback:**
- `memorySearch.fallback` options: `openai`, `gemini`, `local`, `none`

---

## Hybrid Search (BM25 + Vector)

- Combines vector similarity (semantic) + BM25 keyword relevance (exact tokens)
- Falls back to vector-only if FTS5 unavailable

```json5
agents: {
  defaults: {
    memorySearch: {
      query: {
        hybrid: {
          enabled: true,
          vectorWeight: 0.7,
          textWeight: 0.3,
          candidateMultiplier: 4
        }
      }
    }
  }
}
```

- `vectorWeight` + `textWeight` normalized to 1.0
- `finalScore = vectorWeight * vectorScore + textWeight * textScore`

---

## Extra Memory Paths

```json5
agents: {
  defaults: {
    memorySearch: {
      extraPaths: ["../team-docs", "/srv/shared-notes/overview.md"]
    }
  }
}
```
- Absolute or workspace-relative paths
- Directories scanned recursively for `.md` files only
- Symlinks ignored

---

## Embedding Cache

```json5
agents: {
  defaults: {
    memorySearch: {
      cache: {
        enabled: true,
        maxEntries: 50000
      }
    }
  }
}
```

---

## Batch Indexing (OpenAI / Gemini / Voyage)

```json5
agents: {
  defaults: {
    memorySearch: {
      provider: "openai",
      model: "text-embedding-3-small",
      remote: {
        batch: { enabled: true, concurrency: 2 }
      },
      sync: { watch: true }
    }
  }
}
```
- Disabled by default. Enable for large-corpus indexing.
- `remote.batch.wait`, `remote.batch.pollIntervalMs`, `remote.batch.timeoutMinutes` — tune completion behavior
- OpenAI batch is cheapest for large backfills (Batch API pricing)

---

## Session Memory (Experimental)

```json5
agents: {
  defaults: {
    memorySearch: {
      experimental: { sessionMemory: true },
      sources: ["memory", "sessions"]
    }
  }
}
```

**Delta thresholds (when to reindex sessions):**

```json5
sync: {
  sessions: {
    deltaBytes: 100000,   // ~100 KB
    deltaMessages: 50     // JSONL lines
  }
}
```
- Session logs: `~/.openclaw/agents/<agentId>/sessions/*.jsonl`
- Indexed asynchronously; results can be slightly stale
- `memory_get` remains limited to memory files (not sessions)

---

## QMD Backend (Experimental)

- BM25 + vectors + reranking sidecar (local-first)
- Install: `bun install -g https://github.com/tobi/qmd` (binary must be on PATH)
- Requires SQLite with extension support (`brew install sqlite` on macOS)
- QMD state: `~/.openclaw/agents/<agentId>/qmd/`

```json5
memory: {
  backend: "qmd",
  citations: "auto",
  qmd: {
    includeDefaultMemory: true,
    update: { interval: "5m", debounceMs: 15000 },
    limits: { maxResults: 6, timeoutMs: 4000 },
    scope: {
      default: "deny",
      rules: [{ action: "allow", match: { chatType: "direct" } }]
    },
    paths: [
      { name: "docs", path: "~/notes", pattern: "**/*.md" }
    ]
  }
}
```

**Key QMD config fields:**

| Field | Default | Description |
|-------|---------|-------------|
| `command` | `qmd` | Override executable path |
| `searchMode` | `query` | `query` / `search` / `vsearch` |
| `includeDefaultMemory` | `true` | Auto-index `MEMORY.md` + `memory/**/*.md` |
| `update.interval` | `5m` | Refresh cadence |
| `update.debounceMs` | `15000` | Debounce for file changes |
| `update.waitForBootSync` | `false` | Block chat startup on boot refresh |
| `limits.maxResults` | — | Cap search results |
| `limits.timeoutMs` | `4000` | Search timeout |

**Pre-warm QMD index manually:**
```bash
STATE_DIR="${OPENCLAW_STATE_DIR:-$HOME/.openclaw}"
export XDG_CONFIG_HOME="$STATE_DIR/agents/main/qmd/xdg-config"
export XDG_CACHE_HOME="$STATE_DIR/agents/main/qmd/xdg-cache"
qmd update && qmd embed
qmd query "test" -c memory-root --json >/dev/null 2>&1
```

- `memory.citations`: `auto` / `on` / `off` — applies regardless of backend
- If QMD fails → automatic fallback to builtin SQLite provider
- `memory_search` results include `Source: <path#line>` footer when citations enabled

---

## SQLite Vector Acceleration (sqlite-vec)

```json5
agents: {
  defaults: {
    memorySearch: {
      store: {
        vector: {
          enabled: true,
          extensionPath: "/path/to/sqlite-vec"  // optional override
        }
      }
    }
  }
}
```
- `enabled` defaults to `true`; if missing/failed → falls back to in-process cosine similarity

---

## Session Store Schema (sessions.json)

Path: `~/.openclaw/agents/<agentId>/sessions/sessions.json`

**Key fields:**

| Field | Description |
|-------|-------------|
| `sessionId` | Current transcript file id |
| `updatedAt` | Last activity timestamp |
| `chatType` | `direct \| group \| room` |
| `compactionCount` | Times auto-compaction completed |
| `memoryFlushAt` | Timestamp of last pre-compaction flush |
| `memoryFlushCompactionCount` | Compaction count when flush last ran |
| `contextTokens` | Runtime context estimate |
| `inputTokens` / `outputTokens` / `totalTokens` | Rolling token counters |
| `providerOverride` / `modelOverride` | Per-session model selection |
| `sendPolicy` | Per-session send override |

---

## Disable Memory Plugins

```json5
{ plugins: { slots: { memory: "none" } } }
```

---

## Inspection Commands

```
/status              — window usage, session settings, compaction count
/context list        — injected files + rough sizes
/context detail      — per-file, per-tool schema sizes
/compact             — manual compaction (optional instructions)
/compact Focus on decisions and open questions
openclaw status      — CLI: store path + recent sessions
openclaw sessions --json          — dump all entries
openclaw sessions --active <min>  — filter active sessions
```

---

## Troubleshooting

- **Wrong session key:** Check `/status` for `sessionKey`, consult session routing rules
- **Store vs transcript mismatch:** Confirm Gateway host and `openclaw status` store path
- **Compaction spam:** Check model context window size; `reserveTokens` too high; enable session pruning for tool-result bloat
- **Silent turns leaking:** Confirm reply starts with exact token `NO_REPLY`; verify build includes streaming suppression fix (2026.1.10+)
- **Memory search empty:** Check `scope` rules (default QMD scope is DM-only); check `memory.citations` setting; inspect `status().backend` to confirm which engine is serving
- **Local embeddings fail:** Run `pnpm approve-builds` → `pnpm rebuild node-llama-cpp`; set `fallback: "openai"` as safety net
- **QMD first search slow:** Normal — QMD downloads GGUF models on first `qmd query` run; pre-warm with bash commands above
