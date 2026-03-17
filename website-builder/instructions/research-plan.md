# Foundational Website Research — Phase 3

This phase is the FOUNDATION of a quality website. Every word of copy, every design decision, every page structure traces back to what you discover here. Do NOT rush this. Do NOT skip tasks. A well-researched site converts. A poorly-researched site is just another forgettable template.

**Time investment:** 30-60 minutes of focused research work.
**Output:** 20-40 research files across 7 directories.
**Prerequisite:** Business profile completed (Phase 2).

---

## Task 1: Keyword Research

**Goal:** 50-100+ keywords organized by type, intent, and priority.
**Output directory:** `ai/research/02-keyword-research/`

This is NOT "pick 10 keywords and move on." You are building the keyword universe for this business — every term their customers might search for.

### Process:

1. **Start with the business profile.** What services do they offer? What location? What industry?

2. **Search Google for each core service term.** For each search:
   - Note the exact titles of the top 5 results (these are winning keyword patterns)
   - Copy every "People Also Ask" question (these become FAQ content and long-tail targets)
   - Copy every "Related searches" suggestion at the bottom
   - Note any featured snippets (what format? paragraph, list, table?)

3. **Expand with modifiers:**
   - Service + location: "[service] in [city]", "[service] near me"
   - Service + intent: "[service] cost", "[service] reviews", "best [service]"
   - Service + qualifier: "commercial [service]", "residential [service]", "emergency [service]"
   - Problem-based: "how to fix [problem]", "why does [issue] happen"
   - Comparison: "[service A] vs [service B]", "[service] alternatives"

4. **Organize into files:**

**`primary-keywords.md`** — 3-5 highest-value terms:
```markdown
## Primary Keywords

| Keyword | Est. Volume | Intent | Target Page |
|---------|-------------|--------|-------------|
| [keyword] | High | Commercial | Homepage |
| [keyword] | High | Commercial | Services |
```

**`secondary-keywords.md`** — 10-20 specific service/feature terms

**`longtail-keywords.md`** — 15-30 question phrases from PAA and related searches:
```markdown
## Long-Tail Keywords (Questions)

### How-To Questions
1. "How much does [service] cost in [city]?" — FAQ, Blog
2. "How long does [service] take?" — FAQ
3. "How to choose a [service provider]?" — Blog

### Comparison Questions
1. "[Service A] vs [Service B] — which is better?" — Blog

### Problem Questions
1. "Why does [problem] happen?" — Blog
```

**`location-keywords.md`** — Geographic modifiers (if local business):
```markdown
## Location Keywords

### Primary City
- "[service] [city]" — Homepage
- "[service] [city] [state]" — Homepage meta

### Surrounding Areas
- "[service] [nearby city 1]" — Service area page
- "[service] [nearby city 2]" — Service area page
- "[service] [county/region]" — Service area page
```

**`keyword-clusters.md`** — Group all keywords into topic clusters:
```markdown
## Keyword Clusters

### Cluster 1: [Core Service]
- Pillar: [primary keyword]
- Supporting: [keyword], [keyword], [keyword]
- Questions: [question], [question]
- Target content: [pillar page] + [blog posts]

### Cluster 2: [Second Service]
...
```

### Quality standard:
- Minimum 50 keywords total across all files
- Every keyword has a target page or content piece assigned
- PAA questions captured (minimum 10)
- At least 3 distinct keyword clusters identified

---

## Task 2: Competitor Deep Analysis

**Goal:** Understand exactly what the top competitors are doing — their sites, their content, their strengths, their weaknesses.
**Output directory:** `ai/research/03-competitor-analysis/`

This is NOT a surface glance. You are studying these sites like an architect studies buildings.

### Process:

1. **Identify 5-10 competitors.** Sources:
   - Google search for primary keywords — who ranks on page 1?
   - Client-provided competitor URLs
   - Google Maps / local pack results
   - Industry directories

2. **For EACH competitor, create a file in `site-reviews/`:**

