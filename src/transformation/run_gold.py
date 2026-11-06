import argparse
import shutil
from pathlib import Path
from uuid import uuid4

import pandas as pd

from src.utils import PROJECT_ROOT
from src.utils import load_config
from src.transformation.gold import build_customer_360


def run_gold(batch_id):
    if (
        not batch_id
        or Path(batch_id).name != batch_id
        or batch_id in {".", ".."}
    ):
        raise ValueError("Invalid batch ID")

    silver_dir = PROJECT_ROOT / "data" / "silver" / batch_id
    gold_root = PROJECT_ROOT / "data" / "gold"
    final_dir = gold_root / batch_id

    if not silver_dir.is_dir():
        raise FileNotFoundError(f"Silver batch not found: {silver_dir}")

    if final_dir.exists():
        raise FileExistsError(f"Gold batch already exists: {final_dir}")

    # Read trusted Silver datasets.
    crm = pd.read_parquet(silver_dir / "crm_customers.parquet")
    orders = pd.read_parquet(silver_dir / "orders.parquet")
    support = pd.read_parquet(silver_dir / "support_tickets.parquet")

    # Read quarantined records to distinguish invalid from missing data.
    orders_quarantine = pd.read_parquet(
        silver_dir / "quarantine" / "orders.parquet"
    )
    support_quarantine = pd.read_parquet(
        silver_dir / "quarantine" / "support.parquet"
    )

    # Build the Customer 360 dataset.
    config = load_config()
    customer_360 = build_customer_360(
        crm,
        orders,
        support,
        orders_quarantine,
        support_quarantine,
        gold_min=config["segmentation"]["gold_min"],
        silver_min=config["segmentation"]["silver_min"],
    )

    # Stage output before publishing.
    gold_root.mkdir(parents=True, exist_ok=True)
    staging_dir = gold_root / f".{batch_id}.{uuid4()}.tmp"
    staging_dir.mkdir()

    try:
        output_path = staging_dir / "customer_360.parquet"

        customer_360.to_parquet(output_path, index=False)

        staging_dir.rename(final_dir)

    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        raise

    print("\n========== GOLD LAYER REPORT ==========")
    print(f"Batch ID: {batch_id}")
    print(f"Customer 360 records: {len(customer_360)}")

    print("\nOrders status:")
    print(customer_360["orders_status"].value_counts(dropna=False))

    print("\nSupport status:")
    print(customer_360["support_status"].value_counts(dropna=False))

    print("\nCustomer segments:")
    print(customer_360["customer_segment"].value_counts(dropna=False))

    print(f"\nGold output: {final_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build the Gold Customer 360 dataset"
    )
    parser.add_argument(
        "batch_id",
        help="Silver batch ID to process"
    )

    args = parser.parse_args()
    run_gold(args.batch_id)
    