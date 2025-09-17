"""Factory for creating workflow nodes following the Factory Pattern."""

from typing import Dict, Any, Type, Optional, List
from abc import ABC, abstractmethod

from src.workflow.base.workflow_node import WorkflowNode
from src.workflow.nodes.extraction_node import ExtractionNode, EnhancedExtractionNode
from src.workflow.nodes.ner_node import NERNode, MLNERNode
from src.workflow.nodes.embedding_node import EmbeddingNode, CachedEmbeddingNode, BatchEmbeddingNode
from src.workflow.nodes.kg_population_node import KGPopulationNode
from src.workflow.nodes.template_generation_node import TemplateGenerationNode
from src.factories.processor_factory import ProcessorFactory
from src.strategies.embedding_strategy import EmbeddingStrategy, LocalEmbeddingStrategy
from src.core.generation.qme_template_generator import QMETemplateGenerator
from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class NodeFactory(ABC):
    """Abstract factory for creating workflow nodes.
    
    Implements Factory Pattern for node creation.
    Follows Open/Closed Principle - easy to extend with new node types.
    """
    
    @abstractmethod
    def create_node(self, node_type: str, node_config: Dict[str, Any] = None, 
                   node_id: str = None, correlation_id: str = None) -> WorkflowNode:
        """Create a workflow node of the specified type.
        
        Args:
            node_type: Type of node to create
            node_config: Configuration parameters for the node
            node_id: Optional node ID
            correlation_id: Optional correlation ID
            
        Returns:
            WorkflowNode instance
            
        Raises:
            ValueError: If node_type is not supported
        """
        pass
    
    @abstractmethod
    def get_supported_node_types(self) -> List[str]:
        """Get list of supported node types.
        
        Returns:
            List of supported node type names
        """
        pass
    
    def is_node_type_supported(self, node_type: str) -> bool:
        """Check if a node type is supported.
        
        Args:
            node_type: Node type to check
            
        Returns:
            True if supported, False otherwise
        """
        return node_type in self.get_supported_node_types()


