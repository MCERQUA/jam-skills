# Audit Anchors — v2026.4.20 → v2026.7.1

28 confirmed deltas between upstream docs and real OpenClaw behavior, in three waves:

- **1–15** — changelog audit, v2026.4.20 → v2026.5.2 (`docs/jambot/openclaw-skill-update-2026-05-04.md`)
- **16–21** — r/openclaw community deep-read, 2026-05-23
- **22–28** — the v2026.5.7 → v2026.7.1 delta audit, 2026-07-25 (upstream CHANGELOG.md + a full catalog rebuild, 464 → 761 pages)

JamBot runs **`2026.5.7`**. Anchors 22–28 describe what changes when that pin moves; anchors 1–21 describe behavior at or before the pin. When answering any question that touches one of these topics, **the audit anchor wins over upstream prose**.

## Source of truth

Full audit report: [`docs/jambot/openclaw-skill-update-2026-05-04.md`](../../../../docs/jambot/openclaw-skill-update-2026-05-04.md) (in MIKE-AI repo)
Changelog dump: `/tmp/openclaw-changelogs/all-changelogs.txt` (815KB, 3636 lines, all 23 release notes from 4.20 → 5.2)

## Schema

Each `anchor-NN-<slug>.md` has frontmatter:

```yaml
---
anchor: 14
slug: queue-mode-default-flipped
status: confirmed | partially-confirmed
introduced: v2026.4.29
changelog_line: 410
upstream_pages:
  - https://docs.openclaw.ai/concepts/queue.md
  - https://docs.openclaw.ai/concepts/queue-steering.md
old_behavior: "messages.queue.mode default = collect"
new_behavior: "default = steer with 500ms followup-fallback debounce"
skill_files_affected:
  - references/agent-runtime.md:194
---
```

Body: full evidence, JamBot impact, fix instructions for skill files.

## Anchor index

JamBot pin = `2026.5.7`. "Applies at pin" = true for the version we run today.

| # | Slug | Status | Version | Applies at pin |
|---|------|--------|---------|----------------|
| 1 | plugin-sdk-breaking-registerEmbeddedExtensionFactory | confirmed | v2026.4.24 | yes |
| 2 | memory-core-auto-activates | confirmed | v2026.5.2 | yes |
| 3 | strict-tool-allowlist-hard-error | confirmed | v2026.5.2 | yes |
| 4 | embedded-run-timeout-15s | partially-confirmed | v2026.5.2 | yes |
| 5 | per-file-bootstrap-caps | partially-confirmed | v2026.5.2 | yes — but 7.1 made caps per-agent (#84424) |
| 6 | compaction-trigger-and-new-keys | confirmed | v2026.4.26–4.27 | yes |
| 7 | meta-lastTouchedVersion-migration | confirmed | v2026.5.2 | yes |
| 8 | bonjour-disabled-by-default | confirmed | v2026.5.2 | yes |
| 9 | glm-5-consecutive-turn-fix | confirmed | v2026.5.2 | yes — see #27 for the GLM-5.2 era |
| 10 | anthropic-messages-scoping | confirmed | v2026.4.20 | yes |
| 11 | plugins-entries-vs-skills-entries | confirmed | v2026.5.2 | yes |
| 12 | external-plugin-migration | confirmed | v2026.5.2 | yes — BlueBubbles fully REMOVED in 5.12 |
| 13 | tools-exec-yolo-defaults-flip | confirmed | v2026.4.5 | yes |
| 14 | queue-mode-default-flipped | confirmed | v2026.4.29 | yes |
| 15 | rotateBytes-deprecated | confirmed | v2026.4.27 | yes |
| 16 | anthropic-subscription-cutover | confirmed | 2026-04-04 | yes |
| 17 | cve-2026-25253-gateway-bind | confirmed | patched upstream | yes |
| 18 | clawhavoc-supply-chain | confirmed | 2026-05 campaign | yes |
| 19 | openclaw-doctor-destructive | confirmed | ≤2026.6.x | yes — **scope-corrected by #25** |
| 20 | qmd-memory-default-shift | confirmed | community shift | yes |
| 21 | glm5-reliability-divergence | confirmed | community signal | yes — see #27 |
| 22 | gateway-fail-closed-non-loopback | confirmed | **v2026.5.17** | no — **blocks the upgrade** |
| 23 | pairing-and-trusted-proxy-hardening | confirmed | **v2026.5.12** | no — first release past the pin |
| 24 | database-first-sqlite-migration | confirmed | **v2026.6.5–6.9** | no — backup/snapshot impact |
| 25 | doctor-reworked-in-7.1 | confirmed | **v2026.7.1** | no — scopes #19 |
| 26 | agent-cron-scoping-and-protocol-v4 | confirmed | **v2026.5.19 / 7.1** | no |
| 27 | glm-5.2-and-zai-thinking-ladder | confirmed | **v2026.6.8–7.1** | no |
| 28 | openclaw-fleet-first-party-multi-tenant | confirmed | experimental upstream | n/a — informational |

## Upgrade reading order

Bumping `OPENCLAW_VERSION` past `2026.5.7`? Read in this order, then `playbooks/upgrade-5.7-to-7.x.md`:
**#22** (will the gateway even start) → **#23** (will it let anyone in) → **#26B** (will OVU's WS client still speak to it) → **#24** (is the backup still capturing the agent) → **#26A** (will tenant cron survive a staggered roll) → **#27** (retune the Z.AI breaker) → **#25** (doctor is safer now, rules unchanged).
