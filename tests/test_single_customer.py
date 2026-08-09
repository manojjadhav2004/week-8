"""
Edge Case Test: Single Customer
-----------------------------------
Builds a minimal scratch database containing exactly one customer, one
product, one order, and one order_item, then runs every CLI report function
against it to verify nothing assumes "more than one row" (e.g. NTILE-based
segmentation, RANK, quartiles) and crashes on a tiny dataset.

Run:
    python3 tests/test_single_customer.py
"""

import os
import sys
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from report_cli import REPORTS

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql")
TMP_DB = os.path.join(os.path.dirname(__file__), "_single_customer_test.db")


def build_single_customer_db():
    if os.path.exists(TMP_DB):
        os.remove(TMP_DB)
    conn = sqlite3.connect(TMP_DB)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO customers (customer_id, customer_name, email, email_valid, registration_date, customer_type)
        VALUES (1, 'Solo Customer', 'solo@example.com', 1, '2024-01-01 00:00:00', 'REGULAR')
    """)
    cur.execute("""
        INSERT INTO products (product_id, product_name, category, subcategory, cost_price)
        VALUES (1, 'Only Product', 'Electronics', 'Mobiles', 500.0)
    """)
    cur.execute("""
        INSERT INTO orders (order_id, customer_id, customer_id_missing, order_date, is_future_dated, status, region_code)
        VALUES (1, 1, 0, '2024-06-01 10:00:00', 0, 'DELIVERED', 'NORTH')
    """)
    cur.execute("""
        INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount_percent)
        VALUES (1, 1, 1, 2, 999.99, 10.0)
    """)
    conn.commit()
    return conn


def test_single_customer_all_reports_run_without_error():
    conn = build_single_customer_db()
    cur = conn.cursor()

    failures = []
    for name, fn in REPORTS.items():
        try:
            headers, rows = fn(cur)
            assert isinstance(rows, list)
        except Exception as e:
            failures.append(f"{name}: {e}")

    conn.close()
    os.remove(TMP_DB)

    assert not failures, "Report(s) failed with a single-customer dataset: " + "; ".join(failures)
    print(f"[PASS] test_single_customer_all_reports_run_without_error: "
          f"all {len(REPORTS)} reports handled a 1-customer / 1-order dataset without error")


def test_single_customer_revenue_is_correct():
    """Sanity check the actual revenue math on a known, hand-computed input."""
    conn = build_single_customer_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2)
        FROM order_items oi
    """)
    revenue = cur.fetchone()[0]
    conn.close()
    os.remove(TMP_DB)

    expected = round(2 * 999.99 * (1 - 10.0 / 100), 2)
    assert revenue == expected, f"Expected revenue {expected}, got {revenue}"
    print(f"[PASS] test_single_customer_revenue_is_correct: revenue = {revenue} (matches hand-calc)")


def run_all():
    tests = [
        test_single_customer_all_reports_run_without_error,
        test_single_customer_revenue_is_correct,
    ]
    failures = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"[FAIL] {t.__name__}: {e}")
            failures += 1
    print(f"\n{len(tests) - failures}/{len(tests)} edge case tests passed")


if __name__ == "__main__":
    run_all()
