"""
Health checker service for system monitoring and validation.

This module provides health checks for database connectivity, knowledge graph validation,
and overall system health monitoring.
"""

import sqlite3
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from ..storage.database import DatabaseManager
from ..repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
from ..config.app_config import AppConfig

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Health status result."""
    is_healthy: bool
    component: str
    message: str
    details: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[float] = None


class HealthChecker:
    """System health checker with database and knowledge graph validation."""
    
    def __init__(self, config: AppConfig):
        """Initialize health checker with configuration."""
        self.config = config
        self.db_manager = DatabaseManager(config.database_path)
        self.kg_repository = SQLiteKnowledgeGraphRepository(self.db_manager)
    
    def check_database_health(self) -> HealthStatus:
        """Check if database is accessible and functional."""
        start_time = time.time()
        
        try:
            # Check if database file exists
            db_path = Path(self.config.database_path)
            if not db_path.exists():
                return HealthStatus(
                    is_healthy=False,
                    component="database",
                    message="Database file does not exist",
                    details={"path": str(db_path)}
                )
            
            # Test database connection
            with sqlite3.connect(self.config.database_path) as conn:
                cursor = conn.cursor()
                
                # Test basic query
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                if result[0] != 1:
                    return HealthStatus(
                        is_healthy=False,
                        component="database",
                        message="Database query returned unexpected result"
                    )
                
                # Check if required tables exist
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN ('documents', 'knowledge_nodes', 'knowledge_relationships')
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ['documents', 'knowledge_nodes', 'knowledge_relationships']
                missing_tables = [table for table in required_tables if table not in tables]
                
                if missing_tables:
                    return HealthStatus(
                        is_healthy=False,
                        component="database",
                        message="Required tables are missing",
                        details={"missing_tables": missing_tables}
                    )
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthStatus(
                is_healthy=True,
                component="database",
                message="Database is healthy",
                details={"tables": tables},
                response_time_ms=response_time
            )
            
        except sqlite3.Error as e:
            return HealthStatus(
                is_healthy=False,
                component="database",
                message=f"Database error: {str(e)}",
                details={"error_type": type(e).__name__}
            )
        except Exception as e:
            return HealthStatus(
                is_healthy=False,
                component="database",
                message=f"Unexpected error: {str(e)}",
                details={"error_type": type(e).__name__}
            )
    
    def check_knowledge_graph_health(self) -> HealthStatus:
        """Check if knowledge graph has minimum required nodes and is functional."""
        start_time = time.time()
        
        try:
            # Check node count
            node_count = self.kg_repository.get_node_count()
            
            if node_count == 0:
                return HealthStatus(
                    is_healthy=False,
                    component="knowledge_graph",
                    message="Knowledge graph is empty - no nodes found",
                    details={"node_count": node_count}
                )
            
            # Check relationship count
            relationship_count = self.kg_repository.get_relationship_count()
            
            # Check for different node types
            node_types = self.kg_repository.get_node_types_count()
            
            # Minimum health criteria
            min_nodes = 10  # At least 10 nodes for basic functionality
            min_node_types = 2  # At least 2 different node types
            
            is_healthy = (
                node_count >= min_nodes and 
                len(node_types) >= min_node_types
            )
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthStatus(
                is_healthy=is_healthy,
                component="knowledge_graph",
                message="Knowledge graph is healthy" if is_healthy else "Knowledge graph below minimum thresholds",
                details={
                    "node_count": node_count,
                    "relationship_count": relationship_count,
                    "node_types": node_types,
                    "min_nodes_required": min_nodes,
                    "min_node_types_required": min_node_types
                },
                response_time_ms=response_time
            )
            
        except Exception as e:
            return HealthStatus(
                is_healthy=False,
                component="knowledge_graph",
                message=f"Knowledge graph check failed: {str(e)}",
                details={"error_type": type(e).__name__}
            )
    
    def check_file_system_health(self) -> HealthStatus:
        """Check if required directories and files are accessible."""
        start_time = time.time()
        
        try:
            required_dirs = [
                "data/documents",
                "data/database",
                "logs"
            ]
            
            missing_dirs = []
            for dir_path in required_dirs:
                if not Path(dir_path).exists():
                    missing_dirs.append(dir_path)
            
            # Check canonical documents
            canonical_docs = [
                "AMAGuides 5th Edition.pdf",
                "QME-Study-Guide.pdf",
                "Sample3.pdf"
            ]
            
            missing_docs = []
            for doc in canonical_docs:
                if not Path(doc).exists():
                    missing_docs.append(doc)
            
            response_time = (time.time() - start_time) * 1000
            
            # File system is healthy if directories exist (docs are optional)
            is_healthy = len(missing_dirs) == 0
            
            return HealthStatus(
                is_healthy=is_healthy,
                component="file_system",
                message="File system is healthy" if is_healthy else "Required directories are missing",
                details={
                    "missing_directories": missing_dirs,
                    "missing_canonical_docs": missing_docs
                },
                response_time_ms=response_time
            )
            
        except Exception as e:
            return HealthStatus(
                is_healthy=False,
                component="file_system",
                message=f"File system check failed: {str(e)}",
                details={"error_type": type(e).__name__}
            )
    
    def check_configuration_health(self) -> HealthStatus:
        """Check if configuration is valid and complete."""
        start_time = time.time()
        
        try:
            issues = []
            
            # Check database path
            if not self.config.database_path:
                issues.append("Database path not configured")
            
            # Check API keys based on provider settings
            if self.config.qa_provider == "gemini" and not self.config.gemini_api_key:
                issues.append("Gemini API key required but not configured")
            
            if self.config.qa_provider == "openai" and not self.config.openai_api_key:
                issues.append("OpenAI API key required but not configured")
            
            if self.config.embedding_provider == "openai" and not self.config.openai_api_key:
                issues.append("OpenAI API key required for embedding provider but not configured")
            
            # Check file size limits
            if self.config.max_file_size_mb <= 0:
                issues.append("Invalid max file size configuration")
            
            # Check allowed file types
            if not self.config.allowed_file_types:
                issues.append("No allowed file types configured")
            
            response_time = (time.time() - start_time) * 1000
            
            is_healthy = len(issues) == 0
            
            return HealthStatus(
                is_healthy=is_healthy,
                component="configuration",
                message="Configuration is valid" if is_healthy else "Configuration issues found",
                details={
                    "issues": issues,
                    "embedding_provider": self.config.embedding_provider,
                    "qa_provider": self.config.qa_provider,
                    "max_file_size_mb": self.config.max_file_size_mb
                },
                response_time_ms=response_time
            )
            
        except Exception as e:
            return HealthStatus(
                is_healthy=False,
                component="configuration",
                message=f"Configuration check failed: {str(e)}",
                details={"error_type": type(e).__name__}
            )
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get comprehensive health status of all system components."""
        start_time = time.time()
        
        # Run all health checks
        checks = {
            "database": self.check_database_health(),
            "knowledge_graph": self.check_knowledge_graph_health(),
            "file_system": self.check_file_system_health(),
            "configuration": self.check_configuration_health()
        }
        
        # Determine overall health
        all_healthy = all(check.is_healthy for check in checks.values())
        
        # Calculate total response time
        total_response_time = (time.time() - start_time) * 1000
        
        # Count healthy vs unhealthy components
        healthy_count = sum(1 for check in checks.values() if check.is_healthy)
        total_count = len(checks)
        
        return {
            "overall_healthy": all_healthy,
            "healthy_components": healthy_count,
            "total_components": total_count,
            "total_response_time_ms": total_response_time,
            "checks": {
                name: {
                    "healthy": check.is_healthy,
                    "message": check.message,
                    "details": check.details,
                    "response_time_ms": check.response_time_ms
                }
                for name, check in checks.items()
            },
            "timestamp": time.time()
        }
    
    def wait_for_healthy_state(self, timeout_seconds: int = 60, check_interval: int = 5) -> bool:
        """Wait for system to reach healthy state within timeout."""
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            health = self.get_overall_health()
            
            if health["overall_healthy"]:
                logger.info("System reached healthy state")
                return True
            
            logger.info(f"System not healthy yet. Healthy components: {health['healthy_components']}/{health['total_components']}")
            time.sleep(check_interval)
        
        logger.warning(f"System did not reach healthy state within {timeout_seconds} seconds")
        return False