-- ============================================================
-- Query 3: Funnel Conversion by Device Type
-- ============================================================
-- Identifies whether mobile, desktop, or tablet users convert
-- at different rates. Critical for product and UX decisions
-- (e.g., mobile checkout friction).
-- ============================================================

WITH device_stages AS (
    SELECT
        device_type,
        COUNT(DISTINCT CASE WHEN event_type = 'home'     THEN user_id END) AS users_home,
        COUNT(DISTINCT CASE WHEN event_type = 'category' THEN user_id END) AS users_category,
        COUNT(DISTINCT CASE WHEN event_type = 'product'  THEN user_id END) AS users_product,
        COUNT(DISTINCT CASE WHEN event_type = 'cart'     THEN user_id END) AS users_cart,
        COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END) AS users_purchase
    FROM events
    GROUP BY device_type
)

SELECT
    device_type,
    users_home,
    users_purchase,
    ROUND(100.0 * users_product  / NULLIF(users_home, 0), 1)     AS pct_reached_product,
    ROUND(100.0 * users_cart     / NULLIF(users_product, 0), 1)  AS pct_product_to_cart,
    ROUND(100.0 * users_purchase / NULLIF(users_cart, 0), 1)     AS pct_cart_to_purchase,
    ROUND(100.0 * users_purchase / NULLIF(users_home, 0), 2)     AS overall_conversion_pct
FROM device_stages
ORDER BY overall_conversion_pct DESC;
