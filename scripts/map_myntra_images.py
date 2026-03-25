"""
Map Myntra real images to products
"""
import sqlite3
import os
import pandas as pd

DB_PATH = 'data/ecommerce.db'
IMAGES_DIR = 'data/images/myntra'
MYNTRA_CSV = 'data/raw/myntra/styles.csv'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("\n📸 MAPPING MYNTRA REAL IMAGES\n")

# Step 1: Check available images
available_images = set()
if os.path.exists(IMAGES_DIR):
    for f in os.listdir(IMAGES_DIR):
        if f.endswith(('.jpg', '.png', '.jpeg')):
            img_id = f.split('.')[0]
            available_images.add(img_id)
    print(f"✅ Found {len(available_images):,} real images in {IMAGES_DIR}\n")
else:
    print(f"❌ Images folder not found: {IMAGES_DIR}\n")
    conn.close()
    exit()

# Step 2: Read Myntra CSV to get product-image mapping
myntra_map = {}
if os.path.exists(MYNTRA_CSV):
    df = pd.read_csv(MYNTRA_CSV, on_bad_lines='skip', encoding='utf-8')
    print(f"✅ Loaded {len(df):,} products from Myntra CSV\n")
    
    for _, row in df.iterrows():
        img_id = str(row['id'])
        product_name = str(row.get('productDisplayName', ''))
        gender = str(row.get('gender', ''))
        article = str(row.get('articleType', ''))
        
        if img_id in available_images and product_name:
            myntra_map[product_name.lower()] = img_id
    
    print(f"✅ Created mapping for {len(myntra_map):,} products\n")
else:
    print(f"❌ Myntra CSV not found: {MYNTRA_CSV}\n")

# Step 3: Match products by name similarity
print("Step 3: Mapping images to products...\n")

matched = 0
not_matched = 0

# Get fashion/clothing/shoes products
cursor.execute('''
    SELECT product_id, name, category 
    FROM products 
    WHERE category IN (
        'Clothing', 'Shoes', 'Watches', 'Fashion', 
        'Fashion and Silver Jewellery', 'Accessories',
        'Bags', 'Sunglasses', 'Western Wear', 'Ethnic Wear',
        'Innerwear', 'Lingerie and Nightwear', 'Sportswear'
    )
''')

products = cursor.fetchall()
print(f"Processing {len(products):,} fashion products...\n")

for pid, name, category in products:
    name_lower = name.lower()
    
    # Try exact match first
    if name_lower in myntra_map:
        img_id = myntra_map[name_lower]
        img_url = f"images/myntra/{img_id}.jpg"
        cursor.execute('UPDATE products SET image_url = ? WHERE product_id = ?', (img_url, pid))
        matched += 1
    else:
        # Try partial match (first 3 words)
        words = name_lower.split()[:3]
        found = False
        for myntra_name, img_id in myntra_map.items():
            if all(word in myntra_name for word in words if len(word) > 3):
                img_url = f"images/myntra/{img_id}.jpg"
                cursor.execute('UPDATE products SET image_url = ? WHERE product_id = ?', (img_url, pid))
                matched += 1
                found = True
                break
        
        if not found:
            not_matched += 1
    
    if (matched + not_matched) % 10000 == 0:
        conn.commit()
        print(f"  Processed {matched + not_matched:,} products...")

conn.commit()

print(f"\n✅ Matched {matched:,} products with REAL images!")
print(f"⚠️  {not_matched:,} products still need images\n")

# Step 4: For remaining products, use product name placeholders
print("Step 4: Creating name-based placeholders for remaining products...\n")

cursor.execute('''
    SELECT product_id, name, category
    FROM products
    WHERE image_url NOT LIKE 'images/myntra/%'
''')

remaining = cursor.fetchall()
print(f"Creating placeholders for {len(remaining):,} products...\n")

updated = 0
for pid, name, category in remaining:
    # Clean name for URL (first 3 words)
    words = name.split()[:3]
    clean_name = '+'.join(words).replace('&', '').replace(',', '')[:50]
    
    # Color based on category
    colors = {
        'Smartphones': '2874f0',
        'Laptops': '34a853',
        'Electronics': '4285f4',
        'Headphones': 'ea4335',
        'Clothing': 'fbbc04',
        'Shoes': 'ff6d00',
        'Watches': '757575',
        'Home & Kitchen': '00bfa5',
        'Beauty': 'e91e63',
        'Sports & Fitness': 'ff5722',
    }
    
    color = colors.get(category, '333333')
    
    # Create placeholder with product name visible
    img_url = f"https://via.placeholder.com/400x400/{color}/ffffff?text={clean_name}"
    cursor.execute('UPDATE products SET image_url = ? WHERE product_id = ?', (img_url, pid))
    updated += 1
    
    if updated % 50000 == 0:
        conn.commit()
        print(f"  {updated:,} placeholders created...")

conn.commit()

print(f"\n✅ Created {updated:,} name-based placeholders!\n")

# Final summary
print("="*70)
print("📊 FINAL IMAGE SUMMARY")
print("="*70 + "\n")

cursor.execute("SELECT COUNT(*) FROM products WHERE image_url LIKE 'images/myntra/%'")
real_images = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM products WHERE image_url LIKE 'https://via.placeholder%'")
placeholders = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM products")
total = cursor.fetchone()[0]

print(f"Real Myntra Images:   {real_images:>10,} ({real_images/total*100:.1f}%)")
print(f"Name Placeholders:    {placeholders:>10,} ({placeholders/total*100:.1f}%)")
print(f"Total Products:       {total:>10,}")

# Show samples
print("\n📸 Sample Images:\n")
cursor.execute('''
    SELECT name, category, image_url 
    FROM products 
    WHERE image_url LIKE 'images/myntra/%'
    LIMIT 5
''')
print("REAL MYNTRA IMAGES:")
for name, cat, url in cursor.fetchall():
    print(f"  [{cat}] {name[:40]}")
    print(f"  → {url}\n")

conn.close()

print("="*70)
print("✅ IMAGE MAPPING COMPLETE!")
print("="*70)
print("\nRestart API and refresh browser to see REAL images! 🚀\n")