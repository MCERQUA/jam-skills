---
anchor: 13
slug: tools-exec-yolo-defaults-flip
status: confirmed
introduced: v2026.4.5
changelog_line: 3268
upstream_pages:
  - https://docs.openclaw.ai/tools/exec.md
  - https://docs.openclaw.ai/tools/exec-approvals.md
  - https://docs.openclaw.ai/gateway/sandbox-vs-tool-policy-vs-elevated.md
old_behavior: "tools.exec gateway/node host: security=deny/allowlist, ask=on-miss"
new_behavior: "tools.exec gateway/node host: security=full, ask=off (YOLO)"
skill_files_affected:
  - "references/tools-and-exec.md:104-117"
  - "references/security.md"
---

# Anchor #13 — `tools.exec` defaults flipped to YOLO

## What changed

v4.5 line 3268: "Exec defaults: make gateway/node host exec default to YOLO mode by requesting `security=full` with `ask=off`, and align host approval-file fallbacks plus docs/doctor reporting with that no-prompt default."

This is a **major reversal** of the conservative pre-4.5 default. Sandbox host (`host=sandbox`) defaults remain `deny` / `ask=off` — it's only the gateway/node hosts that flipped.

## Effective defaults (5.2)

| Host | security | ask | Sandbox active? |
|------|----------|-----|-----------------|
| gateway | `full` | `off` | No |
| node (paired device) | `full` | `off` | No |
| sandbox | `deny` | `off` | Yes (when configured) |

v4.27 line 1249 added explicit `host=node` exception clarifying the flip applies to node host too.

## What this means

If you don't explicitly configure restrictive policies, the gateway/node will execute ANY shell command the agent asks for, with no human approval gate. This is fine for trusted single-user setups; **dangerous** for multi-tenant or untrusted-user-facing deployments.

## JamBot impact

JamBot is multi-tenant. Each client container's openclaw runs as gateway-host-exec. We have NOT explicitly configured restrictive policies in the canonical `templates/openclaw.json`. **Audit needed.**

Action items:
1. Decide per-client policy — most clients should NOT have free shell exec
2. Update template with restrictive defaults
3. Document override path in `overrides/jambot-exec-policy.md`

## Related v5.2 changes

- Strict tool-allowlist hard-error (anchor #3)
- v4.26 line 1144: `tools.exec.timeoutSec` enforced on background, yieldMs, node system.run
- v4.27 line 1249: host=node fallback rules

## Fix instruction

`annotations/tools__exec.md`: prominent v4.5 YOLO default warning. `overrides/jambot-exec-policy.md`: write proposed restrictive policy.
