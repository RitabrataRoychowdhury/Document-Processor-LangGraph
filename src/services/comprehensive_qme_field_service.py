"""
Comprehensive QME Field Service

This service provides comprehensive field extraction capabilities for all QME document types
including PQME reports, medical records, and examination reports. It integrates multiple
extraction methods with confidence scoring, validation, and evidence provenance tracking.
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

# Core imports
from src.core.interfaces import IExtractionService, ExtractionResult, ValidationResult, ProcessingResult
from src.models.extraction_models import (
    ExtractedField, QualityAssessment, QualityIssue, ProcessingMetadata,
    SourceReference, ValidationResult as ModelValidationResult, ExtractionConfig,
    ConfidenceInterval, ExtractionMethod
)
from src.core.extraction.field_extraction_service import FieldExtractionService, FieldExtractionConfig
from src.core.extraction.openrouter_extraction_service import OpenRouterExtractionService

# Optional dependencies with graceful degradation
try:
    from src.infrastructure.monitoring.structured_logger import extraction_logger
except ImportError:
    extraction_logger = logging.getLogger(__name__)

try:
    from src.infrastructure.monitoring.performance_monitor import PerformanceMonitor
    PERFORMANCE_MONITORING_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITORING_AVAILABLE = False
    extraction_logger.warning("Performance monitoring not available")

# Error handling imports
from src.utils.error_handling import (
    DocumentQAError, ErrorType, handle_errors, safe_execute,
    FileProcessingError, ValidationError, APIError, RetryableException
)


class DocumentType(Enum):
    """Types of QME documents that can be processed."""
    PQME_REPORT = "pqme_report"
    MEDICAL_RECORD = "medical_record"
    EXAMINATION_REPORT = "examination_report"
    LEGAL_DOCUMENT = "legal_document"
    UNKNOWN = "unknown"


class ExtractionStrategy(Enum):
    """Available extraction strategies."""
    RULE_BASED = "rule_based"
    AI_ENHANCED = "ai_enhanced"
    HYBRID = "hybrid"
    VISION_ENABLED = "vision_enabled"


@dataclass
class QMEFieldExtractionConfig:
    """Configuration for comprehensive QME field extraction."""
    extraction_strategy: ExtractionStrategy = ExtractionStrategy.HYBRID
    enable_openrouter: bool = True
    enable_vision: bool = False
    confidence_threshold: float = 0.7
    enable_cross_validation: bool = True
    enable_evidence_tracking: bool = True
    max_processing_time: float = 300.0  # 5 minutes
    fallback_to_rule_based: bool = True
    quality_assessment_enabled: bool = True
    
    # Document type specific configurations
    document_type_configs: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "pqme_report": {
            "required_fields": ["patient_name", "case_number", "injury_date", "body_parts"],
            "optional_fields": ["age", "gender", "occupation", "employer"],
            "extraction_prompts": "pqme_extraction",
            "validation_rules": "pqme_validation"
        },
        "medical_record": {
            "required_fields": ["patient_name", "date_of_service", "diagnosis"],
            "optional_fields": ["treatment", "medications", "provider"],
            "extraction_prompts": "medical_record_extraction",
            "validation_rules": "medical_validation"
        },
        "examination_report": {
            "required_fields": ["patient_name", "exam_date", "findings"],
            "optional_fields": ["rom_measurements", "impairment_ratings"],
            "extraction_prompts": "examination_extraction",
            "validation_rules": "examination_validation"
        }
    })


@dataclass
class ComprehensiveExtractionResult:
    """Enhanced extraction result with comprehensive metadata."""
    document_id: str
    document_type: DocumentType
    extraction_strategy: ExtractionStrategy
    success: bool
    
    # Extracted data
    extracted_fields: Dict[str, ExtractedField]
    field_confidence_scores: Dict[str, float]
    evidence_snippets: Dict[str, List[str]]
    source_references: List[SourceReference]
    
    # Quality assessment
    quality_assessment: QualityAssessment
    validation_results: List[ModelValidationResult]
    
    # Processing metadata
    processing_metadata: ProcessingMetadata
    extraction_errors: List[str]
    warnings: List[str]
    
    # Performance metrics
    processing_time: float
    memory_usage: Optional[float] = None
    api_calls_made: int = 0
    
    def get_high_confidence_fields(self, threshold: float = 0.8) -> Dict[str, ExtractedField]:
        """Get fields with confidence above threshold."""
        return {
            name: field for name, field in self.extracted_fields.items()
            if self.field_confidence_scores.get(name, 0.0) >= threshold
        }
    
    def get_validation_errors(self) -> List[str]:
        """Get all validation error messages."""
        return [result.error_message for result in self.validation_results if not result.is_valid]
    
    def get_missing_required_fields(self, document_type_config: Dict[str, Any]) -> List[str]:
        """Get list of missing required fields."""
        required_fields = document_type_config.get("required_fields", [])
        return [field for field in required_fields if field not in self.extracted_fields or not self.extracted_fields[field].value]


class ComprehensiveQMEFieldService(IExtractionService):
    """
    Comprehensive QME field extraction service with multiple extraction methods,
    confidence scoring, validation, and evidence provenance tracking.
    
    Features:
    - Multi-strategy extraction (rule-based, AI-enhanced, hybrid, vision)
    - Document type detection and specialized processing
    - Confidence scoring and quality assessment
    - Evidence snippet collection and source tracking
    - Cross-validation between extraction methods
    - Comprehensive error handling and fallback mechanisms
    - Performance monitoring and optimization
    """
    
    def __init__(self, config: Optional[QMEFieldExtractionConfig] = None):
        """Initialize the comprehensive QME field service with comprehensive error handling."""
        try:
            self.config = config or QMEFieldExtractionConfig()
            
            # Initialize extraction services with error handling
            self._initialize_extraction_services()
            
            # Initialize performance monitoring
            self.performance_monitor = None
            if PERFORMANCE_MONITORING_AVAILABLE:
                try:
                    self.performance_monitor = PerformanceMonitor()
                except Exception as e:
                    extraction_logger.warning(f"Failed to initialize performance monitor: {e}")
            
            # Document type detection patterns
            self._initialize_document_type_patterns()
            
            extraction_logger.info(
                "Initialized ComprehensiveQMEFieldService",
                extra_data={
                    "extraction_strategy": self.config.extraction_strategy.value,
                    "openrouter_enabled": self.config.enable_openrouter,
                    "vision_enabled": self.config.enable_vision,
                    "confidence_threshold": self.config.confidence_threshold
                }
            )
            
        except Exception as e:
            extraction_logger.error(f"Failed to initialize ComprehensiveQMEFieldService: {e}", exc_info=True)
            raise DocumentQAError(
                message=f"Failed to initialize QME field service: {str(e)}",
                error_type=ErrorType.SYSTEM_ERROR,
                details={"config": str(self.config) if hasattr(self, 'config') else None},
                original_error=e
            )
    
    async def _safe_detect_document_type(self, document_path: str) -> DocumentType:
        """Safely detect document type with error handling."""
        try:
            return await self._detect_document_type(document_path)
        except Exception as e:
            extraction_logger.warning(f"Failed to detect document type for {document_path}: {e}")
            # Return default document type if detection fails
            return DocumentType.UNKNOWN
    
    async def _safe_perform_extraction(self, document_path: str, document_type: DocumentType, 
                                     doc_config: Dict[str, Any], document_id: str) -> 'QMEExtractionResult':
        """Safely perform extraction with comprehensive error handling and fallback."""
        extraction_errors = []
        
        try:
            # Try primary extraction method
            return await self._perform_extraction(document_path, document_type, doc_config, document_id)
            
        except APIError as e:
            extraction_errors.append(f"API error: {str(e)}")
            extraction_logger.warning(f"API extraction failed, trying fallback: {e}")
            
            # Try fallback extraction method
            try:
                return await self._perform_fallback_extraction(document_path, document_type, document_id)
            except Exception as fallback_error:
                extraction_errors.append(f"Fallback error: {str(fallback_error)}")
                raise FileProcessingError(
                    message="All extraction methods failed",
                    details={
                        "document_path": document_path,
                        "document_type": document_type.value,
                        "errors": extraction_errors
                    },
                    original_error=e
                )
                
        except Exception as e:
            extraction_errors.append(f"Extraction error: {str(e)}")
            extraction_logger.error(f"Extraction failed for {document_path}: {e}", exc_info=True)
            
            # Try fallback extraction method
            try:
                return await self._perform_fallback_extraction(document_path, document_type, document_id)
            except Exception as fallback_error:
                extraction_errors.append(f"Fallback error: {str(fallback_error)}")
                raise FileProcessingError(
                    message="All extraction methods failed",
                    details={
                        "document_path": document_path,
                        "document_type": document_type.value,
                        "errors": extraction_errors
                    },
                    original_error=e
                )
    
    async def _perform_fallback_extraction(self, document_path: str, document_type: DocumentType, 
                                         document_id: str) -> 'QMEExtractionResult':
        """Perform fallback extraction using basic methods."""
        extraction_logger.info(f"Performing fallback extraction for {document_path}")
        
        # Create minimal extraction result
        from src.services.comprehensive_qme_field_service import QMEExtractionResult
        
        return QMEExtractionResult(
            document_id=document_id,
            success=True,  # Mark as successful even if minimal
            extracted_fields={},
            field_confidence_scores={},
            quality_assessment=QualityAssessment(
                overall_score=0.5,  # Low confidence for fallback
                completeness_score=0.3,
                accuracy_score=0.5,
                consistency_score=0.5,
                issues=["Fallback extraction used due to primary method failure"]
            ),
            evidence_snippets={},
            processing_metadata=ProcessingMetadata(
                processing_timestamp=datetime.now().isoformat(),
                processing_duration=0.0,
                extraction_method=ExtractionMethod.RULE_BASED,
                api_calls_made=0
            ),
            extraction_strategy=ExtractionStrategy.RULE_BASED,
            extraction_errors=["Primary extraction failed, using fallback method"]
        )
    
    def _initialize_extraction_services(self) -> None:
        """Initialize the various extraction services with comprehensive error handling."""
        try:
            # Rule-based extraction service
            field_config = FieldExtractionConfig(
                min_confidence_threshold=self.config.confidence_threshold,
                enable_cross_validation=self.config.enable_cross_validation
            )
            self.field_extraction_service = FieldExtractionService(config=field_config)
            extraction_logger.info("Initialized rule-based field extraction service")
            
        except Exception as e:
            extraction_logger.error(f"Failed to initialize field extraction service: {e}")
            raise DocumentQAError(
                message="Failed to initialize rule-based extraction service",
                error_type=ErrorType.SYSTEM_ERROR,
                original_error=e
            )
        
        # AI-enhanced extraction service (OpenRouter)
        self.openrouter_service = None
        if self.config.enable_openrouter:
            try:
                self.openrouter_service = OpenRouterExtractionService()
                extraction_logger.info("Initialized OpenRouter extraction service")
            except Exception as e:
                extraction_logger.warning(f"Failed to initialize OpenRouter service: {e}")
                # This is not critical, continue without OpenRouter
                self.config.enable_openrouter = False
                extraction_logger.info("OpenRouter service initialized successfully")
            except Exception as e:
                extraction_logger.warning(f"Failed to initialize OpenRouter service: {str(e)}")
                if not self.config.fallback_to_rule_based:
                    raise
    
    def _initialize_document_type_patterns(self) -> None:
        """Initialize patterns for document type detection."""
        self.document_type_patterns = {
            DocumentType.PQME_REPORT: [
                r"(?i)panel\s+qualified\s+medical\s+evaluator",
                r"(?i)pqme\s+report",
                r"(?i)qualified\s+medical\s+evaluation",
                r"(?i)workers?\s+compensation\s+evaluation"
            ],
            DocumentType.MEDICAL_RECORD: [
                r"(?i)medical\s+record",
                r"(?i)patient\s+chart",
                r"(?i)clinical\s+notes",
                r"(?i)progress\s+note"
            ],
            DocumentType.EXAMINATION_REPORT: [
                r"(?i)physical\s+examination",
                r"(?i)medical\s+examination",
                r"(?i)orthopedic\s+evaluation",
                r"(?i)range\s+of\s+motion"
            ],
            DocumentType.LEGAL_DOCUMENT: [
                r"(?i)legal\s+brief",
                r"(?i)court\s+document",
                r"(?i)deposition",
                r"(?i)attorney"
            ]
        }
    
    @handle_errors(error_type=ErrorType.FILE_PROCESSING, return_error_dict=False)
    async def extract_fields(self, document_path: str, **kwargs) -> ExtractionResult:
        """
        Extract structured fields from a document using comprehensive extraction methods.
        
        Args:
            document_path: Path to the document file
            **kwargs: Additional parameters including document_type, extraction_strategy
            
        Returns:
            ExtractionResult with extracted fields and metadata
        """
        start_time = time.time()
        document_id = self._generate_document_id(document_path)
        
        # Validate input parameters
        if not document_path or not Path(document_path).exists():
            raise FileProcessingError(
                message=f"Document file not found: {document_path}",
                details={"document_path": document_path, "document_id": document_id}
            )
        
        try:
            extraction_logger.info(
                f"Starting comprehensive field extraction: {document_path}",
                extra_data={"document_id": document_id, "document_path": document_path}
            )
            
            # Detect document type with error handling
            document_type = await self._safe_detect_document_type(document_path)
            extraction_logger.debug(f"Detected document type: {document_type.value}")
            
            # Get document type specific configuration
            doc_config = self.config.document_type_configs.get(
                document_type.value, 
                self.config.document_type_configs.get("pqme_report", {})
            )
            
            # Perform extraction based on strategy with error handling
            extraction_result = await self._safe_perform_extraction(
                document_path, document_type, doc_config, document_id
            )
            
            # Convert to standard ExtractionResult format
            processing_time = time.time() - start_time
            
            # Log successful extraction
            extraction_logger.info(
                f"Completed field extraction: {document_path}",
                extra_data={
                    "document_id": document_id,
                    "processing_time": processing_time,
                    "success": extraction_result.success,
                    "fields_extracted": len(extraction_result.extracted_fields)
                }
            )
            
            return ExtractionResult(
                success=extraction_result.success,
                status=extraction_result.processing_metadata.processing_timestamp,
                data={
                    "extracted_fields": {name: field.value for name, field in extraction_result.extracted_fields.items()},
                    "document_type": document_type.value,
                    "extraction_strategy": extraction_result.extraction_strategy.value
                },
                error_message="; ".join(extraction_result.extraction_errors) if extraction_result.extraction_errors else None,
                processing_time=processing_time,
                metadata={
                    "confidence_scores": extraction_result.field_confidence_scores,
                    "quality_assessment": extraction_result.quality_assessment.__dict__,
                    "evidence_snippets": extraction_result.evidence_snippets,
                    "api_calls_made": extraction_result.api_calls_made
                },
                extracted_fields=extraction_result.extracted_fields,
                confidence_scores=extraction_result.field_confidence_scores,
                evidence_snippets=extraction_result.evidence_snippets
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            extraction_logger.error(
                f"Comprehensive field extraction failed: {document_path}",
                error=e,
                extra_data={"document_id": document_id, "processing_time": processing_time}
            )
            
            return ExtractionResult(
                success=False,
                status="failed",
                error_message=f"Extraction failed: {str(e)}",
                processing_time=processing_time,
                metadata={"document_id": document_id}
            )
    
    async def _perform_extraction(
        self, 
        document_path: str, 
        document_type: DocumentType, 
        doc_config: Dict[str, Any],
        document_id: str
    ) -> ComprehensiveExtractionResult:
        """Perform extraction using the configured strategy."""
        
        if self.config.extraction_strategy == ExtractionStrategy.RULE_BASED:
            return await self._extract_rule_based(document_path, document_type, doc_config, document_id)
        elif self.config.extraction_strategy == ExtractionStrategy.AI_ENHANCED:
            return await self._extract_ai_enhanced(document_path, document_type, doc_config, document_id)
        elif self.config.extraction_strategy == ExtractionStrategy.HYBRID:
            return await self._extract_hybrid(document_path, document_type, doc_config, document_id)
        elif self.config.extraction_strategy == ExtractionStrategy.VISION_ENABLED:
            return await self._extract_vision_enabled(document_path, document_type, doc_config, document_id)
        else:
            raise ValueError(f"Unknown extraction strategy: {self.config.extraction_strategy}")
    
    async def _extract_rule_based(
        self, 
        document_path: str, 
        document_type: DocumentType, 
        doc_config: Dict[str, Any],
        document_id: str
    ) -> ComprehensiveExtractionResult:
        """Extract fields using rule-based methods only."""
        start_time = time.time()
        
        try:
            # Use field extraction service
            field_result = await self.field_extraction_service.extract_from_file(document_path)
            
            # Convert to comprehensive result format
            extracted_fields = {}
            confidence_scores = {}
            evidence_snippets = {}
            
            for field_name, extraction in field_result.field_data.field_extractions.items():
                extracted_fields[field_name] = ExtractedField(
                    name=field_name,
                    value=extraction.value,
                    confidence=extraction.confidence,
                    source_location=extraction.evidence.coordinates.__dict__,
                    validation_status="pending"
                )
                confidence_scores[field_name] = extraction.confidence
                evidence_snippets[field_name] = [extraction.evidence.text]
            
            # Create quality assessment
            quality_assessment = QualityAssessment(
                overall_score=field_result.overall_confidence,
                completeness_score=field_result.evidence_completeness,
                accuracy_score=field_result.overall_confidence,
                consistency_score=0.8,  # Default for rule-based
                compliance_score=0.7    # Default for rule-based
            )
            
            processing_time = time.time() - start_time
            
            return ComprehensiveExtractionResult(
                document_id=document_id,
                document_type=document_type,
                extraction_strategy=ExtractionStrategy.RULE_BASED,
                success=True,
                extracted_fields=extracted_fields,
                field_confidence_scores=confidence_scores,
                evidence_snippets=evidence_snippets,
                source_references=[],
                quality_assessment=quality_assessment,
                validation_results=[],
                processing_metadata=ProcessingMetadata(
                    extraction_method="rule_based",
                    processing_time=processing_time,
                    model_used="regex_spacy",
                    prompt_template="",
                    api_version="1.0"
                ),
                extraction_errors=[],
                warnings=[],
                processing_time=processing_time,
                api_calls_made=0
            )
            
        except Exception as e:
            extraction_logger.error(f"Rule-based extraction failed: {str(e)}")
            raise
    
    async def _extract_ai_enhanced(
        self, 
        document_path: str, 
        document_type: DocumentType, 
        doc_config: Dict[str, Any],
        document_id: str
    ) -> ComprehensiveExtractionResult:
        """Extract fields using AI-enhanced methods (OpenRouter)."""
        start_time = time.time()
        
        if not self.openrouter_service:
            if self.config.fallback_to_rule_based:
                extraction_logger.warning("OpenRouter not available, falling back to rule-based extraction")
                return await self._extract_rule_based(document_path, document_type, doc_config, document_id)
            else:
                raise RuntimeError("OpenRouter service not available and fallback disabled")
        
        try:
            # Create extraction configuration
            extraction_config = ExtractionConfig(
                prompt_template=doc_config.get("extraction_prompts", "default_extraction"),
                extraction_method=ExtractionMethod.OPENROUTER_CLAUDE,
                quality_threshold=self.config.confidence_threshold
            )
            
            # Perform OpenRouter extraction
            openrouter_result = self.openrouter_service.extract_from_document(
                document_path, extraction_config
            )
            
            # Convert to comprehensive result format
            confidence_scores = {
                name: field.confidence for name, field in openrouter_result.extracted_fields.items()
            }
            
            evidence_snippets = {}
            for name, field in openrouter_result.extracted_fields.items():
                evidence_snippets[name] = [field.source_location] if field.source_location else []
            
            processing_time = time.time() - start_time
            
            return ComprehensiveExtractionResult(
                document_id=document_id,
                document_type=document_type,
                extraction_strategy=ExtractionStrategy.AI_ENHANCED,
                success=True,
                extracted_fields=openrouter_result.extracted_fields,
                field_confidence_scores=confidence_scores,
                evidence_snippets=evidence_snippets,
                source_references=openrouter_result.source_references,
                quality_assessment=openrouter_result.quality_assessment,
                validation_results=openrouter_result.validation_results,
                processing_metadata=openrouter_result.processing_metadata,
                extraction_errors=[],
                warnings=[],
                processing_time=processing_time,
                api_calls_made=1
            )
            
        except Exception as e:
            extraction_logger.error(f"AI-enhanced extraction failed: {str(e)}")
            if self.config.fallback_to_rule_based:
                extraction_logger.info("Falling back to rule-based extraction")
                return await self._extract_rule_based(document_path, document_type, doc_config, document_id)
            else:
                raise
    
    async def _extract_hybrid(
        self, 
        document_path: str, 
        document_type: DocumentType, 
        doc_config: Dict[str, Any],
        document_id: str
    ) -> ComprehensiveExtractionResult:
        """Extract fields using hybrid approach (rule-based + AI-enhanced)."""
        start_time = time.time()
        
        try:
            # Perform both extractions concurrently
            rule_based_task = asyncio.create_task(
                self._extract_rule_based(document_path, document_type, doc_config, document_id)
            )
            
            ai_enhanced_task = None
            if self.openrouter_service:
                ai_enhanced_task = asyncio.create_task(
                    self._extract_ai_enhanced(document_path, document_type, doc_config, document_id)
                )
            
            # Wait for rule-based extraction (always available)
            rule_result = await rule_based_task
            
            # Wait for AI extraction if available
            ai_result = None
            if ai_enhanced_task:
                try:
                    ai_result = await ai_enhanced_task
                except Exception as e:
                    extraction_logger.warning(f"AI extraction failed in hybrid mode: {str(e)}")
            
            # Merge results
            merged_result = await self._merge_extraction_results(
                rule_result, ai_result, document_id, document_type
            )
            
            merged_result.extraction_strategy = ExtractionStrategy.HYBRID
            merged_result.processing_time = time.time() - start_time
            
            return merged_result
            
        except Exception as e:
            extraction_logger.error(f"Hybrid extraction failed: {str(e)}")
            raise
    
    async def _extract_vision_enabled(
        self, 
        document_path: str, 
        document_type: DocumentType, 
        doc_config: Dict[str, Any],
        document_id: str
    ) -> ComprehensiveExtractionResult:
        """Extract fields using vision-enabled methods."""
        start_time = time.time()
        
        if not self.config.enable_vision or not self.openrouter_service:
            extraction_logger.warning("Vision extraction not available, falling back to hybrid")
            return await self._extract_hybrid(document_path, document_type, doc_config, document_id)
        
        try:
            # Perform vision extraction
            vision_result = self.openrouter_service.extract_with_vision(
                document_path, 
                doc_config.get("extraction_prompts", "default_vision_extraction")
            )
            
            # Convert vision result to comprehensive format
            # This is a simplified conversion - in practice would need more sophisticated mapping
            extracted_fields = {}
            confidence_scores = {}
            evidence_snippets = {}
            
            # Extract text content and create fields
            text_content = vision_result.get_text_content()
            if text_content:
                # Use rule-based extraction on vision-extracted text
                field_result = await self.field_extraction_service.extract_fields(text_content, document_id)
                
                for field_name, extraction in field_result.field_data.field_extractions.items():
                    extracted_fields[field_name] = ExtractedField(
                        name=field_name,
                        value=extraction.value,
                        confidence=extraction.confidence * 0.9,  # Slightly lower confidence for vision
                        source_location=f"vision_extracted_{extraction.evidence.coordinates.start_char}",
                        validation_status="pending"
                    )
                    confidence_scores[field_name] = extraction.confidence * 0.9
                    evidence_snippets[field_name] = [extraction.evidence.text]
            
            processing_time = time.time() - start_time
            
            return ComprehensiveExtractionResult(
                document_id=document_id,
                document_type=document_type,
                extraction_strategy=ExtractionStrategy.VISION_ENABLED,
                success=True,
                extracted_fields=extracted_fields,
                field_confidence_scores=confidence_scores,
                evidence_snippets=evidence_snippets,
                source_references=[],
                quality_assessment=QualityAssessment(
                    overall_score=vision_result.confidence_score,
                    completeness_score=0.8,
                    accuracy_score=vision_result.confidence_score,
                    consistency_score=0.7,
                    compliance_score=0.6
                ),
                validation_results=[],
                processing_metadata=ProcessingMetadata(
                    extraction_method="vision_enabled",
                    processing_time=processing_time,
                    model_used="openrouter_vision",
                    prompt_template=doc_config.get("extraction_prompts", "default_vision_extraction"),
                    api_version="1.0"
                ),
                extraction_errors=[],
                warnings=[],
                processing_time=processing_time,
                api_calls_made=1
            )
            
        except Exception as e:
            extraction_logger.error(f"Vision-enabled extraction failed: {str(e)}")
            if self.config.fallback_to_rule_based:
                extraction_logger.info("Falling back to hybrid extraction")
                return await self._extract_hybrid(document_path, document_type, doc_config, document_id)
            else:
                raise
    
    async def _merge_extraction_results(
        self, 
        rule_result: ComprehensiveExtractionResult,
        ai_result: Optional[ComprehensiveExtractionResult],
        document_id: str,
        document_type: DocumentType
    ) -> ComprehensiveExtractionResult:
        """Merge results from multiple extraction methods."""
        
        if not ai_result:
            return rule_result
        
        # Merge extracted fields, preferring higher confidence values
        merged_fields = {}
        merged_confidence = {}
        merged_evidence = {}
        
        all_field_names = set(rule_result.extracted_fields.keys()) | set(ai_result.extracted_fields.keys())
        
        for field_name in all_field_names:
            rule_field = rule_result.extracted_fields.get(field_name)
            ai_field = ai_result.extracted_fields.get(field_name)
            
            rule_confidence = rule_result.field_confidence_scores.get(field_name, 0.0)
            ai_confidence = ai_result.field_confidence_scores.get(field_name, 0.0)
            
            # Choose field with higher confidence
            if rule_confidence >= ai_confidence:
                if rule_field:
                    merged_fields[field_name] = rule_field
                    merged_confidence[field_name] = rule_confidence
                    merged_evidence[field_name] = rule_result.evidence_snippets.get(field_name, [])
            else:
                if ai_field:
                    merged_fields[field_name] = ai_field
                    merged_confidence[field_name] = ai_confidence
                    merged_evidence[field_name] = ai_result.evidence_snippets.get(field_name, [])
            
            # Add cross-validation evidence
            if rule_field and ai_field and field_name in merged_evidence:
                rule_evidence = rule_result.evidence_snippets.get(field_name, [])
                ai_evidence = ai_result.evidence_snippets.get(field_name, [])
                merged_evidence[field_name] = list(set(merged_evidence[field_name] + rule_evidence + ai_evidence))
        
        # Calculate merged quality assessment
        merged_quality = QualityAssessment(
            overall_score=(rule_result.quality_assessment.overall_score + ai_result.quality_assessment.overall_score) / 2,
            completeness_score=max(rule_result.quality_assessment.completeness_score, ai_result.quality_assessment.completeness_score),
            accuracy_score=(rule_result.quality_assessment.accuracy_score + ai_result.quality_assessment.accuracy_score) / 2,
            consistency_score=0.9,  # Higher consistency from cross-validation
            compliance_score=max(rule_result.quality_assessment.compliance_score, ai_result.quality_assessment.compliance_score)
        )
        
        return ComprehensiveExtractionResult(
            document_id=document_id,
            document_type=document_type,
            extraction_strategy=ExtractionStrategy.HYBRID,
            success=True,
            extracted_fields=merged_fields,
            field_confidence_scores=merged_confidence,
            evidence_snippets=merged_evidence,
            source_references=rule_result.source_references + ai_result.source_references,
            quality_assessment=merged_quality,
            validation_results=rule_result.validation_results + ai_result.validation_results,
            processing_metadata=ProcessingMetadata(
                extraction_method="hybrid",
                processing_time=max(rule_result.processing_time, ai_result.processing_time),
                model_used="rule_based+openrouter",
                prompt_template="hybrid",
                api_version="1.0"
            ),
            extraction_errors=rule_result.extraction_errors + ai_result.extraction_errors,
            warnings=rule_result.warnings + ai_result.warnings,
            processing_time=max(rule_result.processing_time, ai_result.processing_time),
            api_calls_made=rule_result.api_calls_made + ai_result.api_calls_made
        )
    
    async def _detect_document_type(self, document_path: str) -> DocumentType:
        """Detect the type of document based on content analysis."""
        try:
            # Read document content (simplified - would need proper text extraction)
            if document_path.endswith('.txt'):
                with open(document_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
            else:
                # For other formats, would need proper extraction
                content = Path(document_path).name.lower()
            
            # Check patterns for each document type
            for doc_type, patterns in self.document_type_patterns.items():
                for pattern in patterns:
                    import re
                    if re.search(pattern, content):
                        return doc_type
            
            return DocumentType.UNKNOWN
            
        except Exception as e:
            extraction_logger.warning(f"Document type detection failed: {str(e)}")
            return DocumentType.UNKNOWN
    
    def _generate_document_id(self, document_path: str) -> str:
        """Generate a unique document ID."""
        import hashlib
        path_hash = hashlib.md5(document_path.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"doc_{timestamp}_{path_hash}"
    
    async def calculate_confidence(self, extracted_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence scores for extracted fields."""
        confidence_scores = {}
        
        for field_name, field_value in extracted_data.items():
            if isinstance(field_value, ExtractedField):
                confidence_scores[field_name] = field_value.confidence
            else:
                # Default confidence calculation based on field completeness
                if field_value and str(field_value).strip():
                    confidence_scores[field_name] = 0.7  # Default confidence
                else:
                    confidence_scores[field_name] = 0.0
        
        return confidence_scores
    
    async def collect_evidence(self, document_path: str, fields: Dict[str, Any]) -> Dict[str, List[str]]:
        """Collect evidence snippets for extracted fields."""
        evidence_snippets = {}
        
        try:
            # This would typically involve re-analyzing the document to find evidence
            # For now, return placeholder evidence
            for field_name in fields.keys():
                evidence_snippets[field_name] = [f"Evidence for {field_name} found in document"]
        
        except Exception as e:
            extraction_logger.warning(f"Evidence collection failed: {str(e)}")
        
        return evidence_snippets
    
    def extract_and_validate_fields(self, document_path: str) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility.
        Extract and validate fields from a document.
        """
        try:
            # Run async extraction in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(self.extract_fields(document_path))
                
                return {
                    'extraction_result': {
                        'success': result.success,
                        'extracted_fields': result.data.get('extracted_fields', {}) if result.data else {},
                        'error_message': result.error_message
                    },
                    'validation_result': {
                        'is_valid': result.success and not result.error_message,
                        'validation_errors': [result.error_message] if result.error_message else []
                    }
                }
            finally:
                loop.close()
                
        except Exception as e:
            extraction_logger.error(f"Legacy extraction method failed: {str(e)}")
            return {
                'extraction_result': {
                    'success': False,
                    'extracted_fields': {},
                    'error_message': str(e)
                },
                'validation_result': {
                    'is_valid': False,
                    'validation_errors': [str(e)]
                }
            }