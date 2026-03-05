# OpenClaw — Models & Providers Reference

---

## Model Selection Order

1. `agents.defaults.model.primary` (or `agents.defaults.model`)
2. `agents.defaults.model.fallbacks` (in order)
3. Provider auth profile rotation (within current provider, before advancing fallback)

- `agents.defaults.models` → **allowlist** (if set, blocks unlisted models: "Model is not allowed")
- `agents.defaults.imageModel` → used only when primary model can't accept images
- Per-agent override: `agents.list[].model`
- Model refs are `provider/model`, normalized to lowercase. `z.ai/*` → `zai/*`

---

## Core Config Keys

| Key | Purpose |
|-----|---------|
| `agents.defaults.model.primary` | Primary model ref |
| `agents.defaults.model.fallbacks` | Ordered fallback list |
| `agents.defaults.imageModel.primary` | Image-only fallback model |
| `agents.defaults.models` | Allowlist + aliases + per-model params |
| `models.providers` | Custom provider definitions |
| `models.mode` | `merge` (default) or `replace` for `models.json` |

### Per-model params (in `agents.defaults.models.<ref>`)

| Param | Values | Notes |
|-------|--------|-------|
| `alias` | string | Short name for `/model` picker |
| `params.cacheRetention` | `none` / `short` (5m) / `long` (1h) | Anthropic API only |
| `streaming` | `true` / `false` | Ollama disabled by default |
| `reasoning` | `true` / `false` | Thinking-capable model |

### Custom provider model definition fields

| Field | Default | Notes |
|-------|---------|-------|
| `id` | required | Model ID string |
| `name` | required | Display name |
| `reasoning` | `false` | Thinking/reasoning mode |
| `input` | `["text"]` | Also `"image"` |
| `contextWindow` | `200000` | Token context limit |
| `maxTokens` | `8192` | Max output tokens |
| `cost` | `{input:0,output:0,cacheRead:0,cacheWrite:0}` | Per-million pricing |

---

## Supported Providers (Full List)

| Provider | Notes |
|----------|-------|
| `zai` | Z.AI / GLM — default for OpenClaw, prompt cache, binary thinking |
| `anthropic` | Claude API + Claude Code CLI integration |
| `openai` | API + Codex/Responses API support |
| `openrouter` | Multi-model gateway (access 100+ models) |
| `litellm` | Unified proxy across providers |
| `ollama` | Local model execution (streaming off by default) |
| `vllm` | Local model serving framework |
| `lmstudio` | Local LM Studio server (OpenAI-compatible, port 1234) |
| `bedrock` | Amazon Bedrock managed service |
| `mistral` | Mistral AI models |
| `moonshot` | Kimi + Kimi Coding models |
| `minimax` | MiniMax M2.1 — recommended for local/hybrid setups |
| `glm` | GLM models (Chinese LLMs) |
| `qianfan` | Baidu Qianfan platform |
| `huggingface` | Hugging Face inference hosting |
| `together` | Together AI collaborative inference |
| `opencode` | OpenCode Zen (coding-focused) |
| `vercel` | Vercel AI Gateway |
| `cloudflare` | Cloudflare AI Gateway (edge routing) |
| `venice` | Venice AI (privacy-first inference) |
| `nvidia` | NVIDIA GPU-accelerated inference |
| `xiaomi` | Xiaomi AI service |
| `qwen` | Qwen models (OAuth auth) |
| `deepgram` | Audio transcription (not LLM) |
| `synthetic` | Synthetic/test model provider |
| `claude-max-proxy` | Subscription-to-API bridge for Claude Max |

---

## CLI Commands

