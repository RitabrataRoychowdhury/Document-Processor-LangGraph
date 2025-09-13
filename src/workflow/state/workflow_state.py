"""Base workflow state management implementation."""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.base.state_manager import StateManager, StateStatus
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class WorkflowState(StateManager):
    """Base workflow state manager for general workflow operations.
    
    Implements Single Responsibility Principle - manages general workflow state.
    """
    
    def __init__(self, state_id: str = None, correlation_id: str = None):
        super().__init__(state_id, correlation_id)
        self._workflow_type = "general"
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None
    
    def initialize_state(self, initial_data: Dict[str, Any]) -> None:
        """Initialize the workflow state with basic workflow data."""
        required_keys = self.get_required_keys()
        
        # Validate that all required keys are present
        missing_keys = [key for key in required_keys if key not in initial_data]
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")
        
        # Set initial state
        self._current_state = {
            'workflow_id': initial_data.get('workflow_id', self.state_id),
            'correlation_id': self.correlation_id,
            'workflow_type': self._workflow_type,
            'status': StateStatus.INITIALIZED.value,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'progress_percentage': 0,
            'current_step': 'initialized',
            'error_message': None,
            'retry_count': 0,
            **initial_data
        }
        
        self._start_time = datetime.now()
        self.set_status(StateStatus.ACTIVE)
        
        logger.info(f"Initialized workflow state {self.state_id} [correlation_id: {self.correlation_id}]")
    
    def validate_state(self, state_data: Dict[str, Any]) -> bool:
        """Validate workflow state data."""
        required_keys = self.get_required_keys()
        
        # Check required keys
        for key in required_keys:
            if key not in state_data:
                logger.error(f"Missing required key '{key}' in workflow state")
                return False
        
        # Validate progress percentage
        progress = state_data.get('progress_percentage', 0)
        if not isinstance(progress, (int, float)) or progress < 0 or progress > 100:
            logger.error(f"Invalid progress percentage: {progress}")
            return False
        
        # Validate retry count
        retry_count = state_data.get('retry_count', 0)
        if not isinstance(retry_count, int) or retry_count < 0:
            logger.error(f"Invalid retry count: {retry_count}")
            return False
        
        return True
    
    def get_required_keys(self) -> List[str]:
        """Get list of required state keys for workflow state."""
        return [
            'workflow_id',
            'correlation_id',
            'workflow_type',
            'status',
            'created_at',
            'updated_at',
            'progress_percentage',
            'current_step'
        ]
    
    def start_workflow(self) -> None:
        """Mark workflow as started."""
        self.update_state({
            'status': StateStatus.ACTIVE.value,
            'current_step': 'started',
            'progress_percentage': 5
        })
        self._start_time = datetime.now()
        self.set_status(StateStatus.ACTIVE)
        
        logger.info(f"Started workflow {self.state_id}")
    
    def complete_workflow(self, final_data: Dict[str, Any] = None) -> None:
        """Mark workflow as completed."""
        completion_data = {
            'status': StateStatus.COMPLETED.value,
            'current_step': 'completed',
            'progress_percentage': 100,
            'completed_at': datetime.now().isoformat()
        }
        
        if final_data:
            completion_data.update(final_data)
        
        self.update_state(completion_data)
        self._end_time = datetime.now()
        self.set_status(StateStatus.COMPLETED)
        
        execution_time = self.get_execution_time()
        logger.info(f"Completed workflow {self.state_id} in {execution_time:.2f}s")
    
    def fail_workflow(self, error_message: str, error_data: Dict[str, Any] = None) -> None:
        """Mark workflow as failed."""
        failure_data = {
            'status': StateStatus.FAILED.value,
            'current_step': 'failed',
            'error_message': error_message,
            'failed_at': datetime.now().isoformat()
        }
        
        if error_data:
            failure_data.update(error_data)
        
        self.update_state(failure_data)
        self._end_time = datetime.now()
        self.set_status(StateStatus.FAILED)
        
        logger.error(f"Failed workflow {self.state_id}: {error_message}")
    
    def update_progress(self, step: str, percentage: int, data: Dict[str, Any] = None) -> None:
        """Update workflow progress."""
        progress_data = {
            'current_step': step,
            'progress_percentage': max(0, min(100, percentage)),
            'updated_at': datetime.now().isoformat()
        }
        
        if data:
            progress_data.update(data)
        
        self.update_state(progress_data, create_snapshot=False)
        
        logger.debug(f"Workflow {self.state_id} progress: {step} ({percentage}%)")
    
    def increment_retry_count(self) -> int:
        """Increment retry count and return new value."""
        current_count = self.get_value('retry_count', 0)
        new_count = current_count + 1
        self.set_value('retry_count', new_count)
        
        logger.debug(f"Incremented retry count for workflow {self.state_id} to {new_count}")
        return new_count
    
    def get_execution_time(self) -> float:
        """Get workflow execution time in seconds."""
        if not self._start_time:
            return 0.0
        
        end_time = self._end_time or datetime.now()
        return (end_time - self._start_time).total_seconds()
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get a summary of the workflow state."""
        return {
            'workflow_id': self.get_value('workflow_id'),
            'workflow_type': self.get_value('workflow_type'),
            'status': self.get_status().value,
            'current_step': self.get_value('current_step'),
            'progress_percentage': self.get_value('progress_percentage'),
            'execution_time': self.get_execution_time(),
            'retry_count': self.get_value('retry_count'),
            'error_message': self.get_value('error_message'),
            'created_at': self.get_value('created_at'),
            'updated_at': self.get_value('updated_at'),
            'correlation_id': self.correlation_id
        }
    
    def is_retryable(self, max_retries: int = 3) -> bool:
        """Check if workflow can be retried."""
        if self.is_complete():
            return False
        
        retry_count = self.get_value('retry_count', 0)
        return retry_count < max_retries
    
    def reset_for_retry(self) -> None:
        """Reset workflow state for retry."""
        self.update_state({
            'status': StateStatus.ACTIVE.value,
            'current_step': 'retrying',
            'error_message': None,
            'updated_at': datetime.now().isoformat()
        })
        self.set_status(StateStatus.ACTIVE)
        
        logger.info(f"Reset workflow {self.state_id} for retry")


class WorkflowStateFactory:
    """Factory for creating workflow state managers.
    
    Implements Factory Pattern for state creation.
    """
    
    @staticmethod
    def create_workflow_state(workflow_type: str = "general", 
                            state_id: str = None,
                            correlation_id: str = None) -> WorkflowState:
        """Create a workflow state manager.
        
        Args:
            workflow_type: Type of workflow
            state_id: Optional state ID
            correlation_id: Optional correlation ID
            
        Returns:
            WorkflowState instance
        """
        if workflow_type == "document":
            from src.workflow.state.document_state import DocumentState
            return DocumentState(state_id, correlation_id)
        elif workflow_type == "template":
            from src.workflow.state.template_state import TemplateState
            return TemplateState(state_id, correlation_id)
        else:
            return WorkflowState(state_id, correlation_id)
    
    @staticmethod
    def get_supported_types() -> List[str]:
        """Get list of supported workflow types."""
        return ["general", "document", "template"]