---
name: dataforseo
description: "DataForSEO API — keyword research, SERP tracking, competitor analysis, backlink checks, site audits, local SEO/GMB data, brand monitoring. Use when client asks about keywords, rankings, competitors, backlinks, site audit, local SEO, Google reviews, or any SEO data."
metadata:
  version: 1.0.0
  openclaw:
    emoji: "🔍"
---

# DataForSEO API — SEO Data for Client Businesses

You have access to DataForSEO, a comprehensive SEO data API. Use it to get real keyword data, SERP rankings, competitor intelligence, backlink profiles, site audit results, and local business data for the client's business.

## Authentication

Credentials are in your environment variables:
- `DATAFORSEO_LOGIN` — API login email
- `DATAFORSEO_PASSWORD` — API password

**Every request uses HTTP Basic Auth:**
```bash
AUTH=$(echo -n "$DATAFORSEO_LOGIN:$DATAFORSEO_PASSWORD" | base64)

curl -s -X POST "https://api.dataforseo.com/v3/endpoint" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '[{ "param": "value" }]'
```

**Base URL:** `https://api.dataforseo.com/v3/`

## Cost Awareness

This API costs real money. Be efficient:
- **Batch keywords** — up to 1,000 per Google Ads request ($0.05 total, not per keyword)
- **Use Labs** for bulk research ($0.01/task) instead of live SERP ($0.002/query)
- **Use Standard mode** (async) when client isn't waiting for instant results
- **Limit depth to 10** unless client specifically needs deeper results
- **Never run exploratory queries** — know what you're looking for before calling

| API | Cost/task | Best for |
|-----|-----------|----------|
| SERP Live | $0.002 | Checking current rankings for specific keywords |
| Keywords Data | $0.05 | Bulk search volume (up to 1,000 keywords) |
| Labs | $0.01 | Keyword research, competitor analysis, difficulty scores |
| Search Intent | $0.001 | Classifying keyword intent |
| OnPage (basic) | $0.000125/page | Site audits |
| Business Data | $0.004 | GMB profiles, Google reviews |
| Backlinks | $0.02 | Link profiles (requires activation) |

## Quick Reference — Most Useful Endpoints

### Get Search Volume for Keywords
```bash
AUTH=$(echo -n "$DATAFORSEO_LOGIN:$DATAFORSEO_PASSWORD" | base64)
curl -s -X POST "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d "[{
    \"keywords\": [\"keyword1\", \"keyword2\", \"keyword3\"],
    \"location_name\": \"$LOCATION\",
    \"language_name\": \"English\"
  }]"
```
**Returns:** `search_volume`, `competition` (HIGH/MEDIUM/LOW), `cpc`, `monthly_searches[]`

### Check Google Rankings for a Keyword
```bash
curl -s -X POST "https://api.dataforseo.com/v3/serp/google/organic/live/advanced" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d "[{
    \"keyword\": \"roofing company near me\",
    \"location_name\": \"Seattle,Washington,United States\",
    \"language_name\": \"English\",
    \"depth\": 10
  }]"
```
**Returns:** Full SERP with organic results, featured snippets, PAA, knowledge panels

### Check Local Map Pack Rankings
```bash
curl -s -X POST "https://api.dataforseo.com/v3/serp/google/maps/live/advanced" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d "[{
    \"keyword\": \"roofing company\",
    \"location_name\": \"Seattle,Washington,United States\",
    \"language_name\": \"English\"
  }]"
```

### Get Keyword Suggestions
```bash
curl -s -X POST "https://api.dataforseo.com/v3/dataforseo_labs/google/keyword_suggestions/live" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d "[{
    \"keyword\": \"roof repair\",
    \"location_name\": \"United States\",
    \"language_name\": \"English\",
    \"limit\": 50
  }]"
```

### Analyze Competitor Keywords
```bash
curl -s -X POST "https://api.dataforseo.com/v3/dataforseo_labs/google/ranked_keywords/live" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d "[{
    \"target\": \"competitor.com\",
    \"location_name\": \"United States\",
    \"language_name\": \"English\",
    \"limit\": 100
  }]"
```

### Find Competitors for a Domain
```bash
curl -s -X POST "https://api.dataforseo.com/v3/dataforseo_labs/google/competitors_domain/live" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d "[{
    \"target\": \"clientsite.com\",
    \"location_name\": \"United States\",
    \"language_name\": \"English\"
  }]"
```

### Keyword Difficulty Scores
```bash
curl -s -X POST "https://api.dataforseo.com/v3/dataforseo_labs/google/bulk_keyword_difficulty/live" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d "[{
    \"keywords\": [\"keyword1\", \"keyword2\"],
    \"location_name\": \"United States\",
    \"language_name\": \"English\"
  }]"
```

### Search Intent Classification
```bash
curl -s -X POST "https://api.dataforseo.com/v3/dataforseo_labs/google/search_intent/live" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d "[{
    \"keywords\": [\"buy roof shingles\", \"how to fix roof leak\", \"roofer reviews\"],
    \"language_name\": \"English\"
  }]"
```
**Returns:** intent per keyword — `commercial`, `informational`, `navigational`, `transactional`

