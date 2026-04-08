# SEO Platform Dashboard

You have a full SEO analytics dashboard available as a canvas page. Use it to help clients understand their search engine performance, find keyword opportunities, audit technical issues, and track competitors.

## Opening the Dashboard

```
[CANVAS_URL:https://<USER>.jam-bot.com/pages/seo-platform.html]
```

The dashboard auto-detects the client from the hostname. All data is tenant-isolated.

---

## Dashboard Pages (12 Views)

### Projects
Portfolio view of all tracked domains. Each project card shows 6 KPIs: Organic Keywords, Organic Traffic, Backlinks, Site Health %, AI Mentions, and Top 3 count — all with % change indicators. Manage competitors per project. Connect Google Business Profile.

### Dashboard (Overview)
At-a-glance health: 6 KPI cards (keywords, traffic, backlinks, health, top 3, competitors), position distribution chart, top keywords table, competitor comparison, overview trend. Alerts panel shows rank drops, traffic changes, backlink losses.

### Domain Analysis
Deep analysis of any domain: authority score, traffic, backlinks, top pages by traffic, page-keyword map (which URL ranks for which keywords), topic categories, technology stack, WHOIS registration, competitors with overlap %, subdomains breakdown, traffic trend chart.

### Position Tracking
Track keyword rankings over time. KPI cards (visibility %, traffic, avg position, top 3). Ranking trend chart (stacked area: pos 1-3 / 4-10 / 11-20 / 21-100 over time). Full rankings table with change arrows. Tracked keywords panel — add/remove keywords to monitor. CSV export.

### Keyword Magic Tool
Research keywords with 4 modes: Suggestions (related terms), Keyword Ideas (broader brainstorming), Related/Clusters (topic grouping), By Category (category-based). Filters: volume, KD%, CPC, include/exclude. Match types: All, Questions, Broad, Phrase, Exact. Keyword clusters sidebar. Trending searches chips.

### Keyword Overview
Single keyword deep-dive: search volume, CPC, difficulty gauge, intent badge, competition level. SERP features detected. Google Trends chart. Top 10 SERP results with backlink counts. People Also Ask questions. Keyword variations. SERP competitors. YouTube results. Paid ad copies. PPC metrics (impressions, clicks, cost estimates). Recent search history.

