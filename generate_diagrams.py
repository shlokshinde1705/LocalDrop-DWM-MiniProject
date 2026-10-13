import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os
import sqlite3
import pandas as pd
from mining import run_data_mining

os.makedirs('report_assets', exist_ok=True)

# 1. System Architecture & Flowchart
fig, ax = plt.subplots(figsize=(10, 8), dpi=200)
ax.axis('off')

boxes = [
    ("Operational Source Database\n(OLTP: CUSTOMERS, SUPPLIERS, PRODUCTS, ORDERS, SALES)", 0.5, 0.92, 0.8, 0.08, '#D0E1FD'),
    ("Data Preprocessing & Validation\n(Null Handling, Range Filtering, Format Standardization)", 0.5, 0.77, 0.8, 0.08, '#FFE6CC'),
    ("ETL Pipeline (Python Pandas)\n(Extract, Cleanse, Conformed Dimensions, Key Generation)", 0.5, 0.62, 0.8, 0.08, '#D5E8D4'),
    ("Data Warehouse Repository (localdrop_warehouse.db)\n(Star Schema & Snowflake Schema Multidimensional Models)", 0.5, 0.47, 0.8, 0.08, '#FFF2CC'),
    ("Analytical SQL Processing Engine\n(Aggregations, Rolling Windows, KPI Computations)", 0.28, 0.28, 0.42, 0.12, '#E1D5E7'),
    ("Data Mining & ML Engine\n(Decision Tree, Naive Bayes, K-Means, Apriori)", 0.72, 0.28, 0.42, 0.12, '#F8CECC'),
    ("LocalDrop BI Web Portal (Flask & Chart.js GUI)\n(Interactive Dashboards, Tabular Reports, Association Rules)", 0.5, 0.08, 0.86, 0.09, '#DAE8FC')
]

for text, cx, cy, w, h, col in boxes:
    rect = patches.FancyBboxPatch((cx - w/2, cy - h/2), w, h, boxstyle="round,pad=0.02,rounding_size=0.03", 
                                  linewidth=1.5, edgecolor='#2C3E50', facecolor=col)
    ax.add_patch(rect)
    ax.text(cx, cy, text, ha='center', va='center', fontsize=9.5, fontweight='bold', color='#1A252F')

# Connectors
arrow_props = dict(arrowstyle="->", lw=2, color='#2C3E50')
ax.annotate('', xy=(0.5, 0.81), xytext=(0.5, 0.88), arrowprops=arrow_props)
ax.annotate('', xy=(0.5, 0.66), xytext=(0.5, 0.73), arrowprops=arrow_props)
ax.annotate('', xy=(0.5, 0.51), xytext=(0.5, 0.58), arrowprops=arrow_props)

ax.annotate('', xy=(0.28, 0.34), xytext=(0.42, 0.43), arrowprops=arrow_props)
ax.annotate('', xy=(0.72, 0.34), xytext=(0.58, 0.43), arrowprops=arrow_props)

ax.annotate('', xy=(0.35, 0.13), xytext=(0.28, 0.22), arrowprops=arrow_props)
ax.annotate('', xy=(0.65, 0.13), xytext=(0.72, 0.22), arrowprops=arrow_props)

plt.title('Figure 3.1: LocalDrop End-to-End System Architecture and Processing Flow', fontsize=12, fontweight='bold', pad=10)
plt.tight_layout()
plt.savefig('report_assets/fig_flowchart.png')
plt.close()

