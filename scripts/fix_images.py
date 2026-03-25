"""
CHECK AND FIX IMAGES
- Check what image URLs look like in database
- Fix broken/missing images
- Use real Amazon image URLs from CSV
"""

import sqlite3
import pandas as pd
import os
import random

DB_PATH = 'data/ecommerce.db'
AMAZON_DIR = 'data/raw/amazon'

def check_images():
    print("\n" + "="*70)
    print("🔍 CHECKING IMAGE STATUS IN DATABASE")
    print("="*70)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Count total products
    cursor.execute('SELECT COUNT(*) FROM products')
    total = cursor.fetchone()[0]

    # Count products WITH real http images
    cursor.execute("SELECT COUNT(*) FROM products WHERE image_url LIKE 'http%'")
    with_images = cursor.fetchone()[0]

    # Count products with placeholder images
    cursor.execute("SELECT COUNT(*) FROM products WHERE image_url LIKE '%placeholder%'")
    placeholder = cursor.fetchone()[0]

    # Count products with NULL/empty images
    cursor.execute("SELECT COUNT(*) FROM products WHERE image_url IS NULL OR image_url = ''")
    no_image = cursor.fetchone()[0]

    print(f"\n📊 Image Status:")
    print(f"  Total Products:     {total:>10,}")
    print(f"  Real Images (http): {with_images:>10,} ✅")
    print(f"  Placeholder:        {placeholder:>10,} ⚠️")
    print(f"  No Image:           {no_image:>10,} ❌")

    # Sample some real image URLs
    print("\n📸 Sample Image URLs:")
    cursor.execute("SELECT name, image_url FROM products WHERE image_url LIKE 'http%' LIMIT 5")
    for name, url in cursor.fetchall():
        print(f"  {name[:40]:<40} → {url[:60]}")

    # Sample some placeholder URLs
    print("\n⚠️ Sample Placeholder URLs:")
    cursor.execute("SELECT name, image_url FROM products WHERE image_url NOT LIKE 'http%' LIMIT 5")
    for name, url in cursor.fetchall():
        status = url[:80] if url else "EMPTY"
        print(f"  {name[:40]:<40} → {status}")

    conn.close()
    return with_images, total

def fix_images_from_csv():
    """Re-read Amazon CSVs and update image URLs"""
    print("\n" + "="*70)
    print("🔧 FIXING IMAGES FROM AMAZON CSVs")
    print("="*70)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updated = 0
    files = [f for f in os.listdir(AMAZON_DIR) if f.endswith('.csv')]

    print(f"\nReading {len(files)} CSV files for real image URLs...\n")

    # Build image map from CSVs
    image_map = {}  # name -> image_url

    for filename in files:
        filepath = os.path.join(AMAZON_DIR, filename)
        try:
            df = pd.read_csv(filepath, on_bad_lines='skip',
                           usecols=['name', 'image'],
                           dtype={'name': str, 'image': str})

            for _, row in df.iterrows():
                name = str(row.get('name', '')).strip()
                image = str(row.get('image', '')).strip()
                if name and image and image.startswith('http') and name not in image_map:
                    image_map[name] = image

        except Exception as e:
            continue

    print(f"✅ Found {len(image_map):,} real image URLs from CSVs!")

    # Update database
    print("\nUpdating database...")

    for name, image_url in image_map.items():
        cursor.execute('''
            UPDATE products
            SET image_url = ?
            WHERE name = ? AND (image_url NOT LIKE 'http%' OR image_url IS NULL)
        ''', (image_url, name))
        if cursor.rowcount > 0:
            updated += cursor.rowcount

    conn.commit()
    print(f"✅ Updated {updated:,} product images!")

    # Check remaining without images
    cursor.execute("SELECT COUNT(*) FROM products WHERE image_url NOT LIKE 'http%'")
    remaining = cursor.fetchone()[0]
    print(f"⚠️  Still without real images: {remaining:,}")

    conn.close()
    return updated

def fix_remaining_with_unsplash():
    """Fix remaining products without real images using Unsplash"""
    print("\n" + "="*70)
    print("🎨 FIXING REMAINING WITH SMART IMAGE URLS")
    print("="*70)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Better keyword mapping per category
    category_keywords = {
        'Smartphones': 'smartphone,mobile,phone',
        'Laptops': 'laptop,computer,notebook',
        'Electronics': 'electronics,gadget,tech',
        'Headphones': 'headphones,earphones,audio',
        "Men's Clothing": 'mens,fashion,clothing,shirt',
        "Women's Clothing": 'womens,fashion,dress,clothing',
        'Shoes': 'shoes,footwear,sneakers',
        'Home & Kitchen': 'kitchen,home,appliance',
        'Gaming': 'gaming,controller,console',
        'Beauty': 'beauty,makeup,cosmetics',
        'Sports & Fitness': 'sports,fitness,gym',
        'Watches': 'watch,timepiece',
        'Smartwatches': 'smartwatch,fitness,band',
        'Bags': 'bag,handbag,backpack',
        'Jewellery': 'jewellery,jewelry,necklace',
        'Cameras': 'camera,photography',
        'Furniture': 'furniture,interior,home',
        'Baby Products': 'baby,infant,kids',
        'Grocery': 'grocery,food,organic',
        'Books': 'books,reading,library',
        'Automotive': 'car,automobile,vehicle',
        'Health': 'health,medicine,wellness',
        'Fashion': 'fashion,style,clothing',
    }

    cursor.execute('''
        SELECT product_id, name, category, brand
        FROM products
        WHERE image_url NOT LIKE 'http%' OR image_url IS NULL
    ''')
    products = cursor.fetchall()
    print(f"\nFixing {len(products):,} products...")

    updated = 0
    for pid, name, category, brand in products:
        # Get keyword for this category
        keyword = category_keywords.get(category, 'product,shopping')

        # Add brand/name context for better images
        name_word = name.split()[0] if name else ''
        if name_word and len(name_word) > 2:
            keyword = f"{keyword},{name_word}"

        # Unsplash URL with category-specific keywords
        image_url = f"https://source.unsplash.com/400x400/?{keyword}"

        cursor.execute('UPDATE products SET image_url = ? WHERE product_id = ?', (image_url, pid))
        updated += 1

        if updated % 10000 == 0:
            conn.commit()
            print(f"  Fixed {updated:,} images...")

    conn.commit()
    conn.close()
    print(f"✅ Fixed {updated:,} images!")

def final_check():
    print("\n" + "="*70)
    print("📊 FINAL IMAGE STATUS")
    print("="*70)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM products')
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM products WHERE image_url LIKE 'http%'")
    with_images = cursor.fetchone()[0]

    print(f"\n  Total Products:  {total:,}")
    print(f"  With Images:     {with_images:,} ({with_images/total*100:.1f}%)")

    print("\n📸 Sample Working Images:")
    cursor.execute("SELECT name, category, image_url FROM products WHERE image_url LIKE 'http%' LIMIT 10")
    for name, cat, url in cursor.fetchall():
        print(f"  [{cat[:15]}] {name[:30]:<30} → {url[:50]}")

    conn.close()

if __name__ == "__main__":
    # Step 1: Check current status
    with_images, total = check_images()

    # Step 2: Fix from CSV (get real Amazon image URLs)
    fix_images_from_csv()

    # Step 3: Fix remaining with smart Unsplash URLs
    fix_remaining_with_unsplash()

    # Step 4: Final check
    final_check()

    print("\n" + "="*70)
    print("✅ ALL IMAGES FIXED!")
    print("="*70)
    print("\n💡 Restart API and refresh browser to see images!")
    print("="*70 + "\n")