---
anchor: 19
slug: openclaw-doctor-destructive
status: confirmed
introduced: existing behavior (not version-pinned)
changelog_line: null
upstream_pages:
  - https://docs.openclaw.ai/cli/index.md
  - https://docs.openclaw.ai/help/troubleshooting.md
old_behavior: "Upstream docs describe `openclaw doctor` and `openclaw doctor --fix` as diagnostic and self-healing commands."
new_behavior: "Production reports: `openclaw doctor` (especially `--fix`) overwrites custom config with defaults, breaking hard-earned tenant setups. Also: agent edits to `openclaw.json` frequently crash the gateway on next restart (3+ confirmed incidents in the community)."
skill_files_affected:
  - annotations/cli__index.md (extend with destructive-doctor warning)
  - annotations/help__troubleshooting.md (extend)
  - overrides/config-edit-policy.md (new — JamBot rule)
  - playbooks/safe-config-edit.md (new — git-tracked, atomic config edits)
sources:
  - https://reddit.com/comments/1ri9nt0 (220/62 — u/piratebroadcast +6, u/cheechw +7, u/Bulky-Shopping579 +35)
  - https://reddit.com/comments/1r71you (660/269 — "openclaw doctor --fix" cited as destructive in comments)
---

# Anchor #19 — `openclaw doctor` is destructive; never let agents edit `openclaw.json` directly

## What changed

This isn't a version-flip — it's a behavioral correction from production. Upstream docs frame `openclaw doctor` and `openclaw doctor --fix` as helpful diagnostics. Community reports across multiple threads disagree:

- **u/piratebroadcast (+6, 1ri9nt0):** `openclaw doctor` overwrites hard-earned working config.
- **u/Bulky-Shopping579 (+35, 1ri9nt0):** "Bot edited config → restart gateway → bot fails to start — happened 3 times already."
- **u/whoisurhero (+13, 1ri9nt0):** Half-edited Docker-Compose file from API-budget-exhausted edit cycle → no containers start.
- **u/cheechw (+7, 1ri9nt0):** Recommended pattern: never directly edit `openclaw.json`; always use `openclaw config set` which validates input and fails on invalid edits.
- **u/Successful_Bear_2420 (+10, 1ri9nt0):** Agent pre-commits config to git before any change; `.env` passwords excluded via gitignore.

## Why it matters for JamBot

JamBot has 1+ tenant containers per client, each with a managed `openclaw.json` derived from `/mnt/system/base/templates/openclaw.json`. A destructive `doctor --fix` blast OR a corrupted agent-edited JSON in any tenant = that tenant's gateway down + lost custom fields (`thinkingDefault`, `trustedProxies`, `dangerouslyDisableDeviceAuth`, `allowInsecureAuth`).

**JamBot rule:** Agents must NEVER edit `openclaw.json` directly. All changes go through `openclaw config set <path> <value>`. Per-tenant `openclaw.json` directory is git-initialized; agent pre-commits before every change. Never run `openclaw doctor --fix` on a tenant container without a fresh backup. See `overrides/config-edit-policy.md`.

## Safe-edit pattern

```bash
# WRONG — direct edit can break the gateway, may be overwritten on doctor
$EDITOR ~/.openclaw/openclaw.json

# RIGHT — atomic, validated, git-tracked
cd ~/.openclaw && git add openclaw.json && git commit -m "pre-change snapshot"
openclaw config set agents.defaults.compaction.midTurnPrecheck true
# config set validates; gateway is hot-reloaded on success
git add openclaw.json && git commit -m "midTurnPrecheck enabled"
```

## What NOT to do

- Do NOT add `openclaw doctor --fix` to any cron or auto-heal pipeline.
- Do NOT let an agent open openclaw.json as plain text (no `Read` then `Write` agent-loop on this file).
- Do NOT regenerate the JamBot config from a fresh `openclaw doctor` run — start from `/mnt/system/base/templates/openclaw.json` instead.

## References

- Reddit thread 1ri9nt0 — the meme thread that surfaced 4 separate breakage patterns
- Reddit thread 1r71you — corroboration of doctor-fix destructiveness
