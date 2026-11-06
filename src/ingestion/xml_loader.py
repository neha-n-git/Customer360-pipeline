
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd


def load_xml(file_path: str | Path) -> pd.DataFrame:
    """Load customer support records from an XML file."""

    tree = ET.parse(file_path)
    root = tree.getroot()

    records = []

    for customer in root.findall(".//customer"):
        records.append({
            "customerId": customer.findtext("customerId"),
            "tickets": customer.findtext("tickets"),
            "lastTicketDate": customer.findtext("lastTicketDate")
        })

    return pd.DataFrame(records)
