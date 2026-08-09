-- ============================================================
-- aggregations.sql - Basic joins & aggregations (Step 5)
-- Revenue formula: quantity * unit_price * (1 - discount_percent/100)
-- Only positive-quantity rows count as purchases.
-- ============================================================

-- 1. Total revenue per customer
SELECT
    c.customer_id,
    c.customer_name,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS total_revenue
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE oi.quantity > 0
GROUP BY c.customer_id, c.customer_name
ORDER BY total_revenue DESC;


-- 2. Total revenue per category
SELECT
    p.category,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS total_revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
WHERE oi.quantity > 0
GROUP BY p.category
ORDER BY total_revenue DESC;


-- 3. Monthly revenue (all time)
SELECT
    strftime('%Y-%m', o.order_date) AS year_month,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE oi.quantity > 0
GROUP BY year_month
ORDER BY year_month;


-- 4. Top products by quantity sold
SELECT
    p.product_id,
    p.product_name,
    SUM(oi.quantity) AS units_sold
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
WHERE oi.quantity > 0
GROUP BY p.product_id, p.product_name
ORDER BY units_sold DESC
LIMIT 15;


-- 5. Top products by revenue
SELECT
    p.product_id,
    p.product_name,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
WHERE oi.quantity > 0
GROUP BY p.product_id, p.product_name
ORDER BY revenue DESC
LIMIT 15;


-- 6. Top 10 customers by revenue
SELECT
    c.customer_id,
    c.customer_name,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS revenue
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE oi.quantity > 0
GROUP BY c.customer_id, c.customer_name
ORDER BY revenue DESC
LIMIT 10;


-- 7. Average Order Value (AOV)
WITH order_totals AS (
    SELECT
        o.order_id,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS order_value
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE oi.quantity > 0
    GROUP BY o.order_id
)
SELECT ROUND(AVG(order_value), 2) AS average_order_value
FROM order_totals;


-- 8. Customer-level order statistics (order count, total spend, avg spend)
SELECT
    c.customer_id,
    c.customer_name,
    COUNT(DISTINCT o.order_id) AS order_count,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS total_spend,
    ROUND(AVG(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS avg_line_value
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
LEFT JOIN order_items oi ON oi.order_id = o.order_id AND oi.quantity > 0
GROUP BY c.customer_id, c.customer_name
ORDER BY total_spend DESC
LIMIT 15;
