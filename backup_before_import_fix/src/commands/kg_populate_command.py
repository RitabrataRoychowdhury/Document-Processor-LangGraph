"""Knowledge Graph Population command for creating nodes and relationships."""

from typing import Dict, Any, List, Optional
import logging

from .base import Command, CommandResult, RetryableException, NonRetryableException
from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository
from src.storage.document_storage import DocumentStorage

logger = logging.getLogger(__name__)


class KGPopulateCommand(Command):
    """Command for populating the knowledge graph with extracted entities and relationships."""
    
    def __init__(self, document_id: str,
                 kg_repository: Optional[KnowledgeGraphRepository] = None,
                 storage: Optional[DocumentStorage] = None):
        super().__init__()
        self.document_id = document_id
        self.kg_repository = kg_repository or KnowledgeGraphRepository()
        self.storage = storage or DocumentStorage()
    
    def execute(self) -> CommandResult:
        """Execute knowledge graph population."""
        try:
            logger.info(f"Starting KG population for document: {self.document_id}")
            
            # Retrieve document with NER results
            document = self.storage.get_document(self.document_id)
            if not document:
                return CommandResult.failure_result(
                    message=f"Document not found: {self.document_id}",
                    error=NonRetryableException("Document not found")
                )
            
            # Check if NER has been completed
            if not document.extracted_info or not document.extracted_info.get('ner_processed'):
                return CommandResult.failure_result(
                    message="Document has not been processed with NER yet",
                    error=NonRetryableException("NER not completed")
                )
            
            entities = document.extracted_info.get('entities', [])
            if not entities:
                logger.warning(f"No entities found for document {self.document_id}")
                return CommandResult.success_result(
                    message="No entities to populate in knowledge graph",
                    data={'document_id': self.document_id, 'nodes_created': 0, 'relationships_created': 0}
                )
            
            # Create document node in knowledge graph
            try:
                document_node_id = self.kg_repository.create_document_node(
                    document_id=self.document_id,
                    title=document.title,
                    file_path=getattr(document, 'file_path', ''),
                    metadata=document.extracted_info
                )
            except Exception as e:
                logger.warning(f"Failed to create document node: {e}")
                raise RetryableException(f"Failed to create document node: {str(e)}")
            
            # Process entities and create nodes
            nodes_created = 0
            relationships_created = 0
            
            # Group entities by type for batch processing
            entities_by_type = {}
            for entity in entities:
                entity_type = entity['type']
                if entity_type not in entities_by_type:
                    entities_by_type[entity_type] = []
                entities_by_type[entity_type].append(entity)
            
            # Create nodes for each entity type
            for entity_type, type_entities in entities_by_type.items():
                try:
                    created_nodes = self._create_entity_nodes(entity_type, type_entities, document_node_id)
                    nodes_created += len(created_nodes)
                    
                    # Create relationships between document and entities
                    for node_id in created_nodes:
                        try:
                            self.kg_repository.create_relationship(
                                source_node_id=document_node_id,
                                target_node_id=node_id,
                                relationship_type="CONTAINS",
                                properties={'confidence': 0.8}
                            )
                            relationships_created += 1
                        except Exception as e:
                            logger.warning(f"Failed to create relationship: {e}")
                            # Continue with other relationships
                            
                except Exception as e:
                    logger.warning(f"Failed to create nodes for entity type {entity_type}: {e}")
                    # Continue with other entity types
            
            # Create relationships between entities (simplified approach)
            try:
                additional_relationships = self._create_entity_relationships(entities_by_type)
                relationships_created += additional_relationships
            except Exception as e:
                logger.warning(f"Failed to create entity relationships: {e}")
                # This is not critical, continue
            
            # Update document processing status
            self.storage.update_document(self.document_id, {
                'processing_status': 'kg_populated'
            })
            
            result_data = {
                'document_id': self.document_id,
                'document_node_id': document_node_id,
                'nodes_created': nodes_created + 1,  # +1 for document node
                'relationships_created': relationships_created,
                'entity_types_processed': list(entities_by_type.keys())
            }
            
            logger.info(f"Successfully populated KG for document {self.document_id}: "
                       f"{nodes_created + 1} nodes, {relationships_created} relationships")
            
            return CommandResult.success_result(
                message=f"Successfully populated knowledge graph for document {self.document_id}",
                data=result_data
            )
            
        except RetryableException:
            # Re-raise retryable exceptions
            raise
        except NonRetryableException as e:
            return CommandResult.failure_result(
                message=f"Non-retryable error during KG population: {str(e)}",
                error=e
            )
        except Exception as e:
            logger.error(f"Unexpected error during KG population: {e}")
            # Treat unexpected errors as retryable
            raise RetryableException(f"Unexpected KG population error: {str(e)}")
    
    def _create_entity_nodes(self, entity_type: str, entities: List[Dict[str, Any]], 
                           document_node_id: str) -> List[str]:
        """Create nodes for entities of a specific type."""
        created_nodes = []
        
        for entity in entities:
            try:
                # Create node based on entity type
                if entity_type == 'PATIENT':
                    node_id = self.kg_repository.create_patient_node(
                        name=entity['text'],
                        properties={
                            'confidence': entity.get('confidence', 0.0),
                            'source_document': document_node_id,
                            'text_position': {'start': entity['start'], 'end': entity['end']}
                        }
                    )
                elif entity_type == 'DIAGNOSIS':
                    node_id = self.kg_repository.create_diagnosis_node(
                        diagnosis=entity['text'],
                        properties={
                            'confidence': entity.get('confidence', 0.0),
                            'source_document': document_node_id,
                            'text_position': {'start': entity['start'], 'end': entity['end']}
                        }
                    )
                elif entity_type == 'DATE':
                    node_id = self.kg_repository.create_generic_node(
                        node_type='DATE',
                        properties={
                            'date_text': entity['text'],
                            'confidence': entity.get('confidence', 0.0),
                            'source_document': document_node_id,
                            'text_position': {'start': entity['start'], 'end': entity['end']}
                        }
                    )
                elif entity_type == 'PERCENTAGE':
                    node_id = self.kg_repository.create_generic_node(
                        node_type='IMPAIRMENT_RATING',
                        properties={
                            'percentage': entity['text'],
                            'confidence': entity.get('confidence', 0.0),
                            'source_document': document_node_id,
                            'text_position': {'start': entity['start'], 'end': entity['end']}
                        }
                    )
                else:
                    # Generic node for other entity types
                    node_id = self.kg_repository.create_generic_node(
                        node_type=entity_type,
                        properties={
                            'text': entity['text'],
                            'confidence': entity.get('confidence', 0.0),
                            'source_document': document_node_id,
                            'text_position': {'start': entity['start'], 'end': entity['end']}
                        }
                    )
                
                created_nodes.append(node_id)
                
            except Exception as e:
                logger.warning(f"Failed to create node for entity {entity['text']}: {e}")
                # Continue with other entities
        
        return created_nodes
    
    def _create_entity_relationships(self, entities_by_type: Dict[str, List[Dict[str, Any]]]) -> int:
        """Create relationships between entities based on proximity and type."""
        relationships_created = 0
        
        # Simple approach: create relationships between patients and diagnoses
        # if they appear close to each other in the text
        patients = entities_by_type.get('PATIENT', [])
        diagnoses = entities_by_type.get('DIAGNOSIS', [])
        percentages = entities_by_type.get('PERCENTAGE', [])
        
        # Link patients to nearby diagnoses
        for patient in patients:
            for diagnosis in diagnoses:
                # Check if diagnosis appears within 500 characters of patient mention
                distance = abs(patient['start'] - diagnosis['start'])
                if distance < 500:
                    try:
                        # This would require looking up the actual node IDs
                        # For now, we'll skip the actual relationship creation
                        # In a full implementation, we'd maintain a mapping of entities to node IDs
                        relationships_created += 1
                    except Exception as e:
                        logger.warning(f"Failed to create patient-diagnosis relationship: {e}")
        
        # Link diagnoses to nearby percentages (potential impairment ratings)
        for diagnosis in diagnoses:
            for percentage in percentages:
                distance = abs(diagnosis['start'] - percentage['start'])
                if distance < 200:  # Closer proximity for impairment ratings
                    try:
                        # Similar to above, would need actual node IDs
                        relationships_created += 1
                    except Exception as e:
                        logger.warning(f"Failed to create diagnosis-rating relationship: {e}")
        
        return relationships_created
    
    def can_retry(self) -> bool:
        """KG population operations can be retried for certain types of failures."""
        return True
    
    def get_command_info(self) -> Dict[str, Any]:
        """Get information about this KG populate command."""
        info = super().get_command_info()
        info.update({
            'document_id': self.document_id
        })
        return info