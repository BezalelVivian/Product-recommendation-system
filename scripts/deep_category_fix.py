"""
DEEP CATEGORY FIX - Priority-based keyword matching
Analyzes product names and categorizes by PRIMARY product type
"""
import sqlite3

conn = sqlite3.connect('data/ecommerce.db')
cursor = conn.cursor()

print("\n🔍 DEEP CATEGORY ANALYSIS & FIX\n")

# PRIORITY ORDER: More specific categories first!
category_rules = [
    # PRIORITY 1: Exact product types (most specific)
    {
        'category': 'Smartphones',
        'must_have': ['phone', 'mobile', 'smartphone'],
        'exclude': ['holder', 'cover', 'case', 'stand', 'charger', 'cable'],
        'brands': ['iphone', 'galaxy', 'redmi', 'oneplus', 'oppo', 'vivo', 'realme', 'pixel', 'nokia', 'motorola', 'poco', 'iqoo', 'nothing phone']
    },
    {
        'category': 'Laptops',
        'must_have': ['laptop', 'macbook', 'notebook', 'chromebook'],
        'exclude': ['bag', 'stand', 'table', 'sleeve', 'cover', 'skin'],
        'brands': ['hp laptop', 'dell laptop', 'lenovo laptop', 'asus laptop', 'acer laptop', 'msi laptop']
    },
    {
        'category': 'Headphones',
        'must_have': ['headphone', 'earphone', 'earbud', 'earbuds', 'tws', 'airdope', 'airpod'],
        'exclude': ['cover', 'case', 'holder'],
        'brands': ['boat', 'jbl', 'sony headphone', 'bose']
    },
    {
        'category': 'Headphones',
        'must_have': ['neckband'],
        'exclude': [],
        'brands': []
    },
    {
        'category': 'Watches',
        'must_have': ['watch', 'wristwatch', 'timepiece'],
        'exclude': ['band', 'strap', 'holder', 'stand', 'neckband', 'fitness band', 'smart band'],
        'brands': ['rolex', 'titan', 'casio', 'fossil', 'timex', 'fastrack']
    },
    {
        'category': 'Smartwatches',
        'must_have': ['smartwatch', 'apple watch', 'galaxy watch', 'fitbit'],
        'exclude': ['band', 'strap'],
        'brands': ['noise', 'fire-boltt', 'amazfit', 'realme watch']
    },
    {
        'category': 'Fitness Bands',
        'must_have': ['fitness band', 'smart band', 'mi band', 'fitness tracker'],
        'exclude': [],
        'brands': []
    },
    
    # PRIORITY 2: Clothing (very specific keywords)
    {
        'category': 'Clothing',
        'must_have': ['shirt', 'tshirt', 't-shirt', 't shirt', 'polo', 'trouser', 'pant', 'jeans', 'jacket', 'hoodie', 'sweater', 'blazer', 'kurta', 'kurti', 'saree', 'dress', 'top', 'blouse', 'lehenga'],
        'exclude': ['phone', 'laptop', 'watch', 'shoe'],
        'brands': []
    },
    {
        'category': 'Shoes',
        'must_have': ['shoe', 'shoes', 'sneaker', 'boot', 'sandal', 'slipper', 'footwear', 'flip flop', 'floater'],
        'exclude': ['cover', 'lace', 'cleaner', 'polish'],
        'brands': ['nike', 'adidas', 'puma', 'reebok', 'skechers', 'woodland']
    },
    
    # PRIORITY 3: Electronics & Accessories
    {
        'category': 'Electronics',
        'must_have': ['pendrive', 'usb drive', 'flash drive', 'memory card', 'sd card'],
        'exclude': [],
        'brands': ['sandisk', 'samsung evo', 'hp pendrive']
    },
    {
        'category': 'Electronics',
        'must_have': ['router', 'wifi router', 'modem', 'range extender'],
        'exclude': [],
        'brands': ['tp-link', 'netgear', 'd-link']
    },
    {
        'category': 'Electronics',
        'must_have': ['cable', 'charger', 'adapter', 'power bank', 'powerbank', 'usb hub'],
        'exclude': [],
        'brands': []
    },
    {
        'category': 'Electronics',
        'must_have': ['mouse', 'keyboard', 'webcam', 'monitor', 'speaker', 'microphone'],
        'exclude': ['pad'],
        'brands': ['logitech', 'hp mouse', 'dell mouse']
    },
    {
        'category': 'Electronics',
        'must_have': ['television', 'smart tv', 'led tv', 'tv'],
        'exclude': ['stand', 'wall mount'],
        'brands': ['samsung tv', 'lg tv', 'sony tv', 'mi tv']
    },
    
    # PRIORITY 4: Home & Kitchen
    {
        'category': 'Home & Kitchen',
        'must_have': ['mixer', 'grinder', 'blender', 'toaster', 'kettle', 'cooker', 'oven', 'refrigerator', 'washing machine', 'air conditioner', 'ac', 'fan', 'geyser', 'iron', 'vacuum'],
        'exclude': [],
        'brands': ['bajaj', 'philips', 'prestige', 'pigeon', 'havells']
    },
    
    # PRIORITY 5: Sports & Fitness
    {
        'category': 'Sports & Fitness',
        'must_have': ['dumbbell', 'yoga mat', 'gym', 'treadmill', 'cycle', 'bicycle', 'football', 'cricket bat', 'badminton', 'tennis'],
        'exclude': ['holder', 'cover'],
        'brands': []
    },
    
    # PRIORITY 6: Beauty
    {
        'category': 'Beauty',
        'must_have': ['lipstick', 'makeup', 'cosmetic', 'perfume', 'shampoo', 'conditioner', 'face wash', 'cream', 'lotion', 'serum'],
        'exclude': [],
        'brands': ['lakme', 'maybelline', 'loreal']
    },
    
    # PRIORITY 7: Toys
    {
        'category': 'Toys',
        'must_have': ['toy', 'doll', 'lego', 'puzzle', 'board game', 'action figure'],
        'exclude': [],
        'brands': ['hasbro', 'mattel', 'funskool']
    },
]

