# OpenClaw Tools & Exec Reference

---

## Built-In Tools

`exec` · `process` · `read` · `write` · `edit` · `apply_patch` · `browser` · `sessions_spawn` · `sessions_list` · `sessions_history` · `sessions_send` · `session_status` · `agents_list` · `memory_search` · `memory_get` · `web_search` · `web_fetch` · `image` · `pdf` · `message` · `cron` · `gateway` · `nodes` · `canvas`

**Optional plugin tools:** `lobster` · `llm-task` · `voice_call` · `diffs`

### Tool Groups
| Group | Expands To |
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
| `group:openclaw` | All built-in tools (excludes plugins) |

### Tool Profiles (`tools.profile`)
Base allowlist before `tools.allow`/`tools.deny`. Per-agent override: `agents.list[].tools.profile`.

| Profile | Tools |
|---------|-------|
| `minimal` | `session_status` only |
| `coding` | `group:fs`, `group:runtime`, `group:sessions`, `group:memory`, `image` |
| `messaging` | `group:messaging`, `sessions_list`, `sessions_history`, `sessions_send`, `session_status` |
| `full` | No restriction (same as unset) |

```json5
// Messaging-only default + allow Slack/Discord
{ tools: { profile: "messaging", allow: ["slack", "discord"] } }

// Global coding, messaging-only support agent
{ tools: { profile: "coding" }, agents: { list: [{ id: "support", tools: { profile: "messaging", allow: ["slack"] } }] } }
```

### Provider-Specific Tool Policy (`tools.byProvider`)
Restrict tools for specific providers/models. Applied AFTER profile, BEFORE allow/deny (can only narrow).

```json5
{
  tools: {
    profile: "coding",
    byProvider: {
      "google-antigravity": { profile: "minimal" },
      "openai/gpt-5.2": { allow: ["group:fs", "sessions_list"] },
    },
  },
}
```

Per-agent: `agents.list[].tools.byProvider`.

### Tool `alsoAllow` (Safe Additive)
Use `tools.alsoAllow` to add optional plugin tools without entering restrictive allowlist mode:
```json5
{ tools: { alsoAllow: ["lobster", "llm-task"] } }
```

### Loop Detection (`tools.loopDetection`)
Blocks or warns on repetitive no-progress tool-call loops. Default: **disabled**.

```json5
{
  tools: {
    loopDetection: {
      enabled: true,
      warningThreshold: 10,
      criticalThreshold: 20,
      globalCircuitBreakerThreshold: 30,
      historySize: 30,
      detectors: {
        genericRepeat: true,        // same tool + same params
        knownPollNoProgress: true,  // poll-like with identical outputs
        pingPong: true,             // alternating A/B/A/B
      },
    },
  },
}
```

Per-agent override: `agents.list[].tools.loopDetection`.

---

## Exec Tool

### Parameters
| Param | Default | Description |
|-------|---------|-------------|
| `command` | _(required)_ | Shell command |
| `workdir` | cwd | Working directory |
| `env` | — | Key/value env overrides |
| `yieldMs` | 10000 | Auto-background after N ms |
| `background` | false | Background immediately |
| `timeout` | 1800s | Kill on expiry |
| `pty` | false | Pseudo-terminal (for TTY CLIs) |
| `host` | `sandbox` | `sandbox \| gateway \| node` |
| `security` | `deny`/`allowlist` | `deny \| allowlist \| full` |
| `ask` | `on-miss` | `off \| on-miss \| always` |
| `node` | unset | Node id/name (for `host=node`) |
| `elevated` | false | Request elevated mode (gateway host) |

### Config (`tools.exec.*`)
| Field | Default | Description |
|-------|---------|-------------|
| `host` | `sandbox` | Default execution host |
| `security` | `deny`/`allowlist` | Enforcement mode |
| `ask` | `on-miss` | Approval prompts |
| `node` | unset | Default node binding |
| `notifyOnExit` | `true` | System event on background exit |
| `approvalRunningNoticeMs` | `10000` | "Running" notice threshold (0 disables) |
| `pathPrepend` | — | Directories to prepend to PATH |
| `safeBins` | see note | Stdin-only bins exempt from allowlist |

