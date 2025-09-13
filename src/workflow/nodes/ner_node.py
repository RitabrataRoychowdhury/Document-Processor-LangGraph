"""Named Entity Recognition workflow node."""

import re
from typing import Dict, Any, List, Optional, Tuple

from src.workflow.base.workflow_node import WorkflowNode, NodeResult
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class NERNode(WorkflowNode):
    """Node for Named Entity Recognition.
    
    Implements Single Responsibility Principle - handles only NER operations.
    Uses rule-based NER for medical entities (can be extended with ML models).
    """
    
    def __init__(self, node_id: str = None, correlation_id: str = None):
        super().__init__(node_id, correlation_id)
        self._initialize_patterns()
    
    def _initialize_patterns(self) -> None:
        """Initialize regex patterns for medical entity recognition."""
        # Patient name patterns
        self.name_patterns = [
            r'\b(?:Patient|Mr\.|Mrs\.|Ms\.|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            r'\b([A-Z][a-z]+,\s+[A-Z][a-z]+)\b',  # Last, First format
            r'\bName:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        ]
        
        # Date patterns
        self.date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            r'\b([A-Z][a-z]+\s+\d{1,2},\s+\d{4})\b',
            r'\b(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})\b'
        ]
        
        # Medical diagnosis patterns (ICD-10 style)
        self.diagnosis_patterns = [
            r'\b([A-Z]\d{2}(?:\.\d{1,2})?)\b',  # ICD-10 codes
            r'\bdiagnosis:?\s*([^.\n]+)',
            r'\bdiagnosed with\s+([^.\n]+)',
            r'\bcondition:?\s*([^.\n]+)'
        ]
        
        # Body part patterns
        self.body_part_patterns = [
            r'\b(spine|back|neck|shoulder|arm|hand|leg|foot|knee|ankle|hip|wrist|elbow)\b',
            r'\b(lumbar|cervical|thoracic|sacral)\s+(spine|region|area)\b',
            r'\b(left|right)\s+(arm|leg|hand|foot|shoulder|knee|ankle|hip|wrist|elbow)\b'
        ]
        
        # Impairment rating patterns
        self.impairment_patterns = [
            r'\b(\d{1,2})%\s+(?:whole\s+person\s+)?impairment\b',
            r'\bimpairment\s+rating:?\s*(\d{1,2})%\b',
            r'\bWPI:?\s*(\d{1,2})%\b',
            r'\bAMA\s+table\s+(\d+(?:-\d+)?)\b'
        ]
        
        # Medical findings patterns
        self.finding_patterns = [
            r'\bfindings?:?\s*([^.\n]+)',
            r'\bobservation:?\s*([^.\n]+)',
            r'\bnoted\s+([^.\n]+)',
            r'\bevidence\s+of\s+([^.\n]+)'
        ]
    
    def execute(self, state: Dict[str, Any]) -> NodeResult:
        """Execute named entity recognition."""
        try:
            extracted_text = state['extracted_text']
            
            logger.info(f"Starting NER on {len(extracted_text)} characters "
                       f"[correlation_id: {self.correlation_id}]")
            
            # Extract different types of entities
            entities = {
                'patients': self._extract_patients(extracted_text),
                'dates': self._extract_dates(extracted_text),
                'diagnoses': self._extract_diagnoses(extracted_text),
                'body_parts': self._extract_body_parts(extracted_text),
                'impairment_ratings': self._extract_impairment_ratings(extracted_text),
                'findings': self._extract_findings(extracted_text)
            }
            
            # Flatten entities into a single list with metadata
            all_entities = []
            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    all_entities.append({
                        'type': entity_type.rstrip('s'),  # Remove plural
                        'text': entity['text'],
                        'confidence': entity.get('confidence', 0.8),
                        'start_pos': entity.get('start_pos', -1),
                        'end_pos': entity.get('end_pos', -1),
                        'context': entity.get('context', ''),
                        'metadata': entity.get('metadata', {})
                    })
            
            # Calculate statistics
            entity_stats = {
                'total_entities': len(all_entities),
                'entity_types': {entity_type: len(entity_list) 
                               for entity_type, entity_list in entities.items()},
                'unique_entities': len(set(entity['text'].lower() for entity in all_entities))
            }
            
            result_data = {
                'entities_extracted': all_entities,
                'entity_statistics': entity_stats,
                'entities_by_type': entities,
                'ner_method': 'rule_based'
            }
            
            logger.info(f"NER completed: extracted {len(all_entities)} entities "
                       f"[correlation_id: {self.correlation_id}]")
            
            return NodeResult.success_result(
                f"NER completed: {len(all_entities)} entities extracted",
                data=result_data
            )
            
        except Exception as e:
            logger.error(f"NER failed: {e} [correlation_id: {self.correlation_id}]")
            return NodeResult.failure_result(
                f"NER failed: {str(e)}",
                error=e
            )
    
    def _extract_patients(self, text: str) -> List[Dict[str, Any]]:
        """Extract patient names from text."""
        patients = []
        
        for pattern in self.name_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                patient_name = match.group(1).strip()
                if len(patient_name) > 2 and self._is_likely_person_name(patient_name):
                    patients.append({
                        'text': patient_name,
                        'confidence': 0.7,
                        'start_pos': match.start(),
                        'end_pos': match.end(),
                        'context': self._get_context(text, match.start(), match.end()),
                        'metadata': {'pattern_used': pattern}
                    })
        
        return self._deduplicate_entities(patients)
    
    def _extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """Extract dates from text."""
        dates = []
        
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                date_text = match.group(1).strip()
                dates.append({
                    'text': date_text,
                    'confidence': 0.9,
                    'start_pos': match.start(),
                    'end_pos': match.end(),
                    'context': self._get_context(text, match.start(), match.end()),
                    'metadata': {'pattern_used': pattern}
                })
        
        return self._deduplicate_entities(dates)
    
    def _extract_diagnoses(self, text: str) -> List[Dict[str, Any]]:
        """Extract medical diagnoses from text."""
        diagnoses = []
        
        for pattern in self.diagnosis_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                diagnosis_text = match.group(1).strip()
                if len(diagnosis_text) > 3:
                    confidence = 0.9 if re.match(r'^[A-Z]\d{2}', diagnosis_text) else 0.6
                    diagnoses.append({
                        'text': diagnosis_text,
                        'confidence': confidence,
                        'start_pos': match.start(),
                        'end_pos': match.end(),
                        'context': self._get_context(text, match.start(), match.end()),
                        'metadata': {
                            'pattern_used': pattern,
                            'is_icd_code': bool(re.match(r'^[A-Z]\d{2}', diagnosis_text))
                        }
                    })
        
        return self._deduplicate_entities(diagnoses)
    
    def _extract_body_parts(self, text: str) -> List[Dict[str, Any]]:
        """Extract body parts from text."""
        body_parts = []
        
        for pattern in self.body_part_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                body_part_text = match.group().strip()
                body_parts.append({
                    'text': body_part_text,
                    'confidence': 0.8,
                    'start_pos': match.start(),
                    'end_pos': match.end(),
                    'context': self._get_context(text, match.start(), match.end()),
                    'metadata': {'pattern_used': pattern}
                })
        
        return self._deduplicate_entities(body_parts)
    
    def _extract_impairment_ratings(self, text: str) -> List[Dict[str, Any]]:
        """Extract impairment ratings from text."""
        ratings = []
        
        for pattern in self.impairment_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                rating_text = match.group().strip()
                # Extract percentage if available
                percentage_match = re.search(r'(\d{1,2})%', rating_text)
                percentage = int(percentage_match.group(1)) if percentage_match else None
                
                ratings.append({
                    'text': rating_text,
                    'confidence': 0.9,
                    'start_pos': match.start(),
                    'end_pos': match.end(),
                    'context': self._get_context(text, match.start(), match.end()),
                    'metadata': {
                        'pattern_used': pattern,
                        'percentage': percentage
                    }
                })
        
        return self._deduplicate_entities(ratings)
    
    def _extract_findings(self, text: str) -> List[Dict[str, Any]]:
        """Extract medical findings from text."""
        findings = []
        
        for pattern in self.finding_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                finding_text = match.group(1).strip()
                if len(finding_text) > 5:
                    findings.append({
                        'text': finding_text,
                        'confidence': 0.7,
                        'start_pos': match.start(),
                        'end_pos': match.end(),
                        'context': self._get_context(text, match.start(), match.end()),
                        'metadata': {'pattern_used': pattern}
                    })
        
        return self._deduplicate_entities(findings)
    
    def _is_likely_person_name(self, name: str) -> bool:
        """Check if a string is likely a person's name."""
        # Simple heuristics for person names
        words = name.split()
        if len(words) < 1 or len(words) > 4:
            return False
        
        # Check if all words are capitalized
        if not all(word[0].isupper() for word in words):
            return False
        
        # Exclude common non-name words
        excluded_words = {'THE', 'AND', 'OR', 'OF', 'IN', 'ON', 'AT', 'TO', 'FOR'}
        if any(word.upper() in excluded_words for word in words):
            return False
        
        return True
    
    def _get_context(self, text: str, start: int, end: int, context_size: int = 50) -> str:
        """Get context around an entity."""
        context_start = max(0, start - context_size)
        context_end = min(len(text), end + context_size)
        return text[context_start:context_end].strip()
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate entities based on text content."""
        seen = set()
        unique_entities = []
        
        for entity in entities:
            entity_key = entity['text'].lower().strip()
            if entity_key not in seen:
                seen.add(entity_key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """Validate input state for NER."""
        required_keys = self.get_required_inputs()
        
        for key in required_keys:
            if key not in state:
                logger.error(f"Missing required input key: {key}")
                return False
        
        extracted_text = state.get('extracted_text')
        if not isinstance(extracted_text, str) or len(extracted_text.strip()) < 10:
            logger.error("Invalid extracted_text: must be a string with at least 10 characters")
            return False
        
        return True
    
    def get_required_inputs(self) -> List[str]:
        """Get required input keys."""
        return ['extracted_text']
    
    def get_output_keys(self) -> List[str]:
        """Get output keys this node adds to state."""
        return [
            'entities_extracted',
            'entity_statistics',
            'entities_by_type',
            'ner_method'
        ]
    
    def can_retry(self, error: Exception) -> bool:
        """Determine if NER can be retried."""
        # NER is generally retryable unless it's a fundamental input error
        non_retryable_errors = (ValueError, TypeError)
        return not isinstance(error, non_retryable_errors)


class MLNERNode(NERNode):
    """Enhanced NER node using machine learning models.
    
    Extends NERNode with ML-based entity recognition capabilities.
    """
    
    def __init__(self, model_name: str = "en_core_web_sm", 
                 node_id: str = None, correlation_id: str = None):
        super().__init__(node_id, correlation_id)
        self.model_name = model_name
        self.nlp_model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load spaCy NLP model."""
        try:
            import spacy
            self.nlp_model = spacy.load(self.model_name)
            logger.info(f"Loaded spaCy model: {self.model_name}")
        except ImportError:
            logger.warning("spaCy not available, falling back to rule-based NER")
            self.nlp_model = None
        except OSError:
            logger.warning(f"spaCy model {self.model_name} not found, falling back to rule-based NER")
            self.nlp_model = None
    
    def execute(self, state: Dict[str, Any]) -> NodeResult:
        """Execute ML-based NER with rule-based fallback."""
        if self.nlp_model is None:
            # Fallback to rule-based NER
            logger.info("Using rule-based NER fallback")
            return super().execute(state)
        
        try:
            extracted_text = state['extracted_text']
            
            logger.info(f"Starting ML-based NER on {len(extracted_text)} characters "
                       f"[correlation_id: {self.correlation_id}]")
            
            # Process text with spaCy
            doc = self.nlp_model(extracted_text)
            
            # Extract entities using spaCy
            ml_entities = []
            for ent in doc.ents:
                ml_entities.append({
                    'type': ent.label_.lower(),
                    'text': ent.text,
                    'confidence': 0.8,  # spaCy doesn't provide confidence scores by default
                    'start_pos': ent.start_char,
                    'end_pos': ent.end_char,
                    'context': self._get_context(extracted_text, ent.start_char, ent.end_char),
                    'metadata': {
                        'spacy_label': ent.label_,
                        'spacy_description': spacy.explain(ent.label_) if hasattr(spacy, 'explain') else ''
                    }
                })
            
            # Also run rule-based extraction for medical-specific entities
            rule_result = super().execute(state)
            rule_entities = rule_result.data.get('entities_extracted', [])
            
            # Combine ML and rule-based entities
            all_entities = ml_entities + rule_entities
            
            # Deduplicate combined entities
            all_entities = self._deduplicate_entities(all_entities)
            
            # Calculate statistics
            entity_stats = {
                'total_entities': len(all_entities),
                'ml_entities': len(ml_entities),
                'rule_entities': len(rule_entities),
                'unique_entities': len(set(entity['text'].lower() for entity in all_entities))
            }
            
            result_data = {
                'entities_extracted': all_entities,
                'entity_statistics': entity_stats,
                'ner_method': 'ml_and_rules',
                'ml_model': self.model_name
            }
            
            logger.info(f"ML-based NER completed: extracted {len(all_entities)} entities "
                       f"[correlation_id: {self.correlation_id}]")
            
            return NodeResult.success_result(
                f"ML-based NER completed: {len(all_entities)} entities extracted",
                data=result_data
            )
            
        except Exception as e:
            logger.error(f"ML-based NER failed, falling back to rule-based: {e}")
            # Fallback to rule-based NER
            return super().execute(state)
    
    def get_output_keys(self) -> List[str]:
        """Get output keys including ML-specific keys."""
        base_keys = super().get_output_keys()
        return base_keys + ['ml_model', 'ml_entities', 'rule_entities']