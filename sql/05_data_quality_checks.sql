-- ============================================================
-- Query 5: Data Quality Checks
-- ============================================================
-- Before any analysis, systematically validate the dataset for:
--   (a) Missing values in key fields
--   (b) Duplicate event records
--   (c) Orphaned foreign keys (events referencing missing users)
--   (d) Logical impossibilities (e.g., purchase without prior cart)
--   (e) Outlier revenue values (> 3 standard deviations)
-- Documents all assumptions and flags issues for stakeholders.
-- ============================================================

-- (a) Null / missing value audit across events table
SELECT
    'events'                                                  AS table_name,
    COUNT(*)                                                  AS total_rows,
    SUM(CASE WHEN user_id      IS NULL THEN 1 ELSE 0 END)    AS null_user_id,
    SUM(CASE WHEN session_id   IS NULL THEN 1 ELSE 0 END)    AS null_session_id,
    SUM(CASE WHEN event_type   IS NULL THEN 1 ELSE 0 END)    AS null_event_type,
    SUM(CASE WHEN created_at   IS NULL THEN 1 ELSE 0 END)    AS null_created_at,
    SUM(CASE WHEN traffic_source IS NULL THEN 1 ELSE 0 END)  AS null_traffic_source
FROM events

UNION ALL

SELECT
    'orders',
    COUNT(*),
    SUM(CASE WHEN user_id          IS NULL THEN 1 ELSE 0 END),
    SUM(CASE WHEN total_sale_price IS NULL THEN 1 ELSE 0 END),
    SUM(CASE WHEN status           IS NULL THEN 1 ELSE 0 END),
    SUM(CASE WHEN created_at       IS NULL THEN 1 ELSE 0 END),
    0
FROM orders;

-- ──────────────────────────────────────────────────────────

-- (b) Duplicate event detection
-- Flag any (session_id, event_type) pairs appearing more than once
-- (a user shouldn't trigger the same event twice in one session)
SELECT
    session_id,
    event_type,
    COUNT(*) AS occurrences
FROM events
GROUP BY session_id, event_type
HAVING COUNT(*) > 1
ORDER BY occurrences DESC
LIMIT 20;

-- ──────────────────────────────────────────────────────────

-- (c) Orphaned FK check: events referencing users not in users table
SELECT COUNT(*) AS orphaned_event_rows
FROM events e
LEFT JOIN users u ON e.user_id = u.user_id
WHERE u.user_id IS NULL;

-- ──────────────────────────────────────────────────────────

-- (d) Logical funnel integrity check
-- Purchases should only occur within sessions that had a cart event
-- Flag sessions with a purchase but no cart event (data anomaly)
WITH session_events AS (
    SELECT
        session_id,
        MAX(CASE WHEN event_type = 'cart'     THEN 1 ELSE 0 END) AS had_cart,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS had_purchase
    FROM events
    GROUP BY session_id
)
SELECT
    COUNT(*) AS sessions_with_purchase_no_cart
FROM session_events
WHERE had_purchase = 1 AND had_cart = 0;

-- ──────────────────────────────────────────────────────────

-- (e) Revenue outlier detection using z-score approach
-- Flag orders where sale price is more than 3 std devs from mean
WITH stats AS (
    SELECT
        AVG(total_sale_price)    AS mean_price,
        STDDEV(total_sale_price) AS std_price
    FROM orders
)
SELECT
    o.order_id,
    o.total_sale_price,
    ROUND((o.total_sale_price - s.mean_price) / NULLIF(s.std_price, 0), 2) AS z_score
FROM orders o
CROSS JOIN stats s
WHERE ABS((o.total_sale_price - s.mean_price) / NULLIF(s.std_price, 0)) > 3
ORDER BY z_score DESC;
