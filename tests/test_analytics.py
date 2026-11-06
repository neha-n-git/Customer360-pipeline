import pandas as pd

from src.analytics.metrics import (
    customer_count_by_city,
    customer_segmentation,
    high_support_customers,
    revenue_by_city,
    top_customers_by_revenue,
)


def customer_frame():
    return pd.DataFrame({
        "customer_id": ["C0001", "C0002", "C0003", "C0004", "C0005", "C0001"],
        "name": ["One", "Two", "Three", "Four", "Five", "Duplicate One"],
        "city": ["Delhi", "Delhi", None, "Pune", "Pune", "Delhi"],
        "lifetime_value": [120000.0, 60000.0, 40000.0, None, 20000.0, 999999.0],
        "support_tickets": [6, 5, 8, 2, None, 1],
        "customer_segment": ["Gold", "Silver", "Bronze", "Unknown", "Bronze", "Gold"],
    })


def test_top_customers_ranks_known_revenue_and_excludes_null():
    original = customer_frame()
    result = top_customers_by_revenue(original)
    assert result["customer_id"].tolist() == ["C0001", "C0002", "C0003", "C0005"]
    assert result["rank"].tolist() == [1, 2, 3, 4]
    assert original.equals(customer_frame())


def test_customer_segmentation_counts_and_percentages():
    result = customer_segmentation(customer_frame()).set_index("segment")
    assert result.loc["Gold", "customer_count"] == 1
    assert result.loc["Silver", "customer_count"] == 1
    assert result.loc["Bronze", "customer_count"] == 2
    assert result.loc["Unknown", "customer_count"] == 1
    assert result["percentage"].sum() == 100


def test_high_support_customers_includes_more_than_five_only():
    result = high_support_customers(customer_frame())
    assert result["customer_id"].tolist() == ["C0003", "C0001"]


def test_revenue_by_city_groups_multiple_customers_and_unknown():
    result = revenue_by_city(customer_frame()).set_index("city")
    assert result.loc["Delhi", "revenue"] == 180000.0
    assert result.loc["Pune", "revenue"] == 20000.0


def test_customer_count_by_city_counts_unique_customers_and_missing_city():
    result = customer_count_by_city(customer_frame()).set_index("city")
    assert result.loc["Delhi", "customer_count"] == 2
    assert result.loc["Pune", "customer_count"] == 2
    assert result.loc["Unknown", "customer_count"] == 1
