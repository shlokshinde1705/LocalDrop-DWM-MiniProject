"""
LocalDrop: Automated Product & Category Image Ingestion Pipeline
Fetches authentic free-licence photos from Wikimedia Commons for all 120 products and 8 categories.
Saves to:
 - static/images/products/product_<id>.jpg
 - static/images/categories/<category_lowercase_underscored>.jpg
Resizes to max 600x600, JPEG quality 80.
Generates exports/image_credits.csv with accurate licence and attribution metadata.
"""

import os
import sys
import re
import csv
import time
import sqlite3
import requests
from io import BytesIO
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

HEADERS = {
    'User-Agent': 'LocalDropAcademic/1.0 (academic DWM mini-project; contact: student@vit.edu)'
}
WIKIMEDIA_API = 'https://commons.wikimedia.org/w/api.php'

# Query Mapping for All 120 Products
PRODUCT_SEARCH_TERMS = {
    1: ['smartwatch front', 'smartwatch', 'smart watch'],
    2: ['wireless earbuds charging case', 'wireless earbuds', 'bluetooth earphones'],
    3: ['power bank portable charger', 'power bank', 'portable battery pack'],
    4: ['usb webcam', 'computer webcam', 'webcam'],
    5: ['studio headphones', 'noise cancelling headphones', 'headset'],
    6: ['portable bluetooth speaker', 'bluetooth speaker', 'wireless speaker'],
    7: ['fitness tracker band', 'fitness band wristband', 'smartband'],
    8: ['usb-c hub multi-port adapter', 'usb hub', 'usb-c dock'],
    9: ['mechanical keyboard rgb', 'mechanical keyboard', 'computer keyboard'],
    10: ['wireless optical computer mouse', 'computer mouse', 'wireless mouse'],
    11: ['wireless charging pad', 'qi wireless charger', 'wireless charger'],
    12: ['home security camera ip', 'security camera', 'surveillance camera'],
    13: ['universal travel adapter plug', 'travel adapter', 'plug adapter'],
    14: ['usb fast charger adapter', 'wall charger adapter', 'usb charger'],
    15: ['digital voice recorder', 'dictaphone voice recorder', 'audio recorder'],
    16: ['smartphone silicone protective case', 'smartphone case', 'phone cover'],
    17: ['tempered glass screen protector', 'screen protector smartphone', 'phone screen guard'],
    18: ['braided usb-c cable charging', 'usb-c cable', 'usb cable'],
    19: ['desk phone stand aluminum', 'smartphone stand holder', 'phone stand'],
    20: ['car phone mount holder', 'dashboard phone mount', 'car phone holder'],
    21: ['selfie stick tripod', 'selfie stick bluetooth', 'selfie stick'],
    22: ['waterproof phone pouch bag', 'waterproof pouch', 'dry bag phone'],
    23: ['3.5mm aux audio cable', 'audio cable jack', 'aux cord'],
    24: ['camera lens protector glass', 'camera lens filter glass', 'camera filter'],
    25: ['phone ring holder grip', 'smartphone ring grip', 'phone grip'],
    26: ['multi usb charging cable 3-in-1', 'charging cable multi', 'usb charging cable'],
    27: ['cable organizer clips silicone', 'cable clips holder', 'cable organizer'],
    28: ['usb otg adapter plug', 'otg adapter usb', 'usb adapter'],
    29: ['neckband wireless earphones', 'bluetooth neckband headphones', 'neckband headphones'],
    30: ['speaker grille mesh cloth', 'speaker grill mesh', 'speaker cloth'],
    31: ['aluminum laptop stand ergonomic', 'laptop stand desk', 'laptop riser'],
    32: ['led desk lamp adjustable', 'desk lamp modern', 'reading lamp desk'],
    33: ['leather desk mat mousepad', 'large desk mouse pad', 'desk blotter'],
    34: ['wooden desktop organizer shelf', 'wooden desk organizer', 'desk organizer'],
    35: ['lumbar support cushion memory foam', 'lumbar pillow', 'chair cushion'],
    36: ['ergonomic footrest stool office', 'under desk footrest', 'office footrest'],
    37: ['ultrasonic aroma diffuser humidifier', 'essential oil diffuser', 'aroma diffuser'],
    38: ['digital alarm clock led display', 'digital desk clock', 'alarm clock'],
    39: ['cable management box organizer', 'cable storage box', 'cord organizer box'],
    40: ['monitor light bar screenbar', 'monitor lamp light', 'computer screen bar'],
    41: ['laptop cooling pad fan', 'laptop cooler pad', 'notebook cooler'],
    42: ['mini desktop vacuum cleaner', 'table vacuum cleaner', 'portable desk vacuum'],
    43: ['headphone hanger desk mount', 'headphone stand hook', 'headphone holder'],
    44: ['magnetic whiteboard dry erase', 'small whiteboard marker', 'whiteboard'],
    45: ['wooden wall key holder mail organizer', 'wall key holder', 'key rack organizer'],
    46: ['yoga mat rolled exercise', 'exercise yoga mat', 'fitness mat'],
    47: ['fabric resistance exercise bands', 'resistance loop bands', 'exercise bands'],
    48: ['speed jump rope skipping rope', 'skipping rope fitness', 'jump rope'],
    49: ['push up board fitness grips', 'push up grips handles', 'push-up bars'],
    50: ['massage gun deep tissue percussion', 'massage gun massager', 'percussion massager'],
    51: ['hex dumbbells pair gym weights', 'neoprene dumbbells pair', 'dumbbells pair'],
    52: ['protein shaker bottle blender', 'shaker bottle gym', 'gym water bottle'],
    53: ['sports phone armband running', 'running armband case', 'smartphone armband'],
    54: ['microfiber gym towel sports', 'quick dry sports towel', 'microfiber towel'],
    55: ['foam roller fitness massage', 'foam roller cylinder', 'muscle roller foam'],
    56: ['hand grip strength trainer squeezer', 'hand gripper exerciser', 'grip strength trainer'],
    57: ['weightlifting fitness gloves padded', 'gym workout gloves', 'fitness gloves'],
    58: ['ab roller wheel with knee mat', 'abdominal roller wheel', 'ab wheel roller'],
    59: ['running hydration belt bottle waist pack', 'running waist pack', 'running hydration belt'],
    60: ['ankle weights pair exercise', 'wrist ankle weights pair', 'ankle weights'],
    61: ['stainless steel insulated water bottle', 'vacuum flask water bottle', 'insulated bottle'],
    62: ['electric kettle stainless steel modern', 'electric water kettle', 'tea kettle electric'],
    63: ['french press coffee maker glass', 'cafetiere french press', 'coffee press'],
    64: ['digital kitchen food scale electronic', 'kitchen weighing scale', 'food scale digital'],
    65: ['silicone cooking utensils set kitchen', 'silicone kitchen utensils', 'cooking spoons set'],
    66: ['kitchen herb scissors multi-blade', 'herb shears scissors', 'kitchen scissors shears'],
    67: ['vegetable chopper dicer manual', 'food chopper cutter', 'vegetable cutter dicer'],
    68: ['reusable silicone food storage bags', 'silicone food storage pouch', 'reusable zip bag'],
    69: ['glass oil dispenser bottle pourer', 'olive oil dispenser bottle', 'oil vinegar bottle'],
    70: ['ceramic coffee mug cup', 'coffee mug ceramic', 'tea mug ceramic'],
    71: ['stainless steel bento lunch box', 'metal bento lunch box', 'tiffin lunch box'],
    72: ['manual citrus juicer hand squeezer', 'lemon squeezer metal', 'citrus squeezer press'],
    73: ['bamboo wooden cutting board kitchen', 'bamboo chopping board', 'cutting board wood'],
    74: ['double wall glass cup tumbler', 'insulated glass tumbler', 'glass cup double wall'],
    75: ['stainless steel drinking straws set', 'metal reusable straws set', 'reusable straws'],
    76: ['laptop travel backpack waterproof', 'anti-theft backpack laptop', 'travel backpack'],
    77: ['memory foam travel neck pillow', 'travel neck pillow u-shape', 'travel pillow'],
    78: ['travel packing cubes luggage organizer', 'packing cubes set luggage', 'packing organizers'],
    79: ['compact folding travel umbrella', 'pocket travel umbrella windproof', 'small folding umbrella'],
    80: ['digital luggage hanging scale travel', 'luggage scale electronic hanging', 'suitcase scale'],
    81: ['leather passport holder travel wallet', 'passport cover leather wallet', 'passport case'],
    82: ['tsa luggage lock padlock cable', 'travel luggage padlock', 'combination luggage lock'],
    83: ['foldable duffle bag lightweight travel', 'travel duffel bag folding', 'gym duffle bag'],
    84: ['hanging travel toiletry organizer kit', 'wash bag toiletry kit', 'toiletry bag hanging'],
    85: ['eva hard shell electronics case', 'cable organizer travel case', 'electronics travel pouch'],
    86: ['travel shoe storage pouch bags', 'shoe bags travel', 'shoe organizer travel'],
    87: ['rfid blocking slim wallet money clip', 'minimalist card holder wallet', 'money clip wallet'],
    88: ['travel laundry wash bag pouch', 'laundry bag travel', 'drawstring laundry bag'],
    89: ['contoured 3d sleep eye mask', 'sleep eye mask blindfold', 'eye mask sleeping'],
    90: ['mini first aid pouch emergency', 'first aid kit pouch red', 'emergency medical pouch'],
    91: ['electric sonic rechargeable toothbrush', 'electric toothbrush', 'sonic toothbrush'],
    92: ['jade roller gua sha facial massage', 'jade roller facial tool', 'facial jade roller'],
    93: ['electric hair beard trimmer clipper', 'hair trimmer cordless clipper', 'beard trimmer electric'],
    94: ['foldable ionic hair dryer blower', 'hair dryer portable', 'hairdryer compact'],
    95: ['stainless steel manicure nail kit tools', 'manicure grooming set case', 'nail grooming kit'],
    96: ['facial steamer sauna machine mist', 'face sauna vaporizer', 'facial steamer'],
    97: ['bamboo charcoal dental floss picks', 'dental floss sticks picks', 'dental floss picks'],
    98: ['compact pocket makeup mirror led', 'pocket mirror compact makeup', 'compact mirror'],
    99: ['electric foot callus remover pedicure', 'electric callus remover roller', 'electronic foot file'],
    100: ['natural bristle dry body brush wooden', 'dry body brush bristles', 'body bath brush'],
    101: ['essential oil amber roll-on bottle', 'aromatherapy roll on bottle', 'essential oil bottle roll-on'],
    102: ['satin silk hair sleep bonnet cap', 'silk sleep bonnet cap', 'satin sleep cap'],
    103: ['wooden beard comb brush grooming set', 'wooden beard comb', 'beard brush comb'],
    104: ['heated eyelash curler electric', 'eyelash curler makeup tool', 'eyelash curler'],
    105: ['reusable bamboo cotton makeup remover pads', 'reusable cotton rounds pads', 'reusable makeup pads'],
    106: ['dotted bullet journal hardcover notebook', 'bullet journal dotted notebook', 'hardcover journal notebook'],
    107: ['dual tip brush calligraphy pens markers', 'calligraphy brush pens set', 'brush markers pens'],
    108: ['pastel highlighter marker pens stationery', 'pastel highlighter pens', 'highlighter markers set'],
    109: ['retractable gel ink pens stationery pack', 'gel ink pens stationery', 'gel pens pack'],
    110: ['decorative washi tape rolls japanese', 'washi tape rolls patterns', 'masking washi tape'],
    111: ['sticky notes memo cube pad colorful', 'sticky notes memo pad', 'post it notes pad'],
    112: ['metal wire mesh magazine file holder desk', 'magazine file holder desk', 'wire magazine holder'],
    113: ['desktop heavy duty tape dispenser stationery', 'desk tape dispenser', 'tape dispenser office'],
    114: ['acrylic rotating desk pen holder stand', 'rotating pen pencil holder', 'desk pen holder'],
    115: ['office desk stapler with staples set', 'manual office stapler', 'desk stapler'],
    116: ['handcrafted wooden carved bookmark tassel', 'wooden bookmark carved', 'wood bookmark'],
    117: ['rose gold paper clips binder clamps set', 'binder clips paper clips set', 'metal paper clips set'],
    118: ['mechanical drafting pencil set lead refills', 'mechanical pencil drafting', 'mechanical pencil set'],
    119: ['weekly desk planner notepad paper pad', 'weekly planner pad desk', 'desk planner notepad'],
    120: ['precision metal craft paper scissors shears', 'craft scissors precision shears', 'embroidery craft scissors']
}

