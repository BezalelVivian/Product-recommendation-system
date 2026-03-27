import sqlite3

# Connect to your database
conn = sqlite3.connect('data/ecommerce.db')
cursor = conn.cursor()

# Count every row in the products table
cursor.execute("SELECT COUNT(*) FROM products")
total_products = cursor.fetchone()[0]

print(f"🔥 You have exactly {total_products} products in your database!")

conn.close()