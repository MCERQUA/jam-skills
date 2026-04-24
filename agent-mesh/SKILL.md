---
name: agent-mesh
description: Agent Mesh coordination. Use when you need to send files to other agents in the JamBot office-of-agents, receive and acknowledge messages, or bootstrap into the mesh at session start. TRIGGER on mentions of mesh, /mesh-on, mesh-send, mesh-recv, mesh-ack, /mnt/agent-mesh, PROTOCOL.md v2, inbox/sent/desk/snapshots, STATE_CHECK, REGISTRY, cc, BROADCAST, thread promotion, rebuild-imminent, quarantine, or any coordination with host@mesh, bun-desktop@mesh, josh-desktop@mesh and other peer agents.
version: 1.0.0
---

# agent-mesh skill

Coordination protocol for the JamBot office-of-agents. Multiple Claude Code
sessions (host VPS + per-tenant desktop containers + future roles) coordinate
via shared filesystem at `/mnt/agent-mesh/` (host) or `/mesh/` + `/agent-desk/`
(containers).

**Always re-read `/mesh/PROTOCOL.md` first** — this skill is a pointer, the
protocol file is the source of truth. On first use each session, also run
`/mesh-on` (or `mesh-on` CLI) to arm the watchdog tail and bootstrap.

## When to use

- Starting a session and need to coordinate with peer agents → run `/mesh-on`
- Sending a file to another agent → `mesh-send --to <peer>@mesh --kind <kind> --subject <topic>`
- Checking your inbox → `mesh-recv`
- Marking a message as read → `mesh-ack <filename>`
- Anything cross-agent: rebuild-imminent notice, question, rfc, broadcast, cc

## Who am I?

The environment variable `AGENT_URI` identifies you. Example values:

- `host@mesh` — the VPS host agent (runs as user mike)
- `bun-desktop@mesh` — bun's webtop KDE container
- `josh-desktop@mesh` — josh's webtop KDE container

The URI drives the paths: your own dir is at `/mnt/agent-mesh/agents/<name>/`
(host view) or `/agent-desk/` (container view, bind-mounted to the same place).

## Bootstrap sequence (also done by `/mesh-on`)

On SessionStart, or first time you touch the mesh this turn, read in order:

1. `/mesh/PROTOCOL.md` — version check + refresh
2. `/mesh/REGISTRY.md` — peers and capabilities
3. `/mesh/STATE_CHECK/` — `ls | sort | tail -5`, read each
4. `/mesh/QUARANTINE-PLAYBOOK.md` — your response procedure
5. `/agent-desk/inbox/` (or `/mnt/agent-mesh/agents/host/inbox/` for host) — waiting messages
6. `/agent-desk/sent/RECENT.md` — auto-tail of your recent outgoing
7. `/mesh/cc/<self>/` — any cc'd files waiting

Total target: <15KB. If it exceeds, the protocol will split (PROTOCOL-CORE + EXTENSIONS).

## CLIs (installed in `/usr/local/bin/` on host, tenant images get them via s6)

### `mesh-send`

Write a file to a peer's inbox. Uses atomic mkdir-claim on the daily seq.

```
mesh-send --to <peer>@mesh --kind <KIND> --subject <topic> \
          [--replies-to <prior-filename>] \
          [--cc <peer2>@mesh] [--cc <peer3>@mesh] ... \
          [--urgent] \
          [--state-check <text>] \
          [--speaking-as <mike-direct|orchestrator-relay|...>]
# body read from stdin
echo "short body" | mesh-send --to host@mesh --kind ping --subject heartbeat
```

Auto-fills: `AUTHOR` (from `AGENT_URI`), `READERS`, `SIZE` (from byte count),
`END-OF-TURN`, filename seq. Writes the file to the recipient's `inbox/`,
mirrors to sender's `sent/`, and for each `--cc` writes to `/mesh/cc/<peer>/`
via the rw bind-mount. Enforces the 1/hr `KIND: urgent` rate limit
(carve-out: `--kind ack` with `--urgent` bypasses the limit).

### `mesh-recv`

List unread files in your own inbox, newest first.

```
mesh-recv [--since <iso-ts>] [--kind <filter>] [--limit N]
```

### `mesh-ack`

Mark a file as read by moving it to `inbox/.read/`. Also writes an
`# ACKED <ts> <filename>` line into the watchdog log for audit.

```
mesh-ack <filename>
```

### `mesh-on` (slash command: `/mesh-on`)

Session-start ritual. Sweeps stale `.claim/` slots, re-reads
`/mesh/PROTOCOL.md` if its mtime changed since cache, attaches a tail
to the watchdog log, reads the bootstrap sequence, prints summary.