# Statistics
total_fixed = 0
category_stats = {}

print("Analyzing and fixing products by priority...\n")

for idx, rule in enumerate(category_rules, 1):
    cat = rule['category']
    
    # Build WHERE clause
    must_conditions = []
    for keyword in rule['must_have']:
        must_conditions.append(f"LOWER(name) LIKE '%{keyword}%'")
    
    exclude_conditions = []
    for keyword in rule['exclude']:
        exclude_conditions.append(f"LOWER(name) NOT LIKE '%{keyword}%'")
    
    brand_conditions = []
    for brand in rule['brands']:
        brand_conditions.append(f"LOWER(name) LIKE '%{brand}%'")
    
    # Combine conditions
    where_parts = []
    
    if must_conditions:
        where_parts.append(f"({' OR '.join(must_conditions)})")
    
    if brand_conditions:
        where_parts.append(f"({' OR '.join(brand_conditions)})")
    
    if exclude_conditions:
        where_parts.append(f"({' AND '.join(exclude_conditions)})")
    
    if not where_parts:
        continue
    
    where_clause = ' AND '.join(where_parts)
    
    # Update products
    query = f'''
        UPDATE products
        SET category = ?
        WHERE ({where_clause})
        AND category != ?
    '''
    
    cursor.execute(query, (cat, cat))
    count = cursor.rowcount
    
    if count > 0:
        total_fixed += count
        category_stats[cat] = category_stats.get(cat, 0) + count
        print(f"[{idx:2d}] {cat:<25} → Fixed {count:>6,} products")

conn.commit()

# Show final distribution
print("\n" + "="*60)
print("📊 FINAL CATEGORY DISTRIBUTION")
print("="*60 + "\n")

cursor.execute('''
    SELECT category, COUNT(*) as cnt
    FROM products
    GROUP BY category
    HAVING cnt > 100
    ORDER BY cnt DESC
    LIMIT 25
''')

for cat, cnt in cursor.fetchall():
    bar = '█' * min(int(cnt/5000), 40)
    print(f"{cat:<30} {bar:<40} {cnt:>8,}")

# Show problematic products (multiple keywords)
print("\n" + "="*60)
print("⚠️  CHECKING FOR MIXED PRODUCTS")
print("="*60 + "\n")

mixed_checks = [
    ("Phone in Watches", "category = 'Watches' AND (LOWER(name) LIKE '%phone%' OR LOWER(name) LIKE '%mobile%')"),
    ("Laptop in Electronics", "category = 'Electronics' AND LOWER(name) LIKE '%laptop%'"),
    ("Neckband in Watches", "category = 'Watches' AND LOWER(name) LIKE '%neckband%'"),
    ("Pendrive in Smartphones", "category = 'Smartphones' AND (LOWER(name) LIKE '%pendrive%' OR LOWER(name) LIKE '%usb%')"),
]

for desc, condition in mixed_checks:
    cursor.execute(f"SELECT COUNT(*) FROM products WHERE {condition}")
    cnt = cursor.fetchone()[0]
    status = "❌" if cnt > 0 else "✅"
    print(f"{status} {desc:<30} {cnt:>6,} issues")

conn.close()

print("\n" + "="*60)
print(f"✅ Fixed {total_fixed:,} products!")
print("="*60 + "\n")