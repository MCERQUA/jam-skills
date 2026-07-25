---
anchor: 28
slug: openclaw-fleet-first-party-multi-tenant
status: confirmed
introduced: docs page present in the 2026-07-25 catalog (`gateway/multi-tenant-hosting`, `cli/fleet`); marked EXPERIMENTAL upstream
changelog_line: "n/a — surfaced by the 2026-07-25 catalog rebuild (464 -> 761 pages). Upstream page fetched and read in full."
upstream_pages:
  - https://docs.openclaw.ai/gateway/multi-tenant-hosting
  - https://docs.openclaw.ai/cli/fleet
  - https://docs.openclaw.ai/gateway/security
  - https://docs.openclaw.ai/install/docker
old_behavior: "JamBot's overrides state that upstream docs do not describe our deployment model — one openclaw + one openvoiceui container per user, per-tenant bridge network, hand-rolled provisioning via jambot-create-user.sh."
new_behavior: "Upstream now ships `openclaw fleet` (EXPERIMENTAL) with a documented multi-tenant hosting model: one hardened 'cell' per tenant — full Gateway in its own container, own state tree, own credential, own user-defined bridge network, port 18789 inside published ONLY to 127.0.0.1:<allocated-port> on the host. Cells are recorded in the OpenClaw state database."
skill_files_affected:
  - overrides/multi-tenant-isolation.md
  - overrides/docker-deployment.md
  - playbooks/provision-new-tenant.md
sources:
  - cache/gateway__multi-tenant-hosting.md (fetched 2026-07-25)
---

# Anchor #28 — Upstream shipped a first-party multi-tenant model (`openclaw fleet`)

## Why this is an anchor

Our `overrides/` layer has said, for its whole life, that upstream docs describe a single-operator gateway and say nothing about our per-tenant deployment. **That claim is now stale.** `gateway/multi-tenant-hosting` documents a model that converges remarkably closely on what `jambot-create-user.sh` builds by hand — which means upstream prose about multi-tenancy is no longer safe to dismiss, and their security reasoning is now directly applicable to us.

## What upstream's model says (read this before designing anything multi-tenant)

- **The core doctrine:** *"OpenClaw's default security model is one trusted operator boundary per Gateway, not hostile multi-tenant isolation inside one shared Gateway."* Session IDs select routing; **they do not authorize one tenant against another.** Sandboxing reduces blast radius; it does not create a tenant authorization boundary. One complete instance per tenant is the only supported isolation.
- **A "cell"** = full Gateway in a hardened container: own state, credentials, workspace, channel accounts, token, and **loopback-only host port**.
- **Networking:** each cell on its own user-defined bridge; separate bridges prevent direct container-IP traffic between cells while keeping outbound NAT. Gateway listens on `18789` inside; runtime publishes it **only to `127.0.0.1:<allocated-port>`**. Reverse proxy / SSH tunnel / tailnet in front when remote access is needed.
- **Egress:** unrestricted by default. Podman can use `--network internal`; Docker internal networks break the published port, so Fleet rejects that combination — enforce Docker egress with host firewall rules (`DOCKER-USER` chain).
- **State layout:** `<state-dir>/fleet/cells/<tenant>/` → `/home/node/.openclaw`; auth-profile encryption keys in a **separate** `<state-dir>/fleet/auth-profile-secrets/<tenant>/` → `/home/node/.config/openclaw`. The key is deliberately NOT nested under the ordinary state mount.
- **UID:** official image defaults to non-root `node`, UID 1000 — matches JamBot's `chown 1000:1000` rule for `/mnt/clients/<user>/openclaw/`.
- **Hardening baseline:** drops all Linux capabilities, `no-new-privileges`, PID/memory/CPU and optional writable-layer disk limits, per-cell networks, loopback-only publication.
- **Trust boundary, stated plainly:** the Fleet operator and host are trusted by every tenant; resistance to a compromised host is a **non-goal**. Gateway tokens and `--env` values are visible to a host admin via `docker inspect`.
- **EXPERIMENTAL:** commands, flags, and container profile can change between releases **without a deprecation window**. Tested on Linux and macOS; Windows untested.

## How JamBot compares (honest diff, not a migration order)

| Dimension | JamBot today | Upstream cell model |
|---|---|---|
| One gateway per tenant | ✅ `openclaw-<user>` | ✅ one cell per tenant |
| Per-tenant bridge network | ✅ `jambot-<user>` | ✅ per-cell user-defined bridge |
| Gateway port exposure | internal only — reached at `ws://openclaw:18789` from the tenant's OVU container on the shared bridge; not published to the host | published to `127.0.0.1:<port>`, proxied |
| State isolation | ✅ `/mnt/clients/<user>/openclaw/` | ✅ `<state-dir>/fleet/cells/<tenant>/` |
| Auth-profile keys split from state | ❌ same tree | ✅ separate mount |
| Capability drop / `no-new-privileges` | ❌ not set in our compose | ✅ baseline |
| Resource limits | ✅ (2GB/1.0 CPU openclaw, 3GB/0.5 OVU) | ✅ PID/mem/CPU/disk |
| Cross-tenant reachability | ⚠️ `jambot-shared` network joins every tenant's containers for supertonic TTS + Remotion | ✅ separate bridges, no shared app path |

Two gaps worth naming, neither an emergency:
1. **`jambot-shared`** is a deliberate cross-tenant network we attach every tenant to. Upstream's model explicitly avoids a shared data path between cells. This is a real, accepted trade for shared TTS/render services — but it should be an explicit, documented decision, not an accident. Anything new attached to `jambot-shared` widens it.
2. **`no-new-privileges` + capability drop** are cheap, additive hardening we do not currently set. Adding them to the per-tenant compose is a low-risk improvement — but it is a fleet-wide compose change and must be validated on `test-dev` first.

## What NOT to do

- **Do NOT migrate JamBot onto `openclaw fleet`.** It is EXPERIMENTAL with no deprecation window, it does not know about the OVU container that pairs with each openclaw container, and it would replace a working provisioning path (`jambot-create-user.sh`) that also does nginx, Clerk, ports, registry, and skills sync. That is the "rewrite a working system" trap.
- **Do read the upstream page before any multi-tenant security question.** Their doctrine paragraph — session IDs are routing, not authorization — is the correct answer to "can two tenants share a gateway?" and it now has an upstream citation.
