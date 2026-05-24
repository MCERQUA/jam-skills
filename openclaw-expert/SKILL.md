---
name: openclaw-expert
description: OpenClaw expertise for JamBot. Catalog-indexed router into 464 upstream doc pages + JamBot-specific overrides + 21 version-anchor corrections (15 from the 2026.4.20 → 2026.5.2 changelog audit + 6 from the 2026-05-23 r/openclaw deep-read covering the Apr-4 Anthropic subscription cutover, CVE-2026-25253, ClawHavoc supply-chain campaign, destructive `openclaw doctor`, QMD memory shift, and GLM-5 reliability divergence). Use to teach, debug, configure, or build on OpenClaw.
metadata: {"openclaw": {"emoji": "🧠"}}
---

# OpenClaw Expert

**OpenClaw npm latest:** `2026.5.2` (audited 2026-05-04; community-corroborated 2026-05-23). **Catalog refreshed:** see `catalog.json` `fetchedAt`.

This skill is a **router**, not a textbook. Upstream docs at `docs.openclaw.ai` are authoritative — we index them, layer JamBot-specific deltas, and surface **21 audit anchors** that mark version-specific corrections discovered in production:
- Anchors 1-15: derived from the changelog audit (`docs/jambot/openclaw-skill-update-2026-05-04.md`)
- Anchors 16-21: derived from a 2026-05-23 r/openclaw deep-read covering the Apr 4 2026 Anthropic subscription cutover, CVE-2026-25253, the ClawHavoc supply-chain campaign, destructive `openclaw doctor` behavior, community shift to QMD/hybrid memory, and GLM-5 reliability divergence

## How to use this skill

### 1. Find the right page

```bash
# By keyword (most common)
bash {baseDir}/scripts/lookup.sh compaction

# By section
bash {baseDir}/scripts/lookup.sh section:Plugins
bash {baseDir}/scripts/lookup.sh section:Channels

# By JamBot relevance (high|med|low)
bash {baseDir}/scripts/lookup.sh relevance:high

# By audit-anchor number (1–15)
bash {baseDir}/scripts/lookup.sh anchor:13     # YOLO exec defaults flip

# Pages with JamBot annotation
bash {baseDir}/scripts/lookup.sh annotated

# Annotations not verified in 60+ days
bash {baseDir}/scripts/lookup.sh stale 60
```

### 2. Read the right layer first

Order matters when answering a question:

1. **`audit-anchors/`** — version-specific corrections. If the page has an anchor, the skill knows upstream prose is misleading and what to say instead.
2. **`overrides/`** — what JamBot does *differently* than docs. Multi-tenant Docker, `trustedProxies`, `dangerouslyDisableDeviceAuth`, voice flow constraints, etc.
3. **`annotations/<page>.md`** — page-specific JamBot notes, burns, related files. Updated when we touch the topic in production.
4. **`cache/<page>.md`** — frozen snapshot of upstream page (fetched lazily by `fetch-page.sh`, 24h TTL).
5. **Live upstream** — only when current truth matters more than speed: `WebFetch` the URL.

```bash
# Fetch and cache one page
bash {baseDir}/scripts/fetch-page.sh concepts__compaction

# Print cached file path
bash {baseDir}/scripts/fetch-page.sh --path-only plugins__voice-call

# Force refetch
bash {baseDir}/scripts/fetch-page.sh --no-cache providers__zai
```

### 3. Refresh when OpenClaw releases

```bash
# Re-fetch llms.txt, diff, regenerate catalog. Posts diff to stdout.
bash {baseDir}/scripts/refresh-catalog.sh
```

Exit 0 = no changes. Exit 2 = added/removed/renamed pages — review the diff, decide which new pages need annotations.

## Audit anchors (21 total — 15 from changelog audit + 6 from community deep-read)

When answering ANY question about a topic in this list, the audit anchor wins over the upstream prose:

### Changelog audit (anchors 1-15, v2026.4.20 → v2026.5.2)

