# OpenClaw Plugins (Extensions) Reference

Plugins are TypeScript modules that extend OpenClaw with extra tools, commands, channels, providers, and Gateway RPC methods. They run **in-process** with the Gateway — treat as trusted code.

---

## Quick Start

```bash
openclaw plugins list                    # see loaded plugins
openclaw plugins install @openclaw/voice-call   # install from npm
openclaw plugins enable voice-call       # enable it
# restart gateway
```

---

## Official Plugins

| Plugin | Package | Purpose |
|--------|---------|---------|
| Voice Call | `@openclaw/voice-call` | Telephony via Twilio |
| MS Teams | `@openclaw/msteams` | Teams channel (plugin-only since 2026.1.15) |
| Matrix | `@openclaw/matrix` | Matrix channel |
| Nostr | `@openclaw/nostr` | Nostr channel |
| Zalo | `@openclaw/zalo` | Zalo channel |
| Zalo Personal | `@openclaw/zalouser` | Zalo unofficial |
| Memory (Core) | bundled | Memory search (default via `plugins.slots.memory`) |
| Memory (LanceDB) | bundled | Long-term memory with auto-recall/capture |
| ACP (acpx) | bundled | ACP backend for coding harnesses |
| Lobster | bundled | Workflow runtime with approval gates |
| LLM Task | bundled | JSON-only LLM steps for workflows |
| Diffs | bundled | Diff viewer + PDF/PNG renderer |
| Google Antigravity OAuth | bundled | Google AI OAuth flow |
| Gemini CLI OAuth | bundled | Gemini CLI OAuth |
| Qwen OAuth | bundled | Qwen portal auth |
| Copilot Proxy | bundled | VS Code Copilot Proxy bridge |

---

## Plugin Capabilities

Plugins can register:
- **Agent tools** (exposed to the model)
- **CLI commands** (top-level `openclaw <cmd>`)
- **Gateway RPC methods**
- **Gateway HTTP handlers**
- **Background services**
- **Skills** (via `skills/` directories in manifest)
- **Auto-reply commands** (execute without AI agent)
- **Channel plugins** (full messaging channels)
- **Provider auth flows** (OAuth, API key, device code)
- **Hooks** (event-driven automation)

---

## Discovery & Precedence

Scanned in order (first match wins for duplicate ids):

1. `plugins.load.paths` (file or directory)
2. Workspace extensions: `<workspace>/.openclaw/extensions/*.ts` or `*/index.ts`
3. Global extensions: `~/.openclaw/extensions/*.ts` or `*/index.ts`
4. Bundled extensions: `<openclaw>/extensions/*`

### Safety Checks

- Entry resolving outside plugin root → blocked
- World-writable plugin root → blocked
- Suspicious ownership (non-uid, non-root) → blocked
- Non-bundled without install/load-path provenance → warning

---

## Config

```json5
{
  plugins: {
    enabled: true,                    // master toggle (default: true)
    allow: ["voice-call"],            // allowlist (optional)
    deny: ["untrusted-plugin"],       // denylist (deny wins)
    load: {
      paths: ["~/Projects/oss/my-plugin"],  // extra plugin paths
    },
    entries: {
      "voice-call": {
        enabled: true,
        config: { provider: "twilio" },
      },
    },
    slots: {
      memory: "memory-core",          // exclusive category selection ("none" to disable)
    },
  },
}
```

Changes require gateway restart. Unknown plugin ids in entries/allow/deny are **errors**.

---

## Plugin Slots (Exclusive Categories)

Some categories are exclusive (one active at a time):

```json5
{
  plugins: {
    slots: {
      memory: "memory-core",   // or "memory-lancedb" or "none"
    },
  },
}
```

---

## CLI Commands

```bash
openclaw plugins list
openclaw plugins info <id>
openclaw plugins install <path|npm-spec>
openclaw plugins install @openclaw/voice-call --pin   # pin exact version
openclaw plugins install -l ./my-plugin               # link for dev
openclaw plugins update <id>
openclaw plugins update --all
openclaw plugins enable <id>
openclaw plugins disable <id>
openclaw plugins doctor
```

npm installs: registry-only (package name + optional version/tag). Git/URL/file specs rejected.
Dependencies installed with `npm install --ignore-scripts` (no lifecycle scripts).

---

## Plugin SDK Import Paths

| Path | Use Case |
|------|----------|
| `openclaw/plugin-sdk/core` | Generic plugin APIs, provider auth types, shared helpers |
| `openclaw/plugin-sdk/compat` | Broader shared runtime helpers (bundled/internal plugins) |
| `openclaw/plugin-sdk/<channel>` | Channel-specific (telegram, discord, slack, signal, whatsapp, line, etc.) |
| `openclaw/plugin-sdk/<extension>` | Extension-specific (acpx, lobster, llm-task, diffs, etc.) |