# 2. Waterfall Model Diagram
fig, ax = plt.subplots(figsize=(8, 6), dpi=200)
ax.axis('off')
stages = ["Requirement Analysis & DWM Scoping", "Dimensional System Designing", "ETL & Schema Implementation", "Integration & SQL Query Testing", "BI Dashboard Deployment", "System Evaluation & Review"]
colors = ['#34495E', '#2980B9', '#1ABC9C', '#F39C12', '#E67E22', '#27AE60']
for i, (stage, col) in enumerate(zip(stages, colors)):
    x = 0.12 + i * 0.11
    y = 0.85 - i * 0.14
    rect = patches.FancyBboxPatch((x, y), 0.38, 0.09, boxstyle="round,pad=0.01", linewidth=1.5, edgecolor='#1C2833', facecolor=col)
    ax.add_patch(rect)
    ax.text(x + 0.19, y + 0.045, stage, ha='center', va='center', fontsize=9, fontweight='bold', color='white')
    if i < len(stages) - 1:
        ax.annotate('', xy=(x + 0.19 + 0.11, y - 0.05), xytext=(x + 0.19, y),
                    arrowprops=dict(arrowstyle="->", lw=1.8, color='#34495E'))

plt.title('Figure 3.2: Waterfall Development Lifecycle for LocalDrop Project', fontsize=11, fontweight='bold', pad=10)
plt.tight_layout()
plt.savefig('report_assets/fig_waterfall.png')
plt.close()

# 3. Gantt Chart
fig, ax = plt.subplots(figsize=(10, 5), dpi=200)
tasks = [
    "Project Charter & Problem Definition",
    "Literature Survey & Tech Selection",
    "Operational Schema & Data Gen",
    "Data Preprocessing & Validation",
    "ETL Pipeline & Warehouse Modeling",
    "Analytical SQL Query Implementation",
    "Classification (DT & NB) Modules",
    "Clustering (K-Means) & Scatter Plot",
    "Association Rule Mining (Apriori)",
    "Flask Web Portal & UI Development",
    "Testing, Verification & Audit",
    "Documentation & Report Finalization"
]
starts = [1, 2, 4, 6, 7, 9, 10, 11, 12, 13, 15, 16]
durations = [2, 3, 3, 2, 3, 2, 2, 2, 2, 3, 2, 2]
y_pos = np.arange(len(tasks))

ax.barh(y_pos, durations, left=starts, align='center', color='#2980B9', edgecolor='#1B4F72', alpha=0.85, height=0.6)
ax.set_yticks(y_pos)
ax.set_yticklabels(tasks, fontsize=8.5, fontweight='bold')
ax.invert_yaxis()  # labels read top-to-bottom
ax.set_xlabel('Project Timeline (Weeks / Phases)', fontsize=10, fontweight='bold')
ax.set_xlim(0, 19)
ax.grid(axis='x', linestyle='--', alpha=0.6)
plt.title('Figure 3.4: Gantt Chart of Project Development Phases', fontsize=11, fontweight='bold', pad=12)
plt.tight_layout()
plt.savefig('report_assets/fig_gantt.png')
plt.close()

# 4. Sequence Diagram
fig, ax = plt.subplots(figsize=(9, 6), dpi=200)
ax.axis('off')
lifelines = [("Web Browser / Client", 0.15), ("Flask Web Server (app.py)", 0.40), ("Data Warehouse (SQLite)", 0.65), ("Data Mining Engine (mining.py)", 0.88)]
for name, x in lifelines:
    ax.text(x, 0.92, name, ha='center', va='center', fontsize=9, fontweight='bold', 
            bbox=dict(boxstyle='square,pad=0.4', facecolor='#EAEDED', edgecolor='#2C3E50'))
    ax.plot([x, x], [0.10, 0.87], 'k--', lw=1.2)

# Messages
msgs = [
    (0.15, 0.40, 0.80, "1. HTTP GET /dashboard, /analytics", True),
    (0.40, 0.65, 0.72, "2. Execute Analytical SQL Queries", True),
    (0.65, 0.40, 0.64, "3. Return Aggregated Query Results", False),
    (0.40, 0.15, 0.56, "4. Render HTML/Chart.js Visualizations", False),
    (0.15, 0.40, 0.46, "5. HTTP GET /data-mining", True),
    (0.40, 0.88, 0.38, "6. Trigger Model Training (DT, NB, KMeans, Apriori)", True),
    (0.88, 0.65, 0.32, "7. Query Dimensional Datasets for Feature Matrices", True),
    (0.65, 0.88, 0.26, "8. Return Clean Feature Data", False),
    (0.88, 0.40, 0.20, "9. Return Evaluated Metrics, Clusters & Rules", False),
    (0.40, 0.15, 0.14, "10. Return Rendered Mining Analytics UI", False)
]

