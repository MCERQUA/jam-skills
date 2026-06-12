# Advanced Schema Patterns

The types missing from `schema-examples.md`: video, reviews/ratings done safely, multi-location
local business, service-area businesses, Service schema, and auditing what a page ACTUALLY exposes.

## Contents
- VideoObject
- Review vs AggregateRating (and how not to get a manual action)
- LocalBusiness — multi-location pattern
- Service-Area Business (no storefront) + areaServed
- Service schema (one per service page)
- Person / author entity (E-E-A-T)
- FAQPage — current eligibility reality
- Schema at scale (programmatic generation rules)
- Auditing live schema with DataForSEO

---

## VideoObject

For any page with embedded video (service explainers, testimonials, YouTube embeds). Required:
`name`, `description`, `thumbnailUrl`, `uploadDate`.

```json
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "How Spray Foam Insulation Is Installed",
  "description": "Watch our crew insulate a 2,400 sq ft attic in Phoenix, start to finish.",
  "thumbnailUrl": "https://example.com/video/attic-thumb.jpg",
  "uploadDate": "2026-03-14T08:00:00-07:00",
  "duration": "PT4M37S",
  "contentUrl": "https://example.com/video/attic-install.mp4",
  "embedUrl": "https://www.youtube.com/embed/abc123",
  "interactionStatistic": {
    "@type": "InteractionCounter",
    "interactionType": { "@type": "WatchAction" },
    "userInteractionCount": 5432
  }
}
```

Gotchas:
- `duration` is ISO 8601 (`PT4M37S` = 4:37). Wrong format = silent ineligibility.
- For YouTube embeds you still mark up YOUR page; `embedUrl` points at the player, `contentUrl`
  is optional if you don't host the file.
- Add `hasPart` with `Clip` objects (`startOffset`/`endOffset` seconds) for key moments chapters.

---

## Review vs AggregateRating — the safe pattern

**The rule that keeps you out of trouble:** a business may NOT mark up reviews of ITSELF collected
on its own site UNLESS they are genuinely user-submitted on that page, and **self-serving
aggregateRating rich results have been restricted by Google since 2019** — `LocalBusiness` and
`Organization` star snippets generally won't show from your own markup. Stars still show for
`Product`, `Service` (sometimes), recipes, etc.