**Default safe bins:** `jq`, `grep`, `cut`, `sort`, `uniq`, `head`, `tail`, `tr`, `wc`

```json5
{ tools: { exec: { pathPrepend: ["~/bin", "/opt/oss/bin"] } } }
```

### Key Notes
- Sandboxing is **off by default**. `host=sandbox` without container = runs on gateway host, no approvals.
- To require approvals: use `host=gateway` + configure exec-approvals, OR enable sandboxing.
- `env.PATH` and `LD_*`/`DYLD_*` overrides rejected for host execution.
- Shell chaining (`&&`, `||`, `;`) allowed in allowlist mode only when every segment is allowlisted.
- Command substitution (`$()`) rejected in allowlist parsing.

### Per-Session Override
```
/exec host=gateway security=allowlist ask=on-miss node=mac-1
```
Authorized senders only. Updates session state only. Send `/exec` alone to show current values.

### Examples
```json
{ "tool": "exec", "command": "ls -la" }
{"tool":"exec","command":"npm run build","yieldMs":1000}
{"tool":"process","action":"poll","sessionId":"<id>"}
{"tool":"process","action":"send-keys","sessionId":"<id>","keys":["Enter"]}
{"tool":"process","action":"send-keys","sessionId":"<id>","keys":["C-c"]}
{"tool":"process","action":"paste","sessionId":"<id>","text":"line1\nline2\n"}
```

### Per-Agent Node Binding
```bash
openclaw config set agents.list[0].tools.exec.node "node-id-or-name"
```

### `apply_patch` (Experimental — OpenAI Only)
```json5
{ tools: { exec: { applyPatch: { enabled: true, allowModels: ["gpt-5.2"] } } } }
```

---

## Process Tool (Background Session Management)

Manages backgrounded exec sessions. Scoped per agent — each agent can only access its own sessions. **Sessions are in-memory only — lost on gateway restart.**

| Action | Description |
|--------|-------------|
| `list` | View all active and completed sessions |
| `poll` | Retrieve new output since last poll; check exit status |
| `log` | Aggregated output with pagination |
| `write` / `send-keys` / `paste` | Send input to running process |
| `kill` | Terminate session |
| `clear` | Remove session record |

```json
{"tool":"process","action":"list"}
{"tool":"process","action":"poll","sessionId":"<id>"}
{"tool":"process","action":"log","sessionId":"<id>","offset":0,"limit":100}
{"tool":"process","action":"write","sessionId":"<id>","input":"yes\n"}
{"tool":"process","action":"send-keys","sessionId":"<id>","keys":["C-c"]}
{"tool":"process","action":"kill","sessionId":"<id>"}
```

- Logs enter chat history **only** when you explicitly poll/log
- `notifyOnExit: true` (default) fires a system event when a background process ends

---

## Additional Tool Quick Reference

### `image` — Analyze images with configured image model
- `image` (required: path or URL), `prompt` (optional), `model` (optional), `maxBytesMb` (optional)
- Requires `agents.defaults.imageModel` configured (primary or fallbacks)
- Independent of main chat model

### `pdf` — Analyze PDF documents
See `tools/pdf` docs for full behavior, limits, and config.

### `message` — Cross-channel messaging
Actions: `send`, `poll`, `react`/`reactions`/`read`/`edit`/`delete`, `pin`/`unpin`/`list-pins`, `permissions`, `thread-create`/`thread-list`/`thread-reply`, `search`, `sticker`, `member-info`/`role-info`, `emoji-list`/`emoji-upload`/`sticker-upload`, `role-add`/`role-remove`, `channel-info`/`channel-list`, `voice-status`, `event-list`/`event-create`, `timeout`/`kick`/`ban`
- Routes WhatsApp via Gateway; other channels direct
- Session-bound sends constrained to session's target

