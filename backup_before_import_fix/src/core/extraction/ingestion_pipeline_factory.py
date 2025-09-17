"""
Factory for creating ingestion pipeline with all dependencies.
Provides easy setup and configuration of the complete ingestion system.
"""

from typing import Optional

try:
    from src.factories.processor_factory import ProcessorFactory
    from src.strategies.embedding_strategy import EmbeddingStrategy, LocalEmbeddingStrategy, EmbeddingStrategyFactory
    from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository, SQLiteKnowledgeGraphRepository
    from src.core.extraction.ingestion_pipeline import IngestionPipeline, KnowledgeGraphService
    from src.infrastructure.storage.vector_store import VectorStoreManager, vector_store_manager
    from src.utils.logging_config import get_logger
except ImportError:
    from factories.processor_factory import ProcessorFactory
    from strategies.embedding_strategy import EmbeddingStrategy, LocalEmbeddingStrategy, EmbeddingStrategyFactory
    from repositories.knowledge_graph_repository import KnowledgeGraphRepository, SQLiteKnowledgeGraphRepository
    from core.extraction.ingestion_pipeline import IngestionPipeline, KnowledgeGraphService
    from infrastructure.storage.vector_store import VectorStoreManager, vector_store_manager
    from utils.logging_config import get_logger

logger = get_logger(__name__)


class IngestionPipelineFactory:
    """Factory for creating configured ingestion pipeline instances."""
    
    @staticmethod
    def create_default_pipeline(
        embedding_strategy_type: str = "local",
        embedding_model: str = "all-MiniLM-L6-v2",
        openai_api_key: Optional[str] = None,
        kg_repository: Optional[KnowledgeGraphRepository] = None,
        vector_store_name: str = "default"
    ) -> IngestionPipeline:
        """
        Create ingestion pipeline with default configuration.
        
        Args:
            embedding_strategy_type: Type of embedding strategy ('local' or 'openai')
            embedding_model: Model name for embedding generation
            openai_api_key: OpenAI API key (required for 'openai' strategy)
            kg_repository: Knowledge graph repository (uses default if None)
            vector_store_name: Name of vector store to use
            
        Returns:
            Configured IngestionPipeline instance
        """
        # Create processor factory
        processor_factory = ProcessorFactory()
        
        # Create embedding strategy
        if embedding_strategy_type.lower() == "openai":
            if not openai_api_key:
                raise ValueError("OpenAI API key is required for OpenAI embedding strategy")
            embedding_strategy = EmbeddingStrategyFactory.create_openai_strategy(
                api_key=openai_api_key,
                model=embedding_model
            )
        else:
            embedding_strategy = EmbeddingStrategyFactory.create_local_strategy(
                model_name=embedding_model
            )
        
        # Create knowledge graph repository
        if kg_repository is None:
            kg_repository = SQLiteKnowledgeGraphRepository()
        
        # Create vector store
        vector_store = vector_store_manager.get_or_create_store(vector_store_name)
        
        # Create knowledge graph service with vector store integration
        kg_service = EnhancedKnowledgeGraphService(
            kg_repository=kg_repository,
            vector_store=vector_store,
            embedding_strategy=embedding_strategy
        )
        
        # Create and return pipeline
        pipeline = IngestionPipeline(
            processor_factory=processor_factory,
            embedding_strategy=embedding_strategy,
            kg_service=kg_service
        )
        
        logger.info(f"Created ingestion pipeline with {embedding_strategy_type} embeddings and {vector_store_name} vector store")
        return pipeline
    
    @staticmethod
    def create_pipeline_from_config(config: dict) -> IngestionPipeline:
        """
        Create ingestion pipeline from configuration dictionary.
        
        Args:
            config: Configuration dictionary with pipeline settings
            
        Returns:
            Configured IngestionPipeline instance
        """
        return IngestionPipelineFactory.create_default_pipeline(
            embedding_strategy_type=config.get("embedding_strategy_type", "local"),
            embedding_model=config.get("embedding_model", "all-MiniLM-L6-v2"),
            openai_api_key=config.get("openai_api_key"),
            vector_store_name=config.get("vector_store_name", "default")
        )


class EnhancedKnowledgeGraphService(KnowledgeGraphService):
    """Enhanced knowledge graph service with vector store integration."""
    
    def __init__(self, 
                 kg_repository: KnowledgeGraphRepository,
                 vector_store,
                 embedding_strategy: EmbeddingStrategy):
        super().__init__(kg_repository)
        self.vector_store = vector_store
        self.embedding_strategy = embedding_strategy
    
    def populate_graph(self, 
                      document_id: str,
                      sections, 
                      entities,
                      embeddings_map: dict) -> None:
        """
        Enhanced graph population with vector store integration.
        
        Args:
            document_id: Source document ID
            sections: Document sections
            entities: Extracted entities
            embeddings_map: Map of text to embeddings
        """
        # Call parent method to populate SQLite tables
        super().populate_graph(document_id, sections, entities, embeddings_map)
        
        # Add sections to vector store
        for section in sections:
            if section.text_content in embeddings_map:
                self.vector_store.add_document(
                    doc_id=f"section_{section.id}",
                    text=section.text_content,
                    embeddings=embeddings_map[section.text_content],
                    metadata={
                        "type": "section",
                        "section_type": section.section_type,
                        "document_id": document_id,
                        "page_number": section.page_number
                    }
                )
        
        # Add entities to vector store
        for entity in entities:
            if entity.text in embeddings_map:
                self.vector_store.add_document(
                    doc_id=f"{entity.entity_type}_{entity.section_id}_{hash(entity.text)}",
                    text=entity.text,
                    embeddings=embeddings_map[entity.text],
                    metadata={
                        "type": "entity",
                        "entity_type": entity.entity_type,
                        "section_id": entity.section_id,
                        "page_reference": entity.page_reference,
                        "confidence": entity.confidence
                    }
                )
        
        logger.info(f"Added {len(sections)} sections and {len(entities)} entities to vector store")
    
    def search_similar_content(self, query_text: str, top_k: int = 5, min_similarity: float = 0.3):
        """
        Search for similar content using vector store.
        
        Args:
            query_text: Query text
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar documents with metadata
        """
        try:
            results = self.vector_store.search_by_text(
                query_text=query_text,
                embedding_strategy=self.embedding_strategy,
                top_k=top_k,
                min_similarity=min_similarity
            )
            
            return [
                {
                    "text": doc.text,
                    "similarity": similarity,
                    "metadata": doc.metadata
                }
                for doc, similarity in results
            ]
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    def get_vector_store_stats(self) -> dict:
        """Get vector store statistics."""
        return self.vector_store.get_stats()