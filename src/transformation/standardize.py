
import pandas as pd


def normalize_id(series):
    """Standardize customer identifiers."""
    return series.astype("string").str.strip().str.upper()


def standardize_crm(df):
    """Standardize CRM customer data."""

    df = df.copy()

    df["customer_id"] = normalize_id(df["customer_id"])

    df["name"] = df["name"].astype("string").str.strip()
    df["email"] = (
        df["email"]
        .astype("string")
        .str.strip()
        .str.lower()
    )
    df["city"] = df["city"].astype("string").str.strip()

    df["registration_date"] = pd.to_datetime(
        df["registration_date"],
        errors="coerce"
    )

    return df


def standardize_orders(df):
    """Standardize customer order summaries."""

    df = df.copy()

    df = df.rename(columns={
        "cust_id": "customer_id"
    })

    df["customer_id"] = normalize_id(df["customer_id"])

    df["total_orders"] = pd.to_numeric(
        df["total_orders"],
        errors="coerce"
    ).astype("Int64")

    df["lifetime_value"] = pd.to_numeric(
        df["lifetime_value"],
        errors="coerce"
    ).astype("Float64")

    df["last_order_date"] = pd.to_datetime(
        df["last_order_date"],
        errors="coerce"
    )

    return df


def standardize_support(df):
    """Standardize customer support summaries."""

    df = df.copy()

    df = df.rename(columns={
        "customerId": "customer_id",
        "tickets": "support_tickets",
        "lastTicketDate": "last_ticket_date"
    })

    df["customer_id"] = normalize_id(df["customer_id"])

    df["support_tickets"] = pd.to_numeric(
        df["support_tickets"],
        errors="coerce"
    ).astype("Int64")

    df["last_ticket_date"] = pd.to_datetime(
        df["last_ticket_date"],
        errors="coerce"
    )

    return df
