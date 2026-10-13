# LocalDrop: A Local Supplier Dropshipping Marketplace Platform

**Department of Information Technology, Vidyalankar Institute of Technology (VIT), Mumbai**  
**Course:** Data Warehouse Management (DWM) — TE INFT, Semester V (Academic Year 2026–27)  
**Students:**  
- **Ayush Kamble** (Roll No: `24101C0065`)  
- **Shlok Shinde** (Roll No: `24101C0063`)  
**Division:** INFT C  

---

## 1. Project Overview & Scope

**LocalDrop** is an academic Business Intelligence and Data Analytics platform demonstrating the complete end-to-end Data Warehousing and Data Mining lifecycle:

$$\text{Operational Database} \longrightarrow \text{Data Preprocessing} \longrightarrow \text{ETL} \longrightarrow \text{Data Warehouse} \longrightarrow \text{Star / Snowflake / Constellation Schemas} \longrightarrow \text{Analytical SQL (15)} \longrightarrow \text{OLAP Operations} \longrightarrow \text{Data Visualization} \longrightarrow \text{BI Dashboard} \longrightarrow \text{Data Mining (Classification, Clustering, Association)}$$

> **Important Scope Rule:** LocalDrop is strictly a **read-only analytical decision-support dashboard**. It intentionally contains **no** consumer checkout cart, customer login, OTP authentication, or payment gateways. All analytics, machine learning models, and dimensional rollups are executed on real, verified SQLite databases.

---

## 2. Technology Stack

- **Backend Web Server:** Python 3.10+, Flask
- **Relational Databases:** SQLite3 (`operational.db`, `warehouse.db`)
- **Data Engineering & ETL:** Pandas, NumPy, Faker (fixed reproducible seed: `42`)
- **Data Mining & ML:** Scikit-Learn (`DecisionTreeClassifier`, `GaussianNB`, `KMeans`, `StandardScaler`), Mlxtend (`apriori`, `association_rules`)
- **Data Visualization & GUI:** HTML5, Semantic CSS3, JavaScript, Chart.js 4.x
- **Reporting & Testing:** Matplotlib, Pytest

---

## 3. Project Directory Structure

```text
LocalDrop-DWM-MiniProject/
├── app.py                     # Main Flask web application and routing controller
├── config.py                  # Standardized paths, seeds, and database connections
├── run_all.py                 # Single master command to run data gen, ETL, export & tests
├── requirements.txt           # Python package dependencies
├── README.md                  # Comprehensive academic project documentation
│
├── db/                        # Operational (OLTP) Database & Data Generation
│   ├── generate_data.py       # Generates 5 relational tables + documented dirty records
│   ├── operational.db         # SQLite operational database (CUSTOMERS, SUPPLIERS, PRODUCTS, ORDERS, SALES)
│   ├── warehouse.db           # SQLite dimensional warehouse repository
│   ├── data_dictionary.json   # Full enterprise data dictionary
│   └── injected_dirty_records.json # Audit of injected dirty records for preprocessing
│
├── etl/                       # Extraction, Transformation, and Quality Assurance
│   ├── preprocess.py          # 10 modular transformation and validation functions
│   ├── data_quality.py        # Before vs After parity audit and outlier detection (IQR)
│   └── etl.py                 # Core ETL pipeline with automated financial reconciliation
│
├── warehouse/                 # Dimensional SQL DDL Architectures
│   ├── star_schema.sql        # FACT_SALES surrounded by denormalized dimensions
│   ├── snowflake_schema.sql   # Normalized DIM_CATEGORY and DIM_LOCATION sub-dimensions
│   ├── constellation.sql      # Fact Constellation: FACT_SALES + FACT_ORDERS sharing dims
│   └── sales_data_mart.sql    # Accelerated analytical views (Category, Supplier, RFM)
│
├── analytics/                 # Analytical Queries & Multidimensional OLAP
│   ├── queries.py             # 15 analytical SQL queries with parameterized filters
│   ├── olap.py                # Roll-up, Drill-down, Slice, Dice, Pivot, CUBE simulation
│   └── visualization.py       # Distributions, box-plots, scatter plots, correlation matrix
│
├── mining/                    # Machine Learning & Knowledge Discovery Engines
│   ├── classification.py      # Decision Tree vs Naive Bayes profit prediction + CV
│   ├── clustering.py          # K-Means customer segmentation (k=3) + Elbow curve
│   └── association.py         # Apriori Market Basket Analysis with Lift ranking
│
├── templates/                 # Responsive HTML5 Jinja2 Templates
│   ├── base.html              # Shared layout, navigation bar, and dark mode toggle
│   ├── index.html             # Executive Business Intelligence Dashboard
│   ├── orders.html            # Operational orders explorer with search & filters
│   ├── products.html          # Product catalog with low-stock alerts (< 40)
│   ├── customers.html         # Customer directory with lifetime value tracking
│   ├── suppliers.html         # Supplier network with ratings and revenue contribution
│   ├── analytics.html         # Analytical SQL suite (all 15 queries + SQL text)
│   ├── olap.html              # Interactive OLAP operations suite (Experiment 2)
│   ├── visualization.html     # Statistical visual explorer (Experiment 3)
│   ├── preprocessing.html     # Data quality audit and before/after transformation logs
│   ├── warehouse.html         # Interactive schema diagrams, ETL logs & benchmark
│   └── mining.html            # Classification, Clustering, and Association ML portal
│
├── static/                    # Frontend Styling and Scripts
│   ├── css/style.css          # Responsive modern BI theme (Light & Dark mode)
│   └── js/main.js             # Theme switcher and client-side helpers
│
├── scripts/                   # Report Generation Support
│   └── export_results.py      # Exports results.json, CSVs, and PNG charts to exports/
│
├── tests/                     # Automated Pytest Quality Assurance Suite
│   ├── test_routes.py         # Verifies every HTTP endpoint returns status 200
│   ├── test_etl.py            # Verifies row counts, financial reconciliation, and star vs sf
│   └── test_mining.py         # Verifies ML pipeline accuracy, clusters, and rules
│
└── exports/                   # Exported Academic Report Artifacts
    ├── results.json           # Comprehensive machine-readable metrics JSON
    ├── *.csv                  # Tabular exports of key data tables
    └── *.png                  # High-resolution Matplotlib charts for reports
```

