---
upstream: https://docs.openclaw.ai/help/troubleshooting.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: [3, 7, 8]
related_pages: [help__faq, help__debugging, gateway__doctor, gateway__troubleshooting]
---

# Troubleshooting — JamBot annotation

## What docs say (TL;DR)

Per-channel and per-component troubleshooting ladders. `openclaw doctor`, `openclaw status`, `openclaw gateway status`, `openclaw logs --follow`, `openclaw channels status --probe`. Error codes table.

## Triage ladder (verbatim, run in order)

```bash
openclaw status
openclaw gateway status
openclaw doctor                          # since v5.2 also runs meta.lastTouchedVersion migration (anchor #7)
openclaw gateway restart --force --wait 60s   # NEW v5.2
openclaw logs --follow
openclaw channels status --probe
openclaw plugins registry --refresh      # NEW v4.25
openclaw plugins deps                    # NEW v4.27
openclaw sandbox explain                 # debug sandbox/tool-policy/elevated layering
```

## v5.2-era new error patterns

### Anchor #3 — strict tool-allowlist hard-error
```
No callable tools remain after resolving explicit tool allowlist
```
Fix: use `alsoAllow` for plugin tools; check `agents.list[N].tools.allow` against `openclaw plugins list`.

### Anchor #7 — meta.lastTouchedVersion auto-migration
On first 5.2 start, doctor migrates config (auto-adds zai to `plugins.allow` when referenced; updates `channelConfigs`). `git diff` will show legitimate auto-edits — don't blow away.

### Anchor #8 — Bonjour disabled by default for Compose
Pre-v4.25 mDNS probe-loop pegged CPU. Default-off prevents this. To re-enable on host/macvlan: `OPENCLAW_DISABLE_BONJOUR=0`.

## Errors that were real but are NOW FIXED (remove from ladder)

| Error | Fixed in | Changelog line |
|-------|----------|----------------|
| "Agent listener invoked outside active run" gateway crash | v4.10 | line 2840 |
| Tool X not found loop until embedded-run timeout | v4.15 (unknown-tool guard on by default) | line 2479 |
| DM pairing-store entries authorize Matrix room control | v4.15 (patched) | line 2456 |

## Errors STILL in play (verbatim from old skill, still valid)

| Error | Fix |
|-------|-----|
| `Gateway start blocked: set gateway.mode=local` | `openclaw config set gateway.mode local` |
| `refusing to bind gateway ... without auth` | Set `gateway.auth.token` OR (preferred for Docker) `gateway.auth.mode = "trusted-proxy"` + `trustedProxies` |
| `EADDRINUSE` / port conflict | `openclaw gateway --force` |
| `NOT_PAIRED` / `device identity required` | Set `dangerouslyDisableDeviceAuth: true` (JamBot non-negotiable) |
| `unauthorized` during connect | Token mismatch — check `launchctl getenv OPENCLAW_GATEWAY_TOKEN` |
| Z.AI returns thinking-only blocks | Set `thinkingDefault: "off"` |
| Empty `chat.final` from MiniMax | Run `playbooks/debug-empty-final.md` cascade |
| WhatsApp disconnects | `openclaw channels logout && openclaw channels login --verbose` |
| `NODE_BACKGROUND_UNAVAILABLE` | Bring node app to foreground |
| `SYSTEM_RUN_DENIED` | `openclaw approvals get --node <id>` → approve or add to allowlist |

## v4.x `Restart=always` + sysexits 78 interaction

v4.29 added `Restart=always` / `RestartPreventExitStatus=78` to systemd/launchd configs. Sysexit 78 = configuration error; gateway exits cleanly without restart loop. JamBot Docker containers don't use systemd, but if a host gateway is running outside Docker, this matters.

## JamBot-specific triage additions

| Symptom | Try first |
|---------|-----------|
| Voice agent says "NO" or "YES" with nothing else | Bare-token leak. Branch `fix/eradicate-bare-no-yes-responses` deployed live; pending image rebuild. See memory `bare-no-response-fix`. |
| Multi-turn context loss on GLM client | Verify gateway ≥ v5.2 (anchor #9 — GLM consecutive-turn fix) |
| Agent forgets memory entries past first ~150 lines | MEMORY.md cap (anchor #5) — trim file |
| Tool calls truncate at ~15s | Embedded run timeout (anchor #4) — see annotations/concepts__agent.md |
| Container CPU pegged on idle | Pre-v4.25 Bonjour loop (anchor #8) or pre-v4.10 listener crash — verify version |
| Memory sub-agent runs every reply (slow) | Anchor #2 — kill via `plugins.slots.memory: "none"` if confirmed not needed |
| Old config keys silently ignored | Doctor migrations (anchor #7, #15) — run `openclaw doctor --fix` |

## Related JamBot files

- `audit-anchors/anchor-{3,4,5,7,8,9,11,15}.md`
- `playbooks/debug-empty-final.md`
- `annotations/tools__exec.md` — anchor #13 YOLO defaults
- `/jambot-session-monitor` skill — secondary monitoring layer
- `bare-no-response-fix.md` (memory)