### `cron` — Manage Gateway cron jobs
Actions: `status`, `list`, `add`, `update`, `remove`, `run`, `runs`, `wake`
- `wake` enqueues system event + optional immediate heartbeat

### `gateway` — Restart/update Gateway
Actions: `restart`, `config.get`/`config.schema`/`config.apply`/`config.patch`, `update.run`
- `delayMs` (default 2000) avoids interrupting in-flight replies
- Disable: `commands.restart: false`

### `nodes` — Discover/target paired nodes
Actions: `status`, `describe`, `pending`/`approve`/`reject`, `notify`, `run`, `camera_list`/`camera_snap`/`camera_clip`/`screen_record`, `location_get`, `notifications_list`/`notifications_action`, `device_status`/`device_info`/`device_permissions`/`device_health`
- `run` params: `command` (argv array), `cwd`, `env`, `commandTimeoutMs`, `invokeTimeoutMs`, `needsScreenRecording`
- Camera/screen require foreground; images return `MEDIA:<path>`; videos return `FILE:<path>`

### `canvas` — Drive node Canvas
Actions: `present`, `hide`, `navigate`, `eval`, `snapshot`, `a2ui_push`, `a2ui_reset`
- A2UI is v0.8 only (no v0.9 JSONL)
- Smoke test: `openclaw nodes canvas a2ui push --node <id> --text "Hello"`

### `agents_list` — List agent IDs available for `sessions_spawn`
Restricted to per-agent allowlists (`agents.list[].subagents.allowAgents`).

### `web_search` / `web_fetch` — Web search and content extraction
See separate reference: `web-tools.md` for full provider details and config.

---

## Exec Approvals

**File:** `~/.openclaw/exec-approvals.json`

Applies to `host=gateway` or `host=node`. Layered on top of tool policy + elevated (skipped when `elevated=full`). Effective policy = stricter of `tools.exec.*` and approvals defaults.

```json
{
  "version": 1,
  "defaults": {
    "security": "deny",
    "ask": "on-miss",
    "askFallback": "deny",
    "autoAllowSkills": false
  },
  "agents": {
    "main": {
      "security": "allowlist",
      "ask": "on-miss",
      "askFallback": "deny",
      "autoAllowSkills": true,
      "allowlist": [
        { "id": "UUID", "pattern": "~/Projects/**/bin/rg", "lastUsedCommand": "rg -n TODO" }
      ]
    }
  }
}
```

- **`askFallback`:** `deny | allowlist | full` — what happens when no UI available
- Allowlists are per-agent; patterns = case-insensitive glob, binary paths only (basename ignored)
- Examples: `~/Projects/**/bin/peekaboo`, `~/.local/bin/*`, `/opt/homebrew/bin/rg`

### Approval Flow
- exec returns immediately: `status: "approval-pending"` + approval id
- System events: `Exec running`, `Exec finished`, `Exec denied`
- Approve via chat: `/approve <id> allow-once|allow-always|deny`

### Approval Forwarding Config
```json5
{
  approvals: {
    exec: {
      enabled: true,
      mode: "session",        // "session" | "targets" | "both"
      agentFilter: ["main"],
      sessionFilter: ["discord"],
      targets: [{ channel: "slack", to: "U12345678" }],
    },
  },
}
```

```bash
openclaw approvals  # View/edit approvals (gateway or node)
```

---

## Elevated Mode

- `/elevated on` or `/elevated ask` — gateway host + keep approvals
- `/elevated full` — gateway host + **skip** approvals (sets `security=full`)
- `/elevated off` — disable; `/elev` — alias

**Resolution order:** inline directive → session override → `agents.defaults.elevatedDefault`

| Field | Description |
|-------|-------------|
| `tools.elevated.enabled` | Global gate |
| `tools.elevated.allowFrom` | Per-provider sender allowlists |
| `agents.list[].tools.elevated.enabled` | Per-agent gate (can only restrict) |
| `agents.list[].tools.elevated.allowFrom` | Per-agent allowlist |

