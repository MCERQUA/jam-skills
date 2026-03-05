# OpenClaw Teaching Presentations — Template & Module Guide

> Agent instruction: Use this file to create HTML slide decks and show them on canvas.
> All 6 module outlines below contain real, accurate content — fill slides directly from these outlines.

---

## HOW TO USE THIS SYSTEM

### Step 1 — Choose a module
Pick one of the 6 modules below. Each has pre-written slide content.

### Step 2 — Generate the HTML
Copy the **HTML Template** (next section), replace every `<!-- SLIDE N CONTENT -->` block with the slides from the chosen module outline.

### Step 3 — Write the file to canvas folder
```bash
# Write the filled-in HTML to the canvas directory
write: ~/.openclaw/workspace/canvas/openclaw-<module-slug>.html
```

### Step 4 — Show it on canvas
```
canvas.present url="http://127.0.0.1:18793/__openclaw__/canvas/openclaw-<module-slug>.html"
```
Or use the canvas tool:
```json
{"action": "present", "url": "http://127.0.0.1:18793/__openclaw__/canvas/openclaw-<module-slug>.html"}
```

### Slide content rules
- Each `<div class="slide">` = one slide
- Use `<h2>` for slide title, `<ul>/<li>` for bullets
- Use `<pre><code>` for code blocks (already styled)
- Use `<table>` for tables (already styled)
- Total slides per module shown in outline header — add that many `<div class="slide">` blocks

---

## HTML TEMPLATE

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OpenClaw — [MODULE TITLE]</title>
<style>
  /* ── Reset & Base ── */
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #0a0a0a;
    color: #e0e0e0;
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 15px;
    line-height: 1.6;
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    user-select: none;
  }

  /* ── Progress Bar ── */
  #progress-bar {
    position: fixed;
    top: 0; left: 0;
    height: 3px;
    background: linear-gradient(90deg, #1a6cf6, #00d4ff);
    width: 0%;
    transition: width 0.35s cubic-bezier(.4,0,.2,1);
    z-index: 100;
    box-shadow: 0 0 8px #1a6cf688;
  }

  /* ── Header ── */
  #header {
    padding: 14px 28px 10px;
    border-bottom: 1px solid #1a1a2e;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
  }

  #module-label {
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #1a6cf6;
    font-weight: 600;
  }

  #slide-counter {
    font-size: 11px;
    color: #555;
    letter-spacing: 0.08em;
  }

  /* ── Slide Viewport ── */
  #viewport {
    flex: 1;
    overflow: hidden;
    position: relative;
  }

  .slides-container {
    display: flex;
    width: 100%;
    height: 100%;
    transition: transform 0.4s cubic-bezier(.4,0,.2,1);
  }

  /* ── Individual Slide ── */
  .slide {
    min-width: 100%;
    height: 100%;
    padding: 40px 52px 20px;
    overflow-y: auto;
    scroll-behavior: smooth;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .slide h2 {
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
    border-bottom: 1px solid #1a6cf630;
    padding-bottom: 10px;
    letter-spacing: 0.01em;
    flex-shrink: 0;
  }

  .slide h3 {
    font-size: 14px;
    font-weight: 600;
    color: #1a6cf6;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 4px;
  }

  /* ── Lists ── */
  .slide ul, .slide ol {
    padding-left: 22px;
    display: flex;
    flex-direction: column;
    gap: 7px;
  }

  .slide li {
    color: #c8cfe0;
    line-height: 1.55;
  }

  .slide li::marker { color: #1a6cf6; }

  .slide li strong { color: #ffffff; }

  .slide li code {
    background: #0f1929;
    color: #00d4ff;
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 13px;
    border: 1px solid #1a3060;
  }

  /* ── Code Blocks ── */
  pre {
    background: #080d16;
    border: 1px solid #1a2a45;
    border-left: 3px solid #1a6cf6;
    border-radius: 6px;
    padding: 16px 20px;
    overflow-x: auto;
    flex-shrink: 0;
  }

  pre code {
    color: #7ec8f7;
    font-size: 12.5px;
    line-height: 1.65;
    background: transparent;
    border: none;
    padding: 0;
  }

  /* ── Tables ── */
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    flex-shrink: 0;
  }

  th {
    background: #0d1a30;
    color: #1a6cf6;
    padding: 8px 12px;
    text-align: left;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border-bottom: 1px solid #1a3060;
  }

  td {
    padding: 7px 12px;
    color: #b8c4d8;
    border-bottom: 1px solid #111827;
  }

  td code {
    background: #0f1929;
    color: #00d4ff;
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 12px;
    border: 1px solid #1a3060;
  }

  tr:hover td { background: #0d1522; }

  /* ── Callout Box ── */
  .callout {
    background: #0d1a30;
    border: 1px solid #1a6cf640;
    border-left: 3px solid #1a6cf6;
    border-radius: 5px;
    padding: 12px 16px;
    font-size: 13px;
    color: #a0b4cc;
    flex-shrink: 0;
  }

  .callout.warn {
    border-left-color: #f59e0b;
    background: #1a130a;
    color: #c8a87a;
  }

  .callout.ok {
    border-left-color: #22c55e;
    background: #0a1a10;
    color: #7ec89a;
  }

  /* ── Navigation ── */
  #nav {
    padding: 14px 28px;
    border-top: 1px solid #111827;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
  }

  .nav-btn {
    background: #0d1a30;
    border: 1px solid #1a3060;
    color: #7ea8d8;
    padding: 9px 22px;
    border-radius: 5px;
    font-family: inherit;
    font-size: 12px;
    cursor: pointer;
    letter-spacing: 0.06em;
    transition: background 0.18s, border-color 0.18s, color 0.18s;
  }

  .nav-btn:hover:not(:disabled) {
    background: #1a2a50;
    border-color: #1a6cf6;
    color: #ffffff;
  }

  .nav-btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  #slide-dots {
    display: flex;
    gap: 7px;
    align-items: center;
  }

  .dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #1a2a45;
    cursor: pointer;
    transition: background 0.18s, transform 0.18s;
  }

  .dot.active {
    background: #1a6cf6;
    transform: scale(1.35);
  }

  #hint {
    font-size: 10px;
    color: #2a3a55;
    letter-spacing: 0.06em;
  }
