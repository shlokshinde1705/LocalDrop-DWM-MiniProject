"""
LocalDrop: Report Artifact Export Script
Executes all analytical queries, OLAP, and ML models, compiling:
  1. exports/results.json
  2. exports/*.csv
  3. exports/*.png (via Matplotlib)
  4. exports/*.sql (DDL architectures)
"""

import os
import sys
import json
import time
import shutil
import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config
from etl import data_quality
from analytics import queries, olap, visualization
from mining import classification, clustering, association


def export_all_results():
    print("===================================================================")
    print("          LOCALDROP EXPORT ENGINE: GENERATING REPORT ARTIFACTS      ")
    print("===================================================================")

    os.makedirs(config.EXPORTS_DIR, exist_ok=True)

    # 1. Row counts for all tables
    print("[1/5] Collecting table row counts...")
    conn_op = sqlite3.connect(config.OPERATIONAL_DB_PATH)
    op_counts = {}
    for tbl in ['CUSTOMERS', 'SUPPLIERS', 'PRODUCTS', 'ORDERS', 'SALES']:
        op_counts[tbl] = conn_op.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    conn_op.close()

    conn_dw = sqlite3.connect(config.WAREHOUSE_DB_PATH)
    conn_dw.row_factory = sqlite3.Row
    dw_counts = {}
    for tbl in ['FACT_SALES', 'FACT_ORDERS', 'DIM_CUSTOMER', 'DIM_SUPPLIER', 'DIM_PRODUCT', 'DIM_DATE',
                'DIM_CATEGORY', 'DIM_LOCATION', 'DIM_PRODUCT_SF', 'DIM_CUSTOMER_SF', 'DIM_SUPPLIER_SF', 'FACT_SALES_SF']:
        dw_counts[tbl] = conn_dw.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]

    # Star vs Snowflake timing comparison
    print("[2/5] Benchmarking Star vs Snowflake execution latency...")
    star_query = """
        SELECT p.category, ROUND(SUM(f.total_amount), 2) as revenue
        FROM FACT_SALES f
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        GROUP BY p.category ORDER BY revenue DESC
    """
    sf_query = """
        SELECT c.category_name as category, ROUND(SUM(f.total_amount), 2) as revenue
        FROM FACT_SALES_SF f
        JOIN DIM_PRODUCT_SF p ON f.product_key = p.product_key
        JOIN DIM_CATEGORY c ON p.category_id = c.category_id
        GROUP BY c.category_name ORDER BY revenue DESC
    """

    # Warmup
    conn_dw.execute(star_query).fetchall()
    conn_dw.execute(sf_query).fetchall()

    t_s0 = time.perf_counter()
    res_star = conn_dw.execute(star_query).fetchall()
    star_time_ms = round((time.perf_counter() - t_s0) * 1000, 3)

    t_sf0 = time.perf_counter()
    res_sf = conn_dw.execute(sf_query).fetchall()
    sf_time_ms = round((time.perf_counter() - t_sf0) * 1000, 3)
    conn_dw.close()

    schema_benchmark = {
        "identical_results": [dict(r) for r in res_star] == [dict(r) for r in res_sf],
        "star_latency_ms": star_time_ms,
        "snowflake_latency_ms": sf_time_ms,
        "star_joins": 1,
        "snowflake_joins": 2,
        "result_sample": [dict(r) for r in res_star]
    }

    # 2. Collect Data Quality, Analytical SQL, OLAP, and Mining
    print("[3/5] Running Preprocessing Audit, Analytical SQL, OLAP, and ML models...")
    quality_rep = data_quality.generate_data_quality_report()
    analytical_queries = queries.get_all_analytical_queries()
    olap_pivot = olap.olap_pivot()
    olap_cube = olap.olap_cube_simulation()
    class_res = classification.run_classification(force_refresh=True)
    clust_res = clustering.run_clustering(force_refresh=True)
    assoc_res = association.run_association(force_refresh=True)

    master_results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "project": "LocalDrop DWM Mini-Project",
        "operational_table_counts": op_counts,
        "warehouse_table_counts": dw_counts,
        "star_vs_snowflake_benchmark": schema_benchmark,
        "data_quality_summary": quality_rep['summary'],
        "executive_kpis": {
            "total_revenue": analytical_queries['total_revenue']['value'],
            "total_orders": analytical_queries['total_orders']['value'],
            "total_profit": analytical_queries['total_profit']['value'],
            "average_order_value": analytical_queries['average_order_value']['value'],
            "overall_profit_margin_pct": analytical_queries['total_profit']['margin_pct']
        },
        "classification": {
            "target": class_res['target_definition'],
            "relevance_ranking": class_res['relevance_ranking'],
            "decision_tree": class_res['decision_tree']['metrics'],
            "naive_bayes": class_res['naive_bayes']['metrics']
        },
        "clustering": {
            "k": clust_res['k_selected'],
            "silhouette_score": clust_res['silhouette_score_k3'],
            "profiles": clust_res['cluster_profiles'],
            "elbow_curve": clust_res['elbow_curve']
        },
        "association": {
            "total_rules": assoc_res['total_rules_discovered'],
            "min_support": assoc_res['min_support_used'],
            "min_confidence": assoc_res['min_confidence_used'],
            "rules": assoc_res['rules'][:10]
        }
    }

    json_path = os.path.join(config.EXPORTS_DIR, "results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(master_results, f, indent=2)
    print(f" -> Saved {json_path}")

    # 3. Copy DDL SQL Files
    print("[4/5] Copying DDL architecture SQL files...")
    for sfile in ["star_schema.sql", "snowflake_schema.sql", "constellation.sql", "sales_data_mart.sql"]:
        src = os.path.join(config.WAREHOUSE_SQL_DIR, sfile)
        dst = os.path.join(config.EXPORTS_DIR, sfile)
        if os.path.exists(src):
            shutil.copyfile(src, dst)

    # 4. Export CSV Tables
    print("[5/5] Exporting CSV tables and Matplotlib charts...")
    conn_dw = sqlite3.connect(config.WAREHOUSE_DB_PATH)

    # CSV 1: Top Products
    pd.DataFrame(analytical_queries['top_5_products']['data']).to_csv(
        os.path.join(config.EXPORTS_DIR, "top_products.csv"), index=False
    )
    # CSV 2: Top Suppliers
    pd.DataFrame(analytical_queries['supplier_revenue']['data']).to_csv(
        os.path.join(config.EXPORTS_DIR, "top_suppliers.csv"), index=False
    )
    # CSV 3: Category Performance
    pd.DataFrame(analytical_queries['category_sales']['data']).to_csv(
        os.path.join(config.EXPORTS_DIR, "category_sales.csv"), index=False
    )
    # CSV 4: Apriori Rules
    pd.DataFrame(assoc_res['rules']).to_csv(
        os.path.join(config.EXPORTS_DIR, "apriori_rules.csv"), index=False
    )
    # CSV 5: Customer Clusters
    pd.DataFrame(clust_res['cluster_profiles']).to_csv(
        os.path.join(config.EXPORTS_DIR, "customer_clusters.csv"), index=False
    )
    conn_dw.close()

    # 5. Export Matplotlib Static PNG Charts
    # Chart 1: Monthly Sales Trend
    m_data = analytical_queries['monthly_sales']['data']
    m_labels = [f"{r['year']}-{r['month']:02d}" for r in m_data]
    m_rev = [r['monthly_revenue'] for r in m_data]
    m_prof = [r['monthly_profit'] for r in m_data]

    plt.figure(figsize=(10, 4.5), dpi=200)
    plt.plot(m_labels, m_rev, marker='o', color='#2980B9', label='Monthly Revenue (Rs.)', linewidth=2)
    plt.plot(m_labels, m_prof, marker='s', color='#27AE60', label='Net Profit (Rs.)', linewidth=2)
    plt.xticks(rotation=45, ha='right', fontsize=8)
    plt.title('Monthly Sales and Net Profit Trajectory (24-Month Horizon)', fontsize=11, fontweight='bold')
    plt.ylabel('Amount (Rs.)', fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(config.EXPORTS_DIR, "fig_monthly_trend.png"))
    plt.close()

    # Chart 2: Category Revenue Breakdown
    c_data = analytical_queries['category_sales']['data']
    c_labels = [r['category'] for r in c_data]
    c_rev = [r['category_revenue'] for r in c_data]

    plt.figure(figsize=(9, 4.5), dpi=200)
    bars = plt.bar(c_labels, c_rev, color='#34495E', edgecolor='#1C2833', width=0.6)
    plt.xticks(rotation=30, ha='right', fontsize=8.5)
    plt.title('Category-wise Sales Revenue Distribution', fontsize=11, fontweight='bold')
    plt.ylabel('Gross Revenue (Rs.)', fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, h + 15000, f'Rs. {h/100000:.1f}L', ha='center', va='bottom', fontsize=7.5)
    plt.tight_layout()
    plt.savefig(os.path.join(config.EXPORTS_DIR, "fig_category_sales.png"))
    plt.close()

    # Chart 3: K-Means Elbow Curve
    elbow_pts = clust_res['elbow_curve']
    k_vals = [p['k'] for p in elbow_pts]
    inertias = [p['inertia'] for p in elbow_pts]

    plt.figure(figsize=(7, 4), dpi=200)
    plt.plot(k_vals, inertias, marker='o', color='#E67E22', linewidth=2, markersize=6)
    plt.axvline(x=3, color='#C0392B', linestyle='--', label='Optimal Inflection Point (k=3)')
    plt.title('K-Means Clustering: Elbow Method for Optimal K Selection', fontsize=10, fontweight='bold')
    plt.xlabel('Number of Clusters (k)', fontsize=9)
    plt.ylabel('Inertia (Within-Cluster Sum of Squares)', fontsize=9)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(config.EXPORTS_DIR, "fig_elbow_curve.png"))
    plt.close()

    # Chart 4: Customer Segmentation Scatter Plot
    pts = clust_res['scatter_points']
    c_colors = {1: '#27AE60', 2: '#2980B9', 3: '#E67E22'}
    c_labels = {1: 'VIP Champions', 2: 'Regular Loyal', 3: 'Occasional Casual'}

    plt.figure(figsize=(8, 5), dpi=200)
    for cid in [1, 2, 3]:
        sub_pts = [p for p in pts if p['cluster_id'] == cid]
        xs = [p['x'] for p in sub_pts]
        ys = [p['y'] for p in sub_pts]
        plt.scatter(xs, ys, color=c_colors[cid], label=f"Cluster {cid}: {c_labels[cid]}", s=50, alpha=0.8, edgecolors='black', linewidth=0.5)

    for cent in clust_res['centroid_points']:
        plt.scatter(cent['x'], cent['y'], color=c_colors[cent['cluster_id']], s=180, marker='X', edgecolors='black', linewidth=1.5)

    plt.title('K-Means Customer Segmentation (Orders vs. Lifetime Spend)', fontsize=11, fontweight='bold')
    plt.xlabel('Total Orders Placed', fontsize=10)
    plt.ylabel('Total Lifetime Spending (Rs.)', fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(loc='upper left', fontsize=8.5)
    plt.tight_layout()
    plt.savefig(os.path.join(config.EXPORTS_DIR, "fig_cluster_scatter.png"))
    plt.close()

    # Chart 5: Attribute Relevance Mutual Information Ranking
    rel = class_res['relevance_ranking']
    feat_names = [r['feature'] for r in rel]
    feat_scores = [r['importance_score'] for r in rel]

    plt.figure(figsize=(8, 4.5), dpi=200)
    y_pos = np.arange(len(feat_names))
    plt.barh(y_pos, feat_scores, color='#8E44AD', edgecolor='#4A235A', height=0.6)
    plt.yticks(y_pos, feat_names, fontsize=8.5)
    plt.gca().invert_yaxis()
    plt.title('Attribute Relevance Analysis (Mutual Information for Profit Prediction)', fontsize=10.5, fontweight='bold')
    plt.xlabel('Mutual Information Importance Score', fontsize=9.5)
    plt.grid(axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(config.EXPORTS_DIR, "fig_relevance_ranking.png"))
    plt.close()

    # Chart 6: Apriori Association Rules Bar Chart
    if assoc_res['rules']:
        top_rules = assoc_res['rules'][:8]
        r_labels = [r['rule_text'][:38] + ("..." if len(r['rule_text']) > 38 else "") for r in top_rules]
        r_lifts = [r['lift'] for r in top_rules]

        plt.figure(figsize=(9, 4.5), dpi=200)
        y_pos = np.arange(len(r_labels))
        plt.barh(y_pos, r_lifts, color='#D35400', edgecolor='#7E3400', height=0.6)
        plt.yticks(y_pos, r_labels, fontsize=8)
        plt.gca().invert_yaxis()
        plt.title('Top Apriori Association Rules Ranked by Lift', fontsize=11, fontweight='bold')
        plt.xlabel('Lift Metric (Multiplicative Affinity)', fontsize=9.5)
        plt.grid(axis='x', linestyle='--', alpha=0.5)
        for i, v in enumerate(r_lifts):
            plt.text(v + 0.1, i, f"{v}x", va='center', fontsize=8, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(config.EXPORTS_DIR, "fig_apriori_rules.png"))
        plt.close()

    print("\nALL REPORT EXPORT ARTIFACTS PRODUCED SUCCESSFULLY IN exports/!")


if __name__ == "__main__":
    export_all_results()
