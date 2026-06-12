---
name: sinalite
description: "SinaLite wholesale trade printer API integration — product catalog, live pricing, order submission, shipping estimates. Used across tenant websites to display printing products and submit orders."
---

# SinaLite API Skill

Wholesale trade printer. Products: signs, banners, business cards, stickers, marketing materials, stationery, large format, packaging, promotional items.

## Environment Variables

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `SINALITE_CLIENT_ID` | Yes | — | OAuth2 client ID |
| `SINALITE_CLIENT_SECRET` | Yes | — | OAuth2 client secret |
| `SINALITE_API_URL` | No | `https://liveapi.sinalite.com` | Sandbox: `https://api.sinaliteuppy.com` |
| `SINALITE_STORE_CODE` | No | `9` | 6 = Canada, 9 = US |

## Auth Flow

OAuth2 client_credentials grant. Token cached to `/tmp/sinalite_token` for 1 hour.

```
POST {SINALITE_API_URL}/auth/token
Content-Type: application/json

{"client_id":"...","client_secret":"...","audience":"https://apiconnect.sinalite.com","grant_type":"client_credentials"}
→ {"access_token":"...","token_type":"Bearer"}
```

## API Endpoints

### Products

| Method | Path | Description |
|--------|------|-------------|
| GET | `/product` | All products — `[{id, sku, name, category, enabled}]` |
| GET | `/product/{id}` | Single product general data |
| GET | `/product/{id}/{storeCode}` | Product options + pricing combos + metadata |

### Pricing

| Method | Path | Description |
|--------|------|-------------|
| POST | `/price/{id}/{storeCode}` | Real-time price quote for option combination |
| GET | `/variants/{id}/{storeCode}` | All pre-computed pricing variants |

### Orders

| Method | Path | Description |
|--------|------|-------------|
| POST | `/order/new` | Submit order (items, file URLs, shipping/billing, notes) |
| POST | `/order/shippingEstimate` | Shipping rates by carrier with prices + transit days |

### Shipping Carriers

UPS Standard, UPS Express, UPS Expedited, UPS Express Saver, UPS Worldwide Expedited, UPS Saver, FedEx Standard Overnight, FedEx Economy, FedEx Express Saver, FedEx International Economy, FedEx International Priority.

## Helper Script

```bash
# Auth (auto-cached)
/mnt/shared-skills/sinalite/scripts/sinalite-api.sh auth

# Product catalog
/mnt/shared-skills/sinalite/scripts/sinalite-api.sh products

# Single product with options (storeCode defaults to 9/US)
/mnt/shared-skills/sinalite/scripts/sinalite-api.sh product <id> [storeCode]

# Live price quote
/mnt/shared-skills/sinalite/scripts/sinalite-api.sh price <id> <storeCode> '<options_json>'

# Shipping estimate
/mnt/shared-skills/sinalite/scripts/sinalite-api.sh estimate '<items_json>' <state> <zip> <country>

# Submit order
/mnt/shared-skills/sinalite/scripts/sinalite-api.sh order '<order_json>'
```

All output is JSON to stdout. Errors to stderr.

## Website Integration Patterns

### Basic: Product Display

Fetch `/product` on build or SSR, render category pages. Use `/variants/{id}/{storeCode}` for pre-computed price tables (no per-request API call).

### Full: Live Pricing + Ordering

1. Load product options via `/product/{id}/{storeCode}`
2. On option change, call `/price/{id}/{storeCode}` with selected options
3. On cart submit, call `/order/shippingEstimate` for carrier rates
4. Submit via `/order/new` with file upload URLs

### File Upload

SinaLite accepts file URLs in orders. Upload customer files to your own storage (S3, etc.), pass the URL in the order payload.

## Markup Strategy

Typical wholesale print markup: 2x–4x depending on product category. Consider:

- **Commodity items** (business cards, flyers): 2x–2.5x
- **Custom/signage**: 3x–4x
- **Promotional**: 2.5x–3x
- Factor in your design time, customer service, and shipping padding

Store markup rules per product category in website config. Apply on display, not on API calls (keep wholesale prices in API responses for verification).

## Product Categories Quick Reference

- **Signs**: coroplast, aluminum, foam board, A-frame, sintra/PVC, styrene
- **Banners**: vinyl, pull-up, mesh, X-frame
- **Business Cards**: 14pt–32pt, various finishes
- **Stickers/Labels**: roll labels, square cut, cut-to-shape decals
- **Marketing**: postcards, flyers, brochures, door hangers, magnets
- **Stationery**: letterhead, envelopes, notepads
- **Large Format**: floor graphics, car magnets, window graphics, canvas
- **Packaging**: product boxes, corrugated, flexible
- **Promotional**: mugs, tumblers, apparel, keychains

## Notes

- Sandbox URL (`https://api.sinaliteuppy.com`) for development and testing.
- Tokens expire — the script auto-refreshes when cached token is >3600s old.
- Rate limits apply; cache product catalogs and variant lists, only call `/price` live.
- Store code determines currency and shipping origin: 6=Canada (CAD), 9=US (USD).
