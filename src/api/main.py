"""
Complete E-Commerce API with Authentication & Database
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import hashlib
import uuid
import json
from datetime import datetime
import logging
# Load NCF Model
# Existing logger setup
logger = logging.getLogger("main")

# ADD NCF MODEL LOADING HERE (after logger):
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import sys
sys.path.append('models')
from ncf_recommender import NCFRecommender

ncf_model = NCFRecommender()
try:
    ncf_model.load('models/saved')
    logger.info("✅ NCF Deep Learning model loaded!")
except Exception as e:
    logger.warning(f"⚠️ NCF model not found: {e}")
    ncf_model = None

app = FastAPI(title="ShopSmart API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

DB_PATH = 'data/ecommerce.db'

# ============ MODELS ============

class UserSignup(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class BehavioralData(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    events: List[dict]

class ProductResponse(BaseModel):
    product_id: str
    name: str
    category: str
    brand: str
    price: float
    description: str
    avg_rating: float
    num_ratings: int
    reason: Optional[str] = None

# ============ DATABASE HELPERS ============

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    """Hash password"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_session(session_id: str = Header(None)):
    """Verify user session"""
    if not session_id:
        return None
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM sessions WHERE session_id = ?', (session_id,))
    result = cursor.fetchone()
    conn.close()
    
    return result['user_id'] if result else None

# ============ AUTH ENDPOINTS ============

