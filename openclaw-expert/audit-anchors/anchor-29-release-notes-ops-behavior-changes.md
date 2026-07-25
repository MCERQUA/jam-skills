---
anchor: 29
slug: release-notes-ops-behavior-changes
status: confirmed
introduced: v2026.6.11 / v2026.7.1
changelog_line: "releases/2026.7.1 — 'Crash loops now stop for repair': 'A supervised Gateway that repeatedly fails during startup now leaves operators a stable restart and recovery process... Instead of relaunching forever, the control path remains available while automatic channel and provider restarts PAUSE until the underlying problem is fixed.' (a18708c) | releases/2026.6.11 — '#93585 When Linux memory pressure kills a child command or session, systemd-managed OpenClaw gateways now stay running and keep channel connections alive' · '#94915 Gateway readiness checks now turn unhealthy during a restart drain' · '#94445 Scheduled jobs using cloud models now recover from silent, stuck model calls by default' | releases/2026.7.1 — '#81364 ClawHub now checks community plugin and skill releases before download, blocking prohibited releases and requiring explicit acknowledgement for suspicious ones' · '#98704 durable audit history for agent and tool activity'"
upstream_pages:
  - https://docs.openclaw.ai/releases/2026.7.1
  - https://docs.openclaw.ai/releases/2026.6.11
  - https://docs.openclaw.ai/gateway/restart-recovery
  - https://docs.openclaw.ai/gateway/audit
  - https://docs.openclaw.ai/clawhub/security-audits
old_behavior: "A crash-looping gateway relaunches forever. Auto-restart is the operator's job to break. Linux OOM of a child can take the gateway with it. ClawHub downloads are unchecked at the platform level — vetting is entirely the installer's problem (anchor #18). No durable agent/tool audit history."
new_behavior: "6.11/7.1 change operational behavior in ways that INTERACT WITH JAMBOT'S OWN AUTO-HEAL LAYERS: a repeatedly-failing supervised gateway now stops relaunching and pauses automatic channel/provider restarts until repaired; systemd gateways survive OOM of a child; readiness turns unhealthy during restart drain; cloud-model cron jobs self-recover from stuck calls; ClawHub blocks prohibited releases pre-download; a durable filterable/exportable audit history exists."
skill_files_affected:
  - overrides/skill-allowlist.md
  - playbooks/skill-install-vetting.md
  - playbooks/upgrade-5.7-to-7.x.md
  - audit-anchors/anchor-18-clawhavoc-supply-chain.md
sources:
  - https://github.com/openclaw/openclaw/commit/a18708c5c12d93f14eb753b543a6747e8baa8c47
  - https://github.com/openclaw/openclaw/pull/93585
  - https://github.com/openclaw/openclaw/pull/94915
  - https://github.com/openclaw/openclaw/pull/94445
  - https://github.com/openclaw/openclaw/pull/81364
  - https://github.com/openclaw/openclaw/pull/98704
---

# Anchor #29 — Operational behavior changes from the curated release notes (6.11 / 7.1)

Filed 2026-07-25 to close a gap the previous audit **declared but had not closed**: anchors #22–#28 came from grepping the raw changelog for config/auth/storage/cron/protocol/provider terms. That pass explicitly did not cover Control UI, channels, macOS/iOS, or the Codex harness. Reading the *curated* release notes for `2026.6.11` and `2026.7.1` surfaced operational changes the keyword grep missed — because they are described in prose, not in key names.

## A. 🔴 Crash-loop repair PAUSES auto-restart — this fights our Layer 1A/Layer 2

**7.1:** *"A supervised Gateway that repeatedly fails during startup now leaves operators a stable restart and recovery process to inspect and repair. Instead of relaunching forever, the control path remains available while automatic channel and provider restarts pause until the underlying problem is fixed."*

JamBot has two auto-heal layers built for the opposite assumption (CLAUDE.md):

- **Layer 1A** — every openclaw container entrypoint runs `openclaw doctor --repair --yes` before the gateway starts.
- **Layer 2** — `jambot-health-monitor.sh` Check 3.5 greps logs for `Config invalid` / `Unrecognized key` and triggers doctor + restart.