for x1, x2, y, label, is_call in msgs:
    style = "->" if is_call else "-->"
    col = '#1A5276' if is_call else '#27AE60'
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="->" if is_call else "-|>", linestyle='solid' if is_call else 'dashed', lw=1.4, color=col))
    ax.text((x1 + x2)/2, y + 0.02, label, ha='center', va='bottom', fontsize=8, color='#17202A', fontweight='bold' if is_call else 'normal')

plt.title('Figure 3.5: Sequence Diagram Illustrating Request-Response and Mining Workflow', fontsize=11, fontweight='bold', pad=10)
plt.tight_layout()
plt.savefig('report_assets/fig_sequence.png')
plt.close()

# 5. Entity-Relationship (ER) Diagram
fig, ax = plt.subplots(figsize=(10, 6.5), dpi=200)
ax.axis('off')
tables = [
    ("CUSTOMERS", ["customer_id (PK)", "customer_name", "city", "state", "registration_date"], 0.2, 0.8),
    ("SUPPLIERS", ["supplier_id (PK)", "supplier_name", "city", "state", "supplier_rating"], 0.8, 0.8),
    ("PRODUCTS", ["product_id (PK)", "product_name", "category", "supplier_id (FK)", "price", "cost_price", "stock_quantity"], 0.8, 0.25),
    ("ORDERS", ["order_id (PK)", "customer_id (FK)", "product_id (FK)", "supplier_id (FK)", "order_date", "quantity", "order_status"], 0.2, 0.25),
    ("SALES", ["sale_id (PK)", "order_id (FK)", "customer_id (FK)", "product_id (FK)", "supplier_id (FK)", "sale_date", "quantity", "unit_price", "total_amount", "profit"], 0.5, 0.52)
]

for name, cols, x, y in tables:
    h = 0.05 + len(cols) * 0.035
    w = 0.24
    rect = patches.FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="round,pad=0.01", linewidth=1.5, edgecolor='#2C3E50', facecolor='#FDFEFE')
    ax.add_patch(rect)
    header = patches.Rectangle((x - w/2, y + h/2 - 0.045), w, 0.045, facecolor='#2C3E50')
    ax.add_patch(header)
    ax.text(x, y + h/2 - 0.025, name, ha='center', va='center', fontsize=9.5, fontweight='bold', color='white')
    for idx, c in enumerate(cols):
        col_color = '#C0392B' if '(PK)' in c else ('#2980B9' if '(FK)' in c else '#2C3E50')
        ax.text(x - w/2 + 0.015, y + h/2 - 0.065 - idx*0.032, c, ha='left', va='center', fontsize=8, color=col_color, fontweight='bold' if ('(PK)' in c or '(FK)' in c) else 'normal')

# Relationships
ax.annotate('', xy=(0.5, 0.65), xytext=(0.28, 0.8), arrowprops=dict(arrowstyle="-", lw=1.2, color='#7F8C8D'))
ax.annotate('', xy=(0.5, 0.65), xytext=(0.72, 0.8), arrowprops=dict(arrowstyle="-", lw=1.2, color='#7F8C8D'))
ax.annotate('', xy=(0.32, 0.35), xytext=(0.42, 0.45), arrowprops=dict(arrowstyle="-", lw=1.2, color='#7F8C8D'))
ax.annotate('', xy=(0.68, 0.35), xytext=(0.58, 0.45), arrowprops=dict(arrowstyle="-", lw=1.2, color='#7F8C8D'))
ax.annotate('', xy=(0.8, 0.45), xytext=(0.8, 0.68), arrowprops=dict(arrowstyle="-", lw=1.2, color='#7F8C8D'))

