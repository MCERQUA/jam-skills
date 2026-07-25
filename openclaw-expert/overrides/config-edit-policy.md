# Override — `openclaw.json` mutation policy (JamBot, NON-NEGOTIABLE)

Referenced by anchor **#19** (doctor is destructive, ≤6.x) and scope-corrected by anchor **#25** (7.1 rework). This override states the rule; `playbooks/safe-config-edit.md` is the step-by-step.

---

## The rule

**Never edit `openclaw.json` directly** — not with the `Edit` tool, not `sed`, not a Python `json.dump`, not from the host, not "just this once for a new tenant."

Two sanctioned paths:

### 1. `openclaw config set` from INSIDE the container (preferred)

Schema-aware, validated, official.

```bash
sg docker -c "docker exec openclaw-<tenant> openclaw config set tools.exec.pathPrepend '[\"/home/node/.local/bin\",\"/mnt/shared-skills/agent-mesh/bin\"]' --json"
sg docker -c "docker restart openclaw-<tenant>"
```

### 2. Template + re-provision (for new tenants / fleet-wide fields)

Edit `/mnt/system/base/templates/openclaw.json` — the single source of truth — and let provisioning copy it with token substitution. **Never** an inline heredoc in a script; that has drifted from the template twice, and both times shipped a tenant missing a required field.

If you must touch a file directly while bootstrapping, follow it with `openclaw doctor --repair --yes` inside the container **before** the gateway starts.

---

## Why the rule exists

- Older openclaw versions **silently restart-loop** on unknown keys. A single stray field takes the tenant down with no useful error.
- Host-side rewrites lose the JSON5 comments and formatting the file carries — and this file is heavily commented with the *reasons* for values (`timeoutSeconds: 360 // DO NOT revert`, the `memorySearch` disable note). Those comments are operational memory; a `json.dump` deletes them.
- Community-reported breakage (anchor #19): agent edits config → gateway fails to start; reported 3+ times independently.
- The four load-bearing fields (`thinkingDefault`, `trustedProxies`, `allowInsecureAuth`, `dangerouslyDisableDeviceAuth`) are exactly the ones a naive rewrite drops.

---

## Defense layers already in place

These are belt-and-suspenders. **They are not permission to bypass the rule.**

- **Layer 1A** — every openclaw container entrypoint runs `openclaw doctor --repair --yes` before the gateway starts, so a bad config is auto-stripped.
- **Layer 2** — `jambot-health-monitor.sh` Check 3.5 detects `Config invalid` / `Unrecognized key` in logs and triggers doctor + restart.

---

## Version notes

| Version | Doctor behavior on config |
|---|---|
| ≤2026.6.x (**incl. our `2026.5.7` pin**) | `--fix`/`--repair` may replace custom config with defaults — anchor #19 stands in full |
| ≥2026.7.1 | Refuses to replace an **unreadable** `openclaw.json` (#96469); **shows** rather than auto-applies sensitive changes like `gateway.bind=loopback` (#99776); adds non-mutating `doctor --lint --only <check>` — anchor #25 |

`--fix` and `--repair` are aliases; `--force` is the aggressive one that overwrites custom **service** config. Verified against `openclaw doctor --help` on 2026.5.7 — re-verify after any version bump rather than assuming.

---

## Snapshot before you change anything

The per-tenant openclaw workspace is git-tracked (`scripts/jambot-init-agent-repos.sh`, cron daily 04:15). Commit before a change and after it, so a bad edit is one `git diff` away from diagnosis.

⚠️ On ≥2026.6.9 an increasing share of tenant state lives in SQLite and is **not** covered by that snapshot (anchor #24). The config file is still a file — this rule is unaffected — but do not treat "the repo is clean" as "the agent is backed up."
