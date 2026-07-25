---
anchor: 26
slug: agent-cron-scoping-and-protocol-v4
status: confirmed
introduced: v2026.5.19 (protocol v4) / v2026.7.1 (cron scoping)
changelog_line: "CHANGELOG.md 2026.7.1 — 'Agents using OpenClaw's cron tools are now limited to their own scheduled jobs and session targets, while operator-managed cron remains unchanged and mixed-version setups fail closed with an `openclaw gateway restart` instruction. (#96883)' | 2026.5.19 — 'Gateway/protocol: restore Gateway WS protocol v4...' / 'Gateway protocol: require v4 clients and stream explicit chat deltaText/replace frames so SDK clients can consume assistant updates without local diffing. (#80725)'"
upstream_pages:
  - https://docs.openclaw.ai/gateway/protocol
  - https://docs.openclaw.ai/automation/cron-jobs
  - https://docs.openclaw.ai/cli/cron
old_behavior: "Agent-invoked cron tools could see and target scheduled jobs and sessions beyond their own agent. Gateway WS clients could speak older protocol versions and diff assistant updates locally."
new_behavior: "7.1 scopes agent cron tools to the agent's own jobs and session targets; operator-managed cron is unchanged; MIXED-VERSION setups FAIL CLOSED with an `openclaw gateway restart` instruction. 5.19 requires WS protocol v4 clients and streams explicit `deltaText`/`replace` frames."
skill_files_affected:
  - overrides/voice-flow-quirks.md
  - playbooks/cron-as-sub-agent.md
  - playbooks/upgrade-5.7-to-7.x.md
sources:
  - https://github.com/openclaw/openclaw/pull/96883
  - https://github.com/openclaw/openclaw/pull/80725
---

# Anchor #26 — Agent cron scoping (7.1) + Gateway WS protocol v4 required (5.19)

Two separate changes, filed together because both bite the *same* JamBot surface: the things that talk to a tenant gateway from outside the agent's own turn.

## A. Agent cron tools are scoped to the agent (v2026.7.1)

Agents using OpenClaw's cron tools can now only see and target **their own** scheduled jobs and session targets. Operator-managed cron (jobs created from the CLI/config rather than by an agent) is unchanged.

**The clause that matters operationally:** *"mixed-version setups fail closed with an `openclaw gateway restart` instruction."* During a partial fleet roll — some tenants on the new image, some still on 5.7 — cron tooling on the straddling tenants fails closed rather than degrading. This is a correct-but-loud behavior that will look like "cron broke everywhere" if the roll is done tenant-by-tenant over hours.

**JamBot exposure:** the nightly tenant reflections (Group A 02:30 / Group B 02:32–02:53 UTC) fire from *inside* the openclaw containers via openclaw cron. A fleet roll that straddles a reflection window can silently produce a night with missing peer reflections — the exact failure the `pb-20260718-002` playbook lesson says to treat as a dead-man signal, not a glitch. **Roll the fleet outside 02:00–04:00 UTC**, or expect and pre-announce the gap.

## B. Gateway WS protocol v4 is required (v2026.5.19)

The gateway now requires v4 clients and streams explicit `deltaText`/`replace` frames instead of expecting clients to diff assistant updates locally (#80725). Protocol-mismatch errors were also improved (5.19) to name which side is stale.

**JamBot exposure:** OpenVoiceUI connects to `ws://openclaw:18789` from a separate container. If the OVU-side WS client hardcodes an older protocol version or does local diffing of assistant text, it must be checked against v4 *before* the openclaw image is bumped — the two containers version independently, and OVU is not rebuilt by `bump-openclaw-version.sh`.

Check before upgrading:

```bash
grep -rn "protocol" /mnt/system/base/OpenVoiceUI/services/ /mnt/system/base/OpenVoiceUI/server.py 2>/dev/null | grep -i -E "version|v[0-9]"
sg docker -c "docker logs --tail 100 openclaw-<tenant>" | grep -i "protocol"
```

A protocol-mismatch on this path presents as the voice UI connecting and then producing nothing — which historically gets misdiagnosed as an empty-final / provider problem (see `playbooks/debug-empty-final.md`). Rule out the protocol version first on any post-upgrade "the agent went quiet" report.
