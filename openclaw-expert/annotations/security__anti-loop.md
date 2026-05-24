---
upstream: https://docs.openclaw.ai/security/anti-loop.md
relevance: jambot-critical
last-verified: 2026-05-23
audit_anchors: []
related_pages: [security__prompt-injection, concepts__heartbeat, concepts__compaction]
---

# Anti-loop rules — JamBot annotation

## Canonical anti-loop block

Drop verbatim into every tenant's AGENTS.md or SOUL.md. Sourced from r/openclaw 1riiglv (OpenClaw 102) and validated across multiple production agents.

```markdown
## Anti-Loop Rules

- If a task fails twice with the same error, STOP and report to the operator.
  Do not retry a third time with the same approach.

- Never make more than 5 consecutive tool calls without checking in with the
  operator. If the goal needs more, batch progress: "I've done X, Y, Z; about
  to do W, A, B. OK to proceed?"

- If repeating an action with the same result (3+ times), stop and explain
  what's happening. This catches infinite loops where the agent thinks each
  iteration is "different" but they're not.

- If a command times out, report. Do NOT silently re-run. Timeouts are signal.

- When context feels stale ("did the user actually ask this?", "what was the
  goal again?"), ASK rather than guess. Cost of asking < cost of doing the
  wrong thing.

- If a tool returns an error message you don't recognize, stop and quote it
  verbatim to the operator. Do not "interpret" cryptic errors with confident
  fixes.
```

## Why this matters for JamBot

GLM-5-turbo (JamBot primary) is more sensitive than Sonnet to long-session rule degradation (see anchor-21). Anti-loop rules are the safety net that limits the blast radius when a model starts drifting.

The "5 consecutive tool calls" rule is particularly important on voice tenants — voice users can't easily interrupt a runaway agent. Forced check-in points prevent the agent from burning a tenant's budget on a misunderstood request.

## Production signal — the garlic incident (r/openclaw 1tcec4m)

A user's OpenClaw bought groceries via Instacart MCP for 3 months without incident, then ordered 2 KG of garlic because the unit dropdown defaulted to kg. The agent was "stable" until an edge case hit.

**Implication:** stable behavior is not safe behavior. Anti-loop rules + human-in-the-loop sampling are needed even on workflows that have run cleanly for months.

JamBot rule: any tool call with a quantity > N or a unit ≠ expected MUST require explicit human confirmation, regardless of how stable the workflow has been. Bake this into the tool wrapper, not just the prompt.

## Related JamBot files

- `audit-anchors/anchor-21-glm5-reliability-divergence.md` (model sensitivity context)
- `annotations/concepts__heartbeat.md` (anti-loop especially important in unattended cron)
- `annotations/security__prompt-injection.md` (companion block)
