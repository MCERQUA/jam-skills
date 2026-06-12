---
name: cc-backlinks
description: "Free backlink discovery powered by the Common Crawl hyperlink graph — zero cost per query, on-VPS dataset. Additive check alongside paid DataForSEO backlink calls. Compare multiple domains or competitors without burning credits."
version: 1.0.0
---

# Common Crawl Backlinks (Free Backlink Lookup)

You have access to a free backlink discovery tool powered by the Common Crawl hyperlink graph. Use this as an **additive free check** alongside the paid DataForSEO backlink data — it costs nothing per query, so you can run it liberally for every client and every competitor.

## When to use this tool

- Client asks "who links to my site?" and you want a zero-cost first look
- You've already used a DataForSEO backlink call and want a **cross-check** from an independent source
- Comparing multiple competitors at once — DataForSEO would burn credits, CC is free
- Historical trend — CC releases are archived back years, so you can compare a domain across quarters
- The client is on a free tier or trial and you want to show real backlink value before they pay

## Cost

**$0 per query.** The data lives on the VPS (one-time ~16GB download). Query latency is a few seconds per domain.

## How to invoke

The tool lives at `/mnt/system/base/tools/cc-backlinks/`. You call it through the SEO platform API (preferred) or directly via shell when inside the openclaw container.

### Preferred — SEO platform endpoint
```
GET http://172.17.0.1:6350/api/seo/cc-backlinks?domain=example.com&limit=200
```
(Endpoint status: see SEO dashboard integration plan — may be pending deployment.)

### Direct shell fallback
```bash
/mnt/system/base/tools/cc-backlinks/cc-backlinks.sh example.com --limit 200
```
Returns JSON:
```json
{
  "domain": "example.com",
  "release": "cc-main-2026-jan-feb-mar",
  "total": 1234,
  "backlinks": [
    { "linking_domain": "some-site.com", "num_hosts": 12 }
  ]
}
```

`num_hosts` = how many subdomains/hosts that linking domain has — rough proxy for size/authority.

## What you get vs. what you don't

**You get:**
- List of every domain that linked to the target (as of the CC release)
- Coarse size signal via `num_hosts`
- Free, unlimited queries

**You do NOT get:**
- Anchor text or surrounding page context
- Individual page URLs (it's domain-level only)
- Dofollow / nofollow flags
- Link quality / spam scoring
- Fresh data — CC is ~3 months stale (quarterly releases)

**Always disclose these limitations** when presenting results to the client. Frame it as "the free baseline layer" — use DataForSEO for fresh data, anchor text, and quality scoring when the client needs depth.

## How to present results to the client

1. Run CC lookup first (free)
2. Pull top 10-20 linking domains, discuss who they are, what they do
3. Identify high-value vs low-value patterns
4. If they want deeper detail (anchor text, page URLs, quality scores) — recommend a DataForSEO backlink report as the follow-up (paid)

This creates a natural upsell: free data proves there's something worth exploring, paid data unlocks the specifics.

## Competitor comparison workflow

1. Run CC lookup for client domain → save list
2. Run CC lookup for each competitor (free — do as many as you want)
3. Find **linking domains hitting competitors but NOT the client** = outreach opportunities
4. Present as a gap analysis view

This is genuinely useful and costs nothing. Use it as often as possible.

## Update cadence

CC publishes quarterly releases. The release currently cached: `cc-main-2026-jan-feb-mar`. If the user asks for fresher data, check https://commoncrawl.org for newer releases and the admin can swap it in via `CC_RELEASE=<new-release> bash /mnt/system/base/tools/cc-backlinks/download-data.sh`.

---

## Interpreting `num_hosts` — calibrating the free authority signal

`num_hosts` (subdomain/host count of the linking domain) is a SIZE proxy, not a quality score.
Calibrate it against the free Ahrefs DR before drawing conclusions:

```bash
curl -s "https://api.ahrefs.com/v3/public/domain-rating-free?target=<linking-domain>&output=json"
# → {"domain_rating": {"domain_rating": 34.0}}  — $0, no API key
```

Practical tiering for a CC result list:
1. Sort linking domains by `num_hosts` descending.
2. DR-check the top 20–30 (free, ~0.2s apart to be polite).
3. Tier them: DR 50+ = premium links (brag in the report), DR 30–49 = solid, DR <30 = local/niche
   (still valuable for local SEO), DR 0 + tiny num_hosts = likely noise/scraper domains — exclude
   from client-facing counts so the "total backlinks" number stays defensible.

This combo (CC graph + free DR) is a complete $0 backlink-quality picture; DataForSEO
(`backlinks/bulk_spam_score/live`, `backlinks/backlinks/live`) adds spam scores, anchor text, and
page-level URLs when the client pays for depth.

## Quarter-over-quarter trend workflow

CC releases are archived, so backlink GROWTH can be shown for free:
1. Keep each quarter's query output: save JSON to the tenant workspace
   (`seo/cc-backlinks/<domain>-<release>.json`) — server filesystem, never browser storage.
2. Next release: diff `linking_domain` sets → **new domains** (wins to report) vs **lost domains**
   (churn to investigate — did the linking site die, or drop us?).
3. Present as "links gained / lost this quarter" — clients understand deltas far better than
   totals, and it's the same story the paid `backlinks/timeseries_new_lost_summary` endpoint
   tells, at $0 and one-quarter granularity.

## Link-gap → outreach handoff

The competitor-gap output (domains linking to competitors but not the client) feeds two systems:
- **Niche Backlink Intelligence** (`/mnt/system/base/tools/niche-backlinks/` + `/mnt/backlinks/`)
  — add validated gap domains to the per-niche linker DB so every client in that niche benefits.
- **DR-tiered outreach list** — DR-check the gap domains (free, above), keep DR 20+, sort by DR,
  and hand the client/agent a prioritized outreach sheet: domain, DR, which competitors it links
  to, suggested angle (directory listing / supplier page / association membership / guest post).

## Related skills
- `dataforseo` — paid depth: anchors, spam score, timeseries, page-level links
- `online-brand-report` — the report's backlink dimension (already DR-enriched)
- `niche-backlink-intelligence` (docs: `docs/jambot/niche-backlink-intelligence.md`) — per-niche linker database this skill feeds
