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
- **Batch keywords** — up to 1,000 per Google Ads request ($0.09 total, not per keyword)
- **Use Labs** for bulk research ($0.012/task) instead of live SERP ($0.002/query)
- **Use Standard mode** (async) when client isn't waiting for instant results
- **Limit depth to 10** unless client specifically needs deeper results
- **Never run exploratory queries** — know what you're looking for before calling

**Pricing below reflects DataForSEO's 2026-07-01 rate update** (most APIs +~20%: Backlinks, Labs, Domain Analytics, Content Analysis +20%; OnPage +18%; Business Data +16%; Merchant +50%). SERP and Search Intent were NOT in that update — unchanged.

**Full access enabled — no plan blocker.** We have full DataForSEO access including the **Backlinks API** and **AI-mention / Google AI Mode SERP** endpoints. There is no longer any monthly-upgrade/activation gate on backlinks or AI data — call them directly.

| API | Cost/task | Best for |
|-----|-----------|----------|
| SERP Live | $0.002 | Checking current rankings for specific keywords (unchanged) |
| Keywords Data | $0.09 | Bulk search volume (up to 1,000 keywords) |
| Labs | $0.012 | Keyword research, competitor analysis, difficulty scores |
| Search Intent | $0.001 | Classifying keyword intent (unchanged) |
| OnPage (basic) | $0.00015/page | Site audits |
| Business Data | $0.012 | GMB profiles, Google reviews, business listings |
| Backlinks | $0.024 | Link profiles — **full access, no activation needed** |
| AI Mode / AI Mentions | $0.002+ | Google AI Mode SERP + AI-overview brand mentions — **fully enabled** |

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

### Free Domain Rating (Ahrefs — no API key, no cost)
Ahrefs' Domain Rating (DR) is now exposed as a free public endpoint — no auth, no DataForSEO cost. Use it to size up domain authority (0–100 log scale) alongside the DataForSEO backlink profile.
```bash
curl -s "https://api.ahrefs.com/v3/public/domain-rating-free?target=DOMAIN"
```
**Returns:** `{"domain_rating": {"domain_rating": 34.0}}` — DR on a 0–100 log scale.
**Verified live 2026-06-10:** ahrefs.com → 91, CCA → 34, jam-bot.com → 0. Pair with the Backlinks API below for a fuller authority picture (DR = headline number; DataForSEO = the link detail).

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
    "result": [{ "items": [...] }]
  }]
}
```
Check `tasks[0].status_code` — 20100 = success. Data at `tasks[0].result[0].items`.

**Labs endpoints return FLAT item structure** (NOT nested under `keyword_data`):
```json
{
  "keyword": "contractor insurance",
  "keyword_info": { "search_volume": 8100, "cpc": 83.85, "competition": 0.19, "competition_level": "LOW" },
  "keyword_properties": { "keyword_difficulty": 42 },
  "search_intent_info": { "main_intent": "commercial" }
}
```
Access fields directly: `item.keyword`, `item.keyword_info.search_volume`, `item.keyword_properties.keyword_difficulty`.
Do NOT use `item.keyword_data.keyword` — that field does not exist.

---

## SEO Data Persistence

**All queries are automatically saved** to a persistent database via the social dashboard API. Every dollar spent produces permanently stored data that contributes to the client's ongoing SEO campaign.

### Saved Data Endpoints (via social dashboard)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/social-api/api/seo/dashboard?tenant=X` | GET | Aggregated campaign stats, tool breakdown, recent queries |
| `/social-api/api/seo/history?tenant=X&tool=Y` | GET | Query history with filters |
| `/social-api/api/seo/history/:id?tenant=X` | GET | Full saved result with all items |
| `/social-api/api/seo/keyword-tracker?tenant=X` | GET | Deduplicated keyword database across all queries |

### Canvas Pages

- **SEO Tools** (`seo-tools`) — run new queries (all auto-save)
- **SEO Campaign** (`seo-dashboard`) — persistent dashboard showing accumulated data

When the client asks "show me my SEO data" or "what keywords are we tracking":
```
[CANVAS_URL:https://<user>.jam-bot.com/pages/seo-dashboard.html]
```

When the client wants to run a new query:
```
[CANVAS_URL:https://<user>.jam-bot.com/pages/seo-tools.html]
```

---

## Free Authority Signal: Ahrefs DR

For quick domain authority checks without API cost, use the free Ahrefs DR endpoint via `/mnt/system/base/scripts/ahrefs_dr.py`.

**DR 0-100 logarithmic scale** — measures domain authority based on backlink quantity and quality. No API key, no DataForSEO cost, no rate limit beyond courtesy delays.