CATEGORY_SEARCH_TERMS = {
    'electronics': ['consumer electronics gadgets', 'electronic devices technology'],
    'mobile_accessories': ['mobile phone accessories smartphone', 'smartphone accessories gadgets'],
    'home_and_office': ['home office desk workspace setup', 'modern home office desk'],
    'fitness_and_sports': ['fitness gym workout equipment weights', 'sports fitness equipment'],
    'kitchen_and_dining': ['kitchen cookware utensils tableware', 'kitchen utensils cooking'],
    'travel_and_luggage': ['travel luggage suitcase bags holiday', 'travel luggage suitcase'],
    'personal_care': ['personal care cosmetics toiletries grooming', 'skin care toiletries products'],
    'stationery': ['stationery office supplies pens notebooks', 'desk stationery supplies']
}


def search_wikimedia(query_list):
    """Searches Wikimedia Commons API for suitable photographic images."""
    for q in query_list:
        params = {
            'action': 'query',
            'generator': 'search',
            'gsrsearch': q,
            'gsrnamespace': 6,
            'gsrlimit': 6,
            'prop': 'imageinfo',
            'iiprop': 'url|size|mime|extmetadata',
            'iiurlwidth': 600,
            'format': 'json'
        }
        try:
            r = requests.get(WIKIMEDIA_API, headers=HEADERS, params=params, timeout=12)
            if r.status_code != 200:
                continue
            data = r.json()
            pages = data.get('query', {}).get('pages', {})
            for pid, page in pages.items():
                imageinfo = page.get('imageinfo', [])
                if not imageinfo:
                    continue
                info = imageinfo[0]
                mime = info.get('mime', '')
                if mime not in ['image/jpeg', 'image/png', 'image/webp']:
                    continue
                title = page.get('title', '')
                # Filter out obvious flags, icons, maps, drawings, or coats of arms
                if any(x in title.lower() for x in ['flag of', 'coat of arms', 'map of', 'symbol of', 'insignia', 'icon.png', 'logo']):
                    continue

                thumb_url = info.get('thumburl') or info.get('url')
                desc_url = info.get('descriptionurl', f"https://commons.wikimedia.org/wiki/{title.replace(' ', '_')}")
                meta = info.get('extmetadata', {})
                lic = meta.get('LicenseShortName', {}).get('value', 'CC BY-SA / Public Domain')
                lic = re.sub('<[^<]+?>', '', lic).strip() or 'Creative Commons / Public Domain'
                artist = meta.get('Artist', {}).get('value', 'Wikimedia Commons Contributor')
                artist = re.sub('<[^<]+?>', '', artist).strip()[:80] or 'Wikimedia Contributor'

                return thumb_url, desc_url, lic, artist
        except Exception:
            pass
        time.sleep(0.1)

    return None, None, None, None


