# Durable Replies — ack-then-followup for long SMS tasks

## The problem

Mike texts your agent: *"deploy the new design system to nick"*. That's a 5-minute job.

If you process it synchronously in the SMS reply turn, the SMS router's `docker exec` will time out at 300s and the user gets `"Hey — got your message, system hiccup on my end. Try again in a sec?"` — and the actual deploy may have run in the background but no one ever told Mike it finished.

**Every SMS must eventually get a reply, even if the task takes an hour.** Silent threads are forbidden.

## The pattern

### 1. Recognize "this is long"

Before doing the work, decide: will it take >60 seconds?

Long signals:
- Delegating to a subagent or sub-mesh
- Running a build, deploy, migration, image generation
- Kicking off a cron, scheduled run, or external API job
- Waiting on a webhook, mesh ack, or another agent's reply
- Anything calling `subagents/spawn`, `mesh send`, or `docker compose`

### 2. Ack immediately

Your **first SMS reply** acknowledges. Keep it short:

> "Working on this — will text back when done. Tracking it as deploy-abc123."

This is what the operator sees in seconds.

### 3. Spawn the work with self-notification

The kicked-off task MUST text back when it completes. Three patterns:

**Pattern A: Subagent that texts at the end**

```bash
# Inside the agent's reply turn:
bash -c '
  cd /home/node/.openclaw/workspace
  ./scripts/deploy-design-system.sh nick > /tmp/deploy-$$.log 2>&1
  RC=$?
  if [ $RC -eq 0 ]; then
    bash /mnt/shared-skills/sms-router/sms-send.sh test-dev +14374559131 \
      "Deploy done. Design system live on nick.jam-bot.com. No errors."
  else
    bash /mnt/shared-skills/sms-router/sms-send.sh test-dev +14374559131 \
      "Deploy FAILED (exit $RC). Log: /tmp/deploy-$$.log"
  fi
' &
```

The `&` backgrounds it so your agent reply turn can finish + ack the operator immediately.

**Pattern B: Mesh delegation with sms callback**

```bash
# Spawn a sub-mesh agent that handles the work + reports back
mesh_send mesh-agent-nick "deploy design system; on done, sms-send test-dev +14374559131 'deploy done'"
```

**Pattern C: cron-scheduled completion check**

Less ideal — only use when the task is fire-and-forget with no return signal. Schedule a cron to poll status and text when done.

### 4. Register the open thread (optional but recommended)

If the task is genuinely long (>5 min), register it so the system knows there's a pending reply:

```bash
curl -X POST http://172.17.0.1:6450/thread/open \
  -H 'Content-Type: application/json' \
  -d '{
    "tenant": "test-dev",
    "operator_phone": "+14374559131",
    "summary": "Deploy design system to nick",
    "task_id": "deploy-abc123"
  }'
```

This lets a watcher cron nudge the operator if no completion text fires within a threshold.

### 5. Close the thread when done

When the spawned task texts back, also close the thread record:

```bash
curl -X POST http://172.17.0.1:6450/thread/close \
  -H 'Content-Type: application/json' \
  -d '{"task_id": "deploy-abc123", "outcome": "done"}'
```

(Or set `outcome: failed` if the task failed.)

## Rules

- **NEVER ack and then silently drop the task.** If you acked, you owe the operator a completion text.
- **NEVER block the SMS reply turn on a >60s task.** Always background it and ack immediately.
- **NEVER send "system hiccup" as a completion** — the spawned task should always know its own result.
- **Use the `[tenant]` prefix automatically** — `sms-send.sh` does this. Don't double-prefix.

## See also

- `../SKILL.md` — main SMS-router agent skill
- `/home/mike/MIKE-AI/docs/jambot/sms-router.md` — full architecture
