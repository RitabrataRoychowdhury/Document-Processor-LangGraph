# Updated run.sh Script - Complete One-Hit Runnable Solution

## Overview

The `scripts/run.sh` script has been completely rewritten to be a comprehensive, one-hit runnable script that performs all necessary cleanup, setup, and launches the QME system according to your current codebase configuration.

## Key Features

### ✅ Pre-Startup Cleanup (Automatic)
The script automatically performs all the cleanup steps you requested:

```bash
# Removes __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} +

# Removes pytest cache
find . -type d -name ".pytest_cache" -exec rm -rf {} +

# Removes mypy and coverage cache
rm -rf .mypy_cache .coverage coverage.xml htmlcov

# Removes old virtual environments
rm -rf venv .venv

# Removes Python compiled files
find . -name "*.py[co]" -delete
```

### ✅ Complete Environment Setup
- Creates fresh virtual environment (`venv_clean`)
- Installs all dependencies from `requirements.txt`
- Installs additional QME-specific dependencies
- Sets up all required directories
- Configures environment variables

### ✅ System Validation
- Tests all critical imports
- Validates configuration
- Performs comprehensive health checks
- Ensures system readiness

### ✅ Streamlined Startup Options
1. **🌐 Start Streamlit Web Interface (Default)** - Main QME interface
2. **🚀 Start FastAPI Server** - API-only mode for testing
3. **🔄 Start Both Services** - Full system with both interfaces
4. **🧪 Run System Tests** - Comprehensive testing suite
5. **🔍 Run Health Check Only** - System diagnostics

## Usage

### Simple One-Command Startup
```bash
./scripts/run.sh
```

This single command will:
1. ✅ Perform complete cleanup
2. ✅ Create fresh virtual environment
3. ✅ Install all dependencies
4. ✅ Validate system health
5. ✅ Present startup menu
6. ✅ Launch your chosen service

### Default Behavior
- If you just press Enter, it starts the Streamlit web interface
- No complex menus or confusing options
- Clear progress indicators throughout

## What's Different from the Old Script

### ❌ Removed Issues
- **No dependency reinstallation conflicts** - Uses fresh environment
- **No hanging initialization** - Streamlined health checks
- **No complex knowledge base setup** - Optional, not required for startup
- **No confusing menu options** - Simple 5-option menu

### ✅ New Benefits
- **Complete cleanup** - Ensures no cache conflicts
- **Fresh environment** - Eliminates dependency issues
- **Fast startup** - Optimized for quick launch
- **Better error handling** - Clear error messages and troubleshooting
- **Comprehensive logging** - All actions logged to `logs/startup.log`

## Directory Structure Created

The script automatically creates all required directories:

```
data/
├── database/
├── documents/
├── cache/
├── canonical/
├── ama_guidelines/
├── qme_references/
├── sample_documents/
└── exports/

results/
├── generated_documents/
├── templates_archive/
├── validation_reports/
├── performance_reports/
├── quality_reports/
├── audit_trails/
├── extraction_results/
├── metadata/
├── processing_logs/
├── template_results/
└── validation_results/

logs/
```

## Environment Configuration

If `.env` doesn't exist, the script creates a comprehensive template:

```bash
# QME System Environment Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=meta-llama/llama-3.2-90b-vision-instruct:free
GEMINI_API_KEY=your_gemini_api_key_here
DEBUG=false
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=50
STREAMLIT_PORT=8501
API_PORT=8000
DATABASE_URL=sqlite:///data/database/documents.db
ENABLE_CACHING=true
CACHE_TTL_SECONDS=3600
MAX_CONCURRENT_REQUESTS=10
```

## Startup Process

### Step-by-Step Execution
1. **Pre-startup cleanup** - Removes all cache and old environments
2. **Python version validation** - Ensures Python 3.8+
3. **Virtual environment setup** - Creates fresh `venv_clean`
4. **Dependency installation** - Installs all required packages
5. **Environment configuration** - Sets up `.env` and directories
6. **System validation** - Tests imports and configuration
7. **System health check** - Comprehensive system validation
8. **Startup menu** - Simple 5-option selection

### Progress Indicators
- Clear step numbering (1/8, 2/8, etc.)
- Color-coded output (success, warning, error)
- Detailed logging to `logs/startup.log`
- Real-time status updates

## Error Handling

### Comprehensive Error Recovery
- **Python not found** - Clear installation instructions
- **Import errors** - Detailed troubleshooting steps
- **Configuration issues** - Specific remediation guidance
- **Dependency conflicts** - Fresh environment resolution

### Graceful Degradation
- Continues with warnings when possible
- Provides alternative startup methods
- Clear error messages with next steps
- Automatic cleanup on failure

## Integration with Current Codebase

### Aligned with Your Architecture
- Uses `venv_clean` virtual environment (matches your setup)
- Imports from correct module paths (`src.ui.main_app`, etc.)
- Supports both Streamlit and FastAPI modes
- Compatible with your current file structure

### Supports All Current Features
- ✅ OpenRouter extraction service
- ✅ Gemini fallback service
- ✅ Multi-layer extraction system
- ✅ QME template generation
- ✅ Professional template assembly
- ✅ Comprehensive validation

## Recommended Usage

### Daily Development
```bash
cd /Users/ritabrataroychowdhury/Downloads/Dms
./scripts/run.sh
# Press Enter for default Streamlit interface
```

### API Testing
```bash
./scripts/run.sh
# Choose option 2 for FastAPI server
# Access http://localhost:8000/docs
```

### Full System Testing
```bash
./scripts/run.sh
# Choose option 4 for comprehensive tests
```

### System Diagnostics
```bash
./scripts/run.sh
# Choose option 5 for health check only
```

## Success Indicators

You'll know everything is working when:
- ✅ All 8 setup steps complete without errors
- ✅ System validation shows "All critical imports successful"
- ✅ Health check shows "System: OPERATIONAL"
- ✅ Startup menu appears with 5 clear options
- ✅ Your chosen service starts successfully

## Troubleshooting

If issues occur:
1. **Check the logs** - `logs/startup.log` has detailed information
2. **Run health check** - Choose option 5 to diagnose issues
3. **Fresh start** - The script always starts with complete cleanup
4. **Manual cleanup** - Script handles all cleanup automatically

## Conclusion

This updated `run.sh` script provides a complete, one-hit solution that:
- ✅ Performs all requested pre-startup cleanup
- ✅ Sets up a fresh, clean environment
- ✅ Validates system health comprehensively
- ✅ Provides simple, clear startup options
- ✅ Integrates perfectly with your current codebase
- ✅ Handles errors gracefully with clear guidance

**Just run `./scripts/run.sh` and you're ready to go!** 🚀