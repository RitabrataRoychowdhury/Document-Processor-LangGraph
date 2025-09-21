"""
Structured Extractor for QME Document Processing

This module provides structured extraction capabilities for QME documents
with confidence scoring and evidence tracking.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import time

from src.models.extraction_models import (
    ExtractionResult, 
    ExtractedField, 
    QualityAssessment, 
    ProcessingMetadata
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class ExtractionContext:
    """Context for structured extraction operations."""
    document_path: str
    document_type: str
    extraction_config: Dict[str, Any]
    confidence_threshold: float = 0.7
    enable_evidence_tracking: bool = True

class StructuredExtractor:
    """
    Structured extractor for QME documents with confidence scoring.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the structured extractor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)
        self.enable_evidence_tracking = self.config.get('enable_evidence_tracking', True)
        
        logger.info("Initialized StructuredExtractor")
    
    def extract_with_confidence(self, context: ExtractionContext) -> ExtractionResult:
        """
        Extract structured data with confidence scoring.
        
        Args:
            context: Extraction context with document and configuration
            
        Returns:
            ExtractionResult with structured extraction results
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting structured extraction: {context.document_path}")
            
            # Read document content
            document_text = self._read_document(context.document_path)
            
            # Perform structured extraction
            extracted_fields = self._extract_structured_fields(
                document_text, 
                context.document_type,
                context.extraction_config
            )
            
            # Calculate quality assessment
            quality_assessment = self._assess_extraction_quality(extracted_fields)
            
            # Create processing metadata
            processing_time = time.time() - start_time
            metadata = ProcessingMetadata(
                extraction_method="structured_extractor",
                processing_time=processing_time,
                model_used="rule_based_structured",
                prompt_template="structured_extraction",
                api_version="1.0"
            )
            
            # Generate document ID
            document_id = self._generate_document_id(context.document_path)
            
            result = ExtractionResult(
                document_id=document_id,
                extraction_method="structured_extractor",
                confidence_score=quality_assessment.overall_score,
                extracted_fields=extracted_fields,
                quality_assessment=quality_assessment,
                processing_metadata=metadata,
                source_references=[],
                validation_results=[]
            )
            
            logger.info(f"Structured extraction completed: {len(extracted_fields)} fields extracted")
            return result
            
        except Exception as e:
            logger.error(f"Structured extraction failed: {str(e)}")
            raise
    
    def _read_document(self, document_path: str) -> str:
        """
        Read document content from file.
        
        Args:
            document_path: Path to the document
            
        Returns:
            Document content as string
        """
        try:
            with open(document_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Handle binary files
            logger.warning(f"Binary file detected: {document_path}")
            return f"[Binary document: {document_path}]"
        except Exception as e:
            logger.error(f"Failed to read document {document_path}: {str(e)}")
            raise
    
    def _extract_structured_fields(
        self, 
        document_text: str, 
        document_type: str,
        extraction_config: Dict[str, Any]
    ) -> Dict[str, ExtractedField]:
        """
        Extract structured fields from document text.
        
        Args:
            document_text: The document content
            document_type: Type of document being processed
            extraction_config: Configuration for extraction
            
        Returns:
            Dictionary of extracted fields
        """
        extracted_fields = {}
        
        # Use rule-based extraction patterns
        import re
        
        # Patient name extraction
        name_patterns = [
            r'Patient:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Name:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'PATIENT NAME:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, document_text, re.IGNORECASE)
            if match:
                extracted_fields['patient_name'] = ExtractedField(
                    name='patient_name',
                    value=match.group(1).strip(),
                    confidence=0.8,
                    source_location=f'Pattern match: {pattern}',
                    validation_status='pending',
                    notes='Extracted using structured pattern matching'
                )
                break
        
        # Date of birth extraction
        dob_patterns = [
            r'(?:DOB|Date of Birth):?\s*(\d{1,2}/\d{1,2}/\d{4})',
            r'(?:DOB|Date of Birth):?\s*(\d{1,2}-\d{1,2}-\d{4})',
            r'Born:?\s*(\d{1,2}/\d{1,2}/\d{4})'
        ]
        
        for pattern in dob_patterns:
            match = re.search(pattern, document_text, re.IGNORECASE)
            if match:
                extracted_fields['date_of_birth'] = ExtractedField(
                    name='date_of_birth',
                    value=match.group(1).strip(),
                    confidence=0.9,
                    source_location=f'Pattern match: {pattern}',
                    validation_status='pending',
                    notes='Extracted using structured pattern matching'
                )
                break
        
        # Injury date extraction
        injury_patterns = [
            r'(?:Injury|Accident)\s*(?:Date|On):?\s*(\d{1,2}/\d{1,2}/\d{4})',
            r'Date\s*of\s*(?:Injury|Accident):?\s*(\d{1,2}/\d{1,2}/\d{4})'
        ]
        
        for pattern in injury_patterns:
            match = re.search(pattern, document_text, re.IGNORECASE)
            if match:
                extracted_fields['injury_date'] = ExtractedField(
                    name='injury_date',
                    value=match.group(1).strip(),
                    confidence=0.85,
                    source_location=f'Pattern match: {pattern}',
                    validation_status='pending',
                    notes='Extracted using structured pattern matching'
                )
                break
        
        # Case number extraction
        case_patterns = [
            r'(?:Case|Claim)\s*(?:Number|#):?\s*([A-Z0-9-]+)',
            r'WC\s*(?:Number|#):?\s*([A-Z0-9-]+)'
        ]
        
        for pattern in case_patterns:
            match = re.search(pattern, document_text, re.IGNORECASE)
            if match:
                extracted_fields['case_number'] = ExtractedField(
                    name='case_number',
                    value=match.group(1).strip(),
                    confidence=0.9,
                    source_location=f'Pattern match: {pattern}',
                    validation_status='pending',
                    notes='Extracted using structured pattern matching'
                )
                break
        
        # Body parts extraction
        body_part_keywords = [
            'back', 'knee', 'shoulder', 'neck', 'ankle', 'wrist', 
            'spine', 'lumbar', 'cervical', 'thoracic', 'hip', 'elbow'
        ]
        
        found_parts = []
        for keyword in body_part_keywords:
            if keyword.lower() in document_text.lower():
                found_parts.append(keyword.title())
        
        if found_parts:
            extracted_fields['body_parts'] = ExtractedField(
                name='body_parts',
                value=', '.join(list(set(found_parts))[:5]),  # Limit to 5 unique parts
                confidence=0.7,
                source_location='Keyword matching',
                validation_status='pending',
                notes='Extracted using keyword matching'
            )
        
        # Diagnosis extraction
        diagnosis_patterns = [
            r'(?:Diagnosis|Condition):?\s*([^.\n]+)',
            r'Primary\s*Diagnosis:?\s*([^.\n]+)',
            r'Medical\s*Diagnosis:?\s*([^.\n]+)'
        ]
        
        for pattern in diagnosis_patterns:
            match = re.search(pattern, document_text, re.IGNORECASE)
            if match:
                diagnosis_text = match.group(1).strip()
                if len(diagnosis_text) > 5:  # Ensure it's not just whitespace
                    extracted_fields['diagnosis'] = ExtractedField(
                        name='diagnosis',
                        value=diagnosis_text[:200],  # Limit length
                        confidence=0.6,
                        source_location=f'Pattern match: {pattern}',
                        validation_status='pending',
                        notes='Extracted using structured pattern matching'
                    )
                    break
        
        return extracted_fields
    
    def _assess_extraction_quality(self, extracted_fields: Dict[str, ExtractedField]) -> QualityAssessment:
        """
        Assess the quality of extracted fields.
        
        Args:
            extracted_fields: Dictionary of extracted fields
            
        Returns:
            QualityAssessment with quality metrics
        """
        if not extracted_fields:
            return QualityAssessment(
                overall_score=0.0,
                completeness_score=0.0,
                accuracy_score=0.0,
                consistency_score=0.0,
                compliance_score=0.0,
                identified_issues=["No fields extracted"],
                improvement_suggestions=["Review document content and extraction patterns"],
                confidence_intervals={}
            )
        
        # Calculate metrics
        total_fields = len(extracted_fields)
        high_confidence_fields = sum(1 for field in extracted_fields.values() if field.confidence >= 0.8)
        
        completeness_score = min(100.0, (total_fields / 7) * 100)  # Assume 7 expected fields
        accuracy_score = (high_confidence_fields / total_fields) * 100 if total_fields > 0 else 0
        consistency_score = 80.0  # Rule-based extraction is consistent
        compliance_score = 70.0   # Basic compliance for structured extraction
        
        overall_score = (completeness_score + accuracy_score + consistency_score + compliance_score) / 4
        
        return QualityAssessment(
            overall_score=overall_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            compliance_score=compliance_score,
            identified_issues=[],
            improvement_suggestions=[],
            confidence_intervals={}
        )
    
    def _generate_document_id(self, document_path: str) -> str:
        """
        Generate a unique document ID.
        
        Args:
            document_path: Path to the document
            
        Returns:
            Unique document ID
        """
        import hashlib
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path_hash = hashlib.md5(document_path.encode()).hexdigest()[:8]
        return f"doc_{timestamp}_{path_hash}"