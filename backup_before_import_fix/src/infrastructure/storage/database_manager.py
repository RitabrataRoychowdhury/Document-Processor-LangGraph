"""
Enhanced Database Manager with Connection Pooling and Error Handling.

This module provides robust database connection management with connection pooling,
proper error handling, and graceful degradation for the QME system.
"""

import sqlite3
import threading
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any, Generator
from dataclasses import dataclass
from pathlib import Path
from queue import Queue, Empty
import logging

from src.core.exceptions import (
    StorageError, DatabaseConnectionError, ConfigurationError
)
from src.infrastructure.monitoring.structured_logger import storage_logger
from src.infrastructure.monitoring.circuit_breaker import circuit_breaker_registry
from src.infrastructure.monitoring.retry_handler import with_retry, BackoffStrategy


@dataclass
class DatabaseConfig:
    """Configuration for database connections."""
    database_path: str
    max_connections: int = 10
    connection_timeout: int = 30
    retry_attempts: int = 3
    enable_wal_mode: bool = True
    enable_foreign_keys: bool = True
    busy_timeout: int = 30000  # milliseconds
    journal_mode: str = "WAL"
    synchronous: str = "NORMAL"


class DatabaseConnection:
    """Wrapper for database connection with metadata."""
    
    def __init__(self, connection: sqlite3.Connection, created_at: float):
        self.connection = connection
        self.created_at = created_at
        self.last_used = created_at
        self.in_use = False
        self.transaction_active = False
    
    def mark_used(self):
        """Mark connection as recently used."""
        self.last_used = time.time()
    
    def is_expired(self, max_age: int = 3600) -> bool:
        """Check if connection is expired."""
        return (time.time() - self.created_at) > max_age


class DatabaseConnectionPool:
    """Thread-safe database connection pool."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connections: Queue[DatabaseConnection] = Queue(maxsize=config.max_connections)
        self.active_connections: Dict[int, DatabaseConnection] = {}
        self.lock = threading.RLock()
        self.total_connections = 0
        
        # Initialize pool with minimum connections
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool with minimum connections."""
        try:
            # Create initial connections
            for _ in range(min(2, self.config.max_connections)):
                conn = self._create_connection()
                if conn:
                    self.connections.put(conn)
                    self.total_connections += 1
        except Exception as e:
            storage_logger.error(
                "Failed to initialize database connection pool",
                error=e,
                extra_data={"database_path": self.config.database_path}
            )
    
    def _create_connection(self) -> Optional[DatabaseConnection]:
        """Create a new database connection."""
        try:
            # Check if database file exists, create if needed
            db_path = Path(self.config.database_path)
            if not db_path.parent.exists():
                db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create connection
            conn = sqlite3.connect(
                self.config.database_path,
                timeout=self.config.connection_timeout,
                check_same_thread=False
            )
            
            # Configure connection
            conn.execute(f"PRAGMA busy_timeout = {self.config.busy_timeout}")
            conn.execute(f"PRAGMA journal_mode = {self.config.journal_mode}")
            conn.execute(f"PRAGMA synchronous = {self.config.synchronous}")
            
            if self.config.enable_foreign_keys:
                conn.execute("PRAGMA foreign_keys = ON")
            
            # Set row factory for better data access
            conn.row_factory = sqlite3.Row
            
            storage_logger.debug(
                "Created new database connection",
                extra_data={
                    "database_path": self.config.database_path,
                    "total_connections": self.total_connections + 1
                }
            )
            
            return DatabaseConnection(conn, time.time())
            
        except Exception as e:
            storage_logger.error(
                "Failed to create database connection",
                error=e,
                extra_data={"database_path": self.config.database_path}
            )
            return None
    
    def get_connection(self) -> Optional[DatabaseConnection]:
        """Get connection from pool."""
        with self.lock:
            try:
                # Try to get existing connection
                db_conn = self.connections.get_nowait()
                
                # Check if connection is still valid
                if self._is_connection_valid(db_conn):
                    db_conn.mark_used()
                    db_conn.in_use = True
                    thread_id = threading.get_ident()
                    self.active_connections[thread_id] = db_conn
                    return db_conn
                else:
                    # Connection is invalid, close it
                    self._close_connection(db_conn)
                    self.total_connections -= 1
                    
            except Empty:
                pass
            
            # Create new connection if pool allows
            if self.total_connections < self.config.max_connections:
                db_conn = self._create_connection()
                if db_conn:
                    db_conn.in_use = True
                    thread_id = threading.get_ident()
                    self.active_connections[thread_id] = db_conn
                    self.total_connections += 1
                    return db_conn
            
            storage_logger.warning(
                "No database connections available",
                extra_data={
                    "total_connections": self.total_connections,
                    "max_connections": self.config.max_connections
                }
            )
            return None
    
    def return_connection(self, db_conn: DatabaseConnection):
        """Return connection to pool."""
        with self.lock:
            thread_id = threading.get_ident()
            
            if thread_id in self.active_connections:
                del self.active_connections[thread_id]
            
            db_conn.in_use = False
            db_conn.transaction_active = False
            
            # Check if connection is still valid and not expired
            if self._is_connection_valid(db_conn) and not db_conn.is_expired():
                try:
                    self.connections.put_nowait(db_conn)
                except:
                    # Pool is full, close connection
                    self._close_connection(db_conn)
                    self.total_connections -= 1
            else:
                # Connection is invalid or expired
                self._close_connection(db_conn)
                self.total_connections -= 1
    
    def _is_connection_valid(self, db_conn: DatabaseConnection) -> bool:
        """Check if connection is valid."""
        try:
            db_conn.connection.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    def _close_connection(self, db_conn: DatabaseConnection):
        """Close database connection."""
        try:
            db_conn.connection.close()
        except Exception as e:
            storage_logger.warning(
                "Error closing database connection",
                error=e
            )
    
    def close_all(self):
        """Close all connections in pool."""
        with self.lock:
            # Close active connections
            for db_conn in self.active_connections.values():
                self._close_connection(db_conn)
            self.active_connections.clear()
            
            # Close pooled connections
            while not self.connections.empty():
                try:
                    db_conn = self.connections.get_nowait()
                    self._close_connection(db_conn)
                except Empty:
                    break
            
            self.total_connections = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        with self.lock:
            return {
                "total_connections": self.total_connections,
                "active_connections": len(self.active_connections),
                "pooled_connections": self.connections.qsize(),
                "max_connections": self.config.max_connections
            }


