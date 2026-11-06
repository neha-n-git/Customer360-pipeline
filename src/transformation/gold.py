import pandas as pd


def check_unique_ids(df, source):
    """Ensure each source has at most one record per customer."""
    duplicates = df[df.duplicated("customer_id", keep=False)]

    if not duplicates.empty:
        raise ValueError(
            f"{source} contains duplicate customer IDs: "
            f"{duplicates['customer_id'].unique().tolist()}"
        )


def assign_segment(lifetime_value, gold_min=100000, silver_min=50000):
    """Assign a customer segment based on lifetime value."""
    if pd.isna(lifetime_value):
        return "Unknown"
    elif lifetime_value > gold_min:
        return "Gold"
    elif lifetime_value >= silver_min:
        return "Silver"
    else:
        return "Bronze"


def build_customer_360(
    crm,
    orders,
    support,
    orders_quarantine,
    support_quarantine,
    gold_min=100000,
    silver_min=50000,
):
    """Combine trusted Silver data into a customer-level dataset."""

    # Check join keys before merging.
    check_unique_ids(crm, "CRM")
    check_unique_ids(orders, "Orders")
    check_unique_ids(support, "Support")

    # Identify customers whose Orders records were quarantined.
    quarantined_order_ids = set(
        orders_quarantine["customer_id"].dropna()
    )

    quarantined_support_ids = set(
        support_quarantine["customer_id"].dropna()
    )

    # Keep only the fields required for Customer 360.
    order_data = orders[
        [
            "customer_id",
            "total_orders",
            "lifetime_value",
            "last_order_date"
        ]
    ].copy()

    support_data = support[
        [
            "customer_id",
            "support_tickets",
            "last_ticket_date"
        ]
    ].copy()

    # Mark records that actually exist in the trusted datasets.
    order_data["_orders_present"] = True
    support_data["_support_present"] = True

    # CRM is the master population.
    customer_360 = crm[
        [
            "customer_id",
            "name",
            "email",
            "city",
            "registration_date",
            "batch_id",
            "run_id"
        ]
    ].copy()

    # LEFT JOIN preserves every CRM customer.
    customer_360 = customer_360.merge(
        order_data,
        on="customer_id",
        how="left",
        validate="one_to_one"
    )

    customer_360 = customer_360.merge(
        support_data,
        on="customer_id",
        how="left",
        validate="one_to_one"
    )

    # Determine Orders record status.
    orders_present = customer_360["_orders_present"].eq(True)
    orders_quarantined = customer_360["customer_id"].isin(
        quarantined_order_ids
    )

    customer_360["orders_status"] = "AVAILABLE"

    customer_360.loc[
        ~orders_present & ~orders_quarantined,
        "orders_status"
    ] = "NO_RECORD"

    customer_360.loc[
        orders_quarantined,
        "orders_status"
    ] = "QUARANTINED"

    # Identify incomplete Orders records.
    incomplete_orders = (
        orders_present
        & (
            customer_360["total_orders"].isna()
            | customer_360["lifetime_value"].isna()
            | (
                customer_360["total_orders"].fillna(1).gt(0)
                & customer_360["last_order_date"].isna()
            )
        )
    )

    customer_360.loc[
        incomplete_orders,
        "orders_status"
    ] = "INCOMPLETE"

    # Missing source record means zero activity.
    no_orders = customer_360["orders_status"].eq("NO_RECORD")

    customer_360.loc[no_orders, "total_orders"] = 0
    customer_360.loc[no_orders, "lifetime_value"] = 0

    # Quarantined records must not be treated as zero activity.
    invalid_orders = customer_360["orders_status"].eq("QUARANTINED")

    customer_360.loc[invalid_orders, "total_orders"] = pd.NA
    customer_360.loc[invalid_orders, "lifetime_value"] = pd.NA

    # Determine Support record status.
    support_present = customer_360["_support_present"].eq(True)
    support_quarantined = customer_360["customer_id"].isin(
        quarantined_support_ids
    )

    customer_360["support_status"] = "AVAILABLE"

    customer_360.loc[
        ~support_present & ~support_quarantined,
        "support_status"
    ] = "NO_RECORD"

    customer_360.loc[
        support_quarantined,
        "support_status"
    ] = "QUARANTINED"

    incomplete_support = (
        support_present
        & (
            customer_360["support_tickets"].isna()
            | (
                customer_360["support_tickets"].fillna(1).gt(0)
                & customer_360["last_ticket_date"].isna()
            )
        )
    )

    customer_360.loc[
        incomplete_support,
        "support_status"
    ] = "INCOMPLETE"

    no_support = customer_360["support_status"].eq("NO_RECORD")

    customer_360.loc[no_support, "support_tickets"] = 0

    invalid_support = customer_360["support_status"].eq("QUARANTINED")

    customer_360.loc[invalid_support, "support_tickets"] = pd.NA

    # Assign customer segments.
    customer_360["customer_segment"] = (
        customer_360["lifetime_value"].apply(
            assign_segment,
            args=(gold_min, silver_min),
        )
    )

    # Remove temporary merge indicators.
    customer_360 = customer_360.drop(
        columns=["_orders_present", "_support_present"]
    )

    return customer_360