---
upstream: https://docs.openclaw.ai/concepts/queue.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: [14]
related_pages: [concepts__queue-steering, concepts__agent, channels__index]
---

# Queue (active-run queueing) — JamBot annotation

## What docs say (TL;DR)

When a user sends a message while the agent is mid-stream, the gateway queues it. Three modes (post v4.29):

| Mode | Behavior |
|------|----------|
| `collect` | Queue all incoming until current turn ends; deliver as one batch |
| `queue` | One-at-a-time delivery (the OLD `steer` semantics) |
| `steer` | Drains ALL pending steering messages at next model boundary (NEW default) |

## Anchor #14 — default flipped to `steer` (v4.29 line 410)

Pre-v4.29 default was `collect`. v4.29 line 410: "default active-run queueing to `steer` with a 500ms followup fallback debounce".

The 500ms debounce: if multiple steering messages arrive within 500ms of each other, they're coalesced into one delivery to the model.

## Voice flow impact

For OpenVoiceUI voice flow: improvement in most cases. User keeps talking → multiple message chunks arrive → all deliver to next model boundary together (model gets full picture).

If a client wants strict turn-taking (e.g. rigid voicemail-style channel):
```json5
{ messages: { queue: { mode: "collect" } } }
```

## Related v4.29 changes

| Surface | Source |
|---------|--------|
| `messages.visibleReplies` global — operators require visible output to go through `message(action=send)` | line 411 |
| `spawnedBy` field on subagent + agent broadcast events | line 412 |
| `messages.groupChat.visibleReplies: "automatic"` (Discord) — v4.26 default flipped to private | line 936 |

## Burns / incidents

- 2026-04-18 josh: interrupt races between Wake Word Detector and main STT — see `playbooks/debug-empty-final.md`. Queue-mode interaction not directly causal but related.

## Related JamBot files

- `audit-anchors/anchor-14-queue-mode-default-flipped.md`
- `overrides/voice-flow-quirks.md`
- `/jambot-voice-flow` skill — STT + wake word + PTT lifecycle
- `playbooks/debug-empty-final.md`
