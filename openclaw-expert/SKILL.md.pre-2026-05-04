---
name: openclaw-expert
description: Comprehensive guide to OpenClaw architecture, configuration, skills, gateway, memory, and all platform internals. Use for teaching, debugging, and building on OpenClaw.
metadata: {"openclaw": {"emoji": "🧠"}}
---

# OpenClaw Expert

## What is OpenClaw

- **Personal AI assistant platform** — runs on your own devices, connects to channels you already use
- Single **Gateway daemon** (Node ≥ 22) is the control plane: one WS server, all channels, all sessions
- Default port: `ws://127.0.0.1:18789` (Clawdbot uses `18791`)
- Channels: WhatsApp, Telegram, Discord, Slack, Signal, iMessage/BlueBubbles, Matrix, MS Teams, Google Chat, IRC, Nostr, LINE, Twitch, Zalo, Feishu, Mattermost, WebChat
- **Agent Runtime**: Pi agent in RPC mode — streaming LLM + tool execution
- **Skills**: Markdown-defined agent plugins (workspace / managed / bundled), published to ClawHub
- **Sessions**: One per channel/group; `main` = direct 1:1; persistent key = Z.AI prompt cache warm
- **Memory**: `MEMORY.md` (long-term, injected every session) + `memory/YYYY-MM-DD.md` (daily logs, on-demand)
- **Nodes**: macOS/iOS/Android devices with camera, canvas, screen recording, location, system.run
- **Config file**: `~/.openclaw/openclaw.json` (JSON5), workspace: `~/.openclaw/workspace/`

## Architecture Mental Model

```
Channels (WhatsApp / Telegram / Discord / Slack / Signal / iMessage / Matrix / Teams…)
               │
               ▼
┌────────────────────────────────────────────────────────┐
│                     GATEWAY (Node daemon)              │
│  Channels ─ Sessions ─ Agent Runtime ─ Skills ─ Tools  │
│  Memory / Workspace (~/.openclaw/workspace/)           │
└────────────────────────────────────────────────────────┘
               │
    ┌──────────┼──────────────────┐
    ▼          ▼                  ▼
  CLI        Nodes           Canvas Host
(openclaw) (iOS/macOS/Android)  (port 18793)
```

**Message flow:** Channel inbound → access control (allowFrom / dmPolicy / mention gate) → session key resolved → agent runtime → LLM (streaming) → tool execution → response chunks → channel outbound.

**Key insight:** Everything is stateful via sessions. Persistent session key = warm Z.AI prompt cache (3-8s). New session key = cold (15-30s). Context is the bootstrap files injected on first turn (~14K tokens for a full workspace). Sub-agents run in isolated sessions. Multi-agent: each agent has its own workspace, auth, sessions — routed by bindings config.

## Quick Reference — All Reference Files

| Topic | File |
|-------|------|
| Architecture & component diagram | `{baseDir}/references/architecture-overview.md` |
| Gateway wire protocol & handshake | `{baseDir}/references/gateway-protocol.md` |
| Full config schema (`openclaw.json`) | `{baseDir}/references/gateway-configuration.md` |
| **Heartbeat, local models, multiple gateways, Tailscale, OpenAI API compat, trusted proxy, config examples** | `{baseDir}/references/gateway-advanced.md` |
| **OpenResponses API, Tools Invoke API, Chat Completions API** | `{baseDir}/references/http-apis.md` |
| Agent lifecycle, tools, model selection | `{baseDir}/references/agent-runtime.md` |
| Sessions, compaction, pruning | `{baseDir}/references/sessions-and-context.md` |
| Memory files, vector search, QMD backend | `{baseDir}/references/memory-system.md` |
| System prompt assembly, bootstrap injection | `{baseDir}/references/system-prompt.md` |
| Skills format, gating, ClawHub CLI | `{baseDir}/references/skills-system.md` |
| Models, providers list, auth, fallbacks | `{baseDir}/references/models-and-providers.md` |
| Channels overview, DM/group policies, routing | `{baseDir}/references/channels-overview.md` |
| Per-channel setup (WhatsApp/Telegram/Discord/etc.) | `{baseDir}/references/channels-detail.md` |
| **Tools: exec, process, browser, tool profiles, tool groups, byProvider, loop detection, sub-agents, thinking, lobster, llm-task, agent-send, tool policy** | `{baseDir}/references/tools-and-exec.md` |
| **Web tools: web_search, web_fetch (Perplexity, Brave, Gemini, Grok, Kimi)** | `{baseDir}/references/web-tools.md` |
| **ACP Agents: Pi, Claude Code, Codex, OpenCode, Gemini CLI, Kimi harnesses** | `{baseDir}/references/acp-agents.md` |
| **Plugins/extensions: discovery, SDK, tools, channels, providers, hooks** | `{baseDir}/references/plugins-system.md` |
| Cron, webhooks, heartbeat, lifecycle hooks | `{baseDir}/references/automation.md` |
| Security model, sandboxing, prompt injection | `{baseDir}/references/security.md` |
| Full CLI reference (all commands) | `{baseDir}/references/cli-reference.md` |
| Multi-agent routing, isolation, sub-agents | `{baseDir}/references/multi-agent.md` |
| Canvas, nodes, macOS app, voice wake | `{baseDir}/references/canvas-and-nodes.md` |
| Troubleshooting ladder, per-channel fixes | `{baseDir}/references/troubleshooting.md` |
| **Hetzner VPS deployment (Docker)** | `{baseDir}/references/install-hetzner.md` |

