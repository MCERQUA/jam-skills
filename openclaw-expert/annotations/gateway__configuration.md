---
upstream: https://docs.openclaw.ai/gateway/configuration.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: [6, 7, 11, 13, 14, 15]
related_overrides: [openclaw-json-deltas.md]
---

# gateway/configuration — JamBot annotation

## Source of truth

**Canonical:** `/mnt/system/base/templates/openclaw.json` (token-substituted into each client). NEVER inline-heredoc generate this file in scripts. The template has been wrong twice from inline drift.

## JamBot's 4 non-negotiable fields

See `overrides/openclaw-json-deltas.md` for full table. Critical: `dangerouslyDisableDeviceAuth: true` — without this, sessions hit `NOT_PAIRED` forever.

## Audit anchors that apply

### Anchor #7 — `meta.lastTouchedVersion` first-run migration (v5.2)

Auto-runs once on first 5.2 gateway start:
- Adds `zai` to `plugins.allow` when zai is referenced
- Updates `channelConfigs` for stale plugin manifests (anchor #12)
- Other 5.2 fix-ups

After running: gateway writes `meta.lastTouchedVersion: "2026.5.2"`. Don't blow away the file with template re-copy after first 5.2 start. `git diff` will show the auto-edits — good.

### Anchor #6 — Compaction new keys

| Key | Default | Introduced |
|-----|---------|-----------|
| `agents.defaults.compaction.midTurnPrecheck` | opt-in | v4.27 |
| `agents.defaults.compaction.maxActiveTranscriptBytes` | opt-in (requires `truncateAfterCompaction: true`) | v4.26 |
| `agents.defaults.compaction.memoryFlush.model` | inherits primary | v4.27 |
| `agents.defaults.compaction.provider` | unset (registering forces `mode: "safeguard"`) | v4.7 |

JamBot tuning: see `overrides/openclaw-json-deltas.md` "Compaction tuning" section.

### Anchor #15 — `session.maintenance.rotateBytes` DEPRECATED (v4.27)

Doctor `--fix` removes the key. Replacement (different concept): `session.writeLock.acquireTimeoutMs` (default 60s, v5.2). Rotation no longer happens automatically — log management is BYO.

### Anchor #14 — `messages.queue.mode` default = `"steer"` (v4.29)

Changed from `"collect"`. For JamBot voice flow this is mostly an improvement (multiple in-flight user messages get steered at next model boundary instead of one-at-a-time). Override if a client wants strict turn-taking.

### Anchor #13 — `tools.exec` defaults = YOLO (v4.5)

See `annotations/tools__exec.md`. Affects this file because the `tools.exec.security` / `ask` defaults documented in upstream gateway-configuration may be stale.

### Anchor #11 — `plugins.entries` vs `skills.entries` dual-axis

`plugins.slots.memory: "none"` is the ONLY single-knob disable for memory subsystem. Setting only `plugins.entries.memory-core.enabled: false` leaves the skill exposure active (and probably broken).

## New keys not yet in skill (audit doc §2.1)

- `agents.defaults.skipOptionalBootstrapFiles` (v5.2) — skip selected optional workspace files during bootstrap
- `agents.defaults.contextInjection: "never"` (v4.24) — disable workspace bootstrap injection for self-managing agents
- `agents.defaults.systemPromptOverride` (v4.7) — controlled prompt experiments
- `gateway.controlUi.chatMessageMaxWidth` (v5.2)
- `gateway.nodes.pairing.autoApproveCidrs` (v4.24, disabled by default)
- `models.pricing.enabled` (v4.27, default true) — set false for offline installs
- `proxy.enabled` + `proxy.proxyUrl` (v4.27) — operator-managed outbound proxy
- `OPENCLAW_INCLUDE_ROOTS` env (v5.2) — allowlisted `$include` directives
- `OPENCLAW_OTEL_PRELOADED=1` (v4.24) — reuse already-registered OTel SDK
- `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental` (v4.25)

## Hot reload — degraded mode (v4.27)

`gateway.reload` continues in degraded mode when invalidity is scoped to plugin entries (line 932). Other config errors still abort reload.

## Removed/renamed keys (audit doc §4)

JamBot configs may still have these — proactively clean:

- `talk.voiceId`, `talk.apiKey` — v4.5 → use `messages.tts.providers.<id>.*`
- `agents.<>.sandbox.perSession` — v4.5 → use `sandbox.scope` + `enabled`
- `hooks.internal.handlers` — v4.5 → use `hooks.transformsDir`
- `browser.ssrfPolicy.allowPrivateNetwork` — v4.5 → per-policy CIDR fields
- `MOLTBOT_*`, `CLAWDBOT_*` env vars — v4.27 warns; use `OPENCLAW_*`
- `dreaming.storage.mode: "inline"` — v4.15 default flipped to `"separate"`

## Related JamBot files

- `/mnt/system/base/templates/openclaw.json` — canonical
- `overrides/openclaw-json-deltas.md`
- `audit-anchors/anchor-{6,7,11,13,14,15}.md`
- `/jambot-performance` skill — full perf tuning context
- `docs/jambot/openclaw-skill-update-2026-05-04.md` §2.1, §3, §4
