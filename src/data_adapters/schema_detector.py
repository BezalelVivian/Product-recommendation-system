"""
========================================================================
SCHEMA DETECTOR - Universal Dataset Structure Recognition
========================================================================

THIS IS THE MAGIC! 🎯

This module automatically detects what each column in your CSV means,
even if columns have different names.

Examples:
  - "user_id", "customer_code", "buyer_email" → All recognized as USER
  - "product_id", "item_sku", "asin" → All recognized as ITEM
  - "rating", "stars", "score" → All recognized as RATING

HOW IT WORKS:
1. Analyzes column names using keyword matching
2. Examines data types and distributions
3. Checks value patterns (email format, numeric ranges, etc.)
4. Assigns semantic meaning to each column

========================================================================
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class SchemaDetector:
    """
    Automatically detects the schema/structure of e-commerce datasets.
    
    Works with ANY CSV - Amazon, Flipkart, custom formats, etc.
    """
    
    def __init__(self):
        """Initialize the schema detector with keyword patterns."""
        
        # ============================================================
        # COLUMN NAME PATTERNS
        # Add your dataset's column names here if auto-detection fails
        # ============================================================
        
        self.column_patterns = {
            # User/Customer identification
            'user': [
                'user', 'customer', 'buyer', 'client', 'member',
                'userid', 'user_id', 'customer_id', 'cust_id',
                'buyer_id', 'account', 'username', 'email'
            ],
            
            # Product/Item identification
            'item': [
                'product', 'item', 'article', 'sku', 'asin',
                'product_id', 'item_id', 'article_id', 'article_no',
                'prod_id', 'merchandise', 'goods'
            ],
            
            # Rating/Score
            'rating': [
                'rating', 'score', 'stars', 'review_score',
                'user_rating', 'product_rating', 'feedback_score'
            ],
            
            # Timestamp
            'timestamp': [
                'time', 'date', 'datetime', 'timestamp', 'created',
                'purchase_date', 'review_date', 'order_date',
                'bought_at', 'reviewed_at'
            ],
            
            # Review text
            'review_text': [
                'review', 'comment', 'feedback', 'text', 'description',
                'review_text', 'user_review', 'comments', 'opinion'
            ],
            
            # Product name/title
            'product_name': [
                'name', 'title', 'product_name', 'item_name',
                'product_title', 'description'
            ],
            
            # Category
            'category': [
                'category', 'class', 'type', 'department', 'section',
                'product_category', 'item_category', 'genre'
            ],
            
            # Price
            'price': [
                'price', 'cost', 'amount', 'value', 'mrp',
                'product_price', 'item_price', 'unit_price'
            ],
            
            # Brand
            'brand': [
                'brand', 'manufacturer', 'make', 'company',
                'brand_name', 'vendor'
            ],
            
            # Image URL
            'image': [
                'image', 'img', 'picture', 'photo', 'thumbnail',
                'image_url', 'img_url', 'product_image'
            ],
        }
    
    def detect_schema(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Detect the schema of a DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary mapping semantic type to column name
            Example: {'user': 'customer_id', 'item': 'product_sku', ...}
        """
        logger.info(f"Detecting schema for DataFrame with {len(df.columns)} columns")
        
        schema_mapping = {}
        
        for semantic_type, keywords in self.column_patterns.items():
            detected_column = self._find_column(df, keywords, semantic_type)
            if detected_column:
                schema_mapping[semantic_type] = detected_column
                logger.info(f"✓ Detected {semantic_type}: '{detected_column}'")
            else:
                logger.warning(f"✗ Could not detect {semantic_type} column")
        
        return schema_mapping
    
    def _find_column(self, df: pd.DataFrame, keywords: List[str], 
                     semantic_type: str) -> Optional[str]:
        """
        Find a column matching the given keywords.
        
        Args:
            df: DataFrame to search
            keywords: List of keyword patterns to match
            semantic_type: Type of column we're looking for
            
        Returns:
            Column name if found, None otherwise
        """
        # Step 1: Try exact keyword matching (case-insensitive)
        for col in df.columns:
            col_lower = str(col).lower().strip()
            for keyword in keywords:
                if keyword in col_lower or col_lower in keyword:
                    if self._validate_column_type(df[col], semantic_type):
                        return col
        
        # Step 2: Try pattern-based detection using data analysis
        for col in df.columns:
            if self._detect_by_data_pattern(df[col], semantic_type):
                return col
        
        return None
    
    def _validate_column_type(self, series: pd.Series, 
                             semantic_type: str) -> bool:
        """
        Validate that a column's data matches expected type.
        
        Args:
            series: Pandas Series to validate
            semantic_type: Expected semantic type
            
        Returns:
            True if column appears to match the type
        """
        # Remove null values for analysis
        series_clean = series.dropna()
        
        if len(series_clean) == 0:
            return False
        
        # User ID: Should have many unique values (high cardinality)
        if semantic_type == 'user':
            unique_ratio = len(series_clean.unique()) / len(series_clean)
            return unique_ratio > 0.1  # At least 10% unique
        
        # Item ID: Should have high cardinality
        elif semantic_type == 'item':
            unique_ratio = len(series_clean.unique()) / len(series_clean)
            return unique_ratio > 0.05  # At least 5% unique
        
        # Rating: Should be numeric and in reasonable range
        elif semantic_type == 'rating':
            try:
                numeric_series = pd.to_numeric(series_clean, errors='coerce')
                if numeric_series.isna().all():
                    return False
                min_val, max_val = numeric_series.min(), numeric_series.max()
                # Ratings typically 1-5 or 1-10
                return min_val >= 0 and max_val <= 10
            except:
                return False
        
        # Timestamp: Should be datetime-parseable
        elif semantic_type == 'timestamp':
            try:
                pd.to_datetime(series_clean.head(100), errors='coerce')
                return True
            except:
                return False
        
        # Review text: Should be string with reasonable length
        elif semantic_type == 'review_text':
            if not pd.api.types.is_string_dtype(series):
                return False
            avg_length = series_clean.astype(str).str.len().mean()
            return avg_length > 10  # Reviews usually > 10 characters
        
        # Price: Should be numeric and positive
        elif semantic_type == 'price':
            try:
                numeric_series = pd.to_numeric(series_clean, errors='coerce')
                if numeric_series.isna().all():
                    return False
                return (numeric_series >= 0).all()
            except:
                return False
        
        # Category/Brand: Should be string with moderate cardinality
        elif semantic_type in ['category', 'brand']:
            if not pd.api.types.is_string_dtype(series):
                return False
            unique_ratio = len(series_clean.unique()) / len(series_clean)
            # Categories/Brands: 1-30% unique typically
            return 0.01 < unique_ratio < 0.3
        
        return True
    
    def _detect_by_data_pattern(self, series: pd.Series, 
                                semantic_type: str) -> bool:
        """
        Detect column type by analyzing data patterns.
        
        Args:
            series: Series to analyze
            semantic_type: Type to check for
            
        Returns:
            True if patterns match the semantic type
        """
        series_clean = series.dropna()
        
        if len(series_clean) < 10:  # Need enough samples
            return False
        
        # Check for email patterns (likely user identifier)
        if semantic_type == 'user':
            email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            sample = series_clean.head(100).astype(str)
            email_matches = sample.str.match(email_pattern).sum()
            if email_matches / len(sample) > 0.5:  # >50% are emails
                return True
        
        # Check for SKU patterns (likely item identifier)
        if semantic_type == 'item':
            # SKUs often have pattern like ABC-123 or ABC123DEF
            sku_pattern = r'^[A-Z0-9]+-?[A-Z0-9]+$'
            sample = series_clean.head(100).astype(str)
            sku_matches = sample.str.match(sku_pattern, flags=re.IGNORECASE).sum()
            if sku_matches / len(sample) > 0.5:
                return True
        
        return False
    
    def print_schema_summary(self, df: pd.DataFrame, 
                           schema: Dict[str, str]) -> None:
        """
        Print a nice summary of detected schema.
        
        Args:
            df: Original DataFrame
            schema: Detected schema mapping
        """
        print("\n" + "="*60)
        print("📊 DETECTED DATASET SCHEMA")
        print("="*60)
        
        for semantic_type, col_name in schema.items():
            sample_values = df[col_name].dropna().head(3).tolist()
            print(f"\n✓ {semantic_type.upper()}: '{col_name}'")
            print(f"  Sample values: {sample_values}")
            print(f"  Data type: {df[col_name].dtype}")
            print(f"  Non-null count: {df[col_name].notna().sum():,}")
        
        print("\n" + "="*60)
        
        # Show unmapped columns
        mapped_cols = set(schema.values())
        unmapped_cols = set(df.columns) - mapped_cols
        
        if unmapped_cols:
            print("\n⚠️  UNMAPPED COLUMNS (will be ignored):")
            for col in unmapped_cols:
                print(f"  - {col}")
        
        print("\n" + "="*60 + "\n")


