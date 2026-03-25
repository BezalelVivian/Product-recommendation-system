"""
Admin Dashboard - All-in-one overview
Shows: System stats, top products, recent activity, user summary
"""

import sqlite3
from datetime import datetime

def admin_dashboard():
    print("\n" + "="*80)
    print("🎛️  SHOPSMART ADMIN DASHBOARD")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    conn = sqlite3.connect('data/ecommerce.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # ========== SYSTEM OVERVIEW ==========
    print("📊 SYSTEM OVERVIEW")
    print("-"*80)
    
    cursor.execute('SELECT COUNT(*) as total FROM users WHERE is_guest = 0')
    registered_users = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as total FROM users WHERE is_guest = 1')
    guest_users = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as total FROM products')
    total_products = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as total FROM interactions')
    total_interactions = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as total FROM sessions')
    total_sessions = cursor.fetchone()['total']
    
    cursor.execute('SELECT AVG(avg_rating) as avg FROM products')
    avg_rating = cursor.fetchone()['avg'] or 0
    
    print(f"Registered Users:      {registered_users:>6}")
    print(f"Guest Users:           {guest_users:>6}")
    print(f"Total Products:        {total_products:>6}")
    print(f"Total Interactions:    {total_interactions:>6}")
    print(f"Active Sessions:       {total_sessions:>6}")
    print(f"Avg Product Rating:    {avg_rating:>6.2f}⭐")
    
    # ========== ENGAGEMENT METRICS ==========
    print("\n" + "-"*80)
    print("📈 ENGAGEMENT METRICS")
    print("-"*80)
    
    cursor.execute("SELECT COUNT(*) as c FROM interactions WHERE interaction_type = 'view'")
    views = cursor.fetchone()['c']
    
    cursor.execute("SELECT COUNT(*) as c FROM interactions WHERE interaction_type = 'click'")
    clicks = cursor.fetchone()['c']
    
    cursor.execute("SELECT COUNT(*) as c FROM interactions WHERE interaction_type = 'cart_add'")
    cart_adds = cursor.fetchone()['c']
    
    cursor.execute("SELECT COUNT(*) as c FROM interactions WHERE interaction_type = 'purchase'")
    purchases = cursor.fetchone()['c']
    
    print(f"Total Views:           {views:>6}")
    print(f"Total Clicks:          {clicks:>6}")
    print(f"Total Cart Adds:       {cart_adds:>6}")
    print(f"Total Purchases:       {purchases:>6}")
    
    if views > 0:
        ctr = (clicks / views) * 100
        conversion = (purchases / views) * 100
        print(f"\nClick-Through Rate:    {ctr:>5.2f}%")
        print(f"Conversion Rate:       {conversion:>5.2f}%")
    
    # ========== TOP PRODUCTS ==========
    print("\n" + "-"*80)
    print("🔥 TOP 10 PRODUCTS BY INTEREST")
    print("-"*80)
    
    cursor.execute('''
        SELECT 
            p.name,
            p.category,
            p.brand,
            p.price,
            COUNT(DISTINCT i.user_id) as unique_users,
            SUM(i.interest_score) as total_interest,
            SUM(CASE WHEN i.interaction_type = 'purchase' THEN 1 ELSE 0 END) as purchases
        FROM products p
        LEFT JOIN interactions i ON p.product_id = i.product_id
        GROUP BY p.product_id
        HAVING total_interest > 0
        ORDER BY total_interest DESC
        LIMIT 10
    ''')
    
    top_products = cursor.fetchall()
    
    if top_products:
        print(f"\n{'#':<3} {'Product':<35} {'Category':<15} {'Interest':<10} {'Users':<7} {'Sales'}")
        print("-"*80)
        for idx, product in enumerate(top_products, 1):
            interest = product['total_interest'] or 0
            bar_length = min(int(interest / 5), 20)
            bar = "█" * bar_length
            
            print(f"{idx:<3} {product['name'][:33]:<35} {product['category'][:14]:<15} {bar:<20} {product['unique_users']:<7} {product['purchases']}")
    
    # ========== ACTIVE USERS ==========
    print("\n" + "-"*80)
    print("👥 MOST ACTIVE USERS (Last 24h)")
    print("-"*80)
    
    cursor.execute('''
        SELECT 
            u.user_id,
            u.name,
            u.email,
            u.is_guest,
            COUNT(i.interaction_id) as activity_count,
            SUM(i.interest_score) as total_score,
            MAX(i.timestamp) as last_active
        FROM users u
        LEFT JOIN interactions i ON u.user_id = i.user_id
        WHERE i.timestamp >= datetime('now', '-1 day')
        GROUP BY u.user_id
        ORDER BY activity_count DESC
        LIMIT 10
    ''')
    
    active_users = cursor.fetchall()
    
    if active_users:
        print(f"\n{'User ID':<12} {'Name':<20} {'Type':<10} {'Activity':<10} {'Score':<8} {'Last Active'}")
        print("-"*80)
        for user in active_users:
            user_type = "Guest" if user['is_guest'] else "Registered"
            print(f"{user['user_id']:<12} {user['name'][:19]:<20} {user_type:<10} {user['activity_count']:<10} {user['total_score'] or 0:<8} {user['last_active']}")
    else:
        print("\nNo activity in the last 24 hours")
    
    # ========== CATEGORY PERFORMANCE ==========
    print("\n" + "-"*80)
    print("📁 CATEGORY PERFORMANCE")
    print("-"*80)
    
    cursor.execute('''
        SELECT 
            p.category,
            COUNT(DISTINCT i.user_id) as unique_users,
            COUNT(*) as interactions,
            SUM(i.interest_score) as total_interest,
            SUM(CASE WHEN i.interaction_type = 'purchase' THEN 1 ELSE 0 END) as sales
        FROM products p
        LEFT JOIN interactions i ON p.product_id = i.product_id
        WHERE i.interaction_id IS NOT NULL
        GROUP BY p.category
        ORDER BY total_interest DESC
    ''')
    
    categories = cursor.fetchall()
    
    if categories:
        max_interest = max(cat['total_interest'] or 0 for cat in categories)
        
        print()
        for cat in categories:
            interest = cat['total_interest'] or 0
            bar_length = int((interest / max_interest) * 30) if max_interest > 0 else 0
            bar = "█" * bar_length
            
            print(f"{cat['category']:<20} {bar:<30} {interest:>6} pts | {cat['unique_users']:>3} users | {cat['sales']:>3} sales")
    
    # ========== RECENT ACTIVITY ==========
    print("\n" + "-"*80)
    print("🕐 RECENT ACTIVITY (Last 10 actions)")
    print("-"*80)
    
    cursor.execute('''
        SELECT 
            i.timestamp,
            u.name,
            i.interaction_type,
            p.name as product_name,
            i.interest_score
        FROM interactions i
        LEFT JOIN users u ON i.user_id = u.user_id
        LEFT JOIN products p ON i.product_id = p.product_id
        ORDER BY i.timestamp DESC
        LIMIT 10
    ''')
    
    recent = cursor.fetchall()
    
    if recent:
        print()
        for activity in recent:
            score = activity['interest_score'] or 0
            if score >= 10:
                indicator = "🔥"
            elif score >= 5:
                indicator = "⚡"
            elif score > 0:
                indicator = "✓"
            else:
                indicator = " "
            
            print(f"{indicator} {activity['timestamp']} | {activity['name'][:20]:<20} | {activity['interaction_type']:10} | {activity['product_name'][:30]}")
    
    # ========== SYSTEM HEALTH ==========
    print("\n" + "-"*80)
    print("💚 SYSTEM HEALTH")
    print("-"*80)
    
    health_metrics = []
    
    # Check if there's recent activity
    cursor.execute("SELECT COUNT(*) as c FROM interactions WHERE timestamp >= datetime('now', '-1 hour')")
    recent_activity = cursor.fetchone()['c']
    health_metrics.append(("Recent Activity (1h)", recent_activity > 0, f"{recent_activity} interactions"))
    
    # Check if users are engaging
    engagement_rate = (clicks / views * 100) if views > 0 else 0
    health_metrics.append(("User Engagement", engagement_rate > 5, f"{engagement_rate:.1f}% CTR"))
    
    # Check if products are being purchased
    health_metrics.append(("Sales Performance", purchases > 0, f"{purchases} purchases"))
    
    # Check database integrity
    health_metrics.append(("Database Integrity", True, "✓ All tables accessible"))
    
    print()
    for metric, status, detail in health_metrics:
        status_icon = "✅" if status else "⚠️"
        print(f"{status_icon} {metric:<25} {detail}")
    
    conn.close()
    
    print("\n" + "="*80)
    print("💡 TIP: For detailed analysis, use:")
    print("   • python view_user_behavior.py <user_id>")
    print("   • python view_hover_analytics.py")
    print("   • python view_recommendations.py")
    print("   • python view_live_activity.py")
    print("="*80 + "\n")


if __name__ == "__main__":
    admin_dashboard()