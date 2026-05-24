---
anchor: 16
slug: anthropic-subscription-cutover
status: confirmed
introduced: 2026-04-04
changelog_line: null
upstream_pages:
  - https://docs.openclaw.ai/providers/anthropic.md
  - https://docs.openclaw.ai/gateway/cli-backends.md
old_behavior: "Anthropic Pro/Max subscription OAuth tokens could be extracted and used to feed third-party harnesses (OpenClaw, etc.) — subscription quota covered programmatic use."
new_behavior: "On Apr 4 2026 Anthropic cut OAuth-token extraction; Pro/Max subs no longer feed harnesses through that path. SANCTIONED alternative: OpenClaw shells out to the local `claude` CLI with `-p` via a `claude-cli` provider type (`mode: \"oauth\"`). 5-hour Pro/Max cap still applies — kills cron-on-sub setups."
skill_files_affected:
  - annotations/providers__anthropic.md (new — claude-cli config + Docker caveat)
  - playbooks/migrate-to-claude-cli-provider.md (new)
  - overrides/openclaw-json-deltas.md (note JamBot already routes around this via z.ai)
sources:
  - https://reddit.com/comments/1sbshpu (637/429 — initial cutover announcement)
  - https://reddit.com/comments/1svmq20 (253/196 — Anthropic clarified, claude-cli lane sanctioned)
---

# Anchor #16 — Anthropic subscription cutover (Apr 4 2026)

## What changed

**Apr 4 2026:** Anthropic terminated the OAuth-token-extraction pathway that let OpenClaw and similar harnesses run on a Pro/Max subscription. Affected users got a one-time credit + 30% bundle discount; opt-out users got full refund.

**Apr–May 2026 follow-up (r/openclaw 1svmq20):** Anthropic clarified that shelling out to the local `claude` CLI with `-p` is **sanctioned**. OpenClaw added a `claude-cli` provider type to wrap this; quote from upstream docs (per Reddit confirmation): *"OpenClaw-style Claude CLI usage is allowed again, so OpenClaw treats claude -p usage as sanctioned for this integration unless Anthropic publishes a new policy."*

## Why it matters for JamBot

JamBot's standing primary is GLM-5-turbo via Z.AI, so the cutover does NOT block the primary path. But the `claude-cli` provider lane is now the right way to add an Anthropic fallback for a tenant who has their own Pro/Max sub and wants higher-stakes planning to escalate to Sonnet/Opus without paying API rates.

**Critical caveat for JamBot:** the official OpenClaw Docker image does NOT ship the `claude` CLI. Per r/openclaw user u/FFFrank (+8), production setups have been "drop the container, spin up raw Debian VPS, install CLI globally, run session through tmux." JamBot's multi-tenant Compose stack would need a custom layer that installs the CLI inside each tenant container before this provider lane works. Document the cost trade-off explicitly per tenant.

**Cron rule:** the Pro/Max 5-hour cap kills any heartbeat/cron job routed through `claude-cli`. Reserve `claude-cli` for interactive planning only; route automated work through API providers (GLM-5-turbo, OpenRouter free, etc.).

## Config snippet (sanctioned provider lane)

```json5
{
  providers: {
    anthropic: {
      type: "claude-cli",
      mode: "oauth"
      // shells out to local `claude -p` — requires CLI installed in container
    }
  }
}
```

## References

- Reddit thread 1sbshpu — the cutover announcement + community pricing-shock reaction
- Reddit thread 1svmq20 — the clarification + the `claude-cli` provider config
- GitHub issue cited: `openclaw/openclaw#66874` (per u/mehdiweb +13)
- u/mehdiweb (+9 on 1sbshpu): moved 85% of workflows to Haiku, bill dropped $140 → $12/mo — validates JamBot's GLM-5-turbo primary choice
- u/PureSignalLove (+9 on 1sbshpu): "GLM 5.1, MiniMax 2.7, Tri-* are 1/10th the price or less"
