---
upstream: https://docs.openclaw.ai/gateway/trusted-proxy-auth.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: []
related_overrides: [openclaw-json-deltas.md, docker-deployment.md]
related_pages: [gateway__authentication, gateway__operator-scopes]
---

# Trusted proxy auth — JamBot annotation

## What docs say (TL;DR)

Mode `gateway.auth.mode = "trusted-proxy"` delegates auth to a reverse proxy that injects user identity via header. `trustedProxies` is the IP/CIDR allowlist. `userHeader` names the identity header. Optional `requiredHeaders`, `allowUsers`, `allowLoopback`. Cannot mix `gateway.auth.token` and trusted-proxy.

## JamBot's setup

JamBot uses **`trustedProxies` for the Docker bridge case**, with `dangerouslyDisableDeviceAuth: true` (see `overrides/openclaw-json-deltas.md`). Specifically:

```json5
{
  trustedProxies: ["172.0.0.0/8", "10.0.0.0/8"]
}
```

These CIDRs cover Docker default bridge subnets so the openvoiceui→openclaw WebSocket connection is trusted.

We do NOT use `gateway.auth.mode = "trusted-proxy"` in the formal sense — we use `dangerouslyDisableDeviceAuth: true` instead because:
- Each client container is single-tenant (one openvoiceui paired to one openclaw)
- nginx already TLS-terminates and gates per-domain at Cloudflare + Clerk
- The openclaw WebSocket is internal-only (not exposed to host)

## Available knobs (not currently used)

| Key | Purpose |
|-----|---------|
| `gateway.auth.mode = "trusted-proxy"` | Activate full mode |
| `gateway.auth.trustedProxy.userHeader` | Name of identity header (e.g. `x-pomerium-claim-email`) |
| `gateway.auth.trustedProxy.requiredHeaders` | Demand specific headers like `x-forwarded-proto` |
| `gateway.auth.trustedProxy.allowUsers` | Restrict to specific identities |
| `gateway.auth.trustedProxy.allowLoopback` | Allow `127.0.0.1` (default rejected) |
| `gateway.auth.password` | Password fallback for internal clients bypassing proxy |
| `x-openclaw-scopes` (header) | Caller-provided scope narrowing |

## v4.x security posture

- v5.2: `openclaw security audit` intentionally flags trusted-proxy with **critical severity** as a security reminder
- Header stripping rule: proxy MUST overwrite (not append) forwarded headers from clients
- Mixed-config rejection: simultaneous `auth.token` + trusted-proxy is rejected to prevent silent bypass

## Common-proxy header hints (from upstream)

- Pomerium: `x-pomerium-claim-email`
- nginx + oauth2-proxy: `x-auth-request-email`
- Caddy: `x-forwarded-user`

JamBot doesn't use any of these formally.

## Could we benefit from full trusted-proxy mode?

Multi-tenant CRM (`crm.jam-bot.com` + `<user>.crm.jam-bot.com`) → could route Clerk JWT identity into OpenClaw via header injection at nginx level. Currently the OpenVoiceUI Flask layer handles this. Migration to OpenClaw-native trusted-proxy would simplify the auth chain. **Not yet evaluated.**

## Related JamBot files

- `overrides/openclaw-json-deltas.md` — `trustedProxies` + `dangerouslyDisableDeviceAuth` setup
- `overrides/docker-deployment.md` — network topology
- `clerk-signup-config.md` (memory) — Clerk auth chain context