</style>
</head>
<body>

<div id="progress-bar"></div>

<div id="header">
  <span id="module-label">OpenClaw · [MODULE TITLE]</span>
  <span id="slide-counter">1 / N</span>
</div>

<div id="viewport">
  <div class="slides-container" id="slides">

    <!-- ═══════════════════════════════════════
         REPLACE BELOW WITH SLIDE CONTENT
         Each <div class="slide"> = one slide
    ═══════════════════════════════════════ -->

    <div class="slide">
      <h2>Slide 1 Title</h2>
      <ul>
        <li>Bullet one — <strong>key term</strong></li>
        <li>Bullet two with inline <code>code</code></li>
      </ul>
      <pre><code># code block example
openclaw gateway status</code></pre>
    </div>

    <div class="slide">
      <h2>Slide 2 Title</h2>
      <table>
        <tr><th>Column A</th><th>Column B</th></tr>
        <tr><td>Value</td><td><code>example</code></td></tr>
      </table>
      <div class="callout">ℹ️ Callout note here</div>
      <div class="callout warn">⚠️ Warning callout</div>
      <div class="callout ok">✅ Success callout</div>
    </div>

    <!-- ADD MORE SLIDES HERE -->

  </div>
</div>

<div id="nav">
  <button class="nav-btn" id="prev-btn" onclick="prevSlide()">← Prev</button>
  <div id="slide-dots"></div>
  <span id="hint">← → arrow keys</span>
  <button class="nav-btn" id="next-btn" onclick="nextSlide()">Next →</button>
</div>

<script>
  const MODULE_TITLE = '[MODULE TITLE]';
  let current = 0;
  const slides = document.querySelectorAll('.slide');
  const total = slides.length;
  const container = document.getElementById('slides');
  const counter = document.getElementById('slide-counter');
  const progress = document.getElementById('progress-bar');
  const prevBtn = document.getElementById('prev-btn');
  const nextBtn = document.getElementById('next-btn');
  const dotsEl = document.getElementById('slide-dots');

  // Build dots
  slides.forEach((_, i) => {
    const d = document.createElement('div');
    d.className = 'dot' + (i === 0 ? ' active' : '');
    d.onclick = () => goTo(i);
    dotsEl.appendChild(d);
  });

  function goTo(n) {
    current = Math.max(0, Math.min(n, total - 1));
    container.style.transform = `translateX(-${current * 100}%)`;
    counter.textContent = `${current + 1} / ${total}`;
    progress.style.width = `${((current + 1) / total) * 100}%`;
    prevBtn.disabled = current === 0;
    nextBtn.disabled = current === total - 1;
    document.querySelectorAll('.dot').forEach((d, i) =>
      d.classList.toggle('active', i === current));
  }

  function nextSlide() { goTo(current + 1); }
  function prevSlide() { goTo(current - 1); }

  document.addEventListener('keydown', e => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') nextSlide();
    if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')   prevSlide();
    if (e.key === 'Home') goTo(0);
    if (e.key === 'End')  goTo(total - 1);
  });

  goTo(0);
