# OpenClaw HTTP APIs Reference

The Gateway exposes HTTP endpoints alongside its WebSocket server (same port, multiplexed).

---

## 1. OpenResponses API (`POST /v1/responses`)

OpenResponses-compatible endpoint. **Disabled by default.**

### Enable

```json5
{
  gateway: {
    http: {
      endpoints: {
        responses: { enabled: true },
      },
    },
  },
}
```

### Authentication

Bearer token: `Authorization: Bearer <token>`
- `gateway.auth.mode="token"` → use `gateway.auth.token` (or `OPENCLAW_GATEWAY_TOKEN`)
- `gateway.auth.mode="password"` → use `gateway.auth.password` (or `OPENCLAW_GATEWAY_PASSWORD`)
- Rate limited: `429` with `Retry-After` on too many auth failures

### Security

**Full operator-access surface** — valid token = owner/operator credential. Keep on loopback/tailnet/private ingress only.

### Agent Selection

| Method | Example |
|--------|---------|
| `model` field | `"openclaw:main"`, `"openclaw:beta"`, `"agent:main"` |
| Header | `x-openclaw-agent-id: main` |
| Session key | `x-openclaw-session-key: <key>` |

### Session Behavior

Stateless by default (new session per request). Include `user` string for stable session routing.

### Request Shape

```json
{
  "model": "openclaw:main",
  "input": "hi",
  "instructions": "Keep answers brief",
  "tools": [{ "type": "function", "function": { "name": "get_weather", "parameters": {...} } }],
  "tool_choice": "auto",
  "stream": true,
  "max_output_tokens": 1000,
  "user": "user-123"
}
```

`input` accepts: string or array of item objects.

### Item Types

| Type | Description |
|------|-------------|
| `message` | Roles: system, developer, user, assistant. System/developer → system prompt |
| `function_call_output` | Tool results: `{ type, call_id, output }` |
| `input_image` | Base64 or URL: jpeg, png, gif, webp (max 10MB) |
| `input_file` | Base64 or URL: text/plain, markdown, html, csv, json, pdf (max 5MB) |
| `reasoning` | Accepted for compat, ignored |
| `item_reference` | Accepted for compat, ignored |

### Client Tools

Provide `tools` array → model returns `function_call` output items → send `function_call_output` to continue.

### Streaming (SSE)

`stream: true` → `Content-Type: text/event-stream`

Events: `response.created`, `response.in_progress`, `response.output_item.added`, `response.content_part.added`, `response.output_text.delta`, `response.output_text.done`, `response.content_part.done`, `response.output_item.done`, `response.completed`, `response.failed`

Stream ends with `data: [DONE]`.

### File/Image Limits Config

```json5
{
  gateway: {
    http: {
      endpoints: {
        responses: {
          enabled: true,
          maxBodyBytes: 20000000,      // 20MB
          maxUrlParts: 8,
          files: {
            allowUrl: true,
            urlAllowlist: ["cdn.example.com", "*.assets.example.com"],
            allowedMimes: ["text/plain", "text/markdown", "text/html", "text/csv", "application/json", "application/pdf"],
            maxBytes: 5242880,          // 5MB
            maxChars: 200000,
            maxRedirects: 3,
            timeoutMs: 10000,
            pdf: { maxPages: 4, maxPixels: 4000000, minTextChars: 200 },
          },
          images: {
            allowUrl: true,
            urlAllowlist: ["images.example.com"],
            allowedMimes: ["image/jpeg", "image/png", "image/gif", "image/webp"],
            maxBytes: 10485760,         // 10MB
            maxRedirects: 3,
            timeoutMs: 10000,
          },
        },
      },
    },
  },
}
```

### Examples

```bash
# Non-streaming
curl -sS http://127.0.0.1:18789/v1/responses \
  -H 'Authorization: Bearer TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{ "model": "openclaw", "input": "hi" }'

# Streaming
curl -N http://127.0.0.1:18789/v1/responses \
  -H 'Authorization: Bearer TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{ "model": "openclaw", "stream": true, "input": "hi" }'
```

### Errors

`401` (auth), `400` (invalid body), `405` (wrong method). JSON: `{ "error": { "message": "...", "type": "invalid_request_error" } }`

---

## 2. Tools Invoke API (`POST /tools/invoke`)

Invoke a single tool directly without a full agent turn. **Always enabled**, gated by auth + tool policy.

### Request

```json
{
  "tool": "sessions_list",
  "action": "json",
  "args": {},
  "sessionKey": "main",
  "dryRun": false
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `tool` | Yes | Tool name to invoke |
| `action` | No | Mapped into args if tool schema supports `action` |
| `args` | No | Tool-specific arguments |
| `sessionKey` | No | Target session key (default: main) |
| `dryRun` | No | Reserved for future use |

### Tool Policy

Same policy chain as Gateway agents: profiles, allow/deny, per-agent overrides, group policies, subagent policy.

**Hard deny list** (blocked over HTTP even if session policy allows):
- `sessions_spawn`, `sessions_send`, `gateway`, `whatsapp_login`

Customize:
```json5
{
  gateway: {
    tools: {
      deny: ["browser"],       // additional blocks
      allow: ["gateway"],      // remove from default deny
    },
  },
}
```

Optional context headers:
- `x-openclaw-message-channel: <channel>` (e.g. `slack`)
- `x-openclaw-account-id: <accountId>`

### Responses

| Status | Meaning |
|--------|---------|
| `200` | `{ ok: true, result }` |
| `400` | `{ ok: false, error: { type, message } }` |
| `401` | Unauthorized |
| `404` | Tool not found or not allowed |
| `405` | Method not allowed |
| `429` | Rate limited (`Retry-After`) |
| `500` | Execution error (sanitized) |

Max payload: 2MB.

### Example

```bash
curl -sS http://127.0.0.1:18789/tools/invoke \
  -H 'Authorization: Bearer TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{ "tool": "sessions_list", "action": "json", "args": {} }'
```

---

## 3. OpenAI Chat Completions API (`POST /v1/chat/completions`)

OpenAI-compatible endpoint (documented in `gateway-advanced.md`). Disabled by default.

```json5
{
  gateway: {
    http: {
      endpoints: {
        chat: { enabled: true },
      },
    },
  },
}
```
