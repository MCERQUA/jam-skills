---
upstream: https://docs.openclaw.ai/providers/index.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: [9, 10]
related_pages: [providers__zai, providers__minimax, providers__glm, providers__ollama]
---

# Provider directory — JamBot annotation

## What docs say (TL;DR)

56+ providers indexed. Each has its own page with auth/model/knob specifics.

## JamBot-specific provider rules

| Rule | Why |
|------|-----|
| **MiniMax = primary, GLM = fallback** | Standing rule, see memory `feedback_hermes_primary_llm` |
| **Groq = TTS ONLY**, never LLM | Standing rule, see memory `feedback_never_use_groq_for_llm` |
| **Z.AI requires `thinkingDefault: "off"`** | See `overrides/openclaw-json-deltas.md` |
| **Custom anthropic-compat providers MUST set `api: "anthropic-messages"`** | Anchor #10 — auto-default removed v4.20 |

## Currently-active providers in JamBot

| Role | Provider | Notes |
|------|----------|-------|
| LLM primary (TEMPORARY override) | `zai` (GLM-5-turbo) | Per memory `glm-primary-temporary-swap` |
| LLM fallback | `zai` second account | `ZAI_FALLBACK_API_KEY` |
| LLM standing rule | `minimax` (M2.7-highspeed) | Awaiting billing restore |
| LLM mike-only beta | `ollama` cloud (`minimax-m2.7:cloud`) | Per memory `ollama-cloud-minimax` |
| TTS | Supertonic + ElevenLabs | shared network container |
| TTS (legacy) | Groq | TTS ONLY, never LLM |
| Embedding | (per memory engine) | memory-core uses BM25+vector |

## Provider list expansion (v4.5 → v5.2)

The provider list grew from ~26 (Mar 2026) → 56+ (May 2026). Notable additions:

- **NVIDIA** (v4.29 line 417)
- **DeepInfra** (v4.27 line 803)
- **Cerebras** — moved to bundled plugin (v4.26 line 1049)
- **Arcee AI**, **Qwen**, **Fireworks**, **StepFun**, **Mantle** (v4.5)
- **Cloudflare AI gateway**, **Vercel AI gateway**, **LiteLLM** — meta-providers
- **GitHub Copilot** as LLM + embedding provider

JamBot doesn't actively use any of these but they're available if needed.

## Provider transport gotcha (anchor #10)

If wiring a custom provider that's anthropic-compatible:
```json5
{ providers: { custom: { api: "anthropic-messages", ... } } }
```
Without explicit `api`, v4.20+ no longer auto-defaults to anthropic-messages — request will hit the wrong transport silently.

## Related JamBot files

- `annotations/providers__{zai,minimax,glm}.md`
- `audit-anchors/anchor-{9,10}.md`
- Memory: `glm-primary-temporary-swap`, `ollama-cloud-minimax`, `feedback_hermes_primary_llm`, `feedback_never_use_groq_for_llm`
- `overrides/openclaw-json-deltas.md` — Z.AI thinkingDefault rule
