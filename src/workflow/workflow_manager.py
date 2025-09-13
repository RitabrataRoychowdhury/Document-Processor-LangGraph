"""Refactored workflow manager using graph-based architecture with proper design patterns."""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Type
import threading
import queue
import time

from src.models.document import Document, ProcessingJob
from src.storage.document_storage import DocumentStorage
from src.commands import Command, CommandResult, CommandStatus
from src.commands.ingest_command import IngestCommand
from src.commands.ner_command import NERCommand
from src.commands.kg_populate_command import KGPopulateCommand
from src.commands.template_command import TemplateCommand
from src.factories.processor_factory import ProcessorFactory
from src.strategies.embedding_strategy import LocalEmbeddingStrategy
from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository
from src.utils.error_handling import WorkflowError, handle_errors

# Import new graph-based components
from src.workflow.base.workflow_graph import WorkflowGraph, GraphResult, LoggingGraphObserver, MetricsGraphObserver
from src.workflow.base.workflow_node import WorkflowNode, LoggingNodeObserver, MetricsNodeObserver
from src.workflow.base.state_manager import StateManager
from src.workflow.state.workflow_state import WorkflowStateFactory
from src.workflow.graphs.document_processing_graph import DocumentProcessingGraph
from src.workflow.graphs.qme_generation_graph import QMEGenerationGraph
from src.workflow.graphs.knowledge_graph_population_graph import KnowledgeGraphPopulationGraph
from src.workflow.factories.node_factory import NodeFactory
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class RefactoredWorkflowManager:
    """Refactored workflow manager using graph-based architecture.
    
    Implements the following design patterns:
    - Factory Pattern: For creating graphs and nodes
    - Strategy Pattern: For different workflow execution strategies
    - Observer Pattern: For monitoring workflow progress
    - Command Pattern: For backward compatibility with existing commands
    """
    
    def __init__(self, storage: Optional[DocumentStorage] = None,
                 processor_factory: Optional[ProcessorFactory] = None,
                 kg_repository: Optional[KnowledgeGraphRepository] = None,
                 node_factory: Optional[NodeFactory] = None):
        # Core dependencies
        self.storage = storage or DocumentStorage()
        self.processor_factory = processor_factory or ProcessorFactory()
        from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
        self.kg_repository = kg_repository or SQLiteKnowledgeGraphRepository()
        self.embedding_strategy = LocalEmbeddingStrategy()
        from src.workflow.factories.node_factory import StandardNodeFactory
        self.node_factory = node_factory or StandardNodeFactory(
            processor_factory=self.processor_factory,
            embedding_strategy=self.embedding_strategy,
            kg_repository=self.kg_repository
        )
        
        # Graph-based workflow management
        self.active_graphs: Dict[str, WorkflowGraph] = {}
        self.graph_results: Dict[str, GraphResult] = {}
        self.state_managers: Dict[str, StateManager] = {}
        
        # Observers for monitoring
        self.graph_observers = [LoggingGraphObserver(), MetricsGraphObserver()]
        self.node_observers = [LoggingNodeObserver(), MetricsNodeObserver()]
        
        # Legacy support
        self.job_queue = queue.Queue()
        self.active_jobs = {}
        self.command_history = {}
        self.worker_thread = None
        self.running = False
        
        # Performance monitoring
        self.execution_metrics = {
            'graphs_executed': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'average_execution_time': 0.0
        }
        
    def start(self):
        """Start the workflow manager and worker thread."""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.info("Refactored workflow manager started with graph-based architecture")
    
    def execute_document_processing_graph(self, file_path: str, 
                                        correlation_id: str = None) -> GraphResult:
        """Execute document processing using graph-based architecture.
        
        Args:
            file_path: Path to document to process
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            GraphResult with execution outcome
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        graph_id = None
        try:
            # Create document processing graph
            graph = DocumentProcessingGraph(correlation_id=correlation_id)
            graph_id = graph.graph_id
            
            # Add observers
            for observer in self.graph_observers:
                graph.add_observer(observer)
            
            # Create state manager
            state_manager = WorkflowStateFactory.create_workflow_state(
                "document", correlation_id=correlation_id
            )
            
            # Initialize state with all required keys
            initial_state = {
                'workflow_id': correlation_id,
                'correlation_id': correlation_id,
                'workflow_type': 'document_processing',
                'status': 'initialized',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'progress_percentage': 0,
                'current_step': 'initialized',
                'file_path': file_path,
                'processor_factory': self.processor_factory,
                'embedding_strategy': self.embedding_strategy,
                'kg_repository': self.kg_repository,
                'storage': self.storage
            }
            
            state_manager.initialize_state(initial_state)
            
            # Store references
            self.active_graphs[graph_id] = graph
            self.state_managers[graph_id] = state_manager
            
            # Execute graph
            logger.info(f"Starting document processing graph execution for {file_path} "
                       f"[correlation_id: {correlation_id}]")
            
            result = graph.execute(state_manager.get_state())
            
            # Store result and update metrics
            self.graph_results[graph_id] = result
            self._update_execution_metrics(result)
            
            # Update state manager based on result
            if result.success:
                state_manager.complete_workflow(result.final_state)
                logger.info(f"Document processing graph completed successfully "
                           f"[correlation_id: {correlation_id}]")
            else:
                state_manager.fail_workflow(result.message)
                logger.error(f"Document processing graph failed: {result.message} "
                           f"[correlation_id: {correlation_id}]")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing document processing graph: {e} "
                        f"[correlation_id: {correlation_id}]")
            
            # Create failure result
            result = GraphResult.failure_result(
                f"Graph execution error: {str(e)}",
                execution_time=0.0
            )
            result.correlation_id = correlation_id
            
            self._update_execution_metrics(result)
            return result
        
        finally:
            # Cleanup
            if graph_id in self.active_graphs:
                del self.active_graphs[graph_id]
    
    def execute_qme_generation_graph(self, patient_document_id: str,
                                   template_type: str = "qme_report",
                                   correlation_id: str = None) -> GraphResult:
        """Execute QME template generation using graph-based architecture.
        
        Args:
            patient_document_id: ID of patient document
            template_type: Type of template to generate
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            GraphResult with execution outcome
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        graph_id = None
        try:
            # Create QME generation graph
            graph = QMEGenerationGraph(correlation_id=correlation_id)
            graph_id = graph.graph_id
            
            # Add observers
            for observer in self.graph_observers:
                graph.add_observer(observer)
            
            # Create state manager
            state_manager = WorkflowStateFactory.create_workflow_state(
                "template", correlation_id=correlation_id
            )
            
            # Initialize state with all required keys
            initial_state = {
                'workflow_id': correlation_id,
                'correlation_id': correlation_id,
                'workflow_type': 'qme_generation',
                'status': 'initialized',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'progress_percentage': 0,
                'current_step': 'initialized',
                'patient_document_id': patient_document_id,
                'template_type': template_type,
                'kg_repository': self.kg_repository,
                'storage': self.storage
            }
            
            state_manager.initialize_state(initial_state)
            
            # Store references
            self.active_graphs[graph_id] = graph
            self.state_managers[graph_id] = state_manager
            
            # Execute graph
            logger.info(f"Starting QME generation graph execution for document {patient_document_id} "
                       f"[correlation_id: {correlation_id}]")
            
            result = graph.execute(state_manager.get_state())
            
            # Store result and update metrics
            self.graph_results[graph_id] = result
            self._update_execution_metrics(result)
            
            # Update state manager based on result
            if result.success:
                state_manager.complete_workflow(result.final_state)
                logger.info(f"QME generation graph completed successfully "
                           f"[correlation_id: {correlation_id}]")
            else:
                state_manager.fail_workflow(result.message)
                logger.error(f"QME generation graph failed: {result.message} "
                           f"[correlation_id: {correlation_id}]")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing QME generation graph: {e} "
                        f"[correlation_id: {correlation_id}]")
            
            # Create failure result
            result = GraphResult.failure_result(
                f"Graph execution error: {str(e)}",
                execution_time=0.0
            )
            result.correlation_id = correlation_id
            
            self._update_execution_metrics(result)
            return result
        
        finally:
            # Cleanup
            if graph_id in self.active_graphs:
                del self.active_graphs[graph_id]
    
    def execute_knowledge_graph_population(self, document_id: str,
                                         correlation_id: str = None) -> GraphResult:
        """Execute knowledge graph population using graph-based architecture.
        
        Args:
            document_id: ID of document to populate KG from
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            GraphResult with execution outcome
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        graph_id = None
        try:
            # Create KG population graph
            graph = KnowledgeGraphPopulationGraph(correlation_id=correlation_id)
            graph_id = graph.graph_id
            
            # Add observers
            for observer in self.graph_observers:
                graph.add_observer(observer)
            
            # Create state manager
            state_manager = WorkflowStateFactory.create_workflow_state(
                "document", correlation_id=correlation_id
            )
            
            # Initialize state with all required keys
            initial_state = {
                'workflow_id': correlation_id,
                'correlation_id': correlation_id,
                'workflow_type': 'kg_population',
                'status': 'initialized',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'progress_percentage': 0,
                'current_step': 'initialized',
                'document_id': document_id,
                'kg_repository': self.kg_repository,
                'storage': self.storage
            }
            
            state_manager.initialize_state(initial_state)
            
            # Store references
            self.active_graphs[graph_id] = graph
            self.state_managers[graph_id] = state_manager
            
            # Execute graph
            logger.info(f"Starting KG population graph execution for document {document_id} "
                       f"[correlation_id: {correlation_id}]")
            
            result = graph.execute(state_manager.get_state())
            
            # Store result and update metrics
            self.graph_results[graph_id] = result
            self._update_execution_metrics(result)
            
            # Update state manager based on result
            if result.success:
                state_manager.complete_workflow(result.final_state)
                logger.info(f"KG population graph completed successfully "
                           f"[correlation_id: {correlation_id}]")
            else:
                state_manager.fail_workflow(result.message)
                logger.error(f"KG population graph failed: {result.message} "
                           f"[correlation_id: {correlation_id}]")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing KG population graph: {e} "
                        f"[correlation_id: {correlation_id}]")
            
            # Create failure result
            result = GraphResult.failure_result(
                f"Graph execution error: {str(e)}",
                execution_time=0.0
            )
            result.correlation_id = correlation_id
            
            self._update_execution_metrics(result)
            return result
        
        finally:
            # Cleanup
            if graph_id in self.active_graphs:
                del self.active_graphs[graph_id]
    
    def stop(self):
        """Stop the workflow manager."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Workflow manager stopped")
    
    def shutdown(self):
        """Alias for stop() method for compatibility."""
        self.stop()
    
    def submit_document_for_processing(self, file_path: str, api_key: str = None, 
                                     use_graph_execution: bool = True) -> str:
        """Submit a document for processing with option for graph-based or legacy execution.
        
        Args:
            file_path: Path to document to process
            api_key: Optional API key (for backward compatibility)
            use_graph_execution: Whether to use new graph-based execution
            
        Returns:
            Job ID for tracking
        """
        try:
            job_id = str(uuid.uuid4())
            
            if use_graph_execution:
                # Use new graph-based execution
                logger.info(f"Submitting document {file_path} for graph-based processing with job {job_id}")
                
                # Execute graph asynchronously in background
                def execute_graph():
                    try:
                        result = self.execute_document_processing_graph(
                            file_path=file_path,
                            correlation_id=job_id
                        )
                        
                        # Update legacy job tracking for compatibility
                        if result.success:
                            self._update_legacy_job_status(job_id, "completed", None)
                        else:
                            self._update_legacy_job_status(job_id, "failed", result.message)
                            
                    except Exception as e:
                        logger.error(f"Graph execution failed for job {job_id}: {e}")
                        self._update_legacy_job_status(job_id, "failed", str(e))
                
                # Start background execution
                graph_thread = threading.Thread(target=execute_graph, daemon=True)
                graph_thread.start()
                
                # Create legacy job record for compatibility
                processing_job = ProcessingJob(
                    job_id=job_id,
                    document_id=None,
                    status="processing",
                    current_step="graph_execution"
                )
                self.storage.create_processing_job(processing_job)
                
            else:
                # Use legacy command-based execution
                logger.info(f"Submitting document {file_path} for legacy processing with job {job_id}")
                
                processing_job = ProcessingJob(
                    job_id=job_id,
                    document_id=None,
                    status="queued",
                    current_step="queued"
                )
                
                job_data = {
                    'job_id': job_id,
                    'file_path': file_path,
                    'api_key': api_key,
                    'submitted_at': datetime.now(),
                    'commands': ['ingest', 'ner', 'kg_populate']
                }
                
                self.job_queue.put(job_data)
                self.storage.create_processing_job(processing_job)
            
            logger.info(f"Submitted file {file_path} for processing with job {job_id} "
                       f"(graph_execution: {use_graph_execution})")
            
            return job_id
            
        except Exception as e:
            logger.error(f"Error submitting document for processing: {e}")
            raise
    
    def submit_qme_generation(self, patient_document_id: str, 
                            template_type: str = "qme_report") -> str:
        """Submit QME template generation using graph-based execution.
        
        Args:
            patient_document_id: ID of patient document
            template_type: Type of template to generate
            
        Returns:
            Job ID for tracking
        """
        try:
            job_id = str(uuid.uuid4())
            
            logger.info(f"Submitting QME generation for document {patient_document_id} with job {job_id}")
            
            # Execute graph asynchronously in background
            def execute_graph():
                try:
                    result = self.execute_qme_generation_graph(
                        patient_document_id=patient_document_id,
                        template_type=template_type,
                        correlation_id=job_id
                    )
                    
                    # Update legacy job tracking for compatibility
                    if result.success:
                        self._update_legacy_job_status(job_id, "completed", None)
                    else:
                        self._update_legacy_job_status(job_id, "failed", result.message)
                        
                except Exception as e:
                    logger.error(f"QME generation failed for job {job_id}: {e}")
                    self._update_legacy_job_status(job_id, "failed", str(e))
            
            # Start background execution
            graph_thread = threading.Thread(target=execute_graph, daemon=True)
            graph_thread.start()
            
            # Create legacy job record for compatibility
            processing_job = ProcessingJob(
                job_id=job_id,
                document_id=patient_document_id,
                status="processing",
                current_step="qme_generation"
            )
            self.storage.create_processing_job(processing_job)
            
            return job_id
            
        except Exception as e:
            logger.error(f"Error submitting QME generation: {e}")
            raise
    
    def _update_legacy_job_status(self, job_id: str, status: str, error_message: str = None) -> None:
        """Update legacy job status for backward compatibility."""
        try:
            update_data = {
                'status': status,
                'completed_at': datetime.now()
            }
            
            if error_message:
                update_data['error_message'] = error_message
            
            self.storage.update_processing_job(job_id, **update_data)
            
        except Exception as e:
            logger.error(f"Error updating legacy job status: {e}")
    
    def get_job_status(self, job_id: str) -> Optional[ProcessingJob]:
        """Get the current status of a processing job."""
        return self.storage.get_processing_job(job_id)
    
    def get_document_processing_status(self, document_id: str) -> Optional[ProcessingJob]:
        """Get the latest processing job for a document."""
        jobs = self.storage.list_processing_jobs(document_id)
        return jobs[0] if jobs else None
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a processing job if it's still queued."""
        try:
            job = self.storage.get_processing_job(job_id)
            if job and job.status in ['queued', 'pending']:
                self.storage.update_processing_job(
                    job_id,
                    status="cancelled",
                    error_message="Job cancelled by user",
                    completed_at=datetime.now()
                )
                logger.info(f"Cancelled job {job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {e}")
            return False
    
    def _worker_loop(self):
        """Main worker loop for processing jobs."""
        logger.info("Workflow worker thread started")
        
        while self.running:
            try:
                # Get next job from queue (with timeout to allow checking running flag)
                try:
                    job_data = self.job_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                job_id = job_data['job_id']
                
                # Check if job was cancelled
                job = self.storage.get_processing_job(job_id)
                if not job or job.status == 'cancelled':
                    logger.info(f"Skipping cancelled job {job_id}")
                    continue
                
                # Process the job
                self._process_job(job_data)
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(1)  # Brief pause before continuing
        
        logger.info("Workflow worker thread stopped")
    
    def _process_job(self, job_data: Dict[str, Any]):
        """Process a single job using command pattern."""
        job_id = job_data['job_id']
        file_path = job_data.get('file_path')
        commands_to_execute = job_data.get('commands', [])
        
        try:
            logger.info(f"Starting command-based processing for job {job_id}")
            self.active_jobs[job_id] = job_data
            
            # Create processing job record
            processing_job = ProcessingJob(
                job_id=job_id,
                document_id=None,  # Will be set after ingestion
                status="processing",
                current_step="starting"
            )
            self.storage.create_processing_job(processing_job)
            
            document_id = None
            
            # Execute commands in sequence
            for i, command_name in enumerate(commands_to_execute):
                try:
                    logger.info(f"Executing command {command_name} for job {job_id} ({i+1}/{len(commands_to_execute)})")
                    
                    # Update job status
                    self.storage.update_processing_job(
                        job_id,
                        current_step=command_name
                    )
                    
                    # Create and execute command
                    command = self._create_command(command_name, file_path, document_id)
                    result = self._execute_command_with_logging(command)
                    
                    # Store command result
                    self.command_history[f"{job_id}_{command_name}"] = result
                    
                    if not result.success:
                        raise Exception(f"Command {command_name} failed: {result.message}")
                    
                    # Extract document_id from ingest command result
                    if command_name == 'ingest' and 'document_id' in result.data:
                        document_id = result.data['document_id']
                        # Update processing job with document_id
                        self.storage.update_processing_job(job_id, document_id=document_id)
                    
                    logger.info(f"Successfully completed command {command_name} for job {job_id}")
                    
                except Exception as cmd_error:
                    logger.error(f"Command {command_name} failed for job {job_id}: {cmd_error}")
                    raise cmd_error
            
            # Mark job as completed
            self.storage.update_processing_job(
                job_id,
                status="completed",
                current_step="completed",
                completed_at=datetime.now()
            )
            
            if document_id:
                self.storage.update_document(document_id, {
                    'processing_status': 'completed',
                    'updated_at': datetime.now()
                })
            
            logger.info(f"Successfully completed all commands for job {job_id}")
            
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
            
            # Update job with error
            try:
                self.storage.update_processing_job(
                    job_id,
                    status="failed",
                    error_message=str(e),
                    completed_at=datetime.now()
                )
                
                if document_id:
                    self.storage.update_document(document_id, {
                        'processing_status': 'failed',
                        'updated_at': datetime.now()
                    })
                
            except Exception as update_error:
                logger.error(f"Error updating job status: {update_error}")
        
        finally:
            # Remove from active jobs
            self.active_jobs.pop(job_id, None)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue and processing status."""
        return {
            'queue_size': self.job_queue.qsize(),
            'active_jobs': len(self.active_jobs),
            'active_graphs': len(self.active_graphs),
            'running': self.running,
            'active_job_ids': list(self.active_jobs.keys()),
            'active_graph_ids': list(self.active_graphs.keys()),
            'execution_metrics': self.execution_metrics.copy()
        }
    
    def get_graph_status(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific graph execution.
        
        Args:
            graph_id: ID of graph to check
            
        Returns:
            Graph status information or None if not found
        """
        if graph_id in self.active_graphs:
            graph = self.active_graphs[graph_id]
            state_manager = self.state_managers.get(graph_id)
            
            status = {
                'graph_id': graph_id,
                'graph_type': graph.__class__.__name__,
                'status': 'running',
                'graph_info': graph.get_graph_info()
            }
            
            if state_manager:
                status['state_info'] = state_manager.get_state_info()
                status['workflow_summary'] = state_manager.get_workflow_summary()
            
            return status
        
        elif graph_id in self.graph_results:
            result = self.graph_results[graph_id]
            return {
                'graph_id': graph_id,
                'status': 'completed' if result.success else 'failed',
                'result': {
                    'success': result.success,
                    'message': result.message,
                    'execution_time': result.execution_time,
                    'nodes_executed': result.nodes_executed
                }
            }
        
        return None
    
    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get workflow execution metrics."""
        metrics = self.execution_metrics.copy()
        
        # Add observer metrics
        for observer in self.graph_observers:
            if isinstance(observer, MetricsGraphObserver):
                graph_metrics = observer.get_metrics()
                metrics['graph_executions'] = len(graph_metrics)
                if graph_metrics:
                    successful = sum(1 for _, result in graph_metrics if result.success)
                    metrics['graph_success_rate'] = successful / len(graph_metrics)
        
        for observer in self.node_observers:
            if isinstance(observer, MetricsNodeObserver):
                node_metrics = observer.get_metrics()
                metrics['node_executions'] = len(node_metrics)
        
        return metrics
    
    def _update_execution_metrics(self, result: GraphResult) -> None:
        """Update execution metrics with graph result."""
        self.execution_metrics['graphs_executed'] += 1
        
        if result.success:
            self.execution_metrics['successful_executions'] += 1
        else:
            self.execution_metrics['failed_executions'] += 1
        
        # Update average execution time
        total_graphs = self.execution_metrics['graphs_executed']
        current_avg = self.execution_metrics['average_execution_time']
        new_avg = ((current_avg * (total_graphs - 1)) + result.execution_time) / total_graphs
        self.execution_metrics['average_execution_time'] = new_avg
    
    def clear_completed_graphs(self, max_age_hours: int = 24) -> int:
        """Clear completed graph results older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours for keeping results
            
        Returns:
            Number of results cleared
        """
        current_time = datetime.now()
        cleared_count = 0
        
        # This is a simplified implementation - in practice you'd want to track timestamps
        # For now, just clear all completed results if we have too many
        if len(self.graph_results) > 100:
            self.graph_results.clear()
            cleared_count = len(self.graph_results)
            logger.info(f"Cleared {cleared_count} completed graph results")
        
        return cleared_count
    
    def get_workflow_visualization(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow visualization data for a graph.
        
        Args:
            graph_id: ID of graph to visualize
            
        Returns:
            Visualization data or None if not found
        """
        if graph_id in self.active_graphs:
            graph = self.active_graphs[graph_id]
            return {
                'graph_id': graph_id,
                'graph_type': graph.__class__.__name__,
                'nodes': graph.get_graph_info()['nodes'],
                'edges': graph.edges,
                'entry_points': graph.entry_points,
                'exit_points': list(graph.exit_points)
            }
        
        return None
    
    def get_recent_jobs(self, limit: int = 10) -> List[ProcessingJob]:
        """Get recent processing jobs."""
        return self.storage.list_processing_jobs()[:limit]
    
    def _create_command(self, command_name: str, file_path: str = None, document_id: str = None) -> Command:
        """Create a command instance based on command name."""
        if command_name == 'ingest':
            if not file_path:
                raise ValueError("file_path is required for ingest command")
            return IngestCommand(
                file_path=file_path,
                document_id=document_id,
                processor_factory=self.processor_factory,
                storage=self.storage
            )
        elif command_name == 'ner':
            if not document_id:
                raise ValueError("document_id is required for NER command")
            return NERCommand(
                document_id=document_id,
                embedding_strategy=self.embedding_strategy,
                storage=self.storage
            )
        elif command_name == 'kg_populate':
            if not document_id:
                raise ValueError("document_id is required for KG populate command")
            return KGPopulateCommand(
                document_id=document_id,
                kg_repository=self.kg_repository,
                storage=self.storage
            )
        else:
            raise ValueError(f"Unknown command: {command_name}")
    
    def _execute_command_with_logging(self, command: Command) -> CommandResult:
        """Execute a command with comprehensive logging."""
        command_info = command.get_command_info()
        logger.info(f"Executing command: {command_info['command_type']} (ID: {command_info['command_id']})")
        
        try:
            # Execute command with retry logic
            result = command.execute_with_retry(max_attempts=3, backoff_factor=2.0)
            
            if result.success:
                logger.info(f"Command {command_info['command_id']} completed successfully: {result.message}")
            else:
                logger.error(f"Command {command_info['command_id']} failed: {result.message}")
                if result.error:
                    logger.error(f"Command error details: {result.error}")
            
            # Log execution metrics
            if result.execution_time:
                logger.info(f"Command {command_info['command_id']} execution time: {result.execution_time:.2f}s")
            
            if result.retry_count > 0:
                logger.info(f"Command {command_info['command_id']} required {result.retry_count} retries")
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error executing command {command_info['command_id']}: {e}")
            return CommandResult.failure_result(
                message=f"Unexpected command execution error: {str(e)}",
                error=e
            )
    
    def execute_single_command(self, command: Command) -> CommandResult:
        """Execute a single command (useful for testing and manual operations)."""
        return self._execute_command_with_logging(command)
    
    def get_command_history(self, job_id: str = None) -> Dict[str, CommandResult]:
        """Get command execution history, optionally filtered by job ID."""
        if job_id:
            return {k: v for k, v in self.command_history.items() if k.startswith(job_id)}
        return self.command_history.copy()


