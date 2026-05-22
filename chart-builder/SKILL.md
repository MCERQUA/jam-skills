---
name: chart-builder
description: Voice agent / openclaw skill — create and save node-and-edge charts (system maps, architecture diagrams, FAQ trees, decision flows) that the user can open + edit in the Chart Builder canvas page at `/pages/chart-builder.html`. Charts persist server-side via `/api/upload` so the user and the agent can both read+modify the same chart.
trigger: When the user asks to "draw a chart", "make a diagram", "map this out", "show me a system map", or any visual node-graph request — generate the chart JSON below and POST to `/api/upload`. The user can then open Chart Builder to view + edit.
---

# Chart Builder — Schema + Workflow

The Chart Builder is a default canvas page at `/pages/chart-builder.html` on every tenant. It loads/saves chart JSON files via the same `/api/upload` endpoint that handles images — so an agent can generate a chart programmatically and have the user open it in the editor, no separate API.

## File-name convention

Charts saved server-side use filename pattern: `chart-<slug>.json` (e.g. `chart-system-map.json`, `chart-faq-tree-roofing.json`). The server prefixes the filename with `<YYYYMMDD>_<HHMMSS>_` automatically. Chart Builder's load picker filters to `chart-*.json` and shows newest first — saving the same logical name multiple times creates a version history.

## JSON schema (v1)

```json
{
  "version": 1,
  "saved_at": "2026-05-22T06:00:00.000Z",
  "nodes": [
    {
      "id": "n1",
      "x": 3500,
      "y": 2600,
      "text": "Node label",
      "color": "default | blue | green | orange | red | yellow | purple",
      "shape": "default | rect | round"
    }
  ],
  "edges": [
    { "id": "e1", "from": "n1", "to": "n2", "label": "optional edge label" }
  ],
  "nextNodeId": 3,
  "nextEdgeId": 2
}
```

- `x`, `y` are stage coords (stage is 8000×5500 px; center ~4000, 2750). Editor auto-fits on load — relative layout matters more than absolute.
- `id` strings: `n1`, `n2`, ... for nodes; `e1`, `e2`, ... for edges.
- `color` drives node background gradient — use as semantic categories (blue=infra, green=live, orange=parent, red=problem, yellow=warn, purple=automation).
- `shape` — `default`/`rect` are rectangles; `round` is a pill.
- `nextNodeId` / `nextEdgeId` — set to `max(existing) + 1`.

## Layered/stacked layout tip

Sprawl reads poorly. Place related nodes in clusters: top band = external/users, middle = services/domain, bottom = storage/infra. Cluster offset ~600px horizontal / ~300px vertical = clean.

## Save a chart (agent-side)

```bash
cat > /tmp/chart.json <<'JSON'
{
  "version": 1,
  "saved_at": "2026-05-22T06:00:00.000Z",
  "nodes": [
    {"id": "n1", "x": 3800, "y": 2400, "text": "user", "color": "orange", "shape": "round"},
    {"id": "n2", "x": 3800, "y": 2700, "text": "openvoiceui", "color": "blue", "shape": "default"},
    {"id": "n3", "x": 3800, "y": 3000, "text": "openclaw", "color": "green", "shape": "default"}
  ],
  "edges": [
    {"id": "e1", "from": "n1", "to": "n2", "label": "voice"},
    {"id": "e2", "from": "n2", "to": "n3", "label": "ws"}
  ],
  "nextNodeId": 4,
  "nextEdgeId": 3
}
JSON

curl -s -X POST \
  -F "file=@/tmp/chart.json;filename=chart-my-diagram.json" \
  https://<tenant>.jam-bot.com/api/upload \
  -b "$CLERK_SESSION_COOKIE"
```

Response includes `url` (e.g. `/uploads/20260522_063000_chart-my-diagram.json`).

## Read a chart (agent-side)

```bash
curl -s https://<tenant>.jam-bot.com/api/uploads | jq '.uploads[] | select(.filename | test("chart-.*\\.json$"))'
curl -s https://<tenant>.jam-bot.com/uploads/20260522_063000_chart-my-diagram.json
```

Read → modify → re-save for iterative refinement.

## Collaborative workflow

1. User asks agent: "draw the architecture"
2. Agent generates chart JSON + POSTs to `/api/upload` as `chart-architecture.json`
3. Agent tells user "saved as `chart-architecture` — open Chart Builder → Load to see it"
4. User opens, edits visually, hits Save (creates new timestamp)
5. Agent reads latest version next session, sees user's changes, extends further

## Avoid

- No localStorage — VPS is source of truth
- Don't pre-fetch every chart on page load
- Don't generate >40 nodes without grouping strategy — break into multiple charts with a parent index
- Don't fabricate node values when intent is unclear — use placeholder text like `TODO: <subject>` so the user sees what to fill

## Related canvas pages

- `system-map.html` — read-only architecture map (v1; v2 design in mesh delegation)
- `chart-builder.html` — this page (default tool on every tenant)