### Use for:
- Qualifying link prospects before investing in outreach
- Enriching backlink reports with headline authority numbers
- Setting client benchmarks ("your DR is X, top competitor is Y")
- Tiering niche linker databases (tier1/tier2/tier3 by DR)

### DR tier thresholds:
| DR | Tier | What it means |
|----|------|---------------|
| 50+ | Tier 1 | Premium — high equity, harder to earn |
| 30–49 | Tier 2 | Strong — worth active pursuit |
| <30 | Tier 3 | Local/niche — still valuable for local SEO |

### Quick usage:
```bash
# Single domain
python3 /mnt/system/base/scripts/ahrefs_dr.py example.com

# In Python (stdlib only, no pip deps)
import sys; sys.path.insert(0, '/mnt/system/base/scripts')
from ahrefs_dr import get_dr, get_dr_bulk
dr = get_dr("example.com")              # → float e.g. 34.0
scores = get_dr_bulk(["a.com","b.com"]) # → {"a.com": 12.0, "b.com": 67.0}

# Raw curl
curl -s "https://api.ahrefs.com/v3/public/domain-rating-free?target=example.com&output=json"
# → {"domain_rating": {"domain_rating": 34.0}}
```

**Pairs with DataForSEO for comprehensive SEO reporting:** DR = headline authority number; DataForSEO Backlinks API = the detailed link profile, anchor text, and referring page data.

---

## Deep Endpoint Recipes — the high-value calls we're NOT using yet

The pipeline + dashboard currently use ~25 of the ~445 v3 endpoints. These are the proven-valuable ones we already pay access for. Costs are approximate (post 2026-07-01 rates); verify with `GET /v3/appendix/user_data` before bulk runs.

### Domain Rank Overview — ONE cheap call for the whole authority/traffic headline
Replaces `ranked_keywords limit:1` hacks. Returns organic + paid metrics in one shot.
```bash
bash dataforseo.sh "dataforseo_labs/google/domain_rank_overview/live" \
  '[{"target":"clientsite.com","location_name":"United States","language_name":"English"}]'
```
**Returns:** `items[0].metrics.organic` = `{pos_1, pos_2_3, pos_4_10, pos_11_20, ..., count, etv, estimated_paid_traffic_cost}` + same for `paid`. ~$0.012. **Use for:** dashboard KPI headers, monthly client snapshots, competitor scorecards (one call per domain).

### Historical Rank Overview — the REAL trend line (up to 5 years monthly)
The only way to show "your SEO is improving" without waiting months to accumulate snapshots.
```bash
bash dataforseo.sh "dataforseo_labs/google/historical_rank_overview/live" \
  '[{"target":"clientsite.com","location_name":"United States","language_name":"English","date_from":"2025-06-01"}]'
```
**Returns:** monthly `items[]` each with `metrics.organic.{count,etv,pos_1,pos_2_3,...}`. **Cost: ~$0.12 + ~$0.001/row — EXPENSIVE, run once per domain onboarding, then monthly.** The single highest-impact missing chart in both the brand report and the dashboard Position view.

### Keyword Ideas + Related Keywords — the two research modes we claim but never call
```bash
# Broader brainstorm (category-level expansion, multiple seeds allowed)
bash dataforseo.sh "dataforseo_labs/google/keyword_ideas/live" \
  '[{"keywords":["spray foam insulation","attic insulation"],"location_name":"United States","language_name":"English","limit":200}]'

# Depth-N semantic graph (what Google's "searches related to" builds from)
bash dataforseo.sh "dataforseo_labs/google/related_keywords/live" \
  '[{"keyword":"spray foam insulation","location_name":"United States","language_name":"English","depth":2,"limit":100}]'
```
**Gotcha:** `related_keywords` items nest under `keyword_data` (`item.keyword_data.keyword`) — unlike suggestions/ideas which are flat. `depth:2` ≈ 4^2=16 seed expansions; depth 3+ explodes cost. ~$0.012 each.

### Keywords For Site — seed research from a URL instead of a guess
```bash
bash dataforseo.sh "dataforseo_labs/google/keywords_for_site/live" \
  '[{"target":"competitor.com","location_name":"United States","language_name":"English","limit":300}]'
```
What a domain COULD rank for based on its content (vs `ranked_keywords` = what it DOES rank for). Run both on a competitor; the difference = their unrealized strategy. ~$0.012.

