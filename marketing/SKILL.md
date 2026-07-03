---
name: marketing
description: "Marketing skill BUNDLE for local service businesses — routes to sub-skills for SEO content, copywriting, landing pages, conversion optimization, email campaigns, content strategy, social media, ads. TRIGGER on marketing strategy/campaign asks. For raw SEO data (keywords, SERPs, backlinks) → dataforseo; for a client brand report → online-brand-report."
metadata:
  version: 2.1.0
  source: coreyhaines31/marketingskills (MIT) + custom local business extensions
---

# Marketing Skills Bundle

You have access to 25 marketing skills optimized for local service companies and small businesses. Route to the appropriate skill based on the user's request.

## Skill Router

| Task | Skill | Trigger Phrases |
|------|-------|-----------------|
| Set up client context | product-marketing-context | "set up context", "new client", "positioning", "ICP" |
| SEO audit | seo-audit | "SEO audit", "why am I not ranking", "technical SEO" |
| Location/service pages at scale | programmatic-seo | "programmatic SEO", "pages at scale", "template pages" |
| Structured data / rich results | schema-markup | "schema", "JSON-LD", "rich snippets", "structured data" |
| AI search optimization | ai-seo | "AI search", "ChatGPT ranking", "AI Overviews" |
| Landing page conversion | page-cro | "conversion rate", "landing page", "CRO" |
| Write web copy | copywriting | "write copy", "headline", "value prop" |
| Edit existing copy | copy-editing | "edit copy", "improve copy", "rewrite" |
| Lead form optimization | form-cro | "form optimization", "lead form", "quote form" |
| Site structure & navigation | site-architecture | "site structure", "navigation", "URL structure" |
| Competitor comparison pages | competitor-alternatives | "vs page", "competitor", "why choose us" |
| Analytics & tracking setup | analytics-tracking | "GA4", "GTM", "analytics", "tracking" |
| Content planning | content-strategy | "content plan", "blog strategy", "content calendar" |
| Social media content | social-content | "social media", "social post", "Instagram", "Facebook" |
| Outreach emails | cold-email | "cold email", "outreach", "prospecting" |
| Email marketing sequences | email-sequence | "email sequence", "drip campaign", "nurture" |
| Growth ideas | marketing-ideas | "marketing ideas", "growth ideas", "what should I try" |
| Persuasion frameworks | marketing-psychology | "persuasion", "psychology", "behavioral" |
| Ad creative | ad-creative | "ad creative", "ad design", "banner" |
| PPC campaigns | paid-ads | "Google Ads", "PPC", "paid search", "Facebook ads" |
| A/B test design | ab-test-setup | "A/B test", "split test", "experiment" |
| **Local SEO** | **local-seo** | "local SEO", "Google Business Profile", "GBP", "map pack", "citations", "NAP", "local rankings", "near me" |
| **Reviews & Reputation** | **review-management** | "reviews", "reputation", "star rating", "review response", "get more reviews", "review request" |
| **Service Area Pages** | **service-area-pages** | "service area pages", "city pages", "location pages", "[service] in [city]", "neighborhood pages" |
| **SMS Marketing** | **sms-marketing** | "SMS marketing", "text marketing", "text message campaigns", "TCPA", "10DLC", "review request text", "appointment reminder text" |

## Routing Guidance

**"location pages" / "city pages" / "service area pages":**
- If the user wants to build pages for a local service company → use **service-area-pages** (local-specific: unique content, local data, service area schema)
- If the user wants generic pages at scale from data → use **programmatic-seo** (general: template engines, data sources, scaling)

**"local SEO" / "GBP" / "citations":**
- Use **local-seo** for the overall strategy (GBP, citations, NAP, local links, keyword strategy)
- Use **review-management** if the focus is specifically on getting/managing reviews
- Use **service-area-pages** if the focus is specifically on building city pages

**"SMS" / "text message" / "appointment reminders":**
- Use **sms-marketing** for text message campaigns, review request texts, appointment reminders, TCPA compliance
- Cross-reference **review-management** if focus is getting reviews via text
- Cross-reference **customer-followup** if focus is post-service follow-up sequences

## Data Tools (top-level skills — pair with the strategy skills above)

These live OUTSIDE this bundle but power its skills with real data:

| Need | Skill | Notes |
|------|-------|-------|
| Keyword/SERP/backlink/local/AI-visibility DATA | **dataforseo** | The paid system of record — every call auto-saves to the tenant SEO DB. See its "Deep Endpoint Recipes". |
| Full client SEO report + build plan | **online-brand-report** | THE brand-report engine (real data, scored A–F) — never hand-write a report |
| Ongoing SEO dashboard for the client | **seo-platform** | 12-view canvas dashboard; read accumulated data FREE |
| Google-specific quick lookups (PAA, knowledge graph, local pack) | **serper-search** | ~$0.001/query secondary lane |
| Free backlink discovery / competitor link gap | **cc-backlinks** | $0, Common Crawl graph; pair with free Ahrefs DR |
| /llms.txt AI-discovery file | **llms-txt-writer** | Pairs with ai-seo for GEO work |
| Free domain authority (Ahrefs DR) | — | `curl -s "https://api.ahrefs.com/v3/public/domain-rating-free?target=<domain>&output=json"` — $0, no key |

**Typical project flows:**
- *Local service client onboarding:* online-brand-report → local-seo → service-area-pages → schema-markup → page-cro → analytics-tracking
- *AI visibility push:* ai-seo (+ dataforseo AI Mode/LLM-mention recipes) → llms-txt-writer → schema-markup → content-strategy
- *Link building:* cc-backlinks (free gap) → dataforseo backlinks (depth) → local-seo partner network


## Workflow

1. **Always check for product-marketing-context first** — if `.agents/product-marketing-context.md` exists, read it before any task
2. **Route to the specific skill** — read its SKILL.md for detailed instructions
3. **Check references/** — each skill has supporting docs with templates, examples, and frameworks
4. **Cross-reference related skills** — each skill lists related skills at the bottom
