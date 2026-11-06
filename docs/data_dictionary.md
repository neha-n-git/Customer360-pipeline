# Data Dictionary — Customer 360 Pipeline

## 1. Source Datasets

### CRM — `crm_customers.json`

| Source field | Standardized field | Type | Description |
|---|---|---|---|
| customer_id | customer_id | String | Customer identifier; master key |
| name | name | String | Customer full name |
| email | email | String / Null | Lowercase, validated email; invalid values are nullified |
| city | city | String / Null | Registered city; missing values are flagged |
| registration_date | registration_date | Date | Customer registration date |

### Orders — `orders.csv`

| Source field | Standardized field | Type | Description |
|---|---|---|---|
| cust_id | customer_id | String | CRM customer identifier |
| total_orders | total_orders | Nullable Integer | Customer's aggregate order count |
| lifetime_value | lifetime_value | Nullable Decimal | Customer-level aggregate lifetime value |
| last_order_date | last_order_date | Date / Null | Most recent order date |

### Support — `support_tickets.xml`

| Source field | Standardized field | Type | Description |
|---|---|---|---|
| customerId | customer_id | String | CRM customer identifier |
| tickets | support_tickets | Nullable Integer | Aggregate support ticket count |
| lastTicketDate | last_ticket_date | Date / Null | Most recent support ticket date |

## 2. Customer 360 Schema

| Field | Type | Source | Description |
|---|---|---|---|
| customer_id | String | CRM | Unique customer key |
| name | String | CRM | Customer full name |
| email | String / Null | CRM | Validated email; invalid/missing email is null |
| city | String / Null | CRM | Registered city |
| registration_date | Date | CRM | Registration date |
| total_orders | Nullable Integer | Orders | Zero only when no Orders record exists; null when unknown/incomplete |
| lifetime_value | Nullable Decimal | Orders | Zero only when no Orders record exists; null when unknown/quarantined |
| last_order_date | Date / Null | Orders | Most recent order date |
| support_tickets | Nullable Integer | Support | Zero only when no Support record exists; null when unknown/quarantined |
| last_ticket_date | Date / Null | Support | Most recent ticket date |
| customer_segment | String | Derived | Gold, Silver, Bronze or Unknown |
| orders_status | String | Derived | AVAILABLE, NO_RECORD, INCOMPLETE or QUARANTINED |
| support_status | String | Derived | AVAILABLE, NO_RECORD, INCOMPLETE or QUARANTINED |

## 3. Metadata

| Field | Type | Description |
|---|---|---|
| source_file | String | Original source filename |
| ingestion_timestamp | Timestamp | Ingestion timestamp |
| batch_id | String | Logical delivery/batch identifier |
| run_id | String | Unique pipeline execution identifier |
| quality_status | String | VALID, CORRECTED or REJECTED |
| rejection_reason | String / Null | Explicit quarantine reason |
| validation_timestamp | Timestamp | Time validation was performed |

Metadata may be retained in intermediate and quarantine datasets even when not exposed in the final customer-facing Gold schema.

## 4. Type and Null Conventions
- IDs are strings.
- Dates are date values internally and `YYYY-MM-DD` when serialized.
- Monetary values use decimal/numeric types, not binary floating-point for financial precision where practical.
- Counts are integers and must be non-negative.
- Null means unknown, unavailable or not supplied; it is not interchangeable with zero.
- Zero is used for counts/value only when the business rules explicitly define a missing source record as zero.
