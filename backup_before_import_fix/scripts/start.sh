#!/bin/bash

# Document Q&A System - Quick Start
# Simple one-command startup script

echo "🚀 Document Q&A System - Quick Start"
echo "====================================="

# Activate venv and run
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Please run: ./scripts/run.sh first"
    exit 1
fi

# Quick check
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example"
    cp .env.example .env 2>/dev/null || true
fi

echo "🌐 Starting web interface at http://localhost:8501"
echo "📱 Press Ctrl+C to stop"
echo ""

python main.py --web