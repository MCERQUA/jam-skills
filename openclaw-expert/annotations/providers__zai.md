---
upstream: https://docs.openclaw.ai/providers/zai.md
relevance: jambot-critical
last-verified: 2026-05-23
audit_anchors: [9, 10, 21]
related_pages: [providers__glm, providers__minimax, providers__index, providers__anthropic]
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

## Anchor #21 — Community reliability divergence (added 2026-05-23)

Community signal on GLM-5/5.1 diverges in mid-2026: some users (1sdd32v OP) call it "absolute garbage for agentic tasks"; many others (Blade999666, TacomaKMart, PureSignalLove, Strange_Squirrel_886) run it fine 24/7. Hypothesis: GLM-5 is more rule-load sensitive than Sonnet — tenants with bloated system prompts degrade faster.

**Triage when a JamBot tenant reports "GLM weird today":**
1. Check rule budget (SOUL.md + AGENTS.md + MEMORY.md + TOOLS.md size — see anchor-05)
2. Verify anti-loop block is present (see `annotations/security__anti-loop.md`)
3. Confirm gateway v5.2 + `meta.lastTouchedVersion` migration ran (see anchor-7)
4. Only AFTER 1-3: escalate to fallback chain — NOT direct-Anthropic-API as first reaction

See `overrides/glm5-turbo-pin.md` for the full triage + fallback chain.

## JamBot's standing config — TEMPORARY override

Per CLAUDE.md + memory `glm-primary-temporary-swap`: ALL JamBot openclaw clients (except dev-owned stilo) + hermes-test-dev currently run **GLM-5-turbo PRIMARY** with **GLM-5-turbo FALLBACK on a second Z.AI account** (`ZAI_FALLBACK_API_KEY`).

Reason: MiniMax coding-plan billing locked out. Revert to MiniMax-primary when billing restored.

The standing rule (MiniMax=primary, GLM=fallback) still applies — this is an operational override.

**2026-05-23 addition:** when MiniMax billing is restored and we move back, add a non-z.ai third fallback (Haiku via direct Anthropic API or `claude-cli` per anchor-16) — this is the long-standing gap when both z.ai accounts fail together during a z.ai tail-latency window.

## Standing rule (NOT current state)

**MiniMax M2.7-highspeed = PRIMARY. GLM-5-turbo = FALLBACK.** NEVER use GLM as primary in a non-temporary config. See `feedback_hermes_primary_llm.md` in memory.

## Z.AI specifics worth knowing

- `thinkingDefault: "off"` REQUIRED in JamBot openclaw.json — without it, Z.AI returns thinking-only blocks with NO visible text (see `overrides/openclaw-json-deltas.md`)
- `preserveThinking: true` opt-in per-model — replays full historical `reasoning_content`, increases prompt tokens
- `tool_stream: false` to disable tool-call streaming (default true)
- `glm-4.6v` auto-vision — image understanding without separate config

## Cheap-primary validation from community

- r/openclaw 1qzyibu (u/TacomaKMart +11): GLM Coding Plan $3/month, first month often $0.99
- r/openclaw 1sbshpu (u/PureSignalLove +9): "GLM 5.1 / MiniMax 2.7 / Tri-* are 1/10th the price or less"
- r/openclaw 1sbshpu (u/mehdiweb +9): $140 → $12/mo bill drop after moving off Anthropic API to cheap-primary

## Related JamBot files

- `audit-anchors/anchor-09-glm-5-consecutive-turn-fix.md`
- `audit-anchors/anchor-10-anthropic-messages-scoping.md`
- `audit-anchors/anchor-21-glm5-reliability-divergence.md`
- `overrides/glm5-turbo-pin.md` (new — version-pin policy + fallback chain)
- `overrides/openclaw-json-deltas.md` — thinkingDefault rule
- `glm-primary-temporary-swap.md` (in memory) — current operational state
- `feedback_hermes_primary_llm.md` (in memory) — standing rule
