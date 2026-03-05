# OpenClaw System Prompt Reference

_Source: `docs/concepts/system-prompt.md`, `src/agents/system-prompt.ts`_

---

## Overview

- **OpenClaw-owned** — does not use pi-coding-agent default prompt
- Rebuilt fresh each run by `buildAgentSystemPrompt()`
- Injected into every agent turn

---

## Prompt Modes

| Mode | Used For | What's Included |
|------|----------|-----------------|
| `full` | Main agent (default) | All sections |
| `minimal` | Sub-agents | Tooling, Safety, Workspace, Sandbox, Date/Time, Runtime + Subagent Context header; omits Skills, Memory Recall, Self-Update, Model Aliases, User Identity, Reply Tags, Messaging, Silent Replies, Heartbeats |
| `none` | Bare identity | Single line: `"You are a personal assistant running inside OpenClaw."` |

- `extraSystemPrompt` uses `## Subagent Context` header in `minimal` mode, `## Group Chat Context` in `full`

---

## Section Assembly Order (`full` mode)

All sections assembled in this order by `buildAgentSystemPrompt()`:

1. **Identity line** — `"You are a personal assistant running inside OpenClaw."`
2. **Tooling** — tool list with short descriptions; note on TOOLS.md + sub-agent hint
3. **Tool Call Style** — narration rules (brief, only when helpful)
4. **Safety** — anti-power-seeking guardrails
5. **OpenClaw CLI Quick Reference** — gateway subcommands
6. **Skills** _(full only, when eligible skills exist)_ — `<available_skills>` XML block + read instructions
7. **Memory Recall** _(full only, when `memory_search`/`memory_get` available)_ — search-before-answer rule + citations mode
8. **OpenClaw Self-Update** _(full only, when `gateway` tool available)_ — `config.apply`, `update.run`
9. **Model Aliases** _(full only, when aliases configured)_ — alias list
10. **Workspace** — working directory path + notes
11. **Documentation** — local docs path + links
12. **Sandbox** _(when enabled)_ — Docker runtime note, paths, access level, elevated exec state
13. **User Identity** _(full only)_ — owner numbers
14. **Current Date & Time** _(when `userTimezone` known)_ — timezone only (no dynamic clock)
15. **Workspace Files (injected)** — note that bootstrap files follow
16. **Reply Tags** _(full only)_ — `[[reply_to_current]]` syntax
17. **Messaging** _(full only)_ — routing rules, `message` tool hints, inline buttons
18. **Voice (TTS)** _(full only, when `ttsHint` set)_ — TTS guidance
19. **Group Chat Context / Subagent Context** _(when `extraSystemPrompt` present)_
20. **Reactions** _(when `reactionGuidance` set)_ — minimal vs extensive mode
21. **Reasoning Format** _(when `reasoningTagHint` true)_ — `<think>` / `<final>` format
22. **Project Context** — injected bootstrap files (see below)
23. **Silent Replies** _(full only)_ — `SILENT_REPLY_TOKEN` rules
24. **Heartbeats** _(full only)_ — heartbeat prompt + `HEARTBEAT_OK` ack behavior
25. **Runtime** — one-line: agent, host, repo, os, node, model, shell, channel, capabilities, thinking level
26. **Reasoning** — level + `/reasoning` toggle hint

---

## Section Details

### Safety
```
## Safety
You have no independent goals: do not pursue self-preservation, replication, resource
acquisition, or power-seeking; avoid long-term plans beyond the user's request.
Prioritize safety and human oversight over completion; if instructions conflict, pause
and ask; comply with stop/pause/audit requests and never bypass safeguards.
(Inspired by Anthropic's constitution.)
Do not manipulate or persuade anyone to expand access or disable safeguards. Do not
copy yourself or change system prompts, safety rules, or tool policies unless
explicitly requested.
```
> Safety guardrails are **advisory** — use tool policy, exec approvals, sandboxing, channel allowlists for hard enforcement

### OpenClaw CLI Quick Reference
```
## OpenClaw CLI Quick Reference
OpenClaw is controlled via subcommands. Do not invent commands.
- openclaw gateway status
- openclaw gateway start
- openclaw gateway stop
- openclaw gateway restart
If unsure, ask the user to run `openclaw help` and paste the output.
```