Both are restart-driven. On 7.x the gateway itself decides to *stop* restarting after repeated startup failure. Two consequences to design for during the upgrade:

1. Our health monitor may keep restarting a container that upstream has deliberately parked for inspection — converting a diagnosable "stopped for repair" state back into a churn loop, and destroying the stable control path that was the whole point.
2. Conversely, the gateway pausing channel/provider restarts could read to our monitor as a *healthy* container with dead channels — the `monitors-that-report-unreadable-as-fine` shape.

**Do not port Layer 2's restart reflex forward unexamined.** `gateway/restart-recovery` is the page describing the new contract; read it before the fleet roll.

## B. Linux OOM no longer takes the gateway with it (6.11, #93585)

*"When Linux memory pressure kills a child command or session, systemd-managed OpenClaw gateways now stay running and keep channel connections alive while reporting the child failure."*

Directly relevant: on 2026-07-25 this box hit OOM and swap-thrashing, and many unrelated things went "down" at once. This fix reduces one blast-radius path — but note the qualifier **systemd-managed**. JamBot's tenant gateways run under **Docker**, not systemd, so it is not obvious we inherit this. Verify on a 7.x canary rather than assuming; do not cite this as OOM protection for our fleet until tested.

## C. Readiness turns unhealthy during restart drain (6.11, #94915)

*"Gateway readiness checks now turn unhealthy during a restart drain, preventing traffic managers from sending new work to a Gateway that is temporarily rejecting requests."*

We have a traffic manager in front of every tenant: nginx. Today a draining gateway can still be routed to. Post-upgrade this becomes a real readiness signal worth wiring into health checks — a genuine improvement to claim, not a risk.

## D. Cloud-model cron jobs self-recover from stuck calls (6.11, #94445)

*"Scheduled OpenClaw jobs using cloud models now recover from silent, stuck model calls by default, helping prevent later cron work from backing up while local or self-hosted providers keep their existing timeout behavior."*

Our tenant nightly reflections run on `zai_fb/glm-5-turbo` — a cloud model — from inside openclaw cron. A silent stuck call is exactly the failure that produces a night of missing reflections with no error. This is a fix we actively want. Combined with anchor #26A (agent cron scoping, mixed-version fail-closed), the cron surface changes meaningfully across this upgrade in both directions.

## E. ClawHub now blocks at the platform level (7.1, #81364) — updates anchor #18

*"ClawHub now checks community plugin and skill releases before download, blocking prohibited releases and requiring explicit acknowledgement for suspicious ones while leaving existing installs in place when an update is skipped."*

Anchor #18 (ClawHavoc: 1,467 malicious skills) was written when vetting was **entirely the installer's problem**. There is now a platform-side gate.

**This does not retire our vetting.** `overrides/skill-allowlist.md` and `playbooks/skill-install-vetting.md` stand, for a specific reason: a shared skill in `/mnt/system/base/skills/` is mounted into **every tenant simultaneously**, so our blast radius is larger than the single-operator case the platform gate is sized for. Treat the ClawHub check as defense-in-depth that reduces the odds, not as the boundary. The right update is to note that a "suspicious release requiring acknowledgement" is now an explicit, loud signal — and that acknowledging one on our fleet is a decision, never a click-through.

## F. Durable audit history (7.1, #98704)

*"Authorized operators now have a durable audit history for agent and tool activity, with filters, stable paging, bounded JSON export, configurable recording, and automatic retention limits."* (`gateway/audit`)

Worth adopting post-upgrade. It is the per-tenant answer to "what did this agent actually do," which `concepts/multi-user` explicitly says the transcript cannot provide (turn attribution is best-effort). Pairs with `openclaw security audit` (see `annotations/gateway__security__exposure-runbook.md`) as the second half of a real monitoring story for the tenant layer.

## What this anchor does NOT cover

Read honestly: the curated notes for 6.11 and 7.1 were read at the **highlight + section level**, plus targeted sections on credentials, skills/plugins, crash loops, and scheduled work. The intermediate releases (5.20 → 6.10, and 6.33) have **no curated release-notes page in the catalog** and were covered only by the earlier keyword grep. Control UI got a major overhaul in 7.1 that is described but not audited here against our per-tenant Control UI exposure — that remains open.
