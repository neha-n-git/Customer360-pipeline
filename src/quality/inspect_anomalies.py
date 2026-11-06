import duckdb

from src.utils import PROJECT_ROOT


BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"


def inspect_anomalies():

    con = duckdb.connect()

    # 1. Inspect both CRM records for the duplicate customer
    print("\n" + "=" * 60)
    print("1. DUPLICATE CRM RECORD: C0105")
    print("=" * 60)

    crm_path = str(BRONZE_DIR / "crm_customers.parquet")

    duplicate = con.execute("""
        SELECT *
        FROM read_parquet(?)
        WHERE customer_id = 'C0105'
    """, [crm_path]).df()

    print(duplicate.to_string(index=False))

    # 2. Inspect the Orders record with missing total_orders
    print("\n" + "=" * 60)
    print("2. ORDER RECORD WITH MISSING total_orders")
    print("=" * 60)

    orders_path = str(BRONZE_DIR / "orders.parquet")

    missing_orders = con.execute("""
        SELECT *
        FROM read_parquet(?)
        WHERE total_orders IS NULL
    """, [orders_path]).df()

    print(missing_orders.to_string(index=False))

    # 3. Inspect sample values and types from Orders
    print("\n" + "=" * 60)
    print("3. ORDERS DATA SAMPLE")
    print("=" * 60)

    print(con.execute("""
        SELECT cust_id, total_orders, lifetime_value, last_order_date
        FROM read_parquet(?)
        LIMIT 10
    """, [orders_path]).df().to_string(index=False))

    # 4. Inspect sample values from Support
    print("\n" + "=" * 60)
    print("4. SUPPORT DATA SAMPLE")
    print("=" * 60)

    support_path = str(BRONZE_DIR / "support_tickets.parquet")

    print(con.execute("""
        SELECT customerId, tickets, lastTicketDate
        FROM read_parquet(?)
        LIMIT 10
    """, [support_path]).df().to_string(index=False))

    con.close()


if __name__ == "__main__":
    inspect_anomalies()