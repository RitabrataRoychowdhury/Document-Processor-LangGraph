"""
Comprehensive QME Field Service - Complete field extraction and validation pipeline.

This service combines multiple extraction methods with validation to ensure
maximum field extraction success rate for QME template generation.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import PyPDF2
from pathlib import Path

from .qme_field_extractor import QMEFieldExtractor, QMEFieldData, ExtractionResult
from .qme_field_validator import QMEFieldValidator, FieldValidationResult
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ComprehensiveExtractionResult:
    """Complete result of QME field extraction and validation."""
    extraction_result: ExtractionResult
    validation_result: FieldValidationResult
    extraction_methods_used: List[str]
    fallback_attempts: int
    processing_time: float
    document_info: Dict[str, Any]


class ComprehensiveQMEFieldService:
    """
    Complete QME field extraction service with multiple extraction methods
    and comprehensive validation.
    
    Features:
    - Primary regex pattern extraction
    - spaCy NER fallback
    - LLM-based extraction (future enhancement)
    - Comprehensive field validation
    - Extraction confidence scoring
    - Template generation readiness assessment
    """
    
    def __init__(self):
        """Initialize the comprehensive QME field service."""
        self.extractor = QMEFieldExtractor()
        self.validator = QMEFieldValidator()
        
        # Extraction method priorities
        self.extraction_methods = [
            'regex_patterns',
            'spacy_ner',
            'contextual_inference',
            # 'llm_extraction'  # Future enhancement
        ]
    
    def extract_and_validate_fields(self, document_path: str) -> ComprehensiveExtractionResult:
        """
        Extract and validate QME fields from document with fallback methods.
        
        Args:
            document_path: Path to the document file
            
        Returns:
            ComprehensiveExtractionResult with extraction and validation results
        """
        import time
        start_time = time.time()
        
        logger.info(f"Starting comprehensive QME field extraction for: {document_path}")
        
        # Extract document text
        document_text, document_info = self._extract_document_text(document_path)
        
        # Primary extraction attempt
        extraction_result = self.extractor.extract_qme_fields(document_text, doc_id=document_path)
        methods_used = ['regex_patterns']
        fallback_attempts = 0
        
        # Apply fallback methods if extraction is incomplete
        if extraction_result.overall_confidence < 0.8:
            logger.info("Primary extraction incomplete, applying fallback methods")
            extraction_result, additional_methods, attempts = self._apply_fallback_extraction(
                document_text, extraction_result, document_path
            )
            methods_used.extend(additional_methods)
            fallback_attempts = attempts
        
        # Validate extracted fields
        validation_result = self.validator.validate_qme_fields(extraction_result.field_data)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Extraction completed in {processing_time:.2f}s with confidence {extraction_result.overall_confidence:.2%}")
        
        return ComprehensiveExtractionResult(
            extraction_result=extraction_result,
            validation_result=validation_result,
            extraction_methods_used=methods_used,
            fallback_attempts=fallback_attempts,
            processing_time=processing_time,
            document_info=document_info
        )
    
    def _extract_document_text(self, document_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text content from document file."""
        file_path = Path(document_path)
        
        document_info = {
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size if file_path.exists() else 0,
            'file_type': file_path.suffix.lower(),
            'extraction_method': None
        }
        
        try:
            if file_path.suffix.lower() == '.pdf':
                text_content = self._extract_pdf_text(document_path)
                document_info['extraction_method'] = 'PyPDF2'
            elif file_path.suffix.lower() == '.docx':
                text_content = self._extract_docx_text(document_path)
                document_info['extraction_method'] = 'python-docx'
            elif file_path.suffix.lower() == '.txt':
                with open(document_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                document_info['extraction_method'] = 'direct_read'
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
            
            document_info['text_length'] = len(text_content)
            document_info['extraction_success'] = True
            
            return text_content, document_info
            
        except Exception as e:
            logger.error(f"Error extracting text from {document_path}: {e}")
            document_info['extraction_success'] = False
            document_info['extraction_error'] = str(e)
            return "", document_info
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file."""
        text_content = ""
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text_content += f"[Page {page_num + 1}]\n{page_text}\n\n"
        
        return text_content
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            from docx import Document
            doc = Document(file_path)
            text_content = ""
            
            for paragraph in doc.paragraphs:
                text_content += paragraph.text + "\n"
            
            return text_content
        except ImportError:
            logger.error("python-docx not available for DOCX extraction")
            raise
    
    def _apply_fallback_extraction(self, document_text: str, 
                                 primary_result: ExtractionResult,
                                 doc_id: str) -> Tuple[ExtractionResult, List[str], int]:
        """Apply fallback extraction methods to improve field coverage."""
        methods_used = []
        attempts = 0
        
        current_result = primary_result
        
        # Fallback 1: Enhanced pattern matching for missing fields
        if len(current_result.missing_fields) > 0:
            attempts += 1
            enhanced_result = self._enhanced_pattern_extraction(
                document_text, current_result, doc_id
            )
            if enhanced_result.overall_confidence > current_result.overall_confidence:
                current_result = enhanced_result
                methods_used.append('enhanced_patterns')
        
        # Fallback 2: Contextual inference for missing fields
        if len(current_result.missing_fields) > 0:
            attempts += 1
            contextual_result = self._contextual_inference_extraction(
                document_text, current_result, doc_id
            )
            if contextual_result.overall_confidence > current_result.overall_confidence:
                current_result = contextual_result
                methods_used.append('contextual_inference')
        
        # Fallback 3: Cross-field validation and correction
        if current_result.overall_confidence < 0.9:
            attempts += 1
            corrected_result = self._cross_field_validation_correction(current_result)
            if corrected_result.overall_confidence > current_result.overall_confidence:
                current_result = corrected_result
                methods_used.append('cross_field_validation')
        
        return current_result, methods_used, attempts
    
    def _enhanced_pattern_extraction(self, document_text: str, 
                                   current_result: ExtractionResult,
                                   doc_id: str) -> ExtractionResult:
        """Apply enhanced patterns for missing fields."""
        logger.debug("Applying enhanced pattern extraction")
        
        field_data = current_result.field_data
        
        # Enhanced name patterns for difficult cases
        if not field_data.name:
            name_patterns = [
                r'(?:Patient|Injured\s+Worker|Applicant):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*(?:\s+Jr\.|\s+Sr\.|\s+III?)?)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+Jr\.|\s+Sr\.|\s+III?)?)\s*,?\s*(?:a\s+)?\d{2}[- ]year[- ]old',
                r'reference\s+to\s+the\s+applicant,?\s*([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+Jr\.|\s+Sr\.|\s+III?)?)',
            ]
            
            for pattern in name_patterns:
                matches = re.finditer(pattern, document_text, re.IGNORECASE)
                for match in matches:
                    name = match.group(1).strip()
                    if self.extractor._is_valid_name(name):
                        field_data.name = name
                        logger.debug(f"Enhanced extraction found name: {name}")
                        break
                if field_data.name:
                    break
        
        # Enhanced case/claim number patterns
        if not field_data.case_number:
            case_patterns = [
                r'(?:EAMS|Case|File)\s+(?:No|Number|#)\.?:?\s*([A-Z]{2,4}\d+)',
                r'\b([A-Z]{3}\d{8,})\b',  # Generic format like ADJ19802400
            ]
            
            for pattern in case_patterns:
                matches = re.finditer(pattern, document_text, re.IGNORECASE)
                for match in matches:
                    case_num = match.group(1).strip()
                    field_data.case_number = case_num
                    logger.debug(f"Enhanced extraction found case number: {case_num}")
                    break
                if field_data.case_number:
                    break
        
        # Enhanced claim number patterns
        if not field_data.claim_number:
            claim_patterns = [
                r'\b(WC\d+[A-Z0-9\-]*)\b',
                r'(?:Claim|WC)\s+(?:No|Number|#)\.?:?\s*([A-Z0-9\-]+)',
            ]
            
            for pattern in claim_patterns:
                matches = re.finditer(pattern, document_text, re.IGNORECASE)
                for match in matches:
                    claim_num = match.group(1).strip()
                    field_data.claim_number = claim_num
                    logger.debug(f"Enhanced extraction found claim number: {claim_num}")
                    break
                if field_data.claim_number:
                    break
        
        # Recalculate validation
        validation_result = self.validator.validate_qme_fields(field_data)
        
        return ExtractionResult(
            field_data=field_data,
            validation_status=validation_result.is_valid,
            missing_fields=validation_result.missing_required_fields,
            extraction_errors=[issue.message for issue in validation_result.issues if issue.severity == 'error'],
            overall_confidence=validation_result.validation_score
        )
    
    def _contextual_inference_extraction(self, document_text: str,
                                       current_result: ExtractionResult,
                                       doc_id: str) -> ExtractionResult:
        """Apply contextual inference for missing fields."""
        logger.debug("Applying contextual inference extraction")
        
        field_data = current_result.field_data
        
        # Infer gender from context if missing
        if not field_data.gender:
            # Look for gendered titles or pronouns in context
            if re.search(r'\bMr\.\s+[A-Z]', document_text):
                field_data.gender = 'Male'
                logger.debug("Inferred gender 'Male' from title")
            elif re.search(r'\b(?:Mrs\.|Ms\.)\s+[A-Z]', document_text):
                field_data.gender = 'Female'
                logger.debug("Inferred gender 'Female' from title")
            else:
                # Pronoun analysis with context
                male_contexts = len(re.findall(r'\b(?:he|his|him)\s+(?:was|is|had|sustained)', document_text, re.IGNORECASE))
                female_contexts = len(re.findall(r'\b(?:she|her)\s+(?:was|is|had|sustained)', document_text, re.IGNORECASE))
                
                if male_contexts > female_contexts and male_contexts > 0:
                    field_data.gender = 'Male'
                    logger.debug(f"Inferred gender 'Male' from {male_contexts} pronoun contexts")
                elif female_contexts > male_contexts and female_contexts > 0:
                    field_data.gender = 'Female'
                    logger.debug(f"Inferred gender 'Female' from {female_contexts} pronoun contexts")
        
        # Infer employer from occupation context
        if not field_data.employer and field_data.occupation:
            employer_patterns = [
                r'(?:worked|employed)\s+(?:at|by|for)\s+([A-Z][a-zA-Z\s&.,]+?)(?:\s+warehouse|\s+in|\s+located|\s+who)',
                r'([A-Z][a-zA-Z\s&.,]+?)\s+(?:warehouse|store|company|corporation)',
            ]
            
            for pattern in employer_patterns:
                matches = re.finditer(pattern, document_text, re.IGNORECASE)
                for match in matches:
                    employer = match.group(1).strip()
                    if len(employer) > 2:
                        field_data.employer = employer
                        logger.debug(f"Inferred employer: {employer}")
                        break
                if field_data.employer:
                    break
        
        # Recalculate validation
        validation_result = self.validator.validate_qme_fields(field_data)
        
        return ExtractionResult(
            field_data=field_data,
            validation_status=validation_result.is_valid,
            missing_fields=validation_result.missing_required_fields,
            extraction_errors=[issue.message for issue in validation_result.issues if issue.severity == 'error'],
            overall_confidence=validation_result.validation_score
        )
    
    def _cross_field_validation_correction(self, current_result: ExtractionResult) -> ExtractionResult:
        """Apply cross-field validation and correction."""
        logger.debug("Applying cross-field validation and correction")
        
        field_data = current_result.field_data
        
        # Validate name consistency with case/claim numbers
        if field_data.name and field_data.case_number:
            # Check if name appears to be consistent with case context
            name_parts = field_data.name.lower().split()
            if len(name_parts) >= 2:
                # This is a placeholder for more sophisticated validation
                # In a real implementation, you might check against a database
                # or apply more complex consistency rules
                pass
        
        # Validate date consistency
        if field_data.injury_date and field_data.scheduled_exam_date:
            # Ensure exam date is after injury date
            # This would require proper date parsing in a real implementation
            pass
        
        # Validate body part consistency with occupation
        if field_data.body_parts and field_data.occupation:
            # Check if injury is consistent with occupation
            # E.g., knee injury for physical job
            pass
        
        # Recalculate validation
        validation_result = self.validator.validate_qme_fields(field_data)
        
        return ExtractionResult(
            field_data=field_data,
            validation_status=validation_result.is_valid,
            missing_fields=validation_result.missing_required_fields,
            extraction_errors=[issue.message for issue in validation_result.issues if issue.severity == 'error'],
            overall_confidence=validation_result.validation_score
        )
    
    def generate_comprehensive_report(self, result: ComprehensiveExtractionResult) -> str:
        """Generate a comprehensive extraction and validation report."""
        report_lines = []
        report_lines.append("=== Comprehensive QME Field Extraction Report ===")
        report_lines.append(f"Processing Time: {result.processing_time:.2f} seconds")
        report_lines.append(f"Extraction Methods Used: {', '.join(result.extraction_methods_used)}")
        report_lines.append(f"Fallback Attempts: {result.fallback_attempts}")
        report_lines.append("")
        
        # Document information
        report_lines.append("Document Information:")
        for key, value in result.document_info.items():
            report_lines.append(f"  {key.replace('_', ' ').title()}: {value}")
        report_lines.append("")
        
        # Extraction results
        report_lines.append("Extraction Results:")
        report_lines.append(f"  Overall Confidence: {result.extraction_result.overall_confidence:.2%}")
        report_lines.append(f"  Fields Extracted: {len(result.extraction_result.validation_status) - len(result.extraction_result.missing_fields)}/{len(result.extraction_result.validation_status)}")
        
        if result.extraction_result.missing_fields:
            report_lines.append(f"  Missing Fields: {', '.join(result.extraction_result.missing_fields)}")
        report_lines.append("")
        
        # Validation results
        report_lines.append("Validation Results:")
        report_lines.append(f"  Validation Score: {result.validation_result.validation_score:.2%}")
        report_lines.append(f"  Ready for Template Generation: {'Yes' if result.validation_result.ready_for_template_generation else 'No'}")
        
        if result.validation_result.issues:
            report_lines.append(f"  Validation Issues: {len(result.validation_result.issues)}")
        
        if result.validation_result.recommendations:
            report_lines.append("")
            report_lines.append("Recommendations:")
            for rec in result.validation_result.recommendations:
                report_lines.append(f"  • {rec}")
        
        # Detailed field extraction report
        report_lines.append("")
        report_lines.append(self.extractor.get_field_validation_report(result.extraction_result))
        
        return "\n".join(report_lines)
    
    def is_ready_for_template_generation(self, result: ComprehensiveExtractionResult) -> bool:
        """Check if extracted fields are ready for QME template generation."""
        return (result.validation_result.ready_for_template_generation and
                result.extraction_result.overall_confidence >= 0.7)


# Import required modules at the top
import re