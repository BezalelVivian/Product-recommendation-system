import os
import sqlite3
import random
import pickle
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.layers import Input, Embedding, Flatten, Dense, Concatenate, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import LabelEncoder
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("NCF_Trainer")

# --- 1. CONFIGURATION ---
DB_PATH = 'data/ecommerce.db'
MODEL_DIR = 'models/saved'
NUM_USERS = 2000
INTERACTIONS_PER_USER = (10, 50) # Each user interacts with 10 to 50 items
EMBEDDING_SIZE = 32

os.makedirs(MODEL_DIR, exist_ok=True)

def generate_training_data():
    """Generates realistic interaction data based on categories and popularity."""
    logger.info("🧠 Phase 1: Reading database & synthesizing realistic user behaviors...")
    
    conn = sqlite3.connect(DB_PATH)
    products_df = pd.read_sql_query("SELECT product_id, category, avg_rating, popularity_score FROM products", conn)
    conn.close()

    if products_df.empty:
        raise ValueError("Database is empty! Run import_clean_data.py first.")

    # Group products by category to simulate user preferences
    category_groups = products_df.groupby('category')
    all_categories = list(category_groups.groups.keys())
    
    interactions = []
    
    for user_id in range(1, NUM_USERS + 1):
        uid_str = f"USER_{user_id:05d}"
        
        # Give this user 1 to 3 "favorite" categories to create a pattern the AI can learn
        fav_cats = random.sample(all_categories, k=random.randint(1, 3))
        num_interactions = random.randint(*INTERACTIONS_PER_USER)
        
        for _ in range(num_interactions):
            # 80% chance to buy from favorite category, 20% random exploration
            if random.random() < 0.8:
                cat = random.choice(fav_cats)
            else:
                cat = random.choice(all_categories)
                
            cat_products = category_groups.get_group(cat)
            
            # Weight the choice by the product's actual popularity score (higher = more likely to click)
            # Weight the choice by the product's actual popularity score
            weights = cat_products['popularity_score'].values
            weights = np.nan_to_num(weights, nan=0.0) # Catch any weird database NaNs
            weight_sum = weights.sum()
            
            # The Safety Net: Prevent Divide-by-Zero
            if weight_sum > 0:
                weights = weights / weight_sum # Normalize normally
            else:
                weights = np.ones(len(weights)) / len(weights) # Equal chance for all
            
            chosen_product = np.random.choice(cat_products['product_id'].values, p=weights)
            
            # Generate a realistic rating/interaction score (1 to 5)
            base_rating = cat_products[cat_products['product_id'] == chosen_product]['avg_rating'].values[0]
            simulated_rating = np.clip(np.random.normal(loc=base_rating, scale=0.5), 1.0, 5.0)
            
            interactions.append([uid_str, chosen_product, simulated_rating])
            
    df = pd.DataFrame(interactions, columns=['user_id', 'product_id', 'rating'])
    
    # Remove duplicates (a user can only rate an item once)
    df = df.drop_duplicates(subset=['user_id', 'product_id'])
    logger.info(f"📊 Generated {len(df)} unique interactions for {NUM_USERS} users.")
    return df

def build_ncf_model(num_users, num_items):
    """Builds the Neural Collaborative Filtering (NeuMF) Deep Learning Architecture."""
    logger.info("🏗️ Phase 2: Building Dual-Embedding Neural Network...")
    
    # User Input & Embedding
    user_input = Input(shape=(1,), name='user_input')
    user_embedding = Embedding(input_dim=num_users, output_dim=EMBEDDING_SIZE, name='user_embedding')(user_input)
    user_vec = Flatten(name='user_flatten')(user_embedding)
    
    # Item Input & Embedding
    item_input = Input(shape=(1,), name='item_input')
    item_embedding = Embedding(input_dim=num_items, output_dim=EMBEDDING_SIZE, name='item_embedding')(item_input)
    item_vec = Flatten(name='item_flatten')(item_embedding)
    
    # Concatenate to merge User and Item vectors
    concat = Concatenate(name='concatenation')([user_vec, item_vec])
    
    # Multi-Layer Perceptron (MLP) layers to learn complex, non-linear patterns
    fc1 = Dense(128, activation='relu')(concat)
    drop1 = Dropout(0.2)(fc1)
    fc2 = Dense(64, activation='relu')(drop1)
    drop2 = Dropout(0.2)(fc2)
    fc3 = Dense(32, activation='relu')(drop2)
    
    # Output Layer (Predicting a rating from 1 to 5)
    output = Dense(1, activation='linear', name='output')(fc3)
    
    model = Model(inputs=[user_input, item_input], outputs=output)
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
    
    return model

def train_and_export():
    df = generate_training_data()
    
    logger.info("⚙️ Phase 3: Encoding Labels (String to Integer Mapping)...")
    user_encoder = LabelEncoder()
    item_encoder = LabelEncoder()
    
    df['user_idx'] = user_encoder.fit_transform(df['user_id'])
    df['item_idx'] = item_encoder.fit_transform(df['product_id'])
    
    num_users = len(user_encoder.classes_)
    num_items = len(item_encoder.classes_)
    
    # Save the encoders so the FastAPI backend knows how to translate future user IDs
    with open(os.path.join(MODEL_DIR, 'user_encoder.pkl'), 'wb') as f:
        pickle.dump(user_encoder, f)
    with open(os.path.join(MODEL_DIR, 'item_encoder.pkl'), 'wb') as f:
        pickle.dump(item_encoder, f)
        
    logger.info(f"💾 Saved Encoders: {num_users} Users, {num_items} Items.")
    
    model = build_ncf_model(num_users, num_items)
    model.summary()
    
    # Early stopping to prevent overfitting on your GPU
    early_stop = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)
    
    logger.info("🚀 Phase 4: Training Neural Network on RTX 2050...")
    history = model.fit(
        x=[df['user_idx'].values, df['item_idx'].values],
        y=df['rating'].values,
        batch_size=256,
        epochs=15,
        validation_split=0.1,
        callbacks=[early_stop],
        verbose=1
    )
    
    # Export the weights
    model_path = os.path.join(MODEL_DIR, 'ncf_model.h5')
    model.save(model_path)
    logger.info(f"✅ AI Training Complete! Model saved securely to {model_path}.")

if __name__ == "__main__":
    # Suppress TensorFlow informational logs for a cleaner terminal
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 
    train_and_export()