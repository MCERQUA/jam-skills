---
upstream: https://docs.openclaw.ai/concepts/agent.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: [4, 14]
related_pages: [concepts__agent-loop, concepts__agent-runtimes, concepts__queue, concepts__system-prompt]
---

# Agent runtime — JamBot annotation

## What docs say (TL;DR)

Agent lifecycle: bootstrap injection → user message arrives → context build → LLM stream → tool calls → response chunks. Configurable runtimes (Pi, Codex, Claude CLI, Gemini CLI). Multi-agent routing via bindings. Sub-agent spawn for isolated tasks.

## Audit anchors that apply

### Anchor #14 — `messages.queue.mode` default flipped to `"steer"` (v4.29)

| Mode | Pre-v4.29 | v4.29+ |
|------|-----------|--------|
| `collect` (was default) | Queue until current turn done | Renamed to explicit mode |
| `steer` (new default) | (was opt-in, drained one-at-a-time) | Drains ALL pending steering messages at next model boundary |
| `queue` | did not exist | One-at-a-time `steer` semantics moved here |

For JamBot voice flow: mostly improvement. Multiple in-flight user messages now get steered together at next model boundary.

### Anchor #4 — Embedded run timeout = 15s (production-observed, NOT in changelog)

Embedded path uses its own (low) default — NOT `agents.defaults.timeoutSeconds` (600s). Long-running tool calls (build pipeline, DataForSEO bulk, Suno) can silently fail at 15s with truncated output, no clear error.

Verification needed (run on 5.2 gateway):
```bash
openclaw config schema | jq '.properties.agents.properties.defaults' | grep -i timeout
openclaw doctor --json | jq '.config.agents.defaults'
```

## Other v4.x agent runtime changes (audit doc)

- v4.5: `agents.<>.sandbox.perSession` REMOVED → use `sandbox.scope` + `enabled`
- v4.7: `agents.defaults.systemPromptOverride` for controlled prompt experiments
- v4.7: heartbeat prompt-section controls so heartbeat behavior stays enabled without injecting heartbeat instructions every turn
- v4.9 line 2894: LLM idle timeout inherits `agents.defaults.timeoutSeconds` when configured; idle-timeout errors point at `agents.defaults.llm.idleTimeoutSeconds`
- v4.10 line 2776: default LLM idle window extended to 120s; silent no-token idle timeouts on recovery paths
- v4.10 line 2840: "Agent listener invoked outside active run" gateway crash FIXED
- v4.24: `agents.defaults.contextInjection: "never"` for agents that own their prompt lifecycle
- v4.26: `subagents.allowAgents` enforcement for same-agent self-targets
- v4.27: `subagents.runs.json` cache (line 379)
- v4.27: cron `--thread-id` (line 847)
- v4.29: `spawnedBy` field on subagent chat + agent broadcast events (line 412)
- v5.2: `agents.defaults.skipOptionalBootstrapFiles` for skipping selected optional bootstrap files
- v5.2: `threadBindings.spawnSessions` REPLACES split `subagents` / `acp` thread-spawn toggles

## JamBot impact

The 15s embedded timeout (anchor #4) is the silent killer. When DataForSEO/Suno/build-pipeline tool calls truncate, blame ends up on the wrong layer until you remember anchor #4 exists.

The queue-mode flip (anchor #14) interacts with the voice flow's wake-word/PTT lifecycle — see `overrides/voice-flow-quirks.md`.

## Bootstrap injection caps — anchor #5

Per-file caps in v5.2: TOOLS.md ~24K, MEMORY.md ~10.5K, others ~20K. Auto-truncated with marker. Override knob TBD (see anchor #5).

## Burns / incidents

- 2026-04-18: nine-fix cascade for empty-final + interrupt races on josh.jam-bot.com
- 2026-04-19: openvoiceui session recovery + interrupt stack
- 2026-05-04: anchor #4 + #14 documented from production observation

## Related JamBot files

- `audit-anchors/anchor-{4,5,14}.md`
- `playbooks/debug-empty-final.md` — the 13-fix cascade
- `overrides/voice-flow-quirks.md`
- `/jambot-voice-flow` skill — STT, wake word, PTT lifecycle
- `/jambot-performance` skill — heartbeat, contextPruning, compaction tuning
