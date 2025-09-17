"""
Results Storage Service

This service provides comprehensive storage capabilities for QME processing results,
including document metadata, processing logs, quality reports, and audit trails.
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum

# Core imports
from src.core.interfaces import IStorageService

# Optional dependencies with graceful degradation
try:
    from src.infrastructure.monitoring.structured_logger import extraction_logger
except ImportError:
    extraction_logger = logging.getLogger(__name__)


class ResultType(Enum):
    """Types of results that can be stored."""
    EXTRACTION_RESULT = "extraction_result"
    TEMPLATE_RESULT = "template_result"
    VALIDATION_RESULT = "validation_result"
    QUALITY_REPORT = "quality_report"
    PROCESSING_LOG = "processing_log"
    AUDIT_TRAIL = "audit_trail"


@dataclass
class DocumentMetadata:
    """Metadata for stored documents."""
    document_id: str
    original_filename: str
    file_size: int
    mime_type: str
    upload_timestamp: datetime
    processing_status: str
    checksum: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StorageResult:
    """Result of storage operation."""
    success: bool
    storage_id: str
    storage_path: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResultsStorageService(IStorageService):
    """
    Comprehensive results storage service for QME processing results.
    
    Features:
    - Document storage with metadata tracking
    - Processing results storage and retrieval
    - Quality reports and audit trails
    - Automatic directory organization
    - Compression and archiving capabilities
    - Search and filtering functionality
    """
    
    def __init__(self, base_storage_path: str = "results"):
        """Initialize the results storage service."""
        self.base_storage_path = Path(base_storage_path)
        
        # Initialize storage directories
        self.directories = {
            "documents": self.base_storage_path / "documents",
            "extraction_results": self.base_storage_path / "extraction_results",
            "template_results": self.base_storage_path / "template_results",
            "validation_results": self.base_storage_path / "validation_results",
            "quality_reports": self.base_storage_path / "quality_reports",
            "processing_logs": self.base_storage_path / "processing_logs",
            "audit_trails": self.base_storage_path / "audit_trails",
            "metadata": self.base_storage_path / "metadata"
        }
        
        # Ensure all directories exist
        self._ensure_directories()
        
        # Initialize metadata storage
        self.metadata_file = self.directories["metadata"] / "storage_metadata.json"
        self.metadata_cache = self._load_metadata_cache()
        
        extraction_logger.info(
            "Initialized ResultsStorageService",
            extra_data={
                "base_storage_path": str(self.base_storage_path),
                "directories": {k: str(v) for k, v in self.directories.items()}
            }
        )
    
    def _ensure_directories(self) -> None:
        """Ensure all storage directories exist."""
        for directory in self.directories.values():
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_metadata_cache(self) -> Dict[str, Any]:
        """Load metadata cache from storage."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                extraction_logger.warning(f"Failed to load metadata cache: {str(e)}")
        
        return {
            "documents": {},
            "results": {},
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_metadata_cache(self) -> None:
        """Save metadata cache to storage."""
        try:
            self.metadata_cache["last_updated"] = datetime.now().isoformat()
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata_cache, f, indent=2, default=str)
        except Exception as e:
            extraction_logger.error(f"Failed to save metadata cache: {str(e)}")
    
    def _generate_storage_id(self, result_type: ResultType) -> str:
        """Generate unique storage ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        return f"{result_type.value}_{timestamp}"
    
    async def store_document(self, document_data: bytes, metadata: Dict[str, Any]) -> str:
        """Store a document and return its ID."""
        try:
            document_id = self._generate_storage_id(ResultType.EXTRACTION_RESULT)
            
            # Create document metadata
            doc_metadata = DocumentMetadata(
                document_id=document_id,
                original_filename=metadata.get("filename", "unknown"),
                file_size=len(document_data),
                mime_type=metadata.get("mime_type", "application/octet-stream"),
                upload_timestamp=datetime.now(),
                processing_status="stored",
                tags=metadata.get("tags", []),
                custom_metadata=metadata.get("custom_metadata", {})
            )
            
            # Store document file
            file_extension = Path(doc_metadata.original_filename).suffix or ".bin"
            document_path = self.directories["documents"] / f"{document_id}{file_extension}"
            
            with open(document_path, 'wb') as f:
                f.write(document_data)
            
            # Update metadata cache
            self.metadata_cache["documents"][document_id] = asdict(doc_metadata)
            self._save_metadata_cache()
            
            extraction_logger.info(
                f"Document stored successfully: {document_id}",
                extra_data={
                    "document_id": document_id,
                    "filename": doc_metadata.original_filename,
                    "file_size": doc_metadata.file_size
                }
            )
            
            return document_id
            
        except Exception as e:
            extraction_logger.error(f"Failed to store document: {str(e)}")
            raise
    
    async def retrieve_document(self, document_id: str) -> Optional[bytes]:
        """Retrieve a document by ID."""
        try:
            if document_id not in self.metadata_cache["documents"]:
                return None
            
            doc_metadata = self.metadata_cache["documents"][document_id]
            original_filename = doc_metadata["original_filename"]
            file_extension = Path(original_filename).suffix or ".bin"
            document_path = self.directories["documents"] / f"{document_id}{file_extension}"
            
            if not document_path.exists():
                extraction_logger.warning(f"Document file not found: {document_path}")
                return None
            
            with open(document_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            extraction_logger.error(f"Failed to retrieve document {document_id}: {str(e)}")
            return None
    
    async def store_results(self, results: Dict[str, Any]) -> str:
        """Store processing results."""
        try:
            result_type = ResultType(results.get("result_type", "extraction_result"))
            storage_id = self._generate_storage_id(result_type)
            
            # Determine storage directory
            if result_type == ResultType.EXTRACTION_RESULT:
                storage_dir = self.directories["extraction_results"]
            elif result_type == ResultType.TEMPLATE_RESULT:
                storage_dir = self.directories["template_results"]
            elif result_type == ResultType.VALIDATION_RESULT:
                storage_dir = self.directories["validation_results"]
            elif result_type == ResultType.QUALITY_REPORT:
                storage_dir = self.directories["quality_reports"]
            elif result_type == ResultType.PROCESSING_LOG:
                storage_dir = self.directories["processing_logs"]
            else:
                storage_dir = self.directories["extraction_results"]
            
            # Store results file
            results_path = storage_dir / f"{storage_id}.json"
            
            # Add storage metadata
            results_with_metadata = {
                **results,
                "storage_id": storage_id,
                "storage_timestamp": datetime.now().isoformat(),
                "result_type": result_type.value
            }
            
            with open(results_path, 'w') as f:
                json.dump(results_with_metadata, f, indent=2, default=str)
            
            # Update metadata cache
            if "results" not in self.metadata_cache:
                self.metadata_cache["results"] = {}
            
            self.metadata_cache["results"][storage_id] = {
                "storage_id": storage_id,
                "result_type": result_type.value,
                "storage_path": str(results_path),
                "storage_timestamp": datetime.now().isoformat(),
                "document_id": results.get("document_id"),
                "processing_status": results.get("processing_status", "completed")
            }
            
            self._save_metadata_cache()
            
            extraction_logger.info(
                f"Results stored successfully: {storage_id}",
                extra_data={
                    "storage_id": storage_id,
                    "result_type": result_type.value,
                    "storage_path": str(results_path)
                }
            )
            
            return storage_id
            
        except Exception as e:
            extraction_logger.error(f"Failed to store results: {str(e)}")
            raise
    
    async def get_audit_trail(self, process_id: str) -> List[Dict[str, Any]]:
        """Get audit trail for a process."""
        try:
            audit_trail = []
            
            # Search for audit trail files related to the process
            audit_files = list(self.directories["audit_trails"].glob(f"*{process_id}*.json"))
            
            for audit_file in audit_files:
                try:
                    with open(audit_file, 'r') as f:
                        audit_data = json.load(f)
                        audit_trail.append(audit_data)
                except Exception as e:
                    extraction_logger.warning(f"Failed to load audit file {audit_file}: {str(e)}")
            
            # Sort by timestamp
            audit_trail.sort(key=lambda x: x.get("timestamp", ""))
            
            return audit_trail
            
        except Exception as e:
            extraction_logger.error(f"Failed to get audit trail for {process_id}: {str(e)}")
            return []
    
    def store_quality_report(self, report_data: Dict[str, Any]) -> StorageResult:
        """Store quality assessment report."""
        try:
            storage_id = self._generate_storage_id(ResultType.QUALITY_REPORT)
            report_path = self.directories["quality_reports"] / f"{storage_id}.json"
            
            # Add report metadata
            report_with_metadata = {
                **report_data,
                "report_id": storage_id,
                "report_timestamp": datetime.now().isoformat(),
                "report_type": "quality_assessment"
            }
            
            with open(report_path, 'w') as f:
                json.dump(report_with_metadata, f, indent=2, default=str)
            
            return StorageResult(
                success=True,
                storage_id=storage_id,
                storage_path=str(report_path),
                metadata={"report_type": "quality_assessment"}
            )
            
        except Exception as e:
            extraction_logger.error(f"Failed to store quality report: {str(e)}")
            return StorageResult(
                success=False,
                storage_id="",
                error_message=str(e)
            )
    
    def store_processing_log(self, log_data: Dict[str, Any]) -> StorageResult:
        """Store processing log."""
        try:
            storage_id = self._generate_storage_id(ResultType.PROCESSING_LOG)
            log_path = self.directories["processing_logs"] / f"{storage_id}.json"
            
            # Add log metadata
            log_with_metadata = {
                **log_data,
                "log_id": storage_id,
                "log_timestamp": datetime.now().isoformat(),
                "log_type": "processing_log"
            }
            
            with open(log_path, 'w') as f:
                json.dump(log_with_metadata, f, indent=2, default=str)
            
            return StorageResult(
                success=True,
                storage_id=storage_id,
                storage_path=str(log_path),
                metadata={"log_type": "processing_log"}
            )
            
        except Exception as e:
            extraction_logger.error(f"Failed to store processing log: {str(e)}")
            return StorageResult(
                success=False,
                storage_id="",
                error_message=str(e)
            )
    
    def get_stored_results(self, result_type: Optional[ResultType] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get stored results with optional filtering."""
        try:
            results = []
            
            for storage_id, metadata in self.metadata_cache.get("results", {}).items():
                if result_type and metadata.get("result_type") != result_type.value:
                    continue
                
                results.append(metadata)
                
                if len(results) >= limit:
                    break
            
            # Sort by timestamp (newest first)
            results.sort(key=lambda x: x.get("storage_timestamp", ""), reverse=True)
            
            return results
            
        except Exception as e:
            extraction_logger.error(f"Failed to get stored results: {str(e)}")
            return []
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific document."""
        return self.metadata_cache.get("documents", {}).get(document_id)
    
    def search_results(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search results based on query parameters."""
        try:
            results = []
            
            for storage_id, metadata in self.metadata_cache.get("results", {}).items():
                match = True
                
                # Check each query parameter
                for key, value in query.items():
                    if key not in metadata or metadata[key] != value:
                        match = False
                        break
                
                if match:
                    results.append(metadata)
            
            return results
            
        except Exception as e:
            extraction_logger.error(f"Failed to search results: {str(e)}")
            return []
    
    def cleanup_old_results(self, days_old: int = 30) -> int:
        """Clean up results older than specified days."""
        try:
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            cleaned_count = 0
            
            # Clean up old result files
            for result_type in ResultType:
                if result_type == ResultType.EXTRACTION_RESULT:
                    storage_dir = self.directories["extraction_results"]
                elif result_type == ResultType.TEMPLATE_RESULT:
                    storage_dir = self.directories["template_results"]
                elif result_type == ResultType.VALIDATION_RESULT:
                    storage_dir = self.directories["validation_results"]
                elif result_type == ResultType.QUALITY_REPORT:
                    storage_dir = self.directories["quality_reports"]
                elif result_type == ResultType.PROCESSING_LOG:
                    storage_dir = self.directories["processing_logs"]
                else:
                    continue
                
                for file_path in storage_dir.glob("*.json"):
                    if file_path.stat().st_mtime < cutoff_date:
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                        except Exception as e:
                            extraction_logger.warning(f"Failed to delete old file {file_path}: {str(e)}")
            
            extraction_logger.info(f"Cleaned up {cleaned_count} old result files")
            return cleaned_count
            
        except Exception as e:
            extraction_logger.error(f"Failed to cleanup old results: {str(e)}")
            return 0
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            stats = {
                "total_documents": len(self.metadata_cache.get("documents", {})),
                "total_results": len(self.metadata_cache.get("results", {})),
                "storage_directories": {},
                "total_storage_size": 0
            }
            
            # Calculate directory sizes
            for name, directory in self.directories.items():
                if directory.exists():
                    size = sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())
                    file_count = len(list(directory.rglob('*')))
                    stats["storage_directories"][name] = {
                        "size_bytes": size,
                        "file_count": file_count
                    }
                    stats["total_storage_size"] += size
            
            return stats
            
        except Exception as e:
            extraction_logger.error(f"Failed to get storage statistics: {str(e)}")
            return {}


# Factory function for creating results storage service
def create_results_storage_service(base_storage_path: str = "results") -> ResultsStorageService:
    """Factory function to create results storage service."""
    return ResultsStorageService(base_storage_path=base_storage_path)