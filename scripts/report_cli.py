"""
Step 9 - CLI Reporting Tool
------------------------------
Command-line interface for generating business reports on demand, formatted
as clean tables using `tabulate`.

Usage:
    python3 scripts/report_cli.py --report revenue
    python3 scripts/report_cli.py --report top_customers
    python3 scripts/report_cli.py --report top_products
    python3 scripts/report_cli.py --report aov
    python3 scripts/report_cli.py --report segments
    python3 scripts/report_cli.py --report rfm
    python3 scripts/report_cli.py --report retention
    python3 scripts/report_cli.py --report category

    python3 scripts/report_cli.py --help
"""

import sqlite3
import argparse
import sys
from tabulate import tabulate

DB_PATH = "ecommerce.db"

REVENUE_EXPR = "oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)"

REPORTS = {}


def report(name):
    def decorator(fn):
        REPORTS[name] = fn
        return fn
    return decorator


@report("revenue")
def revenue_report(cur):
    cur.execute(f"""
        SELECT strftime('%Y-%m', o.order_date) AS month,
               ROUND(SUM({REVENUE_EXPR}), 2) AS revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE oi.quantity > 0
        GROUP BY month
        ORDER BY month
    """)
    return ["Month", "Revenue"], cur.fetchall()


@report("top_customers")
def top_customers_report(cur):
    cur.execute(f"""
        SELECT c.customer_id, c.customer_name,
               ROUND(SUM({REVENUE_EXPR}), 2) AS revenue
        FROM customers c
        JOIN orders o ON o.customer_id = c.customer_id
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE oi.quantity > 0
        GROUP BY c.customer_id, c.customer_name
        ORDER BY revenue DESC
        LIMIT 10
    """)
    return ["Customer ID", "Name", "Revenue"], cur.fetchall()


@report("top_products")
def top_products_report(cur):
    cur.execute(f"""
        SELECT p.product_id, p.product_name,
               ROUND(SUM({REVENUE_EXPR}), 2) AS revenue,
               SUM(oi.quantity) AS units_sold
        FROM order_items oi
        JOIN products p ON p.product_id = oi.product_id
        WHERE oi.quantity > 0
        GROUP BY p.product_id, p.product_name
        ORDER BY revenue DESC
        LIMIT 10
    """)
    return ["Product ID", "Name", "Revenue", "Units Sold"], cur.fetchall()


@report("aov")
def aov_report(cur):
    cur.execute(f"""
        WITH order_totals AS (
            SELECT o.order_id, SUM({REVENUE_EXPR}) AS order_value
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            WHERE oi.quantity > 0
            GROUP BY o.order_id
        )
        SELECT ROUND(AVG(order_value), 2) AS average_order_value,
               ROUND(MIN(order_value), 2) AS min_order_value,
               ROUND(MAX(order_value), 2) AS max_order_value,
               COUNT(*) AS total_orders
        FROM order_totals
    """)
    return ["Avg Order Value", "Min", "Max", "Total Orders"], cur.fetchall()


@report("segments")
def segments_report(cur):
    cur.execute("""
        WITH order_counts AS (
            SELECT customer_id, COUNT(*) AS order_count
            FROM orders WHERE customer_id IS NOT NULL
            GROUP BY customer_id
        ),
        segmented AS (
            SELECT customer_id,
                CASE WHEN order_count = 1 THEN 'One-Time'
                     WHEN order_count BETWEEN 2 AND 4 THEN 'Occasional'
                     ELSE 'Loyal' END AS frequency_segment
            FROM order_counts
        )
        SELECT frequency_segment, COUNT(*) AS customer_count
        FROM segmented
        GROUP BY frequency_segment
        ORDER BY customer_count DESC
    """)
    return ["Segment", "Customer Count"], cur.fetchall()


