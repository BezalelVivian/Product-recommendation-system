"""
HYBRID RANKING SYSTEM
- Smart Popularity Score for home page
- ML-based personalization
- Advanced Cold Start with MAB
"""

import sqlite3
import numpy as np
from datetime import datetime, timedelta

def calculate_popularity_scores():
    """Calculate smart popularity scores for all products"""
    print("\n🔥 CALCULATING SMART POPULARITY SCORES\n")
    
    conn = sqlite3.connect('data/ecommerce.db')
    cursor = conn.cursor()
    
    # Get all products with interaction data
    cursor.execute('''
        SELECT 
            p.product_id,
            p.avg_rating,
            p.num_ratings,
            COUNT(DISTINCT CASE WHEN i.interaction_type = 'view' THEN i.user_id END) as views,
            COUNT(DISTINCT CASE WHEN i.interaction_type = 'click' THEN i.user_id END) as clicks,
            COUNT(DISTINCT CASE WHEN i.interaction_type = 'cart_add' THEN i.user_id END) as cart_adds,
            COUNT(DISTINCT CASE WHEN i.interaction_type = 'purchase' THEN i.user_id END) as purchases,
            SUM(CASE WHEN i.hover_duration > 3 THEN 1 ELSE 0 END) as high_interest_hovers,
            COUNT(CASE WHEN i.timestamp > datetime('now', '-7 days') THEN 1 END) as recent_interactions
        FROM products p
        LEFT JOIN interactions i ON p.product_id = i.product_id
        GROUP BY p.product_id
    ''')
    
    products = cursor.fetchall()
    
    print(f"Calculating scores for {len(products):,} products...\n")
    
    # Calculate scores
    scores = []
    for p in products:
        pid, rating, num_reviews, views, clicks, carts, purchases, hovers, recent = p
        
        # QUALITY SCORE (0-100): How good is the product?
        quality = (rating / 5.0) * 100 if rating else 40
        
        # SOCIAL PROOF (0-100): How trusted?
        social_proof = min(100, (num_reviews / 50) * 100) if num_reviews else 0
        
        # ENGAGEMENT SCORE (0-100): How much interest?
        total_interactions = views + clicks + carts + purchases
        engagement = min(100, (total_interactions / 10) * 100) if total_interactions else 0
        
        # CONVERSION SCORE (0-100): How likely to buy?
        if views > 0:
            conversion = ((clicks + carts * 2 + purchases * 5) / views) * 20
            conversion = min(100, conversion)
        else:
            conversion = 0
        
        # TRENDING SCORE (0-100): What's hot now?
        trending = min(100, (recent / 5) * 100) if recent else 0
        
        # INTEREST SIGNAL (0-100): Real user interest (hover time)
        interest = min(100, (hovers / 3) * 100) if hovers else 0
        
        # FINAL WEIGHTED SCORE
        final_score = (
            quality * 0.25 +           # 25% - Product quality
            social_proof * 0.20 +      # 20% - Trust factor
            engagement * 0.20 +        # 20% - User engagement
            conversion * 0.15 +        # 15% - Purchase intent
            trending * 0.10 +          # 10% - Recent popularity
            interest * 0.10            # 10% - Deep interest
        )
        
        scores.append((final_score, pid, quality, social_proof, engagement, conversion, trending, interest))
    
    # Add popularity_score column if not exists
    try:
        cursor.execute('ALTER TABLE products ADD COLUMN popularity_score REAL DEFAULT 0')
    except:
        pass
    
    # Update scores
    cursor.executemany('''
        UPDATE products 
        SET popularity_score = ?
        WHERE product_id = ?
    ''', [(s[0], s[1]) for s in scores])
    
    conn.commit()
    
    # Show top 10
    print("🏆 TOP 10 PRODUCTS BY SMART SCORE:\n")
    top10 = sorted(scores, reverse=True)[:10]
    for i, (score, pid, qual, social, engage, conv, trend, inter) in enumerate(top10, 1):
        cursor.execute('SELECT name, category FROM products WHERE product_id = ?', (pid,))
        name, cat = cursor.fetchone()
        print(f"{i:2d}. [{cat[:15]}] {name[:45]}")
        print(f"    Score: {score:>5.1f} | Q:{qual:>4.1f} S:{social:>4.1f} E:{engage:>4.1f} C:{conv:>4.1f} T:{trend:>4.1f} I:{inter:>4.1f}\n")
    
    conn.close()
    print(f"✅ Calculated scores for {len(products):,} products!")

def create_category_rankings():
    """Create rankings per category"""
    print("\n📂 CREATING CATEGORY RANKINGS\n")
    
    conn = sqlite3.connect('data/ecommerce.db')
    cursor = conn.cursor()
    
    # Add category_rank column
    try:
        cursor.execute('ALTER TABLE products ADD COLUMN category_rank INTEGER DEFAULT 999999')
    except:
        pass
    
    # Get categories
    cursor.execute('SELECT DISTINCT category FROM products WHERE category IS NOT NULL')
    categories = [row[0] for row in cursor.fetchall()]
    
    print(f"Ranking products in {len(categories)} categories...\n")
    
    for cat in categories:
        cursor.execute('''
            SELECT product_id, popularity_score
            FROM products
            WHERE category = ?
            ORDER BY popularity_score DESC
        ''', (cat,))
        
        products = cursor.fetchall()
        
        for rank, (pid, score) in enumerate(products, 1):
            cursor.execute('''
                UPDATE products
                SET category_rank = ?
                WHERE product_id = ?
            ''', (rank, pid))
        
        if len(products) > 0:
            print(f"  {cat:<30} → Ranked {len(products):>6,} products")
    
    conn.commit()
    conn.close()
    print(f"\n✅ Category rankings created!")

if __name__ == "__main__":
    calculate_popularity_scores()
    create_category_rankings()
    
    print("\n" + "="*70)
    print("✅ SMART RANKING SYSTEM CREATED!")
    print("="*70)
    print("\nNext: Update API to use these scores!")
    print("="*70 + "\n")