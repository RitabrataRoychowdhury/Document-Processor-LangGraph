"""
Structured Extractor - Orchestrates regex + NER extraction with evidence collection.

This module implements the evidence-first structured extraction pipeline that
combines regex pattern matching with NER enhancement and provides comprehensive
evidence snippet collection and source coordinate tracking.
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
import spacy
from spacy.matcher import Matcher

from .qme_field_extractor import (
    QMEFieldExtractor, QMEFieldData, ExtractionResult, 
    FieldExtraction, EvidenceSnippet, DocumentCoordinate
)
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractionContext:
    """Context information for extraction process."""
    document_id: str
    document_text: str
    page_count: int = 1
    source_file: Optional[str] = None
    processing_timestamp: Optional[str] = None


@dataclass
class ConfidenceMetrics:
    """Detailed confidence scoring metrics."""
    regex_confidence: float = 0.0
    ner_confidence: float = 0.0
    cross_validation_confidence: float = 0.0
    pattern_match_count: int = 0
    entity_probability: float = 0.0
    consistency_score: float = 0.0


class StructuredExtractor:
    """
    Orchestrates regex + NER extraction with evidence snippet collection.
    
    Implements the evidence-first extraction pipeline:
    1. Regex pattern extraction with confidence scoring
    2. NER enhancement layer for missed fields
    3. Cross-document validation for consistency
    4. Evidence provenance tracking with source coordinates
    5. Confidence calculation combining all methods
    """
    
    def __init__(self, spacy_model: str = "en_core_web_sm"):
        """Initialize the structured extractor."""
        self.field_extractor = QMEFieldExtractor(spacy_model)
        self.nlp = self.field_extractor.nlp
        
        # Load extraction patterns
        self.extraction_patterns = self._load_extraction_patterns()
        
        # Cross-validation storage for consistency checking
        self.cross_validation_cache: Dict[str, List[Any]] = {}
        
        # Evidence collection settings
        self.context_window = 100  # Characters around match for context
        
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
    
    def extract_with_confidence(self, context: ExtractionContext) -> ExtractionResult:
        """
        Extract fields with comprehensive confidence scoring and evidence collection.
        
        Args:
            context: Extraction context with document information
            
        Returns:
            ExtractionResult with enhanced confidence metrics and evidence
        """
        logger.info(f"Starting structured extraction for document {context.document_id}")
        
        # Initialize field data container
        field_data = QMEFieldData()
        confidence_breakdown = {}
        cross_validation_results = {}
        
        # Extract each field type with confidence scoring
        field_results = {}
        
        # Extract case numbers
        field_results['case_number'] = self._extract_case_numbers(context)
        field_results['claim_number'] = self._extract_claim_numbers(context)
        
        # Extract patient information
        field_results['name'] = self._extract_patient_names(context)
        field_results['age'] = self._extract_ages(context)
        field_results['gender'] = self._extract_genders(context)
        
        # Extract dates
        field_results['injury_date'] = self._extract_injury_dates(context)
        field_results['scheduled_exam_date'] = self._extract_exam_dates(context)
        
        # Extract medical information
        field_results['body_parts'] = self._extract_body_parts(context)
        field_results['rom_measurements'] = self._extract_rom_measurements(context)
        field_results['ama_table_references'] = self._extract_ama_references(context)
        
        # Extract employment information
        field_results['occupation'] = self._extract_occupations(context)
        field_results['employer'] = self._extract_employers(context)
        
        # Process results and populate field data
        for field_name, extraction in field_results.items():
            if extraction and extraction.confidence > 0.0:
                setattr(field_data, field_name, extraction.value)
                field_data.field_extractions[field_name] = extraction
                field_data.extraction_confidence[field_name] = extraction.confidence
                field_data.extraction_methods[field_name] = extraction.extraction_method
                
                # Store evidence
                if field_name not in field_data.evidence_provenance:
                    field_data.evidence_provenance[field_name] = []
                field_data.evidence_provenance[field_name].append(extraction.evidence)
                
                confidence_breakdown[field_name] = extraction.confidence
                cross_validation_results[field_name] = extraction.cross_validation_score
        
        # Calculate overall metrics
        overall_confidence = self._calculate_overall_confidence(confidence_breakdown)
        evidence_completeness = self._calculate_evidence_completeness(field_data)
        
        # Validate fields
        validation_result = self._validate_extracted_fields(field_data)
        
        return ExtractionResult(
            field_data=field_data,
            validation_status=validation_result['validation_status'],
            missing_fields=validation_result['missing_fields'],
            extraction_errors=validation_result['extraction_errors'],
            overall_confidence=overall_confidence,
            confidence_breakdown=confidence_breakdown,
            evidence_completeness=evidence_completeness,
            cross_validation_results=cross_validation_results
        )
    
    def _extract_case_numbers(self, context: ExtractionContext) -> Optional[FieldExtraction]:
        """Extract case numbers with confidence scoring."""
        if 'case_numbers' not in self.extraction_patterns:
            return None
        
        best_extraction = None
        highest_confidence = 0.0
        
        for pattern_info in self.extraction_patterns['case_numbers']:
            pattern = pattern_info['pattern']
            base_confidence = pattern_info['confidence']
            
            matches = list(re.finditer(pattern, context.document_text, re.IGNORECASE))
            
            for match in matches:
                case_number = match.group(1).strip()
                
                # Calculate confidence
                confidence_metrics = self._calculate_confidence_metrics(
                    match, context, 'regex', base_confidence
                )
                
                total_confidence = self._combine_confidence_scores(confidence_metrics)
                
                if total_confidence > highest_confidence:
                    highest_confidence = total_confidence
                    
                    # Create evidence snippet
                    evidence = self._create_evidence_snippet(
                        match, context, 'regex', pattern_info['description']
                    )
                    
                    best_extraction = FieldExtraction(
                        value=case_number,
                        confidence=total_confidence,
                        evidence=evidence,
                        extraction_method='regex',
                        cross_validation_score=confidence_metrics.consistency_score
                    )
        
        # Enhance with NER if available
        if best_extraction and self.nlp:
            ner_enhancement = self._enhance_with_ner(
                context, 'case_number', best_extraction.value
            )
            if ner_enhancement:
                best_extraction.confidence = max(
                    best_extraction.confidence, 
                    ner_enhancement.confidence
                )
        
        return best_extraction
    
    def _extract_claim_numbers(self, context: ExtractionContext) -> Optional[FieldExtraction]:
        """Extract claim numbers with confidence scoring."""
        # Similar implementation to case numbers but for claim patterns
        return self._extract_with_patterns(context, 'claim_numbers', 'claim_number')
    
    def _extract_patient_names(self, context: ExtractionContext) -> Optional[FieldExtraction]:
        """Extract patient names with confidence scoring."""
        return self._extract_with_patterns(context, 'patient_names', 'name')
    
    def _extract_ages(self, context: ExtractionContext) -> Optional[FieldExtraction]:
        """Extract patient ages using existing patterns."""
        # Use existing age patterns from QMEFieldExtractor
        age_patterns = [
            r'(\d{2})[- ]year[- ]old',
            r'(?:age|Age):\s*(\d{2})',
            r'was\s+a\s+(\d{2})[- ]year[- ]old',
        ]
        
        return self._extract_with_custom_patterns(
            context, age_patterns, 'age', int, lambda x: 18 <= x <= 100
        )
    
    def _extract_genders(self, context: ExtractionContext) -> Optional[FieldExtraction]:
        """Extract patient gender using existing patterns."""
        gender_patterns = [
            (r'(?:Gender|Sex):\s*(Male|Female|M|F)', 0.95),
            (r'\b(Mr\.|Mrs\.|Ms\.)\s+[A-Z]', 0.80),
            (r'\b(he|she|his|her|him)\b', 0.60),
        ]
        
        best_extraction = None
        highest_confidence = 0.0
        
        for pattern, base_confidence in gender_patterns:
            matches = list(re.finditer(pattern, context.document_text, re.IGNORECASE))
            
            for match in matches:
                gender_text = match.group(1).upper()
                
                # Normalize gender
                if gender_text in ['MALE', 'M', 'MR.', 'HE', 'HIS', 'HIM']:
                    gender = 'Male'
                elif gender_text in ['FEMALE', 'F', 'MRS.', 'MS.', 'SHE', 'HER']:
                    gender = 'Female'
                else:
                    continue
                
                confidence_metrics = self._calculate_confidence_metrics(
                    match, context, 'regex', base_confidence
                )
                
                total_confidence = self._combine_confidence_scores(confidence_metrics)
                
                if total_confidence > highest_confidence:
                    highest_confidence = total_confidence
                    
                    evidence = self._create_evidence_snippet(
                        match, context, 'regex', f'Gender pattern: {pattern}'
                    )
                    
                    best_extraction = FieldExtraction(
                        value=gender,
                        confidence=total_confidence,
                        evidence=evidence,
                        extraction_method='regex',
                        cross_validation_score=confidence_metrics.consistency_score
                    )
        
        return best_extraction
    
    def _extract_injury_dates(self, context: ExtractionContext) -> Optional[FieldExtraction]:
        """Extract injury dates with confidence scoring."""
        return self._extract_with_patterns(context, 'dates', 'injury_date')
    
    def _extract_exam_dates(self, context: ExtractionContext) -> Optional[FieldExtraction]:
        """Extract examination dates with confidence scoring."""
        return self._extract_with_patterns(context, 'dates', 'exam_date')
    
    def _extract_body_parts(self, context: ExtractionContext) -> Optional[FieldExtraction]:
        """Extract body parts with confidence scoring."""
        if 'body_parts' not in self.extraction_patterns:
            return None
        
        body_parts = set()
        evidence_snippets = []
        total_confidence = 0.0
        match_count = 0
        
        for pattern_info in self.extraction_patterns['body_parts']:
            pattern = pattern_info['pattern']
            base_confidence = pattern_info['confidence']
            
            matches = list(re.finditer(pattern, context.document_text, re.IGNORECASE))
            
            for match in matches:
                body_part = match.group(1).strip().lower()
                body_part = re.sub(r'\s+', ' ', body_part).title()
                
                if len(body_part) > 2:
                    body_parts.add(body_part)
                    
                    confidence_metrics = self._calculate_confidence_metrics(
                        match, context, 'regex', base_confidence
                    )
                    
                    total_confidence += self._combine_confidence_scores(confidence_metrics)
                    match_count += 1
                    
                    evidence = self._create_evidence_snippet(
                        match, context, 'regex', pattern_info['description']
                    )
                    evidence_snippets.append(evidence)
        
        if body_parts:
            avg_confidence = total_confidence / match_count if match_count > 0 else 0.0
            
            # Use the first evidence snippet as primary
            primary_evidence = evidence_snippets[0] if evidence_snippets else None
            
            return FieldExtraction(
                value=list(body_parts),
                confidence=avg_confidence,
                evidence=primary_evidence,
                extraction_method='regex',
                cross_validation_score=0.0
            )
        
        return None
    
    def _extract_rom_measurements(self, context: ExtractionContext) -> Optional[FieldExtraction]:
        """Extract ROM measurements with confidence scoring."""
        if 'rom_measurements' not in self.extraction_patterns:
            return None
        
        rom_data = {}
        evidence_snippets = []
        total_confidence = 0.0
        match_count = 0
        
        for pattern_info in self.extraction_patterns['rom_measurements']:
            pattern = pattern_info['pattern']
            base_confidence = pattern_info['confidence']
            
            matches = list(re.finditer(pattern, context.document_text, re.IGNORECASE))
            
            for match in matches:
                try:
                    if len(match.groups()) >= 2:
                        body_part = match.group(1).strip().lower()
                        measurement = float(match.group(2))
                        
                        if body_part not in rom_data:
                            rom_data[body_part] = []
                        rom_data[body_part].append(measurement)
                        
                        confidence_metrics = self._calculate_confidence_metrics(
                            match, context, 'regex', base_confidence
                        )
                        
                        total_confidence += self._combine_confidence_scores(confidence_metrics)
                        match_count += 1
                        
                        evidence = self._create_evidence_snippet(
                            match, context, 'regex', pattern_info['description']
                        )
                        evidence_snippets.append(evidence)
                        
                except (ValueError, IndexError):
                    continue
        
        if rom_data:
            avg_confidence = total_confidence / match_count if match_count > 0 else 0.0
            primary_evidence = evidence_snippets[0] if evidence_snippets else None
            
            return FieldExtraction(
                value=rom_data,
                confidence=avg_confidence,
                evidence=primary_evidence,
                extraction_method='regex',
                cross_validation_score=0.0
            )
        
        return None
    
    def _extract_ama_references(self, context: ExtractionContext) -> Optional[FieldExtraction]:
        """Extract AMA table references with confidence scoring."""
        if 'ama_table_references' not in self.extraction_patterns:
            return None
        
        references = set()
        evidence_snippets = []
        total_confidence = 0.0
        match_count = 0
        
        for pattern_info in self.extraction_patterns['ama_table_references']:
            pattern = pattern_info['pattern']
            base_confidence = pattern_info['confidence']
            
            matches = list(re.finditer(pattern, context.document_text, re.IGNORECASE))
            
            for match in matches:
                if pattern == "Combined\\s+Values\\s+Chart":
                    reference = "Combined Values Chart"
                else:
                    reference = match.group(1).strip() if match.groups() else match.group(0).strip()
                
                references.add(reference)
                
                confidence_metrics = self._calculate_confidence_metrics(
                    match, context, 'regex', base_confidence
                )
                
                total_confidence += self._combine_confidence_scores(confidence_metrics)
                match_count += 1
                
                evidence = self._create_evidence_snippet(
                    match, context, 'regex', pattern_info['description']
                )
                evidence_snippets.append(evidence)
        
        if references:
            avg_confidence = total_confidence / match_count if match_count > 0 else 0.0
            primary_evidence = evidence_snippets[0] if evidence_snippets else None
            
            return FieldExtraction(
                value=list(references),
                confidence=avg_confidence,
                evidence=primary_evidence,
                extraction_method='regex',
                cross_validation_score=0.0
            )
        
        return None
    
    def _extract_occupations(self, context: ExtractionContext) -> Optional[FieldExtraction]:
        """Extract occupations using existing patterns."""
        occupation_patterns = [
            (r'(?:\d{2}[- ]year[- ]old\s+)([a-zA-Z\-\s]+?)(?:\s+for|\s+at|\s+with)', 0.85),
            (r'Occupation:\s*([A-Z][a-zA-Z\-\s]+)', 0.95),
            (r'([a-zA-Z\-]+(?:\s+[a-zA-Z\-]+)*)\s+for\s+(?:a\s+)?(?:Costco|company|employer)', 0.80),
        ]
        
        return self._extract_with_custom_patterns(
            context, occupation_patterns, 'occupation', str, lambda x: len(x) > 2
        )
    
    def _extract_employers(self, context: ExtractionContext) -> Optional[FieldExtraction]:
        """Extract employers using existing patterns."""
        employer_patterns = [
            (r'Employer:\s*([A-Z][a-zA-Z\s&.,]+?)(?:\s+Venue|\s+EAMS|\s*$)', 0.95),
            (r'for\s+([A-Z][a-zA-Z\s&.,]+?)(?:\s+warehouse|\s+in|\s+located)', 0.80),
            (r'(?:worked\s+at|employed\s+by)\s+([A-Z][a-zA-Z\s&.,]+)', 0.85),
        ]
        
        return self._extract_with_custom_patterns(
            context, employer_patterns, 'employer', str, lambda x: len(x) > 2
        )
    
    def _extract_with_patterns(self, context: ExtractionContext, pattern_key: str, field_type: str) -> Optional[FieldExtraction]:
        """Generic extraction method using patterns from legal_patterns.json."""
        if pattern_key not in self.extraction_patterns:
            return None
        
        best_extraction = None
        highest_confidence = 0.0
        
        for pattern_info in self.extraction_patterns[pattern_key]:
            pattern = pattern_info['pattern']
            base_confidence = pattern_info['confidence']
            
            matches = list(re.finditer(pattern, context.document_text, re.IGNORECASE))
            
            for match in matches:
                value = match.group(1).strip() if match.groups() else match.group(0).strip()
                
                confidence_metrics = self._calculate_confidence_metrics(
                    match, context, 'regex', base_confidence
                )
                
                total_confidence = self._combine_confidence_scores(confidence_metrics)
                
                if total_confidence > highest_confidence:
                    highest_confidence = total_confidence
                    
                    evidence = self._create_evidence_snippet(
                        match, context, 'regex', pattern_info['description']
                    )
                    
                    best_extraction = FieldExtraction(
                        value=value,
                        confidence=total_confidence,
                        evidence=evidence,
                        extraction_method='regex',
                        cross_validation_score=confidence_metrics.consistency_score
                    )
        
        return best_extraction
    
    def _extract_with_custom_patterns(self, context: ExtractionContext, patterns: List[Tuple], 
                                    field_type: str, value_type: type, 
                                    validator: callable = None) -> Optional[FieldExtraction]:
        """Extract using custom pattern list with confidence scoring."""
        best_extraction = None
        highest_confidence = 0.0
        
        for pattern, base_confidence in patterns:
            matches = list(re.finditer(pattern, context.document_text, re.IGNORECASE))
            
            for match in matches:
                try:
                    raw_value = match.group(1).strip()
                    
                    # Convert to appropriate type
                    if value_type == int:
                        value = int(raw_value)
                    elif value_type == float:
                        value = float(raw_value)
                    else:
                        value = raw_value
                    
                    # Apply validator if provided
                    if validator and not validator(value):
                        continue
                    
                    confidence_metrics = self._calculate_confidence_metrics(
                        match, context, 'regex', base_confidence
                    )
                    
                    total_confidence = self._combine_confidence_scores(confidence_metrics)
                    
                    if total_confidence > highest_confidence:
                        highest_confidence = total_confidence
                        
                        evidence = self._create_evidence_snippet(
                            match, context, 'regex', f'{field_type} pattern'
                        )
                        
                        best_extraction = FieldExtraction(
                            value=value,
                            confidence=total_confidence,
                            evidence=evidence,
                            extraction_method='regex',
                            cross_validation_score=confidence_metrics.consistency_score
                        )
                        
                except (ValueError, IndexError):
                    continue
        
        return best_extraction
    
    def _calculate_confidence_metrics(self, match: re.Match, context: ExtractionContext, 
                                    method: str, base_confidence: float) -> ConfidenceMetrics:
        """Calculate detailed confidence metrics for a match."""
        metrics = ConfidenceMetrics()
        
        if method == 'regex':
            metrics.regex_confidence = base_confidence
            metrics.pattern_match_count = 1
            
            # Adjust confidence based on match quality factors
            match_text = match.group(0)
            
            # Length-based adjustment
            if len(match_text) > 100:  # Very long matches might be less reliable
                metrics.regex_confidence *= 0.85
            elif len(match_text) > 50:
                metrics.regex_confidence *= 0.9
            elif len(match_text) < 3:  # Very short matches might be less reliable
                metrics.regex_confidence *= 0.7
            
            # Position-based adjustment (matches near document start/end might be headers/footers)
            doc_length = len(context.document_text)
            match_position = match.start() / doc_length if doc_length > 0 else 0.5
            
            if match_position < 0.1 or match_position > 0.9:  # Near start or end
                metrics.regex_confidence *= 0.95
            
            # Context quality adjustment
            context_start = max(0, match.start() - 50)
            context_end = min(len(context.document_text), match.end() + 50)
            surrounding_text = context.document_text[context_start:context_end]
            
            # Check for structured context indicators
            structure_indicators = [':', 'Applicant', 'Patient', 'Case', 'Date', 'Injury']
            if any(indicator in surrounding_text for indicator in structure_indicators):
                metrics.regex_confidence *= 1.05  # Boost for structured context
            
            # Cap at 1.0
            metrics.regex_confidence = min(metrics.regex_confidence, 1.0)
        
        elif method == 'ner':
            metrics.ner_confidence = base_confidence
            # NER confidence is typically the entity probability from spaCy
            metrics.entity_probability = base_confidence
        
        # Cross-validation score - check against cached values
        field_type = self._infer_field_type_from_match(match, context)
        if field_type in self.cross_validation_cache:
            cached_values = self.cross_validation_cache[field_type]
            current_value = match.group(1) if match.groups() else match.group(0)
            
            # Simple consistency check - if we've seen this value before, boost confidence
            if current_value.strip().lower() in [v.lower() for v in cached_values]:
                metrics.consistency_score = 0.8
            else:
                # Check for partial matches or similar values
                similarity_scores = []
                for cached_val in cached_values:
                    similarity = self._calculate_string_similarity(current_value, cached_val)
                    similarity_scores.append(similarity)
                
                if similarity_scores:
                    metrics.consistency_score = max(similarity_scores) * 0.6
                else:
                    metrics.consistency_score = 0.1  # New value, low consistency
        else:
            # First occurrence, moderate consistency score
            metrics.consistency_score = 0.5
            
        # Cache this value for future cross-validation
        if field_type not in self.cross_validation_cache:
            self.cross_validation_cache[field_type] = []
        
        current_value = match.group(1) if match.groups() else match.group(0)
        if current_value.strip() not in self.cross_validation_cache[field_type]:
            self.cross_validation_cache[field_type].append(current_value.strip())
        
        return metrics
    
    def _combine_confidence_scores(self, metrics: ConfidenceMetrics) -> float:
        """Combine confidence scores using the algorithm weights."""
        total_confidence = (
            metrics.regex_confidence * self.field_extractor.confidence_weights['regex'] +
            metrics.ner_confidence * self.field_extractor.confidence_weights['ner'] +
            metrics.consistency_score * self.field_extractor.confidence_weights['cross_validation']
        )
        
        return min(total_confidence, 1.0)  # Cap at 1.0
    
    def _create_evidence_snippet(self, match: re.Match, context: ExtractionContext, 
                               method: str, description: str) -> EvidenceSnippet:
        """Create evidence snippet with enhanced source coordinates and provenance."""
        start_pos = max(0, match.start() - self.context_window)
        end_pos = min(len(context.document_text), match.end() + self.context_window)
        
        context_text = context.document_text[start_pos:end_pos]
        match_text = match.group(0)
        
        # Enhanced page number calculation
        page_number = self._calculate_page_number(match.start(), context.document_text)
        
        # Calculate line number for better provenance
        line_number = self._calculate_line_number(match.start(), context.document_text)
        
        coordinates = DocumentCoordinate(
            page_number=page_number,
            start_char=match.start(),
            end_char=match.end(),
            line_number=line_number
        )
        
        return EvidenceSnippet(
            text=match_text,
            context=context_text,
            coordinates=coordinates,
            extraction_method=f"{method} - {description}"
        )
    
    def _calculate_page_number(self, char_position: int, document_text: str) -> int:
        """Calculate page number based on character position with improved accuracy."""
        # Look for page break indicators
        page_breaks = ['\f', '\x0c']  # Form feed characters
        page_indicators = ['Page ', 'PAGE ', 'page ']
        
        # Count explicit page breaks before this position
        text_before = document_text[:char_position]
        explicit_breaks = sum(text_before.count(pb) for pb in page_breaks)
        
        if explicit_breaks > 0:
            return explicit_breaks + 1
        
        # Count page indicators
        page_count = 0
        for indicator in page_indicators:
            page_count += text_before.count(indicator)
        
        if page_count > 0:
            return page_count
        
        # Fallback to character-based estimation
        chars_per_page = 2500  # Adjusted estimate for medical documents
        estimated_page = (char_position // chars_per_page) + 1
        
        return max(1, estimated_page)
    
    def _calculate_line_number(self, char_position: int, document_text: str) -> int:
        """Calculate line number based on character position."""
        text_before = document_text[:char_position]
        return text_before.count('\n') + 1
    
    def generate_evidence_report(self, extraction_result: ExtractionResult) -> str:
        """Generate a comprehensive evidence provenance report."""
        report_lines = []
        report_lines.append("=== Evidence Provenance Report ===")
        report_lines.append(f"Overall Confidence: {extraction_result.overall_confidence:.2%}")
        report_lines.append(f"Evidence Completeness: {extraction_result.evidence_completeness:.2%}")
        report_lines.append("")
        
        # Group by confidence levels
        high_confidence = {}
        medium_confidence = {}
        low_confidence = {}
        
        for field_name, confidence in extraction_result.confidence_breakdown.items():
            if confidence >= 0.8:
                high_confidence[field_name] = confidence
            elif confidence >= 0.5:
                medium_confidence[field_name] = confidence
            else:
                low_confidence[field_name] = confidence
        
        # High confidence fields (accepted)
        if high_confidence:
            report_lines.append("✅ ACCEPTED FIELDS (Confidence ≥ 0.8):")
            for field_name, confidence in high_confidence.items():
                field_value = getattr(extraction_result.field_data, field_name)
                evidence_list = extraction_result.field_data.evidence_provenance.get(field_name, [])
                
                report_lines.append(f"  • {field_name.replace('_', ' ').title()}: {field_value}")
                report_lines.append(f"    Confidence: {confidence:.2%}")
                
                if evidence_list:
                    evidence = evidence_list[0]  # Primary evidence
                    report_lines.append(f"    Source: Page {evidence.coordinates.page_number}, Line {evidence.coordinates.line_number}")
                    report_lines.append(f"    Method: {evidence.extraction_method}")
                    report_lines.append(f"    Context: \"{evidence.context[:100]}...\"")
                report_lines.append("")
        
        # Medium confidence fields (flagged for review)
        if medium_confidence:
            report_lines.append("⚠️  FLAGGED FOR REVIEW (0.5 ≤ Confidence < 0.8):")
            for field_name, confidence in medium_confidence.items():
                field_value = getattr(extraction_result.field_data, field_name)
                evidence_list = extraction_result.field_data.evidence_provenance.get(field_name, [])
                
                report_lines.append(f"  • {field_name.replace('_', ' ').title()}: {field_value}")
                report_lines.append(f"    Confidence: {confidence:.2%} - NEEDS HUMAN REVIEW")
                
                if evidence_list:
                    evidence = evidence_list[0]
                    report_lines.append(f"    Source: Page {evidence.coordinates.page_number}, Line {evidence.coordinates.line_number}")
                    report_lines.append(f"    Context: \"{evidence.context[:100]}...\"")
                report_lines.append("")
        
        # Low confidence fields (missing/rejected)
        if low_confidence or extraction_result.missing_fields:
            report_lines.append("❌ MISSING/REJECTED FIELDS (Confidence < 0.5):")
            
            for field_name in extraction_result.missing_fields:
                report_lines.append(f"  • {field_name.replace('_', ' ').title()}: NOT FOUND")
            
            for field_name, confidence in low_confidence.items():
                field_value = getattr(extraction_result.field_data, field_name)
                report_lines.append(f"  • {field_name.replace('_', ' ').title()}: {field_value} (Confidence: {confidence:.2%})")
            
            report_lines.append("")
        
        # Extraction errors
        if extraction_result.extraction_errors:
            report_lines.append("🔍 EXTRACTION ISSUES:")
            for error in extraction_result.extraction_errors:
                report_lines.append(f"  • {error}")
            report_lines.append("")
        
        # Cross-validation results
        if extraction_result.cross_validation_results:
            report_lines.append("🔗 CROSS-VALIDATION SCORES:")
            for field_name, cv_score in extraction_result.cross_validation_results.items():
                report_lines.append(f"  • {field_name.replace('_', ' ').title()}: {cv_score:.2%}")
        
        return "\n".join(report_lines)
    
    def _enhance_with_ner(self, context: ExtractionContext, field_type: str, 
                         current_value: Any) -> Optional[FieldExtraction]:
        """Enhance extraction using NER if available."""
        if not self.nlp:
            return None
        
        try:
            doc = self.nlp(context.document_text)
            
            # Map field types to spaCy entity labels
            entity_mapping = {
                'name': ['PERSON'],
                'occupation': ['WORK_OF_ART', 'ORG'],  # Sometimes occupations are tagged as these
                'employer': ['ORG'],
                'case_number': ['CARDINAL', 'PRODUCT'],  # Numbers and product codes
                'claim_number': ['CARDINAL', 'PRODUCT'],
                'injury_date': ['DATE'],
                'exam_date': ['DATE'],
                'age': ['CARDINAL'],
                'body_parts': ['PRODUCT', 'WORK_OF_ART']  # Medical terms sometimes tagged as these
            }
            
            if field_type not in entity_mapping:
                return None
            
            target_labels = entity_mapping[field_type]
            best_entity = None
            highest_confidence = 0.0
            
            for ent in doc.ents:
                if ent.label_ in target_labels:
                    # Calculate NER confidence based on entity properties
                    ner_confidence = self._calculate_ner_confidence(ent, field_type, current_value)
                    
                    if ner_confidence > highest_confidence:
                        highest_confidence = ner_confidence
                        best_entity = ent
            
            if best_entity and highest_confidence > 0.3:  # Minimum NER confidence threshold
                # Create evidence snippet for NER match
                evidence = EvidenceSnippet(
                    text=best_entity.text,
                    context=self._get_entity_context(best_entity, context.document_text),
                    coordinates=DocumentCoordinate(
                        page_number=1,  # Simplified for now
                        start_char=best_entity.start_char,
                        end_char=best_entity.end_char
                    ),
                    extraction_method='ner'
                )
                
                return FieldExtraction(
                    value=best_entity.text,
                    confidence=highest_confidence,
                    evidence=evidence,
                    extraction_method='ner',
                    cross_validation_score=0.0
                )
        
        except Exception as e:
            logger.warning(f"NER enhancement failed for {field_type}: {e}")
        
        return None
    
    def _calculate_ner_confidence(self, entity, field_type: str, current_value: Any) -> float:
        """Calculate confidence for NER entity based on field type and context."""
        base_confidence = 0.7  # Base NER confidence
        
        # Adjust based on entity label confidence (if available)
        # spaCy doesn't provide confidence scores directly, so we use heuristics
        
        # Length-based adjustment
        if len(entity.text) < 2:
            base_confidence *= 0.5
        elif len(entity.text) > 50:
            base_confidence *= 0.8
        
        # Field-specific adjustments
        if field_type == 'name':
            # Names should have proper capitalization
            if entity.text.istitle():
                base_confidence *= 1.1
            # Names shouldn't be all caps (likely not a person name)
            if entity.text.isupper():
                base_confidence *= 0.7
        
        elif field_type == 'age':
            # Age should be a reasonable number
            try:
                age_val = int(entity.text)
                if 18 <= age_val <= 100:
                    base_confidence *= 1.2
                else:
                    base_confidence *= 0.3
            except ValueError:
                base_confidence *= 0.1
        
        elif field_type in ['case_number', 'claim_number']:
            # Should contain alphanumeric characters
            if any(c.isalpha() for c in entity.text) and any(c.isdigit() for c in entity.text):
                base_confidence *= 1.1
        
        # Cross-reference with current regex value if available
        if current_value and isinstance(current_value, str):
            similarity = self._calculate_string_similarity(entity.text, current_value)
            if similarity > 0.8:
                base_confidence *= 1.2  # High similarity boosts confidence
            elif similarity < 0.3:
                base_confidence *= 0.7  # Low similarity reduces confidence
        
        return min(base_confidence, 1.0)
    
    def _get_entity_context(self, entity, document_text: str, window: int = 100) -> str:
        """Get context around an entity for evidence snippet."""
        start_pos = max(0, entity.start_char - window)
        end_pos = min(len(document_text), entity.end_char + window)
        return document_text[start_pos:end_pos]
    
    def _calculate_overall_confidence(self, confidence_breakdown: Dict[str, float]) -> float:
        """Calculate overall confidence score."""
        if not confidence_breakdown:
            return 0.0
        
        # Weight critical fields more heavily
        critical_fields = ['name', 'case_number', 'injury_date']
        critical_weight = 0.7
        standard_weight = 0.3
        
        critical_score = 0.0
        critical_count = 0
        standard_score = 0.0
        standard_count = 0
        
        for field, confidence in confidence_breakdown.items():
            if field in critical_fields:
                critical_score += confidence
                critical_count += 1
            else:
                standard_score += confidence
                standard_count += 1
        
        critical_avg = critical_score / critical_count if critical_count > 0 else 0.0
        standard_avg = standard_score / standard_count if standard_count > 0 else 0.0
        
        return critical_avg * critical_weight + standard_avg * standard_weight
    
    def _calculate_evidence_completeness(self, field_data: QMEFieldData) -> float:
        """Calculate evidence completeness score."""
        total_fields = len(self.field_extractor.required_fields)
        fields_with_evidence = len(field_data.evidence_provenance)
        
        return fields_with_evidence / total_fields if total_fields > 0 else 0.0
    
    def _infer_field_type_from_match(self, match: re.Match, context: ExtractionContext) -> str:
        """Infer the field type from the match context."""
        match_text = match.group(0).lower()
        
        # Check for field type indicators in the match or surrounding text
        if any(indicator in match_text for indicator in ['applicant', 'patient', 'name']):
            return 'name'
        elif any(indicator in match_text for indicator in ['case', 'adj', 'eams']):
            return 'case_number'
        elif any(indicator in match_text for indicator in ['claim', 'wc']):
            return 'claim_number'
        elif any(indicator in match_text for indicator in ['injury', 'accident', 'doi']):
            return 'injury_date'
        elif any(indicator in match_text for indicator in ['exam', 'evaluation', 'scheduled']):
            return 'exam_date'
        elif any(indicator in match_text for indicator in ['year', 'old', 'age']):
            return 'age'
        elif any(indicator in match_text for indicator in ['male', 'female', 'gender', 'sex']):
            return 'gender'
        elif any(indicator in match_text for indicator in ['knee', 'shoulder', 'back', 'neck', 'spine']):
            return 'body_parts'
        elif any(indicator in match_text for indicator in ['flexion', 'extension', 'degrees', 'rom']):
            return 'rom_measurements'
        elif any(indicator in match_text for indicator in ['table', 'chapter', 'ama', 'guides']):
            return 'ama_references'
        elif any(indicator in match_text for indicator in ['occupation', 'job', 'title']):
            return 'occupation'
        elif any(indicator in match_text for indicator in ['employer', 'company', 'worked']):
            return 'employer'
        
        return 'unknown'
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings (simple implementation)."""
        if not str1 or not str2:
            return 0.0
        
        str1, str2 = str1.lower().strip(), str2.lower().strip()
        
        if str1 == str2:
            return 1.0
        
        # Simple character-based similarity
        longer = str1 if len(str1) > len(str2) else str2
        shorter = str2 if len(str1) > len(str2) else str1
        
        if len(longer) == 0:
            return 1.0
        
        # Count matching characters
        matches = sum(1 for a, b in zip(shorter, longer) if a == b)
        return matches / len(longer)
    
    def _validate_extracted_fields(self, field_data: QMEFieldData) -> Dict[str, Any]:
        """Validate extracted field data with confidence-based thresholds."""
        validation_status = {}
        missing_fields = []
        extraction_errors = []
        
        for field_name in self.field_extractor.required_fields:
            field_value = getattr(field_data, field_name)
            field_confidence = field_data.extraction_confidence.get(field_name, 0.0)
            
            # Determine if field meets confidence threshold
            is_critical = field_name in self.field_extractor.critical_fields
            required_confidence = (self.field_extractor.confidence_thresholds['critical_fields'] 
                                 if is_critical 
                                 else self.field_extractor.confidence_thresholds['standard_fields'])
            
            if field_value is None or (isinstance(field_value, (list, dict)) and not field_value):
                validation_status[field_name] = False
                missing_fields.append(field_name)
            elif field_confidence < required_confidence:
                validation_status[field_name] = False
                extraction_errors.append(f"{field_name}: confidence {field_confidence:.2f} below threshold {required_confidence:.2f}")
            else:
                validation_status[field_name] = True
        
        return {
            'validation_status': validation_status,
            'missing_fields': missing_fields,
            'extraction_errors': extraction_errors
        }