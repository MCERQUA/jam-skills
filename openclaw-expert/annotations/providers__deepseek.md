---
upstream: https://docs.openclaw.ai/providers/deepseek.md
relevance: jambot-medium
last-verified: 2026-07-25
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

---

<!-- verification-stamp -->
## Verification — 2026-07-25

**Method (be precise about what this stamp does and does not mean):**

- Every config key this file asserts was checked against the **live schema of the version JamBot actually runs** — `openclaw config schema` inside `openclaw-test-dev` at `2026.5.7`, 6,441 schema paths.
- Upstream page re-fetched as Markdown on 2026-07-25 (`scripts/fetch-page.sh --no-cache`).
- **Not done:** the prose was not re-read line-by-line against the 7.x docs. Upstream is at `2026.7.1`; this file is verified for our pin, not for upstream HEAD.

**No config keys asserted here** — nothing schema-checkable; prose-only annotation.

If you change this file, re-run `python3 scripts/sync-annotations.py` so `lastVerified` reaches `catalog.json`.
