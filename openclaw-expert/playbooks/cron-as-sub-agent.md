# Cron-as-dispatcher pattern — heartbeats spawn sub-agents, never run work directly

Per r/openclaw 1qzyibu and 1riiglv (u/BP041 +12), the production-tested pattern for OpenClaw cron jobs is: the cron task itself is a **dispatcher only** that spawns a fresh sub-agent for the actual work and exits. This avoids cron timeout cascade, gives clean failure semantics, and fans out to N heartbeat jobs without each one needing its own agent identity.

## Why not run work directly in the cron task

- Cron tasks have shorter timeouts than agent runs (15s embedded run timeout per anchor-04). Real work — download, summarize, write to memory — blows the cron budget.
- Failures in a dispatcher are clean (the cron either fired or didn't). Failures in a do-the-work cron leave half-state in memory/.
- A dispatcher can be retried safely; a do-the-work cron retry double-writes.
- Sub-agents inherit anti-loop rules from a clean system prompt; the cron task itself often doesn't.

## Pattern

```bash
# WRONG — work in the cron task itself
0 8 * * * openclaw chat send "Daily review: summarize yesterday's MEMORY.md entries and archive 30+ day files"

# RIGHT — dispatcher fans out to sub-agent
0 8 * * * openclaw delegate heartbeat-worker --input "$(cat ~/.openclaw/heartbeats/daily-review.md)"
```

## Sub-agent definition

Create a dedicated heartbeat agent (or delegated sub-agent) with a tight, single-purpose system prompt:

```markdown
# Heartbeat worker — daily review

## Identity
You are a heartbeat sub-agent. You wake on a cron schedule, do ONE focused
task, and exit. You do not engage in conversation. You do not ask clarifying
questions — your input prompt is your full brief.

## Anti-loop (mandatory)
- 5 consecutive tool calls maximum, then exit with status report
- If a tool fails twice with the same error, exit with FAIL status
- If no progress after 60 seconds wall time, exit with TIMEOUT status

## Tools allowed
- Read, Write (workspace/memory/ only)
- mcp__obsidian__* (if mounted)
- openclaw memory archive

## Tools forbidden
- Network fetches (unless explicitly listed in the cron input)
- Channel sends (heartbeat is not a notifier; that's a separate cron)
- Subagent spawn (don't chain — one level only)
```

## Heartbeat brief files (canonical)

```
~/.openclaw/heartbeats/
├── daily-review.md         # 8 AM — promote MEMORY.md, archive logs
├── 6-hourly-backup.md      # */6h — Supermemory backup, channel health
├── weekly-archive.md       # Mon 9 AM — month-old session archive
├── monthly-tools.md        # 1st of month — TOOLS.md from plugin inventory
└── on-error-recovery.md    # triggered by alert — diagnose + remediate
```

Each file is the FULL prompt the sub-agent gets. Self-contained, no implicit context.

## Crontab template

```bash
# JamBot tenant heartbeat schedule
PROVIDER_OVERRIDE=zai/glm-5-turbo   # explicit — never inherit default (which might be claude-cli, see anchor-16)

# Daily 8 AM
0 8 * * * openclaw delegate heartbeat-worker --model "$PROVIDER_OVERRIDE" --input-file ~/.openclaw/heartbeats/daily-review.md >> ~/.openclaw/logs/heartbeats.log 2>&1

# Every 6 hours
0 */6 * * * openclaw delegate heartbeat-worker --model "$PROVIDER_OVERRIDE" --input-file ~/.openclaw/heartbeats/6-hourly-backup.md >> ~/.openclaw/logs/heartbeats.log 2>&1

# Mondays 9 AM
0 9 * * 1 openclaw delegate heartbeat-worker --model "$PROVIDER_OVERRIDE" --input-file ~/.openclaw/heartbeats/weekly-archive.md >> ~/.openclaw/logs/heartbeats.log 2>&1

# 1st of month
0 9 1 * * openclaw delegate heartbeat-worker --model "$PROVIDER_OVERRIDE" --input-file ~/.openclaw/heartbeats/monthly-tools.md >> ~/.openclaw/logs/heartbeats.log 2>&1
```

## Critical: route around `claude-cli` provider

Per anchor-16, the 5h Pro/Max cap kills cron-on-sub setups. Every cron entry MUST specify `--model` explicitly, not inherit the default if the default is `claude-cli`. The `PROVIDER_OVERRIDE` env var above is the JamBot pattern.

## Coherence rule (per u/BP041)

Treat cron jobs as **persistent agents writing to the same memory layer the main agent reads from.** Don't fork to a side-vault. The whole point is the main agent should "see" what the heartbeats did — promoted memories, archived logs, updated TOOLS.md.

## Anti-pattern: notification crons

A heartbeat dispatcher is NOT the right shape for "send me a daily Telegram summary at 9 AM." That's a notifier job — it has different requirements (gateway online, channel adapter healthy, retry on send failure). Use channel-specific cron entries for notifications, not the heartbeat-worker.

## References

- `audit-anchors/anchor-04-embedded-run-timeout-15s.md`
- `audit-anchors/anchor-16-anthropic-subscription-cutover.md` (5h cap detail)
- `annotations/concepts__heartbeat.md`
- `annotations/security__anti-loop.md`
- r/openclaw 1qzyibu, 1riiglv, 1r71you
