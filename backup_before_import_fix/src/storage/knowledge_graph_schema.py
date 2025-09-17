"""Knowledge graph database schema management."""

import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
try:
    from src.utils.logging_config import get_logger
except ImportError:
    from utils.logging_config import get_logger

logger = get_logger(__name__)


class KnowledgeGraphSchemaManager:
    """Manages knowledge graph database schema and migrations."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_knowledge_graph_tables(self):
        """Create all knowledge graph tables."""
        with self.get_connection() as conn:
            self._create_kg_tables(conn)
    
    def _create_kg_tables(self, conn: sqlite3.Connection):
        """Create knowledge graph tables."""
        
        # Patients table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                case_number TEXT,
                medical_record_number TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sections table (document sections)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sections (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                section_type TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                text_content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
            )
        """)
        
        # Claims table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                claim_number TEXT NOT NULL,
                injury_date DATETIME,
                body_parts TEXT,  -- JSON array
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
            )
        """)
        
        # Diagnoses table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS diagnoses (
                id TEXT PRIMARY KEY,
                icd_code TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT,
                certainty REAL DEFAULT 1.0,
                source_section_id TEXT,
                page_reference INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_section_id) REFERENCES sections (id) ON DELETE SET NULL
            )
        """)
        
        # Findings table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY,
                section_id TEXT NOT NULL,
                finding_type TEXT NOT NULL,
                description TEXT NOT NULL,
                page_reference INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (section_id) REFERENCES sections (id) ON DELETE CASCADE
            )
        """)
        
        # Imaging studies table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS imaging_studies (
                id TEXT PRIMARY KEY,
                study_type TEXT NOT NULL,
                study_date DATETIME,
                findings TEXT,
                interpretation TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Impairment ratings table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS impairment_ratings (
                id TEXT PRIMARY KEY,
                diagnosis_id TEXT NOT NULL,
                ama_table TEXT NOT NULL,
                percentage REAL NOT NULL,
                rationale TEXT NOT NULL,
                source_page INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (diagnosis_id) REFERENCES diagnoses (id) ON DELETE CASCADE
            )
        """)
        
        # Knowledge graph nodes table (generic)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_nodes (
                id TEXT PRIMARY KEY,
                node_type TEXT NOT NULL,
                properties TEXT,  -- JSON
                embeddings BLOB,  -- Serialized embeddings
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Knowledge graph relationships table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_relationships (
                id TEXT PRIMARY KEY,
                source_node_id TEXT NOT NULL,
                target_node_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                properties TEXT,  -- JSON
                confidence REAL DEFAULT 1.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_node_id) REFERENCES knowledge_nodes (id) ON DELETE CASCADE,
                FOREIGN KEY (target_node_id) REFERENCES knowledge_nodes (id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better performance
        self._create_kg_indexes(conn)
        
        conn.commit()
        logger.info("Created knowledge graph tables")
    
    def _create_kg_indexes(self, conn: sqlite3.Connection):
        """Create indexes for knowledge graph tables."""
        
        # Patient indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_patients_case_number ON patients (case_number)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_patients_mrn ON patients (medical_record_number)")
        
        # Section indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sections_document ON sections (document_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sections_type ON sections (section_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sections_page ON sections (page_number)")
        
        # Claim indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_claims_patient ON claims (patient_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_claims_number ON claims (claim_number)")
        
        # Diagnosis indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_diagnoses_icd ON diagnoses (icd_code)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_diagnoses_section ON diagnoses (source_section_id)")
        
        # Finding indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_section ON findings (section_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_type ON findings (finding_type)")
        
        # Impairment rating indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_impairment_diagnosis ON impairment_ratings (diagnosis_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_impairment_table ON impairment_ratings (ama_table)")
        
        # Knowledge graph indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kg_nodes_type ON knowledge_nodes (node_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kg_rel_source ON knowledge_relationships (source_node_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kg_rel_target ON knowledge_relationships (target_node_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kg_rel_type ON knowledge_relationships (relationship_type)")
    
    def migrate_existing_database(self):
        """Migrate existing database to include knowledge graph schema."""
        try:
            logger.info("Starting database migration to knowledge graph schema")
            
            # Check if migration is needed
            if self._is_migration_needed():
                # Create new tables
                self.create_knowledge_graph_tables()
                
                # Mark migration as complete
                self._mark_migration_complete()
                
                logger.info("Database migration completed successfully")
            else:
                logger.info("Database migration not needed - schema is up to date")
                
        except Exception as e:
            logger.error(f"Error during database migration: {e}")
            raise
    
    def _is_migration_needed(self) -> bool:
        """Check if migration is needed by looking for knowledge graph tables."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if patients table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='patients'
                """)
                
                return cursor.fetchone() is None
                
        except Exception as e:
            logger.error(f"Error checking migration status: {e}")
            return True
    
    def _mark_migration_complete(self):
        """Mark migration as complete by creating a migration record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create migrations table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        migration_name TEXT NOT NULL,
                        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Record this migration
                cursor.execute("""
                    INSERT INTO migrations (migration_name)
                    VALUES (?)
                """, ("knowledge_graph_schema_v1",))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error marking migration complete: {e}")
            raise
    
    def get_schema_version(self) -> str:
        """Get current schema version."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if migrations table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='migrations'
                """)
                
                if cursor.fetchone() is None:
                    return "legacy"
                
                # Get latest migration
                cursor.execute("""
                    SELECT migration_name FROM migrations 
                    ORDER BY applied_at DESC 
                    LIMIT 1
                """)
                
                result = cursor.fetchone()
                return result[0] if result else "legacy"
                
        except Exception as e:
            logger.error(f"Error getting schema version: {e}")
            return "unknown"
    
    def reset_knowledge_graph_tables(self):
        """Reset knowledge graph tables (for testing/development)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Drop knowledge graph tables in reverse dependency order
                tables_to_drop = [
                    'knowledge_relationships',
                    'knowledge_nodes',
                    'impairment_ratings',
                    'imaging_studies',
                    'findings',
                    'diagnoses',
                    'claims',
                    'sections',
                    'patients'
                ]
                
                for table in tables_to_drop:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                
                conn.commit()
                logger.info("Reset knowledge graph tables")
                
                # Recreate tables
                self.create_knowledge_graph_tables()
                
        except Exception as e:
            logger.error(f"Error resetting knowledge graph tables: {e}")
            raise
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get information about knowledge graph tables."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                info = {
                    'schema_version': self.get_schema_version(),
                    'tables': {}
                }
                
                # Get table counts
                kg_tables = [
                    'patients', 'sections', 'claims', 'diagnoses', 
                    'findings', 'imaging_studies', 'impairment_ratings',
                    'knowledge_nodes', 'knowledge_relationships'
                ]
                
                for table in kg_tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        info['tables'][table] = count
                    except sqlite3.OperationalError:
                        # Table doesn't exist
                        info['tables'][table] = 'not_exists'
                
                return info
                
        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            return {'error': str(e)}