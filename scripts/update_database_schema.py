"""
Update database to track hover time and interest scores
"""

import sqlite3
from pathlib import Path

def update_schema():
    print("\n" + "="*60)
    print("🔄 UPDATING DATABASE SCHEMA")
    print("="*60 + "\n")
    
    conn = sqlite3.connect('data/ecommerce.db')
    cursor = conn.cursor()
    
    try:
        # Add hover_duration to interactions
        print("Adding hover_duration column...")
        cursor.execute('''
            ALTER TABLE interactions 
            ADD COLUMN hover_duration REAL DEFAULT 0
        ''')
        print("✓ Added hover_duration")
    except:
        print("✓ hover_duration already exists")
    
    try:
        # Add interest_score to interactions
        print("Adding interest_score column...")
        cursor.execute('''
            ALTER TABLE interactions 
            ADD COLUMN interest_score INTEGER DEFAULT 0
        ''')
        print("✓ Added interest_score")
    except:
        print("✓ interest_score already exists")
    
    try:
        # Create detailed analytics table
        print("\nCreating analytics table...")
        cursor.execute('''
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
            )
        ''')
        print("✓ Created user_analytics table")
    except Exception as e:
        print(f"Note: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ DATABASE SCHEMA UPDATED!")
    print("="*60 + "\n")

if __name__ == "__main__":
    update_schema()