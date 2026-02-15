"""
View all users in database
"""

import sqlite3
import pandas as pd

conn = sqlite3.connect('data/ecommerce.db')

print("\n" + "="*80)
print("👥 ALL USERS IN DATABASE")
print("="*80 + "\n")

df = pd.read_sql_query('''
    SELECT user_id, email, name, is_guest, created_at, last_login 
    FROM users 
    ORDER BY created_at DESC
''', conn)

print(df.to_string(index=False))
print(f"\n📊 Total Users: {len(df)}")
print(f"   • Registered: {len(df[df['is_guest'] == 0])}")
print(f"   • Guests: {len(df[df['is_guest'] == 1])}")
print("\n" + "="*80 + "\n")

conn.close()