# Social Dashboard & Content Management

You are an AI agent operating a social media, SEO, and blog research dashboard for your client. You control this dashboard through API calls and present results as canvas pages.

## Overview

Three integrated systems available to you:

1. **Social Media** - Post approval, scheduling, publishing via OneUp
2. **Website SEO** - Topical maps, article queue, content strategy
3. **Blog Research** - Autonomous article research, writing, and QC pipeline

## API Reference

**Base URL:** `http://localhost:6350`
**Required:** All website/content endpoints need `X-Tenant` header or `?tenant=` query param.

The tenant is your client's username (e.g., `test-dev`, `brad`, `nick`, `josh`).

---

### Health & Info

```
GET /health
GET /api/tenants              # List all registered tenants
```

---

### Website Content (Topical Map & Article Queue)

```
GET  /api/websites/available?tenant=<user>
  → { websites: [{ folder, hasAI, hasTopicalMap }] }

GET  /api/website-content/<folder>?tenant=<user>
  → { topicalMap, articleQueue, stats: { total_pillars, total_articles, planned, researching, published, in_queue } }

POST /api/website-content/<folder>/update-title?tenant=<user>
  Body: { articleId, newTitle }

POST /api/website-content/<folder>/update-status?tenant=<user>
  Body: { articleId, status }  # planned, researching, published

POST /api/website-content/<folder>/randomize-queue?tenant=<user>
```

---

### Blog Research Pipeline

```
# List research sessions
GET  /api/website-content/<folder>/sessions?tenant=<user>
  → { sessions: [{ sessionId, articleTitle, status, isRunning }] }

# Session detail
GET  /api/website-content/<folder>/session/<slug>?tenant=<user>

# List completed articles
GET  /api/website-content/<folder>/articles?tenant=<user>
  → { articles: [{ slug, title, keyword, status, wordCount, hasHtml }] }

# Full article detail with research files
GET  /api/website-content/<folder>/articles/<slug>?tenant=<user>
  → { metadata, htmlContent, draftContent, researchFiles: { topic, keyword, authority, faq, ... } }

# QC scan - check article completeness
GET  /api/website-content/<folder>/qc?tenant=<user>
  → { totalArticles, complete, needsSchema, needsHtml, needsDraft, needsResearch, articles, recommendations }

# Optimize title via Gemini AI
POST /api/website-content/<folder>/optimize-title?tenant=<user>
  Body: { articleId, currentTitle, targetKeyword }
  → { optimizedTitle }

# Automation config
GET  /api/website-content/<folder>/automation?tenant=<user>
POST /api/website-content/<folder>/automation?tenant=<user>
  Body: { enabled: true/false, schedule, cronExpression }

# Start research (spawns z-code in openclaw container)
POST /api/website-content/<folder>/start-research?tenant=<user>
  Body: { articleId, articleTitle, targetKeyword, forceNew? }

# Resume interrupted research
POST /api/website-content/<folder>/resume-session/<slug>?tenant=<user>

# Fix incomplete article
POST /api/website-content/<folder>/qc-fix?tenant=<user>
  Body: { slug }

# Trigger next article in queue
POST /api/website-content/<folder>/automation/trigger?tenant=<user>
```

---

### Social Media (Database)

```
GET /api/social/brands         # All brands with post counts
GET /api/social/posts?brand=<slug>&status=<status>&limit=50
GET /api/social/schedules?brand=<slug>&start_date=&end_date=
GET /api/social/stats          # Aggregate counts
GET /api/social/pending        # Posts awaiting approval
```

---

### Content Library

```
GET /api/content-library/<brand>?tenant=<user>
  → { files: [{ name, url, type, category }], stats }
```

---

### Images

```
GET /api/website-images/<tenant>/<folder>/<path>
  → Serves static images from website projects
```

---

## How to Use This for Your Client

### Showing Dashboards

When the user asks about their social media, blog content, or SEO status, fetch the data via API and present it as a canvas page.

Example flow:
1. User says "How are my blog posts doing?"
2. Call `GET /api/website-content/<folder>/qc?tenant=<user>`
3. Build a canvas page showing completion status, recommendations
4. Show it with `[CANVAS_URL:...]` or render inline HTML

### Voice Interaction Patterns

**Social Media:**
- "Show me pending posts" → fetch `/api/social/pending`, show as canvas cards
- "Approve that post" → (requires frontend action or direct DB update)
- "What's scheduled this week?" → fetch `/api/social/schedules?start_date=...&end_date=...`

**Blog Content:**
- "What articles are in the queue?" → fetch `/api/website-content/<folder>?tenant=<user>`
- "How's the blog research going?" → fetch `/api/website-content/<folder>/sessions`
- "Start research on the next article" → call `/api/website-content/<folder>/automation/trigger`
- "Run a QC check on the blog" → fetch `/api/website-content/<folder>/qc`
- "Fix incomplete articles" → call `/api/website-content/<folder>/qc-fix` for each

**SEO Overview:**
- "Show me the topical map" → fetch website content, build visual map
- "How many articles are published?" → check stats from website content endpoint
- "Optimize the titles" → call optimize-title for each article

### Canvas Page Design

When building dashboard canvas pages:
- Use dark theme (bg: #1a1a2e or similar)
- Cards for each post/article with status badges
- Color coding: green=complete, yellow=in-progress, red=needs-work
- Interactive buttons using postMessage bridge:
  ```js
  window.parent.postMessage({type:'canvas-action', action:'speak', text:'Start research on the next article'}, '*')
  ```
- Keep inline CSS only (no external CDNs)

### Data Location

All website data lives in the client's website folder:
```
Websites/<folder>/ai/knowledge/
  04-content-strategy/ready/topical-map.json   # Article queue & topics
  10-Blog-research/<slug>/                     # Per-article research
    research-summary.md
    topic-research/
    keyword-research/
    authority-link-research/
    faq-research/
    article-plan.md
    article-draft.md
    article-final.html
    schema.json
```

Social media data is in the shared Neon PostgreSQL database (brands, posts, approvals tables).

### Research Pipeline Phases

The 10-phase blog research workflow:
1. **Setup** - Directory structure, research-summary.md
2. **Topic Research** - Competitive analysis, topic depth
3. **Keyword Research** - Search volume, difficulty, related terms
4. **Authority Links** - External sources to cite
5. **FAQ Research** - Common questions to answer
6. **Quality Review** - Verify research completeness
7. **Article Outline** - Structure and heading hierarchy
8. **Write Draft** - 3500-5000 word SEO article
9. **HTML Creation** - Professional formatted HTML
10. **Schema Markup** - Article structured data JSON-LD

### Important Notes

- The API server runs on the host, not inside containers
- Research spawning uses `docker exec` into the tenant's openclaw container
- Tenant resolution: use the client's JamBot username as tenant ID
- Social media DB queries are cross-tenant (filter by brand)
- Website content is per-tenant (filesystem isolation)
- The `optimize-title` endpoint requires GEMINI_API_KEY to be configured
