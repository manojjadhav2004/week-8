"""
Step 3 - Clean Data
---------------------
Transforms data/raw/*.csv into analysis-ready data/cleaned/*.csv using pandas.

Cleaning performed:
  - Remove duplicate records
  - Handle missing values (flag missing customer_id rather than dropping orders)
  - Fix data types (quantity/discount_percent coerced to numeric, "%" stripped)
  - Fix invalid date formats (DD-MM-YYYY -> standard datetime)
  - Normalize product names (trim + title case)
  - Validate emails (flag invalid, do not drop customers)
  - Validate referential integrity (drop order_items with no matching order)

Outputs:
  - data/cleaned/customers_clean.csv
  - data/cleaned/products_clean.csv
  - data/cleaned/orders_clean.csv
  - data/cleaned/order_items_clean.csv
  - output/cleaning_report.csv  (one row per check, with before/after counts)
"""

import re
import pandas as pd

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean_customers(df):
    log = []
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    log.append(("customers", "duplicate_rows_removed", before - len(df)))

    invalid_email_mask = ~df["email"].astype(str).apply(lambda e: bool(EMAIL_REGEX.match(e.strip())))
    df["email_valid"] = ~invalid_email_mask
    log.append(("customers", "invalid_emails_flagged", int(invalid_email_mask.sum())))

    return df, log


def clean_products(df):
    log = []
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    log.append(("products", "duplicate_rows_removed", before - len(df)))

    original = df["product_name"].copy()
    df["product_name"] = df["product_name"].astype(str).str.strip().str.title()
    changed = (original.astype(str) != df["product_name"]).sum()
    log.append(("products", "product_names_normalized", int(changed)))

    return df, log


def clean_orders(df):
    log = []
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    log.append(("orders", "duplicate_rows_removed", before - len(df)))

    df["customer_id"] = df["customer_id"].replace("", pd.NA).replace("NULL", pd.NA)
    missing_mask = df["customer_id"].isna()
    df["customer_id_missing"] = missing_mask
    log.append(("orders", "missing_customer_id_flagged", int(missing_mask.sum())))

    def parse_date(val):
        val = str(val).strip()
        dt = pd.to_datetime(val, format="%Y-%m-%d %H:%M:%S", errors="coerce")
        if pd.isna(dt):
            dt2 = pd.to_datetime(val, format="%d-%m-%Y", errors="coerce")
            if not pd.isna(dt2):
                return dt2, True
            dt3 = pd.to_datetime(val, errors="coerce")
            return dt3, not pd.isna(dt3)
        return dt, False

    parsed = df["order_date"].apply(parse_date)
    df["order_date"] = parsed.apply(lambda t: t[0])
    fixed_count = int(parsed.apply(lambda t: t[1]).sum())
    log.append(("orders", "date_format_fixed", fixed_count))

    now = pd.Timestamp.now()
    future_mask = df["order_date"] > now
    df["is_future_dated"] = future_mask
    log.append(("orders", "future_dated_orders_flagged", int(future_mask.sum())))

    return df, log


def clean_order_items(df, valid_order_ids, valid_product_ids):
    log = []
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    log.append(("order_items", "duplicate_rows_removed", before - len(df)))

    # Fix data types: quantity and discount_percent coerced to numeric
    df["discount_percent"] = df["discount_percent"].astype(str).str.replace("%", "", regex=False)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["discount_percent"] = pd.to_numeric(df["discount_percent"], errors="coerce")
    bad_numeric = df["quantity"].isna() | df["discount_percent"].isna()
    log.append(("order_items", "unparseable_numeric_rows_dropped", int(bad_numeric.sum())))
    df = df[~bad_numeric].copy()

    # Referential integrity: drop order_items pointing at non-existent orders/products
    orphaned = ~df["order_id"].isin(valid_order_ids)
    log.append(("order_items", "orphaned_order_id_rows_dropped", int(orphaned.sum())))
    df = df[~orphaned].copy()

    bad_product = ~df["product_id"].isin(valid_product_ids)
    log.append(("order_items", "invalid_product_id_rows_dropped", int(bad_product.sum())))
    df = df[~bad_product].copy()

    # Cap discount_percent at 100 rather than silently allowing negative revenue
    over_100 = df["discount_percent"] > 100
    log.append(("order_items", "discount_over_100_capped", int(over_100.sum())))
    df.loc[over_100, "discount_percent"] = 100.0

    return df, log


def main():
    customers_raw = pd.read_csv("data/raw/customers.csv", dtype={"customer_id": "object"})
    products_raw = pd.read_csv("data/raw/products.csv")
    orders_raw = pd.read_csv("data/raw/orders.csv", dtype={"customer_id": "object"})
    order_items_raw = pd.read_csv("data/raw/order_items.csv",
                                   dtype={"quantity": "object", "discount_percent": "object"})

    all_log = []

    customers, log = clean_customers(customers_raw)
    all_log += log

    products, log = clean_products(products_raw)
    all_log += log

    orders, log = clean_orders(orders_raw)
    all_log += log

    order_items, log = clean_order_items(
        order_items_raw, set(orders["order_id"]), set(products["product_id"])
    )
    all_log += log

    customers.to_csv("data/cleaned/customers_clean.csv", index=False)
    products.to_csv("data/cleaned/products_clean.csv", index=False)
    orders.to_csv("data/cleaned/orders_clean.csv", index=False)
    order_items.to_csv("data/cleaned/order_items_clean.csv", index=False)

    report_df = pd.DataFrame(all_log, columns=["table", "check", "count"])
    report_df.to_csv("output/cleaning_report.csv", index=False)

    print("CLEANING REPORT")
    print("=" * 55)
    print(report_df.to_string(index=False))
    print(f"\nCleaned files written to data/cleaned/")
    print(f"  customers_clean.csv   : {len(customers)} rows")
    print(f"  products_clean.csv    : {len(products)} rows")
    print(f"  orders_clean.csv      : {len(orders)} rows")
    print(f"  order_items_clean.csv : {len(order_items)} rows")
    print(f"\nReport saved to output/cleaning_report.csv")


if __name__ == "__main__":
    main()
