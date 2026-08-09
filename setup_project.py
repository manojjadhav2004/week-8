"""
setup_project.py
-------------------
Runs the complete pipeline end-to-end, in order:
  1. Generate raw data
  2. Validate raw data
  3. Clean data
  4. Load into SQLite
  5. Run aggregations
  6. Run window functions
  7. Run cohort analysis
  8. Run customer segmentation / RFM
  9. Generate all CLI sample reports
  10. Run all edge case tests

Usage:
    python setup_project.py
    (or python3 setup_project.py on Mac/Linux)
"""

import subprocess
import sys
import os

PY = sys.executable  # uses whichever interpreter is currently running this script

STEPS = [
    ("Generating raw data", [PY, "scripts/generate_data.py"]),
    ("Validating raw data", [PY, "scripts/check_raw_data.py"]),
    ("Cleaning data", [PY, "scripts/clean_data.py"]),
    ("Loading SQLite database", [PY, "scripts/load_database.py"]),
    ("Running aggregations.sql", [PY, "scripts/run_sql.py", "sql/aggregations.sql"]),
    ("Running window_functions.sql", [PY, "scripts/run_sql.py", "sql/window_functions.sql"]),
    ("Running cohort_analysis.sql", [PY, "scripts/run_sql.py", "sql/cohort_analysis.sql"]),
    ("Running customer_segmentation.sql", [PY, "scripts/run_sql.py", "sql/customer_segmentation.sql"]),
    ("Running edge case tests", [PY, "-m", "pytest", "tests/", "-v"]),
]

REPORT_NAMES = ["revenue", "top_customers", "top_products", "aov", "segments", "rfm", "retention", "category"]


def run_step(title, cmd, quiet=False):
    print(f"\n{'='*70}\n{title}\n{'='*70}")
    result = subprocess.run(cmd, capture_output=quiet)
    if result.returncode != 0:
        if quiet:
            print(result.stdout.decode())
            print(result.stderr.decode())
        print(f"\n[FAILED] {title}")
        sys.exit(1)
    print(f"[OK] {title}")


def generate_sample_reports():
    print(f"\n{'='*70}\nGenerating CLI sample reports\n{'='*70}")
    os.makedirs("output/sample_reports", exist_ok=True)
    for name in REPORT_NAMES:
        out_path = f"output/sample_reports/{name}.txt"
        with open(out_path, "w") as f:
            result = subprocess.run(
                [PY, "scripts/report_cli.py", "--report", name],
                stdout=f, stderr=subprocess.PIPE
            )
        if result.returncode != 0:
            print(f"[FAILED] report: {name}")
            print(result.stderr.decode())
            sys.exit(1)
    print(f"[OK] {len(REPORT_NAMES)} sample reports written to output/sample_reports/")


def main():
    for title, cmd in STEPS[:-1]:
        run_step(title, cmd, quiet=True)

    generate_sample_reports()

    # Edge case tests last, with full pytest output visible
    run_step("Running edge case tests", STEPS[-1][1], quiet=False)

    print(f"\n{'='*70}")
    print("Pipeline complete.")
    print("  Raw data      : data/raw/")
    print("  Cleaned data  : data/cleaned/")
    print("  Database      : ecommerce.db")
    print("  Cleaning log  : output/cleaning_report.csv")
    print("  Sample reports: output/sample_reports/")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
