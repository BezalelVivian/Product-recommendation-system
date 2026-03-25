import sqlite3
import re

conn = sqlite3.connect('data/ecommerce.db')
cursor = conn.cursor()

print("Fixing Amazon-Products category...")

# Update based on product name keywords
updates = [
    ("Smartphones", "%phone%"),
    ("Smartphones", "%mobile%"),
    ("Laptops", "%laptop%"),
    ("Laptops", "%notebook%"),
    ("Headphones", "%headphone%"),
    ("Headphones", "%earphone%"),
    ("Headphones", "%earbud%"),
    ("Smartwatches", "%watch%"),
    ("Cameras", "%camera%"),
    ("Televisions", "%television%"),
    ("Televisions", "%smart tv%"),
    ("Home & Kitchen", "%kitchen%"),
    ("Home & Kitchen", "%cooker%"),
    ("Sports & Fitness", "%fitness%"),
    ("Sports & Fitness", "%sport%"),
    ("Beauty", "%beauty%"),
    ("Beauty", "%makeup%"),
    ("Books", "%book%"),
    ("Clothing", "%shirt%"),
    ("Clothing", "%dress%"),
    ("Shoes", "%shoe%"),
    ("Shoes", "%sandal%"),
]

total_updated = 0
for category, pattern in updates:
    cursor.execute('''
        UPDATE products 
        SET category = ?
        WHERE category = 'Amazon-Products'
        AND LOWER(name) LIKE ?
    ''', (category, pattern))
    updated = cursor.rowcount
    total_updated += updated
    if updated > 0:
        print(f"  {category}: {updated:,} products")

conn.commit()

# Show new distribution
cursor.execute('''
    SELECT category, COUNT(*) as count 
    FROM products 
    GROUP BY category 
    ORDER BY count DESC 
    LIMIT 15
''')

print("\n📊 Updated Categories:")
for cat, count in cursor.fetchall():
    print(f"  {cat:<30} {count:>8,}")

conn.close()
print(f"\n✅ Fixed {total_updated:,} products!")