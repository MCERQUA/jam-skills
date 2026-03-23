---
name: web-search-guidelines
description: Rules and rate limits for web search tools. ALWAYS follow these guidelines when performing any web research to avoid hitting API rate limits and wasting credits.
metadata: {"openclaw": {"autoLoad": true}}
---

# Web Search Guidelines

**ALWAYS follow these rules when doing web research. Rate limits are real — hitting them breaks your session and wastes the user's money.**

---

## Available Search Tools (Priority Order)

You have multiple search tools. Use them in this order to spread load and avoid limits:

### 1. `web_search` (OpenClaw Built-in) — PRIMARY
- **What:** Searches via Brave Search API (auto-detected from env)
- **Limit:** ~1,000 searches/month (free tier), 50 requests/second
- **Cost:** $0.005/search after free tier
- **Use for:** General web queries, current information, fact-checking
- **Parameters:** `query`, `count` (1-10), `country`, `language`, `freshness` (day/week/month/year)

### 2. `web_fetch` (OpenClaw Built-in) — FOR READING PAGES
- **What:** HTTP GET + HTML-to-markdown extraction
- **Limit:** No API cost — just HTTP requests
- **Cache:** 15 minutes (same URL won't re-fetch)
- **Use for:** Reading specific URLs, extracting article content, checking competitor pages
- **Parameters:** `url`, `extractMode` (markdown/text), `maxChars`

### 3. Social Research Scripts — FREE, UNLIMITED
- **What:** Reddit's public JSON API (no authentication needed)
- **Limit:** None (public API, reasonable use)
- **Cost:** $0.00
- **Scripts:**
  - `python3 /mnt/shared-skills/social-research/scripts/search_posts.py "query"` — search Reddit
  - `python3 /mnt/shared-skills/social-research/scripts/get_posts.py "subreddit"` — browse subreddit
  - `python3 /mnt/shared-skills/social-research/scripts/get_post.py "url"` — full post + comments
- **Use for:** Customer sentiment, competitor mentions, market research, content ideas, objection discovery

### 4. Serper (Google SERP) — SECONDARY SEARCH, AUTO-FALLBACK
- **What:** Direct Google Search results (organic, PAA, knowledge graph, places, maps, news, images, scholar)
- **Limit:** ~2,500 free searches total (one-time, NOT monthly), then $0.001/search
- **Cost:** $0.001/search (5x cheaper than Brave)
- **Use for:** When web_search hits limits, Google-specific SERP data (PAA, knowledge graph), local business research, SEO rankings
- **RULE:** Use AFTER web_search, not instead of it. Max 5 Serper calls per task unless doing dedicated research.
- **Endpoints:** web, images, news, places, maps, videos, shopping, scholar, autocomplete

### 5. Direct HTTP via curl/Python — FALLBACK
- **What:** Raw HTTP requests when other tools fail
- **Limit:** None (just standard HTTP)
- **Use for:** APIs with no wrapper, sites that block web_fetch, custom scraping

---

## Rate Limit Rules

### Hard Limits — NEVER Exceed
| Tool | Max Per Minute | Max Per Hour | Max Per Day |
|------|---------------|-------------|-------------|
| `web_search` (Brave) | 10 | 50 | 200 |
| Serper (Google) | 10 | 50 | 100 (budget: ~2,500 total free) |
| `web_fetch` | 20 | 100 | No limit |
| Social Research | 10 | 60 | No limit |

### Burst Rules
- **NEVER fire more than 3 searches in rapid succession** — space them out
- **NEVER search the same query twice** — check if you already have the answer
- **NEVER search for information you already know** — use your training knowledge first
- **NEVER do exploratory "let me see what comes up" searches** — have a specific question

### What Happens When You Hit a Limit
- `web_search` returns an error or empty results
- The session may stall waiting for the timeout
- Credits are consumed even on rate-limited requests
- **Recovery:** Wait 60 seconds, then try a DIFFERENT tool (not the same one)

---

## Search Strategy: The Funnel Approach

When doing research, work from broad to specific and minimize total searches:

### Phase 1: Use What You Know (0 searches)
- Start with your training knowledge — you know a LOT
- Draft an outline/answer FIRST, then identify specific gaps

### Phase 2: Targeted Searches (1-3 searches)
- Search ONLY for the specific gaps you identified
- Use precise, specific queries — not broad exploratory ones
- One good query beats five vague ones

### Phase 3: Deep Dive (web_fetch specific URLs)
- Use `web_fetch` to read specific pages from search results
- web_fetch is free — use it to extract detail from URLs you found

### Phase 4: Social Proof (social research scripts)
- Use Reddit search for customer perspectives, reviews, complaints
- FREE and unlimited — use liberally for market research

### Phase 5: Serper (ONLY if explicitly requested)
- Google SERP data, PAA questions, competitor positions
- Requires user to explicitly ask for it

---

## Multi-Tool Distribution Examples

### Example: Research a competitor
```
GOOD (4 tools, minimal searches):
1. web_search: "CompetitorName reviews pricing" (1 search)
2. web_fetch: read their homepage + pricing page (2 fetches, free)
3. social-research: search Reddit for "CompetitorName" (free)
4. Training knowledge for industry context (free)

BAD (all searches):
1. web_search: "CompetitorName"
2. web_search: "CompetitorName pricing"
3. web_search: "CompetitorName reviews"
4. web_search: "CompetitorName vs alternatives"
5. web_search: "CompetitorName problems"
= 5 searches wasted, could have been 1 search + free tools
```

### Example: Write a blog article
```
GOOD:
1. Training knowledge: draft the article structure
2. web_search: 1-2 searches for current stats/facts you need to verify
3. web_fetch: read 2-3 authoritative sources for quotes/data
4. social-research: search Reddit for real user questions on the topic

BAD:
1. web_search: "topic overview"
2. web_search: "topic statistics 2026"
3. web_search: "topic best practices"
4. web_search: "topic examples"
5. web_search: "topic FAQ"
= 5 searches for what your training + 1 search + free tools could cover
```

### Example: Local SEO keyword research
```
GOOD:
1. Training knowledge: generate seed keyword list from industry knowledge
2. web_search: "service + city" (1-2 searches to verify local landscape)
3. social-research: Reddit search for how people talk about the service
4. ONLY IF USER ASKS: serper autocomplete for keyword expansion

BAD:
1. web_search: "keyword 1"
2. web_search: "keyword 2"
... 20 more searches
= Budget blown in one task
```

---

## Caching & Deduplication Rules

1. **Before any search, ask:** "Do I already have this information from a previous search or my training?"
2. **web_fetch cache is 15 minutes** — don't re-fetch a URL you just read
3. **web_search cache is 15 minutes** — identical queries return cached results (but still count toward limits if the cache expired)
4. **Save search results** — when doing multi-step research, save findings to a file so you don't need to re-search
5. **Combine queries** — "spray foam insulation cost Phoenix AZ" is better than separate searches for "spray foam insulation", "spray foam cost", "insulation Phoenix"

---

## When web_search Fails or Returns Empty

1. **DON'T retry the same query** — it will fail again
2. **Try a different tool:**
   - `web_fetch` a known authoritative URL directly
   - Social research scripts for user-generated content
   - `curl` to a specific API endpoint
3. **Rephrase the query** — shorter, more specific, different terms
4. **Wait 60 seconds** if you suspect rate limiting, then try ONCE more
5. **Fall back to training knowledge** and tell the user what you found vs what you couldn't verify

---

## Budget Awareness

- **Each web_search costs ~$0.005** — that's $1 per 200 searches
- **web_fetch is free** — use it liberally for reading known URLs
- **Social research is free** — use it liberally for market/customer research
- A single research task should use **no more than 5-10 web_searches**
- A full website research project (8 phases) should use **no more than 30-50 total web_searches**
- If you're approaching 10 searches in one task, STOP and reassess your approach
