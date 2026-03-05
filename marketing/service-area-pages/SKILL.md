---
name: service-area-pages
description: When the user wants to create city pages, service area pages, or location-specific landing pages for a local business. Also use when the user mentions "service area pages," "city pages," "location pages," "[service] in [city] pages," "neighborhood pages," "location landing pages," "local landing pages," "area pages," or wants to create pages targeting specific cities or neighborhoods. This skill goes beyond programmatic-seo with local-specific depth — unique content strategies, local data integration, and service area schema. For general SEO pages at scale, see programmatic-seo. For local SEO strategy, see local-seo. For schema markup, see schema-markup.
metadata:
  version: 1.0.0
---

# Service Area Pages

You are an expert in creating high-quality service area landing pages for local businesses. Your goal is to help service companies, insurance agents, and local businesses create city/neighborhood pages that rank, convert, and avoid thin content penalties.

## Initial Assessment

**Check for product marketing context first:**
If `.agents/product-marketing-context.md` exists (or `.claude/product-marketing-context.md` in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Before building service area pages, understand:

1. **Business Context**
   - What services do you offer?
   - What cities/areas do you serve?
   - Storefront or service area business (SAB)?

2. **Current Coverage**
   - How many location pages do you have today?
   - Which cities are missing?
   - What do competitor location pages look like?

3. **Content Resources**
   - Do you have city-specific testimonials?
   - Do you have photos from jobs in specific cities?
   - Can you provide area-specific details (local regulations, climate factors, common issues)?

---

## Core Principles

### 1. Every Page Must Be Genuinely Useful
Google explicitly distinguishes between legitimate location pages and doorway pages. The difference: does the page provide unique value for someone in that specific city, or is it the same generic content with the city name swapped?

### 2. Unique Content Threshold

| Page Type | Min Words | Unique Content % |
|-----------|-----------|-----------------|
| Primary City (your HQ city) | 800+ | 80%+ |
| Major Service Area City | 600+ | 60%+ |
| Secondary Service Area | 500+ | 40%+ |
| Neighborhood Subpage | 400+ | 50%+ |

### 3. Quality Over Quantity
30 strong pages outranks 100 thin ones. Google may de-index thin location pages entirely and flag your site for doorway page penalties.

**Warning thresholds:**
- 30+ location pages: ensure every page has genuinely unique content
- 50+ location pages: requires strong domain authority and truly differentiated content per page
- 100+: almost always triggers thin content issues unless you have proprietary data per location

### 4. Build for the Customer First
A homeowner in Scottsdale searching "plumber Scottsdale" wants to know: do you serve Scottsdale specifically, how fast can you get there, do you know the local issues, and who else in Scottsdale has used you? Answer those questions.

---

## Page Template

### URL Structure Options

| Pattern | Example | When to Use |
|---------|---------|-------------|
| `/locations/[city]/` | `/locations/scottsdale/` | Multi-service, city is primary |
| `/[service]/[city]/` | `/plumbing/scottsdale/` | Service is primary, city is modifier |
| `/[city]/[service]/` | `/scottsdale/plumbing/` | City is primary, many services |
| `/[service]-[city]/` | `/plumbing-scottsdale/` | Simple sites, flat structure |

**Choose ONE pattern and use it consistently.** Don't mix patterns.

**Recommended for most service businesses:** `/[service]/[city]/` — puts the service first (primary intent) with city as qualifier.

### Page Structure

```
Title: [Service] in [City], [State] | [Business Name]
H1: [Service] in [City], [State]
URL: /[service]/[city]/

1. Hero Section
   - H1 with service + city
   - Phone number (click-to-call)
   - Primary CTA ("Get a Free Quote" / "Call Now")
   - Trust signals (rating, years in business, license #)

2. Opening Paragraph (unique per city — 100+ words)
   - Establish you serve this specific city
   - Mention specific neighborhoods/landmarks
   - Mention local conditions that relate to your service
   - State years serving this area

3. Services in [City] (200+ words)
   - List specific services available in this city
   - Mention any city-specific service considerations
   - Emergency/24hr callout if applicable

4. Why Choose [Business] in [City] (150+ words)
   - Local expertise differentiators
   - Response time for this area
   - Licenses/certifications relevant to this jurisdiction
   - Community involvement in this city

5. Local Testimonials (if available)
   - Reviews from customers in this specific city
   - Include first name, neighborhood, service performed
   - Star rating display

6. Area-Specific Content (150+ words — THIS is what makes it unique)
   - See "Making Each Page Unique" section below

7. Service Area Map
   - Embedded Google Map showing service coverage
   - List neighboring cities you also serve (with links)

8. FAQ Section (3-5 questions, city-specific)
   - "How fast can you get to [City]?"
   - "Do you need a permit for [service] in [City]?"
   - "What does [service] cost in [City]?"
   - These become FAQ schema

9. CTA Section
   - Phone number
   - Quote form
   - Hours of operation
   - License number

10. Related Pages (internal links)
    - Other services in this city
    - Same service in neighboring cities
    - Hub/parent service page
```

---

## Making Each Page Unique

This is the hardest part and the most important. Here's how to create genuinely unique content for each city page:

### 1. Local Conditions & Climate

| Industry | City-Specific Angles |
|----------|---------------------|
| HVAC | Average temps, humidity, common system types, monsoon/storm prep |
| Plumbing | Water hardness, common pipe materials in older homes, freeze risk |
| Roofing | Hail zones, wind ratings, sun exposure, common roof types |
| Pest Control | Regional pest seasons, common species by area |
| Insurance | Local risk factors (flood zones, wildfire, hail), state regulations |
| Landscaping | Climate zone, soil types, water restrictions, HOA common plants |

### 2. Local Regulations & Requirements

- Permit requirements for this city/county
- Building codes specific to this jurisdiction
- License requirements for your trade in this area
- HOA considerations common in this neighborhood
- Environmental regulations (water use, disposal, etc.)

### 3. Neighborhood-Specific Details

- Mention specific neighborhoods within the city
- Reference landmarks, major roads, neighborhoods
- "We service homes in [Neighborhood A], [Neighborhood B], and throughout [City]"
- Mention age of housing stock (e.g., "Many homes in [Neighborhood] built in the 1970s have...")

### 4. Local Stats & Data

- Population / number of households
- Average home age and common building styles
- Local climate data relevant to your service
- Property value ranges (affects service pricing context)
- Growth rate (new construction opportunities)

### 5. Community Connection

- Local events you sponsor or attend
- Local organizations you belong to
- Charity work in this specific community
- Years serving this specific area
- Number of jobs completed in this city

### 6. Photos from This City

- Real photos from jobs in this specific city/neighborhood
- Geo-tagged when possible
- Before/after from local projects
- Team photos at local landmarks or job sites
- NO stock photos — Google and customers can tell

---

## Schema Markup for Service Area Pages

### LocalBusiness + Service + areaServed

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "LocalBusiness",
      "@id": "https://example.com/#business",
      "name": "[Business Name]",
      "description": "[Service] provider serving [City], [State]",
      "url": "https://example.com/[service]/[city]/",
      "telephone": "+1-555-555-5555",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "[Your Address]",
        "addressLocality": "[Your City]",
        "addressRegion": "[State]",
        "postalCode": "[ZIP]",
        "addressCountry": "US"
      },
      "geo": {
        "@type": "GeoCoordinates",
        "latitude": "[Your Lat]",
        "longitude": "[Your Long]"
      },
      "areaServed": [
        {
          "@type": "City",
          "name": "[City]",
          "sameAs": "https://en.wikipedia.org/wiki/[City]"
        }
      ],
      "openingHoursSpecification": [
        {
          "@type": "OpeningHoursSpecification",
          "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
          "opens": "08:00",
          "closes": "18:00"
        }
      ],
      "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "4.8",
        "reviewCount": "127"
      },
      "priceRange": "$$"
    },
    {
      "@type": "Service",
      "name": "[Service Type] in [City]",
      "description": "[Description of service in this area]",
      "provider": { "@id": "https://example.com/#business" },
      "areaServed": {
        "@type": "City",
        "name": "[City]"
      },
      "serviceType": "[Service Category]"
    },
    {
      "@type": "BreadcrumbList",
      "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com/" },
        { "@type": "ListItem", "position": 2, "name": "[Service]", "item": "https://example.com/[service]/" },
        { "@type": "ListItem", "position": 3, "name": "[City]", "item": "https://example.com/[service]/[city]/" }
      ]
    },
    {
      "@type": "FAQPage",
      "mainEntity": [
        {
          "@type": "Question",
          "name": "How fast can you get to [City]?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "[Your answer with specific response time]"
          }
        }
      ]
    }
  ]
}
```

### Key Schema Rules
- Use `areaServed` with `@type: "City"` (not just a string)
- Include `geo` coordinates for your business location
- Add `Service` schema with `serviceType` for each primary service
- Add `aggregateRating` only if you have real, verifiable reviews
- Include `BreadcrumbList` matching your URL hierarchy
- Add `FAQPage` for the city-specific FAQ section

---

## Internal Linking Architecture

### Hub and Spoke Model

```
                    Homepage
                       |
            ┌──────────┼──────────┐
         Service 1   Service 2   Service 3
         (hub)       (hub)       (hub)
         /  |  \
     City1 City2 City3  ← service area pages (spokes)
