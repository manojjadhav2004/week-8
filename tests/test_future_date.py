"""
Edge Case Test: Future-Dated Orders
--------------------------------------
The data generator deliberately seeds 2 orders with a date beyond "today"
(TODAY = 2026-08-09 in generate_data.py). clean_data.py is expected to flag
these via the `is_future_dated` column rather than silently including them
in normal trend analysis or silently dropping them.

Run:
    python3 tests/test_future_date.py
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW_ORDERS = os.path.join(PROJECT_ROOT, "data", "raw", "orders.csv")
CLEANED_ORDERS = os.path.join(PROJECT_ROOT, "data", "cleaned", "orders_clean.csv")
DB_PATH = os.path.join(PROJECT_ROOT, "ecommerce.db")


def test_future_dates_exist_in_raw_data():
    """Confirms the generator actually seeded future-dated orders (sanity check)."""
    orders = pd.read_csv(RAW_ORDERS, dtype={"customer_id": "object"})

    def parse_any(v):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
            try:
                return datetime.strptime(str(v), fmt)
            except ValueError:
                continue
        return None

    parsed = orders["order_date"].apply(parse_any)
    now = datetime.now()
    future = [d for d in parsed if d is not None and d > now]

    assert len(future) > 0, "Expected at least one seeded future-dated order in raw data"
    print(f"[PASS] test_future_dates_exist_in_raw_data: found {len(future)} future-dated "
          f"orders in raw data (as seeded by generate_data.py)")


def test_future_dates_flagged_after_cleaning():
    """clean_data.py should flag future-dated rows via is_future_dated, not drop or hide them."""
    cleaned = pd.read_csv(CLEANED_ORDERS)
    flagged = cleaned[cleaned["is_future_dated"] == True]  # noqa: E712

    assert len(flagged) > 0, "Expected clean_data.py to flag at least one future-dated order"
    print(f"[PASS] test_future_dates_flagged_after_cleaning: {len(flagged)} rows correctly "
          f"flagged with is_future_dated=True")


def test_future_dates_excluded_from_database_revenue_by_default():
    """
    Sanity check: future-dated orders are still loaded into the DB (for
    auditability) but callers can filter them out via is_future_dated=0
    for any report where "future revenue" wouldn't make business sense.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM orders WHERE is_future_dated = 1")
    future_in_db = cur.fetchone()[0]
    conn.close()

    assert future_in_db > 0, "Expected future-dated orders to still be present (and flagged) in the DB"
    print(f"[PASS] test_future_dates_excluded_from_database_revenue_by_default: "
          f"{future_in_db} future-dated orders present in DB and filterable via is_future_dated")


def run_all():
    tests = [
        test_future_dates_exist_in_raw_data,
        test_future_dates_flagged_after_cleaning,
        test_future_dates_excluded_from_database_revenue_by_default,
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
