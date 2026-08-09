# E-Commerce Order Analytics System

## 📌 Project Overview

The E-Commerce Order Analytics System is an end-to-end data engineering and
analytics project built using Python, Pandas, SQLite, and SQL.

The project demonstrates a complete data pipeline starting from realistic
e-commerce data generation and continuing through data validation, cleaning,
database loading, SQL analytics, customer segmentation, RFM analysis, cohort
analysis, and command-line reporting.

The system is designed to simulate a real-world e-commerce analytics
workflow where raw data contains quality issues that must be identified,
cleaned, validated, and transformed into business-ready information.

## 🎯 Objective

The objective of this project is to design and develop an end-to-end
e-commerce order analytics system combining Python and SQL. The system
demonstrates:

- Dataset generation
- Data quality validation
- Data cleaning using Pandas
- Handling missing values, duplicate detection and removal
- Data type validation
- Referential integrity validation
- Relational database design (SQLite)
- SQL joins and aggregations
- Window functions and CTE-based analysis
- Cohort analysis and customer retention analysis
- Customer segmentation and RFM analysis
- CLI-based reporting (with `tabulate`)
- Edge-case testing

## 🏗️ Pipeline Overview

```
Python Data Generation (Faker/Random)
            │
            ▼
     Raw CSV Files (data/raw/)
            │
            ▼
   Raw Data Validation (check_raw_data.py)
            │
            ▼
    Pandas Data Cleaning (clean_data.py)
            │
            ▼
     Cleaned CSV Files (data/cleaned/)
            │
            ▼
      SQLite Database (ecommerce.db)
            │
            ▼
   SQL Analytics (aggregations, window functions,
   cohort analysis, RFM, segmentation)
            │
            ▼
      Python CLI Tool (report_cli.py)
```

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Data generation, cleaning, validation, CLI |
| Pandas | Data cleaning and transformation |
| Faker | Realistic customer / product data generation |
| SQLite | Relational database |
| SQL | Business analytics and reporting |
| Window Functions | Ranking, running totals, moving averages, comparisons |
| CTEs | Multi-step SQL analysis |
| Tabulate | CLI table formatting |
| pytest | Edge case testing |

## 📂 Project Structure

```
ecommerce_analytics/
├── data/
│   ├── raw/                       # generated, messy CSVs
│   │   ├── customers.csv
│   │   ├── products.csv
│   │   ├── orders.csv
│   │   └── order_items.csv
│   └── cleaned/                    # cleaned CSVs
│       ├── customers_clean.csv
│       ├── products_clean.csv
│       ├── orders_clean.csv
│       └── order_items_clean.csv
│
├── output/
│   ├── cleaning_report.csv          # before/after counts per cleaning check
│   └── sample_reports/               # saved output of every CLI report
│       ├── revenue.txt
│       ├── top_customers.txt
│       ├── top_products.txt
│       ├── aov.txt
│       ├── segments.txt
│       ├── rfm.txt
│       ├── retention.txt
│       └── category.txt
│
├── scripts/
│   ├── generate_data.py             # Step 1: data generation
│   ├── check_raw_data.py            # Step 2: raw data validation
│   ├── clean_data.py                # Step 3: pandas cleaning
│   ├── load_database.py             # Step 4: load into SQLite
│   ├── run_sql.py                   # generic .sql file runner
│   ├── report_cli.py                # Step 9: CLI reporting tool
│   └── dashboard_app.py             # Flask backend for the web dashboard
│
├── frontend/
│   └── dashboard.html                # web dashboard UI (all 8 reports + overview)
│
├── sql/
│   ├── schema.sql                   # table definitions, PK/FK, indexes
│   ├── aggregations.sql             # Step 5: joins & aggregations
│   ├── window_functions.sql         # Step 6: RANK/DENSE_RANK/LAG/NTILE etc.
│   ├── cohort_analysis.sql          # Step 7: cohorts & retention
│   └── customer_segmentation.sql    # Step 8: frequency/spend/RFM segmentation
│
├── tests/
│   ├── test_edge_cases.py           # empty database
│   ├── test_future_date.py          # future-dated orders
│   └── test_single_customer.py      # minimal 1-customer dataset
│
├── ecommerce.db
├── setup_project.py                  # runs the entire pipeline end-to-end
├── requirements.txt
└── README.md
```

