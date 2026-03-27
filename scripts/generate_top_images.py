import sqlite3
import time
import urllib.request
import os

# --- Configuration ---
DB_PATH = 'data/ecommerce.db'
IMAGE_LIMIT = 50 
IMAGE_DIR = 'static/images' 

def fetch_top_products():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = """
        SELECT product_id, name, category 
        FROM products 
        ORDER BY popularity_score DESC 
        LIMIT ?
    """
    cursor.execute(query, (IMAGE_LIMIT,))
    products = cursor.fetchall()
    conn.close()
    return products

def update_image_in_db(product_id, new_image_path):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products 
        SET image_url = ? 
        WHERE product_id = ?
    """, (new_image_path, product_id))
    conn.commit()
    conn.close()

def main():
    os.makedirs(IMAGE_DIR, exist_ok=True)
    top_products = fetch_top_products()
    print(f"Found {len(top_products)} top products. Fetching UI placeholder images...")
    
    for product in top_products:
        prod_id, name, category = product
        
        short_name = name[:50].strip()
        print(f"Fetching image for: {short_name}...")
        
        # Using a 'seed' ensures the exact same product always gets the exact same photo
        image_url = f"https://picsum.photos/seed/{prod_id}/512/512"
        
        file_name = f"prod_{prod_id}.jpg"
        file_path = os.path.join(IMAGE_DIR, file_name)
        
        try:
            req = urllib.request.Request(
                image_url, 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req) as response, open(file_path, 'wb') as out_file:
                out_file.write(response.read())
            
            db_image_path = f"/static/images/{file_name}"
            update_image_in_db(prod_id, db_image_path)
            
            print(f"  -> Success! Saved as {file_name}")
            
        except Exception as e:
            print(f"  -> Failed to fetch image for {prod_id}: {e}")
        
        # Just a tiny 1-second pause since Picsum is very fast
        time.sleep(1) 

    print("\nAll done! Your top 50 products now have high-quality UI images.")

if __name__ == "__main__":
    main()