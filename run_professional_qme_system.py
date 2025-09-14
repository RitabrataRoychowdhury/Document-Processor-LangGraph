#!/usr/bin/env python3
"""
Professional QME System - Complete Demo Runner

This script demonstrates the complete Professional QME Template Assembly System
integrated with the existing Document Q&A System.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main demo runner for the Professional QME System."""
    
    print("🏥 PROFESSIONAL QME TEMPLATE ASSEMBLY SYSTEM")
    print("=" * 60)
    print("Complete system with gold standard compliance and quality assurance")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("scripts/run.sh"):
        print("❌ Error: Please run this script from the project root directory")
        print("   Current directory:", os.getcwd())
        print("   Expected files: scripts/run.sh, src/, requirements.txt")
        return 1
    
    print("\n🎯 What would you like to do?")
    print("   1) 🌐 Start complete web interface (recommended)")
    print("   2) 🧪 Run Professional Template Assembly demo")
    print("   3) 🔧 Run system health checks")
    print("   4) 📚 Initialize with sample documents")
    print("   5) 🚀 Quick start (skip health checks)")
    print("")
    
    try:
        choice = input("Choose an option (1-5): ").strip()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        return 0
    
    if choice == "1":
        print("\n🌐 Starting complete web interface...")
        print("   This includes:")
        print("   - Document Q&A System")
        print("   - QME Template Generator") 
        print("   - Professional Template Assembly System")
        print("   - Knowledge Base Management")
        print("")
        
        # Run the main system
        try:
            result = subprocess.run(["bash", "scripts/run.sh"], check=False)
            return result.returncode
        except FileNotFoundError:
            print("❌ Error: bash not found. Trying with sh...")
            try:
                result = subprocess.run(["sh", "scripts/run.sh"], check=False)
                return result.returncode
            except FileNotFoundError:
                print("❌ Error: Shell not found. Please run scripts/run.sh manually")
                return 1
    
    elif choice == "2":
        print("\n🧪 Running Professional Template Assembly demo...")
        print("   This will demonstrate:")
        print("   - Template assembly with gold standard compliance")
        print("   - Comprehensive validation and quality assurance")
        print("   - Professional DOCX generation")
        print("   - Download package creation")
        print("")
        
        # Run the professional template demo
        try:
            result = subprocess.run([
                sys.executable, 
                "examples/professional_template_assembler_demo.py"
            ], check=False)
            return result.returncode
        except Exception as e:
            print(f"❌ Error running demo: {e}")
            return 1
    
    elif choice == "3":
        print("\n🔧 Running system health checks...")
        
        # Run health checks using the run script
        try:
            # Use echo to simulate choosing option 3 (health checks)
            result = subprocess.run(
                ["bash", "scripts/run.sh"], 
                input="3\n", 
                text=True, 
                check=False
            )
            return result.returncode
        except Exception as e:
            print(f"❌ Error running health checks: {e}")
            return 1
    
    elif choice == "4":
        print("\n📚 Initializing with sample documents...")
        print("   This will process canonical medical documents into the knowledge base")
        
        # Run knowledge base initialization
        try:
            result = subprocess.run(
                ["bash", "scripts/run.sh"], 
                input="6\n", 
                text=True, 
                check=False
            )
            return result.returncode
        except Exception as e:
            print(f"❌ Error initializing knowledge base: {e}")
            return 1
    
    elif choice == "5":
        print("\n🚀 Quick start - launching web interface...")
        
        # Quick start mode
        try:
            result = subprocess.run(
                ["bash", "scripts/run.sh"], 
                input="7\n", 
                text=True, 
                check=False
            )
            return result.returncode
        except Exception as e:
            print(f"❌ Error in quick start: {e}")
            return 1
    
    else:
        print(f"\n❌ Invalid choice: {choice}")
        print("   Please choose a number between 1-5")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)