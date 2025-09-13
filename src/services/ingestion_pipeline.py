"""
Knowledge Graph Ingestion Pipeline for Document Q&A System.

This module orchestrates the complete ingestion process:
text extraction → section segmentation → NER → embedding → KG population
"""

import re
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass

try:
    from src.factories.processor_factory import ProcessorFactory
    from src.strategies.embedding_strategy import EmbeddingStrategy, LocalEmbeddingStrategy
    from src.models.knowledge_graph import (
        Section, Diagnosis, Finding, ImpairmentRating, 
        KnowledgeNode, KnowledgeRelationship
    )
    from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository
    from src.utils.logging_config import get_logger
    from src.utils.error_handling import DocumentQAError, FileProcessingError
except ImportError:
    from factories.processor_factory import ProcessorFactory
    from strategies.embedding_strategy import EmbeddingStrategy, LocalEmbeddingStrategy
    from models.knowledge_graph import (
        Section, Diagnosis, Finding, ImpairmentRating, 
        KnowledgeNode, KnowledgeRelationship
    )
    from repositories.knowledge_graph_repository import KnowledgeGraphRepository
    from utils.logging_config import get_logger
    from utils.error_handling import DocumentQAError, FileProcessingError

logger = get_logger(__name__)


@dataclass
class ProcessingResult:
    """Result of document processing."""
    success: bool
    document_id: str
    sections: List[Section]
    entities: List[Any]
    embeddings_generated: int
    error_message: Optional[str] = None


@dataclass
class ExtractedEntity:
    """Represents an extracted medical entity."""
    entity_type: str  # 'patient', 'diagnosis', 'finding', 'impairment_rating'
    text: str
    confidence: float
    page_reference: Optional[int] = None
    section_id: Optional[str] = None
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class MedicalSectionSegmenter:
    """Segments medical documents into structured sections."""
    
    # Common medical document section patterns
    SECTION_PATTERNS = {
        'history': [
            r'history\s+of\s+present\s+illness',
            r'chief\s+complaint',
            r'history\s+of\s+injury',
            r'medical\s+history',
            r'past\s+medical\s+history',
            r'social\s+history',
            r'family\s+history'
        ],
        'examination': [
            r'physical\s+examination',
            r'clinical\s+examination',
            r'examination\s+findings',
            r'objective\s+findings',
            r'physical\s+findings'
        ],
        'diagnosis': [
            r'diagnosis',
            r'diagnoses',
            r'impression',
            r'clinical\s+impression',
            r'medical\s+diagnosis'
        ],
        'findings': [
            r'findings',
            r'clinical\s+findings',
            r'examination\s+findings',
            r'imaging\s+findings',
            r'laboratory\s+findings'
        ],
        'treatment': [
            r'treatment',
            r'therapy',
            r'management',
            r'plan',
            r'treatment\s+plan'
        ],
        'impairment': [
            r'impairment\s+rating',
            r'disability\s+rating',
            r'functional\s+capacity',
            r'work\s+restrictions',
            r'permanent\s+disability'
        ]
    }
    
    def segment_document(self, text: str, document_id: str) -> List[Section]:
        """
        Segment document text into medical sections.
        
        Args:
            text: Full document text
            document_id: ID of the source document
            
        Returns:
            List of Section objects
        """
        sections = []
        lines = text.split('\n')
        current_section = None
        current_content = []
        page_number = 1
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check for page breaks (simple heuristic)
            if re.search(r'page\s+\d+', line.lower()) or line.startswith('---'):
                page_number += 1
                continue
            
            # Check if line matches a section header
            section_type = self._identify_section_type(line)
            
            if section_type:
                # Save previous section if exists
                if current_section and current_content:
                    section = Section(
                        id=str(uuid.uuid4()),
                        document_id=document_id,
                        section_type=current_section,
                        page_number=page_number,
                        text_content='\n'.join(current_content)
                    )
                    sections.append(section)
                
                # Start new section
                current_section = section_type
                current_content = [line]
            else:
                # Add to current section
                if current_section:
                    current_content.append(line)
                else:
                    # Default to 'general' section if no header found
                    if not current_section:
                        current_section = 'general'
                    current_content.append(line)
        
        # Save final section
        if current_section and current_content:
            section = Section(
                id=str(uuid.uuid4()),
                document_id=document_id,
                section_type=current_section,
                page_number=page_number,
                text_content='\n'.join(current_content)
            )
            sections.append(section)
        
        logger.info(f"Segmented document {document_id} into {len(sections)} sections")
        return sections
    
    def _identify_section_type(self, line: str) -> Optional[str]:
        """Identify section type from line text."""
        line_lower = line.lower()
        
        for section_type, patterns in self.SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, line_lower):
                    return section_type
        
        return None


