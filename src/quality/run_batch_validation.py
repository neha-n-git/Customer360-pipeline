
import pandas as pd

from src.utils import PROJECT_ROOT
from src.transformation.standardize import (
    standardize_crm,
    standardize_orders,
    standardize_support
)
from src.quality.validators import validate_batch


BATCH_ID = "batch_2026_11_06_001"

bronze_dir = (
    PROJECT_ROOT / "data" / "bronze" / BATCH_ID
)

# Read Bronze datasets
crm = pd.read_parquet(bronze_dir / "crm_customers.parquet")
orders = pd.read_parquet(bronze_dir / "orders.parquet")
support = pd.read_parquet(bronze_dir / "support_tickets.parquet")

# Standardize each dataset
crm = standardize_crm(crm)
orders = standardize_orders(orders)
support = standardize_support(support)

# Execute reusable validation rules
issues = validate_batch(crm, orders, support)

print("\n========== BATCH VALIDATION REPORT ==========")

print(f"Batch ID: {BATCH_ID}")
print(f"CRM records: {len(crm)}")
print(f"Orders records: {len(orders)}")
print(f"Support records: {len(support)}")

print(f"\nTotal quality issues: {len(issues)}")

if not issues.empty:

    print("\nIssues by source:")
    print(issues.groupby("source").size())

    print("\nIssues by severity:")
    print(issues.groupby("severity").size())

    print("\nDetailed issues:")
    print(
        issues[
            [
                "source",
                "record_key",
                "column",
                "rejected_value",
                "reason",
                "severity"
            ]
        ].to_string(index=False)
    )

else:
    print("\nNo quality issues detected.")
