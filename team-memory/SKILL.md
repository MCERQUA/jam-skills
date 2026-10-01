---
name: team-memory
description: ONE shared memory + task board for every agent serving the same person (e.g. Danielle's laptop, desktop, voice and sms lanes). Read `team context` at session start; `team remember` facts the other lanes need; `team task-add` / `team task-set` to coordinate work. TRIGGER at session start, when you learn something about the person's work/preferences/projects that another lane should know, or when you take, hand off or finish a piece of work for them.
---

# team-memory — one brain across lanes

Mike, 2026-10-01: *"her laptop, desktop and voice and sms agents all need to share the same
context/memory/task managers."* Each lane used to keep its own memory, and none of it was shared.
This store is the shared part. Your own private memory still exists; this is what the TEAM knows.

**Where it lives:** `<tenant workspace>/team/`, inside the tenant's own jail cell:
`MEMORY.md` (append-only shared memory), `tasks.json` (task board; `TASKS.md` is generated from it).

## How to run it (same tool everywhere)

| Lane | Command |
|---|---|
| Tenant container (openclaw voice/sms) | `python3 /mnt/shared-skills/team-memory/bin/team <cmd>` |
| Webtop desk | `python3 /skills/team-memory/bin/team <cmd>` |
| Remote laptop (restricted door) | `~/jambot-mesh/bin/mesh team <cmd>` |
| Host | `python3 /mnt/system/base/skills/team-memory/bin/team --tenant <t> <cmd>` |

`AGENT_URI` must be set. It becomes the author, and its first segment is the tenant
(`danielle-desktop@mesh` -> danielle).

## Commands

```
team context                         # session start: memory + open tasks
team memory                          # the shared memory
echo "<fact>" | team remember        # one fact per entry, short; link to detail instead of pasting it
team tasks [--all]
team task-add "<title>" [--owner <agent>@mesh] [--for <person>] [--note "<text>"]
team task-set <T001> <open|doing|waiting|done> [--owner <agent>@mesh] [--note "<text>"]
```

## The habits that make it one brain

1. **Session start:** run `team context` before anything else.
2. **Learned something another lane needs** (a preference, a decision, a project's state, a
   correction)? `team remember` it immediately. Don't wait for the end of the session.
3. **Taking work:** `task-set <id> doing --owner <you>`. **Handing it off:** `task-set <id> waiting
   --owner <them> --note "why"`, plus a mesh message to them. **Finished:** `task-set <id> done --note
   "<what was delivered, where>"`.
4. **Results go back to whoever asked** (the `for` field). Never to a client/account owner unless the
   person says so.
5. **Never put secrets here** (keys, passwords, codes). Never put another client's data here.
6. A failure reading the store is **CANNOT-TELL**, not "the team knows nothing". Say so.