plt.title('Figure 3.8: Operational Relational Database Schema (OLTP Entity-Relationship Diagram)', fontsize=11, fontweight='bold', pad=10)
plt.tight_layout()
plt.savefig('report_assets/fig_er.png')
plt.close()

# 6. Star Schema Diagram
fig, ax = plt.subplots(figsize=(9, 6.5), dpi=200)
ax.axis('off')
fact_cols = ["sale_id (PK)", "product_id (FK)", "customer_id (FK)", "supplier_id (FK)", "date_id (FK)", "quantity", "unit_price", "total_amount", "profit"]
rect_f = patches.FancyBboxPatch((0.36, 0.32), 0.28, 0.36, boxstyle="round,pad=0.01", linewidth=2, edgecolor='#C0392B', facecolor='#FDEDEC')
ax.add_patch(rect_f)
ax.add_patch(patches.Rectangle((0.36, 0.63), 0.28, 0.05, facecolor='#C0392B'))
ax.text(0.5, 0.655, "FACT_SALES", ha='center', va='center', fontsize=10, fontweight='bold', color='white')
for i, c in enumerate(fact_cols):
    ax.text(0.38, 0.60 - i*0.032, c, ha='left', va='center', fontsize=8, fontweight='bold' if ('(PK)' in c or '(FK)' in c) else 'normal')

dims = [
    ("DIM_PRODUCT", ["product_id (PK)", "product_name", "category", "price"], 0.5, 0.85, 0.26, 0.17),
    ("DIM_DATE", ["date_id (PK)", "date_full", "day", "month", "quarter", "year"], 0.5, 0.15, 0.26, 0.20),
    ("DIM_CUSTOMER", ["customer_id (PK)", "customer_name", "city", "state"], 0.16, 0.5, 0.26, 0.17),
    ("DIM_SUPPLIER", ["supplier_id (PK)", "supplier_name", "city", "state", "supplier_rating"], 0.84, 0.5, 0.26, 0.19)
]

for name, cols, cx, cy, w, h in dims:
    rect = patches.FancyBboxPatch((cx - w/2, cy - h/2), w, h, boxstyle="round,pad=0.01", linewidth=1.5, edgecolor='#2980B9', facecolor='#EBF5FB')
    ax.add_patch(rect)
    ax.add_patch(patches.Rectangle((cx - w/2, cy + h/2 - 0.04), w, 0.04, facecolor='#2980B9'))
    ax.text(cx, cy + h/2 - 0.02, name, ha='center', va='center', fontsize=9, fontweight='bold', color='white')
    for i, c in enumerate(cols):
        ax.text(cx - w/2 + 0.015, cy + h/2 - 0.06 - i*0.03, c, ha='left', va='center', fontsize=8)

# Connectors to Fact
ax.annotate('', xy=(0.5, 0.68), xytext=(0.5, 0.76), arrowprops=dict(arrowstyle="<->", lw=2, color='#2C3E50'))
ax.annotate('', xy=(0.5, 0.32), xytext=(0.5, 0.25), arrowprops=dict(arrowstyle="<->", lw=2, color='#2C3E50'))
ax.annotate('', xy=(0.36, 0.5), xytext=(0.29, 0.5), arrowprops=dict(arrowstyle="<->", lw=2, color='#2C3E50'))
ax.annotate('', xy=(0.64, 0.5), xytext=(0.71, 0.5), arrowprops=dict(arrowstyle="<->", lw=2, color='#2C3E50'))

plt.title('Figure 4.1: Star Schema Architectural Layout (Denormalized Dimensions)', fontsize=11, fontweight='bold', pad=10)
plt.tight_layout()
plt.savefig('report_assets/fig_star_schema.png')
plt.close()

# 7. Snowflake Schema Diagram
fig, ax = plt.subplots(figsize=(10, 7), dpi=200)
ax.axis('off')

