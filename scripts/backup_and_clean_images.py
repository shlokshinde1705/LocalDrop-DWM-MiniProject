import os
import shutil

rejected_dir = os.path.join('static', 'images', '_rejected')
rejected_products = os.path.join(rejected_dir, 'products')
rejected_categories = os.path.join(rejected_dir, 'categories')
os.makedirs(rejected_products, exist_ok=True)
os.makedirs(rejected_categories, exist_ok=True)

for p in os.listdir('static/images/products'):
    shutil.copy2(os.path.join('static/images/products', p), os.path.join(rejected_products, p))

for c in os.listdir('static/images/categories'):
    shutil.copy2(os.path.join('static/images/categories', c), os.path.join(rejected_categories, c))

print("Backed up to _rejected:")
print("Products:", len(os.listdir(rejected_products)))
print("Categories:", len(os.listdir(rejected_categories)))

keep_products = {85, 92, 100}
removed_p = 0
for p in os.listdir('static/images/products'):
    pid_str = p.replace('product_', '').replace('.jpg', '')
    if pid_str.isdigit() and int(pid_str) in keep_products:
        continue
    os.remove(os.path.join('static/images/products', p))
    removed_p += 1

removed_c = 0
for c in os.listdir('static/images/categories'):
    os.remove(os.path.join('static/images/categories', c))
    removed_c += 1

print(f"Removed {removed_p} downloaded product images and {removed_c} category images.")
print("Remaining in static/images/products:", os.listdir('static/images/products'))
print("Remaining in static/images/categories:", os.listdir('static/images/categories'))
