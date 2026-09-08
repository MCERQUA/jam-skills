---
name: handoff
description: Wrap up the current work and write a handoff file so a context reset costs nothing. TRIGGER when the user asks to hand off, wrap up, reset context, /clear, or when you notice your own context is nearly spent. The reading half is wired into the global agent instructions, not a separate skill — a fresh session is told to read the handoff file before doing anything else.
---

# handoff — make the reset free

The session is about to be reset. Your job is to make that reset FREE: nothing of value may
live only in this conversation when it ends.

`$ARGUMENTS` is the NEXT task (may be empty — then just close out cleanly).

🔴 **Knowing when to wrap up is part of the job.** Do not start substantial work on a nearly
spent context. Run this instead.

## 0. Where the handoff file lives — ONE stable path per agent

Resolve it in this order and use the first that applies:

1. `$CLAUDE_HANDOFF_FILE` if set (the operator has chosen a path — respect it).
2. `<project working directory>/.claude/NEXT-SESSION.md`.
3. `$HOME/.claude/NEXT-SESSION.md`.

Three rules about that path, each of which was paid for:

- 🔴 **Never a system temp directory.** A handoff under `/tmp`, `/private/tmp` or a
  per-session scratchpad is worse than no handoff, because you believe you have one. macOS
  purges `/private/tmp` on reboot; Linux distros clear `/tmp` on a timer. It must be a path
  that survives a reboot.
- 🔴 **Never a glob.** One exact path. A per-session directory that has to be searched for
  means the next session picks the wrong one, and there are always more siblings than you
  expect.
- 🔴 **Never a shared filesystem path.** If your mesh root (e.g. `/mnt/agent-mesh`) is mounted
  read-write, it is shared with every other agent — a handoff written there is a file other
  agents overwrite. Keep it local to your own filesystem.
- 🔴 **If two agent identities share one home directory, the path must differ per agent.**
  Set `CLAUDE_HANDOFF_FILE` for each, or give each its own project directory. Two agents
  writing one handoff file silently hand each other the wrong task.

## 1. Close out what's open — do it, don't describe it

- Append what was learned to the relevant rig's / project's `LEARNINGS.md` (or its equivalent).
- Update the board, register, or client kit if a fact changed.
- `git commit` every repo you touched. `git push` if the repo has a remote and pushing is
  yours to do.
- Deliver anything finished but unsent — every delivery destination your node owes, not just
  the easiest one. Then notify the requester over the mesh.
- Mesh hygiene: ack what you completed. 🔴 Do NOT ack work you did not finish — leave it
  unread so the next session inherits it honestly.
- Save a memory ONLY for facts that are durable and not already captured in a repo file.

## 2. Write the handoff file

🔴 This is a POINTER SET, not a summary. Everything durable is already in files; the handoff
carries only the delta a fresh session cannot reconstruct.

```
# NEXT SESSION
## Task
<the next task, verbatim from $ARGUMENTS or the mesh message id>
## Read first (in this order)
<2-4 exact paths — the rig's instructions, the LEARNINGS tail, the specific data file>
## Facts not written down anywhere
<the 3-5 things you know only because you were here. If it is in a file, DO NOT repeat it.>
## Live background tasks (do NOT re-arm these after the reset)
<TaskList output: monitor/watcher ids + what each watches. These SURVIVE a context reset
 whenever the process itself keeps running, e.g. a session inside tmux.>
## In flight / half-done
<anything started and not finished, with how to resume — or "nothing">
## Traps
<what would bite a fresh session in the first 10 minutes>
```

Write the *reasons*, not just the facts. "Do not use X, it was rejected on <date> because
<reason>" saves the next session the whole round trip.

## 3. Verify the reset is safe

🔴 Say NO to the reset and explain why if any of these are true:

- a render / long job is still running (its in-session state dies with the conversation)
- something is delivered but UNVERIFIED (you would lose the fact that you never checked it)
- a mesh task is acked but not actually done

## 4. Make sure it actually gets read

🔴 **A handoff nobody opens is worse than no handoff**, because the session that wrote it
believes the reset is paid for. This skill only WRITES. Something has to READ.

If your deployment has the companion `next` skill, that is the reader and you are done. If it
does not, the reading step must live in the global agent instructions instead — one line, and
it is the install step that makes this skill work at all:

> At the start of a session, read the handoff file if one exists (`$CLAUDE_HANDOFF_FILE`, else
> `<project dir>/.claude/NEXT-SESSION.md`, else `$HOME/.claude/NEXT-SESSION.md`), open the
> files it lists in the order given, and check `TaskList` before arming any watcher — watchers
> survive a context reset whenever the process does.

Before you rely on this skill, confirm one of those two readers is in place. Writing to a path
no reader knows about is the failure this section exists to prevent.

## 5. Print exactly this and stop

```
handoff written — <path>
uncommitted: <none | list>   unacked mesh: <none | list>
safe to reset: YES|NO  <one-line reason if NO>

→ reset the context; the next session reads that file first
```
