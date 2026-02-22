-- ============================================================
-- Query 6: Monthly Revenue & Conversion Trend
-- ============================================================
-- Tracks month-over-month revenue, order volume, and conversion
-- rate to identify seasonality and growth/decline patterns.
-- Uses window functions to compute MoM growth rates.
-- ============================================================

WITH monthly_orders AS (
    SELECT
        DATE_TRUNC('month', o.created_at)   AS order_month,
        COUNT(DISTINCT o.order_id)           AS total_orders,
        COUNT(DISTINCT o.user_id)            AS unique_buyers,
        SUM(o.total_sale_price)              AS total_revenue,
        AVG(o.total_sale_price)              AS avg_order_value
    FROM orders o
    WHERE o.status IN ('Complete', 'Shipped', 'Returned')
    GROUP BY DATE_TRUNC('month', o.created_at)
),

monthly_sessions AS (
    SELECT
        DATE_TRUNC('month', created_at)      AS session_month,
        COUNT(DISTINCT session_id)           AS total_sessions,
        COUNT(DISTINCT user_id)              AS unique_visitors
    FROM events
    WHERE event_type = 'home'
    GROUP BY DATE_TRUNC('month', created_at)
),

combined AS (
    SELECT
        ms.session_month                                             AS month,
        ms.total_sessions,
        ms.unique_visitors,
        COALESCE(mo.total_orders, 0)                                AS total_orders,
        COALESCE(mo.unique_buyers, 0)                               AS unique_buyers,
        COALESCE(mo.total_revenue, 0)                               AS total_revenue,
        COALESCE(mo.avg_order_value, 0)                             AS avg_order_value,
        ROUND(
            100.0 * COALESCE(mo.unique_buyers, 0)
                  / NULLIF(ms.unique_visitors, 0), 2
        )                                                            AS visitor_conversion_pct
    FROM monthly_sessions ms
    LEFT JOIN monthly_orders mo ON ms.session_month = mo.order_month
)

SELECT
    month,
    total_sessions,
    unique_visitors,
    total_orders,
    unique_buyers,
    ROUND(total_revenue, 2)                                          AS total_revenue,
    ROUND(avg_order_value, 2)                                        AS avg_order_value,
    visitor_conversion_pct,

    -- Month-over-month revenue growth using LAG window function
    ROUND(
        100.0 * (total_revenue - LAG(total_revenue) OVER (ORDER BY month))
              / NULLIF(LAG(total_revenue) OVER (ORDER BY month), 0), 1
    )                                                                AS mom_revenue_growth_pct

FROM combined
ORDER BY month;
