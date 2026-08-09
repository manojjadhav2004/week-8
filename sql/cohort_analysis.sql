-- ============================================================
-- cohort_analysis.sql - Cohort & retention analysis (Step 7)
-- Customers are grouped by the month of their FIRST purchase (order),
-- not their registration date -- a cohort here means "first ordered in X".
-- ============================================================

-- 1. Assign each customer to a cohort (their first order month)
WITH first_order AS (
    SELECT
        customer_id,
        MIN(date(order_date)) AS first_order_date
    FROM orders
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
)
SELECT
    customer_id,
    strftime('%Y-%m', first_order_date) AS cohort_month
FROM first_order
ORDER BY cohort_month, customer_id
LIMIT 20;


-- 2. Cohort size (number of customers per cohort)
WITH first_order AS (
    SELECT customer_id, MIN(date(order_date)) AS first_order_date
    FROM orders
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
)
SELECT
    strftime('%Y-%m', first_order_date) AS cohort_month,
    COUNT(*) AS cohort_size
FROM first_order
GROUP BY cohort_month
ORDER BY cohort_month;


-- 3. Monthly customer activity relative to their cohort month (month_index)
WITH first_order AS (
    SELECT customer_id, MIN(date(order_date)) AS first_order_date
    FROM orders
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
),
activity AS (
    SELECT
        o.customer_id,
        strftime('%Y-%m', f.first_order_date) AS cohort_month,
        (CAST(strftime('%Y', o.order_date) AS INTEGER) - CAST(strftime('%Y', f.first_order_date) AS INTEGER)) * 12
          + (CAST(strftime('%m', o.order_date) AS INTEGER) - CAST(strftime('%m', f.first_order_date) AS INTEGER))
          AS month_index
    FROM orders o
    JOIN first_order f ON f.customer_id = o.customer_id
    WHERE o.customer_id IS NOT NULL
)
SELECT
    cohort_month,
    month_index,
    COUNT(DISTINCT customer_id) AS active_customers
FROM activity
WHERE month_index BETWEEN 0 AND 5
GROUP BY cohort_month, month_index
ORDER BY cohort_month, month_index
LIMIT 30;


-- 4. Repeat customers (placed more than one order)
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE customer_id IS NOT NULL
GROUP BY customer_id
HAVING order_count > 1
ORDER BY order_count DESC
LIMIT 20;


-- 5. Retention rate per cohort (month 0 through month 3)
WITH first_order AS (
    SELECT customer_id, MIN(date(order_date)) AS first_order_date
    FROM orders
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
),
cohort_size AS (
    SELECT strftime('%Y-%m', first_order_date) AS cohort_month, COUNT(*) AS size
    FROM first_order
    GROUP BY cohort_month
),
activity AS (
    SELECT
        o.customer_id,
        strftime('%Y-%m', f.first_order_date) AS cohort_month,
        (CAST(strftime('%Y', o.order_date) AS INTEGER) - CAST(strftime('%Y', f.first_order_date) AS INTEGER)) * 12
          + (CAST(strftime('%m', o.order_date) AS INTEGER) - CAST(strftime('%m', f.first_order_date) AS INTEGER))
          AS month_index
    FROM orders o
    JOIN first_order f ON f.customer_id = o.customer_id
    WHERE o.customer_id IS NOT NULL
),
retained AS (
    SELECT cohort_month, month_index, COUNT(DISTINCT customer_id) AS active_customers
    FROM activity
    WHERE month_index BETWEEN 0 AND 3
    GROUP BY cohort_month, month_index
)
SELECT
    r.cohort_month,
    r.month_index,
    r.active_customers,
    cs.size AS cohort_size,
    ROUND(1.0 * r.active_customers / cs.size * 100, 2) AS retention_rate_percent
FROM retained r
JOIN cohort_size cs ON cs.cohort_month = r.cohort_month
ORDER BY r.cohort_month, r.month_index
LIMIT 30;


-- 6. Churned customers: no order in the 6 months following their first order,
--    but the data window has enough history to know that for sure.
WITH first_order AS (
    SELECT customer_id, MIN(date(order_date)) AS first_order_date
    FROM orders
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
),
last_order AS (
    SELECT customer_id, MAX(date(order_date)) AS last_order_date
    FROM orders
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
),
dataset_max_date AS (
    SELECT MAX(date(order_date)) AS max_date FROM orders
)
SELECT
    f.customer_id,
    f.first_order_date,
    l.last_order_date,
    CAST(julianday(dm.max_date) - julianday(l.last_order_date) AS INTEGER) AS days_since_last_order
FROM first_order f
JOIN last_order l ON l.customer_id = f.customer_id
CROSS JOIN dataset_max_date dm
WHERE julianday(dm.max_date) - julianday(l.last_order_date) > 180
ORDER BY days_since_last_order DESC
LIMIT 20;
