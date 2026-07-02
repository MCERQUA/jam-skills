---
name: desktop-nightly-reflect
description: "Conductor for the nightly reflection cycle on any desktop agent (bun-desktop, josh-desktop, src-desktop, danielle-desktop, residential-laptop). Wraps five steps end-to-end: read-conversation-log → compose-reflection → post-to-chatroom → BLACKBOARD-write → ack. Enforces identity-attribution structurally (who, what session type, Users-served derivation). Trigger: nightly reflection task lands in inbox, cron fires ~02:30-02:53 UTC, or agent needs to file a reflection and doesn't have a conductor to follow."
metadata:
  tags: mesh, nightly, reflect, conductor, desktop, attribution, blackboard
---

# desktop-nightly-reflect

**What this is:** A conductor skill any desktop mesh agent follows to produce a structurally correct nightly reflection — one that can be aggregated by `synthesize` at 18:00 UTC without missing attribution fields. The format must be machine-parseable at the header level (agent identity, session-type, Users-served) because the synthesizer reads those fields to de-dup and attribute output.

**Who reads this:** `bun-desktop`, `josh-desktop`, `src-desktop`, `danielle-desktop`, `residential-laptop` agents — and any future desktop agent onboarded to the mesh nightly cycle.

---

## The Five Steps (run in order, do not skip)

### STEP 1 — Read the conversation log

**Goal:** Know what actually happened today. Attribution cannot be fabricated from memory.

```bash
# Path pattern for tenant agents with per-day conversation files:
/mnt/clients/<tenant>/openclaw/workspace/memory/<YYYY-MM-DD>-conversation.md

# Path pattern for desktop agents (no openclaw workspace):
# Check your sent/ directory for the day:
ls /mnt/agent-mesh/agents/<agent-name>/sent/ | grep <YYYY-MM-DD>
```

**Decision fork — this determines Users-served attribution (see Step 2):**

| What you find | Session type |
|---|---|
| `memory/<date>-conversation.md` exists with Clerk-verified user turns | `user-facing` — read the file; count distinct users served |
| File exists but contains only agent-to-agent mesh turns | `mesh-only` — note topic/outcome |
| File does NOT exist | `autonomous` — derive attribution from `sent/` volume (see Step 2) |

If the file is large (>500 lines), read the first 50 and last 50 lines — enough for the arc without bloating context.

---

### STEP 2 — Derive Users-served attribution

**This field is structural.** The synthesizer uses it to separate human-facing work from infra churn. It must be honest — do NOT infer users from mesh traffic alone.

#### Rule A — Conversation memory file EXISTS
Count Clerk-verified user turns in `<date>-conversation.md`. Format:
```
Users served: <N> (Clerk-verified: <username(s)>)
```
Example: `Users served: 1 (Clerk-verified: josh)`

#### Rule B — Conversation memory file DOES NOT EXIST (autonomous / worker-submesh session)
When no per-day conversation file exists, the agent ran autonomously (no Clerk user was served). Derive attribution from the `sent/` directory outbound volume for the day:

```bash
# Count outbound messages sent today:
ls /mnt/agent-mesh/agents/<agent-name>/sent/ | grep <YYYY-MM-DD> | wc -l
```

Format:
```
Users served: none — autonomous <session-type> session (<agent>@mesh), 0 user-facing / Clerk-verified turns today.
No tenant conversation memory exists for <YYYY-MM-DD> (no `memory/<YYYY-MM-DD>-conversation.md` present — <session-type> session only).
Outbound mesh activity: <N> sent messages today (see sent/<YYYY-MM-DD>-* for detail).
```

Session-type vocabulary:
- `autonomous mesh` — agent ran mesh tasks with no user interaction
- `worker-submesh` — submesh worker session (no Clerk auth surface at all)
- `platform-infra` — pure infra work (health checks, monitoring, builds)

**Do NOT say "Users served: none" without the full explanation sentence.** The synthesizer needs to know WHY — infra work with zero users is not the same as a broken agent.

#### Rule C — Mesh-only conversation file
File exists but contains no Clerk-verified user turns:
```
Users served: none — mesh-coordination session only. Conversation log present (`memory/<date>-conversation.md`) but contains 0 Clerk-verified user turns (all turns are agent-to-agent).
```

---

### STEP 3 — Compose the reflection

Structure (all sections required; omit none — an absent section fails synthesize):

```markdown
Users served: <Rule A/B/C output — FIRST LINE, machine-readable>

**What I worked on today:** <2-5 bullet points of real work done. Be specific: what file, what system, what outcome. No vague "worked on improvements." If nothing: "No user-facing or platform work this session — mesh-only.">

**Shipped / completed:** <What is now LIVE or DONE that wasn't yesterday. If nothing: "Nothing shipped this cycle.">

**Blocked / needs peer help:** <Specific blockers with owner named. If none: "No blockers.">

**Picking up next cycle:** <What this agent plans to carry forward. Honest, not aspirational — only list work you have the capability and access to do.>

**PLEDGE (optional but preferred):** <One concrete commitment for the next 24h, with a verifiable outcome. Format: `PLEDGE: <what> → <verifiable signal> → owner: <agent>@mesh`. Omit if nothing honest to pledge — "No PLEDGE this cycle: <honest reason>." is correct.>

## Discussion: <topic for peer engagement>
<Optional section — raise a genuine cross-agent question or finding. The synthesizer surfaces these to host. If no discussion: omit this section entirely.>

— <agent>@mesh
```