## Teaching Mode

When the user asks to **teach**, **explain**, or **present** OpenClaw topics:

1. Read the relevant reference file(s) from `{baseDir}/references/`
2. Build an HTML slide deck using the `canvas` tool:
   ```
   canvas present — show a URL or local HTML on the node canvas
   canvas a2ui_push — push A2UI components (v0.8 format)
   canvas hide — hide canvas panel
   ```
3. HTML slides template (minimal):
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
4. Write slide HTML to `~/.openclaw/workspace/canvas/teach-<topic>.html`
5. Use `canvas present` with the local file path or serve via canvas host (port 18793)
6. Walk through each slide conversationally — pause for questions

**Canvas show command** (agent tool call):
```json
{"tool": "canvas", "action": "present", "target": "file:///home/mike/.openclaw/workspace/canvas/teach-topic.html"}
```

## Top 10 FAQ

**Q1: Why are responses slow (15-30s)?**
Cold session — Z.AI prompt cache miss. Use persistent session key. After first warm-up, responses drop to 3-8s. Cache TTL is 30 min idle. See `sessions-and-context.md`.

**Q2: How do I add a new channel?**
`openclaw channels add` or edit `~/.openclaw/openclaw.json` under `channels.<name>`. Run `openclaw gateway restart`. See `channels-detail.md` for per-channel setup steps.

**Q3: How do I create a skill?**
```bash
mkdir -p ~/.openclaw/workspace/skills/my-skill
cat > ~/.openclaw/workspace/skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: One-line description.
---
# My Skill
Instructions for the agent.
EOF
```
Reload: ask agent "refresh skills" or restart gateway. See `skills-system.md`.

**Q4: How do I add a new AI model/provider?**
Set `ZAI_API_KEY` (or relevant env var), update `agents.defaults.model.primary` in config. Use `openclaw models list` and `openclaw models set provider/model`. See `models-and-providers.md`.

**Q5: Bot not replying in group chat?**
Check `requireMention` setting and whether bot is mentioned. Run `openclaw channels status --probe` and `openclaw pairing list <channel>`. See `troubleshooting.md` section 5.2.

**Q6: How do sessions work? What's dmScope?**
`dmScope` controls how DM conversations are isolated. Default `"main"` = all DMs share one session. Use `"per-channel-peer"` for multi-user setups. Session keys determine Z.AI cache warmth. See `sessions-and-context.md`.

**Q7: How do I run a cron job / scheduled task?**
```bash
openclaw cron add --name "daily" --cron "0 9 * * *" --session isolated \
  --message "Morning summary" --announce --channel telegram --to "@me"
```
See `automation.md` for full cron, webhooks, heartbeat reference.

**Q8: How do I sandbox the agent for untrusted users?**
```json5
{ agents: { defaults: { sandbox: { mode: "non-main", scope: "session", workspaceAccess: "none" } } } }
```
Also set `dmPolicy: "pairing"` and tool deny lists. See `security.md`.

**Q9: Context window filling up? Slow compaction?**
Use `/compact` to summarize manually. Enable `contextPruning: { mode: "cache-ttl", ttl: "30m" }`. Run `/context list` to see what's consuming tokens. Keep `TOOLS.md`, `HEARTBEAT.md` small. See `sessions-and-context.md`.

**Q10: How do I use the canvas / show something visually?**
Agent uses `canvas` tool: `present`, `hide`, `navigate`, `eval`, `snapshot`. Nodes (macOS/iOS/Android) must be paired. See `canvas-and-nodes.md`. For A2UI push: v0.8 format only (`beginRendering`, `surfaceUpdate`).

## Troubleshooting Quick-Start

Run these in order (verbatim):

