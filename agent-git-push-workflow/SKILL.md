---
name: agent-git-push-workflow
description: "Mesh agents push their own commits to MCERQUA canonical repos using write-capable SSH deploy keys. Covers one-time SSH config, git clone via per-repo host alias, commit authorship, push semantics, branch strategy, and mesh-coordination rules. Trigger: 'commit and push', 'ship to canonical', 'git push from agent', 'write to repo'."
---

# agent-git-push-workflow

**Who reads this:** any mesh agent that wants to push code/docs/config to a MCERQUA canonical repo without proxying through host@mesh.

**Before this skill existed:** agent drafted file → inline-pasted to host via mesh → host committed + pushed. That's the old pattern — slow, human-in-loop for every change, bottlenecked by host session availability.

**With this skill:** agent edits → `git commit` → `git push` — autonomous. No human touch-points for routine changes.

## Your per-repo write access

Each agent has write-capable SSH deploy keys for a specific scope:

| Agent | Can push to |
|---|---|
| bun-desktop | ovui-bridge, ovui-desktop, OVUI-Ubuntu, jam-skills |
| josh-desktop | ovui-bridge, ovui-desktop, jam-skills |
| residential-laptop | ovui-bridge, jam-skills |
| host@mesh | all MCERQUA repos (uses gh CLI token) |

Private keys are in `/agent-desk/desk/deploy-keys/write/<repo>-write`.

## One-time SSH + git setup

**Run once per container** (or add to your mesh-tools init script). After this, `git push` works inline from the relevant repo checkout.

```bash
#!/bin/bash
set -euo pipefail

WRITE_KEYS=/agent-desk/desk/deploy-keys/write
SSH_DIR=$HOME/.ssh
mkdir -p "$SSH_DIR"; chmod 700 "$SSH_DIR"

# Ensure github.com host key is known (avoid interactive StrictHostKeyChecking prompt)
if ! grep -q "^github.com" "$SSH_DIR/known_hosts" 2>/dev/null; then
  ssh-keyscan -t ed25519,ecdsa github.com 2>/dev/null >> "$SSH_DIR/known_hosts"
fi

# Install every write key + create a per-repo host alias
for src in "$WRITE_KEYS"/*-write; do
  [ -f "$src" ] || continue
  repo=$(basename "$src" -write)                    # e.g. ovui-bridge
  dst="$SSH_DIR/$(basename "$src")"                 # ~/.ssh/ovui-bridge-write
  cp -f "$src" "$dst"; chmod 600 "$dst"

  # Idempotent ~/.ssh/config entry for github-<repo>-push alias
  if ! grep -q "^Host github-${repo}-push$" "$SSH_DIR/config" 2>/dev/null; then
    cat >> "$SSH_DIR/config" <<CFG
Host github-${repo}-push
  HostName github.com
  User git
  IdentityFile ~/.ssh/${repo}-write
  IdentitiesOnly yes
CFG
  fi
done
chmod 600 "$SSH_DIR/config" 2>/dev/null || true

# Git identity — commits from this agent are attributable
git config --global user.name  "${AGENT_URI:-unknown-agent}"
git config --global user.email "${AGENT_URI:-unknown-agent}@jambot-mesh"

echo "done — push aliases ready:"
ls "$SSH_DIR" | grep -- "-write$"
```

## Clone pattern (per repo)

Use the per-repo host alias in the git remote so `git push` uses the right key automatically.

```bash
# Fresh clone with the write alias
git clone git@github-ovui-bridge-push:MCERQUA/ovui-bridge.git /tmp/ovui-bridge
cd /tmp/ovui-bridge

# Or re-point an existing read-only clone
git remote set-url origin git@github-ovui-bridge-push:MCERQUA/ovui-bridge.git
```

For each repo in your scope, substitute `ovui-bridge` with `ovui-desktop`, `OVUI-Ubuntu`, or `jam-skills`.

## Commit + push

Standard git flow, with conventions:

```bash
# Stage + commit
git add path/to/changed.py
git commit -m "[bun-desktop@mesh] <scope>: <one-line summary>

<optional body — why this change, what it unblocks>

Co-Authored-By: bun-desktop@mesh <bun-desktop@jambot-mesh>"

# Push to main (direct-push model, see branch strategy below)
git push origin main
```

