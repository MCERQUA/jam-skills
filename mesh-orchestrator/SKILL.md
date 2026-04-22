---
name: mesh-orchestrator
description: "host@mesh conductor pattern — decompose a multi-agent task, dispatch briefs, track in-flight state, aggregate replies, surface to Mike only on decisions/blockers/completion. Codifies the conductor role Claude Code sessions use when running multi-agent rollouts (config audits, canonical-tree ships, Phase-N verifications). Trigger: 'orchestrate', 'multi-agent', 'dispatch to agents', 'coordinate rollout', 'rollout the thing', 'audit all agents', 'ship to all webtops'."
---

# mesh-orchestrator

**Who reads this:** host@mesh Claude Code sessions when a user directive maps to work across multiple mesh agents. Codifies the "conductor" pattern so each session does it the same way instead of re-deriving.

## When to orchestrate (vs one-agent dispatch)

Orchestrate when:
- The deliverable has per-agent dependencies (ship to bun, ship to josh, ship to residential)
- Any change requires verification on multiple nodes (Phase 5.5 E2E across 3 agents)
- Config rollouts (skills sync, deploy keys, compose bake)
- Audit sweeps ("are all agents healthy / configured / on-version")

Don't orchestrate when:
- A single agent can do the whole thing (delegate to that one)
- The task is pure research (give it to the most-capable idle agent, don't spin up coordination overhead)
- You're the only one who can do it (just do it, don't pretend to coordinate)

## The five-step loop

### 1. Decompose

State the end goal in one sentence. List per-agent deliverables. If different agents get different scopes, write the scope-map in the brief (table is fine).

Example — **end goal:** "every webtop agent has write access to their scoped canonical repos."
- bun-desktop → ovui-bridge + ovui-desktop + OVUI-Ubuntu + jam-skills
- josh-desktop → ovui-bridge + ovui-desktop + jam-skills
- residential-laptop → ovui-bridge + jam-skills

Write the scope-map once; reuse in both the host-side script (`setup-agent-push-keys.sh`) AND the dispatch briefs so agents see the same picture.

### 2. Dispatch

**Same brief template for each agent, with scope substituted.** Loop over agents with a bash for-loop feeding stdin to `mesh-send --to <agent>@mesh`. Include:

