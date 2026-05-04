---
anchor: 8
slug: bonjour-disabled-by-default
status: confirmed
introduced: v2026.4.24 (bundled) + v2026.4.25 (default disabled)
changelog_lines: [1810, 1565, 1567, 483, 1137]
upstream_pages:
  - https://docs.openclaw.ai/gateway/bonjour.md
  - https://docs.openclaw.ai/install/docker.md
old_behavior: "Bonjour/mDNS advertising on by default"
new_behavior: "disabled for bundled Compose gateways on bridge networking"
skill_files_affected:
  - "references/gateway-advanced.md"
  - "references/install-hetzner.md"
  - "references/troubleshooting.md"
---

# Anchor #8 — Bonjour/mDNS disabled by default for Docker Compose

## What changed

- v4.24 line 1810: Bonjour moved into bundled plugin (`@homebridge/ciao`)
- v4.25 line 1565: "disable Bonjour/mDNS advertising by default for bundled Compose gateways on bridge networking, while keeping host/macvlan opt-in with `OPENCLAW_DISABLE_BONJOUR=0`. Fixes #71879."
- v4.25 line 1567: "stop ciao mDNS watchdog failures from looping forever"
- v4.29 line 483: "cap flapping advertiser restarts in a sliding window"
- v4.26 line 1137: "default mDNS advertisements to the system hostname when it is DNS-safe"

## Why it matters for JamBot

JamBot runs Compose gateways on bridge networking — exactly the case the v4.25 default targets. Pre-fix, the openclaw container hit an mDNS probe loop that pegged CPU. Post-fix, default-off prevents this without needing manual config.

## To re-enable (host/macvlan only)

```bash
# In the openclaw container
OPENCLAW_DISABLE_BONJOUR=0
```

Or in `openclaw.json`:
```json5
{ gateway: { bonjour: { enabled: true } } }
```

## Fix instruction

`annotations/gateway__bonjour.md` + `annotations/install__docker.md`: document the flip + the env var override. Cross-reference from `overrides/docker-deployment.md`.
