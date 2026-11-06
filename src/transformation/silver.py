import re
import pandas as pd


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)


def clean_crm(df, id_pattern=None):
    """Clean CRM records and separate conflicting customer profiles."""
    df = df.copy()
    if isinstance(id_pattern, str):
        id_pattern = re.compile(id_pattern)
    id_pattern = id_pattern or re.compile(r"^C\d{4}$")

    business_columns = [
        "customer_id", "name", "email", "city", "registration_date"
    ]

    # Identify customer IDs with conflicting business records.
    duplicate_rows = df[
        df.duplicated(subset=["customer_id"], keep=False)
    ]

    conflicting_ids = []

    for customer_id, group in duplicate_rows.groupby("customer_id"):
        if len(group[business_columns].drop_duplicates()) > 1:
            conflicting_ids.append(customer_id)

    # Quarantine all records belonging to conflicting customer IDs.
    conflicts = df[df["customer_id"].isin(conflicting_ids)].copy()
    clean = df[~df["customer_id"].isin(conflicting_ids)].copy()
    conflicts["quarantine_reason"] = "Conflicting CRM records for customer ID"

    # Remove exact duplicate business records, retaining one copy.
    clean = clean.drop_duplicates(
        subset=business_columns,
        keep="first"
    )

    missing_or_invalid_id = (
        clean["customer_id"].isna()
        | clean["customer_id"].astype("string").str.strip().eq("")
        | ~clean["customer_id"].astype("string").str.fullmatch(
            id_pattern
        ).fillna(False)
    )
    missing_name = (
        clean["name"].isna()
        | clean["name"].astype("string").str.strip().eq("")
    )
    invalid_registration_date = pd.isna(clean["registration_date"])

    invalid_crm = (
        missing_or_invalid_id
        | missing_name
        | invalid_registration_date
    )

    invalid_crm_df = clean[invalid_crm].copy()
    reasons = []
    for index in invalid_crm_df.index:
        record_reasons = []
        if bool(missing_or_invalid_id.loc[index]):
            record_reasons.append("Customer ID is missing or invalid")
        if bool(missing_name.loc[index]):
            record_reasons.append("Customer name is missing")
        if bool(invalid_registration_date.loc[index]):
            record_reasons.append(
                "Registration date is missing or invalid"
            )
        reasons.append("; ".join(record_reasons))
    invalid_crm_df["quarantine_reason"] = reasons
    clean = clean[~invalid_crm].copy()
    quarantine = pd.concat([conflicts, invalid_crm_df], ignore_index=True)

    # Convert blank emails to NULL.
    clean["email"] = clean["email"].replace("", pd.NA)

    # Retain customer records but nullify invalid email addresses.
    invalid_email = (
        clean["email"].notna()
        & ~clean["email"].str.fullmatch(EMAIL_PATTERN, na=False)
    )

    clean.loc[invalid_email, "email"] = pd.NA

    return clean, quarantine


def clean_orders(df, id_pattern=None):
    """Retain valid order summaries and quarantine invalid ones."""
    df = df.copy()
    if isinstance(id_pattern, str):
        id_pattern = re.compile(id_pattern)
    id_pattern = id_pattern or re.compile(r"^C\d{4}$")

    customer_ids = df["customer_id"]
    missing_or_invalid_id = (
        customer_ids.isna()
        | customer_ids.astype("string").str.strip().eq("")
        | ~customer_ids.astype("string").str.fullmatch(
            id_pattern
        ).fillna(False)
    )
    total_orders = pd.to_numeric(df["total_orders"], errors="coerce")
    invalid_total_orders = (
        total_orders.notna()
        & (
            (total_orders < 0)
            | (total_orders % 1 != 0)
        )
    )
    lifetime_value = pd.to_numeric(df["lifetime_value"], errors="coerce")
    invalid_lifetime_value = lifetime_value.isna() | (lifetime_value < 0)

    invalid_orders = (
        missing_or_invalid_id
        | invalid_total_orders
        | invalid_lifetime_value
    )

    quarantine = df[invalid_orders].copy()
    clean = df[~invalid_orders].copy()
    reasons = pd.Series("", index=quarantine.index, dtype="string")
    reasons.loc[
        missing_or_invalid_id.loc[quarantine.index]
    ] = "Customer ID is missing or invalid"
    reasons.loc[
        invalid_total_orders.loc[quarantine.index]
    ] = reasons.loc[
        invalid_total_orders.loc[quarantine.index]
    ].str.cat(
        pd.Series(
            "Order count must be a non-negative whole number",
            index=quarantine.index[invalid_total_orders.loc[quarantine.index]]
        ),
        sep="; "
    ).str.strip("; ")
    reasons.loc[
        invalid_lifetime_value.loc[quarantine.index]
    ] = reasons.loc[
        invalid_lifetime_value.loc[quarantine.index]
    ].str.cat(
        pd.Series(
            "Lifetime value is missing or negative",
            index=quarantine.index[invalid_lifetime_value.loc[quarantine.index]]
        ),
        sep="; "
    ).str.strip("; ")
    quarantine["quarantine_reason"] = reasons.str.strip("; ")

    return clean, quarantine


def clean_support(df, id_pattern=None):
    """Retain valid support summaries and quarantine invalid ones."""
    df = df.copy()
    id_pattern = id_pattern or re.compile(r"^C\d{4}$")
    if isinstance(id_pattern, str):
        id_pattern = re.compile(id_pattern)

    customer_ids = df["customer_id"]
    missing_customer_id = customer_ids.isna() | customer_ids.astype("string").str.strip().eq("")
    invalid_customer_id = ~customer_ids.astype("string").str.strip().str.fullmatch(
        id_pattern
    ).fillna(False)
    invalid_customer_id = invalid_customer_id & ~missing_customer_id

    support_tickets = pd.to_numeric(df["support_tickets"], errors="coerce")
    invalid_support_tickets = (
        support_tickets.isna()
        | ~support_tickets.map(lambda value: pd.notna(value) and value.is_integer())
        | (support_tickets < 0)
    )

    invalid_support = (
        missing_customer_id | invalid_customer_id | invalid_support_tickets
    )

    quarantine = df[invalid_support].copy()
    clean = df[~invalid_support].copy()

    reasons = pd.Series("", index=quarantine.index, dtype="string")
    reasons.loc[missing_customer_id.loc[quarantine.index]] = (
        "Customer ID is missing"
    )
    reasons.loc[invalid_customer_id.loc[quarantine.index]] = (
        "Customer ID has an invalid format"
    )
    reasons.loc[invalid_support_tickets.loc[quarantine.index]] = (
        reasons.loc[invalid_support_tickets.loc[quarantine.index]].str.cat(
            pd.Series(
                "Support ticket count is missing, negative, or fractional",
                index=quarantine.index[
                    invalid_support_tickets.loc[quarantine.index]
                ]
            ),
            sep="; "
        ).str.strip("; ")
    )
    quarantine["quarantine_reason"] = reasons.str.strip("; ")

    return clean, quarantine