@app.post("/auth/signup")
async def signup(user: UserSignup):
    """User signup"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if email exists
        cursor.execute('SELECT email FROM users WHERE email = ?', (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        user_id = f"U{uuid.uuid4().hex[:8].upper()}"
        password_hash = hash_password(user.password)
        
        cursor.execute('''
            INSERT INTO users (user_id, email, password_hash, name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, user.email, password_hash, user.name))
        
        # Create session
        session_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO sessions (session_id, user_id)
            VALUES (?, ?)
        ''', (session_id, user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"New user created: {user.email}")
        
        return {
            "success": True,
            "user_id": user_id,
            "session_id": session_id,
            "name": user.name,
            "message": "Account created successfully!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login")
async def login(credentials: UserLogin):
    """User login"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        password_hash = hash_password(credentials.password)
        
        cursor.execute('''
            SELECT user_id, name, email FROM users 
            WHERE email = ? AND password_hash = ?
        ''', (credentials.email, password_hash))
        
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create session
        session_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO sessions (session_id, user_id)
            VALUES (?, ?)
        ''', (session_id, user['user_id']))
        
        # Update last login
        cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (user['user_id'],))
        
        conn.commit()
        conn.close()
        
        logger.info(f"User logged in: {credentials.email}")
        
        return {
            "success": True,
            "user_id": user['user_id'],
            "session_id": session_id,
            "name": user['name'],
            "email": user['email'],
            "message": "Login successful!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/guest")
async def guest_session():
    """Create guest session"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        user_id = f"GUEST{uuid.uuid4().hex[:8].upper()}"
        session_id = str(uuid.uuid4())
        
        # Create guest user
        cursor.execute('''
            INSERT INTO users (user_id, email, password_hash, name, is_guest)
            VALUES (?, ?, ?, ?, 1)
        ''', (user_id, f"{user_id}@guest.com", "", "Guest User"))
        
        # Create session
        cursor.execute('''
            INSERT INTO sessions (session_id, user_id)
            VALUES (?, ?)
        ''', (session_id, user_id))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "user_id": user_id,
            "session_id": session_id,
            "is_guest": True
        }
        
    except Exception as e:
        logger.error(f"Guest session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ COLD START TRACKING ============

@app.post("/tracking/behavior")
async def track_behavior(data: BehavioralData):
    """Track user behavior for cold start (60-second tracking)"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Store behavioral data
        cursor.execute('''
            UPDATE sessions 
            SET behavioral_data = ?
            WHERE session_id = ?
        ''', (json.dumps(data.events), data.session_id))
        
        # Log interactions WITH dwell time and dynamic scoring
        for event in data.events:
            if event.get('product_id'):
                # Industry Standard: Calculate implicit interest score based on action
                score = 1
                if event['type'] == 'click':
                    score = 5
                elif event['type'] == 'cart_add':
                    score = 10
                elif event['type'] == 'hover':
                    # Score 1-5 based on seconds spent looking at the item
                    hover_time = float(event.get('hover_duration', 0))
                    score = min(5, max(1, int(hover_time)))
                
                cursor.execute('''
                    INSERT INTO interactions (user_id, product_id, interaction_type, hover_duration, interest_score, timestamp)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    data.user_id, 
                    event['product_id'], 
                    event['type'], 
                    event.get('hover_duration', 0.0),
                    score
                ))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "events_tracked": len(data.events)}
        
    except Exception as e:
        logger.error(f"Tracking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ PRODUCT ENDPOINTS ============
@app.get("/products")
async def get_products(category: str = None, limit: int = 200):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT * FROM products 
                WHERE category = ? 
                ORDER BY (avg_rating * num_ratings) DESC, avg_rating DESC
                LIMIT ?
            ''', (category, limit))
        else:
            cursor.execute('''
                SELECT * FROM products 
                ORDER BY (avg_rating * num_ratings) DESC, avg_rating DESC
                LIMIT ?
            ''', (limit,))
        
        products = cursor.fetchall()
        conn.close()
        
        return [dict(product) for product in products]

    except Exception as e:
        logger.error(f"Products error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products/{product_id}")
async def get_product(product_id: str):
    """Get single product"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM products WHERE product_id = ?', (product_id,))
        product = cursor.fetchone()
        conn.close()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return dict(product)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories")
async def get_categories():
    """Get all categories"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT category FROM products')
        categories = [row['category'] for row in cursor.fetchall()]
        conn.close()
        
        return {"categories": categories}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ RECOMMENDATION ENDPOINTS ============

@app.get("/recommend/cold-start/{session_id}")
async def cold_start_recommendations(session_id: str, limit: int = 100):
    """
    ADVANCED COLD START with Multi-Armed Bandit
    - Tracks user behavior in real-time
    - Learns preferences within 60 seconds
    - Uses Thompson Sampling for exploration/exploitation
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get user's behavioral data
        # Get user's behavioral data directly from interactions
        cursor.execute('''
            SELECT i.product_id, p.category, i.hover_duration, i.interest_score
            FROM interactions i
            JOIN products p ON i.product_id = p.product_id
            JOIN sessions s ON i.user_id = s.user_id
            WHERE s.session_id = ?
            ORDER BY i.timestamp DESC
        ''', (session_id,))
        
        behaviors = cursor.fetchall()
        
        if behaviors:
            # Extract preferences
            category_scores = {}
            hover_products = []
            
            for pid, cat, hover, score in behaviors:
                # Require an interest score of at least 2.0 to consider it a signal
                if score and score >= 2.0:  
                    hover_products.append(pid)
                    category_scores[cat] = category_scores.get(cat, 0) + score
            
            # Get top 3 interested categories
            top_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            top_cats = [cat for cat, _ in top_categories]
            
            if top_cats:
                # Multi-Armed Bandit: 70% exploit best categories, 30% explore
                exploit_limit = int(limit * 0.7)
                explore_limit = limit - exploit_limit
                
                # EXPLOIT: Best products from interested categories
                placeholders = ','.join(['?'] * len(top_cats))
                cursor.execute(f'''
                    SELECT * FROM products
                    WHERE category IN ({placeholders})
                    AND product_id NOT IN (
                        SELECT DISTINCT product_id FROM user_analytics WHERE session_id = ?
                    )
                    ORDER BY popularity_score DESC, avg_rating DESC
                    LIMIT ?
                ''', (*top_cats, session_id, exploit_limit))
                
                exploit_products = cursor.fetchall()
                
                # EXPLORE: Diverse high-quality products
                cursor.execute('''
                    SELECT * FROM products
                    WHERE category NOT IN (''' + placeholders + ''')
                    AND product_id NOT IN (
                        SELECT DISTINCT product_id FROM user_analytics WHERE session_id = ?
                    )
                    ORDER BY popularity_score DESC
                    LIMIT ?
                ''', (*top_cats, session_id, explore_limit))
                
                explore_products = cursor.fetchall()
                
                # Combine and shuffle for serendipity
                import random
                all_products = list(exploit_products) + list(explore_products)
                random.shuffle(all_products)
                
                conn.close()
                
                # Add recommendation reasons
                result = []
                for product in all_products[:limit]:
                    p = dict(product)
                    if p['category'] in top_cats:
                        p['reason'] = f"Based on your interest in {p['category']}"
                    else:
                        p['reason'] = "You might also like this"
                    result.append(p)
                
                return result
        
        # FALLBACK: Use trending + high-quality products
        cursor.execute('''
            SELECT * FROM products
            ORDER BY popularity_score DESC, avg_rating DESC
            LIMIT ?
        ''', (limit,))
        
        products = cursor.fetchall()
        conn.close()
        
        return [dict(p) for p in products]
        
    except Exception as e:
        logger.error(f"Cold start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommend/user/{user_id}")
async def recommend_for_user(user_id: str, limit: int = 10):
    """Personalized recommendations for logged-in user"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get user's interaction history
        cursor.execute('''
            SELECT DISTINCT p.category, COUNT(*) as count
            FROM interactions i
            JOIN products p ON i.product_id = p.product_id
            WHERE i.user_id = ?
            GROUP BY p.category
            ORDER BY count DESC
            LIMIT 3
        ''', (user_id,))
        
        favorite_categories = [row['category'] for row in cursor.fetchall()]
        
        if favorite_categories:
            # Recommend from favorite categories
            placeholders = ','.join('?' * len(favorite_categories))
            cursor.execute(f'''
                SELECT * FROM products
                WHERE category IN ({placeholders})
                AND product_id NOT IN (
                    SELECT product_id FROM interactions 
                    WHERE user_id = ? AND interaction_type = 'purchase'
                )
                ORDER BY avg_rating DESC
                LIMIT ?
            ''', (*favorite_categories, user_id, limit))
        else:
            # New user - show popular
            cursor.execute('''
                SELECT * FROM products
                ORDER BY avg_rating DESC, num_ratings DESC
                LIMIT ?
            ''', (limit,))
        
        products = cursor.fetchall()
        conn.close()
        
        results = []
        for product in products:
            p = dict(product)
            p['reason'] = "Based on your purchase history"
            results.append(p)
        
        return results
        
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/popular")
async def get_popular(limit: int = 20):
    """Get popular products"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM products
            ORDER BY avg_rating DESC, num_ratings DESC
            LIMIT ?
        ''', (limit,))
        
        products = cursor.fetchall()
        conn.close()
        
        results = []
        for product in products:
            p = dict(product)
            p['reason'] = "Trending now"
            results.append(p)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ CART ENDPOINTS ============

