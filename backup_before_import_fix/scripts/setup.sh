#!/bin/bash

# Setup script for Document Q&A System
echo "Setting up Document Q&A System..."

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

echo "Setup complete! To activate the environment, run:"
echo "source venv/bin/activate"