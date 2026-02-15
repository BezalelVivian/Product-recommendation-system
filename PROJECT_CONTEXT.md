# Project Context (Share this with Claude in new chats)

## 📋 Project Overview

**Project Name:** Adaptive E-commerce Recommendation System  
**Purpose:** Academic project for data-driven product recommendations (like Amazon/Flipkart)  
**Unique Feature:** Novel cold start solution with behavioral DNA extraction

---

## 🎯 Key Requirements

### **1. Cold Start Innovation (80% Focus)**
- **Problem Solved:** New users with no history
- **Solution:** Passive behavioral tracking (0-60 seconds) + Adaptive strategy
- **What's Novel:**
  - No questionnaires or friction
  - Learns from mouse patterns, scroll behavior, clicks, hovers
  - Transfer learning from existing users
  - Multi-agent system that auto-selects best strategy
  - Works in 60 seconds vs competitors' 5-10 minutes

### **2. Regular Recommendations (20% Focus - Simple but Good)**
- Collaborative Filtering (SVD)
- Content-Based (TF-IDF + Image similarity)
- Sentiment Analysis (from reviews)
- Hybrid weighted ensemble
- Context-aware (time, price, trends)

### **3. Universal Dataset Adapter**
- Must work with ANY e-commerce CSV
- Auto-detect columns (user_id, customer_code, buyer → all recognized as USER)
- Handle different column names automatically
- Create missing features synthetically

---

## 💻 Technical Constraints

**Hardware:**
- RTX 2050 laptop (8GB RAM typical)
- Must run on CPU (GPU optional)
- Lightweight models preferred
- Training time: 10-30 minutes acceptable

**Experience Level:**
- Beginner programmer
- Needs easy-to-modify code
- Wants clean comments everywhere
- Config files > code changes

**Tools:**
- Python 3.8+
- FREE tools only (no paid APIs/services)
- PyTorch, Scikit-learn, FastAPI
- SQLite (no heavy databases)

---

## 🏗️ Architecture Decisions

### **Cold Start (Advanced):**
```python
1. Behavioral Tracking (JavaScript frontend)
   - Mouse movements, scroll patterns
   - Click timing, hover duration
   - Category exploration patterns
   - Price range detection

2. Real-time Clustering (Lightweight ML)
   - Find similar users in <500ms
   - Use pre-computed user embeddings
   - Transfer knowledge from cluster

3. Adaptive Strategy (Multi-agent)
   - Agent 1: Behavioral pattern matcher
   - Agent 2: Visual preference learner
   - Agent 3: Contextual bandit explorer
   - Meta-controller selects best agent
```

### **Regular Recommendations (Simple):**
```python
1. Collaborative Filtering
   - SVD (Singular Value Decomposition)
   - Fast, CPU-friendly, accurate

2. Content-Based
   - TF-IDF for text similarity
   - MobileNet for image features

3. Sentiment Boost
   - VADER or DistilBERT
   - Filter low-quality products
   - Boost high-sentiment items

4. Ensemble
   - Weighted combination
   - weights: {collaborative: 0.4, content: 0.3, sentiment: 0.2, popular: 0.1}
```

---

## 📂 Important File Locations

```
config/
├── settings.yaml          ← Main settings (edit this!)
├── model_config.yaml      ← Algorithm parameters

src/
├── data_adapters/         ← Universal CSV handler (KEY FEATURE)
├── models/cold_start/     ← Cold start innovation (FOCUS HERE)
├── models/collaborative/  ← SVD, ALS models
├── api/main.py           ← FastAPI server

scripts/
├── setup.py              ← Run first
├── train_all_models.py   ← Main training script
├── diagnose.py           ← Troubleshooting tool

docs/
├── TROUBLESHOOTING.md    ← Common errors & fixes
├── HOW_TO_MODIFY.md      ← Making changes guide
```

---

## 🎓 Project Goals

### **For Academic Evaluation:**
1. ✅ Novel cold start approach (research contribution)
2. ✅ Production-ready system (engineering quality)
3. ✅ Universal dataset adapter (practical innovation)
4. ✅ Multiple ML techniques (technical depth)
5. ✅ Well-documented (communication skills)

### **Success Metrics:**
- Cold start: 70%+ accuracy in first session
- Regular: 75-85% precision@10
- System: <100ms response time
- Training: <30 minutes on laptop

---

## 🐛 Common Issues You Might Face

### **Issue 1: "ModuleNotFoundError"**
```bash
# Solution:
pip install -r requirements.txt
# Or individual package:
pip install [package-name]
```

### **Issue 2: "Memory Error during training"**
```yaml
# Edit config/model_config.yaml:
batch_size: 16  # Reduce from 32
n_factors: 20   # Reduce from 50
```

