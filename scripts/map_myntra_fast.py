"""
FAST Myntra Image Mapping - Direct match only
"""
import sqlite3
import os
import pandas as pd

DB_PATH = 'data/ecommerce.db'
IMAGES_DIR = 'data/images/myntra'
MYNTRA_CSV = 'data/raw/myntra/styles.csv'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("\n⚡ FAST MYNTRA IMAGE MAPPING\n")

# Step 1: Get available images
available_images = {f.split('.')[0] for f in os.listdir(IMAGES_DIR) if f.endswith(('.jpg', '.png'))}
print(f"✅ Found {len(available_images):,} images\n")

# Step 2: Read CSV and create ID mapping
df = pd.read_csv(MYNTRA_CSV, on_bad_lines='skip', encoding='utf-8')
print(f"✅ Loaded {len(df):,} Myntra products\n")

# Create simple ID to image mapping
id_map = {}
for _, row in df.iterrows():
    img_id = str(row['id'])
    if img_id in available_images:
        id_map[img_id] = f"images/myntra/{img_id}.jpg"

print(f"✅ {len(id_map):,} images ready to map\n")

# Step 3: Match Myntra products by ID
print("Step 3: Matching Myntra products by ID...\n")

cursor.execute('''
    SELECT product_id FROM products 
    WHERE product_id LIKE 'MYN%'
''')

myntra_products = cursor.fetchall()
print(f"Found {len(myntra_products):,} Myntra products in database\n")

matched = 0
for (pid,) in myntra_products:
    # Extract numeric ID from product_id (MYN000123 -> 123)
    numeric_id = pid.replace('MYN', '').lstrip('0') or '0'
    
    if numeric_id in id_map:
        cursor.execute('UPDATE products SET image_url = ? WHERE product_id = ?', (id_map[numeric_id], pid))
        matched += 1

conn.commit()
print(f"✅ Matched {matched:,} Myntra products with REAL images!\n")

# Step 4: Create name-based placeholders for ALL other products
print("Step 4: Creating name placeholders for remaining products...\n")

colors = {
    'Smartphones': '2874f0', 'Laptops': '34a853', 'Electronics': '4285f4',
    'Headphones': 'ea4335', 'Clothing': 'fbbc04', 'Shoes': 'ff6d00',
    'Watches': '757575', 'Home & Kitchen': '00bfa5', 'Beauty': 'e91e63',
    'Sports & Fitness': 'ff5722',
}

cursor.execute('''
    SELECT product_id, name, category
    FROM products
    WHERE image_url NOT LIKE 'images/myntra/%'
''')

remaining = cursor.fetchall()
print(f"Creating placeholders for {len(remaining):,} products...\n")

batch = []
for pid, name, category in remaining:
    words = name.split()[:3]
    clean = '+'.join(w for w in words if w)[:50]
    color = colors.get(category, '333333')
    url = f"https://via.placeholder.com/400x400/{color}/ffffff?text={clean}"
    batch.append((url, pid))
    
    if len(batch) >= 10000:
        cursor.executemany('UPDATE products SET image_url = ? WHERE product_id = ?', batch)
        conn.commit()
        print(f"  {len(batch):,} done...")
        batch = []

if batch:
    cursor.executemany('UPDATE products SET image_url = ? WHERE product_id = ?', batch)
    conn.commit()

print(f"\n✅ All images updated!\n")

# Summary
cursor.execute("SELECT COUNT(*) FROM products WHERE image_url LIKE 'images/myntra/%'")
real = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM products")
total = cursor.fetchone()[0]

print("="*60)
print(f"Real Images:    {real:>10,} ({real/total*100:.1f}%)")
print(f"Placeholders:   {total-real:>10,} ({(total-real)/total*100:.1f}%)")
print(f"Total:          {total:>10,}")
print("="*60)

conn.close()
print("\n✅ DONE! Restart API now! 🚀\n")