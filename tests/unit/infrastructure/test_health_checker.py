"""
Tests for health checker service.
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

from src.infrastructure.monitoring.health_checker import HealthChecker, HealthStatus
from src.config.app_config import AppConfig


class TestHealthChecker:
    """Test health checker functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        
        self.config = AppConfig(
            database_path=str(self.db_path),
            gemini_api_key="test_key",
            openai_api_key="",
            embedding_provider="local",
            qa_provider="gemini",
            max_file_size_mb=10,
            allowed_file_types=["pdf", "docx", "txt"]
        )
        
        self.health_checker = HealthChecker(self.config)
    
    def test_database_health_no_file(self):
        """Test database health check when file doesn't exist."""
        result = self.health_checker.check_database_health()
        
        assert isinstance(result, HealthStatus)
        assert not result.is_healthy
        assert result.component == "database"
        assert "does not exist" in result.message
    
    def test_database_health_with_file(self):
        """Test database health check with existing database."""
        # Create database file
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE documents (id TEXT PRIMARY KEY)")
            conn.execute("CREATE TABLE kg_nodes (id TEXT PRIMARY KEY)")
            conn.execute("CREATE TABLE kg_relationships (id TEXT PRIMARY KEY)")
        
        result = self.health_checker.check_database_health()
        
        assert isinstance(result, HealthStatus)
        assert result.is_healthy
        assert result.component == "database"
        assert "healthy" in result.message.lower()
        assert result.response_time_ms is not None
        assert result.response_time_ms > 0
    
    def test_database_health_missing_tables(self):
        """Test database health check with missing required tables."""
        # Create database file but without required tables
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE other_table (id TEXT PRIMARY KEY)")
        
        result = self.health_checker.check_database_health()
        
        assert isinstance(result, HealthStatus)
        assert not result.is_healthy
        assert result.component == "database"
        assert "missing" in result.message.lower()
        assert "missing_tables" in result.details
    
    @patch('src.services.health_checker.KnowledgeGraphRepository')
    def test_knowledge_graph_health_empty(self, mock_kg_repo):
        """Test knowledge graph health check when empty."""
        mock_repo_instance = Mock()
        mock_repo_instance.get_node_count.return_value = 0
        mock_kg_repo.return_value = mock_repo_instance
        
        result = self.health_checker.check_knowledge_graph_health()
        
        assert isinstance(result, HealthStatus)
        assert not result.is_healthy
        assert result.component == "knowledge_graph"
        assert "empty" in result.message.lower()
        assert result.details["node_count"] == 0
    
    @patch('src.services.health_checker.KnowledgeGraphRepository')
    def test_knowledge_graph_health_healthy(self, mock_kg_repo):
        """Test knowledge graph health check when healthy."""
        mock_repo_instance = Mock()
        mock_repo_instance.get_node_count.return_value = 50
        mock_repo_instance.get_relationship_count.return_value = 25
        mock_repo_instance.get_node_types_count.return_value = {"Document": 10, "Section": 40}
        mock_kg_repo.return_value = mock_repo_instance
        
        result = self.health_checker.check_knowledge_graph_health()
        
        assert isinstance(result, HealthStatus)
        assert result.is_healthy
        assert result.component == "knowledge_graph"
        assert "healthy" in result.message.lower()
        assert result.details["node_count"] == 50
        assert result.details["relationship_count"] == 25
        assert len(result.details["node_types"]) == 2
    
    def test_configuration_health_valid(self):
        """Test configuration health check with valid config."""
        result = self.health_checker.check_configuration_health()
        
        assert isinstance(result, HealthStatus)
        assert result.is_healthy
        assert result.component == "configuration"
        assert "valid" in result.message.lower()
        assert result.details["embedding_provider"] == "local"
        assert result.details["qa_provider"] == "gemini"
    
    def test_configuration_health_missing_api_key(self):
        """Test configuration health check with missing required API key."""
        # Set QA provider to gemini but remove API key
        self.config.gemini_api_key = ""
        
        result = self.health_checker.check_configuration_health()
        
        assert isinstance(result, HealthStatus)
        assert not result.is_healthy
        assert result.component == "configuration"
        assert "issues found" in result.message.lower()
        assert any("Gemini API key" in issue for issue in result.details["issues"])
    
    def test_configuration_health_invalid_file_size(self):
        """Test configuration health check with invalid file size."""
        self.config.max_file_size_mb = -1
        
        result = self.health_checker.check_configuration_health()
        
        assert isinstance(result, HealthStatus)
        assert not result.is_healthy
        assert result.component == "configuration"
        assert any("Invalid max file size" in issue for issue in result.details["issues"])
    
    @patch('pathlib.Path.exists')
    def test_file_system_health_missing_dirs(self, mock_exists):
        """Test file system health check with missing directories."""
        mock_exists.return_value = False
        
        result = self.health_checker.check_file_system_health()
        
        assert isinstance(result, HealthStatus)
        assert not result.is_healthy
        assert result.component == "file_system"
        assert "missing" in result.message.lower()
        assert len(result.details["missing_directories"]) > 0
    
    @patch('pathlib.Path.exists')
    def test_file_system_health_healthy(self, mock_exists):
        """Test file system health check when healthy."""
        # Mock that all required directories exist
        def mock_exists_side_effect(path_str):
            path = str(path_str)
            return any(req_dir in path for req_dir in ["data/documents", "data/database", "logs"])
        
        mock_exists.side_effect = mock_exists_side_effect
        
        result = self.health_checker.check_file_system_health()
        
        assert isinstance(result, HealthStatus)
        assert result.is_healthy
        assert result.component == "file_system"
        assert "healthy" in result.message.lower()
    
    @patch('src.services.health_checker.KnowledgeGraphRepository')
    def test_overall_health_all_healthy(self, mock_kg_repo):
        """Test overall health when all components are healthy."""
        # Setup mocks for healthy state
        mock_repo_instance = Mock()
        mock_repo_instance.get_node_count.return_value = 50
        mock_repo_instance.get_relationship_count.return_value = 25
        mock_repo_instance.get_node_types_count.return_value = {"Document": 10, "Section": 40}
        mock_kg_repo.return_value = mock_repo_instance
        
        # Create database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE documents (id TEXT PRIMARY KEY)")
            conn.execute("CREATE TABLE kg_nodes (id TEXT PRIMARY KEY)")
            conn.execute("CREATE TABLE kg_relationships (id TEXT PRIMARY KEY)")
        
        with patch('pathlib.Path.exists', return_value=True):
            health = self.health_checker.get_overall_health()
        
        assert health["overall_healthy"] is True
        assert health["healthy_components"] == health["total_components"]
        assert "checks" in health
        assert "timestamp" in health
        assert health["total_response_time_ms"] > 0
    
    @patch('src.services.health_checker.KnowledgeGraphRepository')
    def test_overall_health_some_unhealthy(self, mock_kg_repo):
        """Test overall health when some components are unhealthy."""
        # Setup mocks for unhealthy knowledge graph
        mock_repo_instance = Mock()
        mock_repo_instance.get_node_count.return_value = 0  # Empty KG
        mock_kg_repo.return_value = mock_repo_instance
        
        # Create database (healthy)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE documents (id TEXT PRIMARY KEY)")
            conn.execute("CREATE TABLE kg_nodes (id TEXT PRIMARY KEY)")
            conn.execute("CREATE TABLE kg_relationships (id TEXT PRIMARY KEY)")
        
        with patch('pathlib.Path.exists', return_value=True):
            health = self.health_checker.get_overall_health()
        
        assert health["overall_healthy"] is False
        assert health["healthy_components"] < health["total_components"]
        
        # Check that knowledge graph is marked as unhealthy
        kg_check = health["checks"]["knowledge_graph"]
        assert not kg_check["healthy"]
    
    @patch('src.services.health_checker.KnowledgeGraphRepository')
    def test_wait_for_healthy_state_success(self, mock_kg_repo):
        """Test waiting for healthy state - success case."""
        # Setup mocks for healthy state
        mock_repo_instance = Mock()
        mock_repo_instance.get_node_count.return_value = 50
        mock_repo_instance.get_relationship_count.return_value = 25
        mock_repo_instance.get_node_types_count.return_value = {"Document": 10, "Section": 40}
        mock_kg_repo.return_value = mock_repo_instance
        
        # Create database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE documents (id TEXT PRIMARY KEY)")
            conn.execute("CREATE TABLE kg_nodes (id TEXT PRIMARY KEY)")
            conn.execute("CREATE TABLE kg_relationships (id TEXT PRIMARY KEY)")
        
        with patch('pathlib.Path.exists', return_value=True):
            result = self.health_checker.wait_for_healthy_state(timeout_seconds=1, check_interval=0.1)
        
        assert result is True
    
    def test_wait_for_healthy_state_timeout(self):
        """Test waiting for healthy state - timeout case."""
        # Don't create database, so it will remain unhealthy
        result = self.health_checker.wait_for_healthy_state(timeout_seconds=0.5, check_interval=0.1)
        
        assert result is False