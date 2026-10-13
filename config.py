"""
LocalDrop: Configuration and Environment Setup
Project: LocalDrop - Local Supplier Dropshipping Marketplace Platform
Institute: Vidyalankar Institute of Technology, Department of Information Technology
Students: Ayush Kamble (24101C0065), Shlok Shinde (24101C0063), Division INFT C
"""

import os
import sqlite3

# Base directories
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, "db")
WAREHOUSE_SQL_DIR = os.path.join(BASE_DIR, "warehouse")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

# Database file paths
OPERATIONAL_DB_PATH = os.path.join(DB_DIR, "operational.db")
WAREHOUSE_DB_PATH = os.path.join(DB_DIR, "warehouse.db")
INJECTED_DIRTY_LOG_PATH = os.path.join(DB_DIR, "injected_dirty_records.json")
DATA_DICTIONARY_PATH = os.path.join(DB_DIR, "data_dictionary.json")

# Fixed random seed for complete academic reproducibility
RANDOM_SEED = 42

# Ensure directories exist
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)


def get_operational_db():
    """Establish connection to the Operational Database (OLTP)."""
    conn = sqlite3.connect(OPERATIONAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_warehouse_db():
    """Establish connection to the Data Warehouse (OLAP)."""
    conn = sqlite3.connect(WAREHOUSE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
