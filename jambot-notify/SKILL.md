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
jambot-notify.sh warn health "<tenant>: TOOLS.md 34280c > 20000c limit" --dedup-key <tenant>-tools-md-bloat

# Admin-review chain broken — critical + SMS
jambot-notify.sh critical admin-review "tmux first-reviewer down + revival failed" --ack-required --dedup-key tmux-down

# Container won't restart after 3 attempts — urgent (also posts to host@mesh)
jambot-notify.sh urgent health "openclaw-<tenant> won't start (3 attempts failed)" --dedup-key <tenant>-oc-perma-down
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

## DONE-LATCH RULE — action-demanding alerts must consume the signal that they were actioned

Folded in 2026-09-10, pledge `cce033b9` (2026-09-09 nightly meeting SHARE, `test-dev-voice@mesh`):

> An alert asking a human to reboot/install/restart must consume the signal that they did it, or
> it nags forever and burns trust.

Measured cost (test-dev-voice, 2026-09-08): a kernel-reboot alert paged Mike a third time on
STALE state — his prior two reboots had already succeeded, but the alert only checked "does the
installed kernel differ from the running kernel," never "did the human already do what I last
asked." Mike: *"you already had three tries, I'm not rebooting."* The alert was demanding an
action that had already happened.

**`--dedup-key` and `--ack-required` are NOT a done-latch.** Dedup rate-limits SMS for a
*recurring* condition; ack (§ `jambot-notify.sh` ack-file mechanism) suppresses an alert the HOST
has manually acknowledged as pending-operator, on a TTL. Neither one asks "did the demanded action
already happen?" — both can re-fire (or fail to suppress) against a condition a human already
resolved, because neither reads the thing the action was supposed to change.

**The rule:** before an alert asks a human to DO something, it must name — and check — the exact
signal that clears it, and it must re-check that signal EVERY time before firing again. If the
signal is already clear, the alert must not fire, regardless of dedup/ack state. Concrete pattern
already live on this box, in two forms:

1. **JamFlow's `[human-gated]` why-prefix** (`projects/jam-flow/server/watch.py`, e.g. line
   ~13388: `_why = "[human-gated] " + _why[:580] + " · roll GO queued to Mike (SUDO-QUEUE)"`) — a
   WARN state whose `why` string is machine-readable as "waiting on a human GO", so the
   reconciler (line ~14331) can hold it apart from a genuine unattended regression instead of
   re-alerting on it every sweep.
2. **The SUDO-QUEUE open-GO gate** (`SUDO-QUEUE.md`, read by `host-boot-gate.py`) — a queued sudo
   ask stays a checkbox row until Mike (or a script Mike ran) flips it; nothing re-pages for the
   same row while it is still open, and closing the checkbox — not a timer — is what silences it.

**For a reboot/install/restart-class alert specifically**, the signal is almost always cheap to
check directly instead of trusting a flag: kernel version vs. `uname -r`, service PID/start-time
vs. last-known-bad, a version string vs. the deployed one, container uptime vs. the alert's own
first-fired time. Check the LIVE fact, not a flag that only a script sets — a flag can itself go
stale (the exact "stamp cited as current" defect the 2026-09-09 QA/security cross-lesson
independently reproduced the same night). See `docs/SYSTEM-FACTS.json` fact
`alerts.done_latch_rule`.