class StandardNodeFactory(NodeFactory):
    """Standard implementation of NodeFactory.
    
    Creates standard workflow nodes with default configurations.
    """
    
    def __init__(self, 
                 processor_factory: ProcessorFactory = None,
                 embedding_strategy: EmbeddingStrategy = None,
                 template_generator: QMETemplateGenerator = None,
                 kg_repository: KnowledgeGraphRepository = None):
        """Initialize the node factory with dependencies.
        
        Args:
            processor_factory: Factory for document processors
            embedding_strategy: Strategy for generating embeddings
            template_generator: Generator for QME templates
            kg_repository: Repository for knowledge graph operations
        """
        self.processor_factory = processor_factory or ProcessorFactory()
        self.embedding_strategy = embedding_strategy or LocalEmbeddingStrategy()
        self.template_generator = template_generator or QMETemplateGenerator()
        
        if kg_repository is None:
            from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
            self.kg_repository = SQLiteKnowledgeGraphRepository()
        else:
            self.kg_repository = kg_repository
        
        # Registry of node creators
        self._node_creators = {
            'extraction': self._create_extraction_node,
            'enhanced_extraction': self._create_enhanced_extraction_node,
            'ner': self._create_ner_node,
            'ml_ner': self._create_ml_ner_node,
            'embedding': self._create_embedding_node,
            'cached_embedding': self._create_cached_embedding_node,
            'batch_embedding': self._create_batch_embedding_node,
            'kg_population': self._create_kg_population_node,
            'template_generation': self._create_template_generation_node
        }
    
    def create_node(self, node_type: str, node_config: Dict[str, Any] = None, 
                   node_id: str = None, correlation_id: str = None) -> WorkflowNode:
        """Create a workflow node of the specified type."""
        if node_type not in self._node_creators:
            raise ValueError(f"Unsupported node type: {node_type}. "
                           f"Supported types: {list(self._node_creators.keys())}")
        
        config = node_config or {}
        creator_func = self._node_creators[node_type]
        
        try:
            node = creator_func(config, node_id, correlation_id)
            logger.debug(f"Created {node_type} node with ID {node.node_id}")
            return node
        except Exception as e:
            logger.error(f"Failed to create {node_type} node: {e}")
            raise ValueError(f"Failed to create {node_type} node: {str(e)}") from e
    
    def get_supported_node_types(self) -> List[str]:
        """Get list of supported node types."""
        return list(self._node_creators.keys())
    
    def _create_extraction_node(self, config: Dict[str, Any], 
                               node_id: str = None, correlation_id: str = None) -> ExtractionNode:
        """Create a standard extraction node."""
        return ExtractionNode(
            processor_factory=self.processor_factory,
            node_id=node_id,
            correlation_id=correlation_id
        )
    
    def _create_enhanced_extraction_node(self, config: Dict[str, Any], 
                                        node_id: str = None, correlation_id: str = None) -> EnhancedExtractionNode:
        """Create an enhanced extraction node."""
        return EnhancedExtractionNode(
            processor_factory=self.processor_factory,
            enable_ocr_fallback=config.get('enable_ocr_fallback', True),
            min_text_length=config.get('min_text_length', 50),
            node_id=node_id,
            correlation_id=correlation_id
        )
    
    def _create_ner_node(self, config: Dict[str, Any], 
                        node_id: str = None, correlation_id: str = None) -> NERNode:
        """Create a standard NER node."""
        return NERNode(
            node_id=node_id,
            correlation_id=correlation_id
        )
    
    def _create_ml_ner_node(self, config: Dict[str, Any], 
                           node_id: str = None, correlation_id: str = None) -> MLNERNode:
        """Create an ML-based NER node."""
        return MLNERNode(
            model_name=config.get('model_name', 'en_core_web_sm'),
            node_id=node_id,
            correlation_id=correlation_id
        )
    
    def _create_embedding_node(self, config: Dict[str, Any], 
                              node_id: str = None, correlation_id: str = None) -> EmbeddingNode:
        """Create a standard embedding node."""
        return EmbeddingNode(
            embedding_strategy=self.embedding_strategy,
            chunk_size=config.get('chunk_size', 1000),
            chunk_overlap=config.get('chunk_overlap', 200),
            node_id=node_id,
            correlation_id=correlation_id
        )
    
    def _create_cached_embedding_node(self, config: Dict[str, Any], 
                                     node_id: str = None, correlation_id: str = None) -> CachedEmbeddingNode:
        """Create a cached embedding node."""
        return CachedEmbeddingNode(
            embedding_strategy=self.embedding_strategy,
            chunk_size=config.get('chunk_size', 1000),
            chunk_overlap=config.get('chunk_overlap', 200),
            enable_cache=config.get('enable_cache', True),
            node_id=node_id,
            correlation_id=correlation_id
        )
    
    def _create_batch_embedding_node(self, config: Dict[str, Any], 
                                    node_id: str = None, correlation_id: str = None) -> BatchEmbeddingNode:
        """Create a batch embedding node."""
        return BatchEmbeddingNode(
            embedding_strategy=self.embedding_strategy,
            chunk_size=config.get('chunk_size', 1000),
            chunk_overlap=config.get('chunk_overlap', 200),
            batch_size=config.get('batch_size', 10),
            node_id=node_id,
            correlation_id=correlation_id
        )
    
    def _create_kg_population_node(self, config: Dict[str, Any], 
                                  node_id: str = None, correlation_id: str = None) -> KGPopulationNode:
        """Create a knowledge graph population node."""
        return KGPopulationNode(
            kg_repository=self.kg_repository,
            node_id=node_id,
            correlation_id=correlation_id
        )
    
    def _create_template_generation_node(self, config: Dict[str, Any], 
                                        node_id: str = None, correlation_id: str = None) -> TemplateGenerationNode:
        """Create a template generation node."""
        return TemplateGenerationNode(
            template_generator=self.template_generator,
            kg_repository=self.kg_repository,
            output_directory=config.get('output_directory', 'output/templates'),
            node_id=node_id,
            correlation_id=correlation_id
        )
    
    def register_node_creator(self, node_type: str, creator_func) -> None:
        """Register a custom node creator function.
        
        Args:
            node_type: Name of the node type
            creator_func: Function that creates the node
        """
        self._node_creators[node_type] = creator_func
        logger.info(f"Registered custom node creator for type: {node_type}")
    
    def unregister_node_creator(self, node_type: str) -> None:
        """Unregister a node creator function.
        
        Args:
            node_type: Name of the node type to unregister
        """
        if node_type in self._node_creators:
            del self._node_creators[node_type]
            logger.info(f"Unregistered node creator for type: {node_type}")


