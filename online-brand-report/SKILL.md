---
name: online-brand-report
description: "Generate a fully-populated SEO brand report as a branded canvas HTML page for any client domain using REAL DataForSEO data — brand health score (graded A-F across SEO/Web/Local/Backlinks/Content/Social), keyword rankings, local SEO/GMB, backlinks, and a prioritized action roadmap. Use when a prospect or client asks for a 'brand report', 'online brand report', 'SEO audit', 'online visibility report', or 'digital presence report', or when onboarding a new client. This is THE skill for brand reports — run it; do NOT hand-write, summarize, or improvise a report from other tools."
metadata:
  version: 1.0.0
  openclaw:
    emoji: "📊"
---
# Skill: online-brand-report

Generate a fully-populated SEO brand report HTML page for any client domain using real DataForSEO data.

## When to use

Use this skill when:
- A prospect or client asks for a "brand report", "SEO audit", "online visibility report", or "digital presence report"
- You need to create a canvas page showing a client's brand health score, keyword rankings, local SEO, backlinks, and a prioritized action roadmap
- Onboarding a new client and you want to generate their initial report

## What it produces

A self-contained HTML file saved to the client's canvas-pages directory with:
- **Brand Health Score** (0-100, graded A-F) across 6 dimensions: SEO, Web, Local, Backlinks, Content, Social
- **Found** page: Core Web Vitals, Lighthouse scores, organic keyword rankings, SERP results, local reviews, map pack positions, backlink profile, competitive analysis, content gaps, AI/LLM visibility, social presence
- **Plan** page: Priority 1/2/3 action roadmap auto-generated from audit findings
- **Team** page: Overview of recommended tools and services
- **Day One** page: First-30-days quick wins
- **Sign Up** page: Call to action

## Usage

```
python /mnt/system/base/skills/online-brand-report/generate.py \
  --domain <domain> \
  --name "<Business Name>" \
  --owner "<Owner Name>" \
  --city "<City>" \
  --state "<ST>" \
  --phone "<phone>" \
  --email "<email>" \
  --service "<primary service>" \
  --competitors "comp1.com,comp2.com" \
  --output /mnt/clients/<tenant>/openvoiceui/canvas-pages/brand-report-<slug>.html \
  --tenant <tenant>
```

## Required arguments

| Argument | Description |
|---|---|
| `--domain` | Target domain without https:// (e.g. `spartancoatingsystems.com`) |
| `--name` | Business name (e.g. `"Spartan Coating Systems"`) |

## Optional arguments

| Argument | Default | Description |
|---|---|---|
| `--owner` | "" | Owner or contact name |
| `--city` | "" | Primary city for local SEO |
| `--state` | "" | State abbreviation |
| `--phone` | "" | Phone number |
| `--email` | "" | Contact email |
| `--service` | "" | Primary service (drives keyword research) |
| `--competitors` | "" | Comma-separated competitor domains |
| `--output` | auto | Full path for output HTML (auto-generated from domain if omitted) |
| `--tenant` | test-dev | JamBot tenant for default output path |

## Output

The script prints to stdout:
```
Report generated: /mnt/clients/<tenant>/openvoiceui/canvas-pages/brand-report-<slug>.html
Score: 47/100 (C — Developing — Present But Outranked)
Roadmap: 4 P1 / 3 P2 / 4 P3 action items
Canvas URL: /canvas/brand-report-<slug>.html
```

Progress and cost information prints to stderr during execution.

## Canvas URL

After generation, the report is accessible at:
```
https://<tenant>.jam-bot.com/canvas/brand-report-<slug>.html
```

Or via the canvas pages menu in the tenant's OpenVoiceUI.

## Data sources

