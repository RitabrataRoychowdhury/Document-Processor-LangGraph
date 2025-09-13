"""
Knowledge base initializer for automatic system startup.

This module handles the initialization of the knowledge base with canonical
medical documents during system startup.
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from .ingestion_pipeline import IngestionPipeline
from ..config.app_config import AppConfig
from ..storage.database import DatabaseManager
from ..repositories.document_repository import DocumentRepository

logger = logging.getLogger(__name__)


@dataclass
class InitializationResult:
    """Result of knowledge base initialization."""
    success: bool
    processed_documents: List[str]
    failed_documents: List[str]
    total_processing_time: float
    error_messages: List[str]


class KnowledgeBaseInitializer:
    """Initializes knowledge base with canonical medical documents."""
    
    def __init__(self, config: AppConfig, ingestion_pipeline: IngestionPipeline):
        """Initialize with configuration and ingestion pipeline."""
        self.config = config
        self.pipeline = ingestion_pipeline
        self.db_manager = DatabaseManager(config.database_path)
        self.doc_repository = DocumentRepository(self.db_manager)
        
        # Canonical documents that should be processed on startup
        self.canonical_documents = [
            "AMAGuides 5th Edition.pdf",
            "QME-Study-Guide.pdf", 
            "Sample3.pdf"
        ]
    
    async def initialize_canonical_documents(self) -> InitializationResult:
        """Initialize knowledge base with canonical medical documents."""
        logger.info("Starting knowledge base initialization with canonical documents")
        
        start_time = asyncio.get_event_loop().time()
        processed_docs = []
        failed_docs = []
        error_messages = []
        
        for doc_path in self.canonical_documents:
            try:
                # Check if document exists
                if not Path(doc_path).exists():
                    logger.warning(f"Canonical document not found: {doc_path}")
                    failed_docs.append(doc_path)
                    error_messages.append(f"File not found: {doc_path}")
                    continue
                
                # Check if document is already processed
                if await self._is_document_already_processed(doc_path):
                    logger.info(f"Document already processed, skipping: {doc_path}")
                    processed_docs.append(doc_path)
                    continue
                
                # Process the document
                logger.info(f"Processing canonical document: {doc_path}")
                result = await self.pipeline.process_document(doc_path)
                
                if result.success:
                    processed_docs.append(doc_path)
                    logger.info(f"Successfully processed canonical document: {doc_path}")
                else:
                    failed_docs.append(doc_path)
                    error_msg = f"Failed to process {doc_path}: {result.error_message}"
                    error_messages.append(error_msg)
                    logger.error(error_msg)
                    
            except Exception as e:
                failed_docs.append(doc_path)
                error_msg = f"Exception processing {doc_path}: {str(e)}"
                error_messages.append(error_msg)
                logger.error(error_msg, exc_info=True)
        
        total_time = asyncio.get_event_loop().time() - start_time
        success = len(failed_docs) == 0
        
        logger.info(f"Knowledge base initialization completed in {total_time:.2f}s")
        logger.info(f"Processed: {len(processed_docs)}, Failed: {len(failed_docs)}")
        
        return InitializationResult(
            success=success,
            processed_documents=processed_docs,
            failed_documents=failed_docs,
            total_processing_time=total_time,
            error_messages=error_messages
        )
    
    async def _is_document_already_processed(self, doc_path: str) -> bool:
        """Check if a document has already been processed."""
        try:
            # Get file stats for comparison
            file_path = Path(doc_path)
            file_size = file_path.stat().st_size
            file_mtime = file_path.stat().st_mtime
            
            # Check if document exists in database with same size and modification time
            existing_doc = self.doc_repository.find_by_file_path(doc_path)
            
            if existing_doc is None:
                return False
            
            # Check if file has been modified since last processing
            if (existing_doc.metadata.get('file_size') == file_size and 
                existing_doc.metadata.get('file_mtime') == file_mtime and
                existing_doc.processing_status == 'completed'):
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking if document is processed: {e}")
            return False
    
    async def initialize_directory_monitoring(self, directory: str = "data/documents") -> None:
        """Initialize monitoring of documents directory for new files."""
        logger.info(f"Starting directory monitoring for: {directory}")
        
        try:
            # Ensure directory exists
            Path(directory).mkdir(parents=True, exist_ok=True)
            
            # Process any existing files in the directory
            await self._process_directory_files(directory)
            
            logger.info(f"Directory monitoring initialized for: {directory}")
            
        except Exception as e:
            logger.error(f"Failed to initialize directory monitoring: {e}", exc_info=True)
    
    async def _process_directory_files(self, directory: str) -> None:
        """Process all supported files in the given directory."""
        try:
            directory_path = Path(directory)
            
            if not directory_path.exists():
                logger.warning(f"Directory does not exist: {directory}")
                return
            
            # Find all supported files
            supported_extensions = [f".{ext}" for ext in self.config.allowed_file_types]
            files_to_process = []
            
            for file_path in directory_path.iterdir():
                if (file_path.is_file() and 
                    file_path.suffix.lower() in supported_extensions and
                    file_path.stat().st_size <= self.config.max_file_size_mb * 1024 * 1024):
                    files_to_process.append(str(file_path))
            
            if not files_to_process:
                logger.info(f"No supported files found in directory: {directory}")
                return
            
            logger.info(f"Found {len(files_to_process)} files to process in {directory}")
            
            # Process files
            for file_path in files_to_process:
                try:
                    if not await self._is_document_already_processed(file_path):
                        logger.info(f"Processing file: {file_path}")
                        result = await self.pipeline.process_document(file_path)
                        
                        if result.success:
                            logger.info(f"Successfully processed: {file_path}")
                        else:
                            logger.error(f"Failed to process: {file_path} - {result.error_message}")
                    else:
                        logger.info(f"File already processed, skipping: {file_path}")
                        
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}", exc_info=True)
                    
        except Exception as e:
            logger.error(f"Error processing directory files: {e}", exc_info=True)
    
    async def validate_initialization(self) -> Dict[str, Any]:
        """Validate that initialization was successful."""
        try:
            # Check if canonical documents are in the knowledge base
            canonical_status = {}
            
            for doc_path in self.canonical_documents:
                doc = self.doc_repository.find_by_file_path(doc_path)
                canonical_status[doc_path] = {
                    "exists": doc is not None,
                    "processed": doc.processing_status == 'completed' if doc else False,
                    "node_count": 0  # Will be updated below
                }
            
            # Get knowledge graph statistics
            from ..repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
            kg_repo = SQLiteKnowledgeGraphRepository(self.db_manager)
            
            total_nodes = kg_repo.get_node_count()
            total_relationships = kg_repo.get_relationship_count()
            node_types = kg_repo.get_node_types_count()
            
            return {
                "canonical_documents": canonical_status,
                "knowledge_graph": {
                    "total_nodes": total_nodes,
                    "total_relationships": total_relationships,
                    "node_types": node_types
                },
                "validation_passed": total_nodes > 0 and len(node_types) > 0
            }
            
        except Exception as e:
            logger.error(f"Error validating initialization: {e}", exc_info=True)
            return {
                "validation_passed": False,
                "error": str(e)
            }
    
    def get_initialization_status(self) -> Dict[str, Any]:
        """Get current initialization status."""
        try:
            # Check which canonical documents are processed
            processed_count = 0
            total_count = len(self.canonical_documents)
            
            for doc_path in self.canonical_documents:
                doc = self.doc_repository.find_by_file_path(doc_path)
                if doc and doc.processing_status == 'completed':
                    processed_count += 1
            
            return {
                "canonical_documents_processed": processed_count,
                "total_canonical_documents": total_count,
                "initialization_complete": processed_count == total_count,
                "completion_percentage": (processed_count / total_count) * 100 if total_count > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting initialization status: {e}", exc_info=True)
            return {
                "initialization_complete": False,
                "error": str(e)
            }


async def initialize_system_startup(config: AppConfig, ingestion_pipeline: IngestionPipeline) -> InitializationResult:
    """Initialize system on startup with canonical documents."""
    initializer = KnowledgeBaseInitializer(config, ingestion_pipeline)
    
    # Initialize canonical documents
    result = await initializer.initialize_canonical_documents()
    
    # Initialize directory monitoring
    await initializer.initialize_directory_monitoring()
    
    # Validate initialization
    validation = await initializer.validate_initialization()
    
    if not validation.get("validation_passed", False):
        logger.warning("System initialization validation failed")
        result.success = False
        result.error_messages.append("Initialization validation failed")
    
    return result