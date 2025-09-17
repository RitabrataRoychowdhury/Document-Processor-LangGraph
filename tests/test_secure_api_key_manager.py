"""
Unit tests for Secure API Key Manager

This test suite validates the secure API key management functionality,
including encryption, storage, retrieval, and rotation capabilities.
"""

import os
import json
import pytest
import tempfile
from unittest.mock import patch, Mock
from pathlib import Path
from datetime import datetime, timedelta

from src.config.secure_api_key_manager import (
    SecureAPIKeyManager,
    get_openrouter_api_key,
    store_openrouter_api_key
)


class TestSecureAPIKeyManager:
    """Test suite for secure API key manager"""
    
    @pytest.fixture
    def temp_key_store(self):
        """Create temporary key store for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            key_store_path = os.path.join(temp_dir, "test_keys.enc")
            yield key_store_path
    
    @pytest.fixture
    def key_manager(self, temp_key_store):
        """Create key manager instance for testing"""
        return SecureAPIKeyManager(key_store_path=temp_key_store)
    
    def test_key_manager_initialization(self, temp_key_store):
        """Test key manager initialization"""
        manager = SecureAPIKeyManager(key_store_path=temp_key_store)
        
        assert manager.key_store_path == Path(temp_key_store)
        assert manager.key_store_path.parent.exists()
        assert manager._encryption_key is None
        assert manager._key_data == {}
    
    def test_encryption_key_generation(self, key_manager):
        """Test encryption key generation"""
        with patch.dict(os.environ, {'QME_MASTER_PASSWORD': 'test_password'}):
            key1 = key_manager._get_encryption_key()
            key2 = key_manager._get_encryption_key()
            
            # Should return same key on subsequent calls
            assert key1 == key2
            assert len(key1) > 0
    
    def test_encryption_key_without_master_password(self, key_manager):
        """Test encryption key generation without master password"""
        with patch.dict(os.environ, {}, clear=True):
            key = key_manager._get_encryption_key()
            
            assert key is not None
            assert len(key) > 0
    
    def test_data_encryption_decryption(self, key_manager):
        """Test data encryption and decryption"""
        test_data = "test_api_key_12345"
        
        encrypted = key_manager._encrypt_data(test_data)
        decrypted = key_manager._decrypt_data(encrypted)
        
        assert encrypted != test_data
        assert decrypted == test_data
    
    def test_store_and_retrieve_api_key(self, key_manager):
        """Test storing and retrieving API key"""
        service_name = "test_service"
        api_key = "test_api_key_12345"
        description = "Test API key"
        
        # Store API key
        key_manager.store_api_key(service_name, api_key, description)
        
        # Retrieve API key
        retrieved_key = key_manager.get_api_key(service_name)
        
        assert retrieved_key == api_key
    
    def test_store_api_key_with_expiration(self, key_manager):
        """Test storing API key with expiration"""
        service_name = "expiring_service"
        api_key = "expiring_key_12345"
        expires_days = 30
        
        key_manager.store_api_key(service_name, api_key, expires_days=expires_days)
        
        # Should be able to retrieve immediately
        retrieved_key = key_manager.get_api_key(service_name)
        assert retrieved_key == api_key
        
        # Check expiration date is set
        key_manager._load_key_store()
        key_info = key_manager._key_data[service_name]
        assert key_info['expires_at'] is not None
        
        expiry_date = datetime.fromisoformat(key_info['expires_at'])
        expected_expiry = datetime.now() + timedelta(days=expires_days)
        
        # Allow for small time difference in test execution
        assert abs((expiry_date - expected_expiry).total_seconds()) < 60
    
    def test_expired_key_retrieval(self, key_manager):
        """Test retrieval of expired API key"""
        service_name = "expired_service"
        api_key = "expired_key_12345"
        
        # Store key with past expiration
        key_manager.store_api_key(service_name, api_key)
        
        # Manually set expiration to past date
        key_manager._load_key_store()
        key_manager._key_data[service_name]['expires_at'] = (
            datetime.now() - timedelta(days=1)
        ).isoformat()
        key_manager._save_key_store()
        
        # Should return None for expired key
        retrieved_key = key_manager.get_api_key(service_name)
        assert retrieved_key is None
    
    def test_nonexistent_key_retrieval(self, key_manager):
        """Test retrieval of nonexistent API key"""
        retrieved_key = key_manager.get_api_key("nonexistent_service")
        assert retrieved_key is None
    
    def test_api_key_rotation(self, key_manager):
        """Test API key rotation"""
        service_name = "rotation_service"
        old_key = "old_api_key_12345"
        new_key = "new_api_key_67890"
        
        # Store initial key
        key_manager.store_api_key(service_name, old_key)
        
        # Rotate key
        key_manager.rotate_api_key(service_name, new_key)
        
        # Should retrieve new key
        retrieved_key = key_manager.get_api_key(service_name)
        assert retrieved_key == new_key
        
        # Check rotation metadata
        key_manager._load_key_store()
        key_info = key_manager._key_data[service_name]
        assert 'rotated_at' in key_info
        assert key_info['rotation_count'] == 1
    
    def test_rotation_of_nonexistent_key(self, key_manager):
        """Test rotation of nonexistent API key"""
        service_name = "new_rotation_service"
        new_key = "new_api_key_12345"
        
        # Should create new key entry
        key_manager.rotate_api_key(service_name, new_key)
        
        retrieved_key = key_manager.get_api_key(service_name)
        assert retrieved_key == new_key
    
    def test_list_stored_keys(self, key_manager):
        """Test listing stored keys"""
        # Store multiple keys
        key_manager.store_api_key("service1", "key1", "First service")
        key_manager.store_api_key("service2", "key2", "Second service", expires_days=30)
        
        # Get one key to update usage
        key_manager.get_api_key("service1")
        
        keys_list = key_manager.list_stored_keys()
        
        assert len(keys_list) == 2
        assert "service1" in keys_list
        assert "service2" in keys_list
        
        # Check metadata
        service1_info = keys_list["service1"]
        assert service1_info['description'] == "First service"
        assert service1_info['usage_count'] == 1
        assert service1_info['last_used'] is not None
        assert service1_info['is_expired'] is False
        
        service2_info = keys_list["service2"]
        assert service2_info['expires_at'] is not None
        assert service2_info['usage_count'] == 0
    
    def test_delete_api_key(self, key_manager):
        """Test deleting API key"""
        service_name = "delete_service"
        api_key = "delete_key_12345"
        
        # Store key
        key_manager.store_api_key(service_name, api_key)
        
        # Verify it exists
        assert key_manager.get_api_key(service_name) == api_key
        
        # Delete key
        result = key_manager.delete_api_key(service_name)
        assert result is True
        
        # Verify it's gone
        assert key_manager.get_api_key(service_name) is None
        
        # Try to delete again
        result = key_manager.delete_api_key(service_name)
        assert result is False
    
    def test_usage_tracking(self, key_manager):
        """Test API key usage tracking"""
        service_name = "usage_service"
        api_key = "usage_key_12345"
        
        key_manager.store_api_key(service_name, api_key)
        
        # Use key multiple times
        for i in range(3):
            retrieved_key = key_manager.get_api_key(service_name)
            assert retrieved_key == api_key
        
        # Check usage count
        keys_list = key_manager.list_stored_keys()
        usage_info = keys_list[service_name]
        assert usage_info['usage_count'] == 3
        assert usage_info['last_used'] is not None
    
    def test_key_store_persistence(self, temp_key_store):
        """Test key store persistence across manager instances"""
        service_name = "persistence_service"
        api_key = "persistence_key_12345"
        
        # Store key with first manager instance
        manager1 = SecureAPIKeyManager(key_store_path=temp_key_store)
        manager1.store_api_key(service_name, api_key)
        
        # Retrieve key with second manager instance
        manager2 = SecureAPIKeyManager(key_store_path=temp_key_store)
        retrieved_key = manager2.get_api_key(service_name)
        
        assert retrieved_key == api_key
    
    def test_security_validation(self, key_manager):
        """Test security validation report"""
        # Store various types of keys
        key_manager.store_api_key("normal_service", "normal_key")
        key_manager.store_api_key("expiring_service", "expiring_key", expires_days=1)
        
        # Create expired key manually
        key_manager.store_api_key("expired_service", "expired_key")
        key_manager._load_key_store()
        key_manager._key_data["expired_service"]["expires_at"] = (
            datetime.now() - timedelta(days=1)
        ).isoformat()
        key_manager._save_key_store()
        
        # Create high usage key
        key_manager.store_api_key("high_usage_service", "high_usage_key")
        key_manager._load_key_store()
        key_manager._key_data["high_usage_service"]["usage_count"] = 15000
        key_manager._save_key_store()
        
        report = key_manager.validate_key_security()
        
        assert report['total_keys'] == 4
        assert report['expired_keys'] == 1
        assert report['high_usage_keys'] == 1
        assert len(report['security_issues']) > 0
        assert len(report['recommendations']) > 0
    
    def test_file_permissions(self, key_manager):
        """Test that key store file has correct permissions"""
        service_name = "permission_service"
        api_key = "permission_key_12345"
        
        key_manager.store_api_key(service_name, api_key)
        
        # Check file permissions (should be 600 - owner read/write only)
        file_stat = os.stat(key_manager.key_store_path)
        file_mode = file_stat.st_mode & 0o777
        
        # On some systems, the exact permissions might vary
        # Just check that it's not world-readable
        assert (file_mode & 0o044) == 0  # No group or other read permissions


class TestConvenienceFunctions:
    """Test suite for convenience functions"""
    
    def test_get_openrouter_api_key_from_env(self):
        """Test getting OpenRouter API key from environment"""
        test_key = "env_test_key_12345"
        
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': test_key}):
            retrieved_key = get_openrouter_api_key()
            assert retrieved_key == test_key
    
    def test_get_openrouter_api_key_from_secure_storage(self):
        """Test getting OpenRouter API key from secure storage"""
        test_key = "secure_test_key_12345"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            key_store_path = os.path.join(temp_dir, "test_keys.enc")
            
            # Store key using convenience function
            with patch('src.config.secure_api_key_manager.SecureAPIKeyManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                store_openrouter_api_key(test_key)
                
                # Verify store was called correctly
                mock_manager.store_api_key.assert_called_once_with(
                    'openrouter',
                    test_key,
                    'OpenRouter API key for QME system',
                    365
                )
    
    def test_get_openrouter_api_key_fallback(self):
        """Test fallback behavior when secure storage fails"""
        test_key = "fallback_test_key_12345"
        
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': test_key}):
            with patch('src.config.secure_api_key_manager.SecureAPIKeyManager') as mock_manager_class:
                # Make secure storage fail
                mock_manager_class.side_effect = Exception("Storage failed")
                
                retrieved_key = get_openrouter_api_key()
                assert retrieved_key == test_key
    
    def test_get_openrouter_api_key_none_available(self):
        """Test when no API key is available"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('src.config.secure_api_key_manager.SecureAPIKeyManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager.get_api_key.return_value = None
                mock_manager_class.return_value = mock_manager
                
                retrieved_key = get_openrouter_api_key()
                assert retrieved_key is None


if __name__ == "__main__":
    pytest.main([__file__])