```bash
openclaw onboard [--auth-choice <choice>]
openclaw models list [--all] [--local] [--provider <name>] [--plain] [--json]
openclaw models status [--plain] [--json] [--check]   # --check exits 1=missing/expired, 2=expiring
openclaw models set <provider/model>
openclaw models set-image <provider/model>
openclaw models aliases list/add <alias> <ref>/remove <alias>
openclaw models fallbacks list/add <ref>/remove <ref>/clear
openclaw models image-fallbacks list/add/remove/clear
openclaw models auth login --provider <id>
openclaw models auth login-github-copilot [--profile-id <id>] [--yes]
openclaw models auth setup-token --provider anthropic
openclaw models auth paste-token --provider anthropic
openclaw models scan [--no-probe] [--min-params <b>] [--max-age-days <n>]
                     [--provider <name>] [--max-candidates <n>] [--set-default]
```

### In-chat: `/model [list | <#> | <provider/model> | status | <alias>@<profileId>]`

---

## Auth Failover & Cooldowns

**Flow:** Profile rotation within provider → if all exhausted → next model in fallbacks

**Profile selection order:** `auth.order[provider]` → `auth.profiles` config → stored profiles. OAuth before API keys; oldest `lastUsed` first; cooldown/disabled last.

**Session stickiness:** Profile pinned per session (not rotated per request). Resets on `/new`, `/reset`, compaction, or cooldown. User-pinned (`/model ...@profileId`) stays locked; failure skips to next fallback model.

**Cooldowns (rate-limit / auth errors):** 1m → 5m → 25m → 1h (cap)

**Billing disables:** 5h → doubles per failure → 24h cap; resets after 24h clean.
Config: `auth.cooldowns.billingBackoffHours`, `auth.cooldowns.billingMaxHours`, `auth.cooldowns.failureWindowHours`

**Auth storage:**
- Secrets: `~/.openclaw/agents/<agentId>/agent/auth-profiles.json`
- Runtime cache: `~/.openclaw/agents/<agentId>/agent/auth.json`

---

## Providers — Quick Reference

| Provider | Env Key | Provider ID | Auth Type | API Style |
|----------|---------|-------------|-----------|-----------|
| Anthropic | `ANTHROPIC_API_KEY` | `anthropic` | API key or setup-token | anthropic-messages |
| OpenAI | `OPENAI_API_KEY` | `openai` | API key | openai-completions |
| OpenAI Codex | — | `openai-codex` | OAuth (ChatGPT) | openai |
| OpenCode Zen | `OPENCODE_API_KEY` | `opencode` | API key | openai |
| Z.AI (GLM) | `ZAI_API_KEY` | `zai` | API key | openai-compatible |
| OpenRouter | `OPENROUTER_API_KEY` | `openrouter` | API key | openai-completions |
| xAI | `XAI_API_KEY` | `xai` | API key | — |
| Groq | `GROQ_API_KEY` | `groq` | API key | — |
| Mistral | `MISTRAL_API_KEY` | `mistral` | API key | — |
| Cerebras | `CEREBRAS_API_KEY` | `cerebras` | API key | OpenAI-compat |
| Google Gemini | `GEMINI_API_KEY` | `google` | API key | — |
| Google Vertex | — | `google-vertex` | gcloud ADC | — |
| Google Antigravity | — | `google-antigravity` | OAuth plugin | — |
| Google Gemini CLI | — | `google-gemini-cli` | OAuth plugin | — |
| GitHub Copilot | `COPILOT_GITHUB_TOKEN` / `GH_TOKEN` | `github-copilot` | Device OAuth | — |
| Amazon Bedrock | AWS env vars | `amazon-bedrock` | AWS SDK chain | bedrock-converse-stream |
| Vercel AI Gateway | `AI_GATEWAY_API_KEY` | `vercel-ai-gateway` | API key | anthropic-messages |
| Cloudflare AI Gateway | `CLOUDFLARE_AI_GATEWAY_API_KEY` | `cloudflare-ai-gateway` | API key | anthropic-messages |
| LiteLLM | `LITELLM_API_KEY` | `litellm` | API key | openai-completions |
| Moonshot (Kimi) | `MOONSHOT_API_KEY` | `moonshot` | API key | openai-completions |
| Kimi Coding | `KIMI_API_KEY` | `kimi-coding` | API key | anthropic-messages |
| MiniMax | `MINIMAX_API_KEY` | `minimax` | API key or OAuth plugin | anthropic-messages |
| Venice AI | `VENICE_API_KEY` | `venice` | API key | openai-completions |
| Synthetic | `SYNTHETIC_API_KEY` | `synthetic` | API key | anthropic-messages |
| Qwen | — | `qwen-portal` | OAuth plugin | — |
| Qianfan (Baidu) | — | `qianfan` | API key | openai-compatible |
| Xiaomi MiMo | `XIAOMI_API_KEY` | `xiaomi` | API key | anthropic-messages |
| Ollama | `OLLAMA_API_KEY` | `ollama` | None (local) | openai-completions |

