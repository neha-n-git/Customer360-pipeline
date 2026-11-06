import re
import pandas as pd


ISSUE_COLUMNS = [
    "batch_id",
    "run_id",
    "source",
    "record_key",
    "column",
    "rejected_value",
    "reason",
    "severity",
    "issue_type"
]


def add_issue(
    issues, row, source, column, value,
    reason, severity="ERROR", issue_type="FIELD"
):
    issues.append({
        "batch_id": row.get("batch_id"),
        "run_id": row.get("run_id"),
        "source": source,
        "record_key": row.get("customer_id"),
        "column": column,
        "rejected_value": None if pd.isna(value) else str(value),
        "reason": reason,
        "severity": severity,
        "issue_type": issue_type
    })


def validate_required_columns(df, required_columns, source):
    missing = set(required_columns) - set(df.columns)

    if missing:
        raise ValueError(
            f"{source} is missing required columns: {sorted(missing)}"
        )


def is_missing(value):
    return pd.isna(value) or (
        isinstance(value, str) and not value.strip()
    )


def is_valid_customer_id(value, pattern):
    if is_missing(value):
        return False

    return bool(pattern.fullmatch(str(value).strip()))


def is_non_negative_integer(value):
    if pd.isna(value):
        return False

    try:
        number = float(value)
        return number >= 0 and number.is_integer()
    except (TypeError, ValueError):
        return False


def validate_crm(df, id_pattern=None):
    id_pattern = id_pattern or re.compile(r"^C\d{4}$")
    required = [
        "customer_id", "name", "email", "city",
        "registration_date", "batch_id", "run_id"
    ]

    validate_required_columns(df, required, "CRM")

    issues = []

    email_pattern = re.compile(
        r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
        r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
    )

    for _, row in df.iterrows():

        customer_id = row["customer_id"]

        if is_missing(customer_id):
            add_issue(
                issues, row, "CRM", "customer_id",
                customer_id, "Customer ID is missing"
            )

        elif not is_valid_customer_id(customer_id, id_pattern):
            add_issue(
                issues, row, "CRM", "customer_id",
                customer_id, "Customer ID has an invalid format"
            )

        if is_missing(row["name"]):
            add_issue(
                issues, row, "CRM", "name",
                row["name"], "Customer name is missing"
            )

        if is_missing(row["city"]):
            add_issue(
                issues, row, "CRM", "city",
                row["city"], "City is missing; regional reporting is affected",
                severity="WARNING"
            )

        email = row["email"]

        if not is_missing(email):
            if not email_pattern.fullmatch(str(email).strip()):
                add_issue(
                    issues, row, "CRM", "email", email,
                    "Invalid email format",
                    severity="WARNING"
                )

        if pd.isna(row["registration_date"]):
            add_issue(
                issues, row, "CRM", "registration_date",
                row["registration_date"],
                "Registration date is missing or invalid"
            )

    # Detect duplicate customer IDs.
    duplicate_ids = df[
        df.duplicated(subset=["customer_id"], keep=False)
    ]

    business_columns = [
        "customer_id", "name", "email", "city",
        "registration_date"
    ]

    for customer_id, group in duplicate_ids.groupby(
        "customer_id", dropna=False
    ):
        if len(group[business_columns].drop_duplicates()) == 1:
            reason = "Exact duplicate CRM record"
            issue_type = "EXACT_DUPLICATE"
            severity = "WARNING"
        else:
            reason = "Conflicting records for the same customer ID"
            issue_type = "CONFLICTING_DUPLICATE"
            severity = "ERROR"

        for _, row in group.iterrows():
            add_issue(
                issues, row, "CRM", "customer_id",
                customer_id, reason,
                severity=severity,
                issue_type=issue_type
            )

    return pd.DataFrame(issues, columns=ISSUE_COLUMNS)


def validate_orders(df, id_pattern=None):
    id_pattern = id_pattern or re.compile(r"^C\d{4}$")
    required = [
        "customer_id", "total_orders", "lifetime_value",
        "last_order_date", "batch_id", "run_id"
    ]

    validate_required_columns(df, required, "Orders")

    issues = []

    for _, row in df.iterrows():

        customer_id = row["customer_id"]

        if is_missing(customer_id):
            add_issue(
                issues, row, "Orders", "customer_id",
                customer_id, "Customer ID is missing"
            )

        elif not is_valid_customer_id(customer_id, id_pattern):
            add_issue(
                issues, row, "Orders", "customer_id",
                customer_id, "Customer ID has an invalid format"
            )

        orders = row["total_orders"]

        if pd.isna(orders):
            add_issue(
                issues, row, "Orders", "total_orders",
                orders, "Order count is missing",
                severity="WARNING"
            )

        elif not is_non_negative_integer(orders):
            add_issue(
                issues, row, "Orders", "total_orders",
                orders, "Order count must be a non-negative integer"
            )

        value = row["lifetime_value"]

        if pd.isna(value):
            add_issue(
                issues, row, "Orders", "lifetime_value",
                value, "Lifetime value is missing",
                severity="WARNING"
            )

        else:
            try:
                if float(value) < 0:
                    add_issue(
                        issues, row, "Orders", "lifetime_value",
                        value, "Lifetime value cannot be negative"
                    )
            except (TypeError, ValueError):
                add_issue(
                    issues, row, "Orders", "lifetime_value",
                    value, "Lifetime value must be numeric"
                )

        # last_order_date is optional; missing values remain null.

    return pd.DataFrame(issues, columns=ISSUE_COLUMNS)


def validate_support(df, id_pattern=None):
    id_pattern = id_pattern or re.compile(r"^C\d{4}$")
    required = [
        "customer_id", "support_tickets",
        "last_ticket_date", "batch_id", "run_id"
    ]

    validate_required_columns(df, required, "Support")

    issues = []

    for _, row in df.iterrows():

        customer_id = row["customer_id"]

        if is_missing(customer_id):
            add_issue(
                issues, row, "Support", "customer_id",
                customer_id, "Customer ID is missing"
            )

        elif not is_valid_customer_id(customer_id, id_pattern):
            add_issue(
                issues, row, "Support", "customer_id",
                customer_id, "Customer ID has an invalid format"
            )

        tickets = row["support_tickets"]

        if pd.isna(tickets):
            add_issue(
                issues, row, "Support", "support_tickets",
                tickets, "Support ticket count is missing",
                severity="WARNING"
            )

        elif not is_non_negative_integer(tickets):
            add_issue(
                issues, row, "Support", "support_tickets",
                tickets, "Support ticket count must be a non-negative integer"
            )

        # last_ticket_date is optional; missing values remain null.

    return pd.DataFrame(issues, columns=ISSUE_COLUMNS)


def validate_batch(
    crm, orders, support,
    customer_id_regex=r"^C\d{4}$"
):
    """Run source-level validation for one batch."""

    id_pattern = re.compile(customer_id_regex)

    issues = [
        validate_crm(crm, id_pattern),
        validate_orders(orders, id_pattern),
        validate_support(support, id_pattern)
    ]

    return pd.concat(issues, ignore_index=True)