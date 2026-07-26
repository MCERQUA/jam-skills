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

> ## ✅ RESOLVED FOR JAMBOT — 2026-07-25, verified experimentally against a real 2026.7.1 binary
>
> **This anchor is NOT an upgrade blocker for us. It never was.** The original text below
> asserted that our template "leans on `allowInsecureAuth` + `dangerouslyDisableDeviceAuth`
> instead of a shared secret." **That is factually wrong**, and the error came from reading
> the changelog rather than the config.
>
> What is actually true (audited across **26/26 openclaw tenants**, 2026-07-25):
>
> - `gateway.auth.mode: "token"` with `token: "${OPENCLAW_GATEWAY_TOKEN}"` — **already set on every tenant**
> - every tenant has a **unique 64-char** token in its compose `.env`; no two tenants share one
> - `gateway.bind: "lan"` (the trigger condition) — yes, as described
> - `gateway.trustedProxies` present as well, so **both** accepted auth modes are configured
> - `allowInsecureAuth` / `dangerouslyDisableDeviceAuth` are scoped to **`gateway.controlUi.*`**,
>   NOT to gateway auth. They were never the thing standing in for a shared secret.
>
> **Experimental proof** (throwaway `node:22-slim` + `npm i -g openclaw@2026.7.1`, real
> test-dev config mounted read-only, originals untouched):
>
> | Test | Config | Result |
> |---|---|---|
> | Ours as-is | `bind: lan` + `auth.mode: token` + token in env | **gateway ran, exit 0** — no fail-closed |
> | `doctor --lint --all` | same | 51 checks; bind is a **warning**, not an error |
> | **Control** | `bind: lan`, `auth` and `trustedProxies` REMOVED | **`Refusing to bind gateway to lan without auth.`** |
>
> The control confirms the fail-closed behavior is real in 7.1 — and that our existing
> token config is what satisfies it. Upstream's own error text names the very env var we
> already use: *"Set `OPENCLAW_GATEWAY_TOKEN` or `OPENCLAW_GATEWAY_PASSWORD`"*.
>
> **Phase 0 decision: Option (B) per-tenant shared secret — ALREADY IMPLEMENTED. Ratify, do not build.**
> No OVU-side code change is required; OVU already carries the same token in its env.
>
> ### What this does NOT clear
> Config acceptance and gateway start only. Anchors **#23** (pairing), **#26B** (WS protocol v4 /
> the OVU client), **#24** (SQLite state vs our snapshots), **#26A** (cron scoping) and **#27**
> (Z.AI breaker) are untouched by this test and still gate the upgrade. #22 is off the list; the
> upgrade is not.
>
> ### One real finding this surfaced (new work, not a blocker)
> 7.1's `core/doctor/security` flags `gateway.auth.token` as a **plaintext secret-bearing config
> field** and wants it migrated to a SecretRef (`openclaw secrets configure` → verify with
> `openclaw secrets audit --check`). Worth doing on the upgrade, and it aligns with the
> per-role-secret direction already tracked in SUDO-QUEUE.

## The one-liner

**Original assessment (superseded by the block above — kept for provenance):** this was believed to be the single biggest upgrade blocker between JamBot's pinned `2026.5.7` and anything ≥ `2026.5.17`. Every JamBot openclaw container binds non-loopback by design (the OpenVoiceUI container reaches it at `ws://openclaw:18789` across the per-tenant bridge network). The claim that our template leans on `allowInsecureAuth: true` + `dangerouslyDisableDeviceAuth: true` instead of a shared secret **was incorrect** — see the resolution block.

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
