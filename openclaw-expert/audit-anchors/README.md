# Audit Anchors — v2026.4.20 → v2026.5.2

15 confirmed deltas between upstream docs and production OpenClaw 5.2 behavior. When answering any question that touches one of these topics, **the audit anchor wins over upstream prose**.

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

| # | Slug | Status |
|---|------|--------|
| 1 | plugin-sdk-breaking-registerEmbeddedExtensionFactory | confirmed |
| 2 | memory-core-auto-activates | confirmed |
| 3 | strict-tool-allowlist-hard-error | confirmed |
| 4 | embedded-run-timeout-15s | partially-confirmed |
| 5 | per-file-bootstrap-caps | partially-confirmed |
| 6 | compaction-trigger-and-new-keys | confirmed |
| 7 | meta-lastTouchedVersion-migration | confirmed |
| 8 | bonjour-disabled-by-default | confirmed |
| 9 | glm-5-consecutive-turn-fix | confirmed |
| 10 | anthropic-messages-scoping | confirmed |
| 11 | plugins-entries-vs-skills-entries | confirmed |
| 12 | external-plugin-migration | confirmed |
| 13 | tools-exec-yolo-defaults-flip | confirmed |
| 14 | queue-mode-default-flipped | confirmed |
| 15 | rotateBytes-deprecated | confirmed |
