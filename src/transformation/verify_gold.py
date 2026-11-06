import argparse
import pandas as pd

from src.utils import PROJECT_ROOT


def verify_gold(batch_id):
    gold_dir = PROJECT_ROOT / "data" / "gold" / batch_id

    if not gold_dir.is_dir():
        raise FileNotFoundError(f"Gold batch not found: {gold_dir}")

    df = pd.read_parquet(gold_dir / "customer_360.parquet")

    print("\n========== GOLD DATA VERIFICATION ==========")

    # 1. Customer population and uniqueness
    print("\n1. Customer population")
    print("Total records:", len(df))
    print("Unique customers:", df["customer_id"].nunique())
    print("Duplicate IDs:", df["customer_id"].duplicated().sum())

    # 2. C0310: incomplete Orders record
    print("\n2. C0310 - Incomplete Orders")
    record = df[df["customer_id"] == "C0310"]
    print(record[[
        "total_orders", "lifetime_value", "orders_status"
    ]].to_string(index=False))

    # 3. C0420: quarantined Orders record
    print("\n3. C0420 - Quarantined Orders")
    record = df[df["customer_id"] == "C0420"]
    print(record[[
        "total_orders", "lifetime_value",
        "orders_status", "customer_segment"
    ]].to_string(index=False))

    # 4. Customers without Orders records
    print("\n4. Missing Orders records")
    print("Count:", (df["orders_status"] == "NO_RECORD").sum())

    # 5. Customers without Support records
    print("\n5. Missing Support records")
    print("Count:", (df["support_status"] == "NO_RECORD").sum())

    # 6. Check segmentation
    print("\n6. Customer segments")
    print(df["customer_segment"].value_counts(dropna=False))

    print("\nVerification completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verify Gold Customer 360 data"
    )
    parser.add_argument("batch_id")
    args = parser.parse_args()

    verify_gold(args.batch_id)