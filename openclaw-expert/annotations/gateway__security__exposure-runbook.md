---
upstream: https://docs.openclaw.ai/gateway/security/exposure-runbook
relevance: jambot-critical
last-verified: 2026-07-25
audit_anchors: [17, 22, 23, 28]
related_pages: [gateway__multi-tenant-hosting, gateway__trusted-proxy-auth, gateway__authentication, gateway__security__audit-checks, tools__exec]
---

# Gateway exposure runbook — JamBot annotation

New page in the 2026-07-25 catalog rebuild. It is the closest thing upstream has to a checklist for what JamBot already does, and it surfaced a **command we run but were not using** plus a **correction to our own override**.

## The headline: `openclaw security audit` exists at our pin and we don't run it

```bash
sg docker -c "docker exec openclaw-<tenant> openclaw security audit"          # read-only
sg docker -c "docker exec openclaw-<tenant> openclaw security audit --deep"   # + live gateway probes
```

Verified present on `2026.5.7`. `--deep` adds live Gateway probes and plugin-owned collector checks. **`--fix` mutates** ("tighten defaults + chmod state/config") — do not run it against a tenant; it will happily "fix" the exact flags our deployment depends on.

This belongs in `jambot-health-monitor.sh` as a periodic non-mutating signal. It is not wired today.

## What it actually says about our fleet (live run, `test-dev`, 2026-07-25)

```
Summary: 1 critical · 2 warn · 1 info

CRITICAL  gateway.control_ui.device_auth_disabled
          gateway.controlUi.dangerouslyDisableDeviceAuth=true
WARN      gateway.control_ui.insecure_auth
          gateway.controlUi.allowInsecureAuth=true
WARN      config.insecure_or_dangerous_flags   (the same two flags)
INFO      tools.elevated: enabled · hooks.internal: enabled · browser control: enabled
          groups: open=0, allowlist=0
          trust model: personal assistant (one trusted operator boundary),
                       not hostile multi-tenant on one shared gateway
```

### ACCEPTED RISK — recorded, not ignored

Both findings are **known and deliberate**. `dangerouslyDisableDeviceAuth` is what stops every tenant session from sitting at `NOT_PAIRED` forever; `allowInsecureAuth` supports the Control UI behind our nginx TLS termination. The compensating controls are that the openclaw gateway port is **never published to the host** (OVU reaches it only across the per-tenant bridge at `ws://openclaw:18789`), nginx is the only public path, and Clerk gates the UI.

**This is an accepted-risk entry, and it should be re-examined — not re-accepted by default — during the 5.7→7.x upgrade**, because anchor #22 changes what a non-loopback bind is allowed to do without explicit auth.

### The correction it produced

The audit's own text: *"`allowInsecureAuth=true` does not bypass secure context or device identity checks; only `dangerouslyDisableDeviceAuth` disables Control UI device identity checks."*

`overrides/openclaw-json-deltas.md` described `allowInsecureAuth` as "bypasses control UI auth." That was wrong and is now corrected in place. The practical trap: anyone trying to reduce risk by dropping `dangerouslyDisableDeviceAuth` while keeping `allowInsecureAuth` gets `NOT_PAIRED` sessions — they kept the flag that was never doing that job.

## Where JamBot sits on the exposure ladder

Upstream's table, mapped to us:

| Upstream pattern | JamBot |
|---|---|
| Loopback + SSH tunnel | ❌ |
| Loopback + Tailscale Serve | ❌ (used elsewhere in the mesh, not for tenant gateways) |
| Tailnet/LAN bind | ❌ |
| **Trusted reverse proxy** | ✅ **this is us** — nginx in front, `trustedProxies` on Docker bridge CIDRs |
| Public internet | ❌ — and the gateway port is not host-published, so there is no direct route |

Upstream's required controls for our row: *"`trusted-proxy` auth, strict `trustedProxies`, header overwrite/strip rules, explicit allowed users."* We satisfy the first two. **Header strip/overwrite rules and `gateway.auth.trustedProxy.allowUsers` are worth auditing per tenant** — both keys exist at our pin (verified in the 5.7 schema).

## The bits that do NOT apply — and why saying so matters

Upstream's "minimum safe baseline" recommends `tools.exec: { security: "deny", ask: "always" }` and `tools.profile: "messaging"`. **JamBot deliberately does not run that**, because our tenant agents are owner-facing operators that need exec, not a semi-public messaging bot. Anchor #13 already records that upstream's own defaults flipped to `security: "full", ask: "off"` for the gateway/node host in v4.5.

Do not "harden" a tenant toward this baseline without understanding it removes the agent's ability to work. The baseline is written for the case where *untrusted people can DM the bot* — which is explicitly not the JamBot model (agents are owner-facing, never customer-facing).

## Applicable regardless

- **`session.dmScope`** — upstream is emphatic that multiple DM senders must not share context. Any future tenant channel exposure needs `per-channel-peer`.
- **"Pairing approves the sender to trigger the bot. It does not make that sender a separate host security boundary."** — same doctrine as anchor #28. Worth quoting back at any request to "just let the customer text the agent."
- **Rollback plan** — the page ships a concrete config rollback and credential-rotation order. Cheaper to copy from here than to invent mid-incident.

## Open item for the host

`openclaw security audit` is unwired. Adding it to `jambot-health-monitor.sh` (read-only, per tenant, alert on new CRITICAL ids rather than on the two we've accepted) is a real monitoring gap — "every system needs monitoring," and this one ships with the binary.
