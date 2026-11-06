
import pandas as pd

from src.transformation.standardize import (
    standardize_crm,
    standardize_orders,
    standardize_support
)


def test_standardize_crm():

    df = pd.DataFrame({
        "customer_id": [" c001 "],
        "name": [" Neha "],
        "email": [" NEHA@EXAMPLE.COM "],
        "city": [" Bangalore "],
        "registration_date": ["2025-06-02"]
    })

    result = standardize_crm(df)

    assert result.loc[0, "customer_id"] == "C001"
    assert result.loc[0, "name"] == "Neha"
    assert result.loc[0, "email"] == "neha@example.com"
    assert result.loc[0, "city"] == "Bangalore"
    assert pd.api.types.is_datetime64_any_dtype(
        result["registration_date"]
    )


def test_standardize_orders():

    df = pd.DataFrame({
        "cust_id": [" c001 "],
        "total_orders": ["5"],
        "lifetime_value": ["25000"],
        "last_order_date": ["2026-05-17"]
    })

    result = standardize_orders(df)

    assert result.loc[0, "customer_id"] == "C001"
    assert result.loc[0, "total_orders"] == 5
    assert result.loc[0, "lifetime_value"] == 25000
    assert "cust_id" not in result.columns


def test_standardize_support():

    df = pd.DataFrame({
        "customerId": [" c001 "],
        "tickets": ["3"],
        "lastTicketDate": ["2026-05-17"]
    })

    result = standardize_support(df)

    assert result.loc[0, "customer_id"] == "C001"
    assert result.loc[0, "support_tickets"] == 3
    assert "tickets" not in result.columns
    assert "lastTicketDate" not in result.columns
