---
name: session-monitor-agent
description: session-monitor@mesh nightly reflection author — cross-tenant analysis, latency anomaly detection, error pattern correlation, attribution-drift surfacing. Use when working on the agent's analysis logic, reflection format, or its participation in the nightly meeting.
---

# session-monitor@mesh — skill

The only mesh agent with visibility across **every tenant's** chat session events. It reads what no individual tenant can see, posts an analysis reflection to the nightly chatroom, and surfaces patterns + aha-moments + escalations.

## Files

| Path | Purpose |
|---|---|
| `/home/mike/MIKE-AI/scripts/session-monitor-agent/post-reflection.py` | Main script — read report + baseline, build reflection, post via mesh-chat |
| `/mnt/agent-mesh/mesh/REGISTRY/session-monitor.md` | Mesh agent registry entry |
| `/mnt/agent-mesh/agents/session-monitor/` | Agent home (inbox, sent, snapshots, transcripts) |
| `/mnt/system/monitoring/reports/<date>.json` | Input — daily session report (structured) |
| `/mnt/system/monitoring/reports/<date>-summary.md` | Input — same data, markdown form |

## Cron

```cron
# 22:45 EDT (02:45 UTC) — AFTER Group A+B tenants, BEFORE host kickoff
45 2 * * * /usr/bin/python3 /home/mike/MIKE-AI/scripts/session-monitor-agent/post-reflection.py
```

Pre-requisite cron (separate entry): the daily report MUST run before 22:45 EDT. Current time: `0 2 * * *` UTC = 22:00 EDT prev day. If report cron drifts late, agent reads stale data.

## What it produces (reflection structure)

**Part 1 — Whole-fleet patterns:**
- Cross-tenant error clusters (same error type on ≥2 tenants today)
- Latency regressions vs 7-day baseline (>1.5× median = called out)
- Container restart anomalies (>1 restart in 24h)
- Correlated crash events (≥3 tenants crashing in same 10-min window — shared root cause)

**Part 2 — Per-tenant drilldowns:**
- Tenants with actual user activity (cross-check vs each tenant's own reflection — attribution drift signal)
- Anomaly summary per flagged tenant (restarts + error codes + max LLM ms)

**Part 3 — Aha-moment candidates:**
- "Shared trigger across tenants" insights
- "Desktop blind to voice" attribution gaps with concrete suggestion
- "Latency cliff on tenant X" with hypothesis

**Part 4 — ESCALATE to host:**
- Correlated crashes
- Severe latency regressions (≥3× baseline)
- Fleet stability degradation (≥3 tenants with multiple restarts)

**Part 5 — Process feedback:**
- Self-improvement candidates (e.g. LLM-augmented synthesis as v2)
- Notes for next iteration

## Manual operations

```bash
# Dry-run (print without posting)
python3 /home/mike/MIKE-AI/scripts/session-monitor-agent/post-reflection.py --dry-run

# Save to sent/ but don't post to chatroom
python3 /home/mike/MIKE-AI/scripts/session-monitor-agent/post-reflection.py --print-only

# Post for real (what cron does)
python3 /home/mike/MIKE-AI/scripts/session-monitor-agent/post-reflection.py
```

## Tunables (constants at top of post-reflection.py)

| Constant | Default | Effect |
|---|---|---|
| `BASELINE_DAYS` | 7 | How many prior days to median against |
| `LATENCY_REGRESSION_RATIO` | 1.5 | Today's max_llm_ms ÷ 7-day median — above this = anomaly |
| `MAX_RESTARTS_NORMAL` | 1 | Restarts above this = anomaly |
| `MIN_ERRORS_FOR_CLUSTER` | 2 | Same error type across ≥N tenants = cluster |

## v2 candidates (deferred)

- **LLM-augmented "aha" section** — feed today's report + last 3 days of peer reflections into Z.AI Claude with a synthesis prompt for narrative pattern detection beyond what pure stats can find.
- **Adoption-tracking** — read yesterday's `group-distilled.md` to see whether items the agent ESCALATEd got adopted; auto-promote unshipped-3-nights items to escalation.
- **Cross-post desktop hints** — before each `<tenant>-desktop@mesh` reflection fires, write a note to that desktop's inbox listing today's voice activity, so desktop agents don't blindly report "users served: 0" when their voice tenant had traffic.
- **Cost-to-serve attribution** — pull token usage per tenant from `usage-costs.json` and surface "<tenant> served N users at $X" for ROI visibility.

## Why this agent exists

Origin: 2026-05-15. Mike noted the nightly meetings weren't producing improvements because the system was "ducktaped together" — agents reflected on what they personally knew, but nobody saw the cross-tenant picture. The data has been collected since 2026-03-13; this agent is the first thing that reads it for the mesh.
