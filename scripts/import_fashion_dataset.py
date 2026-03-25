"""
Import Fashion Dataset (44K Indian products)
- Myntra/Jabong products
- Smart image generation (Unsplash)
- Realistic Indian user behavior
"""

import pandas as pd
import sqlite3
import hashlib
from datetime import datetime, timedelta
import random
import numpy as np

def generate_image_url(article_type, base_colour, product_name):
    """Generate relevant image URL using Unsplash"""
    # Map article types to search keywords
    keywords_map = {
        'Shirts': 'shirt,men',
        'Tshirts': 'tshirt',
        'Jeans': 'jeans,denim',
        'Trousers': 'trousers,pants',
        'Tops': 'top,women',
        'Dresses': 'dress,women',
        'Kurtas': 'kurta,indian',
        'Sarees': 'saree,indian',
        'Shoes': 'shoes,footwear',
        'Sandals': 'sandals',
        'Watches': 'watch',
        'Sunglasses': 'sunglasses',
        'Bags': 'bag',
        'Jackets': 'jacket',
        'Sweaters': 'sweater',
        'Shorts': 'shorts'
    }
    
    # Get keyword
    keyword = keywords_map.get(article_type, 'fashion')
    
    # Add color if meaningful
    if base_colour and base_colour.lower() not in ['multi', 'na', 'free size']:
        keyword = f"{keyword},{base_colour.lower()}"
    
    return f"https://source.unsplash.com/300x300/?{keyword}"

def calculate_price(article_type, gender, master_category, year):
    """Smart price calculation based on product attributes"""
    base_prices = {
        'Shirts': (799, 2499),
        'Tshirts': (399, 1299),
        'Jeans': (1299, 3999),
        'Trousers': (999, 2999),
        'Tops': (499, 1999),
        'Dresses': (999, 3999),
        'Kurtas': (799, 2999),
        'Sarees': (1499, 9999),
        'Shoes': (1499, 5999),
        'Sandals': (599, 2499),
        'Watches': (1999, 14999),
        'Sunglasses': (799, 4999),
        'Bags': (1299, 5999),
        'Jackets': (2499, 7999),
        'Sweaters': (1299, 3999)
    }
    
    min_p, max_p = base_prices.get(article_type, (499, 2999))
    
    # Adjust for gender
    if gender == 'Women':
        min_p = int(min_p * 1.1)
        max_p = int(max_p * 1.15)
    
    # Adjust for year (newer = pricier)
    if year and year >= 2018:
        max_p = int(max_p * 1.2)
    
    return random.randint(min_p, max_p)

