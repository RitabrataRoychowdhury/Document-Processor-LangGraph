#!/usr/bin/env python3
"""
API Key Management CLI Utility

This script provides a command-line interface for managing API keys
securely for the QME system.
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.secure_api_key_manager import SecureAPIKeyManager, store_openrouter_api_key, get_openrouter_api_key


def store_key(args):
    """Store an API key"""
    manager = SecureAPIKeyManager()
    
    if args.service == 'openrouter':
        store_openrouter_api_key(args.key, args.expires_days)
        print(f"✅ OpenRouter API key stored successfully")
    else:
        manager.store_api_key(
            args.service, 
            args.key, 
            args.description or f"API key for {args.service}",
            args.expires_days
        )
        print(f"✅ API key for '{args.service}' stored successfully")
    
    if args.expires_days:
        print(f"   Expires in {args.expires_days} days")


def get_key(args):
    """Retrieve an API key"""
    if args.service == 'openrouter':
        key = get_openrouter_api_key()
    else:
        manager = SecureAPIKeyManager()
        key = manager.get_api_key(args.service)
    
    if key:
        if args.show_key:
            print(f"🔑 API key for '{args.service}': {key}")
        else:
            print(f"✅ API key for '{args.service}' found (use --show-key to display)")
    else:
        print(f"❌ No API key found for '{args.service}'")
        sys.exit(1)


def list_keys(args):
    """List all stored API keys"""
    manager = SecureAPIKeyManager()
    keys_list = manager.list_stored_keys()
    
    if not keys_list:
        print("📭 No API keys stored")
        return
    
    print(f"🔐 Stored API Keys ({len(keys_list)} total):")
    print()
    
    for service_name, key_info in keys_list.items():
        status_icon = "❌" if key_info['is_expired'] else "✅"
        print(f"{status_icon} {service_name}")
        print(f"   Description: {key_info['description']}")
        print(f"   Created: {key_info['created_at'][:19] if key_info['created_at'] else 'Unknown'}")
        
        if key_info['expires_at']:
            print(f"   Expires: {key_info['expires_at'][:19]}")
        else:
            print(f"   Expires: Never")
        
        print(f"   Usage: {key_info['usage_count']} times")
        
        if key_info['last_used']:
            print(f"   Last used: {key_info['last_used'][:19]}")
        
        if key_info['rotation_count'] > 0:
            print(f"   Rotated: {key_info['rotation_count']} times")
        
        print()


def rotate_key(args):
    """Rotate an API key"""
    manager = SecureAPIKeyManager()
    
    if args.service == 'openrouter':
        # For OpenRouter, we need to store the new key
        store_openrouter_api_key(args.new_key, args.expires_days)
        print(f"🔄 OpenRouter API key rotated successfully")
    else:
        manager.rotate_api_key(args.service, args.new_key)
        print(f"🔄 API key for '{args.service}' rotated successfully")


def delete_key(args):
    """Delete an API key"""
    manager = SecureAPIKeyManager()
    
    if not args.confirm:
        response = input(f"⚠️  Are you sure you want to delete the API key for '{args.service}'? (y/N): ")
        if response.lower() != 'y':
            print("❌ Deletion cancelled")
            return
    
    success = manager.delete_api_key(args.service)
    
    if success:
        print(f"🗑️  API key for '{args.service}' deleted successfully")
    else:
        print(f"❌ No API key found for '{args.service}'")
        sys.exit(1)


def security_check(args):
    """Perform security validation"""
    manager = SecureAPIKeyManager()
    report = manager.validate_key_security()
    
    print("🔒 Security Validation Report")
    print("=" * 40)
    print(f"Total keys: {report['total_keys']}")
    print(f"Expired keys: {report['expired_keys']}")
    print(f"Unused keys: {report['unused_keys']}")
    print(f"High usage keys: {report['high_usage_keys']}")
    print()
    
    if report['security_issues']:
        print("⚠️  Security Issues:")
        for issue in report['security_issues']:
            print(f"   • {issue}")
        print()
    
    if report['recommendations']:
        print("💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"   • {rec}")
        print()
    
    if not report['security_issues']:
        print("✅ No security issues found")


def setup_openrouter(args):
    """Interactive setup for OpenRouter API key"""
    print("🚀 OpenRouter API Key Setup")
    print("=" * 30)
    print()
    
    # Check if key already exists
    existing_key = get_openrouter_api_key()
    if existing_key and not args.force:
        print("✅ OpenRouter API key already configured")
        print("   Use --force to overwrite existing key")
        return
    
    print("Please enter your OpenRouter API key.")
    print("You can get one from: https://openrouter.ai/keys")
    print()
    
    api_key = input("API Key: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        sys.exit(1)
    
    # Validate key format (basic check)
    if not api_key.startswith(('sk-', 'or-')):
        print("⚠️  Warning: API key doesn't match expected format")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("❌ Setup cancelled")
            return
    
    # Ask about expiration
    print()
    print("Set expiration for the API key:")
    print("1. 1 year (recommended)")
    print("2. 6 months")
    print("3. 3 months")
    print("4. Never expire")
    
    choice = input("Choose option (1-4) [1]: ").strip() or "1"
    
    expires_days = {
        "1": 365,
        "2": 180,
        "3": 90,
        "4": None
    }.get(choice, 365)
    
    # Store the key
    store_openrouter_api_key(api_key, expires_days)
    
    print()
    print("✅ OpenRouter API key configured successfully!")
    
    if expires_days:
        print(f"   Key will expire in {expires_days} days")
    else:
        print("   Key will never expire")
    
    print()
    print("🔧 Next steps:")
    print("   1. Test the configuration: python scripts/manage_api_keys.py get openrouter")
    print("   2. Run the QME system to verify integration")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Secure API Key Management for QME System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive OpenRouter setup
  python scripts/manage_api_keys.py setup-openrouter
  
  # Store an API key
  python scripts/manage_api_keys.py store openrouter sk-your-key-here
  
  # List all keys
  python scripts/manage_api_keys.py list
  
  # Get a key (hidden by default)
  python scripts/manage_api_keys.py get openrouter --show-key
  
  # Security check
  python scripts/manage_api_keys.py security-check
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup OpenRouter command
    setup_parser = subparsers.add_parser('setup-openrouter', help='Interactive OpenRouter API key setup')
    setup_parser.add_argument('--force', action='store_true', help='Overwrite existing key')
    setup_parser.set_defaults(func=setup_openrouter)
    
    # Store command
    store_parser = subparsers.add_parser('store', help='Store an API key')
    store_parser.add_argument('service', help='Service name (e.g., openrouter)')
    store_parser.add_argument('key', help='API key to store')
    store_parser.add_argument('--description', help='Description for the key')
    store_parser.add_argument('--expires-days', type=int, help='Expiration in days')
    store_parser.set_defaults(func=store_key)
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Retrieve an API key')
    get_parser.add_argument('service', help='Service name')
    get_parser.add_argument('--show-key', action='store_true', help='Display the actual key')
    get_parser.set_defaults(func=get_key)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all stored API keys')
    list_parser.set_defaults(func=list_keys)
    
    # Rotate command
    rotate_parser = subparsers.add_parser('rotate', help='Rotate an API key')
    rotate_parser.add_argument('service', help='Service name')
    rotate_parser.add_argument('new_key', help='New API key')
    rotate_parser.add_argument('--expires-days', type=int, help='Expiration in days')
    rotate_parser.set_defaults(func=rotate_key)
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete an API key')
    delete_parser.add_argument('service', help='Service name')
    delete_parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    delete_parser.set_defaults(func=delete_key)
    
    # Security check command
    security_parser = subparsers.add_parser('security-check', help='Perform security validation')
    security_parser.set_defaults(func=security_check)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()