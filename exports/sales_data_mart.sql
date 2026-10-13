-- ============================================================================
-- LocalDrop Data Warehouse: Sales Data Mart Definition
-- Architecture: Purpose-Built Dimensional Views for Business Intelligence
-- Pre-aggregated views accelerating executive and departmental reporting
-- ============================================================================

-- 1. Monthly Category Sales View
DROP VIEW IF EXISTS DM_MONTHLY_CATEGORY_SALES;
CREATE VIEW DM_MONTHLY_CATEGORY_SALES AS
SELECT
    d.year,
    d.quarter,
    d.month,
    d.month_name,
    p.category,
    COUNT(f.sale_id) AS total_transactions,
    SUM(f.quantity) AS units_sold,
    ROUND(SUM(f.total_amount), 2) AS gross_revenue,
    ROUND(SUM(f.profit), 2) AS net_profit,
    ROUND(AVG(f.total_amount), 2) AS average_order_value,
    ROUND((SUM(f.profit) / SUM(f.total_amount)) * 100, 2) AS profit_margin_pct
FROM FACT_SALES f
JOIN DIM_DATE d ON f.date_key = d.date_key
JOIN DIM_PRODUCT p ON f.product_key = p.product_key
GROUP BY d.year, d.quarter, d.month, d.month_name, p.category;

-- 2. Supplier Scorecard View
DROP VIEW IF EXISTS DM_SUPPLIER_SCORECARD;
CREATE VIEW DM_SUPPLIER_SCORECARD AS
SELECT
    s.supplier_id,
    s.supplier_name,
    s.city,
    s.state,
    s.rating,
    COUNT(f.sale_id) AS fulfilled_orders,
    SUM(f.quantity) AS total_units_dispatched,
    ROUND(SUM(f.total_amount), 2) AS total_revenue_generated,
    ROUND(SUM(f.profit), 2) AS total_profit_generated,
    ROUND((SUM(f.profit) / SUM(f.total_amount)) * 100, 2) AS supplier_margin_pct
FROM FACT_SALES f
JOIN DIM_SUPPLIER s ON f.supplier_key = s.supplier_key
GROUP BY s.supplier_id, s.supplier_name, s.city, s.state, s.rating;

-- 3. Customer RFM & Lifetime Value View
DROP VIEW IF EXISTS DM_CUSTOMER_RFM;
CREATE VIEW DM_CUSTOMER_RFM AS
SELECT
    c.customer_id,
    c.customer_name,
    c.city,
    c.state,
    c.registration_date,
    MAX(d.date) AS last_purchase_date,
    COUNT(f.sale_id) AS total_orders_placed,
    SUM(f.quantity) AS total_items_bought,
    ROUND(SUM(f.total_amount), 2) AS lifetime_spending,
    ROUND(AVG(f.total_amount), 2) AS avg_basket_size,
    ROUND(SUM(f.profit), 2) AS lifetime_profit_contribution
FROM FACT_SALES f
JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
JOIN DIM_DATE d ON f.date_key = d.date_key
GROUP BY c.customer_id, c.customer_name, c.city, c.state, c.registration_date;

-- 4. Geographic City Sales Distribution View
DROP VIEW IF EXISTS DM_CITY_PERFORMANCE;
CREATE VIEW DM_CITY_PERFORMANCE AS
SELECT
    c.state,
    c.city,
    COUNT(DISTINCT c.customer_id) AS active_customer_base,
    COUNT(f.sale_id) AS order_volume,
    ROUND(SUM(f.total_amount), 2) AS total_city_revenue,
    ROUND(SUM(f.profit), 2) AS total_city_profit
FROM FACT_SALES f
JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
GROUP BY c.state, c.city;