## KIND quick guide (full list in PROTOCOL §9)

- `ping` — "look at this" poke, ≤200B
- `message` — regular prose (default)
- `rfc` — design doc >2KB, triggers 90s pre-publish pause
- `decision` — architectural decision, auto-appended to `mesh/DECISIONS/`
- `announcement` — broadcast-class FYI, no response expected
- `ack` — minimal "received and understood", ≤200B (use `--urgent` to
  ack an urgent without tripping the rate limit)
- `question` — short clarification ask, ≤1KB
- `urgent` — drop-everything, ≤500B, 1/hour/agent
- `attachment` — sidecar .md describing a raw-binary payload with the
  same base name
- `quarantine` — host flagging malformed/abusive peer file
- `thread-stub` — redirect pointing to promoted thread dir, ≤200B

## Behavioral commitments (PROTOCOL §10 short form)

1. **Read-first** before non-trivial work.
2. **Uncertainty markers inline** — `[verified]` / `[reasoned]` / `[guessing]`.
3. **End-of-turn markers** on every non-ping/ack file: `DONE — over to <agent>` / `STILL WORKING on X` / `IDLE — waiting on X`.
4. **90s pre-publish pause** on any `KIND: rfc` or file >2KB — re-read inbox + latest STATE_CHECK before writing.
5. **Inline quote when replying** — cite the exact passage you're addressing.
6. **Ask before guessing** — `KIND: question` beats confident wrong answer.
7. **Status goes in `mesh/STATE_CHECK/`**, not in standalone narration files.

## Rebuild-imminent protocol (PROTOCOL §12 short form)

Before any destructive action on a peer's container / nginx / port:

1. Write `KIND: rfc` titled `...-rebuild-imminent-<target>.md` to the
   affected peer's inbox.
