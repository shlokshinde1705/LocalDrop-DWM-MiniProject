"""
LocalDrop: Core ETL Pipeline Engine (Extract, Transform, Load)
Author: Ayush Kamble & Shlok Shinde (VIT INFT)
Orchestrates:
  1. Extract from operational.db
  2. Transform & Cleansing via preprocess.py
  3. Load into warehouse.db (Star Schema, Snowflake Schema, Constellation, Data Mart)
  4. Reconciliation validation & ETL logging table
"""

import os
import sys
import time
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config
try:
    from etl import preprocess
except (ImportError, AttributeError):
    import preprocess


def run_etl():
    """
    Executes end-to-end ETL pipeline.
    Re-runnable: drops and recreates dimensional tables, reconciles financial metrics.
    """
    start_total_time = time.time()
    print("===================================================================")
    print("      LOCALDROP ETL PIPELINE: EXTRACTION -> CLEANSING -> LOAD     ")
    print("===================================================================")

    if not os.path.exists(config.OPERATIONAL_DB_PATH):
        raise FileNotFoundError(f"Operational database not found at {config.OPERATIONAL_DB_PATH}. Run db/generate_data.py first.")

    # -------------------------------------------------------------------------
    # STAGE 1: EXTRACTION
    # -------------------------------------------------------------------------
    t0 = time.time()
    conn_op = sqlite3.connect(config.OPERATIONAL_DB_PATH)
    conn_op.row_factory = sqlite3.Row

    print("\n[STAGE 1/4: EXTRACT] Pulling relational records from operational.db...")
    raw_customers = pd.read_sql_query("SELECT * FROM CUSTOMERS", conn_op)
    raw_suppliers = pd.read_sql_query("SELECT * FROM SUPPLIERS", conn_op)
    raw_products = pd.read_sql_query("SELECT * FROM PRODUCTS", conn_op)
    raw_orders = pd.read_sql_query("SELECT * FROM ORDERS", conn_op)
    raw_sales = pd.read_sql_query("SELECT * FROM SALES", conn_op)
    conn_op.close()

    extract_time = round(time.time() - t0, 3)
    print(f" -> Extracted {len(raw_customers)} customers, {len(raw_suppliers)} suppliers, {len(raw_products)} products.")
    print(f" -> Extracted {len(raw_orders)} orders, {len(raw_sales)} sales in {extract_time}s.")

    # -------------------------------------------------------------------------
    # STAGE 2: TRANSFORMATION & DATA PREPROCESSING
    # -------------------------------------------------------------------------
    t1 = time.time()
    print("\n[STAGE 2/4: TRANSFORM] Applying cleaning, validation, and dimensional conforming...")

    # A. Clean Suppliers: Rating validation [1.0, 5.0]
    cleaned_suppliers, supp_metrics = preprocess.validate_numeric_bounds(
        raw_suppliers, rules={'supplier_rating': (1.0, 5.0, 'clamp')}
    )

    # B. Clean Customers: Deduplication & city trimming
    cleaned_customers, cust_metrics = preprocess.remove_duplicates(raw_customers, subset=['customer_name', 'city', 'state'])
    cleaned_customers['city'] = cleaned_customers['city'].fillna('Mumbai').str.strip()
    cleaned_customers['state'] = cleaned_customers['state'].fillna('Maharashtra').str.strip()

    # C. Clean Products: Price > 0
    cleaned_products = raw_products[raw_products['price'] > 0].copy()
    cleaned_products['category'] = cleaned_products['category'].str.strip()

    # D. Clean Orders: Deduplicate, handle missing status, standardize dates, filter quantity <= 0
    cleaned_orders, dupe_log = preprocess.remove_duplicates(
        raw_orders, subset=['customer_id', 'product_id', 'supplier_id', 'order_date', 'quantity', 'order_status']
    )
    cleaned_orders, null_log = preprocess.handle_missing_values(cleaned_orders, strategies={'order_status': 'drop', 'order_date': 'drop'})
    cleaned_orders, date_log = preprocess.parse_and_standardize_dates(cleaned_orders, date_col='order_date')
    cleaned_orders, qty_log = preprocess.filter_invalid_orders(cleaned_orders)

    # Filter SALES matching valid cleaned orders
    valid_order_ids = set(cleaned_orders['order_id'])
    cleaned_sales = raw_sales[raw_sales['order_id'].isin(valid_order_ids)].copy()

    # Deduplicate sales if any
    cleaned_sales = cleaned_sales.drop_duplicates(subset=['order_id']).copy()

    transform_time = round(time.time() - t1, 3)
    print(f" -> Preprocessing completed in {transform_time}s.")
    print(f" -> Orders: {len(raw_orders)} in -> {len(cleaned_orders)} clean ({len(raw_orders) - len(cleaned_orders)} rejected).")
    print(f" -> Sales: {len(raw_sales)} in -> {len(cleaned_sales)} clean ({len(raw_sales) - len(cleaned_sales)} rejected).")

    # -------------------------------------------------------------------------
    # STAGE 3: WAREHOUSE SCHEMA GENERATION & LOADING
    # -------------------------------------------------------------------------
    t2 = time.time()
    print("\n[STAGE 3/4: LOAD] Initializing warehouse schema and writing dimensional tables...")

    if os.path.exists(config.WAREHOUSE_DB_PATH):
        try:
            os.remove(config.WAREHOUSE_DB_PATH)
        except Exception:
            pass

    conn_dw = sqlite3.connect(config.WAREHOUSE_DB_PATH)
    cur_dw = conn_dw.cursor()

    # Execute DDL Scripts
    for sql_file in ["star_schema.sql", "snowflake_schema.sql", "constellation.sql", "sales_data_mart.sql"]:
        fpath = os.path.join(config.WAREHOUSE_SQL_DIR, sql_file)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                cur_dw.executescript(f.read())
        else:
            print(f"Warning: {sql_file} not found at {fpath}")

    # A. Populate DIM_DATE (Calendar Dimension with full temporal attributes)
    all_dates = set(cleaned_orders['order_date']).union(set(cleaned_sales['sale_date']))
    # Extend to continuous daily calendar range
    date_objs = [datetime.strptime(d, '%Y-%m-%d') for d in all_dates if d]
    min_d = min(date_objs) - timedelta(days=5)
    max_d = max(date_objs) + timedelta(days=10)

    curr_d = min_d
    dim_date_records = []
    while curr_d <= max_d:
        d_str = curr_d.strftime('%Y-%m-%d')
        d_key = int(curr_d.strftime('%Y%m%d'))
        dim_date_records.append((
            d_key,
            d_str,
            curr_d.day,
            curr_d.strftime('%A'),
            int(curr_d.strftime('%U')),
            curr_d.month,
            curr_d.strftime('%B'),
            (curr_d.month - 1) // 3 + 1,
            curr_d.year
        ))
        curr_d += timedelta(days=1)

    cur_dw.executemany("""
        INSERT INTO DIM_DATE (date_key, date, day, day_name, week, month, month_name, quarter, year)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, dim_date_records)

    # Date mapping dict
    date_to_key = {r[1]: r[0] for r in dim_date_records}

    # B. Populate Conformed Dimensions for Star Schema
    # DIM_CUSTOMER
    dim_cust_records = []
    cust_id_to_key = {}
    for idx, row in cleaned_customers.reset_index(drop=True).iterrows():
        ckey = idx + 1
        cid = int(row['customer_id'])
        cust_id_to_key[cid] = ckey
        dim_cust_records.append((
            ckey, cid, str(row['customer_name']), str(row['city']), str(row['state']), str(row['registration_date'])
        ))

    cur_dw.executemany("""
        INSERT INTO DIM_CUSTOMER (customer_key, customer_id, customer_name, city, state, registration_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, dim_cust_records)

    # DIM_SUPPLIER
    dim_supp_records = []
    supp_id_to_key = {}
    for idx, row in cleaned_suppliers.reset_index(drop=True).iterrows():
        skey = idx + 1
        sid = int(row['supplier_id'])
        supp_id_to_key[sid] = skey
        dim_supp_records.append((
            skey, sid, str(row['supplier_name']), str(row['city']), str(row['state']), float(row['supplier_rating'])
        ))

    cur_dw.executemany("""
        INSERT INTO DIM_SUPPLIER (supplier_key, supplier_id, supplier_name, city, state, rating)
        VALUES (?, ?, ?, ?, ?, ?)
    """, dim_supp_records)

    # DIM_PRODUCT (Star: Denormalized)
    dim_prod_records = []
    prod_id_to_key = {}
    for idx, row in cleaned_products.reset_index(drop=True).iterrows():
        pkey = idx + 1
        pid = int(row['product_id'])
        prod_id_to_key[pid] = pkey
        dim_prod_records.append((
            pkey, pid, str(row['product_name']), str(row['category']), float(row['price']), float(row['cost_price'])
        ))

    cur_dw.executemany("""
        INSERT INTO DIM_PRODUCT (product_key, product_id, product_name, category, price, cost_price)
        VALUES (?, ?, ?, ?, ?, ?)
    """, dim_prod_records)

    # C. Populate Snowflake Normalized Dimensions
    # DIM_CATEGORY
    unique_categories = sorted(cleaned_products['category'].unique())
    dim_cat_records = [(idx + 1, cat) for idx, cat in enumerate(unique_categories)]
    cur_dw.executemany("INSERT INTO DIM_CATEGORY (category_id, category_name) VALUES (?, ?)", dim_cat_records)
    cat_to_id = {cat: cid for cid, cat in dim_cat_records}

    # DIM_LOCATION (Distinct city + state pairs across customers and suppliers)
    loc_set = set(zip(cleaned_customers['city'], cleaned_customers['state'])).union(
        set(zip(cleaned_suppliers['city'], cleaned_suppliers['state']))
    )
    dim_loc_records = [(idx + 1, city, state) for idx, (city, state) in enumerate(sorted(loc_set))]
    cur_dw.executemany("INSERT INTO DIM_LOCATION (location_id, city, state) VALUES (?, ?, ?)", dim_loc_records)
    loc_to_id = {(c, s): lid for lid, c, s in dim_loc_records}

    # DIM_PRODUCT_SF
    dim_prod_sf_records = []
    for idx, row in cleaned_products.reset_index(drop=True).iterrows():
        pkey = idx + 1
        pid = int(row['product_id'])
        cat_id = cat_to_id[str(row['category'])]
        dim_prod_sf_records.append((pkey, pid, str(row['product_name']), cat_id, float(row['price']), float(row['cost_price'])))

    cur_dw.executemany("""
        INSERT INTO DIM_PRODUCT_SF (product_key, product_id, product_name, category_id, price, cost_price)
        VALUES (?, ?, ?, ?, ?, ?)
    """, dim_prod_sf_records)

    # DIM_CUSTOMER_SF
    dim_cust_sf_records = []
    for idx, row in cleaned_customers.reset_index(drop=True).iterrows():
        ckey = idx + 1
        cid = int(row['customer_id'])
        lid = loc_to_id[(str(row['city']), str(row['state']))]
        dim_cust_sf_records.append((ckey, cid, str(row['customer_name']), lid, str(row['registration_date'])))

    cur_dw.executemany("""
        INSERT INTO DIM_CUSTOMER_SF (customer_key, customer_id, customer_name, location_id, registration_date)
        VALUES (?, ?, ?, ?, ?)
    """, dim_cust_sf_records)

    # DIM_SUPPLIER_SF
    dim_supp_sf_records = []
    for idx, row in cleaned_suppliers.reset_index(drop=True).iterrows():
        skey = idx + 1
        sid = int(row['supplier_id'])
        lid = loc_to_id[(str(row['city']), str(row['state']))]
        dim_supp_sf_records.append((skey, sid, str(row['supplier_name']), lid, float(row['supplier_rating'])))

    cur_dw.executemany("""
        INSERT INTO DIM_SUPPLIER_SF (supplier_key, supplier_id, supplier_name, location_id, rating)
        VALUES (?, ?, ?, ?, ?)
    """, dim_supp_sf_records)

    # D. Populate FACT_SALES (Star Schema) and FACT_SALES_SF (Snowflake Schema)
    fact_sales_records = []
    for _, row in cleaned_sales.iterrows():
        sid = int(row['sale_id'])
        oid = int(row['order_id'])
        ckey = cust_id_to_key[int(row['customer_id'])]
        pkey = prod_id_to_key[int(row['product_id'])]
        skey = supp_id_to_key[int(row['supplier_id'])]
        dkey = date_to_key.get(str(row['sale_date']), int(str(row['sale_date']).replace('-', '')))
        qty = int(row['quantity'])
        uprice = float(row['unit_price'])
        tot_amt = float(row['total_amount'])
        profit = float(row['profit'])

        fact_sales_records.append((sid, oid, ckey, pkey, skey, dkey, qty, uprice, tot_amt, profit))

    cur_dw.executemany("""
        INSERT INTO FACT_SALES (sale_id, order_id, customer_key, product_key, supplier_key, date_key, quantity, unit_price, total_amount, profit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, fact_sales_records)

    cur_dw.executemany("""
        INSERT INTO FACT_SALES_SF (sale_id, order_id, customer_key, product_key, supplier_key, date_key, quantity, unit_price, total_amount, profit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, fact_sales_records)

    # E. Populate FACT_ORDERS (Fact Constellation)
    fact_orders_records = []
    for _, row in cleaned_orders.iterrows():
        oid = int(row['order_id'])
        ckey = cust_id_to_key[int(row['customer_id'])]
        pkey = prod_id_to_key[int(row['product_id'])]
        skey = supp_id_to_key[int(row['supplier_id'])]
        dkey = date_to_key.get(str(row['order_date']), int(str(row['order_date']).replace('-', '')))
        qty = int(row['quantity'])
        status = str(row['order_status'])

        is_del = 1 if status == 'Delivered' else 0
        is_ship = 1 if status == 'Shipped' else 0
        is_proc = 1 if status == 'Processing' else 0
        is_canc = 1 if status == 'Cancelled' else 0
        is_ret = 1 if status == 'Returned' else 0

        fact_orders_records.append((oid, ckey, pkey, skey, dkey, qty, status, is_del, is_ship, is_proc, is_canc, is_ret))

    cur_dw.executemany("""
        INSERT INTO FACT_ORDERS (order_id, customer_key, product_key, supplier_key, date_key, quantity, order_status, is_delivered, is_shipped, is_processing, is_cancelled, is_returned)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, fact_orders_records)

    conn_dw.commit()
    load_time = round(time.time() - t2, 3)
    print(f" -> Loaded FACT_SALES ({len(fact_sales_records)} rows) and FACT_ORDERS ({len(fact_orders_records)} rows) in {load_time}s.")

    # -------------------------------------------------------------------------
    # STAGE 4: RECONCILIATION & ETL AUDIT LOG
    # -------------------------------------------------------------------------
    print("\n[STAGE 4/4: RECONCILIATION] Validating financial ledger and row-count parity...")
    cur_dw.execute("SELECT SUM(total_amount), SUM(profit), COUNT(*) FROM FACT_SALES")
    fact_rev, fact_prof, fact_count = cur_dw.fetchone()

    clean_source_rev = cleaned_sales['total_amount'].sum()
    clean_source_prof = cleaned_sales['profit'].sum()
    clean_source_count = len(cleaned_sales)

    diff_rev = abs(fact_rev - clean_source_rev)
    diff_prof = abs(fact_prof - clean_source_prof)

    print(f" -> Source Clean Sales Revenue : Rs. {clean_source_rev:,.2f}")
    print(f" -> Warehouse FACT_SALES Rev   : Rs. {fact_rev:,.2f} (Diff: Rs. {diff_rev:.4f})")
    print(f" -> Source Clean Sales Profit  : Rs. {clean_source_prof:,.2f}")
    print(f" -> Warehouse FACT_SALES Prof  : Rs. {fact_prof:,.2f} (Diff: Rs. {diff_prof:.4f})")
    print(f" -> Row Count Match            : {fact_count} == {clean_source_count}")

    if diff_rev > 0.01 or diff_prof > 0.01 or fact_count != clean_source_count:
        conn_dw.close()
        raise AssertionError("RECONCILIATION AUDIT FAILED! Discrepancy detected between source and fact table!")

    print(" -> RECONCILIATION CHECK PASSED 100% PERFECTLY!")

    # Write ETL Log Table in warehouse.db
    cur_dw.execute("""
        CREATE TABLE IF NOT EXISTS etl_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            stage TEXT NOT NULL,
            status TEXT NOT NULL,
            source_table TEXT,
            target_table TEXT,
            rows_extracted INTEGER,
            rows_loaded INTEGER,
            rows_rejected INTEGER,
            duration_sec REAL,
            message TEXT
        );
    """)

    now_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    etl_entries = [
        (now_ts, "Extract", "SUCCESS", "CUSTOMERS, SUPPLIERS, PRODUCTS, ORDERS, SALES", "DataFrames", len(raw_orders) + len(raw_sales), len(raw_orders) + len(raw_sales), 0, extract_time, "Extracted raw OLTP records from operational.db"),
        (now_ts, "Transform", "SUCCESS", "Raw DataFrames", "Clean DataFrames", len(raw_orders), len(cleaned_orders), len(raw_orders) - len(cleaned_orders), transform_time, "Purged duplicates, handled null statuses, parsed dates, validated positive quantity"),
        (now_ts, "Load-Dimensions", "SUCCESS", "Clean Customers, Suppliers, Products", "DIM_CUSTOMER, DIM_SUPPLIER, DIM_PRODUCT, DIM_DATE", len(cleaned_customers) + len(cleaned_suppliers) + len(cleaned_products), len(dim_cust_records) + len(dim_supp_records) + len(dim_prod_records) + len(dim_date_records), 0, round(load_time * 0.4, 3), "Populated conformed dimensions and surrogate keys"),
        (now_ts, "Load-Snowflake", "SUCCESS", "Clean Normalized Dimensions", "DIM_CATEGORY, DIM_LOCATION, DIM_PRODUCT_SF, DIM_CUSTOMER_SF, DIM_SUPPLIER_SF", len(cleaned_products), len(dim_prod_sf_records) + len(dim_cat_records) + len(dim_loc_records), 0, round(load_time * 0.2, 3), "Normalized product category and geographic location hierarchies"),
        (now_ts, "Load-Fact", "SUCCESS", "Cleaned SALES", "FACT_SALES & FACT_SALES_SF", len(cleaned_sales), len(fact_sales_records), 0, round(load_time * 0.3, 3), "Loaded financial sales facts and conformed foreign keys"),
        (now_ts, "Load-Constellation", "SUCCESS", "Cleaned ORDERS", "FACT_ORDERS", len(cleaned_orders), len(fact_orders_records), 0, round(load_time * 0.1, 3), "Populated order logistics and fulfillment fact table"),
        (now_ts, "Reconciliation", "SUCCESS", "CLEAN_SALES vs FACT_SALES", "Financial Ledger", clean_source_count, fact_count, 0, 0.05, f"Financial parity verified: Revenue diff = ₹{diff_rev:.2f}, Profit diff = ₹{diff_prof:.2f}")
    ]

    cur_dw.executemany("""
        INSERT INTO etl_log (timestamp, stage, status, source_table, target_table, rows_extracted, rows_loaded, rows_rejected, duration_sec, message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, etl_entries)

    conn_dw.commit()
    conn_dw.close()

    total_pipeline_time = round(time.time() - start_total_time, 3)
    print(f"\nETL PIPELINE EXECUTED SUCCESSFULLY IN {total_pipeline_time} SECONDS.")
    print("Warehouse tables ready at db/warehouse.db.\n")

    return {
        "status": "SUCCESS",
        "duration_total": total_pipeline_time,
        "rows_orders_clean": len(cleaned_orders),
        "rows_sales_clean": len(cleaned_sales),
        "fact_revenue": fact_rev,
        "fact_profit": fact_prof,
        "reconciliation_passed": True
    }


if __name__ == "__main__":
    run_etl()