</script>
</body>
</html>
```

---

## MODULE 1 — "What is OpenClaw?" (5 slides)

**File slug:** `openclaw-what-is-it`
**Module title string:** `What is OpenClaw?`

---

### Slide 1 — The Big Picture

**Title:** `What is OpenClaw?`

- **Personal AI assistant** you self-host on your own machine
- A single **Gateway** (Node.js daemon) is the control plane for ALL messaging channels
- One agent runtime connects to every chat app you already use
- Replies from one place — WhatsApp, Telegram, Discord, Slack, Signal, iMessage, and more
- Runtime requirement: **Node ≥ 22**

```
Your channels → Gateway → Agent → LLM (Anthropic / Z.AI / OpenAI / Ollama…)
```

---

### Slide 2 — Architecture in One View

**Title:** `Core Architecture`

```
WhatsApp / Telegram / Slack / Discord / Signal / iMessage
                  │
                  ▼
    ┌─────────────────────────────────┐
    │            GATEWAY              │
    │  Channels · Agent Runtime       │
    │  Sessions · Tools · Skills      │
    │  Memory / Workspace             │
    └─────────────────────────────────┘
                  │
          ├─ CLI (openclaw …)
          ├─ Control UI / WebChat
          ├─ macOS menu bar app
          └─ iOS / Android Nodes
```

**Key insight:** Gateway = single multiplexed port (WS + HTTP + Control UI + Webhooks)

---

### Slide 3 — Key Directories

**Title:** `Where Everything Lives`

| Path | Purpose |
|------|---------|
| `~/.openclaw/openclaw.json` | Main config file |
| `~/.openclaw/workspace/` | Agent workspace root |
| `~/.openclaw/workspace/AGENTS.md` | Agent instructions |
| `~/.openclaw/workspace/SOUL.md` | Agent personality |
| `~/.openclaw/workspace/skills/<name>/` | Workspace skills |
| `~/.openclaw/credentials/` | Channel credentials |
| `~/.openclaw/agents/<id>/sessions/` | Session transcripts |

---

### Slide 4 — Default Ports

**Title:** `Ports & Endpoints`

| Port | Purpose |
|------|---------|
| `18789` | Gateway (WS + HTTP + Control UI) |
| `18793` | Canvas host (agent-editable HTML) |
| `18791` | Clawdbot variant (non-default) |
| `19001` | Dev profile (`--dev` flag) |

- All traffic through port `18789` by default (loopback)
- Canvas files served from `/__openclaw__/canvas/`
- Control UI: `openclaw dashboard`

---

### Slide 5 — First 5 CLI Commands to Know

**Title:** `Essential CLI`

```bash
openclaw onboard           # Full setup wizard
openclaw gateway status    # Is the gateway running?
openclaw doctor            # Surface config problems
openclaw logs --follow     # Tail live logs
openclaw channels status --probe  # Check all channel connections
```

**Minimal config to get started:**
```json5
{
  agent: {
    model: "anthropic/claude-opus-4-6",
  },
}
```

Full docs: `https://docs.openclaw.ai`

---

## MODULE 2 — "The Gateway Deep Dive" (8 slides)

**File slug:** `openclaw-gateway`
**Module title string:** `The Gateway Deep Dive`

---

### Slide 1 — What the Gateway Actually Is

**Title:** `Gateway = Control Plane`

- Single **Node.js daemon** — one process owns everything
- Multiplexed port: WebSocket RPC + HTTP APIs + Control UI + Webhooks
- Default bind: `ws://127.0.0.1:18789` (loopback)
- One Gateway per host (recommended)
- Never exposes LLM calls directly — all traffic is WS JSON frames

---

### Slide 2 — The 3-Step Handshake

**Title:** `Connection Handshake (Protocol v3)`

**Step 1 — Gateway → Client (challenge):**
```json
{"type":"event","event":"connect.challenge",
 "payload":{"nonce":"...","ts":1737264000000}}
```

**Step 2 — Client → Gateway (connect request):**
```json
{"type":"req","id":"...","method":"connect",
 "params":{"minProtocol":3,"maxProtocol":3,
   "role":"operator","auth":{"token":"..."},
   "device":{"id":"fingerprint","publicKey":"...","signature":"..."}}}
```

**Step 3 — Gateway → Client (hello-ok):**
```json
{"type":"res","id":"...","ok":true,
 "payload":{"type":"hello-ok","protocol":3,
   "policy":{"tickIntervalMs":15000}}}
```

---

### Slide 3 — Wire Protocol Frame Types

