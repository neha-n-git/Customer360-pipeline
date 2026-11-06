
import duckdb
from src.utils import PROJECT_ROOT

BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"


def inspect_validation_issues():

    con = duckdb.connect()

    crm_path = str(BRONZE_DIR / "crm_customers.parquet")
    orders_path = str(BRONZE_DIR / "orders.parquet")

    # 1. Invalid CRM emails
    print("\n========== INVALID EMAILS ==========")

    result = con.execute("""
        SELECT
            customer_id,
            name,
            email,
            city
        FROM read_parquet(?)
        WHERE NOT regexp_full_match(
            TRIM(email),
            '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'
        )
    """, [crm_path]).df()

    print(result.to_string(index=False))

    # 2. Negative lifetime values
    print("\n========== NEGATIVE LIFETIME VALUES ==========")

    result = con.execute("""
        SELECT *
        FROM read_parquet(?)
        WHERE lifetime_value < 0
    """, [orders_path]).df()

    print(result.to_string(index=False))

    # 3. Missing order counts
    print("\n========== MISSING ORDER COUNTS ==========")

    result = con.execute("""
        SELECT *
        FROM read_parquet(?)
        WHERE total_orders IS NULL
    """, [orders_path]).df()

    print(result.to_string(index=False))

    con.close()


if __name__ == "__main__":
    inspect_validation_issues()
