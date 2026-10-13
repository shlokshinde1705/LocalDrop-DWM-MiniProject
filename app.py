"""
LocalDrop: Main Flask Web Application Engine
Institute: Vidyalankar Institute of Technology, Department of Information Technology
Subject: Data Warehouse Management (TE INFT, Sem V)
Students: Ayush Kamble (24101C0065), Shlok Shinde (24101C0063), Division INFT C
"""

import os
import sys
import io
import csv
import json
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, jsonify, Response, send_file, redirect, url_for, abort

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import config
from etl import data_quality
from analytics import queries, olap, visualization
from mining import classification, clustering, association

app = Flask(__name__)
app.config['SECRET_KEY'] = 'localdrop-dwm-academic-key-2026'


def query_db(db_path, query, args=(), one=False):
    """Universal SQLite query executor returning dictionaries."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    if one:
        return dict(rows[0]) if rows else None
    return [dict(r) for r in rows]


@app.context_processor
def utility_processor():
    def product_image_url(product):
        """
        Resolves image URL for product:
        1. static/images/products/product_<id>.jpg if exists
        2. None (caller renders professional neutral placeholder)
        Do NOT use shared category photo for individual products.
        """
        if not product:
            return None

        pid = None
        if isinstance(product, int):
            pid = product
        elif isinstance(product, str) and product.isdigit():
            pid = int(product)
        elif isinstance(product, dict):
            pid = product.get('product_id')
        else:
            try:
                pid = product['product_id']
            except Exception:
                pid = getattr(product, 'product_id', None)

        if pid is not None:
            for ext in ['jpg', 'jpeg', 'webp', 'png']:
                prod_img_rel = f"images/products/product_{pid}.{ext}"
                prod_img_path = os.path.join(config.BASE_DIR, "static", prod_img_rel)
                if os.path.exists(prod_img_path):
                    return url_for('static', filename=prod_img_rel)

        return None

    def category_image_url(category_name):
        """Resolves image URL for a category."""
        if not category_name:
            return None
        cat_slug = category_name.lower().replace('&', 'and').replace(' ', '_').replace('__', '_')
        cat_img_rel = f"images/categories/{cat_slug}.jpg"
        if os.path.exists(os.path.join(config.BASE_DIR, "static", cat_img_rel)):
            return url_for('static', filename=cat_img_rel)
        cat_slug_alt = category_name.lower().replace(' ', '_')
        cat_img_alt_rel = f"images/categories/{cat_slug_alt}.jpg"
        if os.path.exists(os.path.join(config.BASE_DIR, "static", cat_img_alt_rel)):
            return url_for('static', filename=cat_img_alt_rel)
        return None

    return dict(product_image_url=product_image_url, category_image_url=category_image_url)


# =============================================================================
# 1. MAIN DASHBOARD ROUTE (ANALYTICS PORTAL OVERVIEW)
# =============================================================================
@app.route('/dashboard')
@app.route('/')
def dashboard():
    """Executive Business Intelligence Dashboard with interactive KPIs and Chart.js charts."""
    # Capture filter parameters
    filter_year = request.args.get('year', '')
    filter_category = request.args.get('category', '')
    filter_supplier = request.args.get('supplier_id', '')
    filter_state = request.args.get('state', '')

    filters = {
        'year': filter_year,
        'category': filter_category,
        'supplier_id': filter_supplier,
        'state': filter_state
    }

    # Execute Analytical SQL with parameterization
    all_queries = queries.get_all_analytical_queries(filters)
    filter_opts = queries.get_filter_options()

    # Calculate cancellation rate from FACT_ORDERS
    orders_stat = query_db(
        config.WAREHOUSE_DB_PATH,
        "SELECT COUNT(*) AS total, SUM(is_cancelled) AS cancelled, SUM(is_delivered) AS delivered FROM FACT_ORDERS",
        one=True
    )
    total_ord = orders_stat['total'] if orders_stat and orders_stat['total'] else 1
    cancelled_cnt = orders_stat['cancelled'] if orders_stat and orders_stat['cancelled'] else 0
    cancellation_rate = round((cancelled_cnt / total_ord) * 100, 2)

    # Top Suppliers for Dashboard Table
    top_suppliers = all_queries['supplier_revenue']['data'][:5]

    # Top Customers for Dashboard Table
    top_customers = all_queries['customer_spending']['data'][:5]

    # Total Customer Count
    cust_stat = query_db(config.WAREHOUSE_DB_PATH, "SELECT COUNT(*) AS count FROM DIM_CUSTOMER", one=True)
    kpi_customers = f"{cust_stat['count']:,}" if cust_stat else "300"

    # Low Stock Inventory Alert
    low_stock_stat = query_db(config.OPERATIONAL_DB_PATH, "SELECT COUNT(*) AS count FROM PRODUCTS WHERE stock_quantity < 40", one=True)
    low_stock_count = low_stock_stat['count'] if low_stock_stat else 0

    # Dynamic Business Alerts / Observations
    top_cat_data = all_queries['category_sales']['data'][0] if all_queries['category_sales']['data'] else None
    top_cat_name = top_cat_data['category'] if top_cat_data else "Electronics"
    top_cat_rev = f"₹{top_cat_data['category_revenue']:,.2f}" if top_cat_data else "₹0.00"

    business_alerts = [
        {
            "type": "info",
            "title": "Fulfillment Health",
            "message": f"{round(100.0 - cancellation_rate, 1)}% of orders completed successfully ({total_ord - cancelled_cnt:,} delivered) with a low {cancellation_rate}% cancellation rate."
        },
        {
            "type": "warning" if low_stock_count > 0 else "info",
            "title": "Inventory Replenishment Notice",
            "message": f"{low_stock_count} products currently have stock below 40 units and may require supplier restocking."
        },
        {
            "type": "success",
            "title": "Category Sales Leader",
            "message": f"{top_cat_name} generates the highest revenue ({top_cat_rev}) across the marketplace."
        }
    ]

    # Recent Settled Sales
    recent_sales = query_db(
        config.WAREHOUSE_DB_PATH,
        """
        SELECT f.sale_id, f.order_id, d.date AS sale_date, c.customer_name,
               p.product_name, p.category, f.quantity, f.total_amount, f.profit
        FROM FACT_SALES f
        JOIN DIM_CUSTOMER c ON f.customer_key = c.customer_key
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        JOIN DIM_DATE d ON f.date_key = d.date_key
        ORDER BY d.date DESC, f.sale_id DESC
        LIMIT 6
        """
    )

    return render_template(
        'index.html',
        active_page='dashboard',
        kpi_revenue=all_queries['total_revenue']['formatted'],
        kpi_orders=all_queries['total_orders']['formatted'],
        kpi_customers=kpi_customers,
        kpi_profit=all_queries['total_profit']['formatted'],
        kpi_margin=f"{all_queries['total_profit']['margin_pct']}%",
        kpi_aov=all_queries['average_order_value']['formatted'],
        kpi_cancellation=f"{cancellation_rate}%",
        monthly_sales=all_queries['monthly_sales']['data'],
        category_sales=all_queries['category_sales']['data'],
        top_products=all_queries['top_5_products']['data'],
        order_status=all_queries['order_status_distribution']['data'],
        top_suppliers=top_suppliers,
        top_customers=top_customers,
        business_alerts=business_alerts,
        recent_sales=recent_sales,
        filters=filters,
        filter_opts=filter_opts
    )


# =============================================================================
# 2. ORDERS MANAGEMENT ROUTE
# =============================================================================
@app.route('/orders')
def orders():
    """Operational Orders Explorer with search, status filtering, and sorting."""
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    sort_dir = request.args.get('sort', 'desc').lower()
    page = int(request.args.get('page', 1))
    per_page = 25

    where_clauses = ["1=1"]
    params = []

    if search:
        where_clauses.append("(c.customer_name LIKE ? OR p.product_name LIKE ? OR s.supplier_name LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    if status_filter:
        where_clauses.append("o.order_status = ?")
        params.append(status_filter)

    order_sql = "ASC" if sort_dir == 'asc' else "DESC"

    where_str = " AND ".join(where_clauses)

    count_query = f"""
        SELECT COUNT(*) AS total
        FROM ORDERS o
        JOIN CUSTOMERS c ON o.customer_id = c.customer_id
        JOIN PRODUCTS p ON o.product_id = p.product_id
        JOIN SUPPLIERS s ON o.supplier_id = s.supplier_id
        WHERE {where_str}
    """
    total_records = query_db(config.OPERATIONAL_DB_PATH, count_query, params, one=True)['total']

    offset = (page - 1) * per_page
    query = f"""
        SELECT o.order_id, o.order_date, c.customer_name, c.city AS customer_city,
               p.product_name, p.category, s.supplier_name, o.quantity,
               ROUND(p.price * o.quantity, 2) AS total_amount,
               o.order_status
        FROM ORDERS o
        JOIN CUSTOMERS c ON o.customer_id = c.customer_id
        JOIN PRODUCTS p ON o.product_id = p.product_id
        JOIN SUPPLIERS s ON o.supplier_id = s.supplier_id
        WHERE {where_str}
        ORDER BY o.order_date {order_sql}, o.order_id {order_sql}
        LIMIT ? OFFSET ?
    """
    order_rows = query_db(config.OPERATIONAL_DB_PATH, query, params + [per_page, offset])

    # Status summary counts
    status_counts = query_db(
        config.OPERATIONAL_DB_PATH,
        "SELECT order_status, COUNT(*) as cnt FROM ORDERS GROUP BY order_status"
    )

    total_pages = (total_records + per_page - 1) // per_page

    return render_template(
        'orders.html',
        active_page='orders',
        orders=order_rows,
        search=search,
        status_filter=status_filter,
        sort_dir=sort_dir,
        page=page,
        total_pages=total_pages,
        total_records=total_records,
        status_counts=status_counts
    )


# =============================================================================
# 3. PRODUCTS CATALOG ROUTE
# =============================================================================
@app.route('/products')
def products():
    """Product catalog with category filter, supplier mapping, and margin calculation."""
    search = request.args.get('search', '').strip()
    cat_filter = request.args.get('category', '').strip()

    where_clauses = ["1=1"]
    params = []

    if search:
        where_clauses.append("p.product_name LIKE ?")
        params.append(f"%{search}%")

    if cat_filter:
        where_clauses.append("p.category = ?")
        params.append(cat_filter)

    where_str = " AND ".join(where_clauses)
    query = f"""
        SELECT p.product_id, p.product_name, p.category, s.supplier_name,
               p.price, p.cost_price, p.stock_quantity,
               ROUND(p.price - p.cost_price, 2) AS unit_profit,
               ROUND(((p.price - p.cost_price) / p.price) * 100, 1) AS margin_pct
        FROM PRODUCTS p
        JOIN SUPPLIERS s ON p.supplier_id = s.supplier_id
        WHERE {where_str}
        ORDER BY p.category, p.product_name
    """
    product_rows = query_db(config.OPERATIONAL_DB_PATH, query, params)
    categories = query_db(config.OPERATIONAL_DB_PATH, "SELECT DISTINCT category FROM PRODUCTS ORDER BY category")

    total_prods = len(product_rows)
    low_stock_cnt = sum(1 for p in product_rows if p['stock_quantity'] < 40)

    return render_template(
        'products.html',
        active_page='products',
        products=product_rows,
        categories=categories,
        search=search,
        cat_filter=cat_filter,
        total_products=total_prods,
        low_stock_count=low_stock_cnt
    )


# =============================================================================
# 4. CUSTOMERS DIRECTORY ROUTE
# =============================================================================
@app.route('/customers')
def customers():
    """Customer directory with state filtering and lifetime value metrics."""
    search = request.args.get('search', '').strip()
    state_filter = request.args.get('state', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 25

    where_clauses = ["1=1"]
    params = []

    if search:
        where_clauses.append("c.customer_name LIKE ?")
        params.append(f"%{search}%")

    if state_filter:
        where_clauses.append("c.state = ?")
        params.append(state_filter)

    where_str = " AND ".join(where_clauses)

    count_query = f"SELECT COUNT(*) AS total FROM CUSTOMERS c WHERE {where_str}"
    total_records = query_db(config.OPERATIONAL_DB_PATH, count_query, params, one=True)['total']

    offset = (page - 1) * per_page
    query = f"""
        SELECT c.customer_id, c.customer_name, c.city, c.state, c.registration_date,
               COUNT(o.order_id) AS total_orders,
               COALESCE(SUM(s.total_amount), 0.0) AS total_spent,
               COALESCE(SUM(s.profit), 0.0) AS total_profit_contributed
        FROM CUSTOMERS c
        LEFT JOIN ORDERS o ON c.customer_id = o.customer_id
        LEFT JOIN SALES s ON o.order_id = s.order_id
        WHERE {where_str}
        GROUP BY c.customer_id, c.customer_name, c.city, c.state, c.registration_date
        ORDER BY total_spent DESC
        LIMIT ? OFFSET ?
    """
    cust_rows = query_db(config.OPERATIONAL_DB_PATH, query, params + [per_page, offset])
    states = query_db(config.OPERATIONAL_DB_PATH, "SELECT DISTINCT state FROM CUSTOMERS ORDER BY state")

    total_pages = (total_records + per_page - 1) // per_page

    return render_template(
        'customers.html',
        active_page='customers',
        customers=cust_rows,
        states=states,
        search=search,
        state_filter=state_filter,
        page=page,
        total_pages=total_pages,
        total_records=total_records
    )


# =============================================================================
# 5. SUPPLIERS NETWORK ROUTE
# =============================================================================
@app.route('/suppliers')
def suppliers():
    """Supplier directory with quality ratings and revenue contribution."""
    search = request.args.get('search', '').strip()

    params = []
    where_sql = "1=1"
    if search:
        where_sql = "s.supplier_name LIKE ?"
        params.append(f"%{search}%")

    query = f"""
        SELECT s.supplier_id, s.supplier_name, s.city, s.state, s.supplier_rating,
               COUNT(DISTINCT p.product_id) AS catalog_products_count,
               COUNT(DISTINCT o.order_id) AS total_orders_handled,
               COALESCE(SUM(sa.total_amount), 0.0) AS total_revenue_generated,
               COALESCE(SUM(sa.profit), 0.0) AS total_profit_generated
        FROM SUPPLIERS s
        LEFT JOIN PRODUCTS p ON s.supplier_id = p.supplier_id
        LEFT JOIN ORDERS o ON s.supplier_id = o.supplier_id
        LEFT JOIN SALES sa ON o.order_id = sa.order_id
        WHERE {where_sql}
        GROUP BY s.supplier_id, s.supplier_name, s.city, s.state, s.supplier_rating
        ORDER BY total_revenue_generated DESC
    """
    supplier_rows = query_db(config.OPERATIONAL_DB_PATH, query, params)
    total_revenue_all = sum(s['total_revenue_generated'] for s in supplier_rows) or 1.0

    for s in supplier_rows:
        s['revenue_share_pct'] = round((s['total_revenue_generated'] / total_revenue_all) * 100, 1)

    return render_template(
        'suppliers.html',
        active_page='suppliers',
        suppliers=supplier_rows,
        search=search,
        total_suppliers=len(supplier_rows)
    )


# =============================================================================
# 6. ANALYTICS PAGE (15 ANALYTICAL SQL QUERIES)
# =============================================================================
@app.route('/analytics')
def analytics():
    """Dedicated analytical portal executing all 15 SQL queries with live filters."""
    filter_year = request.args.get('year', '')
    filter_category = request.args.get('category', '')
    filter_supplier = request.args.get('supplier_id', '')
    filter_state = request.args.get('state', '')

    filters = {
        'year': filter_year,
        'category': filter_category,
        'supplier_id': filter_supplier,
        'state': filter_state
    }

    all_queries = queries.get_all_analytical_queries(filters)
    filter_opts = queries.get_filter_options()

    return render_template(
        'analytics.html',
        active_page='analytics',
        queries=all_queries,
        filters=filters,
        filter_opts=filter_opts
    )


# =============================================================================
# 7. OLAP OPERATIONS ROUTE
# =============================================================================
@app.route('/olap')
def olap_page():
    """Interactive multidimensional OLAP operations suite (Roll-up, Drill-down, Slice, Dice, Pivot, CUBE)."""
    rollup_lvl = request.args.get('rollup_level', 'quarter')
    drill_mode = request.args.get('drill_mode', 'category_to_product')
    drill_target = request.args.get('drill_target', 'Electronics')
    slice_dim = request.args.get('slice_dim', 'category')
    slice_val = request.args.get('slice_val', 'Electronics')

    # Execute OLAP functions
    res_rollup = olap.olap_rollup(level=rollup_lvl)
    res_drill = olap.olap_drilldown(mode=drill_mode, target_val=drill_target)
    res_slice = olap.olap_slice(slice_dimension=slice_dim, slice_value=slice_val)
    res_dice = olap.olap_dice()
    res_pivot = olap.olap_pivot()
    res_cube = olap.olap_cube_simulation()

    return render_template(
        'olap.html',
        active_page='olap',
        rollup=res_rollup,
        drill=res_drill,
        slice=res_slice,
        dice=res_dice,
        pivot=res_pivot,
        cube=res_cube,
        current_rollup_level=rollup_lvl,
        current_drill_target=drill_target,
        current_slice_dim=slice_dim,
        current_slice_val=slice_val
    )


# =============================================================================
# 8. VISUALIZATION EXPLORER ROUTE
# =============================================================================
@app.route('/visualization')
def visual_explorer():
    """Visual exploration of distributions, box-plots, scatter charts, and correlations."""
    vis_data = visualization.get_visualization_data()
    return render_template(
        'visualization.html',
        active_page='visualization',
        vis=vis_data
    )


# =============================================================================
# 9. DATA PREPROCESSING & QUALITY ROUTE
# =============================================================================
@app.route('/data-preprocessing')
def data_preprocessing():
    """Data Quality audit, before-vs-after metrics, nulls handling, and sample tables."""
    dq_report = data_quality.generate_data_quality_report()
    return render_template(
        'preprocessing.html',
        active_page='data_preprocessing',
        report=dq_report
    )

data_preprocessing_page = data_preprocessing


# =============================================================================
# 10. DATA WAREHOUSE & SCHEMAS ROUTE
# =============================================================================
@app.route('/data-warehouse')
def data_warehouse_page():
    """Interactive visual schemas (Star, Snowflake, Constellation, Data Mart), ETL log, and benchmarks."""
    conn_dw = sqlite3.connect(config.WAREHOUSE_DB_PATH)
    conn_dw.row_factory = sqlite3.Row

    # Table row counts
    table_counts = {}
    for tbl in ['FACT_SALES', 'FACT_ORDERS', 'DIM_CUSTOMER', 'DIM_SUPPLIER', 'DIM_PRODUCT', 'DIM_DATE',
                'DIM_CATEGORY', 'DIM_LOCATION', 'DIM_PRODUCT_SF', 'DIM_CUSTOMER_SF', 'DIM_SUPPLIER_SF', 'FACT_SALES_SF']:
        table_counts[tbl] = conn_dw.execute(f"SELECT COUNT(*) as c FROM {tbl}").fetchone()['c']

    # ETL Logs
    etl_logs = conn_dw.execute("SELECT * FROM etl_log ORDER BY log_id ASC").fetchall()
    etl_logs_list = [dict(r) for r in etl_logs]

    # Star vs Snowflake benchmark query
    t0 = sqlite3.time.time()
    res_star = conn_dw.execute("""
        SELECT p.category, ROUND(SUM(f.total_amount), 2) AS rev
        FROM FACT_SALES f
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        GROUP BY p.category ORDER BY rev DESC
    """).fetchall()
    star_time = round((sqlite3.time.time() - t0) * 1000, 3)

    t1 = sqlite3.time.time()
    res_sf = conn_dw.execute("""
        SELECT c.category_name, ROUND(SUM(f.total_amount), 2) AS rev
        FROM FACT_SALES_SF f
        JOIN DIM_PRODUCT_SF p ON f.product_key = p.product_key
        JOIN DIM_CATEGORY c ON p.category_id = c.category_id
        GROUP BY c.category_name ORDER BY rev DESC
    """).fetchall()
    sf_time = round((sqlite3.time.time() - t1) * 1000, 3)
    conn_dw.close()

    # Load Data Dictionary
    data_dict = {}
    if os.path.exists(config.DATA_DICTIONARY_PATH):
        try:
            with open(config.DATA_DICTIONARY_PATH, "r") as f:
                data_dict = json.load(f)
        except Exception:
            pass

    return render_template(
        'warehouse.html',
        active_page='data_warehouse',
        table_counts=table_counts,
        etl_logs=etl_logs_list,
        star_benchmark={
            "star_time_ms": star_time,
            "sf_time_ms": sf_time,
            "star_data": [dict(r) for r in res_star],
            "sf_data": [dict(r) for r in res_sf],
            "match": [dict(r) for r in res_star] == [dict(r) for r in res_sf]
        },
        data_dictionary=data_dict
    )


# =============================================================================
# 11. BUSINESS INSIGHTS ROUTE (COMBINED OLAP, ANALYTICAL SQL & VISUALIZATION)
# =============================================================================
@app.route('/business-insights')
def business_insights():
    """Unified Business Insights answering practical questions without technical jargon."""
    filter_year = request.args.get('year', '')
    filter_category = request.args.get('category', '')
    filter_supplier = request.args.get('supplier_id', '')
    filter_state = request.args.get('state', '')

    filters = {
        'year': filter_year,
        'category': filter_category,
        'supplier_id': filter_supplier,
        'state': filter_state
    }

    all_queries = queries.get_all_analytical_queries(filters)
    filter_opts = queries.get_filter_options()
    vis_data = visualization.get_visualization_data()
    rollup_data = olap.olap_rollup(level='quarter')

    # Order fulfillment status breakdown
    order_status_rows = query_db(
        config.WAREHOUSE_DB_PATH,
        "SELECT order_status, COUNT(*) as count FROM FACT_ORDERS GROUP BY order_status ORDER BY count DESC"
    )
    total_ord = sum(r['count'] for r in order_status_rows) or 1
    status_summary = []
    for r in order_status_rows:
        d = dict(r)
        d['share_pct'] = round((d['count'] / total_ord) * 100, 1)
        status_summary.append(d)

    return render_template(
        'business_insights.html',
        active_page='business_insights',
        queries=all_queries,
        vis=vis_data,
        rollup=rollup_data,
        status_summary=status_summary,
        total_orders_count=total_ord,
        filters=filters,
        filter_opts=filter_opts
    )


# =============================================================================
# 12. RECOMMENDATIONS ROUTE (DATA-DRIVEN SUGGESTIONS)
# =============================================================================
@app.route('/recommendations')
@app.route('/data-mining')
def recommendations():
    """Actionable recommendations derived from customer segmentation, product affinity, and profitability."""
    class_results = classification.run_classification()
    clust_results = clustering.run_clustering()
    assoc_results = association.run_association()

    return render_template(
        'recommendations.html',
        active_page='recommendations',
        classification=class_results,
        clustering=clust_results,
        association=assoc_results
    )

data_mining_page = recommendations


# =============================================================================
# 12. READ-ONLY CSV EXPORT ROUTE
# =============================================================================
@app.route('/export/csv/<dataset>')
def export_csv(dataset):
    """Dynamic CSV streaming export for any analytical table."""
    conn_dw = sqlite3.connect(config.WAREHOUSE_DB_PATH)

    if dataset == 'orders':
        df = pd.read_sql_query("SELECT * FROM FACT_ORDERS LIMIT 5000", conn_dw)
        filename = "localdrop_fact_orders.csv"
    elif dataset == 'sales':
        df = pd.read_sql_query("SELECT * FROM FACT_SALES LIMIT 5000", conn_dw)
        filename = "localdrop_fact_sales.csv"
    elif dataset == 'products':
        df = pd.read_sql_query("SELECT * FROM DIM_PRODUCT", conn_dw)
        filename = "localdrop_dim_product.csv"
    elif dataset == 'customers':
        df = pd.read_sql_query("SELECT * FROM DIM_CUSTOMER", conn_dw)
        filename = "localdrop_dim_customer.csv"
    elif dataset == 'suppliers':
        df = pd.read_sql_query("SELECT * FROM DIM_SUPPLIER", conn_dw)
        filename = "localdrop_dim_supplier.csv"
    elif dataset == 'apriori_rules':
        assoc = association.run_association()
        df = pd.DataFrame(assoc.get('rules', []))
        filename = "localdrop_apriori_rules.csv"
    elif dataset == 'customer_clusters':
        clust = clustering.run_clustering()
        df = pd.DataFrame(clust.get('cluster_profiles', []))
        filename = "localdrop_customer_clusters.csv"
    else:
        df = pd.read_sql_query("SELECT * FROM FACT_SALES LIMIT 1000", conn_dw)
        filename = "localdrop_export.csv"

    conn_dw.close()

    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


# =============================================================================
# PUBLIC STOREFRONT (CUSTOMER-FACING FRONT-END) ROUTES
# =============================================================================

def get_verified_product_ids():
    """
    Returns list of product IDs with verified existing image files on disk.
    The customer-facing storefront presentation layer exclusively displays
    products that have valid, verified photos.
    """
    prod_img_dir = os.path.join(config.BASE_DIR, "static", "images", "products")
    if not os.path.exists(prod_img_dir):
        return []
    pids = []
    for fname in os.listdir(prod_img_dir):
        if fname.startswith("product_"):
            base, ext = os.path.splitext(fname)
            if ext.lower() in [".jpg", ".jpeg", ".webp", ".png"]:
                pid_str = base[len("product_"):]
                if pid_str.isdigit():
                    pids.append(int(pid_str))
    return sorted(pids)


@app.route('/store')
def store_home():
    """Public Storefront Home: Banner, category list, featured products, top suppliers."""
    verified_pids = get_verified_product_ids()
    if not verified_pids:
        return render_template(
            'store_home.html',
            store_page='home',
            categories=[],
            featured_products=[],
            top_suppliers=[]
        )

    placeholders = ",".join("?" for _ in verified_pids)

    conn = sqlite3.connect(config.OPERATIONAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(f"SELECT DISTINCT category FROM PRODUCTS WHERE product_id IN ({placeholders}) ORDER BY category", verified_pids)
    categories = [r['category'] for r in cur.fetchall()]

    # Featured products: strictly verified products, ordered by units sold, then product_id
    cur.execute(f"""
        SELECT p.*, s.supplier_name, COALESCE(SUM(sa.quantity), 0) AS units_sold
        FROM PRODUCTS p
        JOIN SUPPLIERS s ON p.supplier_id = s.supplier_id
        LEFT JOIN ORDERS o ON p.product_id = o.product_id AND o.order_status = 'Delivered'
        LEFT JOIN SALES sa ON o.order_id = sa.order_id
        WHERE p.product_id IN ({placeholders})
        GROUP BY p.product_id
        ORDER BY units_sold DESC, p.product_id ASC
        LIMIT 8
    """, verified_pids)
    featured_products = [dict(r) for r in cur.fetchall()]

    # Top suppliers: suppliers offering verified products, with product_count reflecting verified catalog items
    cur.execute(f"""
        SELECT s.*, COUNT(p.product_id) AS product_count
        FROM SUPPLIERS s
        JOIN PRODUCTS p ON s.supplier_id = p.supplier_id AND p.product_id IN ({placeholders})
        GROUP BY s.supplier_id
        ORDER BY s.supplier_rating DESC, s.supplier_name ASC
        LIMIT 6
    """, verified_pids)
    top_suppliers = [dict(r) for r in cur.fetchall()]
    conn.close()

    return render_template(
        'store_home.html',
        store_page='home',
        categories=categories,
        featured_products=featured_products,
        top_suppliers=top_suppliers
    )


@app.route('/store/products')
def store_products():
    """Public Storefront Products: Product grid with search, category filter, price sort, pagination."""
    query = request.args.get('q', '').strip()
    selected_category = request.args.get('category', '').strip()
    sort_order = request.args.get('sort', '').strip()
    page = max(1, request.args.get('page', 1, type=int))
    per_page = 12

    verified_pids = get_verified_product_ids()
    if not verified_pids:
        return render_template(
            'store_products.html',
            store_page='products',
            products=[],
            categories=[],
            query=query,
            selected_category=selected_category,
            sort_order=sort_order,
            page=1,
            total_pages=1,
            total_products=0
        )

    placeholders = ",".join("?" for _ in verified_pids)

    conn = sqlite3.connect(config.OPERATIONAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(f"SELECT DISTINCT category FROM PRODUCTS WHERE product_id IN ({placeholders}) ORDER BY category", verified_pids)
    categories = [r['category'] for r in cur.fetchall()]

    sql_base = f"""
        FROM PRODUCTS p
        JOIN SUPPLIERS s ON p.supplier_id = s.supplier_id
        WHERE p.product_id IN ({placeholders})
    """
    params = list(verified_pids)

    if query:
        sql_base += " AND (p.product_name LIKE ? OR p.category LIKE ? OR s.supplier_name LIKE ?)"
        wildcard = f"%{query}%"
        params.extend([wildcard, wildcard, wildcard])

    if selected_category:
        sql_base += " AND p.category = ?"
        params.append(selected_category)

    cur.execute(f"SELECT COUNT(*) AS cnt {sql_base}", params)
    total_products = cur.fetchone()['cnt']
    total_pages = max(1, (total_products + per_page - 1) // per_page)

    if sort_order == 'price_asc':
        order_clause = " ORDER BY p.price ASC"
    elif sort_order == 'price_desc':
        order_clause = " ORDER BY p.price DESC"
    else:
        order_clause = " ORDER BY p.product_id ASC"

    offset = (page - 1) * per_page
    query_sql = f"""
        SELECT p.*, s.supplier_name
        {sql_base}
        {order_clause}
        LIMIT ? OFFSET ?
    """
    cur.execute(query_sql, params + [per_page, offset])
    products = [dict(r) for r in cur.fetchall()]
    conn.close()

    return render_template(
        'store_products.html',
        store_page='products',
        products=products,
        categories=categories,
        query=query,
        selected_category=selected_category,
        sort_order=sort_order,
        page=page,
        total_pages=total_pages,
        total_products=total_products
    )


@app.route('/store/product/<int:product_id>')
def store_product_detail(product_id):
    """Product detail page with supplier details (city, state, rating), price, stock, and more from supplier."""
    verified_pids = get_verified_product_ids()
    if product_id not in verified_pids:
        return "Product not found", 404

    placeholders = ",".join("?" for _ in verified_pids)

    conn = sqlite3.connect(config.OPERATIONAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT p.*, s.supplier_name, s.city, s.state, s.supplier_rating
        FROM PRODUCTS p
        JOIN SUPPLIERS s ON p.supplier_id = s.supplier_id
        WHERE p.product_id = ?
    """, (product_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return "Product not found", 404

    product = dict(row)

    cur.execute(f"""
        SELECT p.*, s.supplier_name
        FROM PRODUCTS p
        JOIN SUPPLIERS s ON p.supplier_id = s.supplier_id
        WHERE p.supplier_id = ? AND p.product_id != ? AND p.product_id IN ({placeholders})
        ORDER BY p.product_id ASC
        LIMIT 4
    """, [product['supplier_id'], product_id] + verified_pids)
    more_products = [dict(r) for r in cur.fetchall()]
    conn.close()

    return render_template(
        'store_product_detail.html',
        store_page='products',
        product=product,
        more_products=more_products
    )


@app.route('/store/suppliers')
def store_suppliers():
    """List of local suppliers with city, state, and rating."""
    query = request.args.get('q', '').strip()
    verified_pids = get_verified_product_ids()
    if not verified_pids:
        return render_template('store_suppliers.html', store_page='suppliers', suppliers=[], query=query)

    placeholders = ",".join("?" for _ in verified_pids)

    conn = sqlite3.connect(config.OPERATIONAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sql = f"""
        SELECT s.*, COUNT(p.product_id) AS product_count
        FROM SUPPLIERS s
        JOIN PRODUCTS p ON s.supplier_id = p.supplier_id AND p.product_id IN ({placeholders})
        WHERE 1=1
    """
    params = list(verified_pids)
    if query:
        sql += " AND (s.supplier_name LIKE ? OR s.city LIKE ? OR s.state LIKE ?)"
        wildcard = f"%{query}%"
        params.extend([wildcard, wildcard, wildcard])

    sql += " GROUP BY s.supplier_id ORDER BY s.supplier_rating DESC, s.supplier_name ASC"

    cur.execute(sql, params)
    suppliers = [dict(r) for r in cur.fetchall()]
    conn.close()

    return render_template(
        'store_suppliers.html',
        store_page='suppliers',
        suppliers=suppliers,
        query=query
    )


@app.route('/store/supplier/<int:supplier_id>')
def store_supplier_detail(supplier_id):
    """Supplier profile with their products."""
    verified_pids = get_verified_product_ids()
    conn = sqlite3.connect(config.OPERATIONAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM SUPPLIERS WHERE supplier_id = ?", (supplier_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return "Supplier not found", 404

    supplier = dict(row)

    if verified_pids:
        placeholders = ",".join("?" for _ in verified_pids)
        cur.execute(f"""
            SELECT p.*, s.supplier_name
            FROM PRODUCTS p
            JOIN SUPPLIERS s ON p.supplier_id = s.supplier_id
            WHERE p.supplier_id = ? AND p.product_id IN ({placeholders})
            ORDER BY p.product_name ASC
        """, [supplier_id] + verified_pids)
        products = [dict(r) for r in cur.fetchall()]
    else:
        products = []
    conn.close()

    return render_template(
        'store_supplier_detail.html',
        store_page='suppliers',
        supplier=supplier,
        products=products
    )


@app.route('/store/about')
def store_about():
    """Short description of the platform and the DWM project (title, students, institute)."""
    return render_template(
        'store_about.html',
        store_page='about'
    )


if __name__ == '__main__':
    print("Starting LocalDrop Academic DWM Portal on http://127.0.0.1:5000...")
    app.run(debug=True, port=5000)
