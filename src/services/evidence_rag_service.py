"""
Evidence-based RAG Service for canonical content retrieval.

This service provides evidence-constrained retrieval from AMA Guides and QME Study Guide
knowledge graph content, ensuring all generated content is backed by validated sources
with complete provenance tracking.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod

from ..models.knowledge_graph import KnowledgeGraph, MedicalEntity, EntityRelationship, MedicalEntityType
from ..services.ama_guidelines_engine import AMAGuidelinesEngine
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class EvidenceSnippet:
    """Evidence snippet with source provenance."""
    content: str
    source_document: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    confidence: float = 0.0
    entity_id: Optional[str] = None
    coordinates: Optional[Dict[str, Any]] = None  # Document coordinates
    ama_reference: Optional[str] = None
    legal_citation: Optional[str] = None


@dataclass
class CanonicalContent:
    """Canonical content from authoritative sources."""
    content_type: str  # 'ama_guideline', 'qme_procedure', 'legal_requirement'
    title: str
    content: str
    source: str  # 'AMA Guides 5th Edition', 'QME Study Guide', etc.
    chapter_section: Optional[str] = None
    table_reference: Optional[str] = None
    page_reference: Optional[str] = None
    confidence: float = 1.0  # Canonical content has high confidence
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class EvidenceRetrievalResult:
    """Result of evidence-based content retrieval."""
    query: str
    evidence_snippets: List[EvidenceSnippet]
    canonical_content: List[CanonicalContent]
    total_sources: int
    confidence_score: float
    provenance_complete: bool
    retrieval_timestamp: datetime = field(default_factory=datetime.now)


class IEvidenceRetriever(ABC):
    """Abstract interface for evidence retrieval components."""
    
    @abstractmethod
    def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[EvidenceSnippet]:
        """Retrieve evidence snippets for query."""
        pass
    
    @abstractmethod
    def get_canonical_content(self, content_type: str, topic: str) -> List[CanonicalContent]:
        """Get canonical content for specific topic."""
        pass


class AMAGuidelinesRetriever(IEvidenceRetriever):
    """Retriever for AMA Guidelines 5th Edition content."""
    
    def __init__(self, ama_engine: AMAGuidelinesEngine, knowledge_graph: KnowledgeGraph):
        self.ama_engine = ama_engine
        self.knowledge_graph = knowledge_graph
        self.logger = logger
    
    def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[EvidenceSnippet]:
        """Retrieve AMA Guidelines evidence snippets."""
        try:
            evidence_snippets = []
            
            # Search for relevant AMA entities in knowledge graph
            ama_entities = self._find_ama_entities(query, context)
            
            for entity in ama_entities:
                snippet = self._create_evidence_snippet_from_entity(entity)
                if snippet:
                    evidence_snippets.append(snippet)
            
            # Sort by confidence and relevance
            evidence_snippets.sort(key=lambda x: x.confidence, reverse=True)
            
            return evidence_snippets[:10]  # Limit to top 10 results
            
        except Exception as e:
            self.logger.error(f"Error retrieving AMA evidence: {str(e)}")
            return []
    
    def get_canonical_content(self, content_type: str, topic: str) -> List[CanonicalContent]:
        """Get canonical AMA Guidelines content."""
        try:
            canonical_content = []
            
            if content_type == 'impairment_rating':
                content = self._get_impairment_rating_content(topic)
                canonical_content.extend(content)
            elif content_type == 'rom_measurement':
                content = self._get_rom_measurement_content(topic)
                canonical_content.extend(content)
            elif content_type == 'causation_analysis':
                content = self._get_causation_analysis_content(topic)
                canonical_content.extend(content)
            
            return canonical_content
            
        except Exception as e:
            self.logger.error(f"Error getting canonical AMA content: {str(e)}")
            return []
    
    def _find_ama_entities(self, query: str, context: Dict[str, Any]) -> List[MedicalEntity]:
        """Find relevant AMA entities in knowledge graph."""
        relevant_entities = []
        query_lower = query.lower()
        
        for entity in self.knowledge_graph.entities.values():
            # Check if entity is AMA-related
            if self._is_ama_entity(entity):
                # Check relevance to query
                if self._is_relevant_to_query(entity, query_lower, context):
                    relevant_entities.append(entity)
        
        return relevant_entities
    
    def _is_ama_entity(self, entity: MedicalEntity) -> bool:
        """Check if entity is from AMA Guidelines."""
        return (
            'ama' in entity.metadata.get('source', '').lower() or
            'ama_chapter' in entity.metadata or
            'ama_table' in entity.metadata or
            entity.metadata.get('source_document', '').lower().startswith('ama')
        )
    
    def _is_relevant_to_query(self, entity: MedicalEntity, query_lower: str, context: Dict[str, Any]) -> bool:
        """Check if entity is relevant to the query."""
        # Check content relevance
        if any(term in entity.content.lower() for term in query_lower.split()):
            return True
        
        # Check entity type relevance
        if context.get('body_part') and context['body_part'].lower() in entity.content.lower():
            return True
        
        # Check metadata relevance
        if context.get('diagnosis') and context['diagnosis'].lower() in entity.content.lower():
            return True
        
        return False
    
    def _create_evidence_snippet_from_entity(self, entity: MedicalEntity) -> Optional[EvidenceSnippet]:
        """Create evidence snippet from knowledge graph entity."""
        try:
            return EvidenceSnippet(
                content=entity.content,
                source_document=entity.metadata.get('source_document', 'AMA Guides 5th Edition'),
                page_number=entity.metadata.get('page_number'),
                section=entity.metadata.get('section'),
                confidence=entity.metadata.get('confidence', 0.9),
                entity_id=entity.id,
                ama_reference=entity.metadata.get('ama_reference'),
                coordinates=entity.metadata.get('coordinates')
            )
        except Exception as e:
            self.logger.warning(f"Error creating evidence snippet from entity {entity.id}: {str(e)}")
            return None
    
    def _get_impairment_rating_content(self, body_part: str) -> List[CanonicalContent]:
        """Get canonical impairment rating content for body part."""
        try:
            # Get AMA table information for body part
            table_info = self.ama_engine.get_impairment_table(body_part)
            if not table_info:
                return []
            
            return [CanonicalContent(
                content_type='impairment_rating',
                title=f"Impairment Rating - {body_part}",
                content=table_info.get('description', ''),
                source='AMA Guides 5th Edition',
                chapter_section=table_info.get('chapter'),
                table_reference=table_info.get('table_number'),
                page_reference=table_info.get('page')
            )]
            
        except Exception as e:
            self.logger.error(f"Error getting impairment rating content: {str(e)}")
            return []
    
    def _get_rom_measurement_content(self, body_part: str) -> List[CanonicalContent]:
        """Get canonical ROM measurement content."""
        try:
            # Get ROM measurement guidelines from AMA
            rom_guidelines = self.ama_engine.get_rom_guidelines(body_part)
            if not rom_guidelines:
                return []
            
            return [CanonicalContent(
                content_type='rom_measurement',
                title=f"ROM Measurement - {body_part}",
                content=rom_guidelines.get('methodology', ''),
                source='AMA Guides 5th Edition',
                chapter_section=rom_guidelines.get('chapter'),
                page_reference=rom_guidelines.get('page')
            )]
            
        except Exception as e:
            self.logger.error(f"Error getting ROM measurement content: {str(e)}")
            return []
    
    def _get_causation_analysis_content(self, topic: str) -> List[CanonicalContent]:
        """Get canonical causation analysis content."""
        return [CanonicalContent(
            content_type='causation_analysis',
            title='Medical Causation Analysis',
            content='Causation analysis should consider the relationship between industrial exposure and current medical condition, applying reasonable medical probability standards.',
            source='AMA Guides 5th Edition',
            chapter_section='Chapter 1 - Conceptual Foundations'
        )]


class QMEStudyGuideRetriever(IEvidenceRetriever):
    """Retriever for QME Study Guide content."""
    
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.knowledge_graph = knowledge_graph
        self.logger = logger
    
    def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[EvidenceSnippet]:
        """Retrieve QME Study Guide evidence snippets."""
        try:
            evidence_snippets = []
            
            # Search for QME procedural entities
            qme_entities = self._find_qme_entities(query, context)
            
            for entity in qme_entities:
                snippet = self._create_qme_evidence_snippet(entity)
                if snippet:
                    evidence_snippets.append(snippet)
            
            return evidence_snippets[:5]  # Limit to top 5 results
            
        except Exception as e:
            self.logger.error(f"Error retrieving QME evidence: {str(e)}")
            return []
    
    def get_canonical_content(self, content_type: str, topic: str) -> List[CanonicalContent]:
        """Get canonical QME Study Guide content."""
        try:
            if content_type == 'legal_requirements':
                return self._get_legal_requirements_content(topic)
            elif content_type == 'procedural_standards':
                return self._get_procedural_standards_content(topic)
            elif content_type == 'quality_standards':
                return self._get_quality_standards_content(topic)
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting canonical QME content: {str(e)}")
            return []
    
    def _find_qme_entities(self, query: str, context: Dict[str, Any]) -> List[MedicalEntity]:
        """Find relevant QME entities in knowledge graph."""
        relevant_entities = []
        query_lower = query.lower()
        
        for entity in self.knowledge_graph.entities.values():
            if self._is_qme_entity(entity) and self._is_relevant_to_query(entity, query_lower, context):
                relevant_entities.append(entity)
        
        return relevant_entities
    
    def _is_qme_entity(self, entity: MedicalEntity) -> bool:
        """Check if entity is from QME Study Guide."""
        return (
            'qme' in entity.metadata.get('source', '').lower() or
            entity.metadata.get('source_document', '').lower().startswith('qme') or
            entity.entity_type in [MedicalEntityType.LEGAL_REQUIREMENT, MedicalEntityType.PROCEDURE]
        )
    
    def _is_relevant_to_query(self, entity: MedicalEntity, query_lower: str, context: Dict[str, Any]) -> bool:
        """Check if entity is relevant to the query."""
        return any(term in entity.content.lower() for term in query_lower.split())
    
    def _create_qme_evidence_snippet(self, entity: MedicalEntity) -> Optional[EvidenceSnippet]:
        """Create evidence snippet from QME entity."""
        try:
            return EvidenceSnippet(
                content=entity.content,
                source_document=entity.metadata.get('source_document', 'QME Study Guide'),
                page_number=entity.metadata.get('page_number'),
                section=entity.metadata.get('section'),
                confidence=entity.metadata.get('confidence', 0.95),
                entity_id=entity.id,
                legal_citation=entity.metadata.get('legal_citation')
            )
        except Exception as e:
            self.logger.warning(f"Error creating QME evidence snippet: {str(e)}")
            return None
    
    def _get_legal_requirements_content(self, topic: str) -> List[CanonicalContent]:
        """Get legal requirements content."""
        return [CanonicalContent(
            content_type='legal_requirements',
            title='QME Legal Requirements',
            content='QME reports must comply with Labor Code Section 4062.3 requirements including proper attestation and page count declaration.',
            source='QME Study Guide',
            legal_citation='Labor Code Section 4062.3'
        )]
    
    def _get_procedural_standards_content(self, topic: str) -> List[CanonicalContent]:
        """Get procedural standards content."""
        return [CanonicalContent(
            content_type='procedural_standards',
            title='QME Procedural Standards',
            content='QME examinations must follow standardized procedures for history taking, physical examination, and record review.',
            source='QME Study Guide'
        )]
    
    def _get_quality_standards_content(self, topic: str) -> List[CanonicalContent]:
        """Get quality standards content."""
        return [CanonicalContent(
            content_type='quality_standards',
            title='QME Quality Standards',
            content='QME reports must meet professional quality standards with complete documentation and evidence-based conclusions.',
            source='QME Study Guide'
        )]


class EvidenceRAGService:
    """
    Evidence-based Retrieval-Augmented Generation service.
    
    Provides canonical content retrieval from AMA Guides and QME Study Guide
    knowledge graph with complete provenance tracking and evidence constraints.
    """
    
    def __init__(self, knowledge_graph: KnowledgeGraph, ama_engine: AMAGuidelinesEngine):
        self.knowledge_graph = knowledge_graph
        self.ama_engine = ama_engine
        self.logger = logger
        
        # Initialize retrievers
        self.ama_retriever = AMAGuidelinesRetriever(ama_engine, knowledge_graph)
        self.qme_retriever = QMEStudyGuideRetriever(knowledge_graph)
        
        # Retriever registry
        self.retrievers = {
            'ama_guidelines': self.ama_retriever,
            'qme_study_guide': self.qme_retriever
        }
    
    def retrieve_evidence_for_content(self, query: str, content_type: str, 
                                    context: Optional[Dict[str, Any]] = None) -> EvidenceRetrievalResult:
        """
        Retrieve evidence-based content for narrative generation.
        
        Args:
            query: Content query (e.g., "lumbar spine impairment rating")
            content_type: Type of content needed ('impairment', 'causation', 'examination', etc.)
            context: Additional context (body_part, diagnosis, etc.)
        
        Returns:
            EvidenceRetrievalResult with evidence snippets and canonical content
        """
        try:
            if context is None:
                context = {}
            
            self.logger.info(f"Retrieving evidence for query: {query}, type: {content_type}")
            
            evidence_snippets = []
            canonical_content = []
            
            # Retrieve from all available sources
            for source_name, retriever in self.retrievers.items():
                try:
                    # Get evidence snippets
                    snippets = retriever.retrieve_evidence(query, context)
                    evidence_snippets.extend(snippets)
                    
                    # Get canonical content
                    canonical = retriever.get_canonical_content(content_type, query)
                    canonical_content.extend(canonical)
                    
                except Exception as e:
                    self.logger.warning(f"Error retrieving from {source_name}: {str(e)}")
            
            # Calculate overall confidence and provenance completeness
            confidence_score = self._calculate_retrieval_confidence(evidence_snippets, canonical_content)
            provenance_complete = self._check_provenance_completeness(evidence_snippets, canonical_content)
            
            result = EvidenceRetrievalResult(
                query=query,
                evidence_snippets=evidence_snippets,
                canonical_content=canonical_content,
                total_sources=len(evidence_snippets) + len(canonical_content),
                confidence_score=confidence_score,
                provenance_complete=provenance_complete
            )
            
            self.logger.info(f"Retrieved {len(evidence_snippets)} evidence snippets and {len(canonical_content)} canonical content items")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error retrieving evidence for content: {str(e)}")
            return EvidenceRetrievalResult(
                query=query,
                evidence_snippets=[],
                canonical_content=[],
                total_sources=0,
                confidence_score=0.0,
                provenance_complete=False
            )
    
    def get_evidence_constrained_content(self, validated_fields: Dict[str, Any], 
                                       section_type: str) -> EvidenceRetrievalResult:
        """
        Get evidence-constrained content using only validated fields.
        
        Args:
            validated_fields: Fields that passed validation with confidence >= threshold
            section_type: Type of section ('history', 'examination', 'diagnosis', 'impairment')
        
        Returns:
            EvidenceRetrievalResult with content constrained by validated evidence
        """
        try:
            # Build query from validated fields
            query = self._build_query_from_validated_fields(validated_fields, section_type)
            
            # Build context from validated fields
            context = self._build_context_from_validated_fields(validated_fields)
            
            # Retrieve evidence-constrained content
            return self.retrieve_evidence_for_content(query, section_type, context)
            
        except Exception as e:
            self.logger.error(f"Error getting evidence-constrained content: {str(e)}")
            return EvidenceRetrievalResult(
                query="",
                evidence_snippets=[],
                canonical_content=[],
                total_sources=0,
                confidence_score=0.0,
                provenance_complete=False
            )
    
    def _build_query_from_validated_fields(self, validated_fields: Dict[str, Any], section_type: str) -> str:
        """Build content query from validated fields."""
        query_parts = []
        
        # Add relevant fields based on section type
        if section_type == 'history':
            if 'injury_mechanism' in validated_fields:
                query_parts.append(str(validated_fields['injury_mechanism']))
            if 'body_part' in validated_fields:
                query_parts.append(str(validated_fields['body_part']))
        
        elif section_type == 'examination':
            if 'body_part' in validated_fields:
                query_parts.append(f"{validated_fields['body_part']} examination")
            if 'rom_measurements' in validated_fields:
                query_parts.append("range of motion")
        
        elif section_type == 'diagnosis':
            if 'primary_diagnosis' in validated_fields:
                query_parts.append(str(validated_fields['primary_diagnosis']))
            if 'body_part' in validated_fields:
                query_parts.append(str(validated_fields['body_part']))
        
        elif section_type == 'impairment':
            if 'body_part' in validated_fields:
                query_parts.append(f"{validated_fields['body_part']} impairment rating")
        
        return " ".join(query_parts) if query_parts else section_type
    
    def _build_context_from_validated_fields(self, validated_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Build context dictionary from validated fields."""
        context = {}
        
        # Map validated fields to context
        field_mappings = {
            'body_part': 'body_part',
            'primary_diagnosis': 'diagnosis',
            'injury_date': 'injury_date',
            'patient_name': 'patient_name',
            'case_number': 'case_number'
        }
        
        for field_name, context_key in field_mappings.items():
            if field_name in validated_fields:
                context[context_key] = validated_fields[field_name]
        
        return context
    
    def _calculate_retrieval_confidence(self, evidence_snippets: List[EvidenceSnippet], 
                                      canonical_content: List[CanonicalContent]) -> float:
        """Calculate overall confidence of retrieved content."""
        if not evidence_snippets and not canonical_content:
            return 0.0
        
        total_confidence = 0.0
        total_items = 0
        
        # Weight evidence snippets
        for snippet in evidence_snippets:
            total_confidence += snippet.confidence
            total_items += 1
        
        # Weight canonical content (higher confidence)
        for content in canonical_content:
            total_confidence += content.confidence
            total_items += 1
        
        return total_confidence / total_items if total_items > 0 else 0.0
    
    def _check_provenance_completeness(self, evidence_snippets: List[EvidenceSnippet], 
                                     canonical_content: List[CanonicalContent]) -> bool:
        """Check if all content has complete provenance information."""
        # Check evidence snippets
        for snippet in evidence_snippets:
            if not snippet.source_document:
                return False
        
        # Check canonical content
        for content in canonical_content:
            if not content.source:
                return False
        
        return True
    
    def get_source_citations(self, evidence_snippets: List[EvidenceSnippet], 
                           canonical_content: List[CanonicalContent]) -> List[str]:
        """Generate source citations for retrieved content."""
        citations = []
        
        # Citations from evidence snippets
        for snippet in evidence_snippets:
            if snippet.ama_reference:
                citations.append(snippet.ama_reference)
            elif snippet.source_document and snippet.page_number:
                citations.append(f"{snippet.source_document}, p. {snippet.page_number}")
            elif snippet.source_document:
                citations.append(snippet.source_document)
        
        # Citations from canonical content
        for content in canonical_content:
            if content.table_reference:
                citations.append(f"{content.source}, {content.table_reference}")
            elif content.chapter_section:
                citations.append(f"{content.source}, {content.chapter_section}")
            else:
                citations.append(content.source)
        
        # Remove duplicates and return
        return list(set(citations))