**Commit message conventions:**
- Prefix subject with `[<your-mesh-URI>]` so host git log + GitHub activity can be filtered by agent
- `<scope>` matches the area touched (e.g. `handler:`, `skill:`, `mesh:`, `docs:`)
- One-line summary (≤72 chars) describing WHAT
- Optional body explaining WHY (not required for trivial changes)
- Don't include `Claude Code` footer — the Co-Authored-By + subject prefix already attributes
- NEVER include API keys, tokens, or secrets — run `git diff --staged | grep -iE "hf_|sk-|eyJ|aia_sk_|-----BEGIN"` before commit (see feedback_mesh_secrets_pattern)

## Branch strategy

**Default: push directly to `main`** (or `master` for ovui-desktop). MCERQUA is a single-owner account — agents are extensions of the owner. Direct push is correct for 95% of changes.

**Open a PR ONLY when:**
- Change is experimental and you want host review before merging
- Change affects >1 repo atomically and you want a single integration point
- You're not sure if the change breaks something (risky refactor, dep bump)

PR flow:
```bash
git checkout -b bun-experiment-foo
git push origin bun-experiment-foo
# You can't gh-cli create the PR yourself (no gh token on mesh agents).
# Instead, mesh-send to host asking for PR creation:
mesh-send --to host@mesh --kind message \
  --subject "PR request: ovui-bridge bun-experiment-foo" \
  --body "Branch pushed. Base: main. Purpose: <brief>. Please open PR + review."
```

## Mesh coordination before risky pushes

Match the rule set in `jambot-tenant-workspace` (if you're editing tenant files) AND this skill's rules for canonical repo commits:

| Change class | Action |
|---|---|
| Typo / docs / comment tweak | Push direct. No announce. |
| Add a new skill to jam-skills | Push direct. Other agents pull on next session start via shared-skills mount. |
| Edit an existing skill in jam-skills | Announce via mesh-send first (other agents may be actively using it) |
| Canonical bridge handler change | Push direct — but coordinate rollout (host bakes new version into images) |
| Canonical MCP server change | Push direct + announce — each agent container needs `s6-svc -r /run/service/ovui-mcp` to pick up |
| Dockerfile / image-bake change | Don't push direct. This triggers image rebuild chain — mesh-send to host for scheduling. |
| Anything under OVUI-Ubuntu root | host-preferred scope; only bun-desktop has write key. Announce major changes. |

## Failure modes + how to diagnose

**Push rejected: "Permission denied (publickey)"**
- Check `~/.ssh/config` has the `github-<repo>-push` alias
- Check `~/.ssh/<repo>-write` exists + mode 600
- Test: `ssh -T git@github-ovui-bridge-push` — should print "Hi MCERQUA/<repo>! You've successfully authenticated..."
- Verify your remote: `git remote get-url origin` — should be `git@github-<repo>-push:MCERQUA/<repo>.git`

**Push rejected: "refusing to update checked out branch"**
- You're pushing to a non-bare repo that has someone checked out on `main`. Shouldn't happen for MCERQUA canonical repos. If it does, something's unusual — mesh-send to host.

**Push rejected: "protected branch"**
- Some repos (MIKE-AI historically) had branch protection. Current state: main is unprotected for our use. If you hit protection: mesh-send to host.

**`git push` hangs**
- SSH connection issue. Check `ssh-keyscan` put github.com in `~/.ssh/known_hosts`. Retry: `ssh -T -v git@github-<repo>-push`.

## Anti-patterns

- ❌ Never copy a write key to a location outside `~/.ssh/` (e.g. `/tmp/`, `/shared/`) — widens leak surface
- ❌ Never paste the private key contents into a mesh message or a file that's mesh-committed (the mesh filesystem is readable across agents — would leak your key to peers)
- ❌ Don't set up write access in multiple containers from the same key material — each agent has its own scoped keys
- ❌ Don't push to a repo outside your scope — your SSH alias won't resolve to an authorized key; push fails
- ❌ Don't `git push --force` on `main` without mesh-coordinating with host first
- ❌ Don't amend pushed commits — create a new commit with a revert/fix

## Cross-refs

- feedback_mesh_secrets_pattern — pre-commit secret scan rule
- feedback_all_sessions_are_you — you own the repo state after pushing
- feedback_branch_discipline — don't mix unrelated work in one commit
- todo_agents_push_autonomy — earlier version tracked this gap
- Host skill `jambot-tenant-workspace` — rules for tenant files (different scope)
