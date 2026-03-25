"""View Complete Database"""
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/ecommerce.db')

print("\n📊 COMPLETE DATABASE OVERVIEW\n")
print("="*80)

# Products by category
print("\n1️⃣ PRODUCTS BY CATEGORY:")
df = pd.read_sql_query('SELECT category, COUNT(*) as count FROM products GROUP BY category ORDER BY count DESC', conn)
print(df.to_string(index=False))

# Total stats
print("\n2️⃣ OVERALL STATS:")
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM products')
print(f"Total Products: {cursor.fetchone()[0]:,}")
cursor.execute('SELECT COUNT(*) FROM users WHERE is_guest=0')
print(f"Registered Users: {cursor.fetchone()[0]}")
cursor.execute('SELECT COUNT(*) FROM interactions')
print(f"Total Interactions: {cursor.fetchone()[0]:,}")

# Sample products
print("\n3️⃣ SAMPLE PRODUCTS:")
df = pd.read_sql_query('SELECT product_id, name, category, brand, price FROM products LIMIT 10', conn)
print(df.to_string(index=False))

conn.close()
print("\n" + "="*80 + "\n")
