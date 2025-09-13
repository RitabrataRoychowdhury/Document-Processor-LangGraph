"""
Simple document processor for processing documents into the knowledge base.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from ..storage.database import DatabaseManager
from ..config.app_config import AppConfig

logger = logging.getLogger(__name__)


def process_document_simple(file_path: str) -> bool:
    """
    Simple document processor that adds a document to the system.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        
        # Get file info
        file_path_obj = Path(file_path)
        file_name = file_path_obj.name
        file_size = file_path_obj.stat().st_size
        file_ext = file_path_obj.suffix.lower()
        
        # Check if file type is supported
        supported_types = ['.pdf', '.docx', '.txt']
        if file_ext not in supported_types:
            logger.error(f"Unsupported file type: {file_ext}")
            return False
        
        # Initialize database
        config = AppConfig.from_env()
        db_manager = DatabaseManager(config.database_path)
        
        # Check if document already exists
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check by title and size (since file_path column doesn't exist)
            cursor.execute("""
                SELECT id FROM documents 
                WHERE title = ? AND file_size = ?
            """, (file_name, file_size))
            
            existing = cursor.fetchone()
            if existing:
                logger.info(f"Document already exists: {file_name}")
                return True
            
            # Insert document record
            import uuid
            from datetime import datetime
            
            doc_id = str(uuid.uuid4())
            now = datetime.now()
            
            # Store file path in extracted_info as JSON
            import json
            extracted_info = json.dumps({"file_path": file_path})
            
            cursor.execute("""
                INSERT INTO documents (
                    id, title, file_type, file_size, processing_status, 
                    upload_timestamp, created_at, updated_at, extracted_info
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id, file_name, file_ext[1:], file_size, 'completed',
                now, now, now, extracted_info
            ))
            
            conn.commit()
            
            logger.info(f"Successfully added document: {file_name} (ID: {doc_id})")
            return True
            
    except Exception as e:
        logger.error(f"Error processing document {file_path}: {e}")
        return False


def get_document_status(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Get the processing status of a document.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Dict with document status information, or None if not found
    """
    try:
        config = AppConfig.from_env()
        db_manager = DatabaseManager(config.database_path)
        
        file_name = os.path.basename(file_path)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, processing_status, upload_timestamp, updated_at, extracted_info
                FROM documents 
                WHERE title = ?
            """, (file_name,))
            
            row = cursor.fetchone()
            if row:
                # Check if the extracted_info contains the file path
                extracted_info = row[5]
                if extracted_info:
                    try:
                        import json
                        info = json.loads(extracted_info)
                        if info.get('file_path') == file_path:
                            return {
                                'id': row[0],
                                'title': row[1],
                                'status': row[2],
                                'uploaded': row[3],
                                'updated': row[4]
                            }
                    except:
                        pass
                
                # Fallback: match by title only
                return {
                    'id': row[0],
                    'title': row[1],
                    'status': row[2],
                    'uploaded': row[3],
                    'updated': row[4]
                }
            
            return None
            
    except Exception as e:
        logger.error(f"Error getting document status for {file_path}: {e}")
        return None


def list_processed_documents() -> list:
    """
    List all processed documents in the system.
    
    Returns:
        List of document information dictionaries
    """
    try:
        config = AppConfig.from_env()
        db_manager = DatabaseManager(config.database_path)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, file_type, file_size, 
                       processing_status, upload_timestamp, updated_at, extracted_info
                FROM documents 
                ORDER BY upload_timestamp DESC
            """)
            
            documents = []
            for row in cursor.fetchall():
                # Try to extract file_path from extracted_info
                file_path = None
                if row[7]:  # extracted_info
                    try:
                        import json
                        info = json.loads(row[7])
                        file_path = info.get('file_path')
                    except:
                        pass
                
                documents.append({
                    'id': row[0],
                    'title': row[1],
                    'file_path': file_path or row[1],  # Use title as fallback
                    'file_type': row[2],
                    'file_size': row[3],
                    'status': row[4],
                    'uploaded': row[5],
                    'updated': row[6]
                })
            
            return documents
            
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return []


def remove_document(file_path: str) -> bool:
    """
    Remove a document from the system.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        bool: True if removal was successful, False otherwise
    """
    try:
        config = AppConfig.from_env()
        db_manager = DatabaseManager(config.database_path)
        
        file_name = os.path.basename(file_path)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get document ID first by title
            cursor.execute("SELECT id FROM documents WHERE title = ?", (file_name,))
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"Document not found: {file_path}")
                return False
            
            doc_id = row[0]
            
            # Remove from documents table
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            
            # Remove related knowledge graph data if it exists
            try:
                cursor.execute("DELETE FROM knowledge_nodes WHERE properties LIKE ?", (f'%{doc_id}%',))
                cursor.execute("DELETE FROM knowledge_relationships WHERE properties LIKE ?", (f'%{doc_id}%',))
            except:
                pass  # Tables might not exist
            
            conn.commit()
            
            logger.info(f"Successfully removed document: {file_path}")
            return True
            
    except Exception as e:
        logger.error(f"Error removing document {file_path}: {e}")
        return False