| # | Topic | One-liner |
|---|-------|-----------|
| 1 | Plugin SDK breaking | `registerEmbeddedExtensionFactory` removed v2026.4.24 → use `registerAgentToolResultMiddleware` |
| 2 | memory-core auto-activates | Bundled `memory-core` + active-memory sub-agent run before every reply unless `plugins.slots.memory: "none"` |
| 3 | Strict tool-allowlist | v5.2 hard-errors with "No callable tools remain after resolving explicit tool allowlist" if allowlisted tool's plugin is disabled |
| 4 | Embedded run timeout = 15s | NOT `agents.defaults.timeoutSeconds`; embedded path uses its own (low) default |
| 5 | Per-file bootstrap caps | TOOLS.md ≈ 24K chars, MEMORY.md ≈ 10.5K chars (auto-truncated with marker) |
| 6 | Compaction trigger ≈ 68% prompt usage | Plus `midTurnPrecheck` (4.27), `maxActiveTranscriptBytes` (4.26), `memoryFlush.model` (4.27), pluggable provider (4.7) |
| 7 | `meta.lastTouchedVersion` migration | Auto-runs on first 5.2 start; auto-adds zai to plugins.allow when referenced |
| 8 | Bonjour disabled by default | For bundled Compose gateways on bridge networking — opt back in via `OPENCLAW_DISABLE_BONJOUR=0` |
| 9 | GLM-5 consecutive-turn fix | v5.2 preserves prior context for z.ai/openrouter z-ai/in-house GLM gateways |
| 10 | Anthropic-messages scoping | v4.20 — custom providers MUST explicitly set `api: "anthropic-messages"` |
| 11 | plugins.entries vs skills.entries | `plugins.slots.memory: "none"` is the only single-knob disable for memory-core |
| 12 | External plugin migration | v5.2 wholesale move: ACPX, OTel, Discord, WhatsApp, Voice Call, Brave, Codex, Memory LanceDB, Teams, Diffs, Lobster, BlueBubbles, Mattermost, Matrix, Tlon, Google Chat, LINE, Nextcloud Talk, Nostr, Zalo, QQ Bot, Synology Chat, Twitch, Feishu, Google Meet, Yuanbao |
| 13 | tools.exec defaults flipped to YOLO | v4.5 — gateway/node host now `security: "full", ask: "off"` (was `deny`/`on-miss`) |
| 14 | messages.queue.mode default flipped | v4.29 — default now `steer` with 500ms followup-fallback debounce (was `collect`) |
| 15 | rotateBytes deprecated | v4.27 — `session.maintenance.rotateBytes` removed; use `session.writeLock.acquireTimeoutMs` (default 60s) |

### Community deep-read (anchors 16-21, added 2026-05-23 from r/openclaw)

| # | Topic | One-liner |
|---|-------|-----------|
| 16 | Anthropic subscription cutover (Apr 4 2026) | Pro/Max OAuth-token extraction killed; sanctioned replacement is `providers.anthropic.type: "claude-cli"` + `mode: "oauth"`; 5h cap kills cron-on-sub |
| 17 | CVE-2026-25253 + gateway-bind exposure | ~500k OpenClaw instances exposed on `0.0.0.0`; CVE patched, but config default still needs `gateway.bind: loopback` |
| 18 | ClawHavoc supply-chain campaign | 1,467 malicious ClawHub skills caught; flagship `capability-evolver` (35k installs) exfiltrating data; **mandatory Skill Vetter + JamBot allowlist** |
| 19 | `openclaw doctor` is destructive | `--fix` overwrites custom config with defaults; 3+ community gateway-crash incidents; **never let agents edit openclaw.json directly** |
| 20 | QMD memory default shift | Default markdown+keyword memory under-performs; community converged on QMD plugin or memory-lancedb hybrid via `plugins.slots.memory` |
| 21 | GLM-5 reliability divergence | Community signal diverges; JamBot triage: rule budget → anti-loop → version migration BEFORE escalating; don't panic-switch primary |

Each anchor has a full file in `audit-anchors/anchor-NN-<slug>.md` with sources (changelog line numbers OR Reddit post IDs), exact config keys, and skill files affected.

## JamBot-specific overrides

`overrides/` holds things JamBot does that docs don't describe:

- `openclaw-json-deltas.md` — the 4 critical fields (`thinkingDefault`, `trustedProxies`, `allowInsecureAuth`, `dangerouslyDisableDeviceAuth`) + compaction tuning
- `docker-deployment.md` — `name: jambot-<user>` rule, `jambot-shared` network, NO `external: true` in compose
- `voice-flow-quirks.md` — single-instance SpeechRecognition rule, wake-word abort loop
- `multi-tenant-isolation.md` — per-user openclaw + openvoiceui pair, port registry
- `skill-allowlist.md` *(added 2026-05-23)* — JamBot ClawHub allowlist + blocklist; mandatory vetting before adding to `/mnt/system/base/skills/`
- `glm5-turbo-pin.md` *(added 2026-05-23)* — primary-model version policy + fallback chain; community-divergence triage

