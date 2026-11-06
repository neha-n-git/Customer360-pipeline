
import pandas as pd
import pytest

from src.quality.validators import (
    validate_crm,
    validate_orders,
    validate_support
)


def test_invalid_crm_email_is_detected():

    df = pd.DataFrame({
        "customer_id": ["C001"],
        "name": ["Test User"],
        "email": ["invalid-email"],
        "city": ["Bangalore"],
        "registration_date": [pd.Timestamp("2025-06-02")],
        "batch_id": ["batch_test"],
        "run_id": ["run_test"]
    })

    issues = validate_crm(df)

    assert "Invalid email format" in issues["reason"].values


def test_negative_lifetime_value_is_detected():

    df = pd.DataFrame({
        "customer_id": ["C001"],
        "total_orders": pd.Series([5], dtype="Int64"),
        "lifetime_value": pd.Series([-5000], dtype="Float64"),
        "last_order_date": [pd.Timestamp("2026-05-17")],
        "batch_id": ["batch_test"],
        "run_id": ["run_test"]
    })

    issues = validate_orders(df)

    assert "Lifetime value cannot be negative" in issues["reason"].values


def test_missing_order_count_is_warning():

    df = pd.DataFrame({
        "customer_id": ["C001"],
        "total_orders": pd.Series([pd.NA], dtype="Int64"),
        "lifetime_value": pd.Series([25000], dtype="Float64"),
        "last_order_date": [pd.Timestamp("2026-05-17")],
        "batch_id": ["batch_test"],
        "run_id": ["run_test"]
    })

    issues = validate_orders(df)

    issue = issues[issues["column"] == "total_orders"]

    assert len(issue) == 1
    assert issue.iloc[0]["severity"] == "WARNING"


def test_missing_required_column_fails():

    df = pd.DataFrame({
        "customer_id": ["C001"]
    })

    with pytest.raises(ValueError):
        validate_orders(df)