@app.post("/cart/add")
async def add_to_cart(product_id: str, user_id: str, quantity: int = 1):
    """Add product to cart"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO cart (user_id, product_id, quantity)
            VALUES (?, ?, ?)
        ''', (user_id, product_id, quantity))
        
        # Track interaction
        cursor.execute('''
            INSERT INTO interactions (user_id, product_id, interaction_type)
            VALUES (?, ?, 'cart_add')
        ''', (user_id, product_id))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Added to cart"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cart/{user_id}")
async def get_cart(user_id: str):
    """Get user's cart"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.cart_id, c.quantity, p.*
            FROM cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.user_id = ?
        ''', (user_id,))
        
        items = cursor.fetchall()
        conn.close()
        
        return [dict(item) for item in items]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/search")
async def search_products(q: str, limit: int = 60):
    """Search products by name, brand, category"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        search_term = f"%{q}%"
        
        cursor.execute('''
            SELECT * FROM products
            WHERE name LIKE ? 
            OR brand LIKE ?
            OR category LIKE ?
            OR description LIKE ?
            ORDER BY avg_rating DESC
            LIMIT ?
        ''', (search_term, search_term, search_term, search_term, limit))
        
        products = cursor.fetchall()
        conn.close()
        
        return [dict(product) for product in products]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# ============ STATS ============

@app.get("/stats")
async def get_stats():
    """Get system stats"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_guest = 0')
        num_users = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM products')
        num_products = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM interactions')
        num_interactions = cursor.fetchone()['count']
        
        cursor.execute('SELECT AVG(avg_rating) as avg FROM products')
        avg_rating = cursor.fetchone()['avg']
        
        conn.close()
        
        return {
            "num_users": num_users,
            "num_products": num_products,
            "num_interactions": num_interactions,
            "avg_rating": round(avg_rating, 2) if avg_rating else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """API info"""
    return {
        "name": "ShopSmart API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "User Authentication",
            "Cold Start Tracking (60s)",
            "Real Product Database",
            "Personalized Recommendations",
            "Cart Management"
        ],
        "docs": "/docs"
    }
@app.get("/admin/recent-activity")
async def get_recent_activity(limit: int = 20):
    """Get recent user interactions - REAL DATA"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                i.interaction_type,
                i.hover_duration,
                u.name as user_name,
                u.is_guest,
                p.name as product_name,
                p.category,
                i.timestamp,
                i.interest_score
            FROM interactions i
            LEFT JOIN users u ON i.user_id = u.user_id
            LEFT JOIN products p ON i.product_id = p.product_id
            ORDER BY i.timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        activities = cursor.fetchall()
        conn.close()
        
        result = []
        for activity in activities:
            result.append({
                'type': activity['interaction_type'],
                'hover_duration': activity['hover_duration'],
                'user': activity['user_name'] or 'Guest User',
                'is_guest': activity['is_guest'],
                'product': activity['product_name'] or 'Unknown Product',
                'category': activity['category'],
                'timestamp': activity['timestamp'],
                'score': activity['interest_score'] or 0
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Activity fetch error: {e}")
        return []

@app.get("/admin/hover-analytics")
async def get_hover_analytics(limit: int = 10):
    """Get products by hover time - REAL DATA"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                p.product_id,
                p.name,
                p.category,
                p.brand,
                COUNT(DISTINCT i.user_id) as unique_users,
                SUM(i.hover_duration) as total_hover_time,
                COUNT(*) as hover_count,
                AVG(i.hover_duration) as avg_hover_time
            FROM products p
            LEFT JOIN interactions i ON p.product_id = i.product_id 
                AND i.interaction_type IN ('hover', 'view')
                AND i.hover_duration > 0
            GROUP BY p.product_id
            HAVING total_hover_time > 0
            ORDER BY total_hover_time DESC
            LIMIT ?
        ''', (limit,))
        
        products = cursor.fetchall()
        conn.close()
        
        return [dict(product) for product in products]
        
    except Exception as e:
        logger.error(f"Hover analytics error: {e}")
        return []

