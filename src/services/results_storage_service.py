"""
Results Storage Service

Provides organized storage and archiving for QME system results including:
- Generated documents with date-based organization
- Processing logs and metadata
- Quality validation reports
- Template archiving and preservation

This service follows SOLID principles with clear separation of concerns.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class ResultType(Enum):
    """Types of results that can be stored"""
    GENERATED_DOCUMENT = "generated_documents"
    PROCESSING_LOG = "processing_logs"
    VALIDATION_REPORT = "validation_reports"
    TEMPLATE_ARCHIVE = "templates_archive"


@dataclass
class StorageResult:
    """Result of a storage operation"""
    success: bool
    file_path: str
    message: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DocumentMetadata:
    """Metadata for stored documents"""
    patient_name: str
    generation_timestamp: datetime
    document_type: str
    file_size: int
    quality_score: Optional[float] = None
    processing_time: Optional[float] = None
    validation_status: Optional[str] = None


class ResultsStorageService:
    """
    Service for organizing and storing QME system results.
    
    Provides date-based organization, metadata tracking, and archival capabilities
    following the requirements for organized folder structure and document preservation.
    """
    
    def __init__(self, base_results_path: str = "results"):
        """
        Initialize the results storage service.
        
        Args:
            base_results_path: Base directory for all results storage
        """
        self.base_path = Path(base_results_path)
        self._ensure_directory_structure()
        
    def _ensure_directory_structure(self) -> None:
        """Ensure all required directories exist"""
        directories = [
            self.base_path / "generated_documents",
            self.base_path / "processing_logs",
            self.base_path / "validation_reports", 
            self.base_path / "templates_archive"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
    def store_generated_document(
        self,
        file_path: str,
        patient_name: str,
        metadata: Optional[DocumentMetadata] = None
    ) -> StorageResult:
        """
        Store a generated QME document with date-based organization.
        
        Args:
            file_path: Path to the document to store
            patient_name: Name of the patient for the document
            metadata: Optional metadata about the document
            
        Returns:
            StorageResult with operation details
        """
        try:
            # Create date-based directory structure
            now = datetime.now()
            date_path = self.base_path / "generated_documents" / str(now.year) / f"{now.month:02d}"
            date_path.mkdir(parents=True, exist_ok=True)
            
            # Generate organized filename
            safe_name = self._sanitize_filename(patient_name)
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            filename = f"QME_Report_{safe_name}_{timestamp}.docx"
            
            destination = date_path / filename
            
            # Copy file to organized location
            if os.path.exists(file_path):
                shutil.copy2(file_path, destination)
                
                # Store metadata if provided
                if metadata:
                    self._store_document_metadata(destination, metadata)
                    
                logger.info(f"Stored generated document: {destination}")
                return StorageResult(
                    success=True,
                    file_path=str(destination),
                    message=f"Document stored successfully in date-organized structure",
                    metadata={"original_path": file_path, "patient_name": patient_name}
                )
            else:
                return StorageResult(
                    success=False,
                    file_path="",
                    message=f"Source file not found: {file_path}"
                )
                
        except Exception as e:
            logger.error(f"Error storing generated document: {e}")
            return StorageResult(
                success=False,
                file_path="",
                message=f"Storage failed: {str(e)}"
            )
            
    def store_processing_log(
        self,
        log_content: str,
        log_type: str,
        timestamp: Optional[datetime] = None
    ) -> StorageResult:
        """
        Store processing logs with organized naming.
        
        Args:
            log_content: Content of the log
            log_type: Type of processing (extraction, generation, validation)
            timestamp: Optional timestamp, defaults to now
            
        Returns:
            StorageResult with operation details
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
                
            log_dir = self.base_path / "processing_logs"
            filename = f"{log_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}.log"
            log_path = log_dir / filename
            
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(log_content)
                
            logger.info(f"Stored processing log: {log_path}")
            return StorageResult(
                success=True,
                file_path=str(log_path),
                message=f"Processing log stored successfully",
                metadata={"log_type": log_type, "timestamp": timestamp.isoformat()}
            )
            
        except Exception as e:
            logger.error(f"Error storing processing log: {e}")
            return StorageResult(
                success=False,
                file_path="",
                message=f"Log storage failed: {str(e)}"
            )
            
    def store_validation_report(
        self,
        report_content: str,
        document_name: str,
        quality_score: Optional[float] = None
    ) -> StorageResult:
        """
        Store quality validation reports.
        
        Args:
            report_content: Content of the validation report
            document_name: Name of the document being validated
            quality_score: Optional overall quality score
            
        Returns:
            StorageResult with operation details
        """
        try:
            timestamp = datetime.now()
            report_dir = self.base_path / "validation_reports"
            
            safe_doc_name = self._sanitize_filename(document_name)
            filename = f"Quality_Report_{safe_doc_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
            report_path = report_dir / filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
                
            logger.info(f"Stored validation report: {report_path}")
            return StorageResult(
                success=True,
                file_path=str(report_path),
                message=f"Validation report stored successfully",
                metadata={
                    "document_name": document_name,
                    "quality_score": quality_score,
                    "timestamp": timestamp.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error storing validation report: {e}")
            return StorageResult(
                success=False,
                file_path="",
                message=f"Report storage failed: {str(e)}"
            )
            
    def archive_template(
        self,
        file_path: str,
        preserve_original: bool = True
    ) -> StorageResult:
        """
        Archive existing templates for preservation.
        
        Args:
            file_path: Path to the template to archive
            preserve_original: Whether to keep the original file
            
        Returns:
            StorageResult with operation details
        """
        try:
            archive_dir = self.base_path / "templates_archive"
            filename = Path(file_path).name
            destination = archive_dir / filename
            
            if preserve_original:
                shutil.copy2(file_path, destination)
            else:
                shutil.move(file_path, destination)
                
            logger.info(f"Archived template: {destination}")
            return StorageResult(
                success=True,
                file_path=str(destination),
                message=f"Template archived successfully",
                metadata={"original_path": file_path, "preserved": preserve_original}
            )
            
        except Exception as e:
            logger.error(f"Error archiving template: {e}")
            return StorageResult(
                success=False,
                file_path="",
                message=f"Archive failed: {str(e)}"
            )
            
    def get_storage_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored results.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            stats = {
                "generated_documents": self._count_files_in_directory("generated_documents"),
                "processing_logs": self._count_files_in_directory("processing_logs"),
                "validation_reports": self._count_files_in_directory("validation_reports"),
                "archived_templates": self._count_files_in_directory("templates_archive"),
                "total_storage_size": self._calculate_total_size(),
                "last_updated": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting storage statistics: {e}")
            return {"error": str(e)}
            
    def cleanup_old_files(self, days_to_keep: int = 30) -> Dict[str, int]:
        """
        Clean up old files based on age.
        
        Args:
            days_to_keep: Number of days to keep files
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            cleanup_stats = {"removed": 0, "kept": 0, "errors": 0}
            
            # Only clean up processing logs and validation reports
            # Keep generated documents and archived templates
            cleanup_dirs = ["processing_logs", "validation_reports"]
            
            for dir_name in cleanup_dirs:
                dir_path = self.base_path / dir_name
                if dir_path.exists():
                    for file_path in dir_path.rglob("*"):
                        if file_path.is_file() and not file_path.name.startswith('.'):
                            try:
                                if file_path.stat().st_mtime < cutoff_date:
                                    file_path.unlink()
                                    cleanup_stats["removed"] += 1
                                else:
                                    cleanup_stats["kept"] += 1
                            except Exception as e:
                                logger.error(f"Error removing file {file_path}: {e}")
                                cleanup_stats["errors"] += 1
                                
            logger.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {"error": str(e)}
            
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        return "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
    def _store_document_metadata(self, document_path: Path, metadata: DocumentMetadata) -> None:
        """Store metadata for a document"""
        metadata_path = document_path.with_suffix('.json')
        metadata_dict = {
            "patient_name": metadata.patient_name,
            "generation_timestamp": metadata.generation_timestamp.isoformat(),
            "document_type": metadata.document_type,
            "file_size": metadata.file_size,
            "quality_score": metadata.quality_score,
            "processing_time": metadata.processing_time,
            "validation_status": metadata.validation_status
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=2)
            
    def _count_files_in_directory(self, directory_name: str) -> int:
        """Count files in a directory"""
        dir_path = self.base_path / directory_name
        if not dir_path.exists():
            return 0
            
        return len([f for f in dir_path.rglob("*") if f.is_file() and not f.name.startswith('.')])
        
    def _calculate_total_size(self) -> int:
        """Calculate total size of all stored files"""
        total_size = 0
        for file_path in self.base_path.rglob("*"):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except OSError:
                    pass  # Skip files that can't be accessed
                    
        return total_size