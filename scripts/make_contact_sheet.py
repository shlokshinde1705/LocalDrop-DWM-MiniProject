"""
Contact Sheet Generator: LocalDrop Product Image Review
Generates exports/image_contact_sheet.html displaying each product photo
alongside its ID, name, category, and source for visual verification.
"""

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'db', 'operational.db')
PROD_IMG_DIR = os.path.join(BASE_DIR, 'static', 'images', 'products')
CAT_IMG_DIR = os.path.join(BASE_DIR, 'static', 'images', 'categories')
OUTPUT_HTML = os.path.join(BASE_DIR, 'exports', 'image_contact_sheet.html')


def build_contact_sheet():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT product_id, product_name, category, price FROM PRODUCTS ORDER BY product_id ASC")
    products = cur.fetchall()

    html_parts = []
    html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>LocalDrop Product Image Contact Sheet</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f8fafc;
            color: #0f172a;
            margin: 0;
            padding: 32px;
        }
        h1 {
            font-size: 1.5rem;
            margin-bottom: 6px;
        }
        p.subtitle {
            font-size: 0.85rem;
            color: #64748b;
            margin-top: 0;
            margin-bottom: 24px;
        }
        .summary-bar {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 16px 20px;
            margin-bottom: 24px;
            display: flex;
            gap: 28px;
            font-size: 0.85rem;
        }
        .summary-item strong {
            display: block;
            font-size: 1.25rem;
            color: #1e3a8a;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
            gap: 16px;
        }
        .card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        .img-container {
            width: 100%;
            height: 200px;
            background: #f1f5f9;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }
        .img-container img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .placeholder {
            color: #94a3b8;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .card-body {
            padding: 12px 14px;
            display: flex;
            flex-direction: column;
            flex: 1;
        }
        .badge {
            font-size: 0.70rem;
            padding: 2px 6px;
            border-radius: 3px;
            display: inline-block;
            margin-bottom: 6px;
            font-weight: 600;
            text-transform: uppercase;
            width: fit-content;
        }
        .badge-dedicated {
            background: #e0f2fe;
            color: #0369a1;
            border: 1px solid #bae6fd;
        }
        .badge-category {
            background: #f1f5f9;
            color: #475569;
            border: 1px solid #cbd5e1;
        }
        .badge-placeholder {
            background: #fef2f2;
            color: #b91c1c;
            border: 1px solid #fecaca;
        }
        .product-title {
            font-size: 0.88rem;
            font-weight: 600;
            margin-bottom: 4px;
            line-height: 1.3;
        }
        .meta {
            font-size: 0.75rem;
            color: #64748b;
            margin-top: auto;
            padding-top: 8px;
            display: flex;
            justify-content: space-between;
        }
    </style>
</head>
<body>
    <h1>LocalDrop Product Image Contact Sheet</h1>
    <p class="subtitle">Visual inspection and quality review ledger for all 120 catalog products</p>
""")

    own_count = 0
    cat_count = 0
    placeholder_count = 0
    card_htmls = []

    for p in products:
        pid = p['product_id']
        name = p['product_name']
        cat = p['category']
        price = p['price']

        prod_file = f"product_{pid}.jpg"
        prod_path = os.path.join(PROD_IMG_DIR, prod_file)

        cat_slug = cat.lower().replace('&', 'and').replace(' ', '_').replace('__', '_')
        cat_file = f"{cat_slug}.jpg"
        cat_path = os.path.join(CAT_IMG_DIR, cat_file)

        if os.path.exists(prod_path):
            img_src = f"../static/images/products/{prod_file}"
            badge_class = "badge-dedicated"
            badge_text = "Dedicated Studio Photo"
            own_count += 1
            img_elem = f'<img src="{img_src}" alt="{name}" loading="lazy">'
        else:
            badge_class = "badge-placeholder"
            badge_text = "Neutral Placeholder"
            placeholder_count += 1
            img_elem = f'''<div style="width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:16px; box-sizing:border-box; text-align:center; background:#f1f5f9;">
                <div style="font-size:0.86rem; font-weight:600; color:#0f172a; line-height:1.35; margin-bottom:6px;">{name}</div>
                <div style="font-size:0.68rem; font-weight:600; color:#64748b; text-transform:uppercase; letter-spacing:0.05em;">{cat}</div>
            </div>'''

        card = f"""
        <div class="card">
            <div class="img-container">
                {img_elem}
            </div>
            <div class="card-body">
                <span class="badge {badge_class}">{badge_text}</span>
                <div class="product-title">{name}</div>
                <div class="meta">
                    <span>#{pid} &bull; {cat}</span>
                    <span>&fnof;{price:,.2f}</span>
                </div>
            </div>
        </div>
        """
        card_htmls.append(card)

    summary_bar = f"""
    <div class="summary-bar">
        <div class="summary-item">
            <strong>120</strong>
            <span>Total Catalog Products</span>
        </div>
        <div class="summary-item">
            <strong>{own_count}</strong>
            <span>Dedicated Studio Photos</span>
        </div>
        <div class="summary-item">
            <strong>{placeholder_count}</strong>
            <span>Plain Neutral Placeholders</span>
        </div>
        <div class="summary-item">
            <strong>0</strong>
            <span>Shared Category Photos</span>
        </div>
    </div>
    <div class="grid">
        {"".join(card_htmls)}
    </div>
</body>
</html>
"""
    html_parts.append(summary_bar)

    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write("".join(html_parts))

    print(f"Contact sheet saved to: {OUTPUT_HTML}")
    print(f"Products with dedicated photo: {own_count}")
    print(f"Products using category photo: {cat_count}")
    print(f"Products using placeholder: {placeholder_count}")


if __name__ == '__main__':
    build_contact_sheet()
