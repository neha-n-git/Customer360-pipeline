
from pathlib import Path

from src.ingestion.json_loader import load_json
from src.ingestion.csv_loader import load_csv
from src.ingestion.xml_loader import load_xml


RAW_DIR = Path("data/raw")


def test_json_loader():
    df = load_json(RAW_DIR / "crm_customers.json")

    assert not df.empty
    assert "customer_id" in df.columns
    print("\nCRM data:")
    print(df.head())


def test_csv_loader():
    df = load_csv(RAW_DIR / "orders.csv")

    assert not df.empty
    assert "cust_id" in df.columns
    assert str(df["cust_id"].dtype) == "string"
    print("\nOrders data:")
    print(df.head())


def test_xml_loader():
    df = load_xml(RAW_DIR / "support_tickets.xml")

    assert not df.empty
    assert "customerId" in df.columns
    print("\nSupport data:")
    print(df.head())
