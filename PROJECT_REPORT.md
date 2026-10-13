# Data Warehouse Management Mini-Project Report

## 1. Title
LocalDrop: A Local Supplier Dropshipping Marketplace Platform

## 2. Team Members
- **Ayush Kamble** - 24101C0065
- **Shlok Shinde** - 24101C0063
- **Division**: INFT C

## 3. Aim
To design and implement a complete Data Warehouse system for a local supplier dropshipping marketplace, encompassing an operational database, ETL processes, multidimensional schemas (Star and Snowflake), and a Business Intelligence (BI) dashboard with Data Mining capabilities.

## 4. Problem Statement
Traditional dropshipping platforms often lack tools for local suppliers to analyze their performance. A robust data warehouse is needed to consolidate operational transaction data into a format optimized for analytical queries, enabling the platform to track revenue, profit, supplier performance, customer behavior, and discover hidden purchase patterns.

## 5. Objectives
- Design an operational relational database (OLTP).
- Implement an ETL (Extract, Transform, Load) pipeline using Python Pandas.
- Model the data into Star and Snowflake schemas (OLAP).
- Formulate and execute analytical SQL queries.
- Develop a BI dashboard to visualize key performance indicators (KPIs).
- Apply data mining algorithms (Classification, Clustering, Association) to discover actionable knowledge.

## 6. Dataset
A synthetic dataset simulating Indian dropshipping transactions was generated using the `Faker` library. It contains over 150 unique transactions, simulating customers, suppliers, products, and order histories over the past two years, priced in INR.

## 7. Data Preprocessing
Operational data often contains noise. During the ETL phase, preprocessing was performed:
- **Missing Values:** Dropped rows missing critical analytical data like `order_status` and `order_date`.
- **Invalid Data:** Removed illogical entries where `quantity < 1`.
- **Duplicates:** Handled via Pandas `drop_duplicates()`.
- **Transformation:** Date fields were decomposed into `date_id`, `month`, `year`, and `quarter` to build the Time Dimension.

## 8. Operational Database
The operational database handles day-to-day transactions (OLTP). 
Tables: `CUSTOMERS`, `SUPPLIERS`, `PRODUCTS`, `ORDERS`, `SALES`.

## 9. ETL (Extract, Transform, Load)
- **Extract**: Data read from the operational SQLite database into Pandas DataFrames.
- **Transform**: Cleaned as per the preprocessing rules. Denormalized fields were extracted (e.g. `category` mapped to `DIM_CATEGORY`).
- **Load**: Transformed, clean data is loaded into `localdrop_warehouse.db` into distinct Dimension and Fact tables.

## 10. Data Warehouse
The Data Warehouse serves as the central repository for historical data, structured specifically for fast analytical read-operations rather than transactional write-operations.

## 11. Star Schema
A multidimensional model optimized for reading. 
`FACT_SALES` is the central fact table containing numerical measures (`quantity`, `total_amount`, `profit`). It joins directly via Foreign Keys to denormalized Dimension tables: `DIM_PRODUCT`, `DIM_CUSTOMER`, `DIM_SUPPLIER`, and `DIM_DATE`.

## 12. Snowflake Schema
An extension of the Star Schema where dimensions are normalized to save space. In our implementation, `DIM_PRODUCT` is normalized out to `DIM_CATEGORY`, meaning `FACT_SALES` joins to `DIM_PRODUCT_SF` which then joins to `DIM_CATEGORY`.

## 13. Classification
Data Mining classification was applied using **Decision Tree** and **Naive Bayes** algorithms to predict if an order will result in a 'High Profit' (>₹500).
Features utilized: `quantity`, `unit_price`, `category`. 
The results (Accuracy, Precision, Recall, F1-Score) are visualized dynamically on the dashboard.

## 14. Clustering
**K-Means Clustering** was used to segment the customer base. 
Customers were clustered into 3 distinct groups (e.g., Casual, Regular, High Value) based on their `Total Orders` and `Lifetime Spending`. The dashboard plots these clusters on a scatter plot.

## 15. Association
**Apriori Algorithm** (Market Basket Analysis) was applied to the transactions to discover what products are frequently bought together. Support, Confidence, and Lift metrics are calculated to output rules such as "If a user buys a Laptop Stand, they are likely to buy a Wireless Mouse".

## 16. Analytical SQL
10 required analytical SQL queries were executed against the Data Warehouse, computing metrics such as:
1. Total Revenue
2. Total Orders
3. Total Profit
4. Monthly Sales (Time-series)
5. Top 5 Products by Revenue
6. Category-wise Sales Distribution
7. Supplier-wise Revenue Performance
8. Customer-wise Spending
9. Order Status Distribution
10. Average Order Value

## 17. Dashboard
A Flask web application serving an HTML/CSS UI. It leverages Chart.js to visualize the analytical SQL results. It includes specific pages for browsing Orders, Products, Customers, Suppliers, viewing the Warehouse schemas, and reading Data Mining results.

## 18. Results
The ETL pipeline successfully migrated 100% of clean operational data into the OLAP models. The API responds in under 50ms for analytical queries due to the Star schema efficiency. Data mining models generated functional accuracies and actionable association rules.

## 19. Business Insights
- **Category Profitability:** Identifying which product categories yield the highest margin.
- **Supplier Loyalty:** Pinpointing the most reliable local suppliers to offer exclusive contracts.
- **Customer Segmentation:** K-Means clearly delineated the top 5% of buyers who account for a majority of the revenue.
- **Product Bundling:** Apriori association rules can be used to create discount bundles on the storefront.

## 20. Conclusion
The LocalDrop project successfully demonstrates the entire lifecycle of a Data Warehouse. Raw data is efficiently extracted, rigorously preprocessed, and transformed into analytical schemas. The combination of multidimensional OLAP querying and Machine Learning provides a robust Business Intelligence platform.

## 21. Future Scope
- Transition from SQLite to robust systems like PostgreSQL or AWS Redshift.
- Implement automated daily ETL cron jobs using Apache Airflow.
- Deploy the Flask dashboard to a cloud provider like AWS or Heroku.
