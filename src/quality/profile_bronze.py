from pathlib import Path

import duckdb

from src.utils import PROJECT_ROOT


# Each Bronze dataset and its customer ID column
DATASETS = {
    "crm_customers": {
        "file": "crm_customers.parquet",
        "id_column": "customer_id"
    },
    "orders": {
        "file": "orders.parquet",
        "id_column": "cust_id"
    },
    "support_tickets": {
        "file": "support_tickets.parquet",
        "id_column": "customerId"
    }
}


def quote_identifier(name):
    """Safely quote a SQL column name."""
    return '"' + name.replace('"', '""') + '"'


def profile_dataset(dataset_name, details):
    file_path = PROJECT_ROOT / "data" / "bronze" / details["file"]
    id_column = details["id_column"]

    print("\n" + "=" * 60)
    print(f"DATASET: {dataset_name}")
    print("=" * 60)

    if not file_path.exists():
        raise FileNotFoundError(f"Bronze file not found: {file_path}")

    connection = duckdb.connect()

    # Inspect the schema
    schema = connection.execute(
        "DESCRIBE SELECT * FROM read_parquet(?)",
        [str(file_path)]
    ).df()

    print("\n1. COLUMN NAMES AND DATA TYPES")
    print(schema[["column_name", "column_type"]].to_string(index=False))

    columns = schema["column_name"].tolist()

    if id_column not in columns:
        raise ValueError(
            f"Expected ID column '{id_column}' not found in {dataset_name}"
        )

    # Calculate row count and null count for every column
    null_expressions = [
        f"COUNT(*) - COUNT({quote_identifier(column)}) "
        f"AS {quote_identifier(column + '_nulls')}"
        for column in columns
    ]

    summary_query = f"""
        SELECT
            COUNT(*) AS total_rows,
            {", ".join(null_expressions)}
        FROM read_parquet(?)
    """

    summary = connection.execute(
        summary_query,
        [str(file_path)]
    ).df()

    print("\n2. ROW COUNT AND NULL COUNTS")
    print(summary.to_string(index=False))

    # Check distinct customer IDs
    quoted_id = quote_identifier(id_column)

    id_summary = connection.execute(
        f"""
        SELECT
            COUNT(DISTINCT {quoted_id}) AS unique_customer_ids,
            COUNT(*) - COUNT({quoted_id}) AS missing_customer_ids
        FROM read_parquet(?)
        """,
        [str(file_path)]
    ).df()

    print("\n3. CUSTOMER ID SUMMARY")
    print(id_summary.to_string(index=False))

    # Find duplicate customer IDs
    duplicates = connection.execute(
        f"""
        SELECT
            {quoted_id},
            COUNT(*) AS record_count
        FROM read_parquet(?)
        WHERE {quoted_id} IS NOT NULL
        GROUP BY {quoted_id}
        HAVING COUNT(*) > 1
        ORDER BY record_count DESC
        LIMIT 10
        """,
        [str(file_path)]
    ).df()

    print("\n4. DUPLICATE CUSTOMER IDs (UP TO 10)")
    if duplicates.empty:
        print("No duplicate customer IDs found.")
    else:
        print(duplicates.to_string(index=False))

    connection.close()


def main():
    print("BRONZE DATA PROFILING")

    for dataset_name, details in DATASETS.items():
        profile_dataset(dataset_name, details)

    print("\nProfiling completed.")


if __name__ == "__main__":
    main()