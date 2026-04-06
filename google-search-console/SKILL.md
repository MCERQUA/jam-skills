---
name: google-search-console
description: "Query Google Search Console data — real search impressions, clicks, CTR, average positions, indexing status, sitemaps. Use when user asks about actual search performance, real clicks, impressions, or indexing issues."
metadata:
  version: 1.0.0
  openclaw:
    requires:
      env: ["GSC_CREDENTIALS_PATH"]
---

# Google Search Console — Real Search Performance

Access real search performance data from Google Search Console. This gives you actual impressions, clicks, CTR, and average position from Google's own data — not estimates.

## When to Use

Activate when the user asks about:
- Real search impressions or clicks ("how many clicks from Google?")
- Click-through rates ("what's our CTR for contractor insurance?")
- Actual search positions ("what position are we really at?")
- Indexing problems ("is our site indexed?", "crawl errors")
- Sitemap status
- Comparing real data vs estimated data
- Search query discovery ("what queries are we showing up for?")

## API Access

The Google Search Console MCP server provides 19 tools. All are **free** (no per-query cost).

### Core Tools

| Tool | Purpose |
|------|---------|
| `list_properties` | List all verified GSC properties |
| `get_search_analytics` | Search performance data (impressions, clicks, CTR, position) |
| `get_performance_overview` | Quick performance summary |
| `inspect_url_enhanced` | Deep URL inspection (index status, crawl, mobile, rich results) |
| `check_indexing_issues` | Site-wide indexing problems |
| `get_sitemaps` | List submitted sitemaps |
| `submit_sitemap` | Submit new sitemap |

### Available Dimensions
`query`, `page`, `country`, `device`, `date`, `searchAppearance`

### Metrics Returned
`clicks`, `impressions`, `ctr`, `position`

## How GSC Complements DataForSEO

DataForSEO estimates traffic from ranking positions. GSC shows what *actually happened*:

- **354 ranked keywords** (DataForSEO) but GSC might show 1,200+ queries with impressions (long-tail, local variants DataForSEO doesn't track)
- **Estimated traffic: 175 ETV** (DataForSEO) vs **actual clicks: ???** (GSC) — the real number could be higher or lower
- **CTR by position** — DataForSEO uses a model, GSC has the real rates
- **Impressions without clicks** — queries where you show up but nobody clicks (title/description optimization opportunities)

## Authentication

Requires a Google service account JSON key. The service account email must be added as a **user** on the GSC property (Settings → Users and permissions).

Setup: `bash ~/scripts/setup-google-analytics-auth.sh`
