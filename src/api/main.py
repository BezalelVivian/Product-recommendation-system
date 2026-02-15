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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        # Log interactions
        for event in data.events:
            if event.get('product_id'):
                cursor.execute('''
                    INSERT INTO interactions (user_id, product_id, interaction_type, timestamp)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (data.user_id, event['product_id'], event['type']))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "events_tracked": len(data.events)}
        
    except Exception as e:
        logger.error(f"Tracking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ PRODUCT ENDPOINTS ============

@app.get("/products", response_model=List[ProductResponse])
async def get_products(category: Optional[str] = None, limit: int = 20):
    """Get products"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT * FROM products 
                WHERE category = ?
                ORDER BY avg_rating DESC
                LIMIT ?
            ''', (category, limit))
        else:
            cursor.execute('''
                SELECT * FROM products 
                ORDER BY avg_rating DESC
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
async def cold_start_recommend(session_id: str, limit: int = 10):
    """Cold start recommendations based on 60-second tracking"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get behavioral data
        cursor.execute('''
            SELECT behavioral_data, user_id FROM sessions
            WHERE session_id = ?
        ''', (session_id,))
        
        session = cursor.fetchone()
        
        if not session or not session['behavioral_data']:
            # Return popular items
            cursor.execute('''
                SELECT * FROM products
                ORDER BY avg_rating DESC, num_ratings DESC
                LIMIT ?
            ''', (limit,))
        else:
            # Analyze behavior and recommend
            events = json.loads(session['behavioral_data'])
            
            # Get viewed categories
            viewed_categories = set()
            for event in events:
                if event.get('category'):
                    viewed_categories.add(event['category'])
            
            if viewed_categories:
                # Recommend from viewed categories
                placeholders = ','.join('?' * len(viewed_categories))
                cursor.execute(f'''
                    SELECT * FROM products
                    WHERE category IN ({placeholders})
                    ORDER BY avg_rating DESC
                    LIMIT ?
                ''', (*viewed_categories, limit))
            else:
                cursor.execute('''
                    SELECT * FROM products
                    ORDER BY avg_rating DESC
                    LIMIT ?
                ''', (limit,))
        
        products = cursor.fetchall()
        conn.close()
        
        results = []
        for product in products:
            p = dict(product)
            p['reason'] = "Based on your browsing behavior"
            results.append(p)
        
        return results
        
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