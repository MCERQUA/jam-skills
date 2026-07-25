---
upstream: https://docs.openclaw.ai/gateway/sandbox-vs-tool-policy-vs-elevated.md
relevance: jambot-critical
last-verified: 2026-07-25
audit_anchors: [13]
related_pages: [tools__exec, tools__exec-approvals, tools__elevated, gateway__sandboxing]
---

# Sandbox vs tool policy vs elevated — JamBot annotation

## What docs say (TL;DR)

Three independent controls:

| Control | Purpose | Example knob |
|---------|---------|--------------|
| **Sandbox** (where) | Where tools run (host vs container) | `agents.defaults.sandbox.mode: "off" \| "non-main" \| "all"` |
| **Tool policy** (which) | Which tools exist + per-tool security | `tools.<tool>.security`, `tools.<tool>.ask`, `tools.allow`, `tools.deny` |
| **Elevated** (escape) | exec escape hatch from sandbox | `tools.elevated.enabled`, `tools.elevated.allowFrom.<provider>` |

## Anchor #13 — defaults flipped to YOLO (v4.5)

The gateway/node host exec defaults are now `security: "full"`, `ask: "off"` — see `annotations/tools__exec.md`. This affects tool policy specifically, NOT sandbox or elevated.

| Layer | Default after v4.5 |
|-------|---------------------|
| sandbox host | `deny` / `ask: off` (unchanged) |
| gateway/node host | `full` / `ask: off` (FLIPPED — was `deny`/`on-miss`) |

## Key invariants (per docs)

1. **Deny always wins** — `tools.deny` cannot be overridden by `/exec` or other commands
2. **Empty allow list blocks everything else** — non-empty `allow` makes unlisted tools unavailable
3. **Tool groups expand** — `group:runtime`, `group:fs`, `group:sessions`, `group:web` simplify config
4. **Elevated does not grant tools** — only affects `exec`; runs outside sandbox when authorized
5. **Workspace access is independent** — `workspaceAccess` permissions separate from bind mount modes
6. **Sandbox tool policy only applies when sandboxed** — `tools.sandbox.tools.*` only inside container
7. **Per-agent overrides available** — most controls support agent-level alongside global defaults

## Bind-mount footgun

Docker `:rw` bind mounts pierce the sandbox. Use `:ro` for sources/secrets when sandboxing. Mounting `/var/run/docker.sock` grants container host control — only intentional.

## Symlink validation

Both normalized paths AND resolved ancestors are checked. Non-existent leaf paths still validated against blocked paths (no path-creation bypass).

## Debug command

```bash
openclaw sandbox explain
```

Shows effective mode, scope, tool policies, and "fix-it paths" — invaluable when a tool is unexpectedly denied or an `exec` can't run.

## JamBot policy — UNRESOLVED

Per `annotations/tools__exec.md`: JamBot's canonical template does NOT explicitly configure restrictive `tools.exec` policy. Each client container's openclaw runs gateway-host-exec with YOLO defaults.

Action items:
1. Decide per-client policy (most clients should not have free shell exec)
2. Update `templates/openclaw.json` with restrictive defaults
3. Document override in `overrides/jambot-exec-policy.md` (TODO)

## Two common fixes when `exec` won't run

1. **Disable sandbox entirely**: `agents.defaults.sandbox.mode: "off"` (already JamBot default)
2. **Whitelist tools in sandboxed environments**: `tools.sandbox.tools.allow: ["bash", "git", ...]`

## Related JamBot files

- `audit-anchors/anchor-13-tools-exec-yolo-defaults-flip.md`
- `annotations/tools__exec.md`
- `overrides/jambot-exec-policy.md` (TODO)
- `/mnt/system/base/templates/openclaw.json`

---

<!-- verification-stamp -->
## Verification — 2026-07-25

**Method (be precise about what this stamp does and does not mean):**

- Every config key this file asserts was checked against the **live schema of the version JamBot actually runs** — `openclaw config schema` inside `openclaw-test-dev` at `2026.5.7`, 6,441 schema paths.
- Upstream page re-fetched as Markdown on 2026-07-25 (`scripts/fetch-page.sh --no-cache`).
- **Not done:** the prose was not re-read line-by-line against the 7.x docs. Upstream is at `2026.7.1`; this file is verified for our pin, not for upstream HEAD.

**Config keys asserted here: 4/4 confirmed present in the 2026.5.7 schema.**

If you change this file, re-run `python3 scripts/sync-annotations.py` so `lastVerified` reaches `catalog.json`.