@report("rfm")
def rfm_report(cur):
    cur.execute(f"""
        WITH dataset_max_date AS (SELECT MAX(date(order_date)) AS max_date FROM orders),
        rfm_base AS (
            SELECT o.customer_id,
                   CAST(julianday(dm.max_date) - julianday(MAX(date(o.order_date))) AS INTEGER) AS recency_days,
                   COUNT(DISTINCT o.order_id) AS frequency,
                   SUM({REVENUE_EXPR}) AS monetary
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            CROSS JOIN dataset_max_date dm
            WHERE oi.quantity > 0 AND o.customer_id IS NOT NULL
            GROUP BY o.customer_id
        ),
        rfm_scores AS (
            SELECT customer_id, monetary,
                   6 - NTILE(5) OVER (ORDER BY recency_days ASC) AS r_score,
                   NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
                   NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
            FROM rfm_base
        ),
        labeled AS (
            SELECT customer_id, monetary,
                CASE
                    WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
                    WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal Customers'
                    WHEN r_score >= 4 AND f_score <= 2 THEN 'Potential Loyalists'
                    WHEN r_score BETWEEN 2 AND 3 AND f_score BETWEEN 2 AND 3 THEN 'Regular Customers'
                    WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
                    WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost'
                    ELSE 'Regular Customers'
                END AS rfm_segment
            FROM rfm_scores
        )
        SELECT rfm_segment, COUNT(*) AS customer_count, ROUND(AVG(monetary), 2) AS avg_monetary
        FROM labeled
        GROUP BY rfm_segment
        ORDER BY customer_count DESC
    """)
    return ["RFM Segment", "Customer Count", "Avg Monetary"], cur.fetchall()


@report("retention")
def retention_report(cur):
    cur.execute("""
        WITH first_order AS (
            SELECT customer_id, MIN(date(order_date)) AS first_order_date
            FROM orders WHERE customer_id IS NOT NULL
            GROUP BY customer_id
        ),
        cohort_size AS (
            SELECT strftime('%Y-%m', first_order_date) AS cohort_month, COUNT(*) AS size
            FROM first_order GROUP BY cohort_month
        ),
        activity AS (
            SELECT o.customer_id,
                   strftime('%Y-%m', f.first_order_date) AS cohort_month,
                   (CAST(strftime('%Y', o.order_date) AS INTEGER) - CAST(strftime('%Y', f.first_order_date) AS INTEGER)) * 12
                     + (CAST(strftime('%m', o.order_date) AS INTEGER) - CAST(strftime('%m', f.first_order_date) AS INTEGER)) AS month_index
            FROM orders o
            JOIN first_order f ON f.customer_id = o.customer_id
            WHERE o.customer_id IS NOT NULL
        ),
        retained AS (
            SELECT cohort_month, month_index, COUNT(DISTINCT customer_id) AS active_customers
            FROM activity WHERE month_index BETWEEN 0 AND 3
            GROUP BY cohort_month, month_index
        )
        SELECT r.cohort_month, r.month_index, r.active_customers, cs.size,
               ROUND(1.0 * r.active_customers / cs.size * 100, 2) AS retention_rate_percent
        FROM retained r
        JOIN cohort_size cs ON cs.cohort_month = r.cohort_month
        ORDER BY r.cohort_month, r.month_index
        LIMIT 20
    """)
    return ["Cohort Month", "Month Index", "Active", "Cohort Size", "Retention %"], cur.fetchall()


@report("category")
def category_report(cur):
    cur.execute(f"""
        SELECT p.category, ROUND(SUM({REVENUE_EXPR}), 2) AS revenue
        FROM order_items oi
        JOIN products p ON p.product_id = oi.product_id
        WHERE oi.quantity > 0
        GROUP BY p.category
        ORDER BY revenue DESC
    """)
    return ["Category", "Revenue"], cur.fetchall()


def main():
    parser = argparse.ArgumentParser(
        description="E-Commerce Order Analytics - CLI Reporting Tool"
    )
    parser.add_argument(
        "--report",
        required=True,
        choices=list(REPORTS.keys()),
        help="Which report to generate: " + ", ".join(REPORTS.keys()),
    )
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    headers, rows = REPORTS[args.report](cur)
    print(f"\n=== {args.report.upper()} REPORT ===\n")
    print(tabulate(rows, headers=headers, tablefmt="github", floatfmt=",.2f"))
    print()

    conn.close()


if __name__ == "__main__":
    main()
