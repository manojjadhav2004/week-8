"""
Edge Case Test: Empty Database
---------------------------------
Verifies that report queries don't crash and behave sensibly when run
against a database with no records at all -- e.g. AOV should return NULL/None
rather than raising a ZeroDivisionError, and count-based reports should
return an empty result set rather than erroring out.

Run:
    python3 tests/test_edge_cases.py
"""

import sqlite3
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from report_cli import REPORTS

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql")


def build_empty_db(path):
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.commit()
    return conn


def test_empty_database_all_reports_run_without_error():
    """
    Every report function should execute against an empty database without
    raising an exception, and should return an empty (or None-filled) result
    rather than crashing on divide-by-zero, missing tables, etc.
    """
    tmp_db = os.path.join(os.path.dirname(__file__), "_empty_test.db")
    conn = build_empty_db(tmp_db)
    cur = conn.cursor()

    failures = []
    for name, fn in REPORTS.items():
        try:
            headers, rows = fn(cur)
            # AOV report always returns exactly one row (with NULLs) even
            # when there's no data; everything else should return zero rows.
            if name == "aov":
                assert len(rows) == 1, f"{name}: expected 1 row (with NULLs), got {len(rows)}"
            else:
                assert len(rows) == 0, f"{name}: expected 0 rows on empty DB, got {len(rows)}"
        except Exception as e:
            failures.append(f"{name}: {e}")

    conn.close()
    os.remove(tmp_db)

    assert not failures, "Report(s) failed on empty database: " + "; ".join(failures)
    print(f"[PASS] test_empty_database_all_reports_run_without_error: "
          f"all {len(REPORTS)} reports handled an empty database gracefully")


def run_all():
    tests = [test_empty_database_all_reports_run_without_error]
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
