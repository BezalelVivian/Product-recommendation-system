import os
import pandas as pd

folders = [
    'data/raw/myntra',
    'data/raw/amazon',
    'data/raw/amazon_reviews',
    'data/raw/amazon_reviews2',
    'data/raw/flipkart_products'
]

for folder in folders:
    print(f"\n{'='*60}")
    print(f"📁 FOLDER: {folder}")
    
    if not os.path.exists(folder):
        print("❌ Folder not found!")
        continue
    
    files = os.listdir(folder)
    csvs = [f for f in files if f.endswith('.csv')]
    imgs = [f for f in files if f.endswith(('.jpg', '.png', '.jpeg'))]
    
    print(f"CSV files ({len(csvs)}):")
    for csv in csvs[:10]:
        print(f"  - {csv}")
    if len(csvs) > 10:
        print(f"  ... and {len(csvs)-10} more")
    
    if imgs:
        print(f"Images: {len(imgs)} files")
    
    # Check columns of first CSV
    if csvs:
        try:
            df = pd.read_csv(f"{folder}/{csvs[0]}", nrows=1)
            print(f"\nColumns in {csvs[0]}:")
            print(f"  {df.columns.tolist()}")
        except Exception as e:
            print(f"Error reading: {e}")