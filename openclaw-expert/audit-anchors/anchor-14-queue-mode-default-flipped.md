---
anchor: 14
slug: queue-mode-default-flipped
status: confirmed
introduced: v2026.4.29
changelog_lines: [410, 409]
upstream_pages:
  - https://docs.openclaw.ai/concepts/queue.md
  - https://docs.openclaw.ai/concepts/queue-steering.md
old_behavior: "messages.queue.mode default = 'collect'"
new_behavior: "default = 'steer' with 500ms followup-fallback debounce"
skill_files_affected:
  - "references/agent-runtime.md:194 (JSON5 default block)"
---

# Anchor #14 — `messages.queue.mode` default flipped to `steer`

## What changed

v4.29 line 410: "default active-run queueing to `steer` with a 500ms followup fallback debounce"

## Old vs new behavior

| Mode | Old (≤ v4.28) | New (v4.29+) |
|------|---------------|--------------|
| `collect` (legacy default) | Queues incoming messages until current turn completes | Renamed: this behavior is now a separate explicit mode |
| `steer` (new default) | (was opt-in, drained one-at-a-time) | Drains **all** pending Pi steering messages at the next model boundary |
| `queue` | did not exist | Replaces old one-at-a-time `steer` semantics |

v4.29 line 409 explicitly renames the one-at-a-time semantics.

## JamBot impact

Voice flow: when a user keeps talking while the agent is mid-stream, multiple incoming messages now get steered together at the next model boundary instead of one-at-a-time. This is generally an improvement for voice — feels more responsive — but agents that relied on `collect` semantics will see different behavior.

If a client opts into structured turn-taking, set explicit:
```json5
{ messages: { queue: { mode: "collect" } } }
```

## Related v4.29 changes

- v4.29 line 411: `messages.visibleReplies` global — operators can require visible output to go through `message(action=send)` for any source chat
- v4.29 line 412: `spawnedBy` field on subagent chat + agent broadcast events

## Fix instruction

`annotations/concepts__queue.md` and `annotations/concepts__queue-steering.md`:
1. Document the v4.29 default flip
2. Explain `collect` / `queue` / `steer` triad with current semantics
3. Cross-reference voice-flow impact in `overrides/voice-flow-quirks.md`
