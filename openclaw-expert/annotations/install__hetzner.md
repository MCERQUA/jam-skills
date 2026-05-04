---
upstream: https://docs.openclaw.ai/install/hetzner.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: [8]
related_overrides: [docker-deployment.md]
related_pages: [install__docker, install__updating]
---

# Install on Hetzner — JamBot annotation

## What docs say (TL;DR)

Hetzner-specific install quickstart. Install OpenClaw as a system service or Docker container. Configure `~/.openclaw/openclaw.json`, set up channels, etc.

## JamBot is on Hetzner — but doesn't follow this guide

JamBot deploys OpenClaw via custom multi-tenant Docker compose, NOT the upstream-recommended single-user install. See `overrides/docker-deployment.md` for the real architecture.

| Upstream guide | JamBot reality |
|-----------------|-----------------|
| Single user, single gateway | Multi-tenant: one openclaw container per client |
| Default `/var/lib/openclaw` data | Per-client `/mnt/clients/<user>/openclaw/` |
| systemd service | Docker Compose with `name: jambot-<user>` |
| Port 18789 on host | Port 18789 internal-only (NOT exposed to host) |
| `claude setup-token` for API auth | Multi-provider env vars baked into container |

## Hetzner-specific bits worth checking

### Anchor #8 — Bonjour disabled by default for Compose
Pre-v4.25 Bonjour mDNS probe-loop pegged CPU on Compose-bridge networks (Hetzner default). v4.25 fixed by disabling default. Verify post-upgrade:

```bash
docker exec openclaw-<user> sh -c 'env | grep BONJOUR'
# expect: nothing, OR OPENCLAW_DISABLE_BONJOUR=1
```

### Bun pin (v5.2)

Per audit doc: should mention Bun 1.3.13 pin. JamBot openclaw Dockerfile should track this; verify `/mnt/system/base/openclaw/Dockerfile` matches.

### `host.docker.internal` mapping (v4.26)

For LM Studio / Ollama running on host (outside container): v4.26 added documented `host.docker.internal` mapping support. JamBot uses Ollama for `ollama-cloud-minimax` (memory) — relevant if we ever switch to local Ollama on host.

### Disk layout (Hetzner volumes)

JamBot uses three mounted Hetzner volumes (per CLAUDE.md):

| Volume | Mount | Purpose |
|--------|-------|---------|
| 104886781 | `/mnt/system` | Docker data, source, templates, openclaw build |
| 104886787 | `/mnt/clients` | Per-user data (isolated) |
| 105451785 | `/mnt/HC_Volume_105451785` (`/mnt/backlinks`) | Niche Backlink Intelligence |

`/dev/sda1` (root) is only OS + `/home/mike`. NEVER put per-tenant data here.

## Upgrade procedure (5.2 cutover)

When upgrading client containers from <5.2:
1. `bash /mnt/system/base/scripts/jambot-build-images.sh` — rebuild with new openclaw npm
2. Pre-cutover audit: `docker exec openclaw-<user> openclaw plugins list --json` per client (anchor #12 audit)
3. Restart one container at a time: `docker compose -f /mnt/clients/<user>/compose/docker-compose.yml restart openclaw`
4. First-start migration runs automatically (anchor #7) — `meta.lastTouchedVersion: "2026.5.2"` written
5. Verify: `docker exec openclaw-<user> openclaw doctor`
6. `git diff /mnt/clients/<user>/openclaw/openclaw.json` to see auto-edits — commit if benign

## Related JamBot files

- `overrides/docker-deployment.md` — full architecture
- `audit-anchors/anchor-{7,8,12}.md`
- `/jambot-openclaw` skill — Dockerfile + z-code wrapper
- `/docker` skill — image registry discipline
- `docs/jambot/docker-images-registry.md`
