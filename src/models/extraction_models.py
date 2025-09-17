"""
Data models for OpenRouter extraction results and configuration.

This module defines the data structures used throughout the extraction pipeline
for storing extraction results, quality assessments, and configuration data.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum


class ExtractionMethod(Enum):
    """Enumeration of available extraction methods"""
    OPENROUTER_CLAUDE = "openrouter_claude_3_5_sonnet"
    OPENROUTER_VISION = "openrouter_vision_claude_3_5_sonnet"
    FALLBACK_RULE_BASED = "fallback_rule_based"


class ValidationStatus(Enum):
    """Enumeration of validation statuses"""
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    NEEDS_REVIEW = "needs_review"


@dataclass
class ConfidenceInterval:
    """Confidence interval for extracted field accuracy"""
    lower_bound: float
    upper_bound: float
    confidence_level: float = 0.95


@dataclass
class ExtractedField:
    """Represents a single extracted field with metadata"""
    name: str
    value: str
    confidence: float
    source_location: str = ""
    validation_status: str = "pending"
    notes: str = ""
    extraction_timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate field data after initialization"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


@dataclass
class QualityIssue:
    """Represents a quality issue identified during assessment"""
    issue_type: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    affected_fields: List[str]
    suggested_fix: str = ""


@dataclass
class QualityAssessment:
    """Comprehensive quality assessment of extraction results"""
    overall_score: float
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    compliance_score: float
    identified_issues: List[QualityIssue] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    confidence_intervals: Dict[str, ConfidenceInterval] = field(default_factory=dict)
    assessment_timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate quality scores after initialization"""
        scores = [
            self.overall_score, self.completeness_score, self.accuracy_score,
            self.consistency_score, self.compliance_score
        ]
        for score in scores:
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"Quality scores must be between 0.0 and 1.0, got {score}")


@dataclass
class ProcessingMetadata:
    """Metadata about the extraction processing"""
    extraction_method: str
    processing_time: float
    model_used: str
    prompt_template: str
    api_version: str
    processing_timestamp: datetime = field(default_factory=datetime.now)
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    error_count: int = 0
    retry_count: int = 0


@dataclass
class SourceReference:
    """Reference to source location in original document"""
    field_name: str
    source_location: str
    confidence: float
    extraction_method: str
    page_number: Optional[int] = None
    section_name: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None  # For vision extraction


@dataclass
class ValidationResult:
    """Result of field validation"""
    field_name: str
    is_valid: bool
    validation_rule: str
    error_message: str = ""
    confidence: float = 1.0
    validation_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExtractionResult:
    """Complete result of document extraction process"""
    document_id: str
    extraction_method: str
    confidence_score: float
    extracted_fields: Dict[str, ExtractedField]
    quality_assessment: QualityAssessment
    processing_metadata: ProcessingMetadata
    source_references: List[SourceReference] = field(default_factory=list)
    validation_results: List[ValidationResult] = field(default_factory=list)
    extraction_timestamp: datetime = field(default_factory=datetime.now)
    
    def get_field_value(self, field_name: str, default: str = "") -> str:
        """Get value of a specific field"""
        field = self.extracted_fields.get(field_name)
        return field.value if field else default
        
    def get_high_confidence_fields(self, threshold: float = 0.8) -> Dict[str, ExtractedField]:
        """Get fields with confidence above threshold"""
        return {
            name: field for name, field in self.extracted_fields.items()
            if field.confidence >= threshold
        }
        
    def get_validation_errors(self) -> List[ValidationResult]:
        """Get all validation errors"""
        return [result for result in self.validation_results if not result.is_valid]


@dataclass
class VisualElement:
    """Represents a visual element detected in document"""
    element_type: str  # "table", "image", "chart", "signature", etc.
    coordinates: Dict[str, float]  # x, y, width, height
    confidence: float
    description: str = ""
    extracted_text: str = ""


@dataclass
class TextRegion:
    """Represents a text region in document"""
    text: str
    coordinates: Dict[str, float]
    confidence: float
    font_info: Optional[Dict[str, Any]] = None
    formatting: Optional[Dict[str, Any]] = None


@dataclass
class VisionExtractionResult:
    """Result of vision-based document extraction"""
    document_id: str
    extraction_method: str
    visual_elements: List[VisualElement] = field(default_factory=list)
    text_regions: List[TextRegion] = field(default_factory=list)
    confidence_score: float = 0.0
    processing_metadata: ProcessingMetadata = None
    extraction_timestamp: datetime = field(default_factory=datetime.now)
    
    def get_text_content(self) -> str:
        """Get all extracted text content"""
        return "\n".join(region.text for region in self.text_regions)
        
    def get_elements_by_type(self, element_type: str) -> List[VisualElement]:
        """Get visual elements of specific type"""
        return [elem for elem in self.visual_elements if elem.element_type == element_type]


@dataclass
class ExtractionConfig:
    """Configuration for extraction process"""
    prompt_template: str
    extraction_method: ExtractionMethod = ExtractionMethod.OPENROUTER_CLAUDE
    quality_threshold: float = 0.7
    enable_vision: bool = False
    max_retries: int = 3
    timeout: int = 60
    custom_prompts: Dict[str, str] = field(default_factory=dict)
    validation_rules: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not 0.0 <= self.quality_threshold <= 1.0:
            raise ValueError(f"Quality threshold must be between 0.0 and 1.0")
        if self.max_retries < 0:
            raise ValueError("Max retries must be non-negative")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")


@dataclass
class BatchExtractionResult:
    """Result of batch document extraction"""
    batch_id: str
    total_documents: int
    successful_extractions: int
    failed_extractions: int
    extraction_results: List[ExtractionResult] = field(default_factory=list)
    batch_quality_assessment: Optional[QualityAssessment] = None
    processing_start_time: datetime = field(default_factory=datetime.now)
    processing_end_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate batch success rate"""
        if self.total_documents == 0:
            return 0.0
        return self.successful_extractions / self.total_documents
        
    @property
    def average_confidence(self) -> float:
        """Calculate average confidence across all extractions"""
        if not self.extraction_results:
            return 0.0
        total_confidence = sum(result.confidence_score for result in self.extraction_results)
        return total_confidence / len(self.extraction_results)


# Type aliases for convenience
ExtractionFieldDict = Dict[str, ExtractedField]
QualityMetrics = Dict[str, float]
ValidationRules = Dict[str, str]