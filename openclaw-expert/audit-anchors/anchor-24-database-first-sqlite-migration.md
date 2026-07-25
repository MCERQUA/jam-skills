---
anchor: 24
slug: database-first-sqlite-migration
status: confirmed
introduced: v2026.6.5 → v2026.6.9 (ongoing through 7.x)
changelog_line: "CHANGELOG.md 2026.6.9 — 'Storage and migrations: avoid SQLite WAL on network filesystems, clean reindex artifacts, keep setup state out of workspace dot-directories, and import default-agent auth profiles into SQLite.' / 'PR #94646 refactor(sqlite): land database-first memory and proxy alignment.' | 2026.6.5 — 'PR #91056 fix: store memory-core dreams state in sqlite.' | Unreleased — 'SQLite snapshots: add `openclaw backup sqlite create|list|verify|restore`. (#94805)'"
upstream_pages:
  - https://docs.openclaw.ai/reference/database-schemas
  - https://docs.openclaw.ai/cli/backup
  - https://docs.openclaw.ai/refactor/database-first
old_behavior: "OpenClaw state lives in JSON/JSONL files under `~/.openclaw/` — sessions, auth profiles, memory state, cron runs. Backing up the directory (or git-snapshotting the `*.md` + `memory/` files) captures the agent."
new_behavior: "From 2026.6.5-6.9 state migrates database-first into SQLite: memory-core dreams state, default-agent auth profiles, plugin state, task/TaskFlow records, and the delivery queue. `openclaw backup sqlite create|list|verify|restore` is the sanctioned snapshot path. SQLite WAL is now explicitly avoided on network filesystems."
skill_files_affected:
  - overrides/multi-tenant-isolation.md
  - playbooks/upgrade-5.7-to-7.x.md
  - annotations/concepts__session.md
sources:
  - https://github.com/openclaw/openclaw/pull/94646
  - https://github.com/openclaw/openclaw/pull/91056
  - https://github.com/openclaw/openclaw/pull/94805
---

# Anchor #24 — State goes database-first (SQLite) from v2026.6.5–6.9

## What changed

Through the 2026.6.x line OpenClaw moved its durable state out of loose JSON files and into SQLite — a "database-first" refactor (#94646) that is still landing in 7.x. Confirmed movers so far: memory-core dreaming state, default-agent auth profiles, plugin state, task/TaskFlow records, the outbound delivery queue, and (in the Unreleased line) session artifacts.

Upstream docs written before 6.5 still describe file-shaped state. On ≥6.9, **the file is no longer the whole truth.**

## Why this matters to JamBot more than most deployments

Three of our systems assume file-shaped agent state:

1. **`jambot-init-agent-repos.sh`** (cron daily 4:15 AM) git-snapshots `*.md` agent files, `memory/`, `business/`, `openclaw.json`, and a redacted `compose-env.txt` per client. On a database-first openclaw, an increasing share of what makes a tenant agent *that* agent lives in SQLite and is **not** in those snapshots. The repo will keep committing cleanly and silently capture less. (This is the same failure shape as `monitors-that-report-unreadable-as-fine` — green because it never looked.)
2. **`jambot-backup.sh`** rsyncs the client volume. A live SQLite database copied mid-write is not guaranteed restorable. `openclaw backup sqlite create` + `verify` exists precisely for this and should front the rsync for openclaw state.
3. **Volume placement.** The 6.8/6.9 entries explicitly avoid SQLite WAL on network filesystems / NFS volumes. `/mnt/clients` is a Hetzner block volume formatted ext4 — a local block device, not NFS — so we are on the safe side of that guard today. Any future move of tenant state onto a network share (Storage Box, NFS, sshfs) would put us on the wrong side of it. **Do not host `/mnt/clients/<tenant>/openclaw/` on a network filesystem.**

## Do this before the 7.x upgrade

- Inventory what actually lives in SQLite on a 7.x container before trusting the existing snapshot job:
  ```bash
  sg docker -c "docker exec openclaw-<tenant> sh -lc 'ls -la ~/.openclaw/*.db* ~/.openclaw/**/*.db* 2>/dev/null'"
  ```
- Extend the agent-repo snapshot to call `openclaw backup sqlite create` and commit the *verified artifact* (not the live db file) — or explicitly record in `docs/jambot/agent-repos-and-page-auth.md` that db state is out of scope and covered elsewhere. Silent partial coverage is the thing to avoid.
- Never `git add` a live `.db`/`.db-wal` — binary, churning, and unrestorable mid-write.

## What NOT to conclude

- This is NOT a reason to pin to 5.7 forever. It is a reason to update the backup/snapshot layer *as part of* the upgrade rather than after the first restore fails.
- The `openclaw.json` mutation rule (CLAUDE.md, anchor #19/#26) is unchanged — config is still a file, and `openclaw config set` is still the only sanctioned mutation path.
