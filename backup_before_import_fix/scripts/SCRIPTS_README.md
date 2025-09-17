# Document Q&A System - Scripts Guide

## 🚀 Available Scripts

This project includes several shell scripts to make development and deployment easier:

### 1. `./scripts/run.sh` - Complete Setup & Run Script

**Purpose**: Full setup script that handles everything from virtual environment creation to running the application.

**What it does**:
- ✅ Checks Python installation
- ✅ Creates virtual environment (if needed)
- ✅ Activates virtual environment
- ✅ Installs/upgrades dependencies
- ✅ Creates necessary directories
- ✅ Copies .env.example to .env (if needed)
- ✅ Runs system health check
- ✅ Provides menu to choose what to run

**Usage**:
```bash
./scripts/run.sh
```

**Menu Options**:
1. **Start web interface** (default) - Launches Streamlit at http://localhost:8501
2. **Run system check only** - Validates system health
3. **Initialize system only** - Sets up without starting web interface
4. **Run tests** - Executes the test suite

---

### 2. `./scripts/start.sh` - Quick Start Script

**Purpose**: Simple script for quick startup when environment is already set up.

**What it does**:
- ✅ Activates existing virtual environment
- ✅ Quick configuration check
- ✅ Starts web interface immediately

**Usage**:
```bash
./scripts/start.sh
```

**Requirements**: Virtual environment must already exist (run `./scripts/run.sh` first)

---

### 3. `./scripts/cleanup.sh` - Complete Cleanup Script

**Purpose**: Comprehensive cleanup that removes all runtime data and optionally the virtual environment.

**What it cleans**:
- 🗑️ **Database files**: `data/database/documents.db` and related files
- 🗑️ **Document storage**: `data/documents/` directory
- 🗑️ **Log files**: `logs/` directory
- 🗑️ **Python cache**: `__pycache__/`, `*.pyc`, `*.pyo` files
- 🗑️ **Test files**: Temporary test scripts
- 🗑️ **Streamlit cache**: `.streamlit/` directory
- 🗑️ **Temporary files**: `.pytest_cache`, `.coverage`, etc.
- 🔌 **Deactivates virtual environment**
- 🗑️ **Optionally removes virtual environment** (asks for confirmation)

**Usage**:
```bash
./scripts/cleanup.sh
```

**Interactive**: Will ask if you want to remove the virtual environment entirely.

---

### 4. `./scripts/docker-build.sh` - Docker Build Script

**Purpose**: Builds the Docker image for containerized deployment.

**What it does**:
- ✅ Checks Docker installation
- ✅ Validates configuration files
- ✅ Builds optimized Docker image
- ✅ Shows image information

**Usage**:
```bash
./scripts/docker-build.sh
```

---

### 5. `./scripts/docker-run.sh` - Docker Run Script

**Purpose**: Runs the application in a Docker container.

**What it does**:
- ✅ Manages container lifecycle
- ✅ Mounts data volumes
- ✅ Loads environment variables
- ✅ Follows container logs

**Usage**:
```bash
./scripts/docker-run.sh
```

---

### 6. `./scripts/docker-compose-up.sh` - Docker Compose Script

**Purpose**: Uses Docker Compose for service orchestration.

**What it does**:
- ✅ Interactive service management
- ✅ Build and deployment options
- ✅ Log viewing and monitoring
- ✅ Service status checking

**Usage**:
```bash
./scripts/docker-compose-up.sh
```

**Menu Options**:
1. **Start services** (build if needed)
2. **Start services** (force rebuild)
3. **Stop services**
4. **View logs**
5. **Show status**

---

## 📋 Common Usage Patterns

### First Time Setup

**Docker (Recommended):**
```bash
# 1. Clone/download the project
# 2. Make scripts executable (if needed)
chmod +x scripts/*.sh

# 3. Run with Docker Compose
./scripts/docker-compose-up.sh
```

**Local Development:**
```bash
# 1. Clone/download the project
# 2. Make scripts executable (if needed)
chmod +x scripts/*.sh

# 3. Run complete setup
./scripts/run.sh
```

