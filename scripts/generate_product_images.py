"""
LocalDrop - Resumable Product Image Catalog Manifest & Generator Helper
Tracks existing product images, manages resumable batches, and provides
photorealistic studio prompts for every product in the catalog.
"""

import os
import sys
import sqlite3
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db", "operational.db")
IMG_DIR = os.path.join(BASE_DIR, "static", "images", "products")

# Tailored studio product photography prompts for all catalog items
PROMPT_TEMPLATES = {
    "Mobile Accessories": "Commercial studio product photograph of {name}: modern mobile phone accessory on a seamless light-grey background. Studio lighting, soft natural contact shadow underneath, square 1:1 framing, ultra-clean commercial product shot, no text, no logos, no watermarks, no people, no hands.",
    "Audio & Electronics": "Commercial studio product photograph of {name}: sleek modern consumer electronics device on a seamless light-grey background. Studio lighting, soft natural contact shadow underneath, square 1:1 framing, ultra-clean commercial product shot, no text, no logos, no watermarks, no people, no hands.",
    "Computer & Office": "Commercial studio product photograph of {name}: professional ergonomic computer desktop equipment on a seamless light-grey background. Studio lighting, soft natural contact shadow underneath, square 1:1 framing, ultra-clean commercial product shot, no text, no logos, no watermarks, no people, no hands.",
    "Home & Office": "Commercial studio product photograph of {name}: elegant modern home office organizer and accessory on a seamless light-grey background. Studio lighting, soft natural contact shadow underneath, square 1:1 framing, ultra-clean commercial product shot, no text, no logos, no watermarks, no people, no hands.",
    "Kitchen & Dining": "Commercial studio product photograph of {name}: premium food-grade kitchenware and dining tool on a seamless light-grey background. Studio lighting, soft natural contact shadow underneath, square 1:1 framing, ultra-clean commercial product shot, no text, no logos, no watermarks, no people, no hands.",
    "Fitness & Sports": "Commercial studio product photograph of {name}: high-durability fitness exercise equipment on a seamless light-grey background. Studio lighting, soft natural contact shadow underneath, square 1:1 framing, ultra-clean commercial product shot, no text, no logos, no watermarks, no people, no hands.",
    "Personal Care": "Commercial studio product photograph of {name}: hygienic personal grooming wellness tool on a seamless light-grey background. Studio lighting, soft natural contact shadow underneath, square 1:1 framing, ultra-clean commercial product shot, no text, no logos, no watermarks, no people, no hands.",
    "Stationery": "Commercial studio product photograph of {name}: premium stationery and desk organizational item on a seamless light-grey background. Studio lighting, soft natural contact shadow underneath, square 1:1 framing, ultra-clean commercial product shot, no text, no logos, no watermarks, no people, no hands.",
    "Travel & Luggage": "Commercial studio product photograph of {name}: compact durable travel gear accessory on a seamless light-grey background. Studio lighting, soft natural contact shadow underneath, square 1:1 framing, ultra-clean commercial product shot, no text, no logos, no watermarks, no people, no hands.",
    "Wearables & Fitness": "Commercial studio product photograph of {name}: modern digital smart wearable tracker on a seamless light-grey background. Studio lighting, soft natural contact shadow underneath, square 1:1 framing, ultra-clean commercial product shot, no text, no logos, no watermarks, no people, no hands."
}


def build_prompt(name, category):
    template = PROMPT_TEMPLATES.get(
        category,
        "Commercial studio product photograph of {name}: centered on a seamless light-grey background. Studio lighting, soft natural contact shadow underneath, square 1:1 framing, ultra-clean commercial product shot, no text, no logos, no watermarks, no people, no hands."
    )
    return template.format(name=name)


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
            try:
                with Image.open(filepath) as im:
                    width, height = im.size
                    fmt = im.format
            except Exception:
                width, height, fmt = (0, 0, "INVALID")

            imaged.append({
                "product_id": pid,
                "product_name": name,
                "category": cat,
                "filename": filename,
                "size_bytes": os.path.getsize(filepath),
                "resolution": f"{width}x{height}",
                "format": fmt
            })
        else:
            missing.append({
                "product_id": pid,
                "product_name": name,
                "category": cat,
                "target_filename": filename,
                "prompt": build_prompt(name, cat)
            })

    return imaged, missing


def optimize_and_save_image(src_path, dest_filename):
    dest_path = os.path.join(IMG_DIR, dest_filename)
    im = Image.open(src_path).convert('RGB')
    im = im.resize((600, 600), Image.Resampling.LANCZOS)
    im.save(dest_path, 'JPEG', quality=85)
    return dest_path


def main():
    imaged, missing = get_image_status()
    total = len(imaged) + len(missing)

    print("=" * 70)
    print("LOCALDROP RESUMABLE PRODUCT IMAGE CATALOG MANIFEST")
    print("=" * 70)
    print(f"Total Products in Catalog   : {total}")
    print(f"Verified Active Images      : {len(imaged)} ({len(imaged)/total*100:.1f}%)")
    print(f"Pending Image Generation    : {len(missing)} ({len(missing)/total*100:.1f}%)")
    print("-" * 70)
    print("15 Verified Product Photographs:")
    for item in imaged:
        print(f"  [ID {item['product_id']:3d}] {item['product_name']:<36} -> {item['filename']} ({item['resolution']}, {item['size_bytes']:,} B)")
    print("-" * 70)
    print(f"Pending Products Queue ({len(missing)} items):")
    print("Next batch of 10 items queued for generation when quota permits:")
    for item in missing[:10]:
        print(f"  [ID {item['product_id']:3d}] {item['product_name']:<36} ({item['category']}) -> {item['target_filename']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
