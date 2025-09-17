"""
Core service interfaces for the QME system.

This module defines the abstract base classes and interfaces that all core services
must implement to ensure consistent API contracts and enable dependency injection.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class ProcessingStatus(Enum):
    """Status enumeration for processing operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProcessingResult:
    """Base result class for all processing operations."""
    success: bool
    status: ProcessingStatus
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExtractionResult(ProcessingResult):
    """Result from document extraction operations."""
    extracted_fields: Optional[Dict[str, Any]] = None
    confidence_scores: Optional[Dict[str, float]] = None
    evidence_snippets: Optional[Dict[str, List[str]]] = None


@dataclass
class ValidationResult(ProcessingResult):
    """Result from validation operations."""
    is_valid: bool = False
    accepted_fields: Optional[Dict[str, Any]] = None
    flagged_fields: Optional[Dict[str, Any]] = None
    missing_fields: Optional[List[str]] = None
    validation_errors: Optional[List[str]] = None


@dataclass
class GenerationResult(ProcessingResult):
    """Result from content generation operations."""
    generated_content: Optional[Dict[str, Any]] = None
    template_data: Optional[bytes] = None
    quality_score: Optional[float] = None


class IExtractionService(ABC):
    """Interface for document extraction services."""
    
    @abstractmethod
    async def extract_fields(self, document_path: str, **kwargs) -> ExtractionResult:
        """Extract structured fields from a document."""
        pass
    
    @abstractmethod
    async def calculate_confidence(self, extracted_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence scores for extracted fields."""
        pass
    
    @abstractmethod
    async def collect_evidence(self, document_path: str, fields: Dict[str, Any]) -> Dict[str, List[str]]:
        """Collect evidence snippets for extracted fields."""
        pass


class IValidationService(ABC):
    """Interface for validation services."""
    
    @abstractmethod
    async def validate_extraction(self, extraction_result: ExtractionResult) -> ValidationResult:
        """Validate extracted data against business rules."""
        pass
    
    @abstractmethod
    async def check_compliance(self, data: Dict[str, Any]) -> ValidationResult:
        """Check data compliance against regulatory requirements."""
        pass
    
    @abstractmethod
    async def validate_quality(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate data quality and completeness."""
        pass


class IGenerationService(ABC):
    """Interface for content generation services."""
    
    @abstractmethod
    async def generate_content(self, validated_data: Dict[str, Any], **kwargs) -> GenerationResult:
        """Generate content from validated data."""
        pass
    
    @abstractmethod
    async def assemble_template(self, content: Dict[str, Any], template_config: Dict[str, Any]) -> GenerationResult:
        """Assemble final template from generated content."""
        pass
    
    @abstractmethod
    async def customize_output(self, template_data: bytes, customizations: Dict[str, Any]) -> GenerationResult:
        """Apply customizations to generated template."""
        pass


class ICalculationService(ABC):
    """Interface for calculation services."""
    
    @abstractmethod
    async def calculate_impairment(self, measurements: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate impairment ratings from measurements."""
        pass
    
    @abstractmethod
    async def apply_ama_tables(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply AMA table calculations."""
        pass
    
    @abstractmethod
    async def validate_calculations(self, calculations: Dict[str, Any]) -> ValidationResult:
        """Validate calculation results."""
        pass


class IKnowledgeService(ABC):
    """Interface for knowledge base services."""
    
    @abstractmethod
    async def query_knowledge_base(self, query: str, **kwargs) -> Dict[str, Any]:
        """Query the knowledge base."""
        pass
    
    @abstractmethod
    async def update_knowledge_base(self, data: Dict[str, Any]) -> bool:
        """Update knowledge base with new data."""
        pass
    
    @abstractmethod
    async def get_references(self, topic: str) -> List[Dict[str, Any]]:
        """Get reference materials for a topic."""
        pass


class IStorageService(ABC):
    """Interface for storage services."""
    
    @abstractmethod
    async def store_document(self, document_data: bytes, metadata: Dict[str, Any]) -> str:
        """Store a document and return its ID."""
        pass
    
    @abstractmethod
    async def retrieve_document(self, document_id: str) -> Optional[bytes]:
        """Retrieve a document by ID."""
        pass
    
    @abstractmethod
    async def store_results(self, results: Dict[str, Any]) -> str:
        """Store processing results."""
        pass
    
    @abstractmethod
    async def get_audit_trail(self, process_id: str) -> List[Dict[str, Any]]:
        """Get audit trail for a process."""
        pass


class IMonitoringService(ABC):
    """Interface for monitoring services."""
    
    @abstractmethod
    async def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log a system event."""
        pass
    
    @abstractmethod
    async def track_performance(self, operation: str, duration: float, metadata: Dict[str, Any]) -> None:
        """Track performance metrics."""
        pass
    
    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Check service health status."""
        pass
    
    @abstractmethod
    async def get_metrics(self, metric_type: str, time_range: Optional[str] = None) -> Dict[str, Any]:
        """Get system metrics."""
        pass