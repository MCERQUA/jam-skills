---
name: residential-pool
description: "Delegate browser/network tasks to a residential-IP node when datacenter IPs get blocked. Pool-aware: checks heartbeat freshness, picks alive node, sends delegate message, handles reply. Use when you see 403/Cloudflare-challenge/access-denied-from-network/empty-challenge-page from sites you otherwise have no reason to be blocked from."
---

# residential-pool

**Why it exists:** JamBot agents run on Hetzner VPS or cloud webtop containers — datacenter IPs. A growing share of sites (Cloudflare, Akamai-protected, Amazon, LinkedIn, Reddit, Instagram, most marketplaces) block or challenge datacenter traffic. When you hit that, you can't continue the task on your own network. Delegate to a **residential-IP-backed executor** instead.

## Detect a datacenter-IP block

Heuristics (any one of these = probable datacenter block):

- HTTP 403 with `Server: cloudflare` + `cf-ray` header + HTML containing "Just a moment..." or "Checking your browser"
- HTTP 403 with `Server: AkamaiGHost` or `x-akamai-transformed` and an Akamai challenge page
- HTTP 200 with `<title>Access denied</title>` or "Please enable JavaScript and cookies" in otherwise-empty body
- `curl`/`fetch` returns 0-byte or interstitial HTML that never reaches expected content
- Target: known to block datacenter ranges (LinkedIn, Instagram, TikTok, most US retail sites)

Don't confuse with actual site errors (500s, real 404s) or rate-limits (429) — those don't benefit from a different IP.

## Check pool liveness

```bash
MESH_ROOT="${MESH_ROOT:-/mesh}"
FRESH_S=120   # alive if heartbeat mtime < 120s old
ALIVE=""
for dir in "$MESH_ROOT/../agents/residential-"*/status/; do
  f="$dir/heartbeat.txt"
  [ -f "$f" ] || continue
  age=$(( $(date +%s) - $(stat -c %Y "$f" 2>/dev/null || echo 0) ))
  if [ "$age" -lt "$FRESH_S" ]; then
    node=$(basename "$(dirname "$dir")")  # e.g. residential-laptop
    ALIVE="$node"
    break
  fi
done
if [ -z "$ALIVE" ]; then
  echo "POOL OFFLINE — no residential node alive"
  # Surface to user: "this task requires a residential IP (site blocks datacenter),
  # and the residential pool is currently offline. Queued for retry."
fi
```

## Delegate a task

```bash
mesh-send --to "$ALIVE@mesh" --kind message --subject "fetch-via-residential-ip: <short-desc>" \
  --end-of-turn "$ALIVE@mesh — reply with <correlation-id>-result" <<EOF
# Delegate: fetch via residential IP

correlation_id: <uuid4>
deadline: 2026-04-22T00:45Z
task:
  type: http-fetch   # or: playwright-scrape, screenshot-site, headless-browse
  url: https://example.com/blocked-page
  intent: "Extract product price and stock status from this page."
  expected_return_shape:
    price: string (USD, e.g. "\$49.99")
    in_stock: boolean
  headers:
    User-Agent: (default — residential node picks a realistic one)

Why: bun-desktop hit Cloudflare 403 from Hetzner IP at 2026-04-22T00:12Z.
EOF
```

Then block your current turn on the reply (or queue the result for the next turn). If the deadline passes, surface the delay to the user.

## Handle the reply

Reply arrives as `kind=message` or `kind=attachment` with `correlation_id: <uuid4>` in the body. Parse the result, incorporate, continue the task.

## Fallbacks

1. **Pool offline, task is non-urgent:** tell the user *"blocked from datacenter IP, retrying when residential comes online — I'll surface when it lands"*. Queue as mesh `kind=question` to host@mesh with `--when-residential-online`.

2. **Pool offline, task is urgent AND read-only:** try one archive layer (Wayback Machine, Google Cache, archive.today) — often enough for research. Never for authenticated/stateful operations.

3. **Delegate returns failure (captcha, login required):** surface directly to user. Don't loop — residential isn't a captcha solver.

## Anti-patterns (do not do)

- ❌ Delegate EVERY http fetch to residential — wasteful; use residential only for confirmed blocks
- ❌ Fake a success response when blocked — violates `feedback_never_regress` and `feedback_openvoiceui_is_ai_computer`
- ❌ Poll `/status/heartbeat.txt` aggressively (>1/s) — mesh filesystem I/O is not free for residential
- ❌ Send secrets in the delegate payload — use the secret-passing rule (pointers only, env var names)
- ❌ Assume residential-laptop is always running — it's a laptop

## Cross-refs

- Host memory: `residential_pool_architecture.md`
- Registry: `/mnt/agent-mesh/mesh/REGISTRY/residential-laptop.md` (+ future `residential-*.md`)
- Mesh protocol: `/mnt/agent-mesh/mesh/PROTOCOL.md`