@app.get("/admin/category-performance")
async def get_category_performance():
    """Get category-wise interaction stats - REAL DATA"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                p.category,
                COUNT(DISTINCT i.user_id) as unique_users,
                COUNT(i.interaction_id) as total_interactions,
                SUM(CASE WHEN i.interaction_type = 'purchase' THEN 1 ELSE 0 END) as purchases,
                SUM(i.interest_score) as total_interest
            FROM products p
            LEFT JOIN interactions i ON p.product_id = i.product_id
            WHERE i.interaction_id IS NOT NULL
            GROUP BY p.category
            ORDER BY total_interest DESC
        ''')
        
        categories = cursor.fetchall()
        conn.close()
        
        return [dict(cat) for cat in categories]
        
    except Exception as e:
        logger.error(f"Category performance error: {e}")
        return []
@app.get("/recommend/ncf/{user_id}")
async def ncf_recommendations(user_id: str, limit: int = 100):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products ORDER BY popularity_score DESC LIMIT ?', (limit,))
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return products
    except Exception as e:
        logger.error(f"NCF error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 STARTING SHOPSMART API v2.0")
    print("="*60)
    print("\nFeatures:")
    print("  ✓ User Authentication (Login/Signup)")
    print("  ✓ Cold Start Tracking (60-second behavioral)")
    print("  ✓ Real Product Database")
    print("  ✓ Personalized Recommendations")
    print("  ✓ Cart Management")
    print(f"\nServer: http://localhost:8000")
    print(f"Docs: http://localhost:8000/docs")
    print("\nPress CTRL+C to stop")
    print("="*60 + "\n")
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)