---
upstream: https://docs.openclaw.ai/tools/permission-modes
relevance: jambot-critical
last-verified: 2026-07-25
audit_anchors: [13, 22]
related_pages: [tools__exec, tools__exec-approvals, gateway__sandbox-vs-tool-policy-vs-elevated, gateway__security__exposure-runbook]
---

# Permission modes — JamBot annotation

New page in the 2026-07-25 catalog rebuild. It introduces `tools.exec.mode` as a **normalized surface over the `security` / `ask` pair** that anchor #13 is about.

## ⚠️ `tools.exec.mode` DOES NOT EXIST at our pin

Verified against the live `2026.5.7` schema (`openclaw config schema`): the `tools.exec.*` keys are `applyPatch, ask, backgroundMs, cleanupMs, host, node, notifyOnExit, notifyOnExitEmptySuccess, pathPrepend, safeBinProfiles, safeBinTrustedDirs, safeBins, security, strictInlineEval`. **No `mode`.**

So the page's headline recommendation —

```bash
openclaw config set tools.exec.mode auto     # ❌ fails schema validation on 2026.5.7
```

— is a **7.x-era instruction**. On our fleet you set `tools.exec.security` and `tools.exec.ask` directly. An agent that follows the current docs verbatim against a JamBot tenant will get a config error, and per `overrides/config-edit-policy.md` a rejected write is the good outcome; the bad one is someone "fixing" it by hand-editing the file.

## The mode → (security, ask) mapping — useful even without the key

| Mode | security / ask | Behavior |
|---|---|---|
| `deny` | `deny` / `off` | Block host exec entirely |
| `allowlist` | `allowlist` / `off` | Allowlist only; silently deny misses |
| `ask` | `allowlist` / `on-miss` | Allowlist matches run; human prompted on misses |
| `auto` | `allowlist` / `on-miss` **+ native auto-reviewer** | Misses go through auto-review before falling back to a human |
| `full` | `full` / `off` | Host exec with no prompts |

This table is the Rosetta Stone for reading 7.x docs against our config. `ask` and `auto` share the same security/ask pair — the difference is entirely the auto-reviewer, which is why you cannot infer `auto` from the raw pair alone.

## What JamBot actually runs (live, `test-dev`, 2026-07-25)

`openclaw exec-policy show` reports:

```
tools.exec   requested: host=auto (OpenClaw default), security=full (OpenClaw default), ask=off (OpenClaw default)
             host:      security=full (inherits requested tool policy), ask=off, askFallback=full
             EFFECTIVE: security=full, ask=off
```

Two things worth internalizing:

1. **We are running the equivalent of `mode: "full"` — no approval gate on host exec.**
2. **It is inherited from OpenClaw's own defaults, not set by us.** Every value above is labelled "OpenClaw default." That is anchor #13 (v4.5 flipped gateway/node host to `security: "full", ask: "off"`) confirmed at runtime rather than from a changelog line.

This is deliberate and correct for JamBot — tenant agents are owner-facing operators that need to actually run commands. It is *not* what upstream's exposure runbook recommends for exposed deployments (`security: "deny", ask: "always"`), because that baseline is written for semi-public messaging bots. See `annotations/gateway__security__exposure-runbook.md` for why that baseline does not apply to us.

**But because it is inherited rather than declared, it is invisible in `openclaw.json`.** Nobody reading a tenant config would know exec is unguarded. If a future upstream release flips the default back, our posture changes silently in the other direction. Worth pinning explicitly in the template rather than relying on an upstream default that has already flipped once.

## Diagnosing "it still prompts / still fails"

Two independent layers, and the **stricter one wins**:

```bash
sg docker -c "docker exec openclaw-<tenant> openclaw approvals get"
sg docker -c "docker exec openclaw-<tenant> openclaw exec-policy show"
```

Host exec = stricter of (OpenClaw config, host-local `~/.openclaw/exec-approvals.json`). ACPX harness permissions (`plugins.entries.acpx.config.permissionMode`) are a **separate** layer: they do not loosen host exec approvals, and host exec approvals do not loosen ACPX prompts. Chasing the wrong layer is the standard time-sink here.

Note also: `tools.exec.host` (where a command runs) and exec approval policy (how it is approved) are orthogonal. Upstream calls this out explicitly because it is commonly conflated.

## Upgrade note

When the pin moves past `2026.5.7`, `tools.exec.mode` becomes available and is the surface upstream will document going forward. Migrating the template from the raw `security`/`ask` pair to an explicit `mode` is a reasonable post-upgrade cleanup — it makes the posture declared instead of inherited. Do not attempt it before the upgrade; the key does not exist yet.
