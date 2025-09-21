#!/usr/bin/env python3
"""
Python Cache Clearing Script
Removes all Python cache files and temporary files that might interfere with new implementations.
"""

import os
import shutil
import glob
import sys
from pathlib import Path

def clear_python_cache():
    """Clear all Python cache files from the project."""
    print("🧹 Clearing Python Cache Files")
    print("==============================")
    
    project_root = Path.cwd()
    cache_patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo", 
        "**/*.pyd",
        "**/.pytest_cache",
        "**/pytest_cache",
        "**/.coverage",
        "**/coverage.xml",
        "**/.mypy_cache",
        "**/mypy_cache",
        "**/.tox",
        "**/build",
        "**/dist",
        "**/*.egg-info"
    ]
    
    removed_count = 0
    
    for pattern in cache_patterns:
        matches = list(project_root.glob(pattern))
        for match in matches:
            try:
                if match.is_file():
                    match.unlink()
                    print(f"🗑️  Removed file: {match}")
                    removed_count += 1
                elif match.is_dir():
                    shutil.rmtree(match)
                    print(f"🗑️  Removed directory: {match}")
                    removed_count += 1
            except Exception as e:
                print(f"⚠️  Could not remove {match}: {e}")
    
    print(f"\n✅ Removed {removed_count} cache files/directories")
    return removed_count

def clear_temporary_files():
    """Clear temporary files that might interfere with new logic."""
    print("\n🧹 Clearing Temporary Files")
    print("===========================")
    
    project_root = Path.cwd()
    temp_patterns = [
        "**/tmp",
        "**/temp", 
        "**/.tmp",
        "**/logs/*.log",
        "**/data/cache/**/*",
        "**/results/processing_logs/**/*",
        "**/*.tmp",
        "**/*.temp",
        "**/.DS_Store",
        "**/Thumbs.db"
    ]
    
    removed_count = 0
    
    for pattern in temp_patterns:
        matches = list(project_root.glob(pattern))
        for match in matches:
            try:
                # Skip .gitkeep files
                if match.name == '.gitkeep':
                    continue
                    
                if match.is_file():
                    match.unlink()
                    print(f"🗑️  Removed temp file: {match}")
                    removed_count += 1
                elif match.is_dir() and any(match.iterdir()):  # Only remove non-empty dirs
                    shutil.rmtree(match)
                    print(f"🗑️  Removed temp directory: {match}")
                    removed_count += 1
            except Exception as e:
                print(f"⚠️  Could not remove {match}: {e}")
    
    print(f"\n✅ Removed {removed_count} temporary files/directories")
    return removed_count

def clear_cached_configurations():
    """Clear cached configuration files that might interfere."""
    print("\n🧹 Clearing Cached Configurations")
    print("=================================")
    
    project_root = Path.cwd()
    config_cache_patterns = [
        "**/.env.cache",
        "**/config.cache",
        "**/.config_cache",
        "**/settings.cache"
    ]
    
    removed_count = 0
    
    for pattern in config_cache_patterns:
        matches = list(project_root.glob(pattern))
        for match in matches:
            try:
                if match.is_file():
                    match.unlink()
                    print(f"🗑️  Removed config cache: {match}")
                    removed_count += 1
            except Exception as e:
                print(f"⚠️  Could not remove {match}: {e}")
    
    print(f"\n✅ Removed {removed_count} cached configuration files")
    return removed_count

def validate_clean_state():
    """Validate that the project is in a clean state."""
    print("\n🔍 Validating Clean State")
    print("========================")
    
    project_root = Path.cwd()
    
    # Check for remaining cache files
    cache_files = list(project_root.glob("**/__pycache__"))
    cache_files.extend(list(project_root.glob("**/*.pyc")))
    cache_files.extend(list(project_root.glob("**/*.pyo")))
    
    if cache_files:
        print(f"⚠️  Found {len(cache_files)} remaining cache files:")
        for cache_file in cache_files[:5]:  # Show first 5
            print(f"   - {cache_file}")
        if len(cache_files) > 5:
            print(f"   ... and {len(cache_files) - 5} more")
        return False
    else:
        print("✅ No Python cache files found")
    
    # Check Python import paths
    try:
        import importlib
        import sys
        
        # Clear import cache
        importlib.invalidate_caches()
        
        # Remove any cached modules from our project
        modules_to_remove = []
        for module_name in sys.modules:
            if module_name.startswith('src.'):
                modules_to_remove.append(module_name)
        
        for module_name in modules_to_remove:
            del sys.modules[module_name]
        
        print(f"✅ Cleared {len(modules_to_remove)} cached modules from sys.modules")
        
    except Exception as e:
        print(f"⚠️  Error clearing import cache: {e}")
        return False
    
    print("✅ Project is in clean state")
    return True

def main():
    """Main cache clearing function."""
    print("🚀 Python Cache Clearing Script")
    print("===============================")
    print(f"Working directory: {Path.cwd()}")
    print()
    
    total_removed = 0
    
    # Clear Python cache files
    total_removed += clear_python_cache()
    
    # Clear temporary files
    total_removed += clear_temporary_files()
    
    # Clear cached configurations
    total_removed += clear_cached_configurations()
    
    # Validate clean state
    is_clean = validate_clean_state()
    
    print(f"\n🎉 Cache Clearing Complete!")
    print("===========================")
    print(f"✅ Total files/directories removed: {total_removed}")
    print(f"✅ Clean state validated: {is_clean}")
    
    if is_clean:
        print("\n✨ Project is ready for fresh implementation testing!")
    else:
        print("\n⚠️  Some cache files may remain - manual cleanup may be needed")
    
    return 0 if is_clean else 1

if __name__ == "__main__":
    sys.exit(main())