---

## Provider Details

### Anthropic

```bash
openclaw onboard --anthropic-api-key "$ANTHROPIC_API_KEY"
# subscription: claude setup-token → openclaw models auth paste-token --provider anthropic
```

```json5
{
  env: { ANTHROPIC_API_KEY: "sk-ant-..." },
  agents: { defaults: { model: { primary: "anthropic/claude-opus-4-6" } } },
}
```

- Prompt caching (API key only): `cacheRetention: "short"` (5m, default) or `"long"` (1h)
- Includes `extended-cache-ttl-2025-04-11` beta flag automatically

**Troubleshooting:**
- `401 / token invalid` → re-run `claude setup-token` on gateway host; auth is **per-agent**
- `No credentials for profile anthropic:default` / `all in cooldown` → `openclaw models status [--json]`

---

### OpenAI

```json5
{ env: { OPENAI_API_KEY: "sk-..." }, agents: { defaults: { model: { primary: "openai/gpt-5.1-codex" } } } }
```

**Codex OAuth:** `openclaw onboard --auth-choice openai-codex`
```json5
{ agents: { defaults: { model: { primary: "openai-codex/gpt-5.3-codex" } } } }
```

---

### Z.AI / GLM

```json5
{ env: { ZAI_API_KEY: "sk-..." }, agents: { defaults: { model: { primary: "zai/glm-4.7" } } } }
```

- Aliases: `z.ai/*` and `z-ai/*` normalize to `zai/*`
- Models: `glm-4.7`, `glm-4.7-flash`, `glm-4.6`
- GLM on Cerebras: model IDs `zai-glm-4.7` / `zai-glm-4.6`, base URL `https://api.cerebras.ai/v1`
- GLM better for coding/tool calling; MiniMax better for writing

---

### Ollama (local)

```bash
export OLLAMA_API_KEY="ollama-local"   # any value; enables auto-discovery
ollama pull gpt-oss:20b
```

```json5
{
  agents: { defaults: { model: {
    primary: "ollama/gpt-oss:20b",
    fallbacks: ["ollama/llama3.3", "ollama/qwen2.5-coder:32b"]
  } } },
}
```

- Auto-discovers tool-capable models from `http://127.0.0.1:11434` (queries `/api/tags` + `/api/show`)
- Only models reporting `tools` capability included; `thinking` → `reasoning: true`
- **Streaming disabled by default** (known SDK issue with tool-capable models)
- Context window from Ollama metadata, else 8192; `maxTokens` = 10× context
- Setting `models.providers.ollama` explicitly disables auto-discovery

**Explicit config (remote host / manual models):**
```json5
{ models: { providers: { ollama: {
    baseUrl: "http://ollama-host:11434/v1", apiKey: "ollama-local",
    api: "openai-completions",
    models: [{ id: "gpt-oss:20b", contextWindow: 8192, maxTokens: 81920 }]
} } } }
```

- Not detected → check `OLLAMA_API_KEY` set, no explicit provider entry, `ollama serve` running
- No models listed → only tool-capable auto-discovered; add explicit entry or pull tool-capable model
- Corrupted output → streaming issue; remove `streaming: true` (streaming off is default)

---

### OpenRouter

