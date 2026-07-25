---
anchor: 25
slug: doctor-reworked-in-7.1
status: confirmed
introduced: v2026.7.1
changelog_line: "CHANGELOG.md 2026.7.1 — '`openclaw doctor` and updates now refuse to replace an unreadable `openclaw.json`, preserving existing Gateway, agent, channel, and plugin settings instead of breaking the installation. (#96469)' / '`doctor --fix` now shows the exact `gateway.bind=loopback` or `gateway.nodes.denyCommands` change needed for sensitive findings without applying it automatically. (#99776)' / 'Operators can run `openclaw doctor --lint --all` to include every opt-in diagnostic check. (#96471)'"
upstream_pages:
  - https://docs.openclaw.ai/cli/doctor
  - https://docs.openclaw.ai/help/troubleshooting
old_behavior: "Anchor #19: `openclaw doctor --fix` overwrites custom config with defaults; community reported 3+ gateway-crash incidents. JamBot rule: never let agents edit openclaw.json, never put doctor --fix in a pipeline."
new_behavior: "v2026.7.1 substantially reworks doctor. It now REFUSES to replace an unreadable `openclaw.json` (#96469), preserves model tuning across retired-model merges (#96544), preserves separate OAuth accounts per provider (#97541), and SHOWS rather than auto-applies sensitive changes like `gateway.bind=loopback` (#99776). A structured lint system landed: `doctor --lint --only <check>` / `--lint --all` / `--lint --json` across ~15 opt-in checks."
skill_files_affected:
  - audit-anchors/anchor-19-openclaw-doctor-destructive.md (scope correction, do NOT retire)
  - playbooks/safe-config-edit.md
  - overrides/config-edit-policy.md
sources:
  - https://github.com/openclaw/openclaw/pull/96469
  - https://github.com/openclaw/openclaw/pull/99776
  - https://github.com/openclaw/openclaw/pull/96471
  - https://github.com/openclaw/openclaw/pull/99249
---

# Anchor #25 — `openclaw doctor` was reworked in 7.1; anchor #19 is now version-scoped

## Read this WITH anchor #19, not instead of it

Anchor #19 says doctor is destructive and agents must never hand-edit `openclaw.json`. That anchor was written against ≤2026.5.x behavior and community reports from that era. **It is still correct for the version JamBot runs (`2026.5.7`).** But it is no longer a blanket statement about all OpenClaw versions, and stating it as one is now the *wrong* answer to a 7.x question.

| Behavior | ≤2026.6.x (incl. our 5.7 pin) | ≥2026.7.1 |
|---|---|---|
| Unreadable/corrupt `openclaw.json` | doctor may replace it with defaults → custom fields lost | **Refuses to replace it** (#96469); existing gateway/agent/channel/plugin settings preserved |
| Sensitive findings (`gateway.bind`, `nodes.denyCommands`) | `--fix` may apply | **Shows the exact change, does not auto-apply** (#99776) |
| Retired model names merging | tuning/aliases could be lost | preserved, conflicts reported (#96544) |
| Multiple OAuth accounts per provider | could collapse | preserved with account ref + display name (#97541) |
| Diagnostics | one monolithic run | structured `--lint --only <check>`, `--lint --all`, `--lint --json` (#96471, #99249) |

## The JamBot rule does NOT relax

CLAUDE.md's Layer 1A already runs `openclaw doctor --repair --yes` in every openclaw container entrypoint before the gateway starts, and Layer 2 (`jambot-health-monitor.sh` Check 3.5) triggers doctor + restart on "Config invalid" / "Unrecognized key". Those layers were built on the ≤6.x contract. On 7.x they get *safer*, not obsolete — but:

- **Still never hand-edit `openclaw.json`.** `openclaw config set` from inside the container remains the only sanctioned mutation path (CLAUDE.md, non-negotiable).
- **Still snapshot before doctor.** #96469 protects an *unreadable* file. It does not promise to preserve a readable-but-unusual one.

## What 7.1 makes newly possible (adopt during the upgrade)

The lint system is the genuinely useful new capability — non-mutating, structured, scriptable, and a direct fit for our "every system needs monitoring" rule:

```bash
# Non-mutating, machine-readable health signal per tenant
openclaw doctor --lint --json --only core/doctor/gateway-health
openclaw doctor --lint --json --only core/doctor/session-locks
openclaw doctor --lint --all --json          # every opt-in check
```

Known checks surfaced in the 7.1 notes: `core/doctor/gateway-health`, `core/doctor/gateway-daemon`, `core/doctor/session-locks`, plus auth-profile, memory-search, workspace-status, tool-result-cap, blocked-channel, plugin-install, state-storage, systemd-linger, and config-audit credential-residue lints. Verify the exact ids against the running binary (`openclaw doctor --help`) before wiring any of them into `jambot-health-monitor.sh` — do not hardcode ids from this file.

## Flag note (verified on 2026.5.7)

`--fix` and `--repair` are aliases (`--fix` is documented as "alias for --repair"); `--force` is the aggressive one that overwrites custom service config. CLAUDE.md's entrypoint use of `openclaw doctor --repair --yes` is valid on our pin. Re-verify the flag set after any version bump — this anchor is the reason to check rather than assume.
