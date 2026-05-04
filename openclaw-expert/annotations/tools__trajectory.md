---
upstream: https://docs.openclaw.ai/tools/trajectory.md
relevance: high
last-verified: 2026-05-04
audit_anchors: []
related_pages: [tools__index, concepts__session]
---

# Trajectory bundles — JamBot annotation

## What docs say (TL;DR)

Per-session "flight recorder" capturing structured timeline of agent runs for debugging/support. Owner-only `/export-trajectory` (alias `/trajectory`) creates redacted bundle in `~/.openclaw/trajectory-exports/`. JSON Lines format with `traceSchema: "openclaw-trajectory"`, `schemaVersion: 1`. Captures runtime events (start/end/metadata/compiled context/prompts/model steps/fallbacks/completion/artifacts), full transcript, tool calls/results, compactions, model changes, labels.

## Bundle layout

```
.openclaw/trajectory-exports/openclaw-trajectory-<session>-<timestamp>/
├── manifest.json
├── events.jsonl
├── session-branch.json
├── metadata.json
├── artifacts.json
├── prompts.json
├── system-prompt.txt
└── tools.json
```

Plus runtime sidecars beside session file:
- `<session>.trajectory.jsonl`
- `<session>.trajectory-path.json` (pointer)

## Limits

- Runtime/session files: 50 MiB
- Runtime events: 200,000
- Total events: 250,000
- Per-line: 256 KiB

## Knobs

| Key | Purpose |
|-----|---------|
| `OPENCLAW_TRAJECTORY=0` (env) | Disable capture entirely |
| `OPENCLAW_TRAJECTORY_DIR` (env) | Custom storage location for sidecars |

## Redaction

Auto-masks credentials, secrets, images, workspace paths, home directories. Group chat behavior: approval prompts and results sent privately to channel owner instead of shared room.

## CLI

```bash
openclaw sessions export-trajectory --session-key "<key>"
```

Slash command: `/export-trajectory` (or `/trajectory` alias). Each invocation requires exec approval (no allow-all).

## JamBot relevance — agent empowerment plan

Per memory `feedback_agent_empowerment_mandate` (v3): bBoN (Best-of-N) trajectory format is referenced for cross-agent rollouts. OpenClaw's trajectory format may be the substrate or interoperable with it. Phase 8 of the empowerment plan needs trajectory capture for divergence-kill / budget enforcement.

**Action item:** when implementing the empowerment plan's Phase 6.5 control plane, evaluate whether OpenClaw trajectory bundles can serve as the trajectory transport (via MinIO+NATS) instead of building a custom one.

## Related JamBot files

- `feedback_agent_empowerment_mandate.md` (memory) — Phase 8 bBoN
- `/jambot-session-monitor` skill — separate session monitoring layer (may complement trajectory)
- `playbooks/debug-empty-final.md` — debug flow that could benefit from trajectory export
