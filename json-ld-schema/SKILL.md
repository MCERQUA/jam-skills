---
name: json-ld-schema
description: "Generate JSON-LD structured-data blocks (LocalBusiness, FAQPage, BreadcrumbList, ContactPage) for local-business landing pages via the shared generate_jsonld.py script. TRIGGER when: adding schema markup / structured data / rich snippets to a website page, or asked about JSON-LD for a local service business. DO NOT TRIGGER for general SEO research (dataforseo) or content writing (article-writer)."
metadata:
  version: 1.0.0
  openclaw:
    emoji: "🧩"
---

# JSON-LD Schema Generator

Shared script for generating JSON-LD schema blocks for local business landers. Originated from src-desktop's shared schema-generator work (mesh pledge, 2026-06-28); promoted to a proper skill 2026-07-03.

## What it generates

| Page type | Schema blocks emitted |
|---|---|
| `home` | LocalBusiness (+ FAQPage if faqs provided) |
| `service` | LocalBusiness (+ FAQPage, BreadcrumbList if provided) |
| `location` | LocalBusiness (+ FAQPage, BreadcrumbList if provided) |
| `contact` | ContactPage |
| `faq` | FAQPage |

LocalBusiness includes `hasOfferCatalog`, `areaServed`, and `aggregateRating` when config supplies them.

## Usage

```bash
cd "$(dirname "$(realpath "$0")")" 2>/dev/null || cd /mnt/shared-skills/json-ld-schema  # container path; host: /mnt/system/base/skills/json-ld-schema

# From config files:
python3 generate_jsonld.py --business examples/seattle-siding-business.json --page examples/homepage-page.json

# Inline NAP (quick):
python3 generate_jsonld.py \
  --name "Acme Roofing" \
  --url "https://acmeroofing.com" \
  --phone "+12065551234" \
  --city Seattle --state WA \
  --page-type home \
  --output html
```

Output defaults to `html` (`<script type="application/ld+json">` tags). Pass `--output json` for raw JSON array.

## Examples

See `examples/` for sample business + page configs — `seattle-siding-business.json` (full business config with services, area served, rating), `homepage-page.json` (home page config with FAQs), plus service/location/contact page samples.

Full option reference: `README.md` in this directory.
