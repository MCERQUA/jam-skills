---
anchor: 11
slug: plugins-entries-vs-skills-entries
status: confirmed
introduced: v2026.4.20 (precedence) + v2026.4.27 (skills strict gating) + v2026.5.2 (doctor migration)
changelog_lines: [2388, 837, 70]
upstream_pages:
  - https://docs.openclaw.ai/plugins/architecture.md
  - https://docs.openclaw.ai/tools/skills.md
  - https://docs.openclaw.ai/tools/skills-config.md
old_behavior: "single enable knob assumed to control everything"
new_behavior: "dual-axis: plugins.entries.* (runtime) and skills.entries.* (prompt-level) are independent"
skill_files_affected:
  - "references/plugins-system.md (top)"
  - "references/memory-system.md:420-424"
  - "references/skills-system.md"
---

# Anchor #11 — `plugins.entries` vs `skills.entries` semantics

## The dual-axis

A bundled component like `memory-core` registers BOTH a plugin entry AND a skill entry:

| Axis | What it controls | Disable knob |
|------|------------------|--------------|
| Runtime / capabilities | Tool surfaces, hooks, gateway-side execution | `plugins.entries.<id>.enabled: false` |
| Prompt / agent-facing | Skills shown to the agent in TOOLS.md, instructions | `skills.entries.<id>.enabled: false` |

Setting only one disables only that axis.

## The single-knob kill switch (memory only)

For memory specifically, `plugins.slots.memory: "none"` disables the entire memory subsystem (anchor #2). This is the recommended kill switch for memory.

## Production reproduction

When Mike tried to disable `memory-core` via `plugins.entries.memory-core.enabled: false`, the hot-reload log showed `skills.entries.memory-core` because the bundled `memory-core` registers both. To fully disable required setting BOTH keys, OR `plugins.slots.memory: "none"`.

## Changelog evidence

- v4.20 line 2388: "keep only the highest-precedence manifest when distinct discovered plugins share an id"
- v4.27 line 837: `skills.entries.coding-agent.enabled` strictly required before bundled coding-agent skill exposes
- v5.2 line 70: doctor migrates stale plugin manifests

## Fix instruction

`annotations/plugins__architecture.md` and `annotations/concepts__memory.md`: clarify the dual-axis. Memory section specifically: `plugins.slots.memory: "none"` is the only single-knob disable.