```json5
{
  env: { OPENROUTER_API_KEY: "sk-or-..." },
  agents: { defaults: { model: { primary: "openrouter/anthropic/claude-sonnet-4-5" } } },
}
```

- Model refs: `openrouter/<provider>/<model>`
- Free model scan: `openclaw models scan` — ranks by image support → tool latency → context → params

---

### MiniMax

```bash
# OAuth (Coding Plan — recommended):
openclaw plugins enable minimax-portal-auth && openclaw gateway restart
openclaw onboard --auth-choice minimax-portal
```

**API key:**
```json5
{
  env: { MINIMAX_API_KEY: "sk-..." },
  agents: { defaults: { model: { primary: "minimax/MiniMax-M2.1" } } },
  models: { mode: "merge", providers: { minimax: {
    baseUrl: "https://api.minimax.io/anthropic",
    apiKey: "${MINIMAX_API_KEY}", api: "anthropic-messages",
    models: [{ id: "MiniMax-M2.1", contextWindow: 200000, maxTokens: 8192,
               cost: { input: 15, output: 60, cacheRead: 2, cacheWrite: 10 } }],
  } } },
}
```

- Model IDs **case-sensitive**: `minimax/MiniMax-M2.1`, `minimax/MiniMax-M2.1-lightning`
- M2.1 Lightning auto-routed by MiniMax (not directly selectable)
- CN: `api.minimaxi.com`; Global: `api.minimax.io`
- **Troubleshooting "Unknown model"** → upgrade to 2026.1.12+ or add `models.providers.minimax` manually
---

### Venice AI

```json5
{
  env: { VENICE_API_KEY: "vapi_..." },
  agents: { defaults: { model: { primary: "venice/llama-3.3-70b" } } },
}
```

- **Private** — no logging/ephemeral (Llama, Qwen, DeepSeek, GLM, etc.)
- **Anonymized** — metadata-stripped proxy (Claude, GPT, Gemini, Grok, Kimi, etc.)

| Use Case | Model | Context |
|----------|-------|---------|
| Default private | `venice/llama-3.3-70b` | 131k |
| Best quality | `venice/claude-opus-45` | 202k |
| Coding | `venice/qwen3-coder-480b-a35b-instruct` | 262k |
| Uncensored | `venice/venice-uncensored` | 32k |

- Models auto-discovered from Venice API. Anonymized adds ~10–50ms proxy latency.
---

### Amazon Bedrock

```bash
export AWS_ACCESS_KEY_ID="AKIA..." AWS_SECRET_ACCESS_KEY="..." AWS_REGION="us-east-1"
```

```json5
{
  models: { providers: { "amazon-bedrock": {
    baseUrl: "https://bedrock-runtime.us-east-1.amazonaws.com",
    api: "bedrock-converse-stream", auth: "aws-sdk",
    models: [{ id: "us.anthropic.claude-opus-4-6-v1:0",
               reasoning: true, input: ["text","image"],
               contextWindow: 200000, maxTokens: 8192 }],
  } } },
  agents: { defaults: { model: { primary: "amazon-bedrock/us.anthropic.claude-opus-4-6-v1:0" } } },
}
```

**Auto-discovery** (enabled by default when AWS creds present):
```json5
{ models: { bedrockDiscovery: { enabled: true, region: "us-east-1",
    providerFilter: ["anthropic","amazon"], refreshInterval: 3600,
    defaultContextWindow: 32000, defaultMaxTokens: 4096 } } }
```

- Auth chain: `AWS_BEARER_TOKEN_BEDROCK` → `AWS_ACCESS_KEY_ID`+secret → `AWS_PROFILE` → SDK default
- EC2 IMDS workaround: set `AWS_PROFILE=default` to trigger detection (actual auth still via IMDS)
- Required IAM: `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`, `bedrock:ListFoundationModels`

---

### Moonshot AI (Kimi)

