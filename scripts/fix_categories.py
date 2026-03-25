"""
Fix miscategorized products and empty categories
"""
import sqlite3

conn = sqlite3.connect('data/ecommerce.db')
cursor = conn.cursor()

print("\n🔧 FIXING CATEGORIES\n")

# Fix Fashion category (consolidate)
print("1. Fixing Fashion categories...")
cursor.execute('''
    UPDATE products 
    SET category = 'Fashion'
    WHERE category IN (
        'Amazon Fashion', 
        'Mens Fashion', 
        'Womens Fashion',
        'Fashion',
        'Fashion Sales and Deals'
    )
''')
print(f"   Updated {cursor.rowcount:,} fashion products")

# Fix phones in wrong categories
print("\n2. Moving phones to Smartphones...")
cursor.execute('''
    UPDATE products
    SET category = 'Smartphones'
    WHERE (
        LOWER(name) LIKE '%phone%'
        OR LOWER(name) LIKE '%mobile%'
        OR LOWER(name) LIKE '%smartphone%'
        OR LOWER(name) LIKE '%iphone%'
        OR LOWER(name) LIKE '%galaxy%'
        OR LOWER(name) LIKE '%redmi%'
        OR LOWER(name) LIKE '%oneplus%'
        OR LOWER(name) LIKE '%oppo%'
        OR LOWER(name) LIKE '%vivo%'
        OR LOWER(name) LIKE '%realme%'
        OR LOWER(name) LIKE '%pixel%'
        OR LOWER(name) LIKE '%nokia%'
    )
    AND category != 'Smartphones'
''')
print(f"   Moved {cursor.rowcount:,} phones to Smartphones")

# Fix headphones in wrong categories
print("\n3. Moving headphones/earphones to Headphones...")
cursor.execute('''
    UPDATE products
    SET category = 'Headphones'
    WHERE (
        LOWER(name) LIKE '%headphone%'
        OR LOWER(name) LIKE '%earphone%'
        OR LOWER(name) LIKE '%earbud%'
        OR LOWER(name) LIKE '%airpod%'
        OR LOWER(name) LIKE '%earbuds%'
        OR LOWER(name) LIKE '%headset%'
        OR LOWER(name) LIKE '%neckband%'
    )
    AND category != 'Headphones'
''')
print(f"   Moved {cursor.rowcount:,} audio products to Headphones")

# Fix laptops
print("\n4. Moving laptops to correct category...")
cursor.execute('''
    UPDATE products
    SET category = 'Laptops'
    WHERE (
        LOWER(name) LIKE '%laptop%'
        OR LOWER(name) LIKE '%macbook%'
        OR LOWER(name) LIKE '%notebook%'
        OR LOWER(name) LIKE '%chromebook%'
    )
    AND category != 'Laptops'
''')
print(f"   Moved {cursor.rowcount:,} laptops")

# Fix watches
print("\n5. Moving watches to correct category...")
cursor.execute('''
    UPDATE products
    SET category = 'Watches'
    WHERE (
        LOWER(name) LIKE '%watch%'
        OR LOWER(name) LIKE '%smartwatch%'
    )
    AND category NOT IN ('Watches', 'Smartwatches')
''')
print(f"   Moved {cursor.rowcount:,} watches")

conn.commit()

# Show category counts
print("\n📊 CATEGORY DISTRIBUTION AFTER FIX:\n")
cursor.execute('''
    SELECT category, COUNT(*) as count
    FROM products
    GROUP BY category
    HAVING count > 100
    ORDER BY count DESC
    LIMIT 30
''')

for cat, count in cursor.fetchall():
    print(f"  {cat:<30} {count:>8,} products")

conn.close()

print("\n✅ Categories fixed!\n")