# Fact
rect_f = patches.FancyBboxPatch((0.38, 0.28), 0.24, 0.32, boxstyle="round,pad=0.01", linewidth=2, edgecolor='#C0392B', facecolor='#FDEDEC')
ax.add_patch(rect_f)
ax.add_patch(patches.Rectangle((0.38, 0.55), 0.24, 0.05, facecolor='#C0392B'))
ax.text(0.5, 0.575, "FACT_SALES", ha='center', va='center', fontsize=9.5, fontweight='bold', color='white')
for i, c in enumerate(fact_cols):
    ax.text(0.395, 0.52 - i*0.028, c, ha='left', va='center', fontsize=7.5)

# Normalized Product & Category
rect_p = patches.FancyBboxPatch((0.38, 0.70), 0.24, 0.16, boxstyle="round,pad=0.01", linewidth=1.5, edgecolor='#2980B9', facecolor='#EBF5FB')
ax.add_patch(rect_p)
ax.add_patch(patches.Rectangle((0.38, 0.82), 0.24, 0.04, facecolor='#2980B9'))
ax.text(0.5, 0.84, "DIM_PRODUCT_SF", ha='center', va='center', fontsize=9, fontweight='bold', color='white')
for i, c in enumerate(["product_id (PK)", "product_name", "category_id (FK)", "price"]):
    ax.text(0.395, 0.79 - i*0.028, c, ha='left', va='center', fontsize=7.5)

rect_cat = patches.FancyBboxPatch((0.70, 0.70), 0.22, 0.16, boxstyle="round,pad=0.01", linewidth=1.5, edgecolor='#8E44AD', facecolor='#F4ECF7')
ax.add_patch(rect_cat)
ax.add_patch(patches.Rectangle((0.70, 0.82), 0.22, 0.04, facecolor='#8E44AD'))
ax.text(0.81, 0.84, "DIM_CATEGORY", ha='center', va='center', fontsize=9, fontweight='bold', color='white')
for i, c in enumerate(["category_id (PK)", "category_name"]):
    ax.text(0.715, 0.79 - i*0.028, c, ha='left', va='center', fontsize=7.5)

# Other dims
dims_sf = [
    ("DIM_DATE", ["date_id (PK)", "date_full", "day", "month", "quarter", "year"], 0.5, 0.11, 0.24, 0.16),
    ("DIM_CUSTOMER", ["customer_id (PK)", "customer_name", "city", "state"], 0.16, 0.44, 0.22, 0.16),
    ("DIM_SUPPLIER", ["supplier_id (PK)", "supplier_name", "city", "state", "supplier_rating"], 0.84, 0.44, 0.22, 0.16)
]
for name, cols, cx, cy, w, h in dims_sf:
    rect = patches.FancyBboxPatch((cx - w/2, cy - h/2), w, h, boxstyle="round,pad=0.01", linewidth=1.5, edgecolor='#2980B9', facecolor='#EBF5FB')
    ax.add_patch(rect)
    ax.add_patch(patches.Rectangle((cx - w/2, cy + h/2 - 0.035), w, 0.035, facecolor='#2980B9'))
    ax.text(cx, cy + h/2 - 0.018, name, ha='center', va='center', fontsize=8.5, fontweight='bold', color='white')
    for i, c in enumerate(cols):
        ax.text(cx - w/2 + 0.012, cy + h/2 - 0.055 - i*0.024, c, ha='left', va='center', fontsize=7.5)

# Connectors
ax.annotate('', xy=(0.5, 0.60), xytext=(0.5, 0.70), arrowprops=dict(arrowstyle="<->", lw=1.8, color='#2C3E50'))
ax.annotate('', xy=(0.62, 0.78), xytext=(0.70, 0.78), arrowprops=dict(arrowstyle="<->", lw=1.8, color='#8E44AD'))
ax.annotate('', xy=(0.5, 0.28), xytext=(0.5, 0.19), arrowprops=dict(arrowstyle="<->", lw=1.8, color='#2C3E50'))
ax.annotate('', xy=(0.38, 0.44), xytext=(0.27, 0.44), arrowprops=dict(arrowstyle="<->", lw=1.8, color='#2C3E50'))
ax.annotate('', xy=(0.62, 0.44), xytext=(0.73, 0.44), arrowprops=dict(arrowstyle="<->", lw=1.8, color='#2C3E50'))

