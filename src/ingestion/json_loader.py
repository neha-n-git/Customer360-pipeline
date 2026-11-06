
import json
from pathlib import Path

import pandas as pd


def load_json(file_path: str | Path) -> pd.DataFrame:
    """Load customer records from a JSON file."""

    file_path = Path(file_path)

    with file_path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError("Expected a JSON array of customer records.")

    return pd.DataFrame(records)