```json5
{
  env: { MOONSHOT_API_KEY: "sk-..." },
  agents: { defaults: { model: { primary: "moonshot/kimi-k2.5" } } },
  models: { mode: "merge", providers: { moonshot: {
    baseUrl: "https://api.moonshot.ai/v1", apiKey: "${MOONSHOT_API_KEY}",
    api: "openai-completions",
    models: [  // all 256k ctx, 8192 maxTokens
      { id: "kimi-k2.5", reasoning: false },
      { id: "kimi-k2-0905-preview", reasoning: false },
      { id: "kimi-k2-turbo-preview", reasoning: false },
      { id: "kimi-k2-thinking", reasoning: true },
      { id: "kimi-k2-thinking-turbo", reasoning: true },
    ],
  } } },
}
```

- China endpoint: `https://api.moonshot.cn/v1` | **Kimi Coding** = separate provider: key `KIMI_API_KEY`, ref `kimi-coding/k2p5`, anthropic-messages API

---

### Synthetic

```json5
{
  env: { SYNTHETIC_API_KEY: "sk-..." },
  agents: { defaults: { model: { primary: "synthetic/hf:MiniMaxAI/MiniMax-M2.1" } } },
  models: { mode: "merge", providers: { synthetic: {
    baseUrl: "https://api.synthetic.new/anthropic",
    apiKey: "${SYNTHETIC_API_KEY}", api: "anthropic-messages",
    models: [{ id: "hf:MiniMaxAI/MiniMax-M2.1", contextWindow: 192000, maxTokens: 65536 }],
  } } },
}
```

Note: OpenClaw appends `/v1`; use base URL without `/v1`.

Selected Synthetic models (all cost $0):

| Model ID | Context | Reasoning |
|----------|---------|-----------|
| `hf:MiniMaxAI/MiniMax-M2.1` | 192k | — |
| `hf:zai-org/GLM-4.7` | 198k | — |
| `hf:moonshotai/Kimi-K2-Thinking` | 256k | ✓ |
| `hf:Qwen/Qwen3-Coder-480B-A35B-Instruct` | 256k | — |
| `hf:Qwen/Qwen3-VL-235B-A22B-Instruct` | 250k | — (vision) |
| `hf:meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` | 524k | — |
| `hf:Qwen/Qwen3-235B-A22B-Thinking-2507` | 256k | ✓ |

---

### LiteLLM Proxy

```json5
{
  models: { providers: { litellm: {
    baseUrl: "http://localhost:4000", apiKey: "${LITELLM_API_KEY}",
    api: "openai-completions",
    models: [{ id: "claude-opus-4-6", reasoning: true, input: ["text","image"],
               contextWindow: 200000, maxTokens: 64000 }],
  } } },
  agents: { defaults: { model: { primary: "litellm/claude-opus-4-6" } } },
}
```

Virtual key: `POST http://localhost:4000/key/generate` with `{"key_alias":"openclaw","max_budget":50.00,"budget_duration":"monthly"}`

---

### Minor Providers

**GitHub Copilot** — interactive TTY required:
```bash
openclaw models auth login-github-copilot   # device flow
openclaw models set github-copilot/gpt-4o
# Also: copilot-proxy plugin (routes through VS Code Copilot Proxy extension)
```

**Qwen** — OAuth free tier (2k req/day):
```bash
openclaw plugins enable qwen-portal-auth
openclaw models auth login --provider qwen-portal --set-default
# models: qwen-portal/coder-model, qwen-portal/vision-model
```

**Vercel AI Gateway** (`AI_GATEWAY_API_KEY`, anthropic-messages):
```json5
{ agents: { defaults: { model: { primary: "vercel-ai-gateway/anthropic/claude-opus-4.6" } } } }
```

**Cloudflare AI Gateway** (`CLOUDFLARE_AI_GATEWAY_API_KEY`):
```json5
{
  agents: { defaults: { model: { primary: "cloudflare-ai-gateway/claude-sonnet-4-5" } } },
  models: { providers: { "cloudflare-ai-gateway": {
    headers: { "cf-aig-authorization": "Bearer <token>" }  // if Gateway auth enabled
  } } },
}
# baseUrl: https://gateway.ai.cloudflare.com/v1/<account_id>/<gateway_id>/anthropic
```

