"""
Create Real E-commerce Database with Proper Products
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import hashlib

np.random.seed(42)
random.seed(42)

# Real product data
# Real product data - INDIAN MARKET
PRODUCTS = [
    # Electronics - Smartphones
    {"name": "iPhone 15 Pro", "category": "Smartphones", "brand": "Apple", "price": 134900, "description": "Latest iPhone with A17 Pro chip, titanium design, 48MP camera"},
    {"name": "Samsung Galaxy S24 Ultra", "category": "Smartphones", "brand": "Samsung", "price": 129999, "description": "Flagship Android phone with S Pen, 200MP camera, AI features"},
    {"name": "OnePlus 12", "category": "Smartphones", "brand": "OnePlus", "price": 64999, "description": "Fast charging, Snapdragon 8 Gen 3, 120Hz display"},
    {"name": "Google Pixel 8 Pro", "category": "Smartphones", "brand": "Google", "price": 106999, "description": "Best camera phone, pure Android, AI magic eraser"},
    {"name": "Xiaomi 14 Pro", "category": "Smartphones", "brand": "Xiaomi", "price": 79999, "description": "Value flagship, Leica camera, 120W fast charging"},
    {"name": "Redmi Note 13 Pro", "category": "Smartphones", "brand": "Redmi", "price": 24999, "description": "200MP camera, AMOLED display, 67W charging"},
    {"name": "Realme 12 Pro+", "category": "Smartphones", "brand": "Realme", "price": 29999, "description": "Periscope telephoto, curved display, fast performance"},
    {"name": "Vivo V30 Pro", "category": "Smartphones", "brand": "Vivo", "price": 41999, "description": "50MP selfie camera, Aura Light, slim design"},
    {"name": "Nothing Phone 2", "category": "Smartphones", "brand": "Nothing", "price": 44999, "description": "Glyph interface, unique design, flagship specs"},
    {"name": "IQOO 12", "category": "Smartphones", "brand": "iQOO", "price": 52999, "description": "Gaming phone, Snapdragon 8 Gen 3, 120W charging"},
    
    # Electronics - Laptops
    {"name": "MacBook Air M2", "category": "Laptops", "brand": "Apple", "price": 114900, "description": "M2 chip, 13.6-inch display, all-day battery"},
    {"name": "Dell Inspiron 15", "category": "Laptops", "brand": "Dell", "price": 54990, "description": "Intel Core i5, 15.6-inch FHD, perfect for work"},
    {"name": "HP Pavilion 14", "category": "Laptops", "brand": "HP", "price": 62990, "description": "AMD Ryzen 7, 14-inch, lightweight, long battery"},
    {"name": "Lenovo IdeaPad Slim 3", "category": "Laptops", "brand": "Lenovo", "price": 42990, "description": "Student laptop, good performance, affordable"},
    {"name": "ASUS VivoBook 15", "category": "Laptops", "brand": "ASUS", "price": 48990, "description": "Thin & light, good battery, everyday computing"},
    {"name": "Acer Aspire 5", "category": "Laptops", "brand": "Acer", "price": 44990, "description": "15.6-inch FHD, Intel i5, best value laptop"},
    
    # Electronics - Headphones
    {"name": "Sony WH-1000XM5", "category": "Headphones", "brand": "Sony", "price": 29990, "description": "Best noise cancellation, 30hr battery, premium sound"},
    {"name": "AirPods Pro 2", "category": "Headphones", "brand": "Apple", "price": 26900, "description": "Active noise cancellation, spatial audio, USB-C"},
    {"name": "Boat Rockerz 450", "category": "Headphones", "brand": "boAt", "price": 1499, "description": "40hr battery, powerful bass, affordable"},
    {"name": "JBL Tune 510BT", "category": "Headphones", "brand": "JBL", "price": 2999, "description": "Wireless on-ear, JBL Pure Bass, foldable"},
    {"name": "Realme Buds Air 3", "category": "Headphones", "brand": "Realme", "price": 3499, "description": "TWS earbuds, ANC, 30hr playback"},
    {"name": "OnePlus Bullets Z2", "category": "Headphones", "brand": "OnePlus", "price": 1999, "description": "Neckband, 30hr battery, Bombastic Bass"},
    
    # Electronics - Smartwatches
    {"name": "Apple Watch Series 9", "category": "Smartwatches", "brand": "Apple", "price": 45900, "description": "Double tap gesture, always-on display, health tracking"},
    {"name": "Samsung Galaxy Watch 6", "category": "Smartwatches", "brand": "Samsung", "price": 30999, "description": "Wear OS, rotating bezel, fitness tracking"},
    {"name": "Noise ColorFit Pro 4", "category": "Smartwatches", "brand": "Noise", "price": 3999, "description": "1.78-inch display, 100 sports modes, 7-day battery"},
    {"name": "Fire-Boltt Phoenix Pro", "category": "Smartwatches", "brand": "Fire-Boltt", "price": 1999, "description": "Bluetooth calling, SpO2, large display"},
    {"name": "boAt Wave Call", "category": "Smartwatches", "brand": "boAt", "price": 2499, "description": "Bluetooth calling, 7-day battery, IP68"},
    
    # Fashion - Men's Clothing
    {"name": "Levi's 511 Slim Fit Jeans", "category": "Men's Clothing", "brand": "Levi's", "price": 3499, "description": "Classic slim fit, comfortable stretch denim"},
    {"name": "Nike Dri-FIT T-Shirt", "category": "Men's Clothing", "brand": "Nike", "price": 1299, "description": "Moisture-wicking, sports tee, breathable"},
    {"name": "Adidas Training Hoodie", "category": "Men's Clothing", "brand": "Adidas", "price": 2999, "description": "Cotton blend, trefoil logo, comfortable"},
    {"name": "US Polo Cotton Shirt", "category": "Men's Clothing", "brand": "US Polo", "price": 1799, "description": "Regular fit, casual shirt, pure cotton"},
    {"name": "Allen Solly Formal Shirt", "category": "Men's Clothing", "brand": "Allen Solly", "price": 1499, "description": "Formal wear, slim fit, office-ready"},
    {"name": "Peter England Trousers", "category": "Men's Clothing", "brand": "Peter England", "price": 1999, "description": "Formal trousers, comfortable fit"},
    
    # Fashion - Women's Clothing
    {"name": "FabIndia Kurta", "category": "Women's Clothing", "brand": "FabIndia", "price": 1899, "description": "Cotton kurta, traditional design, comfortable"},
    {"name": "Biba Ethnic Dress", "category": "Women's Clothing", "brand": "Biba", "price": 2499, "description": "Ethnic wear, stylish design, festival ready"},
    {"name": "W for Woman Top", "category": "Women's Clothing", "brand": "W", "price": 1299, "description": "Western wear, trendy top, multiple colors"},
    {"name": "Aurelia Printed Kurta", "category": "Women's Clothing", "brand": "Aurelia", "price": 1699, "description": "Floral print, A-line kurta, daily wear"},
    
    # Fashion - Shoes
    {"name": "Nike Air Max Impact", "category": "Shoes", "brand": "Nike", "price": 6995, "description": "Sports shoes, Max Air cushioning, running"},
    {"name": "Adidas Ultraboost", "category": "Shoes", "brand": "Adidas", "price": 9999, "description": "Premium running shoes, Boost technology"},
    {"name": "Puma Smash v2", "category": "Shoes", "brand": "Puma", "price": 2999, "description": "Casual sneakers, classic design, everyday wear"},
    {"name": "Bata Red Label Formal", "category": "Shoes", "brand": "Bata", "price": 2499, "description": "Formal shoes, leather, office wear"},
    {"name": "Sparx Running Shoes", "category": "Shoes", "brand": "Sparx", "price": 1499, "description": "Budget running shoes, comfortable, durable"},
    {"name": "Campus Casual Sneakers", "category": "Shoes", "brand": "Campus", "price": 1299, "description": "Trendy sneakers, lightweight, affordable"},
    
    # Home & Kitchen
    {"name": "Prestige Induction Cooktop", "category": "Home & Kitchen", "brand": "Prestige", "price": 2499, "description": "2000W, automatic whistle, Indian cooking"},
    {"name": "Philips Air Fryer", "category": "Home & Kitchen", "brand": "Philips", "price": 8999, "description": "Oil-free cooking, 4.1L capacity, healthy"},
    {"name": "Bajaj Mixer Grinder", "category": "Home & Kitchen", "brand": "Bajaj", "price": 3499, "description": "750W, 3 jars, Indian kitchen essential"},
    {"name": "Hawkins Pressure Cooker", "category": "Home & Kitchen", "brand": "Hawkins", "price": 2299, "description": "5L inner lid, aluminum, durable"},
    {"name": "Butterfly Wet Grinder", "category": "Home & Kitchen", "brand": "Butterfly", "price": 5999, "description": "2L, stone grinder, for idli/dosa batter"},
    
    # Books (Indian Authors & Topics)
    {"name": "The White Tiger - Aravind Adiga", "category": "Books", "brand": "Penguin", "price": 299, "description": "Man Booker Prize winner, Indian story"},
    {"name": "The God of Small Things", "category": "Books", "brand": "Penguin", "price": 399, "description": "Arundhati Roy, Booker Prize winner"},
    {"name": "Sacred Games - Vikram Chandra", "category": "Books", "brand": "Penguin", "price": 499, "description": "Mumbai crime thriller, bestseller"},
    {"name": "Malgudi Days - R.K. Narayan", "category": "Books", "brand": "Penguin", "price": 250, "description": "Classic Indian short stories"},
    
    # Gaming
    {"name": "PS5 Digital Edition", "category": "Gaming", "brand": "Sony", "price": 44990, "description": "Next-gen gaming, 4K, DualSense controller"},
    {"name": "Xbox Series S", "category": "Gaming", "brand": "Microsoft", "price": 36990, "description": "Compact console, Game Pass, 1440p gaming"},
    {"name": "Logitech G102 Mouse", "category": "Gaming", "brand": "Logitech", "price": 1295, "description": "Gaming mouse, RGB, 8000 DPI"},
    {"name": "Cosmic Byte Keyboard", "category": "Gaming", "brand": "Cosmic Byte", "price": 1499, "description": "Mechanical keyboard, RGB, budget gaming"},
    {"name": "Redgear Pro Gamepad", "category": "Gaming", "brand": "Redgear", "price": 699, "description": "Wired controller, PC gaming, affordable"},
]
def create_database():
    """Create SQLite database with all tables"""
    print("Creating database...")
    
    conn = sqlite3.connect('data/ecommerce.db')
    cursor = conn.cursor()
    
    # Drop existing tables
    cursor.execute('DROP TABLE IF EXISTS users')
    cursor.execute('DROP TABLE IF EXISTS products')
    cursor.execute('DROP TABLE IF EXISTS interactions')
    cursor.execute('DROP TABLE IF EXISTS sessions')
    cursor.execute('DROP TABLE IF EXISTS cart')
    
    # Users table
    cursor.execute('''
        CREATE TABLE users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_guest BOOLEAN DEFAULT 0
        )
    ''')
    
    # Products table
    cursor.execute('''
        CREATE TABLE products (
            product_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            brand TEXT,
            price REAL,
            description TEXT,
            image_url TEXT,
            stock INTEGER DEFAULT 100,
            avg_rating REAL DEFAULT 4.0,
            num_ratings INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Interactions table
    cursor.execute('''
        CREATE TABLE interactions (
            interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            product_id TEXT,
            interaction_type TEXT,
            rating INTEGER,
            review_text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    ''')
    
    # Sessions table (for cold start tracking)
    cursor.execute('''
        CREATE TABLE sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            behavioral_data TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Cart table
    cursor.execute('''
        CREATE TABLE cart (
            cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            product_id TEXT,
            quantity INTEGER DEFAULT 1,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    ''')
    
    conn.commit()
    print("✓ Database schema created")
    
    return conn, cursor

def insert_products(cursor):
    """Insert real products into database"""
    print("\nInserting products...")
    
    for i, product in enumerate(PRODUCTS):
        product_id = f"P{i+1:04d}"
        cursor.execute('''
            INSERT INTO products (product_id, name, category, brand, price, description, avg_rating, num_ratings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            product_id,
            product['name'],
            product['category'],
            product['brand'],
            product['price'],
            product['description'],
            round(random.uniform(3.5, 5.0), 1),
            random.randint(50, 500)
        ))
    
    print(f"✓ Inserted {len(PRODUCTS)} products")

def create_demo_users(cursor):
    """Create demo users"""
    print("\nCreating demo users...")
    
    # Hash function for passwords
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    demo_users = [
        ('U0001', 'demo@example.com', 'demo123', 'Demo User', False),
        ('U0002', 'john@example.com', 'john123', 'John Doe', False),
        ('U0003', 'jane@example.com', 'jane123', 'Jane Smith', False),
    ]
    
    for user_id, email, password, name, is_guest in demo_users:
        cursor.execute('''
            INSERT INTO users (user_id, email, password_hash, name, is_guest)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, email, hash_password(password), name, is_guest))
    
    print(f"✓ Created {len(demo_users)} demo users")
    print("\nDemo Login Credentials:")
    print("  Email: demo@example.com | Password: demo123")
    print("  Email: john@example.com | Password: john123")
    print("  Email: jane@example.com | Password: jane123")

def generate_interactions(cursor):
    """Generate sample interactions"""
    print("\nGenerating sample interactions...")
    
    users = ['U0001', 'U0002', 'U0003']
    products = [f"P{i+1:04d}" for i in range(len(PRODUCTS))]
    
    interaction_types = ['view', 'click', 'cart_add', 'purchase', 'review']
    reviews = [
        'Great product!', 'Love it!', 'Excellent quality',
        'Good value', 'Highly recommend', 'Amazing!',
        'Worth the price', 'Perfect!', 'Very satisfied'
    ]
    
    num_interactions = 500
    
    for _ in range(num_interactions):
        user = random.choice(users)
        product = random.choice(products)
        interaction_type = random.choice(interaction_types)
        rating = random.randint(3, 5) if interaction_type == 'review' else None
        review = random.choice(reviews) if interaction_type == 'review' else None
        
        timestamp = datetime.now() - timedelta(days=random.randint(0, 90))
        
        cursor.execute('''
            INSERT INTO interactions (user_id, product_id, interaction_type, rating, review_text, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user, product, interaction_type, rating, review, timestamp))
    
    print(f"✓ Generated {num_interactions} interactions")

def main():
    print("="*60)
    print("🚀 CREATING REAL E-COMMERCE DATABASE")
    print("="*60 + "\n")
    
    conn, cursor = create_database()
    insert_products(cursor)
    create_demo_users(cursor)
    generate_interactions(cursor)
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ DATABASE CREATED SUCCESSFULLY!")
    print("="*60)
    print("\n📊 Database Stats:")
    print(f"  • Products: {len(PRODUCTS)}")
    print(f"  • Demo Users: 3")
    print(f"  • Sample Interactions: 500")
    print("\n💾 Database location: data/ecommerce.db")
    print("\n📋 Next Steps:")
    print("  1. Update API to use database")
    print("  2. Create frontend with login")
    print("  3. Test the system")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()