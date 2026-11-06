# Data Quality Framework — Customer 360 Pipeline

## 1. Quality States
- **VALID:** Passes all applicable validation checks.
- **CORRECTED:** A recoverable representation issue was standardized (for example, whitespace, email casing or blank-to-null); correction is traceable.
- **REJECTED:** The record is unusable for its intended dataset and is quarantined with one or more explicit reasons.
- **INCOMPLETE:** A source record exists but one or more non-key fields are missing. Valid fields may still be used where permitted by business rules.

A record may have multiple issue rows but must be counted only once in record-level valid/rejected totals.

## 2. CRM Checks

| Check | Rule | Handling |
|---|---|---|
| Customer ID | Present, non-empty and matches configurable pattern | Reject if missing/invalid |
| Name | Present and non-empty | Reject if missing |
| Email | Valid format when present | Nullify invalid value and record issue |
| City | Present for regional reporting | Retain customer, flag missing city |
| Registration date | Valid date and not an impossible/future value under configured policy | Reject invalid date |
| Duplicate ID | Repeated normalized customer ID | Deduplicate exact copies; quarantine conflicting group |

## 3. Orders Checks

| Check | Rule | Handling |
|---|---|---|
| Customer ID | Present and valid format | Reject if missing/invalid |
| Total orders | Non-negative integer when present | Reject invalid/fractional/negative value |
| Lifetime value | Numeric and non-negative when present | Reject negative or non-numeric value |
| Last order date | Valid date when present | Reject invalid date |
| Duplicate customer ID | One customer-level summary expected | Investigate/quarantine duplicates; do not arbitrarily aggregate |

A missing field in an otherwise present Orders record is not equivalent to no Orders record. Preserve valid fields and mark the record incomplete.

## 4. Support Checks

| Check | Rule | Handling |
|---|---|---|
| Customer ID | Present and valid format | Reject if missing/invalid |
| Ticket count | Non-negative integer | Reject invalid/fractional/negative value |
| Last ticket date | Valid date when present | Reject invalid date |
| Duplicate customer ID | One customer-level summary expected | Investigate/quarantine duplicates; do not arbitrarily aggregate |

## 5. Standardization and Traceability
- Trim strings, normalize email casing, standardize identifier column names, parse dates, convert numeric types and normalize blank strings to null.
- Record correction counts and, where practical, original and standardized values.
- Preserve source filename, batch ID, run ID and original source record for quarantined records.
- Every rejected record must have an explicit reason code and readable description.

## 6. Cross-Source Checks
- Orders and Support customer IDs must exist in CRM.
- Unmatched source records are quarantined as `UNMATCHED_CUSTOMER_ID`.
- Missing Orders/Support records for a valid CRM customer are not errors.
- A present but quarantined source record must remain distinguishable from an absent source record.
- Validate uniqueness before one-to-one joins.

## 7. Quality Metrics
Generate metrics by source and for the batch:
- Total records ingested/evaluated.
- Valid, corrected, incomplete and rejected record counts.
- Duplicate CRM rows and conflicting duplicate groups.
- Unmatched Orders and Support records.
- Missing values by important field.
- Invalid email count.
- Rejection counts by reason.
- Overall and per-source quality rates.

Record-level counts must be mutually interpretable: multiple issues on one record do not multiply the rejected-record count. Define the quality-rate denominator explicitly in the report; recommended per-source formula is:

`quality_rate = records_passing_required_checks / total_records_evaluated * 100`

Also report corrected and incomplete records separately so the rate is not misleading.

## 8. Outputs
- Detailed issues: Parquet.
- Quarantine datasets: Parquet, retaining original record and metadata.
- Aggregate quality summary: JSON, generated for every batch.
- Log validation and pipeline failures without unnecessarily exposing personal data.
