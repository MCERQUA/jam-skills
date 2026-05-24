# Safe `openclaw.json` editing — atomic, validated, git-tracked

Per anchor-19: `openclaw doctor --fix` is destructive, direct JSON edits crash the gateway, and agent-driven edits are the #1 source of broken tenants. This is the standing JamBot procedure for any change to a tenant's `openclaw.json`.

## The non-negotiable rules

1. **NEVER** open `openclaw.json` directly in an editor on a live tenant.
2. **NEVER** let an agent `Read` + `Write` `openclaw.json` as plain text.
3. **NEVER** run `openclaw doctor --fix` without a fresh backup AND a verified rollback path.
4. **ALWAYS** use `openclaw config set <path> <value>` — it validates input and refuses invalid edits.
5. **ALWAYS** git-commit before AND after each change to a tenant's `openclaw.json` directory.

## Setup (one-time per tenant)

```bash
docker exec jambot-<tenant> sh -c '
  cd ~/.openclaw &&
  git init --quiet &&
  git config user.email "agent@jambot.local" &&
  git config user.name "jambot-agent" &&
  echo "secrets/" > .gitignore &&
  echo "logs/" >> .gitignore &&
  echo "workspace/" >> .gitignore &&
  echo "*.log" >> .gitignore &&
  git add openclaw.json .gitignore &&
  git commit -m "initial tenant config snapshot"
'
```

This excludes secrets, logs, and large workspace files but tracks `openclaw.json` and any plugin/skill config the agent might touch.

## Standard edit cycle

```bash
TENANT="jambot-mike"
FIELD="agents.defaults.compaction.midTurnPrecheck"
VALUE="true"

# 1. Pre-commit snapshot
docker exec $TENANT sh -c 'cd ~/.openclaw && git add openclaw.json && git diff --quiet --cached || git commit -m "pre-change snapshot ($(date -Iseconds))"'

# 2. Atomic validated edit
docker exec $TENANT openclaw config set "$FIELD" "$VALUE"
# Exit code != 0 means validation failed — STOP, do NOT manual-edit

# 3. Post-edit smoke test
docker exec $TENANT openclaw gateway status
docker exec $TENANT openclaw config get "$FIELD"

# 4. Post-commit snapshot
docker exec $TENANT sh -c 'cd ~/.openclaw && git add openclaw.json && git commit -m "set '"$FIELD"'='"$VALUE"'"'
```

## Rollback any single change

```bash
docker exec jambot-<tenant> sh -c 'cd ~/.openclaw && git log --oneline | head -5'
# pick the commit BEFORE the bad change
docker exec jambot-<tenant> sh -c 'cd ~/.openclaw && git checkout <good-sha> -- openclaw.json'
docker exec jambot-<tenant> openclaw gateway restart --force --wait 60s
```

## What's safe to edit via `config set`

Anything in the documented config schema. The validator catches typos, type errors, and unknown keys. Safe examples:

```bash
openclaw config set thinkingDefault "off"
openclaw config set trustedProxies '["172.0.0.0/8","10.0.0.0/8"]'
openclaw config set agents.defaults.compaction.midTurnPrecheck true
openclaw config set plugins.slots.memory "memory-lancedb"
openclaw config set providers.anthropic.type "claude-cli"
```

## What requires the JamBot template

Bulk-field changes or whole-section restructures should start from `/mnt/system/base/templates/openclaw.json` and copy in via a token-substitution script — NEVER inline heredoc generation (template has been corrupted by inline drift twice).

See `CLAUDE.md` "OpenClaw Config — CRITICAL FIELDS" and `overrides/openclaw-json-deltas.md`.

## What MUST never run on a live tenant

```bash
# DON'T:
openclaw doctor --fix              # overwrites custom config (anchor-19)
$EDITOR ~/.openclaw/openclaw.json  # direct edit can corrupt
agent.Write(file=openclaw.json)    # agent edit history shows 3+ gateway crashes
```

## Recovery for "Bot edited config, gateway won't start"

This is the u/Bulky-Shopping579 / u/whoisurhero scenario (r/openclaw 1ri9nt0):

```bash
# 1. Stop the broken container
docker stop jambot-<tenant>

# 2. Mount the config directory on a working container or host
docker run --rm -it -v jambot-<tenant>_openclaw:/x alpine sh
cd /x
git log --oneline | head -5      # find last-known-good
git checkout <good-sha> -- openclaw.json
exit

# 3. Restart
docker start jambot-<tenant>
docker exec jambot-<tenant> openclaw gateway status
```

If no git history exists, copy from `/mnt/system/base/templates/openclaw.json` + JamBot tenant-specific overrides.

## References

- `audit-anchors/anchor-19-openclaw-doctor-destructive.md`
- `overrides/openclaw-json-deltas.md`
- r/openclaw 1ri9nt0 (the meme thread that surfaced 4 separate breakage patterns)
