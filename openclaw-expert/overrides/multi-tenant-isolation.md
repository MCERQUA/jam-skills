# Override — Multi-tenant isolation (JamBot)

**What upstream assumes:** one trusted operator per Gateway. **What JamBot runs:** N tenants, each with its own openclaw + openvoiceui container pair, on one VPS.

> **Status update 2026-07-25:** upstream now *does* document a multi-tenant model — `gateway/multi-tenant-hosting` + `openclaw fleet` (EXPERIMENTAL). See **anchor #28** for the full comparison. This override is no longer "the docs are silent"; it is "the docs describe a different implementation of the same idea."

---

## The unit of isolation

**One tenant = one openclaw container + one openvoiceui container + one bridge network + one data tree.**

| Layer | JamBot | Notes |
|---|---|---|
| Containers | `openclaw-<user>`, `openvoiceui-<user>` | plus optional `webdev-<user>`, `postgres-<user>` |
| Network | `jambot-<user>` (isolated bridge) | per-tenant; created at provision |
| Compose project | `name: jambot-<user>` **mandatory** | without it, `up -d` recreates OTHER tenants' containers |
| Data | `/mnt/clients/<user>/` | `compose/`, `openclaw/`, `openvoiceui/`, `home/` (dev only) |
| Gateway port | `18789` **inside the container only** | not published to the host; OVU reaches it at `ws://openclaw:18789` |
| Public entry | nginx `443` → `127.0.0.1:<OVU_PORT>` | per-tenant port, tracked in `docs/jambot/client-registry.md` |
| UID | `1000:1000` on the openclaw tree | official image runs as non-root `node` |
| Limits | openclaw 2GB/1.0 CPU · OVU 3GB/0.5 · webdev 3GB/1.0 · pg 512MB/0.25 | ~6GB per client |

---

## The deliberate hole: `jambot-shared`

Every tenant's containers are also attached to `jambot-shared` so they can reach shared services (supertonic TTS, Remotion). **This is a real cross-tenant network path and it is intentional.** Upstream's cell model explicitly avoids any shared data path between tenants (anchor #28).

Rules that keep it from widening:
- `jambot-shared` is attached **after** startup, never declared `external: true` in a compose file.
- Post-start attachments are **dropped when a container is recreated** — every roll/recreate path must re-attach, or a tenant silently loses TTS.
- Anything new placed on `jambot-shared` is reachable by every tenant. Treat adding a service there as a security decision, not a plumbing one.

```bash
sg docker -c "docker network connect jambot-shared openvoiceui-<user>"
sg docker -c "docker network connect jambot-shared openclaw-<user>"
sg docker -c "docker network inspect jambot-shared --format '{{range .Containers}}{{.Name}} {{end}}'"
```

---

## What isolation does and does not buy

Upstream states the doctrine plainly and it applies to us verbatim:

> *Session IDs select routing; they do not authorize one tenant against another. Agent sandboxing can reduce the effect of untrusted content and tool execution, but it does not turn one shared Gateway into a tenant authorization boundary.*

So:
- **Never** serve two tenants from one gateway process, one OS user, or one workspace, no matter how convenient the session split looks.
- The **host operator is trusted by every tenant** — that is a non-goal to defend against, not a gap to patch. Gateway tokens and `--env` values are readable via `docker inspect` by anyone with host docker access.
- Shared skills in `/mnt/system/base/skills/` are a **fleet-wide blast radius**: one malicious skill reaches every tenant simultaneously (anchor #18).

---

## Known gaps vs. upstream's hardened baseline

Neither is urgent; both are cheap and additive. Validate on `test-dev` before any fleet change.

1. **Capability drop / `no-new-privileges`** — upstream's cell profile drops all Linux capabilities and sets `no-new-privileges`. Our per-tenant compose does not. Adding them is a compose-level change across every tenant file.
2. **Auth-profile keys are not split from state** — upstream mounts auth-profile encryption keys from a *separate* host path (`fleet/auth-profile-secrets/<tenant>/` → `/home/node/.config/openclaw`) so the key is not nested under the ordinary state mount. Ours share one tree.

---

## Isolation checks

```bash
# Compose project names — any tenant missing `name:` is a recreate hazard
grep -L "^name: jambot-" /mnt/clients/*/compose/docker-compose.yml

# No tenant should have `external: true` networks in compose
grep -l "external: true" /mnt/clients/*/compose/docker-compose.yml

# Per-tenant bridges present
sg docker -c "docker network ls --filter name=jambot- --format '{{.Name}}'"

# Ownership on the openclaw tree
ls -ld /mnt/clients/*/openclaw
```

**Docker address pools are finite** (32 pools). Per-tenant bridges consume them; exhaustion blocks `network create` and therefore blocks new-tenant provisioning entirely. Check pool headroom before planning a batch of new tenants.
