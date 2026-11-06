# KPI Definitions — Customer 360 Pipeline

## 1. Customer Metrics

| KPI | Definition |
|---|---|
| Total Customers | Count of unique usable CRM customers in Customer 360 |
| Customers with Orders | CRM customers with a valid matched Orders record |
| Customers without Orders | CRM customers with no matching Orders source record |
| Average Customer Lifetime Value | Sum of known valid customer lifetime values divided by customers with known lifetime value; customers with no Orders record contribute zero; unknown/quarantined values are excluded from numerator and denominator |
| Average Value per Purchasing Customer | Sum of known valid lifetime value divided by customers with a valid matched Orders record and known lifetime value |

## 2. Revenue Metrics

| KPI | Definition |
|---|---|
| Total Revenue | Sum of known valid lifetime values matched to CRM |
| Top 10 Customers | Ten customers ranked by known lifetime value descending; use customer_id ascending as deterministic tie-breaker |
| Revenue by City | Sum of known valid lifetime values grouped by CRM city |
| Revenue Contribution by City | City revenue divided by total known valid revenue × 100 |
| Average Order Value | Sum of known valid lifetime value divided by sum of known valid order counts for customers with `total_orders > 0`; exclude missing order counts |
| Revenue Concentration | Sum of the top 10 customers' known lifetime values divided by total known valid revenue × 100 |

Lifetime value is a customer-level aggregate, not transaction-level or monthly sales data.

## 3. Segmentation

- Gold: lifetime value > 100000.
- Silver: 50000 <= lifetime value <= 100000.
- Bronze: lifetime value < 50000.
- No Orders source record means lifetime value zero and Bronze.
- Unknown/quarantined lifetime value means Unknown.

For each segment report customer count, percentage of eligible customers, known lifetime value total, revenue contribution and average known order count. Unknown values must not be silently counted as zero.

## 4. Regional Metrics

| KPI | Definition |
|---|---|
| Customer Count by City | Count of usable CRM customers grouped by city; report missing city separately |
| Revenue by City | Sum of known valid lifetime value grouped by CRM city |
| Average Customer Value by City | Known lifetime value total divided by customers with known lifetime value in that city |
| Average Orders by City | Average of non-null total_orders for customers in that city |
| Segment Distribution by City | Customer count by city and segment, including Unknown where applicable |

## 5. Support Metrics

| KPI | Definition |
|---|---|
| Total Support Tickets | Sum of valid matched support ticket counts |
| Average Tickets per Customer | Total valid matched tickets divided by usable CRM customer count |
| High-Support Customers | Customers with more than five valid matched support tickets |
| Support Tickets by City | Sum of valid matched support tickets grouped by CRM city |
| Customer Value vs Support Volume | Comparison using known lifetime value and valid support ticket counts; do not infer dissatisfaction from ticket volume alone |

## 6. Data Quality Metrics

| KPI | Definition |
|---|---|
| Total Records Processed | Total source records ingested across CRM, Orders and Support |
| Valid Records | Distinct records passing required validation checks |
| Corrected Records | Distinct records with recoverable standardization corrections |
| Rejected Records | Distinct records quarantined; multiple issue rows count as one rejected record |
| Duplicate CRM Records | Extra CRM rows beyond one per duplicate customer ID |
| Unmatched Records | Orders/Support records referencing IDs absent from CRM |
| Data Quality Rate | Per-source passing records divided by records evaluated × 100 |

## 7. Calculation Notes
- Revenue uses matched, valid, known lifetime values only.
- A customer with no Orders record contributes zero; a customer with unknown value does not.
- Average Order Value excludes customers with missing order counts and zero order counts.
- Percentages must use explicitly stated populations.
- Guard against division by zero; return null or a documented not-applicable value.
- All KPIs in a report must use the same batch ID and run ID.
