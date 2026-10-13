-- 1. Total revenue
SELECT SUM(total_amount) AS total_revenue FROM FACT_SALES;

-- 2. Total orders
SELECT COUNT(DISTINCT order_id) AS total_orders FROM FACT_SALES;

-- 3. Total profit
SELECT SUM(profit) AS total_profit FROM FACT_SALES;

-- 4. Monthly sales
SELECT 
    d.year, 
    d.month, 
    SUM(f.total_amount) as monthly_revenue 
FROM FACT_SALES f
JOIN DIM_DATE d ON f.date_id = d.date_id
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- 5. Top 5 products
SELECT 
    p.product_name, 
    SUM(f.quantity) as total_sold, 
    SUM(f.total_amount) as total_revenue
FROM FACT_SALES f
JOIN DIM_PRODUCT p ON f.product_id = p.product_id
GROUP BY p.product_name
ORDER BY total_revenue DESC
LIMIT 5;

-- 6. Category-wise sales
SELECT 
    p.category, 
    SUM(f.total_amount) as category_revenue
FROM FACT_SALES f
JOIN DIM_PRODUCT p ON f.product_id = p.product_id
GROUP BY p.category
ORDER BY category_revenue DESC;

-- 7. Supplier-wise revenue
SELECT 
    s.supplier_name, 
    SUM(f.total_amount) as total_revenue
FROM FACT_SALES f
JOIN DIM_SUPPLIER s ON f.supplier_id = s.supplier_id
GROUP BY s.supplier_name
ORDER BY total_revenue DESC;

-- 8. Customer-wise spending
SELECT 
    c.customer_name, 
    SUM(f.total_amount) as total_spent
FROM FACT_SALES f
JOIN DIM_CUSTOMER c ON f.customer_id = c.customer_id
GROUP BY c.customer_name
ORDER BY total_spent DESC;

-- 9. Order status distribution (From Operational DB)
-- Note: Data Warehouse FACT_SALES only contains 'Delivered' orders as per our ETL rule.
-- If we want to show all order statuses, we query the operational DB ORDERS table.
SELECT 
    order_status, 
    COUNT(order_id) as status_count
FROM ORDERS
GROUP BY order_status;

-- 10. Average order value
SELECT 
    AVG(order_total) as average_order_value
FROM (
    SELECT order_id, SUM(total_amount) as order_total
    FROM FACT_SALES
    GROUP BY order_id
);
