import argparse
import shutil
from uuid import uuid4

import pandas as pd

from src.utils import PROJECT_ROOT
from src.utils import load_config
from src.transformation.standardize import (
    standardize_crm,
    standardize_orders,
    standardize_support
)
from src.transformation.silver import (
    clean_crm,
    clean_orders,
    clean_support
)
from src.quality.validators import validate_batch


def run_silver(batch_id):
    # Prevent unsafe folder names.
    from pathlib import Path

    if (
        not batch_id
        or Path(batch_id).name != batch_id
        or batch_id in {".", ".."}
    ):
        raise ValueError("Invalid batch ID")

    bronze_dir = PROJECT_ROOT / "data" / "bronze" / batch_id
    silver_root = PROJECT_ROOT / "data" / "silver"
    final_dir = silver_root / batch_id

    if not bronze_dir.is_dir():
        raise FileNotFoundError(f"Bronze batch not found: {bronze_dir}")

    if final_dir.exists():
        raise FileExistsError(
            f"Silver batch already exists: {final_dir}"
        )

    # Read Bronze Parquet files.
    crm = pd.read_parquet(bronze_dir / "crm_customers.parquet")
    orders = pd.read_parquet(bronze_dir / "orders.parquet")
    support = pd.read_parquet(bronze_dir / "support_tickets.parquet")

    # Standardize source schemas and data types.
    crm = standardize_crm(crm)
    orders = standardize_orders(orders)
    support = standardize_support(support)

    # Validate before applying cleaning rules.
    config = load_config()
    issues = validate_batch(
        crm,
        orders,
        support,
        config["quality"]["customer_id_pattern"],
    )

    # Apply Silver transformations.
    clean_crm_df, crm_conflicts = clean_crm(
        crm,
        config["quality"]["customer_id_pattern"],
    )
    clean_orders_df, orders_quarantine = clean_orders(
        orders,
        config["quality"]["customer_id_pattern"],
    )
    clean_support_df, support_quarantine = clean_support(
        support,
        config["quality"]["customer_id_pattern"],
    )

    valid_crm_ids = set(clean_crm_df["customer_id"].dropna())

    unmatched_orders = clean_orders_df[
        ~clean_orders_df["customer_id"].isin(valid_crm_ids)
    ].copy()
    unmatched_orders["quarantine_reason"] = (
        config["quality"]["unmatched_reason"]
    )
    clean_orders_df = clean_orders_df[
        clean_orders_df["customer_id"].isin(valid_crm_ids)
    ].copy()
    if not unmatched_orders.empty:
        orders_quarantine = pd.concat(
            [orders_quarantine, unmatched_orders],
            ignore_index=True
        )

    unmatched_support = clean_support_df[
        ~clean_support_df["customer_id"].isin(valid_crm_ids)
    ].copy()
    unmatched_support["quarantine_reason"] = (
        config["quality"]["unmatched_reason"]
    )
    clean_support_df = clean_support_df[
        clean_support_df["customer_id"].isin(valid_crm_ids)
    ].copy()
    if not unmatched_support.empty:
        support_quarantine = pd.concat(
            [support_quarantine, unmatched_support],
            ignore_index=True
        )

    # Create a staging directory so incomplete output isn't published.
    silver_root.mkdir(parents=True, exist_ok=True)
    staging_dir = silver_root / f".{batch_id}.{uuid4()}.tmp"
    staging_dir.mkdir()

    try:
        quarantine_dir = staging_dir / "quarantine"
        quarantine_dir.mkdir()

        # Write trusted Silver datasets.
        clean_crm_df.to_parquet(
            staging_dir / "crm_customers.parquet",
            index=False
        )
        clean_orders_df.to_parquet(
            staging_dir / "orders.parquet",
            index=False
        )
        clean_support_df.to_parquet(
            staging_dir / "support_tickets.parquet",
            index=False
        )

        # Preserve the complete validation report.
        issues.to_parquet(
            staging_dir / "quality_issues.parquet",
            index=False
        )

        # Write quarantined records separately.
        crm_conflicts.to_parquet(
            quarantine_dir / "crm_conflicts.parquet",
            index=False
        )
        orders_quarantine.to_parquet(
            quarantine_dir / "orders.parquet",
            index=False
        )
        support_quarantine.to_parquet(
            quarantine_dir / "support.parquet",
            index=False
        )

        # Publish the completed Silver batch.
        staging_dir.rename(final_dir)

    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        raise

    print("\n========== SILVER LAYER REPORT ==========")
    print(f"Batch ID: {batch_id}")

    print("\nTrusted Silver records:")
    print(f"CRM: {len(clean_crm_df)}")
    print(f"Orders: {len(clean_orders_df)}")
    print(f"Support: {len(clean_support_df)}")

    print("\nQuarantined records:")
    print(f"CRM conflicts: {len(crm_conflicts)}")
    print(f"Orders: {len(orders_quarantine)}")
    print(f"Support: {len(support_quarantine)}")

    print(f"\nQuality issues recorded: {len(issues)}")
    print(f"Silver output: {final_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build the Silver layer for a data batch"
    )
    parser.add_argument(
        "batch_id",
        help="Name of the Bronze batch to process"
    )

    args = parser.parse_args()
    run_silver(args.batch_id)