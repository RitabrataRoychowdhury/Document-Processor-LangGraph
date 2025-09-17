"""
Results organization and archival service for the QME system.

This module provides automated organization of processing results with date-based
archival, cleanup policies, and efficient storage management.
"""

import os
import shutil
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ResultType(Enum):
    """Types of results that can be stored."""
    DOCUMENT_PROCESSING = "document_processing"
    TEMPLATE_GENERATION = "template_generation"
    VALIDATION_REPORT = "validation_report"
    PERFORMANCE_METRICS = "performance_metrics"
    AUDIT_TRAIL = "audit_trail"


@dataclass
class ResultMetadata:
    """Metadata for stored results."""
    result_id: str
    result_type: ResultType
    created_at: datetime
    file_path: str
    file_size: int
    user_id: Optional[str] = None
    document_id: Optional[str] = None
    processing_time: Optional[float] = None
    tags: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['result_type'] = self.result_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResultMetadata':
        """Create from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['result_type'] = ResultType(data['result_type'])
        return cls(**data)


class ResultsOrganizer:
    """Service for organizing and managing processing results."""
    
    def __init__(self, base_path: str = "results", config: Optional[Dict[str, Any]] = None):
        self.base_path = Path(base_path)
        self.config = config or {}
        
        # Configuration
        self.max_age_days = self.config.get('max_age_days', 90)
        self.archive_after_days = self.config.get('archive_after_days', 30)
        self.max_storage_gb = self.config.get('max_storage_gb', 10)
        self.cleanup_interval_hours = self.config.get('cleanup_interval_hours', 24)
        
        # Initialize directory structure
        self._initialize_directories()
        
        # Load existing metadata
        self.metadata_file = self.base_path / "metadata.json"
        self.metadata = self._load_metadata()
    
    def _initialize_directories(self):
        """Initialize the directory structure for results storage."""
        directories = [
            "active",
            "archived",
            "exports",
            "temp",
            "generated_documents",
            "validation_reports",
            "performance_reports",
            "audit_trails"
        ]
        
        for directory in directories:
            (self.base_path / directory).mkdir(parents=True, exist_ok=True)
        
        # Create date-based subdirectories for current year/month
        current_date = datetime.now()
        year_month = current_date.strftime("%Y/%m")
        
        for result_type in ResultType:
            type_dir = self.base_path / "active" / result_type.value / year_month
            type_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_metadata(self) -> Dict[str, ResultMetadata]:
        """Load existing metadata from file."""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
                return {
                    result_id: ResultMetadata.from_dict(metadata)
                    for result_id, metadata in data.items()
                }
        except (json.JSONError, KeyError, ValueError) as e:
            logger.error(f"Error loading metadata: {e}")
            return {}
    
    def _save_metadata(self):
        """Save metadata to file."""
        try:
            data = {
                result_id: metadata.to_dict()
                for result_id, metadata in self.metadata.items()
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def store_result(self, 
                    result_data: Any, 
                    result_type: ResultType,
                    result_id: Optional[str] = None,
                    user_id: Optional[str] = None,
                    document_id: Optional[str] = None,
                    processing_time: Optional[float] = None,
                    tags: Optional[List[str]] = None) -> str:
        """Store a processing result with metadata."""
        
        if result_id is None:
            result_id = self._generate_result_id(result_type)
        
        # Determine file path
        current_date = datetime.now()
        year_month = current_date.strftime("%Y/%m")
        
        file_name = f"{result_id}_{current_date.strftime('%Y%m%d_%H%M%S')}"
        
        # Determine file extension based on result type and data
        if isinstance(result_data, bytes):
            if result_type == ResultType.TEMPLATE_GENERATION:
                file_name += ".docx"
            else:
                file_name += ".bin"
        elif isinstance(result_data, (dict, list)):
            file_name += ".json"
        else:
            file_name += ".txt"
        
        file_path = self.base_path / "active" / result_type.value / year_month / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Store the data
        try:
            if isinstance(result_data, bytes):
                with open(file_path, 'wb') as f:
                    f.write(result_data)
            elif isinstance(result_data, (dict, list)):
                with open(file_path, 'w') as f:
                    json.dump(result_data, f, indent=2, default=str)
            else:
                with open(file_path, 'w') as f:
                    f.write(str(result_data))
            
            # Create metadata
            file_size = file_path.stat().st_size
            metadata = ResultMetadata(
                result_id=result_id,
                result_type=result_type,
                created_at=current_date,
                file_path=str(file_path),
                file_size=file_size,
                user_id=user_id,
                document_id=document_id,
                processing_time=processing_time,
                tags=tags
            )
            
            self.metadata[result_id] = metadata
            self._save_metadata()
            
            logger.info(f"Stored result {result_id} of type {result_type.value}")
            return result_id
            
        except Exception as e:
            logger.error(f"Error storing result {result_id}: {e}")
            raise
    
    def retrieve_result(self, result_id: str) -> Optional[Any]:
        """Retrieve a stored result by ID."""
        if result_id not in self.metadata:
            logger.warning(f"Result {result_id} not found in metadata")
            return None
        
        metadata = self.metadata[result_id]
        file_path = Path(metadata.file_path)
        
        if not file_path.exists():
            logger.warning(f"Result file not found: {file_path}")
            return None
        
        try:
            if file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    return json.load(f)
            elif file_path.suffix in ['.docx', '.bin']:
                with open(file_path, 'rb') as f:
                    return f.read()
            else:
                with open(file_path, 'r') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error retrieving result {result_id}: {e}")
            return None
    
    def list_results(self, 
                    result_type: Optional[ResultType] = None,
                    user_id: Optional[str] = None,
                    document_id: Optional[str] = None,
                    tags: Optional[List[str]] = None,
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None) -> List[ResultMetadata]:
        """List results with optional filtering."""
        results = []
        
        for metadata in self.metadata.values():
            # Apply filters
            if result_type and metadata.result_type != result_type:
                continue
            if user_id and metadata.user_id != user_id:
                continue
            if document_id and metadata.document_id != document_id:
                continue
            if tags and not any(tag in (metadata.tags or []) for tag in tags):
                continue
            if start_date and metadata.created_at < start_date:
                continue
            if end_date and metadata.created_at > end_date:
                continue
            
            results.append(metadata)
        
        # Sort by creation date (newest first)
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results
    
    def archive_old_results(self) -> int:
        """Archive results older than the configured threshold."""
        archived_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.archive_after_days)
        
        for result_id, metadata in list(self.metadata.items()):
            if metadata.created_at < cutoff_date:
                if self._archive_result(result_id):
                    archived_count += 1
        
        logger.info(f"Archived {archived_count} old results")
        return archived_count
    
    def _archive_result(self, result_id: str) -> bool:
        """Archive a single result."""
        if result_id not in self.metadata:
            return False
        
        metadata = self.metadata[result_id]
        current_path = Path(metadata.file_path)
        
        if not current_path.exists():
            # Remove metadata for missing file
            del self.metadata[result_id]
            self._save_metadata()
            return False
        
        # Create archive path
        archive_path = self.base_path / "archived" / current_path.name
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.move(str(current_path), str(archive_path))
            
            # Update metadata
            metadata.file_path = str(archive_path)
            self._save_metadata()
            
            logger.debug(f"Archived result {result_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error archiving result {result_id}: {e}")
            return False
    
    def cleanup_old_results(self) -> int:
        """Delete results older than the maximum age."""
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        
        for result_id, metadata in list(self.metadata.items()):
            if metadata.created_at < cutoff_date:
                if self._delete_result(result_id):
                    deleted_count += 1
        
        logger.info(f"Deleted {deleted_count} old results")
        return deleted_count
    
    def _delete_result(self, result_id: str) -> bool:
        """Delete a single result."""
        if result_id not in self.metadata:
            return False
        
        metadata = self.metadata[result_id]
        file_path = Path(metadata.file_path)
        
        try:
            if file_path.exists():
                file_path.unlink()
            
            del self.metadata[result_id]
            self._save_metadata()
            
            logger.debug(f"Deleted result {result_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting result {result_id}: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        total_size = 0
        type_counts = {}
        type_sizes = {}
        
        for metadata in self.metadata.values():
            total_size += metadata.file_size
            
            result_type = metadata.result_type.value
            type_counts[result_type] = type_counts.get(result_type, 0) + 1
            type_sizes[result_type] = type_sizes.get(result_type, 0) + metadata.file_size
        
        return {
            'total_results': len(self.metadata),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'type_counts': type_counts,
            'type_sizes_mb': {k: round(v / (1024 * 1024), 2) for k, v in type_sizes.items()},
            'oldest_result': min((m.created_at for m in self.metadata.values()), default=None),
            'newest_result': max((m.created_at for m in self.metadata.values()), default=None)
        }
    
    def _generate_result_id(self, result_type: ResultType) -> str:
        """Generate a unique result ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        return f"{result_type.value}_{timestamp}"
    
    def export_results(self, 
                      result_ids: List[str], 
                      export_path: Optional[str] = None) -> str:
        """Export multiple results to a single archive."""
        if export_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = str(self.base_path / "exports" / f"export_{timestamp}.zip")
        
        export_dir = Path(export_path).parent
        export_dir.mkdir(parents=True, exist_ok=True)
        
        import zipfile
        
        try:
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for result_id in result_ids:
                    if result_id in self.metadata:
                        metadata = self.metadata[result_id]
                        file_path = Path(metadata.file_path)
                        
                        if file_path.exists():
                            # Add file to zip with metadata
                            zipf.write(file_path, f"{result_id}/{file_path.name}")
                            
                            # Add metadata as JSON
                            metadata_json = json.dumps(metadata.to_dict(), indent=2)
                            zipf.writestr(f"{result_id}/metadata.json", metadata_json)
            
            logger.info(f"Exported {len(result_ids)} results to {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
            raise