def download_and_save_image(img_url, target_path):
    """Downloads image, converts to RGB, resizes to max 600x600, and saves as JPEG quality 80."""
    try:
        r = requests.get(img_url, headers=HEADERS, timeout=15)
        if r.status_code == 200 and len(r.content) > 1000:
            img = Image.open(BytesIO(r.content))
            img = img.convert('RGB')
            img.thumbnail((600, 600), Image.Resampling.LANCZOS)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            img.save(target_path, 'JPEG', quality=80, optimize=True)
            return True
    except Exception as e:
        pass
    return False


def run_pipeline():
    print("=" * 60)
    print("LocalDrop Product & Category Image Ingestion Pipeline")
    print("=" * 60)

    # 1. Directories setup
    products_dir = os.path.join(config.BASE_DIR, "static", "images", "products")
    categories_dir = os.path.join(config.BASE_DIR, "static", "images", "categories")
    exports_dir = os.path.join(config.BASE_DIR, "exports")
    os.makedirs(products_dir, exist_ok=True)
    os.makedirs(categories_dir, exist_ok=True)
    os.makedirs(exports_dir, exist_ok=True)

    credits_csv_path = os.path.join(exports_dir, "image_credits.csv")
    credits_records = []

    # 2. Fetch Category Representative Images (8 Categories)
    print("\n--- INGESTING CATEGORY IMAGES (8 CATEGORIES) ---")
    cat_success = 0
    for cat_slug, search_terms in CATEGORY_SEARCH_TERMS.items():
        target_file = os.path.join(categories_dir, f"{cat_slug}.jpg")
        print(f"Category: {cat_slug} ... ", end="", flush=True)
        img_url, desc_url, lic, author = search_wikimedia(search_terms)
        if img_url and download_and_save_image(img_url, target_file):
            print(f"Downloaded ({lic})")
            cat_success += 1
            credits_records.append({
                'product_id': f"cat_{cat_slug}",
                'filename': f"categories/{cat_slug}.jpg",
                'source': 'downloaded',
                'source_url': desc_url,
                'licence': lic,
                'author': author
            })
            # Also save alternative underscore/ampersand variations if applicable
            if cat_slug == 'home_and_office':
                Image.open(target_file).save(os.path.join(categories_dir, "home_&_office.jpg"), 'JPEG', quality=80)
            elif cat_slug == 'fitness_and_sports':
                Image.open(target_file).save(os.path.join(categories_dir, "fitness_&_sports.jpg"), 'JPEG', quality=80)
            elif cat_slug == 'kitchen_and_dining':
                Image.open(target_file).save(os.path.join(categories_dir, "kitchen_&_dining.jpg"), 'JPEG', quality=80)
            elif cat_slug == 'travel_and_luggage':
                Image.open(target_file).save(os.path.join(categories_dir, "travel_&_luggage.jpg"), 'JPEG', quality=80)
        else:
            print("Failed")

    # 3. Fetch Product Images (120 Products)
    print("\n--- INGESTING PRODUCT IMAGES (120 PRODUCTS) ---")
    conn = sqlite3.connect(config.OPERATIONAL_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT product_id, product_name, category FROM PRODUCTS ORDER BY product_id ASC")
    products = cur.fetchall()
    conn.close()

    prod_downloaded = 0
    prod_missing = []

    for pid, pname, pcat in products:
        filename = f"product_{pid}.jpg"
        target_path = os.path.join(products_dir, filename)
        search_terms = PRODUCT_SEARCH_TERMS.get(pid, [pname, pcat])
        
        print(f"[{pid:3d}/120] {pname[:32]:32} ... ", end="", flush=True)
        img_url, desc_url, lic, author = search_wikimedia(search_terms)

        if img_url and download_and_save_image(img_url, target_path):
            print(f"OK ({lic[:20]})")
            prod_downloaded += 1
            credits_records.append({
                'product_id': pid,
                'filename': f"products/{filename}",
                'source': 'downloaded',
                'source_url': desc_url,
                'licence': lic,
                'author': author
            })
        else:
            print("NOT FOUND")
            prod_missing.append((pid, pname, pcat))

        # Respectful API rate limiting
        time.sleep(0.08)

    # 4. Save credits CSV
    with open(credits_csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['product_id', 'filename', 'source', 'source_url', 'licence', 'author']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(credits_records)

    # 5. Calculate total folder size
    total_bytes = 0
    for root, _, files in os.walk(os.path.join(config.BASE_DIR, "static", "images")):
        for f in files:
            total_bytes += os.path.getsize(os.path.join(root, f))
    total_mb = total_bytes / (1024 * 1024)

    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Categories successfully ingested: {cat_success} / 8")
    print(f"Products downloaded from Wikimedia: {prod_downloaded} / 120")
    print(f"Products missing: {len(prod_missing)}")
    if prod_missing:
        print("Missing product IDs:", [p[0] for p in prod_missing])
    print(f"Total static/images folder size: {total_mb:.2f} MB ({total_bytes} bytes)")
    print(f"Credits recorded in: {credits_csv_path}")


if __name__ == '__main__':
    run_pipeline()