```bash
openclaw status
openclaw gateway status
openclaw logs --follow
openclaw doctor
openclaw channels status --probe
```

**Healthy signals:**
- `gateway status` → `Runtime: running` and `RPC probe: ok`
- `doctor` → no blocking errors
- `channels status --probe` → `connected` or `ready`
- `logs --follow` → steady activity, no repeating fatal errors

**Common errors → fixes:**

| Error | Fix |
|-------|-----|
| `Gateway start blocked: set gateway.mode=local` | `openclaw config set gateway.mode local` |
| `refusing to bind gateway ... without auth` | Set `gateway.auth.token` in config |
| `EADDRINUSE` / port conflict | `openclaw gateway --force` |
| `NOT_PAIRED` / `device identity required` | Auth token missing or wrong in connect |
| `unauthorized` during connect | Token mismatch — check `launchctl getenv OPENCLAW_GATEWAY_TOKEN` |
| No replies in group chat | Check `requireMention` + `openclaw pairing list <channel>` |
| WhatsApp disconnects | `openclaw channels logout && openclaw channels login --verbose` |
| Model auth failed | `openclaw models status` → re-run `claude setup-token` or set API key |
| `NODE_BACKGROUND_UNAVAILABLE` | Bring node app to foreground |
| `SYSTEM_RUN_DENIED` | `openclaw approvals get --node <id>` → approve or add to allowlist |

**Full troubleshooting:** `{baseDir}/references/troubleshooting.md`

## Reference File Index

| File | 1-line Description |
|------|--------------------|
| `architecture-overview.md` | Component diagram, message flow, ports, wire protocol, key directories, minimal config |
| `gateway-protocol.md` | WebSocket handshake (3-step), frame formats, RPC methods, event types, auth, node pairing |
| `gateway-configuration.md` | Full `openclaw.json` schema: agents, channels, session, tools, skills, cron, hooks, gateway, env |
| `gateway-advanced.md` | Heartbeat, local models, multiple gateways, Tailscale, OpenAI API, trusted proxy, config examples |
| `http-apis.md` | OpenResponses API (`/v1/responses`), Tools Invoke API (`/tools/invoke`), Chat Completions API |
| `agent-runtime.md` | Agent lifecycle (11 steps), workspace layout, bootstrap injection, tools table, queue modes, multi-agent |
| `sessions-and-context.md` | Session keys, dmScope, reset policy, compaction vs pruning, JSONL format, inspect commands |
| `memory-system.md` | Memory files, vector search providers, hybrid BM25+vector, QMD backend, embedding config |
| `system-prompt.md` | Prompt assembly order (26 sections), bootstrap file injection, token cost, `/context` commands |
| `skills-system.md` | SKILL.md format, frontmatter keys, gating (`requires.*`), installer specs, ClawHub CLI, `{baseDir}` |
| `models-and-providers.md` | Provider table (26 providers), auth types, fallback config, Ollama, Z.AI, OpenRouter, model aliases |
| `channels-overview.md` | DM/group policies, mention gating, routing priority, session keys, message flow, reply tags |
| `channels-detail.md` | Per-channel setup: WhatsApp, Telegram, Discord, Slack, Signal, iMessage, BlueBubbles, Teams, Matrix + more |
| `tools-and-exec.md` | Full tool inventory, tool profiles/groups/byProvider, exec, process, browser, sub-agents, thinking, tool policy |
| `web-tools.md` | web_search + web_fetch: Perplexity, Brave, Gemini, Grok, Kimi providers, Firecrawl fallback |
| `acp-agents.md` | ACP agent sessions: Pi, Claude Code, Codex, OpenCode, Gemini CLI, Kimi harnesses, thread binding |
| `plugins-system.md` | Plugin architecture, SDK paths, tool/channel/provider registration, hooks, CLI, distribution |
| `automation.md` | Cron jobs, heartbeat, webhooks (`/hooks/wake`, `/hooks/agent`), lifecycle hooks, Gmail Pub/Sub |
| `security.md` | Threat model, 5 trust boundaries, sandbox setup, DM pairing, network exposure, prompt injection, incident response |
| `cli-reference.md` | Every CLI command: setup, config, gateway, messaging, agents, sessions, memory, channels, models, nodes, cron |
| `multi-agent.md` | Multi-agent config, binding rules (6-priority), broadcast groups, session isolation, sub-agents, skills scope |
| `canvas-and-nodes.md` | Canvas system, A2UI v0.8, node commands (camera/screen/location/SMS), macOS app, voice wake, headless node |
| `troubleshooting.md` | Triage ladder, log reading, 12 issue categories, per-channel fixes, config migration table, node error codes |
