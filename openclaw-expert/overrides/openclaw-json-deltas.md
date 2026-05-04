# JamBot openclaw.json — overrides over upstream defaults

Canonical template: `/mnt/system/base/templates/openclaw.json`. Scripts MUST copy from this template (with token substitution), NEVER inline heredocs. The template has been wrong twice from inline drift. See CLAUDE.md "OpenClaw Config — CRITICAL FIELDS".

## The 4 non-negotiable fields

These four fields MUST exist in every JamBot client's openclaw.json:

| Field | Value | Why |
|-------|-------|-----|
| `thinkingDefault` | `"off"` | Z.AI/GLM returns thinking-only blocks with NO visible text without this — visible text disappears |
| `trustedProxies` | `["172.0.0.0/8", "10.0.0.0/8"]` | Required for Docker network WebSocket connections (openvoiceui→openclaw via internal bridge). See anchor in `gateway/trusted-proxy-auth.md` |
| `allowInsecureAuth` | `true` | Bypasses control UI auth — fine for single-tenant container behind nginx |
| `dangerouslyDisableDeviceAuth` | `true` | **CRITICAL** — disables WebSocket device pairing. Without this, sessions get `NOT_PAIRED` forever |

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