**Title:** `3 Frame Types`

```json
// Request (client → gateway)
{"type":"req","id":"<uuid>","method":"chat.send","params":{}}

// Response (gateway → client)
{"type":"res","id":"<uuid>","ok":true,"payload":{}}
// or on error:
{"type":"res","id":"<uuid>","ok":false,"error":{}}

// Event (gateway → client, server-push)
{"type":"event","event":"agent","payload":{},"seq":0,"stateVersion":0}
```

- **First frame MUST be** `connect` or socket is closed hard
- Side-effecting methods require **idempotency keys**

---

### Slide 4 — Agent Streaming Event Flow

**Title:** `What Happens After chat.send`

| Event | Phase |
|-------|-------|
| `res` (accepted) | Immediate ack — `runId` returned |
| `agent` + `stream=lifecycle` + `phase=start` | Agent started |
| `agent` + `stream=assistant` | Streaming text (cumulative) |
| `chat` + `state=delta` | Context update during stream |
| `agent` + `stream=lifecycle` + `phase=end` | LLM done |
| `chat` + `state=final` | Full response — definitive |
| `tick` / `health` | Keepalive every ~15s |

**During tool use:** only `tick`/`health`/`presence` arrive. `chat.final` comes after ALL tools complete.

---

### Slide 5 — Bind Modes & Auth

**Title:** `Bind + Auth`

| Bind | Effect |
|------|--------|
| `loopback` | Default — local only |
| `lan` | `0.0.0.0` — requires auth |
| `tailnet` | Tailscale IP only |
| `custom` | Explicit address |

```json5
// Gateway auth config
{
  gateway: {
    bind: "loopback",
    auth: { mode: "token", token: "your-long-random-token" }
  }
}
```

Generate token: `openclaw doctor --generate-gateway-token`
**Non-loopback binds require auth — fail-closed by default.**

---

### Slide 6 — Roles: Operator vs Node

**Title:** `Two Client Roles`

| Role | Who | Scopes |
|------|-----|--------|
| `operator` | CLI, UI, scripts | `operator.read` / `write` / `admin` / `approvals` / `pairing` |
| `node` | iOS, macOS, Android | caps + commands + permissions declared at connect |

**Node caps example:** `["camera", "canvas", "screen", "location"]`
**Node commands example:** `["camera.snap", "canvas.navigate", "location.get"]`

- Non-local nodes must **sign** the challenge nonce
- Local (loopback/gateway tailnet IP) → auto-approval eligible

---

### Slide 7 — Node Pairing Flow

**Title:** `Pairing a Node Device`

1. Node connects → sends `node.pair.request`
2. Gateway stores pending → emits `node.pair.requested` to operators
3. Operator approves:
```bash
openclaw nodes pending
openclaw nodes approve <requestId>
```
4. Fresh device token issued → `hello-ok.auth.deviceToken`
5. Node reconnects with token on future connects
6. Pending requests **expire after 5 minutes**

State files: `~/.openclaw/nodes/paired.json`, `~/.openclaw/nodes/pending.json`

---

### Slide 8 — Gateway CLI Cheat Sheet

**Title:** `Gateway CLI Reference`

```bash
# Start / install
openclaw gateway --port 18789
openclaw gateway --force          # kill existing first
openclaw gateway install          # launchd / systemd service
openclaw gateway install --force  # replace existing service

# Status
openclaw gateway status
openclaw gateway status --deep
openclaw gateway status --json
openclaw health --json

# Operations
openclaw gateway restart
openclaw gateway stop
openclaw logs --follow
openclaw doctor

# Multiple instances
OPENCLAW_CONFIG_PATH=~/.openclaw/b.json OPENCLAW_STATE_DIR=~/.openclaw-b \
  openclaw gateway --port 19001
```

---

## MODULE 3 — "Building Skills" (6 slides)

**File slug:** `openclaw-skills`
**Module title string:** `Building Skills`

---

### Slide 1 — What is a Skill?

**Title:** `Skills = Agent Plugins`

- A folder with a `SKILL.md` file — that's it
- Injected into the agent's system prompt when eligible
- Can include scripts, config files, and instructions
- Three load locations (highest to lowest precedence):
  1. `<workspace>/skills/` — per-agent, private
  2. `~/.openclaw/skills/` — shared across all agents
  3. Bundled (shipped with install)
- Use `{baseDir}` placeholder to reference the skill folder path

---

### Slide 2 — SKILL.md Format

**Title:** `SKILL.md Structure`