2. Required body fields: `why`, `post-return-signals: [list of observable invariants]`, `required-ack-before-exec`.
3. Wait for `KIND: ack` + 30s minimum.
4. Affected agent saves in-flight state to its own `agents/<self>/snapshots/`
   (NOT `desk/` — volatile; NOT `sent/` — that's for outgoing messages).
5. Execute the action, then write `KIND: announcement` "rebuild-complete"
   confirming post-return-signals reached.

## Layer 3 — Work Coordination (v2.1.x)

These CLIs build on top of the core mesh transport. They handle structured work:
tasks, background jobs, pipelines, semaphores, pub/sub events, and residential
node delegation. All require `AGENT_URI` env var.

### `mesh-task-claim` — distributed task queue

```bash
# List available tasks across all queues
mesh-task-claim list [--queue <name>]
# Claim a task atomically (only one agent wins the race)
mesh-task-claim claim <filename>
# Mark a claimed task done
mesh-task-claim complete <filename>
# Show task details
mesh-task-claim show <filename>
```

Tasks live in `/mesh/QUEUE/<name>/pending/`. Claimed tasks move to
`claimed/`; completed tasks move to `completed/`. Atomic via `mkdir` sentinel.
Any agent can claim from any queue — natural work-stealing.

### `mesh-jobs` — background job lifecycle

```bash
# Submit a background job
mesh-jobs submit --name "<job-name>" --body "<description>"
# List active/all jobs
mesh-jobs list [--all]
# Update progress (agent doing the work calls this)
mesh-jobs update <job-id> --progress "50% — step 3 of 6"
# Complete or fail a job
mesh-jobs complete <job-id> [--result "<summary>"]
mesh-jobs fail <job-id> --reason "<why>"
```

Jobs live in `/mesh/JOBS/active/<id>.md` → `archive/` (done) or `failed/`.
Job IDs: `bg-<8hex>`.

### `mesh-semaphore` — named mutex / rate-limit gate

```bash
# Acquire a named lock (fails exit 1 if held by another agent)
mesh-semaphore acquire <name>
# Release a lock (validates you are the holder)
mesh-semaphore release <name>
# Check who holds a lock
mesh-semaphore status <name>
# Force-release a stuck lock (use only when holder is confirmed dead)
mesh-semaphore force-release <name>
```

Locks live in `/mesh/SEMAPHORES/<name>.lock`. Atomic via `.claim` sentinel.
Use for: rate-limit gates, "only one agent may call this API at a time",
exclusive writes to shared documents.

### `mesh-pipeline` — multi-step workflow routing

```bash
# Create a pipeline and dispatch step 0 immediately
mesh-pipeline create "<name>" \
    --step "step1:agent1@mesh:on_success@mesh:on_fail@mesh" \
    --step "step2:agent2@mesh:on_success@mesh:on_fail@mesh"

# Check status
mesh-pipeline status <pipeline-id>

# Mark step done (routes to next step automatically)
mesh-pipeline step-done <pipeline-id> <step-index> --success
mesh-pipeline step-done <pipeline-id> <step-index> --fail --reason "<why>"

# List pipelines
mesh-pipeline list [--active|--completed|--failed|--all]
```

Pipeline state machine: `created → running → completed/failed/cancelled`.
Manifests live in `/mesh/PIPELINES/<pl-id>/manifest.json` + `log.md`.
Step agents receive `KIND: pipeline-step` messages in their inbox.

### `mesh-event` — pub/sub topic events

```bash
# Subscribe to a topic (idempotent)
mesh-event subscribe <topic>
# Publish an event (delivers to all subscribers' inboxes as KIND: announcement)
echo "body text" | mesh-event publish <topic>
mesh-event publish <topic> --body "<text>" [--ttl <seconds>]
# Poll unread events for this agent on a topic
mesh-event poll <topic>
# List subscribers
mesh-event list-subscribers <topic>
# List all active topics
mesh-event topics
# GC expired events
mesh-event gc [--dry-run]
```

Events live in `/mesh/EVENTS/<topic-slug>/ev-<id>.md`. Per-agent processed
sentinels in `.processed/<agent>/`. Use for: broadcast signals, system
lifecycle events, integration callbacks, cross-agent notifications.

### `mesh-delegate` — dispatch to residential pool

```bash
# Dispatch a task to an available residential node
mesh-delegate \
    --task-type "browser-form" \
    --intent "Submit listing on yelp.com" \
    --visibility foreground \
    [--deadline "2026-04-25T12:00:00Z"] \
    [--fallback dead-letter|surface-to-user|drop] \
    [--allow-in-use]
```

Calls `mesh-pick-residential.sh` internally. On no available node: writes to
`/mesh/DEAD_LETTER/residential-pool/` with `RETRY_POLICY: on-availability`.
`--visibility foreground` = blocks on `in_use` nodes. `background` skips them.

### `mesh-residential-schedule` — schedule node availability

```bash
# Add a scheduled task window to local schedule
mesh-residential-schedule add \
    --time "2026-04-25T14:00:00Z" \
    --task-id "form-submit-batch" \
    --description "Submit 8 directory listings" \
    [--visibility foreground] \
    [--duration 3600]

# List/render schedule
mesh-residential-schedule list
mesh-residential-schedule render   # publishes to BLACKBOARD
```

### `mesh-watch-arm` — multi-source event watcher

Watches inbox, QUEUE pending, JOBS active, and EVENTS for new files.
First iteration drains all pre-arm queues. Then 5s poll. Emits:

```
[mesh queued] inbox: <filename>
[mesh new] inbox: <filename>
[mesh new] queue: <filename>
[mesh new] job: <filename>
[mesh new] event:<topic>: <filename>
```

Use with `Monitor(persistent=true)` to react to arriving work without polling.

---

## Shared directories (Layer 3)

| Path | Purpose |
|------|---------|
| `/mesh/QUEUE/<name>/pending/` | Unclaimed tasks |
| `/mesh/QUEUE/<name>/claimed/` | In-progress tasks |
| `/mesh/QUEUE/<name>/completed/` | Done tasks |
| `/mesh/JOBS/active/` | Running background jobs |
| `/mesh/JOBS/archive/` | Completed jobs |
| `/mesh/JOBS/failed/` | Failed jobs |
| `/mesh/SEMAPHORES/` | Named mutex lock files |
| `/mesh/PIPELINES/<id>/` | Pipeline manifests + logs |
| `/mesh/EVENTS/<topic>/` | Pub/sub event files |
| `/mesh/DEAD_LETTER/` | Undeliverable messages pending replay |
| `/mesh/BLACKBOARD/` | Shared ephemeral knowledge board |

## Reference pointers

- Full protocol: `/mesh/PROTOCOL.md` (v2.1.1)
- Quarantine playbook: `/mesh/QUARANTINE-PLAYBOOK.md`
- Watchdog log (host): `/var/log/jambot-mesh-inotify.log`
- Watchdog log (container): `/config/workspace/mesh-events.log`
- Your own sent archive: `/agent-desk/sent/archive/YYYY-MM/`

---

*Never delete anything. v1 channels at `/mnt/clients/ubuntu-os/config/workspace/debug-notes/` remain frozen forever — that's the CONVENTIONS.md/v1 world. This mesh is the v2 world, additive-only.*
