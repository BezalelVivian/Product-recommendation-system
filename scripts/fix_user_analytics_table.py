import sqlite3

conn = sqlite3.connect('data/ecommerce.db')
cursor = conn.cursor()

print("\n🔧 Fixing user_analytics table...\n")

# Add missing category column
try:
    cursor.execute('ALTER TABLE user_analytics ADD COLUMN category TEXT')
    print("✅ Added 'category' column to user_analytics")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e):
        print("✅ Column 'category' already exists")
    else:
        print(f"❌ Error: {e}")

conn.commit()
conn.close()

print("\n✅ Done! Restart API now.\n")