class ConfigurableNodeFactory(StandardNodeFactory):
    """Configurable node factory that supports custom configurations.
    
    Extends StandardNodeFactory with advanced configuration capabilities.
    """
    
    def __init__(self, 
                 processor_factory: ProcessorFactory = None,
                 embedding_strategy: EmbeddingStrategy = None,
                 template_generator: QMETemplateGenerator = None,
                 kg_repository: KnowledgeGraphRepository = None,
                 default_configs: Dict[str, Dict[str, Any]] = None):
        """Initialize configurable node factory.
        
        Args:
            processor_factory: Factory for document processors
            embedding_strategy: Strategy for generating embeddings
            template_generator: Generator for QME templates
            kg_repository: Repository for knowledge graph operations
            default_configs: Default configurations for each node type
        """
        super().__init__(processor_factory, embedding_strategy, template_generator, kg_repository)
        
        self.default_configs = default_configs or {}
        self._node_profiles = {}  # Named configuration profiles
    
    def create_node(self, node_type: str, node_config: Dict[str, Any] = None, 
                   node_id: str = None, correlation_id: str = None) -> WorkflowNode:
        """Create a node with merged default and provided configurations."""
        # Merge default config with provided config
        default_config = self.default_configs.get(node_type, {})
        merged_config = {**default_config, **(node_config or {})}
        
        return super().create_node(node_type, merged_config, node_id, correlation_id)
    
    def create_node_from_profile(self, profile_name: str, node_id: str = None, 
                                correlation_id: str = None) -> WorkflowNode:
        """Create a node from a named configuration profile.
        
        Args:
            profile_name: Name of the configuration profile
            node_id: Optional node ID
            correlation_id: Optional correlation ID
            
        Returns:
            WorkflowNode instance
            
        Raises:
            ValueError: If profile is not found
        """
        if profile_name not in self._node_profiles:
            raise ValueError(f"Node profile '{profile_name}' not found. "
                           f"Available profiles: {list(self._node_profiles.keys())}")
        
        profile = self._node_profiles[profile_name]
        node_type = profile['node_type']
        config = profile.get('config', {})
        
        return self.create_node(node_type, config, node_id, correlation_id)
    
    def register_node_profile(self, profile_name: str, node_type: str, 
                             config: Dict[str, Any] = None) -> None:
        """Register a named configuration profile.
        
        Args:
            profile_name: Name of the profile
            node_type: Type of node this profile creates
            config: Configuration parameters for the profile
        """
        if not self.is_node_type_supported(node_type):
            raise ValueError(f"Unsupported node type for profile: {node_type}")
        
        self._node_profiles[profile_name] = {
            'node_type': node_type,
            'config': config or {}
        }
        
        logger.info(f"Registered node profile '{profile_name}' for type '{node_type}'")
    
    def get_node_profiles(self) -> List[str]:
        """Get list of available node profiles.
        
        Returns:
            List of profile names
        """
        return list(self._node_profiles.keys())
    
    def set_default_config(self, node_type: str, config: Dict[str, Any]) -> None:
        """Set default configuration for a node type.
        
        Args:
            node_type: Node type to set default config for
            config: Default configuration parameters
        """
        if not self.is_node_type_supported(node_type):
            raise ValueError(f"Unsupported node type: {node_type}")
        
        self.default_configs[node_type] = config
        logger.info(f"Set default configuration for node type: {node_type}")
    
    def get_default_config(self, node_type: str) -> Dict[str, Any]:
        """Get default configuration for a node type.
        
        Args:
            node_type: Node type to get default config for
            
        Returns:
            Default configuration dictionary
        """
        return self.default_configs.get(node_type, {})


