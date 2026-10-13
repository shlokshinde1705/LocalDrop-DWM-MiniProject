import os
import glob
from PIL import Image

brain_dir = r'C:\Users\SHLOK\.gemini\antigravity\brain\6c1e8348-38cb-4384-8e04-6f6a7bbc1974'

# Categories to process
cat_mapping = {
    'electronics': 'cat_electronics',
    'mobile_accessories': 'cat_mobile_acc',
    'home_and_office': 'cat_home_office',
    'fitness_and_sports': 'cat_fitness_sports',
    'kitchen_and_dining': 'cat_kitchen_dining',
    'travel_and_luggage': 'cat_travel_luggage',
    'personal_care': 'cat_personal_care',
    'stationery': 'cat_stationery'
}

cat_dir = os.path.join('static', 'images', 'categories')
os.makedirs(cat_dir, exist_ok=True)

for slug, prefix in cat_mapping.items():
    matches = glob.glob(os.path.join(brain_dir, f'{prefix}_*.jpg'))
    if not matches:
        print(f'Missing category image for {slug} ({prefix})')
        continue
    src = sorted(matches)[-1]
    dst = os.path.join(cat_dir, f'{slug}.jpg')
    im = Image.open(src).convert('RGB')
    im.thumbnail((600, 600), Image.Resampling.LANCZOS)
    im.save(dst, 'JPEG', quality=80, optimize=True)
    # Also save ampersand alias if applicable
    if '_and_' in slug:
        amp_dst = os.path.join(cat_dir, f"{slug.replace('_and_', '_&_')}.jpg")
        im.save(amp_dst, 'JPEG', quality=80, optimize=True)
    print(f'Processed category {slug} from {os.path.basename(src)}')

# Products to process
prod_mapping = {
    20: 'product_20_carmount',
    40: 'product_40_screenbar',
    85: 'eva_electronics_case',
    92: 'jade_roller_set',
    100: 'dry_body_brush'
}

prod_dir = os.path.join('static', 'images', 'products')
os.makedirs(prod_dir, exist_ok=True)

for pid, prefix in prod_mapping.items():
    matches = glob.glob(os.path.join(brain_dir, f'{prefix}_*.jpg'))
    if not matches:
        print(f'Missing product image for {pid} ({prefix})')
        continue
    src = sorted(matches)[-1]
    dst = os.path.join(prod_dir, f'product_{pid}.jpg')
    im = Image.open(src).convert('RGB')
    im.thumbnail((600, 600), Image.Resampling.LANCZOS)
    im.save(dst, 'JPEG', quality=80, optimize=True)
    print(f'Processed product {pid} from {os.path.basename(src)}')

print("Finished processing new studio images.")
