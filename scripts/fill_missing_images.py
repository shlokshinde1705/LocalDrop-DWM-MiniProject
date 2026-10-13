import os
import re
import csv
import time
import requests
from io import BytesIO
from PIL import Image

HEADERS = {'User-Agent': 'LocalDropAcademic/1.0 (academic DWM project; contact: student@vit.edu)'}
WIKIMEDIA_API = 'https://commons.wikimedia.org/w/api.php'

FALLBACK_TERMS = {
    67: ['mandoline slicer kitchen', 'food chopper cutter', 'onion chopper'],
    83: ['duffel bag sports', 'duffle bag travel', 'travel bag duffle'],
    85: ['zipper carrying case pouch', 'hard shell case eva', 'travel gadget pouch'],
    88: ['laundry bag cotton drawstring', 'wash bag laundry travel', 'laundry bag'],
    92: ['jade roller facial tool', 'gua sha stone tool', 'massage roller stone'],
    95: ['manicure set grooming tools', 'nail clippers manicure kit', 'nail scissors manicure'],
    100: ['bath body brush wooden bristle', 'wooden body brush', 'dry skin brush'],
    101: ['essential oil amber bottle dropper', 'essential oil glass bottle', 'aromatherapy oil bottle'],
    106: ['blank notebook journal hardcover', 'moleskine notebook diary', 'leather journal notebook'],
    119: ['desk calendar planner notebook', 'spiral desk notepad planner', 'schedule planner pad'],
    120: ['craft scissors shears paper', 'embroidery scissors shears', 'tailor shears scissors']
}

products_dir = "static/images/products"
credits_csv_path = "exports/image_credits.csv"

# Load existing credits
credits = []
if os.path.exists(credits_csv_path):
    with open(credits_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        credits = list(reader)

saved_count = 0
still_missing = []

for pid, terms in FALLBACK_TERMS.items():
    target_path = os.path.join(products_dir, f"product_{pid}.jpg")
    found = False
    for t in terms:
        params = {
            'action': 'query',
            'generator': 'search',
            'gsrsearch': t,
            'gsrnamespace': 6,
            'gsrlimit': 6,
            'prop': 'imageinfo',
            'iiprop': 'url|size|mime|extmetadata',
            'iiurlwidth': 600,
            'format': 'json'
        }
        try:
            r = requests.get(WIKIMEDIA_API, headers=HEADERS, params=params, timeout=12)
            if r.status_code == 200:
                pages = r.json().get('query', {}).get('pages', {})
                for _, page in pages.items():
                    info = page.get('imageinfo', [{}])[0]
                    mime = info.get('mime', '')
                    if mime in ['image/jpeg', 'image/png', 'image/webp']:
                        title = page.get('title', '')
                        if any(x in title.lower() for x in ['flag of', 'coat of arms', 'map of', 'symbol of', 'insignia', 'logo']):
                            continue
                        img_url = info.get('thumburl') or info.get('url')
                        img_r = requests.get(img_url, headers=HEADERS, timeout=12)
                        if img_r.status_code == 200 and len(img_r.content) > 1000:
                            img = Image.open(BytesIO(img_r.content)).convert('RGB')
                            img.thumbnail((600, 600), Image.Resampling.LANCZOS)
                            img.save(target_path, 'JPEG', quality=80)

                            meta = info.get('extmetadata', {})
                            lic = meta.get('LicenseShortName', {}).get('value', 'CC BY-SA / Public Domain')
                            lic = re.sub('<[^<]+?>', '', lic).strip() or 'Creative Commons / Public Domain'
                            artist = meta.get('Artist', {}).get('value', 'Wikimedia Commons Contributor')
                            artist = re.sub('<[^<]+?>', '', artist).strip()[:80] or 'Wikimedia Contributor'
                            desc_url = info.get('descriptionurl', '')

                            credits.append({
                                'product_id': pid,
                                'filename': f"products/product_{pid}.jpg",
                                'source': 'downloaded',
                                'source_url': desc_url,
                                'licence': lic,
                                'author': artist
                            })
                            print(f"Product {pid}: Successfully downloaded via '{t}' ({lic})")
                            found = True
                            saved_count += 1
                            break
        except Exception:
            pass
        if found:
            break
        time.sleep(0.1)

    if not found:
        still_missing.append(pid)
        print(f"Product {pid}: Not found")

# Rewrite credits CSV
with open(credits_csv_path, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['product_id', 'filename', 'source', 'source_url', 'licence', 'author']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(credits)

print(f"\nSecondary search saved: {saved_count} / {len(FALLBACK_TERMS)}")
print(f"Still missing: {still_missing}")
