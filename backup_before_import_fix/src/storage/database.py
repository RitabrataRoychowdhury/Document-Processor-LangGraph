"""Database setup and schema management for the Document Q&A System."""

import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
import sys
import os as os_module

# Add the src directory to path to import config.py
src_dir = os_module.path.dirname(os_module.path.dirname(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import from the config.py file (not the config directory)
try:
    from config import config
except ImportError:
    # Fallback: create a minimal config for testing
    class MinimalConfig:
        DATABASE_PATH = 'data/database/documents.db'
    
    config = MinimalConfig()

try:
    from src.storage.knowledge_graph_schema import KnowledgeGraphSchemaManager
except ImportError:
    from storage.knowledge_graph_schema import KnowledgeGraphSchemaManager


class DatabaseManager:
    """Manages database connections and schema setup."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager."""
        self.db_path = db_path or config.DATABASE_PATH
        self._ensure_database_directory()
        self._initialize_database()
        self._initialize_knowledge_graph_schema()
    
    def _ensure_database_directory(self):
        """Ensure database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _initialize_database(self):
        """Initialize database with required tables."""
        with self.get_connection() as conn:
            self._create_tables(conn)
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _create_tables(self, conn: sqlite3.Connection):
        """Create all required tables."""
        
        # Documents table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                upload_timestamp DATETIME NOT NULL,
                processing_status TEXT NOT NULL DEFAULT 'pending',
                original_text TEXT,
                document_type TEXT,
                extracted_info TEXT,  -- JSON string
                analysis TEXT,
                summary TEXT,
                embeddings BLOB,  -- Serialized embeddings
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Processing jobs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processing_jobs (
                job_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                current_step TEXT,
                progress_percentage INTEGER DEFAULT 0,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
            )
        """)
        
        # Q&A sessions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS qa_sessions (
                session_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
            )
        """)
        
        # Q&A interactions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS qa_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                sources TEXT,  -- JSON string of source references
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES qa_sessions (session_id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents (processing_status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_processing_jobs_document ON processing_jobs (document_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_qa_sessions_document ON qa_sessions (document_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_qa_interactions_session ON qa_interactions (session_id)")
        
        conn.commit()
    
    def _initialize_knowledge_graph_schema(self):
        """Initialize knowledge graph schema if needed."""
        try:
            kg_schema_manager = KnowledgeGraphSchemaManager(self.db_path)
            kg_schema_manager.migrate_existing_database()
        except Exception as e:
            # Log error but don't fail initialization
            print(f"Warning: Could not initialize knowledge graph schema: {e}")
    
    def reset_database(self):
        """Reset database by dropping and recreating all tables."""
        with self.get_connection() as conn:
            # Drop all tables
            conn.execute("DROP TABLE IF EXISTS qa_interactions")
            conn.execute("DROP TABLE IF EXISTS qa_sessions")
            conn.execute("DROP TABLE IF EXISTS processing_jobs")
            conn.execute("DROP TABLE IF EXISTS documents")
            
            # Recreate tables
            self._create_tables(conn)
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get table counts
            tables_info = {}
            for table in ['documents', 'processing_jobs', 'qa_sessions', 'qa_interactions']:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                tables_info[table] = cursor.fetchone()[0]
            
            # Get database file size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            return {
                'database_path': self.db_path,
                'database_size_bytes': db_size,
                'tables': tables_info,
                'created_at': datetime.now().isoformat()
            }


# Global database manager instance
db_manager = DatabaseManager()