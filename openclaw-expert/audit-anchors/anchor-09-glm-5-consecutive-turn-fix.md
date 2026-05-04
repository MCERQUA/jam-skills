---
anchor: 9
slug: glm-5-consecutive-turn-fix
status: confirmed
introduced: v2026.5.2
changelog_line: 69
upstream_pages:
  - https://docs.openclaw.ai/providers/zai.md
  - https://docs.openclaw.ai/providers/glm.md
old_behavior: "GLM-5 / z.ai consecutive turns reset Pi state"
new_behavior: "v5.2 preserves prior context for z.ai direct, openrouter z-ai/*, in-house GLM gateways"
skill_files_affected:
  - "references/models-and-providers.md (Z.AI section)"
---

# Anchor #9 — GLM-5 consecutive-turn context preservation fix

## What changed

v5.2 line 69: "Agents/compaction: keep prior context on consecutive turns against z.ai-style providers (z.ai direct, openrouter z-ai/*, in-house GLM gateways), avoiding accidental Pi state reset after successful turns. (#76056)"

## Why it matters for JamBot

JamBot's standing config is GLM-5-turbo primary (temporary inversion from MiniMax — see memory `glm-primary-temporary-swap`). On 5.1 and earlier, every other GLM turn lost prior context, making multi-turn conversations feel like the agent forgot what just happened. v5.2 fixes this.

This explains the long-standing "GLM agents seemed to reset between turns on 5.1" behavior pattern Mike noticed across multiple clients.

## Affected providers

- `zai` (direct Z.AI API)
- `openrouter` with `z-ai/*` model paths
- In-house GLM gateways (custom provider configs hitting GLM-compatible endpoints)

## Fix instruction

`annotations/providers__zai.md` and `annotations/providers__glm.md`:
- Note the v5.2 fix
- Cross-reference memory `glm-primary-temporary-swap.md`
- Add "if multi-turn context loss observed, verify gateway version ≥ 5.2"
