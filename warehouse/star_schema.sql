-- ============================================================================
-- LocalDrop Data Warehouse: Star Schema Definition
-- Architecture: Ralph Kimball Dimensional Modeling Methodology
-- Conformed Dimensions surrounding a centralized Sales Fact Table
-- ============================================================================

-- 1. Dimension Table: DIM_DATE
-- Granularity: One row per unique calendar day
CREATE TABLE IF NOT EXISTS DIM_DATE (
    date_key INTEGER PRIMARY KEY,        -- Surrogate key (YYYYMMDD)
    date TEXT NOT NULL UNIQUE,          -- ISO Date (YYYY-MM-DD)
    day INTEGER NOT NULL,               -- Day of month (1-31)
    day_name TEXT NOT NULL,             -- Monday, Tuesday, ...
    week INTEGER NOT NULL,              -- Week of year (1-53)
    month INTEGER NOT NULL,             -- Month number (1-12)
    month_name TEXT NOT NULL,           -- January, February, ...
    quarter INTEGER NOT NULL,           -- Quarter (1-4)
    year INTEGER NOT NULL               -- Calendar year (e.g. 2024, 2025, 2026)
);

-- 2. Dimension Table: DIM_CUSTOMER
-- Granularity: One row per customer profile (SCD Type 1)
CREATE TABLE IF NOT EXISTS DIM_CUSTOMER (
    customer_key INTEGER PRIMARY KEY,   -- Surrogate Key
    customer_id INTEGER NOT NULL UNIQUE,-- Natural / Business Key
    customer_name TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    registration_date TEXT NOT NULL
);

-- 3. Dimension Table: DIM_SUPPLIER
-- Granularity: One row per verified dropshipping supplier
CREATE TABLE IF NOT EXISTS DIM_SUPPLIER (
    supplier_key INTEGER PRIMARY KEY,   -- Surrogate Key
    supplier_id INTEGER NOT NULL UNIQUE,-- Natural / Business Key
    supplier_name TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    rating REAL NOT NULL
);

-- 4. Dimension Table: DIM_PRODUCT (Denormalized)
-- Granularity: One row per retail product SKU
CREATE TABLE IF NOT EXISTS DIM_PRODUCT (
    product_key INTEGER PRIMARY KEY,    -- Surrogate Key
    product_id INTEGER NOT NULL UNIQUE, -- Natural / Business Key
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,             -- Denormalized category attribute
    price REAL NOT NULL,
    cost_price REAL NOT NULL
);

-- 5. Fact Table: FACT_SALES
-- Granularity: One row per settled dropshipping line item sale
CREATE TABLE IF NOT EXISTS FACT_SALES (
    sale_id INTEGER PRIMARY KEY,        -- Business Key
    order_id INTEGER NOT NULL,
    customer_key INTEGER NOT NULL,      -- FK to DIM_CUSTOMER
    product_key INTEGER NOT NULL,       -- FK to DIM_PRODUCT
    supplier_key INTEGER NOT NULL,      -- FK to DIM_SUPPLIER
    date_key INTEGER NOT NULL,          -- FK to DIM_DATE
    quantity INTEGER NOT NULL,          -- Additive Measure
    unit_price REAL NOT NULL,           -- Semi-additive Measure
    total_amount REAL NOT NULL,         -- Additive Measure (quantity * unit_price)
    profit REAL NOT NULL,               -- Additive Measure (total_amount - wholesale cost)
    FOREIGN KEY (customer_key) REFERENCES DIM_CUSTOMER(customer_key),
    FOREIGN KEY (product_key) REFERENCES DIM_PRODUCT(product_key),
    FOREIGN KEY (supplier_key) REFERENCES DIM_SUPPLIER(supplier_key),
    FOREIGN KEY (date_key) REFERENCES DIM_DATE(date_key)
);

-- Performance Indexes on Star Schema Joins
CREATE INDEX IF NOT EXISTS idx_star_fact_customer ON FACT_SALES(customer_key);
CREATE INDEX IF NOT EXISTS idx_star_fact_product ON FACT_SALES(product_key);
CREATE INDEX IF NOT EXISTS idx_star_fact_supplier ON FACT_SALES(supplier_key);
CREATE INDEX IF NOT EXISTS idx_star_fact_date ON FACT_SALES(date_key);
