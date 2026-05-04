---
upstream: https://docs.openclaw.ai/gateway/protocol.md
relevance: high
last-verified: 2026-05-04
audit_anchors: []
related_pages: [gateway__configuration, gateway__bridge-protocol, gateway__openai-http-api, gateway__tools-invoke-http-api]
---

# Gateway protocol — JamBot annotation

## What docs say (TL;DR)

WebSocket handshake (3-step), frame formats, RPC methods, event types, auth, node pairing. Default WS endpoint `ws://127.0.0.1:18789`. Clawdbot uses `18791`. Canvas host on `18793`.

## New v4.x RPC + events (audit doc §2.4-2.5)

### HTTP/RPC

| Surface | Introduced | Notes |
|---------|-----------|-------|
| `POST /tools/invoke` (plugin-backed catalog tools, e.g. `browser`) | v4.24 line 1856 | First-class tool invocation surface |
| `POST /tools/invoke` SDK-facing RPC w/ shared HTTP policy + typed approval/refusal | v5.2 line 41 | Refines v4.24 |
| `gateway.commands.list` RPC | v4.10 line 2748 | List available commands |
| `gateway.models.authStatus` RPC | v4.15 line 2443 | Provider auth status |
| `gateway.doctor.memory.remHarness` RPC | v4.29 line 416 | Read-only memory diagnostics |
| `gateway.proxy.validate` (CLI surface) | v5.2 line 33 | Proxy config validation |

### WS events

| Event | Introduced | Source |
|-------|-----------|--------|
| `node.presence.alive` | v4.27 line 763 | Node liveness pings |
| `spawnedBy` field on subagent chat + agent broadcast events | v4.29 line 412 | Provenance tracking |
| `compaction_start` / `compaction_end` (renamed) | v4.20 line 2395 | Was different name pre-4.20 |
| `before_agent_finalize` plugin hook | v4.25 line 1377 | Plugin-only |
| `model_call_started` / `model_call_ended` plugin hooks | v4.25 line 1405 | Telemetry only |
| `device.token.rotate` echo policy | v4.26 changed | Token rotation now echoes through specific path |

### OTEL spans (v4.25)

| Span | Source |
|------|--------|
| `openclaw.harness.run` | line 1382 |
| `openclaw.exec` | line 1421 |
| `gen_ai.client.token.usage` (GenAI metric) | line 1409 |

Opt-in via `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`.

## JamBot's protocol-level setup

JamBot connects openvoiceui→openclaw via internal Docker network: `ws://openclaw:18789`. Auth: `dangerouslyDisableDeviceAuth: true` + `trustedProxies` allows the WS upgrade through.

The `/tools/invoke` HTTP surface is potentially useful for the social-dashboard API (`api-social.jam-bot.com`) to invoke OpenClaw tools without going through chat — but currently social-dashboard has its own bridge layer.

## Bridge protocol (gateway-to-gateway)

v4.x added `bridge-protocol.md` for multi-gateway federation. Not currently used in JamBot — single-gateway-per-tenant.

## OpenAI HTTP API + OpenResponses API

`openai-http-api.md` and `openresponses-http-api.md` are first-class endpoints. JamBot doesn't expose these externally; they're internal-only behind the openvoiceui proxy.

v5.2 line 47: GPT-5 API-key sessions in fresh Control UI/WebChat default to OpenAI Responses transport.

## Related JamBot files

- `overrides/openclaw-json-deltas.md` — `dangerouslyDisableDeviceAuth` + `trustedProxies`
- `overrides/docker-deployment.md` — internal `ws://openclaw:18789`
- `annotations/gateway__configuration.md` — config side
