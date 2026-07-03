# S&S Activewear — Inventory Reference

## Inventory Endpoint

**GET** `/v2/inventory/`

Real-time inventory levels by SKU, style, and warehouse.

### Filtering

| Filter | URL Pattern | Identifier Types |
|--------|-------------|-----------------|
| By product | `/v2/inventory/{id}` | SkuID, Sku, GTIN, YourSku (comma-separated) |
| By style | `/v2/inventory/?style={id}` | StyleID, PartNumber, BrandName (comma-separated) |
| By StyleID | `/v2/inventory/?styleid={id}` | StyleID only |
| By PartNumber | `/v2/inventory/?partnumber={pn}` | PartNumber only |
| Warehouse filter | `?Warehouses={abbr}` | Comma-separated codes |
| Format | `?mediatype=json|xml` | Default: json |

### Examples

```
/v2/inventory/81480
/v2/inventory/B00760004
/v2/inventory/81480,B00760004,00821780008137
/v2/inventory/?style=00760
/v2/inventory/?style=00760,Gildan%205000
/v2/inventory/?style=bella%20%2B%20canvas%203001cvc
/v2/inventory/?styleid=39
/v2/inventory/?partnumber=00760
/v2/inventory/B00760004?Warehouses=BC,ON
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| sku | String | S&S supplier SKU number |
| gtin | String | Industry standard identifier |
| skuID_Master | Integer | Unique unchanging SKU identifier |
| yourSku | String | Custom SKU (via CrossRef API) |
| styleID | Integer | Unique unchanging style identifier |
| warehouses | Array | Per-warehouse inventory |

### Warehouse Object

| Field | Type | Description |
|-------|------|-------------|
| warehouseAbbr | String | Warehouse code |
| skuID | Integer | SKU identifier for warehouse |
| qty | Integer | Available quantity for sale |

### Warehouse Codes

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
| DS | Drop Ship |

### Example Response

```json
[
  {
    "sku": "B00760004",
    "gtin": "00821780001001",
    "skuID_Master": 2343,
    "yourSku": "",
    "styleID": 39,
    "warehouses": [
      { "warehouseAbbr": "IL", "skuID": 2343, "qty": 10000 },
      { "warehouseAbbr": "NV", "skuID": 55405, "qty": 0 },
      { "warehouseAbbr": "NJ", "skuID": 81480, "qty": 5000 },
      { "warehouseAbbr": "KS", "skuID": 104321, "qty": 3200 }
    ]
  }
]
```

### Usage Patterns

**Check stock for a single SKU:**
```bash
curl -u "$SS_ACCOUNT:$SS_API_KEY" \
  "https://api-ca.ssactivewear.com/v2/inventory/B00760004"
```

**Check all sizes of a style at specific warehouses:**
```bash
curl -u "$SS_ACCOUNT:$SS_API_KEY" \
  "https://api-ca.ssactivewear.com/v2/inventory/?style=00760&Warehouses=IL,KS"
```

**Bulk inventory check (multiple SKUs):**
```bash
curl -u "$SS_ACCOUNT:$SS_API_KEY" \
  "https://api-ca.ssactivewear.com/v2/inventory/B00760003,B00760004,B00760005"
```

### Notes

- Inventory is real-time — no caching guarantees
- `qty` of 0 means out of stock at that warehouse
- Use `?Warehouses=` to limit to specific fulfillment centers for faster shipping
- Combine with `/v2/daysintransit/{zip}` to find fastest warehouse for a destination
