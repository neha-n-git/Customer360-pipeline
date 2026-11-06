
from pathlib import Path

import pandas as pd


def load_csv(file_path: str | Path) -> pd.DataFrame:
    """Load customer order summaries from a CSV file."""

    return pd.read_csv(
        file_path,
        dtype={"cust_id": "string"}
    )