class NodeFactoryBuilder:
    """Builder for creating configured node factories.
    
    Implements Builder Pattern for factory configuration.
    """
    
    def __init__(self):
        self._processor_factory = None
        self._embedding_strategy = None
        self._template_generator = None
        self._kg_repository = None
        self._default_configs = {}
        self._node_profiles = {}
        self._factory_type = 'standard'
    
    def with_processor_factory(self, processor_factory: ProcessorFactory) -> 'NodeFactoryBuilder':
        """Set the processor factory.
        
        Args:
            processor_factory: Factory for document processors
            
        Returns:
            Self for method chaining
        """
        self._processor_factory = processor_factory
        return self
    
    def with_embedding_strategy(self, embedding_strategy: EmbeddingStrategy) -> 'NodeFactoryBuilder':
        """Set the embedding strategy.
        
        Args:
            embedding_strategy: Strategy for generating embeddings
            
        Returns:
            Self for method chaining
        """
        self._embedding_strategy = embedding_strategy
        return self
    
    def with_template_generator(self, template_generator: QMETemplateGenerator) -> 'NodeFactoryBuilder':
        """Set the template generator.
        
        Args:
            template_generator: Generator for QME templates
            
        Returns:
            Self for method chaining
        """
        self._template_generator = template_generator
        return self
    
    def with_kg_repository(self, kg_repository: KnowledgeGraphRepository) -> 'NodeFactoryBuilder':
        """Set the knowledge graph repository.
        
        Args:
            kg_repository: Repository for knowledge graph operations
            
        Returns:
            Self for method chaining
        """
        self._kg_repository = kg_repository
        return self
    
    def with_default_config(self, node_type: str, config: Dict[str, Any]) -> 'NodeFactoryBuilder':
        """Add a default configuration for a node type.
        
        Args:
            node_type: Node type to configure
            config: Default configuration parameters
            
        Returns:
            Self for method chaining
        """
        self._default_configs[node_type] = config
        return self
    
    def with_node_profile(self, profile_name: str, node_type: str, 
                         config: Dict[str, Any] = None) -> 'NodeFactoryBuilder':
        """Add a named node profile.
        
        Args:
            profile_name: Name of the profile
            node_type: Type of node this profile creates
            config: Configuration parameters for the profile
            
        Returns:
            Self for method chaining
        """
        self._node_profiles[profile_name] = {
            'node_type': node_type,
            'config': config or {}
        }
        return self
    
    def configurable(self) -> 'NodeFactoryBuilder':
        """Set factory type to configurable.
        
        Returns:
            Self for method chaining
        """
        self._factory_type = 'configurable'
        return self
    
    def build(self) -> NodeFactory:
        """Build the configured node factory.
        
        Returns:
            Configured NodeFactory instance
        """
        if self._factory_type == 'configurable':
            factory = ConfigurableNodeFactory(
                processor_factory=self._processor_factory,
                embedding_strategy=self._embedding_strategy,
                template_generator=self._template_generator,
                kg_repository=self._kg_repository,
                default_configs=self._default_configs
            )
            
            # Register node profiles
            for profile_name, profile_data in self._node_profiles.items():
                factory.register_node_profile(
                    profile_name,
                    profile_data['node_type'],
                    profile_data['config']
                )
            
            return factory
        else:
            return StandardNodeFactory(
                processor_factory=self._processor_factory,
                embedding_strategy=self._embedding_strategy,
                template_generator=self._template_generator,
                kg_repository=self._kg_repository
            )


# Convenience functions for common factory configurations

def create_standard_node_factory() -> StandardNodeFactory:
    """Create a standard node factory with default dependencies.
    
    Returns:
        StandardNodeFactory instance
    """
    return StandardNodeFactory()


def create_configurable_node_factory(default_configs: Dict[str, Dict[str, Any]] = None) -> ConfigurableNodeFactory:
    """Create a configurable node factory with optional default configurations.
    
    Args:
        default_configs: Default configurations for node types
        
    Returns:
        ConfigurableNodeFactory instance
    """
    return ConfigurableNodeFactory(default_configs=default_configs)


def create_medical_workflow_factory() -> ConfigurableNodeFactory:
    """Create a node factory optimized for medical document workflows.
    
    Returns:
        ConfigurableNodeFactory with medical-specific configurations
    """
    medical_configs = {
        'enhanced_extraction': {
            'enable_ocr_fallback': True,
            'min_text_length': 100
        },
        'ml_ner': {
            'model_name': 'en_core_web_sm'
        },
        'cached_embedding': {
            'chunk_size': 800,
            'chunk_overlap': 150,
            'enable_cache': True
        },
        'template_generation': {
            'output_directory': 'output/qme_templates'
        }
    }
    
    factory = ConfigurableNodeFactory(default_configs=medical_configs)
    
    # Register medical workflow profiles
    factory.register_node_profile('medical_extraction', 'enhanced_extraction')
    factory.register_node_profile('medical_ner', 'ml_ner')
    factory.register_node_profile('medical_embedding', 'cached_embedding')
    factory.register_node_profile('qme_template', 'template_generation')
    
    return factory