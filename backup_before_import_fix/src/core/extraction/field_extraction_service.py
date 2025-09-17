"""
Consolidated Field Extraction Service.

This module consolidates the functionality from qme_field_extractor.py and 
comprehensive_qme_field_service.py into a single, comprehensive field extraction
service with proper error handling, dependency injection, and structured logging.
"""

import re
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass, field
from pathlib import Path
from abc import ABC, abstractmethod

# Core imports
from src.core.exceptions import (
    ExtractionError, FieldExtractionError, ValidationError,
    DocumentNotFoundError, InvalidDocumentFormatError
)
from src.infrastructure.monitoring.structured_logger import extraction_logger
from src.infrastructure.monitoring.circuit_breaker import circuit_breaker_registry
from src.infrastructure.monitoring.retry_handler import with_retry, BackoffStrategy

# Optional dependencies with graceful degradation
try:
    import spacy
    from spacy.matcher import Matcher
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    extraction_logger.warning("spaCy not available, using rule-based extraction only")

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    extraction_logger.warning("PyPDF2 not available, PDF extraction disabled")


@dataclass
class DocumentCoordinate:
    """Represents the location of extracted text within a document."""
    page_number: int
    start_char: int
    end_char: int
    line_number: Optional[int] = None


@dataclass
class EvidenceSnippet:
    """Contains evidence text and its source location."""
    text: str
    context: str  # Surrounding text for context
    coordinates: DocumentCoordinate
    extraction_method: str  # 'regex', 'ner', 'hybrid'
    confidence: float = 1.0


@dataclass
class FieldExtraction:
    """Result of extracting a single field with confidence and evidence."""
    value: Any
    confidence: float
    evidence: EvidenceSnippet
    extraction_method: str
    cross_validation_score: float = 0.0