```markdown
---
name: my-skill-name
description: One-line description shown in prompt and UI
user-invocable: true
metadata: {"openclaw": {"emoji": "🛠️", "requires": {"bins": ["uv"], "env": ["MY_API_KEY"]}, "primaryEnv": "MY_API_KEY"}}
---

# Skill Instructions

When the user asks to X, do Y.
Run the helper at `{baseDir}/scripts/run.sh`.
```

**Required:** `name`, `description`
**Optional:** `metadata`, `homepage`, `user-invocable`, `disable-model-invocation`, `command-dispatch`

---

### Slide 3 — Gating Rules

**Title:** `When Skills Load (Gating)`

| Gate | Type | Behavior |
|------|------|----------|
| `always: true` | bool | Skip all gates |
| `os` | array | `["darwin","linux","win32"]` |
| `requires.bins` | array | ALL must be on `PATH` |
| `requires.anyBins` | array | At least ONE on `PATH` |
| `requires.env` | array | All must exist in env |
| `requires.config` | array | Paths in `openclaw.json` must be truthy |

- Skills snapshot taken **when session starts** — changes apply on next session
- `load.watch: true` (default) → hot reload on `SKILL.md` change

---

### Slide 4 — Creating a Skill (Step by Step)

**Title:** `Create a Custom Skill`

```bash
# 1. Create directory
mkdir -p ~/.openclaw/workspace/skills/hello-world

# 2. Create SKILL.md
cat > ~/.openclaw/workspace/skills/hello-world/SKILL.md << 'EOF'
---
name: hello_world
description: A simple skill that says hello.
---

# Hello World Skill

When the user asks for a greeting, use exec to echo "Hello!"
EOF

# 3. Inspect / test
openclaw skills list
openclaw skills list --eligible
openclaw skills info hello_world
openclaw skills check
```

---

### Slide 5 — Token Impact & Config

**Title:** `Token Cost & Config`

**Token math:**
```
total_chars = 195 + Σ(97 + len(name) + len(description) + len(location))
rough_tokens ≈ total_chars / 4
```
- ~24 tokens per skill minimum (plus name/description length)
- Use `disable-model-invocation: true` for noisy skills (user slash command only)

**Config overrides:**
```json5
{
  skills: {
    load: { extraDirs: ["~/my-skill-pack/skills"], watch: true },
    entries: {
      "my-skill": { enabled: true, apiKey: "KEY_HERE",
                    env: { MY_API_KEY: "KEY_HERE" } }
    }
  }
}
```

---

### Slide 6 — ClawHub Registry

**Title:** `ClawHub — Public Registry`

```bash
npm i -g clawhub           # install CLI

clawhub login              # browser OAuth
clawhub search "postgres"  # search registry
clawhub install <slug>     # install to ./skills/
clawhub update --all       # update all installed
clawhub list               # list installed (reads .clawhub/lock.json)

# Publish your own
clawhub publish ./my-skill --slug my-skill \
  --name "My Skill" --version 1.0.0 \
  --changelog "Initial release" --tags latest
```

**Registry:** https://clawhub.ai
**Moderation:** GitHub account ≥ 1 week old required to publish. 3+ reports → auto-hidden.

---

## MODULE 4 — "Channel Integration" (7 slides)

**File slug:** `openclaw-channels`
**Module title string:** `Channel Integration`

---

### Slide 1 — Supported Channels

**Title:** `20+ Channels, One Gateway`

| Channel | Transport | Notes |
|---------|-----------|-------|
| WhatsApp | Baileys (WA Web) | QR pairing; dedicated number recommended |
| Telegram | grammY Bot API | Fastest setup — just a bot token |
| Discord | discord.js | Guilds + DMs + threads |
| Slack | Bolt SDK / Socket Mode | Workspace app |
| Signal | signal-cli JSON-RPC | Separate bot number required |
| BlueBubbles | REST + webhook | Recommended iMessage path |
| Matrix | matrix-bot-sdk | E2EE support; plugin install |
| Google Chat | HTTP webhook | Needs public URL; plugin |
| Microsoft Teams | Bot Framework | Azure Bot; plugin |

Channels run **simultaneously** — configure multiple, Gateway routes per chat.

---

### Slide 2 — DM Policies

**Title:** `Who Can DM Your Bot?`

| Policy | Behavior |
|--------|----------|
| `pairing` | **Default.** Unknown sender gets 8-char code; held until approved. 1hr expiry. Max 3 pending. |
| `allowlist` | Only senders in `allowFrom` — others silently dropped |
| `open` | All senders accepted (requires `allowFrom: ["*"]`) |
| `disabled` | All DMs blocked |

```bash
# Manage pairing
openclaw pairing list telegram
openclaw pairing approve telegram <CODE>
```