```markdown
# Competitor Review: [Business Name]

**URL:** [website URL]
**Google ranking position:** [for primary keyword]

## Site Structure
- **Pages:** [list every page in their navigation]
- **Blog:** [yes/no, how many posts, how recent]
- **Service pages:** [individual or grouped?]

## Homepage Analysis
- **H1:** "[exact headline]"
- **Hero section:** [describe: image/video, CTA text, layout]
- **Sections in order:** [list every section from top to bottom]
  1. Hero — [description]
  2. [Section] — [description]
  3. ...
- **Primary CTA:** "[exact button text]" → [where it goes]
- **Secondary CTAs:** [list]
- **Trust signals:** [badges, ratings, certifications, numbers]
- **Above the fold:** [what's visible before scrolling]

## Visual Design
- **Color scheme:** [primary, secondary, accent colors]
- **Typography:** [heading font, body font, sizes]
- **Photography style:** [stock, custom, illustrations, icons]
- **Overall aesthetic:** [modern/corporate/playful/minimal/premium]
- **Dark or light mode:** [which]
- **Animations:** [any motion, scroll effects, hover states?]
- **Layout style:** [full-width/contained, grid/asymmetric, dense/spacious]

## Content Quality
- **Copy style:** [professional/casual/technical/salesy]
- **Specificity:** [generic or detailed?]
- **Trust elements:** [testimonials, case studies, reviews, awards]
- **FAQ:** [yes/no, how many questions, quality of answers]
- **Social proof:** [review count, Google rating, BBB, certifications]

## SEO Indicators
- **Title tag:** "[exact title]"
- **Meta description:** "[if visible in search results]"
- **H2 structure:** [list main H2s]
- **Structured data:** [any schema markup visible?]
- **Page speed:** [fast/medium/slow]
- **Mobile experience:** [good/poor, responsive?]

## Strengths (What They Do Well)
1. [strength]
2. [strength]

## Weaknesses (What We Can Beat)
1. [weakness/gap]
2. [weakness/gap]

## Specific Things to Learn From
- [specific element or approach worth noting]
```

3. **After reviewing ALL competitors, create `pattern-analysis.md`:**

```markdown
# Competitor Pattern Analysis

## Common Homepage Elements
Every competitor has:
- [element] (X out of Y have this)
- [element]

Most competitors have:
- [element] (X out of Y)

Few competitors have:
- [element] (only X)

## Common CTA Patterns
- Primary CTA: [most common text] (X competitors)
- Secondary CTA: [most common] (X competitors)
- CTA placement: [where: hero, sticky nav, floating, footer]

## Common Section Ordering
Typical homepage flow:
1. [Section] — all competitors
2. [Section] — most competitors
3. ...

## Trust Signal Patterns
Most used trust signals:
1. [signal type] — X competitors
2. [signal type] — X competitors

## Design Trends in This Niche
- Colors: [common palette trends]
- Typography: [common choices]
- Imagery: [what kind of photos/graphics]
- Layout: [common layout patterns]
- Animations: [what motion is used]

## Content Patterns
- Average homepage word count: ~[number]
- FAQ presence: [X of Y competitors]
- Blog presence: [X of Y competitors]
- Testimonial style: [named/anonymous, detailed/brief]

## Price/Value Communication
How competitors communicate pricing:
- [pattern]
```

4. **Create `gaps-opportunities.md`:**

```markdown
# Gaps & Opportunities

## Things NO competitor does well:
1. [gap] — OPPORTUNITY: [how we exploit it]
2. [gap] — OPPORTUNITY: [how we exploit it]

## Things only 1-2 competitors do:
1. [element] — We should: [include/skip and why]

## Content gaps:
1. [topic nobody covers] — We can own this
2. [question nobody answers well]

## Design gaps:
1. [visual weakness across the niche]
2. [UX problem they all share]

## Our differentiation strategy:
Based on all analysis above, we will stand out by:
1. [differentiator]
2. [differentiator]
3. [differentiator]
```

### Quality standard:
- Minimum 5 competitors reviewed with individual files
- Pattern analysis identifies at least 5 common patterns
- At least 3 exploitable gaps identified
- Every competitor's homepage fully documented (sections, CTAs, design)

---

## Task 3: Content Strategy & Page Planning

**Goal:** Map every page of the site with its keywords, sections, content needs, and purpose.
**Output directory:** `ai/research/04-content-strategy/`

### Process:

1. **Create `page-plan.md`** — the master page map:

```markdown
# Website Page Plan

## Pages

| Page | URL | Primary Keyword | Section Count | Priority |
|------|-----|----------------|---------------|----------|
| Homepage | / | [keyword] | 8-12 | Critical |
| About | /about | [keyword] | 5-7 | High |
| Services | /services | [keyword] | 6-8 | Critical |
| [Service 1] | /services/[slug] | [keyword] | 5-7 | High |
| Contact | /contact | [keyword] | 3-4 | Critical |
| Blog | /blog | [keyword] | 2-3 | Medium |
| Service Areas | /areas | [keyword] | 4-6 | Medium |

## Navigation Structure
- Home
- About
- Services
  - [Sub-service 1]
  - [Sub-service 2]
- [Service Areas] (if local)
- Blog
- Contact
```

