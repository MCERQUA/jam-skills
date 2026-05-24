---
upstream: https://docs.openclaw.ai/providers/deepseek.md
relevance: jambot-medium
last-verified: 2026-05-23
audit_anchors: []
related_pages: [providers__index, providers__zai, providers__anthropic]
---

# DeepSeek provider — JamBot annotation

## TL;DR

DeepSeek family is mixed — some variants work fine with OpenClaw tool-use, the **Reasoner** variant specifically does not.

| Variant | Tool calls | Notes |
|---|---|---|
| DeepSeek v3.2 / v4 | OK | Cheap-and-decent backup for tool-driven workflows |
| DeepSeek Coder | OK | Code-specific tasks |
| **DeepSeek Reasoner** | **BROKEN** | Produces malformed tool calls in OpenClaw (r/openclaw 1r71you) |

## Why JamBot cares

Not currently in the JamBot primary or fallback chain (we run GLM-5-turbo, see anchor-21). DeepSeek is a candidate for:
- Cheap secondary on cost-sensitive tenants
- OpenRouter free-tier rotation when a `*-free` DeepSeek variant is available

If we ever wire DeepSeek into a tenant chain, **explicitly exclude Reasoner**. Whitelist the variant in `providers.<n>.allowed_models` rather than allowing the full DeepSeek catalog.

## Cost caveat (per r/openclaw 1sdd32v)

MiMo V2 Pro Token Plan ($16/mo) reportedly blew through monthly quota in 1 day because credit deducts on session-history/bootstrap/tool-outputs/cache. **JamBot's bootstrap-cap design** (TOOLS.md ≤ 24K chars, MEMORY.md ≤ 10.5K chars — see anchor-05) is the right defense against this class of surprise on token-plan providers. Same caveat applies if we add a DeepSeek token plan.

## Related JamBot files

- `audit-anchors/anchor-05-per-file-bootstrap-caps.md`
- `annotations/providers__index.md`