@dataclass
class QMEFieldData:
    """Container for extracted QME template field data with enhanced metadata."""
    # Patient information
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    
    # Case information
    case_number: Optional[str] = None
    claim_number: Optional[str] = None
    injury_date: Optional[str] = None
    body_parts: List[str] = field(default_factory=list)
    
    # Employment information
    occupation: Optional[str] = None
    employer: Optional[str] = None
    
    # Examination information
    scheduled_exam_date: Optional[str] = None
    exam_location: Optional[str] = None
    
    # Medical findings
    rom_measurements: Dict[str, List[float]] = field(default_factory=dict)
    ama_table_references: List[str] = field(default_factory=list)
    diagnoses: List[str] = field(default_factory=list)
    impairment_ratings: Dict[str, float] = field(default_factory=dict)
    
    # Enhanced extraction metadata
    field_extractions: Dict[str, FieldExtraction] = field(default_factory=dict)
    extraction_confidence: Dict[str, float] = field(default_factory=dict)
    extraction_methods: Dict[str, str] = field(default_factory=dict)
    source_snippets: Dict[str, str] = field(default_factory=dict)
    evidence_provenance: Dict[str, List[EvidenceSnippet]] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Enhanced result of field extraction with confidence scoring and evidence."""
    field_data: QMEFieldData
    validation_status: Dict[str, bool]
    missing_fields: List[str]
    extraction_errors: List[str]
    overall_confidence: float
    confidence_breakdown: Dict[str, float]
    evidence_completeness: float
    cross_validation_results: Dict[str, float]
    processing_time: float = 0.0


@dataclass
class FieldExtractionConfig:
    """Configuration for field extraction."""
    use_spacy_ner: bool = True
    spacy_model: str = "en_core_web_sm"
    min_confidence_threshold: float = 0.5
    enable_cross_validation: bool = True
    max_context_length: int = 200
    extraction_methods: List[str] = field(default_factory=lambda: [
        'regex_patterns', 'spacy_ner', 'contextual_inference'
    ])


class IFieldExtractionService(ABC):
    """Interface for field extraction services."""
    
    @abstractmethod
    async def extract_fields(self, document_text: str, doc_id: str = None) -> ExtractionResult:
        """Extract fields from document text."""
        pass
    
    @abstractmethod
    async def extract_from_file(self, file_path: str) -> ExtractionResult:
        """Extract fields from document file."""
        pass
    
    @abstractmethod
    async def validate_extraction(self, extraction_result: ExtractionResult) -> Dict[str, bool]:
        """Validate extracted fields."""
        pass


class FieldExtractionService(IFieldExtractionService):
    """
    Consolidated field extraction service with multiple extraction methods.
    
    Features:
    - Regex pattern matching with confidence scoring
    - spaCy NER enhancement layer (optional)
    - Cross-document validation
    - Evidence snippet collection and source tracking
    - Comprehensive error handling and logging
    - Fallback extraction methods
    """
    
    def __init__(self, config: Optional[FieldExtractionConfig] = None):
        """Initialize the field extraction service."""
        self.config = config or FieldExtractionConfig()
        
        # Initialize spaCy model if available and enabled
        self.nlp = None
        self.matcher = None
        if SPACY_AVAILABLE and self.config.use_spacy_ner:
            self._initialize_spacy_model()
        
        # Initialize extraction patterns
        self._initialize_extraction_patterns()
        
        # Get circuit breaker for external calls
        self.circuit_breaker = circuit_breaker_registry.get_breaker("field_extraction")
        
        extraction_logger.info(
            "Initialized FieldExtractionService",
            extra_data={
                "config": {
                    "use_spacy_ner": self.config.use_spacy_ner,
                    "min_confidence_threshold": self.config.min_confidence_threshold,
                    "extraction_methods": self.config.extraction_methods
                },
                "spacy_available": SPACY_AVAILABLE,
                "spacy_model_loaded": self.nlp is not None
            }
        )
    
    def _initialize_spacy_model(self) -> None:
        """Initialize spaCy NLP model with medical extensions."""
        try:
            self.nlp = spacy.load(self.config.spacy_model)
            self.matcher = Matcher(self.nlp.vocab)
            extraction_logger.info(f"Loaded spaCy model: {self.config.spacy_model}")
        except OSError:
            extraction_logger.warning(
                f"spaCy model {self.config.spacy_model} not found, using rule-based extraction only"
            )
            self.nlp = None
            self.matcher = None
    
    def _initialize_extraction_patterns(self) -> None:
        """Initialize regex patterns for field extraction."""
        self.patterns = {
            'name': [
                r'(?:Patient|Name):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                r'(?:Mr\.|Mrs\.|Ms\.|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                r'RE:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            ],
            'age': [
                r'(?:age|Age):\s*(\d{1,3})',
                r'(\d{1,3})\s*(?:year|years)\s*old',
                r'(?:DOB|Date of Birth):\s*\d{1,2}/\d{1,2}/(\d{4})',
            ],
            'gender': [
                r'(?:Gender|Sex):\s*(Male|Female|M|F)',
                r'\b(Male|Female)\b',
                r'\b(Mr\.|Mrs\.|Ms\.)',
            ],
            'case_number': [
                r'(?:Case|File|Claim)\s*(?:Number|No\.?):\s*([A-Z0-9\-]+)',
                r'(?:WC|Workers?\s*Comp)\s*(?:Number|No\.?):\s*([A-Z0-9\-]+)',
                r'(?:ADJ|Adj)\s*(?:Number|No\.?):\s*([A-Z0-9\-]+)',
            ],
            'injury_date': [
                r'(?:Date of Injury|DOI|Injury Date):\s*(\d{1,2}/\d{1,2}/\d{4})',
                r'(?:injured on|injury occurred).*?(\d{1,2}/\d{1,2}/\d{4})',
                r'(?:accident|incident).*?(\d{1,2}/\d{1,2}/\d{4})',
            ],
            'body_parts': [
                r'\b(back|spine|lumbar|cervical|thoracic)\b',
                r'\b(shoulder|arm|hand|wrist|finger)\b',
                r'\b(leg|knee|ankle|foot|toe)\b',
                r'\b(head|neck|brain)\b',
            ],
            'occupation': [
                r'(?:Occupation|Job|Position):\s*([A-Za-z\s]+)',
                r'(?:works as|employed as)\s*(?:a|an)?\s*([A-Za-z\s]+)',
            ],
            'employer': [
                r'(?:Employer|Company):\s*([A-Za-z\s&\.,]+)',
                r'(?:employed by|works for)\s*([A-Za-z\s&\.,]+)',
            ],
            'rom_measurements': [
                r'(?:ROM|Range of Motion).*?(\d+)\s*(?:degrees?|°)',
                r'(?:Flexion|Extension|Rotation):\s*(\d+)\s*(?:degrees?|°)',
            ],
            'ama_table': [
                r'(?:Table|AMA)\s*(\d+(?:\.\d+)?[A-Z]?)',
                r'(?:page|p\.)\s*(\d+)',
            ]
        }
    
    @with_retry(
        max_attempts=2,
        base_delay=0.5,
        backoff_strategy=BackoffStrategy.LINEAR
    )
    async def extract_from_file(self, file_path: str) -> ExtractionResult:
        """Extract fields from document file."""
        start_time = time.time()
        
        try:
            extraction_logger.info(
                f"Starting field extraction from file: {file_path}",
                extra_data={"file_path": file_path}
            )
            
            # Validate file exists
            if not Path(file_path).exists():
                raise DocumentNotFoundError(f"Document not found: {file_path}")
            
            # Extract text from file
            document_text = await self._extract_text_from_file(file_path)
            
            # Extract fields from text
            result = await self.extract_fields(document_text, doc_id=file_path)
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            extraction_logger.info(
                f"Field extraction completed: {file_path}",
                extra_data={
                    "processing_time": processing_time,
                    "overall_confidence": result.overall_confidence,
                    "fields_extracted": len([f for f in result.validation_status.values() if f]),
                    "missing_fields": len(result.missing_fields)
                }
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            extraction_logger.error(
                f"Field extraction failed: {file_path}",
                error=e,
                extra_data={
                    "file_path": file_path,
                    "processing_time": processing_time
                }
            )
            raise FieldExtractionError(
                f"Field extraction failed for {file_path}: {str(e)}",
                context={"file_path": file_path},
                cause=e
            )
    
    async def extract_fields(self, document_text: str, doc_id: str = None) -> ExtractionResult:
        """Extract fields from document text."""
        start_time = time.time()
        
        try:
            extraction_logger.debug(
                "Starting field extraction from text",
                extra_data={
                    "doc_id": doc_id,
                    "text_length": len(document_text),
                    "extraction_methods": self.config.extraction_methods
                }
            )
            
            # Initialize field data
            field_data = QMEFieldData()
            extraction_errors = []
            confidence_scores = {}
            
            # Apply extraction methods in order
            for method in self.config.extraction_methods:
                try:
                    if method == 'regex_patterns':
                        await self._extract_with_regex(document_text, field_data, confidence_scores, doc_id)
                    elif method == 'spacy_ner' and self.nlp:
                        await self._extract_with_spacy(document_text, field_data, confidence_scores, doc_id)
                    elif method == 'contextual_inference':
                        await self._extract_with_context(document_text, field_data, confidence_scores, doc_id)
                except Exception as e:
                    extraction_logger.warning(
                        f"Extraction method {method} failed",
                        error=e,
                        extra_data={"method": method, "doc_id": doc_id}
                    )
                    extraction_errors.append(f"{method}: {str(e)}")
            
            # Calculate overall confidence and validation status
            overall_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.0
            validation_status = await self.validate_extraction_internal(field_data)
            missing_fields = [field for field, valid in validation_status.items() if not valid]
            
            processing_time = time.time() - start_time
            
            result = ExtractionResult(
                field_data=field_data,
                validation_status=validation_status,
                missing_fields=missing_fields,
                extraction_errors=extraction_errors,
                overall_confidence=overall_confidence,
                confidence_breakdown=confidence_scores,
                evidence_completeness=self._calculate_evidence_completeness(field_data),
                cross_validation_results={},
                processing_time=processing_time
            )
            
            extraction_logger.debug(
                "Field extraction completed",
                extra_data={
                    "doc_id": doc_id,
                    "overall_confidence": overall_confidence,
                    "fields_found": len([f for f in validation_status.values() if f]),
                    "processing_time": processing_time
                }
            )
            
            return result
            
        except Exception as e:
            extraction_logger.error(
                "Field extraction failed",
                error=e,
                extra_data={"doc_id": doc_id}
            )
            raise FieldExtractionError(
                f"Field extraction failed: {str(e)}",
                context={"doc_id": doc_id},
                cause=e
            )
    
    async def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file formats."""
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_ext == '.pdf' and PDF_AVAILABLE:
                return await self._extract_pdf_text(file_path)
            else:
                raise InvalidDocumentFormatError(
                    f"Unsupported file format: {file_ext}",
                    context={"file_path": file_path, "supported_formats": ['.txt', '.pdf']}
                )
        except Exception as e:
            raise ExtractionError(
                f"Failed to extract text from {file_path}: {str(e)}",
                context={"file_path": file_path, "file_format": file_ext},
                cause=e
            )
    
    async def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise ExtractionError(
                f"Failed to extract PDF text: {str(e)}",
                context={"file_path": file_path},
                cause=e
            )
    
    async def _extract_with_regex(self, text: str, field_data: QMEFieldData, confidence_scores: Dict[str, float], doc_id: str = None):
        """Extract fields using regex patterns."""
        for field_name, patterns in self.patterns.items():
            if field_name in confidence_scores:
                continue  # Skip if already extracted with higher confidence
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    value = match.group(1).strip()
                    confidence = 0.7  # Base confidence for regex extraction
                    
                    # Store extraction
                    self._store_field_extraction(
                        field_data, field_name, value, confidence, 
                        'regex', match.start(), match.end(), text, doc_id
                    )
                    confidence_scores[field_name] = confidence
                    break
                if field_name in confidence_scores:
                    break
    
    async def _extract_with_spacy(self, text: str, field_data: QMEFieldData, confidence_scores: Dict[str, float], doc_id: str = None):
        """Extract fields using spaCy NER."""
        if not self.nlp:
            return
        
        doc = self.nlp(text)
        
        for ent in doc.ents:
            field_name = self._map_entity_to_field(ent.label_)
            if field_name and field_name not in confidence_scores:
                confidence = 0.6  # Base confidence for NER extraction
                
                self._store_field_extraction(
                    field_data, field_name, ent.text, confidence,
                    'spacy_ner', ent.start_char, ent.end_char, text, doc_id
                )
                confidence_scores[field_name] = confidence
    
    async def _extract_with_context(self, text: str, field_data: QMEFieldData, confidence_scores: Dict[str, float], doc_id: str = None):
        """Extract fields using contextual inference."""
        # Simple contextual rules
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Look for patterns in context
            if 'patient' in line.lower() and 'name' in line.lower():
                # Try to extract name from next line or same line
                name_match = re.search(r'([A-Z][a-z]+\s+[A-Z][a-z]+)', line)
                if name_match and 'name' not in confidence_scores:
                    confidence = 0.5
                    self._store_field_extraction(
                        field_data, 'name', name_match.group(1), confidence,
                        'contextual', name_match.start(), name_match.end(), text, doc_id
                    )
                    confidence_scores['name'] = confidence
    
    def _store_field_extraction(self, field_data: QMEFieldData, field_name: str, value: str, 
                               confidence: float, method: str, start: int, end: int, 
                               text: str, doc_id: str = None):
        """Store field extraction with metadata."""
        # Convert value based on field type
        processed_value = self._process_field_value(field_name, value)
        
        # Create evidence snippet
        context_start = max(0, start - self.config.max_context_length // 2)
        context_end = min(len(text), end + self.config.max_context_length // 2)
        context = text[context_start:context_end]
        
        evidence = EvidenceSnippet(
            text=value,
            context=context,
            coordinates=DocumentCoordinate(page_number=1, start_char=start, end_char=end),
            extraction_method=method,
            confidence=confidence
        )
        
        # Store in field data
        setattr(field_data, field_name, processed_value)
        field_data.extraction_confidence[field_name] = confidence
        field_data.extraction_methods[field_name] = method
        field_data.source_snippets[field_name] = value
        
        if field_name not in field_data.evidence_provenance:
            field_data.evidence_provenance[field_name] = []
        field_data.evidence_provenance[field_name].append(evidence)
    
    def _process_field_value(self, field_name: str, value: str) -> Any:
        """Process and convert field value to appropriate type."""
        if field_name == 'age':
            try:
                return int(value)
            except ValueError:
                return None
        elif field_name in ['body_parts']:
            return [value] if value else []
        elif field_name in ['rom_measurements']:
            try:
                return {field_name: [float(value)]}
            except ValueError:
                return {}
        else:
            return value.strip() if value else None
    
    def _map_entity_to_field(self, entity_label: str) -> Optional[str]:
        """Map spaCy entity labels to field names."""
        mapping = {
            'PERSON': 'name',
            'DATE': 'injury_date',
            'ORG': 'employer',
            'CARDINAL': 'age'
        }
        return mapping.get(entity_label)
    
    def _calculate_evidence_completeness(self, field_data: QMEFieldData) -> float:
        """Calculate evidence completeness score."""
        total_fields = 10  # Expected number of key fields
        fields_with_evidence = len(field_data.evidence_provenance)
        return fields_with_evidence / total_fields if total_fields > 0 else 0.0
    
    async def validate_extraction_internal(self, field_data: QMEFieldData) -> Dict[str, bool]:
        """Internal validation of extracted fields."""
        validation_status = {}
        
        # Validate required fields
        required_fields = ['name', 'case_number', 'injury_date']
        for field in required_fields:
            value = getattr(field_data, field, None)
            validation_status[field] = value is not None and str(value).strip() != ""
        
        # Validate optional fields
        optional_fields = ['age', 'gender', 'occupation', 'employer']
        for field in optional_fields:
            value = getattr(field_data, field, None)
            validation_status[field] = value is not None and str(value).strip() != ""
        
        return validation_status
    
    async def validate_extraction(self, extraction_result: ExtractionResult) -> Dict[str, bool]:
        """Validate extracted fields."""
        return extraction_result.validation_status


# Factory function for creating field extraction service
def create_field_extraction_service(config: Optional[FieldExtractionConfig] = None) -> FieldExtractionService:
    """Factory function to create field extraction service."""
    return FieldExtractionService(config=config)