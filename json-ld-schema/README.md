# JSON-LD Schema Generator

Shared script for generating JSON-LD schema blocks for local business landers.

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

See `examples/` for sample business + page configs:

- `seattle-siding-business.json` — full business config with services, area served, rating
- `homepage-page.json` — home page config with FAQs
- `bellevue-location-page.json` — location page with breadcrumbs
- `siding-repair-page.json` — service page
- `contact-page.json` — contact page

## Integration (website-builder)

Call from any build pipeline step that needs JSON-LD:

```bash
python3 /path/to/tools/schema/generate_jsonld.py \
  --business "$BIZ_CONFIG" \
  --page "$PAGE_CONFIG" \
  --output html >> $OUTPUT_FILE
```
