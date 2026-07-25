# Playbook — Provision a new JamBot tenant (openclaw side)

**Scope:** what the OpenClaw layer needs for a new `<username>.jam-bot.com` tenant, and the traps that have actually bitten. The end-to-end provisioning is owned by `scripts/jambot-create-user.sh` — **this playbook does not replace it.** It explains what that script does at the OpenClaw layer so you can verify, debug, or extend it.

**Anchors:** #22 (non-loopback fail-closed), #23 (pairing hardening), #28 (upstream's own multi-tenant model), #19/#25 (config mutation), #18 (skill vetting).
**Overrides:** `multi-tenant-isolation.md`, `docker-deployment.md`, `openclaw-json-deltas.md`.

---

## 1. Run the script — do not hand-roll

```bash
sudo bash scripts/jambot-create-user.sh <user> <domain> [port]      # client
sudo bash scripts/jambot-create-dev.sh <user> <domain> <gh-user>    # dev (adds SSH, git, jb CLI, docker)
```

Never paste a multi-line sudo sequence for Mike to run — write/extend the script instead (CLAUDE.md, no exceptions).

The script provisions: Linux user → directories → `openclaw.json` from the template → compose + `.env` → nginx site → containers up → `jambot-shared` network attach → sub-mesh setup.

---

## 2. What must be true at the OpenClaw layer

### 2.1 `openclaw.json` comes from the template, always

Canonical: `/mnt/system/base/templates/openclaw.json` → `/mnt/clients/<user>/openclaw/openclaw.json` with token substitution. **Never an inline heredoc** — that has drifted out of sync with the template twice, and both times a tenant shipped missing a required field.

The four fields that must survive substitution or the tenant is broken:

| Field | Failure if missing |
|---|---|
| `thinkingDefault: "off"` | Z.AI/GLM returns thinking-only blocks — no visible text at all |
| `trustedProxies: ["172.0.0.0/8","10.0.0.0/8"]` | Docker-network WebSocket rejected |
| `allowInsecureAuth: true` | control UI auth blocks access |
| `dangerouslyDisableDeviceAuth: true` | **permanent `NOT_PAIRED`** — the classic new-tenant symptom |

### 2.2 Compose isolation

`name: jambot-<username>` at the top of `docker-compose.yml` is **mandatory**. Without it Compose falls back to the directory name — every tenant has a `compose/` dir, so `up -d` for one tenant recreates other tenants' containers.

**Never** put `external: true` shared networks in the compose file. Attach after startup:

```bash
sg docker -c "docker network connect jambot-shared openvoiceui-<user>"
sg docker -c "docker network connect jambot-shared openclaw-<user>"
```

⚠️ Post-start network attachments are **dropped on recreate** — `compose up -d` only restores compose-declared networks. Any roll/recreate path must re-attach.

### 2.3 Ports and registry

`jambot-create-user.sh` auto-assigns the next free port. If you assign one by hand you must update **both** `docs/jambot/client-registry.md` (the only home of the port counters) and `registry.json`. The openclaw gateway port `18789` is internal-only and is not per-tenant.

### 2.4 Workspace files are client data

`SOUL.md`, `TOOLS.md`, `AGENTS.md`, `IDENTITY.md`, `CLIENT.md` are **create-once, skip-if-exists**. Never overwrite, never symlink (OpenClaw does not follow symlinks). Chown the openclaw tree `1000:1000` — the official image runs as non-root `node`, UID 1000.

### 2.5 Skills

Shared skills mount from `/mnt/system/base/skills/`; tenant-local skills live in the client's `openclaw/workspace/local-skills/`. Anything entering the shared dir reaches **every tenant at once** — vet before adding (anchor #18, `playbooks/skill-install-vetting.md`).

---

## 3. Verify — a tenant is not provisioned until these pass

```bash
U=<user>
sg docker -c "docker ps --filter name=$U --format '{{.Names}}\t{{.Status}}'"
sg docker -c "docker exec openclaw-$U openclaw --version"
sg docker -c "docker exec openclaw-$U openclaw gateway status"
sg docker -c "docker network inspect jambot-shared --format '{{range .Containers}}{{.Name}} {{end}}'" | tr ' ' '\n' | grep "$U"
sg docker -c "docker logs --tail 100 openclaw-$U" | grep -iE "NOT_PAIRED|config invalid|unrecognized key|fail"
curl -sk -o /dev/null -w '%{http_code}\n' https://$U.jam-bot.com
```

Then the one that actually matters: **hold a real turn in the UI.** Containers up ≠ tenant working. A gateway can be healthy while every reply comes back empty.

Also: add the subdomain to Clerk → Allowed Subdomains, or auth silently fails for that tenant only.

---

## 4. Version-dependent traps (read before provisioning on a NEWER image)

JamBot pins `2026.5.7`. If the image has moved:

- **≥2026.5.12** — setup-code pairing now requires approval; a non-interactive provision that used to pair silently may stall (anchor #23).
- **≥2026.5.17** — a non-loopback gateway bind without explicit shared-secret or trusted-proxy auth **fails closed**, and the image default command no longer bypasses config validation. A brand-new tenant is the *most* likely place to hit this, because nothing about it is grandfathered (anchor #22).
- **≥2026.6.9** — tenant state is database-first (SQLite). The agent-repo snapshot job captures `*.md` + `memory/` + `openclaw.json`; it does **not** capture db state (anchor #24).

---

## 5. Common failures

| Symptom | Cause | Fix |
|---|---|---|
| Session stuck `NOT_PAIRED` forever | `dangerouslyDisableDeviceAuth` missing/false | restore from template, restart |
| Agent replies with nothing visible | `thinkingDefault` not `"off"` | restore from template, restart |
| Provisioning one tenant restarted others | missing `name: jambot-<user>` in compose | add it; never run `up -d` without it |
| WS refused from the OVU container | `trustedProxies` missing, or attachment dropped on recreate | restore field; re-attach `jambot-shared` |
| Gateway restart-loops on boot | invalid config / unknown key | entrypoint `openclaw doctor --repair --yes` (Layer 1A) should strip it; if not, diff against the template |
| `network create` fails during provision | Docker address pool exhausted | known failure mode — pools are finite; see the pool-exhaustion fix script |
| Agent starts with zero context | `skipBootstrap: true` | never set this |
