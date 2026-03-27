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
import sys
from fastapi.staticfiles import StaticFiles

class ColdStartPreferences(BaseModel):
    categories: List[str]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

DB_PATH = 'data/ecommerce.db'

class UserSignup(BaseModel): email: str; password: str; name: str
class UserLogin(BaseModel): email: str; password: str
class BehavioralData(BaseModel): session_id: str; user_id: Optional[str] = None; events: List[dict]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str: return hashlib.sha256(password.encode()).hexdigest()

# ============ AUTH ============
@app.get("/categories")
def get_categories(limit: int = 20):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT category, COUNT(product_id) as total 
        FROM products 
        GROUP BY category 
        ORDER BY total DESC 
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{"name": row["category"], "count": row["total"]} for row in rows]

@app.post("/auth/signup")
async def signup(user: UserSignup):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT email FROM users WHERE email = ?', (user.email,))
        if cursor.fetchone(): raise HTTPException(status_code=400, detail="Email already registered")
        user_id = f"U{uuid.uuid4().hex[:8].upper()}"
        cursor.execute('INSERT INTO users (user_id, email, password_hash, name) VALUES (?, ?, ?, ?)', 
                       (user_id, user.email, hash_password(user.password), user.name))
        session_id = str(uuid.uuid4())
        cursor.execute('INSERT INTO sessions (session_id, user_id) VALUES (?, ?)', (session_id, user_id))
        conn.commit()
        conn.close()
        return {"success": True, "user_id": user_id, "session_id": session_id, "name": user.name}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login")
async def login(credentials: UserLogin):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, name, email FROM users WHERE email = ? AND password_hash = ?', 
                       (credentials.email, hash_password(credentials.password)))
        user = cursor.fetchone()
        if not user: raise HTTPException(status_code=401, detail="Invalid credentials")
        session_id = str(uuid.uuid4())
        cursor.execute('INSERT INTO sessions (session_id, user_id) VALUES (?, ?)', (session_id, user['user_id']))
        conn.commit()
        conn.close()
        return {"success": True, "user_id": user['user_id'], "session_id": session_id, "name": user['name']}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/guest")
async def guest_session():
    try:
        conn = get_db()
        cursor = conn.cursor()
        user_id = f"GUEST{uuid.uuid4().hex[:8].upper()}"
        session_id = str(uuid.uuid4())
        cursor.execute('INSERT INTO users (user_id, email, password_hash, name, is_guest) VALUES (?, ?, ?, ?, 1)', 
                       (user_id, f"{user_id}@guest.com", "", "Guest User"))
        cursor.execute('INSERT INTO sessions (session_id, user_id) VALUES (?, ?)', (session_id, user_id))
        conn.commit()
        conn.close()
        return {"success": True, "user_id": user_id, "session_id": session_id, "is_guest": True}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/tracking/behavior")
async def track_behavior(data: BehavioralData):
    try:
        conn = get_db()
        cursor = conn.cursor()
        for event in data.events:
            if event.get('product_id'):
                score = 5 if event['type'] == 'click' else 10 if event['type'] == 'cart_add' else min(5, max(1, int(float(event.get('hover_duration', 0)))))
                cursor.execute('''INSERT INTO interactions (user_id, product_id, interaction_type, hover_duration, interest_score, timestamp)
                                  VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''', 
                               (data.user_id, event['product_id'], event['type'], event.get('hover_duration', 0.0), score))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/products")
def get_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    sort_by: str = "popularity",
    user_id: Optional[str] = None,
    limit: int = 400
):
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    
    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")
        
    if category:
        query += " AND category = ?"
        params.append(category)
        
    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
        
    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)
        
    if min_rating is not None:
        query += " AND avg_rating >= ?"
        params.append(min_rating)
        
    if sort_by == "popularity":
        if not category and not search:
            query += " ORDER BY (popularity_score * RANDOM()) DESC"
        else:
            query += " ORDER BY popularity_score DESC"
    elif sort_by == "price_low":
        query += " ORDER BY price ASC"
    elif sort_by == "price_high":
        query += " ORDER BY price DESC"
    elif sort_by == "rating":
        query += " ORDER BY avg_rating DESC"
        
    query += " LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return products

