---
upstream: https://docs.openclaw.ai/providers/anthropic.md
relevance: jambot-critical
last-verified: 2026-05-23
audit_anchors: [16]
related_pages: [gateway__cli-backends, providers__index, providers__zai]
---

# Anthropic provider — JamBot annotation

## TL;DR

Three Anthropic lanes exist as of mid-2026:

| Lane | Type | Quota source | Use for |
|---|---|---|---|
| API key | `anthropic` | Pay-as-you-go | Direct API calls; pricey but reliable |
| `claude-cli` (OAuth) | `claude-cli` + `mode: "oauth"` | Pro/Max subscription | Interactive planning only — see 5h cap below |
| Bedrock | `anthropic-bedrock` | AWS billing | Enterprise — not used in JamBot |

The Apr 4 2026 cutover killed token extraction (see anchor-16). The `claude-cli` lane is the sanctioned replacement.

## When to use `claude-cli` mode in JamBot

JamBot's primary is GLM-5-turbo via z.ai (see anchor-21). The `claude-cli` lane is a **secondary** for tenants who have their own Pro/Max sub and want higher-stakes planning to escalate to Sonnet/Opus without paying API rates.

Use cases:
- Tenant wants a "human-grade" review pass on agent output before it ships
- One-off complex planning that benefits from Anthropic-class reasoning
- Cross-checking GLM output on edge cases

Don't use for:
- Routine heartbeat/cron work — see 5h cap
- Tools that need vision (claude-cli OAuth tier may lack vision quota)
- Multi-tenant load — each tenant needs their OWN Anthropic sub

## Config

```json5
{
  providers: {
    anthropic: {
      type: "claude-cli",
      mode: "oauth"
      // Shells out to local `claude -p` — see Docker note below
    }
  }
}
```

## Docker install caveat (CRITICAL for JamBot)

The official OpenClaw Docker image does **NOT** bundle the `claude` CLI. Per r/openclaw 1svmq20 (u/FFFrank +8): production setups have been "drop the container, spin up raw Debian VPS, install CLI globally, run session through tmux."

JamBot's multi-tenant Compose stack would need a custom layer that installs the `claude` CLI inside each tenant container before this provider works. Add to the per-tenant Dockerfile:

```dockerfile
RUN curl -fsSL https://claude.ai/install.sh | sh && \
    claude --version  # verify install
```

Then mount the tenant's `~/.claude/` auth directory if persisting across container restarts.

## 5-hour cap reality

Pro/Max subscriptions enforce a 5-hour rolling cap. Heartbeat crons running every 30s will exhaust this in ~10 minutes. **Reserve `claude-cli` for interactive paths only.** Route automated work through API providers (GLM-5-turbo, OpenRouter free, etc.).

## DeepSeek-style models — separate caveat

NOT specific to Anthropic but related: per r/openclaw 1r71you, **DeepSeek Reasoner** produces malformed tool calls in OpenClaw. DeepSeek v3.2 / Coder work fine. See `providers__deepseek.md`.

## Related JamBot files

- `audit-anchors/anchor-16-anthropic-subscription-cutover.md`
- `playbooks/migrate-to-claude-cli-provider.md`
- `overrides/glm5-turbo-pin.md`
- `overrides/openclaw-json-deltas.md`
