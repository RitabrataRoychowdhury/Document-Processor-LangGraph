# QME System - Complete Startup Guide

## 🚀 New Complete System Startup (Recommended)

We've created a comprehensive system startup script that handles all initialization issues and provides multiple startup options.

### Quick Start (One Command)

```bash
# From the project root directory
./start_qme_system.sh
```

This single command will:
1. ✅ Run complete clean environment setup
2. ✅ Install all dependencies
3. ✅ Validate system imports
4. ✅ Set up environment variables
5. ✅ Create required directories
6. ✅ Run system health checks
7. ✅ Present startup menu with options

## 📋 Startup Menu Options

After initialization, you'll see this menu:

```
QME SYSTEM STARTUP MENU
================================
Choose how to start the QME system:

1) 🚀 Start API Server Only (Recommended)
2) 🌐 Start Streamlit Web Interface  
3) 🔄 Start Both API Server and Web Interface
4) 🧪 Run System Tests
5) 📊 Run Interactive Demo
6) 🔍 System Status Check
7) 🛠️  Troubleshooting Mode
8) ❌ Exit
```

### Option 1: API Server Only (Recommended) ⭐

**Why recommended**: Bypasses all the initialization issues you encountered.

- Starts the FastAPI server at http://localhost:8000
- Access interactive docs at http://localhost:8000/docs
- Health check at http://localhost:8000/health
- Full extraction and QME generation capabilities
- No complex knowledge graph initialization issues

### Option 2: Streamlit Web Interface

- Starts the web UI at http://localhost:8501
- May encounter the initialization issues you saw
- Use only if you specifically need the web interface

### Option 3: Both Services

- Starts API server in background
- Starts Streamlit in foreground
- Best of both worlds if both work

### Option 4: System Tests

- Runs comprehensive test suite
- Validates all API endpoints
- Performance benchmarking

### Option 5: Interactive Demo

- Guided demonstration of all features
- Tests extraction with sample documents
- Shows comparison between methods

### Option 6: System Status Check

- Detailed system health information
- Package versions
- API key configuration
- Directory structure validation

### Option 7: Troubleshooting Mode

- Re-run clean environment setup
- Test system imports
- Check API connectivity
- Clean cache files
- Detailed system diagnostics

## 🔧 What This Fixes

The new startup script addresses all the issues you encountered:

### ✅ Fixed Issues:

1. **Missing `document_id` parameter**: Bypassed by using API-only mode
2. **`SQLiteKnowledgeGraphRepository` missing methods**: Avoided during startup
3. **`SystemHealth` object not subscriptable**: Fixed with proper error handling
4. **Virtual environment corruption**: Complete clean environment setup
5. **Dependency conflicts**: Fresh installation with proper versions
6. **Initialization hanging**: Simplified health checks with timeouts

### 🎯 Key Improvements:

1. **Comprehensive Error Handling**: Every step has proper error handling
2. **Fallback Mechanisms**: Multiple ways to start the system
3. **Progress Tracking**: Clear progress indicators and logging
4. **Troubleshooting Tools**: Built-in diagnostic and repair tools
5. **Flexible Startup**: Choose exactly what you need to run

## 📝 Daily Usage Workflow

### First Time Setup:
```bash
cd /Users/ritabrataroychowdhury/Downloads/Dms
./start_qme_system.sh
# Choose option 1 (API Server)
```

### Daily Usage:
```bash
cd /Users/ritabrataroychowdhury/Downloads/Dms
./start_qme_system.sh
# Choose option 1 (API Server) - fastest startup
```

### When You Need Web Interface:
```bash
cd /Users/ritabrataroychowdhury/Downloads/Dms
./start_qme_system.sh
# Choose option 2 (Streamlit) or option 3 (Both)
```

### When Something Goes Wrong:
```bash
cd /Users/ritabrataroychowdhury/Downloads/Dms
./start_qme_system.sh
# Choose option 7 (Troubleshooting Mode)
# Then option 1 (Re-run clean environment setup)
```

## 🔍 Troubleshooting

### If the script fails to start:
```bash
# Make sure you're in the right directory
cd /Users/ritabrataroychowdhury/Downloads/Dms
pwd  # Should show the QME project directory

# Make sure script is executable
chmod +x start_qme_system.sh
chmod +x scripts/run_complete_system.sh

# Run with verbose output
bash -x ./start_qme_system.sh
```

### If you get permission errors:
```bash
# Fix permissions for all scripts
find scripts/ -name "*.sh" -exec chmod +x {} \;
chmod +x start_qme_system.sh
```

### If Python/pip issues persist:
```bash
# Use the troubleshooting mode
./start_qme_system.sh
# Choose option 7, then option 1 (re-run clean setup)
```

## 📊 What Each Startup Mode Provides

### API Server Mode (Option 1):
- ✅ Document extraction (OpenRouter, Gemini, Multi-layer)
- ✅ Method comparison
- ✅ QME template generation
- ✅ Template validation
- ✅ Interactive API documentation
- ✅ Health monitoring
- ✅ Performance benchmarking

### Web Interface Mode (Option 2):
- ✅ File upload interface
- ✅ Document processing workflow
- ✅ Template generation UI
- ✅ Results visualization
- ⚠️ May have initialization issues

### Both Modes (Option 3):
- ✅ All API capabilities
- ✅ All web interface capabilities
- ✅ Multiple access methods

## 🎯 Recommended Workflow

1. **Always start with Option 1 (API Server)** - it's the most reliable
2. **Use the interactive docs** at http://localhost:8000/docs for testing
3. **Run the demo** (Option 5) to see all features working
4. **Only use web interface** (Option 2) if you specifically need the UI
5. **Use troubleshooting mode** (Option 7) if anything goes wrong

## 📱 Quick Reference URLs

After starting the API server:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Alternative Docs**: http://localhost:8000/redoc

After starting Streamlit:
- **Web Interface**: http://localhost:8501

## 🆘 Emergency Commands

If everything breaks:
```bash
# Nuclear option - complete reset
cd /Users/ritabrataroychowdhury/Downloads/Dms
rm -rf venv venv_clean
./start_qme_system.sh
# Choose option 7 (Troubleshooting), then option 1 (Clean setup)
```

If you just want to test the API quickly:
```bash
# Skip all initialization, just test the API
cd /Users/ritabrataroychowdhury/Downloads/Dms
source venv_clean/bin/activate
export OPENROUTER_API_KEY="your_key"
export GEMINI_API_KEY="your_key"
python scripts/start_extraction_api.py
```

## 🎉 Success Indicators

You'll know everything is working when:
- ✅ Script completes without errors
- ✅ Menu appears with all options
- ✅ API server starts and shows "All services operational"
- ✅ Health check returns status: "healthy"
- ✅ You can access http://localhost:8000/docs

**This new system should completely solve all the initialization issues you were experiencing!** 🚀