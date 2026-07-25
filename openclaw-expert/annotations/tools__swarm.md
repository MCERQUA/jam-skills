---
upstream: https://docs.openclaw.ai/tools/swarm
relevance: jambot-critical
last-verified: 2026-07-25
audit_anchors: [24]
related_pages: [tools__code-mode, tools__subagents, concepts__delegate-architecture, concepts__multi-agent]
---

# Swarm — JamBot annotation

New page in the 2026-07-25 catalog rebuild. Experimental, opt-in sub-agent fan-out driven from a [Code Mode](/tools/code-mode) script.

## ⚠️ Not available at our pin

`tools.swarm` **does not exist** in the live `2026.5.7` schema (verified via `openclaw config schema`; no `swarm` or `codeMode` paths at all). Neither does Code Mode, which Swarm is built on. Both arrived after our pin.

What we *do* have at `2026.5.7` is `agents.defaults.subagents.*` — and it is already configured in `/mnt/system/base/templates/openclaw.json`:

```json5
subagents: {
  maxConcurrent: 8,
  maxSpawnDepth: 2,
  maxChildrenPerAgent: 4,
  archiveAfterMinutes: 60,
  model: "zai_fb/glm-5-turbo",
  runTimeoutSeconds: 900,
}
```

So the JamBot answer to "can our agents fan out work?" is **yes, via subagents — not via Swarm.** See `annotations/tools__subagents.md`.

## What Swarm adds over plain subagents (for the upgrade decision)

Upstream's framing: *"There is no graph DSL and no separate workflow format. The program is the orchestration."* You write ordinary JS/TS control flow (`Promise.all`, `while`, `if`) inside a Code Mode script, and Swarm supplies:

- awaitable **collector children** with structured results
- **bounded concurrency** and fan-out caps
- live **progress reporting** into the session dashboard
- first-completion pipelines and decision gates

Config shape (7.x), for reference when the pin moves:

```json5
tools: {
  swarm: {
    enabled: true,
    maxConcurrent: 8,
    maxChildrenPerGroup: 50,
    maxTotalPerGroup: 200,
    waitTimeoutSecondsMax: 600,
    defaultAgentId: "",
  },
}
```

`tools.swarm: true` is accepted as boolean shorthand for enabled-with-defaults. The recommended enable path is **Settings → Labs → Swarm** in the Control UI, which writes the key immediately — note that this is a **UI path that mutates `openclaw.json`**, so it is one of the few sanctioned non-CLI config writes (`overrides/config-edit-policy.md`).

## Adopt-or-not, honestly

**Do not plan a Swarm adoption yet.** Three reasons, in order:

1. **It does not exist on the version we run.** Any design work is speculative until the pin moves (`playbooks/upgrade-5.7-to-7.x.md`).
2. **It is marked experimental.** Same caution as anchor #28 gives for `openclaw fleet` — experimental upstream surfaces change without a deprecation window, and JamBot has a working alternative.
3. **We already have an orchestration layer.** The client sub-mesh (`docs/jambot/client-submesh.md`) and the agent mesh do multi-agent coordination at a *higher* level than a single gateway's sub-agent tree, with an approval bridge. Swarm would sit *underneath* that, not replace it. The interesting question is whether Swarm makes a single tenant agent better at parallel in-session work — not whether it replaces the mesh. It does not.

The one genuine draw: `maxChildrenPerGroup: 50` / `maxTotalPerGroup: 200` are far above our `maxChildrenPerAgent: 4`. If a tenant workload ever needs wide in-session fan-out (bulk page audits, per-URL checks), Swarm is the upstream-supported way to get it. Until then, subagents plus the existing per-tenant caps are the right tool.

## Cost caution

Wide fan-out multiplies token spend per turn, and our subagents run on `zai_fb/glm-5-turbo`. Anything that raises fan-out caps needs the model-discipline question answered first (haiku/triage vs sonnet/composition vs opus/heavy) — a 50-child group on the wrong tier is an expensive way to learn that.
