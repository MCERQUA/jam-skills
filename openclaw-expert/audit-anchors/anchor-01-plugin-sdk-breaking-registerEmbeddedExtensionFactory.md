---
anchor: 1
slug: plugin-sdk-breaking-registerEmbeddedExtensionFactory
status: confirmed
introduced: v2026.4.24
changelog_line: 1759
upstream_pages:
  - https://docs.openclaw.ai/plugins/architecture.md
  - https://docs.openclaw.ai/plugins/sdk-overview.md
  - https://docs.openclaw.ai/plugins/sdk-runtime.md
old_behavior: "api.registerEmbeddedExtensionFactory(...) — Pi-only compatibility path"
new_behavior: "api.registerAgentToolResultMiddleware(...) + contracts.agentToolResultMiddleware declaring targeted harnesses"
skill_files_affected:
  - "references/plugins-system.md (no current SDK depth — add Breaking Changes section)"
---

# Anchor #1 — Plugin SDK breaking: `registerEmbeddedExtensionFactory` removed

## What changed

v2026.4.24 removed the Pi-only `api.registerEmbeddedExtensionFactory(...)` compatibility path. Bundled tool-result rewrites must now use `api.registerAgentToolResultMiddleware(...)` with `contracts.agentToolResultMiddleware` declaring the targeted harnesses, so transforms run consistently across Pi and Codex app-server dynamic tools.

## Migration map (from audit doc §5)

| Old API | Replacement | Notes |
|---------|-------------|-------|
| `registerEmbeddedExtensionFactory(...)` | `registerAgentToolResultMiddleware(...)` + `contracts.agentToolResultMiddleware` | runs across Pi and Codex |
| `providerAuthEnvVars` | `setup.providers[].envVars` | v4.24 line 1796 |
| `command-auth` | `command-status` (compat alias retained) | v4.9 line 2904 |
| `test/helpers/*` repo bridges | `openclaw/plugin-sdk/*-test-contracts` subpaths | v4.27 line 790 |
| Implicit startup sidecar load | `activation.onStartup` explicit declaration | v4.27 line 781 |
| `channel-config-schema-legacy` | bundled-channel schema SDK surface | v4.27 |

## New SDK surfaces (v4.27–v4.29)

- `api.runtime.state.openKeyedStore(...)` — restart-safe SQLite-backed plugin state with TTL/eviction (v4.29 line 419)
- `api.registerHook("before_agent_finalize", ...)` — v4.25 line 1377
- `api.registerHook("model_call_started" | "model_call_ended", ...)` — v4.25 line 1405
- `api.registerHook("session_state" | "next_turn_context" | "trusted_tool_policy" | "ui_descriptors" | "events" | "scheduler_cleanup" | "run_scoped_plugin_context")` — v4.27 line 801
- `setup.requiresRuntime: false` — descriptor-only setup contract, v4.24 line 1794
- `modelCatalog.aliases` / `modelCatalog.suppressions` — declarative model rows manifest contract, v4.24/4.27

## JamBot impact

JamBot ships zero in-house plugins today, but Cycle 6 ovui-desktop is a plugin (8 tools). If any internal plugin still uses the legacy API, the gateway will boot-fail on 5.2.

## Fix instruction

Add `Breaking Changes — v2026.4.24+` section near top of `annotations/plugins__architecture.md` with the migration map above and a `contracts.agentToolResultMiddleware` example.
