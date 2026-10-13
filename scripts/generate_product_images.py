"""
LocalDrop - Resumable Product Image Catalog Manifest & Generator Helper
Tracks existing product images and provides prompts for any missing items.
"""

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db", "operational.db")
IMG_DIR = os.path.join(BASE_DIR, "static", "images", "products")


def get_image_status():
    os.makedirs(IMG_DIR, exist_ok=True)
    existing_files = set(os.listdir(IMG_DIR))
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT product_id, product_name, category, price FROM PRODUCTS ORDER BY product_id")
    products = cur.fetchall()
    conn.close()

    imaged = []
    missing = []

    for pid, name, cat, price in products:
        filename = f"product_{pid}.jpg"
        filepath = os.path.join(IMG_DIR, filename)
        if filename in existing_files and os.path.getsize(filepath) > 0:
            imaged.append({
                "product_id": pid,
                "product_name": name,
                "category": cat,
                "filename": filename,
                "size_bytes": os.path.getsize(filepath)
            })
        else:
            missing.append({
                "product_id": pid,
                "product_name": name,
                "category": cat,
                "target_filename": filename
            })

    return imaged, missing


def main():
    imaged, missing = get_image_status()
    print("=" * 60)
    print("LOCALDROP PRODUCT IMAGE STATUS REPORT")
    print("=" * 60)
    print(f"Total Products in Catalog : {len(imaged) + len(missing)}")
    print(f"Products with Images      : {len(imaged)}")
    print(f"Products Pending Images   : {len(missing)}")
    print("-" * 60)
    print("Products with verified images:")
    for item in imaged:
        print(f"  [ID {item['product_id']:3d}] {item['product_name']:<40} -> {item['filename']} ({item['size_bytes']:,} B)")
    print("-" * 60)
    if missing:
        print(f"Next 10 missing products to generate when quota resets:")
        for item in missing[:10]:
            print(f"  [ID {item['product_id']:3d}] {item['product_name']:<40} -> {item['target_filename']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
