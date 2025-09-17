"""
Comprehensive Health Check System for Production-Ready QME System.

This module provides detailed component health validation including:
- Database connectivity and performance checks
- API availability and response time monitoring
- Knowledge graph status and data integrity
- File system access and disk space monitoring
- Processing queue status and resource utilization
- Memory usage and system performance metrics

Designed for load balancer integration and automated monitoring.
"""

import sqlite3
import time
import logging
import psutil
import requests
import asyncio
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.storage.database import DatabaseManager
from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
from src.config.app_config import AppConfig

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Detailed health status result for a component."""
    component: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    response_time_ms: Optional[float] = None
    timestamp: float = field(default_factory=time.time)
    metrics: Dict[str, float] = field(default_factory=dict)
    
    @property
    def is_healthy(self) -> bool:
        """Check if component is healthy"""
        return self.status == HealthStatus.HEALTHY
    
    @property
    def is_critical(self) -> bool:
        """Check if component is in critical state"""
        return self.status == HealthStatus.CRITICAL


@dataclass
class SystemHealth:
    """Overall system health status"""
    overall_status: HealthStatus
    components: Dict[str, ComponentHealth]
    summary: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    
    @property
    def is_healthy(self) -> bool:
        """Check if entire system is healthy"""
        return self.overall_status == HealthStatus.HEALTHY
    
    @property
    def critical_components(self) -> List[str]:
        """Get list of components in critical state"""
        return [name for name, health in self.components.items() if health.is_critical]
    
    @property
    def healthy_components(self) -> List[str]:
        """Get list of healthy components"""
        return [name for name, health in self.components.items() if health.is_healthy]


class ComprehensiveHealthChecker:
    """
    Comprehensive health checker for production-ready QME system.
    
    Provides detailed health validation for all system components including:
    - Database connectivity and performance
    - API availability and response times
    - Knowledge graph status and integrity
    - File system access and disk space
    - Memory usage and system resources
    - Processing queue status
    """
    
    def __init__(self, config: AppConfig):
        """Initialize comprehensive health checker."""
        self.config = config
        self.db_manager = DatabaseManager(config.database_path)
        self.kg_repository = SQLiteKnowledgeGraphRepository(self.db_manager)
        
        # Health check configuration
        self.check_timeout = 30.0  # seconds
        self.api_timeout = 10.0    # seconds
        self.disk_warning_threshold = 85.0  # percent
        self.disk_critical_threshold = 95.0  # percent
        self.memory_warning_threshold = 80.0  # percent
        self.memory_critical_threshold = 90.0  # percent
        
        # Thread pool for concurrent health checks
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Health check registry
        self.health_checks: Dict[str, Callable[[], ComponentHealth]] = {
            "database": self.check_database_health,
            "knowledge_graph": self.check_knowledge_graph_health,
            "file_system": self.check_file_system_health,
            "system_resources": self.check_system_resources,
            "configuration": self.check_configuration_health,
            "api_endpoints": self.check_api_health,
            "processing_queue": self.check_processing_queue_health,
            "external_dependencies": self.check_external_dependencies
        }
    
    def check_database_health(self) -> ComponentHealth:
        """Comprehensive database health check with performance metrics."""
        start_time = time.time()
        
        try:
            db_path = Path(self.config.database_path)
            
            # Check database file existence and permissions
            if not db_path.exists():
                return ComponentHealth(
                    component="database",
                    status=HealthStatus.CRITICAL,
                    message="Database file does not exist",
                    details={"path": str(db_path)}
                )
            
            if not os.access(db_path, os.R_OK | os.W_OK):
                return ComponentHealth(
                    component="database",
                    status=HealthStatus.CRITICAL,
                    message="Database file permissions insufficient",
                    details={"path": str(db_path)}
                )
            
            # Get database file size
            db_size_mb = db_path.stat().st_size / (1024 * 1024)
            
            # Test database connection and performance
            connection_start = time.time()
            with sqlite3.connect(self.config.database_path, timeout=self.check_timeout) as conn:
                conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better performance
                cursor = conn.cursor()
                
                # Test basic connectivity
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                connection_time = (time.time() - connection_start) * 1000
                
                if result[0] != 1:
                    return ComponentHealth(
                        component="database",
                        status=HealthStatus.CRITICAL,
                        message="Database connectivity test failed"
                    )
                
                # Check database integrity
                integrity_start = time.time()
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()
                integrity_time = (time.time() - integrity_start) * 1000
                
                if integrity_result[0] != "ok":
                    return ComponentHealth(
                        component="database",
                        status=HealthStatus.CRITICAL,
                        message="Database integrity check failed",
                        details={"integrity_result": integrity_result[0]}
                    )
                
                # Check required tables and their row counts
                table_check_start = time.time()
                required_tables = ['documents', 'knowledge_nodes', 'knowledge_relationships']
                table_info = {}
                
                for table in required_tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        table_info[table] = count
                    except sqlite3.OperationalError:
                        return ComponentHealth(
                            component="database",
                            status=HealthStatus.CRITICAL,
                            message=f"Required table '{table}' does not exist"
                        )
                
                table_check_time = (time.time() - table_check_start) * 1000
                
                # Check database performance with a more complex query
                perf_start = time.time()
                cursor.execute("""
                    SELECT COUNT(*) as total_nodes,
                           COUNT(DISTINCT type) as node_types
                    FROM knowledge_nodes
                """)
                perf_result = cursor.fetchone()
                perf_time = (time.time() - perf_start) * 1000
                
                # Determine health status based on performance
                total_response_time = (time.time() - start_time) * 1000
                
                if total_response_time > 5000:  # 5 seconds
                    status = HealthStatus.WARNING
                    message = "Database responding slowly"
                elif total_response_time > 10000:  # 10 seconds
                    status = HealthStatus.CRITICAL
                    message = "Database response time critical"
                else:
                    status = HealthStatus.HEALTHY
                    message = "Database is healthy and performing well"
                
                return ComponentHealth(
                    component="database",
                    status=status,
                    message=message,
                    details={
                        "database_size_mb": round(db_size_mb, 2),
                        "table_counts": table_info,
                        "total_nodes": perf_result[0] if perf_result else 0,
                        "node_types": perf_result[1] if perf_result else 0,
                        "integrity_status": "ok"
                    },
                    response_time_ms=total_response_time,
                    metrics={
                        "connection_time_ms": connection_time,
                        "integrity_check_time_ms": integrity_time,
                        "table_check_time_ms": table_check_time,
                        "performance_query_time_ms": perf_time,
                        "database_size_mb": db_size_mb
                    }
                )
                
        except sqlite3.OperationalError as e:
            return ComponentHealth(
                component="database",
                status=HealthStatus.CRITICAL,
                message=f"Database operational error: {str(e)}",
                details={"error_type": "OperationalError", "error": str(e)}
            )
        except sqlite3.DatabaseError as e:
            return ComponentHealth(
                component="database",
                status=HealthStatus.CRITICAL,
                message=f"Database error: {str(e)}",
                details={"error_type": "DatabaseError", "error": str(e)}
            )
        except Exception as e:
            return ComponentHealth(
                component="database",
                status=HealthStatus.CRITICAL,
                message=f"Unexpected database error: {str(e)}",
                details={"error_type": type(e).__name__, "error": str(e)}
            )
    
    def check_system_resources(self) -> ComponentHealth:
        """Check system resource utilization (memory, disk, CPU)."""
        start_time = time.time()
        
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage for database directory
            db_path = Path(self.config.database_path).parent
            disk = psutil.disk_usage(str(db_path))
            disk_percent = (disk.used / disk.total) * 100
            
            # CPU usage (average over 1 second)
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Process-specific metrics
            current_process = psutil.Process()
            process_memory = current_process.memory_info()
            process_cpu = current_process.cpu_percent()
            
            # Determine status based on thresholds
            status = HealthStatus.HEALTHY
            issues = []
            
            if memory_percent >= self.memory_critical_threshold:
                status = HealthStatus.CRITICAL
                issues.append(f"Memory usage critical: {memory_percent:.1f}%")
            elif memory_percent >= self.memory_warning_threshold:
                status = HealthStatus.WARNING
                issues.append(f"Memory usage high: {memory_percent:.1f}%")
            
            if disk_percent >= self.disk_critical_threshold:
                status = HealthStatus.CRITICAL
                issues.append(f"Disk usage critical: {disk_percent:.1f}%")
            elif disk_percent >= self.disk_warning_threshold:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
                issues.append(f"Disk usage high: {disk_percent:.1f}%")
            
            message = "System resources healthy" if not issues else "; ".join(issues)
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                component="system_resources",
                status=status,
                message=message,
                details={
                    "memory": {
                        "total_gb": round(memory.total / (1024**3), 2),
                        "available_gb": round(memory.available / (1024**3), 2),
                        "used_percent": memory_percent
                    },
                    "disk": {
                        "total_gb": round(disk.total / (1024**3), 2),
                        "free_gb": round(disk.free / (1024**3), 2),
                        "used_percent": round(disk_percent, 1)
                    },
                    "cpu": {
                        "usage_percent": cpu_percent,
                        "core_count": psutil.cpu_count()
                    },
                    "process": {
                        "memory_mb": round(process_memory.rss / (1024**2), 2),
                        "cpu_percent": process_cpu
                    }
                },
                response_time_ms=response_time,
                metrics={
                    "memory_usage_percent": memory_percent,
                    "disk_usage_percent": disk_percent,
                    "cpu_usage_percent": cpu_percent,
                    "process_memory_mb": process_memory.rss / (1024**2)
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                component="system_resources",
                status=HealthStatus.CRITICAL,
                message=f"Failed to check system resources: {str(e)}",
                details={"error_type": type(e).__name__, "error": str(e)}
            )
    
    def check_api_health(self) -> ComponentHealth:
        """Check external API availability and response times."""
        start_time = time.time()
        
        try:
            api_checks = {}
            overall_status = HealthStatus.HEALTHY
            
            # Check OpenAI API if configured
            if hasattr(self.config, 'openai_api_key') and self.config.openai_api_key:
                openai_start = time.time()
                try:
                    # Simple API health check (just check if endpoint is reachable)
                    response = requests.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {self.config.openai_api_key}"},
                        timeout=self.api_timeout
                    )
                    openai_time = (time.time() - openai_start) * 1000
                    
                    if response.status_code == 200:
                        api_checks["openai"] = {
                            "status": "healthy",
                            "response_time_ms": openai_time,
                            "status_code": response.status_code
                        }
                    else:
                        api_checks["openai"] = {
                            "status": "unhealthy",
                            "response_time_ms": openai_time,
                            "status_code": response.status_code,
                            "error": f"HTTP {response.status_code}"
                        }
                        overall_status = HealthStatus.WARNING
                        
                except requests.RequestException as e:
                    api_checks["openai"] = {
                        "status": "error",
                        "error": str(e)
                    }
                    overall_status = HealthStatus.WARNING
            
            # Check Gemini API if configured
            if hasattr(self.config, 'gemini_api_key') and self.config.gemini_api_key:
                # Gemini doesn't have a simple health check endpoint
                api_checks["gemini"] = {
                    "status": "configured",
                    "note": "API key present but no health check endpoint available"
                }
            
            response_time = (time.time() - start_time) * 1000
            
            if not api_checks:
                return ComponentHealth(
                    component="api_endpoints",
                    status=HealthStatus.WARNING,
                    message="No external APIs configured",
                    details={"configured_apis": []},
                    response_time_ms=response_time
                )
            
            healthy_apis = len([api for api in api_checks.values() if api.get("status") == "healthy"])
            total_apis = len(api_checks)
            
            if healthy_apis == total_apis:
                message = f"All {total_apis} APIs healthy"
            else:
                message = f"{healthy_apis}/{total_apis} APIs healthy"
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.WARNING
            
            return ComponentHealth(
                component="api_endpoints",
                status=overall_status,
                message=message,
                details={"api_checks": api_checks},
                response_time_ms=response_time,
                metrics={
                    "healthy_apis": healthy_apis,
                    "total_apis": total_apis,
                    "health_ratio": healthy_apis / total_apis if total_apis > 0 else 0
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                component="api_endpoints",
                status=HealthStatus.CRITICAL,
                message=f"API health check failed: {str(e)}",
                details={"error_type": type(e).__name__, "error": str(e)}
            )
    
    def check_processing_queue_health(self) -> ComponentHealth:
        """Check processing queue status and capacity."""
        start_time = time.time()
        
        try:
            # For now, this is a placeholder since we don't have a formal queue system
            # In a production system, this would check Redis/RabbitMQ/etc.
            
            # Check if there are any stuck processing files
            processing_dir = Path("data/processing")
            if processing_dir.exists():
                processing_files = list(processing_dir.glob("*"))
                stuck_files = []
                
                # Check for files older than 1 hour (potentially stuck)
                current_time = time.time()
                for file_path in processing_files:
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > 3600:  # 1 hour
                        stuck_files.append({
                            "file": file_path.name,
                            "age_hours": round(file_age / 3600, 2)
                        })
                
                status = HealthStatus.HEALTHY
                message = "Processing queue healthy"
                
                if stuck_files:
                    status = HealthStatus.WARNING
                    message = f"{len(stuck_files)} potentially stuck files detected"
                
                details = {
                    "active_processing_files": len(processing_files),
                    "stuck_files": stuck_files
                }
            else:
                status = HealthStatus.HEALTHY
                message = "No processing queue directory (normal for current implementation)"
                details = {"queue_type": "in_memory"}
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                component="processing_queue",
                status=status,
                message=message,
                details=details,
                response_time_ms=response_time,
                metrics={
                    "queue_length": len(processing_files) if 'processing_files' in locals() else 0,
                    "stuck_items": len(stuck_files) if 'stuck_files' in locals() else 0
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                component="processing_queue",
                status=HealthStatus.WARNING,
                message=f"Queue health check failed: {str(e)}",
                details={"error_type": type(e).__name__, "error": str(e)}
            )
    
    def check_external_dependencies(self) -> ComponentHealth:
        """Check external service dependencies."""
        start_time = time.time()
        
        try:
            dependencies = {}
            overall_status = HealthStatus.HEALTHY
            
            # Check internet connectivity
            try:
                response = requests.get("https://www.google.com", timeout=5)
                dependencies["internet"] = {
                    "status": "available" if response.status_code == 200 else "limited",
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            except requests.RequestException:
                dependencies["internet"] = {"status": "unavailable"}
                overall_status = HealthStatus.WARNING
            
            # Check DNS resolution
            try:
                import socket
                socket.gethostbyname("api.openai.com")
                dependencies["dns"] = {"status": "working"}
            except socket.gaierror:
                dependencies["dns"] = {"status": "failing"}
                overall_status = HealthStatus.WARNING
            
            response_time = (time.time() - start_time) * 1000
            
            working_deps = len([dep for dep in dependencies.values() 
                              if dep.get("status") in ["available", "working"]])
            total_deps = len(dependencies)
            
            if working_deps == total_deps:
                message = "All external dependencies available"
            else:
                message = f"{working_deps}/{total_deps} dependencies available"
                overall_status = HealthStatus.WARNING
            
            return ComponentHealth(
                component="external_dependencies",
                status=overall_status,
                message=message,
                details={"dependencies": dependencies},
                response_time_ms=response_time,
                metrics={
                    "available_dependencies": working_deps,
                    "total_dependencies": total_deps
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                component="external_dependencies",
                status=HealthStatus.WARNING,
                message=f"Dependency check failed: {str(e)}",
                details={"error_type": type(e).__name__, "error": str(e)}
            )

    def check_knowledge_graph_health(self) -> ComponentHealth:
        """Comprehensive knowledge graph health check with data integrity validation."""
        start_time = time.time()
        
        try:
            # Check node count and types
            node_count = self.kg_repository.get_node_count()
            relationship_count = self.kg_repository.get_relationship_count()
            node_types = self.kg_repository.get_node_types_count()
            
            # Production thresholds (from requirements)
            min_nodes = 1000  # Minimum 1000 nodes for production
            min_relationships = 500  # Minimum 500 relationships
            min_node_types = 5  # At least 5 different node types
            
            # Determine status based on thresholds
            status = HealthStatus.HEALTHY
            issues = []
            
            if node_count == 0:
                status = HealthStatus.CRITICAL
                issues.append("Knowledge graph is empty")
            elif node_count < min_nodes:
                status = HealthStatus.WARNING
                issues.append(f"Node count ({node_count}) below production threshold ({min_nodes})")
            
            if relationship_count < min_relationships:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
                issues.append(f"Relationship count ({relationship_count}) below threshold ({min_relationships})")
            
            if len(node_types) < min_node_types:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
                issues.append(f"Node type diversity ({len(node_types)}) below threshold ({min_node_types})")
            
            # Check data integrity
            integrity_issues = []
            
            # Check for orphaned nodes (nodes without relationships)
            try:
                orphaned_nodes = self.kg_repository.get_orphaned_node_count()
                if orphaned_nodes > node_count * 0.1:  # More than 10% orphaned
                    integrity_issues.append(f"High orphaned node count: {orphaned_nodes}")
            except:
                pass  # Method might not exist in current implementation
            
            # Check for duplicate nodes
            try:
                duplicate_count = self.kg_repository.get_duplicate_node_count()
                if duplicate_count > 0:
                    integrity_issues.append(f"Duplicate nodes detected: {duplicate_count}")
            except:
                pass  # Method might not exist
            
            if integrity_issues:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
                issues.extend(integrity_issues)
            
            # Calculate graph density (relationships per node)
            graph_density = relationship_count / node_count if node_count > 0 else 0
            
            message = "Knowledge graph is healthy and well-populated"
            if issues:
                message = "; ".join(issues)
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                component="knowledge_graph",
                status=status,
                message=message,
                details={
                    "node_count": node_count,
                    "relationship_count": relationship_count,
                    "node_types": dict(node_types) if hasattr(node_types, 'items') else node_types,
                    "graph_density": round(graph_density, 2),
                    "thresholds": {
                        "min_nodes": min_nodes,
                        "min_relationships": min_relationships,
                        "min_node_types": min_node_types
                    },
                    "integrity_checks": {
                        "orphaned_nodes": orphaned_nodes if 'orphaned_nodes' in locals() else "unknown",
                        "duplicate_nodes": duplicate_count if 'duplicate_count' in locals() else "unknown"
                    }
                },
                response_time_ms=response_time,
                metrics={
                    "node_count": node_count,
                    "relationship_count": relationship_count,
                    "node_type_count": len(node_types) if hasattr(node_types, '__len__') else 0,
                    "graph_density": graph_density,
                    "completeness_score": min(node_count / min_nodes, 1.0) * 100
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                component="knowledge_graph",
                status=HealthStatus.CRITICAL,
                message=f"Knowledge graph check failed: {str(e)}",
                details={"error_type": type(e).__name__, "error": str(e)}
            )
    
    def check_file_system_health(self) -> ComponentHealth:
        """Comprehensive file system health check with disk space and permissions."""
        start_time = time.time()
        
        try:
            # Required directories with their purposes
            required_dirs = {
                "data/documents": "Document storage",
                "data/database": "Database files",
                "data/qme_references": "QME reference data",
                "logs": "Application logs",
                "results": "Generated results",
                "config": "Configuration files"
            }
            
            # Check directory existence and permissions
            dir_status = {}
            missing_dirs = []
            permission_issues = []
            
            for dir_path, purpose in required_dirs.items():
                path_obj = Path(dir_path)
                
                if not path_obj.exists():
                    missing_dirs.append({"path": dir_path, "purpose": purpose})
                    dir_status[dir_path] = "missing"
                else:
                    # Check permissions
                    readable = os.access(path_obj, os.R_OK)
                    writable = os.access(path_obj, os.W_OK)
                    
                    if not readable or not writable:
                        permission_issues.append({
                            "path": dir_path,
                            "readable": readable,
                            "writable": writable
                        })
                        dir_status[dir_path] = "permission_error"
                    else:
                        dir_status[dir_path] = "healthy"
            
            # Check canonical documents (optional but recommended)
            canonical_docs = {
                "AMAGuides 5th Edition.pdf": "AMA Guidelines reference",
                "QME-Study-Guide.pdf": "QME study guide",
                "Sample3.pdf": "Sample QME report"
            }
            
            doc_status = {}
            missing_docs = []
            
            for doc_path, purpose in canonical_docs.items():
                path_obj = Path(doc_path)
                
                if not path_obj.exists():
                    missing_docs.append({"path": doc_path, "purpose": purpose})
                    doc_status[doc_path] = "missing"
                else:
                    # Check file size (should not be empty)
                    file_size = path_obj.stat().st_size
                    if file_size == 0:
                        doc_status[doc_path] = "empty"
                    else:
                        doc_status[doc_path] = "available"
            
            # Check disk space for critical directories
            disk_usage = {}
            for dir_path in ["data", "logs", "results"]:
                if Path(dir_path).exists():
                    try:
                        usage = psutil.disk_usage(dir_path)
                        disk_usage[dir_path] = {
                            "total_gb": round(usage.total / (1024**3), 2),
                            "free_gb": round(usage.free / (1024**3), 2),
                            "used_percent": round((usage.used / usage.total) * 100, 1)
                        }
                    except:
                        disk_usage[dir_path] = "error"
            
            # Determine overall status
            status = HealthStatus.HEALTHY
            issues = []
            
            if missing_dirs:
                status = HealthStatus.CRITICAL
                issues.append(f"{len(missing_dirs)} required directories missing")
            
            if permission_issues:
                status = HealthStatus.CRITICAL
                issues.append(f"{len(permission_issues)} permission issues")
            
            if missing_docs:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
                issues.append(f"{len(missing_docs)} canonical documents missing")
            
            # Check for low disk space
            for dir_path, usage in disk_usage.items():
                if isinstance(usage, dict) and usage["used_percent"] > 90:
                    if status == HealthStatus.HEALTHY:
                        status = HealthStatus.WARNING
                    issues.append(f"Low disk space in {dir_path}: {usage['used_percent']}%")
            
            message = "File system healthy" if not issues else "; ".join(issues)
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                component="file_system",
                status=status,
                message=message,
                details={
                    "directory_status": dir_status,
                    "document_status": doc_status,
                    "missing_directories": missing_dirs,
                    "permission_issues": permission_issues,
                    "missing_documents": missing_docs,
                    "disk_usage": disk_usage
                },
                response_time_ms=response_time,
                metrics={
                    "healthy_directories": len([s for s in dir_status.values() if s == "healthy"]),
                    "total_directories": len(dir_status),
                    "available_documents": len([s for s in doc_status.values() if s == "available"]),
                    "total_documents": len(doc_status)
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                component="file_system",
                status=HealthStatus.CRITICAL,
                message=f"File system check failed: {str(e)}",
                details={"error_type": type(e).__name__, "error": str(e)}
            )
    
    def check_configuration_health(self) -> ComponentHealth:
        """Comprehensive configuration validation with security checks."""
        start_time = time.time()
        
        try:
            issues = []
            warnings = []
            config_details = {}
            
            # Core configuration checks
            if not hasattr(self.config, 'database_path') or not self.config.database_path:
                issues.append("Database path not configured")
            else:
                config_details["database_path"] = "configured"
            
            # API provider configuration
            providers_configured = []
            
            if hasattr(self.config, 'qa_provider'):
                config_details["qa_provider"] = self.config.qa_provider
                
                if self.config.qa_provider == "gemini":
                    if not hasattr(self.config, 'gemini_api_key') or not self.config.gemini_api_key:
                        issues.append("Gemini API key required but not configured")
                    else:
                        providers_configured.append("gemini")
                        
                elif self.config.qa_provider == "openai":
                    if not hasattr(self.config, 'openai_api_key') or not self.config.openai_api_key:
                        issues.append("OpenAI API key required but not configured")
                    else:
                        providers_configured.append("openai")
            else:
                warnings.append("No QA provider configured")
            
            # Embedding provider configuration
            if hasattr(self.config, 'embedding_provider'):
                config_details["embedding_provider"] = self.config.embedding_provider
                
                if self.config.embedding_provider == "openai":
                    if not hasattr(self.config, 'openai_api_key') or not self.config.openai_api_key:
                        issues.append("OpenAI API key required for embedding provider")
                    elif "openai" not in providers_configured:
                        providers_configured.append("openai")
            
            # File handling configuration
            if hasattr(self.config, 'max_file_size_mb'):
                if self.config.max_file_size_mb <= 0:
                    issues.append("Invalid max file size configuration")
                elif self.config.max_file_size_mb > 100:
                    warnings.append(f"Large max file size: {self.config.max_file_size_mb}MB")
                config_details["max_file_size_mb"] = self.config.max_file_size_mb
            else:
                warnings.append("Max file size not configured")
            
            if hasattr(self.config, 'allowed_file_types'):
                if not self.config.allowed_file_types:
                    issues.append("No allowed file types configured")
                else:
                    config_details["allowed_file_types"] = list(self.config.allowed_file_types)
            else:
                warnings.append("Allowed file types not configured")
            
            # Security configuration checks
            security_issues = []
            
            # Check for default/weak configurations
            if hasattr(self.config, 'secret_key'):
                if self.config.secret_key in ['default', 'changeme', '']:
                    security_issues.append("Default or weak secret key detected")
            
            # Check environment-specific settings
            env_checks = {
                "debug_mode": getattr(self.config, 'debug', False),
                "log_level": getattr(self.config, 'log_level', 'INFO'),
                "environment": getattr(self.config, 'environment', 'development')
            }
            
            if env_checks["debug_mode"] and env_checks["environment"] == "production":
                security_issues.append("Debug mode enabled in production environment")
            
            # Determine overall status
            status = HealthStatus.HEALTHY
            all_issues = issues + security_issues
            
            if all_issues:
                status = HealthStatus.CRITICAL
            elif warnings:
                status = HealthStatus.WARNING
            
            message_parts = []
            if all_issues:
                message_parts.append(f"{len(all_issues)} critical issues")
            if warnings:
                message_parts.append(f"{len(warnings)} warnings")
            
            if not message_parts:
                message = "Configuration is valid and secure"
            else:
                message = "; ".join(message_parts)
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                component="configuration",
                status=status,
                message=message,
                details={
                    "critical_issues": all_issues,
                    "warnings": warnings,
                    "configuration": config_details,
                    "providers_configured": providers_configured,
                    "environment_checks": env_checks,
                    "security_status": "secure" if not security_issues else "issues_detected"
                },
                response_time_ms=response_time,
                metrics={
                    "critical_issues": len(all_issues),
                    "warnings": len(warnings),
                    "providers_configured": len(providers_configured),
                    "config_completeness": (len(config_details) / 6) * 100  # Out of 6 key configs
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                component="configuration",
                status=HealthStatus.CRITICAL,
                message=f"Configuration check failed: {str(e)}",
                details={"error_type": type(e).__name__, "error": str(e)}
            )
    
    def run_health_checks(self, components: Optional[List[str]] = None) -> SystemHealth:
        """
        Run comprehensive health checks for specified components or all components.
        
        Args:
            components: List of component names to check, or None for all components
            
        Returns:
            SystemHealth object with detailed results
        """
        start_time = time.time()
        
        # Determine which checks to run
        checks_to_run = components or list(self.health_checks.keys())
        
        # Run health checks concurrently
        component_results = {}
        
        if len(checks_to_run) == 1:
            # Single check - run directly
            component_name = checks_to_run[0]
            if component_name in self.health_checks:
                component_results[component_name] = self.health_checks[component_name]()
        else:
            # Multiple checks - run concurrently
            future_to_component = {}
            
            for component_name in checks_to_run:
                if component_name in self.health_checks:
                    future = self.executor.submit(self.health_checks[component_name])
                    future_to_component[future] = component_name
            
            # Collect results with timeout
            for future in as_completed(future_to_component, timeout=self.check_timeout):
                component_name = future_to_component[future]
                try:
                    component_results[component_name] = future.result()
                except Exception as e:
                    logger.error(f"Health check failed for {component_name}: {e}")
                    component_results[component_name] = ComponentHealth(
                        component=component_name,
                        status=HealthStatus.CRITICAL,
                        message=f"Health check execution failed: {str(e)}",
                        details={"error_type": type(e).__name__, "error": str(e)}
                    )
        
        # Determine overall system status
        overall_status = self._determine_overall_status(component_results)
        
        # Calculate summary metrics
        total_response_time = (time.time() - start_time) * 1000
        
        summary = {
            "total_components": len(component_results),
            "healthy_components": len([c for c in component_results.values() if c.is_healthy]),
            "warning_components": len([c for c in component_results.values() if c.status == HealthStatus.WARNING]),
            "critical_components": len([c for c in component_results.values() if c.is_critical]),
            "total_response_time_ms": total_response_time,
            "check_timestamp": time.time()
        }
        
        return SystemHealth(
            overall_status=overall_status,
            components=component_results,
            summary=summary
        )
    
    def _determine_overall_status(self, component_results: Dict[str, ComponentHealth]) -> HealthStatus:
        """Determine overall system status based on component health."""
        if not component_results:
            return HealthStatus.UNKNOWN
        
        statuses = [component.status for component in component_results.values()]
        
        # If any component is critical, system is critical
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        
        # If any component has warnings, system has warnings
        if HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        
        # If all components are healthy, system is healthy
        if all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        
        return HealthStatus.UNKNOWN
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a quick health summary for monitoring dashboards."""
        health = self.run_health_checks()
        
        return {
            "status": health.overall_status.value,
            "healthy": health.is_healthy,
            "components": {
                name: {
                    "status": component.status.value,
                    "message": component.message,
                    "response_time_ms": component.response_time_ms
                }
                for name, component in health.components.items()
            },
            "summary": health.summary,
            "timestamp": health.timestamp
        }
    
    def get_health_metrics(self) -> Dict[str, float]:
        """Get health metrics for monitoring systems (Prometheus, etc.)."""
        health = self.run_health_checks()
        
        metrics = {}
        
        # Overall system metrics
        metrics["system_health_status"] = 1.0 if health.is_healthy else 0.0
        metrics["system_response_time_ms"] = health.summary["total_response_time_ms"]
        metrics["healthy_components_ratio"] = (
            health.summary["healthy_components"] / health.summary["total_components"]
            if health.summary["total_components"] > 0 else 0.0
        )
        
        # Component-specific metrics
        for name, component in health.components.items():
            prefix = f"component_{name}"
            metrics[f"{prefix}_health_status"] = 1.0 if component.is_healthy else 0.0
            
            if component.response_time_ms:
                metrics[f"{prefix}_response_time_ms"] = component.response_time_ms
            
            # Add component-specific metrics
            for metric_name, value in component.metrics.items():
                metrics[f"{prefix}_{metric_name}"] = value
        
        return metrics
    
    def create_health_endpoints(self) -> Dict[str, Callable]:
        """
        Create health check endpoints for load balancer integration.
        
        Returns:
            Dictionary of endpoint handlers
        """
        def liveness_probe():
            """Basic liveness check - is the service running?"""
            return {"status": "alive", "timestamp": time.time()}
        
        def readiness_probe():
            """Readiness check - is the service ready to handle requests?"""
            # Check critical components only
            critical_components = ["database", "configuration"]
            health = self.run_health_checks(critical_components)
            
            return {
                "status": "ready" if health.is_healthy else "not_ready",
                "components": {
                    name: component.status.value
                    for name, component in health.components.items()
                },
                "timestamp": time.time()
            }
        
        def health_check():
            """Full health check for monitoring systems"""
            return self.get_health_summary()
        
        def health_metrics():
            """Health metrics in Prometheus format"""
            metrics = self.get_health_metrics()
            
            # Convert to Prometheus format
            prometheus_output = []
            for metric_name, value in metrics.items():
                prometheus_output.append(f"qme_{metric_name} {value}")
            
            return "\n".join(prometheus_output)
        
        return {
            "/health/live": liveness_probe,
            "/health/ready": readiness_probe,
            "/health": health_check,
            "/health/metrics": health_metrics
        }
    
    def wait_for_healthy_state(
        self, 
        timeout_seconds: int = 60, 
        check_interval: int = 5,
        required_components: Optional[List[str]] = None
    ) -> bool:
        """
        Wait for system to reach healthy state within timeout.
        
        Args:
            timeout_seconds: Maximum time to wait
            check_interval: Time between health checks
            required_components: Specific components that must be healthy (None for all)
            
        Returns:
            True if system becomes healthy, False if timeout
        """
        start_time = time.time()
        components_to_check = required_components or list(self.health_checks.keys())
        
        logger.info(f"Waiting for healthy state (timeout: {timeout_seconds}s, components: {components_to_check})")
        
        while time.time() - start_time < timeout_seconds:
            health = self.run_health_checks(components_to_check)
            
            if health.is_healthy:
                logger.info(f"System reached healthy state in {time.time() - start_time:.1f}s")
                return True
            
            # Log current status
            healthy_count = len(health.healthy_components)
            total_count = len(health.components)
            critical_components = health.critical_components
            
            logger.info(
                f"System not healthy yet. Healthy: {healthy_count}/{total_count}, "
                f"Critical: {critical_components}"
            )
            
            time.sleep(check_interval)
        
        logger.warning(f"System did not reach healthy state within {timeout_seconds} seconds")
        
        # Log final status for debugging
        final_health = self.run_health_checks(components_to_check)
        for name, component in final_health.components.items():
            if not component.is_healthy:
                logger.warning(f"Component '{name}' unhealthy: {component.message}")
        
        return False
    
    def get_component_health(self, component_name: str) -> ComponentHealth:
        """Get health status for a specific component."""
        if component_name not in self.health_checks:
            return ComponentHealth(
                component=component_name,
                status=HealthStatus.UNKNOWN,
                message=f"Unknown component: {component_name}",
                details={"available_components": list(self.health_checks.keys())}
            )
        
        return self.health_checks[component_name]()
    
    def export_health_report(self, file_path: str, include_metrics: bool = True):
        """Export comprehensive health report to JSON file."""
        try:
            health = self.run_health_checks()
            
            report = {
                "report_metadata": {
                    "generated_at": time.time(),
                    "generated_by": "ComprehensiveHealthChecker",
                    "system_name": "QME System"
                },
                "overall_status": health.overall_status.value,
                "summary": health.summary,
                "components": {}
            }
            
            # Add detailed component information
            for name, component in health.components.items():
                component_data = {
                    "status": component.status.value,
                    "message": component.message,
                    "details": component.details,
                    "response_time_ms": component.response_time_ms,
                    "timestamp": component.timestamp
                }
                
                if include_metrics and component.metrics:
                    component_data["metrics"] = component.metrics
                
                report["components"][name] = component_data
            
            # Write report to file
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Health report exported to: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export health report: {e}", exc_info=True)
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


# Global health checker instance
_health_checker: Optional[ComprehensiveHealthChecker] = None


def get_health_checker(config: Optional[AppConfig] = None) -> ComprehensiveHealthChecker:
    """Get global health checker instance."""
    global _health_checker
    
    if _health_checker is None:
        if config is None:
            from src.config.app_config import AppConfig
            config = AppConfig()
        _health_checker = ComprehensiveHealthChecker(config)
    
    return _health_checker


def initialize_health_checker(config: AppConfig) -> ComprehensiveHealthChecker:
    """Initialize global health checker with configuration."""
    global _health_checker
    _health_checker = ComprehensiveHealthChecker(config)
    return _health_checker