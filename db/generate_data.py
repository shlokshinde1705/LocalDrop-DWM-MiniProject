"""
LocalDrop: Operational Database Generator (OLTP)
Generates realistic, reproducible synthetic data for Indian Dropshipping Marketplace.
Creates operational.db with exactly 5 relational tables:
  1. CUSTOMERS
  2. SUPPLIERS
  3. PRODUCTS
  4. ORDERS
  5. SALES
Injects documented anomalies for Data Preprocessing and Quality verification.
"""

import os
import sys
import json
import random
import sqlite3
from datetime import datetime, timedelta
from faker import Faker

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

def init_operational_db():
    """Create schema for operational.db with 5 tables, PK/FK constraints, and indexes."""
    if os.path.exists(config.OPERATIONAL_DB_PATH):
        try:
            os.remove(config.OPERATIONAL_DB_PATH)
        except Exception:
            pass

    conn = sqlite3.connect(config.OPERATIONAL_DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    # Drop existing tables
    cur.executescript("""
        DROP TABLE IF EXISTS SALES;
        DROP TABLE IF EXISTS ORDERS;
        DROP TABLE IF EXISTS PRODUCTS;
        DROP TABLE IF EXISTS SUPPLIERS;
        DROP TABLE IF EXISTS CUSTOMERS;

        CREATE TABLE CUSTOMERS (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            city TEXT,
            state TEXT,
            registration_date DATE NOT NULL
        );

        CREATE TABLE SUPPLIERS (
            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            supplier_rating REAL NOT NULL
        );

        CREATE TABLE PRODUCTS (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            supplier_id INTEGER NOT NULL,
            price REAL NOT NULL,
            cost_price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL,
            FOREIGN KEY (supplier_id) REFERENCES SUPPLIERS(supplier_id)
        );

        CREATE TABLE ORDERS (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            supplier_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            order_status TEXT,
            FOREIGN KEY (customer_id) REFERENCES CUSTOMERS(customer_id),
            FOREIGN KEY (product_id) REFERENCES PRODUCTS(product_id),
            FOREIGN KEY (supplier_id) REFERENCES SUPPLIERS(supplier_id)
        );

        CREATE TABLE SALES (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            supplier_id INTEGER NOT NULL,
            sale_date DATE NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_amount REAL NOT NULL,
            profit REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES ORDERS(order_id),
            FOREIGN KEY (customer_id) REFERENCES CUSTOMERS(customer_id),
            FOREIGN KEY (product_id) REFERENCES PRODUCTS(product_id),
            FOREIGN KEY (supplier_id) REFERENCES SUPPLIERS(supplier_id)
        );

        -- Performance Indexes on Foreign Keys
        CREATE INDEX idx_products_supplier ON PRODUCTS(supplier_id);
        CREATE INDEX idx_orders_customer ON ORDERS(customer_id);
        CREATE INDEX idx_orders_product ON ORDERS(product_id);
        CREATE INDEX idx_orders_supplier ON ORDERS(supplier_id);
        CREATE INDEX idx_orders_date ON ORDERS(order_date);
        CREATE INDEX idx_sales_order ON SALES(order_id);
        CREATE INDEX idx_sales_customer ON SALES(customer_id);
        CREATE INDEX idx_sales_product ON SALES(product_id);
        CREATE INDEX idx_sales_supplier ON SALES(supplier_id);
        CREATE INDEX idx_sales_date ON SALES(sale_date);
    """)

    conn.commit()
    conn.close()
    print("Operational database schema initialized successfully.")


def generate_operational_data():
    """Generate realistic synthetic data with seasonal trends and injected dirty records."""
    random.seed(config.RANDOM_SEED)
    fake = Faker('en_IN')
    Faker.seed(config.RANDOM_SEED)

    conn = sqlite3.connect(config.OPERATIONAL_DB_PATH)
    cur = conn.cursor()

    # Major Indian Cities and States
    indian_locations = [
        ('Mumbai', 'Maharashtra'), ('Pune', 'Maharashtra'), ('Nagpur', 'Maharashtra'),
        ('Nashik', 'Maharashtra'), ('Bengaluru', 'Karnataka'), ('Mysuru', 'Karnataka'),
        ('Hyderabad', 'Telangana'), ('Warangal', 'Telangana'), ('Chennai', 'Tamil Nadu'),
        ('Coimbatore', 'Tamil Nadu'), ('Kolkata', 'West Bengal'), ('Siliguri', 'West Bengal'),
        ('Delhi', 'Delhi'), ('Ahmedabad', 'Gujarat'), ('Surat', 'Gujarat'),
        ('Vadodara', 'Gujarat'), ('Jaipur', 'Rajasthan'), ('Udaipur', 'Rajasthan'),
        ('Lucknow', 'Uttar Pradesh'), ('Kanpur', 'Uttar Pradesh'), ('Kochi', 'Kerala'),
        ('Thiruvananthapuram', 'Kerala'), ('Indore', 'Madhya Pradesh'), ('Bhopal', 'Madhya Pradesh'),
        ('Chandigarh', 'Punjab'), ('Patna', 'Bihar')
    ]

    # 1. GENERATE CUSTOMERS (300 records)
    print("Generating 300 customers...")
    customers_data = []
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 9, 30)
    days_range = (end_date - start_date).days

    for cid in range(1, 301):
        name = fake.name()
        loc = random.choice(indian_locations)
        reg_days = random.randint(0, min(days_range - 60, 500))
        reg_date = (start_date + timedelta(days=reg_days)).strftime('%Y-%m-%d')
        customers_data.append((name, loc[0], loc[1], reg_date))

    cur.executemany("""
        INSERT INTO CUSTOMERS (customer_name, city, state, registration_date)
        VALUES (?, ?, ?, ?)
    """, customers_data)

    # 2. GENERATE SUPPLIERS (25 records)
    print("Generating 25 suppliers...")
    supplier_names = [
        "Aarav Electronics Hub", "Bharat Retail & Tech", "Chirag Office Solutions",
        "Deccan Gadgets & Cables", "Eastern Craft & Living", "Frontier Travel Gear",
        "Godavari Lifestyle Goods", "Himalaya Fitness Equipment", "Indus Digital Supply",
        "Jaipur Royal Furnishings", "Kalyan Electronics Co", "Lotus Home Appliances",
        "Maratha Tech Accessories", "Nilgiri Herbal & Wellness", "Omkar Sports Emporium",
        "Pragati Modern Stationery", "Quality Dropship India", "Rajdhani Mobile Care",
        "Sahyadri Consumer Direct", "Tirupati Household Supplies", "Utsav Festive Imports",
        "Vardhaman Industrial Retail", "Western Cargo Drop", "Zenith Audio & Power",
        "Konkan Express Suppliers"
    ]
    suppliers_data = []
    for sid, sname in enumerate(supplier_names, start=1):
        loc = random.choice(indian_locations)
        # Star suppliers have 4.7-4.9, regular have 3.6-4.6, a couple 3.2-3.5
        if sid in [1, 4, 8, 13, 24]:
            rating = round(random.uniform(4.7, 4.9), 1)
        else:
            rating = round(random.uniform(3.5, 4.6), 1)
        suppliers_data.append((sname, loc[0], loc[1], rating))

    cur.executemany("""
        INSERT INTO SUPPLIERS (supplier_name, city, state, supplier_rating)
        VALUES (?, ?, ?, ?)
    """, suppliers_data)

    # 3. GENERATE PRODUCTS (120 products across 8 categories = 15 per category)
    print("Generating 120 products across 8 categories...")
    catalog_templates = {
        'Electronics': [
            ("Apex Pro Smart Watch", 1800, 3499),
            ("Sonic Wireless Bluetooth Earbuds", 750, 1699),
            ("VoltMax 20000mAh Power Bank", 650, 1299),
            ("Crystal HD USB Webcam", 900, 1850),
            ("Noise-Cancelling Studio Headset", 1400, 2799),
            ("Mini Portable Bluetooth Speaker", 500, 1099),
            ("AeroFit Pulse Fitness Band", 950, 1999),
            ("Ultra-Slim 7-in-1 USB-C Hub", 450, 999),
            ("RGB Backlit Mechanical Keyboard", 1200, 2499),
            ("Silent Optical Wireless Mouse", 280, 599),
            ("Fast Wireless Charging Pad 15W", 380, 799),
            ("Smart Wi-Fi Security Cam", 1350, 2699),
            ("Universal International Travel Adapter", 320, 699),
            ("Dual-Port 65W GaN Fast Charger", 780, 1599),
            ("Digital Voice Recorder Pen", 850, 1750)
        ],
        'Mobile Accessories': [
            ("Armor MagSafe Phone Case", 150, 399),
            ("Tempered Glass Screen Guard (Pack of 3)", 90, 249),
            ("Braided Fast Charging Type-C Cable", 110, 299),
            ("Aluminum Desk Phone Stand", 140, 349),
            ("Magnetic Dashboard Car Phone Mount", 190, 449),
            ("Extendable Bluetooth Selfie Stick Tripod", 320, 699),
            ("Waterproof Mobile Pouch Bag", 80, 199),
            ("3.5mm Aux Audio Converter Cable", 70, 179),
            ("Camera Lens Protector Glass", 60, 149),
            ("Phone Ring Grip & Kickstand", 50, 129),
            ("Multi-Device Braided 3-in-1 Cable", 180, 429),
            ("Silicone Cable Organizer Clips", 40, 99),
            ("OTG USB 3.0 Adapter Plug", 65, 159),
            ("Wireless Neckband Earphones", 450, 999),
            ("Anti-Dust Mobile Speaker Mesh", 35, 89)
        ],
        'Home & Office': [
            ("Ergonomic Aluminum Laptop Stand", 420, 899),
            ("Adjustable Eye-Care LED Desk Lamp", 550, 1199),
            ("Large PU Leather Desk Mat Mouse Pad", 250, 599),
            ("Multi-Tier Wooden Desktop Organizer", 350, 799),
            ("Ergonomic Memory Foam Lumbar Cushion", 480, 999),
            ("Footrest Ergonomic Rocking Stool", 650, 1399),
            ("Aroma Diffuser Ultrasonic Humidifier", 520, 1149),
            ("Digital Alarm Clock with Temperature", 220, 499),
            ("Cable Management Box Organizer", 200, 449),
            ("Monitor Screen Light Bar", 850, 1899),
            ("Laptop Cooling Pad with 5 Fans", 620, 1299),
            ("Mini Desktop Dust Vacuum Cleaner", 190, 429),
            ("Under-Desk Headphone Hanger Mount", 110, 249),
            ("Magnetic Whiteboard with Marker Set", 280, 649),
            ("Wall Hanging Key & Mail Holder", 160, 379)
        ],
        'Fitness & Sports': [
            ("Non-Slip TPE Eco Yoga Mat 6mm", 450, 999),
            ("Fabric Resistance Booty Bands Set", 200, 499),
            ("Adjustable Speed Jump Rope Steel Cable", 120, 299),
            ("Push-Up Board Color-Coded 14-in-1", 380, 849),
            ("Deep Tissue Muscle Massage Gun", 1250, 2799),
            ("Neoprene Hex Dumbbells Pair 3kg", 600, 1299),
            ("Gym Shaker Protein Bottle with Blender", 160, 399),
            ("Sweat-Resistant Sports Armband", 110, 249),
            ("Microfiber Quick-Dry Gym Towel", 130, 299),
            ("High-Density Foam Roller 45cm", 340, 749),
            ("Grip Strength Trainer Hand Squeezer", 90, 229),
            ("Breathable Padded Weightlifting Gloves", 180, 399),
            ("Ab Roller Wheel with Knee Mat", 280, 599),
            ("Reflective Running Hydration Waist Belt", 190, 429),
            ("Ankle Weights Set 1kg Pair", 290, 649)
        ],
        'Kitchen & Dining': [
            ("Stainless Steel Insulated Water Bottle 1L", 320, 749),
            ("Automatic Electric Kettle 1.8L", 550, 1199),
            ("Manual French Press Coffee Plunger", 420, 899),
            ("Digital Food Kitchen Weight Scale", 280, 599),
            ("Silicone Cooking Utensils Set of 10", 380, 849),
            ("Herb Scissors 5-Blade with Cover", 110, 249),
            ("Vegetable Chopper Dicer 12-in-1", 450, 999),
            ("Reusable Silicone Food Storage Bags", 190, 449),
            ("Oil Dispenser Glass Bottle Non-Drip", 140, 329),
            ("Ceramic Coffee Mug with Wooden Lid", 160, 369),
            ("Stainless Steel Bento Lunch Box", 390, 849),
            ("Manual Citrus Juicer Hand Squeezer", 120, 279),
            ("Bamboo Cutting Board Large", 260, 599),
            ("Double-Wall Glass Tumbler Pair", 220, 499),
            ("Stainless Steel Straws Set with Brush", 60, 149)
        ],
        'Travel & Luggage': [
            ("Waterproof Anti-Theft Laptop Backpack", 850, 1899),
            ("Memory Foam Neck Travel Pillow Set", 280, 649),
            ("Packing Cubes Compression Set of 6", 360, 799),
            ("Compact Travel Umbrella Windproof", 240, 549),
            ("Digital Luggage Hanging Weight Scale", 170, 399),
            ("Leather Passport Holder Travel Wallet", 190, 449),
            ("TSA Approved Cable Luggage Lock Pair", 130, 299),
            ("Foldable Lightweight Duffle Bag 35L", 320, 699),
            ("Toiletry Organizer Hanging Kit Bag", 260, 599),
            ("Hard EVA Electronics Organizer Case", 210, 479),
            ("Shoe Storage Travel Bags Pack of 4", 90, 219),
            ("RFID Blocking Slim Money Clip Wallet", 150, 349),
            ("Travel Laundry Bag Wash Pouch", 80, 189),
            ("Sleep Eye Mask 3D Contoured with Plugs", 95, 229),
            ("Mini First Aid Emergency Pouch", 110, 269)
        ],
        'Personal Care': [
            ("Sonic Rechargeable Electric Toothbrush", 650, 1399),
            ("Facial Jade Roller & Gua Sha Set", 180, 429),
            ("Cordless Hair & Beard Trimmer Set", 520, 1149),
            ("Ionic Hair Dryer Foldable 1400W", 750, 1599),
            ("Nail Care Grooming Kit Stainless Steel", 160, 369),
            ("Hot Steam Facial Sauna Vaporizer", 340, 749),
            ("Organic Bamboo Charcoal Floss Sticks", 70, 169),
            ("Compact LED Lighted Pocket Makeup Mirror", 140, 329),
            ("Electric Foot Callus Dead Skin Remover", 380, 829),
            ("Natural Bristle Dry Body Skin Brush", 150, 349),
            ("Aromatherapy Essential Oil Roll-On", 120, 279),
            ("Satin Silk Sleep Cap Hair Bonnet", 110, 259),
            ("Beard Comb & Wooden Brush Duo", 130, 299),
            ("Electric Heated Eyelash Curler", 190, 449),
            ("Reusable Makeup Remover Bamboo Pads", 90, 219)
        ],
        'Stationery': [
            ("Hardcover Dotted Bullet Journal Notebook", 190, 449),
            ("Dual Tip Brush Pen Calligraphy Set of 12", 280, 629),
            ("Pastel Aesthetic Highlighter Pens Set of 6", 110, 249),
            ("Retractable Gel Ink Pens 0.5mm Pack of 10", 140, 329),
            ("Vintage Washi Tape Decorative Rolls 10x", 120, 279),
            ("Sticky Notes Memo Cube 400 Sheets", 80, 189),
            ("Metal Wire Mesh Magazine Holder", 210, 469),
            ("Heavy Duty Desktop Tape Dispenser", 130, 299),
            ("Rotating Acrylic Pen Holder Stand", 160, 379),
            ("Stapler with 1000 Staples & Remover", 115, 269),
            ("Artisan Wooden Bookmark Handcrafted", 60, 149),
            ("Paper Clips & Binder Clamps Rose Gold Set", 95, 229),
            ("Mechanical Pencil Set with Refill Leads", 135, 309),
            ("Weekly Productivity Desk Planner Pad", 175, 399),
            ("Precision Metal Paper Craft Scissors", 90, 219)
        ]
    }

    products_data = []
    pid = 1
    for category, items in catalog_templates.items():
        for name, cost, price in items:
            supplier_id = random.randint(1, 25)
            # Give star suppliers more catalog assignments
            if random.random() < 0.4:
                supplier_id = random.choice([1, 4, 8, 13, 24])
            stock = random.randint(30, 450)
            # A few items have intentional low stock for UI testing (< 40)
            if pid in [7, 23, 44, 76, 102]:
                stock = random.randint(5, 25)
            products_data.append((name, category, supplier_id, float(price), float(cost), stock))
            pid += 1

    cur.executemany("""
        INSERT INTO PRODUCTS (product_name, category, supplier_id, price, cost_price, stock_quantity)
        VALUES (?, ?, ?, ?, ?, ?)
    """, products_data)

    # Fetch products to memory for fast order generation
    cur.execute("SELECT product_id, product_name, category, supplier_id, price, cost_price FROM PRODUCTS")
    products_list = cur.fetchall()
    prod_map = {p[0]: p for p in products_list}

    # Identify Co-Purchase Bundles (Product IDs)
    # We will query product IDs for targeted bundling
    cur.execute("SELECT product_id, product_name FROM PRODUCTS")
    pname_to_id = {row[1]: row[0] for row in cur.fetchall()}

    bundle_groups = [
        # Bundle 1: Laptop Office Kit
        [pname_to_id.get("Ergonomic Aluminum Laptop Stand", 31),
         pname_to_id.get("Silent Optical Wireless Mouse", 10),
         pname_to_id.get("Ultra-Slim 7-in-1 USB-C Hub", 8)],
        # Bundle 2: Smart Fitness Wearables
        [pname_to_id.get("Apex Pro Smart Watch", 1),
         pname_to_id.get("Sonic Wireless Bluetooth Earbuds", 2),
         pname_to_id.get("AeroFit Pulse Fitness Band", 7)],
        # Bundle 3: Desk Stationery Synergy
        [pname_to_id.get("Adjustable Eye-Care LED Desk Lamp", 32),
         pname_to_id.get("Hardcover Dotted Bullet Journal Notebook", 106),
         pname_to_id.get("Multi-Tier Wooden Desktop Organizer", 34)],
        # Bundle 4: Active Workout Gear
        [pname_to_id.get("Non-Slip TPE Eco Yoga Mat 6mm", 46),
         pname_to_id.get("Stainless Steel Insulated Water Bottle 1L", 61),
         pname_to_id.get("Gym Shaker Protein Bottle with Blender", 52)],
        # Bundle 5: Mobile Travel Essentials
        [pname_to_id.get("VoltMax 20000mAh Power Bank", 3),
         pname_to_id.get("Braided Fast Charging Type-C Cable", 18),
         pname_to_id.get("Magnetic Dashboard Car Phone Mount", 20)]
    ]

    # 4. GENERATE ORDERS (5,000 realistic orders spanning Oct 2024 - Oct 2026)
    print("Generating 5,000 orders across 24 months with seasonal distribution...")
    orders_data = []
    statuses = ['Delivered', 'Delivered', 'Delivered', 'Delivered', 'Delivered',
                'Delivered', 'Delivered', 'Shipped', 'Processing', 'Cancelled', 'Returned']

    # Define customer cohorts for clear K-Means customer segmentation
    # VIP: Customers 1..45 (high volume & spend, 25-45 orders each)
    # Regular: Customers 46..150 (medium volume, 8-20 orders each)
    # Occasional: Customers 151..300 (low volume, 2-6 orders each)
    customer_order_distribution = []
    for c in range(1, 46):
        customer_order_distribution.extend([c] * random.randint(28, 42))
    for c in range(46, 151):
        customer_order_distribution.extend([c] * random.randint(12, 22))
    for c in range(151, 301):
        customer_order_distribution.extend([c] * random.randint(3, 8))

    # Adjust sample size to approximately 5000
    random.shuffle(customer_order_distribution)
    selected_customers = customer_order_distribution[:4900]

    order_start = datetime(2024, 10, 1)
    order_end = datetime(2026, 9, 30)
    total_days = (order_end - order_start).days

    for cust_id in selected_customers:
        # Seasonality: higher probability in Oct-Nov (Festive season in India)
        # Random day with seasonal weight
        day_offset = random.randint(0, total_days)
        curr_date = order_start + timedelta(days=day_offset)
        month = curr_date.month
        # Festive season boost
        if month in [10, 11] and random.random() < 0.25:
            # Re-pick date in festive range to boost peak
            curr_date = datetime(curr_date.year, random.choice([10, 11]), random.randint(1, 28))

        date_str = curr_date.strftime('%Y-%m-%d')

        # Check if customer executes a known bundle (20% probability)
        if random.random() < 0.20:
            bundle = random.choice(bundle_groups)
            for prod_id in bundle:
                prod = prod_map[prod_id]
                qty = random.randint(1, 2) if cust_id > 45 else random.randint(1, 4)
                status = random.choice(statuses)
                orders_data.append((cust_id, prod_id, prod[3], date_str, qty, status))
        else:
            # Random product with preference for star electronics & gadgets
            if random.random() < 0.35:
                # Star products
                prod_id = random.choice([1, 2, 3, 7, 8, 10, 31, 46, 61, 76])
            else:
                prod_id = random.randint(1, 120)

            prod = prod_map[prod_id]
            qty = random.randint(1, 3) if cust_id > 45 else random.randint(2, 5)
            status = random.choice(statuses)
            orders_data.append((cust_id, prod_id, prod[3], date_str, qty, status))

    # Sort chronologically
    orders_data.sort(key=lambda x: x[3])

    cur.executemany("""
        INSERT INTO ORDERS (customer_id, product_id, supplier_id, order_date, quantity, order_status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, orders_data)

    # 5. GENERATE SALES (For all non-cancelled orders)
    print("Generating SALES rows for non-cancelled orders...")
    cur.execute("""
        SELECT order_id, customer_id, product_id, supplier_id, order_date, quantity, order_status
        FROM ORDERS
        WHERE order_status != 'Cancelled'
    """)
    valid_orders = cur.fetchall()

    sales_data = []
    for o in valid_orders:
        oid, cid, pid, sid, odate, qty, status = o
        prod = prod_map[pid]
        unit_price = float(prod[4])
        cost_price = float(prod[5])
        tot_amt = round(qty * unit_price, 2)
        profit = round(qty * (unit_price - cost_price), 2)

        # Sale date: 1 to 4 days after order date
        try:
            od_dt = datetime.strptime(odate, '%Y-%m-%d')
            s_dt = od_dt + timedelta(days=random.randint(1, 4))
            sale_date = s_dt.strftime('%Y-%m-%d')
        except Exception:
            sale_date = odate

        sales_data.append((oid, cid, pid, sid, sale_date, qty, unit_price, tot_amt, profit))

    cur.executemany("""
        INSERT INTO SALES (order_id, customer_id, product_id, supplier_id, sale_date, quantity, unit_price, total_amount, profit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sales_data)

    # 6. DELIBERATELY INJECT DOCUMENTED DIRTY RECORDS FOR DATA PREPROCESSING
    print("Injecting documented dirty records for ETL Preprocessing demonstration...")
    injected_counts = {
        "duplicate_orders": 15,
        "null_order_statuses": 12,
        "negative_quantities": 8,
        "bad_date_formats": 6,
        "out_of_range_ratings": 4
    }

    # A) Injected Duplicate Orders (15 duplicates)
    cur.execute("SELECT customer_id, product_id, supplier_id, order_date, quantity, order_status FROM ORDERS LIMIT 15")
    sample_dupes = cur.fetchall()
    cur.executemany("""
        INSERT INTO ORDERS (customer_id, product_id, supplier_id, order_date, quantity, order_status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, sample_dupes)

    # B) Injected NULL Order Statuses (12 rows)
    cur.execute("""
        UPDATE ORDERS
        SET order_status = NULL
        WHERE order_id IN (SELECT order_id FROM ORDERS WHERE order_status = 'Processing' LIMIT 12)
    """)

    # C) Injected Negative Quantities (8 rows)
    cur.execute("""
        UPDATE ORDERS
        SET quantity = -abs(quantity)
        WHERE order_id IN (SELECT order_id FROM ORDERS WHERE quantity > 1 LIMIT 8)
    """)

    # D) Injected Bad Date Formats (6 rows)
    bad_dates = ['15/10/2025', '2025.11.05', '04-12-2025', 'BAD-DATE-2025', '25/01/2026', '2026/02/31']
    for idx, bdate in enumerate(bad_dates):
        cur.execute(f"UPDATE ORDERS SET order_date = '{bdate}' WHERE order_id = {100 + idx * 25}")

    # E) Injected Out-of-Range Supplier Ratings (4 rows)
    cur.execute("UPDATE SUPPLIERS SET supplier_rating = 6.4 WHERE supplier_id = 2")
    cur.execute("UPDATE SUPPLIERS SET supplier_rating = 5.8 WHERE supplier_id = 7")
    cur.execute("UPDATE SUPPLIERS SET supplier_rating = -1.2 WHERE supplier_id = 11")
    cur.execute("UPDATE SUPPLIERS SET supplier_rating = 0.0 WHERE supplier_id = 19")

    conn.commit()

    # Save Injected Dirty Log for Data Quality Verification
    with open(config.INJECTED_DIRTY_LOG_PATH, "w") as f:
        json.dump(injected_counts, f, indent=4)
    print(f"Injected dirty record metrics saved to {config.INJECTED_DIRTY_LOG_PATH}")

    # Generate and save Data Dictionary
    save_data_dictionary()

    # Log summary counts
    cur.execute("SELECT COUNT(*) FROM CUSTOMERS")
    n_cust = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM SUPPLIERS")
    n_supp = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM PRODUCTS")
    n_prod = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM ORDERS")
    n_ord = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM SALES")
    n_sales = cur.fetchone()[0]

    conn.close()

    print("\n--- OPERATIONAL DATABASE GENERATION COMPLETED ---")
    print(f"CUSTOMERS : {n_cust}")
    print(f"SUPPLIERS : {n_supp}")
    print(f"PRODUCTS  : {n_prod}")
    print(f"ORDERS    : {n_ord} (Includes {injected_counts['duplicate_orders']} duplicates)")
    print(f"SALES     : {n_sales}")
    print(f"Path      : {config.OPERATIONAL_DB_PATH}\n")


def save_data_dictionary():
    """Build and save comprehensive data dictionary for operational and warehouse schemas."""
    data_dict = {
        "CUSTOMERS": {
            "description": "Registered consumer accounts purchasing dropshipped goods across India.",
            "columns": {
                "customer_id": {"type": "INTEGER (PK)", "description": "Unique identifier for customer."},
                "customer_name": {"type": "TEXT", "description": "Full name of the customer."},
                "city": {"type": "TEXT", "description": "City of residence."},
                "state": {"type": "TEXT", "description": "Indian state of residence."},
                "registration_date": {"type": "DATE", "description": "Date account was opened."}
            }
        },
        "SUPPLIERS": {
            "description": "Verified local regional manufacturers and dropshipping partners.",
            "columns": {
                "supplier_id": {"type": "INTEGER (PK)", "description": "Unique supplier identifier."},
                "supplier_name": {"type": "TEXT", "description": "Business or trade name."},
                "city": {"type": "TEXT", "description": "Fulfillment center city."},
                "state": {"type": "TEXT", "description": "Fulfillment center state."},
                "supplier_rating": {"type": "REAL", "description": "Quality score between 1.0 and 5.0."}
            }
        },
        "PRODUCTS": {
            "description": "Catalog of 120 products spanning 8 standard retail categories.",
            "columns": {
                "product_id": {"type": "INTEGER (PK)", "description": "Unique product SKU."},
                "product_name": {"type": "TEXT", "description": "Trade title of product item."},
                "category": {"type": "TEXT", "description": "Merchandising category (e.g. Electronics)."},
                "supplier_id": {"type": "INTEGER (FK)", "description": "Associated manufacturing supplier."},
                "price": {"type": "REAL", "description": "Selling retail price in INR."},
                "cost_price": {"type": "REAL", "description": "Wholesale supplier cost in INR."},
                "stock_quantity": {"type": "INTEGER", "description": "Remaining available warehouse units."}
            }
        },
        "ORDERS": {
            "description": "Transactional log of consumer purchase orders over a 24-month horizon.",
            "columns": {
                "order_id": {"type": "INTEGER (PK)", "description": "Order transaction serial number."},
                "customer_id": {"type": "INTEGER (FK)", "description": "Purchasing customer ID."},
                "product_id": {"type": "INTEGER (FK)", "description": "Ordered product SKU."},
                "supplier_id": {"type": "INTEGER (FK)", "description": "Fulfilling supplier partner."},
                "order_date": {"type": "TEXT/DATE", "description": "Date order placed by consumer."},
                "quantity": {"type": "INTEGER", "description": "Number of units ordered."},
                "order_status": {"type": "TEXT", "description": "Delivered, Shipped, Processing, Cancelled, Returned."}
            }
        },
        "SALES": {
            "description": "Financial settlement records generated for all non-cancelled orders.",
            "columns": {
                "sale_id": {"type": "INTEGER (PK)", "description": "Financial sales invoice identifier."},
                "order_id": {"type": "INTEGER (FK)", "description": "Originating purchase order ID."},
                "customer_id": {"type": "INTEGER (FK)", "description": "Customer key."},
                "product_id": {"type": "INTEGER (FK)", "description": "Product key."},
                "supplier_id": {"type": "INTEGER (FK)", "description": "Supplier key."},
                "sale_date": {"type": "DATE", "description": "Settlement date of payment."},
                "quantity": {"type": "INTEGER", "description": "Quantity settled."},
                "unit_price": {"type": "REAL", "description": "Selling unit price in INR."},
                "total_amount": {"type": "REAL", "description": "Gross sales revenue (quantity * unit_price)."},
                "profit": {"type": "REAL", "description": "Net profit (total_amount - wholesale cost)."}
            }
        }
    }
    with open(config.DATA_DICTIONARY_PATH, "w") as f:
        json.dump(data_dict, f, indent=4)


if __name__ == "__main__":
    init_operational_db()
    generate_operational_data()
