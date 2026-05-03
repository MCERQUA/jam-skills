---
name: docker
description: Mike-AI VPS Docker handbook. Inventory, image registry, compose locations, build/cleanup recipes, and maintenance discipline. Use when ANY docker question comes up — running containers, cached images, build cache, disk pressure, "what's that container", "is this image still needed", pruning, rebuilding, deploying. Replaces fumbling around with `docker images` / `docker ps` / find / grep — read this first.
---

# Docker handbook — Mike-AI VPS

This is the canonical entry point for everything Docker on this VPS. Before running `docker images`, `docker ps`, or any cleanup command, **read the registry** so you know what's there and why.

## CANONICAL TRACKING FILES — keep these updated

| File | Purpose | Update when |
|---|---|---|
| `docs/jambot/docker-images-registry.md` | Per-image ledger: name, tag, size, created date, what containers use it, **WHY it exists**, removal candidates | Any time you `docker build`, `docker pull`, `docker rmi`, or add/retire a compose stack. Same commit as the change. |
| `docs/jambot/client-registry.md` | Per-client port + Clerk + webdev assignments — drives compose env vars | Adding/removing a client |
| This skill (`SKILL.md`) | Pointers + recipes + discipline | Any time the recipe set changes or a new compose stack is introduced |

If you can't find an image's purpose in the registry, **add it before pruning**. "Don't know what it is" is not a removal reason — find out, document, then decide.

## DOCKER-RELATED PATHS — bookmark these

### Source / build context dirs
| Path | What it is |
|---|---|
| `/mnt/system/base/ovui-ubuntu/` | KDE/Selkies webtop image (`ovui-ubuntu:dev`). Build: `docker build -t ovui-ubuntu:dev .` |
| `/mnt/system/base/openclaw/` | OpenClaw gateway image (`jambot/openclaw:latest`). Has its own Dockerfile. |
| `/mnt/system/base/OpenVoiceUI/deploy/openclaw/` | Alternate openclaw build location |
| `/mnt/system/base/OpenVoiceUI/` | OpenVoiceUI Flask app source (`jambot/openvoiceui:latest`) |
| `/mnt/system/base/airadio/` | AI-Radio platform compose + source |
| `/mnt/system/base/twenty-crm/` | Twenty CRM compose |
| `/mnt/system/base/phase-6-5/` | Phase 6.5 control plane: MinIO + NATS + Langfuse + Clickhouse |
| `/mnt/system/base/templates/docker-compose.yml` | Per-client compose template (used by `jambot-create-user.sh`) |
| `/mnt/clients/<user>/compose/docker-compose.yml` | Per-client live compose (one per tenant) |

### Build + ops scripts
| Script | What it does |
|---|---|
| `scripts/jambot-build-images.sh` | Builds `jambot/openvoiceui:latest`, `jambot/openclaw:latest`, `jambot/supertonic:latest`. **Does NOT build `ovui-ubuntu` — that's separate (see below).** |
| `scripts/jambot-build-webdev.sh` | Builds `jambot/webdev:latest` |
| `scripts/jambot-create-user.sh` | Provisions a new client (compose, dirs, nginx, starts containers) |
| `scripts/jambot-create-dev.sh` | Provisions a developer (create-user + SSH + docker access) |
| `scripts/jambot-supertonic.sh` | Manages supertonic-tts shared service |
| `scripts/jambot-twenty-provision.sh` | Manages Twenty CRM workspaces |

### ovui-ubuntu image (separate from `jambot-build-images.sh`)
Build manually: `cd /mnt/system/base/ovui-ubuntu && docker build -t ovui-ubuntu:dev .`

After rebuild, recreate webtops one at a time:
```bash
sg docker -c "docker stop webtop-ubuntu-os-<user>"
sg docker -c "docker rm webtop-ubuntu-os-<user>"
# (compose up -d will recreate using the new image)
sg docker -c "docker compose -f /mnt/clients/<user>/compose/docker-compose.yml up -d"
```

### Storage layout (CRITICAL — disk pressure here costs real money)
| Path | Purpose | Watch for |
|---|---|---|
| `/var/lib/docker/` (= `/mnt/system/docker`) | Docker daemon data root — images, containers, volumes, build cache | >80% full = take action |
| `/mnt/clients/` | Per-user data (compose, openclaw workspace, openvoiceui uploads) | Per-tenant disk leaks |
| `/mnt/system/base/` | Source + templates + skills | Branch sprawl, orphaned worktrees |

Disk size targets (from CLAUDE.md):
- `/dev/sda1` (root): keep below 80%
- `/mnt/system`: keep below 80% — it holds Docker data root
- `/mnt/clients`: monitor per-user growth

## INVENTORY COMMANDS