- `on`/`ask` do NOT force `security=full`; configured policy still applies
- No-op for unsandboxed agents
- Tool policy still applies — if `exec` denied, elevated can't override
- Directive-only message persists; inline in normal message applies to that message only

---

## Browser Tool

### Profiles
| Profile | Description |
|---------|-------------|
| `openclaw` | Managed isolated browser (no extension) |
| `chrome` | Extension relay to existing Chrome tab |

### Config (`~/.openclaw/openclaw.json`)
```json5
{
  browser: {
    enabled: true,
    defaultProfile: "chrome",
    headless: false,
    attachOnly: false,
    executablePath: "/usr/bin/brave-browser",
    remoteCdpTimeoutMs: 1500,
    remoteCdpHandshakeTimeoutMs: 3000,
    profiles: {
      openclaw: { cdpPort: 18800, color: "#FF4500" },
      work: { cdpPort: 18801, color: "#0066CC" },
      remote: { cdpUrl: "http://10.0.0.42:9222" },
    },
  },
}
```

```bash
openclaw config set browser.executablePath "/usr/bin/google-chrome"
```

### CLI Reference
```bash
# Basics
openclaw browser status | start | stop | tabs
openclaw browser open https://example.com
openclaw browser focus <targetId> | close <targetId>

# Inspection
openclaw browser screenshot [--full-page] [--ref 12]
openclaw browser snapshot                             # AI snapshot (numeric refs)
openclaw browser snapshot --interactive               # role snapshot (e12 refs, best for actions)
openclaw browser snapshot --efficient                 # compact preset
openclaw browser snapshot --labels                    # screenshot with ref overlays
openclaw browser snapshot --frame "iframe#main" --interactive
openclaw browser console --level error
openclaw browser errors --clear
openclaw browser requests --filter api --clear
openclaw browser pdf

# Actions
openclaw browser navigate https://example.com
openclaw browser click 12 | click e12 --double
openclaw browser type 23 "hello" --submit
openclaw browser press Enter | hover 44 | drag 10 11
openclaw browser select 9 OptionA OptionB
openclaw browser wait "#main" --url "**/dash" --load networkidle --fn "window.ready===true"
openclaw browser upload /tmp/file.pdf
openclaw browser dialog --accept
openclaw browser highlight e12
openclaw browser trace start | trace stop

# State
openclaw browser cookies | cookies set session abc123 --url "https://example.com" | cookies clear
openclaw browser storage local get | set theme dark | clear
openclaw browser set offline on | headers --json '{"X-Debug":"1"}' | credentials user pass
openclaw browser set geo 37.7749 -122.4194 --origin "https://example.com"
openclaw browser set timezone America/New_York | locale en-US | device "iPhone 14"
```

- Refs are **not stable across navigations** — re-snapshot after navigation
- CSS selectors not supported for actions
- `upload` and `dialog` are **arming** calls — run before the triggering click

### Snapshot Formats & Debug
| Mode | Refs | Use |
|------|------|-----|
| Default (`--format ai`) | Numeric `12` | Standard |
| `--format aria` | None | Inspection only |
| `--interactive` (role) | Role `e12` | Best for actions |
| `--efficient` | Role `e12` | Compact, lower tokens |

**Debug:** snapshot `--interactive` → click/type ref → fails? `highlight <ref>` → page oddities: `errors --clear` + `requests --filter api --clear` → deep: `trace start` → reproduce → `trace stop`

### Chrome Extension Setup
```bash
openclaw browser extension install
# Chrome: chrome://extensions → Developer mode → Load unpacked → select printed dir
# Click extension on tab to attach (badge = ON)
openclaw browser --browser-profile chrome tabs
```

### Browserless
```json5
{
  browser: {
    profiles: {
      browserless: { cdpUrl: "https://production-sfo.browserless.io?token=<KEY>" }
    }
  }
}
```

### Docker Playwright
```bash
docker compose run --rm openclaw-cli \
  node /app/node_modules/playwright-core/cli.js install chromium
```