## 📦 Installation

```bash
pip install -r requirements.txt
```

## ▶️ Running the Complete Project

Run everything in one command:

```bash
python3 setup_project.py
```

This runs, in order: generate → validate → clean → load DB → aggregations →
window functions → cohort analysis → segmentation/RFM → sample reports →
edge case tests. It exits non-zero on the first failure.

### Or run each stage individually

```bash
# Step 1: generate raw messy data into data/raw/
python3 scripts/generate_data.py

# Step 2: validate raw data quality (read-only, prints a report)
python3 scripts/check_raw_data.py

# Step 3: clean data into data/cleaned/, write output/cleaning_report.csv
python3 scripts/clean_data.py

# Step 4: build ecommerce.db from sql/schema.sql and load cleaned CSVs
python3 scripts/load_database.py

# Step 5: joins & aggregations
python3 scripts/run_sql.py sql/aggregations.sql

# Step 6: window functions & CTEs
python3 scripts/run_sql.py sql/window_functions.sql

# Step 7: cohort & retention analysis
python3 scripts/run_sql.py sql/cohort_analysis.sql

# Step 8: customer segmentation & RFM
python3 scripts/run_sql.py sql/customer_segmentation.sql

# Step 9: CLI reports
python3 scripts/report_cli.py --report revenue
python3 scripts/report_cli.py --report top_customers
python3 scripts/report_cli.py --report top_products
python3 scripts/report_cli.py --report aov
python3 scripts/report_cli.py --report segments
python3 scripts/report_cli.py --report rfm
python3 scripts/report_cli.py --report retention
python3 scripts/report_cli.py --report category
python3 scripts/report_cli.py --help

# Step 10: edge case tests
python3 tests/test_edge_cases.py
python3 tests/test_future_date.py
python3 tests/test_single_customer.py
# or all at once:
python3 -m pytest tests/ -v
```

## 🖥️ Web Dashboard

A full browser dashboard covers all 8 reports, plus an overview page with
KPI cards and charts. It's a Flask backend (`scripts/dashboard_app.py`) that
imports the exact same `REPORTS` functions from `report_cli.py` — so every
number shown in the browser matches the CLI output exactly.

```bash
pip install flask     # already in requirements.txt
cd scripts
python3 dashboard_app.py
```

Then open **http://localhost:5000**. Sidebar navigation:

| Page | Shows |
|---|---|
| Overview | KPI cards (revenue, orders, customers, AOV) + monthly revenue line chart + category donut chart |
| Revenue | Monthly revenue bar chart + full data table |
| Category | Revenue-by-category horizontal bar chart + table |
| Top Products | Top 10 products by revenue, chart + table (revenue & units sold) |
| Top Customers | Top 10 customers by revenue, chart + table |
| AOV | KPI cards: average / min / max order value, total orders |
| Segments | One-Time / Occasional / Loyal donut chart + table |
| RFM | Segment bar chart + color-coded table (Champions/Loyal/At Risk/Lost badges) |
| Retention | Cohort retention table (month 0–3, with retention %) |

API endpoints, if you want to hit them directly:
- `GET /api/overview` → KPI summary
- `GET /api/reports` → list of valid report names
- `GET /api/report/<name>` → `{ headers, rows }` for any of the 8 report types

Charts use Chart.js (loaded from CDN); everything else is plain HTML/CSS/JS,
no build step required.

## 📊 Available Reports