```bash
# Full overview — start here
sg docker -c "docker system df"

# Image-level: what's there, when created
sg docker -c "docker images --format 'table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}\t{{.Size}}'"

# Containers: running + stopped, when created
sg docker -c "docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.CreatedAt}}'"

# Build cache breakdown
sg docker -c "docker buildx du --verbose | head -50"

# Per-image: what containers reference it
sg docker -c "docker ps -a --filter ancestor=<image:tag>"

# Host disk
df -h /var/lib/docker /mnt/system /mnt/clients
```

## COMMON DECISIONS

### "Is this image safe to remove?"
1. Read `docs/jambot/docker-images-registry.md` — find the row.
2. If row says **ACTIVE**: NO — running containers depend on it.
3. If row says **STOPPED but PARKED**: NO — intentional infrastructure.
4. If row says **REMOVAL CANDIDATE**: confirm with Mike, then remove.
5. If image is NOT in the registry: do NOT remove. Investigate, add registry row, then decide.

### "Disk is at 85%, what do I prune?"
Order of safety (safest first):
1. Dangling intermediate images: `docker image prune -f`
2. Build cache (anything unused >7 days): `docker builder prune --keep-storage 4GB --filter unused-for=168h -f`
3. Stopped containers older than 7 days: `docker container prune --filter 'until=168h' -f`
4. Removal-candidate images from registry: only after Mike confirms each.

Never run `docker system prune -a` — it will obliterate referenced images that have stopped containers (e.g., parked twenty CRM stack) and force expensive re-pulls.

### "I just rebuilt an image — what do I do with the live containers?"
Live containers keep running on the OLD image hash until recreated. Two options:
- **Hot patch** the running container (live edit + service restart inside the container) — survives until next recreate.
- **Recreate** the container so it picks up the new `:latest` / `:dev` tag — definitive, briefly disconnects users.

Decide based on disruption tolerance. For webtops: hot-patch buys you a day; recreate during a maintenance window.

### "Container in restart loop"
Find it: `sg docker -c "docker ps -a --filter status=restarting"`. Don't ignore it — a 10-second restart loop burns CPU and writes logs forever. Either fix the root cause or remove the container.

## SHELL ACCESS PATTERN

Mike is in the `docker` group but interactive shells don't always pick it up. Use `sg docker -c "<cmd>"` to force the group context.

```bash
sg docker -c "docker ps"
sg docker -c "docker logs <container>"
sg docker -c "docker exec <container> <cmd>"
sg docker -c "docker compose -f <path> up -d"
```

## COMPOSE STACK MAP

Each compose stack should have a `name:` directive at the top — without it, Compose uses the dir name and can clobber other stacks' containers.

| Stack | File | Project name | Containers |
|---|---|---|---|
| Per-client | `/mnt/clients/<user>/compose/docker-compose.yml` | `jambot-<user>` | `openvoiceui-<user>`, `openclaw-<user>`, `webdev-<user>-<project>` (optional) |
| Webtop | (sibling compose, sometimes inline) | varies | `webtop-ubuntu-os-<user>` |
| AI-Radio | `/mnt/system/base/airadio/docker-compose.yml` | `airadio` | `ai-radio`, `airadio-db`, `airadio-worker` |
| Twenty CRM | `/mnt/system/base/twenty-crm/docker-compose.yml` | varies | `twenty-server`, `twenty-worker`, `twenty-db`, `twenty-redis` |
| Phase 6.5 control plane | `/mnt/system/base/phase-6-5/docker-compose.yml` | `jambot-obs` | `minio`, `nats`, `langfuse`, `clickhouse-server` (langfuse + clickhouse currently parked) |
| Supertonic TTS | (managed by `jambot-supertonic.sh`) | shared | `supertonic-tts` (on `jambot-shared` network) |
| Coturn | (system) | — | `coturn` |

## SHARED NETWORK

`jambot-shared` is connected manually after `compose up`, never declared as `external: true` in the compose file (causes startup failures during partial outages).

```bash
sg docker -c "docker network connect jambot-shared <container>"
```

## DISCIPLINE — RULES OF THE ROAD

1. **Update the registry in the SAME commit as the docker change.** Stale registry = wasted storage = real money out the door.
2. **Never `docker system prune -a`.** It will eat parked images. Use targeted prunes from this skill.
3. **Never delete an image whose row isn't in the registry.** Add a row, then decide.
4. **Quarterly audit** — re-run the inventory, refresh date stamps, reconcile registry against reality.
5. **Always `name:` in compose** — `name: jambot-<user>` for client stacks, `name: airadio` etc. Without this, `compose up -d` for one stack can recreate containers from a sibling stack.
6. **Hot-patch is temporary** — anything live-edited inside a container is gone on recreate. Bake it into the image and rebuild before declaring done.

## RELATED SKILLS

- `/jambot-webdev` — webdev container architecture (websites, switching active project)
- `/jambot-openclaw` — OpenClaw image specifics (Dockerfile, z-code, UID 1000)
- `/jambot-session-monitor` — container event monitoring + health
- `/jambot-performance` — openclaw runtime tuning (compaction, contextPruning)
- `/provision-ovui-node` — full ovui-node provisioning (uses several images from this registry)