### **Issue 3: "Dataset not recognized"**
```python
# Check: src/data_adapters/column_mapper.py
# Add your column names to the mapping dict
```

### **Issue 4: "Port already in use"**
```yaml
# Edit config/settings.yaml:
api:
  port: 8001  # Change from 8000
```

---

## 🔧 How to Modify

### **Change Algorithm:**
```python
# File: src/models/collaborative/simple_svd.py
# Line 30-40: Hyperparameters
n_factors = 50      # ← Change this
learning_rate = 0.01  # ← Or this
```

### **Change Weights:**
```yaml
# File: config/model_config.yaml
weights:
  collaborative: 0.5  # ← Adjust these
  content_based: 0.3
  sentiment: 0.2
```

### **Enable/Disable Features:**
```yaml
# File: config/settings.yaml
features:
  sentiment_analysis: true   # ← Toggle
  diversity_filter: true
  cold_start_tracking: true
```

---

## 💡 When Asking Claude for Help

### **Provide This Info:**
1. This PROJECT_CONTEXT.md file (paste it)
2. The specific error message (full text)
3. What you were trying to do
4. What you've already tried

### **Example:**
```
"I'm working on the adaptive recommendation system.
Here's the context: [paste PROJECT_CONTEXT.md]

Error I'm getting:
[paste full error]

I was trying to: train the models
I already tried: reinstalling packages

Help me fix this."
```

---

## 🎯 Design Principles

1. **Beginner-Friendly First**
   - Clear variable names
   - Comments on every function
   - No "clever" code

2. **Config Over Code**
   - Settings in YAML files
   - Easy to change without coding
   - Sensible defaults

3. **Modular Architecture**
   - Each component independent
   - Easy to swap algorithms
   - Plug-and-play design

4. **Fail Gracefully**
   - Fallback strategies everywhere
   - Never crash, always degrade
   - Clear error messages

5. **Documentation Everywhere**
   - README for each module
   - Inline comments
   - Tutorial notebooks

---

## 📊 Dataset Format Expected

**Any of these work (auto-detected):**

### Format 1: Amazon-style
```csv
user_id,product_id,rating,timestamp,review_text
U001,P001,5,2024-01-15,"Great product!"
```

### Format 2: Flipkart-style
```csv
customer_code,item_sku,stars,purchase_date,comment
C123,SKU456,4,2024-01-20,"Good value"
```

### Format 3: Custom
```csv
buyer_email,article_no,score,date,feedback
user@example.com,ART789,4.5,2024-01-25,"Nice"
```

**System auto-maps:**
- user_id / customer_code / buyer_email → USER
- product_id / item_sku / article_no → ITEM
- rating / stars / score → RATING
- review_text / comment / feedback → TEXT

---

## 🚀 Quick Commands Reference

```bash
# First time setup
pip install -r requirements.txt
python scripts/setup.py

# Train models
python scripts/train_all_models.py

# Start API
python src/api/main.py

# Test system
python scripts/test_recommendations.py

# Diagnose issues
python scripts/diagnose.py

# Run with your data
cp your_data.csv data/raw/
python scripts/train_all_models.py
```

---

## 🎬 Expected Workflow

### **Week 1: Setup & Understand**
```bash
Day 1: Install & run with sample data
Day 2: Explore notebooks
Day 3: Read code & comments
Day 4: Try with your own data
Day 5: Understand results
```

### **Week 2-3: Customize**
```bash
Day 8: Modify config files
Day 10: Change algorithm weights
Day 12: Add new features
Day 15: Test improvements
```

### **Week 4: Polish**
```bash
Day 22: Optimize performance
Day 24: Create presentation
Day 26: Practice demo
Day 28: Final testing
```

---

## 📝 Important Notes

1. **No Login Required for Recommendations**
   - Anonymous browsing supported
   - Session-based tracking
   - Optional user accounts

2. **Privacy & Legal**
   - Cookie consent banner included
   - Privacy policy template provided
   - GDPR-compliant (with proper setup)

3. **Tracking is Standard**
   - Amazon, Flipkart do same thing
   - Browser APIs (legal to use)
   - Users can block if they want

4. **Training Schedule**
   - Initial: One time (30 min)
   - Updates: Weekly/Monthly (10 min)
   - Daily: Just load models (2 sec)

---

## ✅ Project Status Checklist

- [x] Project structure created
- [x] Universal dataset adapter
- [x] Cold start innovation
- [x] Regular recommendation models
- [x] REST API
- [x] Documentation
- [x] Sample data
- [x] Testing framework
- [x] Beginner-friendly code
- [x] Config-driven design

---

**Use this file whenever you need help from Claude in a new chat!**
**Just paste it and explain your issue.**