Correct AggregateRating nested in a Product/Service:

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Attic Insulation Package",
  "image": "https://example.com/attic-package.jpg",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "reviewCount": "127",
    "bestRating": "5"
  },
  "review": [{
    "@type": "Review",
    "author": { "@type": "Person", "name": "Maria G." },
    "datePublished": "2026-02-11",
    "reviewRating": { "@type": "Rating", "ratingValue": "5" },
    "reviewBody": "Crew was in and out in a day, energy bill dropped $90/month."
  }],
  "offers": {
    "@type": "Offer",
    "price": "3400",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock"
  }
}
```

Don'ts (each one is a documented manual-action trigger):
- Don't copy Google/Yelp review counts into your own `aggregateRating` — third-party ratings
  belong to the third party.
- Don't mark up reviews that aren't visible on the page.
- Don't put `aggregateRating` on every page sitewide pointing at the same rating.

---

## LocalBusiness — multi-location pattern

One `LocalBusiness` per LOCATION PAGE, each with its own NAP + geo, all tied to one parent
`Organization` via `parentOrganization`/`@id`. Never one blob listing every address.

```json
{
  "@context": "https://schema.org",
  "@type": "HVACBusiness",
  "@id": "https://example.com/locations/tempe/#business",
  "name": "Desert Air — Tempe",
  "parentOrganization": { "@id": "https://example.com/#org" },
  "url": "https://example.com/locations/tempe/",
  "telephone": "+1-480-555-0142",
  "image": "https://example.com/img/tempe-storefront.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "1200 E Apache Blvd",
    "addressLocality": "Tempe",
    "addressRegion": "AZ",
    "postalCode": "85281",
    "addressCountry": "US"
  },
  "geo": { "@type": "GeoCoordinates", "latitude": 33.4147, "longitude": -111.9093 },
  "openingHoursSpecification": [{
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday"],
    "opens": "07:00", "closes": "18:00"
  }],
  "priceRange": "$$"
}
```

Use the most specific subtype that exists: `HVACBusiness`, `RoofingContractor`, `Plumber`,
`Electrician`, `InsuranceAgency`, `HomeAndConstructionBusiness` (fallback). Specific subtype >
generic `LocalBusiness` for entity disambiguation.

---

## Service-Area Business (no storefront) + areaServed

For contractors who serve an area but hide their address (matches GBP service-area setup):
omit `streetAddress`, declare `areaServed`.

```json
{
  "@context": "https://schema.org",
  "@type": "RoofingContractor",
  "name": "Spartan Roofing",
  "url": "https://example.com",
  "telephone": "+1-580-555-0100",
  "areaServed": [
    { "@type": "City", "name": "Lawton", "containedInPlace": { "@type": "State", "name": "Oklahoma" } },
    { "@type": "City", "name": "Duncan", "containedInPlace": { "@type": "State", "name": "Oklahoma" } },
    { "@type": "AdministrativeArea", "name": "Comanche County, OK" }
  ]
}
```

On each "[Service] in [City]" money page, pair the business schema with a `Service` block whose
`areaServed` is THAT city only — this is the schema half of the service-area-pages strategy.

---

## Service schema (one per service page)

```json
{
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "Spray Foam Insulation — Tempe, AZ",
  "serviceType": "Spray foam insulation installation",
  "provider": { "@id": "https://example.com/#org" },
  "areaServed": { "@type": "City", "name": "Tempe" },
  "hasOfferCatalog": {
    "@type": "OfferCatalog",
    "name": "Insulation Services",
    "itemListElement": [
      { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "Attic insulation" } },
      { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "Crawl space encapsulation" } }
    ]
  }
}
```

---

## Person / author entity (E-E-A-T)

On articles, a real author entity beats a byline string — and AI engines use it for source
credibility:

```json
{
  "@type": "Person",
  "@id": "https://example.com/about/jane/#person",
  "name": "Jane Smith",
  "jobTitle": "Master Electrician, License #E-12345",
  "worksFor": { "@id": "https://example.com/#org" },
  "sameAs": ["https://www.linkedin.com/in/janesmith"],
  "knowsAbout": ["residential wiring", "EV charger installation"]
}
```
Reference it from `Article.author` via `@id`.

---

## FAQPage — current eligibility reality

Since Google's 2023 cutback, FAQ rich results show mainly for **well-known, authoritative
government and health sites**. For everyone else: the stars/dropdowns rarely render, BUT the
markup still helps entity/answer extraction (AI Overviews, assistants). So: keep FAQPage on
genuinely Q&A-formatted pages, write answers ≤ ~300 chars where possible, never inject FAQs
that aren't visible — but don't promise clients the dropdown rich result.

---

## Schema at scale (programmatic pages)

1. Generate from the same data record that builds the page (one source of truth — schema can
   never disagree with visible content).
2. Template per page type: money page = LocalBusiness/Service + BreadcrumbList; blog =
   Article + Person + BreadcrumbList; comparison = ItemList.
3. Always emit `@id` anchors (`#org`, `#person`, `#business`) and cross-reference instead of
   duplicating objects — one Organization defined once, referenced everywhere.
4. Validate a SAMPLE of each template (Rich Results Test), not every page; re-validate when the
   template changes.
5. CI check: every generated page parses as valid JSON-LD (a stray unescaped quote in a business
   name silently kills the whole block).

---

## Auditing live schema with DataForSEO

What a page ACTUALLY exposes (post-render) often differs from what the template intends. Two
zero-effort checks using data we already pay for:

```bash
# Single page, live — full checks incl. structured data flags
bash /mnt/system/base/skills/dataforseo/scripts/dataforseo.sh "on_page/instant_pages" \
  '[{"url":"https://clientsite.com/","enable_javascript":false}]'

# After a site crawl (on_page/task_post): extract all microdata/JSON-LD found per page
bash /mnt/system/base/skills/dataforseo/scripts/dataforseo.sh "on_page/microdata" \
  '[{"id":"<crawl-task-id>","url":"https://clientsite.com/services/"}]'
```

The brand-report pipeline's schema check (`fetch_ai.py`) only detects that JSON-LD EXISTS on the
homepage — use the calls above when you need to know WHICH types are present and valid.
