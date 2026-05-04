---
anchor: 7
slug: meta-lastTouchedVersion-migration
status: confirmed
introduced: v2026.5.2
changelog_line: 70
upstream_pages:
  - https://docs.openclaw.ai/gateway/configuration.md
  - https://docs.openclaw.ai/cli/doctor.md
  - https://docs.openclaw.ai/install/updating.md
old_behavior: "operator manually applied config migrations between releases"
new_behavior: "auto-managed meta.lastTouchedVersion drives one-time 5.2 migrations on first start"
skill_files_affected:
  - "references/gateway-configuration.md (top, before Hot Reload)"
  - "references/troubleshooting.md"
---

# Anchor #7 — `meta.lastTouchedVersion` doctor migration

## What changed

v5.2 line 70: "run a one-time 2026.5.2 configured-plugin install repair based on `meta.lastTouchedVersion`"

The 5.2 first-run migration auto-runs:
- Adds `zai` to `plugins.allow` when `zai` is referenced anywhere in config
- Updates `channelConfigs` for stale plugin manifests (anchor #12 territory)
- Other fix-ups encoded in 5.2 source

After running, gateway writes `meta.lastTouchedVersion: "2026.5.2"` to config to skip on subsequent starts.

## JamBot impact

When upgrading any client container to 5.2, the first gateway start will mutate `openclaw.json` automatically. This is good (keeps configs current), but means:
- Don't blow away the file with template re-copy after first 5.2 start
- `git diff` on `/mnt/clients/<user>/openclaw/openclaw.json` will show the auto-edits

## Verification

```bash
docker exec openclaw-<user> sh -c 'cat ~/.openclaw/openclaw.json' | jq '.meta.lastTouchedVersion'
```

## Fix instruction

`annotations/gateway__configuration.md`: add `## First-Run on 5.2 (meta.lastTouchedVersion)` section explaining the auto-migration. Also reference in `playbooks/upgrade-tenant-to-5-2.md` (TODO).
