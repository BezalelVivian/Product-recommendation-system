"""
View live activity feed - Real-time stream of what's happening
"""

import sqlite3
import time
from datetime import datetime

def view_live_activity(duration_seconds=30):
    """
    Show live activity feed
    
    Args:
        duration_seconds: How long to monitor (default 30 seconds)
    """
    
    print("\n" + "="*80)
    print("📡 LIVE ACTIVITY FEED")
    print("="*80)
    print(f"Monitoring for {duration_seconds} seconds... (Press Ctrl+C to stop)\n")
    
    conn = sqlite3.connect('data/ecommerce.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get the latest interaction ID to start from
    cursor.execute('SELECT MAX(interaction_id) as last_id FROM interactions')
    last_id = cursor.fetchone()['last_id'] or 0
    
    start_time = time.time()
    activity_count = 0
    
    try:
        while (time.time() - start_time) < duration_seconds:
            # Check for new interactions
            cursor.execute('''
                SELECT 
                    i.interaction_id,
                    i.user_id,
                    u.name,
                    i.product_id,
                    p.name as product_name,
                    p.category,
                    i.interaction_type,
                    i.hover_duration,
                    i.interest_score,
                    i.timestamp
                FROM interactions i
                LEFT JOIN users u ON i.user_id = u.user_id
                LEFT JOIN products p ON i.product_id = p.product_id
                WHERE i.interaction_id > ?
                ORDER BY i.interaction_id ASC
            ''', (last_id,))
            
            new_activities = cursor.fetchall()
            
            for activity in new_activities:
                activity_count += 1
                last_id = activity['interaction_id']
                
                # Format timestamp
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Format user
                user_name = activity['name'] or activity['user_id']
                if 'GUEST' in activity['user_id']:
                    user_name = f"👤 {user_name}"
                else:
                    user_name = f"👨 {user_name}"
                
                # Format action
                action = activity['interaction_type'].upper()
                
                # Add details for hover
                if activity['hover_duration'] and activity['hover_duration'] > 0:
                    action += f" ({activity['hover_duration']:.1f}s)"
                
                # Interest indicator
                score = activity['interest_score'] or 0
                if score >= 10:
                    indicator = "🔥"
                elif score >= 5:
                    indicator = "⚡"
                elif score > 0:
                    indicator = "✓"
                else:
                    indicator = " "
                
                # Product name
                product = activity['product_name'] or activity['product_id']
                
                # Format output
                print(f"{indicator} [{timestamp}] {user_name[:20]:<20} → {action:15} → {product[:35]:<35} (Score: {score:+3})")
            
            # Sleep for a bit before checking again
            time.sleep(0.5)
        
        print("\n" + "-"*80)
        print(f"✅ Monitoring complete. Captured {activity_count} activities in {duration_seconds} seconds.")
        
    except KeyboardInterrupt:
        elapsed = int(time.time() - start_time)
        print("\n" + "-"*80)
        print(f"⏹️ Stopped. Captured {activity_count} activities in {elapsed} seconds.")
    
    conn.close()
    print("="*80 + "\n")


def show_recent_activity(limit=20):
    """Show most recent activities"""
    
    print("\n" + "="*80)
    print(f"🕐 RECENT ACTIVITY (Last {limit} actions)")
    print("="*80 + "\n")
    
    conn = sqlite3.connect('data/ecommerce.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            i.user_id,
            u.name,
            i.product_id,
            p.name as product_name,
            p.category,
            i.interaction_type,
            i.hover_duration,
            i.interest_score,
            i.timestamp
        FROM interactions i
        LEFT JOIN users u ON i.user_id = u.user_id
        LEFT JOIN products p ON i.product_id = p.product_id
        ORDER BY i.timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    activities = cursor.fetchall()
    
    if activities:
        for activity in activities:
            timestamp = activity['timestamp']
            user_name = activity['name'] or activity['user_id']
            action = activity['interaction_type']
            product = activity['product_name'] or activity['product_id']
            score = activity['interest_score'] or 0
            
            if activity['hover_duration'] and activity['hover_duration'] > 0:
                action += f" ({activity['hover_duration']:.1f}s)"
            
            if score >= 10:
                indicator = "🔥"
            elif score >= 5:
                indicator = "⚡"
            elif score > 0:
                indicator = "✓"
            else:
                indicator = " "
            
            print(f"{indicator} {timestamp} | {user_name[:20]:<20} | {action:20} | {product[:35]}")
    else:
        print("No recent activity")
    
    conn.close()
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'recent':
        # Show recent activity
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        show_recent_activity(limit)
    else:
        # Show live feed
        duration = int(sys.argv[1]) if len(sys.argv) > 1 else 30
        print("💡 TIP: For recent activity only, use: python view_live_activity.py recent")
        print("💡 TIP: To monitor for longer, use: python view_live_activity.py 60\n")
        view_live_activity(duration)