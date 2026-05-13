---
name: jambot-notify
description: "Unified admin notification CLI — single entry point for any script/cron/agent that needs to alert Mike. Routes to log + email + SMS + mesh based on urgency. Dedupes per-category to prevent flapping. Use when you need Mike to see something."
metadata: {"openclaw": {"emoji": "🚨", "requires": {"env": ["AGENTMAIL_API_KEY"], "anyBins": ["bash", "curl"]}}}
---

# jambot-notify — unified admin notification

Single CLI any script/cron/agent calls to alert Mike. Replaces ad-hoc send_alert() functions scattered across health-monitor, backup, deploy scripts.

## Quick usage

```bash
/home/mike/MIKE-AI/scripts/jambot-notify.sh <urgency> <category> <summary> [--body "..."] [--ack-required] [--dedup-key X]
```

## Urgency levels

| Level | Channels fired | Use when |
|---|---|---|
| `info` | log only | FYI / status / "happened cleanly" |
| `warn` | log + email | Recoverable issue, attention needed in hours, not minutes |
| `critical` | log + email + SMS | System-down / data-at-risk / pipeline broken — Mike needs to know soon |
| `urgent` | log + email + SMS + mesh-urgent to host@mesh | Drop everything; immediate human required |

## Categories

`health` `admin-review` `build` `backup` `security` `other`

## Dedup

`--dedup-key X` suppresses SMS for the same `(category + key)` within 30 min. Logs still fire every time. Use for flapping systems (e.g. `--dedup-key "${user}-openclaw-down"` so a restart loop doesn't blast 12 SMS in 30 min).

## Examples

```bash
# Backup succeeded — log only
jambot-notify.sh info backup "Nightly backup completed in 4m12s"

# Health check flagged TOOLS.md too large — warn + email
jambot-notify.sh warn health "josh: TOOLS.md 34280c > 20000c limit" --dedup-key josh-tools-md-bloat

# Admin-review chain broken — critical + SMS
jambot-notify.sh critical admin-review "tmux first-reviewer down + revival failed" --ack-required --dedup-key tmux-down

# Container won't restart after 3 attempts — urgent (also posts to host@mesh)
jambot-notify.sh urgent health "openclaw-josh won't start (3 attempts failed)" --dedup-key josh-oc-perma-down
```

## Channels reference

| Channel | Backend | Cost | Latency |
|---|---|---|---|
| Log | `/var/log/jambot-notify.log` + `/home/mike/MIKE-AI/logs/jambot-alerts.log` | $0 | instant |
| Email | AgentMail (`openvoiceui-ai@agentmail.to` → `mikecerqua@gmail.com`) | low | seconds |
| SMS | Twilio (`TWILIO_*` env from `.platform-keys.env`) | $0.01/msg | seconds |
| Mesh-urgent | `mesh-send --kind urgent --to host@mesh` → tmux watcher emits as Monitor event | $0 | seconds (when tmux is up) |

## Don't

- Don't call this for routine mesh acks (use mesh-ack instead)
- Don't bypass dedup for known-flapping systems
- Don't use `urgent` for anything that can wait an hour — overuse trains Mike to ignore SMS
