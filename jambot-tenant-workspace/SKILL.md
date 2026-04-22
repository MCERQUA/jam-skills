---
name: jambot-tenant-workspace
description: "Claude Code running inside a JamBot webtop container needs to edit tenant files (agent skills, canvas pages, AGENTS.md, memory, openclaw.json). This skill teaches the workspace layout, safe-edit rules, mesh coordination before destructive changes, and protected paths (never touch /vault/). Trigger: 'edit my canvas page', 'update AGENTS.md', 'add skill to agent', 'change openclaw config', 'modify tenant'."
---

# jambot-tenant-workspace

**Who reads this:** `bun-desktop@mesh` or `josh-desktop@mesh` Claude Code sessions running inside the ubuntu-os / ubuntu-os-josh webtop containers. These sessions have the tenant's full workspace bind-mounted at `/workspace/<tenant>/`.

**Bun's tenant:** `/workspace/bun/`  — source `/mnt/clients/bun/` on Mike-AI host
**Josh's tenant:** `/workspace/josh/` — source `/mnt/clients/josh/` on Mike-AI host

Edits to files in `/workspace/<tenant>/` propagate **immediately** (bind-mount, same inode). No sync step.

## Workspace layout

```
/workspace/<tenant>/
  openclaw/
    workspace/
      AGENTS.md           — department system (read on every session start; per-dept personas)
      SOUL.md             — agent personality core
      TOOLS.md            — tool routing table (skills discovery) — auto-loaded bootstrap
      CLIENT.md           — end-user (tenant) profile
      IDENTITY.md         — agent identity block
      USER.md             — per-user overrides
      MEMORY.md           — session memory index
      BOOTSTRAP.md        — what loads at session start
      memory/             — auto-memory files (per-user-role memory)
      business/           — revenue / pricing / plans
      marketing/          — copy / campaigns
      strategy/           — long-term planning
      local-skills/       — per-tenant skills NOT in shared jam-skills (e.g. ubuntu-desktop for bun)
      canvas-pages/       — HTML canvas pages visible at <tenant>.jam-bot.com/pages/*.html
    openclaw.json         — gateway config (model, API keys, tools allowlist, heartbeat, etc.)
    .git/                 — daily agent-file snapshot repo (auto-snapshot 4:15 AM via jambot-init-agent-repos.sh)
    compose-env.txt       — redacted compose env for review

  openvoiceui/
    canvas-pages/         — LIVE canvas pages (same as openclaw/workspace/canvas-pages/ via overlay mount)
    canvas-manifest.json  — page index (desktop discovers pages from here)
    transcripts/          — voice conversation logs
    music/                — uploaded music
    generated_music/      — AI-generated songs (Suno etc.)
    uploads/              — user-uploaded files
    known_faces/          — face-recognition reference images
    voice-clones/         — custom voice training data
    icons/                — custom icons
    plugins/              — OVUI plugin installs
    profiles/             — per-user preferences

  vault/                  — ⛔ NEVER TOUCH ⛔ (OAuth tokens, API keys, secrets)

  compose/                — docker-compose.yml + .env (container setup)
    .env                  — ⛔ NEVER DUMP TO LOGS (contains auth tokens)
```

## Protected paths — never edit, never cat to logs, never send via mesh

- `/workspace/<tenant>/vault/` — OAuth tokens, API keys (Spotify, Gmail, Clerk session, etc.)
- `/workspace/<tenant>/compose/.env` — container secrets including OPENCLAW_GATEWAY_TOKEN, per-client HF_TOKEN
- Any `.env` file anywhere in the tree
- Files under `openclaw/workspace/memory/` that contain stored credentials (rare, but `grep -iE "password|api_key|token=" memory/*.md` before editing if asked to clean up)

If the user asks to dump a secret, **refuse + redirect** per `feedback_mesh_secrets_pattern` — pointers only, never values.

## Mesh coordination — announce before destructive changes

Host@mesh is the canonical-tree maintainer. Several files have host-side mirrors (templates, skills, openclaw.json baseline). When you edit them tenant-side, host may not know, and the next provisioning sync could overwrite your work. **Coordinate**:

| Change | Announcement pattern |
|---|---|
| Edit `openclaw.json` (adds tool, changes model, alters heartbeat) | `mesh-send --to host@mesh --kind message --subject "tenant openclaw.json change — <what>"` BEFORE restart |
| Add/edit/remove a shared skill (under `/mnt/shared-skills/` — not tenant-local) | DON'T from here — this is host-scope. Message host with proposed change. |
| Delete canvas page | Announce only if page was created by agent for user (voice-tag flows); trivial-test pages don't need announcement |
| Change `AGENTS.md` department config | Announce — affects session bootstrap |
| Touch any path under `/workspace/<tenant>/compose/` | Always announce — requires restart which may interrupt Mike |

