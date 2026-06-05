---
name: cli-coding-agents
description: Z-Code CLI coding agent — local exec binary (NOT a network service or ACP agent) for heavy coding tasks like canvas pages, games, dashboards, and multi-file edits. Read before delegating any 100+ line file or multi-step coding task.
---

# Z-Code — CLI Coding Agent

You have a coding CLI tool on PATH. Use it for ANY heavy coding task (canvas pages, games, dashboards, multi-file edits, 100+ line files). Run via `exec()` — this is NOT an ACP agent, NOT a network service. It is a local binary.

## Z-Code (GLM via Claude CLI)

```bash
exec("z-code -p 'Build X at /app/runtime/canvas-pages/my-page.html. Dark theme, inline CSS/JS, no CDN.' --allowedTools 'Edit,Write,Read' 2>&1 | tail -30")
```

## Rules

- `--allowedTools "Edit,Write,Read"` is **REQUIRED** or it can't touch files
- Always pipe through `| tail -30` to capture output
- For full details: `exec("cat /mnt/shared-skills/coding-delegation/SKILL.md")`
- **NEVER say "ACP not configured" or "can't spawn agents"** — z-code is an exec tool, not a network service
- **If z-code times out on a large file**, break the task into sections (structure → CSS → JS) as separate exec calls

## Passing skills to Z-Code

When the user says "use /skill-name in z-code", run:

```bash
exec("z-code -p 'Read /mnt/shared-skills/<skill-name>/SKILL.md then answer: <the user question>' --allowedTools 'Read,Glob,Grep' 2>&1 | tail -50")
```
