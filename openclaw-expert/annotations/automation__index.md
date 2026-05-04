---
upstream: https://docs.openclaw.ai/automation/index.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: []
related_pages: [automation__cron-jobs, automation__hooks, automation__standing-orders, automation__taskflow, automation__tasks]
---

# Automation — JamBot annotation

## What docs say (TL;DR)

Cron jobs, lifecycle hooks, webhooks, standing orders, task flow. All persist in `~/.openclaw/cron/` with run logs in `runs/<jobId>.jsonl`.

## New v4.x automation surfaces (audit doc)

| Surface | Introduced | Source |
|---------|-----------|--------|
| `commitments.enabled` / `commitments.maxPerDay` | v4.29 line 408 | Opt-in inferred follow-up commitments with hidden batched extraction |
| `cron.maxConcurrentRuns` cron-nested lane | v4.26 line 1229 | Dedicated `cron-nested` isolated agent-turn lane |
| `cron.failureAlert.includeSkipped` | v4.26 line 1235 | Failure alerts now include skipped runs |
| `openclaw cron add --thread-id` | v4.27 line 847 | Bind cron run to specific thread |
| `openclaw cron edit --failure-alert-include-skipped` | v4.26 line 1235 | CLI for above |
| `openclaw cron add --tools` PowerShell-style parsing | v4.20 line 2410 | Fixed |
| Webhook ingress plugin | v4.7 line 2928 | Per-route shared-secret endpoints |

## Inferred commitments (v4.29) — JamBot interest

Pattern: agent infers a follow-up from conversation, batches it for review. Useful for the Office filing-cabinet system (`docs/jambot/office-system-overview.md`) which already does similar manual commitment tracking.

**Possible future integration:** wire OpenClaw `commitments.*` → Office matters file. Not yet evaluated.

## v4.15 dreaming default flip

`dreaming.storage.mode: "separate"` is now the DEFAULT (was `inline`). Writes go to `memory/dreaming/{phase}/YYYY-MM-DD.md`. JamBot was unaware — check if any client config still sets `inline` and remove if so.

## JamBot cron usage today

- `jambot-init-agent-repos.sh` daily 4:15 AM — git snapshots agent files
- `jambot-health-monitor.sh` every 5 min
- `jambot-crm-automations.sh` daily 5 AM (CRM pipeline + stale-deal alerts)
- `jambot-backup.sh` (Storage Box rsync + Twilio SMS alerts)
- `jambot-supertonic.sh` health check
- Office system: 11 cron jobs (all read-only, no outbound) — see `docs/jambot/office-system-overview.md`

## Webhook plugin (v4.7)

Per-route shared-secret endpoints. JamBot uses a custom webhook surface (`api-social.jam-bot.com/webhooks/meshy`) — could potentially migrate to OpenClaw's bundled webhook plugin for consistency. Not yet evaluated.

## Hooks (lifecycle)

| Hook | Introduced | Surface |
|------|-----------|---------|
| `before_agent_finalize` | v4.25 line 1377 | Plugin-only |
| `model_call_started` / `model_call_ended` | v4.25 line 1405 | Plugin-only telemetry |
| `session_state` / `next_turn_context` / `trusted_tool_policy` / `ui_descriptors` / `events` / `scheduler_cleanup` / `run_scoped_plugin_context` | v4.27 line 801 | Plugin-only |

## Related JamBot files

- `docs/jambot/unified-ledger-system.md` — read-only event ledger across cron/voice/email/git
- `docs/jambot/office-system-overview.md` — Office filing cabinet (commitment-like)
- `/jambot-performance` skill — heartbeat tuning (related to cron)
