"""Knowledge graph population workflow node."""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from src.workflow.base.workflow_node import WorkflowNode, NodeResult
from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class KGPopulationNode(WorkflowNode):
    """Node for knowledge graph population.
    
    Implements Single Responsibility Principle - handles only KG population.
    Follows Dependency Inversion - depends on KnowledgeGraphRepository abstraction.
    """
    
    def __init__(self, kg_repository: KnowledgeGraphRepository = None,
                 node_id: str = None, correlation_id: str = None):
        super().__init__(node_id, correlation_id)
        # Use dependency injection - don't create default if not provided
        if kg_repository is None:
            raise ValueError("KnowledgeGraphRepository must be provided via dependency injection")
        self.kg_repository = kg_repository
    
    def execute(self, state: Dict[str, Any]) -> NodeResult:
        """Execute knowledge graph population."""
        try:
            document_id = state.get('document_id')
            extracted_text = state['extracted_text']
            entities = state.get('entities_extracted', [])
            chunk_embeddings = state.get('chunk_embeddings', [])
            
            logger.info(f"Starting KG population for document {document_id} with {len(entities)} entities "
                       f"[correlation_id: {self.correlation_id}]")
            
            # Create document node
            document_node = self._create_document_node(state)
            document_node_id = self.kg_repository.create_node(document_node)
            
            # Create section nodes from text chunks
            section_nodes = self._create_section_nodes(document_node_id, chunk_embeddings, extracted_text)
            section_node_ids = []
            for section_node in section_nodes:
                section_id = self.kg_repository.create_node(section_node)
                section_node_ids.append(section_id)
                
                # Create relationship between document and section
                self.kg_repository.create_relationship(
                    document_node_id, section_id, 'HAS_SECTION',
                    {'created_at': datetime.now().isoformat()}
                )
            
            # Process entities and create nodes
            entity_nodes_created = 0
            relationships_created = 0
            
            for entity in entities:
                try:
                    # Create entity node
                    entity_node = self._create_entity_node(entity, document_node_id)
                    entity_node_id = self.kg_repository.create_node(entity_node)
                    entity_nodes_created += 1
                    
                    # Create relationship between document and entity
                    self.kg_repository.create_relationship(
                        document_node_id, entity_node_id, 'CONTAINS_ENTITY',
                        {
                            'confidence': entity.get('confidence', 0.0),
                            'extraction_method': entity.get('metadata', {}).get('pattern_used', 'unknown'),
                            'created_at': datetime.now().isoformat()
                        }
                    )
                    relationships_created += 1
                    
                    # Create relationships between entity and relevant sections
                    relevant_sections = self._find_relevant_sections(entity, section_node_ids, chunk_embeddings)
                    for section_id in relevant_sections:
                        self.kg_repository.create_relationship(
                            section_id, entity_node_id, 'MENTIONS_ENTITY',
                            {
                                'confidence': entity.get('confidence', 0.0),
                                'created_at': datetime.now().isoformat()
                            }
                        )
                        relationships_created += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to create entity node for '{entity.get('text', '')}': {e}")
                    continue
            
            # Create inter-entity relationships
            inter_entity_relationships = self._create_inter_entity_relationships(entities)
            for rel in inter_entity_relationships:
                try:
                    self.kg_repository.create_relationship(
                        rel['source_id'], rel['target_id'], rel['relationship_type'],
                        rel['properties']
                    )
                    relationships_created += 1
                except Exception as e:
                    logger.warning(f"Failed to create relationship: {e}")
                    continue
            
            # Calculate KG statistics
            kg_stats = {
                'document_nodes': 1,
                'section_nodes': len(section_node_ids),
                'entity_nodes': entity_nodes_created,
                'total_nodes': 1 + len(section_node_ids) + entity_nodes_created,
                'total_relationships': relationships_created,
                'entities_processed': len(entities),
                'entities_successful': entity_nodes_created,
                'success_rate': entity_nodes_created / len(entities) if entities else 1.0
            }
            
            result_data = {
                'document_node_id': document_node_id,
                'section_node_ids': section_node_ids,
                'entity_nodes_created': entity_nodes_created,
                'relationships_created': relationships_created,
                'kg_statistics': kg_stats,
                'kg_population_completed': True
            }
            
            logger.info(f"KG population completed: {entity_nodes_created} entity nodes, "
                       f"{relationships_created} relationships created "
                       f"[correlation_id: {self.correlation_id}]")
            
            return NodeResult.success_result(
                f"KG population completed: {entity_nodes_created} nodes, {relationships_created} relationships",
                data=result_data
            )
            
        except Exception as e:
            logger.error(f"KG population failed: {e} [correlation_id: {self.correlation_id}]")
            return NodeResult.failure_result(
                f"KG population failed: {str(e)}",
                error=e
            )
    
    def _create_document_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create a document node from state data."""
        return {
            'node_type': 'Document',
            'properties': {
                'document_id': state.get('document_id'),
                'file_path': state.get('file_path'),
                'file_type': state.get('file_type', 'unknown'),
                'file_size': state.get('file_size', 0),
                'text_length': state.get('text_length', len(state.get('extracted_text', ''))),
                'processing_status': 'completed',
                'created_at': datetime.now().isoformat(),
                'metadata': state.get('document_metadata', {})
            }
        }
    
    def _create_section_nodes(self, document_node_id: str, chunk_embeddings: List[Dict[str, Any]], 
                            full_text: str) -> List[Dict[str, Any]]:
        """Create section nodes from text chunks."""
        section_nodes = []
        
        for i, chunk_data in enumerate(chunk_embeddings):
            chunk_text = chunk_data.get('text', '')
            if len(chunk_text.strip()) < 20:  # Skip very short chunks
                continue
            
            # Determine section type based on content
            section_type = self._classify_section_type(chunk_text)
            
            section_node = {
                'node_type': 'Section',
                'properties': {
                    'section_id': f"{document_node_id}_section_{i}",
                    'document_id': document_node_id,
                    'section_type': section_type,
                    'text_content': chunk_text,
                    'text_length': len(chunk_text),
                    'chunk_index': i,
                    'start_position': chunk_data.get('start_pos', -1),
                    'embedding': chunk_data.get('embedding', []),
                    'created_at': datetime.now().isoformat()
                }
            }
            section_nodes.append(section_node)
        
        return section_nodes
    
    def _classify_section_type(self, text: str) -> str:
        """Classify section type based on content."""
        text_lower = text.lower()
        
        # Medical document section patterns
        if any(keyword in text_lower for keyword in ['history', 'chief complaint', 'present illness']):
            return 'history'
        elif any(keyword in text_lower for keyword in ['examination', 'physical exam', 'findings']):
            return 'examination'
        elif any(keyword in text_lower for keyword in ['diagnosis', 'impression', 'assessment']):
            return 'diagnosis'
        elif any(keyword in text_lower for keyword in ['treatment', 'plan', 'recommendation']):
            return 'treatment'
        elif any(keyword in text_lower for keyword in ['impairment', 'disability', 'rating']):
            return 'impairment'
        elif any(keyword in text_lower for keyword in ['conclusion', 'summary']):
            return 'conclusion'
        else:
            return 'general'
    
    def _create_entity_node(self, entity: Dict[str, Any], document_node_id: str) -> Dict[str, Any]:
        """Create an entity node from extracted entity data."""
        entity_type = entity.get('type', 'unknown')
        entity_text = entity.get('text', '')
        
        # Create specialized node based on entity type
        if entity_type == 'patient':
            return self._create_patient_node(entity, document_node_id)
        elif entity_type == 'diagnosis':
            return self._create_diagnosis_node(entity, document_node_id)
        elif entity_type == 'body_part':
            return self._create_body_part_node(entity, document_node_id)
        elif entity_type == 'impairment_rating':
            return self._create_impairment_rating_node(entity, document_node_id)
        elif entity_type == 'finding':
            return self._create_finding_node(entity, document_node_id)
        else:
            return self._create_generic_entity_node(entity, document_node_id)
    
    def _create_patient_node(self, entity: Dict[str, Any], document_node_id: str) -> Dict[str, Any]:
        """Create a patient node."""
        return {
            'node_type': 'Patient',
            'properties': {
                'name': entity.get('text', ''),
                'document_id': document_node_id,
                'confidence': entity.get('confidence', 0.0),
                'context': entity.get('context', ''),
                'extraction_metadata': entity.get('metadata', {}),
                'created_at': datetime.now().isoformat()
            }
        }
    
    def _create_diagnosis_node(self, entity: Dict[str, Any], document_node_id: str) -> Dict[str, Any]:
        """Create a diagnosis node."""
        metadata = entity.get('metadata', {})
        is_icd_code = metadata.get('is_icd_code', False)
        
        return {
            'node_type': 'Diagnosis',
            'properties': {
                'description': entity.get('text', ''),
                'icd_code': entity.get('text', '') if is_icd_code else None,
                'is_icd_code': is_icd_code,
                'document_id': document_node_id,
                'confidence': entity.get('confidence', 0.0),
                'context': entity.get('context', ''),
                'extraction_metadata': metadata,
                'created_at': datetime.now().isoformat()
            }
        }
    
    def _create_body_part_node(self, entity: Dict[str, Any], document_node_id: str) -> Dict[str, Any]:
        """Create a body part node."""
        return {
            'node_type': 'BodyPart',
            'properties': {
                'name': entity.get('text', ''),
                'document_id': document_node_id,
                'confidence': entity.get('confidence', 0.0),
                'context': entity.get('context', ''),
                'extraction_metadata': entity.get('metadata', {}),
                'created_at': datetime.now().isoformat()
            }
        }
    
    def _create_impairment_rating_node(self, entity: Dict[str, Any], document_node_id: str) -> Dict[str, Any]:
        """Create an impairment rating node."""
        metadata = entity.get('metadata', {})
        percentage = metadata.get('percentage')
        
        return {
            'node_type': 'ImpairmentRating',
            'properties': {
                'description': entity.get('text', ''),
                'percentage': percentage,
                'document_id': document_node_id,
                'confidence': entity.get('confidence', 0.0),
                'context': entity.get('context', ''),
                'extraction_metadata': metadata,
                'created_at': datetime.now().isoformat()
            }
        }
    
    def _create_finding_node(self, entity: Dict[str, Any], document_node_id: str) -> Dict[str, Any]:
        """Create a finding node."""
        return {
            'node_type': 'Finding',
            'properties': {
                'description': entity.get('text', ''),
                'document_id': document_node_id,
                'confidence': entity.get('confidence', 0.0),
                'context': entity.get('context', ''),
                'extraction_metadata': entity.get('metadata', {}),
                'created_at': datetime.now().isoformat()
            }
        }
    
    def _create_generic_entity_node(self, entity: Dict[str, Any], document_node_id: str) -> Dict[str, Any]:
        """Create a generic entity node."""
        return {
            'node_type': 'Entity',
            'properties': {
                'entity_type': entity.get('type', 'unknown'),
                'text': entity.get('text', ''),
                'document_id': document_node_id,
                'confidence': entity.get('confidence', 0.0),
                'context': entity.get('context', ''),
                'extraction_metadata': entity.get('metadata', {}),
                'created_at': datetime.now().isoformat()
            }
        }
    
    def _find_relevant_sections(self, entity: Dict[str, Any], section_node_ids: List[str],
                              chunk_embeddings: List[Dict[str, Any]]) -> List[str]:
        """Find sections that are relevant to an entity."""
        relevant_sections = []
        entity_start = entity.get('start_pos', -1)
        entity_end = entity.get('end_pos', -1)
        
        # If we have position information, find overlapping sections
        if entity_start >= 0 and entity_end >= 0:
            for i, chunk_data in enumerate(chunk_embeddings):
                chunk_start = chunk_data.get('start_pos', -1)
                chunk_text = chunk_data.get('text', '')
                
                # Check if entity position overlaps with chunk
                if chunk_start >= 0:
                    chunk_end = chunk_start + len(chunk_text)
                    if (entity_start >= chunk_start and entity_start <= chunk_end) or \
                       (entity_end >= chunk_start and entity_end <= chunk_end):
                        if i < len(section_node_ids):
                            relevant_sections.append(section_node_ids[i])
                
                # Also check if entity text appears in chunk text
                elif entity.get('text', '').lower() in chunk_text.lower():
                    if i < len(section_node_ids):
                        relevant_sections.append(section_node_ids[i])
        
        # If no position-based matches, use text-based matching
        if not relevant_sections:
            entity_text = entity.get('text', '').lower()
            for i, chunk_data in enumerate(chunk_embeddings):
                chunk_text = chunk_data.get('text', '').lower()
                if entity_text in chunk_text and i < len(section_node_ids):
                    relevant_sections.append(section_node_ids[i])
        
        return relevant_sections
    
    def _create_inter_entity_relationships(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create relationships between entities based on medical knowledge."""
        relationships = []
        
        # Group entities by type
        entities_by_type = {}
        for entity in entities:
            entity_type = entity.get('type', 'unknown')
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)
        
        # Create diagnosis -> body_part relationships
        diagnoses = entities_by_type.get('diagnosis', [])
        body_parts = entities_by_type.get('body_part', [])
        
        for diagnosis in diagnoses:
            for body_part in body_parts:
                # Check if they appear in similar context
                if self._entities_related_by_context(diagnosis, body_part):
                    relationships.append({
                        'source_id': f"diagnosis_{hash(diagnosis.get('text', ''))}",
                        'target_id': f"body_part_{hash(body_part.get('text', ''))}",
                        'relationship_type': 'AFFECTS',
                        'properties': {
                            'confidence': min(diagnosis.get('confidence', 0.0), body_part.get('confidence', 0.0)),
                            'created_at': datetime.now().isoformat()
                        }
                    })
        
        # Create diagnosis -> impairment_rating relationships
        impairment_ratings = entities_by_type.get('impairment_rating', [])
        
        for diagnosis in diagnoses:
            for rating in impairment_ratings:
                if self._entities_related_by_context(diagnosis, rating):
                    relationships.append({
                        'source_id': f"diagnosis_{hash(diagnosis.get('text', ''))}",
                        'target_id': f"impairment_rating_{hash(rating.get('text', ''))}",
                        'relationship_type': 'HAS_RATING',
                        'properties': {
                            'confidence': min(diagnosis.get('confidence', 0.0), rating.get('confidence', 0.0)),
                            'created_at': datetime.now().isoformat()
                        }
                    })
        
        return relationships
    
    def _entities_related_by_context(self, entity1: Dict[str, Any], entity2: Dict[str, Any]) -> bool:
        """Check if two entities are related based on their context."""
        context1 = entity1.get('context', '').lower()
        context2 = entity2.get('context', '').lower()
        
        # Simple heuristic: if contexts overlap significantly, they're related
        if not context1 or not context2:
            return False
        
        # Check for overlapping words (excluding common words)
        words1 = set(context1.split()) - {'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'with'}
        words2 = set(context2.split()) - {'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'with'}
        
        overlap = len(words1.intersection(words2))
        total_unique = len(words1.union(words2))
        
        # If more than 30% overlap, consider them related
        return (overlap / total_unique) > 0.3 if total_unique > 0 else False
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """Validate input state for KG population."""
        required_keys = self.get_required_inputs()
        
        for key in required_keys:
            if key not in state:
                logger.error(f"Missing required input key: {key}")
                return False
        
        extracted_text = state.get('extracted_text')
        if not isinstance(extracted_text, str) or len(extracted_text.strip()) < 10:
            logger.error("Invalid extracted_text: must be a string with at least 10 characters")
            return False
        
        entities = state.get('entities_extracted', [])
        if not isinstance(entities, list):
            logger.error("Invalid entities_extracted: must be a list")
            return False
        
        return True
    
    def get_required_inputs(self) -> List[str]:
        """Get required input keys."""
        return ['extracted_text', 'entities_extracted']
    
    def get_output_keys(self) -> List[str]:
        """Get output keys this node adds to state."""
        return [
            'document_node_id',
            'section_node_ids',
            'entity_nodes_created',
            'relationships_created',
            'kg_statistics',
            'kg_population_completed'
        ]
    
    def can_retry(self, error: Exception) -> bool:
        """Determine if KG population can be retried."""
        # KG population is generally retryable for database connection issues
        non_retryable_errors = (ValueError, TypeError)
        return not isinstance(error, non_retryable_errors)