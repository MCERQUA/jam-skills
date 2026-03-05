---
name: local-seo
description: When the user wants to optimize for local search, Google Business Profile, local pack rankings, citations, or local visibility. Also use when the user mentions "local SEO," "Google Business Profile," "GBP," "map pack," "local pack," "NAP," "citations," "local rankings," "near me keywords," "service area," "local search," "Google Maps ranking," "Bing Places," "Apple Business Connect," "local link building," "why am I not in the map pack," or "local visibility." Use this for any local business wanting to rank in their geographic area. For review-specific strategies, see review-management. For building city/service pages at scale, see service-area-pages. For general SEO audits, see seo-audit.
metadata:
  version: 1.0.0
---

# Local SEO

You are an expert in local search engine optimization. Your goal is to help local service companies, insurance agents, and brick-and-mortar businesses rank in the local pack, Google Maps, and organic search for geographic queries.

## Initial Assessment

**Check for product marketing context first:**
If `.agents/product-marketing-context.md` exists (or `.claude/product-marketing-context.md` in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Before optimizing, understand:

1. **Business Type**
   - Storefront (physical location customers visit) or Service Area Business (SAB)?
   - Single location or multi-location?
   - What services do you offer?

2. **Current State**
   - Do you have a Google Business Profile? Is it verified?
   - Current star rating and review count?
   - Do you know which keywords you want to rank for?

3. **Competitive Landscape**
   - Who ranks in the map pack for your target keywords?
   - How many reviews do top competitors have?
   - What cities/areas do you serve?

---

## Core Principles

### 1. NAP Consistency Is Foundational
Name, Address, Phone number must be **identical** everywhere — your website, GBP, every directory, every citation. Even small differences ("St" vs "Street", "LLC" vs no "LLC") dilute trust. Fix this before doing anything else.

### 2. Google Business Profile Is Your Local Homepage
For local businesses, GBP drives more conversions than your website. Treat it accordingly — optimize it, post to it, respond to reviews on it, upload photos to it weekly.

### 3. Reviews Are the Strongest Differentiator
Review velocity (how fast you get new reviews) matters more than total count. A business with 90 reviews getting 15/month outperforms one with 200 reviews that stopped growing 2 years ago.

### 4. Local Relevance Signals Compound
Google's local algorithm weighs "local relevance" heavily. Links from local businesses, citations on local directories, content mentioning local landmarks — these compound when done consistently.

### 5. Target Buyers, Not Browsers
For local businesses: target "[service] + [city]" keywords, not "how to" keywords. You want customers ready to hire, not DIY researchers.

---

## Google Business Profile Optimization

### Categories

**Primary category** is the single most important GBP ranking factor.

- Set primary category to your main service (e.g., "Plumber" not "Plumbing Service")
- Add all relevant secondary categories
- Audit competitor categories: search your target keywords on Google Maps, check what categories top-ranking competitors use
- If competitors ranking above you have a category you don't, add it

**Category audit method:**
Search "[service] in [city]" on Google Maps for your top 3 keywords. For each map pack result, note their primary + secondary categories. Compare against yours. Add any relevant categories you're missing.

### Photos

Businesses with photos get 42% more direction requests and 35% more website clicks (Google data).

**Photo strategy:**
- Upload at least 1 new photo per week (consistency > volume)
- Types that matter: before/after work, team on job sites, trucks in neighborhoods you serve, completed installations, equipment close-ups
- NO stock photos — Google can detect them and they hurt trust
- Geo-tag photos with service area locations when possible

**Photo audit:** Count your photos vs top 3 competitors. Note upload recency. Build an 8-week upload plan with specific photo types per week.

### Posts

- Post weekly with keyword + location in every update
- Use posts for: offers, updates, events, service highlights
- Include a CTA (call, learn more, book) in every post
- Posts expire after 7 days — consistency matters

### Products/Services Section

- Fill out the Products section even if you're a service business
- Each product/service entry = additional keyword opportunity
- Add descriptions with target keywords naturally included

### Other Profile Optimization

- Business description: include primary keywords and all service areas
- Q&A: seed your own Q&A with common customer questions (and answers)
- Attributes: fill out every applicable attribute
- Service area: for SABs, list specific cities/neighborhoods (Google no longer allows entire states)
- Business hours: keep accurate — "business is open at time of search" is now a top-5 local ranking factor (Whitespark 2026)

---

## Citation Building & NAP Cleanup

### Priority Directory List (in order of authority)

**Tier 1 — Must Have:**
1. Google Business Profile
2. Bing Places
3. Apple Business Connect
4. Yelp
5. Facebook Business Page
6. BBB (Better Business Bureau)

**Tier 2 — High Value:**
7. Yellow Pages / YP.com
8. Angi (formerly Angie's List)
9. HomeAdvisor (now part of Angi)
10. Nextdoor Business
11. Local Chamber of Commerce
12. Industry-specific directories

**Tier 3 — Supporting:**
13. Manta
14. Hotfrog
15. Foursquare
16. CitySearch
17. MapQuest
18. Superpages

### NAP Audit Process

1. Search "[business name] + [city]" on Google
2. Check the first 10 pages of results for every directory listing
3. For each listing, log: directory name, URL, name as shown, address as shown, phone as shown, website URL
4. Compare every listing against your canonical NAP
5. Flag ANY differences — even "St" vs "Street" or missing suite numbers
6. Sort by authority (Tier 1 first) and fix from top down

**Canonical NAP format** — pick one and use it everywhere:
```
Business Name LLC           (or whatever your legal/marketing name is)
123 Main Street, Suite 100  (full street name, no abbreviations)
Phoenix, AZ 85001
(602) 555-1234              (consistent format with area code)
```

### Citation Building for New Businesses

1. Start with Tier 1 directories — claim and verify all
2. Add Tier 2 within first month
3. Build 5-10 new citations per month until you reach 50+
4. Include the same business description, categories, and photos across all

---

## Local Link Building

### Local Link Network Strategy

The highest-ROI local link building approach: build a network of partner businesses in your city.

**Target list — search Google Maps for your city + each complementary trade:**
- For home services: roofer, HVAC, plumber, electrician, painter, landscaper, pest control, garage door, concrete, cleaning
- For insurance: mortgage brokers, real estate agents, auto dealers, financial advisors, CPAs
- For any local business: other non-competing businesses serving the same customer base

**Qualification criteria (check before outreach):**
- Domain Authority/Rating 15+ (gold if 30+)
- 50+ referring domains (their site has trust equity to pass)
- 60+ indexed pages (topical authority)

**Outreach script:**
"Hey [Name], I run [Business] here in [City]. I'm putting together a trusted local partners page — a list of the best [trades] in [City] that we recommend to our customers. Your company stood out and I'd love to feature you. No cost, no catch. If you're interested, I'll send the draft. And if you ever want to do something similar, happy to help you set it up too."

**Build the partner page right:**
- URL: `/trusted-local-partners` or `/recommended-contractors`
- Title: "Trusted [Service] Pros in [City] We Recommend"
- For each partner: business name (linked, dofollow), 2-3 sentences about what they do and why you recommend them, their service area
- Keep total outbound links to 5-8 per page (fewer links = more equity per link)
- Link TO this page from: homepage, about page, 2-3 service pages contextually, footer

**Get partners to reciprocate:**
- Send a pre-written blurb about YOUR business they can copy-paste onto their partner page
- Record a 3-min Loom showing them how to set up their own partners page
- 70-80% follow-through rate when you remove all friction

**Track monthly:**
| Partner | Their DA | Page URL | Your Link Live? | Anchor Text | Date Added | Status |
Check: links still live, still dofollow, partner page still indexed, their DA hasn't tanked.

### Other Local Link Sources

- Local news coverage (sponsor events, provide expert quotes)
- Chamber of Commerce membership
- Local charity sponsorships
- School program sponsorships
- Community event sponsorships
- Local business awards
- Guest posts on local blogs
- Supplier/vendor pages

### Link Building Rules

- 80-90% of links should point to your homepage
- Use branded anchor text (safest and most effective)
- Quality over quantity — 10 local DA 20+ links beat 100 random directory links
- Every link should be from a real website with real traffic

---

## Local Keyword Strategy

### Keyword Patterns

| Pattern | Example | Intent |
|---------|---------|--------|
| [service] [city] | "plumber phoenix" | High — ready to hire |
| [service] near me | "plumber near me" | High — immediate need |
| [service] [neighborhood] | "plumber arcadia" | High — very specific |
| [emergency/24hr] [service] [city] | "emergency plumber phoenix" | Urgent — highest intent |
| best [service] [city] | "best plumber phoenix" | Comparison shopping |
| [service] [city] reviews | "phoenix plumber reviews" | Research phase |
| [service] [city] cost | "plumber cost phoenix" | Price shopping |

### Keyword Research Process

1. List all your services
2. List all cities/neighborhoods you serve
3. Create the matrix: every service x every location
4. Check search volume for top combinations
5. Prioritize: start with highest-volume city + highest-revenue service
6. Build pages for priority combos first (see service-area-pages skill)

### On-Page Rules for Local Pages

- H1 must include keyword AND city: "Plumber in Phoenix, AZ"
- URL should be descriptive: `/plumbing-services-phoenix/`
- Address in the footer of every page
- Phone number visible without scrolling
- Front-load keyword in meta title
- Link GBP to your location page (not homepage) for each city

---

## Multi-Location Strategy

### Separate GBP Per Location
- Each physical location needs its own verified GBP
- Each GBP links to that location's specific page on your website
- Maintain unique photos, posts, and responses per location

### Location Pages
- Every location needs a dedicated page (see service-area-pages skill)
- Each page must have unique content — not just city name swapped
- Include: local team, local testimonials, area-specific services, local landmarks
- See the service-area-pages skill for full page template

### Service Area Businesses (SABs)
- No address shown on GBP (just service area)
- List specific cities/neighborhoods as your service area
- Google no longer allows entire states — list the metro area cities individually
- Still need location pages for every city you serve

---

## Monitoring & Reporting

### Weekly
- Respond to all reviews within 24 hours
- Upload 1+ new GBP photo
- Post 1 GBP update
- Check for new 404 errors

### Monthly
- Track local pack rankings for target keywords
- Monitor review velocity (reviews per month)
- Check citation accuracy (spot check 5 directories)
- Track phone calls from GBP and website
- Monitor direction requests
- Check that partner links are still live

### Quarterly
- Full NAP audit across all citations
- Competitor review and category audit
- Content gap analysis (which service+city pages are missing)
- Backlink gap analysis vs top 3 competitors
- GBP photo count and recency vs competitors

---

## Output Format

### Local SEO Audit
1. **NAP Consistency Score** — % of citations with correct NAP
2. **GBP Optimization Score** — categories, photos, posts, reviews, description
3. **Citation Coverage** — which directories you're on vs. should be
4. **Local Rankings** — current positions for target keywords
5. **Competitor Gap** — where competitors outperform you and why
6. **Priority Action Plan** — ordered by impact

### Execution Plan
- Week 1: Citation audit + review strategy (foundations)
- Week 2: Service area page gap analysis + GBP category audit
- Week 3: Photo audit + backlink gap analysis
- Week 4+: Execute — build pages, fix citations, upload photos, outreach

---

## References

- [Local Link Building Guide](references/local-link-building.md): Complete partner network strategy with outreach scripts, page templates, and tracking
- [GBP Optimization Checklist](references/gbp-checklist.md): Full Google Business Profile audit checklist
- [Citation Directory List](references/citation-directories.md): Complete directory list by industry with submission guides

---

## Task-Specific Questions

1. Are you a storefront or service area business?
2. Is your Google Business Profile claimed and verified?
3. How many reviews do you have vs. your top competitor?
4. How many cities/areas do you serve?
5. Have you done a NAP audit before?
6. Who are your top 3 local competitors?

---

## Related Skills

- **review-management**: For review solicitation, response templates, and reputation monitoring
- **service-area-pages**: For building city + service landing pages
- **schema-markup**: For LocalBusiness structured data
- **seo-audit**: For broader technical SEO issues
- **programmatic-seo**: For location pages at scale (this skill adds local-specific depth)
- **site-architecture**: For URL structure and internal linking
