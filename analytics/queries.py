"""
LocalDrop: Analytical SQL Queries Engine
Implements 15 analytical queries over localdrop_warehouse.db.
Supports parameterized dashboard filters (year, category, supplier_id, state)
without string concatenation of user inputs.
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


def build_filter_clauses(filters=None):
    """
    Builds parameterized SQL WHERE clause based on optional dashboard filters:
    filters dict: {'year': int/str, 'category': str, 'supplier_id': int/str, 'state': str}
    Returns: (where_clause_str, params_list)
    """
    if not filters:
        return "", []

    clauses = []
    params = []

    if filters.get('year'):
        try:
            clauses.append("d.year = ?")
            params.append(int(filters['year']))
        except ValueError:
            pass

    if filters.get('category'):
        clauses.append("p.category = ?")
        params.append(str(filters['category']).strip())

    if filters.get('supplier_id'):
        try:
            clauses.append("s.supplier_id = ?")
            params.append(int(filters['supplier_id']))
        except ValueError:
            pass

    if filters.get('state'):
        clauses.append("c.state = ?")
        params.append(str(filters['state']).strip())

    if clauses:
        return "WHERE " + " AND ".join(clauses), params
    return "", []


def get_all_analytical_queries(filters=None):
    """
    Executes all 15 analytical SQL queries with optional filters.
    Returns: dict mapping query_key -> { 'title': str, 'purpose': str, 'sql': str, 'data': list[dict] }
    """
    conn = get_dw_conn()
    filter_clause, filter_params = build_filter_clauses(filters)

    results = {}

    # Query 1: Total Revenue
    q1_sql = f"""
        SELECT ROUND(SUM(f.total_amount), 2) AS total_revenue
        FROM FACT_SALES f
        JOIN DIM_DATE d ON f.date_key = d.date_key
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        JOIN DIM_SUPPLIER s ON f.supplier_key = s.supplier_key
        JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
        {filter_clause}
    """
    row1 = conn.execute(q1_sql, filter_params).fetchone()
    rev = row1['total_revenue'] if row1 and row1['total_revenue'] else 0.0
    results['total_revenue'] = {
        "id": 1,
        "title": "Total Revenue",
        "purpose": "Computes aggregate gross marketplace sales turnover across settled transactions.",
        "sql": q1_sql.strip(),
        "value": rev,
        "formatted": f"₹{rev:,.2f}"
    }

    # Query 2: Total Orders
    q2_sql = f"""
        SELECT COUNT(DISTINCT f.order_id) AS total_orders
        FROM FACT_SALES f
        JOIN DIM_DATE d ON f.date_key = d.date_key
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        JOIN DIM_SUPPLIER s ON f.supplier_key = s.supplier_key
        JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
        {filter_clause}
    """
    row2 = conn.execute(q2_sql, filter_params).fetchone()
    orders_cnt = row2['total_orders'] if row2 else 0
    results['total_orders'] = {
        "id": 2,
        "title": "Total Orders",
        "purpose": "Measures total settled consumer purchase transactions fulfilling dropshipping demand.",
        "sql": q2_sql.strip(),
        "value": orders_cnt,
        "formatted": f"{orders_cnt:,}"
    }

    # Query 3: Total Profit
    q3_sql = f"""
        SELECT ROUND(SUM(f.profit), 2) AS total_profit,
               ROUND((SUM(f.profit) / NULLIF(SUM(f.total_amount), 0)) * 100, 2) AS overall_profit_margin_pct
        FROM FACT_SALES f
        JOIN DIM_DATE d ON f.date_key = d.date_key
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        JOIN DIM_SUPPLIER s ON f.supplier_key = s.supplier_key
        JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
        {filter_clause}
    """
    row3 = conn.execute(q3_sql, filter_params).fetchone()
    prof = row3['total_profit'] if row3 and row3['total_profit'] else 0.0
    margin = row3['overall_profit_margin_pct'] if row3 and row3['overall_profit_margin_pct'] else 0.0
    results['total_profit'] = {
        "id": 3,
        "title": "Total Net Profit",
        "purpose": "Evaluates net marketplace profitability after deducting supplier wholesale inventory costs.",
        "sql": q3_sql.strip(),
        "value": prof,
        "margin_pct": margin,
        "formatted": f"₹{prof:,.2f}"
    }

    # Query 4: Monthly Sales
    q4_sql = f"""
        SELECT d.year, d.month, d.month_name,
               ROUND(SUM(f.total_amount), 2) AS monthly_revenue,
               ROUND(SUM(f.profit), 2) AS monthly_profit,
               COUNT(f.sale_id) AS transactions_count
        FROM FACT_SALES f
        JOIN DIM_DATE d ON f.date_key = d.date_key
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        JOIN DIM_SUPPLIER s ON f.supplier_key = s.supplier_key
        JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
        {filter_clause}
        GROUP BY d.year, d.month, d.month_name
        ORDER BY d.year ASC, d.month ASC
    """
    rows4 = conn.execute(q4_sql, filter_params).fetchall()
    results['monthly_sales'] = {
        "id": 4,
        "title": "Monthly Sales Trend",
        "purpose": "Analyzes longitudinal revenue and profit trajectory over sequential 24-month horizon.",
        "sql": q4_sql.strip(),
        "data": [dict(r) for r in rows4]
    }

    # Query 5: Top 5 Products by Revenue
    q5_sql = f"""
        SELECT p.product_name, p.category,
               SUM(f.quantity) AS total_units_sold,
               ROUND(SUM(f.total_amount), 2) AS revenue,
               ROUND(SUM(f.profit), 2) AS profit,
               ROUND((SUM(f.profit) / SUM(f.total_amount)) * 100, 1) AS margin_pct
        FROM FACT_SALES f
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        JOIN DIM_DATE d ON f.date_key = d.date_key
        JOIN DIM_SUPPLIER s ON f.supplier_key = s.supplier_key
        JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
        {filter_clause}
        GROUP BY p.product_name, p.category
        ORDER BY revenue DESC
        LIMIT 5
    """
    rows5 = conn.execute(q5_sql, filter_params).fetchall()
    results['top_5_products'] = {
        "id": 5,
        "title": "Top 5 Products by Revenue",
        "purpose": "Identifies primary catalog revenue drivers to prioritize inventory and dropshipping agreements.",
        "sql": q5_sql.strip(),
        "data": [dict(r) for r in rows5]
    }

    # Query 6: Category-wise Sales
    q6_sql = f"""
        SELECT p.category,
               COUNT(f.sale_id) AS total_sales_count,
               SUM(f.quantity) AS units_sold,
               ROUND(SUM(f.total_amount), 2) AS category_revenue,
               ROUND(SUM(f.profit), 2) AS category_profit,
               ROUND((SUM(f.profit) / SUM(f.total_amount)) * 100, 2) AS margin_pct
        FROM FACT_SALES f
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        JOIN DIM_DATE d ON f.date_key = d.date_key
        JOIN DIM_SUPPLIER s ON f.supplier_key = s.supplier_key
        JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
        {filter_clause}
        GROUP BY p.category
        ORDER BY category_revenue DESC
    """
    rows6 = conn.execute(q6_sql, filter_params).fetchall()
    results['category_sales'] = {
        "id": 6,
        "title": "Category-wise Sales Distribution",
        "purpose": "Measures merchandise category performance to optimize catalog breadth and marketing.",
        "sql": q6_sql.strip(),
        "data": [dict(r) for r in rows6]
    }

    # Query 7: Supplier-wise Revenue
    q7_sql = f"""
        SELECT s.supplier_name, s.city, s.state, s.rating,
               COUNT(f.sale_id) AS orders_fulfilled,
               ROUND(SUM(f.total_amount), 2) AS supplier_revenue,
               ROUND(SUM(f.profit), 2) AS supplier_profit
        FROM FACT_SALES f
        JOIN DIM_SUPPLIER s ON f.supplier_key = s.supplier_key
        JOIN DIM_DATE d ON f.date_key = d.date_key
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
        {filter_clause}
        GROUP BY s.supplier_name, s.city, s.state, s.rating
        ORDER BY supplier_revenue DESC
        LIMIT 10
    """
    rows7 = conn.execute(q7_sql, filter_params).fetchall()
    results['supplier_revenue'] = {
        "id": 7,
        "title": "Supplier-wise Revenue Performance",
        "purpose": "Evaluates local manufacturer fulfillment contribution and partner rating alignment.",
        "sql": q7_sql.strip(),
        "data": [dict(r) for r in rows7]
    }

    # Query 8: Customer-wise Spending
    q8_sql = f"""
        SELECT c.customer_name, c.city, c.state,
               COUNT(f.sale_id) AS total_orders,
               SUM(f.quantity) AS total_items,
               ROUND(SUM(f.total_amount), 2) AS total_spent,
               ROUND(AVG(f.total_amount), 2) AS average_spend_per_order
        FROM FACT_SALES f
        JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
        JOIN DIM_DATE d ON f.date_key = d.date_key
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        JOIN DIM_SUPPLIER s ON f.supplier_key = s.supplier_key
        {filter_clause}
        GROUP BY c.customer_name, c.city, c.state
        ORDER BY total_spent DESC
        LIMIT 10
    """
    rows8 = conn.execute(q8_sql, filter_params).fetchall()
    results['customer_spending'] = {
        "id": 8,
        "title": "Top Customer Lifetime Spending",
        "purpose": "Recognizes highest-spending customer cohorts to design personalized loyalty rewards.",
        "sql": q8_sql.strip(),
        "data": [dict(r) for r in rows8]
    }

    # Query 9: Order Status Distribution (From FACT_ORDERS in Constellation)
    q9_sql = """
        SELECT order_status,
               COUNT(order_key) AS status_count,
               ROUND((COUNT(order_key) * 100.0 / (SELECT COUNT(*) FROM FACT_ORDERS)), 2) AS percentage
        FROM FACT_ORDERS
        GROUP BY order_status
        ORDER BY status_count DESC
    """
    rows9 = conn.execute(q9_sql).fetchall()
    results['order_status_distribution'] = {
        "id": 9,
        "title": "Order Fulfillment Status Breakdown",
        "purpose": "Monitors logistics pipeline efficiency across Delivered, Shipped, Processing, Cancelled, and Returned.",
        "sql": q9_sql.strip(),
        "data": [dict(r) for r in rows9]
    }

    # Query 10: Average Order Value (AOV)
    q10_sql = f"""
        SELECT ROUND(AVG(order_total), 2) AS average_order_value,
               ROUND(MIN(order_total), 2) AS min_order_value,
               ROUND(MAX(order_total), 2) AS max_order_value
        FROM (
            SELECT f.order_id, SUM(f.total_amount) AS order_total
            FROM FACT_SALES f
            JOIN DIM_DATE d ON f.date_key = d.date_key
            JOIN DIM_PRODUCT p ON f.product_key = p.product_key
            JOIN DIM_SUPPLIER s ON f.supplier_key = s.supplier_key
            JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
            {filter_clause}
            GROUP BY f.order_id
        )
    """
    row10 = conn.execute(q10_sql, filter_params).fetchone()
    aov = row10['average_order_value'] if row10 and row10['average_order_value'] else 0.0
    results['average_order_value'] = {
        "id": 10,
        "title": "Average Order Value (AOV)",
        "purpose": "Evaluates customer purchasing power and average cart monetary commitment.",
        "sql": q10_sql.strip(),
        "value": aov,
        "min": row10['min_order_value'] if row10 else 0.0,
        "max": row10['max_order_value'] if row10 else 0.0,
        "formatted": f"₹{aov:,.2f}"
    }

    # Query 11: Month-over-Month (MoM) Growth Analysis
    q11_sql = f"""
        WITH MonthlyTotals AS (
            SELECT d.year, d.month,
                   ROUND(SUM(f.total_amount), 2) AS revenue
            FROM FACT_SALES f
            JOIN DIM_DATE d ON f.date_key = d.date_key
            JOIN DIM_PRODUCT p ON f.product_key = p.product_key
            JOIN DIM_SUPPLIER s ON f.supplier_key = s.supplier_key
            JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
            {filter_clause}
            GROUP BY d.year, d.month
        )
        SELECT curr.year, curr.month, curr.revenue AS current_revenue,
               prev.revenue AS previous_revenue,
               ROUND(((curr.revenue - prev.revenue) / NULLIF(prev.revenue, 0)) * 100, 2) AS mom_growth_pct
        FROM MonthlyTotals curr
        LEFT JOIN MonthlyTotals prev ON (curr.year = prev.year AND curr.month = prev.month + 1)
                                      OR (curr.year = prev.year + 1 AND curr.month = 1 AND prev.month = 12)
        ORDER BY curr.year, curr.month
    """
    rows11 = conn.execute(q11_sql, filter_params).fetchall()
    results['mom_growth'] = {
        "id": 11,
        "title": "Month-over-Month (MoM) Growth Rate",
        "purpose": "Measures sequential monthly revenue acceleration to detect seasonal spikes and market contractions.",
        "sql": q11_sql.strip(),
        "data": [dict(r) for r in rows11]
    }

    # Query 12: Profit Margin Percentage by Category
    q12_sql = f"""
        SELECT p.category,
               ROUND(SUM(f.total_amount), 2) AS revenue,
               ROUND(SUM(f.profit), 2) AS net_profit,
               ROUND((SUM(f.profit) / SUM(f.total_amount)) * 100, 2) AS profit_margin_pct
        FROM FACT_SALES f
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        JOIN DIM_DATE d ON f.date_key = d.date_key
        JOIN DIM_SUPPLIER s ON f.supplier_key = s.supplier_key
        JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
        {filter_clause}
        GROUP BY p.category
        ORDER BY profit_margin_pct DESC
    """
    rows12 = conn.execute(q12_sql, filter_params).fetchall()
    results['category_profit_margin'] = {
        "id": 12,
        "title": "Profit Margin Ranking by Category",
        "purpose": "Identifies most lucrative categories to steer dropshipping procurement contracts.",
        "sql": q12_sql.strip(),
        "data": [dict(r) for r in rows12]
    }

    # Query 13: Top 5 Suppliers by Net Profit with Average Rating
    q13_sql = f"""
        SELECT s.supplier_name, s.rating,
               ROUND(SUM(f.total_amount), 2) AS revenue_generated,
               ROUND(SUM(f.profit), 2) AS net_profit_generated,
               ROUND((SUM(f.profit) / SUM(f.total_amount)) * 100, 1) AS margin_pct,
               COUNT(f.sale_id) AS orders_handled
        FROM FACT_SALES f
        JOIN DIM_SUPPLIER s ON f.supplier_key = s.supplier_key
        JOIN DIM_DATE d ON f.date_key = d.date_key
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
        {filter_clause}
        GROUP BY s.supplier_name, s.rating
        ORDER BY net_profit_generated DESC
        LIMIT 5
    """
    rows13 = conn.execute(q13_sql, filter_params).fetchall()
    results['top_suppliers_profit'] = {
        "id": 13,
        "title": "Top 5 Suppliers by Net Profit Contribution",
        "purpose": "Recognizes highest value-add supplier partners correlating fulfillment quality with earnings.",
        "sql": q13_sql.strip(),
        "data": [dict(r) for r in rows13]
    }

    # Query 14: Top 10 Indian Cities by Revenue
    q14_sql = f"""
        SELECT c.city, c.state,
               COUNT(DISTINCT c.customer_id) AS customer_count,
               COUNT(f.sale_id) AS orders_count,
               ROUND(SUM(f.total_amount), 2) AS total_revenue
        FROM FACT_SALES f
        JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
        JOIN DIM_DATE d ON f.date_key = d.date_key
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        JOIN DIM_SUPPLIER s ON f.supplier_key = s.supplier_key
        {filter_clause}
        GROUP BY c.city, c.state
        ORDER BY total_revenue DESC
        LIMIT 10
    """
    rows14 = conn.execute(q14_sql, filter_params).fetchall()
    results['top_cities_revenue'] = {
        "id": 14,
        "title": "Top 10 Cities by Revenue Volume",
        "purpose": "Guides regional logistics infrastructure and hyper-local supply chain warehousing.",
        "sql": q14_sql.strip(),
        "data": [dict(r) for r in rows14]
    }

    # Query 15: Cancellation & Return Rates by Supplier
    q15_sql = """
        SELECT s.supplier_name, s.rating,
               COUNT(fo.order_key) AS total_orders_assigned,
               SUM(fo.is_delivered) AS delivered_count,
               SUM(fo.is_cancelled) AS cancelled_count,
               SUM(fo.is_returned) AS returned_count,
               ROUND((SUM(fo.is_cancelled) * 100.0 / COUNT(fo.order_key)), 2) AS cancellation_rate_pct,
               ROUND((SUM(fo.is_returned) * 100.0 / COUNT(fo.order_key)), 2) AS return_rate_pct
        FROM FACT_ORDERS fo
        JOIN DIM_SUPPLIER s ON fo.supplier_key = s.supplier_key
        GROUP BY s.supplier_name, s.rating
        HAVING total_orders_assigned >= 50
        ORDER BY cancellation_rate_pct DESC
        LIMIT 10
    """
    rows15 = conn.execute(q15_sql).fetchall()
    results['supplier_risk_rates'] = {
        "id": 15,
        "title": "Supplier Cancellation and Return Rate Scorecard",
        "purpose": "Audits operational supply chain friction to enforce supplier Service Level Agreements (SLAs).",
        "sql": q15_sql.strip(),
        "data": [dict(r) for r in rows15]
    }

    conn.close()
    return results


def get_filter_options():
    """Returns available distinct filter values for frontend dropdowns."""
    conn = get_dw_conn()
    years = [r[0] for r in conn.execute("SELECT DISTINCT year FROM DIM_DATE ORDER BY year DESC").fetchall()]
    categories = [r[0] for r in conn.execute("SELECT DISTINCT category FROM DIM_PRODUCT ORDER BY category").fetchall()]
    suppliers = [dict(r) for r in conn.execute("SELECT supplier_id, supplier_name FROM DIM_SUPPLIER ORDER BY supplier_name").fetchall()]
    states = [r[0] for r in conn.execute("SELECT DISTINCT state FROM DIM_CUSTOMER ORDER BY state").fetchall()]
    conn.close()
    return {
        "years": years,
        "categories": categories,
        "suppliers": suppliers,
        "states": states
    }


if __name__ == "__main__":
    queries = get_all_analytical_queries()
    print("Executed all 15 Analytical Queries successfully:")
    print(f"Total Revenue : Rs. {queries['total_revenue']['value']:,.2f}")
    print(f"Total Orders  : {queries['total_orders']['formatted']}")
    print(f"Total Profit  : Rs. {queries['total_profit']['value']:,.2f}")
    print(f"Avg Order Val : Rs. {queries['average_order_value']['value']:,.2f}")