@app.get("/search")
async def search_products(q: str, limit: int = 60):
    try:
        conn = get_db()
        cursor = conn.cursor()
        search = f"%{q}%"
        cursor.execute('''SELECT * FROM products WHERE name LIKE ? OR brand LIKE ? OR category LIKE ? 
                          ORDER BY ( (num_ratings * avg_rating) + (50 * 4.0) ) / (num_ratings + 50) DESC LIMIT ?''', 
                       (search, search, search, limit))
        products = cursor.fetchall()
        conn.close()
        return [dict(p) for p in products]
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# ============ THE INDUSTRY-STANDARD PERSONA AI ============
@app.get("/recommend/cold-start/{session_id}")
async def cold_start_recommendations(session_id: str, limit: int = 400):
    try:
        conn = get_db()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Fetch the last 15 interactions with full product context
        cursor.execute('''
            SELECT p.category, p.brand, p.price, i.interest_score
            FROM interactions i 
            JOIN products p ON i.product_id = p.product_id 
            WHERE i.user_id = ? 
            ORDER BY i.timestamp DESC 
            LIMIT 15
        ''', (session_id,))
        
        recent_items = cursor.fetchall()
        
        if recent_items:
            # 2. Build the Real-Time User Persona
            category_scores = {}
            brands_seen = []
            prices = []
            
            for item in recent_items:
                if item['interest_score'] and item['interest_score'] >= 2.0:
                    cat = item['category']
                    brand = item['brand']
                    price = item['price']
                    
                    # Accumulate scores to find their TRUE favorite category
                    category_scores[cat] = category_scores.get(cat, 0) + item['interest_score']
                    
                    if brand and brand != 'Generic' and brand not in brands_seen:
                        brands_seen.append(brand)
                        
                    if price:
                        prices.append(price)

            # Extract the absolute most dominant traits
            top_categories = sorted(category_scores, key=category_scores.get, reverse=True)[:3]
            primary_category = top_categories[0] if top_categories else None
            primary_brand = brands_seen[0] if brands_seen else None
            
            # Calculate Price Bracketing (Affinity Range)
            min_price, max_price = 0, 999999
            if prices:
                avg_price = sum(prices) / len(prices)
                min_price = avg_price * 0.4  # Willing to go slightly cheaper
                max_price = avg_price * 2.0  # Willing to go up to double the price

            if top_categories:
                cat_placeholders = ','.join(['?'] * len(top_categories))
                
                # 3. The Dynamic Scoring Engine (Brand Affinity + Price Bracketing + Dominant Category)
                query = f"""
                    SELECT *, 
                    (
                        (CASE WHEN category = ? THEN 100 ELSE 0 END) +  /* Massive boost to their #1 category */
                        (CASE WHEN category IN ({cat_placeholders}) THEN 30 ELSE 0 END) + /* Moderate boost to secondary categories */
                        (CASE WHEN brand = ? THEN 80 ELSE 0 END) +      /* Brand Loyalty boost */
                        (CASE WHEN price BETWEEN ? AND ? THEN 40 ELSE 0 END) + /* Price Bracket match */
                        (avg_rating * 5)                                /* Quality assurance */
                    ) as match_score
                    FROM products
                    WHERE category IN ({cat_placeholders})
                    ORDER BY match_score DESC, popularity_score DESC
                    LIMIT ?
                """
                
                # Bind parameters safely
                params = [primary_category] + top_categories + [primary_brand, min_price, max_price] + top_categories + [limit]
                
                cursor.execute(query, params)
                products = cursor.fetchall()
                
                if len(products) > 0:
                    conn.close()
                    return [dict(p) for p in products]
                
        # Fallback if no valid clicks
        cursor.execute('SELECT * FROM products ORDER BY (popularity_score * RANDOM()) DESC LIMIT ?', (limit,))
        products = cursor.fetchall()
        conn.close()
        return [dict(p) for p in products]
        
    except Exception as e:
        logger.error(f"Persona AI failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommend/ncf/{user_id}")
async def ncf_recommendations(user_id: str, limit: int = 15):
    if ncf_model: return ncf_model.predict_for_user(user_id, top_k=limit)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products ORDER BY popularity_score DESC LIMIT ?', (limit,))
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products

# ============ CART & STATS ============
@app.post("/cart/add")
async def add_to_cart(product_id: str, user_id: str, quantity: int = 1):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)', (user_id, product_id, quantity))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/cart/{user_id}")
async def get_cart(user_id: str):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''SELECT c.cart_id, c.quantity, p.* FROM cart c JOIN products p ON c.product_id = p.product_id WHERE c.user_id = ?''', (user_id,))
        items = cursor.fetchall()
        conn.close()
        return [dict(item) for item in items]
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cart/remove/{cart_id}")
async def remove_from_cart(cart_id: int):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cart WHERE cart_id = ?', (cart_id,))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60 + "\n🚀 STARTING SHOPSMART API v2.0\n" + "="*60)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)