class MedicalNERExtractor:
    """Named Entity Recognition for medical documents."""
    
    # Medical entity patterns
    ENTITY_PATTERNS = {
        'diagnosis': [
            r'diagnosis\s*:\s*([^.\n]+)',
            r'diagnosed\s+with\s+([^.\n]+)',
            r'condition\s*:\s*([^.\n]+)',
            r'icd[- ]?(?:9|10)\s*:\s*([A-Z]\d+(?:\.\d+)?)',
        ],
        'finding': [
            r'finding\s*:\s*([^.\n]+)',
            r'noted\s+([^.\n]+)',
            r'observed\s+([^.\n]+)',
            r'examination\s+reveals?\s+([^.\n]+)',
        ],
        'impairment_rating': [
            r'(\d+%)\s+(?:whole\s+person\s+)?impairment',
            r'impairment\s+rating\s*:\s*(\d+%)',
            r'disability\s+rating\s*:\s*(\d+%)',
            r'ama\s+(?:guides\s+)?table\s+([^,\n\s]+)',
            r'has\s+(\d+%)\s+(?:whole\s+person\s+)?impairment',
            r'based\s+on\s+ama.*?(\d+%)',
            r'(\d+%)\s+whole\s+person',
            r'patient\s+has\s+(\d+%)',
            r'table\s+([^,\n\s]+).*?(\d+%)',
            r'patient\s+has\s+(\d+%)\s+whole\s+person\s+impairment',
        ],
        'patient': [
            r'patient\s*:\s*([A-Za-z\s]+)',
            r'name\s*:\s*([A-Za-z\s]+)',
            r'mr\.\s+([A-Za-z\s]+)',
            r'ms\.\s+([A-Za-z\s]+)',
        ]
    }
    
    def extract_entities(self, sections: List[Section]) -> List[ExtractedEntity]:
        """
        Extract medical entities from document sections.
        
        Args:
            sections: List of document sections
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        for section in sections:
            section_entities = self._extract_from_section(section)
            entities.extend(section_entities)
        
        logger.info(f"Extracted {len(entities)} entities from {len(sections)} sections")
        return entities
    
    def _extract_from_section(self, section: Section) -> List[ExtractedEntity]:
        """Extract entities from a single section."""
        entities = []
        text = section.text_content
        
        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    entity_text = match.group(1).strip() if match.groups() else match.group(0).strip()
                    
                    if len(entity_text) > 3:  # Filter out very short matches
                        entity = ExtractedEntity(
                            entity_type=entity_type,
                            text=entity_text,
                            confidence=0.8,  # Simple confidence score
                            page_reference=section.page_number,
                            section_id=section.id,
                            properties={
                                'section_type': section.section_type,
                                'pattern_matched': pattern
                            }
                        )
                        entities.append(entity)
        
        return entities


class KnowledgeGraphService:
    """Service for populating knowledge graph with extracted entities."""
    
    def __init__(self, kg_repository: KnowledgeGraphRepository):
        self.kg_repository = kg_repository
    
    def populate_graph(self, 
                      document_id: str,
                      sections: List[Section], 
                      entities: List[ExtractedEntity],
                      embeddings_map: Dict[str, List[float]]) -> None:
        """
        Populate knowledge graph with sections, entities, and relationships.
        
        Args:
            document_id: Source document ID
            sections: Document sections
            entities: Extracted entities
            embeddings_map: Map of text to embeddings
        """
        # Save sections
        for section in sections:
            self.kg_repository.save_section(section)
            
            # Create knowledge node for section
            section_node = KnowledgeNode(
                id=f"section_{section.id}",
                node_type="section",
                properties={
                    "section_type": section.section_type,
                    "page_number": section.page_number,
                    "text_content": section.text_content[:500]  # Truncate for storage
                },
                embeddings=embeddings_map.get(section.text_content)
            )
            self.kg_repository.save_node(section_node)
            
            # Create relationship: Document -> Section
            doc_section_rel = KnowledgeRelationship(
                id=str(uuid.uuid4()),
                source_node_id=document_id,
                target_node_id=section.id,
                relationship_type="HAS_SECTION",
                confidence=1.0
            )
            self.kg_repository.save_relationship(doc_section_rel)
        
        # Process entities by type
        diagnoses = [e for e in entities if e.entity_type == 'diagnosis']
        findings = [e for e in entities if e.entity_type == 'finding']
        impairment_ratings = [e for e in entities if e.entity_type == 'impairment_rating']
        
        # Save diagnoses
        for entity in diagnoses:
            diagnosis = Diagnosis(
                id=str(uuid.uuid4()),
                icd_code=self._extract_icd_code(entity.text),
                description=entity.text,
                certainty=entity.confidence,
                source_section_id=entity.section_id,
                page_reference=entity.page_reference
            )
            self.kg_repository.save_diagnosis(diagnosis)
            
            # Create knowledge node
            diag_node = KnowledgeNode(
                id=f"diagnosis_{diagnosis.id}",
                node_type="diagnosis",
                properties={
                    "icd_code": diagnosis.icd_code,
                    "description": diagnosis.description,
                    "certainty": diagnosis.certainty
                },
                embeddings=embeddings_map.get(entity.text)
            )
            self.kg_repository.save_node(diag_node)
            
            # Create relationship: Section -> Diagnosis
            if entity.section_id:
                section_diag_rel = KnowledgeRelationship(
                    id=str(uuid.uuid4()),
                    source_node_id=entity.section_id,
                    target_node_id=diagnosis.id,
                    relationship_type="CONTAINS_DIAGNOSIS",
                    confidence=entity.confidence
                )
                self.kg_repository.save_relationship(section_diag_rel)
        
        # Save findings
        for entity in findings:
            finding = Finding(
                id=str(uuid.uuid4()),
                section_id=entity.section_id or "",
                finding_type="clinical",
                description=entity.text,
                page_reference=entity.page_reference or 1
            )
            self.kg_repository.save_finding(finding)
            
            # Create knowledge node
            finding_node = KnowledgeNode(
                id=f"finding_{finding.id}",
                node_type="finding",
                properties={
                    "finding_type": finding.finding_type,
                    "description": finding.description
                },
                embeddings=embeddings_map.get(entity.text)
            )
            self.kg_repository.save_node(finding_node)
            
            # Create relationship: Section -> Finding
            if entity.section_id:
                section_finding_rel = KnowledgeRelationship(
                    id=str(uuid.uuid4()),
                    source_node_id=entity.section_id,
                    target_node_id=finding.id,
                    relationship_type="CONTAINS_FINDING",
                    confidence=entity.confidence
                )
                self.kg_repository.save_relationship(section_finding_rel)
        
        # Save impairment ratings
        for entity in impairment_ratings:
            # Try to link to a diagnosis
            related_diagnosis_id = self._find_related_diagnosis(entity, diagnoses)
            
            rating = ImpairmentRating(
                id=str(uuid.uuid4()),
                diagnosis_id=related_diagnosis_id or "",
                ama_table=self._extract_ama_table(entity.text),
                percentage=self._extract_percentage(entity.text),
                rationale=entity.text,
                source_page=entity.page_reference
            )
            self.kg_repository.save_impairment_rating(rating)
            
            # Create knowledge node
            rating_node = KnowledgeNode(
                id=f"impairment_{rating.id}",
                node_type="impairment_rating",
                properties={
                    "ama_table": rating.ama_table,
                    "percentage": rating.percentage,
                    "rationale": rating.rationale
                },
                embeddings=embeddings_map.get(entity.text)
            )
            self.kg_repository.save_node(rating_node)
            
            # Create relationship: Diagnosis -> ImpairmentRating
            if related_diagnosis_id:
                diag_rating_rel = KnowledgeRelationship(
                    id=str(uuid.uuid4()),
                    source_node_id=related_diagnosis_id,
                    target_node_id=rating.id,
                    relationship_type="HAS_RATING",
                    confidence=entity.confidence
                )
                self.kg_repository.save_relationship(diag_rating_rel)
        
        logger.info(f"Populated knowledge graph with {len(sections)} sections and {len(entities)} entities")
    
    def _extract_icd_code(self, text: str) -> str:
        """Extract ICD code from diagnosis text."""
        # Look for ICD-10 pattern with decimal and optional letter suffix
        icd_match = re.search(r'([A-Z]\d+\.\d+[A-Z]?)', text)
        if icd_match:
            return icd_match.group(1)
        # Look for ICD-10 pattern without decimal but with letter suffix
        icd_match = re.search(r'([A-Z]\d{2,3}[A-Z])', text)
        if icd_match:
            return icd_match.group(1)
        # Look for basic ICD-10 pattern
        icd_match = re.search(r'([A-Z]\d{2,3})', text)
        if icd_match:
            return icd_match.group(1)
        return "UNKNOWN"
    
    def _extract_ama_table(self, text: str) -> str:
        """Extract AMA table reference from text."""
        # Look for table number pattern (digits-digits or just digits)
        table_match = re.search(r'table\s+(\d+(?:-\d+)?)', text, re.IGNORECASE)
        if table_match:
            return table_match.group(1).strip()
        # Look for table followed by alphanumeric identifier (but not common words)
        ama_match = re.search(r'table\s+([A-Z]?\d+[A-Z]?(?:-[A-Z]?\d+[A-Z]?)?)', text, re.IGNORECASE)
        return ama_match.group(1).strip() if ama_match else "UNKNOWN"
    
    def _extract_percentage(self, text: str) -> float:
        """Extract percentage from impairment rating text."""
        pct_match = re.search(r'(\d+(?:\.\d+)?)%', text)
        return float(pct_match.group(1)) if pct_match else 0.0
    
    def _find_related_diagnosis(self, rating_entity: ExtractedEntity, diagnoses: List[ExtractedEntity]) -> Optional[str]:
        """Find related diagnosis for an impairment rating."""
        # Simple heuristic: find diagnosis in same section
        for diag in diagnoses:
            if diag.section_id == rating_entity.section_id:
                return diag.section_id  # Use section_id as proxy for diagnosis_id
        return None


class IngestionPipeline:
    """Main ingestion pipeline orchestrating the complete process."""
    
    def __init__(self,
                 processor_factory: ProcessorFactory,
                 embedding_strategy: EmbeddingStrategy,
                 kg_service: KnowledgeGraphService):
        self.processor_factory = processor_factory
        self.embedding_strategy = embedding_strategy
        self.kg_service = kg_service
        self.segmenter = MedicalSectionSegmenter()
        self.ner_extractor = MedicalNERExtractor()
    
    async def process_document(self, file_path: str, document_id: str) -> ProcessingResult:
        """
        Execute complete ingestion pipeline for a document.
        
        Args:
            file_path: Path to document file
            document_id: Unique document identifier
            
        Returns:
            ProcessingResult with processing details
        """
        try:
            logger.info(f"Starting ingestion pipeline for document: {file_path}")
            
            # Step 1: Text extraction
            text = await self._extract_text(file_path)
            
            # Step 2: Section segmentation
            sections = self.segmenter.segment_document(text, document_id)
            
            # Step 3: Named Entity Recognition
            entities = self.ner_extractor.extract_entities(sections)
            
            # Step 4: Embedding generation
            embeddings_map = await self._generate_embeddings(sections, entities)
            
            # Step 5: Knowledge graph population
            self.kg_service.populate_graph(document_id, sections, entities, embeddings_map)
            
            result = ProcessingResult(
                success=True,
                document_id=document_id,
                sections=sections,
                entities=entities,
                embeddings_generated=len(embeddings_map)
            )
            
            logger.info(f"Successfully processed document {document_id}: "
                       f"{len(sections)} sections, {len(entities)} entities, "
                       f"{len(embeddings_map)} embeddings")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            return ProcessingResult(
                success=False,
                document_id=document_id,
                sections=[],
                entities=[],
                embeddings_generated=0,
                error_message=str(e)
            )
    
    async def _extract_text(self, file_path: str) -> str:
        """Extract text from document using appropriate processor."""
        file_extension = file_path.lower().split('.')[-1]
        processor = self.processor_factory.create_processor(f".{file_extension}")
        return processor.extract_text(file_path)
    
    async def _generate_embeddings(self, 
                                 sections: List[Section], 
                                 entities: List[ExtractedEntity]) -> Dict[str, List[float]]:
        """Generate embeddings for sections and entities."""
        embeddings_map = {}
        
        # Generate embeddings for sections
        for section in sections:
            if section.text_content and len(section.text_content.strip()) > 10:
                try:
                    embeddings = self.embedding_strategy.generate_embeddings(section.text_content)
                    embeddings_map[section.text_content] = embeddings
                except Exception as e:
                    logger.warning(f"Failed to generate embeddings for section {section.id}: {e}")
        
        # Generate embeddings for entities
        for entity in entities:
            if entity.text and len(entity.text.strip()) > 3:
                try:
                    embeddings = self.embedding_strategy.generate_embeddings(entity.text)
                    embeddings_map[entity.text] = embeddings
                except Exception as e:
                    logger.warning(f"Failed to generate embeddings for entity '{entity.text}': {e}")
        
        return embeddings_map
    
    def process_multiple_documents(self, file_paths: List[str]) -> List[ProcessingResult]:
        """Process multiple documents sequentially."""
        results = []
        
        for file_path in file_paths:
            document_id = str(uuid.uuid4())
            # Note: Using synchronous call since async processing would require more complex setup
            # In a real implementation, you might want to use asyncio.run() or similar
            try:
                import asyncio
                result = asyncio.run(self.process_document(file_path, document_id))
            except:
                # Fallback to synchronous processing
                result = self._process_document_sync(file_path, document_id)
            
            results.append(result)
        
        return results
    
    def _process_document_sync(self, file_path: str, document_id: str) -> ProcessingResult:
        """Synchronous version of document processing."""
        try:
            logger.info(f"Starting synchronous ingestion pipeline for document: {file_path}")
            
            # Step 1: Text extraction
            file_extension = file_path.lower().split('.')[-1]
            processor = self.processor_factory.create_processor(f".{file_extension}")
            text = processor.extract_text(file_path)
            
            # Step 2: Section segmentation
            sections = self.segmenter.segment_document(text, document_id)
            
            # Step 3: Named Entity Recognition
            entities = self.ner_extractor.extract_entities(sections)
            
            # Step 4: Embedding generation
            embeddings_map = {}
            for section in sections:
                if section.text_content and len(section.text_content.strip()) > 10:
                    try:
                        embeddings = self.embedding_strategy.generate_embeddings(section.text_content)
                        embeddings_map[section.text_content] = embeddings
                    except Exception as e:
                        logger.warning(f"Failed to generate embeddings for section {section.id}: {e}")
            
            for entity in entities:
                if entity.text and len(entity.text.strip()) > 3:
                    try:
                        embeddings = self.embedding_strategy.generate_embeddings(entity.text)
                        embeddings_map[entity.text] = embeddings
                    except Exception as e:
                        logger.warning(f"Failed to generate embeddings for entity '{entity.text}': {e}")
            
            # Step 5: Knowledge graph population
            self.kg_service.populate_graph(document_id, sections, entities, embeddings_map)
            
            result = ProcessingResult(
                success=True,
                document_id=document_id,
                sections=sections,
                entities=entities,
                embeddings_generated=len(embeddings_map)
            )
            
            logger.info(f"Successfully processed document {document_id}: "
                       f"{len(sections)} sections, {len(entities)} entities, "
                       f"{len(embeddings_map)} embeddings")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            return ProcessingResult(
                success=False,
                document_id=document_id,
                sections=[],
                entities=[],
                embeddings_generated=0,
                error_message=str(e)
            )