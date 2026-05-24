# GLM-5-turbo primary — JamBot version pin + fallback chain

JamBot pins `zai/glm-5-turbo` as primary across tenant agents. This document explains why, captures the community signal divergence (per anchor-21), and defines the fallback chain.

## Why GLM-5-turbo primary

- **Cost:** roughly 1/10th of Anthropic API per token (per r/openclaw 1sbshpu u/PureSignalLove)
- **Subscription model:** GLM Coding Plan $3/month (first month often $0.99) with effectively unlimited prompts (per r/openclaw 1qzyibu u/TacomaKMart)
- **JamBot z.ai routing:** Account A primary + Account B fallback both via `https://api.z.ai/api/anthropic` (Anthropic-messages protocol facade)
- **Hermes-style HERMES.md detection isn't a risk here** — JamBot uses OpenClaw, not Hermes; we don't trip the Apr 4 OAuth-extraction policy (anchor-16)
- **MiniMax was earlier primary; rolled back to GLM** — see memory `glm-primary-temporary-swap` for the timeline

## Community divergence to keep in mind

Per anchor-21, community reports on GLM-5/5.1 quality DIVERGE sharply:
- Positive: TacomaKMart, Blade999666, PureSignalLove, Strange_Squirrel_886 — running fine 24/7
- Negative: OP of 1sdd32v migrated off, called GLM "absolute garbage" for agentic tasks

Hypothesis: GLM-5 sensitivity to rule load is higher than Sonnet. Tenants with bloated SOUL.md / many skills / weak anti-loop rules will hit this more often.

**JamBot policy when a tenant reports "GLM weird today":**
1. Triage per anchor-21 (rule budget, anti-loop, version migration state)
2. Do NOT panic-switch the standing primary
3. If sustained — escalate to fallback chain (below), not direct-to-Anthropic

## Version pin

Z.AI runs server-side updates silently. We don't get to pin to a specific model build the way local models allow. The pin is therefore at the **provider level**, not model-version level:

```json5
{
  providers: {
    zai: {
      type: "anthropic",        // anthropic-messages protocol
      base_url: "https://api.z.ai/api/anthropic",
      api_key: "${ZAI_API_KEY}", // account A
    },
    "zai-fallback": {
      type: "anthropic",
      base_url: "https://api.z.ai/api/anthropic",
      api_key: "${ZAI_API_KEY_B}",  // account B, same endpoint
    }
  },
  agents: {
    defaults: {
      model: "zai/glm-5-turbo",
      fallbacks: [
        "zai-fallback/glm-5-turbo",
        "anthropic/claude-haiku-4-5"     // see below
      ]
    }
  }
}
```

## Fallback chain rationale

| Tier | Provider | Cost | Why |
|---|---|---|---|
| Primary | `zai/glm-5-turbo` account A | $3/mo subscription | Cheap, unlimited |
| Fallback 1 | `zai/glm-5-turbo` account B | $3/mo subscription | Same model, different account, dodges single-account quota throttle |
| Fallback 2 | `anthropic/claude-haiku-4-5` | API pay-per-use | Non-z.ai escape hatch when both A+B fail together (z.ai tail-latency outage) |

**Why Haiku not Sonnet:** Haiku is ~4x cheaper than Sonnet at similar tool-use reliability. When fallback fires, it's usually a brief z.ai outage; we just need to keep the conversation moving. Sonnet is reserved for explicit escalation via `claude-cli` provider (anchor-16) on tenants who want it.

## Known recurring failure mode (per SKILL.md §1A)

When z.ai tail latency exceeds the openclaw 45s lane timeout (happens ~every couple of days for ~5min windows), BOTH primary and fallback-1 fail together because both ARE z.ai. The non-z.ai fallback (Haiku via direct Anthropic API) handles these windows.

Implementation note: this requires `credential-pools` to do the rotation cleanly. See `audit-anchors/anchor-09-glm-5-consecutive-turn-fix.md` for the multi-turn context preservation in v5.2 that makes pool rotation safe.

## When to bump the standing primary

NOT casually. The standing primary moved MiniMax → GLM-5 once; each move is a multi-tenant change requiring:

1. **Empirical evidence** — sustained quality drop or sustained cost overrun on 3+ tenants
2. **Mike approval** — production-affecting change per CLAUDE.md
3. **Documented in memory** — update `glm-primary-temporary-swap.md` with the rationale
4. **Staged rollout** — single tenant first for 1 week, then 50% of tenants for 1 week, then all

## References

- `audit-anchors/anchor-09-glm-5-consecutive-turn-fix.md`
- `audit-anchors/anchor-16-anthropic-subscription-cutover.md`
- `audit-anchors/anchor-21-glm5-reliability-divergence.md`
- `annotations/providers__zai.md`
- `annotations/providers__anthropic.md`
- Memory: `glm-primary-temporary-swap.md`
- SKILL.md §1A "Current operational state"
