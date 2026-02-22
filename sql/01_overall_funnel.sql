-- ============================================================
-- Query 1: Overall Purchase Funnel
-- ============================================================
-- Measures how many unique users reach each stage of the
-- web journey: home → category → product → cart → purchase.
-- Uses conditional aggregation to count distinct users per stage.
-- ============================================================

SELECT
    COUNT(DISTINCT CASE WHEN event_type = 'home'     THEN user_id END) AS stage_1_home,
    COUNT(DISTINCT CASE WHEN event_type = 'category' THEN user_id END) AS stage_2_category,
    COUNT(DISTINCT CASE WHEN event_type = 'product'  THEN user_id END) AS stage_3_product,
    COUNT(DISTINCT CASE WHEN event_type = 'cart'     THEN user_id END) AS stage_4_cart,
    COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END) AS stage_5_purchase,

    -- Drop-off rates between consecutive stages
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN event_type = 'category' THEN user_id END)
              / NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'home' THEN user_id END), 0), 1
    ) AS pct_home_to_category,

    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN event_type = 'product' THEN user_id END)
              / NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'category' THEN user_id END), 0), 1
    ) AS pct_category_to_product,

    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN event_type = 'cart' THEN user_id END)
              / NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'product' THEN user_id END), 0), 1
    ) AS pct_product_to_cart,

    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END)
              / NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'cart' THEN user_id END), 0), 1
    ) AS pct_cart_to_purchase,

    -- Overall conversion: home to purchase
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END)
              / NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'home' THEN user_id END), 0), 2
    ) AS overall_conversion_rate_pct

FROM events;
