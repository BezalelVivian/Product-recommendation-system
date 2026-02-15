"""
================================================================
SETUP SCRIPT - First Time Installation & Sample Data Generation
================================================================

Run this FIRST to set up the project!

What it does:
1. Checks Python version
2. Creates necessary directories
3. Generates sample e-commerce data (if you don't have your own)
4. Validates installation

Usage:
    python scripts/setup.py
================================================================
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_python_version():
    """Check if Python version is 3.8 or higher."""
    logger.info("Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error(f"❌ Python {version.major}.{version.minor} detected")
        logger.error("⚠️  Python 3.8+ required!")
        logger.error("Please upgrade: https://www.python.org/downloads/")
        sys.exit(1)
    
    logger.info(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")


def create_directories():
    """Create necessary project directories."""
    logger.info("Creating project directories...")
    
    dirs = [
        'data/raw',
        'data/processed',
        'data/features',
        'data/sample_datasets',
        'models/cold_start',
        'models/collaborative',
        'models/checkpoints',
        'logs',
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"  ✓ Created: {dir_path}")


def generate_sample_data():
    """Generate sample e-commerce dataset for testing."""
    logger.info("\nGenerating sample e-commerce data...")
    
    np.random.seed(42)
    
    # Parameters
    n_users = 1000
    n_products = 500
    n_interactions = 5000
    
    # Product categories
    categories = ['Electronics', 'Fashion', 'Home & Kitchen', 'Books', 'Sports', 'Toys']
    brands = ['BrandA', 'BrandB', 'BrandC', 'BrandD', 'BrandE']
    
    # Generate product catalog
    products = []
    for i in range(n_products):
        products.append({
            'product_id': f'P{i:04d}',
            'product_name': f'Product {i}',
            'category': np.random.choice(categories),
            'brand': np.random.choice(brands),
            'price': round(np.random.uniform(10, 500), 2),
            'description': f'This is product {i} with great features'
        })
    
    df_products = pd.DataFrame(products)
    
    # Generate user interactions
    interactions = []
    for i in range(n_interactions):
        user_id = f'U{np.random.randint(0, n_users):04d}'
        product_id = f'P{np.random.randint(0, n_products):04d}'
        rating = np.random.choice([1, 2, 3, 4, 5], p=[0.05, 0.1, 0.15, 0.3, 0.4])
        
        # Generate review text based on rating
        if rating >= 4:
            reviews = ['Great product!', 'Excellent quality', 'Highly recommend', 'Love it!']
        elif rating == 3:
            reviews = ['Good', 'Okay product', 'Average', 'Decent']
        else:
            reviews = ['Not good', 'Disappointed', 'Poor quality', 'Not recommended']
        
        interactions.append({
            'user_id': user_id,
            'product_id': product_id,
            'rating': rating,
            'timestamp': pd.Timestamp.now() - pd.Timedelta(days=np.random.randint(1, 365)),
            'review_text': np.random.choice(reviews)
        })
    
    df_interactions = pd.DataFrame(interactions)
    
    # Save to CSV
    products_path = 'data/sample_datasets/products.csv'
    interactions_path = 'data/sample_datasets/interactions.csv'
    
    df_products.to_csv(products_path, index=False)
    df_interactions.to_csv(interactions_path, index=False)
    
    logger.info(f"  ✓ Generated {n_products} products → {products_path}")
    logger.info(f"  ✓ Generated {n_interactions} interactions → {interactions_path}")
    logger.info(f"  ✓ {n_users} users, {n_products} products")


def create_env_file():
    """Create .env file with default settings."""
    logger.info("\nCreating .env file...")
    
    env_content = """# Adaptive Recommendation System - Environment Variables

# Database
DATABASE_URL=sqlite:///data/recommendations.db

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Secret Key (change this in production!)
SECRET_KEY=your-secret-key-change-in-production

# Model Paths
MODEL_PATH=models/
DATA_PATH=data/

# Logging
LOG_LEVEL=INFO
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    logger.info("  ✓ Created .env file")


def print_next_steps():
    """Print what to do next."""
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    
    print("\n📋 NEXT STEPS:\n")
    
    print("1. Install dependencies:")
    print("   pip install -r requirements.txt")
    
    print("\n2. Train models with sample data:")
    print("   python scripts/train_all_models.py")
    
    print("\n3. Start the API server:")
    print("   python src/api/main.py")
    
    print("\n4. Open your browser:")
    print("   http://localhost:8000/docs")
    
    print("\n" + "="*60)
    print("💡 TIP: To use your own data, put CSV files in data/raw/")
    print("="*60 + "\n")


def main():
    """Main setup function."""
    print("\n" + "="*60)
    print("🚀 ADAPTIVE RECOMMENDATION SYSTEM - SETUP")
    print("="*60 + "\n")
    
    try:
        check_python_version()
        create_directories()
        generate_sample_data()
        create_env_file()
        print_next_steps()
        
    except Exception as e:
        logger.error(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