| Report | Description |
|---|---|
| `revenue` | Monthly revenue trend |
| `top_customers` | Top 10 customers by revenue |
| `top_products` | Top 10 products by revenue and units sold |
| `aov` | Average Order Value (+ min / max / order count) |
| `segments` | Purchase-frequency segmentation (One-Time / Occasional / Loyal) |
| `rfm` | RFM segment summary (Champions, Loyal, At Risk, Lost, etc.) |
| `retention` | Cohort retention rate, month 0 through month 3 |
| `category` | Revenue by product category |

Invalid report names are rejected by `argparse` itself:
```bash
$ python3 scripts/report_cli.py --report abc
error: argument --report: invalid choice: 'abc' (choose from 'revenue', 'top_customers', ...)
```

## 🧪 Edge Case Testing

| Test file | What it verifies |
|---|---|
| `test_edge_cases.py` | All 8 CLI reports run without error against a completely empty database (no divide-by-zero, no crashes on empty result sets) |
| `test_future_date.py` | Future-dated orders are seeded, correctly flagged by `clean_data.py` (`is_future_dated`), and remain queryable/filterable in the database rather than being silently dropped |
| `test_single_customer.py` | All 8 CLI reports run correctly against a minimal 1-customer / 1-order / 1-product dataset, and the revenue formula is verified against a hand-calculated value |

Run all of them:
```bash
python3 -m pytest tests/ -v
```

## 🔐 Data Quality & Design Notes

- **Intentional raw-data issues** (seeded by `generate_data.py`): duplicate
  rows in every table, missing `customer_id` (~5% of orders), invalid dates
  (`DD-MM-YYYY` in ~8% of orders), 2 deliberately future-dated orders,
  messy product-name casing/whitespace, invalid emails (~2%), numeric fields
  occasionally stored as text (`"5"`, `"12.5%"`), 8 orphaned `order_items`
  rows, and a few rows with `discount_percent > 100`.
- **Cleaning philosophy**: rather than silently dropping rows with issues,
  `clean_data.py` mostly **flags** them (`customer_id_missing`,
  `is_future_dated`, `email_valid`) so they stay auditable in the database.
  The only rows actually dropped are ones that break referential integrity
  (`order_items` with no matching `order_id`/`product_id`) or truly can't be
  parsed as numbers — those can't be meaningfully analyzed either way.
  `discount_percent > 100` is capped at 100 rather than dropped, since it's
  a clear data-entry bug (not a broken relationship) and capping avoids
  the negative-revenue value the raw formula would otherwise produce.
- **Revenue formula**, used consistently everywhere:
  `quantity * unit_price * (1 - discount_percent / 100)`. Only
  positive-quantity rows count as purchases.
- **RFM scoring**: Recency, Frequency, and Monetary are each bucketed into
  quintiles (`NTILE(5)`) per customer. Recency is inverted so that a
  *lower* `recency_days` (a more recent purchase) maps to a *higher* R
  score — this is a common off-by-inversion bug in RFM SQL and was caught
  and fixed during testing.
- **Cohorts** are defined by each customer's **first order month**, not
  their registration date, since retention is measured from actual
  purchase behavior.

## 📈 Business Questions This Answers

- Which customers and products generate the most revenue?
- Which categories perform best?
- What's the monthly revenue trend, and how volatile is it (moving average)?
- What's the Average Order Value?
- Which customers are one-time buyers vs. loyal repeat buyers?
- Which customers are high-value (Champions) vs. at risk of churning?
- How well are customer cohorts retained over their first few months?

## Sample results (from a generated run)

- 600 customers, 148 products, 1,500 orders, 3,500 order_items after cleaning
  (out of 606 / 152 / 1,505 / 3,514 raw rows — duplicates and orphaned rows removed)
- 80 orders (~5%) with missing customer_id, flagged not dropped
- 108 orders (~7%) with `DD-MM-YYYY` dates, all successfully reparsed
- 2 future-dated orders, correctly flagged
- 8 orphaned `order_items` rows, correctly dropped
- All SQL files (aggregations, window functions, cohort analysis,
  segmentation) run without error against the cleaned database
- 6/6 edge case tests pass (`pytest tests/`)
