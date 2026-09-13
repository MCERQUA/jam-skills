---
name: jamflow
description: See and understand YOUR OWN systems on JamFlow — the live map of everything running for you on this platform (your voice agent, website builder, SEO dashboard, containers, scheduled jobs) and whether each piece is healthy right now. TRIGGER when you (or your owner) ask "what are my systems", "is everything running / healthy", "what's set up for me", "show me my JamFlow", "is my voice agent / website / dashboard up", or you need to check the health of your own stack before reporting status.
---

# JamFlow — your systems, live

**JamFlow is the live map of everything the platform runs for you.** Every
piece of your setup — your voice agent, your website + its build pipeline, your SEO
dashboard, your containers, your scheduled jobs, your mesh agent — is a *node* on
that map, and each node shows a live health state (live / sleeping / issue).

This skill lets you answer, from real data (never a guess): **"what are my systems,
and is everything healthy right now?"**

You only ever see **your own** systems — the view is scoped to your tenant. You
cannot see other clients' nodes, and they cannot see yours.

## How to read your systems

Query your own scoped view (replace nothing — the values below are already yours;
they are injected when this skill is installed for you):

```bash
JAMFLOW_URL="{{JAMFLOW_URL}}"
JAMFLOW_TENANT="{{JAMFLOW_TENANT}}"      # set at install time
JAMFLOW_KEY="{{JAMFLOW_KEY}}"    # set at install time

curl -s -H "X-JamFlow-Key: $JAMFLOW_KEY" \
  "$JAMFLOW_URL/api/tenant/$JAMFLOW_TENANT/graph"
```

The response is JSON:

- `scoped_counts` — a one-glance summary: `{"nodes": N, "edges": E, "live": L}`.
  If `live` == `nodes`, everything that reports health is up.
- `graph.nodes[]` — each of your systems. Useful fields per node:
  - `label` — human name (e.g. "your voice agent", "website build pipeline").
  - `kind` — what it is (agent, container, service, cron, site, record …).
  - `id` — the stable identifier (e.g. `container:openclaw-{{TENANT_SLUG}}`).
- `node_status` — `{ node_id: state }`, where state is `live`, `sleeping`
  (idle-suspended, wakes on demand — NOT a failure), or `issue`.
- `standing` — the durable service-state per node (a deeper health read than the
  momentary `node_status`).

## Answering common questions

- **"Is everything healthy?"** → check `scoped_counts.live` vs `.nodes`, then list
  any node whose `node_status` is `issue`. `sleeping` is normal (it wakes on use).
- **"What's set up for me?"** → list `graph.nodes[].label` grouped by `kind`.
- **"Is my <voice agent / website / dashboard> up?"** → find the node whose `label`
  or `id` matches, report its `node_status` + `standing`.

**Always report from the live query — never from memory.** A node's health changes
minute to minute; only the live call is truth.

## If the call fails

- `401` → your `JAMFLOW_KEY` is missing/wrong (re-check the install-injected value).
- `404 unknown tenant` → your `JAMFLOW_TENANT` value is wrong.
- connection refused / timeout → the platform's JamFlow service may be briefly
  down; report "JamFlow is momentarily unreachable, retrying" and try once more.
  Do NOT invent a status.

## What JamFlow is NOT

- It is **not** a control panel — this is a read-only *view* of your systems. You
  don't start/stop things here; you observe and report health.
- The full operational board (every client's systems, the whole server) belongs to
  the platform host. You only get your own slice — by design.

---
