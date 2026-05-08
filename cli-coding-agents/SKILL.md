---
name: cli-coding-agents
description: MaxCode and Z-Code CLI coding agents — local exec binaries (NOT network services or ACP agents) for heavy coding tasks like canvas pages, games, dashboards, and multi-file edits. Read before delegating any 100+ line file or multi-step coding task.
---

# MaxCode & Z-Code — CLI Coding Agents

You have two coding CLI tools on PATH. Use them for ANY heavy coding task (canvas pages, games, dashboards, multi-file edits, 100+ line files). Run via `exec()` — these are NOT ACP agents, NOT network services. They are local binaries.

## MaxCode (MiniMax M2.7, fast)

```bash
exec("maxcode -p 'Build X at /app/runtime/canvas-pages/my-page.html. Dark theme, inline CSS/JS, no CDN.' --allowedTools 'Edit,Write,Read' 2>&1 | tail -30")
```

## Z-Code (GLM-4.7 via Claude CLI)

```bash
exec("z-code -p 'Your task here' --allowedTools 'Edit,Write,Read' 2>&1 | tail -30")
```

## Rules

- `--allowedTools "Edit,Write,Read"` is **REQUIRED** or they can't touch files
- Always pipe through `| tail -30` to capture output
- For full details: `exec("cat /mnt/shared-skills/coding-delegation/SKILL.md")`
- **NEVER say "ACP not configured" or "can't spawn agents"** — these are exec tools, not network services

## Passing skills to MaxCode/Z-Code

When the user says "use /skill-name in maxcode", run:

```bash
exec("maxcode -p 'Read /mnt/shared-skills/<skill-name>/SKILL.md then answer: <the user question>' --allowedTools 'Read,Glob,Grep' 2>&1 | tail -50")
```
