# OpenClaw Automation Reference

---

## CRON JOBS

### Config

```json5
{
  cron: {
    enabled: true,                        // default true
    store: "~/.openclaw/cron/jobs.json",
    maxConcurrentRuns: 1,
  },
}
```

- Disable: `cron.enabled: false` or `OPENCLAW_SKIP_CRON=1`
- Jobs file: `~/.openclaw/cron/jobs.json` (edit only when Gateway stopped)
- Run history: `~/.openclaw/cron/runs/<jobId>.jsonl` (auto-pruned)

### Schedule Kinds

| Kind | Field | Example |
|------|-------|---------|
| `at` | `schedule.at` (ISO 8601 or relative) | `"2026-02-01T16:00:00Z"` or `"20m"` |
| `every` | `schedule.everyMs` (ms) | `3600000` |
| `cron` | `schedule.expr` + optional `tz` | `"0 7 * * *"` |

- ISO without timezone → **UTC**; cron without `--tz` → **gateway host timezone**

### Session Targets

| Target | Payload Kind | Context | History |
|--------|-------------|---------|---------|
| `main` | `systemEvent` | Full | Shared |
| `isolated` | `agentTurn` | None (fresh) | `cron:<jobId>` |

- `wakeMode: "now"` (default) — immediate heartbeat; `"next-heartbeat"` — wait
- One-shot (`at`) jobs auto-delete after success; use `deleteAfterRun: false` to keep

### Delivery (isolated only)

| Field | Values |
|-------|--------|
| `delivery.mode` | `announce` (default) \| `none` |
| `delivery.channel` | `whatsapp` `telegram` `discord` `slack` `signal` `imessage` `mattermost` `last` |
| `delivery.to` | phone / chat ID / `channel:<id>` / `-100…:topic:<id>` |
| `delivery.bestEffort` | `true` = don't fail job if delivery fails |

- `announce`: posts via outbound adapters; skips `HEARTBEAT_OK`; avoids dup if agent already messaged same target
- `none`: no external message; no main-session summary

### Model Overrides (isolated only)

| Field | Example |
|-------|---------|
| `model` | `"anthropic/claude-sonnet-4-20250514"` or alias `"opus"` |
| `thinking` | `"off"` `"minimal"` `"low"` `"medium"` `"high"` `"xhigh"` |

Resolution: job payload > `hooks.gmail.model` > agent config default

### CLI

```bash
# One-shot (UTC, auto-delete)
openclaw cron add --name "Reminder" --at "2026-02-01T16:00:00Z" \
  --session main --system-event "Check docs" --wake now --delete-after-run

# One-shot relative time
openclaw cron add --name "Remind" --at "20m" \
  --session main --system-event "Standup in 10 min." --wake now

# Recurring isolated → channel delivery
openclaw cron add --name "Morning status" --cron "0 7 * * *" --tz "America/Los_Angeles" \
  --session isolated --message "Summarize inbox + calendar." \
  --announce --channel whatsapp --to "+15551234567"

# Telegram topic delivery
openclaw cron add --name "Nightly" --cron "0 22 * * *" --tz "America/Los_Angeles" \
  --session isolated --message "Summarize today." \
  --announce --channel telegram --to "-1001234567890:topic:123"

# Model + thinking override
openclaw cron add --name "Deep analysis" --cron "0 6 * * 1" \
  --session isolated --message "Weekly analysis." --model "opus" --thinking high \
  --announce --channel whatsapp --to "+15551234567"

# Agent pinning / management
openclaw cron add --name "Ops" --cron "0 6 * * *" --session isolated --message "Check ops queue" --agent ops
openclaw cron edit <jobId> --agent ops && openclaw cron edit <jobId> --clear-agent
openclaw cron list
openclaw cron run <jobId>               # force; add --due to only run if due
openclaw cron runs --id <jobId> --limit 50
openclaw cron edit <jobId> --message "Updated" --model "opus"

# Immediate system event (no job created)
openclaw system event --mode now --text "Next heartbeat: check battery."
```

### JSON Tool Call Shapes

```json
{ "name": "Reminder", "schedule": { "kind": "at", "at": "2026-02-01T16:00:00Z" },
  "sessionTarget": "main", "wakeMode": "now",
  "payload": { "kind": "systemEvent", "text": "Reminder text" }, "deleteAfterRun": true }
```

```json
{ "name": "Morning brief",
  "schedule": { "kind": "cron", "expr": "0 7 * * *", "tz": "America/Los_Angeles" },
  "sessionTarget": "isolated", "wakeMode": "next-heartbeat",
  "payload": { "kind": "agentTurn", "message": "Summarize overnight updates." },
  "delivery": { "mode": "announce", "channel": "slack", "to": "channel:C1234567890", "bestEffort": true } }
```