def import_fashion_dataset():
    print("\n" + "="*80)
    print("👔 IMPORTING FASHION DATASET (44K Products)")
    print("="*80 + "\n")
    
    # Load CSV
    print("📂 Loading styles.csv...")
    try:
        df = pd.read_csv('data/raw/styles.csv', on_bad_lines='skip')
        print(f"✓ Loaded {len(df)} products\n")
    except FileNotFoundError:
        print("❌ File not found: data/raw/styles.csv")
        print("\nPlease copy styles.csv to data/raw/")
        return
    
    # Show dataset info
    print("📊 Dataset Overview:")
    print(f"  Columns: {df.columns.tolist()}")
    print(f"  Gender distribution:")
    if 'gender' in df.columns:
        print(df['gender'].value_counts().to_string())
    print()
    
    # Connect to database
    conn = sqlite3.connect('data/ecommerce.db')
    cursor = conn.cursor()
    
    # Clear existing products
    print("🗑️  Clearing old products...")
    cursor.execute('DELETE FROM products')
    cursor.execute('DELETE FROM interactions')
    conn.commit()
    
    # Process products
    print("\n📦 Processing products...")
    
    products_added = 0
    
    # Gender distribution tracking (Male 70%, Female 20%, Kids 10%)
    male_count = 0
    female_count = 0
    kids_count = 0
    
    for idx, row in df.iterrows():
        # Skip if essential data missing
        if pd.isna(row.get('articleType')):
            continue
        
        # Gender filtering for distribution
        gender = str(row.get('gender', 'Men'))
        
        # Apply distribution (approximate)
        if gender == 'Men':
            if male_count > len(df) * 0.7:
                continue
            male_count += 1
        elif gender == 'Women':
            if female_count > len(df) * 0.2:
                continue
            female_count += 1
        elif gender in ['Boys', 'Girls', 'Unisex']:
            if kids_count > len(df) * 0.1:
                continue
            kids_count += 1
        
        # Extract data
        product_id = f"M{row.get('id', idx):06d}"
        
        product_name = str(row.get('productDisplayName', f"{row.get('articleType', 'Product')} {idx}"))[:200]
        
        # Category mapping
        article_type = str(row.get('articleType', 'Apparel'))
        sub_category = str(row.get('subCategory', 'Clothing'))
        
        # Map to our categories
        if article_type in ['Shirts', 'Tshirts', 'Kurtas', 'Sweaters', 'Jackets']:
            if gender == 'Women':
                category = "Women's Clothing"
            else:
                category = "Men's Clothing"
        elif article_type in ['Jeans', 'Trousers', 'Shorts']:
            category = "Men's Clothing" if gender == 'Men' else "Women's Clothing"
        elif article_type in ['Dresses', 'Tops', 'Sarees', 'Lehenga']:
            category = "Women's Clothing"
        elif article_type in ['Shoes', 'Sandals', 'Flip Flops', 'Casual Shoes', 'Sports Shoes']:
            category = 'Shoes'
        elif article_type in ['Watches']:
            category = 'Smartwatches'
        elif article_type in ['Bags', 'Backpacks', 'Handbags']:
            category = 'Accessories'
        else:
            category = 'Fashion'
        
        # Brand
        brand = 'Indian Brand'  # Dataset doesn't have brand, using generic
        
        # Price
        price = calculate_price(
            article_type, 
            gender, 
            str(row.get('masterCategory', '')),
            row.get('year')
        )
        
        # Description
        description = f"{gender}'s {article_type} - {row.get('baseColour', 'Colored')} - {row.get('season', 'All Season')} - {row.get('usage', 'Casual')}"
        
        # Generate image URL
        image_url = generate_image_url(
            article_type,
            str(row.get('baseColour', '')),
            product_name
        )
        
        # Rating
        avg_rating = round(random.uniform(3.5, 4.8), 1)
        num_ratings = random.randint(10, 500)
        
        # Insert
        try:
            cursor.execute('''
                INSERT INTO products (
                    product_id, name, category, brand, price,
                    description, image_url, avg_rating, num_ratings
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product_id, product_name, category, brand, price,
                description, image_url, avg_rating, num_ratings
            ))
            
            products_added += 1
            
            if (idx + 1) % 5000 == 0:
                print(f"  Processed {idx + 1} products...")
                conn.commit()
        except Exception as e:
            continue
    
    conn.commit()
    
    print(f"\n✓ Added {products_added} products")
    
    # Generate realistic interactions
    print("\n👥 Generating realistic Indian user interactions...")
    
    # Get all products
    cursor.execute('SELECT product_id, category, price FROM products')
    products = cursor.fetchall()
    
    # Create demo users
    demo_users = [
        ('U0001', 'demo@example.com', 'Demo User'),
        ('U0002', 'rajesh@example.com', 'Rajesh Kumar'),
        ('U0003', 'priya@example.com', 'Priya Sharma'),
        ('U0004', 'amit@example.com', 'Amit Patel'),
        ('U0005', 'sneha@example.com', 'Sneha Reddy'),
    ]
    
    for user_id, email, name in demo_users:
        try:
            password_hash = hashlib.sha256('password123'.encode()).hexdigest()
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, email, password_hash, name, is_guest)
                VALUES (?, ?, ?, ?, 0)
            ''', (user_id, email, password_hash, name))
        except:
            pass
    
    # Generate interactions (realistic patterns)
    num_interactions = min(10000, len(products) * 3)
    
    interaction_types = ['view', 'hover', 'click', 'cart_add', 'purchase']
    weights = [50, 30, 15, 3, 2]  # Realistic distribution
    
    for _ in range(num_interactions):
        user_id = random.choice(['U0001', 'U0002', 'U0003', 'U0004', 'U0005'])
        product = random.choice(products)
        interaction_type = random.choices(interaction_types, weights=weights)[0]
        
        hover_duration = 0
        if interaction_type == 'hover':
            hover_duration = round(random.uniform(1.5, 8.0), 1)
        
        timestamp = datetime.now() - timedelta(days=random.randint(0, 60))
        
        try:
            cursor.execute('''
                INSERT INTO interactions (
                    user_id, product_id, interaction_type,
                    hover_duration, timestamp
                ) VALUES (?, ?, ?, ?, ?)
            ''', (user_id, product[0], interaction_type, hover_duration, timestamp))
        except:
            continue
    
    conn.commit()
    
    # Stats
    cursor.execute('SELECT COUNT(DISTINCT category) FROM products')
    num_categories = cursor.fetchone()[0]
    
    cursor.execute('SELECT MIN(price), MAX(price), AVG(price) FROM products')
    price_stats = cursor.fetchone()
    
    #cursor.execute('SELECT gender, COUNT(*) FROM (SELECT category FROM products) GROUP BY category')
    
    conn.close()
    
    print(f"✓ Generated {num_interactions} realistic interactions")
    
    print("\n" + "="*80)
    print("✅ FASHION DATASET IMPORTED!")
    print("="*80)
    print(f"\n📊 Statistics:")
    print(f"  Products:        {products_added:,}")
    print(f"  Male products:   {male_count:,} (~{male_count/products_added*100:.0f}%)")
    print(f"  Female products: {female_count:,} (~{female_count/products_added*100:.0f}%)")
    print(f"  Kids products:   {kids_count:,} (~{kids_count/products_added*100:.0f}%)")
    print(f"  Categories:      {num_categories}")
    print(f"  Price Range:     ₹{price_stats[0]:.0f} - ₹{price_stats[1]:.0f}")
    print(f"  Avg Price:       ₹{price_stats[2]:.0f}")
    print(f"  Interactions:    {num_interactions:,}")
    print(f"  Users:           5")
    
    print("\n📋 Next Steps:")
    print("  1. Train: python scripts/train_from_database.py")
    print("  2. Start API: python src/api/main.py")
    print("  3. Browse: start frontend/shop.html")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    import_fashion_dataset()