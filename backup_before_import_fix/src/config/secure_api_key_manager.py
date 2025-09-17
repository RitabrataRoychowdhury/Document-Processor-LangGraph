"""
Secure API Key Management for OpenRouter Integration

This module provides secure storage and retrieval of API keys with encryption
and rotation capabilities for enhanced security.
"""

import os
import json
import base64
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class SecureAPIKeyManager:
    """
    Secure API key management with encryption and rotation capabilities.
    """
    
    def __init__(self, key_store_path: str = ".kiro/secure/api_keys.enc"):
        """
        Initialize secure API key manager.
        
        Args:
            key_store_path: Path to encrypted key store file
        """
        self.key_store_path = Path(key_store_path)
        self.key_store_path.parent.mkdir(parents=True, exist_ok=True)
        self._encryption_key: Optional[bytes] = None
        self._key_data: Dict[str, Any] = {}
        
    def _get_encryption_key(self) -> bytes:
        """
        Get or generate encryption key for API key storage.
        
        Returns:
            Encryption key bytes
        """
        if self._encryption_key is not None:
            return self._encryption_key
        
        # Try to get master password from environment
        master_password = os.getenv('QME_MASTER_PASSWORD')
        if not master_password:
            # Generate a default key based on system info (less secure)
            import platform
            import getpass
            
            system_info = f"{platform.node()}{getpass.getuser()}"
            master_password = system_info
            logger.warning(
                "No QME_MASTER_PASSWORD set. Using system-based key. "
                "Set QME_MASTER_PASSWORD environment variable for better security."
            )
        
        # Derive encryption key from master password
        salt = b'qme_system_salt_2024'  # In production, use random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        self._encryption_key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        return self._encryption_key
    
    def _encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data as base64 string
        """
        fernet = Fernet(self._get_encryption_key())
        encrypted_data = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted data as base64 string
            
        Returns:
            Decrypted data
        """
        fernet = Fernet(self._get_encryption_key())
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        return fernet.decrypt(decoded_data).decode()
    
    def _load_key_store(self) -> None:
        """Load encrypted key store from file"""
        if not self.key_store_path.exists():
            self._key_data = {}
            return
        
        try:
            with open(self.key_store_path, 'r') as f:
                encrypted_content = f.read()
            
            if encrypted_content.strip():
                decrypted_content = self._decrypt_data(encrypted_content)
                self._key_data = json.loads(decrypted_content)
            else:
                self._key_data = {}
                
        except Exception as e:
            logger.error(f"Failed to load key store: {str(e)}")
            self._key_data = {}
    
    def _save_key_store(self) -> None:
        """Save encrypted key store to file"""
        try:
            json_content = json.dumps(self._key_data, indent=2)
            encrypted_content = self._encrypt_data(json_content)
            
            with open(self.key_store_path, 'w') as f:
                f.write(encrypted_content)
            
            # Set restrictive permissions
            os.chmod(self.key_store_path, 0o600)
            
        except Exception as e:
            logger.error(f"Failed to save key store: {str(e)}")
            raise
    
    def store_api_key(
        self, 
        service_name: str, 
        api_key: str, 
        description: str = "",
        expires_days: Optional[int] = None
    ) -> None:
        """
        Store API key securely.
        
        Args:
            service_name: Name of the service (e.g., 'openrouter')
            api_key: The API key to store
            description: Optional description
            expires_days: Optional expiration in days
        """
        self._load_key_store()
        
        expiry_date = None
        if expires_days:
            expiry_date = (datetime.now() + timedelta(days=expires_days)).isoformat()
        
        self._key_data[service_name] = {
            'api_key': self._encrypt_data(api_key),
            'description': description,
            'created_at': datetime.now().isoformat(),
            'expires_at': expiry_date,
            'last_used': None,
            'usage_count': 0
        }
        
        self._save_key_store()
        logger.info(f"API key stored for service: {service_name}")
    
    def get_api_key(self, service_name: str) -> Optional[str]:
        """
        Retrieve API key for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            API key or None if not found/expired
        """
        self._load_key_store()
        
        if service_name not in self._key_data:
            logger.warning(f"No API key found for service: {service_name}")
            return None
        
        key_info = self._key_data[service_name]
        
        # Check expiration
        if key_info.get('expires_at'):
            expiry_date = datetime.fromisoformat(key_info['expires_at'])
            if datetime.now() > expiry_date:
                logger.warning(f"API key for {service_name} has expired")
                return None
        
        # Update usage tracking
        key_info['last_used'] = datetime.now().isoformat()
        key_info['usage_count'] = key_info.get('usage_count', 0) + 1
        self._save_key_store()
        
        try:
            return self._decrypt_data(key_info['api_key'])
        except Exception as e:
            logger.error(f"Failed to decrypt API key for {service_name}: {str(e)}")
            return None
    
    def rotate_api_key(self, service_name: str, new_api_key: str) -> None:
        """
        Rotate API key for a service.
        
        Args:
            service_name: Name of the service
            new_api_key: New API key
        """
        self._load_key_store()
        
        if service_name not in self._key_data:
            logger.warning(f"No existing API key found for service: {service_name}")
            self.store_api_key(service_name, new_api_key, "Rotated key")
            return
        
        # Backup old key info
        old_key_info = self._key_data[service_name].copy()
        
        # Update with new key
        self._key_data[service_name].update({
            'api_key': self._encrypt_data(new_api_key),
            'rotated_at': datetime.now().isoformat(),
            'previous_rotation': old_key_info.get('rotated_at'),
            'rotation_count': old_key_info.get('rotation_count', 0) + 1
        })
        
        self._save_key_store()
        logger.info(f"API key rotated for service: {service_name}")
    
    def list_stored_keys(self) -> Dict[str, Dict[str, Any]]:
        """
        List all stored API keys with metadata (without actual keys).
        
        Returns:
            Dictionary of service names and their metadata
        """
        self._load_key_store()
        
        result = {}
        for service_name, key_info in self._key_data.items():
            result[service_name] = {
                'description': key_info.get('description', ''),
                'created_at': key_info.get('created_at'),
                'expires_at': key_info.get('expires_at'),
                'last_used': key_info.get('last_used'),
                'usage_count': key_info.get('usage_count', 0),
                'rotation_count': key_info.get('rotation_count', 0),
                'is_expired': self._is_key_expired(key_info)
            }
        
        return result
    
    def _is_key_expired(self, key_info: Dict[str, Any]) -> bool:
        """Check if a key is expired"""
        if not key_info.get('expires_at'):
            return False
        
        expiry_date = datetime.fromisoformat(key_info['expires_at'])
        return datetime.now() > expiry_date
    
    def delete_api_key(self, service_name: str) -> bool:
        """
        Delete API key for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if deleted, False if not found
        """
        self._load_key_store()
        
        if service_name in self._key_data:
            del self._key_data[service_name]
            self._save_key_store()
            logger.info(f"API key deleted for service: {service_name}")
            return True
        
        return False
    
    def validate_key_security(self) -> Dict[str, Any]:
        """
        Validate the security of stored keys.
        
        Returns:
            Security validation report
        """
        self._load_key_store()
        
        report = {
            'total_keys': len(self._key_data),
            'expired_keys': 0,
            'unused_keys': 0,
            'high_usage_keys': 0,
            'security_issues': [],
            'recommendations': []
        }
        
        for service_name, key_info in self._key_data.items():
            # Check for expired keys
            if self._is_key_expired(key_info):
                report['expired_keys'] += 1
                report['security_issues'].append(f"Expired key for {service_name}")
            
            # Check for unused keys
            if not key_info.get('last_used'):
                report['unused_keys'] += 1
            
            # Check for high usage
            usage_count = key_info.get('usage_count', 0)
            if usage_count > 10000:  # Arbitrary threshold
                report['high_usage_keys'] += 1
                report['recommendations'].append(f"Consider rotating high-usage key for {service_name}")
        
        # General recommendations
        if report['expired_keys'] > 0:
            report['recommendations'].append("Remove or rotate expired API keys")
        
        if not os.getenv('QME_MASTER_PASSWORD'):
            report['security_issues'].append("No master password set - using system-based encryption")
            report['recommendations'].append("Set QME_MASTER_PASSWORD environment variable")
        
        return report


def get_openrouter_api_key() -> Optional[str]:
    """
    Convenience function to get OpenRouter API key.
    
    Returns:
        OpenRouter API key or None
    """
    # First try environment variable (for backward compatibility)
    env_key = os.getenv('OPENROUTER_API_KEY')
    if env_key:
        return env_key
    
    # Then try secure key manager
    try:
        key_manager = SecureAPIKeyManager()
        return key_manager.get_api_key('openrouter')
    except Exception as e:
        logger.error(f"Failed to retrieve API key from secure storage: {str(e)}")
        return None


def store_openrouter_api_key(api_key: str, expires_days: Optional[int] = 365) -> None:
    """
    Convenience function to store OpenRouter API key securely.
    
    Args:
        api_key: The API key to store
        expires_days: Optional expiration in days (default 1 year)
    """
    key_manager = SecureAPIKeyManager()
    key_manager.store_api_key(
        'openrouter', 
        api_key, 
        'OpenRouter API key for QME system',
        expires_days
    )