"""Enhanced workflow manager using the new LLD-based architecture."""

import uuid
from typing import Dict, Any, Optional, List, Type
from datetime import datetime
from enum import Enum

from src.workflow.base.workflow_graph import WorkflowGraph, GraphResult
from src.workflow.base.state_manager import StateManager
from src.workflow.state.workflow_state import WorkflowState, WorkflowStateFactory
from src.workflow.state.document_state import DocumentState
from src.workflow.state.template_state import TemplateState
from src.workflow.graphs.document_processing_graph import DocumentProcessingGraph
from src.workflow.graphs.qme_generation_graph import QMEGenerationGraph
from src.workflow.graphs.knowledge_graph_population_graph import KnowledgeGraphPopulationGraph
from src.workflow.factories.node_factory import NodeFactory, create_medical_workflow_factory
from src.factories.processor_factory import ProcessorFactory
from src.strategies.embedding_strategy import EmbeddingStrategy, LocalEmbeddingStrategy
from src.services.qme_template_generator import QMETemplateGenerator
from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class WorkflowType(Enum):
    """Types of workflows supported by the enhanced workflow manager."""
    DOCUMENT_PROCESSING = "document_processing"
    QME_GENERATION = "qme_generation"
    KNOWLEDGE_GRAPH_POPULATION = "kg_population"


