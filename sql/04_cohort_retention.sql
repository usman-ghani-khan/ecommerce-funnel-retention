-- ============================================================
-- Query 4: Monthly Cohort Retention
-- ============================================================
-- Groups users by their first purchase month (acquisition cohort).
-- Measures what % of each cohort returns to purchase in subsequent
-- months (Month 0 = first purchase month, Month 1 = one month later, etc.)
--
-- Technique: 
--   1. CTE to find each user's first purchase date
--   2. Join back to all orders to get repeat purchases
--   3. Calculate month offset between cohort month and order month
--   4. Aggregate to get retention rates per cohort x month offset
-- ============================================================

WITH first_purchase AS (
    -- Each user's first order date → defines their cohort
    SELECT
        user_id,
        MIN(DATE_TRUNC('month', created_at)) AS cohort_month
    FROM orders
    WHERE status IN ('Complete', 'Returned', 'Shipped')
    GROUP BY user_id
),

user_orders AS (
    -- All orders per user with month offset from their cohort
    SELECT
        o.user_id,
        fp.cohort_month,
        DATE_TRUNC('month', o.created_at)                            AS order_month,
        -- Month number since first purchase (0 = acquisition month)
        CAST(
            (EXTRACT(YEAR FROM o.created_at)  - EXTRACT(YEAR FROM fp.cohort_month)) * 12
          + (EXTRACT(MONTH FROM o.created_at) - EXTRACT(MONTH FROM fp.cohort_month))
        AS INTEGER)                                                  AS month_number
    FROM orders o
    JOIN first_purchase fp ON o.user_id = fp.user_id
    WHERE o.status IN ('Complete', 'Returned', 'Shipped')
),

cohort_sizes AS (
    -- Number of users in each cohort (denominator for retention %)
    SELECT
        cohort_month,
        COUNT(DISTINCT user_id) AS cohort_size
    FROM first_purchase
    GROUP BY cohort_month
)

SELECT
    uo.cohort_month,
    cs.cohort_size,
    uo.month_number,
    COUNT(DISTINCT uo.user_id)                                               AS retained_users,
    ROUND(
        100.0 * COUNT(DISTINCT uo.user_id) / NULLIF(cs.cohort_size, 0), 1
    )                                                                        AS retention_pct
FROM user_orders uo
JOIN cohort_sizes cs ON uo.cohort_month = cs.cohort_month
WHERE uo.month_number BETWEEN 0 AND 11     -- track up to 12 months
GROUP BY uo.cohort_month, cs.cohort_size, uo.month_number
ORDER BY uo.cohort_month, uo.month_number;