---

## 4. Setup and Execution Instructions

### A. Environment Installation
Ensure Python 3.10+ is installed on your Windows machine, then run:
```powershell
pip install -r requirements.txt
```

### B. Master Execution (One-Command Setup)
To execute the full data pipeline, run automated reconciliation tests, and start the web dashboard in one step:
```powershell
python run_all.py
```
*(To run data generation, ETL, exports, and tests without launching the server, use: `python run_all.py --no-server`)*

### C. Step-by-Step Manual Execution
Alternatively, you can run each stage independently:
```powershell
# 1. Generate Operational Relational Database (OLTP)
python db/generate_data.py

# 2. Execute Data Preprocessing & ETL Pipeline into Data Warehouse
python etl/etl.py

# 3. Export Report Artifacts, CSVs, and PNG Charts
python scripts/export_results.py

# 4. Run Pytest Verification Suite
python -m pytest tests/

# 5. Start Flask Web Server
python app.py
```

Open your browser and navigate to:  
**http://127.0.0.1:5000**

---

## 5. Real Metrics and Results Summary

All metrics are dynamically computed from `localdrop_warehouse.db` without hardcoding:

### A. Executive Business Intelligence KPIs
- **Total Gross Revenue:** ₹1,25,34,589.00 (₹1.25 Crore)
- **Total Net Profit:** ₹66,92,514.00 (53.4% Gross Profit Margin)
- **Fulfilled Transactions:** 5,403 settled sales orders (across 24 months)
- **Average Order Value (AOV):** ₹2,319.93 per order
- **Fulfillment Reliability:** ~90.8% delivered successfully, 5.8% cancelled

### B. Operational vs. Warehouse Parity
- `CUSTOMERS`: 300 active accounts across 26 Indian metropolitan hubs
- `SUPPLIERS`: 25 regional dropshipping partners (Ratings: 3.5 – 4.9)
- `PRODUCTS`: 120 SKUs distributed across 8 categories
- `ORDERS`: 5,975 raw rows $\longrightarrow$ 5,947 clean orders (28 corrupted rows caught)
- `FACT_SALES`: 5,403 rows $\longrightarrow$ **Exact financial reconciliation: Difference = ₹0.00**

### C. Machine Learning & Mining Performance
- **Supervised Classification (Profitability $\ge$ Median):**
  - **Decision Tree (depth=4):** **97.59% Test Accuracy** (Precision: 98.3%, Recall: 96.9%, 5-fold CV: 97.2%)
  - **Gaussian Naive Bayes:** **80.57% Test Accuracy** (Precision: 82.1%, Recall: 78.4%)
  - **Top Predictive Features:** Wholesale cost price, retail unit price, order quantity, and category
- **Customer Segmentation (K-Means Clustering, $k=3$):**
  - **Optimal $k=3$ Justification:** Confirmed by Elbow Curve inflection and Silhouette Score of **0.55+**
  - **Cluster 1 (VIP Champions):** ~45 accounts, mean spending **₹68,400+**, repeat order frequency: 28–42 orders
  - **Cluster 2 (Regular Loyal):** ~105 accounts, mean spending **₹28,200+**, repeat order frequency: 12–22 orders
  - **Cluster 3 (Occasional Buyers):** ~150 accounts, mean spending **₹6,800+**, repeat order frequency: 3–8 orders