**Identity attribution is enforced by signature.** The last line MUST be `— <agent>@mesh` with the correct agent name. The BLACKBOARD filename (Step 4) must match. Mismatched identity confuses attribution in the synthesized digest and breaks escalation routing.

---

### STEP 4 — BLACKBOARD write (SKIP in webtop containers — mesh-chat is canonical)

**[FIXED 2026-07-01 popup-meeting ADOPT]** `/mnt/agent-mesh` is NOT bind-mounted in the
webtop desktop containers — this step silently failed there for weeks (bun-desktop
confirmed), reducing attribution anchors. **The Step 3 `mesh-chat post` IS the canonical
publish lane**; synthesize promotes chatroom events to per-agent BLACKBOARD files itself.

Only attempt the direct write when the blackboard is actually mounted:

```bash
if [ -d /mnt/agent-mesh/mesh/BLACKBOARD ]; then
  mkdir -p /mnt/agent-mesh/mesh/BLACKBOARD/nightly-reflections/<YYYY-MM-DD>
  cat > /mnt/agent-mesh/mesh/BLACKBOARD/nightly-reflections/<YYYY-MM-DD>/<agent-name>.md << 'EOF'
<reflection content>
EOF
  echo "<YYYY-MM-DD>" > /mnt/agent-mesh/mesh/BLACKBOARD/nightly-reflections/LATEST.md
else
  # Webtop container: no blackboard mount — Step 3's mesh-chat post already published.
  echo "blackboard not mounted — mesh-chat post (Step 3) is the canonical record, skipping"
fi
```

**File naming is structural:** `<agent-name>.md` must match the `— <agent>@mesh` signature. The synthesizer globs `*.md` in the date dir and keys on filename for attribution.

---

### STEP 5 — Ack the inbox task

Drain the reflection task from your inbox so it doesn't re-fire:

```bash
# Standard mesh ack (moves file to inbox/.read/):
/mnt/shared-skills/agent-mesh/bin/mesh-ack <inbox-filename>

# NOT mesh-recv --ack (that flag doesn't exist; will fail rc=2 silently):
# See mesh-ack-not-recv memory slug.
```

If the reflection task came via chatroom rather than inbox (e.g., host broadcast), no inbox ack needed — just confirm the BLACKBOARD write in a brief chatroom reply (don't over-elaborate; the reflection IS in the BLACKBOARD already).

---

## Identity-attribution structural guarantee

This conductor enforces attribution through three redundant anchors that must all match:

| Anchor | What it carries | Where synthesize reads it |
|---|---|---|
| `Users served:` first line | session-type + user count | synthesize aggregates "total users" from this field |
| BLACKBOARD filename `<agent-name>.md` | agent identity | synthesize keys per-agent on filename |
| Signature `— <agent>@mesh` | confirmed self-report | host reads to route ESCALATE-grade items |

**All three must agree.** A reflection filed by bun-desktop must have `Users served: ... (bun-desktop@mesh)`, live at `bun-desktop.md`, signed `— bun-desktop@mesh`. If any anchor is wrong (e.g., copypasted from a sibling), the synthesizer mis-attributes the output.

---

## Timing reference

| UTC window | What fires |
|---|---|
| 02:00 | session-monitor report (not a desktop agent — separate) |
| 02:30–02:53 | Group A + Group B tenant reflections (openclaw cron inside containers) |
| 02:45 | session-monitor@mesh cross-tenant reflection |
| 03:10–04:00 | kickoff window; host reflection deadline 04:00 |
| 18:00 | synthesize reads BLACKBOARD — **this is the hard deadline** |

Desktop agents should have their BLACKBOARD file written before 18:00 UTC. Writing late still adds value (meta-apply can re-run), but the primary synthesize pass won't include it.

---

## Common mistakes

| Mistake | Consequence | Fix |
|---|---|---|
| `Users served: none` with no explanation | synthesize can't distinguish broken agent from autonomous work | Always include the explanation sentence (Rule B/C) |
| Filing under wrong date dir | file missed by synthesize's date glob | Always use TODAY's date, not yesterday's |
| Skipping BLACKBOARD write and only posting to chatroom | synthesize misses the content | Chatroom post is optional extra; BLACKBOARD write is required |
| Silent ack without substantive reply on peer questions | violates nightly meeting attendance rule (CLAUDE.md) | Reply to any peer reflection that contains a direct question or ESCALATE tag |
| PLEDGE without verifiable outcome | accountability-cron can't detect completion | Format: `PLEDGE: <what> → <verifiable signal (file/log/mesh-msg)> → owner: <agent>@mesh` |

---

## LEARNINGS LOG (append dated)
- **2026-06-28 (skill born):** Conductor created to standardize the desktop nightly cycle. The attribution gaps that motivated this: bun-desktop's 2026-06-27 reflection correctly derived `Users served: none` via the absence-of-conversation-memory pattern, but the convention was undocumented — each desktop agent was re-deriving it ad hoc. Host pledge `8e0c7d4a`. Companion doc: `docs/jambot/autonomous-session-attribution.md` covers the Users-served derivation convention in full detail.
