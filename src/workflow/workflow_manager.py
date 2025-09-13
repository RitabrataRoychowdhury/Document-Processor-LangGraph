"""Workflow manager for coordinating document processing workflows using command pattern."""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import threading
import queue
import time
import logging

from src.models.document import Document, ProcessingJob
from src.storage.document_storage import DocumentStorage
from src.commands import Command, CommandResult, CommandStatus
from src.commands.ingest_command import IngestCommand
from src.commands.ner_command import NERCommand
from src.commands.kg_populate_command import KGPopulateCommand
from src.factories.processor_factory import ProcessorFactory
from src.strategies.embedding_strategy import LocalEmbeddingStrategy
from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository
from src.utils.error_handling import WorkflowError, handle_errors

logger = logging.getLogger(__name__)


class WorkflowManager:
    """Manages document processing workflows using command pattern."""
    
    def __init__(self, storage: Optional[DocumentStorage] = None,
                 processor_factory: Optional[ProcessorFactory] = None,
                 kg_repository: Optional[KnowledgeGraphRepository] = None):
        self.storage = storage or DocumentStorage()
        self.processor_factory = processor_factory or ProcessorFactory()
        from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
        self.kg_repository = kg_repository or SQLiteKnowledgeGraphRepository()
        self.embedding_strategy = LocalEmbeddingStrategy()
        
        self.job_queue = queue.Queue()
        self.active_jobs = {}
        self.command_history = {}
        self.worker_thread = None
        self.running = False
        
    def start(self):
        """Start the workflow manager and worker thread."""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.info("Workflow manager started")
    
    def stop(self):
        """Stop the workflow manager."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Workflow manager stopped")
    
    def shutdown(self):
        """Alias for stop() method for compatibility."""
        self.stop()
    
    def submit_document_for_processing(self, file_path: str, api_key: str = None) -> str:
        """Submit a document for processing using command pattern and return job ID."""
        try:
            # Create processing job
            job_id = str(uuid.uuid4())
            processing_job = ProcessingJob(
                job_id=job_id,
                document_id=None,  # Will be set after ingestion
                status="queued",
                current_step="queued"
            )
            
            # Add to job queue with commands to execute
            job_data = {
                'job_id': job_id,
                'file_path': file_path,
                'api_key': api_key,
                'submitted_at': datetime.now(),
                'commands': ['ingest', 'ner', 'kg_populate']
            }
            
            self.job_queue.put(job_data)
            logger.info(f"Submitted file {file_path} for processing with job {job_id}")
            
            return job_id
            
        except Exception as e:
            logger.error(f"Error submitting document for processing: {e}")
            raise
    
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
            'running': self.running,
            'active_job_ids': list(self.active_jobs.keys())
        }
    
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


# Global workflow manager instance
_workflow_manager = None


def get_workflow_manager() -> WorkflowManager:
    """Get the global workflow manager instance."""
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