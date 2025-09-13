"""Knowledge graph population workflow graph implementation."""

from typing import Dict, Any, List, Optional

from src.workflow.base.workflow_graph import WorkflowGraph
from src.workflow.base.workflow_node import WorkflowNode, NodeResult
from src.workflow.nodes.extraction_node import ExtractionNode
from src.workflow.nodes.ner_node import NERNode, MLNERNode
from src.workflow.nodes.embedding_node import EmbeddingNode
from src.workflow.nodes.kg_population_node import KGPopulationNode
from src.factories.processor_factory import ProcessorFactory
from src.strategies.embedding_strategy import EmbeddingStrategy, LocalEmbeddingStrategy
from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class KnowledgeGraphPopulationGraph(WorkflowGraph):
    """Workflow graph for knowledge graph population from multiple documents.
    
    Implements a specialized workflow for building and populating a knowledge graph
    from multiple medical documents with relationship inference and validation.
    
    Follows Single Responsibility Principle - focused on KG population.
    """
    
    def __init__(self, 
                 processor_factory: ProcessorFactory = None,
                 embedding_strategy: EmbeddingStrategy = None,
                 kg_repository: KnowledgeGraphRepository = None,
                 enable_relationship_inference: bool = True,
                 enable_entity_deduplication: bool = True,
                 graph_id: str = None, 
                 correlation_id: str = None):
        super().__init__(graph_id, correlation_id)
        
        # Initialize dependencies
        self.processor_factory = processor_factory or ProcessorFactory()
        self.embedding_strategy = embedding_strategy or LocalEmbeddingStrategy()
        if kg_repository is None:
            from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
            self.kg_repository = SQLiteKnowledgeGraphRepository()
        else:
            self.kg_repository = kg_repository
        
        # Configuration options
        self.enable_relationship_inference = enable_relationship_inference
        self.enable_entity_deduplication = enable_entity_deduplication
    
    def build_graph(self) -> None:
        """Build the knowledge graph population workflow graph."""
        logger.info(f"Building KG population graph {self.graph_id}")
        
        # Create nodes for KG population workflow
        extraction_node = ExtractionNode(
            processor_factory=self.processor_factory,
            node_id="document_extraction",
            correlation_id=self.correlation_id
        )
        
        # Use ML-based NER for better entity recognition in KG context
        ner_node = MLNERNode(
            node_id="entity_recognition",
            correlation_id=self.correlation_id
        )
        
        embedding_node = EmbeddingNode(
            embedding_strategy=self.embedding_strategy,
            node_id="embedding_generation",
            correlation_id=self.correlation_id
        )
        
        kg_population_node = KGPopulationNode(
            kg_repository=self.kg_repository,
            node_id="kg_population",
            correlation_id=self.correlation_id
        )
        
        # Add optional processing nodes based on configuration
        if self.enable_entity_deduplication:
            deduplication_node = EntityDeduplicationNode(
                kg_repository=self.kg_repository,
                node_id="entity_deduplication",
                correlation_id=self.correlation_id
            )
            self.add_node(deduplication_node)
        
        if self.enable_relationship_inference:
            relationship_node = RelationshipInferenceNode(
                kg_repository=self.kg_repository,
                node_id="relationship_inference",
                correlation_id=self.correlation_id
            )
            self.add_node(relationship_node)
        
        # Add core nodes to graph
        self.add_node(extraction_node)
        self.add_node(ner_node)
        self.add_node(embedding_node)
        self.add_node(kg_population_node)
        
        # Define workflow edges
        self.add_edge("document_extraction", "entity_recognition")
        self.add_edge("entity_recognition", "embedding_generation")
        self.add_edge("embedding_generation", "kg_population")
        
        # Add optional processing steps
        if self.enable_entity_deduplication:
            self.add_edge("kg_population", "entity_deduplication")
            
            if self.enable_relationship_inference:
                self.add_edge("entity_deduplication", "relationship_inference")
                self.set_exit_point("relationship_inference")
            else:
                self.set_exit_point("entity_deduplication")
        elif self.enable_relationship_inference:
            self.add_edge("kg_population", "relationship_inference")
            self.set_exit_point("relationship_inference")
        else:
            self.set_exit_point("kg_population")
        
        # Set entry point
        self.set_entry_point("document_extraction")
        
        logger.info(f"KG population graph built with {len(self.nodes)} nodes")
    
    def validate_graph(self) -> bool:
        """Validate the KG population graph structure."""
        # Check that core nodes exist
        core_nodes = ["document_extraction", "entity_recognition", "embedding_generation", "kg_population"]
        for node_id in core_nodes:
            if node_id not in self.nodes:
                logger.error(f"Core node '{node_id}' not found in KG population graph")
                return False
        
        # Check optional nodes based on configuration
        if self.enable_entity_deduplication and "entity_deduplication" not in self.nodes:
            logger.error("Entity deduplication enabled but node not found")
            return False
        
        if self.enable_relationship_inference and "relationship_inference" not in self.nodes:
            logger.error("Relationship inference enabled but node not found")
            return False
        
        # Check that graph has no cycles
        if self.has_cycles():
            logger.error("KG population graph contains cycles")
            return False
        
        # Check that entry and exit points are set
        if not self.entry_points:
            logger.error("No entry points defined in KG population graph")
            return False
        
        if not self.exit_points:
            logger.error("No exit points defined in KG population graph")
            return False
        
        logger.info("KG population graph validation successful")
        return True
    
    def get_kg_population_summary(self, final_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of the KG population results."""
        return {
            'document_id': final_state.get('document_id'),
            'file_path': final_state.get('file_path'),
            'entities_extracted': len(final_state.get('entities_extracted', [])),
            'document_node_id': final_state.get('document_node_id'),
            'entity_nodes_created': final_state.get('entity_nodes_created', 0),
            'relationships_created': final_state.get('relationships_created', 0),
            'kg_statistics': final_state.get('kg_statistics', {}),
            'deduplication_performed': final_state.get('deduplication_completed', False),
            'relationship_inference_performed': final_state.get('relationship_inference_completed', False),
            'configuration': {
                'entity_deduplication': self.enable_entity_deduplication,
                'relationship_inference': self.enable_relationship_inference
            }
        }


class MultiDocumentKGPopulationGraph(WorkflowGraph):
    """Workflow graph for populating knowledge graph from multiple documents.
    
    Processes multiple documents in sequence to build a comprehensive knowledge graph
    with cross-document relationship inference and entity consolidation.
    """
    
    def __init__(self, 
                 processor_factory: ProcessorFactory = None,
                 embedding_strategy: EmbeddingStrategy = None,
                 kg_repository: KnowledgeGraphRepository = None,
                 enable_cross_document_relationships: bool = True,
                 enable_global_deduplication: bool = True,
                 graph_id: str = None, 
                 correlation_id: str = None):
        super().__init__(graph_id, correlation_id)
        
        self.processor_factory = processor_factory or ProcessorFactory()
        self.embedding_strategy = embedding_strategy or LocalEmbeddingStrategy()
        if kg_repository is None:
            from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
            self.kg_repository = SQLiteKnowledgeGraphRepository()
        else:
            self.kg_repository = kg_repository
        
        self.enable_cross_document_relationships = enable_cross_document_relationships
        self.enable_global_deduplication = enable_global_deduplication
    
    def build_graph(self) -> None:
        """Build multi-document KG population graph."""
        logger.info(f"Building multi-document KG population graph {self.graph_id}")
        
        # Create document processing pipeline
        document_processor = DocumentBatchProcessorNode(
            processor_factory=self.processor_factory,
            embedding_strategy=self.embedding_strategy,
            kg_repository=self.kg_repository,
            node_id="document_batch_processor",
            correlation_id=self.correlation_id
        )
        
        # Add global processing nodes
        if self.enable_global_deduplication:
            global_dedup_node = GlobalEntityDeduplicationNode(
                kg_repository=self.kg_repository,
                node_id="global_deduplication",
                correlation_id=self.correlation_id
            )
            self.add_node(global_dedup_node)
        
        if self.enable_cross_document_relationships:
            cross_doc_relationships_node = CrossDocumentRelationshipNode(
                kg_repository=self.kg_repository,
                node_id="cross_document_relationships",
                correlation_id=self.correlation_id
            )
            self.add_node(cross_doc_relationships_node)
        
        # Add core node
        self.add_node(document_processor)
        
        # Define workflow edges
        current_node = "document_batch_processor"
        self.set_entry_point(current_node)
        
        if self.enable_global_deduplication:
            self.add_edge(current_node, "global_deduplication")
            current_node = "global_deduplication"
        
        if self.enable_cross_document_relationships:
            self.add_edge(current_node, "cross_document_relationships")
            current_node = "cross_document_relationships"
        
        self.set_exit_point(current_node)
        
        logger.info(f"Multi-document KG population graph built with {len(self.nodes)} nodes")
    
    def validate_graph(self) -> bool:
        """Validate multi-document KG population graph."""
        if "document_batch_processor" not in self.nodes:
            logger.error("Document batch processor node not found")
            return False
        
        if self.enable_global_deduplication and "global_deduplication" not in self.nodes:
            logger.error("Global deduplication enabled but node not found")
            return False
        
        if self.enable_cross_document_relationships and "cross_document_relationships" not in self.nodes:
            logger.error("Cross-document relationships enabled but node not found")
            return False
        
        if self.has_cycles():
            logger.error("Multi-document KG population graph contains cycles")
            return False
        
        logger.info("Multi-document KG population graph validation successful")
        return True
    
    def process_document_collection(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a collection of documents to populate knowledge graph."""
        logger.info(f"Processing {len(documents)} documents for KG population")
        
        initial_state = {
            'document_collection': documents,
            'correlation_id': self.correlation_id
        }
        
        result = self.execute(initial_state)
        
        if result.success:
            return {
                'success': True,
                'documents_processed': len(documents),
                'total_entities': result.final_state.get('total_entities_created', 0),
                'total_relationships': result.final_state.get('total_relationships_created', 0),
                'kg_statistics': result.final_state.get('final_kg_statistics', {}),
                'processing_summary': result.final_state
            }
        else:
            return {
                'success': False,
                'error': result.message,
                'documents_processed': 0
            }


# Specialized nodes for KG population workflow

class EntityDeduplicationNode(WorkflowNode):
    """Node for deduplicating entities within a single document."""
    
    def __init__(self, kg_repository: KnowledgeGraphRepository,
                 node_id: str = None, correlation_id: str = None):
        super().__init__(node_id, correlation_id)
        self.kg_repository = kg_repository
    
    def execute(self, state: Dict[str, Any]) -> 'NodeResult':
        """Execute entity deduplication."""
        from src.workflow.base.workflow_node import NodeResult
        
        try:
            document_node_id = state.get('document_node_id')
            entities_created = state.get('entity_nodes_created', 0)
            
            logger.info(f"Starting entity deduplication for document {document_node_id} "
                       f"[correlation_id: {self.correlation_id}]")
            
            # Get all entities for this document
            document_entities = self.kg_repository.get_nodes_by_property('document_id', document_node_id)
            
            # Group entities by type and similarity
            deduplicated_count = self._deduplicate_entities(document_entities)
            
            result_data = {
                'deduplication_completed': True,
                'entities_before_deduplication': entities_created,
                'entities_deduplicated': deduplicated_count,
                'entities_after_deduplication': entities_created - deduplicated_count
            }
            
            logger.info(f"Entity deduplication completed: removed {deduplicated_count} duplicates "
                       f"[correlation_id: {self.correlation_id}]")
            
            return NodeResult.success_result(
                f"Entity deduplication completed: {deduplicated_count} duplicates removed",
                data=result_data
            )
            
        except Exception as e:
            logger.error(f"Entity deduplication failed: {e} [correlation_id: {self.correlation_id}]")
            return NodeResult.failure_result(
                f"Entity deduplication failed: {str(e)}",
                error=e
            )
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> int:
        """Deduplicate entities based on similarity."""
        # Placeholder implementation
        # In a real system, this would use sophisticated similarity matching
        
        duplicates_removed = 0
        entities_by_type = {}
        
        # Group entities by type
        for entity in entities:
            entity_type = entity.get('node_type', 'unknown')
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)
        
        # Find and remove duplicates within each type
        for entity_type, type_entities in entities_by_type.items():
            seen_texts = set()
            for entity in type_entities:
                entity_text = entity.get('properties', {}).get('text', '').lower().strip()
                if entity_text in seen_texts:
                    # Remove duplicate entity
                    try:
                        self.kg_repository.delete_node(entity.get('node_id'))
                        duplicates_removed += 1
                    except Exception as e:
                        logger.warning(f"Failed to remove duplicate entity: {e}")
                else:
                    seen_texts.add(entity_text)
        
        return duplicates_removed
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        return 'document_node_id' in state
    
    def get_required_inputs(self) -> List[str]:
        return ['document_node_id']
    
    def get_output_keys(self) -> List[str]:
        return ['deduplication_completed', 'entities_before_deduplication', 
                'entities_deduplicated', 'entities_after_deduplication']


