"""
Enhanced Knowledge Graph-Driven Document Processing Pipeline.

This module implements intelligent semantic chunking, advanced medical entity extraction,
relationship mapping, and comprehensive provenance tracking for QME document processing.
"""

import os
import re
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path

try:
    import spacy
    from spacy.matcher import Matcher
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available, falling back to rule-based extraction")

from ..models.knowledge_graph import (
    KnowledgeNode, KnowledgeRelationship, Patient, Diagnosis, 
    ImagingStudy, Finding, ImpairmentRating, Claim, Section
)
from ..repositories.knowledge_graph_repository import KnowledgeGraphRepository, SQLiteKnowledgeGraphRepository
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ProvenanceReference:
    """Tracks the source of extracted information."""
    doc_id: str
    page: Optional[int] = None
    offset: Optional[int] = None
    snippet: Optional[str] = None
    confidence: float = 1.0
    extraction_method: str = "rule_based"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MedicalEntity:
    """Enhanced medical entity with provenance and relationships."""
    id: str
    entity_type: str  # Patient, Diagnosis, ImagingStudy, Findings, Claim, Treatment, ImpairmentRating
    text: str
    normalized_text: str
    confidence: float
    provenance: List[ProvenanceReference]
    metadata: Dict[str, Any] = field(default_factory=dict)
    relationships: List[str] = field(default_factory=list)  # IDs of related entities
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class EntityRelationship:
    """Relationship between medical entities with confidence scoring."""
    id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str  # "DIAGNOSES", "TREATS", "CAUSES", "RATES_IMPAIRMENT", etc.
    confidence: float
    evidence: str  # Text evidence supporting the relationship
    provenance: List[ProvenanceReference]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SemanticChunk:
    """Semantically coherent chunk of medical text."""
    id: str
    text: str
    chunk_type: str  # "history", "examination", "diagnosis", "treatment", "assessment"
    page_number: Optional[int] = None
    start_offset: int = 0
    end_offset: int = 0
    entities: List[MedicalEntity] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedDocumentProcessor:
    """
    Enhanced document processor with intelligent semantic chunking and medical entity extraction.
    
    Features:
    - Intelligent semantic chunking preserving medical context boundaries
    - Advanced medical entity extraction using spaCy medical models
    - Relationship mapping with confidence scoring
    - Comprehensive provenance tracking
    - Integration with knowledge graph repository
    """
    
    def __init__(self, 
                 kg_repository: Optional[KnowledgeGraphRepository] = None,
                 spacy_model: str = "en_core_web_sm"):
        """
        Initialize the enhanced document processor.
        
        Args:
            kg_repository: Knowledge graph repository for storing entities
            spacy_model: spaCy model name for NLP processing
        """
        self.kg_repository = kg_repository or SQLiteKnowledgeGraphRepository()
        self.spacy_model_name = spacy_model
        self.nlp = None
        self.matcher = None
        
        # Initialize spaCy model and medical patterns
        self._initialize_nlp_model()
        self._initialize_medical_patterns()
        
        # Medical section patterns for semantic chunking
        self._initialize_section_patterns()
        
        # Entity relationship patterns
        self._initialize_relationship_patterns()
    
    def _initialize_nlp_model(self) -> None:
        """Initialize spaCy NLP model with medical extensions."""
        if not SPACY_AVAILABLE:
            logger.warning("spaCy not available, using rule-based extraction only")
            return
        
        try:
            self.nlp = spacy.load(self.spacy_model_name)
            self.matcher = Matcher(self.nlp.vocab)
            logger.info(f"Loaded spaCy model: {self.spacy_model_name}")
        except OSError:
            logger.warning(f"spaCy model {self.spacy_model_name} not found, using rule-based extraction")
            self.nlp = None
            self.matcher = None
    
    def _initialize_medical_patterns(self) -> None:
        """Initialize medical entity extraction patterns."""
        # Patient name patterns
        self.patient_patterns = [
            r'\bPatient:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'\b(?:Mr\.|Mrs\.|Ms\.|Dr\.)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'\bName:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'\b([A-Z][a-z]+,\s+[A-Z][a-z]+)',  # Last, First format
        ]
        
        # Diagnosis patterns (ICD-10 and descriptive)
        self.diagnosis_patterns = [
            r'\b([A-Z]\d{2}(?:\.\d{1,2})?)\b',  # ICD-10 codes
            r'\bdiagnosis:?\s*([^.\n]+)',
            r'\bdiagnosed with\s+([^.\n]+)',
            r'\bcondition:?\s*([^.\n]+)',
            r'\b(arthritis|diabetes|hypertension|pneumonia|bronchitis|sclerosis|stenosis)\b',
        ]
        
        # Imaging study patterns
        self.imaging_patterns = [
            r'\b(MRI|CT|X-ray|ultrasound|mammogram)\s+(?:of\s+)?([^.\n]+)',
            r'\b(magnetic resonance imaging|computed tomography|radiograph)\s+(?:of\s+)?([^.\n]+)',
            r'\bimaging\s+(?:study|studies):?\s*([^.\n]+)',
        ]
        
        # Treatment patterns
        self.treatment_patterns = [
            r'\btreatment:?\s*([^.\n]+)',
            r'\btherapy:?\s*([^.\n]+)',
            r'\bmedication:?\s*([^.\n]+)',
            r'\bsurgery:?\s*([^.\n]+)',
            r'\bprocedure:?\s*([^.\n]+)',
        ]
        
        # Impairment rating patterns
        self.impairment_patterns = [
            r'\b(\d{1,2})%\s+(?:whole\s+person\s+)?impairment\b',
            r'\bimpairment\s+rating:?\s*(\d{1,2})%\b',
            r'\bWPI:?\s*(\d{1,2})%\b',
            r'\bAMA\s+table\s+(\d+(?:-\d+)?)\b',
        ]
        
        # Findings patterns
        self.findings_patterns = [
            r'\bfindings?:?\s*([^.\n]+)',
            r'\bobservation:?\s*([^.\n]+)',
            r'\bnoted\s+([^.\n]+)',
            r'\bevidence\s+of\s+([^.\n]+)',
            r'\breveals?\s+([^.\n]+)',
        ]
        
        # Claim information patterns
        self.claim_patterns = [
            r'\bclaim\s+(?:number|#):?\s*([A-Z0-9-]+)',
            r'\bcase\s+(?:number|#):?\s*([A-Z0-9-]+)',
            r'\binjury\s+date:?\s*([0-9/\-]+)',
            r'\bdate\s+of\s+injury:?\s*([0-9/\-]+)',
        ]
    
    def _initialize_section_patterns(self) -> None:
        """Initialize patterns for identifying medical document sections."""
        self.section_patterns = {
            'history': [
                r'\bhistory\s+of\s+present\s+illness\b',
                r'\bchief\s+complaint\b',
                r'\bbackground\b',
                r'HISTORY\s+OF\s+PRESENT\s+ILLNESS',
            ],
            'examination': [
                r'\bphysical\s+examination\b',
                r'PHYSICAL\s+EXAMINATION',
                r'\bobservation\b',
                r'\binspection\b',
                r'\bpalpation\b',
            ],
            'diagnosis': [
                r'\bdiagnosis\b',
                r'DIAGNOSIS',
                r'\bimpression\b',
                r'\bassessment\b',
            ],
            'treatment': [
                r'\btreatment\b',
                r'TREATMENT',
                r'\btherapy\b',
                r'\bmanagement\b',
                r'\bplan\b',
            ],
            'findings': [
                r'\bfindings?\b',
                r'\bresults?\b',
                r'\bobservations?\b',
            ]
        }
    
    def _initialize_relationship_patterns(self) -> None:
        """Initialize patterns for detecting entity relationships."""
        self.relationship_patterns = {
            'DIAGNOSES': [
                r'diagnosed\s+with',
                r'suffers?\s+from',
                r'has\s+(?:a\s+)?(?:diagnosis\s+of|condition\s+of)',
            ],
            'TREATS': [
                r'treated?\s+(?:with|using)',
                r'therapy\s+for',
                r'medication\s+for',
            ],
            'CAUSES': [
                r'caused\s+by',
                r'due\s+to',
                r'resulting\s+from',
            ],
            'RATES_IMPAIRMENT': [
                r'impairment\s+rating\s+(?:of|is)',
                r'rated\s+at',
                r'percentage\s+(?:of|is)',
            ],
            'SHOWS': [
                r'shows?',
                r'reveals?',
                r'demonstrates?',
            ]
        }

    def process_patient_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process patient documents through the enhanced pipeline.
        
        Args:
            documents: List of document dictionaries with 'file_path' and 'doc_id'
            
        Returns:
            Processing result with extracted entities and relationships
        """
        logger.info(f"Starting enhanced processing of {len(documents)} documents")
        
        processing_result = {
            'processed_documents': [],
            'total_entities': 0,
            'total_relationships': 0,
            'entities_by_type': {},
            'processing_errors': [],
            'provenance_records': []
        }
        
        for doc_info in documents:
            try:
                doc_result = self._process_single_document(doc_info)
                processing_result['processed_documents'].append(doc_result)
                processing_result['total_entities'] += doc_result.get('entity_count', 0)
                processing_result['total_relationships'] += doc_result.get('relationship_count', 0)
                
                # Aggregate entity counts by type
                for entity_type, count in doc_result.get('entities_by_type', {}).items():
                    processing_result['entities_by_type'][entity_type] = (
                        processing_result['entities_by_type'].get(entity_type, 0) + count
                    )
                
            except Exception as e:
                error_info = {
                    'document': doc_info.get('file_path', 'unknown'),
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                processing_result['processing_errors'].append(error_info)
                logger.error(f"Error processing document {doc_info.get('file_path')}: {e}")
        
        logger.info(f"Enhanced processing completed: {processing_result['total_entities']} entities, "
                   f"{processing_result['total_relationships']} relationships")
        
        return processing_result
    
    def _process_single_document(self, doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single document through the enhanced pipeline."""
        file_path = doc_info['file_path']
        doc_id = doc_info.get('doc_id', str(uuid.uuid4()))
        
        logger.info(f"Processing document: {file_path}")
        
        # Extract text content
        text_content = self._extract_text_content(file_path)
        
        # Perform intelligent semantic chunking
        semantic_chunks = self.perform_semantic_chunking(text_content, doc_id)
        
        # Extract medical entities from chunks
        all_entities = []
        for chunk in semantic_chunks:
            chunk_entities = self.extract_medical_entities(chunk.text, doc_id, chunk.page_number)
            all_entities.extend(chunk_entities)
            chunk.entities = chunk_entities
        
        # Establish relationships between entities
        relationships = self.establish_relationships(all_entities)
        
        # Store in knowledge graph
        self._store_in_knowledge_graph(all_entities, relationships, semantic_chunks)
        
        # Prepare result
        entities_by_type = {}
        for entity in all_entities:
            entity_type = entity.entity_type
            entities_by_type[entity_type] = entities_by_type.get(entity_type, 0) + 1
        
        return {
            'document_id': doc_id,
            'file_path': file_path,
            'entity_count': len(all_entities),
            'relationship_count': len(relationships),
            'entities_by_type': entities_by_type,
            'chunk_count': len(semantic_chunks),
            'entities': [self._entity_to_dict(e) for e in all_entities],
            'relationships': [self._relationship_to_dict(r) for r in relationships]
        }

    def _extract_text_content(self, file_path: str) -> str:
        """Extract text content from document file."""
        try:
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.pdf':
                return self._extract_pdf_text(file_path)
            elif file_extension == '.docx':
                return self._extract_docx_text(file_path)
            elif file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            import PyPDF2
            text_content = ""
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
            
            return text_content
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            from docx import Document
            doc = Document(file_path)
            text_content = ""
            
            for paragraph in doc.paragraphs:
                text_content += paragraph.text + "\n"
            
            return text_content
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            raise

    def perform_semantic_chunking(self, text: str, doc_id: str) -> List[SemanticChunk]:
        """
        Perform intelligent semantic chunking that preserves medical context boundaries.
        
        Args:
            text: Document text content
            doc_id: Document identifier
            
        Returns:
            List of semantic chunks with preserved medical context
        """
        logger.info("Performing semantic chunking with medical context preservation")
        
        chunks = []
        
        # Split text into lines first to better detect section headers
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        current_chunk = ""
        current_chunk_type = "general"
        current_page = 1
        char_offset = 0
        
        for line in lines:
            # Detect section type for this line
            line_section_type = self._detect_section_type(line)
            
            # If this line indicates a new section, save current chunk and start new one
            if line_section_type != "general" and line_section_type != current_chunk_type:
                # Save current chunk if it has content
                if current_chunk.strip():
                    chunk = SemanticChunk(
                        id=str(uuid.uuid4()),
                        text=current_chunk.strip(),
                        chunk_type=current_chunk_type,
                        page_number=current_page,
                        start_offset=char_offset - len(current_chunk),
                        end_offset=char_offset,
                        metadata={'doc_id': doc_id}
                    )
                    chunks.append(chunk)
                
                # Start new chunk with this line
                current_chunk = line + "\n"
                current_chunk_type = line_section_type
            else:
                # Add line to current chunk
                current_chunk += line + "\n"
            
            char_offset += len(line) + 1
            
            # Estimate page breaks (rough approximation)
            if char_offset % 3000 == 0:  # Assume ~3000 chars per page
                current_page += 1
        
        # Add final chunk
        if current_chunk.strip():
            chunk = SemanticChunk(
                id=str(uuid.uuid4()),
                text=current_chunk.strip(),
                chunk_type=current_chunk_type,
                page_number=current_page,
                start_offset=char_offset - len(current_chunk),
                end_offset=char_offset,
                metadata={'doc_id': doc_id}
            )
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} semantic chunks")
        return chunks
    
    def _detect_section_type(self, text: str) -> str:
        """Detect the type of medical section based on content."""
        text_lower = text.lower()
        
        for section_type, patterns in self.section_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return section_type
        
        return "general"

    def extract_medical_entities(self, text: str, doc_id: str, page_number: Optional[int] = None) -> List[MedicalEntity]:
        """
        Extract medical entities using advanced NER with spaCy medical models.
        
        Args:
            text: Text content to process
            doc_id: Document identifier for provenance
            page_number: Page number for provenance
            
        Returns:
            List of extracted medical entities with provenance
        """
        logger.debug(f"Extracting medical entities from {len(text)} characters")
        
        entities = []
        
        # Extract different types of entities
        entities.extend(self._extract_patients(text, doc_id, page_number))
        entities.extend(self._extract_diagnoses(text, doc_id, page_number))
        entities.extend(self._extract_imaging_studies(text, doc_id, page_number))
        entities.extend(self._extract_findings(text, doc_id, page_number))
        entities.extend(self._extract_claims(text, doc_id, page_number))
        entities.extend(self._extract_treatments(text, doc_id, page_number))
        entities.extend(self._extract_impairment_ratings(text, doc_id, page_number))
        
        # Use spaCy for additional entity extraction if available
        if self.nlp:
            entities.extend(self._extract_spacy_entities(text, doc_id, page_number))
        
        # Deduplicate entities
        entities = self._deduplicate_entities(entities)
        
        logger.debug(f"Extracted {len(entities)} medical entities")
        return entities
    
    def _extract_patients(self, text: str, doc_id: str, page_number: Optional[int]) -> List[MedicalEntity]:
        """Extract patient entities."""
        entities = []
        
        for pattern in self.patient_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                patient_name = match.group(1).strip()
                
                # Clean up the patient name - remove newlines and extra text
                patient_name = re.sub(r'\n.*', '', patient_name).strip()
                
                if self._is_valid_patient_name(patient_name):
                    provenance = ProvenanceReference(
                        doc_id=doc_id,
                        page=page_number,
                        offset=match.start(),
                        snippet=self._get_context_snippet(text, match.start(), match.end()),
                        confidence=0.8,
                        extraction_method="pattern_matching"
                    )
                    
                    entity = MedicalEntity(
                        id=str(uuid.uuid4()),
                        entity_type="Patient",
                        text=patient_name,
                        normalized_text=patient_name.title(),
                        confidence=0.8,
                        provenance=[provenance],
                        metadata={'pattern_used': pattern}
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_diagnoses(self, text: str, doc_id: str, page_number: Optional[int]) -> List[MedicalEntity]:
        """Extract diagnosis entities."""
        entities = []
        
        for pattern in self.diagnosis_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                diagnosis_text = match.group(1).strip() if match.groups() else match.group().strip()
                
                if len(diagnosis_text) > 2:
                    # Determine confidence based on pattern type
                    confidence = 0.9 if re.match(r'^[A-Z]\d{2}', diagnosis_text) else 0.7
                    
                    provenance = ProvenanceReference(
                        doc_id=doc_id,
                        page=page_number,
                        offset=match.start(),
                        snippet=self._get_context_snippet(text, match.start(), match.end()),
                        confidence=confidence,
                        extraction_method="pattern_matching"
                    )
                    
                    entity = MedicalEntity(
                        id=str(uuid.uuid4()),
                        entity_type="Diagnosis",
                        text=diagnosis_text,
                        normalized_text=diagnosis_text.lower().strip(),
                        confidence=confidence,
                        provenance=[provenance],
                        metadata={
                            'pattern_used': pattern,
                            'is_icd_code': bool(re.match(r'^[A-Z]\d{2}', diagnosis_text))
                        }
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_imaging_studies(self, text: str, doc_id: str, page_number: Optional[int]) -> List[MedicalEntity]:
        """Extract imaging study entities."""
        entities = []
        
        for pattern in self.imaging_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                study_type = match.group(1).strip()
                study_details = match.group(2).strip() if len(match.groups()) > 1 else ""
                
                provenance = ProvenanceReference(
                    doc_id=doc_id,
                    page=page_number,
                    offset=match.start(),
                    snippet=self._get_context_snippet(text, match.start(), match.end()),
                    confidence=0.8,
                    extraction_method="pattern_matching"
                )
                
                entity = MedicalEntity(
                    id=str(uuid.uuid4()),
                    entity_type="ImagingStudy",
                    text=match.group().strip(),
                    normalized_text=f"{study_type.upper()}: {study_details}",
                    confidence=0.8,
                    provenance=[provenance],
                    metadata={
                        'study_type': study_type,
                        'study_details': study_details,
                        'pattern_used': pattern
                    }
                )
                entities.append(entity)
        
        return entities
    
    def _extract_findings(self, text: str, doc_id: str, page_number: Optional[int]) -> List[MedicalEntity]:
        """Extract medical findings entities."""
        entities = []
        
        for pattern in self.findings_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                finding_text = match.group(1).strip() if match.groups() else match.group().strip()
                
                if len(finding_text) > 5:
                    provenance = ProvenanceReference(
                        doc_id=doc_id,
                        page=page_number,
                        offset=match.start(),
                        snippet=self._get_context_snippet(text, match.start(), match.end()),
                        confidence=0.7,
                        extraction_method="pattern_matching"
                    )
                    
                    entity = MedicalEntity(
                        id=str(uuid.uuid4()),
                        entity_type="Findings",
                        text=finding_text,
                        normalized_text=finding_text.lower().strip(),
                        confidence=0.7,
                        provenance=[provenance],
                        metadata={'pattern_used': pattern}
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_claims(self, text: str, doc_id: str, page_number: Optional[int]) -> List[MedicalEntity]:
        """Extract claim information entities."""
        entities = []
        
        for pattern in self.claim_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                claim_info = match.group(1).strip()
                
                provenance = ProvenanceReference(
                    doc_id=doc_id,
                    page=page_number,
                    offset=match.start(),
                    snippet=self._get_context_snippet(text, match.start(), match.end()),
                    confidence=0.9,
                    extraction_method="pattern_matching"
                )
                
                entity = MedicalEntity(
                    id=str(uuid.uuid4()),
                    entity_type="Claim",
                    text=match.group().strip(),
                    normalized_text=claim_info.upper(),
                    confidence=0.9,
                    provenance=[provenance],
                    metadata={'pattern_used': pattern}
                )
                entities.append(entity)
        
        return entities
    
    def _extract_treatments(self, text: str, doc_id: str, page_number: Optional[int]) -> List[MedicalEntity]:
        """Extract treatment entities."""
        entities = []
        
        for pattern in self.treatment_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                treatment_text = match.group(1).strip() if match.groups() else match.group().strip()
                
                if len(treatment_text) > 3:
                    provenance = ProvenanceReference(
                        doc_id=doc_id,
                        page=page_number,
                        offset=match.start(),
                        snippet=self._get_context_snippet(text, match.start(), match.end()),
                        confidence=0.7,
                        extraction_method="pattern_matching"
                    )
                    
                    entity = MedicalEntity(
                        id=str(uuid.uuid4()),
                        entity_type="Treatment",
                        text=treatment_text,
                        normalized_text=treatment_text.lower().strip(),
                        confidence=0.7,
                        provenance=[provenance],
                        metadata={'pattern_used': pattern}
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_impairment_ratings(self, text: str, doc_id: str, page_number: Optional[int]) -> List[MedicalEntity]:
        """Extract impairment rating entities."""
        entities = []
        
        for pattern in self.impairment_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                rating_text = match.group().strip()
                
                # Extract percentage value
                percentage_match = re.search(r'(\d{1,2})%', rating_text)
                percentage = int(percentage_match.group(1)) if percentage_match else None
                
                provenance = ProvenanceReference(
                    doc_id=doc_id,
                    page=page_number,
                    offset=match.start(),
                    snippet=self._get_context_snippet(text, match.start(), match.end()),
                    confidence=0.9,
                    extraction_method="pattern_matching"
                )
                
                entity = MedicalEntity(
                    id=str(uuid.uuid4()),
                    entity_type="ImpairmentRating",
                    text=rating_text,
                    normalized_text=f"{percentage}% impairment" if percentage else rating_text,
                    confidence=0.9,
                    provenance=[provenance],
                    metadata={
                        'percentage': percentage,
                        'pattern_used': pattern
                    }
                )
                entities.append(entity)
        
        return entities
    
    def _extract_spacy_entities(self, text: str, doc_id: str, page_number: Optional[int]) -> List[MedicalEntity]:
        """Extract entities using spaCy NER if available."""
        entities = []
        
        if not self.nlp:
            return entities
        
        try:
            doc = self.nlp(text)
            
            for ent in doc.ents:
                # Map spaCy entity to our medical entity type
                entity_type = self._map_spacy_entity_type(ent.label_)
                
                if entity_type:
                    provenance = ProvenanceReference(
                        doc_id=doc_id,
                        page=page_number,
                        offset=ent.start_char,
                        snippet=self._get_context_snippet(text, ent.start_char, ent.end_char),
                        confidence=0.6,  # Lower confidence for spaCy entities
                        extraction_method="spacy_ner"
                    )
                    
                    entity = MedicalEntity(
                        id=str(uuid.uuid4()),
                        entity_type=entity_type,
                        text=ent.text,
                        normalized_text=ent.text.lower().strip(),
                        confidence=0.6,
                        provenance=[provenance],
                        metadata={'spacy_label': ent.label_}
                    )
                    entities.append(entity)
        
        except Exception as e:
            logger.warning(f"Error in spaCy entity extraction: {e}")
        
        return entities
    
    def _map_spacy_entity_type(self, spacy_label: str) -> Optional[str]:
        """Map spaCy entity labels to our medical entity types."""
        mapping = {
            'PERSON': 'Patient',
            'ORG': None,  # Skip organizations for now
            'DATE': None,  # Handle dates separately
            'MONEY': None,
            'PERCENT': 'ImpairmentRating',
            'CARDINAL': None,
            'ORDINAL': None,
        }
        return mapping.get(spacy_label)

    def establish_relationships(self, entities: List[MedicalEntity]) -> List[EntityRelationship]:
        """
        Establish relationships between medical entities with confidence scoring.
        
        Args:
            entities: List of extracted medical entities
            
        Returns:
            List of entity relationships with confidence scores
        """
        logger.info(f"Establishing relationships between {len(entities)} entities")
        
        relationships = []
        
        # Group entities by type for efficient relationship detection
        entities_by_type = {}
        for entity in entities:
            entity_type = entity.entity_type
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)
        
        # Establish diagnosis-impairment relationships
        if 'Diagnosis' in entities_by_type and 'ImpairmentRating' in entities_by_type:
            relationships.extend(self._establish_diagnosis_impairment_relationships(
                entities_by_type['Diagnosis'], entities_by_type['ImpairmentRating']
            ))
        
        # Establish patient-diagnosis relationships
        if 'Patient' in entities_by_type and 'Diagnosis' in entities_by_type:
            relationships.extend(self._establish_patient_diagnosis_relationships(
                entities_by_type['Patient'], entities_by_type['Diagnosis']
            ))
        
        # Establish diagnosis-treatment relationships
        if 'Diagnosis' in entities_by_type and 'Treatment' in entities_by_type:
            relationships.extend(self._establish_diagnosis_treatment_relationships(
                entities_by_type['Diagnosis'], entities_by_type['Treatment']
            ))
        
        # Establish imaging-findings relationships
        if 'ImagingStudy' in entities_by_type and 'Findings' in entities_by_type:
            relationships.extend(self._establish_imaging_findings_relationships(
                entities_by_type['ImagingStudy'], entities_by_type['Findings']
            ))
        
        logger.info(f"Established {len(relationships)} entity relationships")
        return relationships
    
    def _establish_diagnosis_impairment_relationships(self, diagnoses: List[MedicalEntity], 
                                                   ratings: List[MedicalEntity]) -> List[EntityRelationship]:
        """Establish relationships between diagnoses and impairment ratings."""
        relationships = []
        
        for diagnosis in diagnoses:
            for rating in ratings:
                # Check if they appear in similar context
                confidence = self._calculate_relationship_confidence(
                    diagnosis, rating, "RATES_IMPAIRMENT"
                )
                
                if confidence > 0.5:
                    relationship = EntityRelationship(
                        id=str(uuid.uuid4()),
                        source_entity_id=diagnosis.id,
                        target_entity_id=rating.id,
                        relationship_type="RATES_IMPAIRMENT",
                        confidence=confidence,
                        evidence=self._get_relationship_evidence(diagnosis, rating),
                        provenance=diagnosis.provenance + rating.provenance
                    )
                    relationships.append(relationship)
        
        return relationships
    
    def _establish_patient_diagnosis_relationships(self, patients: List[MedicalEntity], 
                                                 diagnoses: List[MedicalEntity]) -> List[EntityRelationship]:
        """Establish relationships between patients and diagnoses."""
        relationships = []
        
        for patient in patients:
            for diagnosis in diagnoses:
                # Assume patient-diagnosis relationship if they're in the same document
                confidence = 0.8  # High confidence for same-document relationships
                
                relationship = EntityRelationship(
                    id=str(uuid.uuid4()),
                    source_entity_id=patient.id,
                    target_entity_id=diagnosis.id,
                    relationship_type="HAS_DIAGNOSIS",
                    confidence=confidence,
                    evidence=f"Patient {patient.text} and diagnosis {diagnosis.text} in same document",
                    provenance=patient.provenance + diagnosis.provenance
                )
                relationships.append(relationship)
        
        return relationships
    
    def _establish_diagnosis_treatment_relationships(self, diagnoses: List[MedicalEntity], 
                                                   treatments: List[MedicalEntity]) -> List[EntityRelationship]:
        """Establish relationships between diagnoses and treatments."""
        relationships = []
        
        for diagnosis in diagnoses:
            for treatment in treatments:
                confidence = self._calculate_relationship_confidence(
                    diagnosis, treatment, "TREATS"
                )
                
                if confidence > 0.4:
                    relationship = EntityRelationship(
                        id=str(uuid.uuid4()),
                        source_entity_id=treatment.id,
                        target_entity_id=diagnosis.id,
                        relationship_type="TREATS",
                        confidence=confidence,
                        evidence=self._get_relationship_evidence(treatment, diagnosis),
                        provenance=diagnosis.provenance + treatment.provenance
                    )
                    relationships.append(relationship)
        
        return relationships
    
    def _establish_imaging_findings_relationships(self, imaging_studies: List[MedicalEntity], 
                                                findings: List[MedicalEntity]) -> List[EntityRelationship]:
        """Establish relationships between imaging studies and findings."""
        relationships = []
        
        for imaging in imaging_studies:
            for finding in findings:
                confidence = self._calculate_relationship_confidence(
                    imaging, finding, "SHOWS"
                )
                
                if confidence > 0.5:
                    relationship = EntityRelationship(
                        id=str(uuid.uuid4()),
                        source_entity_id=imaging.id,
                        target_entity_id=finding.id,
                        relationship_type="SHOWS",
                        confidence=confidence,
                        evidence=self._get_relationship_evidence(imaging, finding),
                        provenance=imaging.provenance + finding.provenance
                    )
                    relationships.append(relationship)
        
        return relationships
    
    def _calculate_relationship_confidence(self, entity1: MedicalEntity, entity2: MedicalEntity, 
                                         relationship_type: str) -> float:
        """Calculate confidence score for a potential relationship."""
        confidence = 0.0
        
        # Check if entities appear in similar context (same provenance)
        for prov1 in entity1.provenance:
            for prov2 in entity2.provenance:
                if prov1.doc_id == prov2.doc_id:
                    confidence += 0.3
                    
                    # Check proximity (within same page or close offsets)
                    if prov1.page == prov2.page:
                        confidence += 0.2
                    
                    if (prov1.offset is not None and prov2.offset is not None and 
                        abs(prov1.offset - prov2.offset) < 500):
                        confidence += 0.3
        
        # Check for relationship patterns in context
        if relationship_type in self.relationship_patterns:
            for prov1 in entity1.provenance:
                if prov1.snippet:
                    for pattern in self.relationship_patterns[relationship_type]:
                        if re.search(pattern, prov1.snippet, re.IGNORECASE):
                            confidence += 0.4
                            break
        
        return min(confidence, 1.0)
    
    def _get_relationship_evidence(self, entity1: MedicalEntity, entity2: MedicalEntity) -> str:
        """Get textual evidence supporting a relationship."""
        evidence_parts = []
        
        # Collect snippets from both entities
        for prov in entity1.provenance + entity2.provenance:
            if prov.snippet and len(prov.snippet.strip()) > 10:
                evidence_parts.append(prov.snippet.strip())
        
        # Return combined evidence, limited to reasonable length
        evidence = " | ".join(evidence_parts[:3])  # Limit to 3 snippets
        return evidence[:500] + "..." if len(evidence) > 500 else evidence

    def _store_in_knowledge_graph(self, entities: List[MedicalEntity], 
                                relationships: List[EntityRelationship],
                                chunks: List[SemanticChunk]) -> None:
        """Store extracted entities and relationships in the knowledge graph."""
        logger.info("Storing entities and relationships in knowledge graph")
        
        try:
            # Store entities as knowledge nodes
            for entity in entities:
                knowledge_node = KnowledgeNode(
                    id=entity.id,
                    node_type=entity.entity_type.lower(),
                    properties={
                        'text': entity.text,
                        'normalized_text': entity.normalized_text,
                        'confidence': entity.confidence,
                        'metadata': entity.metadata,
                        'provenance': [self._provenance_to_dict(p) for p in entity.provenance]
                    }
                )
                self.kg_repository.save_node(knowledge_node)
            
            # Store relationships
            for relationship in relationships:
                kg_relationship = KnowledgeRelationship(
                    id=relationship.id,
                    source_node_id=relationship.source_entity_id,
                    target_node_id=relationship.target_entity_id,
                    relationship_type=relationship.relationship_type,
                    properties={
                        'evidence': relationship.evidence,
                        'provenance': [self._provenance_to_dict(p) for p in relationship.provenance]
                    },
                    confidence=relationship.confidence
                )
                self.kg_repository.save_relationship(kg_relationship)
            
            # Store semantic chunks as sections
            for chunk in chunks:
                section = Section(
                    id=chunk.id,
                    document_id=chunk.metadata.get('doc_id', ''),
                    section_type=chunk.chunk_type,
                    page_number=chunk.page_number or 1,
                    text_content=chunk.text
                )
                self.kg_repository.save_section(section)
            
            logger.info("Successfully stored entities and relationships in knowledge graph")
            
        except Exception as e:
            logger.error(f"Error storing in knowledge graph: {e}")
            raise

    def process_specific_pqme_files(self) -> Dict[str, Any]:
        """
        Process the specific PQME files mentioned in the requirements.
        
        Returns:
            Processing results for the specific files
        """
        pqme_files = [
            "Injured worker-PQME-(09.05.2025)-AA CL-09.09.2025.p5.pdf",
            "Injured worker-PQME-(09.08.2025)-DA CL-09.09.2025.p4.pdf"
        ]
        
        documents = []
        for filename in pqme_files:
            file_path = os.path.join(".", filename)
            if os.path.exists(file_path):
                documents.append({
                    'file_path': file_path,
                    'doc_id': str(uuid.uuid4())
                })
                logger.info(f"Found PQME file: {filename}")
            else:
                logger.warning(f"PQME file not found: {filename}")
        
        if documents:
            return self.process_patient_documents(documents)
        else:
            logger.warning("No PQME files found for processing")
            return {
                'processed_documents': [],
                'total_entities': 0,
                'total_relationships': 0,
                'processing_errors': ['No PQME files found']
            }

    # Utility methods
    
    def _is_valid_patient_name(self, name: str) -> bool:
        """Validate if a string is likely a patient name."""
        if len(name) < 2 or len(name) > 50:
            return False
        
        # Check for common non-name patterns
        excluded_patterns = [
            r'^\d+$',  # Only numbers
            r'^[A-Z]{3,}$',  # All caps (likely acronym)
            r'(page|section|chapter|table|figure)',  # Document elements
        ]
        
        for pattern in excluded_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return False
        
        return True
    
    def _get_context_snippet(self, text: str, start: int, end: int, context_size: int = 100) -> str:
        """Get context snippet around an entity."""
        snippet_start = max(0, start - context_size)
        snippet_end = min(len(text), end + context_size)
        return text[snippet_start:snippet_end].strip()
    
    def _deduplicate_entities(self, entities: List[MedicalEntity]) -> List[MedicalEntity]:
        """Remove duplicate entities based on normalized text and type."""
        seen = set()
        unique_entities = []
        
        for entity in entities:
            key = (entity.entity_type, entity.normalized_text)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
            else:
                # Merge provenance from duplicate
                for existing in unique_entities:
                    if (existing.entity_type == entity.entity_type and 
                        existing.normalized_text == entity.normalized_text):
                        existing.provenance.extend(entity.provenance)
                        # Update confidence to maximum
                        existing.confidence = max(existing.confidence, entity.confidence)
                        break
        
        return unique_entities
    
    def _entity_to_dict(self, entity: MedicalEntity) -> Dict[str, Any]:
        """Convert MedicalEntity to dictionary."""
        return {
            'id': entity.id,
            'entity_type': entity.entity_type,
            'text': entity.text,
            'normalized_text': entity.normalized_text,
            'confidence': entity.confidence,
            'provenance': [self._provenance_to_dict(p) for p in entity.provenance],
            'metadata': entity.metadata,
            'relationships': entity.relationships,
            'created_at': entity.created_at.isoformat()
        }
    
    def _relationship_to_dict(self, relationship: EntityRelationship) -> Dict[str, Any]:
        """Convert EntityRelationship to dictionary."""
        return {
            'id': relationship.id,
            'source_entity_id': relationship.source_entity_id,
            'target_entity_id': relationship.target_entity_id,
            'relationship_type': relationship.relationship_type,
            'confidence': relationship.confidence,
            'evidence': relationship.evidence,
            'provenance': [self._provenance_to_dict(p) for p in relationship.provenance],
            'created_at': relationship.created_at.isoformat()
        }
    
    def _provenance_to_dict(self, provenance: ProvenanceReference) -> Dict[str, Any]:
        """Convert ProvenanceReference to dictionary."""
        return {
            'doc_id': provenance.doc_id,
            'page': provenance.page,
            'offset': provenance.offset,
            'snippet': provenance.snippet,
            'confidence': provenance.confidence,
            'extraction_method': provenance.extraction_method,
            'created_at': provenance.created_at.isoformat()
        }


# Factory function for easy instantiation
def create_enhanced_document_processor(kg_repository: Optional[KnowledgeGraphRepository] = None) -> EnhancedDocumentProcessor:
    """
    Factory function to create an enhanced document processor.
    
    Args:
        kg_repository: Optional knowledge graph repository
        
    Returns:
        Configured EnhancedDocumentProcessor instance
    """
    return EnhancedDocumentProcessor(kg_repository=kg_repository)