**OpenCode Zen** (`OPENCODE_API_KEY` or `OPENCODE_ZEN_API_KEY`, billed per request):
```json5
{ env: { OPENCODE_API_KEY: "sk-..." }, agents: { defaults: { model: { primary: "opencode/claude-opus-4-6" } } } }
```

**Xiaomi MiMo** (`XIAOMI_API_KEY`, anthropic-messages, 262k ctx):
```json5
{ env: { XIAOMI_API_KEY: "key" }, agents: { defaults: { model: { primary: "xiaomi/mimo-v2-flash" } } },
  models: { mode: "merge", providers: { xiaomi: {
    baseUrl: "https://api.xiaomimimo.com/anthropic", api: "anthropic-messages", apiKey: "XIAOMI_API_KEY",
    models: [{ id: "mimo-v2-flash", contextWindow: 262144, maxTokens: 8192 }],
  } } } }
```

**Qianfan (Baidu)** — key format `bce-v3/ALTAK-...`:
```bash
openclaw onboard --auth-choice qianfan-api-key
```

**Claude Max API Proxy** (community; wraps Claude Code CLI, uses Claude Max/Pro subscription):
```bash
npm install -g claude-max-api-proxy && claude-max-api   # http://localhost:3456
```
```json5
{ env: { OPENAI_API_KEY: "not-needed", OPENAI_BASE_URL: "http://localhost:3456/v1" },
  agents: { defaults: { model: { primary: "openai/claude-opus-4" } } } }
# Models: claude-opus-4, claude-sonnet-4, claude-haiku-4
```

---

## OAuth vs API Key

- **API key** — most providers; set env var, stored as `type: "api_key"` in `auth-profiles.json`
- **Setup-token** — `anthropic`; run `claude setup-token` → `openclaw models auth paste-token --provider anthropic`
- **OAuth PKCE** — `openai-codex`; `openclaw models auth login --provider openai-codex` (ChatGPT browser redirect)
- **OAuth plugin** — `google-antigravity`, `google-gemini-cli`, `minimax-portal`, `qwen-portal`; enable plugin → `openclaw models auth login --provider <id>`
- **AWS SDK** — `amazon-bedrock`; env vars / instance role / `AWS_PROFILE` chain
- Tokens auto-refresh; re-run login if refresh fails
- Multiple profiles: separate agents OR `auth.order[provider]` config + `/model ...@profileId`

---

## Fallback Config Examples

```json5
// Primary + fallback + allowlist with aliases
{
  agents: { defaults: {
    model: {
      primary: "anthropic/claude-opus-4-6",
      fallbacks: ["minimax/MiniMax-M2.1", "ollama/llama3.3"],
    },
    models: {
      "anthropic/claude-opus-4-6": { alias: "Opus" },
      "minimax/MiniMax-M2.1": { alias: "Minimax" },
    },
  } }
}
```

```json5
// Local proxy (LM Studio / vLLM / any OpenAI-compatible)
{
  agents: { defaults: {
    model: { primary: "lmstudio/minimax-m2.1-gs32" },
    models: { "lmstudio/minimax-m2.1-gs32": { alias: "Minimax" } },
  } },
  models: { providers: { lmstudio: {
    baseUrl: "http://localhost:1234/v1", apiKey: "LMSTUDIO_KEY",
    api: "openai-responses",
    models: [{ id: "minimax-m2.1-gs32", contextWindow: 196608, maxTokens: 8192 }],
  } } },
}
```

---

## Notes

- **GLM**: better for coding/tool calling | **MiniMax**: better for writing/vibes | **Opus**: strongest reasoning
- **Venice**: default `llama-3.3-70b` (private) / `claude-opus-45` (best quality via anonymized proxy)
- **OpenRouter scan** ranks free models: image → tool latency → context → params
- `openclaw models status --check` → exit `1` missing/expired, `2` expiring (CI-friendly)
