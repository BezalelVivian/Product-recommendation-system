# 🔧 TROUBLESHOOTING GUIDE

Complete solutions for common issues.

---

## 🚫 Installation Issues

### Error: "ModuleNotFoundError: No module named 'X'"

**Solution 1: Install missing package**
```bash
pip install [package-name]
```

**Solution 2: Reinstall all dependencies**
```bash
pip install -r requirements.txt
```

**Solution 3: Upgrade pip first**
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

### Error: "Could not find a version that satisfies the requirement"

**Cause:** Package not available for your Python version

**Solution:**
```bash
# Check Python version
python --version

# If < 3.8, upgrade Python
# Download from: https://www.python.org/downloads/

# If using Anaconda:
conda create -n recsys python=3.10
conda activate recsys
pip install -r requirements.txt
```

---

### Error: "Microsoft Visual C++ 14.0 or greater is required" (Windows)

**Solution:**
1. Download Visual C++ Build Tools
2. Install from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
3. Retry: `pip install -r requirements.txt`

---

## 💾 Memory Issues

### Error: "MemoryError" or "Killed" during training

**Solution 1: Reduce batch size**
```yaml
# Edit: config/model_config.yaml
training:
  batch_size: 8  # Reduce from 32
```

**Solution 2: Reduce model complexity**
```yaml
# Edit: config/model_config.yaml
collaborative_filtering:
  svd:
    n_factors: 20  # Reduce from 50
    n_epochs: 10   # Reduce from 20
```

**Solution 3: Use lighter profile**
```yaml
# Edit: config/model_config.yaml
active_profile: "low_resource"  # Change from "balanced"
```

**Solution 4: Close other applications**
- Close browser tabs
- Close other programs
- Free up RAM

---

## 🔌 API Issues

### Error: "Address already in use" or "Port 8000 busy"

**Solution: Change port**
```yaml
# Edit: config/settings.yaml
api:
  port: 8001  # Change from 8000
```

Then start API:
```bash
python src/api/main.py
# Access at: http://localhost:8001/docs
```

---

### Error: "Cannot connect to API" or "Connection refused"

**Check if API is running:**
```bash
# Look for this message:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

**If not running:**
```bash
# Start it:
python src/api/main.py
```

**If still not working:**
```bash
# Try different host:
# Edit config/settings.yaml
api:
  host: "127.0.0.1"  # Instead of 0.0.0.0
```

---

## 📊 Data Issues

### Error: "KeyError: 'user_id'" or similar column errors

**Cause:** Dataset columns not detected correctly

**Solution 1: Let system auto-detect**
```python
# This should work automatically
python scripts/train_all_models.py
```

**Solution 2: Manual mapping**
```python
# Edit: src/data_adapters/schema_detector.py
# Add your column names around line 40:

'user': [
    'user', 'customer', 'buyer',
    'YOUR_USER_COLUMN_NAME',  # ← Add here
],
```

**Solution 3: Rename columns in CSV**
- Open your CSV in Excel/LibreOffice
- Rename columns to: user_id, item_id, rating, timestamp
- Save and retry

---

### Error: "Empty DataFrame" or "No data loaded"

**Check 1: File exists**
```bash
ls data/raw/
# Should show your CSV file
```

**Check 2: File format**
- Must be CSV format
- UTF-8 encoding
- Has header row

**Check 3: File not empty**
```python
import pandas as pd
df = pd.read_csv('data/raw/your_file.csv')
print(len(df))  # Should be > 0
```

---

## 🤖 Model Training Issues

### Error: "RuntimeError: CUDA out of memory"

**Solution: Disable GPU**
```yaml
# Edit: config/settings.yaml
training:
  use_gpu: false  # Force CPU mode
```

---

### Training is very slow (>1 hour)

**Solution 1: Reduce data size (for testing)**
```python
# Edit: scripts/train_all_models.py
# Around line 20, add:
df = df.sample(frac=0.1)  # Use 10% of data for testing
```

**Solution 2: Reduce epochs**
```yaml
# Edit: config/model_config.yaml
collaborative_filtering:
  svd:
    n_epochs: 5  # Reduce from 20
```

**Solution 3: Use faster algorithm**
```yaml
# Edit: config/model_config.yaml
collaborative_filtering:
  algorithm: "als"  # Faster than SVD
