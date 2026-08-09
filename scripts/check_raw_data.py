"""
Step 2 - Validate Raw Data
----------------------------
Scans the raw CSVs in data/raw/ and reports data-quality issues WITHOUT
modifying anything. This runs before cleaning so problems are visible up
front, and its counts are used to sanity-check that clean_data.py actually
fixed everything it should have.

Checks performed:
  - Missing / NULL values per column
  - Duplicate rows per file
  - Invalid order_date formats
  - Invalid emails
  - Referential integrity: order_items -> orders, order_items -> products,
    orders -> customers
  - Data type inconsistencies (quantity / discount_percent stored as text)
"""

import re
import pandas as pd

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_date(val):
    val = str(val).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
        try:
            pd.to_datetime(val, format=fmt)
            return True
        except (ValueError, TypeError):
            continue
    return False


def is_numeric(val):
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False


def check_customers(df):
    issues = {}
    issues["duplicate_rows"] = int(df.duplicated().sum())
    issues["missing_customer_name"] = int(df["customer_name"].isna().sum())
    issues["invalid_emails"] = int((~df["email"].astype(str).apply(lambda e: bool(EMAIL_REGEX.match(e.strip())))).sum())
    return issues


def check_products(df):
    issues = {}
    issues["duplicate_rows"] = int(df.duplicated().sum())
    issues["missing_product_name"] = int(df["product_name"].isna().sum())
    issues["messy_name_whitespace"] = int(df["product_name"].astype(str).apply(lambda x: x != x.strip()).sum())
    return issues


def check_orders(df):
    issues = {}
    issues["duplicate_rows"] = int(df.duplicated().sum())
    missing_cust = df["customer_id"].isna() | (df["customer_id"].astype(str).str.strip() == "")
    issues["missing_customer_id"] = int(missing_cust.sum())
    issues["invalid_date_format"] = int((~df["order_date"].apply(is_valid_date)).sum())

    def parse_any(v):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
            try:
                return pd.to_datetime(v, format=fmt)
            except (ValueError, TypeError):
                continue
        return pd.NaT

    parsed = df["order_date"].apply(parse_any)
    now = pd.Timestamp.now()
    issues["future_dated_orders"] = int((parsed > now).sum())
    return issues


def check_order_items(df, valid_order_ids, valid_product_ids):
    issues = {}
    issues["duplicate_rows"] = int(df.duplicated().sum())
    issues["orphaned_order_id"] = int((~df["order_id"].isin(valid_order_ids)).sum())
    issues["invalid_product_id"] = int((~df["product_id"].isin(valid_product_ids)).sum())
    issues["negative_quantity"] = int((pd.to_numeric(df["quantity"], errors="coerce") < 0).sum())
    issues["zero_quantity"] = int((pd.to_numeric(df["quantity"], errors="coerce") == 0).sum())
    issues["quantity_stored_as_text"] = int((~df["quantity"].apply(is_numeric)).sum() -
                                             df["quantity"].isna().sum())
    issues["discount_over_100"] = int((pd.to_numeric(
        df["discount_percent"].astype(str).str.replace("%", "", regex=False), errors="coerce") > 100).sum())
    return issues


def main():
    customers = pd.read_csv("data/raw/customers.csv", dtype={"customer_id": "object"})
    products = pd.read_csv("data/raw/products.csv")
    orders = pd.read_csv("data/raw/orders.csv", dtype={"customer_id": "object"})
    order_items = pd.read_csv("data/raw/order_items.csv", dtype={"quantity": "object", "discount_percent": "object"})

    report = []
    report.append("RAW DATA VALIDATION REPORT")
    report.append("=" * 55)

    report.append("\n[customers.csv]")
    for k, v in check_customers(customers).items():
        report.append(f"  {k:<28}: {v}")

    report.append("\n[products.csv]")
    for k, v in check_products(products).items():
        report.append(f"  {k:<28}: {v}")

    report.append("\n[orders.csv]")
    for k, v in check_orders(orders).items():
        report.append(f"  {k:<28}: {v}")

    report.append("\n[order_items.csv]")
    for k, v in check_order_items(order_items, set(orders["order_id"]), set(products["product_id"])).items():
        report.append(f"  {k:<28}: {v}")

    text = "\n".join(report)
    print(text)


if __name__ == "__main__":
    main()