### Daily Development
```bash
# Quick start (if already set up)
./scripts/start.sh

# Or use full script for menu options
./scripts/run.sh
```

### Testing & Development
```bash
# Run tests
./scripts/run.sh  # Choose option 4

# System health check
./scripts/run.sh  # Choose option 2
```

### Cleanup & Reset
```bash
# Clean everything but keep venv
./scripts/cleanup.sh  # Answer 'n' when asked about venv

# Complete reset (remove everything)
./scripts/cleanup.sh  # Answer 'y' when asked about venv
```

---

## 🔧 Script Features

### Error Handling
- ✅ Checks for Python installation
- ✅ Validates virtual environment creation
- ✅ Handles missing dependencies gracefully
- ✅ Provides clear error messages

### User Experience
- 🎨 **Colored output** for better readability
- 📋 **Progress indicators** for long operations
- ❓ **Interactive menus** for user choice
- 💡 **Helpful hints** and next steps

### Safety Features
- 🛡️ **Safe file removal** (checks existence first)
- 🔍 **Process termination** before cleanup
- ❓ **Confirmation prompts** for destructive operations
- 📝 **Detailed logging** of cleanup operations

---

## 🐛 Troubleshooting

### "Permission denied" Error
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

### "Python not found" Error
```bash
# Install Python 3.8+
# macOS: brew install python3
# Ubuntu: sudo apt install python3 python3-venv
```

### "Virtual environment activation failed"
```bash
# Remove and recreate venv
./scripts/cleanup.sh  # Remove venv when asked
./scripts/run.sh      # Will create new venv
```

### "Requirements installation failed"
```bash
# Update pip and try again
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### "API key not configured"
```bash
# Edit .env file with your Gemini API key
nano .env
# or
code .env
```

---

## 📁 What Gets Created/Cleaned

### Created by Scripts:
```
project/
├── venv/                 # Virtual environment
├── .env                  # Configuration (from .env.example)
├── data/
│   ├── database/         # SQLite database files
│   └── documents/        # Uploaded document storage
├── logs/                 # Application logs
└── .streamlit/           # Streamlit cache
```

### Cleaned by cleanup.sh:
- All files/directories listed above
- Python cache files (`__pycache__/`, `*.pyc`)
- Test artifacts (`.pytest_cache`, `.coverage`)
- Temporary test files

---

## 🎯 Quick Reference

| Task | Command | Description |
|------|---------|-------------|
| **Docker setup** | `./scripts/docker-compose-up.sh` | Docker Compose deployment |
| **Docker build** | `./scripts/docker-build.sh` | Build Docker image |
| **Docker run** | `./scripts/docker-run.sh` | Run Docker container |
| **First setup** | `./scripts/run.sh` | Complete setup and run |
| **Quick start** | `./scripts/start.sh` | Fast startup (if already set up) |
| **Run tests** | `./scripts/run.sh` → 4 | Execute test suite |
| **Health check** | `./scripts/run.sh` → 2 | Validate system |
| **Clean data** | `./scripts/cleanup.sh` → n | Clean data, keep venv |
| **Full reset** | `./scripts/cleanup.sh` → y | Remove everything |

---

## 💡 Pro Tips

1. **Development Workflow**:
   ```bash
   ./scripts/run.sh          # Initial setup
   # ... develop ...
   ./scripts/start.sh         # Quick restarts
   ./scripts/cleanup.sh       # Clean when needed
   ```

2. **Testing Workflow**:
   ```bash
   ./scripts/run.sh → 4       # Run tests
   ./scripts/cleanup.sh → n   # Clean data between tests
   ```

3. **Deployment Preparation**:
   ```bash
   ./scripts/cleanup.sh → y   # Complete clean
   ./scripts/run.sh → 2       # Health check
   ```

4. **Debugging Issues**:
   ```bash
   ./scripts/run.sh → 2       # System check
   ./scripts/cleanup.sh → n   # Clean data
   ./scripts/run.sh → 1       # Fresh start
   ```

---

🎉 **Happy coding with the Document Q&A System!** 🚀