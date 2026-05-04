---
anchor: 3
slug: strict-tool-allowlist-hard-error
status: confirmed
introduced: v2026.5.2 (trend builds from 4.27)
changelog_lines: [837, 56]
upstream_pages:
  - https://docs.openclaw.ai/tools/index.md
  - https://docs.openclaw.ai/gateway/configuration.md
old_behavior: "tools.allow referencing missing-plugin tool silently dropped"
new_behavior: "v5.2 hard-errors at config load: 'No callable tools remain after resolving explicit tool allowlist'"
skill_files_affected:
  - "references/tools-and-exec.md:60-65 (alsoAllow section)"
---

# Anchor #3 — Strict tool-allowlist hard-error in v5.2

## What changed

- v4.27 line 837: `skills.entries.coding-agent.enabled` now strictly required before bundled coding-agent skill exposes
- v5.2 line 56: "validate configured web-search providers plus statically suppressed model/provider pairs against the active plugin set at config load"

The trend: validation now happens at config load, not at first use. The error string Mike hit in production:

```
No callable tools remain after resolving explicit tool allowlist
```

## Reproduction

`agents.list[N].tools.allow: ["browser", ...]` where `@openclaw/browser` is not enabled → gateway boot fails on 5.2.

## Workaround

Use `alsoAllow` for plugin tools — that surface tolerates plugin absence and won't force the rest of your config into restrictive mode.

## JamBot impact

Affects every client whose openclaw.json was hand-tuned with `tools.allow` lists. Audit these before pushing 5.2 to clients.

## Fix instruction

Add explicit warning under `alsoAllow` section in annotations: "Strict 5.2+: `tools.allow` referencing a tool whose plugin is disabled hard-errors at load. Use `alsoAllow` for plugin tools to avoid forcing the rest of your config into restrictive mode."