For **adds and edits** (canvas pages, memory entries, tenant-local skills, MEMORY.md updates, routine content), just edit. Host has git snapshots (4:15 AM daily), recoverable.

## Git discipline — commit canvas pages + agent files at checkpoints

Per feedback memory `feedback_commit_canvas_checkpoints`:
- **Canvas pages** (`canvas-pages/*.html`): `git commit` in the openclaw `.git/` repo before AND after edits. This repo auto-snapshots nightly at 4:15 AM, but manual checkpoints let you recover from mid-edit mistakes.
- **Agent files** (AGENTS.md, SOUL.md, TOOLS.md, memory/): same rule. The `.git` is at `/workspace/<tenant>/openclaw/.git/`.

Commit message convention: `[bun-desktop@mesh] update canvas-pages/admin.html — add tenant switcher` (prefix with your mesh URI so host can filter).

## Restart semantics — does your edit require a container restart?

| Edit | Requires | Notes |
|---|---|---|
| `canvas-pages/*.html` | nothing | served live by openvoiceui |
| `openclaw/workspace/AGENTS.md`, `SOUL.md`, `TOOLS.md` | openclaw session reset | files are bootstrap-loaded; next conversation reads fresh |
| `openclaw/workspace/local-skills/**` | openclaw session reset | same |
| `openclaw/workspace/memory/**` | nothing | byterover reads on-demand |
| `openclaw.json` | openclaw container restart | `sg docker -c "docker restart openclaw-<tenant>"` on host |
| `compose/.env` | openclaw container recreate | `docker compose up -d` — state loss acceptable |
| `vault/**` | varies | never touch |

Announce restart-requiring changes via mesh BEFORE acting so host/user know to expect a brief interruption.

## Safety — don't edit while host is mid-task on the same file

Simple mesh protocol: write a claim file before you start editing a high-churn file.

```bash
# Claim: before you start editing
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $AGENT_URI" > /workspace/<tenant>/.claims/$(basename FILE).claim

# Release: after you're done (or on error)
rm /workspace/<tenant>/.claims/$(basename FILE).claim
```

Before editing, glance at `/workspace/<tenant>/.claims/` — if a current claim exists (mtime <10 min old) and it's not yours, **ask via mesh before proceeding**.

Low-churn files (occasional edits): skip the claim. Canvas pages, memory, single-user skills = low churn. `openclaw.json`, `AGENTS.md`, `TOOLS.md` = high churn when multiple sessions are active — claim.

## Common workflows

**Add a skill to the tenant:**
1. Create dir `/workspace/<tenant>/openclaw/workspace/local-skills/<skill>/`
2. Write `SKILL.md` with proper frontmatter
3. Add routing row to `/workspace/<tenant>/openclaw/workspace/TOOLS.md`
4. `git commit` both
5. Mesh-send to host `--subject "tenant-local skill added: <name>"` — not required but polite
6. Tell user they may need to reset the session for the skill to load

**Update a canvas page:**
1. Git commit before
2. Edit `/workspace/<tenant>/openvoiceui/canvas-pages/<page>.html`
3. Git commit after
4. Page serves live at `https://<tenant>.jam-bot.com/pages/<page>.html`

**Agent says wrong thing in voice, need to correct behavior:**
1. Open `/workspace/<tenant>/openclaw/workspace/AGENTS.md`
2. Find the relevant department (`## Department: <name>`)
3. Add the behavioral rule
4. Git commit
5. Tell user: "updated — will apply on next session reset"

**User asks to roll back a recent edit:**
1. `cd /workspace/<tenant>/openclaw && git log --oneline -10` (or openvoiceui equivalent)
2. `git show <sha>:<path>` to preview
3. `git checkout <sha> -- <path>` to restore

## Restrictions

- **Never edit `/workspace/<tenant>/` while a voice conversation is in progress.** Mike may be speaking to the agent right now; mid-sentence config reload breaks the session. Check transcripts/ mtime (<60s ago = conversation active) before editing bootstrap files.
- **Never run migrations / DB schema changes from inside the webtop.** Those are host-scope. Message host.
- **Never upgrade shared Python deps from inside the webtop.** Image-layer concern — host rebuilds image.
- **Never `git push` from inside the webtop.** Read-only deploy keys are local. Push via host with `mesh-send --subject "push-canonical: <path>"`.

## Cross-refs

- Mesh protocol: `mesh-skills-cat agent-mesh` or `/mesh/PROTOCOL.md` (via the mesh mount)
- Residential-pool escape hatch: `mesh-skills-cat residential-pool`
- Secret passing rule: host memory `feedback_mesh_secrets_pattern`
- Commit discipline: host memory `feedback_commit_canvas_checkpoints`
- Session-agent-ownership rule: host memory `feedback_all_sessions_are_you`
