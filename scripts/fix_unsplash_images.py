"""
Fix Unsplash image URLs with CORRECT categories
"""
import sqlite3

conn = sqlite3.connect('data/ecommerce.db')
cursor = conn.cursor()

print("\n🖼️  FIXING IMAGE URLs\n")

# Get all products
cursor.execute('SELECT product_id, name, category FROM products')
products = cursor.fetchall()

print(f"Updating {len(products):,} image URLs...\n")

updated = 0
for pid, name, category in products:
    # Clean product name - first 2 words only
    words = name.split()[:2]
    clean_name = '+'.join(words).replace('&', '').replace(',', '')
    
    # Use CURRENT category (not old one!)
    clean_cat = category.replace(' ', '+').replace('&', '')
    
    # Better Unsplash URL
    img_url = f"https://source.unsplash.com/400x400/?{clean_name},{clean_cat}"
    
    cursor.execute('UPDATE products SET image_url = ? WHERE product_id = ?', (img_url, pid))
    updated += 1
    
    if updated % 50000 == 0:
        conn.commit()
        print(f"  {updated:,} done...")

conn.commit()
print(f"\n✅ Updated {updated:,} image URLs with correct categories!\n")

# Show samples
print("📸 Sample URLs:\n")
for cat in ['Smartphones', 'Laptops', 'Headphones', 'Clothing', 'Shoes']:
    cursor.execute('SELECT name, image_url FROM products WHERE category = ? LIMIT 1', (cat,))
    result = cursor.fetchone()
    if result:
        name, url = result
        print(f"{cat}:")
        print(f"  {name[:50]}")
        print(f"  {url}\n")

conn.close()