```

---

### Warning: "Convergence not reached"

**Not a problem!** This is just a warning.

**If you want to fix it:**
```yaml
# Edit: config/model_config.yaml
collaborative_filtering:
  svd:
    n_epochs: 30  # Increase from 20
    lr_all: 0.01  # Increase learning rate
```

---

## 🌐 Browser/Frontend Issues

### API docs page not loading

**Check 1: API is running**
```bash
# Should see:
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Check 2: Correct URL**
```
# Try these:
http://localhost:8000/docs
http://127.0.0.1:8000/docs
http://0.0.0.0:8000/docs
```

**Check 3: Clear browser cache**
- Press Ctrl+Shift+R (Windows)
- Press Cmd+Shift+R (Mac)

---

## 📁 File/Path Issues

### Error: "FileNotFoundError" or "No such file or directory"

**Solution: Check you're in correct directory**
```bash
pwd  # Should show: .../adaptive-recommendation-system

# If not:
cd adaptive-recommendation-system
```

**Create missing directories:**
```bash
python scripts/setup.py
```

---

## 🐍 Python Environment Issues

### Multiple Python versions installed

**Solution: Use virtual environment**
```bash
# Create virtual environment
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies:
pip install -r requirements.txt
```

---

### Packages installed but still "Module not found"

**Solution: Check which Python**
```bash
# Check Python location:
which python  # Mac/Linux
where python  # Windows

# Install packages for that specific Python:
/path/to/python -m pip install -r requirements.txt
```

---

## 📈 Performance Issues

### Recommendations are slow (>1 second)

**Solution 1: Enable caching**
```yaml
# Edit: config/settings.yaml
cache:
  enabled: true
  backend: "memory"
```

**Solution 2: Reduce num_items**
```yaml
# Edit: config/settings.yaml
recommendations:
  num_items: 5  # Reduce from 10
```

**Solution 3: Precompute embeddings**
```bash
# Run this once:
python scripts/precompute_embeddings.py
```

---

## 🔍 Debugging Steps

### General debugging workflow:

**Step 1: Enable debug logging**
```yaml
# Edit: config/settings.yaml
logging:
  level: "DEBUG"  # Change from "INFO"
```

**Step 2: Check logs**
```bash
# View log file:
cat logs/app.log

# Or tail it live:
tail -f logs/app.log
```

**Step 3: Run diagnostic**
```bash
python scripts/diagnose.py
cat logs/diagnostic_report.txt
```

**Step 4: Test individual components**
```bash
# Test data loading:
python src/data_adapters/schema_detector.py

# Test models:
python scripts/test_models.py
```

---

## 🆘 Still Stuck?

### 1. Check existing GitHub issues
Search similar problems in recommendation system repositories

### 2. Ask on Stack Overflow
- Tag: `python`, `machine-learning`, `recommendation-system`
- Include: Full error message, what you tried

### 3. Ask Claude in new chat
Share `PROJECT_CONTEXT.md` + your error:

```
"I'm working on the adaptive recommendation system.
Here's the context: [paste PROJECT_CONTEXT.md]

Error I'm getting:
[paste full error message]

What I tried:
[list what you've tried]

Help me fix this."
```

### 4. Community Forums
- r/learnpython (Reddit)
- r/MachineLearning (Reddit)
- Python Discord servers

---

## 📝 Error Code Reference

| Code | Meaning | Solution |
|------|---------|----------|
| E001 | Data loading failed | Check file path and format |
| E002 | Column mapping failed | Add column names to schema_detector.py |
| E003 | Model training failed | Reduce batch_size or n_factors |
| E004 | Memory error | Use low_resource profile |
| E005 | Port unavailable | Change API port in settings.yaml |
| E006 | GPU unavailable | Set use_gpu: false |

---

## ✅ Prevention Checklist

Before starting, verify:

- [ ] Python 3.8+ installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Ran setup script (`python scripts/setup.py`)
- [ ] Data files in correct location (`data/raw/`)
- [ ] Enough disk space (5GB+)
- [ ] Enough RAM (4GB+ free)

---

**Remember: Most errors have simple solutions. Don't give up! 💪**
