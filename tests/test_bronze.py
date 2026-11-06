
from pathlib import Path

import pandas as pd

from src.utils import PROJECT_ROOT


def test_bronze_files_exist():

    bronze_dir = PROJECT_ROOT / "data" / "bronze"
    batch_dirs = [path for path in bronze_dir.iterdir() if path.is_dir()]
    assert batch_dirs, "No Bronze batch found"
    latest_batch = max(batch_dirs, key=lambda path: path.stat().st_mtime)

    expected_files = [
        "crm_customers.parquet",
        "orders.parquet",
        "support_tickets.parquet"
    ]

    for filename in expected_files:
        assert (latest_batch / filename).exists()


def test_bronze_metadata():

    bronze_dir = PROJECT_ROOT / "data" / "bronze"
    batch_dirs = [path for path in bronze_dir.iterdir() if path.is_dir()]
    assert batch_dirs, "No Bronze batch found"
    latest_batch = max(batch_dirs, key=lambda path: path.stat().st_mtime)

    df = pd.read_parquet(
        latest_batch / "crm_customers.parquet"
    )

    assert "source_file" in df.columns
    assert "ingestion_timestamp" in df.columns
    assert "batch_id" in df.columns

    assert not df.empty
