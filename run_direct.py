#!/usr/bin/env python3
"""
Direct runner for the QME system that bypasses run.sh script issues.
This ensures we use the current directory's code with all fixes applied.
"""

import sys
import os
import subprocess

def main():
    print("🚀 QME System - Direct Runner")
    print("=" * 40)
    
    # Ensure we're using the current directory
    current_dir = os.getcwd()
    print(f"📁 Working directory: {current_dir}")
    
    # Add current directory to Python path
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    print("🔍 Testing imports...")
    try:
        # Test critical imports
        from src.ui.upload_interface import UploadInterface
        from src.core.extraction.openrouter_extraction_service import OpenRouterExtractionService
        from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
        print("✅ All imports successful - fixes are active")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return 1
    
    print("\n🌐 Starting Streamlit application...")
    print("📍 URL: http://localhost:8501")
    print("⏹️  Press Ctrl+C to stop")
    print("-" * 40)
    
    # Run streamlit directly
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "src/ui/main_app.py",
            "--server.port=8501",
            "--server.address=localhost",
            "--server.headless=false",
            "--browser.gatherUsageStats=false"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())