---
anchor: 6
slug: compaction-trigger-and-new-keys
status: confirmed
introduced: v2026.4.7 (provider) + v2026.4.26/4.27 (new keys)
changelog_lines: [378, 1058, 903]
upstream_pages:
  - https://docs.openclaw.ai/concepts/compaction.md
  - https://docs.openclaw.ai/reference/session-management-compaction.md
old_behavior: "compaction.mode = 'default' | 'safeguard'; triggers near context full"
new_behavior: "default trigger ≈ 68% prompt usage; auto-retry on failure; 3 new keys"
skill_files_affected:
  - "references/gateway-configuration.md:113"
  - "references/sessions-and-context.md:148-156"
  - "references/memory-system.md:71-76"
---

# Anchor #6 — Compaction triggers + new keys + pluggable provider

## Confirmed new keys

| Key | Default | Introduced | Changelog line |
|-----|---------|-----------|----------------|
| `agents.defaults.compaction.midTurnPrecheck` | opt-in | v4.27 | 378 |
| `agents.defaults.compaction.maxActiveTranscriptBytes` | opt-in | v4.26 | 1058 |
| `agents.defaults.compaction.memoryFlush.model` | inherits primary | v4.27 | 903 |
| `agents.defaults.compaction.provider` | unset | v4.7 | (4.7) |

Setting `provider` automatically forces `mode: "safeguard"`.

## Behaviors

- `midTurnPrecheck` detects tool-loop context pressure and triggers compaction before the next tool call instead of waiting for end-of-turn
- `maxActiveTranscriptBytes` preflight runs normal local compaction when the active JSONL grows too large; **requires `truncateAfterCompaction: true`** to function
- `memoryFlush.model` lets pre-compaction memory flush use an exact override (e.g. `ollama/qwen3:8b`) without inheriting the active session fallback chain

## Production observation (NOT confirmed in changelog)

- "68% prompt usage" trigger — consistent with `reserveTokensFloor: 24000` default + small `keepRecentTokens` default; NOT a hardcoded 68%
- Auto-retry on compaction failure — implemented via run-level retry loop

## Related

- `/compact` slash command accepts guidance: `/compact Focus on API decisions`
- `/new` resets without compacting (preserve full history on disk, fresh conversation)
- v4.20 line 2395: events renamed `compaction_start` / `compaction_end`

## Fix instruction

`annotations/concepts__compaction.md`:
1. Document the 4 new keys with introduction versions
2. Note `provider` registration auto-forces `mode: "safeguard"`
3. Note `maxActiveTranscriptBytes` requires `truncateAfterCompaction: true`
4. Flag 68% threshold as production-observed, not changelog-confirmed
