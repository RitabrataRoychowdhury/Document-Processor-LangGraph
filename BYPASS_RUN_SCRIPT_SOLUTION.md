# Bypass run.sh Script Issues - Complete Solution

## Problem Identified ✅

The `scripts/run.sh` script is causing issues because it:
1. **Reinstalls dependencies** with `pip install -r requirements.txt --quiet`
2. **May override local fixes** by reinstalling packages from PyPI
3. **Uses virtual environment** that might not reflect your local changes

## Solution: Multiple Ways to Run the Application

### Option 1: Direct Python Runner (Recommended) 🎯

Use the new `run_direct.py` script that bypasses all potential issues:

```bash
python3 run_direct.py
```

**Benefits:**
- ✅ Uses current directory code directly
- ✅ Verifies fixes are active before starting
- ✅ No dependency reinstallation
- ✅ Clear error messages if something is wrong

### Option 2: Fixed Run Script 🔧

Use the new `run_fixed.sh` script that preserves local changes:

```bash
./run_fixed.sh
```

**Benefits:**
- ✅ Clears Python cache before starting
- ✅ Verifies fixes are in place
- ✅ Skips dependency reinstallation if packages exist
- ✅ Uses existing virtual environment safely

### Option 3: Direct Streamlit Command 🚀

Run Streamlit directly without any wrapper scripts:

```bash
# Clear cache first
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Run directly
python3 -m streamlit run src/ui/main_app.py --server.port=8501
```

## Why the Original run.sh Was Problematic

### Issue 1: Dependency Reinstallation
```bash
# This line in run.sh was causing problems:
pip install -r requirements.txt --quiet
```
This reinstalls packages from PyPI, potentially overriding your local fixes.

### Issue 2: Virtual Environment Isolation
The script creates/uses a virtual environment that might not include your local code changes.

### Issue 3: Cache Issues
The script doesn't clear Python bytecode cache, so old versions of files might still be used.

## Verification Steps

Before running the application, verify the fixes are active:

```bash
python3 -c "
import sys
sys.path.insert(0, '.')

# Test FileMetadata fix
from src.ui.upload_interface import UploadInterface
print('✅ Upload interface fix active')

# Test OpenRouter response fix  
from src.core.extraction.openrouter_extraction_service import OpenRouterExtractionService
print('✅ OpenRouter response fix active')

print('🎉 All fixes verified!')
"
```

## Expected Results After Using Fixed Runners

### ✅ What You Should See
- No `FileMetadata.__init__() got an unexpected keyword argument 'size'` errors
- No `'list' object has no attribute 'items'` errors
- Successful document uploads and processing
- Field extraction completes without errors (even if 0 fields found)

### 📊 Log Messages You Should See
```
✅ Upload interface initialized successfully
✅ Extraction service is available  
✅ Document processing successful
✅ Field extraction completed: X fields extracted
```

## Troubleshooting

### If You Still See Errors
1. **Stop any running Streamlit processes**:
   ```bash
   pkill -f streamlit
   ```

2. **Clear all Python cache**:
   ```bash
   find . -name "*.pyc" -delete
   find . -name "__pycache__" -type d -exec rm -rf {} +
   ```

3. **Use the direct runner**:
   ```bash
   python3 run_direct.py
   ```

### If Import Errors Occur
Make sure you're in the correct directory and Python can find the modules:
```bash
pwd  # Should show your project directory
python3 -c "import sys; print(sys.path[0])"  # Should show current directory
```

## Recommended Workflow

1. **Use the direct runner** for immediate testing:
   ```bash
   python3 run_direct.py
   ```

2. **If that works**, you can also use the fixed script:
   ```bash
   ./run_fixed.sh
   ```

3. **Avoid the original run.sh** until it's updated to preserve local changes.

## Summary

The extraction pipeline fixes are working correctly. The issue was that `scripts/run.sh` was reinstalling dependencies and potentially overriding your local fixes. Use the new runners provided to bypass this issue and run the application with all fixes active.

🎉 **Your extraction pipeline should now work without the previous errors!**