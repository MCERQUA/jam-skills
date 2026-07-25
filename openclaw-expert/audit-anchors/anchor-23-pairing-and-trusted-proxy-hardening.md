---
anchor: 23
slug: pairing-and-trusted-proxy-hardening
status: confirmed
introduced: v2026.5.12 (with follow-ups in 5.17 and 5.19)
changelog_line: "CHANGELOG.md 2026.5.12 — 'Require approval for setup-code device pairing [AI]. (#81292)' / 'Require explicit browser device pairing [AI]. (#81289)' / 'Require Control UI pairing before proxy-scoped access [AI]. (#81288)' / 'Harden trusted-proxy source validation [AI]. (#81290)' / 'Gateway/auth: make explicit trusted-proxy mode fail closed instead of accepting local password fallback credentials after trusted-proxy identity checks fail. Fixes #78684.'"
upstream_pages:
  - https://docs.openclaw.ai/gateway/trusted-proxy-auth
  - https://docs.openclaw.ai/gateway/pairing
  - https://docs.openclaw.ai/gateway/authentication
old_behavior: "Device pairing could be waved off wholesale with `dangerouslyDisableDeviceAuth: true`; trusted-proxy callers could fall back to local password credentials; setup-code and browser pairing did not require explicit approval."
new_behavior: "2026.5.12 requires approval for setup-code pairing, requires explicit browser device pairing, requires Control UI pairing before proxy-scoped access, and hardens trusted-proxy source validation. Explicit `trusted-proxy` mode now fails closed rather than accepting a local password fallback after an identity check fails. 5.19 partially relaxed this: same-host trusted-proxy callers may use the documented local direct `gateway.auth.password` fallback again (#82953), while token fallback stays rejected."
skill_files_affected:
  - overrides/openclaw-json-deltas.md
  - playbooks/upgrade-5.7-to-7.x.md
sources:
  - https://github.com/openclaw/openclaw/pull/81288
  - https://github.com/openclaw/openclaw/pull/81289
  - https://github.com/openclaw/openclaw/pull/81290
  - https://github.com/openclaw/openclaw/pull/81292
  - https://github.com/openclaw/openclaw/issues/78684
  - https://github.com/openclaw/openclaw/pull/82953
---

# Anchor #23 — Pairing + trusted-proxy hardening lands in the FIRST release after our pin (v2026.5.12)

## Why this anchor exists

JamBot pins `2026.5.7`. The very next release, `2026.5.12`, shipped a four-PR security batch that tightens exactly the two mechanisms our multi-tenant template disables or leans on:

- `dangerouslyDisableDeviceAuth: true` — our defense against permanent `NOT_PAIRED` sessions
- `trustedProxies: ["172.0.0.0/8","10.0.0.0/8"]` — how the OVU container's WS connection is accepted

Read this together with **anchor #22** (non-loopback fail-closed, 5.17). They are the same upgrade wall seen from two angles: 5.12 hardens *who* is allowed in, 5.17 hardens *whether the gateway starts at all*.

## The 5.12 batch, verbatim impact

| Change | JamBot surface it touches |
|---|---|
| Require approval for setup-code device pairing (#81292) | Any provisioning flow that pairs a new tenant non-interactively |
| Require explicit browser device pairing (#81289) | Control UI / dashboard access per tenant |
| Require Control UI pairing before proxy-scoped access (#81288) | Our nginx → gateway proxy path |
| Harden trusted-proxy source validation (#81290) | `trustedProxies` CIDR acceptance from the Docker bridge |
| Explicit `trusted-proxy` mode fails closed (#78684) | Removes the silent password-fallback safety net |

## The 5.17 / 5.19 follow-ups (do not skip these)

- **5.17** — "Gateway/pairing: reject forged loopback Control UI origins from non-local proxy paths." Our nginx terminates TLS and proxies to `127.0.0.1:<port>`; origins arriving that way are exactly the shape this check scrutinizes.
- **5.19** — "allow same-host trusted-proxy callers to use the documented local direct `gateway.auth.password` fallback after revisiting the #78684 fail-closed policy, while keeping token fallback rejected" (#82953). This is a *partial relaxation*: if you read only the 5.12 entry you will over-estimate how closed the door is on 5.19+.
- **5.19** — "CLI/doctor: seed Control UI allowed origins when migrating legacy non-loopback gateway bind host aliases like `0.0.0.0`" (#83286). Doctor will try to help here; see anchor #26 before letting it.

## JamBot rule

`dangerouslyDisableDeviceAuth: true` remains correct for our deployment and must stay in the template — but on ≥5.12 it can no longer be assumed to cover every pairing path. When a tenant on a newer image shows `NOT_PAIRED` or a Control UI that will not authorize, do NOT reach for another `dangerously*` flag. Check, in order:

1. Is the bind non-loopback without explicit auth? → anchor #22, not this one.
2. Does `trustedProxies` actually cover the source address the gateway sees (not the address you expect)? Source validation hardened in #81290.
3. Is this a Control-UI/browser path rather than the OVU WS path? Those now require explicit pairing regardless of the WS device-auth flag.

## Verification

```bash
sg docker -c "docker exec openclaw-<tenant> openclaw gateway status"
sg docker -c "docker logs --tail 200 openclaw-<tenant>" | grep -iE "pair|trusted|proxy|auth|fail"
```