---

## Authoring: Agent Tools

See `plugins/agent-tools` for the dedicated guide. Tools are registered with `api.registerTool(...)`.

## Authoring: Auto-Reply Commands

```ts
api.registerCommand({
  name: "mystatus",
  description: "Show plugin status",
  acceptsArgs: true,
  requireAuth: true,
  handler: (ctx) => ({ text: `Plugin running! Channel: ${ctx.channel}` }),
});
```

- Processed **before** built-in commands and AI agent
- Case-insensitive, global across channels
- Reserved names (help, status, reset, etc.) cannot be overridden

## Authoring: Channel Plugins

```ts
const plugin = {
  id: "acmechat",
  meta: { id: "acmechat", label: "AcmeChat", selectionLabel: "AcmeChat (API)",
          docsPath: "/channels/acmechat", blurb: "Demo.", aliases: ["acme"] },
  capabilities: { chatTypes: ["direct"] },
  config: {
    listAccountIds: (cfg) => Object.keys(cfg.channels?.acmechat?.accounts ?? {}),
    resolveAccount: (cfg, aid) => cfg.channels?.acmechat?.accounts?.[aid ?? "default"] ?? { accountId: aid },
  },
  outbound: { deliveryMode: "direct", sendText: async ({ text }) => ({ ok: true }) },
};
export default (api) => { api.registerChannel({ plugin }); };
```

Required adapters: `config.listAccountIds` + `config.resolveAccount`, `capabilities`, `outbound.deliveryMode` + `outbound.sendText`.
Optional: `setup`, `security`, `status`, `gateway`, `mentions`, `threading`, `streaming`, `actions`, `commands`.

### Channel Onboarding Hooks

- `configure(ctx)` — baseline setup flow
- `configureInteractive(ctx)` — fully own interactive setup
- `configureWhenConfigured(ctx)` — override for already-configured channels

## Authoring: Provider Auth

```ts
api.registerProvider({
  id: "acme", label: "AcmeAI",
  auth: [{
    id: "oauth", label: "OAuth", kind: "oauth",
    run: async (ctx) => ({
      profiles: [{ profileId: "acme:default", credential: { type: "oauth", provider: "acme", access: "...", refresh: "...", expires: Date.now() + 3600000 } }],
      defaultModel: "acme/opus-1",
    }),
  }],
});
```

## Authoring: Gateway RPC

```ts
api.registerGatewayMethod("myplugin.status", ({ respond }) => { respond(true, { ok: true }); });
```

## Authoring: CLI Commands

```ts
api.registerCli(({ program }) => {
  program.command("mycmd").action(() => console.log("Hello"));
}, { commands: ["mycmd"] });
```

## Authoring: Hooks

```ts
api.registerHook("command:new", async () => { /* ... */ },
  { name: "my-plugin.command-new", description: "Runs on /new" });
```

## Authoring: Background Services

```ts
api.registerService({ id: "my-service", start: () => api.logger.info("ready"), stop: () => api.logger.info("bye") });
```

---

## Runtime Helpers

### TTS (telephony)
```ts
const result = await api.runtime.tts.textToSpeechTelephony({ text: "Hello", cfg: api.config });
// Returns PCM audio buffer + sample rate
```

### STT (transcription)
```ts
const { text } = await api.runtime.stt.transcribeAudioFile({ filePath: "/tmp/audio.ogg", cfg: api.config, mime: "audio/ogg" });
```

---

## Package Packs

A directory with `package.json` containing `openclaw.extensions`:

```json
{ "name": "my-pack", "openclaw": { "extensions": ["./src/safety.ts", "./src/tools.ts"] } }
```

Each entry becomes a plugin. Multi-extension packs: id = `name/<fileBase>`.

---

## Distribution (npm)

- Plugins: separate packages under `@openclaw/*`
- `package.json` must include `openclaw.extensions` with entry files (.js or .ts)
- `openclaw plugins install <npm-spec>` → `npm pack` → extract to `~/.openclaw/extensions/<id>/`
- Scoped packages normalized to unscoped id for `plugins.entries.*`

---

## External Channel Catalogs

Drop JSON at: `~/.openclaw/mpm/plugins.json`, `~/.openclaw/mpm/catalog.json`, or `~/.openclaw/plugins/catalog.json`.
Or set `OPENCLAW_PLUGIN_CATALOG_PATHS` env var.

Format: `{ "entries": [{ "name": "@scope/pkg", "openclaw": { "channel": {...}, "install": {...} } }] }`
