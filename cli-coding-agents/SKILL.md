---
name: cli-coding-agents
description: CLI coding agents (z-code, claude-code, opencode) — registry-driven launcher for heavy coding tasks. z-code runs locally; claude-code/opencode run host-side via the dispatch queue under proper subscriptions. Read before delegating any 100+ line file, multi-step coding task, or when the user names a specific coding agent.
---

# CLI Coding Agents

You have access to REAL coding agents — full agentic harnesses that are much better at heavy coding than doing it yourself. They are registry-driven: check `registry.json` in this directory for what's available.

## The one launcher

```bash
exec("bash /mnt/shared-skills/cli-coding-agents/run.sh <agent-name> 'Build X at /app/runtime/canvas-pages/my-page.html. Dark theme, inline CSS/JS. Include the FULL absolute output path.'")
```

| Agent | What it is | When |
|-------|-----------|------|
| `z-code` | Claude Code harness on GLM (local, always available) | **DEFAULT** for all heavy coding |
| `claude-code` | Real Claude (Anthropic), runs host-side | Escalation: hardest work, or user asks for Claude by name |
| `opencode` | Alternative harness | When enabled in registry |

**If the user names an agent ("use z-code", "use claude code", "use opencode") — use that one.** If it's disabled, say so plainly and offer z-code.

## NON-NEGOTIABLE: wrap it in a sub-agent

`run.sh` BLOCKS until the coding agent finishes (up to 14 min). NEVER call it from the main voice session. Always:

```
sessions_spawn({
  task: "Run: bash /mnt/shared-skills/cli-coding-agents/run.sh z-code '<detailed brief with full output path>' — then verify the output file exists and summarize what was built in .agents/<label>.md",
  label: "cli-<short-name>"
})
```

Speak first ("I'm putting a real coding agent on it — I'll open it on screen the moment it's done"), then spawn. The completion loop announces the result to the user automatically.

## How remote agents work (claude-code, opencode)

Their subscriptions can't live inside this container. `run.sh` files your task to `.cli-tasks/` and the HOST runs it in your workspace, then your run.sh call returns with the result. Up to ~1 min extra latency (dispatcher polls every minute). Everything else is identical from your side.

- Filesystem view differs host-side — **give output paths RELATIVE to the workspace root** in remote briefs (e.g. `canvas-pages/my-page.html`): that resolves correctly in both modes. `/app/runtime/...` paths only exist locally.

## Rules

- Always include the complete output path in the prompt — the agent can't guess it
- Be detailed in the brief: sections, style rules, data contracts, done-criteria
- If a local run times out on a huge file, split the task (structure → CSS → JS)
- **NEVER say "ACP not configured" or "can't spawn agents"** — these are exec tools, not network services
- After the CLI agent finishes, VERIFY the output file exists before telling the user it's done
- More background: `exec("cat /mnt/shared-skills/coding-delegation/SKILL.md")`

## Passing skills to a CLI agent

```bash
exec("bash /mnt/shared-skills/cli-coding-agents/run.sh z-code 'Read /mnt/shared-skills/<skill-name>/SKILL.md then: <task>'")
```

## Direct z-code (legacy form, still valid for quick local runs)

```bash
exec("z-code -p 'Build X at /app/runtime/canvas-pages/my-page.html.' --allowedTools 'Edit,Write,Read' 2>&1 | tail -30")
```
