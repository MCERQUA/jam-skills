# OpenClaw Multi-Agent Reference

---

## What Is an Agent?

Each agent is a fully isolated "brain" with its own:
- **Workspace** — files, AGENTS.md, SOUL.md, USER.md, persona rules, `cwd`
- **State dir (`agentDir`)** — auth profiles, model registry, per-agent config
- **Session store** — `~/.openclaw/agents/<agentId>/sessions/`
- **Auth** — `~/.openclaw/agents/<agentId>/agent/auth-profiles.json` (NOT shared)

> Workspace is default `cwd`, not a hard sandbox. Relative paths resolve inside workspace; absolute paths reach the host unless sandboxing is enabled.

---

## Paths Quick Map

| Item | Default Path |
|------|-------------|
| Config | `~/.openclaw/openclaw.json` |
| State dir | `~/.openclaw` (or `OPENCLAW_STATE_DIR`) |
| Workspace | `~/.openclaw/workspace` |
| Agent dir | `~/.openclaw/agents/<agentId>/agent` |
| Sessions | `~/.openclaw/agents/<agentId>/sessions/` |
| Session store | `~/.openclaw/agents/<agentId>/sessions/sessions.json` |
| Transcripts | `~/.openclaw/agents/<agentId>/sessions/<SessionId>.jsonl` |

Single-agent default: `agentId = main`, sessions keyed as `agent:main:<mainKey>`.

---

## CLI Commands

```bash
openclaw agents list                            # list all agents
openclaw agents list --bindings                 # list agents + routing rules
openclaw agents add work                        # wizard: add new agent
openclaw agents add work --workspace ~/.openclaw/workspace-work
openclaw agents delete work

openclaw agents set-identity --workspace ~/.openclaw/workspace --from-identity
openclaw agents set-identity --agent main --name "OpenClaw" --emoji "🦞" --avatar avatars/openclaw.png

openclaw agent --agent ops --message "Summarize logs"       # run single turn
openclaw agent --to +15555550123 --message "status update"
openclaw agent --agent ops --message "report" --deliver --reply-channel slack --reply-to "#reports"
openclaw agent --session-id 1234 --message "Summarize" --thinking medium

openclaw status                                 # store path + recent sessions
openclaw sessions --json                        # dump all session entries
openclaw sessions --active 60                   # only active last 60 min
openclaw security audit                         # verify DM scope settings
openclaw doctor                                 # migrate legacy agent.* configs
```

---

## `agents.list` Config Fields

| Field | Description |
|-------|-------------|
| `id` | Unique agent identifier |
| `default` | `true` = fallback when no binding matches |
| `name` | Display name |
| `workspace` | Path to workspace dir |
| `agentDir` | Path to agent state dir (auth, model registry) |
| `model` | Override model for this agent |
| `identity.name` | Agent display name |
| `identity.theme` | Theme string |
| `identity.emoji` | Emoji icon |
| `identity.avatar` | Workspace-relative path or URL |
| `groupChat.mentionPatterns` | `["@bot", "@name"]` — required mentions in group chats |
| `sandbox.mode` | `"off"` \| `"all"` \| `"non-main"` |
| `sandbox.scope` | `"session"` \| `"agent"` \| `"shared"` |
| `sandbox.docker.setupCommand` | Runs once on container creation |
| `sandbox.docker.env` | Env vars injected into sandbox |
| `tools.allow` | Array of allowed tool names / group shorthands |
| `tools.deny` | Array of denied tool names / group shorthands |
| `tools.profile` | Tool profile name (e.g. `"coding"`, `"messaging"`) |
| `tools.elevated.enabled` | Per-agent elevated mode |
| `subagents.model` | Default model for sub-agents spawned by this agent |
| `subagents.thinking` | Default thinking level for sub-agents |
| `subagents.allowAgents` | `["agentId", ...]` or `["*"]` — cross-agent spawn allowlist |

---

## Full Config Example: Two WhatsApps → Two Agents

```js
{
  agents: {
    list: [
      {
        id: "home",
        default: true,
        name: "Home",
        workspace: "~/.openclaw/workspace-home",
        agentDir: "~/.openclaw/agents/home/agent",
      },
      {
        id: "work",
        name: "Work",
        workspace: "~/.openclaw/workspace-work",
        agentDir: "~/.openclaw/agents/work/agent",
      },
    ],
  },
  bindings: [
    { agentId: "home", match: { channel: "whatsapp", accountId: "personal" } },
    { agentId: "work", match: { channel: "whatsapp", accountId: "biz" } },
    // Per-peer override wins over account-level rule:
    {
      agentId: "work",
      match: { channel: "whatsapp", accountId: "personal", peer: { kind: "group", id: "1203630...@g.us" } },
    },
  ],
  tools: {
    agentToAgent: {
      enabled: false,          // agent-to-agent OFF by default; must explicitly enable + allowlist
      allow: ["home", "work"],
    },
  },
  channels: {
    whatsapp: {
      accounts: { personal: {}, biz: {} },
    },
  },
}
```

