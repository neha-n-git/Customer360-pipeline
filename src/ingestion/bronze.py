from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import shutil

from src.ingestion.json_loader import load_json
from src.ingestion.csv_loader import load_csv
from src.ingestion.xml_loader import load_xml


def add_metadata(df, source_file, batch_id, run_id, timestamp):
    """Attach ingestion metadata to a DataFrame."""

    df = df.copy()

    df["source_file"] = source_file
    df["ingestion_timestamp"] = timestamp
    df["batch_id"] = batch_id
    df["run_id"] = run_id

    return df


def ingest_to_bronze(config, project_root, batch_id):
    """Load one source batch and safely publish it to Bronze."""

    # Identify the input and output directories
    raw_dir = project_root / config["paths"]["raw"] / batch_id
    bronze_dir = project_root / config["paths"]["bronze"]

    final_dir = bronze_dir / batch_id

    # Check that the input batch exists
    if not raw_dir.is_dir():
        raise FileNotFoundError(
            f"Raw batch directory not found: {raw_dir}"
        )

    # Prevent accidental overwriting
    if final_dir.exists():
        raise FileExistsError(
            f"Bronze batch already exists: {final_dir}"
        )

    # Create Bronze directory
    bronze_dir.mkdir(parents=True, exist_ok=True)

    # Identify this execution attempt
    run_id = str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    # Load source datasets
    crm = load_json(raw_dir / config["sources"]["crm"])
    orders = load_csv(raw_dir / config["sources"]["orders"])
    support = load_xml(raw_dir / config["sources"]["support"])

    datasets = {
        "crm_customers": (crm, config["sources"]["crm"]),
        "orders": (orders, config["sources"]["orders"]),
        "support_tickets": (support, config["sources"]["support"])
    }

    # Write into a temporary directory first
    staging_dir = bronze_dir / f".{batch_id}.{run_id}.tmp"
    staging_dir.mkdir(parents=True)

    try:
        for dataset_name, (df, source_file) in datasets.items():

            df = add_metadata(
                df,
                source_file,
                batch_id,
                run_id,
                timestamp
            )

            output_path = staging_dir / f"{dataset_name}.parquet"

            df.to_parquet(output_path, index=False)

            print(f"Saved {dataset_name}: {len(df)} records")

        # Publish only after all three writes succeed
        staging_dir.rename(final_dir)

    except Exception:
        # Remove incomplete output if anything fails
        if staging_dir.exists():
            shutil.rmtree(staging_dir)

        raise

    print(f"\nBronze ingestion completed.")
    print(f"Batch ID: {batch_id}")
    print(f"Run ID: {run_id}")

    return {
        "batch_id": batch_id,
        "run_id": run_id
    }