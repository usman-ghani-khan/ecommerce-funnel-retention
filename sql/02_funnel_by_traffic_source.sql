-- ============================================================
-- Query 2: Funnel Conversion by Traffic Source
-- ============================================================
-- Breaks down funnel performance by acquisition channel.
-- Identifies which traffic sources drive the highest-quality
-- visitors (those who convert to purchase, not just sessions).
-- Uses CTEs for readability and modular stage-level counts.
-- ============================================================

WITH stage_counts AS (
    SELECT
        traffic_source,
        COUNT(DISTINCT CASE WHEN event_type = 'home'     THEN user_id END) AS users_home,
        COUNT(DISTINCT CASE WHEN event_type = 'category' THEN user_id END) AS users_category,
        COUNT(DISTINCT CASE WHEN event_type = 'product'  THEN user_id END) AS users_product,
        COUNT(DISTINCT CASE WHEN event_type = 'cart'     THEN user_id END) AS users_cart,
        COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END) AS users_purchase
    FROM events
    GROUP BY traffic_source
)

SELECT
    traffic_source,
    users_home,
    users_category,
    users_product,
    users_cart,
    users_purchase,

    -- Stage-to-stage conversion rates
    ROUND(100.0 * users_category / NULLIF(users_home, 0), 1)     AS pct_home_to_category,
    ROUND(100.0 * users_product  / NULLIF(users_category, 0), 1) AS pct_category_to_product,
    ROUND(100.0 * users_cart     / NULLIF(users_product, 0), 1)  AS pct_product_to_cart,
    ROUND(100.0 * users_purchase / NULLIF(users_cart, 0), 1)     AS pct_cart_to_purchase,

    -- Overall session-to-purchase conversion
    ROUND(100.0 * users_purchase / NULLIF(users_home, 0), 2)     AS overall_conversion_pct

FROM stage_counts
ORDER BY overall_conversion_pct DESC;
