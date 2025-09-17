"""Document storage service with SQLite backend for metadata and processing results."""

import json
import pickle
from datetime import datetime
from typing import Dict, Any, List, Optional
import sqlite3

from src.models.document import Document, ProcessingJob, QASession, QAInteraction
from src.storage.database import db_manager
from src.utils.logging_config import get_logger
from src.utils.error_handling import DatabaseError, StorageError, handle_errors

logger = get_logger(__name__)


class DocumentStorage:
    """Document storage service managing documents, processing jobs, and Q&A sessions."""
    
    def __init__(self):
        self.db_manager = db_manager
    
    # Document operations
    def create_document(self, document: Document) -> str:
        """Create a new document record."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                doc_data = document.to_dict()
                
                cursor.execute("""
                    INSERT INTO documents (
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
                
                conn.commit()
                logger.info(f"Created document record: {document.id}")
                return document.id
                
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            raise
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """Retrieve a document by ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM documents WHERE id = ?
                """, (document_id,))
                
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
            logger.error(f"Error retrieving document {document_id}: {e}")
            raise
    
    def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
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
                
                values.append(document_id)
                
                query = f"""
                    UPDATE documents 
                    SET {', '.join(set_clauses)}
                    WHERE id = ?
                """
                
                cursor.execute(query, values)
                conn.commit()
                
                updated = cursor.rowcount > 0
                if updated:
                    logger.info(f"Updated document: {document_id}")
                
                return updated
                
        except Exception as e:
            logger.error(f"Error updating document {document_id}: {e}")
            raise
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document and all related data."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete document (cascading will handle related records)
                cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
                conn.commit()
                
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Deleted document: {document_id}")
                
                return deleted
                
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            raise
    
    def list_documents(self, status_filter: Optional[str] = None) -> List[Document]:
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
    
    # Processing job operations
    def create_processing_job(self, job: ProcessingJob) -> str:
        """Create a new processing job record."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                job_data = job.to_dict()
                
                cursor.execute("""
                    INSERT INTO processing_jobs (
                        job_id, document_id, status, current_step,
                        progress_percentage, error_message, created_at, completed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_data['job_id'], job_data['document_id'], job_data['status'],
                    job_data['current_step'], job_data['progress_percentage'],
                    job_data['error_message'], job_data['created_at'], job_data['completed_at']
                ))
                
                conn.commit()
                logger.info(f"Created processing job: {job.job_id}")
                return job.job_id
                
        except Exception as e:
            logger.error(f"Error creating processing job: {e}")
            raise
    
    def get_processing_job(self, job_id: str) -> Optional[ProcessingJob]:
        """Retrieve a processing job by ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM processing_jobs WHERE job_id = ?
                """, (job_id,))
                
                row = cursor.fetchone()
                if row:
                    return ProcessingJob.from_dict(dict(row))
                
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving processing job {job_id}: {e}")
            raise
    
    def update_processing_job(self, job_id: str, status: Optional[str] = None, 
                            current_step: Optional[str] = None, 
                            progress_percentage: Optional[int] = None,
                            error_message: Optional[str] = None,
                            completed_at: Optional[datetime] = None) -> bool:
        """Update processing job status and progress."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                set_clauses = []
                values = []
                
                if status is not None:
                    set_clauses.append("status = ?")
                    values.append(status)
                
                if current_step is not None:
                    set_clauses.append("current_step = ?")
                    values.append(current_step)
                
                if progress_percentage is not None:
                    set_clauses.append("progress_percentage = ?")
                    values.append(progress_percentage)
                
                if error_message is not None:
                    set_clauses.append("error_message = ?")
                    values.append(error_message)
                
                if completed_at is not None:
                    set_clauses.append("completed_at = ?")
                    values.append(completed_at.isoformat())
                
                if not set_clauses:
                    return False
                
                values.append(job_id)
                
                query = f"""
                    UPDATE processing_jobs 
                    SET {', '.join(set_clauses)}
                    WHERE job_id = ?
                """
                
                cursor.execute(query, values)
                conn.commit()
                
                updated = cursor.rowcount > 0
                if updated:
                    logger.info(f"Updated processing job: {job_id}")
                
                return updated
                
        except Exception as e:
            logger.error(f"Error updating processing job {job_id}: {e}")
            raise
    
    def list_processing_jobs(self, document_id: Optional[str] = None) -> List[ProcessingJob]:
        """List processing jobs, optionally filtered by document ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                if document_id:
                    cursor.execute("""
                        SELECT * FROM processing_jobs 
                        WHERE document_id = ?
                        ORDER BY created_at DESC
                    """, (document_id,))
                else:
                    cursor.execute("""
                        SELECT * FROM processing_jobs 
                        ORDER BY created_at DESC
                    """)
                
                jobs = []
                for row in cursor.fetchall():
                    jobs.append(ProcessingJob.from_dict(dict(row)))
                
                return jobs
                
        except Exception as e:
            logger.error(f"Error listing processing jobs: {e}")
            raise
    
    # Q&A session operations
    def create_qa_session(self, session: QASession) -> str:
        """Create a new Q&A session."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                session_data = session.to_dict()
                
                cursor.execute("""
                    INSERT INTO qa_sessions (session_id, document_id, created_at)
                    VALUES (?, ?, ?)
                """, (
                    session_data['session_id'], session_data['document_id'], 
                    session_data['created_at']
                ))
                
                conn.commit()
                logger.info(f"Created Q&A session: {session.session_id}")
                return session.session_id
                
        except Exception as e:
            logger.error(f"Error creating Q&A session: {e}")
            raise
    
    def get_qa_session(self, session_id: str) -> Optional[QASession]:
        """Retrieve a Q&A session by ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get session
                cursor.execute("""
                    SELECT * FROM qa_sessions WHERE session_id = ?
                """, (session_id,))
                
                session_row = cursor.fetchone()
                if not session_row:
                    return None
                
                session = QASession.from_dict(dict(session_row))
                
                # Get interactions
                cursor.execute("""
                    SELECT * FROM qa_interactions 
                    WHERE session_id = ?
                    ORDER BY timestamp ASC
                """, (session_id,))
                
                for interaction_row in cursor.fetchall():
                    interaction_dict = dict(interaction_row)
                    sources = json.loads(interaction_dict['sources']) if interaction_dict['sources'] else []
                    
                    session.add_interaction(
                        question=interaction_dict['question'],
                        answer=interaction_dict['answer'],
                        sources=sources
                    )
                
                return session
                
        except Exception as e:
            logger.error(f"Error retrieving Q&A session {session_id}: {e}")
            raise
    
    def add_qa_interaction(self, session_id: str, question: str, answer: str, 
                          sources: Optional[List[str]] = None) -> int:
        """Add a Q&A interaction to a session."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO qa_interactions (session_id, question, answer, sources, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    session_id, question, answer, 
                    json.dumps(sources) if sources else None,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                interaction_id = cursor.lastrowid
                logger.info(f"Added Q&A interaction to session {session_id}")
                return interaction_id
                
        except Exception as e:
            logger.error(f"Error adding Q&A interaction: {e}")
            raise
    
    def list_qa_sessions(self, document_id: Optional[str] = None) -> List[QASession]:
        """List Q&A sessions, optionally filtered by document ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                if document_id:
                    cursor.execute("""
                        SELECT * FROM qa_sessions 
                        WHERE document_id = ?
                        ORDER BY created_at DESC
                    """, (document_id,))
                else:
                    cursor.execute("""
                        SELECT * FROM qa_sessions 
                        ORDER BY created_at DESC
                    """)
                
                sessions = []
                for row in cursor.fetchall():
                    sessions.append(QASession.from_dict(dict(row)))
                
                return sessions
                
        except Exception as e:
            logger.error(f"Error listing Q&A sessions: {e}")
            raise
    
    # Utility methods
    def get_document_with_embeddings(self, document_id: str) -> Optional[Document]:
        """Get document with embeddings for Q&A purposes."""
        document = self.get_document(document_id)
        if document and document.processing_status == 'completed':
            return document
        return None
    
    def search_documents_by_content(self, query: str, limit: int = 10) -> List[Document]:
        """Search documents by content (simple text search)."""
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
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Document counts by status
                cursor.execute("""
                    SELECT processing_status, COUNT(*) 
                    FROM documents 
                    GROUP BY processing_status
                """)
                stats['documents_by_status'] = dict(cursor.fetchall())
                
                # Total documents
                cursor.execute("SELECT COUNT(*) FROM documents")
                stats['total_documents'] = cursor.fetchone()[0]
                
                # Processing jobs by status
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM processing_jobs 
                    GROUP BY status
                """)
                stats['jobs_by_status'] = dict(cursor.fetchall())
                
                # Q&A sessions count
                cursor.execute("SELECT COUNT(*) FROM qa_sessions")
                stats['total_qa_sessions'] = cursor.fetchone()[0]
                
                # Q&A interactions count
                cursor.execute("SELECT COUNT(*) FROM qa_interactions")
                stats['total_qa_interactions'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            raise