- Pairing allowlist stored: `~/.openclaw/credentials/<channel>-allowFrom.json`

---

### Slide 3 — Group Policies & Mention Gating

**Title:** `Group Access Control`

**Decision flow (evaluated in order):**
```
groupPolicy=disabled  → drop
groupPolicy=allowlist → group in list? no → drop
requireMention=yes    → mentioned? no → context only
otherwise             → reply
```

**Mention config:**
```json5
{
  channels: {
    telegram: { groups: { "*": { requireMention: true } } }
  },
  agents: {
    list: [{ id: "main", groupChat: {
      mentionPatterns: ["@?openclaw", "\\+?15555550123"],
      historyLimit: 50
    }}]
  }
}
```

---

### Slide 4 — Channel Routing to Agents

**Title:** `Routing Priority (6-Step)`

Priority order (first match wins):
1. **Exact peer match** — `bindings` with `peer.kind` + `peer.id`
2. **Guild match** — Discord `guildId`
3. **Team match** — Slack `teamId`
4. **Account match** — `accountId` on the channel
5. **Channel match** — any account on that channel type
6. **Default agent** — first list entry / `main`

```json5
{
  bindings: [
    { match: { channel: "slack", teamId: "T123" }, agentId: "support" },
    { match: { channel: "telegram", peer: { kind: "group", id: "-100123" } },
      agentId: "support" }
  ]
}
```

---

### Slide 5 — Session Keys by Context

**Title:** `Session Key Shapes`

| Context | Key Pattern |
|---------|------------|
| DM (default) | `agent:<agentId>:main` |
| WhatsApp group | `agent:<agentId>:whatsapp:group:<jid>` |
| Telegram group | `agent:<agentId>:telegram:group:<chatId>` |
| Telegram forum topic | `agent:<agentId>:telegram:group:<chatId>:topic:<threadId>` |
| Discord channel | `agent:<agentId>:discord:channel:<channelId>` |
| Discord thread | `agent:<agentId>:discord:channel:<channelId>:thread:<threadId>` |
| Slack channel | `agent:<agentId>:slack:channel:<channelId>` |

**Persistent session key = warm LLM cache = fast replies**

---

### Slide 6 — Text Chunking & Streaming

**Title:** `Message Limits & Streaming`

| Channel | Default Limit | Config Key |
|---------|--------------|------------|
| Telegram | 4000 chars | `channels.telegram.textChunkLimit` |
| Twitch | 500 chars | hardcoded (auto-chunked) |
| Zalo | 2000 chars | hardcoded |

**Telegram draft streaming:**
```json5
{
  channels: {
    telegram: {
      streamMode: "partial",  // off | partial | block
      draftChunk: { minChars: 200, maxChars: 800, breakPreference: "paragraph" }
    }
  }
}
```
- `partial` = default, frequent draft updates
- `block` = chunked drafts
- Draft streaming: **DM only** (not groups)

---

### Slide 7 — Channel Troubleshooting Ladder

**Title:** `Diagnosing Channel Issues`

**Run in this order:**
```bash
openclaw status
openclaw gateway status
openclaw logs --follow
openclaw doctor
openclaw channels status --probe
```

| Symptom | Check | Fix |
|---------|-------|-----|
| WhatsApp: no DM replies | `openclaw pairing list whatsapp` | Approve sender |
| Telegram: group silent | Check mention gating | Mention bot or `requireMention: false` |
| Discord: bot online, no replies | `openclaw channels status --probe` | Enable guild/channel, check message content intent |
| Slack: no responses | Check app + bot token scopes | Verify Socket Mode tokens |

---

## MODULE 5 — "Agent Internals" (8 slides)

**File slug:** `openclaw-agent-internals`
**Module title string:** `Agent Internals`

---

### Slide 1 — Agent Lifecycle (11 Steps)

**Title:** `What Happens on Every Message`

1. **Workspace resolution** — find agent workspace path
2. **Session resolution** — validate params, resolve sessionKey, return `runId` immediately
3. **Model selection** — primary → fallbacks → provider auth failover
4. **Skills snapshot** — workspace > managed > bundled
5. **Session write lock** — `SessionManager` opened
6. **System prompt build** — base + skills + bootstrap + per-run overrides
7. **Bootstrap injection** — workspace files injected (first turn only)
8. **Agent run** — `runEmbeddedPiAgent` serializes via queues, enforces timeout
9. **Tool execution loop** — tool start/update/end events streamed
10. **Reply shaping** — assemble text + tool summaries, filter `NO_REPLY`
11. **Completion** — `chat.final` emitted, JSONL transcript written

---

