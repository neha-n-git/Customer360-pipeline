
import duckdb
from src.utils import PROJECT_ROOT

BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"


def validate_bronze():

    con = duckdb.connect()

    crm_path = str(BRONZE_DIR / "crm_customers.parquet")
    orders_path = str(BRONZE_DIR / "orders.parquet")
    support_path = str(BRONZE_DIR / "support_tickets.parquet")

    print("\n========== CRM VALIDATION ==========")

    crm = con.execute("""
        SELECT
            COUNT(*) AS total_records,

            COUNT(*) FILTER (
                WHERE TRIM(customer_id) = ''
            ) AS empty_ids,

            COUNT(*) FILTER (
                WHERE NOT regexp_full_match(
                    TRIM(email),
                    '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'
                )
            ) AS invalid_emails,

            COUNT(*) FILTER (
                WHERE name != TRIM(name)
                   OR email != TRIM(email)
                   OR city != TRIM(city)
            ) AS whitespace_records,

            COUNT(*) FILTER (
                WHERE TRY_CAST(registration_date AS DATE) IS NULL
            ) AS invalid_dates

        FROM read_parquet(?)
    """, [crm_path]).df()

    print(crm.to_string(index=False))

    print("\n========== ORDERS VALIDATION ==========")

    orders = con.execute("""
        SELECT
            COUNT(*) AS total_records,

            COUNT(*) FILTER (
                WHERE total_orders IS NULL
            ) AS missing_order_counts,

            COUNT(*) FILTER (
                WHERE total_orders < 0
            ) AS negative_order_counts,

            COUNT(*) FILTER (
                WHERE total_orders != FLOOR(total_orders)
                  AND total_orders IS NOT NULL
            ) AS fractional_order_counts,

            COUNT(*) FILTER (
                WHERE lifetime_value < 0
            ) AS negative_lifetime_values,

            COUNT(*) FILTER (
                WHERE TRY_CAST(last_order_date AS DATE) IS NULL
            ) AS invalid_dates

        FROM read_parquet(?)
    """, [orders_path]).df()

    print(orders.to_string(index=False))

    print("\n========== SUPPORT VALIDATION ==========")

    support = con.execute("""
        SELECT
            COUNT(*) AS total_records,

            COUNT(*) FILTER (
                WHERE TRY_CAST(tickets AS BIGINT) IS NULL
            ) AS invalid_ticket_counts,

            COUNT(*) FILTER (
                WHERE TRY_CAST(tickets AS BIGINT) < 0
            ) AS negative_ticket_counts,

            COUNT(*) FILTER (
                WHERE TRY_CAST(lastTicketDate AS DATE) IS NULL
            ) AS invalid_dates

        FROM read_parquet(?)
    """, [support_path]).df()

    print(support.to_string(index=False))

    con.close()


if __name__ == "__main__":
    validate_bronze()