### Agent Tool Notes
- Single `browser` tool; accepts `profile` and `target` (`sandbox|host|node`)
- Sandboxed sessions: default `target="sandbox"`; host requires `agents.defaults.sandbox.browser.allowHostControl=true`

---

## Slash Commands

### Config
```json5
{
  commands: {
    native: "auto",        // auto=on for Discord/Telegram
    nativeSkills: "auto",
    text: true,
    bash: false,
    config: false,
    debug: false,
    restart: false,
    allowFrom: { "*": ["user1"], discord: ["user:123"] },
    useAccessGroups: true,
  },
}
```

### Directives (stripped before model; persist only in directive-only messages)
| Directive | Notes |
|-----------|-------|
| `/think <off\|minimal\|low\|medium\|high\|xhigh>` | aliases: `/thinking`, `/t` |
| `/verbose on\|full\|off` | alias: `/v` |
| `/reasoning on\|off\|stream` | alias: `/reason` |
| `/elevated on\|off\|ask\|full` | alias: `/elev` |
| `/exec host=... security=... ask=... node=...` | per-session exec defaults |
| `/model <name>` | alias: `/models` |
| `/queue <mode>` | plus `debounce:2s cap:25 drop:summarize` |

### Full Command List
```
/help | /commands | /status | /whoami (/id)
/skill <name> [input]
/allowlist [add|remove]         — requires commands.config: true
/approve <id> allow-once|allow-always|deny
/context [list|detail|json]
/subagents list|stop|log|info|send
/config show|get|set|unset      — requires commands.config: true
/debug show|set|unset|reset     — requires commands.debug: true
/usage off|tokens|full|cost
/tts off|always|inbound|tagged|...   (Discord: /voice)
/stop | /restart               — restart requires commands.restart: true
/reset | /new [model]
/send on|off|inherit           — owner-only
/activation mention|always     — groups only
/dock-telegram | /dock-discord | /dock-slack
/bash <command>                — requires commands.bash: true + elevated allowlists
/compact [instructions]        — text only
! <command>  |  !poll  |  !stop  — text only, host bash
```

- Commands accept optional `:` between command and args (e.g. `/think: high`)
- Unauthorized command-only messages silently ignored
- Fast path: command-only from allowlisted senders bypasses queue + model
- Inline shortcuts (allowlisted only): `/help`, `/commands`, `/status`, `/whoami`
- `/model list` → `/model 3` → `/model openai/gpt-5.2` → `/model status`

---

## Sub-Agents

Non-blocking. Returns `{ status: "accepted", runId, childSessionKey }` immediately. Runs on `subagent` lane. Result announced to requester chat. Auto-archived after 60 min (transcripts kept as `*.deleted.<timestamp>`).

### `sessions_spawn` Parameters
| Param | Default | Description |
|-------|---------|-------------|
| `task` | _(required)_ | What to do |
| `label` | — | Short ID label |
| `runtime` | `"subagent"` | `"subagent"` or `"acp"` (see `acp-agents.md`) |
| `agentId` | caller's | Spawn under different agent |
| `model` | — | Override model (invalid values → warning + default) |
| `thinking` | — | Override thinking level |
| `runTimeoutSeconds` | config or 0 | Abort after N seconds |
| `thread` | `false` | Request channel thread binding |
| `mode` | `"run"` | `"run"` (one-shot) or `"session"` (persistent, requires `thread: true`) |
| `cleanup` | `"keep"` | `"delete"` archives immediately after announce |
| `sandbox` | `"inherit"` | `"inherit"` or `"require"` (rejects unsandboxed targets) |
| `streamTo` | — | `"parent"` streams progress summaries back as system events |
| `attachments` | — | Inline file attachments (subagent only, not ACP) |
| `attachAs` | — | `mountPath` reserved for future mount support |

### Attachments
Files materialized into child workspace at `.openclaw/attachments/<uuid>/` with `.manifest.json`.
Config: `tools.sessions_spawn.attachments` (`enabled`, `maxTotalBytes`, `maxFiles`, `maxFileBytes`, `retainOnSessionKeep`).