- Clear subject (agents' filters look at subject)
- Per-agent scope (what THIS agent specifically gets)
- Verification steps (how agent knows it worked)
- Reply format (subject convention, tuples expected, etc.)
- `--end-of-turn` (e.g. `"<agent>@mesh — reply with <corr-id>-result"` or `"none"` for purely informational)

Don't dispatch bulk same-body to all agents if scopes differ — write it once per agent with the right scope in the body.

### 3. Track

Keep in-flight state in your current conversation context (don't spin up an external state file for a 3-agent rollout). Mental model:

```
rollout-id: phase5.5-e2e
  bun-desktop:        dispatched @ <ts> → awaiting reply
  josh-desktop:       dispatched @ <ts> → GREEN (r01-result landed)
  residential-laptop: dispatched @ <ts> → BLOCKED (HF 503, waiting warm)
```

For long rollouts (>5 agents or >2 hours), file a `reference_rollout_<name>.md` memory so future-you can resume. For routine rollouts (what host@mesh does daily), don't — conversation context is enough.

### 4. Aggregate

Process replies as they land via monitor events. For each reply:

- Green result → ack silently (`kind=message`, `end-of-turn: none`), update local mental state
- Blocker → diagnose, dispatch follow-up brief with unblocks, OR escalate to Mike if unblocker needs his hands (sudo, OAuth, decisions)
- Retraction / correction → update local state, silently ack

Use mesh-send rate limits as your guide for noise level. If you're sending >1 ack per agent per ~5 min, you're probably being too chatty — consolidate into one per-cycle message instead of one per event.

### 5. Close

When all agents are green (or non-blocking items are accepted):

- Update registry entries (`/mnt/agent-mesh/mesh/REGISTRY/<agent>.md`) if role/status changed
- Update MEMORY.md index if the rollout landed a new durable rule
- File follow-up TODOs as separate memory entries (non-blocking items)
- **Surface to Mike** with a single tight summary — what landed, what's next, what requires his hands (sudo, creds, decisions). ONE message per completed rollout, not per-agent.

## Silent-mesh rule in this context

Per `feedback_silent_mesh_processing` memory: mesh housekeeping is INVISIBLE to Mike. He sees only: (a) decisions that need his input, (b) unresolvable blockers, (c) user-facing task completions.

Orchestrator-specific application:
- Dispatches — silent. Mike doesn't need to see every brief.
- Acks — silent. Mike doesn't need to see every "ok green".
- Corrections / minor back-and-forth — silent.
- Surface: **"all 3 agents green"** OR **"blocker — need your sudo"** OR **"decision required: A or B?"**.

## Decomposition patterns

### Pattern A — scope map

Agents get the same general brief, different per-agent scopes. Use when rollout differs by agent capability/role:

- Ship to canonical (which repos each agent can write to)
- Audit config (each agent reports own state)
- Install feature (per-agent env differs)

### Pattern B — sequential dependency

Agent 1 must finish before Agent 2 starts. Typically because Agent 2 pulls from Agent 1's output. Pattern:

1. Dispatch to A with expected deliverable
2. Wait for A's reply
3. Extract deliverable, embed in brief for B
4. Dispatch to B

Don't pre-dispatch to B hoping A will land in time — handles the race badly.

### Pattern C — research then converge

1. Dispatch same research question to multiple agents in parallel
2. Aggregate findings
3. Synthesize into a plan
4. Dispatch the plan to one agent for execution

This session's model-routing work (residential research → host synth → residential execute) is pattern C.

### Pattern D — mirror + verify

1. Land the change on node A, verify
2. Use A's green as blueprint for nodes B & C
3. Dispatch mirror with verification steps
4. Final sweep confirms all 3 green

Phase 5.5 grounder rollout was pattern D (josh first, then bun, then residential).

## Mesh-send hygiene

Every brief should include:

- **Subject** starts with the deliverable type + agent-specific hint
  (e.g. `"Phase 5.5 ui_ground — E2E smoke on your bridge"`, NOT `"hi"`)
- **Correlation ID** for async replies (use the existing `<feature>-<phase>-r<N>-result` convention)
- **Deadline** if time-sensitive (ISO8601 or relative)
- **Expected return shape** so the agent knows what a good reply looks like
- **`end-of-turn` frontmatter** — `<agent> — reply with ...` for reply-expected, `none` for informational

Never paste secrets inline (see `feedback_mesh_secrets_pattern`). Pre-send grep for token patterns before hitting mesh-send. This rule matters more when dispatching at scale because one leaky brief contaminates every replica.

## Surfacing pattern

When you surface to Mike at close-of-rollout, the message template:

```markdown
**<rollout name> — DONE/BLOCKED/GREEN across N agents**

| Node | State | Notes |
|---|---|---|
| bun | ✅ | <brief win> |
| josh | ✅ | <brief win> |
| residential | ⏳ | <what's outstanding, who owns> |

**Needs you:** <list, or "nothing">
**Filed follow-ups:** <list of memory files>
**Commits:** <list of SHAs>
```

This is the density Mike expects. Don't blow it out with the full mesh-chatter transcript — he saw the mesh events as they landed.

## Anti-patterns

- ❌ Surfacing every mesh-send to Mike ("ok, dispatched to bun...", "ok, got green from josh...") — spams him with plumbing
- ❌ Asking Mike permission for per-agent dispatches when he approved the rollout — waste of turns
- ❌ Re-deriving the decomposition mid-rollout — write the scope-map upfront
- ❌ Dispatching before writing the verification step — agents will ship, you'll have no way to confirm
- ❌ One giant mesh message per agent with every possible instruction — split by concern (install + verify + reply format, each short)
- ❌ Letting a blocker sit silently — if an agent reports BLOCKED and you can't unblock within your current turn, surface to Mike OR escalate to another agent; don't leave it hanging

## Cross-refs

- `feedback_silent_mesh_processing` — Mike's "don't be the receptionist" rule
- `feedback_all_sessions_are_you` — commit + push at close
- `feedback_mesh_secrets_pattern` — pre-dispatch secret scan
- `agent-git-push-workflow` — so agents can ship their own commits during execution
- `jambot-tenant-workspace` — if rollout touches tenant files
- PROTOCOL.md — mesh protocol v2.0.1
