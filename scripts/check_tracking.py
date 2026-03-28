import sqlite3
import pandas as pd

def check_tracking():
    # Connect to your database
    conn = sqlite3.connect('data/ecommerce.db')
    
    print("\n" + "="*50)
    print("🔍 LAST 10 USER INTERACTIONS RECORDED")
    print("="*50)
    
    # Fetch the exact telemetry data the AI uses to make decisions
    query = """
        SELECT 
            i.timestamp,
            i.user_id,
            p.category, 
            p.name, 
            i.interaction_type, 
            i.interest_score
        FROM interactions i
        JOIN products p ON i.product_id = p.product_id
        ORDER BY i.timestamp DESC
        LIMIT 10
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        if df.empty:
            print("⚠️ NO TRACKING DATA FOUND! Your frontend isn't saving clicks.")
        else:
            print(df.to_string(index=False))
    except Exception as e:
        print(f"Database error: {e}")
        
    print("="*50 + "\n")
    conn.close()

if __name__ == "__main__":
    check_tracking()