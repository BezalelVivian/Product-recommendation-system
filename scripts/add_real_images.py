"""
Add better image URLs for products
Uses product-specific keywords
"""

import sqlite3

def fix_images():
    print("\n🖼️ Updating product images...\n")
    
    conn = sqlite3.connect('data/ecommerce.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT product_id, name, category, brand FROM products')
    products = cursor.fetchall()
    
    updated = 0
    for pid, name, category, brand in products:
        # Create better search keywords
        keywords = f"{category},{brand},{name.split()[0]},{name.split()[1] if len(name.split()) > 1 else ''}"
        img_url = f"https://source.unsplash.com/400x400/?{keywords}"
        
        cursor.execute('UPDATE products SET image_url = ? WHERE product_id = ?', (img_url, pid))
        updated += 1
        
        if updated % 1000 == 0:
            print(f"Updated {updated} images...")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Updated {updated} product images!\n")

if __name__ == "__main__":
    fix_images()