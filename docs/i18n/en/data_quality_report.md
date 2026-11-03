# Data Quality Report

**Date:** 2026-11-03
**Directory:** `emporio_musica/data`

## Counts

| File | Records |
|---|---:|
| categories | 9 |
| products | 65 |
| customers | 50 |
| orders | 20 |
| order_items | 22 |
| promotions | 25 |

## Findings

| Severity | Category | Description |
|---|---|---|
| warning | duplicate | Duplicate e-mails: 11 (bruno.martins@jmail.com), 43 (bruno.martins@jmail.com) |
| warning | inventory | Active products with zero stock: 96 |
| warning | total | Order 3: charged total 3450.00 differs from the item sum 3498.00. |
| warning | total | Order 20: charged total 1400.00 differs from the item sum 1488.00. |
| info | description | Product 135 has a potentially divergent name and description; keep the name as the canonical source. |
| info | description | Product 136 has a potentially divergent name and description; keep the name as the canonical source. |
| info | description | Product 137 has a potentially divergent name and description; keep the name as the canonical source. |
| info | description | Product 138 has a potentially divergent name and description; keep the name as the canonical source. |
| info | description | Product 139 has a potentially divergent name and description; keep the name as the canonical source. |
| info | description | Product 140 has a potentially divergent name and description; keep the name as the canonical source. |
| info | description | Product 141 has a potentially divergent name and description; keep the name as the canonical source. |
| info | description | Product 142 has a potentially divergent name and description; keep the name as the canonical source. |
| info | description | Product 143 has a potentially divergent name and description; keep the name as the canonical source. |
| info | description | Product 144 has a potentially divergent name and description; keep the name as the canonical source. |
| info | promotion | Active promotions: 127 (10%), 121 (20%), 90 (18%), 94 (8%) |

## Handling assumptions

- Structured fields (`name`, `price_brl`, `stock_quantity`, `status`) prevail over descriptions.
- `is_active` indicates an active promotion; the CSV has no expiration date.
- An active product with zero stock is treated as temporarily unavailable.
- `orders.total_brl` is the charged amount, even when it differs from the sum of the items.
- Duplicate e-mails are not merged.
- Customers have no ZIP code; shipping outside the metropolitan area is by quote.