Update (patch): `{ "jobId": "job-123", "patch": { "enabled": false } }`

### Retry Backoff (recurring)

30s → 1m → 5m → 15m → 60m on consecutive errors. Resets after success.
One-shot jobs: disable after `ok`, `error`, or `skipped` — no retry.

---

## HEARTBEAT vs CRON

### Decision Guide

| Use Case | Use |
|----------|-----|
| Check inbox every 30 min | Heartbeat |
| Send daily report at 9am sharp | Cron (isolated) |
| One-shot reminder | Cron `--at` (main) |
| Weekly deep analysis | Cron (isolated) w/ `--model` |
| Background project health check | Heartbeat |

### Heartbeat Config

```json5
{ agents: { defaults: { heartbeat: { every: "30m", target: "last",
  activeHours: { start: "08:00", end: "22:00" } } } } }
```

- `HEARTBEAT.md` checklist read each cycle; reply `HEARTBEAT_OK` → no message delivered
- Keep small to minimize token overhead

### Session Comparison

| | Heartbeat | Cron (main) | Cron (isolated) |
|--|-----------|-------------|-----------------|
| Session | Main | Main (system event) | `cron:<jobId>` |
| History | Shared | Shared | Fresh each run |
| Context | Full | Full | None |
| Model | Main model | Main model | Can override |

**Cost:** Heartbeat = 1 turn/interval (keep `HEARTBEAT.md` small). Cron main = piggybacks on next heartbeat. Cron isolated = full agent turn (use cheaper model).

---

## WEBHOOKS

### Config

```json5
{
  hooks: {
    enabled: true,
    token: "shared-secret",
    path: "/hooks",
    allowedAgentIds: ["hooks", "main"],  // omit/"*"=any; []=deny explicit routing
  },
}
```

### Auth

- `Authorization: Bearer <token>` ← recommended
- `x-openclaw-token: <token>`
- `?token=<token>` ← deprecated

### Endpoints

**`POST /hooks/wake`** — main session system event

```json
{ "text": "New email received", "mode": "now" }
```

Returns `200`. `mode`: `now` (default) | `next-heartbeat`

**`POST /hooks/agent`** — isolated agent run, summary posted to main

```json
{ "message": "Summarize inbox", "name": "Email", "agentId": "hooks",
  "sessionKey": "hook:email:msg-123", "wakeMode": "now",
  "deliver": true, "channel": "last", "to": "+15551234567",
  "model": "openai/gpt-5.2-mini", "thinking": "low", "timeoutSeconds": 120 }
```

Returns `202`. Only `message` required. Reuse `sessionKey` → multi-turn hook conversations.

**`POST /hooks/<name>`** — custom mapped; resolved via `hooks.mappings`

Response codes: `200` wake, `202` agent, `400` bad payload, `401` auth, `413` oversized

### Examples

```bash
curl -X POST http://127.0.0.1:18789/hooks/wake \
  -H 'Authorization: Bearer SECRET' -H 'Content-Type: application/json' \
  -d '{"text":"New email received","mode":"now"}'

curl -X POST http://127.0.0.1:18789/hooks/agent \
  -H 'x-openclaw-token: SECRET' -H 'Content-Type: application/json' \
  -d '{"message":"Summarize inbox","name":"Email","model":"openai/gpt-5.2-mini"}'
```

### Mappings Config

```json5
{ hooks: { presets: ["gmail"],
  mappings: [{ match: { path: "gmail" }, action: "agent", wakeMode: "now",
    name: "Gmail", sessionKey: "hook:gmail:{{messages[0].id}}",
    messageTemplate: "Email from {{messages[0].from}}: {{messages[0].snippet}}",
    model: "openai/gpt-5.2-mini", deliver: true, channel: "last" }] } }
```

- `hooks.transformsDir` + `transform.module` → JS/TS custom logic
- `allowUnsafeExternalContent: true` → disables safety wrapper (dangerous, trusted sources only)
- Security: keep behind loopback/tailnet; dedicated hook token; set `allowedAgentIds` for multi-agent

---

## LIFECYCLE HOOKS

### Discovery (precedence order)

1. `<workspace>/hooks/` — per-agent
2. `~/.openclaw/hooks/` — user-installed, shared
3. `<openclaw>/dist/hooks/bundled/` — bundled

Each hook: directory with `HOOK.md` (metadata) + `handler.ts` (logic)

### HOOK.md Frontmatter