```

### Linking Rules

**From each service area page, link to:**
- Parent service page (breadcrumb + contextual)
- Same service in neighboring cities ("Also serving [City B], [City C]")
- Other services in the same city ("Need [other service] in [City]? →")
- Homepage (via breadcrumb/nav)

**From the parent service page, link to:**
- All city pages for this service
- Can use a "Service Areas" section with a list/map

**From the homepage:**
- Link to top service hubs
- Optional: "Areas We Serve" section with top cities

### Cross-Linking Between City Pages

**At bottom of each city page:**
> **Also Serving:** [City A] | [City B] | [City C] | [City D]

Each linked to its respective service area page. This creates a mesh of internal links that distributes authority.

### Sitemap

- Include all service area pages in your XML sitemap
- Consider a separate sitemap for location pages if you have 30+
- Submit to Search Console after adding new pages

---

## Gap Analysis Process

### Finding Missing Pages

1. **List your services** (e.g., plumbing, HVAC, electrical)
2. **List all cities you serve** (including suburbs and neighborhoods)
3. **Create the matrix:** every service × every city
4. **Check which combos have pages** (crawl your site)
5. **Check which combos competitors have** (crawl competitor sites)
6. **Highlight gaps:** competitors have a page for [service] + [city] and you don't

### Prioritization

Prioritize building pages for:
1. **Highest search volume** — "[plumber] [largest city]" before "[plumber] [small suburb]"
2. **Highest revenue service** — your most profitable service first
3. **Competitor presence** — if 3 competitors have a page and you don't, you're invisible
4. **Proximity** — cities closest to your location first

---

## What NOT to Do

### Doorway Page Traps

Google will penalize these patterns:
- **City name swap only** — same content with just the city name changed
- **Thin pages** — under 300 words with no unique value
- **No local content** — nothing specific to that city
- **Mass generation** — 200 pages created the same day with template content
- **No internal links** — orphan pages Google can barely find

### Content to Avoid

- Generic "about [city]" text copied from Wikipedia
- Fake testimonials or reviews
- Stock photos with no local relevance
- Weather data as filler (unless relevant to your service)
- Population/demographics as filler (unless relevant)

### Technical Mistakes

- Duplicate title tags across city pages
- Same meta description on every page
- No canonical tags
- Missing from XML sitemap
- Blocking city pages in robots.txt

---

## Output Format

### For a Single Page

Provide:
- Complete page content (H1, all sections, FAQ)
- Meta title and description
- Schema markup (JSON-LD)
- Internal linking recommendations

### For a Page Build-Out Plan

Provide:
- Service × City matrix with priority ranking
- URL structure recommendation
- Content template with sections to customize per city
- Schema template
- Build schedule (which pages to create first)

---

## Task-Specific Questions

1. What services do you offer?
2. What cities/neighborhoods do you serve?
3. Do you have city-specific testimonials or photos?
4. How many service area pages do you have today?
5. What do your top competitors' location pages look like?
6. Are there local regulations or permits specific to certain cities?

---

## Related Skills

- **local-seo**: For comprehensive local search strategy (GBP, citations, reviews)
- **programmatic-seo**: For general pages-at-scale strategy (this skill adds local-specific depth)
- **schema-markup**: For detailed structured data implementation
- **site-architecture**: For URL structure and navigation decisions
- **copywriting**: For writing compelling, unique city page content
- **review-management**: For getting city-specific testimonials to use on location pages
