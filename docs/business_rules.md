# Business Rules — Customer 360 Pipeline

## 1. Customer Master
- CRM is the master customer dataset.
- Each unique, valid `customer_id` represents one customer.
- Orders and Support records must match a CRM customer.
- Unmatched Orders and Support records are quarantined with reason `UNMATCHED_CUSTOMER_ID`; they do not create customer profiles.
- Customer 360 retains all usable CRM customers, including customers without Orders or Support records.
- A CRM record with an unusable/missing customer ID cannot be included in Customer 360.

## 2. Missing Records vs Missing Fields
- No matching Orders record: `total_orders = 0`, `lifetime_value = 0`, `last_order_date = null`.
- No matching Support record: `support_tickets = 0`, `last_ticket_date = null`.
- A present but invalid or quarantined source record is not treated as an absent record.
- Missing individual fields are handled according to field-level validation rules and must not be silently converted to zero.

## 3. Duplicate CRM Records
- Identify duplicates by normalized `customer_id`.
- Exact duplicate business records: retain one deterministic copy and report the duplicate count.
- Conflicting records for the same customer ID: quarantine all records for that ID. Do not arbitrarily select a winner or merge fields.
- Record duplicate IDs, conflict status, source rows/files and resolution action in the quality report.
- This conservative policy avoids inventing a customer profile from conflicting source values.

## 4. Data Standardization
- Standardize source identifier columns to `customer_id`.
- Trim leading/trailing whitespace from strings.
- Normalize email addresses to lowercase.
- Convert blank and whitespace-only strings to null.
- Parse dates to date values; serialize dates as `YYYY-MM-DD`.
- Convert counts to non-negative integers.
- Convert lifetime value to a numeric decimal type.
- Preserve identifiers as strings.

## 5. Data Quality and Handling
- Validate customer IDs before joins. The expected pattern must be configurable and confirmed against the source specification.
- CRM `customer_id`, `name`, and `registration_date` are mandatory. Missing or invalid values make the record unusable and it is quarantined.
- `city` is required for regional reporting. If missing, retain an otherwise usable customer but flag the missing city; exclude it from city-grouped reporting or report it under an explicit Unknown category.
- `email` is optional. Invalid email is set to null, the issue is recorded, and the otherwise usable customer is retained.
- Orders `customer_id` is mandatory. `total_orders` must be a non-negative integer when present. `lifetime_value` must be numeric and non-negative when present. Invalid negative values cause the Orders record to be quarantined.
- Missing `total_orders` or `lifetime_value` in a present Orders record is an incomplete record, not a missing Orders record. Preserve valid fields and leave missing fields null.
- Support `customer_id` is mandatory. `support_tickets` must be a non-negative integer. Invalid negative counts cause the Support record to be quarantined.
- Invalid dates and invalid mandatory identifiers are quarantined. Missing optional dates remain null.
- Recoverable standardizations (trimming, casing, blank-to-null) are counted and traceable.
- Every quarantined record retains its original record and a clear rejection reason.
- Run source-level and cross-source checks.

## 6. Customer Segmentation
- Gold: `lifetime_value > 100000`.
- Silver: `50000 <= lifetime_value <= 100000`.
- Bronze: `lifetime_value < 50000`.
- A customer with no Orders record has lifetime value zero and is Bronze.
- A customer with unknown lifetime value because the Orders record was quarantined or the value is missing is Unknown.
- Segmentation thresholds are configurable.

## 7. Revenue
- `lifetime_value` is the customer-level aggregate supplied by the Orders dataset.
- It is the revenue measure for customer-level and city-level reporting; it is not transaction-level or monthly revenue.
- Only valid, matched lifetime values contribute to revenue.
- Unmatched Orders records are excluded and reported separately.
- A present Orders record with a valid lifetime value but missing order count may still contribute its lifetime value.
- A quarantined or unknown lifetime value is excluded from revenue totals and averages.
- Customers with no Orders record contribute zero.

## 8. Support Analysis
- High-support customers have more than five support tickets.
- Ticket volume measures support demand; it does not by itself establish dissatisfaction.
- Only valid, matched Support records contribute to support metrics.

## 9. Reporting and Execution
- Generate outputs for each batch, with batch ID and execution timestamp.
- Generate detailed quality issues and an aggregate JSON quality summary.
- Distinguish valid, corrected, rejected, duplicate and unmatched records.
- Keep business thresholds, ID patterns, paths and other configurable parameters outside transformation logic.
- Gold outputs and KPI reports must be derived from the same validated batch.
