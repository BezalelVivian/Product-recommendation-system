import sqlite3

def inspect_database(db_path="data/ecommerce.db"):
    print(f"--- Inspecting {db_path} ---")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print("No tables found. Check if the database name is correct.")
            return

        for table_name in tables:
            table = table_name[0]
            print(f"\nTable: {table}")
            print("-" * 20)
            
            # Get column info for each table
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            
            for col in columns:
                # col structure: (cid, name, type, notnull, dflt_value, pk)
                name = col[1]
                data_type = col[2]
                print(f"- {name} ({data_type})")

        conn.close()
        print("\n--- Inspection Complete ---")
        
    except sqlite3.Error as e:
        print(f"Database Error: {e}")

if __name__ == "__main__":
    inspect_database()