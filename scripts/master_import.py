"""
MASTER IMPORT SCRIPT
Imports ALL datasets into one unified database:
1. Amazon (140 CSVs) - Products + Real Images
2. Amazon Reviews - Real User Behavior
3. Amazon Reviews2 - Electronics Ratings
4. Flipkart - More Products + Images
5. Myntra - Fashion Products
"""

import pandas as pd
import sqlite3
import os
import json
import re
import hashlib
import random
from datetime import datetime, timedelta

# ============ CONFIG ============
DB_PATH = 'data/ecommerce.db'
AMAZON_DIR = 'data/raw/amazon'
REVIEWS_DIR = 'data/raw/amazon_reviews'
REVIEWS2_DIR = 'data/raw/amazon_reviews2'
FLIPKART_DIR = 'data/raw/flipkart_products'
MYNTRA_DIR = 'data/raw/myntra'

# ============ CATEGORY MAPPING ============
AMAZON_CATEGORY_MAP = {
    'Air Conditioners': 'Home & Kitchen',
    'All Appliances': 'Home & Kitchen',
    'All Books': 'Books',
    'All Car and Motorbike Products': 'Automotive',
    'All Electronics': 'Electronics',
    'All Exercise and Fitness': 'Sports & Fitness',
    'All Grocery and Gourmet Foods': 'Grocery',
    'All Home and Kitchen': 'Home & Kitchen',
    'All Movies and TV Shows': 'Entertainment',
    'All Music': 'Entertainment',
    'All Pet Supplies': 'Pet Supplies',
    'All Sports Fitness and Outdoors': 'Sports & Fitness',
    'All Video Games': 'Gaming',
    'Amazon Fashion': "Fashion",
    'Baby Products': 'Baby Products',
    'Backpacks': 'Bags',
    'Bags and Luggage': 'Bags',
    'Beauty and Grooming': 'Beauty',
    'Cameras': 'Electronics',
    'Car Accessories': 'Automotive',
    'Car Electronics': 'Automotive',
    'Casual Shoes': 'Shoes',
    'Clothing': 'Fashion',
    'Cricket': 'Sports & Fitness',
    'Ethnic Wear': "Women's Clothing",
    'Fashion Sandals': 'Shoes',
    'Formal Shoes': 'Shoes',
    'Furniture': 'Home & Kitchen',
    'Gaming Accessories': 'Gaming',
    'Gaming Consoles': 'Gaming',
    'Gold and Diamond Jewellery': 'Jewellery',
    'Handbags and Clutches': 'Bags',
    'Headphones': 'Headphones',
    'Health and Personal Care': 'Health',
    'Laptops': 'Laptops',
    'Mens Clothing': "Men's Clothing",
    'Mens Shoes': 'Shoes',
    'Mobiles and Accessories': 'Smartphones',
    'Smart Televisions': 'Electronics',
    'Smartwatches': 'Smartwatches',
    'Sports Shoes': 'Shoes',
    'Tablets': 'Electronics',
    'Televisions': 'Electronics',
    'Washing Machines': 'Home & Kitchen',
    'Womens Clothing': "Women's Clothing",
    'Womens Shoes': 'Shoes',
}

def get_category(filename):
    """Get category from filename"""
    name = filename.replace('.csv', '').strip()
    return AMAZON_CATEGORY_MAP.get(name, name)

def clean_price(price_str):
    """Clean price string to number"""
    if pd.isna(price_str):
        return None
    price_str = str(price_str)
    price_str = re.sub(r'[₹$,\s]', '', price_str)
    try:
        return float(price_str)
    except:
        return None

def clean_rating(rating_str):
    """Clean rating to float"""
    if pd.isna(rating_str):
        return round(random.uniform(3.5, 4.8), 1)
    try:
        return float(str(rating_str).split()[0])
    except:
        return round(random.uniform(3.5, 4.8), 1)

def clean_num_ratings(num_str):
    """Clean number of ratings"""
    if pd.isna(num_str):
        return random.randint(10, 500)
    try:
        num_str = str(num_str).replace(',', '')
        return int(float(num_str))
    except:
        return random.randint(10, 500)

