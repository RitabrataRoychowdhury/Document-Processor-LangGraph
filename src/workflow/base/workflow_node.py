"""Abstract base class for workflow nodes following LLD principles."""

import uuid
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Type
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class NodeStatus(Enum):
    """Status of a workflow node execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class NodeResult:
    """Result of a workflow node execution."""
    success: bool
    status: NodeStatus
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None
    execution_time: float = 0.0
    retry_count: int = 0
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    @classmethod
    def success_result(cls, message: str, data: Dict[str, Any] = None, 
                      execution_time: float = 0.0) -> 'NodeResult':
        """Create a successful result."""
        return cls(
            success=True,
            status=NodeStatus.COMPLETED,
            message=message,
            data=data or {},
            execution_time=execution_time
        )
    
    @classmethod
    def failure_result(cls, message: str, error: Exception = None,
                      execution_time: float = 0.0) -> 'NodeResult':
        """Create a failure result."""
        return cls(
            success=False,
            status=NodeStatus.FAILED,
            message=message,
            error=error,
            execution_time=execution_time
        )


@dataclass
class NodeMetrics:
    """Metrics for node execution."""
    node_id: str
    node_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_time: float = 0.0
    memory_usage: Optional[float] = None
    retry_count: int = 0
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class WorkflowNode(ABC):
    """Abstract base class for all workflow nodes.
    
    Implements Single Responsibility Principle - each node handles one specific operation.
    Follows Open/Closed Principle - easy to extend without modifying existing nodes.
    Implements Dependency Inversion - depends on abstractions, not concretions.
    """
    
    def __init__(self, node_id: str = None, correlation_id: str = None):
        self.node_id = node_id or str(uuid.uuid4())
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.metrics = NodeMetrics(
            node_id=self.node_id,
            node_type=self.__class__.__name__,
            start_time=datetime.now(),
            correlation_id=self.correlation_id
        )
        self._observers: List['NodeObserver'] = []
    
    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> NodeResult:
        """Execute the node's primary operation.
        
        Args:
            state: Current workflow state
            
        Returns:
            NodeResult with execution outcome
        """
        pass
    
    @abstractmethod
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """Validate input state before execution.
        
        Args:
            state: Current workflow state
            
        Returns:
            True if input is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_required_inputs(self) -> List[str]:
        """Get list of required input keys from state.
        
        Returns:
            List of required state keys
        """
        pass
    
    @abstractmethod
    def get_output_keys(self) -> List[str]:
        """Get list of output keys this node adds to state.
        
        Returns:
            List of output state keys
        """
        pass
    
    def can_retry(self, error: Exception) -> bool:
        """Determine if the node can be retried after an error.
        
        Args:
            error: The exception that occurred
            
        Returns:
            True if retry is possible, False otherwise
        """
        # Default implementation - can retry for most errors except critical ones
        critical_errors = (ValueError, TypeError, AttributeError)
        return not isinstance(error, critical_errors)
    
    def execute_with_retry(self, state: Dict[str, Any], max_attempts: int = 3,
                          backoff_factor: float = 2.0) -> NodeResult:
        """Execute node with retry logic and comprehensive logging.
        
        Args:
            state: Current workflow state
            max_attempts: Maximum number of retry attempts
            backoff_factor: Exponential backoff factor
            
        Returns:
            NodeResult with execution outcome
        """
        start_time = time.time()
        self.metrics.start_time = datetime.now()
        
        logger.info(f"Starting node execution: {self.node_id} ({self.__class__.__name__}) "
                   f"[correlation_id: {self.correlation_id}]")
        
        # Notify observers of start
        self._notify_observers('start', state)
        
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                # Validate input before execution
                if not self.validate_input(state):
                    error_msg = f"Input validation failed for node {self.node_id}"
                    logger.error(f"{error_msg} [correlation_id: {self.correlation_id}]")
                    result = NodeResult.failure_result(error_msg)
                    self._notify_observers('error', state, result)
                    return result
                
                # Execute the node
                logger.debug(f"Executing node {self.node_id} (attempt {attempt + 1}/{max_attempts}) "
                           f"[correlation_id: {self.correlation_id}]")
                
                result = self.execute(state)
                result.correlation_id = self.correlation_id
                result.retry_count = attempt
                
                # Calculate execution time
                execution_time = time.time() - start_time
                result.execution_time = execution_time
                self.metrics.execution_time = execution_time
                self.metrics.end_time = datetime.now()
                self.metrics.retry_count = attempt
                
                if result.success:
                    logger.info(f"Node {self.node_id} completed successfully in {execution_time:.2f}s "
                              f"[correlation_id: {self.correlation_id}]")
                    self._notify_observers('success', state, result)
                    return result
                else:
                    logger.warning(f"Node {self.node_id} failed: {result.message} "
                                 f"[correlation_id: {self.correlation_id}]")
                    if not self.can_retry(result.error) or attempt == max_attempts - 1:
                        self._notify_observers('error', state, result)
                        return result
                    
                    last_error = result.error
                    
            except Exception as e:
                last_error = e
                logger.error(f"Exception in node {self.node_id} (attempt {attempt + 1}): {e} "
                           f"[correlation_id: {self.correlation_id}]")
                
                if not self.can_retry(e) or attempt == max_attempts - 1:
                    result = NodeResult.failure_result(
                        f"Node execution failed after {attempt + 1} attempts: {str(e)}",
                        error=e,
                        execution_time=time.time() - start_time
                    )
                    result.correlation_id = self.correlation_id
                    result.retry_count = attempt
                    self._notify_observers('error', state, result)
                    return result
            
            # Wait before retry with exponential backoff
            if attempt < max_attempts - 1:
                sleep_time = backoff_factor ** attempt
                logger.info(f"Retrying node {self.node_id} in {sleep_time:.1f}s "
                          f"[correlation_id: {self.correlation_id}]")
                time.sleep(sleep_time)
        
        # Should not reach here, but handle gracefully
        result = NodeResult.failure_result(
            f"Node execution failed after {max_attempts} attempts",
            error=last_error,
            execution_time=time.time() - start_time
        )
        result.correlation_id = self.correlation_id
        result.retry_count = max_attempts - 1
        self._notify_observers('error', state, result)
        return result
    
    def add_observer(self, observer: 'NodeObserver') -> None:
        """Add an observer for node events."""
        self._observers.append(observer)
    
    def remove_observer(self, observer: 'NodeObserver') -> None:
        """Remove an observer."""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, event: str, state: Dict[str, Any], 
                         result: NodeResult = None) -> None:
        """Notify all observers of an event."""
        for observer in self._observers:
            try:
                observer.on_node_event(self, event, state, result)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}")
    
    def get_node_info(self) -> Dict[str, Any]:
        """Get information about this node."""
        return {
            'node_id': self.node_id,
            'node_type': self.__class__.__name__,
            'correlation_id': self.correlation_id,
            'required_inputs': self.get_required_inputs(),
            'output_keys': self.get_output_keys(),
            'metrics': {
                'start_time': self.metrics.start_time.isoformat() if self.metrics.start_time else None,
                'end_time': self.metrics.end_time.isoformat() if self.metrics.end_time else None,
                'execution_time': self.metrics.execution_time,
                'retry_count': self.metrics.retry_count
            }
        }


