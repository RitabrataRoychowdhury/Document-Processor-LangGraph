#!/usr/bin/env python3
"""
Startup script for QME Document Extraction Testing API

This script starts the FastAPI server with proper configuration and validation.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

# Add project root to path
sys.path.append('.')

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'python-multipart',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_environment():
    """Check environment configuration."""
    print("\n🔧 Checking environment configuration...")
    
    # Check for API keys
    api_keys = {
        'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY')
    }
    
    configured_apis = []
    for key, value in api_keys.items():
        if value:
            print(f"   ✅ {key}: configured")
            configured_apis.append(key.split('_')[0].lower())
        else:
            print(f"   ⚠️ {key}: not configured")
    
    if not configured_apis:
        print("   ⚠️ No API keys configured - some features may not work")
    else:
        print(f"   📡 Available APIs: {', '.join(configured_apis)}")
    
    # Check configuration files
    config_files = [
        'config/settings/openrouter_config.yaml',
        'config/settings/gemini_config.yaml',
        'config/templates/qme_template_structure.yaml'
    ]
    
    print("\n📁 Checking configuration files...")
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"   ✅ {config_file}")
        else:
            print(f"   ⚠️ {config_file}: not found (will use defaults)")
    
    return True

def check_directories():
    """Ensure required directories exist."""
    print("\n📂 Checking/creating directories...")
    
    directories = [
        'results/generated_documents',
        'results/templates_archive',
        'results/quality_reports',
        'logs',
        'data/cache'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")
    
    return True

def wait_for_server(url: str, timeout: int = 30) -> bool:
    """Wait for server to be ready."""
    print(f"\n⏳ Waiting for server to start at {url}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print("   ✅ Server is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
        print("   ⏳ Still waiting...")
    
    print("   ❌ Server failed to start within timeout")
    return False

def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """Start the FastAPI server."""
    print(f"\n🚀 Starting QME Document Extraction Testing API")
    print("=" * 60)
    print(f"📍 Server will be available at: http://localhost:{port}")
    print(f"📚 API Documentation: http://localhost:{port}/docs")
    print(f"🔍 Health Check: http://localhost:{port}/health")
    print("=" * 60)
    
    # Build uvicorn command
    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.api.extraction_testing_api:app",
        "--host", host,
        "--port", str(port),
        "--log-level", "info"
    ]
    
    if reload:
        cmd.append("--reload")
    
    try:
        # Start server
        process = subprocess.Popen(cmd)
        
        # Wait for server to be ready
        server_url = f"http://localhost:{port}"
        if wait_for_server(server_url):
            print(f"\n🎉 Server started successfully!")
            print(f"   API Base URL: {server_url}")
            print(f"   Interactive Docs: {server_url}/docs")
            print(f"   Health Check: {server_url}/health")
            print("\n💡 Test the API with:")
            print(f"   python scripts/test_extraction_api.py --url {server_url}")
            print("\n🛑 Press Ctrl+C to stop the server")
        
        # Wait for process to complete or be interrupted
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        process.terminate()
        process.wait()
        print("   ✅ Server stopped")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        return False
    
    return True

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start QME Document Extraction Testing API")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload on code changes"
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip dependency and environment checks"
    )
    
    args = parser.parse_args()
    
    if not args.skip_checks:
        # Run pre-flight checks
        if not check_dependencies():
            print("\n❌ Dependency check failed. Please install missing packages.")
            sys.exit(1)
        
        check_environment()
        check_directories()
    
    # Start server
    reload = not args.no_reload
    success = start_server(args.host, args.port, reload)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()