```markdown
---
name: my-hook
description: "Does something useful"
metadata:
  { "openclaw": { "emoji": "🎯", "events": ["command:new"],
    "requires": { "bins": ["node"] } } }
---
```

`requires` fields: `bins`, `anyBins`, `env`, `config`, `os`

### Event Types

| Event | Trigger |
|-------|---------|
| `command:new` | `/new` issued |
| `command:reset` | `/reset` issued |
| `command:stop` | `/stop` issued |
| `command` | Any command |
| `agent:bootstrap` | Before workspace bootstrap; can mutate `context.bootstrapFiles` |
| `gateway:startup` | After channels start |
| `tool_result_persist` | Plugin API: transform tool results before transcript (synchronous) |

### Handler Signature

```typescript
import type { HookHandler } from "../../src/hooks/hooks.js";
const handler: HookHandler = async (event) => {
  if (event.type !== "command" || event.action !== "new") return;
  event.messages.push("Hook executed!");  // push to send msg to user
};
export default handler;
```

Event fields: `type`, `action`, `sessionKey`, `timestamp`, `messages[]`, `context.workspaceDir`, `context.bootstrapFiles`, `context.cfg`

### CLI

```bash
openclaw hooks list [--eligible] [--verbose] [--json]
openclaw hooks info <name>
openclaw hooks check
openclaw hooks enable <name>
openclaw hooks disable <name>
openclaw hooks install <path-or-spec>   # npm hook pack
```

### Config

```json
{ "hooks": { "internal": { "enabled": true,
  "entries": { "session-memory": { "enabled": true }, "my-hook": { "enabled": true, "env": { "MY_VAR": "val" } } },
  "load": { "extraDirs": ["/path/to/more/hooks"] }
}}}
```

### Bundled Hooks

| Hook | Event | Output |
|------|-------|--------|
| `session-memory` | `command:new` | `<workspace>/memory/YYYY-MM-DD-slug.md` |
| `command-logger` | `command` | `~/.openclaw/logs/commands.log` (JSONL) |
| `boot-md` | `gateway:startup` | Runs `BOOT.md` via agent |
| `soul-evil` | `agent:bootstrap` | Swaps `SOUL.md` with `SOUL_EVIL.md` in-memory |

soul-evil extra config: `"file": "SOUL_EVIL.md", "chance": 0.1, "purge": { "at": "21:00", "duration": "15m" }`

### Best Practices / Troubleshooting

- Keep fast: `void asyncFn()` (fire-and-forget); wrap in `try/catch`, don't rethrow; return early for irrelevant events
- Prefer specific events (`command:new`) over general (`command`)
- Not discovered → needs `HOOK.md` + `handler.ts`; `openclaw hooks list`
- Not eligible → `openclaw hooks info <name>` (check missing bins/env/config)
- Not executing → verify enabled, restart gateway, check `./scripts/clawlog.sh | grep hook`

---

## GMAIL PUB/SUB INTEGRATION

### Prerequisites

- `gcloud` installed and logged in
- `gog` (gogcli) installed and authorized for Gmail account
- OpenClaw hooks enabled with `presets: ["gmail"]`
- Tailscale (supported); other tunnels are DIY/unsupported

### Hook Config

```json5
{
  hooks: {
    enabled: true,
    token: "OPENCLAW_HOOK_TOKEN",
    presets: ["gmail"],
    gmail: {
      model: "openrouter/meta-llama/llama-3.3-70b-instruct:free",
      thinking: "off",
    },
  },
}
```

### Wizard (Recommended)

```bash
openclaw webhooks gmail setup --account openclaw@gmail.com
openclaw webhooks gmail run    # manual daemon (auto-renews watch)
```

- Gateway auto-starts `gog gmail watch serve` when `hooks.gmail.account` set
- Suppress auto-start: `OPENCLAW_SKIP_GMAIL_WATCHER=1`
- Don't run manual daemon simultaneously (port conflict `127.0.0.1:8788`)

### One-Time GCP Setup

```bash
gcloud auth login && gcloud config set project <project-id>
gcloud services enable gmail.googleapis.com pubsub.googleapis.com
gcloud pubsub topics create gog-gmail-watch
gcloud pubsub topics add-iam-policy-binding gog-gmail-watch \
  --member=serviceAccount:gmail-api-push@system.gserviceaccount.com --role=roles/pubsub.publisher
```

⚠️ Topic must be in the **same GCP project** as the OAuth client used by `gog`.

### Start Watch

```bash
gog gmail watch start --account openclaw@gmail.com \
  --label INBOX --topic projects/<project-id>/topics/gog-gmail-watch
```

