---
anchor: 4
slug: embedded-run-timeout-15s
status: partially-confirmed
introduced: unknown (production-observed; needs upstream code citation)
changelog_lines: [2776, 2894, 822]
upstream_pages:
  - https://docs.openclaw.ai/concepts/agent.md
  - https://docs.openclaw.ai/concepts/retry.md
  - https://docs.openclaw.ai/gateway/configuration.md
old_behavior: "agents.defaults.timeoutSeconds (600s) applies everywhere"
new_behavior: "embedded path uses its own (low) default — 15s observed in production"
skill_files_affected:
  - "references/agent-runtime.md:351"
---

# Anchor #4 — Embedded run timeout = 15s default; lane timeout = 45s

## Status: PARTIALLY CONFIRMED

Production-observed during the 2026-05-04 session. Changelog evidence is thin:

- v4.10 line 2776: "extend the default LLM idle window to 120s and keep silent no-token idle timeouts on recovery paths"
- v4.9 line 2894: "make the LLM idle timeout inherit `agents.defaults.timeoutSeconds` when configured, disable the unconfigured idle watchdog for cron runs, and point idle-timeout errors at `agents.defaults.llm.idleTimeoutSeconds`"
- v4.27 line 822: "use a 15s Slack SDK pong timeout by default" — this is socket-mode ping, NOT embedded run timeout

The 15s/45s defaults Mike hit are likely:
- A new `tools.exec.command.embeddedTimeoutSeconds` or `agents.defaults.embeddedRunTimeoutSeconds` knob (NOT in changelog)
- OR the existing run-level guard with new defaults shipped in code without changelog mention

## Verification needed

Run on a 5.2 gateway:
```bash
openclaw config schema | jq '.properties.agents.properties.defaults' | grep -i timeout
openclaw doctor --json | jq '.config.agents.defaults'
```

Then update this anchor with the exact config key + default.

## JamBot impact

Long-running tool calls (build pipeline executors, DataForSEO bulk queries, Suno generation) can silently fail at 15s without any clear timeout error, just truncated output.

## Fix instruction (interim)

`annotations/concepts__agent.md`: "Embedded run timeout ≠ `agents.defaults.timeoutSeconds`. Embedded path uses its own (low) default — verify via `openclaw doctor` if you suspect a 15s cutoff. See audit-anchors/anchor-04 for follow-up."