### Slide 2 — Workspace Files

**Title:** `Bootstrap Workspace Files`

| File | Loaded When |
|------|------------|
| `AGENTS.md` | Every session |
| `SOUL.md` | Every session |
| `USER.md` | Every session |
| `IDENTITY.md` | Every session |
| `TOOLS.md` | Every session |
| `HEARTBEAT.md` | Every session |
| `MEMORY.md` | Every session (when present) |
| `BOOT.md` | On gateway restart |
| `BOOTSTRAP.md` | First run only (delete after) |
| `memory/YYYY-MM-DD.md` | NOT auto-injected — `memory_search` only |

Max per file: `bootstrapMaxChars` default 20,000 chars

---

### Slide 3 — System Prompt Sections

**Title:** `System Prompt Assembly Order`

1. Tooling — tool list + descriptions
2. Safety — guardrail reminder
3. Skills — compact list with paths
4. OpenClaw Self-Update — `config.apply`/`update.run`
5. Workspace — working directory path
6. Documentation — local docs + public mirror
7. Workspace Files — bootstrap files follow
8. Sandbox — (when enabled) paths + elevated exec
9. Current Date & Time — timezone only (no clock, for cache stability)
10. Reply Tags — optional syntax
11. Heartbeats — prompt + ack behavior
12. Runtime — host/OS/node/model/thinking level

---

### Slide 4 — Built-in Tools (Core)

**Title:** `Core Built-in Tools`

| Tool | Description |
|------|-------------|
| `read` | Read files |
| `write` | Write files |
| `edit` | Edit files |
| `exec` | Shell commands — params: `command`, `timeout`, `background`, `elevated`, `host` |
| `process` | Manage background exec sessions — `list`/`poll`/`log`/`write`/`kill` |
| `web_search` | Brave Search (requires `BRAVE_API_KEY`) |
| `web_fetch` | HTML → markdown fetch |
| `browser` | Managed browser — `start`/`snapshot`/`act`/`screenshot`/`pdf` |
| `canvas` | Node canvas — `present`/`hide`/`navigate`/`eval`/`a2ui_push` |
| `nodes` | Paired device control — `camera_snap`/`screen_record`/`location_get` |
| `cron` | Gateway cron jobs — `add`/`remove`/`run`/`runs` |

---

### Slide 5 — Session Tools (Agent-to-Agent)

**Title:** `Session & Memory Tools`

| Tool | Purpose |
|------|---------|
| `sessions_list` | Discover active sessions |
| `sessions_history` | Fetch session transcript |
| `sessions_send` | Message another session |
| `sessions_spawn` | Spawn sub-agent (non-blocking) |
| `session_status` | Context window + model state |
| `memory_search` | Semantic search over MEMORY.md + daily logs |
| `memory_get` | Read specific memory file |

**Tool groups for policy:**
- `group:runtime` = `exec, bash, process`
- `group:fs` = `read, write, edit, apply_patch`
- `group:ui` = `browser, canvas`
- `group:automation` = `cron, gateway`

---

### Slide 6 — Context Window & Compaction

**Title:** `Context Management`

**Compaction** — triggered when session nears context window limit:
- Auto: default on — emits `🧹 Auto-compaction complete`
- Manual: `/compact [optional instructions]`
- Pre-compaction memory flush: writes durable memory before summarizing

**Session pruning** (Anthropic API only):
- Trims old tool results from in-memory context before LLM call
- Never modifies JSONL transcripts
- Protected: last 3 assistant messages + tool results after cutoff

```json5
{
  agent: {
    contextPruning: {
      mode: "cache-ttl",
      ttl: "30m",          // keep cache warm 30 min
      tools: { allow: ["exec", "read"] }
    }
  }
}
```

---

### Slide 7 — Queue Modes (Steering)

**Title:** `Message Queue Modes`

| Mode | Behavior |
|------|---------|
| `collect` | Coalesce queued messages into one followup (**default**) |
| `followup` | Hold until current turn ends, then new agent turn |
| `steer` | Inject after next tool boundary; skip remaining tools |
| `steer-backlog` | Steer now AND preserve for followup |
| `interrupt` | Abort active run, run newest message (legacy) |

```json5
{
  messages: {
    queue: { mode: "collect", debounceMs: 1000, cap: 20, drop: "summarize" }
  }
}
```

Chat override: `/queue steer debounce:2s cap:25` | `/queue default`

---

### Slide 8 — Model Selection & Switching

**Title:** `Model Configuration`

**Selection order:** primary → fallbacks → provider auth failover

