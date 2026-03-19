---
name: ssactivewear
description: "S&S Activewear wholesale apparel API — search products, check inventory, place orders, track shipments, manage returns. Use when asked to look up blank apparel, check stock, order wholesale clothing, or track a shipment from S&S Activewear."
metadata: {"openclaw": {"emoji": "👕", "requires": {"env": ["SS_ACCOUNT", "SS_API_KEY"], "anyBins": ["curl"]}}}
disable-model-invocation: true
---

# S&S Activewear Skill

Wholesale blank apparel distributor API. Search products, check real-time inventory, place orders, track shipments, and process returns.

**Base URL (Canada):** `https://api-ca.ssactivewear.com/v2/`
**Base URL (US):** `https://api.ssactivewear.com/v2/`
**Auth:** HTTP Basic Auth — `$SS_ACCOUNT` (account number) + `$SS_API_KEY` (API key)
**Rate Limit:** 60 requests/minute
**Format:** JSON (default) or XML via `?mediatype=xml`

## When to Use

Use this skill when the user asks to:
- Search for blank apparel products (t-shirts, hoodies, hats, etc.)
- Look up a specific product by SKU, style, or brand
- Check inventory/stock levels at warehouses
- Place a wholesale apparel order
- Track a shipment or order status
- Process a return
- Check shipping times to a ZIP code
- Compare prices across products
- Find product specifications (sizing, dimensions)

## Auth Header (All Requests)

```bash
-u "$SS_ACCOUNT:$SS_API_KEY"
```

---

## Canvas Page Integration — USE THESE PROXY ENDPOINTS

**When building canvas pages that display S&S products, ALWAYS use these server-side proxy endpoints.** The canvas page runs in a browser iframe — it cannot call the S&S API directly (CORS + credentials). The openvoiceui server proxies these requests and handles auth.

**All proxy endpoints return JSON with full image URLs already resolved (no manual URL construction needed).**

### Canvas Page Fetch Examples

```javascript
// Search styles by keyword — returns styles with images
const resp = await fetch('/api/ssactivewear/search?q=Gildan');
const data = await resp.json();
// data = { styles: [{styleID, brand, style, title, description, image, ...}], count: N }

// Get all products (SKUs) for a style — includes images, pricing, stock
// Use `partnumber` from search results (e.g. Gildan 5000 → partnumber=00060)
const resp = await fetch('/api/ssactivewear/products?partnumber=00060');
const data = await resp.json();
// data = { products: [{sku, brand, style, color, size, price, piecePrice, dozenPrice, casePrice, qty, image, imageBack, swatch, ...}], count: N }

// Get products by style ID
const resp = await fetch('/api/ssactivewear/products?styleid=39');

// Get single product by SKU
const resp = await fetch('/api/ssactivewear/products/B00760004');

// Check inventory by style
const resp = await fetch('/api/ssactivewear/inventory?style=00760');

// Check inventory by SKU
const resp = await fetch('/api/ssactivewear/inventory/B00760004');

// Get all brands
const resp = await fetch('/api/ssactivewear/brands');

// Get all categories
const resp = await fetch('/api/ssactivewear/categories');

// Get transit times for a ZIP code
const resp = await fetch('/api/ssactivewear/transit/60440');
```

### Product Object (from proxy)

```json
{
  "sku": "B00760004",
  "brand": "Gildan",
  "style": "2000",
  "title": "Gildan 2000",
  "color": "White",
  "size": "L",
  "price": 3.28,
  "piecePrice": 3.28,
  "dozenPrice": 2.96,
  "casePrice": 2.78,
  "qty": 15000,
  "image": "https://www.ssactivewear.com/Images/Products/xxx_fm.jpg",
  "imageBack": "https://www.ssactivewear.com/Images/Products/xxx_fm.jpg",
  "swatch": "https://www.ssactivewear.com/Images/Swatch/xxx_fm.jpg",
  "warehouses": [{"warehouseAbbr": "IL", "qty": 5000}, ...]
}
```

**Image URLs are ready to use in `<img src="...">` tags — no prefix needed.**

**Image size variants:** Replace `_fm` in the URL with `_fl` (large) or `_fs` (small).

---

## Core Operations (Server-Side curl — for non-canvas use)

### 1. Search Products by Keyword

```bash
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/styles/?search=Gildan%205000' | jq .
```

Returns style objects with `styleID`, `partNumber`, `brandName`, `styleName`, `title`, `description`, `baseCategory`.

### 2. Get Product Details (All Colors/Sizes for a Style)

```bash
# By part number
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/products/?partnumber=00760' | jq .

# By style ID
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/products/?styleid=39' | jq .

# By SKU
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/products/B00760004' | jq .
```

Returns product objects with: `sku`, `gtin`, `brandName`, `styleName`, `colorName`, `sizeName`, pricing (`piecePrice`, `dozenPrice`, `casePrice`, `customerPrice`, `salePrice`), `qty` (total stock), `warehouses[]` (per-warehouse stock), image URLs.

### 3. Check Inventory

```bash
# By SKU
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/inventory/B00760004' | jq .

# By style (all colors/sizes)
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/inventory/?style=00760' | jq .

# Filter to specific warehouses
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/inventory/?style=00760&Warehouses=IL,KS' | jq .
```