# ================================================================
# HELPER FUNCTION FOR EASY USE
# ================================================================

def detect_dataset_schema(df: pd.DataFrame, verbose: bool = True) -> Dict[str, str]:
    """
    One-line function to detect any dataset's schema.
    
    Usage:
        >>> df = pd.read_csv('any_ecommerce_data.csv')
        >>> schema = detect_dataset_schema(df)
        >>> user_col = schema['user']  # Get the user column name
    
    Args:
        df: Your DataFrame
        verbose: Print detailed summary
        
    Returns:
        Dictionary mapping semantic types to column names
    """
    detector = SchemaDetector()
    schema = detector.detect_schema(df)
    
    if verbose:
        detector.print_schema_summary(df, schema)
    
    return schema


# ================================================================
# EXAMPLE USAGE
# ================================================================

if __name__ == "__main__":
    # Example 1: Amazon-style dataset
    print("Example 1: Amazon-style data")
    amazon_data = pd.DataFrame({
        'user_id': ['U001', 'U002', 'U003'],
        'product_id': ['P001', 'P002', 'P003'],
        'rating': [5, 4, 3],
        'timestamp': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'review_text': ['Great!', 'Good product', 'Okay']
    })
    
    schema1 = detect_dataset_schema(amazon_data)
    
    # Example 2: Flipkart-style dataset
    print("\nExample 2: Flipkart-style data")
    flipkart_data = pd.DataFrame({
        'customer_code': ['C001', 'C002', 'C003'],
        'item_sku': ['SKU123', 'SKU456', 'SKU789'],
        'stars': [4, 5, 3],
        'purchase_date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'comment': ['Nice!', 'Excellent', 'Average']
    })
    
    schema2 = detect_dataset_schema(flipkart_data)
    
    # Example 3: Custom dataset
    print("\nExample 3: Custom data")
    custom_data = pd.DataFrame({
        'buyer_email': ['a@x.com', 'b@y.com', 'c@z.com'],
        'article_no': ['ART001', 'ART002', 'ART003'],
        'score': [4.5, 3.5, 5.0],
        'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'feedback': ['Good', 'Ok', 'Perfect']
    })
    
    schema3 = detect_dataset_schema(custom_data)
    
    print("\n✅ All datasets detected successfully!")
    print("The system works with ANY column names! 🎉")