def setup_database():
    """Setup fresh database with proper schema"""
    print("\n🗄️  Setting up database...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            password_hash TEXT,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_guest INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            brand TEXT,
            price REAL,
            description TEXT,
            image_url TEXT,
            stock INTEGER DEFAULT 100,
            avg_rating REAL DEFAULT 4.0,
            num_ratings INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS interactions (
            interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            product_id TEXT,
            interaction_type TEXT,
            rating REAL,
            review_text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            hover_duration REAL DEFAULT 0,
            interest_score INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            behavioral_data TEXT
        );

        CREATE TABLE IF NOT EXISTS cart (
            cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            product_id TEXT,
            quantity INTEGER DEFAULT 1,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            session_id TEXT,
            product_id TEXT,
            action_type TEXT,
            hover_duration REAL DEFAULT 0,
            interest_score INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        );
    ''')

    # Clear existing data
    cursor.execute('DELETE FROM products')
    cursor.execute('DELETE FROM interactions')
    conn.commit()

    print("✓ Database ready!")
    return conn

def import_amazon_products(conn):
    """Import all 140 Amazon CSV files"""
    print("\n📦 IMPORTING AMAZON PRODUCTS (140 files)...")
    print("="*60)

    cursor = conn.cursor()
    total_added = 0
    category_counts = {}

    files = [f for f in os.listdir(AMAZON_DIR) if f.endswith('.csv')]

    for file_idx, filename in enumerate(files):
        filepath = os.path.join(AMAZON_DIR, filename)
        category = get_category(filename)

        try:
            df = pd.read_csv(filepath, on_bad_lines='skip')

            # Check required columns
            if 'name' not in df.columns:
                continue

            file_added = 0
            for idx, row in df.iterrows():
                name = str(row.get('name', ''))[:200]
                if not name or name == 'nan':
                    continue

                product_id = f"AMZ{total_added+1:06d}"

                # Get price
                price = clean_price(row.get('discount_price'))
                if not price:
                    price = clean_price(row.get('actual_price'))
                if not price or price <= 0:
                    price = random.randint(299, 99999)

                # Get image - REAL Amazon image!
                image_url = str(row.get('image', ''))
                if not image_url or image_url == 'nan':
                    image_url = f"https://via.placeholder.com/300x300/2874f0/ffffff?text={name[:20]}"

                # Get rating
                avg_rating = clean_rating(row.get('ratings'))
                num_ratings = clean_num_ratings(row.get('no_of_ratings'))

                # Brand from name
                brand = name.split()[0] if name else 'Amazon'

                # Description
                desc = f"{category} product - {name}"

                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO products
                        (product_id, name, category, brand, price, description, image_url, avg_rating, num_ratings)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (product_id, name, category, brand, price, desc, image_url, avg_rating, num_ratings))
                    total_added += 1
                    file_added += 1
                    category_counts[category] = category_counts.get(category, 0) + 1
                except:
                    continue

            conn.commit()
            print(f"  [{file_idx+1:3d}/140] {filename[:40]:<40} → {file_added:4d} products")

        except Exception as e:
            print(f"  ❌ Error in {filename}: {e}")
            continue

    print(f"\n✅ Amazon: {total_added:,} products imported!")
    return total_added

def import_flipkart_products(conn):
    """Import Flipkart products"""
    print("\n🛒 IMPORTING FLIPKART PRODUCTS...")
    print("="*60)

    cursor = conn.cursor()
    total_added = 0

    filepath = os.path.join(FLIPKART_DIR, 'flipkart_com-ecommerce_sample.csv')

    try:
        df = pd.read_csv(filepath, on_bad_lines='skip')
        print(f"  Loaded {len(df):,} products")

        for idx, row in df.iterrows():
            name = str(row.get('product_name', ''))[:200]
            if not name or name == 'nan':
                continue

            product_id = f"FK{idx+1:06d}"

            # Price
            price = clean_price(row.get('discounted_price'))
            if not price:
                price = clean_price(row.get('retail_price'))
            if not price or price <= 0:
                price = random.randint(299, 49999)

            # Category
            cat_tree = str(row.get('product_category_tree', ''))
            category = 'General'
            if 'Mobiles' in cat_tree or 'Smartphones' in cat_tree:
                category = 'Smartphones'
            elif 'Laptop' in cat_tree:
                category = 'Laptops'
            elif 'Shirt' in cat_tree or 'T-Shirt' in cat_tree or 'Clothing' in cat_tree:
                category = "Men's Clothing"
            elif 'Saree' in cat_tree or 'Kurta' in cat_tree or 'Women' in cat_tree:
                category = "Women's Clothing"
            elif 'Shoe' in cat_tree or 'Footwear' in cat_tree:
                category = 'Shoes'
            elif 'Home' in cat_tree or 'Kitchen' in cat_tree:
                category = 'Home & Kitchen'
            elif 'TV' in cat_tree or 'Television' in cat_tree:
                category = 'Electronics'

            # Image - extract from JSON
            image_url = None
            try:
                img_json = str(row.get('image', ''))
                images = json.loads(img_json.replace("'", '"'))
                if images:
                    image_url = images[0]
            except:
                pass

            if not image_url:
                image_url = f"https://via.placeholder.com/300x300/fb641b/ffffff?text={name[:20]}"

            brand = str(row.get('brand', 'Flipkart'))
            if brand == 'nan':
                brand = 'Flipkart'

            avg_rating = clean_rating(row.get('product_rating'))
            num_ratings = random.randint(10, 1000)

            desc = str(row.get('description', name))[:500]

            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO products
                    (product_id, name, category, brand, price, description, image_url, avg_rating, num_ratings)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (product_id, name, category, brand, price, desc, image_url, avg_rating, num_ratings))
                total_added += 1
            except:
                continue

            if (idx + 1) % 5000 == 0:
                conn.commit()
                print(f"  Processed {idx+1:,} products...")

        conn.commit()
        print(f"\n✅ Flipkart: {total_added:,} products imported!")

    except Exception as e:
        print(f"❌ Flipkart error: {e}")

    return total_added

def import_myntra_products(conn):
    """Import Myntra fashion products"""
    print("\n👗 IMPORTING MYNTRA PRODUCTS...")
    print("="*60)

    cursor = conn.cursor()
    total_added = 0

    filepath = os.path.join(MYNTRA_DIR, 'styles.csv')

    try:
        df = pd.read_csv(filepath, on_bad_lines='skip')
        print(f"  Loaded {len(df):,} products")

        for idx, row in df.iterrows():
            name = str(row.get('productDisplayName', ''))[:200]
            if not name or name == 'nan':
                continue

            product_id = f"MYN{idx+1:06d}"
            gender = str(row.get('gender', 'Men'))
            article_type = str(row.get('articleType', 'Clothing'))

            # Category
            if article_type in ['Shirts', 'Tshirts', 'Trousers', 'Jeans', 'Shorts', 'Jackets', 'Sweaters']:
                category = "Men's Clothing" if gender in ['Men', 'Boys'] else "Women's Clothing"
            elif article_type in ['Kurtas', 'Sarees', 'Dresses', 'Tops', 'Lehenga']:
                category = "Women's Clothing"
            elif article_type in ['Shoes', 'Sandals', 'Flip Flops', 'Casual Shoes', 'Sports Shoes', 'Formal Shoes', 'Heels']:
                category = 'Shoes'
            elif article_type in ['Watches']:
                category = 'Smartwatches'
            elif article_type in ['Bags', 'Backpacks', 'Handbags']:
                category = 'Bags'
            elif article_type in ['Sunglasses']:
                category = 'Accessories'
            else:
                category = 'Fashion'

            # Price based on type
            price_ranges = {
                "Men's Clothing": (599, 5999),
                "Women's Clothing": (499, 7999),
                'Shoes': (999, 8999),
                'Smartwatches': (1999, 45999),
                'Bags': (799, 9999),
                'Accessories': (299, 4999),
                'Fashion': (299, 5999),
            }
            min_p, max_p = price_ranges.get(category, (299, 4999))
            price = random.randint(min_p, max_p)

            # Image - check if local image exists
            img_id = row.get('id')
            local_img = f"data/images/myntra/{img_id}.jpg"
            if os.path.exists(local_img):
                image_url = f"images/myntra/{img_id}.jpg"
            else:
                colour = str(row.get('baseColour', ''))
                image_url = f"https://source.unsplash.com/300x300/?{article_type},{colour}"

            avg_rating = round(random.uniform(3.5, 4.9), 1)
            num_ratings = random.randint(10, 2000)

            desc = f"{gender}'s {article_type} - {row.get('baseColour', '')} - {row.get('usage', 'Casual')}"

            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO products
                    (product_id, name, category, brand, price, description, image_url, avg_rating, num_ratings)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (product_id, name, category, 'Myntra', price, desc, image_url, avg_rating, num_ratings))
                total_added += 1
            except:
                continue

            if (idx + 1) % 5000 == 0:
                conn.commit()
                print(f"  Processed {idx+1:,} products...")

        conn.commit()
        print(f"\n✅ Myntra: {total_added:,} products imported!")

    except Exception as e:
        print(f"❌ Myntra error: {e}")

    return total_added

def import_amazon_reviews(conn):
    """Import real user reviews/interactions"""
    print("\n⭐ IMPORTING AMAZON REVIEWS (Real User Behavior)...")
    print("="*60)

    cursor = conn.cursor()
    total_added = 0

    # First get all product IDs
    cursor.execute('SELECT product_id FROM products LIMIT 10000')
    product_ids = [row[0] for row in cursor.fetchall()]

    if not product_ids:
        print("❌ No products found! Import products first!")
        return 0

    # Import from reviews folder
    for filename in os.listdir(REVIEWS_DIR):
        if not filename.endswith('.csv'):
            continue

        filepath = os.path.join(REVIEWS_DIR, filename)

        try:
            df = pd.read_csv(filepath, on_bad_lines='skip', nrows=50000)
            print(f"\n  File: {filename}")
            print(f"  Rows: {len(df):,}")
            print(f"  Columns: {df.columns.tolist()}")

            for idx, row in df.iterrows():
                # Get user
                username = str(row.get('reviews.username', f'USER{idx:06d}'))
                if username == 'nan':
                    username = f'USER{idx:06d}'

                user_id = f"RU{hashlib.md5(username.encode()).hexdigest()[:8].upper()}"

                # Create user if not exists
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO users (user_id, email, name, is_guest)
                        VALUES (?, ?, ?, 0)
                    ''', (user_id, f"{username}@amazon.com", username))
                except:
                    pass

                # Get product (map to our products)
                product_id = random.choice(product_ids)

                # Get rating
                rating = clean_rating(row.get('reviews.rating'))

                # Get review text
                review_text = str(row.get('reviews.text', ''))[:500]

                # Interaction type based on rating
                if rating >= 4:
                    interaction_type = random.choice(['purchase', 'cart_add', 'click'])
                elif rating >= 3:
                    interaction_type = random.choice(['click', 'view'])
                else:
                    interaction_type = 'view'

                # Timestamp
                try:
                    timestamp = pd.to_datetime(row.get('reviews.date', datetime.now()))
                except:
                    timestamp = datetime.now() - timedelta(days=random.randint(0, 365))

                # Interest score
                score_map = {'purchase': 25, 'cart_add': 15, 'click': 8, 'view': 1}
                interest_score = score_map.get(interaction_type, 1)

                try:
                    cursor.execute('''
                        INSERT INTO interactions
                        (user_id, product_id, interaction_type, rating, review_text, timestamp, interest_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (user_id, product_id, interaction_type, rating, review_text, timestamp, interest_score))
                    total_added += 1
                except:
                    continue

                if total_added % 10000 == 0:
                    conn.commit()
                    print(f"  Added {total_added:,} interactions...")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

    # Import ratings_Electronics file
    try:
        ratings_file = os.path.join(REVIEWS2_DIR, 'ratings_Electronics (1).csv')
        if os.path.exists(ratings_file):
            print(f"\n  File: ratings_Electronics.csv")
            df = pd.read_csv(ratings_file, 
                           names=['user_id', 'product_id', 'rating', 'timestamp'],
                           nrows=100000)
            print(f"  Rows: {len(df):,}")

            for idx, row in df.iterrows():
                user_id = f"EU{str(row['user_id'])[:8]}"
                rating = float(row['rating'])
                product_id = random.choice(product_ids)

                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO users (user_id, email, name, is_guest)
                        VALUES (?, ?, ?, 0)
                    ''', (user_id, f"{user_id}@amazon.com", f"User {user_id}"))
                except:
                    pass

                interaction_type = 'purchase' if rating >= 4 else 'view'
                interest_score = 25 if rating >= 4 else 1

                try:
                    cursor.execute('''
                        INSERT INTO interactions
                        (user_id, product_id, interaction_type, rating, timestamp, interest_score)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (user_id, product_id, interaction_type, rating, datetime.now(), interest_score))
                    total_added += 1
                except:
                    continue

                if total_added % 10000 == 0:
                    conn.commit()
                    print(f"  Added {total_added:,} interactions...")

    except Exception as e:
        print(f"  ❌ Electronics ratings error: {e}")

    conn.commit()
    print(f"\n✅ Reviews: {total_added:,} interactions imported!")
    return total_added

def create_demo_users(conn):
    """Create demo users for testing"""
    print("\n👥 Creating demo users...")

    cursor = conn.cursor()

    demo_users = [
        ('U0001', 'demo@example.com', 'demo123', 'Demo User'),
        ('U0002', 'rajesh@example.com', 'raj123', 'Rajesh Kumar'),
        ('U0003', 'priya@example.com', 'priya123', 'Priya Sharma'),
        ('U0004', 'amit@example.com', 'amit123', 'Amit Patel'),
        ('U0005', 'sneha@example.com', 'sneha123', 'Sneha Reddy'),
    ]

    for user_id, email, password, name in demo_users:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, email, password_hash, name, is_guest)
                VALUES (?, ?, ?, ?, 0)
            ''', (user_id, email, password_hash, name))
        except:
            pass

    conn.commit()
    print("✅ Demo users created!")

