---
name: sms-router
description: Send SMS to your operator. Use when you need to text status updates, ack a long-running task, or notify the user of an event. Reply tool for SMS conversations and proactive outbound texts from inside the agent runtime.
---

# SMS Router — agent-side tool

Sends an SMS to your operator (Mike, or a tenant operator) via the JamBot SMS router on port 6450 (host IP auto-detected from the container's default route — different per tenant bridge). The router routes through Twilio Canadian number `+16476991930`.

## When to use

1. **Acking a long task** — if you received an SMS and the task will take more than 60 seconds, REPLY IMMEDIATELY with an ack like "Working on this, will text back when done. — <self>", then continue the work. Use this tool to send the follow-up SMS when complete.

2. **Proactive status updates** — when something important happens in your tenant (build done, ticket closed, anomaly detected, commitment due), text the operator on your own initiative.

3. **Delegated-task completions** — if you delegated work to a subagent or kicked off an async job, the spawned task should call this tool when it finishes (or include the call in its tail).

## Usage

```bash
bash /mnt/shared-skills/sms-router/sms-send.sh <tenant> <to-phone-E164> "<body>"
```

The script automatically:
- Adds `[<tenant>]` prefix to the body so the operator knows which agent texted them
- Logs to ledger
- Returns JSON with Twilio SID

**Example** — texting Mike that today's reflection is done:

```bash
bash /mnt/shared-skills/sms-router/sms-send.sh test-dev +14374559131 \
  "Nightly synthesize complete. 23 actions logged today, 3 open commitments rolled to tomorrow."
```

**Example** — texting back after a 30-min subagent job finishes:

```bash
# (inside the spawned task, after it completes)
bash /mnt/shared-skills/sms-router/sms-send.sh nick +16476856286 \
  "Website rebuild done. New version live at nick.jam-bot.com. 4 pages updated, no broken links."
```

## Rules

- **Plaintext only.** No markdown, no emojis, no links (unless explicitly asked).
- **Under 320 chars** when possible (1 SMS segment), 1500 absolute max.
- **Don't omit the tenant prefix** — the router adds `[<tenant>]` automatically, but the body should NOT start with one yourself.
- **Don't text yourself** — if you ARE the operator's agent and you're already in a reply turn, just return text normally. Use this tool only for unsolicited / follow-up messages outside the immediate reply.
- **Track open threads** — if you ack a long task, optionally POST to `/thread/open` so the system knows there's a pending follow-up. (See `references/durable-replies.md`.)

## Endpoints

- `POST /send` — outbound SMS  (this skill wraps it)
- `POST /thread/open` — register a pending follow-up
- `POST /thread/close` — close a pending follow-up + send the final SMS
- `GET /admin/registry` — see who's registered + open threads

## See also

- `/home/mike/MIKE-AI/docs/jambot/sms-router.md` — full architecture
- `references/durable-replies.md` — long-task ack-then-followup pattern
