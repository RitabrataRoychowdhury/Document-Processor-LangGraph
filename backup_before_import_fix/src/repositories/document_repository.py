"""Document repository interface and SQLite implementation."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import sqlite3
import json
import pickle

try:
    from src.models.document import Document, ProcessingJob, QASession
    from src.storage.database import db_manager
    from src.utils.logging_config import get_logger
except ImportError:
    from models.document import Document, ProcessingJob, QASession
    from storage.database import db_manager
    from utils.logging_config import get_logger

logger = get_logger(__name__)


class DocumentRepository(ABC):
    """Abstract repository interface for document operations."""
    
    @abstractmethod
    def save(self, document: Document) -> str:
        """Save document and return ID."""
        pass
    
    @abstractmethod
    def find_by_id(self, doc_id: str) -> Optional[Document]:
        """Find document by ID."""
        pass
    
    @abstractmethod
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Document]:
        """Find documents matching criteria."""
        pass
    
    @abstractmethod
    def update(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """Update document fields."""
        pass
    
    @abstractmethod
    def delete(self, doc_id: str) -> bool:
        """Delete document."""
        pass
    
    @abstractmethod
    def list_all(self, status_filter: Optional[str] = None) -> List[Document]:
        """List all documents, optionally filtered by status."""
        pass
    
    @abstractmethod
    def search_by_content(self, query: str, limit: int = 10) -> List[Document]:
        """Search documents by content."""
        pass


class SQLiteDocumentRepository(DocumentRepository):
    """SQLite implementation of DocumentRepository wrapping existing document_storage.py."""
    
    def __init__(self, db_manager_instance=None):
        try:
            from src.storage.database import db_manager as default_db_manager
        except ImportError:
            from storage.database import db_manager as default_db_manager
        self.db_manager = db_manager_instance or default_db_manager
    
    def save(self, document: Document) -> str:
        """Save document and return ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                doc_data = document.to_dict()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO documents (
                        id, title, file_type, file_size, upload_timestamp,
                        processing_status, original_text, document_type,
                        extracted_info, analysis, summary, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_data['id'], doc_data['title'], doc_data['file_type'],
                    doc_data['file_size'], doc_data['upload_timestamp'],
                    doc_data['processing_status'], doc_data['original_text'],
                    doc_data['document_type'], doc_data['extracted_info'],
                    doc_data['analysis'], doc_data['summary'],
                    doc_data['created_at'], doc_data['updated_at']
                ))
                
                # Handle embeddings separately
                if document.embeddings:
                    cursor.execute("""
                        UPDATE documents SET embeddings = ? WHERE id = ?
                    """, (pickle.dumps(document.embeddings), document.id))
                
                conn.commit()
                logger.info(f"Saved document: {document.id}")
                return document.id
                
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            raise
    
    def find_by_id(self, doc_id: str) -> Optional[Document]:
        """Find document by ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM documents WHERE id = ?
                """, (doc_id,))
                
                row = cursor.fetchone()
                if row:
                    doc_dict = dict(row)
                    
                    # Handle embeddings separately if they exist
                    if doc_dict.get('embeddings'):
                        try:
                            doc_dict['embeddings'] = pickle.loads(doc_dict['embeddings'])
                        except:
                            doc_dict['embeddings'] = None
                    
                    return Document.from_dict(doc_dict)
                
                return None
                
        except Exception as e:
            logger.error(f"Error finding document {doc_id}: {e}")
            raise
    
    def find_by_file_path(self, file_path: str) -> Optional[Document]:
        """Find document by file path (using title as proxy)."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Use title field as proxy for file path
                file_name = Path(file_path).name
                cursor.execute("""
                    SELECT * FROM documents 
                    WHERE title = ? OR title LIKE ?
                """, (file_name, f"%{file_name}%"))
                
                row = cursor.fetchone()
                if row:
                    doc_dict = dict(row)
                    return Document.from_dict(doc_dict)
                
                return None
                
        except Exception as e:
            logger.error(f"Error finding document by file path {file_path}: {e}")
            return None

    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Document]:
        """Find documents matching criteria."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic WHERE clause
                where_clauses = []
                values = []
                
                for key, value in criteria.items():
                    if key in ['processing_status', 'file_type', 'document_type']:
                        where_clauses.append(f"{key} = ?")
                        values.append(value)
                    elif key == 'title_contains':
                        where_clauses.append("title LIKE ?")
                        values.append(f"%{value}%")
                    elif key == 'created_after':
                        where_clauses.append("created_at > ?")
                        values.append(value.isoformat() if isinstance(value, datetime) else value)
                    elif key == 'created_before':
                        where_clauses.append("created_at < ?")
                        values.append(value.isoformat() if isinstance(value, datetime) else value)
                
                where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                query = f"""
                    SELECT * FROM documents 
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                """
                
                cursor.execute(query, values)
                
                documents = []
                for row in cursor.fetchall():
                    doc_dict = dict(row)
                    
                    # Handle embeddings separately if they exist
                    if doc_dict.get('embeddings'):
                        try:
                            doc_dict['embeddings'] = pickle.loads(doc_dict['embeddings'])
                        except:
                            doc_dict['embeddings'] = None
                    
                    documents.append(Document.from_dict(doc_dict))
                
                return documents
                
        except Exception as e:
            logger.error(f"Error finding documents by criteria: {e}")
            raise
    
    def update(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """Update document fields."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                set_clauses = []
                values = []
                
                for key, value in updates.items():
                    if key == 'extracted_info' and isinstance(value, dict):
                        set_clauses.append(f"{key} = ?")
                        values.append(json.dumps(value))
                    elif key == 'embeddings' and isinstance(value, list):
                        set_clauses.append(f"{key} = ?")
                        values.append(pickle.dumps(value))
                    elif key in ['created_at', 'updated_at', 'upload_timestamp'] and isinstance(value, datetime):
                        set_clauses.append(f"{key} = ?")
                        values.append(value.isoformat())
                    else:
                        set_clauses.append(f"{key} = ?")
                        values.append(value)
                
                if not set_clauses:
                    return False
                
                # Always update the updated_at timestamp
                if 'updated_at' not in updates:
                    set_clauses.append("updated_at = ?")
                    values.append(datetime.now().isoformat())
                
                values.append(doc_id)
                
                query = f"""
                    UPDATE documents 
                    SET {', '.join(set_clauses)}
                    WHERE id = ?
                """
                
                cursor.execute(query, values)
                conn.commit()
                
                updated = cursor.rowcount > 0
                if updated:
                    logger.info(f"Updated document: {doc_id}")
                
                return updated
                
        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {e}")
            raise
    
    def delete(self, doc_id: str) -> bool:
        """Delete document."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete document (cascading will handle related records)
                cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                conn.commit()
                
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Deleted document: {doc_id}")
                
                return deleted
                
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            raise
    
    def list_all(self, status_filter: Optional[str] = None) -> List[Document]:
        """List all documents, optionally filtered by status."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                if status_filter:
                    cursor.execute("""
                        SELECT * FROM documents 
                        WHERE processing_status = ?
                        ORDER BY created_at DESC
                    """, (status_filter,))
                else:
                    cursor.execute("""
                        SELECT * FROM documents 
                        ORDER BY created_at DESC
                    """)
                
                documents = []
                for row in cursor.fetchall():
                    doc_dict = dict(row)
                    
                    # Handle embeddings separately if they exist
                    if doc_dict.get('embeddings'):
                        try:
                            doc_dict['embeddings'] = pickle.loads(doc_dict['embeddings'])
                        except:
                            doc_dict['embeddings'] = None
                    
                    documents.append(Document.from_dict(doc_dict))
                
                return documents
                
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            raise
    
    def search_by_content(self, query: str, limit: int = 10) -> List[Document]:
        """Search documents by content."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Simple text search in original_text, analysis, and summary
                cursor.execute("""
                    SELECT * FROM documents 
                    WHERE (original_text LIKE ? OR analysis LIKE ? OR summary LIKE ?)
                    AND processing_status = 'completed'
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (f'%{query}%', f'%{query}%', f'%{query}%', limit))
                
                documents = []
                for row in cursor.fetchall():
                    doc_dict = dict(row)
                    
                    # Handle embeddings separately if they exist
                    if doc_dict.get('embeddings'):
                        try:
                            doc_dict['embeddings'] = pickle.loads(doc_dict['embeddings'])
                        except:
                            doc_dict['embeddings'] = None
                    
                    documents.append(Document.from_dict(doc_dict))
                
                return documents
                
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            raise