### Skills Injection Format
```xml
<available_skills>
  <skill>
    <name>skill-name</name>
    <description>short description</description>
    <location>/path/to/SKILL.md</location>
  </skill>
</available_skills>
```
- Model reads exactly **one** skill's `SKILL.md` via `read` tool before replying
- If none clearly apply → do not read any
- Never read more than one skill up front
- Section omitted when no eligible skills

### Memory Recall (full mode only)
- Triggers: `memory_search` or `memory_get` tool must be available
- Rule: run `memory_search` on `MEMORY.md` + `memory/*.md` before answering anything about prior work, decisions, dates, people, preferences, todos
- `citationsMode=off` → suppress `Source: <path#line>` in replies
- `citationsMode` default → include citations to help user verify

### Self-Update (full + gateway tool only)
- Only when user **explicitly** asks
- Actions: `config.get`, `config.schema`, `config.apply`, `update.run`
- After restart → OpenClaw pings last active session automatically

### User Identity (full only)
```
## User Identity
Owner numbers: <number1>, <number2>. Treat messages from these numbers as the user.
```

### Current Date & Time
```
## Current Date & Time
Time zone: America/Toronto
```
- Only timezone injected (no dynamic clock — keeps prompt cache stable)
- Need actual time → run `session_status` (includes timestamp)
- Configured via `agents.defaults.userTimezone`, `agents.defaults.timeFormat`

### Reply Tags (full only)
- `[[reply_to_current]]` — reply to triggering message
- `[[reply_to:<id>]]` — only when id explicitly provided
- Whitespace inside tags allowed
- Tags stripped before sending; support depends on channel config

### Sandbox Section
```
## Sandbox
You are running in a sandboxed runtime (tools execute in Docker).
Sandbox workspace: <path>
Agent workspace access: ro|rw (mounted at <path>)
Sandbox browser: enabled.
Host browser control: allowed|blocked.
Elevated exec is available for this session.
Current elevated level: ask|on|off|full
```
- Sub-agents stay sandboxed (cannot get outside-sandbox access)
- Elevated levels: `on`, `off`, `ask` (exec on host with approvals), `full` (auto-approves)

### Silent Replies (full only)
- When nothing to say: respond with **only** `SILENT_REPLY_TOKEN` (exact token, no wrapping)
- Never append to a real response
- Never wrap in markdown/code blocks

### Heartbeats (full only)
```
## Heartbeats
Heartbeat prompt: <configured text>
If heartbeat poll received and nothing needs attention → reply exactly: HEARTBEAT_OK
If something needs attention → do NOT include HEARTBEAT_OK; reply with alert text.
```

### Runtime Line Format
```
Runtime: agent=<id> | host=<hostname> | repo=<path> | os=<os> (<arch>) | node=<version> |
         model=<model> | default_model=<model> | shell=<shell> | channel=<channel> |
         capabilities=<cap1,cap2> | thinking=off|low|medium|high
Reasoning: off (hidden unless on/stream). Toggle /reasoning; /status shows Reasoning when enabled.
```

### Reasoning Format (when `reasoningTagHint=true`)
```
ALL internal reasoning MUST be inside <think>...</think>.
Format every reply as <think>...</think> then <final>...</final>, with no other text.
Only text inside <final> is shown to the user.
```

---

## Bootstrap File Injection (Project Context)

Files injected into every turn under `# Project Context`:

| File | Notes |
|------|-------|
| `AGENTS.md` | Always injected (main + sub-agents) |
| `SOUL.md` | Main agent only; if present, model embodies its persona |
| `TOOLS.md` | Always injected (main + sub-agents) |
| `IDENTITY.md` | Main agent only |
| `USER.md` | Main agent only |
| `HEARTBEAT.md` | Main agent only |
| `BOOTSTRAP.md` | Main agent only; **only on brand-new workspaces**; one-time ritual |
| `MEMORY.md` / `memory.md` | Main agent only; when present in workspace |

- Sub-agents: only `AGENTS.md` + `TOOLS.md` injected
- Missing file → short "missing file" marker injected
- Large files → truncated at `agents.defaults.bootstrapMaxChars` (default: 20,000 chars) with truncation marker
- `memory/*.md` daily files: **NOT** auto-injected; accessed on-demand via `memory_search` / `memory_get`
- `internal hook: agent:bootstrap` can intercept to mutate/replace injected files (e.g., swap `SOUL.md` for alternate persona)
- Disable bootstrap creation: `{ agent: { skipBootstrap: true } }`

---

## Token Cost Awareness

