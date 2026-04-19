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
