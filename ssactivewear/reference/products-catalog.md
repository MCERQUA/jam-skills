# S&S Activewear — Products & Catalog Reference

## Products Endpoint

**GET** `/v2/products/`

### Filtering

| Filter | URL Pattern | Identifier Types |
|--------|-------------|-----------------|
| By product | `/v2/products/{id}` | SkuID, Sku, GTIN, YourSku (comma-separated) |
| By style | `/v2/products/?style={id}` | StyleID, PartNumber, BrandName+Name |
| By StyleID | `/v2/products/?styleid={id}` | StyleID only |
| By PartNumber | `/v2/products/?partnumber={pn}` | PartNumber only |
| Warehouse filter | `?Warehouses={abbr}` | Comma-separated warehouse codes (IL, NV, NJ, KS, GA, TX, FL, OH, BC, ON) |
| Field selection | `?fields={f1,f2}` | Any product object field names |
| Format | `?mediatype=json|xml` | Default: json |

### Examples

```
/v2/products/81480
/v2/products/B00760004
/v2/products/81480,B00760004,00821780008137
/v2/products/?style=00760
/v2/products/?style=Gildan%205000
/v2/products/?styleid=39
/v2/products/B00760003?Warehouses=IL,KS
/v2/products/B00760003?fields=Sku,Gtin,Qty,CustomerPrice
```

### Product Object Fields

| Field | Type | Description |
|-------|------|-------------|
| sku | String | S&S Activewear SKU number |
| gtin | String | Industry standard identifier (UPC/EAN) |
| skuID_Master | Integer | Unique unchanging SKU ID |
| yourSku | String | Custom SKU set via CrossRef API |
| styleID | Integer | Unique unchanging style ID |
| brandName | String | Brand name |
| styleName | String | Style name (unique within brand) |
| colorName | String | Product color |
| colorCode | String | Two-digit color code |
| colorPriceCodeName | String | Pricing category of color |
| colorGroup | String | Similar color grouping |
| colorGroupName | String | Similar color grouping name |
| colorFamilyID | Integer | Base color family ID |
| colorFamily | String | Base color family name (e.g., "Red", "Blue") |
| colorSwatchImage | String | Medium swatch image URL |
| colorSwatchTextColor | String | HTML color code for text overlay on swatch |
| colorFrontImage | String | Medium front product image URL |
| colorSideImage | String | Medium side product image URL |
| colorBackImage | String | Medium back product image URL |
| colorDirectSideImage | String | Medium direct side image URL |
| colorOnModelFrontImage | String | Medium on-model front image URL |
| colorOnModelSideImage | String | Medium on-model side image URL |
| colorOnModelBackImage | String | Medium on-model back image URL |
| color1 | String | Primary HTML color code |
| color2 | String | Secondary HTML color code |
| sizeName | String | Size designation |
| sizeCode | String | One-digit size code |
| sizeOrder | String | Sort order for size |
| sizePriceCodeName | String | Size pricing category |
| caseQty | Integer | Units per mill case |
| unitWeight | Decimal | Single unit weight (lbs) |
| mapPrice | Decimal | Minimum Advertised Price |
| piecePrice | Decimal | Piece-level price |
| dozenPrice | Decimal | Dozen-level price |
| casePrice | Decimal | Case-level price |
| salePrice | Decimal | Sale price (0 if none) |
| customerPrice | Decimal | Your negotiated price |
| saleExpiration | String | Sale end date (MM/DD/YYYY) |
| noeRetailing | Boolean | Prohibits eRetailing platform sales (Amazon, eBay, etc.) |
| caseWeight | Decimal | Full case weight in pounds |
| caseWidth | Decimal | Case width in inches |
| caseLength | Decimal | Case length in inches |
| caseHeight | Decimal | Case height in inches |
| PolyPackQty | Integer | Pieces per poly pack |
| qty | Integer | Combined warehouse inventory |
| countryOfOrigin | String | Manufacturing country |
| warehouses | Array | Per-warehouse inventory details |

### Warehouse Object (nested in product)

