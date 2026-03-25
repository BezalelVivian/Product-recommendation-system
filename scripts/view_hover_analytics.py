"""
View product hover analytics - which products get most attention
"""

import sqlite3

def view_hover_analytics():
    print("\n" + "="*80)
    print("🔥 PRODUCT HOVER ANALYTICS - Interest Heatmap")
    print("="*80 + "\n")
    
    conn = sqlite3.connect('data/ecommerce.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Products by total hover time
    cursor.execute('''
        SELECT 
            p.product_id,
            p.name,
            p.category,
            p.brand,
            p.price,
            COUNT(DISTINCT i.user_id) as unique_users,
            COUNT(*) as total_hovers,
            SUM(i.hover_duration) as total_hover_time,
            AVG(i.hover_duration) as avg_hover_time,
            MAX(i.hover_duration) as max_hover_time,
            SUM(i.interest_score) as total_interest
        FROM products p
        LEFT JOIN interactions i ON p.product_id = i.product_id 
            AND i.interaction_type IN ('hover', 'view')
            AND i.hover_duration > 0
        GROUP BY p.product_id
        HAVING total_hover_time > 0
        ORDER BY total_hover_time DESC
        LIMIT 20
    ''')
    
    products = cursor.fetchall()
    
    if not products:
        print("❌ No hover data yet. Users need to browse products first!")
        return
    
    print("TOP 20 PRODUCTS BY HOVER TIME\n")
    print(f"{'#':<3} {'Product':<35} {'Category':<15} {'Users':<7} {'Total Time':<12} {'Avg Time':<10} {'Interest'}")
    print("-"*80)
    
    for idx, product in enumerate(products, 1):
        total_time = product['total_hover_time'] or 0
        avg_time = product['avg_hover_time'] or 0
        
        # Visual bar
        bar_length = min(int(total_time / 2), 30)
        bar = "█" * bar_length
        
        print(f"{idx:<3} {product['name'][:33]:<35} {product['category'][:14]:<15} {product['unique_users']:<7} {total_time:>6.1f}s {bar:<30} {avg_time:>4.1f}s  {product['total_interest'] or 0:>4}")
    
    # Category analysis
    print("\n" + "-"*80)
    print("📊 CATEGORY INTEREST ANALYSIS")
    print("-"*80 + "\n")
    
    cursor.execute('''
        SELECT 
            p.category,
            COUNT(DISTINCT i.user_id) as unique_users,
            COUNT(*) as total_interactions,
            SUM(i.hover_duration) as total_hover_time,
            AVG(i.hover_duration) as avg_hover_time,
            SUM(i.interest_score) as total_interest
        FROM products p
        LEFT JOIN interactions i ON p.product_id = i.product_id
        WHERE i.hover_duration > 0
        GROUP BY p.category
        ORDER BY total_hover_time DESC
    ''')
    
    categories = cursor.fetchall()
    
    if categories:
        max_time = max(cat['total_hover_time'] for cat in categories)
        
        for cat in categories:
            total_time = cat['total_hover_time'] or 0
            bar_length = int((total_time / max_time) * 40) if max_time > 0 else 0
            bar = "█" * bar_length
            
            print(f"{cat['category']:<20} {bar:<40} {total_time:>6.1f}s ({cat['unique_users']} users)")
    
    conn.close()
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    view_hover_analytics()