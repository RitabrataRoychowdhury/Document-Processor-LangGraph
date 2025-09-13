"""Document processing workflow graph implementation."""

from typing import Dict, Any, List

from src.workflow.base.workflow_graph import WorkflowGraph
from src.workflow.nodes.extraction_node import ExtractionNode, EnhancedExtractionNode
from src.workflow.nodes.ner_node import NERNode, MLNERNode
from src.workflow.nodes.embedding_node import EmbeddingNode, CachedEmbeddingNode
from src.workflow.nodes.kg_population_node import KGPopulationNode
from src.factories.processor_factory import ProcessorFactory
from src.strategies.embedding_strategy import EmbeddingStrategy, LocalEmbeddingStrategy
from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class DocumentProcessingGraph(WorkflowGraph):
    """Workflow graph for document processing pipeline.
    
    Implements the complete document processing workflow:
    1. Text extraction from document
    2. Named entity recognition
    3. Vector embedding generation
    4. Knowledge graph population
    
    Follows Open/Closed Principle - easy to extend with new processing steps.
    """
    
    def __init__(self, 
                 processor_factory: ProcessorFactory = None,
                 embedding_strategy: EmbeddingStrategy = None,
                 kg_repository: KnowledgeGraphRepository = None,
                 use_enhanced_extraction: bool = True,
                 use_ml_ner: bool = False,
                 use_cached_embeddings: bool = True,
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
        self.use_enhanced_extraction = use_enhanced_extraction
        self.use_ml_ner = use_ml_ner
        self.use_cached_embeddings = use_cached_embeddings
    
    def build_graph(self) -> None:
        """Build the document processing workflow graph."""
        logger.info(f"Building document processing graph {self.graph_id}")
        
        # Create nodes based on configuration
        if self.use_enhanced_extraction:
            extraction_node = EnhancedExtractionNode(
                processor_factory=self.processor_factory,
                node_id="extraction",
                correlation_id=self.correlation_id
            )
        else:
            extraction_node = ExtractionNode(
                processor_factory=self.processor_factory,
                node_id="extraction",
                correlation_id=self.correlation_id
            )
        
        if self.use_ml_ner:
            ner_node = MLNERNode(
                node_id="ner",
                correlation_id=self.correlation_id
            )
        else:
            ner_node = NERNode(
                node_id="ner",
                correlation_id=self.correlation_id
            )
        
        if self.use_cached_embeddings:
            embedding_node = CachedEmbeddingNode(
                embedding_strategy=self.embedding_strategy,
                node_id="embedding",
                correlation_id=self.correlation_id
            )
        else:
            embedding_node = EmbeddingNode(
                embedding_strategy=self.embedding_strategy,
                node_id="embedding",
                correlation_id=self.correlation_id
            )
        
        kg_population_node = KGPopulationNode(
            kg_repository=self.kg_repository,
            node_id="kg_population",
            correlation_id=self.correlation_id
        )
        
        # Add nodes to graph
        self.add_node(extraction_node)
        self.add_node(ner_node)
        self.add_node(embedding_node)
        self.add_node(kg_population_node)
        
        # Define workflow edges (sequential processing)
        self.add_edge("extraction", "ner")
        self.add_edge("ner", "embedding")
        self.add_edge("embedding", "kg_population")
        
        # Set entry and exit points
        self.set_entry_point("extraction")
        self.set_exit_point("kg_population")
        
        logger.info(f"Document processing graph built with {len(self.nodes)} nodes")
    
    def validate_graph(self) -> bool:
        """Validate the document processing graph structure."""
        # Check that all required nodes exist
        required_nodes = ["extraction", "ner", "embedding", "kg_population"]
        for node_id in required_nodes:
            if node_id not in self.nodes:
                logger.error(f"Required node '{node_id}' not found in graph")
                return False
        
        # Check that graph has no cycles
        if self.has_cycles():
            logger.error("Document processing graph contains cycles")
            return False
        
        # Check that entry and exit points are set
        if not self.entry_points:
            logger.error("No entry points defined in document processing graph")
            return False
        
        if not self.exit_points:
            logger.error("No exit points defined in document processing graph")
            return False
        
        # Validate node dependencies
        extraction_node = self.nodes["extraction"]
        ner_node = self.nodes["ner"]
        embedding_node = self.nodes["embedding"]
        kg_node = self.nodes["kg_population"]
        
        # Check that NER node can receive extraction output
        extraction_outputs = set(extraction_node.get_output_keys())
        ner_inputs = set(ner_node.get_required_inputs())
        if not ner_inputs.issubset(extraction_outputs):
            missing_inputs = ner_inputs - extraction_outputs
            logger.error(f"NER node missing required inputs from extraction: {missing_inputs}")
            return False
        
        # Check that embedding node can receive NER output
        ner_outputs = set(ner_node.get_output_keys())
        embedding_inputs = set(embedding_node.get_required_inputs())
        combined_outputs = extraction_outputs.union(ner_outputs)
        if not embedding_inputs.issubset(combined_outputs):
            missing_inputs = embedding_inputs - combined_outputs
            logger.error(f"Embedding node missing required inputs: {missing_inputs}")
            return False
        
        # Check that KG node can receive all previous outputs
        embedding_outputs = set(embedding_node.get_output_keys())
        kg_inputs = set(kg_node.get_required_inputs())
        all_outputs = extraction_outputs.union(ner_outputs).union(embedding_outputs)
        if not kg_inputs.issubset(all_outputs):
            missing_inputs = kg_inputs - all_outputs
            logger.error(f"KG population node missing required inputs: {missing_inputs}")
            return False
        
        logger.info("Document processing graph validation successful")
        return True
    
    def get_processing_summary(self, final_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of the document processing results."""
        return {
            'document_id': final_state.get('document_id'),
            'file_path': final_state.get('file_path'),
            'file_type': final_state.get('file_type'),
            'text_length': final_state.get('text_length', 0),
            'entities_extracted': len(final_state.get('entities_extracted', [])),
            'embeddings_generated': bool(final_state.get('document_embedding')),
            'kg_populated': final_state.get('kg_population_completed', False),
            'nodes_created': final_state.get('entity_nodes_created', 0),
            'relationships_created': final_state.get('relationships_created', 0),
            'processing_configuration': {
                'enhanced_extraction': self.use_enhanced_extraction,
                'ml_ner': self.use_ml_ner,
                'cached_embeddings': self.use_cached_embeddings
            }
        }


class ParallelDocumentProcessingGraph(WorkflowGraph):
    """Parallel document processing workflow graph.
    
    Processes multiple documents in parallel for better performance.
    Extends DocumentProcessingGraph with parallel processing capabilities.
    """
    
    def __init__(self, 
                 processor_factory: ProcessorFactory = None,
                 embedding_strategy: EmbeddingStrategy = None,
                 kg_repository: KnowledgeGraphRepository = None,
                 max_parallel_documents: int = 3,
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
        
        self.max_parallel_documents = max_parallel_documents
    
    def build_graph(self) -> None:
        """Build parallel document processing graph."""
        logger.info(f"Building parallel document processing graph {self.graph_id}")
        
        # Create multiple processing pipelines
        for i in range(self.max_parallel_documents):
            pipeline_id = f"pipeline_{i}"
            
            # Create nodes for this pipeline
            extraction_node = ExtractionNode(
                processor_factory=self.processor_factory,
                node_id=f"extraction_{i}",
                correlation_id=self.correlation_id
            )
            
            ner_node = NERNode(
                node_id=f"ner_{i}",
                correlation_id=self.correlation_id
            )
            
            embedding_node = EmbeddingNode(
                embedding_strategy=self.embedding_strategy,
                node_id=f"embedding_{i}",
                correlation_id=self.correlation_id
            )
            
            kg_node = KGPopulationNode(
                kg_repository=self.kg_repository,
                node_id=f"kg_population_{i}",
                correlation_id=self.correlation_id
            )
            
            # Add nodes to graph
            self.add_node(extraction_node)
            self.add_node(ner_node)
            self.add_node(embedding_node)
            self.add_node(kg_node)
            
            # Create pipeline edges
            self.add_edge(f"extraction_{i}", f"ner_{i}")
            self.add_edge(f"ner_{i}", f"embedding_{i}")
            self.add_edge(f"embedding_{i}", f"kg_population_{i}")
            
            # Set as entry and exit points
            self.set_entry_point(f"extraction_{i}")
            self.set_exit_point(f"kg_population_{i}")
        
        logger.info(f"Parallel document processing graph built with {len(self.nodes)} nodes "
                   f"({self.max_parallel_documents} pipelines)")
    
    def validate_graph(self) -> bool:
        """Validate the parallel document processing graph."""
        # Check that we have the expected number of pipelines
        expected_nodes = self.max_parallel_documents * 4  # 4 nodes per pipeline
        if len(self.nodes) != expected_nodes:
            logger.error(f"Expected {expected_nodes} nodes, found {len(self.nodes)}")
            return False
        
        # Validate each pipeline
        for i in range(self.max_parallel_documents):
            pipeline_nodes = [f"extraction_{i}", f"ner_{i}", f"embedding_{i}", f"kg_population_{i}"]
            
            for node_id in pipeline_nodes:
                if node_id not in self.nodes:
                    logger.error(f"Pipeline {i} missing node: {node_id}")
                    return False
        
        # Check that there are no cross-pipeline dependencies
        for node_id, next_nodes in self.edges.items():
            pipeline_num = node_id.split('_')[-1] if '_' in node_id else '0'
            
            for next_node in next_nodes:
                next_pipeline_num = next_node.split('_')[-1] if '_' in next_node else '0'
                
                if pipeline_num != next_pipeline_num:
                    logger.error(f"Cross-pipeline dependency detected: {node_id} -> {next_node}")
                    return False
        
        logger.info("Parallel document processing graph validation successful")
        return True


class StreamingDocumentProcessingGraph(DocumentProcessingGraph):
    """Streaming document processing graph for real-time processing.
    
    Extends DocumentProcessingGraph with streaming capabilities for processing
    documents as they arrive.
    """
    
    def __init__(self, 
                 processor_factory: ProcessorFactory = None,
                 embedding_strategy: EmbeddingStrategy = None,
                 kg_repository: KnowledgeGraphRepository = None,
                 buffer_size: int = 10,
                 graph_id: str = None, 
                 correlation_id: str = None):
        super().__init__(processor_factory, embedding_strategy, kg_repository, 
                        graph_id=graph_id, correlation_id=correlation_id)
        self.buffer_size = buffer_size
        self._document_buffer: List[Dict[str, Any]] = []
    
    def add_document_to_buffer(self, document_data: Dict[str, Any]) -> None:
        """Add a document to the processing buffer."""
        self._document_buffer.append(document_data)
        
        if len(self._document_buffer) >= self.buffer_size:
            self._process_buffer()
    
    def _process_buffer(self) -> None:
        """Process all documents in the buffer."""
        logger.info(f"Processing buffer with {len(self._document_buffer)} documents")
        
        for document_data in self._document_buffer:
            try:
                result = self.execute(document_data)
                if result.success:
                    logger.info(f"Successfully processed document: {document_data.get('file_path')}")
                else:
                    logger.error(f"Failed to process document: {result.message}")
            except Exception as e:
                logger.error(f"Error processing document {document_data.get('file_path')}: {e}")
        
        # Clear buffer after processing
        self._document_buffer.clear()
    
    def flush_buffer(self) -> None:
        """Process any remaining documents in the buffer."""
        if self._document_buffer:
            self._process_buffer()
    
    def get_buffer_status(self) -> Dict[str, Any]:
        """Get current buffer status."""
        return {
            'buffer_size': len(self._document_buffer),
            'buffer_capacity': self.buffer_size,
            'buffer_full': len(self._document_buffer) >= self.buffer_size
        }