plt.title('Figure 4.2: Snowflake Schema with Normalized Product Category Dimension', fontsize=11, fontweight='bold', pad=10)
plt.tight_layout()
plt.savefig('report_assets/fig_snowflake_schema.png')
plt.close()

# 8. High-Res Cluster Scatter Plot
mining_res = run_data_mining()
scatter_data = mining_res['scatter_data']
df_sc = pd.DataFrame(scatter_data)

fig, ax = plt.subplots(figsize=(8, 5.5), dpi=200)
colors = {1: '#E74C3C', 2: '#2ECC71', 3: '#3498DB'}
labels = {1: 'Cluster 1: High-Value Customers (High Orders & Spending)',
          2: 'Cluster 2: Casual Buyers (Low Volume & Infrequent)',
          3: 'Cluster 3: Regular Buyers (Moderate Orders & Value)'}

for c_id in [1, 2, 3]:
    sub = df_sc[df_sc['cluster'] == c_id]
    ax.scatter(sub['x'], sub['y'], color=colors[c_id], label=labels[c_id], s=70, alpha=0.85, edgecolors='black', linewidth=0.8)

# Calculate centroids
for c_id in [1, 2, 3]:
    sub = df_sc[df_sc['cluster'] == c_id]
    if not sub.empty:
        mx, my = sub['x'].mean(), sub['y'].mean()
        ax.scatter(mx, my, color=colors[c_id], s=200, marker='X', edgecolors='black', linewidth=1.5)
        ax.text(mx + 0.15, my + 400, f'Centroid {c_id}', fontsize=8.5, fontweight='bold', color='#1C2833')

ax.set_xlabel('Total Customer Orders (Count)', fontsize=10, fontweight='bold')
ax.set_ylabel('Total Lifetime Spending (₹ INR)', fontsize=10, fontweight='bold')
ax.set_title('Figure 5.6: K-Means Customer Clustering Scatter Plot (k=3)', fontsize=11, fontweight='bold', pad=12)
ax.legend(loc='upper left', fontsize=8.5, frameon=True)
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('report_assets/fig_cluster_scatter.png')
plt.close()

# 9. Monthly Sales Chart
dw = sqlite3.connect('localdrop_warehouse.db')
dw.row_factory = sqlite3.Row
m_data = dw.execute('''SELECT d.year || '-' || printf('%02d', d.month) as month, ROUND(SUM(f.total_amount),2) as rev 
FROM FACT_SALES f JOIN DIM_DATE d ON f.date_id = d.date_id GROUP BY d.year, d.month ORDER BY d.year, d.month''').fetchall()

months = [r['month'] for r in m_data]
revs = [r['rev'] for r in m_data]

fig, ax = plt.subplots(figsize=(9, 4.8), dpi=200)
bars = ax.bar(months, revs, color='#2980B9', edgecolor='#1B4F72', width=0.6, alpha=0.9)
ax.plot(months, revs, color='#E74C3C', marker='o', linewidth=2, markersize=5)
ax.set_xticklabels(months, rotation=45, ha='right', fontsize=8.5)
ax.set_ylabel('Monthly Revenue (₹ INR)', fontsize=10, fontweight='bold')
ax.set_title('Figure 5.1: Monthly Sales Revenue Trend (OLAP Analytical Result)', fontsize=11, fontweight='bold', pad=10)
ax.grid(axis='y', linestyle='--', alpha=0.6)
for bar in bars:
    yval = bar.get_height()
    if yval > 0:
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 1000, f'₹{int(yval):,}', ha='center', va='bottom', fontsize=7, rotation=90)
ax.set_ylim(0, max(revs) * 1.25)
plt.tight_layout()
plt.savefig('report_assets/fig_monthly_trend.png')
plt.close()

print('All diagram assets generated successfully!')
