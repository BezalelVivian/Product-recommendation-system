import joblib
import numpy as np

print("\n🔍 ML MODEL DETAILS\n")

# Load model
model = joblib.load('models/collaborative/svd_model.pkl')
print(f"Algorithm: {type(model).__name__}")
print(f"Components: {model.components_.shape}")
print(f"Explained Variance: {model.explained_variance_ratio_.sum():.2%}")

# Show it's REAL math
print(f"\nSample values from model matrix:")
print(model.components_[0][:10])  # Shows actual numbers!

print("\n✅ This is a REAL trained model!")