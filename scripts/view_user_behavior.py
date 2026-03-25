"""
View detailed behavior of a specific user
Shows: What they viewed, hovered, clicked, bought
"""

import sqlite3
import sys
from datetime import datetime

def view_user_behavior(user_id):
    print("\n" + "="*80)
    print(f"👤 USER BEHAVIOR ANALYSIS: {user_id}")
    print("="*80 + "\n")
    
    conn = sqlite3.connect('data/ecommerce.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get user info
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ User {user_id} not found!")
        return
    
    print(f"Name: {user['name']}")
    print(f"Email: {user['email']}")
    print(f"Type: {'Guest' if user['is_guest'] else 'Registered'}")
    print(f"Joined: {user['created_at']}")
    print(f"Last Login: {user['last_login']}")
    
    # Get interaction summary
    cursor.execute('''
        SELECT 
            interaction_type,
            COUNT(*) as count,
            AVG(CASE WHEN hover_duration > 0 THEN hover_duration ELSE NULL END) as avg_hover,
            SUM(interest_score) as total_score
        FROM interactions 
        WHERE user_id = ?
        GROUP BY interaction_type
        ORDER BY count DESC
    ''', (user_id,))
    
    print("\n" + "-"*80)
    print("📊 INTERACTION SUMMARY")
    print("-"*80)
    
    summary = cursor.fetchall()
    if summary:
        for row in summary:
            hover_info = f", Avg Hover: {row['avg_hover']:.1f}s" if row['avg_hover'] else ""
            print(f"  {row['interaction_type']:15} → {row['count']:3} times, Score: {row['total_score'] or 0:4}{hover_info}")
    else:
        print("  No interactions yet")
    
    # Get detailed timeline
    cursor.execute('''
        SELECT 
            i.product_id,
            p.name,
            p.category,
            p.brand,
            p.price,
            i.interaction_type,
            i.hover_duration,
            i.interest_score,
            i.timestamp
        FROM interactions i
        LEFT JOIN products p ON i.product_id = p.product_id
        WHERE i.user_id = ?
        ORDER BY i.timestamp DESC
        LIMIT 50
    ''', (user_id,))
    
    print("\n" + "-"*80)
    print("🕐 ACTIVITY TIMELINE (Last 50 actions)")
    print("-"*80)
    
    activities = cursor.fetchall()
    if activities:
        for activity in activities:
            timestamp = activity['timestamp']
            product = activity['name'] or activity['product_id']
            action = activity['interaction_type']
            score = activity['interest_score'] or 0
            
            # Format action
            if activity['hover_duration'] and activity['hover_duration'] > 0:
                action_str = f"{action} ({activity['hover_duration']:.1f}s hover)"
            else:
                action_str = action
            
            # Interest indicator
            if score >= 10:
                indicator = "🔥"
            elif score >= 5:
                indicator = "⚡"
            elif score > 0:
                indicator = "✓"
            else:
                indicator = "  "
            
            print(f"{indicator} {timestamp} | {action_str:20} | {product[:40]:40} | Score: {score:3}")
    else:
        print("  No activity recorded")
    
    # Get product interests (products with highest total score)
    cursor.execute('''
        SELECT 
            p.product_id,
            p.name,
            p.category,
            p.brand,
            p.price,
            COUNT(*) as interaction_count,
            SUM(i.interest_score) as total_interest,
            MAX(i.hover_duration) as max_hover
        FROM interactions i
        JOIN products p ON i.product_id = p.product_id
        WHERE i.user_id = ?
        GROUP BY p.product_id
        ORDER BY total_interest DESC
        LIMIT 10
    ''', (user_id,))
    
    print("\n" + "-"*80)
    print("🎯 TOP INTERESTED PRODUCTS")
    print("-"*80)
    
    interests = cursor.fetchall()
    if interests:
        print(f"{'Product':<40} {'Category':<15} {'Brand':<12} {'Interest'} {'Max Hover'}")
        print("-"*80)
        for product in interests:
            hover_str = f"{product['max_hover']:.1f}s" if product['max_hover'] else "-"
            print(f"{product['name'][:38]:<40} {product['category'][:14]:<15} {product['brand'][:11]:<12} {product['total_interest']:8} {hover_str:>8}")
    else:
        print("  No product interactions yet")
    
    # Category preferences
    cursor.execute('''
        SELECT 
            p.category,
            COUNT(*) as views,
            SUM(i.interest_score) as total_score
        FROM interactions i
        JOIN products p ON i.product_id = p.product_id
        WHERE i.user_id = ?
        GROUP BY p.category
        ORDER BY total_score DESC
    ''', (user_id,))
    
    print("\n" + "-"*80)
    print("📁 CATEGORY PREFERENCES")
    print("-"*80)
    
    categories = cursor.fetchall()
    if categories:
        for cat in categories:
            bar_length = min(int(cat['total_score'] / 5), 40)
            bar = "█" * bar_length
            print(f"{cat['category']:<20} {bar} {cat['total_score']} points ({cat['views']} views)")
    else:
        print("  No category data")
    
    conn.close()
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        print("Usage: python view_user_behavior.py <user_id>")
        print("\nExample: python view_user_behavior.py U0001")
        print("\nAvailable users:")
        
        conn = sqlite3.connect('data/ecommerce.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, name, email FROM users WHERE is_guest = 0 LIMIT 10')
        users = cursor.fetchall()
        for user in users:
            print(f"  {user[0]} - {user[1]} ({user[2]})")
        conn.close()
        sys.exit(1)
    
    view_user_behavior(user_id)