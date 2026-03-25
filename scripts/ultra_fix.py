"""
ULTRA FIX - Remove ALL wrong products from main categories
"""
import sqlite3

conn = sqlite3.connect('data/ecommerce.db')
cursor = conn.cursor()

print("\n⚡ ULTRA FIX - FINAL CLEANUP\n")

# STRICT RULES: If product name doesn't match category, move it out!
strict_fixes = [
    # Smartphones - ONLY actual phones
    ("Smartphones", ["phone", "mobile", "smartphone", "iphone", "galaxy", "redmi", "oneplus", "oppo", "vivo", "realme", "pixel", "nokia", "motorola", "poco", "iqoo", "nothing phone"], 
     ["conditioner", "fan", "cooler", "air", "iron", "steamer", "heater"]),
    
    # Laptops - ONLY actual laptops
    ("Laptops", ["laptop", "macbook", "notebook", "chromebook", "thinkpad", "pavilion laptop", "ideapad", "vivobook"],
     ["fix it", "pro uv", "cleaner", "polish", "cover", "bag", "stand"]),
    
    # Headphones - ONLY audio devices
    ("Headphones", ["headphone", "earphone", "earbud", "earbuds", "airpod", "neckband", "tws", "headset"],
     ["holder", "stand", "cover", "case"]),
    
    # Clothing - ONLY wearable clothes
    ("Clothing", ["shirt", "tshirt", "t-shirt", "trouser", "jeans", "jacket", "hoodie", "kurta", "kurti", "saree", "dress", "top", "blouse"],
     ["fan", "conditioner", "air", "cooler", "iron", "steamer", "heater", "machine"]),
    
    # Shoes - ONLY footwear
    ("Shoes", ["shoe", "shoes", "sneaker", "boot", "sandal", "slipper", "footwear", "flip flop"],
     ["odour", "absorber", "cleaner", "polish", "dryer", "rack", "iron", "teflon", "washing"]),
]

print("Removing mismatched products from main categories...\n")

for category, must_have, must_not_have in strict_fixes:
    # Build conditions
    must_conditions = " OR ".join([f"LOWER(name) LIKE '%{kw}%'" for kw in must_have])
    exclude_conditions = " AND ".join([f"LOWER(name) NOT LIKE '%{kw}%'" for kw in must_not_have])
    
    # Move products that DON'T match to General
    query = f'''
        UPDATE products
        SET category = 'General'
        WHERE category = ?
        AND NOT ({must_conditions})
    '''
    
    cursor.execute(query, (category,))
    count1 = cursor.rowcount
    
    # Also move products that have excluded keywords
    query2 = f'''
        UPDATE products
        SET category = 'General'
        WHERE category = ?
        AND NOT ({exclude_conditions})
    '''
    
    cursor.execute(query2, (category,))
    count2 = cursor.rowcount
    
    total = count1 + count2
    if total > 0:
        print(f"{category:<20} → Moved {total:>8,} wrong products to General")

conn.commit()

# Show clean results
print("\n📊 CLEAN MAIN CATEGORIES:\n")
for cat in ['Smartphones', 'Laptops', 'Headphones', 'Clothing', 'Shoes', 'Watches']:
    cursor.execute('SELECT COUNT(*) FROM products WHERE category = ?', (cat,))
    count = cursor.fetchone()[0]
    print(f"{cat:<20} {count:>10,} products")

# Sample check
print("\n📸 SAMPLE PRODUCTS:\n")
for cat in ['Smartphones', 'Laptops', 'Headphones']:
    cursor.execute('SELECT name FROM products WHERE category = ? LIMIT 3', (cat,))
    print(f"{cat}:")
    for (name,) in cursor.fetchall():
        print(f"  • {name[:60]}")
    print()

conn.close()
print("✅ ULTRA FIX COMPLETE!\n")