2. **Create per-page content briefs in `content-briefs/`:**

```markdown
# Content Brief: [Page Name]

## SEO Targets
- **Primary keyword:** [keyword]
- **Secondary keywords:** [keyword], [keyword]
- **Search intent:** [informational / commercial / transactional / navigational]

## Page Meta
- **H1:** "[Exact headline — keyword + benefit]"
- **Title tag:** "[50-60 chars]"
- **Meta description:** "[150-160 chars with keyword + compelling reason to click]"

## Sections (in order)
1. **[Section Name]** — [Template: Hero/Features/etc.]
   - Purpose: [why this section exists on this page]
   - Content needed: [what text/data this section requires]
   - Keywords to include: [specific keywords for this section]
   - CTA: [if applicable, what CTA and where it links]

2. **[Section Name]** — [Template]
   - Purpose:
   - Content needed:
   - Keywords to include:
   ...

## Content Requirements
- **Word count target:** [X words]
- **Testimonials needed:** [Y, with industry-specific context]
- **FAQ questions:** [list specific questions from keyword research]
- **Stats/numbers:** [specific data points to include]
- **Images needed:** [describe what images each section needs]

## Internal Links
- Link TO: [page] with anchor text "[text]"
- Link FROM: [page] should link here
```

3. **Create `faq-research.md`:**

Research REAL questions people ask about this business/industry:

```markdown
# FAQ Research

## Sources Checked
- Google "People Also Ask" for: [keywords searched]
- Reddit threads: [subreddits checked]
- Quora questions: [topics searched]
- Industry forums: [if applicable]

## Questions Found (grouped by topic)

### [Topic 1: Pricing/Cost]
1. "[Exact question]" — Source: [PAA/Reddit/etc.]
2. "[Exact question]"

### [Topic 2: Process/How-it-works]
1. "[Exact question]"

### [Topic 3: Comparison/Selection]
1. "[Exact question]"

### [Topic 4: Industry-specific]
1. "[Exact question]"

## Selected for Website FAQ (8-12 best questions)
1. "[Question]" — Target page: [page], keyword: [keyword]
2. ...

## Selected for Blog Posts (questions needing long answers)
1. "[Question]" — Could be a full article
2. ...
```

### Quality standard:
- Every page has a content brief with specific keywords and section plan
- H1 written for every page (keyword + benefit, not generic)
- Minimum 8 FAQ questions sourced from real search data
- Internal linking plan sketched

---

## Task 4: Topical Map

**Goal:** Build the complete topic architecture — pillar pages, cluster content, internal linking structure.
**Output directory:** `ai/research/05-topical-map/`

A topical map shows Google you are THE authority on a subject by covering it comprehensively with interlinked content.

### Process:

1. **Identify 3-5 pillar topics** based on keyword clusters from Task 1.

2. **Create `topical-map.md`:**

```markdown
# Topical Map: [Business Name]

## Pillar 1: [Core Topic]
**Pillar page:** /[url] — "[Primary keyword]"
**Purpose:** Comprehensive overview of [topic]

### Cluster Content:
| Content | URL/Type | Target Keyword | Links To Pillar |
|---------|----------|---------------|-----------------|
| [Title] | /blog/[slug] | [keyword] | Yes — "[anchor]" |
| [Title] | /services/[slug] | [keyword] | Yes — "[anchor]" |
| [Title] | /blog/[slug] | [keyword] | Yes — "[anchor]" |

## Pillar 2: [Second Topic]
...
```

3. **Document internal linking strategy:**

```markdown
# Internal Linking Architecture

## Link Flow
- Homepage → All pillar pages
- Pillar pages → Their cluster content
- Cluster content → Back to pillar
- Cluster content → Related clusters (cross-linking)
- Every page → Contact/CTA page

## Anchor Text Strategy
- Use keyword-rich anchor text (not "click here")
- Vary anchor text for same target page
- Natural placement within content paragraphs
```

### Quality standard:
- Minimum 3 pillar topics identified
- Each pillar has 3-5 cluster content pieces mapped
- Internal linking strategy documented
- Every cluster piece has a target keyword

---

