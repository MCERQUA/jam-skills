# Research & Planning — Phase 2

This phase happens AFTER discovery (Phase 1) and BEFORE any code. Everything you build is informed by what you learn here.

---

## Step 1: Keyword Research

**Goal:** Identify 10-20 keywords this site should rank for.

### How to find keywords:

1. **Start with the obvious** — what would this business's customers type into Google?
   - "[service] [location]" — "epoxy flooring contractor tampa"
   - "[service] insurance/cost/near me" — "epoxy contractor insurance cost"
   - "[industry] [service type]" — "commercial epoxy flooring"

2. **Search Google** for each candidate keyword and note:
   - What the top results' title tags say (these are your competitors)
   - "People also ask" questions (these become your FAQ)
   - "Related searches" at the bottom (these are secondary keywords)

3. **Categorize your keywords:**

| Category | Example | Where Used |
|----------|---------|-----------|
| Primary (3-5) | "epoxy flooring contractor insurance" | Homepage H1, meta title |
| Secondary (5-10) | "general liability epoxy contractors", "workers comp flooring" | Service pages, feature sections |
| Long-tail (5-10) | "how much does epoxy contractor insurance cost" | FAQ, blog posts |
| Location (if local) | "epoxy flooring phoenix az" | Service area pages, meta desc |

### Document format:

```markdown
## Target Keywords

### Primary
1. [keyword] — Monthly volume estimate: [high/medium/low]
2. [keyword] — Monthly volume estimate: [high/medium/low]

### Secondary
1. [keyword]
2. [keyword]

### Long-tail / Questions
1. [keyword/question]
2. [keyword/question]

### Location Keywords (if applicable)
1. [keyword]
```

---

## Step 2: Competitor Scan

**Goal:** Understand what's already ranking and find gaps to exploit.

### For each of the top 3-5 competitors:

1. **Visit their site** and note:
   - What pages do they have?
   - What's their H1 on the homepage?
   - What sections do they include? (features, FAQ, testimonials, etc.)
   - What's their visual style? (colors, imagery, layout)

2. **Identify gaps:**
   - Do they have an FAQ section? (Most don't — easy win for SEO)
   - Do they have real testimonials with names/companies?
   - Is their content specific or generic?
   - Do they have blog content?
   - Is their site mobile-friendly?

3. **Document what we'll do better:**
   - More specific content
   - Better visual design
   - FAQ section targeting long-tail keywords
   - Industry-specific testimonials
   - Better structured data

---

## Step 3: Content Plan

**Goal:** Map every page, every section, every headline BEFORE writing code.

### Page-by-page plan:

For EACH page, fill in:

```markdown
## [Page Name]

**URL:** /[path]
**Primary keyword:** [keyword]
**Secondary keywords:** [keyword1], [keyword2]

**H1:** "[Exact headline — must contain primary keyword, must be benefit-focused]"
**Meta title:** "[Title tag — 50-60 chars, keyword at front]"
**Meta description:** "[150-160 chars, keyword + compelling reason to click]"

**Sections (in order):**
1. Hero — [brief description of content]
2. [Section] — [brief description]
3. [Section] — [brief description]
...

**Key content to write:**
- [specific paragraph/list/data needed]
- [testimonials needed]
- [FAQ questions that target long-tail keywords]
```

### Example (SEO Leadgen — Insurance):

```markdown
## Homepage

**URL:** /
**Primary keyword:** epoxy flooring contractor insurance
**Secondary keywords:** epoxy coating insurance, insurance for epoxy companies

**H1:** "Comprehensive Insurance for Epoxy Flooring Contractors"
**Meta title:** "Epoxy Flooring Contractor Insurance — Quotes from A-Rated Carriers"
**Meta description:** "Specialized insurance for epoxy contractors. GL, workers' comp, auto, professional liability. Licensed in all 50 states. Same-day certificates. Free quote."

**Sections:**
1. Hero — H1 + subtitle about specialized coverage + CTA "Get Your Free Quote"
2. TrustBar — A-Rated Carriers, 50 States, Same-Day COI, 4.9★ Rating
3. Stats — 20+ years, 1000+ contractors, 2hr claims response, 50 states
4. CoverageGrid — 8 coverage types with descriptions specific to epoxy work
5. HowItWorks — 3 steps: Tell us about your business → Get custom recommendation → Get covered
6. Testimonials — 4 realistic testimonials from epoxy contractors
7. FAQ — 8 questions targeting long-tail keywords
8. CTA — Quote CTA with bullet list of benefits
9. Footer — Real contact info, coverage links, resource links
```

---

## Step 4: Headline Drafts

**Write the H1 for EVERY page before building anything.**

### Rules:
- Must contain the page's primary keyword
- Must be benefit-focused (what the customer gets)
- Must be specific to this business (not generic)
- 5-12 words is the sweet spot

### Bad vs Good:

| Bad (generic/scary) | Good (keyword + benefit) |
|---|---|
| "Welcome to Our Website" | "Comprehensive Insurance for Epoxy Flooring Contractors" |
| "One Job Goes Wrong And You're Out of Business" | "Insurance Coverage Built for Epoxy Flooring Professionals" |
| "About Our Company" | "Built by People Who Understand Epoxy Contractors" |
| "Our Services" | "Insurance Coverage for Every Type of Epoxy Work" |
| "Contact Us" | "Get Your Epoxy Contractor Insurance Quote in Minutes" |

---

## Deliverable

Save the complete research plan (keywords + competitor notes + page plan + headlines) to the project's `.claude/CLAUDE.md` under a "Content Plan" section. This document drives everything in Phase 5.
