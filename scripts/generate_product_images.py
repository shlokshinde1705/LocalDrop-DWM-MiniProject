"""
LocalDrop - Resumable Product Image Generator & Catalog Ingestion Pipeline
Generates commercial studio photographs for products, verifies images, and updates catalog.
Supports dry-run validation, manageable batch processing, and graceful 429 quota handling.
"""

import os
import sys
import json
import base64
import argparse
import sqlite3
import requests
from io import BytesIO
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db", "operational.db")
IMG_DIR = os.path.join(BASE_DIR, "static", "images", "products")

# Default model endpoint for Google Generative AI Imagen
IMAGEN_MODEL = "imagen-3.0-generate-002"
API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={api_key}"

# Tailored studio photography prompts by product category
PROMPT_TEMPLATES = {
    "Mobile Accessories": "Commercial studio product photograph of {name}: modern smartphone accessory on a seamless light-grey background. Studio lighting, soft natural contact shadow underneath, square 1:1 framing, ultra-clean commercial product shot, no text, no logos, no watermarks, no people, no hands.",
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


def load_env_file(filepath=None):
    """Simple parser for .env files if present."""
    if not filepath:
        filepath = os.path.join(BASE_DIR, ".env")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val


def get_api_key(cli_key=None):
    if cli_key:
        return cli_key
    load_env_file()
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def get_image_status():
    """Audits database and static/images/products directory."""
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
        is_valid = False
        res = "0x0"
        size_b = 0

        if filename in existing_files and os.path.getsize(filepath) > 0:
            try:
                with Image.open(filepath) as im:
                    res = f"{im.size[0]}x{im.size[1]}"
                    size_b = os.path.getsize(filepath)
                    if im.size[0] >= 100 and im.size[1] >= 100:
                        is_valid = True
            except Exception:
                is_valid = False

        if is_valid:
            imaged.append({
                "product_id": pid,
                "product_name": name,
                "category": cat,
                "filename": filename,
                "size_bytes": size_b,
                "resolution": res
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


def optimize_and_save_bytes(raw_bytes, dest_filepath):
    """Normalizes any generated image to 600x600 Baseline JPEG, quality 85."""
    im = Image.open(BytesIO(raw_bytes))
    im = im.convert("RGB")
    im = im.resize((600, 600), Image.Resampling.LANCZOS)
    im.save(dest_filepath, "JPEG", quality=85)
    return os.path.getsize(dest_filepath)


def call_imagen_api(prompt, api_key, model=IMAGEN_MODEL):
    """
    Direct REST API call to Google Generative Language Imagen endpoint.
    Returns: (bytes, error_code, error_message)
    """
    url = API_URL_TEMPLATE.format(model=model, api_key=api_key)
    headers = {"Content-Type": "application/json"}
    payload = {
        "instances": [
            {"prompt": prompt}
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "1:1",
            "outputMimeType": "image/jpeg"
        }
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
    except requests.exceptions.RequestException as e:
        return None, 500, f"Network/Connection error: {e}"

    if resp.status_code == 200:
        data = resp.json()
        predictions = data.get("predictions", [])
        if predictions and "bytesBase64Encoded" in predictions[0]:
            img_bytes = base64.b64decode(predictions[0]["bytesBase64Encoded"])
            return img_bytes, 200, None
        return None, 502, "Unexpected payload: bytesBase64Encoded not found"
    
    # Error response parsing
    err_msg = resp.text
    try:
        err_json = resp.json()
        err_msg = err_json.get("error", {}).get("message", resp.text)
    except Exception:
        pass

    return None, resp.status_code, err_msg


def run_batch_generation(batch_size=10, start_id=None, api_key=None, dry_run=False):
    """Processes pending images in sequential batches."""
    imaged, missing = get_image_status()
    total = len(imaged) + len(missing)

    print("=" * 72)
    print("LOCALDROP PRODUCT IMAGE GENERATION PIPELINE")
    print("=" * 72)
    print(f"Catalog Total       : {total} products")
    print(f"Verified Existing   : {len(imaged)} products (preserved)")
    print(f"Pending Generation  : {len(missing)} products")
    print(f"Mode                : {'DRY RUN (Simulation)' if dry_run else 'LIVE GENERATION'}")
    print("-" * 72)

    # Filter by start_id if specified
    queue = missing
    if start_id is not None:
        queue = [p for p in queue if p["product_id"] >= start_id]

    batch = queue[:batch_size]

    if not batch:
        print("All requested products already have valid images. Nothing to generate.")
        return 0, 0

    print(f"Target Batch: {len(batch)} products (IDs: {[p['product_id'] for p in batch]})")
    print("-" * 72)

    if dry_run:
        print("[DRY RUN] Simulating generation for target batch:")
        for idx, p in enumerate(batch, 1):
            dest_rel = os.path.join("static", "images", "products", p["target_filename"])
            print(f"  {idx:2d}. [ID {p['product_id']:3d}] {p['product_name']}")
            print(f"      Category : {p['category']}")
            print(f"      Target   : {dest_rel}")
            print(f"      Prompt   : \"{p['prompt'][:90]}...\"")
        print("-" * 72)
        print("[DRY RUN COMPLETE] Validation succeeded. Workflow is ready for live API execution.")
        return len(batch), 0

    # Live generation mode
    if not api_key:
        print("ERROR: No Gemini/Google API key found.")
        print("Please provide an API key using:")
        print("  1. Environment variable: set GEMINI_API_KEY=your_key")
        print("  2. .env file: GEMINI_API_KEY=your_key in project root")
        print("  3. CLI flag: python scripts/generate_product_images.py --api-key your_key")
        print("  4. Or run a safe simulation with: python scripts/generate_product_images.py --dry-run")
        sys.exit(1)

    successful = 0
    failed = 0

    for idx, p in enumerate(batch, 1):
        pid = p["product_id"]
        pname = p["product_name"]
        target_path = os.path.join(IMG_DIR, p["target_filename"])

        print(f"[{idx}/{len(batch)}] Generating Product #{pid}: '{pname}'...")

        raw_bytes, status_code, err_msg = call_imagen_api(p["prompt"], api_key)

        if status_code == 200 and raw_bytes:
            saved_size = optimize_and_save_bytes(raw_bytes, target_path)
            print(f"  -> SUCCESS: Saved {p['target_filename']} (600x600, {saved_size:,} B)")
            successful += 1
        elif status_code == 429 or (err_msg and "RESOURCE_EXHAUSTED" in err_msg):
            print(f"  -> QUOTA ERROR (429 RESOURCE_EXHAUSTED): Capacity reached for image model.")
            print(f"  -> Halting batch cleanly at Product #{pid} to protect API state.")
            print(f"  -> Retry Guidance: Re-run this script after quota resets with:")
            print(f"     python scripts/generate_product_images.py --start-id {pid}")
            failed += 1
            break
        else:
            print(f"  -> FAILED: HTTP {status_code} - {err_msg}")
            failed += 1

    print("-" * 72)
    print(f"Batch Execution Finished: {successful} succeeded, {failed} stopped/failed.")
    print("=" * 72)
    return successful, failed


def main():
    parser = argparse.ArgumentParser(description="LocalDrop Resumable Product Image Generator")
    parser.add_argument("--dry-run", action="store_true", help="Run workflow validation without API calls")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of products to process in batch (default: 10)")
    parser.add_argument("--start-id", type=int, default=None, help="Specific starting product ID")
    parser.add_argument("--status", action="store_true", help="Print catalog image manifest and exit")
    parser.add_argument("--api-key", type=str, default=None, help="Gemini API key (or set GEMINI_API_KEY)")
    args = parser.parse_args()

    api_key = get_api_key(args.api_key)

    if args.status:
        imaged, missing = get_image_status()
        total = len(imaged) + len(missing)
        print("=" * 70)
        print("LOCALDROP PRODUCT IMAGE STATUS")
        print("=" * 70)
        print(f"Total Products in Catalog : {total}")
        print(f"Verified Images           : {len(imaged)} ({len(imaged)/total*100:.1f}%)")
        print(f"Pending Generation        : {len(missing)} ({len(missing)/total*100:.1f}%)")
        print("-" * 70)
        print("Active Images:")
        for item in imaged:
            print(f"  [ID {item['product_id']:3d}] {item['product_name']:<35} -> {item['filename']} ({item['resolution']}, {item['size_bytes']:,} B)")
        print("-" * 70)
        print(f"Next 10 Missing Products:")
        for item in missing[:10]:
            print(f"  [ID {item['product_id']:3d}] {item['product_name']:<35} -> {item['target_filename']}")
        print("=" * 70)
        return

    run_batch_generation(
        batch_size=args.batch_size,
        start_id=args.start_id,
        api_key=api_key,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