### Keyword Gap
Competitor comparison: your domain vs 1-2 competitors. Auto-discover competitors or enter manually. Keywords classified as Missing (they rank, you don't), Weak (they top 10, you 20+), Untapped (both rank low), Strong (you outrank them). Opportunities table sorted by volume. Risk factors table. Full filterable results with pagination.

### Site Audit
Technical SEO health check. Fetch sitemap, start crawl (up to 200 pages). Health score gauge. Issues by severity (critical/warning/notice) with expandable page-level details. Duplicate tags, non-indexable pages, resource issues, link analysis (all FREE after crawl). Lighthouse scores (Performance, Accessibility, Best Practices, SEO). Page Deep-Dive: enter any URL for heading structure, word count, link analysis. Page screenshot.

### Backlinks
Backlink profile: total backlinks, referring domains, dofollow ratio, domain rating. Growth chart (from saved data or full historical API). New/lost backlinks comparison. Referring domains table (paginated). Individual backlinks table (actual linking URLs, anchor text, type). Anchor text breakdown. Link building opportunities (domains linking to competitors but not you). Analysis history.

### AI Visibility
AI model mentions: what ChatGPT, Claude, Gemini, Perplexity say about the brand. Grouped by platform with expandable responses showing the actual AI answer, cited sources, and search volume. Top AI-citing domains. Web mentions: sentiment analysis (positive/neutral/negative gauge), top web sources, full mentions table with search and pagination.

### Local SEO
Google Business Profile data: name, rating, address, phone, hours, category. Review feed with star ratings. Review rating distribution chart. Map pack rankings (what position the business appears in Google Maps for keywords). Full review history with owner responses. GMB posts (promotions, updates, events). Autocomplete suggestions for content ideas.

### Content & Brand Monitor
Brand monitoring across the web. KPI cards (total mentions, positive, neutral, negative with sentiment percentages). Mention feed (expandable, sortable, filterable). News feed from Google News. Top source domains. Phrase trends (word frequency from mentions). Source type breakdown. Rating distribution from review sites across the web. Mention trend chart over time.

---

## Managing Projects (FREE)

You can add, list, and batch-import projects for your client. This is how domains get into the SEO dashboard.

**Base URL:** `http://172.17.0.1:6350/api/seo`

### List Projects
```bash
curl -s "http://172.17.0.1:6350/api/seo/projects?tenant=<USER>"
```
Returns all active projects with their domain, label, location, competitors, GMB data.

### Add a Single Project
```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"domain":"example.com","label":"Example Site","brand_name":"Example Inc","location_name":"United States","language_name":"English"}' \
  "http://172.17.0.1:6350/api/seo/projects?tenant=<USER>"
```
Fields: `domain` (required), `label`, `brand_name`, `phone`, `address`, `business_category`, `location_name` (default: "United States"), `language_name` (default: "English"), `competitors` (array), `gmb_query` (search term for Google Business Profile lookup).

If the domain already exists, only the fields you provide are updated — existing values are preserved.

### Batch Add Projects (for bulk imports)
```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"projects":[{"domain":"site1.com","label":"Site 1"},{"domain":"site2.com","label":"Site 2"}]}' \
  "http://172.17.0.1:6350/api/seo/projects/batch?tenant=<USER>"
```
Accepts an array of project objects. Each uses the same fields as single add. Returns `{ added: [...], updated: [...], errors: [...], total: N }`. Domains are auto-cleaned (strips `https://`, trailing slashes, lowercased). Safe to re-run — existing domains are updated, not duplicated.

**Example: Adding many domains at once**
```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"projects":[
    {"domain":"clientsite.com","label":"Main Site","brand_name":"Client Name"},
    {"domain":"clientblog.com","label":"Blog"},
    {"domain":"clientstore.com","label":"Store","business_category":"E-commerce"}
  ]}' \
  "http://172.17.0.1:6350/api/seo/projects/batch?tenant=<USER>"
```

### Connect Google Business Profile (COSTS ~$0.004)
After adding a project, search for the business on Google Maps to connect their GMB profile:
```bash
# Step 1: Search for the business
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"endpoint":"business_data/google/my_business_info/live","data":[{"keyword":"Business Name City","location_name":"United States","language_name":"English"}]}' \
  "http://172.17.0.1:6350/api/seo/proxy?tenant=<USER>"
```
This returns matching businesses with `title`, `address`, `phone`, `rating`, `cid`, `place_id`, `category`.

```bash
# Step 2: Connect the matching business to the project
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"domain":"example.com","gmb_cid":"<cid>","gmb_place_id":"<place_id>","gmb_name":"<title>","gmb_address":"<address>","gmb_phone":"<phone>","gmb_rating":"<rating>","gmb_category":"<category>"}' \
  "http://172.17.0.1:6350/api/seo/projects?tenant=<USER>"
```

### When to Add Projects
- When a client asks to track a new domain
- When onboarding a client with multiple domains — use batch endpoint
- When the client mentions a domain they own that isn't being tracked yet
- Always confirm with the client before adding projects (they control what gets tracked)

---

## Reading Data (FREE — No API Cost)

All accumulated data endpoints read from the database. Use these to answer client questions about their SEO performance.

**Base URL:** `http://172.17.0.1:6350/api/seo`

### Quick Summary
```bash
curl -s "http://172.17.0.1:6350/api/seo/dashboard?tenant=<USER>"
```
Returns: total queries, cost, tools used, top targets, recent queries.

### Keywords
```bash
curl -s "http://172.17.0.1:6350/api/seo/accumulated/keywords?tenant=<USER>&domain=<DOMAIN>&limit=50"
```
Returns: keyword, volume, cpc, difficulty, intent, rank, domain. Sorted by volume.

### Backlinks
```bash
curl -s "http://172.17.0.1:6350/api/seo/accumulated/backlinks?tenant=<USER>&domain=<DOMAIN>"
```
Returns: summary (total, referring_domains, rank, dofollow/nofollow), individual backlinks (url_from, url_to, anchor, type).

### Competitors
```bash
curl -s "http://172.17.0.1:6350/api/seo/accumulated/competitors?tenant=<USER>&domain=<DOMAIN>"
```
Returns: competitor domains with organic keywords, traffic, common keywords, rank.

### Site Audit
```bash
curl -s "http://172.17.0.1:6350/api/seo/accumulated/audits?tenant=<USER>&domain=<DOMAIN>"
```
Returns: onpage_score, pages_count, warnings, errors, notices, checks.

### Local SEO
```bash
curl -s "http://172.17.0.1:6350/api/seo/accumulated/local?tenant=<USER>"
```
Returns: maps rankings, business data, reviews with star distribution.

### Brand Mentions
```bash
curl -s "http://172.17.0.1:6350/api/seo/accumulated/content-monitor?tenant=<USER>&domain=<DOMAIN>"
```
Returns: mentions, news, phrase trends, top sources, sentiment breakdown.

### Alerts
```bash
curl -s "http://172.17.0.1:6350/api/seo/alerts?tenant=<USER>"
```
Returns: active alerts (rank drops, traffic changes, backlink losses).

### Tracked Keywords
```bash
curl -s "http://172.17.0.1:6350/api/seo/tracked-keywords?tenant=<USER>&domain=<DOMAIN>"
```
Returns: keywords being actively monitored.

### Data Pipeline Health
```bash
curl -s "http://172.17.0.1:6350/api/seo/diagnostic?tenant=<USER>&domain=<DOMAIN>"
```
Returns: per-view data health checks, field validation, staleness detection.

---

## Refreshing Data (COSTS MONEY)

These call DataForSEO live API. Only trigger when the client explicitly asks.

| Action | Cost | What It Does |
|--------|------|-------------|
| Dashboard Refresh | ~$0.03 | Updates keywords, traffic, competitors |
| Domain Analysis Refresh | ~$0.09 | Full domain scan including top pages |
| Position Tracking Refresh | ~$0.02 | Updates keyword rankings |
| Keyword Search | ~$0.01 | Discovers keywords for a seed term |
| Keyword Analyze | ~$0.10 | Deep-dive on single keyword |
| Site Audit (crawl) | ~$0.075 | Crawls up to 200 pages |
| Lighthouse | ~$0.004 | Performance/accessibility scores |
| Backlinks Check | ~$0.06 | Summary + referring domains + anchors |
| AI Model Scan | ~$0.10 | Check ChatGPT/Gemini/Claude mentions |
| Web Mentions Scan | ~$0.07 | Brand monitoring across web |
| Local SEO Refresh | ~$0.007 | GMB profile + map rankings |
| Report Generation | FREE | Generates HTML report from saved data |

**Weekly auto-refresh runs Sundays 2am** — updates ranked keywords, traffic, backlinks summary, and generates snapshots + alerts for all active projects.

---

## Generating Reports

```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"domain":"<DOMAIN>"}' \
  "http://172.17.0.1:6350/api/seo/report/generate?tenant=<USER>"
```

Returns a URL to the generated HTML report. The report includes:
- KPI summary, position distribution, traffic trend
- AI executive summary + keyword strategy + technical recommendations
- Keyword performance table with intent classification
- Backlink profile with dofollow/nofollow split, top anchors, referring domains
- Competitor analysis with common keywords
- Content strategy and local SEO recommendations
- Priority action plan

Reports are saved as canvas pages and appear in the report history.

---

## How to Help Clients

When a client asks about their SEO:

1. **Check their data first** — use the accumulated endpoints (FREE) to see current state
2. **Navigate them to the right page** — use `[CANVAS_URL:...]` to open the dashboard
3. **Explain in context** — reference their actual numbers, not generic advice
4. **Suggest actions** — recommend refreshes for stale data, specific keyword research, competitor analysis
5. **Cost awareness** — always mention the cost before triggering paid API calls

Example client questions and how to handle them:
- "How are my rankings?" → Fetch accumulated/keywords, summarize top performers and position distribution
- "Who are my competitors?" → Fetch accumulated/competitors, highlight the biggest threats
- "Is my site healthy?" → Fetch diagnostic endpoint, explain any issues found
- "What keywords should I target?" → Open Keyword Magic page, suggest relevant seed keywords based on their business
- "How's my backlink profile?" → Fetch accumulated/backlinks, compare dofollow ratio and growth
- "Are AI chatbots mentioning me?" → Check AI visibility data, explain what it means for their business
