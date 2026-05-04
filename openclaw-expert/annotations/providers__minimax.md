---
upstream: https://docs.openclaw.ai/providers/minimax.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: []
related_pages: [providers__zai, providers__glm, providers__index]
---

# MiniMax provider — JamBot annotation

## What docs say (TL;DR)

Provider id `minimax`. Auth via `MINIMAX_API_KEY`. Models include MiniMax M2.7-highspeed. Standard openai-completions transport.

## Standing rule

**MiniMax M2.7-highspeed = PRIMARY. GLM-5-turbo = FALLBACK** in JamBot. The rule has been violated 15+ times historically — see `feedback_hermes_primary_llm.md` in memory.

## CURRENT operational override (TEMPORARY — 2026-04-20+)

GLM-5-turbo currently primary across all clients except dev-owned stilo. Reason: MiniMax coding-plan billing locked out. Revert to MiniMax-primary when billing restored. See memory `glm-primary-temporary-swap`.

## Key behaviors

### Empty `chat.final` failure mode

MiniMax-M2.7-highspeed returns `chat.final` with zero text 15+ times per 30 minutes under load. The 13-fix recovery cascade in `playbooks/debug-empty-final.md` handles this.

This is the SINGLE MOST IMPORTANT thing to know about MiniMax in JamBot's context.

### v4.20 line 2384 (security): MINIMAX_API_HOST workspace env injection BLOCKED

Pre-4.20, agents could try to inject `MINIMAX_API_HOST` env var to redirect MiniMax traffic. v4.20 blocks this entirely. Skill should NOT mention this as a knob.

### v4.5: MiniMax Search added (web_search backend)

`web_search` can route to MiniMax Search alongside Perplexity, Brave, Gemini, Grok, Kimi. See `tools/web.md`.

## Ollama Cloud MiniMax — live on mike only (2026-04-20)

Free MiniMax via Ollama partnership: `https://ollama.com/v1`, `minimax-m2.7:cloud`, `openai-completions`. Primary on mike.jam-bot.com w/ GLM fallbacks. Rollout gated on real voice latency — DO NOT propagate platform-wide yet. Rollback + gotchas: memory `ollama-cloud-minimax`.

## Related JamBot files

- `playbooks/debug-empty-final.md` — empty-final recovery cascade
- `feedback_hermes_primary_llm.md` (memory) — standing rule
- `glm-primary-temporary-swap.md` (memory) — current operational state
- `ollama-cloud-minimax.md` (memory) — Ollama partnership rollout
- `feedback_never_use_groq_for_llm.md` (memory) — Groq=TTS only, never LLM