class WorkflowManager(RefactoredWorkflowManager):
    """Backward compatibility wrapper for the refactored workflow manager.
    
    This class maintains the same interface as the original WorkflowManager
    while using the new graph-based architecture internally.
    """
    
    def __init__(self, storage: Optional[DocumentStorage] = None,
                 processor_factory: Optional[ProcessorFactory] = None,
                 kg_repository: Optional[KnowledgeGraphRepository] = None):
        super().__init__(storage, processor_factory, kg_repository)
        logger.info("Initialized WorkflowManager with backward compatibility wrapper")
    
    def submit_document_for_processing(self, file_path: str, api_key: str = None) -> str:
        """Submit document for processing (backward compatible interface)."""
        # Default to graph-based execution for better performance
        return super().submit_document_for_processing(file_path, api_key, use_graph_execution=True)


# Global workflow manager instance
_workflow_manager = None


def get_workflow_manager() -> WorkflowManager:
    """Get the global workflow manager instance."""
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = WorkflowManager()
        _workflow_manager.start()
    return _workflow_manager


def get_refactored_workflow_manager() -> RefactoredWorkflowManager:
    """Get the refactored workflow manager instance directly."""
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = WorkflowManager()
        _workflow_manager.start()
    return _workflow_manager


def shutdown_workflow_manager():
    """Shutdown the global workflow manager."""
    global _workflow_manager
    if _workflow_manager:
        _workflow_manager.stop()
        _workflow_manager = None