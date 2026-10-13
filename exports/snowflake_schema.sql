-- ============================================================================
-- LocalDrop Data Warehouse: Snowflake Schema Definition
-- Architecture: Normalized Dimensional Hierarchy
-- Decomposes low-cardinality attributes (Category, Location) into discrete sub-dimensions
-- ============================================================================

-- 1. Sub-Dimension: DIM_CATEGORY (Normalized from Product)
CREATE TABLE IF NOT EXISTS DIM_CATEGORY (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL UNIQUE
);

-- 2. Sub-Dimension: DIM_LOCATION (Normalized from Customer and Supplier)
CREATE TABLE IF NOT EXISTS DIM_LOCATION (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    UNIQUE(city, state)
);

-- 3. Normalized Product Dimension: DIM_PRODUCT_SF
CREATE TABLE IF NOT EXISTS DIM_PRODUCT_SF (
    product_key INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL UNIQUE,
    product_name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    price REAL NOT NULL,
    cost_price REAL NOT NULL,
    FOREIGN KEY (category_id) REFERENCES DIM_CATEGORY(category_id)
);

-- 4. Normalized Customer Dimension: DIM_CUSTOMER_SF
CREATE TABLE IF NOT EXISTS DIM_CUSTOMER_SF (
    customer_key INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL UNIQUE,
    customer_name TEXT NOT NULL,
    location_id INTEGER NOT NULL,
    registration_date TEXT NOT NULL,
    FOREIGN KEY (location_id) REFERENCES DIM_LOCATION(location_id)
);

-- 5. Normalized Supplier Dimension: DIM_SUPPLIER_SF
CREATE TABLE IF NOT EXISTS DIM_SUPPLIER_SF (
    supplier_key INTEGER PRIMARY KEY,
    supplier_id INTEGER NOT NULL UNIQUE,
    supplier_name TEXT NOT NULL,
    location_id INTEGER NOT NULL,
    rating REAL NOT NULL,
    FOREIGN KEY (location_id) REFERENCES DIM_LOCATION(location_id)
);

-- 6. Snowflake Fact Table: FACT_SALES_SF
CREATE TABLE IF NOT EXISTS FACT_SALES_SF (
    sale_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    customer_key INTEGER NOT NULL,
    product_key INTEGER NOT NULL,
    supplier_key INTEGER NOT NULL,
    date_key INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    total_amount REAL NOT NULL,
    profit REAL NOT NULL,
    FOREIGN KEY (customer_key) REFERENCES DIM_CUSTOMER_SF(customer_key),
    FOREIGN KEY (product_key) REFERENCES DIM_PRODUCT_SF(product_key),
    FOREIGN KEY (supplier_key) REFERENCES DIM_SUPPLIER_SF(supplier_key),
    FOREIGN KEY (date_key) REFERENCES DIM_DATE(date_key)
);

-- Performance Indexes on Snowflake Joins
CREATE INDEX IF NOT EXISTS idx_sf_product_category ON DIM_PRODUCT_SF(category_id);
CREATE INDEX IF NOT EXISTS idx_sf_customer_location ON DIM_CUSTOMER_SF(location_id);
CREATE INDEX IF NOT EXISTS idx_sf_supplier_location ON DIM_SUPPLIER_SF(location_id);
CREATE INDEX IF NOT EXISTS idx_sf_fact_customer ON FACT_SALES_SF(customer_key);
CREATE INDEX IF NOT EXISTS idx_sf_fact_product ON FACT_SALES_SF(product_key);
CREATE INDEX IF NOT EXISTS idx_sf_fact_supplier ON FACT_SALES_SF(supplier_key);
CREATE INDEX IF NOT EXISTS idx_sf_fact_date ON FACT_SALES_SF(date_key);
