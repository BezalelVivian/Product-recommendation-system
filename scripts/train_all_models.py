"""
Train all recommendation models - FIXED VERSION
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import pandas as pd
import numpy as np
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

from src.data_adapters.schema_detector import detect_dataset_schema
from src.data_adapters.column_mapper import map_to_standard_format


def load_data():
    """Load and prepare data."""
    logger.info("="*60)
    logger.info("STEP 1: LOADING DATA")
    logger.info("="*60)
    
    raw_path = Path('data/raw')
    sample_path = Path('data/sample_datasets')
    
    csv_files = list(raw_path.glob('*.csv'))
    
    if not csv_files:
        logger.info("No data in data/raw/, using sample data...")
        csv_files = list(sample_path.glob('interactions.csv'))
    
    if not csv_files:
        logger.error("❌ No CSV files found!")
        sys.exit(1)
    
    data_file = csv_files[0]
    logger.info(f"Loading: {data_file}")
    
    df = pd.read_csv(data_file)
    logger.info(f"✓ Loaded {len(df):,} rows, {len(df.columns)} columns")
    
    logger.info("\nDetecting dataset schema...")
    schema = detect_dataset_schema(df, verbose=True)
    
    logger.info("Mapping to standard format...")
    df_standard = map_to_standard_format(df, schema)
    
    logger.info(f"✓ Standardized dataset ready: {len(df_standard):,} rows")
    logger.info(f"✓ Columns: {df_standard.columns.tolist()}")
    
    return df_standard


def train_collaborative_filtering(df):
    """Train collaborative filtering using scikit-learn SVD."""
    logger.info("\n" + "="*60)
    logger.info("STEP 2: TRAINING COLLABORATIVE FILTERING (SVD)")
    logger.info("="*60)
    
    try:
        logger.info("Preparing data for matrix factorization...")
        
        # Use standardized column names
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
        
        logger.info("Training SVD model (this takes 2-5 minutes)...")
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
        logger.error(f"❌ Collaborative filtering training failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def train_content_based(df):
    """Train content-based model."""
    logger.info("\n" + "="*60)
    logger.info("STEP 3: TRAINING CONTENT-BASED FILTERING")
    logger.info("="*60)
    
    try:
        if 'review_text' not in df.columns or df['review_text'].isna().all():
            logger.warning("⚠️  No review text available, skipping content-based model")
            return None
        
        logger.info("Creating TF-IDF vectors from review text...")
        
        item_reviews = df.groupby('item')['review_text'].apply(
            lambda x: ' '.join(x.astype(str))
        ).reset_index()
        
        vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(item_reviews['review_text'])
        
        logger.info("Calculating item similarity...")
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        model_path = 'models/content_based/'
        Path(model_path).mkdir(parents=True, exist_ok=True)
        
        joblib.dump(vectorizer, f'{model_path}tfidf_vectorizer.pkl')
        joblib.dump(similarity_matrix, f'{model_path}similarity_matrix.pkl')
        joblib.dump(item_reviews, f'{model_path}item_mapping.pkl')
        
        logger.info(f"✓ Content model saved")
        logger.info(f"✓ Similarity matrix shape: {similarity_matrix.shape}")
        
        return {'vectorizer': vectorizer, 'similarity': similarity_matrix}
        
    except Exception as e:
        logger.error(f"❌ Content-based training failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def train_cold_start_model(df):
    """Train cold start model."""
    logger.info("\n" + "="*60)
    logger.info("STEP 4: TRAINING COLD START MODEL")
    logger.info("="*60)
    
    try:
        logger.info("Computing popular items for cold start...")
        
        item_stats = df.groupby('item').agg({
            'rating': ['mean', 'count'],
            'user': 'count'
        }).reset_index()
        
        item_stats.columns = ['item', 'avg_rating', 'num_ratings', 'num_users']
        
        item_stats['popularity_score'] = (
            item_stats['avg_rating'] * 0.5 + 
            np.log1p(item_stats['num_ratings']) * 0.5
        )
        
        popular_items = item_stats.sort_values('popularity_score', ascending=False)
        
        model_path = 'models/cold_start/'
        Path(model_path).mkdir(parents=True, exist_ok=True)
        joblib.dump(popular_items, f'{model_path}popular_items.pkl')
        
        logger.info(f"✓ Cold start model saved")
        logger.info(f"✓ Top item: {popular_items.iloc[0]['item']} "
                   f"(score: {popular_items.iloc[0]['popularity_score']:.2f})")
        
        return popular_items
        
    except Exception as e:
        logger.error(f"❌ Cold start training failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_metadata(df):
    """Save training metadata."""
    logger.info("\n" + "="*60)
    logger.info("STEP 5: SAVING METADATA")
    logger.info("="*60)
    
    metadata = {
        'training_date': datetime.now().isoformat(),
        'num_users': df['user'].nunique(),
        'num_items': df['item'].nunique(),
        'num_interactions': len(df),
        'avg_rating': df['rating'].mean(),
        'sparsity': 1 - (len(df) / (df['user'].nunique() * df['item'].nunique()))
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
    """Main training pipeline."""
    print("\n" + "="*60)
    print("🚀 ADAPTIVE RECOMMENDATION SYSTEM - MODEL TRAINING")
    print("="*60 + "\n")
    
    start_time = datetime.now()
    
    try:
        df = load_data()
        
        collab_model = train_collaborative_filtering(df)
        content_model = train_content_based(df)
        cold_start_model = train_cold_start_model(df)
        
        save_metadata(df)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "="*60)
        print("✅ TRAINING COMPLETE!")
        print("="*60)
        print(f"\n⏱️  Total time: {duration/60:.1f} minutes")
        print(f"📊 Models trained: {sum([collab_model is not None, content_model is not None, cold_start_model is not None])}/3")
        print(f"💾 Models saved to: models/")
        
        print("\n📋 NEXT STEPS:")
        print("  1. Start API: python src/api/main.py")
        print("  2. Open browser: http://localhost:8000/docs")
        print("  3. Test recommendations!")
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        logger.error(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()