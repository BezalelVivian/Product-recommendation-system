import sqlite3

conn = sqlite3.connect('data/ecommerce.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(products);")

print("Your exact column names are:")
for col in cursor.fetchall():
    print(f"- {col[1]}")
    