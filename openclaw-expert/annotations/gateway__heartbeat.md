---
upstream: https://docs.openclaw.ai/gateway/heartbeat.md
relevance: jambot-high
last-verified: 2026-05-23
audit_anchors: [16]
related_pages: [concepts__agent, concepts__queue, security__anti-loop, automation__index]
---

# Heartbeat — JamBot annotation

## What the docs say

Heartbeat is a recurring cron-driven prompt that wakes the agent on a schedule (daily, hourly, etc.) to do maintenance: review memories, archive logs, refresh facts, send proactive notifications.

## Cron-as-dispatcher pattern (community-recommended)

Per r/openclaw 1qzyibu and 1riiglv (u/BP041 +12): **heartbeat crons should DISPATCH work, not RUN it directly.** The cron task itself spawns a fresh sub-agent for the actual work and exits.

Why:
- Cron tasks have shorter timeouts than agent runs. A heartbeat that needs to do real work (download data, summarize, write to memory) blows the cron timeout.
- Failures in a dispatcher are clean — the cron either fired or didn't. Failures in a do-the-work cron leave half-state.
- The dispatcher pattern fans out neatly to N heartbeat jobs without each one needing its own agent identity.

```bash
# Heartbeat cron entry (dispatcher only)
*/30 * * * * openclaw delegate "heartbeat-worker" --input "${HEARTBEAT_PROMPT}"
```

## HEARTBEAT.md content (canonical pattern)

Per r/openclaw 1qzyibu:

```markdown
# Heartbeat

## Daily (8 AM)
- Review yesterday's MEMORY.md entries; promote stable items to memory/
- Archive logs older than 30 days
- Reconcile open ACTIVE-TASK.md items vs project files

## 6-hourly
- Supermemory backup (if installed)
- Verify channel adapter health (telegram/discord/etc.)

## Weekly (Mon 9 AM)
- Verify logs index; archive month-old session files
- Re-check MEMORY.md size; split if > 10K chars (anchor-5)

## Monthly (1st)
- Update TOOLS.md from current plugin inventory
- Review skill allowlist; remove unused
```

## JamBot-specific rules

- **5h subscription cap (anchor-16):** heartbeat crons MUST NOT route through `claude-cli` provider — they'll exhaust the Pro/Max cap in ~10 minutes. Use API providers (GLM-5-turbo, OpenRouter free) for cron-driven work.
- **Anti-loop:** see `annotations/security__anti-loop.md`. Heartbeats running unattended are the highest-risk surface for runaway loops. Bake the anti-loop block into the heartbeat sub-agent's system prompt.
- **Memory layer:** heartbeats write to the same memory layer the main agent reads from. Per u/BP041 — treat crons as "persistent agents writing to the same memory layer." Don't fork to a side-vault.

## Related JamBot files

- `audit-anchors/anchor-16-anthropic-subscription-cutover.md` (5h cap detail)
- `annotations/security__anti-loop.md`
- `annotations/concepts__queue.md`
- `playbooks/cron-as-sub-agent.md` (new — full dispatch pattern)
