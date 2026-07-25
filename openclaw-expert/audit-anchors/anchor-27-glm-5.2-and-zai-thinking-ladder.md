---
anchor: 27
slug: glm-5.2-and-zai-thinking-ladder
status: confirmed
introduced: v2026.6.8 (GLM-5.2 catalog) / v2026.6.10 (thinking ladder) / v2026.7.1 (429 semantics)
changelog_line: "CHANGELOG.md 2026.6.8 — 'Providers/models: add GLM-5.2 support and Claude Haiku 4.5 catalog entries...(#92796)' | 2026.6.10 — 'Expands zai/glm-5.2 thinking choices beyond binary on/off and sends high or max requests as the intended Z.AI reasoning effort. (PR #94136)' / 'Prevents bundled Z.ai GLM-5 models from falling through to OpenAI and producing misleading API-key errors, so they use Z.AI by default. (PR #94461)' | 2026.7.1 — 'Z.AI and similar HTTP 429 responses now distinguish temporary service overload from ordinary rate limiting and preserve provider-supplied retry timing. (#98165)'"
upstream_pages:
  - https://docs.openclaw.ai/providers/zai
  - https://docs.openclaw.ai/tools/thinking
  - https://docs.openclaw.ai/plugins/reference/zai
old_behavior: "GLM-5 era. `thinkingDefault` is effectively binary (off/on) for Z.AI models; JamBot forces `thinkingDefault: \"off\"` because Z.AI/GLM otherwise returns thinking-only blocks with no visible text. `providers/glm.md` is a distinct doc page. GLM-5 bundled models could fall through to OpenAI and emit misleading API-key errors."
new_behavior: "GLM-5.2 lands in the catalog (6.8). Thinking choices for `zai/glm-5.2` expand beyond binary on/off — off/low/high/max mapped to Z.AI reasoning effort (6.10, 7.1). Bundled Z.AI GLM-5 models no longer fall through to OpenAI (6.10). Z.AI 429s now distinguish temporary overload from rate limiting and honor provider retry timing (7.1). Docs consolidated GLM under Z.AI in 5.22 — `providers/glm.md` no longer exists as its own page."
skill_files_affected:
  - overrides/glm5-turbo-pin.md
  - overrides/openclaw-json-deltas.md
  - audit-anchors/anchor-09-glm-5-consecutive-turn-fix.md
  - audit-anchors/anchor-21-glm5-reliability-divergence.md
sources:
  - https://github.com/openclaw/openclaw/pull/92796
  - https://github.com/openclaw/openclaw/pull/94136
  - https://github.com/openclaw/openclaw/pull/94461
  - https://github.com/openclaw/openclaw/pull/98165
---

# Anchor #27 — GLM-5.2, the Z.AI thinking ladder, and 429 semantics (v2026.6.8 → 7.1)

## Why this is an anchor and not just news

Two long-standing JamBot facts get *narrower* on 6.8+:

**1. `thinkingDefault: "off"` is no longer a binary escape hatch.**
Our template pins `thinkingDefault: "off"` because Z.AI/GLM otherwise returns thinking-only blocks with no visible text — one of the four non-negotiable config fields (CLAUDE.md). From 6.10, `zai/glm-5.2` supports a real ladder — **off / low / high / max** — mapped onto Z.AI's reasoning-effort parameter, and 7.1 exposes those choices for trusted official external providers before full runtime activation.

`"off"` remains the correct JamBot default: the visible-text failure is a real production burn, and the voice path has no tolerance for an empty final. But on 6.10+ the answer to "can we get reasoning without losing visible text?" changes from *no* to *test `low` on one tenant* — and anyone answering from the old anchor alone will give the stale answer.

**2. GLM docs consolidated under Z.AI (5.22).**
`https://docs.openclaw.ai/providers/glm.md` is gone; the content lives under `providers/zai` and the new `plugins/reference/zai` page. The catalog rebuild of 2026-07-25 dropped `providers__glm` accordingly. Any reference to a standalone GLM provider page is stale — route to `providers__zai`.

## The reliability picture (updates anchors #9 and #21)

- **6.10 (#94461)** — bundled Z.AI GLM-5 models no longer fall through to OpenAI and emit misleading "API key" errors. This is directly relevant to anchor #21's triage advice: a chunk of the community's "GLM-5 is unreliable" signal was a *routing* bug producing a provider error that pointed at the wrong provider. Anchor #21's rule — rule budget → anti-loop → version migration BEFORE panic-switching the primary — is reinforced, not weakened: this was a version-migration fix.
- **7.1 (#98165)** — Z.AI 429s now distinguish temporary service overload from ordinary rate limiting and preserve provider-supplied retry timing. Our Z.AI circuit breaker (max 2 trips / 5 min, per `openclaw-perf`) was tuned against the old undifferentiated 429 behavior. On 7.x it may trip on transient overload that the provider already told us how long to wait for. **Re-tune the breaker after the upgrade rather than porting the current numbers forward blind.**
- **7.1 (#97540)** — Z.AI endpoint/model detection now fails gracefully on oversized or endless error responses instead of exhausting host memory. Given the 2026-07-25 box-OOM incident, this is a real (if indirect) memory-pressure fix worth having.

## Still true, do not re-derive

Z.AI stays on the **subscription** endpoint `api.z.ai/api/anthropic` with `api: "anthropic-messages"` and provider `zai` — never `open.bigmodel.cn`. Nothing in the 5.7→7.1 delta changes that; see `overrides/glm5-turbo-pin.md` and anchor #10.