### Config
```json5
{
  agents: {
    defaults: {
      subagents: {
        model: "minimax/MiniMax-M2.1",
        thinking: "low",
        maxConcurrent: 4,         // default: 8
        archiveAfterMinutes: 30,  // default: 60
      },
    },
  },
}
```

### Cross-Agent Spawning
```json5
{ agents: { list: [{ id: "orchestrator", subagents: { allowAgents: ["researcher", "coder"] } }] } }
```

### `/subagents` Commands
| Command | Description |
|---------|-------------|
| `/subagents list` | List all runs |
| `/subagents stop <id\|#\|all>` | Stop a run |
| `/subagents log <id\|#> [limit] [tools]` | View transcript |
| `/subagents info <id\|#>` | Run metadata |
| `/subagents send <id\|#> <message>` | Send to running sub-agent |

### Thread-Bound Sessions
When thread bindings enabled (currently Discord only), sub-agents stay bound to a thread:
- Spawn with `thread: true` + `mode: "session"` for persistent thread binding
- Follow-ups in thread route to bound session
- `/focus <target>`, `/unfocus`, `/agents`, `/session idle`, `/session max-age` for manual control
- Config: `session.threadBindings.enabled`, `channels.discord.threadBindings.spawnSubagentSessions`

### Nested Sub-Agents
Default `maxSpawnDepth: 1` (sub-agents can't spawn children). Set `maxSpawnDepth: 2` for orchestrator pattern.

```json5
{
  agents: { defaults: { subagents: {
    maxSpawnDepth: 2,           // allow sub-agents to spawn children (1-5)
    maxChildrenPerAgent: 5,     // max active children per session (1-20)
    maxConcurrent: 8,           // global lane cap
    runTimeoutSeconds: 900,     // default timeout
  } } },
}
```

| Depth | Session Key | Role | Can Spawn? |
|-------|-------------|------|------------|
| 0 | `agent:<id>:main` | Main agent | Always |
| 1 | `agent:<id>:subagent:<uuid>` | Orchestrator (depth 2) or leaf (depth 1) | Only if `maxSpawnDepth >= 2` |
| 2 | `...:subagent:<uuid>:subagent:<uuid>` | Leaf worker | Never |

- Depth-1 orchestrators get `sessions_spawn`, `subagents`, `sessions_list`, `sessions_history`
- Cascade stop: stopping depth-1 → auto-stops all depth-2 children

### Stopping
- `/stop` — aborts main + all active sub-agents (cascades)
- `/subagents kill <id>` — stops specific + cascades to children
- `/subagents kill all` — stops all + cascades
- `runTimeoutSeconds` — auto-abort (does NOT auto-archive)

### Auto-Archive
- Sessions archived after `agents.defaults.subagents.archiveAfterMinutes` (default 60)
- Transcript renamed to `*.deleted.<timestamp>` (same folder, NOT deleted)
- `cleanup: "delete"` archives immediately after announce
- Pending timers lost on gateway restart

### Default Denied Tools
`sessions_list`, `sessions_history`, `sessions_send`, `sessions_spawn`, `gateway`, `agents_list`, `whatsapp_login`, `session_status`, `cron`, `memory_search`, `memory_get`

### Customize Sub-Agent Tools
```json5
{
  tools: {
    subagents: {
      tools: {
        deny: ["browser"],
        // allow: ["read","exec","process"] — restrict to only these
      },
    },
  },
}
```

### System Prompt
- **Included:** Tooling, Workspace, Runtime, `AGENTS.md`, `TOOLS.md`
- **Excluded:** `SOUL.md`, `IDENTITY.md`, `USER.md`, `HEARTBEAT.md`, `BOOTSTRAP.md`
- Auth: per-agent (`~/.openclaw/agents/<agentId>/agent/auth-profiles.json`); main profiles merged as fallback

---

## Tool Policy & Gating

### Filtering Order (Each Level Can Only Restrict — Cannot Re-Grant)
1. Tool profile (`tools.profile` or `agents.list[].tools.profile`)
2. Provider tool profile (`tools.byProvider[provider].profile`)
3. Global tool policy (`tools.allow` / `tools.deny`)
4. Provider tool policy (`tools.byProvider[provider].allow/deny`)
5. Agent-specific (`agents.list[].tools.allow/deny`)
6. Agent provider policy (`agents.list[].tools.byProvider[provider].allow/deny`)
7. Sandbox tool policy (`tools.sandbox.tools`)
8. Subagent tool policy (`tools.subagents.tools`)

### Multi-Agent Config Examples
```json5
// Personal (full) + Restricted Family
{
  agents: { list: [
    { id: "main", default: true, sandbox: { mode: "off" } },
    {
      id: "family",
      sandbox: { mode: "all", scope: "agent" },
      tools: { allow: ["read"], deny: ["exec","write","edit","apply_patch","process","browser"] }
    }
  ]}
}

// Global coding + messaging-only support agent
{
  tools: { profile: "coding" },
  agents: { list: [{ id: "support", tools: { profile: "messaging", allow: ["slack"] } }] }
}
```

### Sandbox Modes / Scopes
| Mode | Description | Scope | Container per |
|------|-------------|-------|--------------|
| `off` | No sandboxing | `session` | Session (default) |
| `all` | Always sandbox | `agent` | Agent |
| `non-main` | Sandbox non-main sessions | `shared` | Shared |

⚠️ `non-main` is based on `session.mainKey` (default `"main"`), not agent id.

### Precedence
```
agents.list[].sandbox.* > agents.defaults.sandbox.*
agents.list[].tools.* merges with (cannot expand beyond) global tools.*
```

### Troubleshooting
1. **Tools still available despite deny:** Check filter order; verify logs: `[tools] filtering tools for agent:${agentId}`
2. **Agent not sandboxed:** Agent-specific config takes precedence — set `agents.list[].sandbox.mode: "all"`
3. **Container not isolated per agent:** Set `scope: "agent"` (default is `"session"`)

```bash
openclaw agents list --bindings
docker ps --filter "name=openclaw-sbx-"
openclaw sandbox explain
tail -f "${OPENCLAW_STATE_DIR:-$HOME/.openclaw}/logs/gateway.log" | grep -E "routing|sandbox|tools"
```

---

## Lobster (Typed Workflow Runtime)

Lobster is an optional plugin that runs multi-step tool pipelines as a single deterministic operation with approval gates.

**Install:** `lobster` CLI on gateway host. Enable via config:
```json5
{ tools: { alsoAllow: ["lobster"] } }
// Or per-agent:
{ agents: { list: [{ id: "main", tools: { alsoAllow: ["lobster"] } }] } }
```

**Key features:**
- **One call instead of many** — replaces repeated LLM tool invocations with a single structured execution
- **Approval gates** — side effects (email sends, writes) pause and return a resume token until approved
- **Resumable state** — halted workflows return a token; continue without re-executing previous steps
- **Constrained grammar** — pipelines stored as data, not arbitrary code; runtime enforces timeouts + output limits

**Pattern:**
```
inbox list | categorize | apply | approve --prompt 'Proceed?'
```

**Use with `llm-task`:** Each step can invoke an LLM to classify/transform data before passing to the next step.

---

## LLM Task Plugin

Enables structured LLM calls within workflows (especially Lobster pipelines). Returns JSON-only output.

**Enable:**
```json5
{
  plugins: { entries: { "llm-task": { enabled: true } } },
  agents: { list: [{ id: "main", tools: { allow: ["llm-task"] } }] },
}
```

**Config (optional):**
```json5
{
  plugins: { entries: { "llm-task": { enabled: true, config: {
    defaultProvider: "openai-codex",
    defaultModel: "gpt-5.2",
    allowedModels: ["openai-codex/gpt-5.3-codex"],
    maxTokens: 800,
    timeoutMs: 30000,
  } } } },
}
```

**Parameters:**
| Param | Description |
|-------|-------------|
| `prompt` | Instruction for the model |
| `input` | Input text/data |
| `schema` | Optional JSON schema for output validation |
| `model` | Model override |
| `temperature` | Temperature override |
| `maxTokens` | Max output tokens |

**Important:** Output is untrusted unless validated against a schema. Any side-effecting operations should be gated behind an approval step. Result returned in `details.json`.

---

## Thinking Levels (`/think`)

Controls reasoning depth per message, session, or globally.

| Level | Aliases | Notes |
|-------|---------|-------|
| `off` | — | No extended thinking |
| `minimal` | — | "think" |
| `low` | — | "think hard" |
| `medium` | — | "think harder" |
| `high` | `highest`, `max` | "ultrathink" (max budget) |
| `xhigh` | `x-high`, `extra-high` | "ultrathink+" (GPT-5.2/Codex only) |
| `adaptive` | — | Provider-managed (Anthropic Claude 4.6 family) |

**Resolution order:** inline directive → session override → `agents.defaults.thinkingDefault` → `adaptive` (Claude 4.6) / `low` (other reasoning) / `off`

**Usage:**
```
/think:medium          — set session default (sticks until changed)
/think:high What is X  — inline (this message only)
/think off             — disable for session
/think                 — show current level
```

**Config (global default):**
```json5
{ agents: { defaults: { thinkingDefault: "low" } } }
```

**Provider limits:**
- **Z.AI**: Binary on/off only — all non-off levels → `low`
- **Moonshot**: Binary enabled/disabled. When enabled, only `tool_choice` `auto|none` accepted
- **Anthropic Claude 4.6**: Defaults to `adaptive` when no level set

**Companion directives:**
- `/verbose on|full|off` — show tool call details (tool summaries as separate bubbles). `/verbose full` also forwards tool outputs
- `/reasoning on|off|stream` — display thinking blocks as separate `Reasoning:` messages. `stream` (Telegram only): streams reasoning during generation, sends final answer without it
- Send directive alone to see current level

---

## Browser Login

For sites requiring authentication, **do not give credentials to the model**. Use the dedicated OpenClaw browser profile instead.

```bash
openclaw browser start          # opens the orange-tinted OpenClaw profile
# Manually log in to sites in this profile — cookies persist
```

**For X/Twitter specifically:** Use the **host browser** (manual login) for reading, searching, and posting to avoid bot-detection triggers.

**Sandboxed agents:** Enable host browser control if needed:
```json5
{ agents: { defaults: { sandbox: { browser: { allowHostControl: true } } } } }
```
Then use `target: "host"` in browser tool calls to reach the manually-logged-in profile.

---

## Agent Send (`openclaw agent`)

Runs a single agent turn without an inbound chat message. Useful for scripting, cron jobs, and testing.

```bash
openclaw agent --to "+15551234567"                        # target by phone/peer
openclaw agent --session-id <key>                         # reuse existing session
openclaw agent --agent researcher --message "Summarize X" # target specific agent
openclaw agent --local                                    # bypass gateway, run embedded
openclaw agent --deliver                                  # send reply back to channel
openclaw agent --json                                     # structured JSON output
```

- Falls back to embedded local execution if gateway is unreachable
- `--deliver` supports `--channel`, `--to`, `--account` overrides
- Thinking levels and verbose settings persist into session store

---

## Reactions

| Field | Behavior |
|-------|----------|
| `emoji` (required to add) | Emoji to add |
| `emoji=""` | Remove bot's reactions (most channels) |
| `remove: true` | Remove specific emoji (requires `emoji`) |

| Channel | Notes |
|---------|-------|
| Discord/Slack | `emoji=""` removes all bot reactions; `remove:true` removes just that emoji |
| Google Chat | Same as Discord/Slack |
| Telegram | `emoji=""` removes; `remove:true` still needs non-empty emoji |
| WhatsApp | `emoji=""` or `remove:true` both remove |
| Signal | Inbound notifications → system events (`channels.signal.reactionNotifications: true`) |
