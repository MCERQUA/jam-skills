# JamBot Docker deployment — overrides over upstream `install/docker.md`

Upstream docs assume a single-user gateway. JamBot is multi-tenant: per-client openclaw + openvoiceui pair, isolated network, shared-network membership for Supertonic TTS.

## Compose project name — CRITICAL

**Every docker-compose.yml MUST have `name: jambot-<username>` at the top.**

Without this, Docker Compose uses the directory name. Since all users have `compose/` dirs, `docker compose up -d` for one user will **recreate other users' containers**.

```yaml
name: jambot-bun
services:
  openclaw:
    image: jambot/openclaw:latest
    container_name: openclaw-bun
    ...
```

## NEVER use `external: true` shared networks in docker-compose.yml

Connect shared networks manually after startup:

```bash
sg docker -c "docker network connect jambot-shared openvoiceui-<username>"
sg docker -c "docker network connect jambot-shared openclaw-<username>"
```

If `external: true` is in compose, every `up -d` tries to recreate the shared network and fails or detaches other clients.

## Network topology

| Layer | Purpose | Members |
|-------|---------|---------|
| `jambot-<user>` (per-client bridge) | Isolation; openclaw↔openvoiceui internal | openclaw-<user>, openvoiceui-<user>, optional webdev/postgres |
| `jambot-shared` (shared bridge) | Cross-tenant services | All openvoiceui + openclaw containers + supertonic-tts + remotion |

## Bonjour/mDNS — anchor #8

v4.25 disabled Bonjour by default for bundled Compose gateways on bridge networking — exactly our setup. No action needed; just don't re-enable via `OPENCLAW_DISABLE_BONJOUR=0` unless you've moved to host or macvlan networking.

## Resource limits per client (6GB total)

| Container | Memory | CPU |
|-----------|--------|-----|
| openclaw | 2GB | 1.0 |
| openvoiceui | 3GB | 0.5 |
| webdev (if present) | 3GB | 1.0 |
| postgres (if present) | 512MB | 0.25 |

`scripts/jambot-set-resource-limits.sh` adds these to all client compose files.

## Image registry discipline

Per CLAUDE.md, every docker build/pull/rmi/compose-stack change updates `docs/jambot/docker-images-registry.md` in the same commit. Use `/docker` skill before fumbling around with `docker images` or `find`.

## See also

- `/jambot-openclaw` skill — Dockerfiles, z-code, container UIDs, dev access
- `/docker` skill — registry, prune recipes, maintenance discipline
- `docs/jambot/multi-website-system.md` — webdev container placement
- `audit-anchors/anchor-08.md` — Bonjour default flip
- `audit-anchors/anchor-12.md` — external plugin migration (impacts which channels work in 5.2)