```json5
{
  agent: {
    model: {
      primary: "anthropic/claude-opus-4-6",
      fallbacks: ["zai/glm-4.7-flash", "openai/gpt-5.2"]
    }
  }
}
```

**Model ref format:** `provider/model` (split on first `/`)

```bash
# CLI
openclaw models list
openclaw models status
openclaw models set anthropic/claude-opus-4-6
openclaw models aliases add sonnet anthropic/claude-sonnet-4-5

# Chat commands
/model            # numbered picker
/model 3          # select by number
/model openai/gpt-5.2
/model status
```

---

## MODULE 6 — "Security & Operations" (5 slides)

**File slug:** `openclaw-security`
**Module title string:** `Security & Operations`

---

### Slide 1 — 5 Trust Boundaries

**Title:** `Threat Model`

```
UNTRUSTED ZONE (channels: WhatsApp, Telegram, Discord…)
     ↓
TB1: Channel Access   — Device pairing, allowFrom, token auth
     ↓
TB2: Session Isolation — Session key = agent:channel:peer, tool policy per agent
     ↓
TB3: Tool Execution   — Docker sandbox OR host (exec approvals), SSRF blocking
     ↓
TB4: External Content — Fetched URLs wrapped in XML + security notice
     ↓
TB5: Supply Chain     — ClawHub: GitHub account age, pattern moderation
```

**Core philosophy:** Identity → Scope → Model (in that order). Start minimum access, widen carefully.

---

### Slide 2 — Exec Sandboxing (Docker)

**Title:** `Docker Sandbox Modes`

| `sandbox.mode` | Effect |
|---------------|--------|
| `"off"` | No sandbox — all tools on host |
| `"non-main"` | Sandbox non-main sessions (groups/channels) |
| `"all"` | Every session sandboxed |

| `sandbox.scope` | Containers |
|----------------|-----------|
| `"session"` | **Default.** One container per session |
| `"agent"` | One per agent |
| `"shared"` | Single shared |

| `workspaceAccess` | Effect |
|------------------|--------|
| `"none"` | **Default.** Isolated sandbox only |
| `"ro"` | Workspace mounted read-only at `/agent` |
| `"rw"` | Workspace mounted read/write at `/workspace` |

```bash
scripts/sandbox-setup.sh   # build default image
```

---

### Slide 3 — Tool Policy

**Title:** `Tool Allow/Deny Policy`

- `deny` **always wins** over `allow`
- Non-empty `allow` list = everything else blocked
- Tool policy = hard stop — no override possible

**Three access profile examples:**
```json5
// Personal — full access
{ agents: { list: [{ id: "personal", sandbox: { mode: "off" } }] } }

// Family — read-only
{
  agents: { list: [{ id: "family",
    sandbox: { mode: "all", workspaceAccess: "ro" },
    tools: { allow: ["read"],
             deny: ["write","edit","exec","browser"] } }] }
}

// Public — no filesystem
{
  agents: { list: [{ id: "public",
    sandbox: { mode: "all", workspaceAccess: "none" },
    tools: { allow: ["sessions_list","sessions_history","message"],
             deny: ["read","write","exec","browser","canvas"] } }] }
}
```

---

### Slide 4 — Security Audit & Secrets

**Title:** `Audit & Secrets Management`

```bash
# Run audit
openclaw security audit           # standard check
openclaw security audit --deep    # + live Gateway probe
openclaw security audit --fix     # apply safe guardrails auto

# Generate gateway token
openclaw doctor --generate-gateway-token

# Fix file permissions
chmod 700 ~/.openclaw
chmod 600 ~/.openclaw/openclaw.json
chmod 600 ~/.openclaw/credentials/*.json
```

**Log redaction:** `logging.redactSensitive: "tools"` (default — keep enabled)

**Secret scanning in CI:**
```bash
detect-secrets scan --baseline .secrets.baseline
detect-secrets audit .secrets.baseline
```

---

### Slide 5 — Incident Response Playbook

**Title:** `Incident Response (4 Steps)`

**Step 1 — Stop blast radius:**
- Disable elevated tools or stop Gateway
- `dmPolicy: "disabled"`, add mention gating, remove `"*"` allow-all

**Step 2 — Rotate secrets:**
- `gateway.auth.token` → restart
- Node pairings, model provider credentials, channel tokens, `hooks.token`

**Step 3 — Review artifacts:**
```bash
# Logs
/tmp/openclaw/openclaw-YYYY-MM-DD.log
~/.openclaw/agents/<id>/sessions/*.jsonl
# Check extensions/
ls ~/.openclaw/extensions/
```

**Step 4 — Re-audit:**
```bash
openclaw security audit --deep
```

Security contact: `security@openclaw.ai`
