#!/usr/bin/env python3
"""
Data migration script to convert existing processed documents to new knowledge graph schema.
This script ensures backward compatibility by migrating existing data without data loss.
"""

import sys
import os
import sqlite3
import json
import pickle
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.storage.database import db_manager
    from src.storage.knowledge_graph_schema import KnowledgeGraphSchemaManager
    from src.models.document import Document
    from src.models.knowledge_graph import KnowledgeNode, KnowledgeRelationship
    from src.utils.logging_config import get_logger
    from src.config.app_config import app_config
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you're running this script from the project root directory")
    sys.exit(1)

logger = get_logger(__name__)


class DataMigrationManager:
    """Manages migration of existing data to new knowledge graph schema."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize migration manager."""
        self.db_path = db_path or app_config.database_path
        self.kg_schema_manager = KnowledgeGraphSchemaManager(self.db_path)
        self.migration_log = []
    
    def run_migration(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Run complete data migration.
        
        Args:
            dry_run: If True, only analyze what would be migrated without making changes
            
        Returns:
            Migration results summary
        """
        logger.info(f"Starting data migration (dry_run={dry_run})")
        
        try:
            # Step 1: Ensure knowledge graph schema exists
            if not dry_run:
                self.kg_schema_manager.migrate_existing_database()
                logger.info("Knowledge graph schema migration completed")
            
            # Step 2: Analyze existing data
            analysis = self._analyze_existing_data()
            logger.info(f"Data analysis completed: {analysis}")
            
            if dry_run:
                return {
                    'success': True,
                    'dry_run': True,
                    'analysis': analysis,
                    'migration_log': self.migration_log
                }
            
            # Step 3: Migrate documents to knowledge graph nodes
            document_migration = self._migrate_documents_to_kg()
            logger.info(f"Document migration completed: {document_migration}")
            
            # Step 4: Create relationships between existing entities
            relationship_migration = self._create_document_relationships()
            logger.info(f"Relationship migration completed: {relationship_migration}")
            
            # Step 5: Migrate Q&A sessions to knowledge graph context
            qa_migration = self._migrate_qa_sessions()
            logger.info(f"Q&A session migration completed: {qa_migration}")
            
            # Step 6: Update document processing status
            status_update = self._update_processing_status()
            logger.info(f"Status update completed: {status_update}")
            
            migration_summary = {
                'success': True,
                'dry_run': False,
                'analysis': analysis,
                'document_migration': document_migration,
                'relationship_migration': relationship_migration,
                'qa_migration': qa_migration,
                'status_update': status_update,
                'migration_log': self.migration_log
            }
            
            logger.info("Data migration completed successfully")
            return migration_summary
            
        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'migration_log': self.migration_log
            }
    
    def _analyze_existing_data(self) -> Dict[str, Any]:
        """Analyze existing data to determine migration scope."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Check if tables exist
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN ('documents', 'processing_jobs', 'qa_sessions', 'qa_interactions')
                """)
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                analysis = {
                    'existing_tables': existing_tables,
                    'documents': 0,
                    'processed_documents': 0,
                    'processing_jobs': 0,
                    'qa_sessions': 0,
                    'qa_interactions': 0,
                    'documents_with_embeddings': 0,
                    'documents_with_analysis': 0,
                    'kg_tables_exist': False
                }
                
                # Count existing data
                if 'documents' in existing_tables:
                    cursor.execute("SELECT COUNT(*) FROM documents")
                    analysis['documents'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM documents WHERE processing_status = 'completed'")
                    analysis['processed_documents'] = cursor.fetchone()[0]
                    
                    # Check for embeddings column (may not exist in older schemas)
                    try:
                        cursor.execute("SELECT COUNT(*) FROM documents WHERE embeddings IS NOT NULL")
                        analysis['documents_with_embeddings'] = cursor.fetchone()[0]
                    except sqlite3.OperationalError:
                        analysis['documents_with_embeddings'] = 0
                    
                    try:
                        cursor.execute("SELECT COUNT(*) FROM documents WHERE analysis IS NOT NULL AND analysis != ''")
                        analysis['documents_with_analysis'] = cursor.fetchone()[0]
                    except sqlite3.OperationalError:
                        analysis['documents_with_analysis'] = 0
                
                if 'processing_jobs' in existing_tables:
                    cursor.execute("SELECT COUNT(*) FROM processing_jobs")
                    analysis['processing_jobs'] = cursor.fetchone()[0]
                
                if 'qa_sessions' in existing_tables:
                    cursor.execute("SELECT COUNT(*) FROM qa_sessions")
                    analysis['qa_sessions'] = cursor.fetchone()[0]
                
                if 'qa_interactions' in existing_tables:
                    cursor.execute("SELECT COUNT(*) FROM qa_interactions")
                    analysis['qa_interactions'] = cursor.fetchone()[0]
                
                # Check if knowledge graph tables exist
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN ('knowledge_nodes', 'knowledge_relationships')
                """)
                kg_tables = cursor.fetchall()
                analysis['kg_tables_exist'] = len(kg_tables) >= 2
                
                self.migration_log.append(f"Analysis completed: {analysis}")
                return analysis
                
        except Exception as e:
            logger.error(f"Error analyzing existing data: {e}")
            raise
    
    def _migrate_documents_to_kg(self) -> Dict[str, Any]:
        """Migrate existing documents to knowledge graph nodes."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get all processed documents
                cursor.execute("""
                    SELECT * FROM documents 
                    WHERE processing_status = 'completed'
                """)
                
                documents = cursor.fetchall()
                migrated_count = 0
                skipped_count = 0
                
                for doc_row in documents:
                    # Convert row to dict - doc_row is now a sqlite3.Row object
                    doc_dict = dict(doc_row)
                    
                    try:
                        # Check if document node already exists
                        cursor.execute("""
                            SELECT id FROM knowledge_nodes 
                            WHERE node_type = 'Document' AND properties LIKE ?
                        """, (f'%"source_doc_id": "{doc_dict["id"]}"%',))
                        
                        if cursor.fetchone():
                            skipped_count += 1
                            continue
                        
                        # Create document node
                        node_id = str(uuid.uuid4())
                        properties = {
                            'source_doc_id': doc_dict['id'],
                            'title': doc_dict['title'],
                            'file_type': doc_dict['file_type'],
                            'file_size': doc_dict['file_size'],
                            'document_type': doc_dict.get('document_type', 'unknown'),
                            'processing_status': doc_dict['processing_status'],
                            'upload_timestamp': doc_dict['upload_timestamp'],
                            'has_analysis': bool(doc_dict.get('analysis')),
                            'has_embeddings': bool(doc_dict.get('embeddings'))
                        }
                        
                        # Handle embeddings
                        embeddings = None
                        if doc_dict.get('embeddings'):
                            try:
                                embeddings = pickle.loads(doc_dict['embeddings'])
                                if isinstance(embeddings, list) and len(embeddings) > 0:
                                    embeddings = embeddings  # Keep as is
                                else:
                                    embeddings = None
                            except:
                                embeddings = None
                        
                        cursor.execute("""
                            INSERT INTO knowledge_nodes (id, node_type, properties, embeddings, created_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            node_id,
                            'Document',
                            json.dumps(properties),
                            pickle.dumps(embeddings) if embeddings else None,
                            datetime.now().isoformat()
                        ))
                        
                        # Create sections if analysis exists
                        if doc_dict.get('analysis'):
                            self._create_section_nodes(cursor, node_id, doc_dict)
                        
                        migrated_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error migrating document {doc_dict['id']}: {e}")
                        continue
                
                conn.commit()
                
                result = {
                    'migrated_documents': migrated_count,
                    'skipped_documents': skipped_count,
                    'total_processed': len(documents)
                }
                
                self.migration_log.append(f"Document migration: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Error migrating documents: {e}")
            raise
    
    def _create_section_nodes(self, cursor: sqlite3.Cursor, document_node_id: str, doc_dict: Dict[str, Any]):
        """Create section nodes from document analysis."""
        try:
            analysis = doc_dict.get('analysis', '')
            if not analysis:
                return
            
            # Try to parse analysis as JSON first
            try:
                analysis_data = json.loads(analysis)
                if isinstance(analysis_data, dict) and 'sections' in analysis_data:
                    sections = analysis_data['sections']
                else:
                    # Treat as single section
                    sections = [{'type': 'content', 'content': analysis}]
            except:
                # Treat as plain text
                sections = [{'type': 'content', 'content': analysis}]
            
            for i, section in enumerate(sections):
                section_id = str(uuid.uuid4())
                section_properties = {
                    'document_node_id': document_node_id,
                    'section_type': section.get('type', 'content'),
                    'section_index': i,
                    'content': section.get('content', ''),
                    'page_number': section.get('page', 1)
                }
                
                cursor.execute("""
                    INSERT INTO knowledge_nodes (id, node_type, properties, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    section_id,
                    'Section',
                    json.dumps(section_properties),
                    datetime.now().isoformat()
                ))
                
                # Create relationship between document and section
                rel_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO knowledge_relationships (id, source_node_id, target_node_id, relationship_type, properties, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    rel_id,
                    document_node_id,
                    section_id,
                    'HAS_SECTION',
                    json.dumps({'section_index': i}),
                    datetime.now().isoformat()
                ))
                
        except Exception as e:
            logger.error(f"Error creating section nodes: {e}")
    
    def _create_document_relationships(self) -> Dict[str, Any]:
        """Create relationships between existing entities."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get all document nodes
                cursor.execute("""
                    SELECT id, properties FROM knowledge_nodes 
                    WHERE node_type = 'Document'
                """)
                
                document_nodes = cursor.fetchall()
                relationships_created = 0
                
                for doc_id, properties_json in document_nodes:
                    try:
                        properties = json.loads(properties_json)
                        source_doc_id = properties.get('source_doc_id')
                        
                        if not source_doc_id:
                            continue
                        
                        # Create relationships with Q&A sessions
                        cursor.execute("""
                            SELECT session_id FROM qa_sessions 
                            WHERE document_id = ?
                        """, (source_doc_id,))
                        
                        qa_sessions = cursor.fetchall()
                        for (session_id,) in qa_sessions:
                            # Create QA session node if it doesn't exist
                            cursor.execute("""
                                SELECT id FROM knowledge_nodes 
                                WHERE node_type = 'QASession' AND properties LIKE ?
                            """, (f'%"session_id": "{session_id}"%',))
                            
                            if not cursor.fetchone():
                                qa_node_id = str(uuid.uuid4())
                                qa_properties = {
                                    'session_id': session_id,
                                    'document_id': source_doc_id
                                }
                                
                                cursor.execute("""
                                    INSERT INTO knowledge_nodes (id, node_type, properties, created_at)
                                    VALUES (?, ?, ?, ?)
                                """, (
                                    qa_node_id,
                                    'QASession',
                                    json.dumps(qa_properties),
                                    datetime.now().isoformat()
                                ))
                                
                                # Create relationship
                                rel_id = str(uuid.uuid4())
                                cursor.execute("""
                                    INSERT INTO knowledge_relationships (id, source_node_id, target_node_id, relationship_type, created_at)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (
                                    rel_id,
                                    doc_id,
                                    qa_node_id,
                                    'HAS_QA_SESSION',
                                    datetime.now().isoformat()
                                ))
                                
                                relationships_created += 1
                        
                    except Exception as e:
                        logger.error(f"Error creating relationships for document {doc_id}: {e}")
                        continue
                
                conn.commit()
                
                result = {
                    'relationships_created': relationships_created,
                    'documents_processed': len(document_nodes)
                }
                
                self.migration_log.append(f"Relationship migration: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Error creating relationships: {e}")
            raise
    
    def _migrate_qa_sessions(self) -> Dict[str, Any]:
        """Migrate Q&A sessions to include knowledge graph context."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get all Q&A sessions
                cursor.execute("""
                    SELECT s.session_id, s.document_id, COUNT(i.id) as interaction_count
                    FROM qa_sessions s
                    LEFT JOIN qa_interactions i ON s.session_id = i.session_id
                    GROUP BY s.session_id, s.document_id
                """)
                
                sessions = cursor.fetchall()
                migrated_sessions = 0
                
                for session_id, document_id, interaction_count in sessions:
                    try:
                        # Update session metadata to include KG context
                        cursor.execute("""
                            UPDATE qa_sessions 
                            SET created_at = COALESCE(created_at, ?)
                            WHERE session_id = ? AND created_at IS NULL
                        """, (datetime.now().isoformat(), session_id))
                        
                        # Add metadata about knowledge graph usage
                        # This could be expanded to track which KG nodes were used in responses
                        migrated_sessions += 1
                        
                    except Exception as e:
                        logger.error(f"Error migrating Q&A session {session_id}: {e}")
                        continue
                
                conn.commit()
                
                result = {
                    'migrated_sessions': migrated_sessions,
                    'total_sessions': len(sessions)
                }
                
                self.migration_log.append(f"Q&A session migration: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Error migrating Q&A sessions: {e}")
            raise
    
    def _update_processing_status(self) -> Dict[str, Any]:
        """Update document processing status to reflect knowledge graph integration."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Update documents that have been migrated to KG
                cursor.execute("""
                    UPDATE documents 
                    SET updated_at = ?
                    WHERE id IN (
                        SELECT JSON_EXTRACT(properties, '$.source_doc_id')
                        FROM knowledge_nodes 
                        WHERE node_type = 'Document'
                    )
                """, (datetime.now().isoformat(),))
                
                updated_count = cursor.rowcount
                conn.commit()
                
                result = {
                    'updated_documents': updated_count
                }
                
                self.migration_log.append(f"Status update: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Error updating processing status: {e}")
            raise
    
    def rollback_migration(self) -> Dict[str, Any]:
        """Rollback migration by removing knowledge graph data while preserving original data."""
        try:
            logger.info("Starting migration rollback")
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Remove knowledge graph data
                cursor.execute("DELETE FROM knowledge_relationships")
                relationships_removed = cursor.rowcount
                
                cursor.execute("DELETE FROM knowledge_nodes")
                nodes_removed = cursor.rowcount
                
                conn.commit()
                
                result = {
                    'success': True,
                    'nodes_removed': nodes_removed,
                    'relationships_removed': relationships_removed
                }
                
                logger.info(f"Migration rollback completed: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """Main migration script entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate existing data to knowledge graph schema')
    parser.add_argument('--dry-run', action='store_true', help='Analyze data without making changes')
    parser.add_argument('--rollback', action='store_true', help='Rollback migration')
    parser.add_argument('--db-path', help='Database path (optional)')
    
    args = parser.parse_args()
    
    try:
        migration_manager = DataMigrationManager(args.db_path)
        
        if args.rollback:
            result = migration_manager.rollback_migration()
        else:
            result = migration_manager.run_migration(dry_run=args.dry_run)
        
        print("\n" + "="*50)
        print("MIGRATION RESULTS")
        print("="*50)
        print(json.dumps(result, indent=2))
        
        if result.get('success'):
            print("\n✅ Migration completed successfully!")
        else:
            print(f"\n❌ Migration failed: {result.get('error')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Migration script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()