### SERP Competitors — who actually wins the keywords you care about
```bash
bash dataforseo.sh "dataforseo_labs/google/serp_competitors/live" \
  '[{"keywords":["roof repair phoenix","roof replacement phoenix"],"location_name":"United States","language_name":"English","limit":20}]'
```
**Returns:** `items[]` = `{domain, avg_position, median_position, rating, etv, keywords_count}` ranked by visibility for YOUR keyword set — finds the real SERP-level rivals that `competitors_domain` (profile-similarity) misses. ~$0.012.

### Backlinks you're missing (all ~$0.024 base)
```bash
# Growth over time — the backlink trend chart nobody can draw today
bash dataforseo.sh "backlinks/timeseries_summary/live" \
  '[{"target":"clientsite.com","date_from":"2025-06-01","group_range":"month"}]'

# New vs lost — churn detection ("you lost 12 links last month")
bash dataforseo.sh "backlinks/timeseries_new_lost_summary/live" \
  '[{"target":"clientsite.com","date_from":"2025-06-01","group_range":"month"}]'

# Toxic-link screening — spam score 0-100 per domain, up to 1000 targets
bash dataforseo.sh "backlinks/bulk_spam_score/live" \
  '[{"targets":["clientsite.com","competitor1.com","competitor2.com"]}]'

# Link gap — who links to BOTH competitors but NOT you (instant outreach list)
bash dataforseo.sh "backlinks/domain_intersection/live" \
  '[{"targets":{"1":"competitor1.com","2":"competitor2.com"},"exclude_targets":["clientsite.com"],"limit":50}]'

# Backlink-profile competitors (similar link profiles = same niche authorities)
bash dataforseo.sh "backlinks/competitors/live" \
  '[{"target":"clientsite.com","limit":10}]'

# Bulk authority compare — rank for up to 1000 domains in ONE call
bash dataforseo.sh "backlinks/bulk_ranks/live" \
  '[{"targets":["clientsite.com","comp1.com","comp2.com","comp3.com"]}]'
```
**`domain_intersection` gotcha:** `targets` is an OBJECT keyed "1","2"… not an array.

### Google AI Mode SERP — what Google's AI search actually says (GEO ground truth)
```bash
bash dataforseo.sh "serp/google/ai_mode/live/advanced" \
  '[{"keyword":"best spray foam insulation company phoenix","location_name":"Phoenix,Arizona,United States","language_name":"English"}]'
```
**Returns:** the AI Mode answer with `references[]` (cited domains/urls). Is the client cited? Are competitors? ~$0.002 — as cheap as a normal SERP. **This is the AI-visibility check for Google specifically; pair with `llm_mentions` for ChatGPT/Claude/Gemini/Perplexity.**

### LLM Mentions suite — brand visibility across AI assistants
```bash
# Where the domain is mentioned across LLM answers
bash dataforseo.sh "ai_optimization/llm_mentions/search/live" \
  '[{"target":[{"domain":"clientsite.com"}],"location_name":"United States","language_name":"English","limit":50}]'

# Top domains LLMs cite for a topic — who owns the AI answer box in your niche
bash dataforseo.sh "ai_optimization/llm_mentions/top_domains/live" \
  '[{"keyword":"spray foam insulation","location_name":"United States","language_name":"English","limit":20}]'

# Aggregated mention metrics (share-of-voice number for reports)
bash dataforseo.sh "ai_optimization/llm_mentions/aggregated_metrics/live" \
  '[{"target":[{"domain":"clientsite.com"}],"location_name":"United States","language_name":"English"}]'

# Ask the actual model and read the answer (per-platform spot check)
bash dataforseo.sh "ai_optimization/chat_gpt/llm_responses/live" \
  '[{"user_prompt":"who is the best spray foam insulation company in phoenix?","model_name":"gpt-4.1-mini","max_output_tokens":500}]'
# same shape: ai_optimization/{claude,gemini,perplexity}/llm_responses/live
```
`llm_responses` is priced per call + model tokens (≈$0.005–0.05 depending on model) — use for monthly spot checks, not loops.

### Google Trends — seasonality the client can SEE
```bash
bash dataforseo.sh "keywords_data/google_trends/explore/live" \
  '[{"keywords":["spray foam insulation"],"location_name":"United States","date_from":"2025-06-01","date_to":"2026-06-01","type":"web"}]'
```
**Returns:** `items[0].data[]` weekly interest values 0-100. Free-tier-cheap (~$0.001-0.005). Perfect for "book insulation jobs before October" seasonal advice and report sparklines.

