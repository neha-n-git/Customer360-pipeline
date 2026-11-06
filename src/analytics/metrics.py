import pandas as pd


SEGMENT_ORDER = ["Gold", "Silver", "Bronze", "Unknown"]


def _unique_customers(df):
    """Return one deterministic customer row and report duplicate count separately."""
    result = df.copy()
    if result["customer_id"].isna().any():
        result = result[result["customer_id"].notna()].copy()
    return result.drop_duplicates(subset="customer_id", keep="first")


def top_customers_by_revenue(df, limit=10):
    customers = _unique_customers(df)
    known_revenue = customers[
        customers["lifetime_value"].notna()
    ][["customer_id", "name", "lifetime_value"]].copy()
    known_revenue["lifetime_value"] = (
        known_revenue["lifetime_value"].astype(float)
    )
    known_revenue = known_revenue.sort_values(
        ["lifetime_value", "customer_id"],
        ascending=[False, True],
        kind="stable"
    ).head(limit)
    known_revenue["rank"] = range(1, len(known_revenue) + 1)
    return known_revenue[
        ["customer_id", "name", "lifetime_value", "rank"]
    ]


def customer_segmentation(df):
    customers = _unique_customers(df)
    segments = customers["customer_segment"].astype("string")
    segments = segments.where(
        segments.isin(SEGMENT_ORDER),
        pd.NA
    )
    segments = segments.fillna("Unknown").astype(object)

    counts = (
        pd.Series(segments)
        .value_counts()
        .reindex(SEGMENT_ORDER, fill_value=0)
    )
    total = len(customers)
    result = counts.rename("customer_count").rename_axis("segment").reset_index()
    result["percentage"] = (
        result["customer_count"].div(total).mul(100)
        if total
        else 0.0
    )
    return result


def high_support_customers(df):
    customers = _unique_customers(df)
    result = customers[
        customers["support_tickets"].notna()
        & customers["support_tickets"].gt(5)
    ][[
        "customer_id",
        "name",
        "support_tickets",
        "lifetime_value",
    ]].copy()
    return result.sort_values(
        ["support_tickets", "customer_id"],
        ascending=[False, True],
        kind="stable"
    )


def revenue_by_city(df):
    customers = _unique_customers(df)
    known_revenue = customers[
        customers["lifetime_value"].notna()
    ][["city", "lifetime_value"]].copy()
    known_revenue["city"] = (
        known_revenue["city"].astype("string").fillna("Unknown")
        .replace("", "Unknown")
    )
    return (
        known_revenue.groupby("city", as_index=False)["lifetime_value"]
        .sum()
        .rename(columns={"lifetime_value": "revenue"})
        .sort_values(["revenue", "city"], ascending=[False, True])
        .reset_index(drop=True)
    )


def customer_count_by_city(df):
    customers = _unique_customers(df)
    cities = customers["city"].astype("string").fillna("Unknown")
    cities = cities.replace("", "Unknown")
    result = (
        pd.DataFrame({"city": cities})
        .groupby("city", as_index=False)
        .size()
        .rename(columns={"size": "customer_count"})
        .sort_values(["customer_count", "city"], ascending=[False, True])
        .reset_index(drop=True)
    )
    return result