The skill fetches from 10 DataForSEO endpoint categories:
1. `business_data/google/my_business_info` — GMB profile, rating, review count
2. `on_page/lighthouse` — Core Web Vitals (LCP, CLS, TBT), Lighthouse performance/SEO/accessibility
3. `dataforseo_labs/google/ranked_keywords` — organic keyword rankings by position bucket
4. `serp/google/organic/live/advanced` — SERP results for service+city queries
5. `business_data/google/reviews` — review distribution and recent reviews
6. `serp/google/maps/live/advanced` — map pack positions per city
7. `backlinks/summary` + `backlinks/referring_domains` + `backlinks/anchors` — backlink profile
8. `dataforseo_labs/google/competitors_domain` + `bulk_traffic_estimation` — competitive analysis
9. `dataforseo_labs/google/keyword_suggestions` + `domain_intersection` — content gaps
10. Direct HTTP checks — llms.txt, JSON-LD schema, social profiles
11. **Brand-name SERP discovery** (`fetch_discovery.py`) — runs a small fan-out of brand-name
    Google SERPs ("what anyone types in") via DataForSEO and harvests the FULL off-site
    footprint: real social profiles, directory/citation/review listings (Yelp, BBB, Angi,
    HomeAdvisor, Houzz, MapQuest, YellowPages, Manta, SprayFoam.org…), Google Business presence
    (knowledge_graph / local_pack), and long-tail mentions (state registration, FMCSA, press,
    video). A distinctive **brand-slug filter** rejects look-alike competitors and generic
    category pages so "grab everything" stays accurate. This is the deterministic ground truth
    that fixed the old fragile "no Facebook / no GMB" false negatives.
12. **Serper Places enrichment** (`fetch_serper.py`) — Serper.dev `/places` returns the rich,
    verified GMB listing (exact name, rating + review count, phone, street address, website,
    category) and a NAP phone cross-check (flags a caller-supplied phone that disagrees with
    the verified GMB number). Authoritative for the GMB listing fields when present.
    `fetch_connected_and_mentions()` also runs a Serper /search fan-out (brand + phone + address),
    brand-matches result snippets, and returns connected-site candidates + a full mention inventory.
13. **Reverse-analytics — hidden site network** (`fetch_dnslytics.py`) — headless-renders the
    site (Playwright) to capture its Google Analytics / GTM / AdSense IDs (JS-injected, so a raw
    fetch misses them), then reverses each via DNSlytics (`reverseganalytics` / `reverseadsense`)
    to find every other domain the same operator runs — the DBA / lead-gen / supporting sites
    keyword search can't surface. Requires `DNSLYTICS_API_KEY` (`.openclaw-keys.env`); no-key-safe
    (skips the headless render entirely when absent).

Credentials: DataForSEO from `/mnt/system/base/.platform-keys.env`; `SERPER_API_KEY` from
`/mnt/system/base/.openclaw-keys.env` (or the environment). Serper enrichment is additive — if
the key is absent it's skipped and the DataForSEO data stands.

### Detection robustness (why it no longer misses the obvious)

The Local/GMB + Social dimensions are now multi-sourced and authoritative-merged so the report
never again flips between "GMB 4.8★ / Facebook found" and "no GMB / no Facebook" run-to-run:
- **GMB existence**: union of my_business_info + brand-SERP knowledge panel + Serper Places.
  Found by ANY = found. Listing fields (NAP/rating/reviews) prefer Serper Places.
- **Social**: SERP-discovered profiles override the fragile homepage-scrape + HEAD-probe — a
  profile Google returns for the brand EXISTS regardless of what a flaky bot probe concluded.

## Error handling

Every fetcher is individually wrapped — if one data source fails, the rest of the report still generates with safe defaults (zeros, empty lists, "N/A"). The report never fails completely due to a single API error.

## Example

```
python /mnt/system/base/skills/online-brand-report/generate.py \
  --domain spartancoatingsystems.com \
  --name "Spartan Coating Systems" \
  --owner "Stephen Smith" \
  --city "Lawton" \
  --state "OK" \
  --phone "+1-580-555-0100" \
  --email "info@spartancoatingsystems.com" \
  --service "spray foam insulation" \
  --tenant test-dev
```

## Notes

- The HTML file is fully self-contained (CSS, JS, Chart.js from CDN) — share the file directly or serve via canvas
- Report CSS and structure matches the JamBot dark-theme design system
- Template source: `/mnt/clients/test-dev/openvoiceui/canvas-pages/online-brand-report-template.html`
- Generation takes 60-120 seconds depending on DataForSEO API response times
