---
upstream: https://docs.openclaw.ai/plugins/codex-computer-use.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: []
related_pages: [plugins__codex-harness, tools__browser]
---

# Codex Computer Use — JamBot annotation

## What docs say (TL;DR)

Codex-native MCP plugin for local desktop control through OpenClaw's Codex harness. OpenClaw doesn't execute desktop actions directly — Codex owns native MCP tool calls during Codex-mode turns. Marketplace-driven install (none / `marketplaceSource` / `marketplacePath` / `marketplaceName`). macOS-specific; requires Accessibility + Screen Recording permissions. Alternative: direct `cua-driver` MCP server via OpenClaw registry.

## JamBot relevance — Cycle 6 ovui-desktop overlap

JamBot's Cycle 6 ovui-desktop work is the **same surface** but JamBot-built (not Codex-driven). 8-tool plugin for KDE/desktop control via CDP. The session log `session-2026-04-19-cycle6-ovui-core-shipped.md` covers this.

**Decision point**: should we migrate ovui-desktop to use Codex Computer Use as the substrate?

| Option | Pros | Cons |
|--------|------|------|
| Keep ovui-desktop (current) | Already shipped; Linux/KDE-tuned; CDP-based | More to maintain; Codex-specific MCP wiring not used |
| Migrate to Codex Computer Use | Codex-native; bigger ecosystem | macOS-specific upstream; would need Linux port; loses CDP advantage |

Probably **keep ovui-desktop** for now — JamBot is Linux-native, Codex Computer Use is macOS-specific.

## Config

```json5
{
  plugins: {
    entries: {
      codex: {
        config: {
          computerUse: {
            enabled: true,            // intentionally fails closed
            autoInstall: true,         // automatic plugin availability
            pluginName: "computer-use",
            mcpServerName: "computer-use",
            marketplaceDiscoveryTimeoutMs: 60000   // configurable for slower marketplace
          }
        }
      }
    }
  }
}
```

## Marketplace flow

| Source option | Effect |
|---------------|--------|
| (none) | Auto-discover from defaults |
| `marketplaceSource` | Explicit URL/path |
| `marketplacePath` | Local filesystem path |
| `marketplaceName` | Named registry entry |

Default preference order: `openai-bundled` → `openai-curated` → `local`. Bundled macOS marketplace at `/Applications/Codex.app/Contents/Resources/plugins/openai-bundled`.

## Status reasons (9 possible)

`/codex computer-use status` returns one of:
- `disabled`
- `marketplace_missing`
- `plugin_not_installed`
- `plugin_disabled`
- `remote_install_unsupported`
- `mcp_missing`
- `ready`
- `check_failed`
- `auto_install_blocked`

## Gotchas

- Turn-start auto-install **refuses new `marketplaceSource` values** — use explicit `/codex computer-use install` command first
- Codex app-server doesn't support remote `plugin/install` — installs need local marketplace access
- "Native hook relay unavailable" error → fresh session via `/new` or `/reset`, OR gateway restart
- After changing `agentRuntime` or Computer Use config: `/new` or `/reset` to pick up

## OpenClaw intentionally fails closed

When `computerUse.enabled: true` but the plugin/MCP isn't ready, OpenClaw fails closed (no silent fallback to non-desktop tools). Good security posture; bad UX if you expect graceful degradation.

## Related JamBot files

- `session-2026-04-19-cycle6-ovui-core-shipped.md` (memory) — current ovui-desktop state
- `session-2026-04-19-cycle6-phase4-widget-chat-sync.md` (memory)
- `feedback_agent_empowerment_mandate.md` (memory) — Phase 6 grounding (UI-TARS-1.5-7B is the target; computer use is one path)
- `/jambot-openclaw` skill — container architecture