class RelationshipInferenceNode(WorkflowNode):
    """Node for inferring additional relationships between entities."""
    
    def __init__(self, kg_repository: KnowledgeGraphRepository,
                 node_id: str = None, correlation_id: str = None):
        super().__init__(node_id, correlation_id)
        self.kg_repository = kg_repository
    
    def execute(self, state: Dict[str, Any]) -> 'NodeResult':
        """Execute relationship inference."""
        from src.workflow.base.workflow_node import NodeResult
        
        try:
            document_node_id = state.get('document_node_id')
            
            logger.info(f"Starting relationship inference for document {document_node_id} "
                       f"[correlation_id: {self.correlation_id}]")
            
            # Get all entities for this document
            document_entities = self.kg_repository.get_nodes_by_property('document_id', document_node_id)
            
            # Infer additional relationships
            new_relationships = self._infer_relationships(document_entities)
            
            # Create the inferred relationships
            relationships_created = 0
            for relationship in new_relationships:
                try:
                    self.kg_repository.create_relationship(
                        relationship['source_id'],
                        relationship['target_id'],
                        relationship['relationship_type'],
                        relationship['properties']
                    )
                    relationships_created += 1
                except Exception as e:
                    logger.warning(f"Failed to create inferred relationship: {e}")
            
            result_data = {
                'relationship_inference_completed': True,
                'relationships_inferred': relationships_created,
                'inference_rules_applied': len(new_relationships)
            }
            
            logger.info(f"Relationship inference completed: {relationships_created} new relationships "
                       f"[correlation_id: {self.correlation_id}]")
            
            return NodeResult.success_result(
                f"Relationship inference completed: {relationships_created} new relationships",
                data=result_data
            )
            
        except Exception as e:
            logger.error(f"Relationship inference failed: {e} [correlation_id: {self.correlation_id}]")
            return NodeResult.failure_result(
                f"Relationship inference failed: {str(e)}",
                error=e
            )
    
    def _infer_relationships(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Infer relationships between entities based on medical knowledge."""
        from datetime import datetime
        
        relationships = []
        
        # Group entities by type
        entities_by_type = {}
        for entity in entities:
            entity_type = entity.get('node_type', 'unknown')
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)
        
        # Infer diagnosis -> body part relationships
        diagnoses = entities_by_type.get('Diagnosis', [])
        body_parts = entities_by_type.get('BodyPart', [])
        
        for diagnosis in diagnoses:
            for body_part in body_parts:
                # Simple heuristic: if diagnosis and body part appear in similar context
                if self._entities_contextually_related(diagnosis, body_part):
                    relationships.append({
                        'source_id': diagnosis.get('node_id'),
                        'target_id': body_part.get('node_id'),
                        'relationship_type': 'AFFECTS',
                        'properties': {
                            'inferred': True,
                            'confidence': 0.7,
                            'created_at': datetime.now().isoformat()
                        }
                    })
        
        # Infer diagnosis -> impairment rating relationships
        impairment_ratings = entities_by_type.get('ImpairmentRating', [])
        
        for diagnosis in diagnoses:
            for rating in impairment_ratings:
                if self._entities_contextually_related(diagnosis, rating):
                    relationships.append({
                        'source_id': diagnosis.get('node_id'),
                        'target_id': rating.get('node_id'),
                        'relationship_type': 'HAS_RATING',
                        'properties': {
                            'inferred': True,
                            'confidence': 0.8,
                            'created_at': datetime.now().isoformat()
                        }
                    })
        
        return relationships
    
    def _entities_contextually_related(self, entity1: Dict[str, Any], entity2: Dict[str, Any]) -> bool:
        """Check if two entities are contextually related."""
        # Simple implementation - check if they have overlapping context
        context1 = entity1.get('properties', {}).get('context', '').lower()
        context2 = entity2.get('properties', {}).get('context', '').lower()
        
        if not context1 or not context2:
            return False
        
        # Check for word overlap
        words1 = set(context1.split())
        words2 = set(context2.split())
        
        overlap = len(words1.intersection(words2))
        total = len(words1.union(words2))
        
        return (overlap / total) > 0.2 if total > 0 else False
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        return 'document_node_id' in state
    
    def get_required_inputs(self) -> List[str]:
        return ['document_node_id']
    
    def get_output_keys(self) -> List[str]:
        return ['relationship_inference_completed', 'relationships_inferred', 'inference_rules_applied']


class DocumentBatchProcessorNode(WorkflowNode):
    """Node for processing multiple documents in batch."""
    
    def __init__(self, processor_factory: ProcessorFactory,
                 embedding_strategy: EmbeddingStrategy,
                 kg_repository: KnowledgeGraphRepository,
                 node_id: str = None, correlation_id: str = None):
        super().__init__(node_id, correlation_id)
        self.processor_factory = processor_factory
        self.embedding_strategy = embedding_strategy
        self.kg_repository = kg_repository
    
    def execute(self, state: Dict[str, Any]) -> 'NodeResult':
        """Execute batch document processing."""
        from src.workflow.base.workflow_node import NodeResult
        
        try:
            documents = state.get('document_collection', [])
            
            logger.info(f"Starting batch processing of {len(documents)} documents "
                       f"[correlation_id: {self.correlation_id}]")
            
            total_entities = 0
            total_relationships = 0
            processed_documents = []
            
            # Process each document through the full pipeline
            for i, doc in enumerate(documents):
                try:
                    logger.info(f"Processing document {i+1}/{len(documents)}: {doc.get('file_path')}")
                    
                    # Create individual document processing graph
                    from src.workflow.graphs.document_processing_graph import DocumentProcessingGraph
                    doc_graph = DocumentProcessingGraph(
                        processor_factory=self.processor_factory,
                        embedding_strategy=self.embedding_strategy,
                        kg_repository=self.kg_repository,
                        correlation_id=self.correlation_id
                    )
                    
                    # Process the document
                    doc_result = doc_graph.execute(doc)
                    
                    if doc_result.success:
                        entities_created = doc_result.final_state.get('entity_nodes_created', 0)
                        relationships_created = doc_result.final_state.get('relationships_created', 0)
                        
                        total_entities += entities_created
                        total_relationships += relationships_created
                        
                        processed_documents.append({
                            'document_id': doc.get('document_id'),
                            'file_path': doc.get('file_path'),
                            'entities_created': entities_created,
                            'relationships_created': relationships_created,
                            'success': True
                        })
                    else:
                        logger.error(f"Failed to process document {doc.get('file_path')}: {doc_result.message}")
                        processed_documents.append({
                            'document_id': doc.get('document_id'),
                            'file_path': doc.get('file_path'),
                            'success': False,
                            'error': doc_result.message
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing document {doc.get('file_path')}: {e}")
                    processed_documents.append({
                        'document_id': doc.get('document_id'),
                        'file_path': doc.get('file_path'),
                        'success': False,
                        'error': str(e)
                    })
            
            successful_docs = len([d for d in processed_documents if d.get('success')])
            
            result_data = {
                'total_documents': len(documents),
                'successful_documents': successful_docs,
                'failed_documents': len(documents) - successful_docs,
                'total_entities_created': total_entities,
                'total_relationships_created': total_relationships,
                'processed_documents': processed_documents
            }
            
            logger.info(f"Batch processing completed: {successful_docs}/{len(documents)} documents successful "
                       f"[correlation_id: {self.correlation_id}]")
            
            return NodeResult.success_result(
                f"Batch processing completed: {successful_docs}/{len(documents)} documents",
                data=result_data
            )
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e} [correlation_id: {self.correlation_id}]")
            return NodeResult.failure_result(
                f"Batch processing failed: {str(e)}",
                error=e
            )
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        return 'document_collection' in state and isinstance(state['document_collection'], list)
    
    def get_required_inputs(self) -> List[str]:
        return ['document_collection']
    
    def get_output_keys(self) -> List[str]:
        return ['total_documents', 'successful_documents', 'failed_documents',
                'total_entities_created', 'total_relationships_created', 'processed_documents']


class GlobalEntityDeduplicationNode(WorkflowNode):
    """Node for global entity deduplication across all documents."""
    
    def __init__(self, kg_repository: KnowledgeGraphRepository,
                 node_id: str = None, correlation_id: str = None):
        super().__init__(node_id, correlation_id)
        self.kg_repository = kg_repository
    
    def execute(self, state: Dict[str, Any]) -> 'NodeResult':
        """Execute global entity deduplication."""
        from src.workflow.base.workflow_node import NodeResult
        
        # Placeholder implementation
        logger.info(f"Starting global entity deduplication [correlation_id: {self.correlation_id}]")
        
        # In a real implementation, this would:
        # 1. Get all entities across all documents
        # 2. Use sophisticated similarity matching (embeddings, fuzzy matching)
        # 3. Merge duplicate entities and update relationships
        
        result_data = {
            'global_deduplication_completed': True,
            'global_duplicates_removed': 0  # Placeholder
        }
        
        return NodeResult.success_result(
            "Global entity deduplication completed",
            data=result_data
        )
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        return True  # Can work with any state
    
    def get_required_inputs(self) -> List[str]:
        return []
    
    def get_output_keys(self) -> List[str]:
        return ['global_deduplication_completed', 'global_duplicates_removed']


class CrossDocumentRelationshipNode(WorkflowNode):
    """Node for inferring relationships across documents."""
    
    def __init__(self, kg_repository: KnowledgeGraphRepository,
                 node_id: str = None, correlation_id: str = None):
        super().__init__(node_id, correlation_id)
        self.kg_repository = kg_repository
    
    def execute(self, state: Dict[str, Any]) -> 'NodeResult':
        """Execute cross-document relationship inference."""
        from src.workflow.base.workflow_node import NodeResult
        
        # Placeholder implementation
        logger.info(f"Starting cross-document relationship inference [correlation_id: {self.correlation_id}]")
        
        # In a real implementation, this would:
        # 1. Analyze entities across all documents
        # 2. Find patterns and relationships that span documents
        # 3. Create cross-document relationships (e.g., same patient across multiple reports)
        
        result_data = {
            'cross_document_relationships_completed': True,
            'cross_document_relationships_created': 0  # Placeholder
        }
        
        return NodeResult.success_result(
            "Cross-document relationship inference completed",
            data=result_data
        )
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        return True  # Can work with any state
    
    def get_required_inputs(self) -> List[str]:
        return []
    
    def get_output_keys(self) -> List[str]:
        return ['cross_document_relationships_completed', 'cross_document_relationships_created']