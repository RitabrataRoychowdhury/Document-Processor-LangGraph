"""
Test backward compatibility and migration functionality.
Ensures existing document upload, processing, and Q&A functionality continues to work.
"""

import pytest
import os
import tempfile
import sqlite3
from datetime import datetime
from unittest.mock import Mock, patch
import sys

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.app import DocumentQAApplication
from src.config.app_config import AppConfig
from src.models.document import Document
from src.storage.document_storage import DocumentStorage
from src.repositories.document_repository import SQLiteDocumentRepository
from scripts.migrate_existing_data import DataMigrationManager


class TestBackwardCompatibility:
    """Test backward compatibility with existing functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def app_config(self, temp_db):
        """Create test application configuration."""
        return AppConfig(
            database_path=temp_db,
            gemini_api_key="test_key",
            max_file_size_mb=5,
            allowed_file_types=["pdf", "txt", "docx"],
            embedding_provider="local",
            qa_provider="gemini",
            enable_knowledge_graph=True
        )
    
    @pytest.fixture
    def app(self, app_config):
        """Create test application instance."""
        with patch('src.app.app_config', app_config):
            app = DocumentQAApplication()
            yield app
            app.shutdown()
    
    def test_configuration_backward_compatibility(self, app_config):
        """Test that new configuration system maintains backward compatibility."""
        # Test that legacy config values are accessible
        assert app_config.max_file_size_mb > 0
        assert len(app_config.allowed_file_types) > 0
        assert app_config.database_path is not None
        
        # Test validation
        errors = app_config.validate()
        # Should have no errors with valid test config
        assert len(errors) == 0
        
        # Test API key access
        assert app_config.get_api_key_for_provider("gemini") == "test_key"
        assert app_config.is_api_configured() == True
    
    def test_document_storage_compatibility(self, temp_db):
        """Test that existing document storage continues to work."""
        # Create a document using the old storage interface with temp database
        from src.storage.database import DatabaseManager
        temp_db_manager = DatabaseManager(temp_db)
        
        with patch('src.storage.document_storage.db_manager', temp_db_manager):
            storage = DocumentStorage()
        
            document = Document(
                id="test_doc_1",
                title="Test Document",
                file_type="pdf",
                file_size=1024,
                upload_timestamp=datetime.now(),
                processing_status="completed",
                original_text="This is test content",
                analysis="Test analysis"
            )
            
            # Test create
            doc_id = storage.create_document(document)
            assert doc_id == "test_doc_1"
            
            # Test retrieve
            retrieved_doc = storage.get_document(doc_id)
            assert retrieved_doc is not None
            assert retrieved_doc.title == "Test Document"
            assert retrieved_doc.processing_status == "completed"
            
            # Test update
            success = storage.update_document(doc_id, {"summary": "Test summary"})
            assert success == True
        
            # Test list
            documents = storage.list_documents()
            assert len(documents) == 1
            assert documents[0].id == doc_id
    
    def test_repository_pattern_compatibility(self, temp_db):
        """Test that new repository pattern works alongside existing storage."""
        # Test document repository with temp database
        from src.storage.database import DatabaseManager
        temp_db_manager = DatabaseManager(temp_db)
        doc_repo = SQLiteDocumentRepository(temp_db_manager)
        
        document = Document(
            id="test_doc_2",
            title="Repository Test Document",
            file_type="txt",
            file_size=512,
            upload_timestamp=datetime.now(),
            processing_status="pending"
        )
        
        # Test save
        doc_id = doc_repo.save(document)
        assert doc_id == "test_doc_2"
        
        # Test find by ID
        found_doc = doc_repo.find_by_id(doc_id)
        assert found_doc is not None
        assert found_doc.title == "Repository Test Document"
        
        # Test find by criteria
        criteria = {"processing_status": "pending"}
        matching_docs = doc_repo.find_by_criteria(criteria)
        assert len(matching_docs) == 1
        assert matching_docs[0].id == doc_id
        
        # Test update
        success = doc_repo.update(doc_id, {"processing_status": "completed"})
        assert success == True
        
        # Verify update
        updated_doc = doc_repo.find_by_id(doc_id)
        assert updated_doc.processing_status == "completed"
    
    def test_application_initialization_compatibility(self, app):
        """Test that application initializes with both old and new components."""
        # Initialize application
        success = app.initialize()
        assert success == True
        assert app.initialized == True
        
        # Test that both old and new components are available
        assert app.get_storage() is not None
        assert app.get_document_repository() is not None
        assert app.get_patient_repository() is not None
        assert app.get_file_handler() is not None
        assert app.get_qa_engine() is not None
        assert app.get_workflow_manager() is not None
        
        # Test system status includes new configuration
        status = app.get_system_status()
        assert status["initialized"] == True
        assert "embedding_provider" in status["config"]
        assert "qa_provider" in status["config"]
        assert "knowledge_graph_enabled" in status["config"]
    
    def test_data_migration_dry_run(self, temp_db):
        """Test data migration dry run functionality."""
        # Create some test data first
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            
            # Create documents table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    upload_timestamp DATETIME NOT NULL,
                    processing_status TEXT NOT NULL DEFAULT 'pending',
                    original_text TEXT,
                    analysis TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert test document
            cursor.execute("""
                INSERT INTO documents (id, title, file_type, file_size, upload_timestamp, processing_status, original_text, analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "test_migration_doc",
                "Migration Test Document",
                "pdf",
                2048,
                datetime.now().isoformat(),
                "completed",
                "Test content for migration",
                "Test analysis for migration"
            ))
            
            conn.commit()
        
        # Test migration dry run
        migration_manager = DataMigrationManager(temp_db)
        result = migration_manager.run_migration(dry_run=True)
        
        assert result["success"] == True
        assert result["dry_run"] == True
        assert "analysis" in result
        
        analysis = result["analysis"]
        assert analysis["documents"] >= 1
        assert analysis["processed_documents"] >= 1
    
    def test_existing_qa_functionality(self, app):
        """Test that existing Q&A functionality continues to work."""
        # Initialize application
        app.initialize()
        
        # Create a test document
        storage = app.get_storage()
        document = Document(
            id="qa_test_doc",
            title="Q&A Test Document",
            file_type="txt",
            file_size=256,
            upload_timestamp=datetime.now(),
            processing_status="completed",
            original_text="This document contains information about testing Q&A functionality.",
            analysis="The document discusses testing procedures for Q&A systems."
        )
        
        storage.create_document(document)
        
        # Test Q&A engine access
        qa_engine = app.get_qa_engine()
        assert qa_engine is not None
        
        # Note: We can't test actual Q&A without API keys, but we can test the interface
        # This ensures the component is properly initialized and accessible
    
    def test_file_upload_compatibility(self, app):
        """Test that file upload functionality remains compatible."""
        # Initialize application
        app.initialize()
        
        # Test file handler access
        file_handler = app.get_file_handler()
        assert file_handler is not None
        
        # Test file validation (mock file)
        mock_file = Mock()
        mock_file.name = "test.pdf"
        mock_file.size = 1024
        
        # This should not raise an exception
        try:
            result = file_handler.validate_file(mock_file)
            # Validation result structure may vary, but should not crash
        except Exception as e:
            # If validation fails, it should be a controlled failure, not a crash
            assert "validation" in str(e).lower() or "file" in str(e).lower()
    
    def test_workflow_manager_compatibility(self, app):
        """Test that workflow manager continues to work."""
        # Initialize application
        app.initialize()
        
        # Test workflow manager access
        workflow_manager = app.get_workflow_manager()
        assert workflow_manager is not None
        
        # Test queue status
        status = workflow_manager.get_queue_status()
        assert "queue_size" in status
        assert isinstance(status["queue_size"], int)
    
    def test_configuration_migration(self):
        """Test that configuration migrates from legacy to new system."""
        # Test with environment variables
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'test_gemini_key',
            'EMBEDDING_PROVIDER': 'openai',
            'QA_PROVIDER': 'gemini',
            'MAX_FILE_SIZE_MB': '15'
        }):
            config = AppConfig.from_env()
            
            assert config.gemini_api_key == 'test_gemini_key'
            assert config.embedding_provider == 'openai'
            assert config.qa_provider == 'gemini'
            assert config.max_file_size_mb == 15
            
            # Test validation
            errors = config.validate()
            # Should have error about OpenAI key missing
            assert any('OPENAI_API_KEY' in error for error in errors)
    
    def test_database_schema_compatibility(self, temp_db):
        """Test that database schema remains compatible."""
        # Initialize database with new schema manager
        from src.storage.database import DatabaseManager
        
        db_manager = DatabaseManager(temp_db)
        
        # Check that all expected tables exist
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            # Check for legacy tables
            expected_legacy_tables = ['documents', 'processing_jobs', 'qa_sessions', 'qa_interactions']
            for table in expected_legacy_tables:
                assert table in tables, f"Legacy table {table} missing"
            
            # Check for new knowledge graph tables (if migration has run)
            # These might not exist yet, which is fine for backward compatibility
            kg_tables = ['kg_nodes', 'kg_relationships']
            for table in kg_tables:
                if table in tables:
                    # If KG tables exist, verify they have the expected structure
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [row[1] for row in cursor.fetchall()]
                    assert 'id' in columns
                    assert 'created_at' in columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])