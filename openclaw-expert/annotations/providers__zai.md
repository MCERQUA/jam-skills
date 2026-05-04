---
upstream: https://docs.openclaw.ai/providers/zai.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: [9, 10]
related_pages: [providers__glm, providers__minimax, providers__index]
---

# Z.AI provider — JamBot annotation

## What docs say (TL;DR)

Provider id `zai`. Auth via `ZAI_API_KEY` bearer token. Default model `zai/glm-5.1`. Auto-detection via `zai-api-key` onboarding picks regional endpoint from key prefix. Forward resolution: unknown `glm-5*` synthesizes metadata from `glm-4.7` template. Tool-call streaming default-on. `glm-4.6v` auto-resolves for vision. `preserveThinking` opt-in.

## Anchor #9 — GLM-5 consecutive-turn fix (v5.2)

v5.2 line 69: keep prior context on consecutive turns against z.ai-style providers (z.ai direct, openrouter `z-ai/*`, in-house GLM gateways). Pre-5.2 every other turn lost prior context — explains the long-standing "GLM agents seemed to reset between turns" pattern.

If you observe multi-turn context loss on GLM clients: verify gateway version ≥ 5.2.

## Anchor #10 — Anthropic-messages scoping (v4.20)

Custom providers using anthropic-compat transport MUST explicitly set `api: "anthropic-messages"`. Auto-default removed v4.20.

(Z.AI direct doesn't need this since it's a first-class provider, but documented here for cross-reference if a JamBot client wires GLM through a custom provider proxy.)

## JamBot's standing config — TEMPORARY override

Per CLAUDE.md + memory `glm-primary-temporary-swap`: ALL JamBot openclaw clients (except dev-owned stilo) + hermes-test-dev currently run **GLM-5-turbo PRIMARY** with **GLM-5-turbo FALLBACK on a second Z.AI account** (`ZAI_FALLBACK_API_KEY`).

Reason: MiniMax coding-plan billing locked out. Revert to MiniMax-primary when billing restored.

The standing rule (MiniMax=primary, GLM=fallback) still applies — this is an operational override.

## Standing rule (NOT current state)

**MiniMax M2.7-highspeed = PRIMARY. GLM-5-turbo = FALLBACK.** NEVER use GLM as primary in a non-temporary config. See `feedback_hermes_primary_llm.md` in memory.

## Z.AI specifics worth knowing

- `thinkingDefault: "off"` REQUIRED in JamBot openclaw.json — without it, Z.AI returns thinking-only blocks with NO visible text (see `overrides/openclaw-json-deltas.md`)
- `preserveThinking: true` opt-in per-model — replays full historical `reasoning_content`, increases prompt tokens
- `tool_stream: false` to disable tool-call streaming (default true)
- `glm-4.6v` auto-vision — image understanding without separate config

## Related JamBot files

- `audit-anchors/anchor-{9,10}.md`
- `overrides/openclaw-json-deltas.md` — thinkingDefault rule
- `glm-primary-temporary-swap.md` (in memory) — current operational state
- `feedback_hermes_primary_llm.md` (in memory) — standing rule
