"""
Step 4 - Load Data into SQLite
---------------------------------
Creates ecommerce.db from sql/schema.sql, then loads the cleaned CSVs from
data/cleaned/ into the customers / products / orders / order_items tables.
"""

import sqlite3
import pandas as pd

DB_PATH = "ecommerce.db"
SCHEMA_PATH = "sql/schema.sql"


def main():
    with open(SCHEMA_PATH) as f:
        schema_sql = f.read()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(schema_sql)
    conn.commit()

    customers = pd.read_csv("data/cleaned/customers_clean.csv")
    products = pd.read_csv("data/cleaned/products_clean.csv")
    orders = pd.read_csv("data/cleaned/orders_clean.csv")
    order_items = pd.read_csv("data/cleaned/order_items_clean.csv")

    # Booleans -> 0/1 for SQLite CHECK/INTEGER columns
    customers["email_valid"] = customers["email_valid"].astype(int)
    orders["customer_id_missing"] = orders["customer_id_missing"].astype(int)
    orders["is_future_dated"] = orders["is_future_dated"].astype(int)

    customers.to_sql("customers", conn, if_exists="append", index=False)
    products.to_sql("products", conn, if_exists="append", index=False)
    orders.to_sql("orders", conn, if_exists="append", index=False)
    order_items.to_sql("order_items", conn, if_exists="append", index=False)
    conn.commit()

    cur = conn.cursor()
    print("Database loaded:", DB_PATH)
    for t in ["customers", "products", "orders", "order_items"]:
        n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n} rows")

    conn.close()


if __name__ == "__main__":
    main()