### Local SEO deep cuts
```bash
# GMB Q&A — unanswered questions = free local content + trust wins
bash dataforseo.sh "business_data/google/questions_and_answers/live" \
  '[{"keyword":"Business Name City State","location_name":"City,State,United States","language_name":"English"}]'

# GMB posts/updates the business has published (async task flow)
bash dataforseo.sh "business_data/google/my_business_updates/task_post" \
  '[{"keyword":"Business Name City State","location_name":"City,State,United States","language_name":"English"}]'

# Competitor density — every business in a category + area, with ratings
bash dataforseo.sh "business_data/business_listings/search/live" \
  '[{"categories":["insulation_contractor"],"location_coordinate":"33.4484,-112.0740,10","limit":50}]'

# Local Finder — full local ranking beyond the 3-pack
bash dataforseo.sh "serp/google/local_finder/live/advanced" \
  '[{"keyword":"spray foam insulation","location_name":"Phoenix,Arizona,United States","language_name":"English","depth":20}]'
```
**`my_business_info` gotcha (hard-won):** the live endpoint accepts `location_name`/`language_name` for SERP-style lookups BUT some param combos return 40501 — when it errors, retry with `location_code` (e.g. 2840 = US) + `language_code:"en"` instead of names.

### OnPage one-shots (no crawl task needed)
```bash
# Instant single-page audit — checks, meta, content stats in one live call
bash dataforseo.sh "on_page/instant_pages" \
  '[{"url":"https://clientsite.com/service-page","enable_javascript":false}]'

# Structured-data extraction — what schema a page ACTUALLY exposes (pairs with /schema-markup skill)
bash dataforseo.sh "on_page/microdata" '[{"id":"<crawl-task-id>","url":"https://clientsite.com/"}]'

# Parsed content (headings, word count, links) for any URL — content brief raw material
bash dataforseo.sh "on_page/content_parsing/live" \
  '[{"url":"https://clientsite.com/blog/post","enable_javascript":false}]'
```
After a full crawl (`on_page/task_post`), also free-to-read: `redirect_chains`, `duplicate_content`, `keyword_density`, `waterfall` — all GET with the task id, already paid for by the crawl.

### Domain intelligence
```bash
# WHOIS + visibility enrichment (age, expiry, registrar + backlink/rank data)
bash dataforseo.sh "domain_analytics/whois/overview/live" \
  '[{"filters":[["domain","=","clientsite.com"]],"limit":1}]'

# Tech stack (CMS, analytics, CDN, frameworks)
bash dataforseo.sh "domain_analytics/technologies/domain_technologies/live" \
  '[{"target":"clientsite.com"}]'
```
**WHOIS gotcha:** takes a `filters` array, NOT a bare `target` param.

### Brand monitoring extras
```bash
# Review-site rating distribution across the web (not just Google)
bash dataforseo.sh "content_analysis/rating_distribution/live" \
  '[{"keyword":"Brand Name","search_mode":"as_is"}]'

# What topics trend in citations of your niche over time
bash dataforseo.sh "content_analysis/category_trends/live" \
  '[{"category_code":10994,"date_from":"2026-01-01"}]'
```

### Recommended adoption order (value ÷ cost)
1. **`domain_rank_overview`** — cheapest full-domain headline; use everywhere.
2. **`serp/google/ai_mode`** — $0.002 GEO ground truth; add to brand report + dashboard AI view.
3. **`backlinks/timeseries_summary` + `timeseries_new_lost_summary`** — unlocks the growth charts both UIs stub today.
4. **`historical_rank_overview`** — once per onboarding + monthly; the proof-of-progress chart.
5. **`bulk_spam_score`** — toxic-link flag in every backlink section.
6. **`backlinks/domain_intersection`** — turnkey link-prospect list (feeds niche-backlinks DB).
7. **`serp_competitors`** — true SERP rivals for the money keywords.
8. **`business_data/google/questions_and_answers`** — local content goldmine, near-free.
9. **`google_trends/explore`** — seasonality visuals.
10. **`llm_mentions` aggregated + `keyword_ideas`/`related_keywords`** — round out AI share-of-voice + research modes.

---

## Rules
- **Always tell the client the cost** before running expensive queries
- **Batch keywords** — never send 50 individual search volume requests when you can send 1 with 50 keywords
- **Use Labs endpoints** for research — they're 60-70% cheaper than live SERP
- **Don't re-query data you already have** — check the keyword tracker first via `/social-api/api/seo/keyword-tracker`
- **Present data clearly** — tables, sorted by relevance/opportunity, with actionable insights
- **Combine with other skills** — feed keyword data into the marketing skill, use GMB data with customer-comms
- **DataForSEO does NOT autocorrect typos** — if a keyword returns null results, check spelling
