import argparse
import pandas as pd

from src.utils import PROJECT_ROOT


def verify_silver(batch_id):
    silver_dir = PROJECT_ROOT / "data" / "silver" / batch_id

    if not silver_dir.is_dir():
        raise FileNotFoundError(
            f"Silver batch not found: {silver_dir}"
        )

    crm = pd.read_parquet(
        silver_dir / "crm_customers.parquet"
    )
    orders = pd.read_parquet(
        silver_dir / "orders.parquet"
    )
    quarantine = pd.read_parquet(
        silver_dir / "quarantine" / "orders.parquet"
    )

    print("\n========== SILVER DATA VERIFICATION ==========")

    print("\n1. CRM duplicate check")
    print(
        "C0105 occurrences:",
        (crm["customer_id"] == "C0105").sum()
    )

    print("\n2. Invalid email handling")
    for customer_id in ["C0125", "C0250", "C0375"]:
        record = crm[crm["customer_id"] == customer_id]
        email = record["email"].iloc[0] if not record.empty else "NOT FOUND"
        print(f"{customer_id} email: {email}")

    print("\n3. Missing order count")
    record = orders[orders["customer_id"] == "C0310"]
    print("C0310 exists:", not record.empty)

    if not record.empty:
        print("C0310 total_orders:", record["total_orders"].iloc[0])

    print("\n4. Quarantine check")
    print(
        "C0420 quarantined:",
        (quarantine["customer_id"] == "C0420").any()
    )
    print(
        "C0420 in trusted Orders:",
        (orders["customer_id"] == "C0420").any()
    )

    print("\nVerification completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verify a Silver data batch"
    )
    parser.add_argument(
        "batch_id",
        help="Silver batch ID to verify"
    )

    args = parser.parse_args()
    verify_silver(args.batch_id)