---

## Channel Routing Rules (Deterministic, Most-Specific Wins)

| Priority | Match |
|----------|-------|
| 1 (highest) | Exact `peer` match (`peer.kind` + `peer.id`) |
| 2 | `guildId` (Discord) |
| 3 | `teamId` (Slack) |
| 4 | `accountId` match for a channel |
| 5 | Channel-level match (any account) |
| 6 (lowest) | Default agent (`default: true`, else first in list, else `main`) |

> Peer bindings must appear **above** channel-wide rules in config.

---

## Binding Examples

```json5
// Route by channel:
{ agentId: "chat", match: { channel: "whatsapp" } }
{ agentId: "opus", match: { channel: "telegram" } }

// Route one DM to different agent:
{ agentId: "opus", match: { channel: "whatsapp", peer: { kind: "direct", id: "+15551234567" } } }

// Route a group:
{ agentId: "family", match: { channel: "whatsapp", peer: { kind: "group", id: "120363999@g.us" } } }

// Route one Slack workspace:
{ match: { channel: "slack", teamId: "T123" }, agentId: "support" }
```

---

## Broadcast Groups (Multiple Agents, Same Peer)

```json5
{
  broadcast: {
    strategy: "parallel",
    "120363403215116621@g.us": ["alfred", "baerbel"],  // WhatsApp group → 2 agents
    "+15555550123": ["support", "logger"],
  },
}
```

---

## Session Key Shapes

| Context | Key Format |
|---------|-----------|
| Direct chat (default) | `agent:<agentId>:<mainKey>` (e.g. `agent:main:main`) |
| DM per-peer | `agent:<agentId>:dm:<peerId>` |
| DM per-channel-peer | `agent:<agentId>:<channel>:dm:<peerId>` |
| DM per-account-channel-peer | `agent:<agentId>:<channel>:<accountId>:dm:<peerId>` |
| Group | `agent:<agentId>:<channel>:group:<id>` |
| Channel/room | `agent:<agentId>:<channel>:channel:<id>` |
| Thread | base key + `:thread:<threadId>` |
| Telegram topic | group key + `:topic:<topicId>` |
| Sub-agent | `agent:<agentId>:subagent:<uuid>` |
| Cron | `cron:<job.id>` |
| Webhook | `hook:<uuid>` |

---

## Session Isolation (`dmScope`)

| Value | Isolation |
|-------|-----------|
| `main` (default) | All DMs share main session — single-user only |
| `per-peer` | Isolated by sender id across channels |
| `per-channel-peer` | Isolated by channel + sender — **recommended for multi-user** |
| `per-account-channel-peer` | Isolated by account + channel + sender — multi-account inboxes |

```json5
{
  session: {
    dmScope: "per-channel-peer",          // recommended for multi-user
    identityLinks: { alice: ["telegram:123456789", "discord:987654321012345678"] },
    reset: { mode: "daily", atHour: 4, idleMinutes: 120 },
    resetByType: {
      direct: { mode: "idle", idleMinutes: 240 },
      group:  { mode: "idle", idleMinutes: 120 },
    },
    resetByChannel: { discord: { mode: "idle", idleMinutes: 10080 } },
    mainKey: "main",
  },
}
```

> **Security warning:** Without `dmScope` isolation, multiple users share one context — private info leaks between senders.

---

## Per-Agent Sandbox & Tools

### Sandbox Modes & Scopes

**`sandbox.mode`:** `off` (host) | `non-main` (sandbox groups/channels, main on host) | `all` (always sandbox)

**`sandbox.scope`:** `session` (one container/session, default) | `agent` (one container/agent) | `shared` (shared across agents)

> `agents.list[].sandbox.docker.*` overrides are **ignored** when scope resolves to `"shared"`.

### Tool Filtering Order (most restrictive wins, cannot grant back)

1. Tool profile (`tools.profile` or `agents.list[].tools.profile`)
2. Provider tool profile
3. Global tool policy (`tools.allow` / `tools.deny`)
4. Provider tool policy
5. Agent tool policy (`agents.list[].tools.allow/deny`)
6. Agent provider policy
7. Sandbox tool policy
8. Subagent tool policy