When the user asks about anything in these overrides, **the override wins** — docs may describe a different deployment model.

## Playbooks (task-shaped recipes)

`playbooks/` holds end-to-end workflows that span multiple doc pages:

- `debug-empty-final.md` — the 13-fix MiniMax empty-response recovery cascade
- `tune-compaction.md` — sizing context window, cache TTL, transcript rotation
- `provision-new-tenant.md` — full client provisioning flow
- `add-new-channel.md` — Telegram/Discord/Slack channel onboarding
- `migrate-to-claude-cli-provider.md` *(added 2026-05-23)* — wire `providers.anthropic.type: "claude-cli"` post-Apr-4-cutover; Docker install caveat
- `safe-config-edit.md` *(added 2026-05-23)* — atomic, validated, git-tracked `openclaw.json` editing per anchor-19
- `skill-install-vetting.md` *(added 2026-05-23)* — pre-install vetting workflow with Skill Vetter (anchor-18)
- `cron-as-sub-agent.md` *(added 2026-05-23)* — heartbeats dispatch sub-agents, never run work directly (anchor-16 5h cap defense)

## Version metadata

| File | Purpose |
|------|---------|
| `catalog.json` | 464 doc pages × {url, section, relevance, annotation, audit_anchors, lastVerified, tags} |
| `audit-anchors/anchor-NN-*.md` | 21 version-anchor correction files (15 changelog + 6 community deep-read) |
| `annotations/<page-id>.md` | JamBot notes per upstream page (page id = url path with `/` → `__`) |
| `cache/<page-id>.md` | Lazy-fetched frozen snapshot (24h TTL) |
| `cache/<page-id>.meta.json` | Fetch metadata (sha256, fetchedAt, bytes) |
| `overrides/*.md` | JamBot-specific deployment deltas |
| `playbooks/*.md` | Multi-page task recipes |
| `references/` | **DEPRECATED** — pre-redesign prose. Do not extend. New work goes into annotations or playbooks. |
| `SKILL.md.pre-2026-05-04` | Frozen pre-redesign skill for archaeology |

## Quick reference

**Default ports:** Gateway WS `127.0.0.1:18789`, Clawdbot `18791`, Canvas host `18793`
**Config file:** `~/.openclaw/openclaw.json` (JSON5)
**Workspace:** `~/.openclaw/workspace/`
**Logs:** `~/.openclaw/logs/`
**Sessions:** `~/.openclaw/agents/<agent>/sessions/`
**Cron runs:** `~/.openclaw/cron/runs/<jobId>.jsonl`

**JamBot-specific paths:**
- Container config: `/mnt/clients/<user>/openclaw/openclaw.json`
- Container workspace: `/mnt/clients/<user>/openclaw/workspace/`
- Shared skills (mounted into containers): `/mnt/system/base/skills/`
- Canonical openclaw.json template: `/mnt/system/base/templates/openclaw.json`

## Diagnostic commands (verbatim)

```bash
openclaw status
openclaw gateway status
openclaw doctor                          # since v5.2 also runs meta.lastTouchedVersion migration
openclaw gateway restart --force --wait 60s   # NEW v5.2 (anchor #15 territory)
openclaw logs --follow
openclaw channels status --probe
openclaw plugins registry --refresh      # NEW v4.25
openclaw plugins deps                    # NEW v4.27
openclaw migrate plan --dry-run          # NEW v4.26
openclaw sandbox explain                 # debug sandbox/tool-policy/elevated layering
```

## Maintenance discipline

- After ANY OpenClaw upgrade: run `refresh-catalog.sh`. If exit code 2, review diff and add annotations for new high-relevance pages.
- After hitting a production gotcha: write an annotation file, link it in `catalog.json`, bump `lastVerified` to today.
- Annotations older than 60 days: re-verify with `bash scripts/lookup.sh stale 60`. If still correct, bump `lastVerified` only.
- Never re-prose upstream docs in this skill. Cache them. Annotate the deltas.
