"""
LocalDrop: OLAP Operations Engine
Implements core multidimensional OLAP operations over localdrop_warehouse.db:
  1. Roll-up (Day -> Month -> Quarter -> Year)
  2. Drill-down (Year -> Quarter -> Month, Category -> Product)
  3. Slice (Fix single dimension attribute)
  4. Dice (Sub-cube selection across 2+ dimensions)
  5. Pivot (Category x Quarter matrix)
  6. Simulated CUBE and ROLLUP (using UNION ALL GROUP BY combinations for SQLite)
"""

import os
import sys
import sqlite3
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config


def get_dw_conn():
    conn = sqlite3.connect(config.WAREHOUSE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def olap_rollup(level='quarter', year_filter=None):
    """
    Roll-up: Aggregates detailed sales up the temporal hierarchy.
    Levels: 'day', 'month', 'quarter', 'year'
    """
    conn = get_dw_conn()
    level = level.lower().strip()
    where_sql = ""
    params = []

    if year_filter:
        try:
            where_sql = "WHERE d.year = ?"
            params.append(int(year_filter))
        except ValueError:
            pass

    if level == 'year':
        sql = f"""
            SELECT d.year AS time_dimension,
                   COUNT(f.sale_id) AS transaction_count,
                   SUM(f.quantity) AS total_units_sold,
                   ROUND(SUM(f.total_amount), 2) AS total_revenue,
                   ROUND(SUM(f.profit), 2) AS total_profit
            FROM FACT_SALES f
            JOIN DIM_DATE d ON f.date_key = d.date_key
            {where_sql}
            GROUP BY d.year
            ORDER BY d.year ASC
        """
    elif level == 'month':
        sql = f"""
            SELECT d.year || ' ' || d.month_name AS time_dimension,
                   d.year, d.month,
                   COUNT(f.sale_id) AS transaction_count,
                   SUM(f.quantity) AS total_units_sold,
                   ROUND(SUM(f.total_amount), 2) AS total_revenue,
                   ROUND(SUM(f.profit), 2) AS total_profit
            FROM FACT_SALES f
            JOIN DIM_DATE d ON f.date_key = d.date_key
            {where_sql}
            GROUP BY d.year, d.month, d.month_name
            ORDER BY d.year ASC, d.month ASC
        """
    elif level == 'day':
        sql = f"""
            SELECT d.date AS time_dimension,
                   COUNT(f.sale_id) AS transaction_count,
                   SUM(f.quantity) AS total_units_sold,
                   ROUND(SUM(f.total_amount), 2) AS total_revenue,
                   ROUND(SUM(f.profit), 2) AS total_profit
            FROM FACT_SALES f
            JOIN DIM_DATE d ON f.date_key = d.date_key
            {where_sql}
            GROUP BY d.date
            ORDER BY d.date DESC
            LIMIT 30
        """
    else:  # default 'quarter'
        sql = f"""
            SELECT d.year || ' Q' || d.quarter AS time_dimension,
                   d.year, d.quarter,
                   COUNT(f.sale_id) AS transaction_count,
                   SUM(f.quantity) AS total_units_sold,
                   ROUND(SUM(f.total_amount), 2) AS total_revenue,
                   ROUND(SUM(f.profit), 2) AS total_profit
            FROM FACT_SALES f
            JOIN DIM_DATE d ON f.date_key = d.date_key
            {where_sql}
            GROUP BY d.year, d.quarter
            ORDER BY d.year ASC, d.quarter ASC
        """

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return {
        "operation": "Roll-up",
        "current_level": level,
        "concept": "Climbing up the concept hierarchy: Day -> Month -> Quarter -> Year. Summarizes data by collapsing granular dimensions.",
        "sql": sql.strip(),
        "data": [dict(r) for r in rows]
    }


def olap_drilldown(mode='category_to_product', target_val='Electronics'):
    """
    Drill-down: Navigates from higher-level summary down to detailed lower-level data.
    Modes:
      - 'category_to_product': Drills down from Category into individual Products
      - 'year_to_months': Drills down from Year into 12 Months
    """
    conn = get_dw_conn()

    if mode == 'year_to_months':
        year = int(target_val) if str(target_val).isdigit() else 2025
        sql = """
            SELECT d.month, d.month_name AS period_name,
                   COUNT(f.sale_id) AS transaction_count,
                   SUM(f.quantity) AS total_units_sold,
                   ROUND(SUM(f.total_amount), 2) AS revenue,
                   ROUND(SUM(f.profit), 2) AS profit
            FROM FACT_SALES f
            JOIN DIM_DATE d ON f.date_key = d.date_key
            WHERE d.year = ?
            GROUP BY d.month, d.month_name
            ORDER BY d.month ASC
        """
        rows = conn.execute(sql, [year]).fetchall()
        concept_desc = f"Drilled down from Calendar Year '{year}' into its 12 constituent Monthly sub-periods."
    else:
        # Default: Category to product
        category = str(target_val).strip() if target_val else 'Electronics'
        sql = """
            SELECT p.product_id, p.product_name, p.category,
                   p.price AS unit_selling_price,
                   COUNT(f.sale_id) AS total_orders,
                   SUM(f.quantity) AS total_units_sold,
                   ROUND(SUM(f.total_amount), 2) AS total_revenue,
                   ROUND(SUM(f.profit), 2) AS total_profit
            FROM FACT_SALES f
            JOIN DIM_PRODUCT p ON f.product_key = p.product_key
            WHERE p.category = ?
            GROUP BY p.product_id, p.product_name, p.category, p.price
            ORDER BY total_revenue DESC
        """
        rows = conn.execute(sql, [category]).fetchall()
        concept_desc = f"Drilled down from Parent Category '{category}' into granular product SKUs and their individual margins."

    conn.close()

    return {
        "operation": "Drill-down",
        "mode": mode,
        "target_value": target_val,
        "concept": concept_desc,
        "sql": sql.strip(),
        "data": [dict(r) for r in rows]
    }


def olap_slice(slice_dimension='category', slice_value='Electronics'):
    """
    Slice: Performs a selection on one dimension of the given cube, resulting in a sub-cube.
    Example: Fixing Category = 'Electronics' and analyzing across Years and States.
    """
    conn = get_dw_conn()
    dim = slice_dimension.lower().strip()

    if dim == 'year':
        year = int(slice_value) if str(slice_value).isdigit() else 2025
        sql = """
            SELECT p.category AS dimension_attribute,
                   COUNT(f.sale_id) AS transaction_count,
                   SUM(f.quantity) AS units_sold,
                   ROUND(SUM(f.total_amount), 2) AS revenue,
                   ROUND(SUM(f.profit), 2) AS profit
            FROM FACT_SALES f
            JOIN DIM_DATE d ON f.date_key = d.date_key
            JOIN DIM_PRODUCT p ON f.product_key = p.product_key
            WHERE d.year = ?
            GROUP BY p.category
            ORDER BY revenue DESC
        """
        rows = conn.execute(sql, [year]).fetchall()
        slice_desc = f"Slice on Year = {year}: Sliced 2D cross-section showing Category performance for that specific year."
    elif dim == 'state':
        state = str(slice_value).strip() if slice_value else 'Maharashtra'
        sql = """
            SELECT p.category AS dimension_attribute,
                   COUNT(f.sale_id) AS transaction_count,
                   SUM(f.quantity) AS units_sold,
                   ROUND(SUM(f.total_amount), 2) AS revenue,
                   ROUND(SUM(f.profit), 2) AS profit
            FROM FACT_SALES f
            JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
            JOIN DIM_PRODUCT p ON f.product_key = p.product_key
            WHERE c.state = ?
            GROUP BY p.category
            ORDER BY revenue DESC
        """
        rows = conn.execute(sql, [state]).fetchall()
        slice_desc = f"Slice on State = '{state}': Sliced 2D cross-section analyzing category revenues within that state."
    else:  # default 'category'
        cat = str(slice_value).strip() if slice_value else 'Electronics'
        sql = """
            SELECT d.year AS dimension_attribute,
                   COUNT(f.sale_id) AS transaction_count,
                   SUM(f.quantity) AS units_sold,
                   ROUND(SUM(f.total_amount), 2) AS revenue,
                   ROUND(SUM(f.profit), 2) AS profit
            FROM FACT_SALES f
            JOIN DIM_PRODUCT p ON f.product_key = p.product_key
            JOIN DIM_DATE d ON f.date_key = d.date_key
            WHERE p.category = ?
            GROUP BY d.year
            ORDER BY d.year ASC
        """
        rows = conn.execute(sql, [cat]).fetchall()
        slice_desc = f"Slice on Category = '{cat}': Sliced 2D cross-section evaluating category revenue across calendar years."

    conn.close()

    return {
        "operation": "Slice",
        "slice_dimension": dim,
        "slice_value": slice_value,
        "concept": slice_desc,
        "sql": sql.strip(),
        "data": [dict(r) for r in rows]
    }


def olap_dice(categories=None, states=None, years=None):
    """
    Dice: Defines a sub-cube by performing a selection on two or more dimensions.
    Example: Category IN ('Electronics', 'Mobile Accessories')
             AND State IN ('Maharashtra', 'Karnataka')
             AND Year IN (2025, 2026)
    """
    if not categories:
        categories = ['Electronics', 'Mobile Accessories', 'Home & Office']
    if not states:
        states = ['Maharashtra', 'Karnataka', 'Telangana']
    if not years:
        years = [2025, 2026]

    conn = get_dw_conn()

    cat_placeholders = ",".join(["?"] * len(categories))
    state_placeholders = ",".join(["?"] * len(states))
    year_placeholders = ",".join(["?"] * len(years))

    sql = f"""
        SELECT d.year, c.state, p.category,
               COUNT(f.sale_id) AS order_count,
               SUM(f.quantity) AS units_sold,
               ROUND(SUM(f.total_amount), 2) AS revenue,
               ROUND(SUM(f.profit), 2) AS profit
        FROM FACT_SALES f
        JOIN DIM_DATE d ON f.date_key = d.date_key
        JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        WHERE p.category IN ({cat_placeholders})
          AND c.state IN ({state_placeholders})
          AND d.year IN ({year_placeholders})
        GROUP BY d.year, c.state, p.category
        ORDER BY d.year ASC, c.state ASC, revenue DESC
    """

    params = list(categories) + list(states) + [int(y) for y in years]
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return {
        "operation": "Dice",
        "selected_categories": categories,
        "selected_states": states,
        "selected_years": years,
        "concept": "Dice extracts a smaller multi-dimensional sub-cube constrained by bounding intervals across 3 dimensions: Category, State, and Year.",
        "sql": sql.strip(),
        "data": [dict(r) for r in rows]
    }


def olap_pivot():
    """
    Pivot: Rotates the data axes in view in order to provide an alternative data presentation.
    Category x Quarter Revenue Matrix (Heatmap representation).
    """
    conn = get_dw_conn()
    sql = """
        SELECT
            p.category,
            ROUND(SUM(CASE WHEN d.quarter = 1 THEN f.total_amount ELSE 0 END), 2) AS q1_revenue,
            ROUND(SUM(CASE WHEN d.quarter = 2 THEN f.total_amount ELSE 0 END), 2) AS q2_revenue,
            ROUND(SUM(CASE WHEN d.quarter = 3 THEN f.total_amount ELSE 0 END), 2) AS q3_revenue,
            ROUND(SUM(CASE WHEN d.quarter = 4 THEN f.total_amount ELSE 0 END), 2) AS q4_revenue,
            ROUND(SUM(f.total_amount), 2) AS total_revenue,
            ROUND(SUM(f.profit), 2) AS total_profit
        FROM FACT_SALES f
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        JOIN DIM_DATE d ON f.date_key = d.date_key
        GROUP BY p.category
        ORDER BY total_revenue DESC
    """
    rows = conn.execute(sql).fetchall()
    conn.close()

    return {
        "operation": "Pivot",
        "concept": "Pivoting swaps dimensional axes: Rows = Merchandise Category, Columns = Quarters (Q1-Q4), producing an executive cross-tabular revenue matrix.",
        "sql": sql.strip(),
        "data": [dict(r) for r in rows]
    }


def olap_cube_simulation():
    """
    CUBE & ROLLUP Simulation:
    Standard ANSI SQL provides GROUP BY CUBE(Category, Year).
    Because SQLite does not natively support the CUBE keyword, we simulate it
    using UNION ALL combinations of GROUP BY across all powerset combinations of (Category, Year):
      1. Group by (Category, Year)
      2. Group by (Category, ALL Years)
      3. Group by (ALL Categories, Year)
      4. Group by (ALL Categories, ALL Years) -> Grand Total!
    """
    conn = get_dw_conn()
    sql = """
        SELECT category_dim, year_dim, total_revenue, total_profit, aggregation_level
        FROM (
            -- Level 1: Category x Year
            SELECT p.category AS category_dim,
                   CAST(d.year AS TEXT) AS year_dim,
                   ROUND(SUM(f.total_amount), 2) AS total_revenue,
                   ROUND(SUM(f.profit), 2) AS total_profit,
                   'Cell (Category, Year)' AS aggregation_level
            FROM FACT_SALES f
            JOIN DIM_PRODUCT p ON f.product_key = p.product_key
            JOIN DIM_DATE d ON f.date_key = d.date_key
            GROUP BY p.category, d.year

            UNION ALL

            -- Level 2: Sub-total by Category across ALL Years
            SELECT p.category AS category_dim,
                   'ALL YEARS' AS year_dim,
                   ROUND(SUM(f.total_amount), 2) AS total_revenue,
                   ROUND(SUM(f.profit), 2) AS total_profit,
                   'Sub-total by Category' AS aggregation_level
            FROM FACT_SALES f
            JOIN DIM_PRODUCT p ON f.product_key = p.product_key
            GROUP BY p.category

            UNION ALL

            -- Level 3: Sub-total by Year across ALL Categories
            SELECT 'ALL CATEGORIES' AS category_dim,
                   CAST(d.year AS TEXT) AS year_dim,
                   ROUND(SUM(f.total_amount), 2) AS total_revenue,
                   ROUND(SUM(f.profit), 2) AS total_profit,
                   'Sub-total by Year' AS aggregation_level
            FROM FACT_SALES f
            JOIN DIM_DATE d ON f.date_key = d.date_key
            GROUP BY d.year

            UNION ALL

            -- Level 4: Grand Total
            SELECT 'GRAND TOTAL' AS category_dim,
                   'ALL TIME' AS year_dim,
                   ROUND(SUM(f.total_amount), 2) AS total_revenue,
                   ROUND(SUM(f.profit), 2) AS total_profit,
                   'Grand Total (0D)' AS aggregation_level
            FROM FACT_SALES f
        )
        ORDER BY
            CASE WHEN category_dim = 'GRAND TOTAL' THEN 4
                 WHEN category_dim = 'ALL CATEGORIES' THEN 3
                 WHEN year_dim = 'ALL YEARS' THEN 2
                 ELSE 1 END,
            category_dim, year_dim;
    """
    rows = conn.execute(sql).fetchall()
    conn.close()

    return {
        "operation": "CUBE Simulation",
        "concept": "Simulates multi-dimensional CUBE(Category, Year) via UNION ALL group combinations. Generates all 2^N = 4 aggregations including cells, sub-totals, and grand totals.",
        "sql": sql.strip(),
        "data": [dict(r) for r in rows]
    }


if __name__ == "__main__":
    p = olap_pivot()
    print("OLAP Pivot generated:")
    print(f"Categories pivoted: {len(p['data'])}")
    cb = olap_cube_simulation()
    print(f"CUBE simulation rows: {len(cb['data'])}")
