# JamBot openclaw.json — overrides over upstream defaults

Canonical template: `/mnt/system/base/templates/openclaw.json`. Scripts MUST copy from this template (with token substitution), NEVER inline heredocs. The template has been wrong twice from inline drift. See CLAUDE.md "OpenClaw Config — CRITICAL FIELDS".

## The 5 non-negotiable fields

These MUST exist in every JamBot client's openclaw.json. **Note the exact nesting** — two of them
sit under `gateway.controlUi`, not at gateway top level, and reading them as gateway-wide auth is
the mistake that made anchor #22 look like an upgrade blocker for a year.

| Field (full path) | Value | Why |
|-------|-------|-----|
| `agents.defaults.thinkingDefault` | `"off"` | Z.AI/GLM returns thinking-only blocks with NO visible text without this — visible text disappears |
| **`gateway.auth`** | `{mode: "token", token: "${OPENCLAW_GATEWAY_TOKEN}"}` | **This is JamBot's actual gateway authentication** — a unique 64-char per-tenant secret from compose `.env`, expanded at config load. It is what lets us bind `lan` at all. On ≥2026.5.17 a `lan` bind without this **refuses to start** (anchor #22). Never remove it, and never let it fall back to a literal placeholder. |
| `gateway.trustedProxies` | `["172.16.0.0/12", "10.0.0.0/8"]` | Required for Docker network WebSocket connections (openvoiceui→openclaw via internal bridge). We deliberately carry BOTH this and `gateway.auth` — the two accepted auth modes — which is why #22 was a non-event. See anchor #23 (5.12 hardened the trusted-proxy path). |
| `gateway.controlUi.allowInsecureAuth` | `true` | Relaxes the secure-context requirement for the Control UI. ⚠️ **It does NOT bypass device identity checks** — see the correction below. **Control-UI scoped; not gateway auth.** |
| `gateway.controlUi.dangerouslyDisableDeviceAuth` | `true` | **CRITICAL** — disables WebSocket device pairing. Without this, sessions get `NOT_PAIRED` forever. This is the flag that actually disables device identity. **Control-UI scoped; not gateway auth.** |

> **Verified 2026-07-25 across 26/26 tenants** — every one has `gateway.auth.mode: "token"` with a
> unique 64-char token, plus `gateway.bind: "lan"` and `trustedProxies`. Confirmed experimentally
> against a real `openclaw@2026.7.1` binary: our config starts clean, and the same config with
> `auth`/`trustedProxies` removed produces `Refusing to bind gateway to lan without auth.`
> Full evidence in `audit-anchors/anchor-22-*.md` and `playbooks/upgrade-5.7-to-7.x.md` Phase 0.

> **⚠️ CORRECTED 2026-07-25 — the two flags do different things, and we had them conflated.**
> Verified by running `openclaw security audit` inside `openclaw-test-dev` at `2026.5.7`. The
> binary's own finding text:
>
> > `gateway.controlUi.allowInsecureAuth=true` **does not bypass secure context or device identity
> > checks; only `dangerouslyDisableDeviceAuth` disables Control UI device identity checks.**
>
> So "bypasses control UI auth" was wrong for `allowInsecureAuth`. Practical consequence: if you
> ever try to reduce risk by dropping `dangerouslyDisableDeviceAuth` and keeping `allowInsecureAuth`,
> you get `NOT_PAIRED` sessions — the flag you kept was never the one doing that work.
>
> Both flags are **knowingly accepted risk** for JamBot (audit rates them CRITICAL + WARN). The
> justification is the deployment shape, not a claim that the audit is wrong — see
> `annotations/gateway__security__exposure-runbook.md` for the recorded accepted-risk entry.

## Forbidden field

| Field | Value | Why |
|-------|-------|-----|
| `skipBootstrap` | `true` | NEVER. Disables ALL bootstrap file injection. Agent starts with zero context. |

## Compaction tuning

See audit-anchor #6 for the new keys. JamBot deltas:

```json5
{
  agents: {
    defaults: {
      compaction: {
        // Tune these per client based on observed transcript size
        maxActiveTranscriptBytes: 600000,    // anchor #6 — preflight before context fills
        truncateAfterCompaction: true,        // REQUIRED with maxActiveTranscriptBytes
        midTurnPrecheck: true,                 // anchor #6 — catch tool-loop pressure mid-turn
        memoryFlush: { model: null }           // inherits primary; override for cost
      },
      contextPruning: { mode: "cache-ttl", ttl: "30m" },
      memorySearch: { enabled: true }          // anchor #2 — active-memory recall
    }
  }
}
```

Performance impact + gotchas: see `/jambot-performance` skill.

## Session lock

```json5
{
  session: {
    writeLock: { acquireTimeoutMs: 60000 }    // anchor #15 — replaces removed rotateBytes
  }
}
```

## Memory kill switch (when disabling memory subsystem entirely)

Per anchor #11, the ONLY single-knob disable is:
```json5
{ plugins: { slots: { memory: "none" } } }
```
NOT `plugins.entries.memory-core.enabled: false` — that only disables runtime, not skill exposure.

## Legacy keys to remove on upgrade to 5.2

Doctor migration auto-strips these (anchor #7), but proactively clean during template review:

- `session.maintenance.rotateBytes` — anchor #15
- `talk.voiceId` / `talk.apiKey` — removed v4.5; use `messages.tts.providers.<id>.*`
- `agents.<>.sandbox.perSession` — removed v4.5; use `sandbox.scope` + `enabled`
- `hooks.internal.handlers` — removed v4.5; use `hooks.transformsDir`
- `browser.ssrfPolicy.allowPrivateNetwork` — removed v4.5; use per-policy CIDR fields
- `MOLTBOT_*` / `CLAWDBOT_*` env vars — use `OPENCLAW_*` (warns at startup post v4.27)

## See also

- `overrides/docker-deployment.md` — `name: jambot-<user>` rule, jambot-shared network
- `overrides/jambot-exec-policy.md` — policy for YOLO defaults flip (anchor #13) (TODO)
- `audit-anchors/anchor-{2,6,7,11,13,15}.md` — version-specific corrections
- `/jambot-performance` skill — compaction/contextPruning/heartbeat tuning
- `/jambot-openclaw` skill — Dockerfile, z-code wrapper, container UIDs
