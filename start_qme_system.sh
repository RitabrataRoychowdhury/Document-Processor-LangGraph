#!/bin/bash

# QME System Launcher
# Simple wrapper to start the complete QME system

echo "🚀 Starting QME System Complete Initialization..."
echo "================================================"

# Check if we're in the right directory
if [ ! -f "scripts/run_complete_system.sh" ]; then
    echo "❌ Error: Please run this script from the QME project root directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected files: scripts/run_complete_system.sh"
    exit 1
fi

# Make sure the script is executable
chmod +x scripts/run_complete_system.sh

# Run the complete system startup script
./scripts/run_complete_system.sh

echo ""
echo "🎉 QME System startup completed!"