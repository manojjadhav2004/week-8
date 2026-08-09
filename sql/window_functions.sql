-- ============================================================
-- window_functions.sql - Advanced analytical calculations (Step 6)
-- ============================================================

-- 1. Rank customers by lifetime value (RANK)
WITH customer_ltv AS (
    SELECT
        o.customer_id,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS lifetime_value
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE oi.quantity > 0 AND o.customer_id IS NOT NULL
    GROUP BY o.customer_id
)
SELECT
    customer_id,
    ROUND(lifetime_value, 2) AS lifetime_value,
    RANK() OVER (ORDER BY lifetime_value DESC) AS ltv_rank
FROM customer_ltv
ORDER BY ltv_rank
LIMIT 20;


-- 2. Cumulative (running) revenue over time
WITH daily_revenue AS (
    SELECT
        date(o.order_date) AS order_date,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE oi.quantity > 0
    GROUP BY date(o.order_date)
)
SELECT
    order_date,
    ROUND(revenue, 2) AS revenue,
    ROUND(SUM(revenue) OVER (ORDER BY order_date
          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_revenue
FROM daily_revenue
ORDER BY order_date
LIMIT 20;


-- 3. Three-month moving average of revenue
WITH monthly_revenue AS (
    SELECT
        strftime('%Y-%m', o.order_date) AS year_month,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE oi.quantity > 0
    GROUP BY year_month
)
SELECT
    year_month,
    ROUND(revenue, 2) AS revenue,
    ROUND(AVG(revenue) OVER (
        ORDER BY year_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS moving_avg_3month
FROM monthly_revenue
ORDER BY year_month;


-- 4. Current-month vs previous-month revenue comparison (LAG)
WITH monthly_revenue AS (
    SELECT
        strftime('%Y-%m', o.order_date) AS year_month,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE oi.quantity > 0
    GROUP BY year_month
)
SELECT
    year_month,
    ROUND(revenue, 2) AS revenue,
    ROUND(LAG(revenue) OVER (ORDER BY year_month), 2) AS previous_month_revenue
FROM monthly_revenue
ORDER BY year_month;


-- 5. Month-over-month revenue growth %
WITH monthly_revenue AS (
    SELECT
        strftime('%Y-%m', o.order_date) AS year_month,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE oi.quantity > 0
    GROUP BY year_month
),
with_lag AS (
    SELECT
        year_month,
        revenue,
        LAG(revenue) OVER (ORDER BY year_month) AS prev_revenue
    FROM monthly_revenue
)
SELECT
    year_month,
    ROUND(revenue, 2) AS revenue,
    ROUND(prev_revenue, 2) AS previous_month_revenue,
    CASE WHEN prev_revenue IS NULL OR prev_revenue = 0 THEN NULL
         ELSE ROUND((revenue - prev_revenue) / prev_revenue * 100, 2)
    END AS mom_growth_percent
FROM with_lag
ORDER BY year_month;


-- 6. Rank products within each category by revenue (DENSE_RANK)
WITH product_revenue AS (
    SELECT
        p.category,
        p.product_name,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS revenue
    FROM order_items oi
    JOIN products p ON p.product_id = oi.product_id
    WHERE oi.quantity > 0
    GROUP BY p.category, p.product_name
)
SELECT
    category,
    product_name,
    ROUND(revenue, 2) AS revenue,
    DENSE_RANK() OVER (PARTITION BY category ORDER BY revenue DESC) AS rank_in_category
FROM product_revenue
ORDER BY category, rank_in_category
LIMIT 30;


-- 7. Customer order sequencing (ROW_NUMBER)
SELECT
    customer_id,
    order_id,
    order_date,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY date(order_date)) AS order_sequence
FROM orders
WHERE customer_id IS NOT NULL
ORDER BY customer_id, order_sequence
LIMIT 25;


-- 8. Customer lifetime value quartiles (NTILE)
WITH customer_ltv AS (
    SELECT
        o.customer_id,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS lifetime_value
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE oi.quantity > 0 AND o.customer_id IS NOT NULL
    GROUP BY o.customer_id
)
SELECT
    customer_id,
    ROUND(lifetime_value, 2) AS lifetime_value,
    NTILE(4) OVER (ORDER BY lifetime_value DESC) AS ltv_quartile
FROM customer_ltv
ORDER BY ltv_quartile, lifetime_value DESC
LIMIT 20;
