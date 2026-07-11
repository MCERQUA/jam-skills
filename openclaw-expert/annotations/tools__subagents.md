---
upstream: https://docs.openclaw.ai/tools/subagents.md
relevance: jambot-high
last-verified: 2026-07-11
audit_anchors: []
related_pages: [automation__tasks, gateway__heartbeat, concepts__queue, gateway__protocol]
---

# Sub-agents — JamBot annotation

## What the docs say (TL;DR)

`sessions_spawn` is non-blocking; the child runs in `agent:<id>:subagent:<uuid>`.
On completion an **announce** step hands the child's latest assistant text back to
the requester session as an internal `agent` turn (stable idempotency key).
Delivery order: wake/steer active requester run → requester-agent handoff →
queue routing → exponential-backoff retry → give up. The clean waiting
primitive is **`sessions_yield`** — spawn, yield, and the completion arrives as
the next model-visible message. Never poll `/subagents list` in a loop.

Key config (`agents.defaults.subagents`): `model`, `runTimeoutSeconds`,
`maxConcurrent`, `maxSpawnDepth`, `maxChildrenPerAgent`, `archiveAfterMinutes`,
`announceTimeoutMs` (default 120000). Suppression tokens: child replying
`ANNOUNCE_SKIP` posts nothing; `NO_REPLY` suppresses announce output.

## The JamBot gap (root-caused 2026-07-11)

The announce fallback for an **idle** requester routes through the tasks layer:
"session-queued delivery surfaces on the next heartbeat." JamBot runs
`heartbeat.every: "0m"` (deliberately disabled — see jambot-performance skill),
so that fallback is DEAD here. Symptom: agent promises "I'll let you know when
it's done," the announce lands silently in history, and the user only hears
about it when they complain (which opens a new turn that finally sees it).

**Fix shipped 2026-07-11 (`feat/subagent-completion-loop` in OpenVoiceUI):**
1. OVUI's `EventDispatcher` (services/gateways/openclaw.py) detects subagent
   `lifecycle end` events with NO live subscription (originating HTTP stream
   timed out / aborted / cron spawn) → debounced **orphan continuation**:
   sends `[SUBAGENT_COMPLETE]` chat.send, collects the agent's reply.
2. Reply is broadcast to browsers over the persistent `/ws/clawdbot` socket as
   `proactive_message` frames with server-generated TTS; app.js plays them,
   parses `[CANVAS:...]` tags, and adds to transcript. Socket now has
   keepalive (25s) + client auto-reconnect.
3. `templates/AGENTS.md` + `SOUL.md` teach the completion contract and
   `sessions_yield` for short waits.

Heartbeat stays OFF — do not re-enable it to "fix" completion delivery; the
orphan continuation covers it without burning the shared Z.AI budget.

## spawnedBy provenance

Since gateway v4.29, subagent chat + agent broadcast events carry
`spawnedBy` (canonical parent key like `agent:openvoiceui:main`). OVUI's
orphan detection maps it back to the chat.send alias via the dispatcher's
learned alias→canonical table, falling back to stripping the
`agent:<id>:` prefix.

## Related JamBot files

- `/mnt/system/base/OpenVoiceUI/services/gateways/openclaw.py` — orphan
  tracking in EventDispatcher + `_run_orphan_continuation` + `_SUBAGENT_NUDGE_MSG`
- `/mnt/system/base/OpenVoiceUI/server.py` — `/ws/clawdbot` push registry +
  `push_proactive_message`
- `/mnt/system/base/OpenVoiceUI/src/app.js` — `proactive_message` handler,
  WS auto-reconnect
- `/mnt/system/base/templates/AGENTS.md` — the agent-facing contract