class EnhancedWorkflowManager:
    """Enhanced workflow manager using LLD-based architecture.
    
    Implements the Facade pattern to provide a simple interface to the complex
    workflow subsystem. Manages workflow execution, state, and monitoring.
    
    Follows Single Responsibility Principle - manages workflow orchestration.
    Implements Dependency Inversion - depends on abstractions, not concretions.
    """
    
    def __init__(self,
                 node_factory: NodeFactory = None,
                 processor_factory: ProcessorFactory = None,
                 embedding_strategy: EmbeddingStrategy = None,
                 template_generator: QMETemplateGenerator = None,
                 kg_repository: KnowledgeGraphRepository = None):
        """Initialize the enhanced workflow manager.
        
        Args:
            node_factory: Factory for creating workflow nodes
            processor_factory: Factory for document processors
            embedding_strategy: Strategy for generating embeddings
            template_generator: Generator for QME templates
            kg_repository: Repository for knowledge graph operations
        """
        # Initialize dependencies
        self.node_factory = node_factory or create_medical_workflow_factory()
        self.processor_factory = processor_factory or ProcessorFactory()
        self.embedding_strategy = embedding_strategy or LocalEmbeddingStrategy()
        self.template_generator = template_generator or QMETemplateGenerator()
        
        if kg_repository is None:
            from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
            self.kg_repository = SQLiteKnowledgeGraphRepository()
        else:
            self.kg_repository = kg_repository
        
        # Workflow management
        self._active_workflows: Dict[str, Dict[str, Any]] = {}
        self._workflow_history: List[Dict[str, Any]] = []
        self._workflow_graphs: Dict[WorkflowType, Type[WorkflowGraph]] = {
            WorkflowType.DOCUMENT_PROCESSING: DocumentProcessingGraph,
            WorkflowType.QME_GENERATION: QMEGenerationGraph,
            WorkflowType.KNOWLEDGE_GRAPH_POPULATION: KnowledgeGraphPopulationGraph
        }
    
    def execute_document_processing_workflow(self, 
                                           file_path: str,
                                           document_id: str = None,
                                           workflow_config: Dict[str, Any] = None) -> str:
        """Execute document processing workflow.
        
        Args:
            file_path: Path to the document to process
            document_id: Optional document ID
            workflow_config: Optional workflow configuration
            
        Returns:
            Workflow execution ID
        """
        workflow_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        
        logger.info(f"Starting document processing workflow {workflow_id} for {file_path}")
        
        try:
            # Create document state
            document_state = DocumentState(workflow_id, correlation_id)
            
            # Initialize state with document information
            initial_data = {
                'workflow_id': workflow_id,
                'document_id': document_id or str(uuid.uuid4()),
                'file_path': file_path,
                'file_type': self._get_file_type(file_path),
                'workflow_type': WorkflowType.DOCUMENT_PROCESSING.value
            }
            document_state.initialize_state(initial_data)
            
            # Create and configure workflow graph
            config = workflow_config or {}
            graph = DocumentProcessingGraph(
                processor_factory=self.processor_factory,
                embedding_strategy=self.embedding_strategy,
                kg_repository=self.kg_repository,
                use_enhanced_extraction=config.get('use_enhanced_extraction', True),
                use_ml_ner=config.get('use_ml_ner', False),
                use_cached_embeddings=config.get('use_cached_embeddings', True),
                graph_id=workflow_id,
                correlation_id=correlation_id
            )
            
            # Register workflow
            self._register_workflow(workflow_id, WorkflowType.DOCUMENT_PROCESSING, 
                                  document_state, graph)
            
            # Execute workflow asynchronously
            self._execute_workflow_async(workflow_id, document_state.get_state())
            
            return workflow_id
            
        except Exception as e:
            logger.error(f"Failed to start document processing workflow: {e}")
            raise
    
    def execute_qme_generation_workflow(self,
                                      patient_file_path: str,
                                      patient_document_id: str = None,
                                      template_type: str = 'qme_report',
                                      output_directory: str = None,
                                      workflow_config: Dict[str, Any] = None) -> str:
        """Execute QME template generation workflow.
        
        Args:
            patient_file_path: Path to the patient document
            patient_document_id: Optional patient document ID
            template_type: Type of template to generate
            output_directory: Directory for output files
            workflow_config: Optional workflow configuration
            
        Returns:
            Workflow execution ID
        """
        workflow_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        
        logger.info(f"Starting QME generation workflow {workflow_id} for {patient_file_path}")
        
        try:
            # Create template state
            template_state = TemplateState(workflow_id, correlation_id)
            
            # Initialize state with template information
            initial_data = {
                'workflow_id': workflow_id,
                'patient_document_id': patient_document_id or str(uuid.uuid4()),
                'patient_file_path': patient_file_path,
                'file_path': patient_file_path,  # Alias for compatibility
                'template_type': template_type,
                'workflow_type': WorkflowType.QME_GENERATION.value
            }
            template_state.initialize_state(initial_data)
            
            # Create and configure workflow graph
            config = workflow_config or {}
            graph = QMEGenerationGraph(
                processor_factory=self.processor_factory,
                template_generator=self.template_generator,
                kg_repository=self.kg_repository,
                output_directory=output_directory or 'output/templates',
                graph_id=workflow_id,
                correlation_id=correlation_id
            )
            
            # Register workflow
            self._register_workflow(workflow_id, WorkflowType.QME_GENERATION, 
                                  template_state, graph)
            
            # Execute workflow asynchronously
            self._execute_workflow_async(workflow_id, template_state.get_state())
            
            return workflow_id
            
        except Exception as e:
            logger.error(f"Failed to start QME generation workflow: {e}")
            raise
    
    def execute_kg_population_workflow(self,
                                     documents: List[Dict[str, Any]],
                                     workflow_config: Dict[str, Any] = None) -> str:
        """Execute knowledge graph population workflow.
        
        Args:
            documents: List of documents to process for KG population
            workflow_config: Optional workflow configuration
            
        Returns:
            Workflow execution ID
        """
        workflow_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        
        logger.info(f"Starting KG population workflow {workflow_id} for {len(documents)} documents")
        
        try:
            # Create workflow state
            workflow_state = WorkflowState(workflow_id, correlation_id)
            
            # Initialize state with KG population information
            initial_data = {
                'workflow_id': workflow_id,
                'document_collection': documents,
                'workflow_type': WorkflowType.KNOWLEDGE_GRAPH_POPULATION.value
            }
            workflow_state.initialize_state(initial_data)
            
            # Create and configure workflow graph
            config = workflow_config or {}
            graph = KnowledgeGraphPopulationGraph(
                processor_factory=self.processor_factory,
                embedding_strategy=self.embedding_strategy,
                kg_repository=self.kg_repository,
                enable_relationship_inference=config.get('enable_relationship_inference', True),
                enable_entity_deduplication=config.get('enable_entity_deduplication', True),
                graph_id=workflow_id,
                correlation_id=correlation_id
            )
            
            # Register workflow
            self._register_workflow(workflow_id, WorkflowType.KNOWLEDGE_GRAPH_POPULATION, 
                                  workflow_state, graph)
            
            # Execute workflow asynchronously
            self._execute_workflow_async(workflow_id, workflow_state.get_state())
            
            return workflow_id
            
        except Exception as e:
            logger.error(f"Failed to start KG population workflow: {e}")
            raise
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a workflow.
        
        Args:
            workflow_id: ID of the workflow to check
            
        Returns:
            Workflow status information or None if not found
        """
        if workflow_id not in self._active_workflows:
            # Check workflow history
            for workflow in self._workflow_history:
                if workflow['workflow_id'] == workflow_id:
                    return workflow
            return None
        
        workflow_info = self._active_workflows[workflow_id]
        state_manager = workflow_info['state_manager']
        
        # Get state summary based on workflow type
        if isinstance(state_manager, DocumentState):
            summary = state_manager.get_processing_summary()
        elif isinstance(state_manager, TemplateState):
            summary = state_manager.get_generation_summary()
        else:
            summary = state_manager.get_workflow_summary()
        
        return {
            'workflow_id': workflow_id,
            'workflow_type': workflow_info['workflow_type'].value,
            'status': summary,
            'created_at': workflow_info['created_at'],
            'last_updated': state_manager.get_state().get('updated_at')
        }
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel an active workflow.
        
        Args:
            workflow_id: ID of the workflow to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        if workflow_id not in self._active_workflows:
            logger.warning(f"Workflow {workflow_id} not found or already completed")
            return False
        
        try:
            workflow_info = self._active_workflows[workflow_id]
            state_manager = workflow_info['state_manager']
            
            # Update state to cancelled
            state_manager.update_state({
                'status': 'cancelled',
                'cancelled_at': datetime.now().isoformat()
            })
            state_manager.set_status(state_manager.StateStatus.CANCELLED)
            
            # Move to history
            self._move_workflow_to_history(workflow_id)
            
            logger.info(f"Cancelled workflow {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel workflow {workflow_id}: {e}")
            return False
    
    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get list of active workflows.
        
        Returns:
            List of active workflow information
        """
        active_workflows = []
        
        for workflow_id, workflow_info in self._active_workflows.items():
            state_manager = workflow_info['state_manager']
            
            active_workflows.append({
                'workflow_id': workflow_id,
                'workflow_type': workflow_info['workflow_type'].value,
                'status': state_manager.get_status().value,
                'created_at': workflow_info['created_at'],
                'progress': state_manager.get_value('progress_percentage', 0)
            })
        
        return active_workflows
    
    def get_workflow_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get workflow execution history.
        
        Args:
            limit: Maximum number of workflows to return
            
        Returns:
            List of completed workflow information
        """
        return self._workflow_history[-limit:] if limit > 0 else self._workflow_history
    
    def get_workflow_metrics(self) -> Dict[str, Any]:
        """Get workflow execution metrics.
        
        Returns:
            Workflow metrics and statistics
        """
        total_workflows = len(self._workflow_history) + len(self._active_workflows)
        active_count = len(self._active_workflows)
        completed_count = len([w for w in self._workflow_history if w.get('status') == 'completed'])
        failed_count = len([w for w in self._workflow_history if w.get('status') == 'failed'])
        
        # Calculate success rate
        success_rate = (completed_count / len(self._workflow_history)) * 100 if self._workflow_history else 0
        
        # Group by workflow type
        type_counts = {}
        for workflow in self._workflow_history + list(self._active_workflows.values()):
            workflow_type = workflow.get('workflow_type', 'unknown')
            if isinstance(workflow_type, WorkflowType):
                workflow_type = workflow_type.value
            type_counts[workflow_type] = type_counts.get(workflow_type, 0) + 1
        
        return {
            'total_workflows': total_workflows,
            'active_workflows': active_count,
            'completed_workflows': completed_count,
            'failed_workflows': failed_count,
            'success_rate': success_rate,
            'workflows_by_type': type_counts,
            'supported_workflow_types': [wt.value for wt in WorkflowType]
        }
    
    def _register_workflow(self, workflow_id: str, workflow_type: WorkflowType,
                          state_manager: StateManager, graph: WorkflowGraph) -> None:
        """Register a new workflow for tracking."""
        self._active_workflows[workflow_id] = {
            'workflow_id': workflow_id,
            'workflow_type': workflow_type,
            'state_manager': state_manager,
            'graph': graph,
            'created_at': datetime.now().isoformat()
        }
        
        logger.debug(f"Registered workflow {workflow_id} of type {workflow_type.value}")
    
    def _execute_workflow_async(self, workflow_id: str, initial_state: Dict[str, Any]) -> None:
        """Execute workflow asynchronously (placeholder for async execution)."""
        # In a real implementation, this would use threading or async/await
        # For now, we'll execute synchronously but simulate async behavior
        
        import threading
        
        def execute_workflow():
            try:
                workflow_info = self._active_workflows[workflow_id]
                graph = workflow_info['graph']
                state_manager = workflow_info['state_manager']
                
                # Update state to running
                state_manager.update_state({
                    'status': 'running',
                    'started_at': datetime.now().isoformat()
                })
                
                # Execute the workflow graph
                result = graph.execute(initial_state)
                
                # Update state based on result
                if result.success:
                    state_manager.complete_workflow(result.final_state)
                    logger.info(f"Workflow {workflow_id} completed successfully")
                else:
                    state_manager.fail_workflow(result.message)
                    logger.error(f"Workflow {workflow_id} failed: {result.message}")
                
                # Move to history
                self._move_workflow_to_history(workflow_id)
                
            except Exception as e:
                logger.error(f"Error executing workflow {workflow_id}: {e}")
                
                # Update state to failed
                if workflow_id in self._active_workflows:
                    workflow_info = self._active_workflows[workflow_id]
                    state_manager = workflow_info['state_manager']
                    state_manager.fail_workflow(str(e))
                    self._move_workflow_to_history(workflow_id)
        
        # Start execution in a separate thread
        thread = threading.Thread(target=execute_workflow, daemon=True)
        thread.start()
    
    def _move_workflow_to_history(self, workflow_id: str) -> None:
        """Move a workflow from active to history."""
        if workflow_id in self._active_workflows:
            workflow_info = self._active_workflows.pop(workflow_id)
            state_manager = workflow_info['state_manager']
            
            # Create history entry
            history_entry = {
                'workflow_id': workflow_id,
                'workflow_type': workflow_info['workflow_type'],
                'status': state_manager.get_status().value,
                'created_at': workflow_info['created_at'],
                'completed_at': datetime.now().isoformat(),
                'execution_time': state_manager.get_execution_time(),
                'final_state': state_manager.get_workflow_summary()
            }
            
            self._workflow_history.append(history_entry)
            
            # Limit history size
            max_history = 1000
            if len(self._workflow_history) > max_history:
                self._workflow_history = self._workflow_history[-max_history:]
    
    def _get_file_type(self, file_path: str) -> str:
        """Get file type from file path."""
        import os
        return os.path.splitext(file_path)[1].lower().lstrip('.')
    
    def shutdown(self) -> None:
        """Shutdown the workflow manager and clean up resources."""
        logger.info("Shutting down enhanced workflow manager")
        
        # Cancel all active workflows
        active_workflow_ids = list(self._active_workflows.keys())
        for workflow_id in active_workflow_ids:
            self.cancel_workflow(workflow_id)
        
        logger.info("Enhanced workflow manager shutdown complete")


# Convenience functions for creating workflow managers

def create_enhanced_workflow_manager() -> EnhancedWorkflowManager:
    """Create an enhanced workflow manager with default configuration.
    
    Returns:
        EnhancedWorkflowManager instance
    """
    return EnhancedWorkflowManager()


def create_medical_workflow_manager() -> EnhancedWorkflowManager:
    """Create a workflow manager optimized for medical document processing.
    
    Returns:
        EnhancedWorkflowManager with medical-specific configuration
    """
    node_factory = create_medical_workflow_factory()
    
    return EnhancedWorkflowManager(
        node_factory=node_factory
    )


# Global workflow manager instance
_enhanced_workflow_manager = None


def get_enhanced_workflow_manager() -> EnhancedWorkflowManager:
    """Get the global enhanced workflow manager instance.
    
    Returns:
        Global EnhancedWorkflowManager instance
    """
    global _enhanced_workflow_manager
    if _enhanced_workflow_manager is None:
        _enhanced_workflow_manager = create_medical_workflow_manager()
    return _enhanced_workflow_manager


def shutdown_enhanced_workflow_manager():
    """Shutdown the global enhanced workflow manager."""
    global _enhanced_workflow_manager
    if _enhanced_workflow_manager:
        _enhanced_workflow_manager.shutdown()
        _enhanced_workflow_manager = None