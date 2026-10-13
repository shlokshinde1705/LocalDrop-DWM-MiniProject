-- ============================================================================
-- LocalDrop Data Warehouse: Fact Constellation Schema
-- Architecture: Multiple Fact Tables sharing Conformed Dimensions
-- Tables: FACT_SALES (Financial Settlement) & FACT_ORDERS (Order Lifecycle & Fulfillment)
-- ============================================================================

-- Fact Table 2: FACT_ORDERS (Order Logistics & Fulfillment Fact)
-- Shares DIM_CUSTOMER, DIM_PRODUCT, DIM_SUPPLIER, DIM_DATE with FACT_SALES
CREATE TABLE IF NOT EXISTS FACT_ORDERS (
    order_key INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,          -- Natural Business Key
    customer_key INTEGER NOT NULL,      -- FK to Conformed DIM_CUSTOMER
    product_key INTEGER NOT NULL,       -- FK to Conformed DIM_PRODUCT
    supplier_key INTEGER NOT NULL,      -- FK to Conformed DIM_SUPPLIER
    date_key INTEGER NOT NULL,          -- FK to Conformed DIM_DATE
    quantity INTEGER NOT NULL,          -- Additive Measure
    order_status TEXT NOT NULL,         -- Degenerate Dimension
    is_delivered INTEGER NOT NULL,      -- Semi-additive Flag (1/0)
    is_shipped INTEGER NOT NULL,        -- Semi-additive Flag (1/0)
    is_processing INTEGER NOT NULL,     -- Semi-additive Flag (1/0)
    is_cancelled INTEGER NOT NULL,      -- Semi-additive Flag (1/0)
    is_returned INTEGER NOT NULL,       -- Semi-additive Flag (1/0)
    FOREIGN KEY (customer_key) REFERENCES DIM_CUSTOMER(customer_key),
    FOREIGN KEY (product_key) REFERENCES DIM_PRODUCT(product_key),
    FOREIGN KEY (supplier_key) REFERENCES DIM_SUPPLIER(supplier_key),
    FOREIGN KEY (date_key) REFERENCES DIM_DATE(date_key)
);

CREATE INDEX IF NOT EXISTS idx_const_orders_customer ON FACT_ORDERS(customer_key);
CREATE INDEX IF NOT EXISTS idx_const_orders_product ON FACT_ORDERS(product_key);
CREATE INDEX IF NOT EXISTS idx_const_orders_supplier ON FACT_ORDERS(supplier_key);
CREATE INDEX IF NOT EXISTS idx_const_orders_date ON FACT_ORDERS(date_key);
CREATE INDEX IF NOT EXISTS idx_const_orders_status ON FACT_ORDERS(order_status);
