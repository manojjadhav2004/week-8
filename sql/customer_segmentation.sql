-- ============================================================
-- customer_segmentation.sql - Segmentation & RFM analysis (Step 8)
-- ============================================================

-- 1. Purchase frequency segmentation: One-Time / Occasional / Loyal
WITH order_counts AS (
    SELECT customer_id, COUNT(*) AS order_count
    FROM orders
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
)
SELECT
    customer_id,
    order_count,
    CASE
        WHEN order_count = 1 THEN 'One-Time'
        WHEN order_count BETWEEN 2 AND 4 THEN 'Occasional'
        ELSE 'Loyal'
    END AS frequency_segment
FROM order_counts
ORDER BY order_count DESC
LIMIT 30;


-- 2. Frequency segment summary (counts per segment)
WITH order_counts AS (
    SELECT customer_id, COUNT(*) AS order_count
    FROM orders
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
),
segmented AS (
    SELECT
        customer_id,
        CASE
            WHEN order_count = 1 THEN 'One-Time'
            WHEN order_count BETWEEN 2 AND 4 THEN 'Occasional'
            ELSE 'Loyal'
        END AS frequency_segment
    FROM order_counts
)
SELECT frequency_segment, COUNT(*) AS customer_count
FROM segmented
GROUP BY frequency_segment
ORDER BY customer_count DESC;


-- 3. Spend tier segmentation: Low / Medium / High
WITH customer_spend AS (
    SELECT
        o.customer_id,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS total_spend
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE oi.quantity > 0 AND o.customer_id IS NOT NULL
    GROUP BY o.customer_id
)
SELECT
    customer_id,
    ROUND(total_spend, 2) AS total_spend,
    CASE
        WHEN total_spend > 100000 THEN 'High'
        WHEN total_spend >= 40000 THEN 'Medium'
        ELSE 'Low'
    END AS spend_tier
FROM customer_spend
ORDER BY total_spend DESC
LIMIT 30;


-- 4. Spend tier summary
WITH customer_spend AS (
    SELECT
        o.customer_id,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS total_spend
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE oi.quantity > 0 AND o.customer_id IS NOT NULL
    GROUP BY o.customer_id
),
tiered AS (
    SELECT
        customer_id,
        CASE
            WHEN total_spend > 100000 THEN 'High'
            WHEN total_spend >= 40000 THEN 'Medium'
            ELSE 'Low'
        END AS spend_tier
    FROM customer_spend
)
SELECT spend_tier, COUNT(*) AS customer_count
FROM tiered
GROUP BY spend_tier
ORDER BY customer_count DESC;


-- 5. RFM base metrics: Recency, Frequency, Monetary per customer
WITH dataset_max_date AS (
    SELECT MAX(date(order_date)) AS max_date FROM orders
),
rfm_base AS (
    SELECT
        o.customer_id,
        CAST(julianday(dm.max_date) - julianday(MAX(date(o.order_date))) AS INTEGER) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS monetary
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    CROSS JOIN dataset_max_date dm
    WHERE oi.quantity > 0 AND o.customer_id IS NOT NULL
    GROUP BY o.customer_id
)
SELECT
    customer_id,
    recency_days,
    frequency,
    ROUND(monetary, 2) AS monetary
FROM rfm_base
ORDER BY monetary DESC
LIMIT 20;


-- 6. RFM scoring (1-5 quintiles per dimension) and segment labeling
WITH dataset_max_date AS (
    SELECT MAX(date(order_date)) AS max_date FROM orders
),
rfm_base AS (
    SELECT
        o.customer_id,
        CAST(julianday(dm.max_date) - julianday(MAX(date(o.order_date))) AS INTEGER) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS monetary
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    CROSS JOIN dataset_max_date dm
    WHERE oi.quantity > 0 AND o.customer_id IS NOT NULL
    GROUP BY o.customer_id
),
rfm_scores AS (
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary,
        -- Lower recency_days is better -> reverse the quintile order
        6 - NTILE(5) OVER (ORDER BY recency_days ASC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
    FROM rfm_base
)
SELECT
    customer_id,
    recency_days,
    frequency,
    ROUND(monetary, 2) AS monetary,
    r_score, f_score, m_score,
    (r_score + f_score + m_score) AS rfm_total,
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
ORDER BY rfm_total DESC
LIMIT 30;


-- 7. RFM segment summary (customer count + avg monetary per segment)
WITH dataset_max_date AS (
    SELECT MAX(date(order_date)) AS max_date FROM orders
),
rfm_base AS (
    SELECT
        o.customer_id,
        CAST(julianday(dm.max_date) - julianday(MAX(date(o.order_date))) AS INTEGER) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS monetary
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    CROSS JOIN dataset_max_date dm
    WHERE oi.quantity > 0 AND o.customer_id IS NOT NULL
    GROUP BY o.customer_id
),
rfm_scores AS (
    SELECT
        customer_id,
        monetary,
        6 - NTILE(5) OVER (ORDER BY recency_days ASC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
    FROM rfm_base
),
labeled AS (
    SELECT
        customer_id,
        monetary,
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
SELECT
    rfm_segment,
    COUNT(*) AS customer_count,
    ROUND(AVG(monetary), 2) AS avg_monetary
FROM labeled
GROUP BY rfm_segment
ORDER BY customer_count DESC;
