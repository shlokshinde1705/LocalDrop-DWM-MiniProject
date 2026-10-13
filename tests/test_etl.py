"""
Test Suite: ETL Reconciliation and Dimensional Schema Parity
Verifies table counts, financial parity, and Star vs Snowflake identical query totals.
"""

import sqlite3
import pytest
import config


def test_operational_tables_exist_and_populated():
    conn = sqlite3.connect(config.OPERATIONAL_DB_PATH)
    tables = ['CUSTOMERS', 'SUPPLIERS', 'PRODUCTS', 'ORDERS', 'SALES']
    for tbl in tables:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        assert cnt > 0, f"Table {tbl} must not be empty"
    conn.close()


def test_warehouse_tables_exist_and_populated():
    conn = sqlite3.connect(config.WAREHOUSE_DB_PATH)
    tables = [
        'FACT_SALES', 'FACT_ORDERS', 'DIM_CUSTOMER', 'DIM_SUPPLIER', 'DIM_PRODUCT',
        'DIM_DATE', 'DIM_CATEGORY', 'DIM_LOCATION', 'DIM_PRODUCT_SF', 'FACT_SALES_SF'
    ]
    for tbl in tables:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        assert cnt > 0, f"Warehouse table {tbl} must not be empty"
    conn.close()


def test_etl_financial_reconciliation():
    """Verify that FACT_SALES financial ledger matches source sales ledger."""
    conn_dw = sqlite3.connect(config.WAREHOUSE_DB_PATH)
    res = conn_dw.execute("SELECT SUM(total_amount), SUM(profit), COUNT(*) FROM FACT_SALES").fetchone()
    tot_rev, tot_prof, cnt = res

    assert tot_rev > 1000000.0, "Total revenue should reflect realistic 24-month turnover (> Rs. 10 Lakhs)"
    assert tot_prof > 500000.0, "Total profit should reflect realistic margins (> Rs. 5 Lakhs)"
    assert cnt > 4000, "Should have fulfilled thousands of settled transactions"
    conn_dw.close()


def test_star_vs_snowflake_query_parity():
    """Verify that Star Schema and Snowflake Schema return identical aggregated results."""
    conn = sqlite3.connect(config.WAREHOUSE_DB_PATH)
    star_res = conn.execute("""
        SELECT p.category, ROUND(SUM(f.total_amount), 2) AS rev
        FROM FACT_SALES f
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        GROUP BY p.category ORDER BY p.category
    """).fetchall()

    sf_res = conn.execute("""
        SELECT c.category_name, ROUND(SUM(f.total_amount), 2) AS rev
        FROM FACT_SALES_SF f
        JOIN DIM_PRODUCT_SF p ON f.product_key = p.product_key
        JOIN DIM_CATEGORY c ON p.category_id = c.category_id
        GROUP BY c.category_name ORDER BY c.category_name
    """).fetchall()

    conn.close()

    assert len(star_res) == len(sf_res)
    assert star_res == sf_res, "Star and Snowflake schema aggregations must return 100% identical numbers!"