Returns: `sku`, `gtin`, `skuID_Master`, `styleID`, `warehouses[].warehouseAbbr`, `warehouses[].qty`.

### 4. Check Shipping Time

```bash
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/daysintransit/60440' | jq .
```

Returns per-warehouse `daysInTransit` and `cutOffTime` for same-day shipping.

### 5. Place an Order

```bash
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  -X POST 'https://api-ca.ssactivewear.com/v2/orders/' \
  -H 'Content-Type: application/json' \
  -d '{
    "address": "123 Main St",
    "city": "Chicago",
    "state": "IL",
    "zip": "60601",
    "customer": "Company Name",
    "attn": "John Doe",
    "residential": false,
    "shippingMethod": "1",
    "poNumber": "PO-12345",
    "emailConfirmation": "orders@example.com",
    "autoselectWarehouse": true,
    "AutoSelectWarehouse_Preference": "fewest",
    "lines": [
      { "identifier": "B00760004", "qty": 24 }
    ]
  }' | jq .
```

**Required:** `address`, `city`, `state`, `zip`, `lines[].identifier`, `lines[].qty`

**Shipping methods:** 1=Ground, 40=UPS Ground, 54=Cheapest, 6=Will Call, 91=UPS Express Saver

**Warehouse autoselect:** Set `autoselectWarehouse: true` with `"fewest"` (fewer shipments) or `"fastest"` (faster delivery).

**Test mode:** Add `"testOrder": true` to validate without placing a real order.

Response returns order `guid`, `orderNumber`, `orderStatus`, `total`, line items with prices.

### 6. Get Order Status

```bash
# All open orders
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/orders/?lines=true' | jq .

# By order number
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/orders/61519822?lines=true&Boxes=true' | jq .

# All orders (last 3 months)
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/orders/?All=True&lines=true' | jq .
```

### 7. Track Shipment

```bash
# By order number
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/TrackingDataByOrderNum/32526736' | jq .

# By tracking number
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/TrackingDataByTrackingNum/1Z999AA10123456784' | jq .

# By invoice
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/TrackingDataByInvoice/83713072' | jq .
```

Returns: `carrierName`, `trackingNumber`, `origin`, `actualDeliveryDateTime`, `signedBy`, `latestCheckpoint` (date, time, location, status).

### 8. Create Return

```bash
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  -X POST 'https://api-ca.ssactivewear.com/v2/returns/' \
  -H 'Content-Type: application/json' \
  -d '{
    "emailConfirmation": "returns@example.com",
    "shippingLabelRequired": true,
    "lines": [
      {
        "invoiceNumber": "83713072",
        "identifier": "B00760004",
        "qty": 5,
        "returnReason": 1
      }
    ]
  }' | jq .
```

**Return reasons:** 1=Do Not Need, 2=Damaged/Defective, 3=Keying Error, 4=Wrong Quantity, 5=Other, 6=Picking Error

Add `"isReplace": true` for replacement instead of refund.

### 9. Get All Brands

```bash
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/brands/' | jq '.[].name'
```

### 10. Get All Categories

```bash
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/categories/' | jq '.[] | {id: .categoryID, name: .name}'
```

### 11. Get Product Specs (Sizing/Measurements)

```bash
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/specs/?style=00760' | jq .
```

Returns per-size specifications: `specName` (e.g., "Chest Width", "Body Length"), `value`, `sizeName`.

### 12. Custom SKU Mapping (Cross-Reference)

```bash
# Get your custom SKU mappings
curl -s -u "$SS_ACCOUNT:$SS_API_KEY" \
  'https://api-ca.ssactivewear.com/v2/crossref/' | jq .
```

Maps your internal SKUs (`yourSku`) to S&S SKUs. Use `yourSku` as an identifier in products/inventory/order endpoints.

---

## Warehouse Codes

| Code | Location |
|------|----------|
| IL | Illinois |
| NV | Nevada |
| NJ | New Jersey |
| KS | Kansas |
| GA | Georgia |
| TX | Texas |
| FL | Florida |
| OH | Ohio |
| BC | British Columbia (Canada) |
| ON | Ontario (Canada) |

## Product Image URLs

Images from product responses use relative paths. Full URL: `https://www.ssactivewear.com/{imageField}`

Size modifiers — replace `_fm` in the URL:
- `_fl` = large
- `_fm` = medium (default)
- `_fs` = small

## Field Selection

All GET endpoints support `?fields=Field1,Field2` to return only specific fields, reducing response size.

## Error Handling

HTTP 404 with:
```json
{"errors": [{"field": "Identifier", "message": "Requested item(s) were not found or have been discontinued."}]}
```

Rate limit exceeded returns HTTP 429. Check `X-Rate-Limit-Remaining` header.

## Important Notes

- **NEVER place real orders without explicit user confirmation.** Always confirm items, quantities, shipping address, and total before submitting.
- Use `testOrder: true` to validate order structure without placing a real order.
- Inventory is real-time — check stock before quoting availability.
- Orders shipping from multiple warehouses generate multiple order objects in the response.
- Orders over 1000 lbs automatically use LTL freight.
