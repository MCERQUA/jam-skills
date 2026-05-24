---
upstream: https://docs.openclaw.ai/tools/skills.md
relevance: jambot-critical
last-verified: 2026-05-23
audit_anchors: [18]
related_pages: [tools__skills, plugins__architecture, security__prompt-injection]
---

# Skill Vetter — JamBot annotation (mandatory tenant tool)

## What it is

**Skill Vetter** (`clawhub.ai/spclaudehome/skill-vetter`) is an agent-driven scanner that reviews ClawHub skill source code before install. Surfaced in r/openclaw 1riiglv (OpenClaw 102 community guide).

## Why JamBot ships this with every tenant

The ClawHavoc campaign (anchor-18) caught 1,467 malicious ClawHub skills. The flagship case — `capability-evolver`, #1 on ClawHub with 35k installs — was exfiltrating data to Chinese cloud storage before being removed. The Skill Vetter scans for these patterns BEFORE the malicious code runs in a tenant container.

JamBot's multi-tenant deployment makes any compromised skill catastrophic — single bad skill mounted into `/mnt/system/base/skills/` reaches every tenant simultaneously.

## Install (per new tenant)

```bash
# Inside the tenant container
openclaw skills install clawhub.ai/spclaudehome/skill-vetter

# Verify the vetter itself first (vet the vetter)
openclaw skills inspect clawhub.ai/spclaudehome/skill-vetter
```

## Skill-install workflow with Vetter

```bash
# Step 1 — get the skill manifest WITHOUT installing
openclaw skills fetch clawhub.ai/<author>/<skill> --dry-run

# Step 2 — run Vetter on the manifest
openclaw delegate skill-vetter --input "Vet ./fetched/<skill>/"

# Step 3 — if Vetter passes AND human review passes, install
openclaw skills install clawhub.ai/<author>/<skill>

# Step 4 — monitor for 3 days (cost + egress)
tail -f ~/.openclaw/logs/skills-*.log
```

## Manual review checklist (Vetter doesn't catch everything)

- `scripts/` folder: reject unless explicitly justified and reviewed
- Network calls: must be to documented public APIs, not "telemetry.<random>.com"
- File reads: must stay within the skill's declared scope
- `eval`, `Function`, dynamic `require`: rejected unless bounded inputs are obvious

## Skill blocklist (as of 2026-05-23)

See `overrides/skill-allowlist.md` for the full JamBot policy. Headline blocks:

- `capability-evolver` (post-incident; copycats may exist under similar names)
- `self-improving-agent` (132 stars, unaudited per community)
- Any skill whose only contributor account is < 30 days old

## Related JamBot files

- `audit-anchors/anchor-18-clawhavoc-supply-chain.md`
- `overrides/skill-allowlist.md` (new — JamBot-wide policy)
- `playbooks/skill-install-vetting.md` (new — full workflow)
- `annotations/security__prompt-injection.md` (DESCRIPTION.md injection vector)