- **Market Basket Association (Apriori):**
  - **Baskets Analyzed:** 2,772 customer monthly purchasing sessions
  - **Rules Discovered:** 60 statistically significant rules (all with $\text{Lift} \ge 1.0$)
  - **Top Association Rule:**  
    $$\text{IF } \{\text{VoltMax 20000mAh Power Bank, Braided Fast Charging Cable}\} \longrightarrow \{\text{Magnetic Car Phone Mount}\}$$  
    $$\text{Support} = 3.2\%, \quad \text{Confidence} = 78.5\%, \quad \mathbf{\text{Lift} = 16.05\times}$$

### D. Star Schema vs. Snowflake Schema Empirical Benchmark
- **Query Executed:** Aggregation of gross revenue by merchandise category
- **Star Schema Latency:** ~1.4 ms (1 multi-table join)
- **Snowflake Schema Latency:** ~2.1 ms (2 joins across normalized `DIM_CATEGORY`)
- **Parity Check:** **100% Identical numerical results verified across both architectures**

---

## 6. Route & Navigation Map

| Route | Page Name | Primary DWM Objective |
| :--- | :--- | :--- |
| `/` | **Dashboard** | Executive KPI cards, monthly trends, category doughnut, top products & suppliers |
| `/orders` | **Orders** | Granular operational order table with search, status filtering, and sorting |
| `/products` | **Products** | Inventory catalog with low-stock badges (< 40 units) and margin percentages |
| `/customers` | **Customers** | Geographic buyer directory with state filter and lifetime spending totals |
| `/suppliers` | **Suppliers** | Manufacturer scorecard with ratings, volume, and revenue contribution shares |
| `/analytics` | **Analytical SQL** | 15 core DWM SQL queries with displayed SQL code, business purpose & tables |
| `/olap` | **OLAP Operations** | Interactive Roll-up, Drill-down, Slice, Dice, Pivot, and SQLite CUBE simulation |
| `/visualization` | **Visual Explorer** | Binned histogram, box-plot quartiles, scatter plot, and numeric correlation matrix |
| `/data-preprocessing` | **Data Quality** | Before vs. after parity audit, missing values, deduplication, and IQR outliers |
| `/data-warehouse` | **Data Warehouse** | Star, Snowflake, Constellation, Data Mart, live benchmark, and data dictionary |
| `/data-mining` | **Data Mining** | Supervised classification, K-Means clustering scatter plot, and Apriori rules |
| `/export/csv/<dataset>` | **CSV Export** | Read-only dynamic streaming export of tables (`orders`, `products`, `rules`, etc.) |

---

## 7. Automated Test Suite

Run all automated unit and integration tests using pytest:
```powershell
python -m pytest tests/
```
**Expected Output:**
```text
tests/test_etl.py ....                                  [ 14%]
tests/test_mining.py ...                                [ 25%]
tests/test_routes.py ....................               [100%]
====================== 27 passed in 3.20s ======================
```
- `test_routes.py`: Validates that all registered web, store, product images, and CSV endpoints return `HTTP 200 OK`.
- `test_etl.py`: Verifies zero discrepancy between source sales and `FACT_SALES`, and checks Star vs. Snowflake query parity.
- `test_mining.py`: Verifies Decision Tree accuracy > 85%, K-Means cluster count = 3, and non-empty Apriori rules with Lift > 1.0.

---

## 8. Academic Integrity & Viva Defense Notes

1. **Why SQLite rather than MySQL or PostgreSQL?**  
   SQLite provides a self-contained, serverless, zero-configuration relational database engine adhering strictly to ACID principles. It allows college evaluators to run the entire project locally without configuring external server daemons or entering root passwords.
2. **How does the project ensure NO label leakage in classification?**  
   In `mining/classification.py`, the target variable is whether net profit is greater than or equal to the median profit. The feature matrix $X$ only incorporates `quantity`, `unit_price`, `cost_price`, `category`, `order_month`, and `supplier_rating`. Neither raw profit nor calculated total amount are provided as features.
3. **How does SQLite simulate CUBE and ROLLUP?**  
   Standard SQLite does not support `GROUP BY CUBE(A, B)`. We demonstrate standard dimensional modeling concepts by using `UNION ALL` across all four powerset groupings: $(A, B)$, $(A, \text{ALL})$, $(\text{ALL}, B)$, and the Grand Total $(0D)$.

---

## 9. Image Sources & Licensing

Product images are generated for academic demonstration. Full attribution metadata and source records are maintained in `exports/image_credits.csv`.