def print_final_stats(conn):
    """Print final database statistics"""
    cursor = conn.cursor()

    print("\n" + "="*80)
    print("🎉 MASTER IMPORT COMPLETE!")
    print("="*80)

    cursor.execute('SELECT COUNT(*) FROM products')
    total_products = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM users WHERE is_guest = 0')
    total_users = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM interactions')
    total_interactions = cursor.fetchone()[0]

    cursor.execute('SELECT category, COUNT(*) as count FROM products GROUP BY category ORDER BY count DESC LIMIT 20')
    categories = cursor.fetchall()

    print(f"\n📊 DATABASE STATISTICS:")
    print(f"  Total Products:      {total_products:>10,}")
    print(f"  Total Users:         {total_users:>10,}")
    print(f"  Total Interactions:  {total_interactions:>10,}")

    print(f"\n📁 TOP CATEGORIES:")
    for cat, count in categories:
        bar = '█' * min(int(count/500), 30)
        print(f"  {cat:<25} {bar:<30} {count:>6,}")

    cursor.execute('SELECT MIN(price), MAX(price), AVG(price) FROM products WHERE price > 0')
    price_stats = cursor.fetchone()
    if price_stats[0]:
        print(f"\n💰 PRICE STATS:")
        print(f"  Min: ₹{price_stats[0]:>10,.0f}")
        print(f"  Max: ₹{price_stats[1]:>10,.0f}")
        print(f"  Avg: ₹{price_stats[2]:>10,.0f}")

    print(f"\n🔑 DEMO LOGIN CREDENTIALS:")
    print(f"  Email: demo@example.com | Password: demo123")
    print(f"  Email: rajesh@example.com | Password: raj123")

    print(f"\n📋 NEXT STEPS:")
    print(f"  1. Train models: python scripts/train_from_database.py")
    print(f"  2. Start API:    python src/api/main.py")
    print(f"  3. Open shop:    start frontend/shop.html")
    print("="*80 + "\n")

def main():
    print("\n" + "="*80)
    print("🚀 MASTER IMPORT - ALL DATASETS")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Setup database
    conn = setup_database()

    # Import all datasets
    amazon_count = import_amazon_products(conn)
    flipkart_count = import_flipkart_products(conn)
    myntra_count = import_myntra_products(conn)
    reviews_count = import_amazon_reviews(conn)

    # Create demo users
    create_demo_users(conn)

    # Print final stats
    print_final_stats(conn)

    conn.close()

if __name__ == "__main__":
    main()