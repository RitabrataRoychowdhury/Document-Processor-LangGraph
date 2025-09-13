#!/bin/bash

# Document Q&A System - Enhanced Cleanup Script
# This script cleans up all runtime data, databases, logs, performance metrics, and deactivates the virtual environment

# Don't exit on errors for cleanup operations

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to safely remove files/directories
safe_remove() {
    if [ -e "$1" ]; then
        print_status "Removing: $1"
        rm -rf "$1"
        return 0
    else
        print_status "Not found: $1 (already clean)"
        return 1
    fi
}

# Function to get file/directory size
get_size() {
    if [ -e "$1" ]; then
        if command -v du >/dev/null 2>&1; then
            du -sh "$1" 2>/dev/null | cut -f1
        else
            echo "unknown"
        fi
    else
        echo "0"
    fi
}

echo "🧹 Document Q&A System - Enhanced Cleanup Script"
echo "================================================"

# Change to project root
cd "$PROJECT_ROOT"

# Show current system status before cleanup
print_status "Checking current system status..."
if [ -f "data/database/documents.db" ]; then
    DB_SIZE=$(get_size "data/database/documents.db")
    print_status "Database size: $DB_SIZE"
fi

if [ -d "logs" ]; then
    LOG_SIZE=$(get_size "logs")
    print_status "Logs size: $LOG_SIZE"
fi

if [ -d "data/documents" ]; then
    DOC_COUNT=$(find data/documents -type f 2>/dev/null | wc -l | tr -d ' ')
    print_status "Documents stored: $DOC_COUNT files"
fi

# Stop any running processes
echo ""
print_status "Stopping any running processes..."
pkill -f "streamlit run" 2>/dev/null && print_success "Stopped Streamlit processes" || true
pkill -f "python.*main_app.py" 2>/dev/null && print_success "Stopped main app processes" || true
pkill -f "python.*startup.py" 2>/dev/null && print_success "Stopped startup processes" || true
sleep 2

# Clean up database files
echo ""
print_status "Cleaning up database files..."
REMOVED_DB=0
safe_remove "data/database/documents.db" && REMOVED_DB=1
safe_remove "data/database/documents.db-journal"
safe_remove "data/database/documents.db-wal"
safe_remove "data/database/documents.db-shm"

if [ $REMOVED_DB -eq 1 ]; then
    print_warning "All processed documents and Q&A history have been removed"
fi

# Clean up document storage
echo ""
print_status "Cleaning up document storage..."
if [ -d "data/documents" ]; then
    DOC_COUNT=$(find data/documents -type f 2>/dev/null | wc -l | tr -d ' ')
    if [ "$DOC_COUNT" -gt 0 ]; then
        print_warning "Removing $DOC_COUNT uploaded documents"
    fi
fi
safe_remove "data/documents"

# Clean up performance metrics and logs
echo ""
print_status "Cleaning up performance metrics and logs..."
safe_remove "logs"

# Look for exported performance metrics
find . -name "performance_metrics_*.json" -type f 2>/dev/null | while read -r file; do
    safe_remove "$file"
done

# Clean up entire data directory if empty
if [ -d "data" ]; then
    if [ -z "$(find data -type f 2>/dev/null)" ]; then
        print_status "Removing empty data directory structure"
        rmdir data/database 2>/dev/null || true
        rmdir data 2>/dev/null || true
    else
        print_status "Data directory contains files, keeping structure"
    fi
fi

# Clean up Python cache files
echo ""
print_status "Cleaning up Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
print_success "Python cache cleared"

# Clean up test files and artifacts
echo ""
print_status "Cleaning up test files and artifacts..."
safe_remove ".pytest_cache"
safe_remove ".coverage"
safe_remove "htmlcov"
safe_remove "coverage.xml"
safe_remove "test-results.xml"

# Remove any temporary test files
find . -name "test_*.tmp" -type f -delete 2>/dev/null || true
find . -name "*.temp" -type f -delete 2>/dev/null || true

# Clean up Streamlit cache and config
echo ""
print_status "Cleaning up Streamlit cache and configuration..."
safe_remove ".streamlit"
safe_remove "$HOME/.streamlit" 2>/dev/null || true

# Clean up any backup files
echo ""
print_status "Cleaning up backup and temporary files..."
find . -name "*.bak" -type f -delete 2>/dev/null || true
find . -name "*.backup" -type f -delete 2>/dev/null || true
find . -name "*~" -type f -delete 2>/dev/null || true
find . -name ".DS_Store" -type f -delete 2>/dev/null || true

# Clean up any lock files
find . -name "*.lock" -type f -delete 2>/dev/null || true
find . -name "*.pid" -type f -delete 2>/dev/null || true

# Check for and clean up any migration backups
echo ""
print_status "Checking for migration backups..."
find . -name "*.backup_*" -type f 2>/dev/null | while read -r file; do
    print_status "Found migration backup: $file"
    safe_remove "$file"
done

# Deactivate virtual environment if active
echo ""
print_status "Checking virtual environment..."
if [[ "$VIRTUAL_ENV" != "" ]]; then
    VENV_NAME=$(basename "$VIRTUAL_ENV")
    print_status "Deactivating virtual environment: $VENV_NAME"
    deactivate 2>/dev/null || true
    print_success "Virtual environment deactivated"
else
    print_status "No virtual environment currently active"
fi

# Optional: Remove virtual environment entirely
echo ""
read -p "❓ Do you want to remove the virtual environment entirely? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "venv" ]; then
        VENV_SIZE=$(get_size "venv")
        print_status "Removing virtual environment directory ($VENV_SIZE)..."
        rm -rf venv
        print_success "Virtual environment removed"
    else
        print_status "Virtual environment directory not found"
    fi
else
    print_status "Keeping virtual environment directory"
fi

# Optional: Remove configuration files
echo ""
read -p "❓ Do you want to remove configuration files (.env)? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    safe_remove ".env"
    print_warning "Configuration removed - you'll need to reconfigure on next run"
else
    print_status "Keeping configuration files"
fi

# Show final cleanup summary
echo ""
print_success "Cleanup completed!"
echo ""
echo "📊 Cleanup Summary:"
echo "   ✅ Database files removed"
echo "   ✅ Document storage cleared"
echo "   ✅ Performance metrics cleared"
echo "   ✅ Log files removed"
echo "   ✅ Python cache cleared"
echo "   ✅ Test artifacts removed"
echo "   ✅ Streamlit cache cleared"
echo "   ✅ Temporary files cleared"
echo "   ✅ Virtual environment deactivated"

# Check remaining disk usage
if [ -d "." ]; then
    REMAINING_SIZE=$(get_size ".")
    echo "   📁 Remaining project size: $REMAINING_SIZE"
fi

echo ""
print_success "System is now clean and ready for fresh start!"
echo ""
echo "💡 To run the system again:"
echo "   ./scripts/run.sh              - Quick start with health checks"
echo "   ./scripts/deploy.sh           - Full deployment with initialization"
echo ""
echo "🔧 What was cleaned:"
echo "   • All processed documents and embeddings"
echo "   • Q&A session history and interactions"
echo "   • Knowledge graph data and relationships"
echo "   • Performance monitoring metrics"
echo "   • System logs and debug information"
echo "   • Python cache and temporary files"
echo ""
echo "🛡️  What was preserved:"
echo "   • Source code and configuration templates"
echo "   • Virtual environment (unless removed)"
echo "   • Environment configuration (unless removed)"
echo ""