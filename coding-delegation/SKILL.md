---
name: coding-delegation
description: When and how to delegate coding tasks to sub-agents (maxcode, z-code, claude_launch). Use for canvas pages, games, dashboards, websites, or any task over 100 lines of code.
---

# Coding Delegation — Sub-Agents for Heavy Work

You MUST delegate these tasks — do NOT try to write them yourself:
- ANY canvas page (HTML games, dashboards, tools, visualizations)
- Files over 100 lines
- Multi-file refactoring
- Websites or web apps
- Anything requiring 500+ lines of code

**Why:** You run on GLM-4.7 with limited context. Sub-agents are built for code generation — they have file tools, can iterate, and cost less per token.

## MaxCode — High-Speed Coding CLI

`maxcode` is a command-line tool (NOT an ACP agent). Run it with `exec()`:

```
exec("maxcode -p 'Build a dashboard at /app/runtime/canvas-pages/my-dashboard.html. Dark theme, inline CSS/JS, no CDN.' --allowedTools 'Edit,Write,Read' 2>&1 | tail -20")
```

**Flags:**
- `-p "prompt"` — task description (be detailed, include full output path)
- `--allowedTools "Edit,Write,Read"` — REQUIRED for filesystem access
- `2>&1 | tail -20` — capture output

**When to use:** Full canvas pages, games, dashboards, any 500+ line file, complex interactive pages.

## Claude Launch — Background Coding Sessions

Spawns a background coding agent that works autonomously:

```
claude_launch({
  prompt: "Build a solar system at /app/runtime/canvas-pages/solar-system.html. Use Three.js import map from cdn.jsdelivr.net. Dark theme, inline CSS.",
  backend: "z-code",
  workdir: "/app/runtime"
})
```

**Tools:**
| Tool | Purpose |
|------|---------|
| `claude_launch` | Spawn a session with a prompt |
| `claude_respond` | Send follow-up instructions |
| `claude_kill` | Stop a session |
| `claude_sessions` | List active/completed sessions |
| `claude_output` | Read session output |
| `claude_fg` / `claude_bg` | Foreground/background |

**Backends:**
| Backend | Best For |
|---------|----------|
| `z-code` (default) | General coding — Z.AI credits |
| `maxcode` | High-speed bulk — MiniMax M2.7 |

## Critical Rules

1. **Always include the full absolute path** in your prompt. Canvas pages go to `/app/runtime/canvas-pages/<name>.html`.

2. **Always tell the user** you're launching a session and what it's building.

3. **Check output** with `claude_output` or `claude_sessions` to monitor progress.

4. **Don't duplicate work** — if a session is building something, don't also build it yourself.

5. **Review before showing** — after a session completes, read the file and verify before opening for the user.

## Passing Skill Context to Spawned Agents

Spawned agents (z-code/maxcode) have ZERO access to your skills, TOOLS.md, or conversation context. They only know what you put in the prompt.

**When a task needs skill knowledge:**
1. Read the skill first: `exec("cat /mnt/shared-skills/<skill>/SKILL.md")`
2. Extract the relevant rules and patterns
3. Include them in your `claude_launch` prompt or `system_prompt` parameter

**Do NOT:**
- Assume spawned agents know about your skills
- Say "use the stitch skill" in the prompt — it can't read skills
- Paste the ENTIRE skill file if it's huge — extract only relevant parts
