import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.analytics.metrics import (
    customer_count_by_city,
    customer_segmentation,
    high_support_customers,
    revenue_by_city,
    top_customers_by_revenue,
)
from src.utils import PROJECT_ROOT


METRIC_OUTPUTS = {
    "top_customers_by_revenue.csv": top_customers_by_revenue,
    "customer_segmentation.csv": customer_segmentation,
    "high_support_customers.csv": high_support_customers,
    "revenue_by_city.csv": revenue_by_city,
    "customer_count_by_city.csv": customer_count_by_city,
}


def run_analytics(batch_id):
    if (
        not batch_id
        or Path(batch_id).name != batch_id
        or batch_id in {".", ".."}
    ):
        raise ValueError("Invalid batch ID")

    gold_path = PROJECT_ROOT / "data" / "gold" / batch_id / "customer_360.parquet"
    output_dir = PROJECT_ROOT / "data" / "analytics" / batch_id
    if not gold_path.is_file():
        raise FileNotFoundError(f"Gold output not found: {gold_path}")
    if output_dir.exists():
        raise FileExistsError(f"Analytics batch already exists: {output_dir}")

    gold = pd.read_parquet(gold_path)
    original_gold = gold.copy(deep=True)
    output_dir.mkdir(parents=True)
    results = {}

    try:
        for filename, metric in METRIC_OUTPUTS.items():
            result = metric(gold)
            result.to_csv(output_dir / filename, index=False)
            results[filename] = len(result)

        if not gold.equals(original_gold):
            raise RuntimeError("Analytics modified the input Gold DataFrame")

        unknown_revenue = int(gold["lifetime_value"].isna().sum())
        duplicate_ids = int(gold["customer_id"].duplicated().sum())
        summary = {
            "batch_id": batch_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "gold_records_read": len(gold),
            "metric_record_counts": results,
            "unknown_lifetime_value_records": unknown_revenue,
            "duplicate_customer_ids_removed_from_metrics": duplicate_ids,
            "excluded_unknown_revenue_reason": (
                "NULL or quarantined lifetime_value excluded from revenue metrics"
            ),
            "output_files": [
                "top_customers_by_revenue.csv",
                "customer_segmentation.csv",
                "high_support_customers.csv",
                "revenue_by_city.csv",
                "customer_count_by_city.csv",
                "execution_summary.json",
            ],
        }
        (output_dir / "execution_summary.json").write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8",
        )
    except Exception:
        for path in output_dir.iterdir():
            if path.is_file():
                path.unlink()
        output_dir.rmdir()
        raise

    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Customer 360 analytics for a Gold batch"
    )
    parser.add_argument("batch_id", help="Gold batch ID to analyze")
    args = parser.parse_args()
    run_analytics(args.batch_id)