class NodeObserver(ABC):
    """Observer interface for node events."""
    
    @abstractmethod
    def on_node_event(self, node: WorkflowNode, event: str, 
                     state: Dict[str, Any], result: NodeResult = None) -> None:
        """Handle node event.
        
        Args:
            node: The node that generated the event
            event: Event type ('start', 'success', 'error')
            state: Current workflow state
            result: Node result (for success/error events)
        """
        pass


class LoggingNodeObserver(NodeObserver):
    """Observer that logs node events."""
    
    def on_node_event(self, node: WorkflowNode, event: str,
                     state: Dict[str, Any], result: NodeResult = None) -> None:
        """Log node events with structured logging."""
        if event == 'start':
            logger.info(f"Node {node.node_id} started [correlation_id: {node.correlation_id}]")
        elif event == 'success':
            logger.info(f"Node {node.node_id} succeeded: {result.message} "
                       f"[correlation_id: {node.correlation_id}]")
        elif event == 'error':
            logger.error(f"Node {node.node_id} failed: {result.message} "
                        f"[correlation_id: {node.correlation_id}]")


class MetricsNodeObserver(NodeObserver):
    """Observer that collects node metrics."""
    
    def __init__(self):
        self.metrics: List[NodeMetrics] = []
    
    def on_node_event(self, node: WorkflowNode, event: str,
                     state: Dict[str, Any], result: NodeResult = None) -> None:
        """Collect node metrics."""
        if event in ['success', 'error']:
            self.metrics.append(node.metrics)
    
    def get_metrics(self) -> List[NodeMetrics]:
        """Get collected metrics."""
        return self.metrics.copy()
    
    def clear_metrics(self) -> None:
        """Clear collected metrics."""
        self.metrics.clear()