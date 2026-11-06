import argparse

from src.utils import load_config, PROJECT_ROOT, configure_logging
from src.ingestion.bronze import ingest_to_bronze
from src.transformation.run_silver import run_silver
from src.transformation.run_gold import run_gold


def run_pipeline(batch_id):
    logger = configure_logging(batch_id=batch_id)

    print("Starting Customer 360 Pipeline...")
    print(f"Processing batch: {batch_id}")
    logger.info("Starting Customer 360 pipeline batch=%s", batch_id)

    # Load configuration
    config = load_config()

    # Stage 1: Ingestion and Bronze storage
    result = ingest_to_bronze(config, PROJECT_ROOT, batch_id)
    run_id = result["run_id"]
    logger = configure_logging(batch_id=batch_id, run_id=run_id)
    logger.info("Bronze ingestion completed run_id=%s", run_id)

    print("\nStarting Silver transformation...")
    run_silver(batch_id)
    logger.info("Silver transformation completed")

    print("\nStarting Gold transformation...")
    run_gold(batch_id)
    logger.info("Gold transformation completed")

    print("\nPipeline execution completed successfully.")
    print(f"Batch ID: {result['batch_id']}")
    print(f"Run ID: {result['run_id']}")
    logger.info("Pipeline completed run_id=%s", run_id)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Run the Customer 360 Data Pipeline"
    )

    parser.add_argument(
        "batch_id",
        help="Name of the incoming batch folder"
    )

    args = parser.parse_args()

    run_pipeline(args.batch_id)