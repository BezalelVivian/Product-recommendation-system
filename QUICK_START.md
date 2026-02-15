# 🚀 QUICK START GUIDE (5 Minutes)

Get your recommendation system running in just 5 minutes!

---

## Step 1: Check Requirements (30 seconds)

```bash
# Check Python version (need 3.8+)
python --version
# If less than 3.8, install from: https://www.python.org/downloads/
```

**Your System:**
- ✅ RTX 2050 laptop - Perfect!
- ✅ Works on CPU (GPU optional)
- ✅ Need ~4GB free RAM

---

## Step 2: Install Dependencies (2-3 minutes)

```bash
# Navigate to project folder
cd adaptive-recommendation-system

# Install all required packages
pip install -r requirements.txt

# Wait for installation to complete...
```

**If installation fails:**
```bash
# Try this instead:
python -m pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt
```

---

## Step 3: Run Setup (30 seconds)

```bash
# This creates folders and generates sample data
python scripts/setup.py
```

**What this does:**
- Creates necessary directories
- Generates 1000 sample users, 500 products
- Creates sample interactions
- Sets up configuration

---

## Step 4: Train Models (10-15 minutes)

```bash
# Train all recommendation models
python scripts/train_all_models.py

# Go grab a coffee ☕ - this takes ~10-15 minutes
```

**What's happening:**
- Training collaborative filtering (SVD)
- Training content-based models
- Training sentiment analysis
- Training cold start models
- Saving all models to disk

**Progress bars will show you the status!**

---

## Step 5: Start the API (5 seconds)

```bash
# Start the recommendation server
python src/api/main.py

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete.
```

---

## Step 6: Test It! (1 minute)

Open your web browser and go to:

```
http://localhost:8000/docs
```

**You'll see an interactive API documentation page!**

### Try these:

1. **Get recommendations for a user:**
   - Click on `/recommend/user/{user_id}`
   - Click "Try it out"
   - Enter user_id: `U0001`
   - Click "Execute"
   - See personalized recommendations! 🎉

2. **Search products:**
   - Click on `/search`
   - Try query: `electronics`
   - See results!

---

## 🎉 SUCCESS! Your System is Running!

You now have a complete recommendation system working locally.

---

## What's Next?

### Use Your Own Data:

```bash
# 1. Put your CSV file in data/raw/
cp your_data.csv data/raw/

# 2. Retrain with your data
python scripts/train_all_models.py

# That's it! System auto-detects your columns.
```

### Customize Settings:

```bash
# Edit configuration (no coding needed!)
# Open: config/settings.yaml
# Change weights, enable/disable features, etc.
```

### Learn More:

- Read: `docs/TUTORIAL_FOR_BEGINNERS.md`
- Explore: `notebooks/01_Quick_Demo.ipynb`
- Understand: `PROJECT_CONTEXT.md`

---

## 🐛 Troubleshooting

### "Port 8000 already in use"
```yaml
# Edit config/settings.yaml, change:
api:
  port: 8001  # Use different port
```

### "Memory Error"
```yaml
# Edit config/model_config.yaml, change:
collaborative_filtering:
  svd:
    n_factors: 20  # Reduce from 50
training:
  batch_size: 16  # Reduce from 32
```

### "Module not found"
```bash
# Reinstall dependencies:
pip install -r requirements.txt
```

### Still stuck?
```bash
# Run diagnostic:
python scripts/diagnose.py
# Check: logs/diagnostic_report.txt
```

---

## 📊 Quick Commands Reference

```bash
# Setup (first time only)
python scripts/setup.py

# Train models
python scripts/train_all_models.py

# Start API
python src/api/main.py

# Test recommendations
python scripts/test_recommendations.py

# Check for issues
python scripts/diagnose.py

# Use your own data
cp your_data.csv data/raw/
python scripts/train_all_models.py
```

---

## 🎓 Your System Features

✅ **Works with ANY CSV** - Auto-detects columns  
✅ **Novel Cold Start** - Learns from behavior in 60 seconds  
✅ **Multiple Algorithms** - Collaborative + Content + Sentiment  
✅ **Production-Ready** - REST API included  
✅ **Well-Documented** - Comments everywhere  
✅ **Beginner-Friendly** - Easy to understand and modify  

---

## 💪 You're All Set!

Your adaptive recommendation system is now running and ready to use!

For detailed help, see:
- `README.md` - Complete documentation
- `docs/TUTORIAL_FOR_BEGINNERS.md` - Learning guide
- `docs/TROUBLESHOOTING.md` - Common issues
- `PROJECT_CONTEXT.md` - Share with Claude for help

**Good luck with your project! 🚀**