### Get Google My Business Info
```bash
curl -s -X POST "https://api.dataforseo.com/v3/business_data/google/my_business_info/live" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d "[{
    \"keyword\": \"Business Name City State\",
    \"location_name\": \"City,State,United States\"
  }]"
```
**Returns:** Name, address, phone, hours, rating, review count, categories, photos, attributes

### Get Google Reviews
```bash
curl -s -X POST "https://api.dataforseo.com/v3/business_data/google/reviews/live" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d "[{
    \"keyword\": \"Business Name City State\",
    \"depth\": 100
  }]"
```

### Run a Site Audit (Async)
```bash
# Step 1: Start crawl
curl -s -X POST "https://api.dataforseo.com/v3/on_page/task_post" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d "[{
    \"target\": \"clientsite.com\",
    \"max_crawl_pages\": 200,
    \"load_resources\": true
  }]"
# Save the task ID from response

# Step 2: Check if ready (wait ~5 min for small sites)
curl -s "https://api.dataforseo.com/v3/on_page/summary/$TASK_ID" \
  -H "Authorization: Basic $AUTH"

# Step 3: Get pages with issues
curl -s "https://api.dataforseo.com/v3/on_page/pages/$TASK_ID" \
  -H "Authorization: Basic $AUTH"

# Step 4: Duplicate title/description tags
curl -s "https://api.dataforseo.com/v3/on_page/duplicate_tags/$TASK_ID" \
  -H "Authorization: Basic $AUTH"
```

### Lighthouse Score (Single Page)
```bash
curl -s -X POST "https://api.dataforseo.com/v3/on_page/lighthouse/live" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d "[{
    \"url\": \"https://clientsite.com\",
    \"for_mobile\": true
  }]"
```

### Backlink Summary
```bash
curl -s -X POST "https://api.dataforseo.com/v3/backlinks/summary/live" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d "[{\"target\": \"clientsite.com\", \"backlinks_status_type\": \"live\"}]"
```

### Traffic Estimation
```bash
curl -s -X POST "https://api.dataforseo.com/v3/dataforseo_labs/google/bulk_traffic_estimation/live" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d "[{\"targets\": [\"site1.com\", \"site2.com\", \"site3.com\"]}]"
```

---

## Workflow Templates

### "Research keywords for my business"
1. Get seed suggestions: `labs/keyword_suggestions` with business-related seed terms
2. Pull search volume: `keywords_data/google_ads/search_volume` (batch all suggestions)
3. Score difficulty: `labs/bulk_keyword_difficulty`
4. Classify intent: `labs/search_intent`
5. Present: table with keyword, volume, difficulty, intent, CPC — sorted by opportunity

### "How am I ranking?"
1. Get all ranked keywords: `labs/ranked_keywords` for client's domain
2. Check specific targets: `serp/google/organic/live` for priority keywords
3. Check map pack: `serp/google/maps/live` for local keywords
4. Present: rankings table with position, keyword, URL, search volume

### "Analyze my competitors"
1. Find competitors: `labs/competitors_domain` for client's domain
2. Compare keywords: `labs/domain_intersection` between client + top competitors
3. Estimate traffic: `labs/bulk_traffic_estimation` for all domains
4. Find gaps: keywords competitors rank for that client doesn't
5. Present: competitor comparison table

### "Audit my website"
1. Start crawl: `on_page/task_post` (200-500 pages)
2. Get Lighthouse: `on_page/lighthouse/live` for homepage
3. Review pages: `on_page/pages` for issues
4. Check duplicates: `on_page/duplicate_tags`
5. Check indexability: `on_page/non_indexable`
6. Present: issue summary with priorities

### "Check my Google reviews"
1. Get GMB info: `business_data/google/my_business_info/live`
2. Get reviews: `business_data/google/reviews/live`
3. Present: rating, review count, recent reviews with sentiment

---

## Location Format

Always use full location strings:
- `"City,State,United States"` — e.g., `"Seattle,Washington,United States"`
- `"United States"` — for country-wide data
- Get all locations: `GET /v3/serp/google/locations`

## Response Structure

Every response:
```json
{
  "status_code": 20000,
  "cost": 0.002,
  "tasks": [{
    "status_code": 20100,
    "result": [{ /* data */ }]
  }]
}
```
Check `tasks[0].status_code` — 20100 = success. Check `tasks[0].result` for data.

## Rules
- **Always tell the client the cost** before running expensive queries
- **Batch keywords** — never send 50 individual search volume requests when you can send 1 with 50 keywords
- **Use Labs endpoints** for research — they're 60-70% cheaper than live SERP
- **Cache results mentally** — if you already queried something this session, don't query it again
- **Present data clearly** — tables, sorted by relevance/opportunity, with actionable insights
- **Combine with other skills** — feed keyword data into the marketing skill, use GMB data with customer-comms
