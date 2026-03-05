# OpenClaw ACP Agents Reference

Agent Client Protocol (ACP) sessions let OpenClaw run external coding harnesses (Pi, Claude Code, Codex, OpenCode, Gemini CLI, Kimi) through an ACP backend plugin.

---

## ACP vs Sub-Agents

| Area | ACP Session | Sub-Agent Run |
|------|-------------|---------------|
| Runtime | ACP backend plugin (e.g. acpx) | OpenClaw native sub-agent runtime |
| Session key | `agent:<agentId>:acp:<uuid>` | `agent:<agentId>:subagent:<uuid>` |
| Commands | `/acp ...` | `/subagents ...` |
| Spawn tool | `sessions_spawn` with `runtime:"acp"` | `sessions_spawn` (default runtime) |
| Sandbox | Host-only (blocked from sandboxed sessions) | Supports sandbox inheritance |

---

## Quick Start

```text
/acp spawn codex --mode persistent --thread auto
/acp status
/acp model anthropic/claude-opus-4-5
/acp permissions strict
/acp timeout 120
/acp steer tighten logging and continue
/acp cancel          # stop current turn
/acp close           # close session + remove bindings
```

Natural language triggers: "run this in Codex", "start Claude Code in a thread" → OpenClaw routes to ACP runtime.

---

## Spawning ACP Sessions

### From `sessions_spawn` tool

```json
{
  "task": "Open the repo and summarize failing tests",
  "runtime": "acp",
  "agentId": "codex",
  "thread": true,
  "mode": "session"
}
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `task` | Yes | Initial prompt sent to ACP session |
| `runtime` | Yes (for ACP) | Must be `"acp"` |
| `agentId` | No | Target harness id. Falls back to `acp.defaultAgent` |
| `thread` | No (default `false`) | Request thread binding where supported |
| `mode` | No | `run` (one-shot) or `session` (persistent). Default `run`. If `thread: true` and mode omitted, defaults to `session` |
| `cwd` | No | Working directory (validated by backend/runtime policy) |
| `label` | No | Operator-facing label |
| `streamTo` | No | `"parent"` streams progress summaries back as system events |

### From `/acp spawn` command

```text
/acp spawn codex --mode persistent --thread auto
/acp spawn codex --mode oneshot --thread off
/acp spawn codex --thread here --cwd /repo
```

Thread modes: `auto` (bind current or create), `here` (require active thread), `off` (unbound).

---

## Thread-Bound Sessions

- Enabled per-channel adapter (currently: Discord)
- Follow-up messages in bound thread route to the same ACP session
- Unfocus/close/archive/idle-timeout/max-age expiry removes binding

Required config:
```json5
{
  acp: { enabled: true },
  session: {
    threadBindings: { enabled: true, idleHours: 24, maxAgeHours: 0 },
  },
  channels: {
    discord: {
      threadBindings: { enabled: true, spawnAcpSessions: true },
    },
  },
}
```

---

## ACP Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `/acp spawn` | Create ACP session | `/acp spawn codex --mode persistent --thread auto --cwd /repo` |
| `/acp cancel` | Cancel in-flight turn | `/acp cancel agent:codex:acp:<uuid>` |
| `/acp steer` | Send instruction to running session | `/acp steer --session support prioritize failing tests` |
| `/acp close` | Close session + unbind threads | `/acp close` |
| `/acp status` | Show backend, mode, state, capabilities | `/acp status` |
| `/acp set-mode` | Set runtime mode | `/acp set-mode plan` |
| `/acp set` | Generic runtime config write | `/acp set model openai/gpt-5.2` |
| `/acp cwd` | Set working directory | `/acp cwd /Users/user/Projects/repo` |
| `/acp permissions` | Set approval policy profile | `/acp permissions strict` |
| `/acp timeout` | Set runtime timeout (seconds) | `/acp timeout 120` |
| `/acp model` | Set model override | `/acp model anthropic/claude-opus-4-5` |
| `/acp reset-options` | Clear runtime overrides | `/acp reset-options` |
| `/acp sessions` | List recent ACP sessions | `/acp sessions` |
| `/acp doctor` | Backend health + fixes | `/acp doctor` |
| `/acp install` | Print install steps | `/acp install` |

---

## Session Target Resolution

1. Explicit target argument (key → UUID → label)
2. Current thread binding
3. Current requester session fallback

---

## acpx Harness Aliases

Built-in: `pi`, `claude`, `codex`, `opencode`, `gemini`, `kimi`

---

## Required Config

```json5
{
  acp: {
    enabled: true,
    dispatch: { enabled: true },   // pause dispatch with false
    backend: "acpx",
    defaultAgent: "codex",
    allowedAgents: ["pi", "claude", "codex", "opencode", "gemini", "kimi"],
    maxConcurrentSessions: 8,
    stream: { coalesceIdleMs: 300, maxChunkChars: 1200 },
    runtime: { ttlMinutes: 120 },
  },
}
```

---

## Plugin Setup (acpx)

```bash
openclaw plugins install acpx
openclaw config set plugins.entries.acpx.enabled true
/acp doctor   # verify health
```

### acpx Command/Version Config

```json5
{
  plugins: {
    entries: {
      acpx: {
        enabled: true,
        config: {
          command: "../acpx/dist/cli.js",   // or absolute path
          expectedVersion: "any",            // disables strict version matching
        },
      },
    },
  },
}
```

---

## Permission Configuration

ACP sessions are non-interactive (no TTY for approval prompts).

### `permissionMode`

| Value | Behavior |
|-------|----------|
| `approve-all` | Auto-approve all file writes and shell commands |
| `approve-reads` | Auto-approve reads only; writes/exec require prompts |
| `deny-all` | Deny all permission prompts |

### `nonInteractivePermissions`

| Value | Behavior |
|-------|----------|
| `fail` | Abort with `AcpRuntimeError` **(default)** |
| `deny` | Silently deny and continue (graceful degradation) |

```bash
openclaw config set plugins.entries.acpx.config.permissionMode approve-all
openclaw config set plugins.entries.acpx.config.nonInteractivePermissions fail
```

---

## Sandbox Compatibility

- ACP runs on host runtime, NOT inside sandbox
- Sandboxed sessions **cannot** spawn ACP sessions
- `sandbox="require"` is unsupported for `runtime="acp"`
- Use `runtime="subagent"` from sandboxed sessions

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ACP runtime backend is not configured` | Install + enable backend plugin, run `/acp doctor` |
| `ACP is disabled by policy` | Set `acp.enabled=true` |
| `ACP dispatch is disabled` | Set `acp.dispatch.enabled=true` |
| `ACP agent "<id>" is not allowed` | Update `acp.allowedAgents` |
| `Unable to resolve session target` | Run `/acp sessions`, copy exact key/label |
| `--thread here` outside thread | Use `--thread auto` or `off` |
| `Sandboxed sessions cannot spawn ACP` | Use `runtime="subagent"` instead |
| `AcpRuntimeError: Permission prompt unavailable` | Set `permissionMode=approve-all` |
| ACP session stalls after completing | Check `ps aux | grep acpx`; kill stale processes |