| Field | Type | Description |
|-------|------|-------------|
| warehouseAbbr | String | Warehouse code (IL, NV, NJ, KS, GA, TX, FL, OH, BC, ON) |
| skuID | Integer | SKU-warehouse identifier |
| qty | Integer | Available quantity |
| closeout | Boolean | Discontinued/closeout status |
| dropship | Boolean | Drop-ship eligible |
| excludeFreeFreight | Boolean | Ineligible for free freight promotions |
| fullCaseOnly | Boolean | Case-only ordering required |
| expectedInventory | String | Enroute quantities and expected dates |
| returnable | Boolean | Return eligibility |

### Image URL Construction

Base URL: `https://www.ssactivewear.com/{imageField}`

Size modifiers — replace `_fm` in the URL:
- `_fl` = large
- `_fm` = medium (default)
- `_fs` = small

---

## Styles Endpoint

**GET** `/v2/styles/`

### Filtering

| Filter | URL Pattern |
|--------|-------------|
| All styles | `/v2/styles/` |
| By identifier | `/v2/styles/{id}` (StyleID, PartNumber, BrandName+Name) |
| Search | `/v2/styles/?search={query}` |
| By StyleID | `/v2/styles/?styleid={id}` |
| By PartNumber | `/v2/styles/?partnumber={pn}` |
| Field selection | `?fields={f1,f2}` |
| Format | `?mediatype=json|xml` |

### Style Object Fields

| Field | Type | Description |
|-------|------|-------------|
| styleID | Integer | Unique unchanging style identifier |
| partNumber | String | First 5 digits of SKU; same across all SKUs in style |
| brandName | String | Manufacturing brand |
| styleName | String | Brand-unique style name |
| title | String | Short style description |
| description | String | Extended HTML-formatted description |
| baseCategory | String | Primary category (one per style) |
| categories | String | Comma-separated category IDs |
| catalogPageNumber | String | Current catalog page reference |
| newStyle | Boolean | New product indicator |
| comparableGroup | String | Similar products grouping |
| companionGroup | String | Product family grouping |
| brandImage | String | Brand image URL (medium) |
| styleImage | String | Style image URL (medium) |

---

## Categories Endpoint

**GET** `/v2/categories/`

| Filter | URL Pattern |
|--------|-------------|
| All | `/v2/categories/` |
| By ID | `/v2/categories/{categoryID}` |
| Fields | `?fields=CategoryID,Name` |

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| categoryID | Integer | Unique category ID |
| name | String | Category name |
| image | String | Deprecated |

---

## Brands Endpoint

**GET** `/v2/brands/`

| Filter | URL Pattern |
|--------|-------------|
| All | `/v2/brands/` |
| By ID | `/v2/brands/{brandID}` |

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| brandID | Integer | Unique brand ID |
| name | String | Brand name |
| image | String | Brand image URL (`_fl`/`_fm`/`_fs` sizes) |
| noeRetailing | Boolean | Prohibits eRetailing platform sales |

---

## Specs Endpoint

**GET** `/v2/specs/`

Returns product specifications (measurements, dimensions, etc.) per size.

| Filter | URL Pattern |
|--------|-------------|
| All | `/v2/specs/` |
| By SpecID | `/v2/specs/{specID}` |
| By style | `/v2/specs/?style={id}` (StyleID, PartNumber, BrandName) |
| Fields | `?fields=BrandName,StyleName,SizeName,SpecName,Value` |

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| specID | Integer | Unique spec ID |
| styleID | Integer | Style identifier |
| partNumber | String | Part number |
| brandName | String | Brand |
| styleName | String | Style |
| sizeName | String | Size this spec applies to |
| sizeOrder | String | Sort order |
| specName | String | Specification name (e.g., "Neck Size", "Chest Width") |
| value | String | Specification value |

---

## Error Response

All endpoints return HTTP 404 with:
```json
{
  "errors": [
    {
      "field": "Identifier",
      "message": "Requested item(s) were not found or have been discontinued."
    }
  ]
}
```