## Task 5: Local SEO Research (if applicable)

**Goal:** Geographic targeting strategy — what cities, what keywords, what local content.
**Output directory:** `ai/research/06-local-seo/`

Skip this task if the business is purely online/national.

### Process:

1. **Identify target service areas:**
   - Primary city/region
   - Surrounding cities within service radius
   - Any expansion targets

2. **Research local competitors per area:**
   - Who ranks for "[service] in [city]" for each target city?
   - What local trust signals do they use? (Google reviews, local awards, BBB)

3. **Create `service-areas.md`:**

```markdown
# Service Area Targeting

## Primary Market: [City, State]
- Population: [X]
- Search volume for "[service] [city]": [est.]
- Top 3 local competitors: [names]
- Content plan: Homepage + dedicated section

## Secondary Markets:
### [City 2]
- Distance from primary: [X miles]
- Search volume: [est.]
- Content plan: [service area page / mention on homepage]

### [City 3]
...

## Local Content Plan
- Service area page: /areas — lists all cities
- Individual city pages (if warranted): /areas/[city-slug]
- Google Business Profile optimization notes
- Local schema markup requirements
```

---

## Task 6: Conversion Pattern Research

**Goal:** Understand exactly how visitors in this niche convert — what CTAs work, what trust signals matter, what the conversion funnel looks like.
**Output directory:** `ai/research/07-conversion-patterns/`

This is where you study HOW people buy in this industry, not just what they search for.

### Process:

1. **Analyze CTAs across all competitor sites reviewed:**

```markdown
# CTA Analysis

## Primary CTAs Found
| Competitor | CTA Text | Placement | Style |
|-----------|----------|-----------|-------|
| [name] | "[text]" | Hero + sticky nav | Button, filled, contrast color |
| [name] | "[text]" | Hero only | Button with phone icon |

## Most Effective Patterns
Based on analysis:
- Best CTA text pattern: [e.g., "Get Your Free [X]" outperforms "Contact Us"]
- Best placement: [e.g., hero + repeated every 2-3 sections]
- Phone vs form: [which is more prominent in this niche]

## Our CTA Strategy
- Primary CTA: "[text]" — [placement plan]
- Secondary CTA: "[text]"
- Phone CTA: [yes/no, where]
```

2. **Document trust signals that matter in this niche:**

```markdown
# Trust Signals

## Industry-Specific Trust
- [e.g., "Licensed & Insured" — every competitor shows this]
- [e.g., BBB accreditation — 3 of 5 show this]
- [certifications specific to this industry]

## Social Proof
- Google review count: [competitors average X reviews]
- Star ratings displayed: [where and how]
- Testimonial style: [named with company? anonymous?]
- Case studies: [do competitors have these?]

## Authority Signals
- Years in business
- Team size / number of technicians
- Number of projects completed
- Awards / recognition
- Industry associations

## Our Trust Signal Plan
Must have:
1. [signal] — [where on site]
2. [signal]

Should have:
1. [signal]

Would be nice:
1. [signal]
```

3. **Map the conversion funnel:**

```markdown
# Conversion Funnel

## How customers buy [service] in this niche:
1. **Awareness:** [how they find out they need this — search? referral? emergency?]
2. **Research:** [what they search, what they compare]
3. **Evaluation:** [how they narrow options — reviews? price? speed?]
4. **Decision:** [what tips them over — trust? urgency? offer?]
5. **Action:** [form? phone call? booking? chat?]

## Our page must address each stage:
- Stage 1-2: [Hero + above-the-fold content]
- Stage 3: [Features/Services + Social Proof sections]
- Stage 4: [Trust signals + Testimonials + FAQ]
- Stage 5: [CTA + Contact form + Phone number]
```

### Quality standard:
- CTA analysis covers all reviewed competitors
- Trust signals specific to this industry identified
- Conversion funnel mapped with page elements assigned to each stage

---

## After All Tasks Complete

1. Update `ai/research-status.json` — all phases should be `complete`
2. Review all research files for consistency
3. Proceed to Phase 4: Design Planning

The research phase is DONE when you can answer these questions from your files:
- What are the top 50 keywords and which pages target them?
- What do the top 5 competitor sites look like, section by section?
- What do competitors do well that we must match?
- What do competitors miss that we can exploit?
- What CTAs and trust signals work in this niche?
- What content (pages + blog) do we need to build authority?
- How does the customer journey work in this industry?

If you can't answer any of these, you have more research to do.
