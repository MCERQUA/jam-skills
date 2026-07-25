---
upstream: https://docs.openclaw.ai/tools/exec.md
relevance: jambot-critical
last-verified: 2026-07-25
audit_anchors: [13]
related_overrides: [openclaw-json-deltas.md]
related_pages: [tools__exec-approvals, gateway__sandbox-vs-tool-policy-vs-elevated]
---

# tools/exec — JamBot annotation

## What docs say (TL;DR)

`exec` runs shell commands on configurable hosts (gateway / node / sandbox). Approvals via tool policy + per-host security mode (`deny` / `allowlist` / `full`) + ask gates (`always` / `on-miss` / `off`). Sandbox layered separately.

## ⚠️ Anchor #13 — defaults flipped to YOLO in v2026.4.5

| Host | security | ask | Sandbox active? |
|------|----------|-----|-----------------|
| gateway | `full` | `off` | No |
| node (paired device) | `full` | `off` | No |
| sandbox | `deny` | `off` | Yes (when configured) |

**Pre-v4.5 was `deny` / `on-miss` for gateway/node.** The flip to `full` / `off` means: without explicit restrictive policy, the gateway/node executes any shell command the agent asks for, no human approval gate.

## JamBot impact — UNRESOLVED

- JamBot is multi-tenant
- Each client's openclaw runs gateway-host-exec
- Canonical `templates/openclaw.json` does NOT explicitly configure restrictive `tools.exec` policy
- Therefore: every client's agent can run arbitrary shell commands on its own openclaw container

This is contained (per-client container, isolated network), but it's not what we'd choose if we'd known about the flip. Action items:

1. Decide per-client policy (most clients should not have free shell exec)
2. Update template with restrictive defaults
3. Document in `overrides/jambot-exec-policy.md` (TODO)

## Strict tool-allowlist hard-error (anchor #3)

If you DO add `agents.list[N].tools.allow: ["exec", ...]`, v5.2 hard-errors at config load if any allowlisted tool's plugin is missing. Use `alsoAllow` for plugin tools to avoid forcing the rest into restrictive mode.

## Other v4.5+ changes

- v4.26 line 1144: `tools.exec.timeoutSec` enforced on background runs, `yieldMs` waits, and node `system.run` (when no per-call timeout)
- v4.27 line 1249: `host=auto` no longer cross-host-overrides; `host=node` preserved when configured
- v4.5 line 3020: `browser.ssrfPolicy.allowPrivateNetwork` REMOVED; use per-policy CIDR fields

> **⚠️ KEY NAME CORRECTED 2026-07-25.** The removed key is right, but the replacement is not
> "per-policy CIDR fields" generically — at `2026.5.7` the live schema exposes
> `browser.ssrfPolicy.dangerouslyAllowPrivateNetwork`, `browser.ssrfPolicy.allowedHostnames`,
> and `browser.ssrfPolicy.hostnameAllowlist`. Grepping for `allowPrivateNetwork` finds nothing;
> the modern spelling carries the `dangerously` prefix.

## Burns / incidents

- 2026-05-04 audit: production-observed strict allowlist hard-error from anchor #3 — verified path

## Related JamBot files

- `audit-anchors/anchor-{3,13}.md`
- `overrides/jambot-exec-policy.md` (TODO write)
- `overrides/openclaw-json-deltas.md`
- `/mnt/system/base/templates/openclaw.json`

---

<!-- verification-stamp -->
## Verification — 2026-07-25

**Method (be precise about what this stamp does and does not mean):**

- Every config key this file asserts was checked against the **live schema of the version JamBot actually runs** — `openclaw config schema` inside `openclaw-test-dev` at `2026.5.7`, 6,441 schema paths.
- Upstream page re-fetched as Markdown on 2026-07-25 (`scripts/fetch-page.sh --no-cache`).
- **Not done:** the prose was not re-read line-by-line against the 7.x docs. Upstream is at `2026.7.1`; this file is verified for our pin, not for upstream HEAD.

**Config keys asserted here: 2/4 confirmed present in the 2026.5.7 schema.**

Not resolvable as schema paths (expected for RPC method names, plugin-manifest fields, OTel metric names, and shorthand references — confirm the kind before treating as drift):

- `browser.ssrfPolicy.allowPrivateNetwork`
- `system.run`

If you change this file, re-run `python3 scripts/sync-annotations.py` so `lastVerified` reaches `catalog.json`.
