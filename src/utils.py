import json
import logging
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def configure_logging(name="customer360", batch_id=None, run_id=None):
    config = load_config()
    log_dir = PROJECT_ROOT / config["paths"].get("logs", "logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    suffix = batch_id or "pipeline"
    log_path = log_dir / f"{suffix}.log"
    if not any(
        isinstance(handler, logging.FileHandler)
        and Path(handler.baseFilename) == log_path
        for handler in logger.handlers
    ):
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s"
        ))
        logger.addHandler(handler)

    if run_id:
        logger = logging.LoggerAdapter(logger, {
            "context": f"batch={batch_id} run={run_id}",
        })
    return logger


def load_config():
    """Load pipeline configuration from the project config folder."""

    config_path = PROJECT_ROOT / "config" / "pipeline_config.json"

    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)
