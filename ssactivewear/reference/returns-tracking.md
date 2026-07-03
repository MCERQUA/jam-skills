# S&S Activewear — Returns, Tracking & Cross-Reference

## Create Return

**POST** `/v2/returns/`

Content-Type: `application/json` or `application/xml`

### Request Body

```json
{
  "emailConfirmation": "returns@example.com",
  "testOrder": false,
  "shippingLabelRequired": true,
  "showBoxes": false,
  "lines": [
    {
      "invoiceNumber": "83713072",
      "identifier": "B00760004",
      "qty": 5,
      "returnReason": 1,
      "isReplace": false
    }
  ]
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| lines | Array | At least one return line |
| lines[].invoiceNumber | String | Original invoice number |
| lines[].identifier | String | SkuID, Sku, or GTIN |
| lines[].qty | Integer | Quantity to return |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| emailConfirmation | String | "" | Confirmation email |
| testOrder | Boolean | false | Test mode (creates + cancels) |
| shippingLabelRequired | Boolean | true | Generate shipping label |
| showBoxes | Boolean | false | Include box details in response |
| lines[].returnReason | Integer | — | Reason code (see below) |
| lines[].isReplace | Boolean | false | Replacement instead of refund |
| lines[].returnReasonComment | String | — | Required if reason=2 or 6 AND isReplace=true |

### Return Reason Codes

| Code | Reason |
|------|--------|
| 1 | Do Not Need |
| 2 | Damaged/Defective |
| 3 | Keying Error |
| 4 | Wrong Quantity |
| 5 | Other |
| 6 | Picking Error |

### Response

Returns array with Credit and/or Replacement order objects including:
- `returnInformation` — RA number, shipping labels, return address
- `shippingLabelURL` — URL to download shipping label
- `returnToAddress` — where to ship returns
- `raNumber` — return authorization number
- `originalInvoice` — original invoice(s)
- `boxes` — tracking numbers, labels (PNG + ZPL/Base64)

---

## Get Returns

**GET** `/v2/returns/`

| Filter | URL Pattern |
|--------|-------------|
| By identifier | `/v2/returns/{id}` (PONumber, OrderNumber, InvoiceNumber, GUID) |
| By invoice date | `?invoicedate=YYYY-MM-DD` |
| Include lines | `?lines=true` |
| Include boxes | `?Boxes=true` |
| Field selection | `?fields=FIELD1,FIELD2` |

---

## Delete Return

**DELETE** `/v2/returns/{id}`

Cancels a pending return.

---

## Tracking

Multiple tracking endpoints for different lookup methods:

| Endpoint | Parameter |
|----------|-----------|
| `/v2/TrackingDataByInvoice/{invoiceNumbers}` | Comma-separated invoice numbers |
| `/v2/TrackingDataByOrderNum/{orderNumbers}` | Comma-separated order numbers |
| `/v2/TrackingDataByShipDate/{dates}` | Comma-separated dates (YYYY-MM-DD) |
| `/v2/TrackingDataByShippingDateRange/{start,end}` | Start and end dates |
| `/v2/TrackingDataByTrackingNum/{trackingNumbers}` | Comma-separated tracking numbers |
| `/v2/TrackingDataByActualDeliveryDate/{dates}` | Delivery date(s) |

### Tracking Response Fields

| Field | Type | Description |
|-------|------|-------------|
| carrierName | String | Shipping carrier |
| trackingNumber | String | Tracking identifier |
| origin | String | Shipment origin |
| actualDeliveryDateTime | String | Delivery timestamp |
| signedBy | String | Signature info |
| orderNumber | String | Associated order |
| invoiceNumber | String | Associated invoice |
| latestCheckpoint | Object | Most recent tracking update |

### Checkpoint Object

| Field | Type |
|-------|------|
| checkpointDate | String |
| checkpointTime | String |
| checkpointLocation | String |
| checkpointStatusMessage | String |

### Example

```bash
curl -u "$SS_ACCOUNT:$SS_API_KEY" \
  "https://api-ca.ssactivewear.com/v2/TrackingDataByOrderNum/32526736"
```

---

## Days In Transit

**GET** `/v2/daysintransit/{zipCode}`

Returns delivery timeframes from each warehouse to a destination ZIP code.

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| zipCode | String | Destination ZIP |
| warehouses | Array | Per-warehouse transit info |
| warehouseAbbr | String | Warehouse code |
| cutOffTime | String | Same-day ship cutoff (e.g., "4:00 CT") |
| daysInTransit | Integer | Estimated delivery days |

### Example

```bash
curl -u "$SS_ACCOUNT:$SS_API_KEY" \
  "https://api-ca.ssactivewear.com/v2/daysintransit/60440"
```

Response:
```json
[
  {
    "zipCode": "60440",
    "warehouses": [
      { "warehouseAbbr": "IL", "cutOffTime": "4:00 CT", "daysInTransit": 1 },
      { "warehouseAbbr": "NJ", "cutOffTime": "3:00 ET", "daysInTransit": 3 },
      { "warehouseAbbr": "KS", "cutOffTime": "3:00 CT", "daysInTransit": 2 },
      { "warehouseAbbr": "NV", "cutOffTime": "2:00 PT", "daysInTransit": 4 }
    ]
  }
]
```

---

## Cross-Reference (Custom SKU Mapping)

Map your own SKU numbers to S&S SKUs.

### Get Cross-References

**GET** `/v2/crossref/`

| Filter | URL Pattern |
|--------|-------------|
| All | `/v2/crossref/` |
| By YourSku | `/v2/crossref/{yourSku}` |
| Field selection | `?fields=YourSku,BrandName,StyleName,ColorName,SizeName` |

### Response

```json
[
  {
    "yourSku": "G2000whtxl",
    "skuID": 2345,
    "sku": "B00760003",
    "gtin": "00821780003735",
    "brandName": "Gildan",
    "styleName": "2000",
    "colorName": "White",
    "sizeName": "S"
  }
]
```

### Create/Update Cross-Reference

**PUT** `/v2/crossref/`

### Delete Cross-Reference

**DELETE** `/v2/crossref/{yourSku}`
