# OpenClaw Glossary

Key terms from the OpenClaw documentation, one-line definitions.

---

**A2UI** — The Android/iOS native Node app that connects a phone to the Gateway as a device (camera, SMS, screen, exec, location).

**AGENTS.md** — Bootstrap file injected into the system prompt listing all configured agents, their roles, and routing rules.

**Agent** — A named AI persona defined in `gateway.yaml` with its own model, system prompt, tools, skills, memory, and channel bindings.

**Bootstrap** — The set of Markdown files (SOUL.md, IDENTITY.md, TOOLS.md, etc.) injected into the agent's system prompt at session start to establish identity and context.

**BOOTSTRAP.md** — A bootstrap file that contains additional startup instructions or context injected before the first user message in a session.

**Cache TTL** — The duration (e.g., `30m`) that a Z.AI / provider prompt cache stays warm; after expiry, the next message triggers a cold (slow) inference with full token reload.

**Canvas** — The browser-based visual layer (iframe overlay or dedicated URL) used to display rich UI content — slides, dashboards, code, diagrams — served from the Gateway's canvas file system.

**Channel** — A messaging platform integration (Discord, Telegram, WhatsApp, Slack, etc.) that routes inbound messages to agents and delivers agent replies.

**ClawHub** — The OpenClaw package registry and CLI for discovering, installing, publishing, and syncing community skills (`openclaw hub search`, `openclaw hub install`).

**Compaction** — The process of summarizing and truncating a session's conversation history when it approaches the context window limit, flushing key facts to MEMORY.md first.

**Context** — Everything the model sees in a single inference call: system prompt, bootstrap files, injected skills, memory recall, tool definitions, and conversation history.

**Context Pruning** — A lighter alternative to full compaction; trims old assistant messages from the session (e.g., keeps last 3) based on a `cache-ttl` or message-count rule, without full summarization.

**Cron** — Scheduled automation jobs defined in `gateway.yaml` that fire on a time schedule (cron expression or `@interval`) and deliver a message to an agent session.

**DM Policy** — Per-channel config that controls whether the agent responds to direct messages, and whether users must be paired/whitelisted first (`dmPolicy: open | paired | whitelist`).

**Gateway** — The central OpenClaw server process that manages WebSocket connections from channels, nodes, and operators; routes messages to agents; and runs the AI inference loop.

**Group Policy** — Per-channel config that controls whether the agent responds in group chats and whether it requires an @mention (`groupPolicy: off | mention | all`).

**Heartbeat** — A scheduled self-message sent to an agent on a timer (separate from cron) to trigger proactive behavior, memory checks, or status updates without external input.

**Hook** — A lifecycle event handler (defined via `HOOK.md` frontmatter) that fires on Gateway events like `session.start`, `message.before`, or `message.after`.

**IDENTITY.md** — Bootstrap file that defines who the agent is — name, backstory, personality, and behavioral guidelines — injected into the system prompt.

**Memory** — Persistent facts about users, sessions, or the world written by the agent to dated Markdown files and MEMORY.md, recalled at session start via vector or keyword search.

**MEMORY.md** — The agent's running long-term memory file, appended during compaction and recalled at session start to give the agent persistent context across sessions.

**Node** — A device (phone, desktop, headless host) connected to the Gateway that exposes hardware tools: camera, screen recording, exec, location, SMS.

**Operator** — A Gateway client role with elevated privileges (vs. `agent` or `user`); can send admin commands, inspect sessions, and call privileged RPC methods.

**Pairing** — The authentication handshake where a device (Node or channel) exchanges a token with the Gateway to establish a trusted identity before receiving messages.

**Pi Agent** — The informal name for the Clawdbot/OpenClaw voice agent persona used in the ai-eyes project; the "local free" mode vs. the Hume EVI DJ-FoamBot mode.

**Provider** — A configured AI model backend (Anthropic, Z.AI, OpenAI, Groq, Gemini, etc.) with its API key, base URL, and model name defined in `gateway.yaml`.

**RPC** — Remote Procedure Call; the request/response message format used over the Gateway WebSocket wire protocol (e.g., `chat.send`, `session.get`, `agent.list`).

**Sandbox** — The exec tool security layer that restricts which shell commands an agent can run, optionally requiring user approval before execution.

**Session** — A named conversation context identified by a `session_key` string; stores message history, compaction state, and memory for one agent-user interaction thread.

**Skill** — A self-contained plugin (Markdown + optional code) installed from ClawHub or locally that adds instructions, tools, prompts, or config overrides to an agent.

**SOUL.md** — Bootstrap file containing the agent's core values, ethical guidelines, and behavioral boundaries — the deepest layer of agent identity.

**Tool** — A callable function exposed to the agent during inference (file read, exec, web fetch, camera, etc.), defined in tool groups and gated by sandbox/policy rules.

**TOOLS.md** — Bootstrap file injected into the system prompt that documents all available tools and how the agent should use them.

**USER.md** — Bootstrap file containing information about the current user — preferences, context, and relationship history — injected to personalize agent behavior.

**Webhook** — An inbound HTTP endpoint on the Gateway that accepts external POST events (e.g., GitHub, Gmail Pub/Sub) and routes them as messages to an agent session.

**Workspace** — The directory on disk where an agent's files live — bootstrap Markdown files, memory logs, skill overrides, session JSONL store, and config.
