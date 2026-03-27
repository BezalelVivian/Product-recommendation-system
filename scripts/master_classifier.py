import sqlite3
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("Master_Classifier")

def categorize_product(name):
    """Deep text analysis to properly classify 1.1 Million products."""
    name = str(name).lower()
    
    # 1. AUDIO & HEADPHONES (Catches earbuds, TWS, etc.)
    if any(k in name for k in ['earbud', 'earphone', 'headphone', 'tws', 'airpod', 'buds', 'headset', 'speaker', 'soundbar', 'home theater']):
        return 'Audio & Headphones'
        
    # 2. STORAGE & DRIVES (Catches the SanDisk pendrives)
    if any(k in name for k in ['sandisk', 'pen drive', 'pendrive', 'flash drive', 'hdd', 'ssd', 'hard drive', 'memory card', 'microsd', 'seagate', 'wd ']):
        return 'Storage & Drives'
        
    # 3. MOBILE ACCESSORIES (Catches cases, covers, chargers)
    if any(k in name for k in ['case', 'cover', 'screen protector', 'tempered glass', 'charger', 'adapter', 'type-c', 'lightning cable', 'power bank', 'pop socket']):
        return 'Mobile Accessories'
        
    # 4. SMARTWATCHES
    if any(k in name for k in ['smartwatch', 'fitness band', 'smart watch', 'apple watch', 'galaxy watch', 'fire-boltt', 'noise fit']):
        return 'Smartwatches & Wearables'
        
    # 5. LAPTOPS & COMPUTERS
    if any(k in name for k in ['laptop', 'macbook', 'notebook', 'desktop', 'thinkpad', 'ideapad', 'pavilion']):
        return 'Laptops & Computers'
        
    # 6. SMARTPHONES
    if any(k in name for k in ['smartphone', 'iphone', 'samsung galaxy', 'redmi', 'poco', 'realme', 'oneplus', 'vivo', 'oppo', 'iqoo']):
        return 'Smartphones'
        
    # 7. TELEVISIONS
    if any(k in name for k in [' tv', 'television', 'smart tv', 'oled', 'qled', 'android tv']):
        return 'Televisions'
        
    # 8. FASHION
    if any(k in name for k in ['t-shirt', 'shirt', 'jeans', 'trouser', 'kurta', 'saree', 'lehenga', 'dress', 'jacket']):
        return 'Fashion & Clothing'
        
    # 9. FOOTWEAR
    if any(k in name for k in ['shoe', 'sneaker', 'sandal', 'slipper', 'flip flop', 'boot', 'crocs']):
        return 'Footwear'
        
    # 10. HOME & KITCHEN APPLIANCES
    if any(k in name for k in ['fridge', 'refrigerator', 'washing machine', 'microwave', 'oven', 'mixer', 'grinder', 'kettle', 'purifier', 'vacuum', 'fan ', 'heater', 'iron ']):
        return 'Home & Kitchen Appliances'
        
    # 11. BEAUTY & GROOMING
    if any(k in name for k in ['cream', 'lotion', 'makeup', 'perfume', 'trimmer', 'shaver', 'hair dryer', 'shampoo', 'face wash']):
        return 'Beauty & Grooming'
        
    # Fallback
    return 'General Products'

def run_deep_scan():
    conn = sqlite3.connect('data/ecommerce.db')
    cursor = conn.cursor()
    
    logger.info("🚀 Starting Deep Scan of 1.1 Million Products...")
    start_time = time.time()
    
    cursor.execute('SELECT product_id, name FROM products')
    all_products = cursor.fetchall()
    
    updates = []
    for pid, name in all_products:
        if name:
            new_cat = categorize_product(name)
            updates.append((new_cat, pid))
            
    logger.info("💾 Writing clean categories to database...")
    
    # Bulk update is lightning fast
    cursor.executemany('UPDATE products SET category = ? WHERE product_id = ?', updates)
    conn.commit()
    conn.close()
    
    elapsed = round(time.time() - start_time, 2)
    logger.info(f"🎉 DONE! Successfully classified {len(updates):,} products in {elapsed} seconds.")

if __name__ == "__main__":
    run_deep_scan()
    