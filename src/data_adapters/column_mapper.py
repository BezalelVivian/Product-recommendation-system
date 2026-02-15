"""
Column Mapper - Standardize Any Dataset
"""

import pandas as pd
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class ColumnMapper:
    """Maps diverse column names to standardized format."""
    
    def __init__(self):
        self.mapping = {}
    
    def transform_with_defaults(self, df: pd.DataFrame,
                                detected_schema: Dict[str, str]) -> pd.DataFrame:
        """Transform and add missing columns with defaults."""
        
        # Create reverse mapping: semantic_type -> standard_name
        standard_names = {
            'user': 'user',
            'item': 'item',
            'rating': 'rating',
            'timestamp': 'timestamp',
            'review_text': 'review_text',
            'product_name': 'product_name',
            'category': 'category',
            'price': 'price',
            'brand': 'brand',
            'image': 'image'
        }
        
        # Build new dataframe with standard columns
        df_standard = pd.DataFrame()
        
        for semantic_type, original_col in detected_schema.items():
            if semantic_type in standard_names:
                standard_col = standard_names[semantic_type]
                df_standard[standard_col] = df[original_col]
        
        # Add missing CRITICAL columns
        if 'user' not in df_standard.columns:
            logger.error("❌ CRITICAL: No user column found!")
            raise ValueError("User column is required!")
            
        if 'item' not in df_standard.columns:
            logger.error("❌ CRITICAL: No item column found!")
            raise ValueError("Item column is required!")
        
        # Add missing optional columns
        if 'rating' not in df_standard.columns:
            df_standard['rating'] = 0.0
        
        if 'timestamp' not in df_standard.columns:
            df_standard['timestamp'] = pd.Timestamp.now()
        
        if 'review_text' not in df_standard.columns:
            df_standard['review_text'] = ""
        
        if 'price' not in df_standard.columns:
            df_standard['price'] = 0.0
        
        if 'category' not in df_standard.columns:
            df_standard['category'] = "Unknown"
        
        if 'brand' not in df_standard.columns:
            df_standard['brand'] = "Unknown"
        
        logger.info(f"Transformed dataset to standard format with {len(df_standard.columns)} columns")
        logger.info("Added default values for missing columns")
        
        return df_standard


def map_to_standard_format(df: pd.DataFrame, 
                           detected_schema: Dict[str, str],
                           add_defaults: bool = True) -> pd.DataFrame:
    """One-line function to standardize any dataset."""
    mapper = ColumnMapper()
    return mapper.transform_with_defaults(df, detected_schema)


if __name__ == "__main__":
    from schema_detector import detect_dataset_schema
    
    df = pd.DataFrame({
        'buyer_email': ['user1@x.com', 'user2@y.com'],
        'article_no': ['ART001', 'ART002'],
        'score': [4.5, 3.5]
    })
    
    print("Original DataFrame:")
    print(df)
    
    schema = detect_dataset_schema(df, verbose=False)
    df_standard = map_to_standard_format(df, schema)
    
    print("\n\nStandardized DataFrame:")
    print(df_standard)
    print(f"\nColumns: {df_standard.columns.tolist()}")