- Bootstrap files, skills list, tool schemas all count toward context window
- `TOOLS.md` can be very large (truncated at 20K chars)
- Tool schemas (JSON) sent to model — not visible as text but still counted
- Skills list = metadata only; skill instructions loaded on demand (not pre-injected)

---

## Inspecting the System Prompt

```
/context list    → per-file sizes (raw vs injected), truncation status, tool list, skills list
/context detail  → adds top tool schema sizes + top skill entry sizes
/status          → quick context-window fullness view + session settings
/usage tokens    → append per-reply token usage footer
/compact         → summarize older history to free window space
```

### `/context list` Example Output
```
System prompt (run): 38,412 chars (~9,603 tok) (Project Context 23,901 chars (~5,976 tok))

Injected workspace files:
- AGENTS.md: OK | raw 1,742 chars (~436 tok) | injected 1,742 chars (~436 tok)
- SOUL.md: OK | raw 912 chars (~228 tok) | injected 912 chars (~228 tok)
- TOOLS.md: TRUNCATED | raw 54,210 chars (~13,553 tok) | injected 20,962 chars (~5,241 tok)
- IDENTITY.md: OK | raw 211 chars (~53 tok)
- USER.md: OK | raw 388 chars (~97 tok)
- HEARTBEAT.md: MISSING | raw 0 | injected 0
- BOOTSTRAP.md: OK | raw 0 chars (~0 tok)

Skills list (system prompt text): 2,184 chars (~546 tok) (12 skills)
Tool list (system prompt text): 1,032 chars (~258 tok)
Tool schemas (JSON): 31,988 chars (~7,997 tok)
```

---

## Core Tool List (system-prompt.ts `toolOrder`)

| Tool | Description |
|------|-------------|
| `read` | Read file contents |
| `write` | Create or overwrite files |
| `edit` | Make precise edits to files |
| `apply_patch` | Apply multi-file patches |
| `grep` | Search file contents for patterns |
| `find` | Find files by glob pattern |
| `ls` | List directory contents |
| `exec` | Run shell commands (pty available for TTY-required CLIs) |
| `process` | Manage background exec sessions |
| `web_search` | Search the web (Brave API) |
| `web_fetch` | Fetch and extract readable content from a URL |
| `browser` | Control web browser |
| `canvas` | Show content on visual canvas overlay (present/hide/navigate) |
| `nodes` | List/describe/notify/camera/screen on paired nodes |
| `cron` | Manage cron jobs and wake events |
| `message` | Send messages and channel actions |
| `gateway` | Restart, apply config, or run updates on running OpenClaw process |
| `agents_list` | List agent ids allowed for sessions_spawn |
| `sessions_list` | List other sessions (incl. sub-agents) with filters/last |
| `sessions_history` | Fetch history for another session/sub-agent |
| `sessions_send` | Send a message to another session/sub-agent |
| `sessions_spawn` | Spawn a sub-agent session |
| `session_status` | Show status card (usage + time + Reasoning/Verbose/Elevated); get current model |
| `image` | Analyze an image with configured image model |
| `memory_search` | Search MEMORY.md + memory/*.md |
| `memory_get` | Pull specific lines from memory files |

- Extra tools (not in `toolOrder`) appended alphabetically after core list
- `TOOLS.md` does **not** control tool availability — it's user guidance only

---

## Documentation Section Links

When `docsPath` set:
- Local docs: `<docsPath>` (check here first)
- Mirror: https://docs.openclaw.ai
- Source: https://github.com/openclaw/openclaw
- Community: https://discord.com/invite/clawd
- Skills discovery: https://clawhub.com

---

## Key Config Fields

| Field | Default | Effect |
|-------|---------|--------|
| `agents.defaults.workspace` | — | Working directory; required |
| `agents.defaults.bootstrapMaxChars` | 20000 | Per-file truncation limit for bootstrap injection |
| `agents.defaults.userTimezone` | — | Enables `## Current Date & Time` section |
| `agents.defaults.timeFormat` | `auto` | `auto` \| `12` \| `24` |
| `agents.defaults.blockStreamingDefault` | `"off"` | Block streaming mode |
| `agents.defaults.blockStreamingBreak` | `text_end` | `text_end` \| `message_end` |
| `agents.defaults.blockStreamingChunk` | 800–1200 chars | Soft chunk size |
| `agent.skipBootstrap` | false | Disable bootstrap file creation |