class EnhancedDatabaseManager:
    """Enhanced database manager with connection pooling and error handling."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection_pool = DatabaseConnectionPool(config)
        self.circuit_breaker = circuit_breaker_registry.get_breaker("database")
        
        storage_logger.info(
            "Initialized EnhancedDatabaseManager",
            extra_data={
                "database_path": config.database_path,
                "max_connections": config.max_connections,
                "connection_timeout": config.connection_timeout
            }
        )
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get database connection with automatic cleanup."""
        db_conn = None
        try:
            db_conn = self.connection_pool.get_connection()
            if not db_conn:
                raise DatabaseConnectionError(
                    "Unable to obtain database connection",
                    context={"database_path": self.config.database_path}
                )
            
            yield db_conn.connection
            
        except Exception as e:
            storage_logger.error(
                "Database operation failed",
                error=e,
                extra_data={"database_path": self.config.database_path}
            )
            
            # Rollback transaction if active
            if db_conn and db_conn.transaction_active:
                try:
                    db_conn.connection.rollback()
                    db_conn.transaction_active = False
                except Exception as rollback_error:
                    storage_logger.error(
                        "Failed to rollback transaction",
                        error=rollback_error
                    )
            
            raise
        finally:
            if db_conn:
                self.connection_pool.return_connection(db_conn)
    
    @with_retry(
        max_attempts=3,
        base_delay=0.5,
        backoff_strategy=BackoffStrategy.EXPONENTIAL
    )
    async def execute_query(self, query: str, params: tuple = ()) -> list:
        """Execute query with retry logic."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            raise StorageError(
                f"Query execution failed: {str(e)}",
                context={"query": query[:100], "params": str(params)[:100]},
                cause=e
            )
    
    @with_retry(
        max_attempts=3,
        base_delay=0.5,
        backoff_strategy=BackoffStrategy.EXPONENTIAL
    )
    async def execute_transaction(self, operations: list) -> bool:
        """Execute multiple operations in a transaction."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                try:
                    conn.execute("BEGIN TRANSACTION")
                    
                    for operation in operations:
                        query = operation.get('query')
                        params = operation.get('params', ())
                        cursor.execute(query, params)
                    
                    conn.commit()
                    return True
                    
                except Exception as e:
                    conn.rollback()
                    raise e
                    
        except Exception as e:
            raise StorageError(
                f"Transaction execution failed: {str(e)}",
                context={"operations_count": len(operations)},
                cause=e
            )
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                pool_stats = self.connection_pool.get_stats()
                
                return {
                    "status": "healthy",
                    "database_accessible": True,
                    "test_query_result": result[0] if result else None,
                    "connection_pool": pool_stats
                }
                
        except Exception as e:
            storage_logger.error(
                "Database health check failed",
                error=e,
                extra_data={"database_path": self.config.database_path}
            )
            
            return {
                "status": "unhealthy",
                "database_accessible": False,
                "error": str(e),
                "connection_pool": self.connection_pool.get_stats()
            }
    
    def close(self):
        """Close database manager and all connections."""
        storage_logger.info("Closing database manager")
        self.connection_pool.close_all()


# Factory function for creating database manager
def create_database_manager(database_path: str, **config_kwargs) -> EnhancedDatabaseManager:
    """Factory function to create enhanced database manager."""
    config = DatabaseConfig(database_path=database_path, **config_kwargs)
    return EnhancedDatabaseManager(config)