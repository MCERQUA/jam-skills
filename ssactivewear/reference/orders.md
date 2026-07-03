# S&S Activewear — Orders Reference

## Create Order

**POST** `/v2/orders/`

Content-Type: `application/json` or `application/xml`

### Request Body

```json
{
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
  "testOrder": false,
  "autoselectWarehouse": true,
  "autoselectWarehouse_Warehouses": "IL,KS,GA",
  "AutoSelectWarehouse_Preference": "fewest",
  "AutoSelectWarehouse_Fewest_MaxDIT": 5,
  "lines": [
    {
      "identifier": "B00760004",
      "qty": 24
    },
    {
      "identifier": "81480",
      "qty": 12,
      "warehouseAbbr": "IL"
    }
  ]
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| address | String | Street address |
| city | String | City |
| state | String | State code |
| zip | String | 5-digit ZIP |
| lines | Array | At least one line item |
| lines[].identifier | String | SkuID_Master, Sku, or GTIN |
| lines[].qty | Integer | Order quantity |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| customer | String | "" | Company/recipient name |
| attn | String | "" | Attention line |
| residential | Boolean | true | Residential address flag |
| shippingMethod | String | "1" | Shipping method code |
| shipBlind | Boolean | account default | Override blind ship setting |
| poNumber | String | "" | Customer PO number |
| emailConfirmation | String | "" | Email for order confirmation |
| testOrder | Boolean | false | Creates then cancels (no charge) |
| shipByDate | String | — | Format: MM/DD/YYYY |
| autoselectWarehouse | Boolean | false | Let system choose warehouse |
| autoselectWarehouse_Warehouses | String | all | Comma-separated warehouse codes |
| AutoSelectWarehouse_Preference | String | "fewest" | "fewest" shipments or "fastest" delivery |
| AutoSelectWarehouse_Fewest_MaxDIT | Integer | 10 | Max transit days (fewest mode) |
| promotionCode | String | — | Discount promotion code |
| rejectLineErrors | Boolean | true | Reject entire order if any item unavailable |
| rejectLineErrors_Email | Boolean | true | Email about unfillable items |
| lines[].warehouseAbbr | String | — | Specific warehouse for this item |

### Shipping Methods

| Code | Method |
|------|--------|
| 1 | Ground |
| 6 | Will Call / PickUp |
| 8 | Messenger Pickup |
| 40 | UPS Ground |
| 54 | Misc Cheapest |
| 81 | Purolator Ground |
| 82 | Purolator Express |
| 83 | Purolator Express 12PM |
| 91 | UPS Express Saver |

**Note:** Orders over 1000 lbs automatically use Echo Logistics LTL freight.

### Payment

```json
{
  "paymentProfile": {
    "email": "account@example.com",
    "profileID": 123456789
  }
}
```

Get profileID from: `GET /v2/paymentprofiles/{email}`

### Response

Returns array of order objects (multiple if items ship from different warehouses):

```json
[
  {
    "guid": "54d61c23-2b42-4021-ae34-5e6bba9eb36a",
    "orderNumber": "61519822",
    "customerNumber": "123456",
    "orderDate": "2024-01-15T10:30:00",
    "expectedDeliveryDate": "2024-01-19T00:00:00",
    "orderStatus": "In Progress",
    "shippingCarrier": "UPS",
    "shippingMethod": "Ground",
    "shippingAddress": {
      "customer": "Company Name",
      "attn": "John Doe",
      "address": "123 Main St",
      "city": "Chicago",
      "state": "IL",
      "zip": "60601"
    },
    "subtotal": 120.00,
    "shipping": 12.50,
    "tax": 0.00,
    "total": 132.50,
    "lines": [
      {
        "lineNumber": 1,
        "sku": "B00760004",
        "gtin": "00821780001001",
        "qtyOrdered": 24,
        "price": 5.00,
        "brandName": "Gildan",
        "styleName": "2000",
        "colorName": "White",
        "sizeName": "L",
        "returnable": true
      }
    ]
  }
]
```

---

## Get Orders

**GET** `/v2/orders/`

### Filtering

| Filter | URL Pattern | Description |
|--------|-------------|-------------|
| Open orders | `/v2/orders/` | Not yet invoiced |
| All (3 months) | `/v2/orders/?All=True` | Open + invoiced |
| By identifier | `/v2/orders/{id}` | PONumber, OrderNumber, InvoiceNumber, or GUID |
| By invoice date | `?invoicedate=YYYY-MM-DD` | Single or comma-separated dates |
| By date range | `?invoicestartdate=...&invoiceenddate=...` | Date range filter |
| By barcode | `?shippinglabelbarcode=VALUE` | Format: InvoiceNumber.BoxNumberLane |
| Include lines | `?lines=true` | Add line item details |
| Include boxes | `?Boxes=true` | Add box information |
| Include billing | `?Billing=true` | Add billing address |
| AR child invoices | `?includeARChildInvoices=true` | Parent + child account orders |
| Field selection | `?fields=FIELD1,FIELD2` | Return only specified fields |

### Order Response Fields

**Core:**
`guid`, `orderNumber`, `invoiceNumber`, `poNumber`, `customerNumber`, `orderDate`, `shipDate`, `invoiceDate`, `orderType` (CSR/Web/EDI/Credit), `orderStatus`, `terms`

**Company/Warehouse:**
`companyName`, `warehouseAbbr`

**Shipping:**
`shippingCarrier`, `shippingMethod`, `trackingNumber`, `shipBlind`, `dropship`, `deliveryStatus` (Picked Up/In Transit/Out For Delivery/Delivered/Exception), `shippingAddress` object

**Financial:**
`subtotal`, `shipping`, `shippingSaved`, `tax`, `cod`, `smallOrderFee`, `cuponDiscount`, `sampleDiscount`, `setUpFee`, `restockFee`, `debitCredit`, `total`

**Metrics:**
`totalPieces`, `totalLines`, `totalWeight`, `totalBoxes`

**Lines (when `?lines=true`):**
`lineNumber`, `type` (S/NS), `skuID`, `sku`, `gtin`, `yourSku`, `qtyOrdered`, `qtyShipped`, `price`, `brandName`, `styleName`, `title`, `colorName`, `sizeName`, `returnable`

---

## Delete Order

**DELETE** `/v2/orders/{orderNumber}`

Cancels an open order. Only works on orders not yet shipped.

---

## Payment Profiles

**GET** `/v2/paymentprofiles/{email}`

Returns saved payment methods for an account email.

```json
[
  {
    "profileID": 123456789,
    "profileType": "Credit Card",
    "name": "BMO Harris Bank 1234 (John Doe)"
  }
]
```

---

## Invoices

**GET** `/v2/invoices/{invoiceNumber}`

Returns PDF invoice document.

| Filter | URL Pattern |
|--------|-------------|
| By invoice | `/v2/invoices/{invoiceNumber}` |
| By GUID | `/v2/invoices/?Guid={guid}` |
| By order | `/v2/invoices/?OrderNumber={orderNumber}` |

Response: `application/pdf` attachment.

---

## Test Order Pattern

Set `testOrder: true` to validate an order without actually placing it. The order is created and immediately cancelled — no charge.

```bash
curl -u "$SS_ACCOUNT:$SS_API_KEY" \
  -X POST "https://api-ca.ssactivewear.com/v2/orders/" \
  -H "Content-Type: application/json" \
  -d '{
    "address": "123 Test St",
    "city": "Chicago",
    "state": "IL",
    "zip": "60601",
    "testOrder": true,
    "lines": [
      { "identifier": "B00760004", "qty": 1 }
    ]
  }'
```