### Tool Group Shorthands

| Group | Expands To |
|-------|-----------|
| `group:runtime` | `exec`, `bash`, `process` |
| `group:fs` | `read`, `write`, `edit`, `apply_patch` |
| `group:sessions` | `sessions_list`, `sessions_history`, `sessions_send`, `sessions_spawn`, `session_status` |
| `group:memory` | `memory_search`, `memory_get` |
| `group:ui` | `browser`, `canvas` |
| `group:automation` | `cron`, `gateway` |
| `group:messaging` | `message` |
| `group:nodes` | `nodes` |
| `group:openclaw` | All built-in OpenClaw tools |

### Config: Personal (host) + Restricted Family Agent (sandboxed)

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "default": true,
        "workspace": "~/.openclaw/workspace",
        "sandbox": { "mode": "off" }
      },
      {
        "id": "family",
        "workspace": "~/.openclaw/workspace-family",
        "sandbox": { "mode": "all", "scope": "agent" },
        "tools": {
          "allow": ["read"],
          "deny": ["exec", "write", "edit", "apply_patch", "process", "browser"]
        }
      }
    ]
  },
  "bindings": [
    { "agentId": "family", "match": { "provider": "whatsapp", "accountId": "*", "peer": { "kind": "group", "id": "120363424282127706@g.us" } } }
  ]
}
```

### Config: Global coding profile + messaging-only agent

```json
{
  "tools": { "profile": "coding" },
  "agents": {
    "list": [
      { "id": "support", "tools": { "profile": "messaging", "allow": ["slack"] } }
    ]
  }
}
```

---

## Sub-Agents

Sub-agents run in isolated background sessions (`agent:<agentId>:subagent:<uuid>`) on a dedicated `subagent` queue lane, then announce results back to the requester chat.

### `sessions_spawn` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `task` | string | required | What to do |
| `label` | string | — | Short identifier for logs/UI |
| `agentId` | string | caller's agent | Spawn under different agent (must be allowlisted) |
| `model` | string | — | Override model |
| `thinking` | string | — | `off`, `low`, `medium`, `high` |
| `runTimeoutSeconds` | number | `0` (no limit) | Abort after N seconds |
| `cleanup` | `"delete"` \| `"keep"` | `"keep"` | Archive immediately after announce |

Returns immediately: `{ status: "accepted", runId, childSessionKey }`

### Sub-agent Model Resolution (first match wins)

1. Explicit `model` in `sessions_spawn`
2. `agents.list[].subagents.model`
3. `agents.defaults.subagents.model`
4. Target agent's normal model resolution

### Sub-agent Defaults

```json5
{
  agents: {
    defaults: {
      subagents: {
        model: "minimax/MiniMax-M2.1",
        thinking: "low",
        maxConcurrent: 8,        // default: 8
        archiveAfterMinutes: 60, // default: 60; renames to *.deleted.<timestamp>
      },
    },
  },
}
```

### Cross-Agent Spawning

```json5
{
  agents: {
    list: [
      {
        id: "orchestrator",
        subagents: {
          allowAgents: ["researcher", "coder"],  // or ["*"] for any
        },
      },
    ],
  },
}
```

### Default Denied Tools for Sub-Agents

`sessions_list`, `sessions_history`, `sessions_send`, `sessions_spawn`, `gateway`, `agents_list`, `whatsapp_login`, `session_status`, `cron`, `memory_search`, `memory_get`

### Custom Sub-Agent Tool Policy

```json5
{
  tools: {
    subagents: {
      tools: {
        deny: ["browser", "firecrawl"],                              // added to default deny list
        allow: ["read", "exec", "process", "write", "edit", "apply_patch"],  // restrict to these only
      },
    },
  },
}
```

### Sub-agent Context

- **Included:** Tooling, Workspace, Runtime sections, `AGENTS.md`, `TOOLS.md`
- **Not included:** `SOUL.md`, `IDENTITY.md`, `USER.md`, `HEARTBEAT.md`, `BOOTSTRAP.md`

### `/subagents` Slash Commands

```
/subagents list | stop <id|#|all> | log <id|#> [limit] [tools] | info <id|#> | send <id|#> <msg>
```

### Sub-agent Limitations
- No nested spawning; announce + archive timers lost on gateway restart; shared process → set `maxConcurrent`

---

## Session Tools (`sessions_*`)

#| Tool | Key Params | Returns / Notes |
|------|-----------|-----------------|
| `sessions_list` | `kinds?`, `limit?`, `activeMinutes?`, `messageLimit?` | Array of: `key`, `kind`, `channel`, `displayName`, `sessionId`, `model`, `contextTokens`, `transcriptPath` |
| `sessions_history` | `sessionKey` (required), `limit?`, `includeTools?` | Raw transcript messages |
| `sessions_send` | `sessionKey`, `message`, `timeoutSeconds?` | `0`=fire-and-forget; `>0`=wait for reply. Triggers ping-pong (max `session.agentToAgent.maxPingPongTurns`, default 5). Reply `REPLY_SKIP` / `ANNOUNCE_SKIP` to stop. |
| `sessions_spawn` | `task`, `label?`, `agentId?`, `model?`, `thinking?`, `runTimeoutSeconds?`, `cleanup?` | Returns `{ status: "accepted", runId, childSessionKey }` immediately |

### Sandbox Session Visibility

```json5
// default: sandboxed agents only see sessions they spawned
agents: { defaults: { sandbox: { sessionToolsVisibility: "spawned" } } }
// or: "all" to see everything
```

---

## Skills: Shared vs Per-Agent

| Scope | Location | Availability |
|-------|----------|--------------|
| Managed/shared | `~/.openclaw/skills/` | All agents |
| Bundled | Shipped with install | All agents (filter via `allowBundled`) |
| Workspace-specific | `<workspace>/skills/` | Only that agent |
| Extra dirs | `skills.load.extraDirs` | All agents |

### Skills Config

```json5
{
  skills: {
    allowBundled: ["gemini", "peekaboo"],          // restrict bundled skills to this list
    load: {
      extraDirs: ["~/Projects/skills"],
      watch: true,
      watchDebounceMs: 250,
    },
    install: {
      preferBrew: true,
      nodeManager: "npm",                          // npm | pnpm | yarn | bun
    },
    entries: {
      "nano-banana-pro": {
        enabled: true,
        apiKey: "GEMINI_KEY_HERE",
        env: { GEMINI_API_KEY: "GEMINI_KEY_HERE" },
      },
      peekaboo: { enabled: true },
      sag: { enabled: false },
    },
  },
}
```

> **Sandboxed skills:** Docker sandbox does NOT inherit host `process.env`. Use `agents.defaults.sandbox.docker.env` or `agents.list[].sandbox.docker.env` instead of `skills.entries.<skill>.env`.

---

## Troubleshooting

### Agent not sandboxed despite `mode: "all"`
- Agent-specific config takes precedence over `agents.defaults` — set `agents.list[].sandbox.mode: "all"` explicitly.

### Tools still available despite deny list
- Check filtering order: global → agent → sandbox → subagent.
- Each level can only further restrict, not grant back.
- Check logs: `[tools] filtering tools for agent:${agentId}`

### Container not isolated per agent
- Set `scope: "agent"` in agent-specific sandbox config.
- Default `scope: "session"` creates one container per session, not per agent.

### `non-main` sandbox mode sandboxing wrong sessions
- `non-main` is based on `session.mainKey` (default `"main"`), **not agent id**.
- Groups/channels always get non-main keys → always sandboxed.
- To never sandbox an agent, use `agents.list[].sandbox.mode: "off"`.

### Verify routing and sandbox

```bash
openclaw agents list --bindings
docker ps --filter "name=openclaw-sbx-"
tail -f "${OPENCLAW_STATE_DIR:-$HOME/.openclaw}/logs/gateway.log" | grep -E "routing|sandbox|tools"
```

### Auth collisions between agents
- Never reuse `agentDir` across agents.
- To share creds: copy `auth-profiles.json` into the other agent's `agentDir`.

### `tools.elevated` per-agent
- `tools.elevated` is global (sender-based). Both global AND per-agent must allow.
- To restrict: `agents.list[].tools.elevated.enabled: false` or deny `exec` for that agent.

---

## `agents.defaults` (Global Defaults for All Agents)

```json5
{
  agents: {
    defaults: {
      model: { primary: "anthropic/claude-sonnet-4" },
      sandbox: {
        mode: "non-main",
        scope: "session",
        sessionToolsVisibility: "spawned",
        docker: {
          setupCommand: "apt-get update && apt-get install -y git",
          env: { MY_KEY: "value" },
        },
      },
      subagents: {
        model: "minimax/MiniMax-M2.1",
        thinking: "low",
        maxConcurrent: 4,
        archiveAfterMinutes: 60,
      },
    },
  },
}
```

> `agents.list[].sandbox.*` overrides `agents.defaults.sandbox.*` field by field.
> Legacy `agent.*` configs → migrate with `openclaw doctor`.
