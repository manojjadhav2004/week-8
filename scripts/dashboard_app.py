"""
Dashboard backend - serves all 8 CLI reports + an overview KPI summary
as JSON, and serves the dashboard frontend.

Reuses the exact REPORTS functions from report_cli.py, so every number
shown in the dashboard is guaranteed to match the CLI tool's output.

Run:
    pip install flask
    python3 scripts/dashboard_app.py
Then open http://localhost:5000
"""

import os
import sys
import sqlite3
from flask import Flask, jsonify, send_from_directory

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_cli import REPORTS, REVENUE_EXPR

PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DB_PATH = os.path.join(PROJECT_ROOT, "ecommerce.db")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

app = Flask(__name__, static_folder=None)


def get_cursor():
    conn = sqlite3.connect(DB_PATH)
    return conn, conn.cursor()


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "dashboard.html")


@app.route("/api/overview")
def api_overview():
    conn, cur = get_cursor()
    cur.execute(f"""
        SELECT
            COUNT(DISTINCT o.order_id) AS total_orders,
            COUNT(DISTINCT o.customer_id) AS total_customers,
            ROUND(SUM({REVENUE_EXPR}), 2) AS total_revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE oi.quantity > 0
    """)
    orders, customers, revenue = cur.fetchone()

    cur.execute(f"""
        WITH order_totals AS (
            SELECT o.order_id, SUM({REVENUE_EXPR}) AS order_value
            FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
            WHERE oi.quantity > 0 GROUP BY o.order_id
        )
        SELECT ROUND(AVG(order_value), 2) FROM order_totals
    """)
    aov = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM products")
    total_products = cur.fetchone()[0]

    conn.close()
    return jsonify({
        "total_orders": orders,
        "total_customers": customers,
        "total_revenue": revenue,
        "average_order_value": aov,
        "total_products": total_products,
    })


@app.route("/api/report/<name>")
def api_report(name):
    if name not in REPORTS:
        return jsonify({"error": f"Unknown report '{name}'. Valid: {list(REPORTS.keys())}"}), 404

    conn, cur = get_cursor()
    try:
        headers, rows = REPORTS[name](cur)
        return jsonify({"headers": headers, "rows": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/reports")
def api_reports_list():
    return jsonify({"reports": list(REPORTS.keys())})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
