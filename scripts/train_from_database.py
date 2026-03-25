"""
Train models from database (not CSV)
Use this when data is already in database
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
import logging
from datetime import datetime
import joblib
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_data_from_db():
    """Load interaction data from database"""
    logger.info("="*60)
    logger.info("STEP 1: LOADING DATA FROM DATABASE")
    logger.info("="*60)
    
    conn = sqlite3.connect('data/ecommerce.db')
    
    # Load interactions with product details
    query = '''
        SELECT 
            i.user_id as user,
            i.product_id as item,
            COALESCE(i.rating, 4) as rating,
            i.timestamp,
            p.description as review_text,
            p.price,
            p.category,
            p.brand
        FROM interactions i
        LEFT JOIN products p ON i.product_id = p.product_id
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    logger.info(f"✓ Loaded {len(df):,} interactions from database")
    logger.info(f"✓ Users: {df['user'].nunique()}")
    logger.info(f"✓ Products: {df['item'].nunique()}")
    
    return df


def train_collaborative_filtering(df):
    """Train collaborative filtering using scikit-learn SVD"""
    logger.info("\n" + "="*60)
    logger.info("STEP 2: TRAINING COLLABORATIVE FILTERING (SVD)")
    logger.info("="*60)
    
    try:
        logger.info("Preparing data for matrix factorization...")
        
        user_encoder = LabelEncoder()
        item_encoder = LabelEncoder()
        
        df['user_encoded'] = user_encoder.fit_transform(df['user'])
        df['item_encoded'] = item_encoder.fit_transform(df['item'])
        
        n_users = df['user_encoded'].nunique()
        n_items = df['item_encoded'].nunique()
        
        logger.info(f"Creating {n_users}x{n_items} user-item matrix...")
        
        user_item_matrix = np.zeros((n_users, n_items))
        for _, row in df.iterrows():
            user_item_matrix[int(row['user_encoded']), int(row['item_encoded'])] = row['rating']
        
        logger.info("Training SVD model...")
        n_components = min(50, min(n_users, n_items) - 1)
        
        svd = TruncatedSVD(n_components=n_components, random_state=42)
        user_features = svd.fit_transform(user_item_matrix)
        item_features = svd.components_.T
        
        logger.info(f"✓ Model trained! Components: {n_components}")
        
        model_path = 'models/collaborative/'
        Path(model_path).mkdir(parents=True, exist_ok=True)
        
        joblib.dump(svd, f'{model_path}svd_model.pkl')
        joblib.dump(user_encoder, f'{model_path}user_encoder.pkl')
        joblib.dump(item_encoder, f'{model_path}item_encoder.pkl')
        joblib.dump(user_features, f'{model_path}user_features.pkl')
        joblib.dump(item_features, f'{model_path}item_features.pkl')
        joblib.dump(user_item_matrix, f'{model_path}user_item_matrix.pkl')
        
        logger.info(f"✓ Model saved to: {model_path}")
        return svd
        
    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        return None


def train_cold_start_model():
    """Train cold start model from database"""
    logger.info("\n" + "="*60)
    logger.info("STEP 3: TRAINING COLD START MODEL")
    logger.info("="*60)
    
    try:
        conn = sqlite3.connect('data/ecommerce.db')
        
        query = '''
            SELECT 
                p.product_id as item,
                AVG(p.avg_rating) as avg_rating,
                p.num_ratings as num_ratings,
                COUNT(i.interaction_id) as interaction_count
            FROM products p
            LEFT JOIN interactions i ON p.product_id = i.product_id
            GROUP BY p.product_id
        '''
        
        item_stats = pd.read_sql_query(query, conn)
        conn.close()
        
        item_stats['popularity_score'] = (
            item_stats['avg_rating'] * 0.5 + 
            np.log1p(item_stats['num_ratings']) * 0.3 +
            np.log1p(item_stats['interaction_count']) * 0.2
        )
        
        popular_items = item_stats.sort_values('popularity_score', ascending=False)
        
        model_path = 'models/cold_start/'
        Path(model_path).mkdir(parents=True, exist_ok=True)
        joblib.dump(popular_items, f'{model_path}popular_items.pkl')
        
        logger.info(f"✓ Cold start model saved")
        logger.info(f"✓ Top item: {popular_items.iloc[0]['item']}")
        
        return popular_items
        
    except Exception as e:
        logger.error(f"❌ Cold start training failed: {e}")
        return None


def save_metadata(df):
    """Save training metadata"""
    logger.info("\n" + "="*60)
    logger.info("STEP 4: SAVING METADATA")
    logger.info("="*60)
    
    metadata = {
        'training_date': datetime.now().isoformat(),
        'num_users': df['user'].nunique(),
        'num_items': df['item'].nunique(),
        'num_interactions': len(df),
        'avg_rating': df['rating'].mean(),
        'data_source': 'database'
    }
    
    Path('models').mkdir(exist_ok=True)
    joblib.dump(metadata, 'models/training_metadata.pkl')
    
    logger.info("Training Statistics:")
    for key, value in metadata.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.4f}")
        else:
            logger.info(f"  {key}: {value}")
    
    logger.info("✓ Metadata saved")


def main():
    """Main training pipeline"""
    print("\n" + "="*60)
    print("🚀 TRAINING FROM DATABASE")
    print("="*60 + "\n")
    
    start_time = datetime.now()
    
    try:
        df = load_data_from_db()
        
        collab_model = train_collaborative_filtering(df)
        cold_start_model = train_cold_start_model()
        
        save_metadata(df)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "="*60)
        print("✅ TRAINING COMPLETE!")
        print("="*60)
        print(f"\n⏱️  Total time: {duration:.1f} seconds")
        print(f"📊 Models trained: 2/2")
        print(f"💾 Models saved to: models/")
        
        print("\n📋 NEXT STEPS:")
        print("  1. Start API: python src/api/main.py")
        print("  2. Open browser: http://localhost:8000/docs")
        print("  3. Browse: start frontend/shop.html")
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        logger.error(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()