"""
QME Field Extractor - Enhanced extraction with confidence scoring and evidence provenance.

This module implements robust pattern matching and NLP extraction for specific
QME template fields from advocacy letters and PQME documents with confidence
scoring and evidence tracking.
"""

import re
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass, field
import spacy
from spacy.matcher import Matcher
from pathlib import Path

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


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
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    case_number: Optional[str] = None
    claim_number: Optional[str] = None
    injury_date: Optional[str] = None
    body_parts: List[str] = field(default_factory=list)
    occupation: Optional[str] = None
    employer: Optional[str] = None
    scheduled_exam_date: Optional[str] = None
    rom_measurements: Dict[str, List[float]] = field(default_factory=dict)
    ama_table_references: List[str] = field(default_factory=list)
    
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


class QMEFieldExtractor:
    """
    Enhanced QME field extractor with confidence scoring and evidence provenance.
    
    Implements:
    - Regex pattern matching with confidence scoring
    - spaCy NER enhancement layer
    - Cross-document validation
    - Evidence snippet collection and source tracking
    - Confidence calculation algorithm (regex: 0.6, NER: 0.3, cross-validation: 0.1)
    """
    
    def __init__(self, spacy_model: str = "en_core_web_sm"):
        """Initialize the enhanced QME field extractor."""
        self.spacy_model_name = spacy_model
        self.nlp = None
        self.matcher = None
        
        # Load extraction patterns from legal_patterns.json
        self.extraction_patterns = self._load_extraction_patterns()
        
        # Initialize NLP components
        self._initialize_nlp()
        self._initialize_patterns()
        
        # Required fields for QME template
        self.required_fields = [
            'name', 'age', 'gender', 'case_number', 'claim_number',
            'injury_date', 'body_parts', 'occupation', 'employer', 'scheduled_exam_date',
            'rom_measurements', 'ama_table_references'
        ]
        
        # Confidence weights for algorithm (as specified in requirements)
        self.confidence_weights = {
            'regex': 0.6,
            'ner': 0.3,
            'cross_validation': 0.1
        }
        
        # Confidence thresholds for validation
        self.confidence_thresholds = {
            'critical_fields': 0.8,  # Critical fields like name, case_number, injury_date
            'standard_fields': 0.5,  # Standard fields
            'flagged_review': 0.5    # Fields below this need human review
        }
        
        # Critical fields that require higher confidence
        self.critical_fields = ['name', 'case_number', 'injury_date', 'body_parts']
    
    def _load_extraction_patterns(self) -> Dict[str, Any]:
        """Load extraction patterns from legal_patterns.json."""
        try:
            patterns_path = Path(__file__).parent.parent.parent / "data" / "qme_references" / "legal_patterns.json"
            with open(patterns_path, 'r') as f:
                data = json.load(f)
                return data.get('extraction_patterns', {})
        except Exception as e:
            logger.warning(f"Could not load extraction patterns: {e}")
            return {}
    
    def _initialize_nlp(self) -> None:
        """Initialize spaCy NLP model."""
        try:
            self.nlp = spacy.load(self.spacy_model_name)
            self.matcher = Matcher(self.nlp.vocab)
            logger.info(f"Loaded spaCy model: {self.spacy_model_name}")
        except OSError:
            logger.warning(f"spaCy model {self.spacy_model_name} not found")
            self.nlp = None
            self.matcher = None
    
    def _initialize_patterns(self) -> None:
        """Initialize extraction patterns for QME fields."""
        
        # Name patterns - multiple formats
        self.name_patterns = [
            # "Applicant: Nick Diaz Jr."
            r'(?:Applicant|Patient|Name):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*(?:\s+Jr\.|\s+Sr\.|\s+III?)?)',
            # "Re: Applicant: Nick Diaz Jr."
            r'Re:\s*Applicant:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*(?:\s+Jr\.|\s+Sr\.|\s+III?)?)',
            # Direct name in context
            r'the applicant,?\s*([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+Jr\.|\s+Sr\.|\s+III?)?)',
            # Name followed by comma and age
            r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+Jr\.|\s+Sr\.|\s+III?)?),?\s*(?:a\s*)?(\d{2})[- ]year[- ]old',
        ]
        
        # Age patterns
        self.age_patterns = [
            # "43-year-old" or "43 year old"
            r'(\d{2})[- ]year[- ]old',
            # "age 43" or "Age: 43"
            r'(?:age|Age):\s*(\d{2})',
            # "was a 43-year-old"
            r'was\s+a\s+(\d{2})[- ]year[- ]old',
        ]
        
        # Gender patterns
        self.gender_patterns = [
            # Direct gender specification
            r'(?:Gender|Sex):\s*(Male|Female|M|F)',
            # Contextual gender (Mr./Mrs./Ms.)
            r'\b(Mr\.|Mrs\.|Ms\.)\s+[A-Z]',
            # Pronoun-based inference
            r'\b(he|she|his|her|him)\b',
        ]
        
        # Case/Claim number patterns
        self.case_number_patterns = [
            # "EAMS No: ADJ19802400"
            r'EAMS\s+No:\s*([A-Z0-9]+)',
            # "Case No:" or "Case Number:"
            r'Case\s+(?:No|Number):\s*([A-Z0-9-]+)',
            # "ADJ" followed by numbers
            r'\b(ADJ\d+)\b',
        ]
        
        self.claim_number_patterns = [
            # "Claim No: WC608-H07190"
            r'Claim\s+No:\s*([A-Z0-9-]+)',
            # "WC" followed by numbers and hyphens
            r'\b(WC\d+[A-Z0-9-]*)\b',
            # General claim pattern
            r'Claim\s+(?:Number|#):\s*([A-Z0-9-]+)',
        ]
        
        # Injury date patterns
        self.injury_date_patterns = [
            # "July 24, 2024"
            r'(?:injury|injured)\s+on\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})',
            # "Date of injury: 07/24/2024"
            r'(?:Date\s+of\s+injury|Injury\s+date):\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
            # "sustained an injury on July 24, 2024"
            r'sustained.*?(?:injury|accident).*?on\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})',
            # ISO date format
            r'(?:injury|injured).*?(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})',
        ]
        
        # Body part patterns
        self.body_part_patterns = [
            # "left knee injury"
            r'(?:sustained|suffered).*?((?:left|right|bilateral)?\s*(?:knee|shoulder|back|neck|ankle|wrist|hand|foot|hip|elbow|spine|lumbar|cervical|thoracic))\s+(?:injury|pain|condition)',
            # Direct body part mention
            r'\b((?:left|right|bilateral)?\s*(?:knee|shoulder|back|neck|ankle|wrist|hand|foot|hip|elbow|spine|lumbar|cervical|thoracic))\b',
            # Injury to body part
            r'injury\s+to\s+(?:the\s+)?((?:left|right|bilateral)?\s*(?:knee|shoulder|back|neck|ankle|wrist|hand|foot|hip|elbow|spine|lumbar|cervical|thoracic))',
        ]
        
        # Occupation patterns
        self.occupation_patterns = [
            # "was a 43-year-old front-end supervisor for"
            r'(?:\d{2}[- ]year[- ]old\s+)([a-zA-Z\-\s]+?)(?:\s+for|\s+at|\s+with)',
            # "Occupation: Front-End Supervisor"
            r'Occupation:\s*([A-Z][a-zA-Z\-\s]+)',
            # Job title context - more specific
            r'([a-zA-Z\-]+(?:\s+[a-zA-Z\-]+)*)\s+for\s+(?:a\s+)?(?:Costco|company|employer)',
        ]
        
        # Employer patterns
        self.employer_patterns = [
            # "Employer: Costco"
            r'Employer:\s*([A-Z][a-zA-Z\s&.,]+?)(?:\s+Venue|\s+EAMS|\s*$)',
            # "for Costco warehouse"
            r'for\s+([A-Z][a-zA-Z\s&.,]+?)(?:\s+warehouse|\s+in|\s+located)',
            # "worked at Costco"
            r'(?:worked\s+at|employed\s+by)\s+([A-Z][a-zA-Z\s&.,]+)',
        ]
        
        # Scheduled exam date patterns
        self.exam_date_patterns = [
            # "scheduled to take place on September 9, 2025"
            r'scheduled\s+to\s+take\s+place\s+on\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})',
            # "examination is scheduled for September 9, 2025"
            r'examination.*?scheduled.*?(?:for|on)\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})',
            # "Exam Date: 09/09/2025"
            r'Exam\s+Date:\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
            # "at 09:00 a.m. on September 9, 2025"
            r'at\s+\d{1,2}:\d{2}\s+[ap]\.?m\.?\s+(?:on\s+)?([A-Z][a-z]+\s+\d{1,2},\s+\d{4})',
        ]
    
    def extract_qme_fields(self, text: str, doc_id: str = None) -> ExtractionResult:
        """
        Extract all QME template fields from document text with enhanced confidence scoring.
        
        Args:
            text: Document text content
            doc_id: Document identifier for tracking
            
        Returns:
            ExtractionResult with enhanced confidence metrics and evidence
        """
        logger.info(f"Extracting QME fields from document {doc_id}")
        
        # Initialize field data container
        field_data = QMEFieldData()
        
        # Use structured extractor for enhanced extraction if available
        try:
            from .structured_extractor import StructuredExtractor, ExtractionContext
            
            structured_extractor = StructuredExtractor(self.spacy_model_name)
            context = ExtractionContext(
                document_id=doc_id or "unknown",
                document_text=text,
                page_count=1,
                source_file=None
            )
            
            # Perform enhanced extraction
            enhanced_result = structured_extractor.extract_with_confidence(context)
            
            # Fallback to legacy extraction for any missing critical fields
            self._enhance_with_legacy_extraction(enhanced_result.field_data, text)
            
            # Re-validate after enhancement
            validation_result = self._validate_fields(enhanced_result.field_data)
            
            # Update result with any legacy enhancements
            enhanced_result.validation_status = validation_result['validation_status']
            enhanced_result.missing_fields = validation_result['missing_fields']
            enhanced_result.extraction_errors = validation_result['extraction_errors']
            
            return enhanced_result
            
        except ImportError as e:
            logger.warning(f"Structured extractor not available, using legacy extraction: {e}")
            # Fall back to legacy extraction
            pass
        
        # Legacy extraction fallback
        field_data.name = self._extract_name(text)
        field_data.age = self._extract_age(text)
        field_data.gender = self._extract_gender(text)
        field_data.case_number = self._extract_case_number(text)
        field_data.claim_number = self._extract_claim_number(text)
        field_data.injury_date = self._extract_injury_date(text)
        field_data.body_parts = self._extract_body_parts(text)
        field_data.occupation = self._extract_occupation(text)
        field_data.employer = self._extract_employer(text)
        field_data.scheduled_exam_date = self._extract_exam_date(text)
        
        # Validate extracted fields
        validation_result = self._validate_fields(field_data)
        
        return ExtractionResult(
            field_data=field_data,
            validation_status=validation_result['validation_status'],
            missing_fields=validation_result['missing_fields'],
            extraction_errors=validation_result['extraction_errors'],
            overall_confidence=validation_result['overall_confidence'],
            confidence_breakdown={},
            evidence_completeness=0.0,
            cross_validation_results={}
        )
    
    def _enhance_with_legacy_extraction(self, field_data: QMEFieldData, text: str) -> None:
        """Enhance extraction results with legacy methods for missing fields."""
        # Only use legacy methods for fields that are missing or have low confidence
        
        if not field_data.name:
            field_data.name = self._extract_name(text)
            
        if not field_data.age:
            field_data.age = self._extract_age(text)
            
        if not field_data.gender:
            field_data.gender = self._extract_gender(text)
            
        if not field_data.case_number:
            field_data.case_number = self._extract_case_number(text)
            
        if not field_data.claim_number:
            field_data.claim_number = self._extract_claim_number(text)
            
        if not field_data.injury_date:
            field_data.injury_date = self._extract_injury_date(text)
            
        if not field_data.body_parts:
            field_data.body_parts = self._extract_body_parts(text)
            
        if not field_data.occupation:
            field_data.occupation = self._extract_occupation(text)
            
        if not field_data.employer:
            field_data.employer = self._extract_employer(text)
            
        if not field_data.scheduled_exam_date:
            field_data.scheduled_exam_date = self._extract_exam_date(text)
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract patient name using multiple pattern approaches."""
        for pattern in self.name_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                if self._is_valid_name(name):
                    logger.debug(f"Extracted name: {name}")
                    return name
        
        # Fallback: Use spaCy NER if available
        if self.nlp:
            return self._extract_name_spacy(text)
        
        return None
    
    def _extract_age(self, text: str) -> Optional[int]:
        """Extract patient age."""
        for pattern in self.age_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    age = int(match.group(1))
                    if 18 <= age <= 100:  # Reasonable age range
                        logger.debug(f"Extracted age: {age}")
                        return age
                except ValueError:
                    continue
        return None
    
    def _extract_gender(self, text: str) -> Optional[str]:
        """Extract patient gender."""
        # Direct gender patterns
        for pattern in self.gender_patterns[:2]:  # Skip pronoun patterns for now
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                gender_text = match.group(1).upper()
                if gender_text in ['MALE', 'M', 'MR.']:
                    return 'Male'
                elif gender_text in ['FEMALE', 'F', 'MRS.', 'MS.']:
                    return 'Female'
        
        # Pronoun-based inference (lower confidence)
        male_pronouns = re.findall(r'\b(he|his|him)\b', text, re.IGNORECASE)
        female_pronouns = re.findall(r'\b(she|her)\b', text, re.IGNORECASE)
        
        # Be more lenient with pronoun detection
        if len(male_pronouns) > len(female_pronouns) and len(male_pronouns) >= 1:
            logger.debug(f"Inferred gender 'Male' from pronouns: {male_pronouns}")
            return 'Male'
        elif len(female_pronouns) > len(male_pronouns) and len(female_pronouns) >= 1:
            logger.debug(f"Inferred gender 'Female' from pronouns: {female_pronouns}")
            return 'Female'
        
        return None
    
    def _extract_case_number(self, text: str) -> Optional[str]:
        """Extract case number."""
        for pattern in self.case_number_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                case_num = match.group(1).strip()
                logger.debug(f"Extracted case number: {case_num}")
                return case_num
        return None
    
    def _extract_claim_number(self, text: str) -> Optional[str]:
        """Extract claim number."""
        for pattern in self.claim_number_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                claim_num = match.group(1).strip()
                logger.debug(f"Extracted claim number: {claim_num}")
                return claim_num
        return None
    
    def _extract_injury_date(self, text: str) -> Optional[str]:
        """Extract injury date."""
        for pattern in self.injury_date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1).strip()
                # Normalize date format
                normalized_date = self._normalize_date(date_str)
                if normalized_date:
                    logger.debug(f"Extracted injury date: {normalized_date}")
                    return normalized_date
        return None
    
    def _extract_body_parts(self, text: str) -> List[str]:
        """Extract injured body parts."""
        body_parts = set()
        
        for pattern in self.body_part_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                body_part = match.group(1).strip().lower()
                # Clean up and normalize
                body_part = re.sub(r'\s+', ' ', body_part)
                if len(body_part) > 2:
                    body_parts.add(body_part.title())
        
        result = list(body_parts)
        if result:
            logger.debug(f"Extracted body parts: {result}")
        return result
    
    def _extract_occupation(self, text: str) -> Optional[str]:
        """Extract patient occupation."""
        for pattern in self.occupation_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                occupation = match.group(1).strip()
                # Clean up occupation text
                occupation = re.sub(r'\s+', ' ', occupation).title()
                if len(occupation) > 2 and not occupation.lower() in ['a', 'an', 'the']:
                    logger.debug(f"Extracted occupation: {occupation}")
                    return occupation
        return None
    
    def _extract_employer(self, text: str) -> Optional[str]:
        """Extract employer name."""
        for pattern in self.employer_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                employer = match.group(1).strip()
                # Clean up employer name
                employer = re.sub(r'\s+', ' ', employer)
                if len(employer) > 2:
                    logger.debug(f"Extracted employer: {employer}")
                    return employer
        return None
    
    def _extract_exam_date(self, text: str) -> Optional[str]:
        """Extract scheduled examination date."""
        for pattern in self.exam_date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1).strip()
                # Normalize date format
                normalized_date = self._normalize_date(date_str)
                if normalized_date:
                    logger.debug(f"Extracted exam date: {normalized_date}")
                    return normalized_date
        return None
    
    def _extract_name_spacy(self, text: str) -> Optional[str]:
        """Extract name using spaCy NER as fallback."""
        if not self.nlp:
            return None
        
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON" and self._is_valid_name(ent.text):
                return ent.text.strip()
        return None
    
    def _is_valid_name(self, name: str) -> bool:
        """Validate if extracted text is a valid person name."""
        if not name or len(name) < 3:
            return False
        
        # Check for common non-name patterns
        invalid_patterns = [
            r'^\d+',  # Starts with number
            r'[<>@#$%^&*()]',  # Contains special characters
            r'^(the|and|or|of|in|at|to|for|with|by)'  # Common words
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return False
        
        # Should contain at least one capital letter
        if not re.search(r'[A-Z]', name):
            return False
        
        return True
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize date string to consistent format."""
        if not date_str:
            return None
        
        # Handle different date formats
        date_patterns = [
            (r'([A-Z][a-z]+)\s+(\d{1,2}),\s+(\d{4})', r'\1 \2, \3'),  # "July 24, 2024"
            (r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', r'\1/\2/\3'),     # "07/24/2024"
            (r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})', r'\2/\3/\1'),     # "2024/07/24"
        ]
        
        for pattern, replacement in date_patterns:
            match = re.match(pattern, date_str)
            if match:
                return re.sub(pattern, replacement, date_str)
        
        return date_str
    
    def _validate_fields(self, field_data: QMEFieldData) -> Dict[str, Any]:
        """Validate extracted field data and calculate confidence scores."""
        validation_status = {}
        missing_fields = []
        extraction_errors = []
        
        # Check each required field
        for field_name in self.required_fields:
            field_value = getattr(field_data, field_name)
            
            if field_value is None or (isinstance(field_value, (list, dict)) and not field_value):
                validation_status[field_name] = False
                missing_fields.append(field_name)
            else:
                validation_status[field_name] = True
        
        # Calculate overall confidence using extraction confidence if available
        if field_data.extraction_confidence:
            # Use weighted confidence from extractions
            total_confidence = 0.0
            confidence_count = 0
            
            for field_name in self.required_fields:
                if field_name in field_data.extraction_confidence:
                    total_confidence += field_data.extraction_confidence[field_name]
                    confidence_count += 1
            
            overall_confidence = total_confidence / confidence_count if confidence_count > 0 else 0.0
        else:
            # Fallback to simple field count ratio
            valid_fields = sum(validation_status.values())
            total_fields = len(self.required_fields)
            overall_confidence = valid_fields / total_fields if total_fields > 0 else 0.0
        
        return {
            'validation_status': validation_status,
            'missing_fields': missing_fields,
            'extraction_errors': extraction_errors,
            'overall_confidence': overall_confidence
        }
    
    def get_field_validation_report(self, extraction_result: ExtractionResult) -> str:
        """Generate a human-readable validation report."""
        report_lines = []
        report_lines.append("=== QME Field Extraction Report ===")
        report_lines.append(f"Overall Confidence: {extraction_result.overall_confidence:.2%}")
        report_lines.append("")
        
        # Successfully extracted fields
        report_lines.append("Successfully Extracted Fields:")
        for field_name, is_valid in extraction_result.validation_status.items():
            if is_valid:
                field_value = getattr(extraction_result.field_data, field_name)
                report_lines.append(f"  ✓ {field_name.replace('_', ' ').title()}: {field_value}")
        
        # Missing fields
        if extraction_result.missing_fields:
            report_lines.append("")
            report_lines.append("Missing Fields:")
            for field_name in extraction_result.missing_fields:
                report_lines.append(f"  ✗ {field_name.replace('_', ' ').title()}")
        
        # Extraction errors
        if extraction_result.extraction_errors:
            report_lines.append("")
            report_lines.append("Extraction Errors:")
            for error in extraction_result.extraction_errors:
                report_lines.append(f"  ! {error}")
        
        return "\n".join(report_lines)