### Run Push Handler (Manual)

```bash
gog gmail watch serve \
  --account openclaw@gmail.com --bind 127.0.0.1 --port 8788 \
  --path /gmail-pubsub --token <shared> \
  --hook-url http://127.0.0.1:18789/hooks/gmail \
  --hook-token OPENCLAW_HOOK_TOKEN --include-body --max-bytes 20000
```

### Test & Cleanup

```bash
gog gmail send --account openclaw@gmail.com --to openclaw@gmail.com --subject "test" --body "ping"
gog gmail watch status --account openclaw@gmail.com
# Cleanup:
gog gmail watch stop --account openclaw@gmail.com
gcloud pubsub subscriptions delete gog-gmail-watch-push && gcloud pubsub topics delete gog-gmail-watch
```

### Troubleshooting

- `Invalid topicName` → project mismatch
- `User not authorized` → missing `roles/pubsub.publisher`
- Empty messages → fetch via `gog gmail history --account ... --since <historyId>`

---

## AUTH MONITORING

### CLI Check (Preferred)

```bash
openclaw models status --check
```

Exit codes: `0` OK · `1` expired/missing · `2` expiring within 24h

Works in cron/systemd; no extra scripts needed.

### Optional Scripts (`scripts/`)

- `auth-monitor.sh` — cron/systemd timer; ntfy/phone alerts
- `claude-auth-status.sh` — auth checker; uses `openclaw models status --json` (falls back to direct file reads)
- `mobile-reauth.sh` — guided re-auth over SSH; `termux-quick-auth.sh` / `termux-auth-widget.sh` / `termux-sync-widget.sh` — Termux phone flows
- `systemd/openclaw-auth-monitor.{service,timer}` — systemd user timer

---

## AUTOMATION TROUBLESHOOTING

### Command Ladder

```bash
openclaw status && openclaw gateway status && openclaw logs --follow && openclaw doctor
openclaw channels status --probe && openclaw cron status && openclaw cron list && openclaw system heartbeat last
```

### Cron Not Firing

```bash
openclaw cron status && openclaw cron list && openclaw cron runs --id <jobId> --limit 20 && openclaw logs --follow
```

| Symptom | Cause |
|---------|-------|
| `cron: scheduler disabled` | `cron.enabled=false` or `OPENCLAW_SKIP_CRON=1` |
| `cron: timer tick failed` | Scheduler tick crashed; check logs |
| `reason: not-due` | Manual run without `--force` and job not due |

### Cron Fired But No Delivery

```bash
openclaw cron runs --id <jobId> --limit 20 && openclaw channels status --probe
```

| Symptom | Cause |
|---------|-------|
| Run `ok`, no message | `delivery.mode = "none"` |
| Delivery skipped | `channel`/`to` missing or invalid |
| `unauthorized` / `Forbidden` | Channel auth/permissions issue |

### Heartbeat Suppressed

```bash
openclaw system heartbeat last && openclaw config get agents.defaults.heartbeat
```

| Symptom | Cause |
|---------|-------|
| `reason=quiet-hours` | Outside `activeHours` window |
| `requests-in-flight` | Main lane busy; deferred |
| `empty-heartbeat-file` | `HEARTBEAT.md` has no actionable content |
| `alerts-disabled` | Visibility settings suppress outbound |

### Timezone Gotchas

```bash
openclaw config get agents.defaults.heartbeat.activeHours.timezone
openclaw config get agents.defaults.userTimezone
```

- `userTimezone` unset → falls back to host timezone (or `activeHours.timezone` if set)
- Cron without `--tz` → gateway host timezone
- ISO `at` timestamps without timezone → **UTC**

---

## POLLS

Channels: WhatsApp (2–12 opts), Discord (2–10 opts, `--poll-duration-hours` 1–768h default 24), MS Teams (Adaptive Cards, votes in `~/.openclaw/msteams-polls.json`)

```bash
openclaw message poll --target +15555550123 --poll-question "Lunch?" --poll-option "Yes" --poll-option "No"
openclaw message poll --channel discord --target channel:123456789 --poll-question "Plan?" --poll-option "A" --poll-option "B" --poll-duration-hours 48
openclaw message poll --channel msteams --target conversation:19:abc@thread.tacv2 --poll-question "Lunch?" --poll-option "Pizza" --poll-option "Sushi"
# --poll-multi for multi-select (WhatsApp/Discord)
```

Gateway RPC `poll`: params `to`, `question`, `options[]`, `maxSelections`, `durationHours`, `channel`, `idempotencyKey` (required)
