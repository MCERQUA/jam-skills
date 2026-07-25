---
anchor: 22
slug: gateway-fail-closed-non-loopback
status: confirmed
introduced: v2026.5.17
changelog_line: "CHANGELOG.md 2026.5.17 — 'Gateway/Docker: fail closed for non-loopback gateway starts without explicit shared-secret or trusted-proxy auth, and stop the image default command from bypassing config validation. Fixes #82865. (#82866)'"
upstream_pages:
  - https://docs.openclaw.ai/gateway/authentication
  - https://docs.openclaw.ai/gateway/security/exposure-runbook
  - https://docs.openclaw.ai/gateway/multi-tenant-hosting
  - https://docs.openclaw.ai/install/docker
old_behavior: "A gateway bound to a non-loopback address (0.0.0.0 inside a container) starts with `allowInsecureAuth: true` and no shared secret. The Docker image's default command bypasses config validation, so a config the validator would reject still boots."
new_behavior: "From 2026.5.17 the gateway FAILS CLOSED on a non-loopback bind unless explicit shared-secret OR trusted-proxy auth is configured, and the image default command no longer bypasses config validation."
skill_files_affected:
  - overrides/openclaw-json-deltas.md
  - overrides/docker-deployment.md
  - playbooks/upgrade-5.7-to-7.x.md
sources:
  - https://github.com/openclaw/openclaw/pull/82866
  - https://github.com/openclaw/openclaw/issues/82865
---

# Anchor #22 — Gateway fails closed on non-loopback bind without explicit auth (v2026.5.17)

## The one-liner

**This is the single biggest upgrade blocker between JamBot's pinned `2026.5.7` and anything ≥ `2026.5.17`.** Every JamBot openclaw container binds non-loopback by design (the OpenVoiceUI container reaches it at `ws://openclaw:18789` across the per-tenant bridge network). Our template leans on `allowInsecureAuth: true` + `dangerouslyDisableDeviceAuth: true` instead of a shared secret. On 2026.5.17+, that combination is exactly what now fails closed.

## Why JamBot is directly in the blast radius

From `/mnt/system/base/templates/openclaw.json`, the four load-bearing fields (see `overrides/openclaw-json-deltas.md`):

| Field | Purpose | Status after 5.17 |
|---|---|---|
| `trustedProxies: ["172.0.0.0/8","10.0.0.0/8"]` | accept Docker-network WS | **This is the survival path** — trusted-proxy auth is one of the two accepted modes |
| `allowInsecureAuth: true` | bypass control-UI auth | No longer sufficient on its own for a non-loopback bind |
| `dangerouslyDisableDeviceAuth: true` | kill WS device pairing (`NOT_PAIRED`) | Still needed, but see anchor #23 — the pairing paths hardened in 5.12 |
| `thinkingDefault: "off"` | Z.AI/GLM visible-text fix | Unaffected by this anchor |

The failure mode on upgrade is **not** a warning in the logs — it is a gateway that will not start, fleet-wide, on every tenant at once, the moment `jambot-build-images.sh` bakes a newer `OPENCLAW_VERSION`.

## What to do BEFORE bumping the version pin

1. **Decide the auth mode explicitly.** Two supported shapes:
   - **Trusted-proxy** (closest to what we already have): keep `trustedProxies` covering the Docker bridge ranges and make the mode explicit rather than implied. Note anchor #23 — 5.12 hardened trusted-proxy source validation and made explicit `trusted-proxy` mode fail closed rather than silently accepting a local password fallback.
   - **Shared secret**: give each tenant gateway a per-tenant secret and teach the OpenVoiceUI container to present it. This is the more durable option and matches the per-role-secret direction already tracked in the SUDO-QUEUE, but it is a code change on the OVU side, not a config flip.
2. **Validate on ONE tenant first** (`test-dev`), not a fleet roll. Bring the image up, confirm the gateway binds and OVU pairs, then roll.
3. **Config validation is no longer bypassed by the image default command.** A tenant config that boots today on 5.7 may be rejected outright. Run `openclaw config validate` (or `openclaw doctor --lint`, see anchor #26) inside a 7.x container against a copy of each tenant config before the roll.

## What NOT to do

- Do NOT bump `OPENCLAW_VERSION` via `bump-openclaw-version.sh` and roll the fleet in one step. This anchor makes that a fleet-wide outage, not a degraded state.
- Do NOT "fix" a fail-closed gateway by re-binding to loopback — the OVU container is a separate container and cannot reach a loopback-bound gateway. That is a regression, not a repair.
- Do NOT assume `allowInsecureAuth: true` still covers this. It covers control-UI auth, not the bind-mode gate.

## Verification

```bash
# Current pin (expect 2026.5.7 until the upgrade lands)
grep -n OPENCLAW_VERSION /mnt/system/base/OpenVoiceUI/deploy/openclaw/Dockerfile

# What a tenant is actually running
sg docker -c "docker exec openclaw-<tenant> openclaw --version"

# Bind + auth posture of a tenant config
python3 -c "import json;c=json.load(open('/mnt/clients/<tenant>/openclaw/openclaw.json'));print({k:c.get(k) for k in ('gateway','trustedProxies','allowInsecureAuth','dangerouslyDisableDeviceAuth')})"
```
