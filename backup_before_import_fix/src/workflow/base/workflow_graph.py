"""Abstract base class for workflow graphs following LLD principles."""

import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from src.workflow.base.workflow_node import WorkflowNode, NodeResult, NodeObserver
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class GraphStatus(Enum):
    """Status of workflow graph execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class GraphResult:
    """Result of workflow graph execution."""
    success: bool
    status: GraphStatus
    message: str
    final_state: Dict[str, Any] = field(default_factory=dict)
    node_results: Dict[str, NodeResult] = field(default_factory=dict)
    execution_time: float = 0.0
    nodes_executed: int = 0
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    @classmethod
    def success_result(cls, message: str, final_state: Dict[str, Any] = None,
                      node_results: Dict[str, NodeResult] = None,
                      execution_time: float = 0.0, nodes_executed: int = 0) -> 'GraphResult':
        """Create a successful graph result."""
        return cls(
            success=True,
            status=GraphStatus.COMPLETED,
            message=message,
            final_state=final_state or {},
            node_results=node_results or {},
            execution_time=execution_time,
            nodes_executed=nodes_executed
        )
    
    @classmethod
    def failure_result(cls, message: str, final_state: Dict[str, Any] = None,
                      node_results: Dict[str, NodeResult] = None,
                      execution_time: float = 0.0, nodes_executed: int = 0) -> 'GraphResult':
        """Create a failure graph result."""
        return cls(
            success=False,
            status=GraphStatus.FAILED,
            message=message,
            final_state=final_state or {},
            node_results=node_results or {},
            execution_time=execution_time,
            nodes_executed=nodes_executed
        )


class WorkflowGraph(ABC):
    """Abstract base class for workflow graphs.
    
    Implements the Template Method pattern for graph execution.
    Follows Open/Closed Principle - easy to extend with new graph types.
    Implements Single Responsibility - manages graph structure and execution flow.
    """
    
    def __init__(self, graph_id: str = None, correlation_id: str = None):
        self.graph_id = graph_id or str(uuid.uuid4())
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.nodes: Dict[str, WorkflowNode] = {}
        self.edges: Dict[str, List[str]] = {}  # node_id -> list of next node_ids
        self.entry_points: List[str] = []
        self.exit_points: Set[str] = set()
        self._observers: List['GraphObserver'] = []
        self._execution_order: List[str] = []
    
    @abstractmethod
    def build_graph(self) -> None:
        """Build the workflow graph structure.
        
        This method should add nodes and define the execution flow.
        """
        pass
    
    @abstractmethod
    def validate_graph(self) -> bool:
        """Validate the graph structure.
        
        Returns:
            True if graph is valid, False otherwise
        """
        pass
    
    def add_node(self, node: WorkflowNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.node_id] = node
        if node.node_id not in self.edges:
            self.edges[node.node_id] = []
        
        logger.debug(f"Added node {node.node_id} ({node.__class__.__name__}) to graph {self.graph_id}")
    
    def add_edge(self, from_node_id: str, to_node_id: str) -> None:
        """Add an edge between two nodes."""
        if from_node_id not in self.edges:
            self.edges[from_node_id] = []
        
        if to_node_id not in self.edges[from_node_id]:
            self.edges[from_node_id].append(to_node_id)
        
        logger.debug(f"Added edge from {from_node_id} to {to_node_id} in graph {self.graph_id}")
    
    def set_entry_point(self, node_id: str) -> None:
        """Set a node as an entry point."""
        if node_id in self.nodes and node_id not in self.entry_points:
            self.entry_points.append(node_id)
            logger.debug(f"Set {node_id} as entry point in graph {self.graph_id}")
    
    def set_exit_point(self, node_id: str) -> None:
        """Set a node as an exit point."""
        if node_id in self.nodes:
            self.exit_points.add(node_id)
            logger.debug(f"Set {node_id} as exit point in graph {self.graph_id}")
    
    def get_next_nodes(self, node_id: str) -> List[str]:
        """Get the next nodes to execute after the given node."""
        return self.edges.get(node_id, [])
    
    def has_cycles(self) -> bool:
        """Check if the graph has cycles using DFS."""
        visited = set()
        rec_stack = set()
        
        def has_cycle_util(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in self.edges.get(node_id, []):
                if neighbor not in visited:
                    if has_cycle_util(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if has_cycle_util(node_id):
                    return True
        
        return False
    
    def topological_sort(self) -> List[str]:
        """Get topological ordering of nodes."""
        visited = set()
        stack = []
        
        def topological_sort_util(node_id: str):
            visited.add(node_id)
            
            for neighbor in self.edges.get(node_id, []):
                if neighbor not in visited:
                    topological_sort_util(neighbor)
            
            stack.append(node_id)
        
        for node_id in self.nodes:
            if node_id not in visited:
                topological_sort_util(node_id)
        
        return stack[::-1]  # Reverse to get correct order
    
    def execute(self, initial_state: Dict[str, Any]) -> GraphResult:
        """Execute the workflow graph.
        
        Template method that defines the execution algorithm.
        """
        import time
        
        start_time = time.time()
        correlation_id = initial_state.get('correlation_id', self.correlation_id)
        
        logger.info(f"Starting graph execution: {self.graph_id} [correlation_id: {correlation_id}]")
        
        # Build and validate graph
        try:
            self.build_graph()
            if not self.validate_graph():
                return GraphResult.failure_result(
                    f"Graph validation failed for {self.graph_id}",
                    execution_time=time.time() - start_time
                )
        except Exception as e:
            logger.error(f"Error building/validating graph {self.graph_id}: {e}")
            return GraphResult.failure_result(
                f"Graph setup failed: {str(e)}",
                execution_time=time.time() - start_time
            )
        
        # Notify observers of start
        self._notify_observers('start', initial_state)
        
        # Execute the graph
        try:
            result = self._execute_graph(initial_state)
            result.correlation_id = correlation_id
            result.execution_time = time.time() - start_time
            
            if result.success:
                logger.info(f"Graph {self.graph_id} completed successfully in {result.execution_time:.2f}s "
                          f"[correlation_id: {correlation_id}]")
                self._notify_observers('success', result.final_state, result)
            else:
                logger.error(f"Graph {self.graph_id} failed: {result.message} "
                           f"[correlation_id: {correlation_id}]")
                self._notify_observers('error', result.final_state, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error in graph {self.graph_id}: {e} [correlation_id: {correlation_id}]")
            result = GraphResult.failure_result(
                f"Unexpected graph execution error: {str(e)}",
                execution_time=time.time() - start_time
            )
            result.correlation_id = correlation_id
            self._notify_observers('error', initial_state, result)
            return result
    
    def _execute_graph(self, initial_state: Dict[str, Any]) -> GraphResult:
        """Execute the graph nodes in the correct order.
        
        This is the core execution logic that can be overridden by subclasses.
        """
        current_state = initial_state.copy()
        node_results = {}
        nodes_executed = 0
        
        # Get execution order
        if not self.entry_points:
            return GraphResult.failure_result("No entry points defined")
        
        # Simple sequential execution starting from entry points
        # More sophisticated graphs can override this method
        executed_nodes = set()
        nodes_to_execute = self.entry_points.copy()
        
        while nodes_to_execute:
            current_node_id = nodes_to_execute.pop(0)
            
            if current_node_id in executed_nodes:
                continue
            
            if current_node_id not in self.nodes:
                logger.warning(f"Node {current_node_id} not found in graph")
                continue
            
            node = self.nodes[current_node_id]
            
            # Execute the node
            logger.debug(f"Executing node {current_node_id} in graph {self.graph_id}")
            result = node.execute_with_retry(current_state)
            node_results[current_node_id] = result
            nodes_executed += 1
            executed_nodes.add(current_node_id)
            
            if not result.success:
                return GraphResult.failure_result(
                    f"Node {current_node_id} failed: {result.message}",
                    final_state=current_state,
                    node_results=node_results,
                    nodes_executed=nodes_executed
                )
            
            # Update state with node results
            current_state.update(result.data)
            
            # Add next nodes to execution queue
            next_nodes = self.get_next_nodes(current_node_id)
            for next_node_id in next_nodes:
                if next_node_id not in executed_nodes:
                    nodes_to_execute.append(next_node_id)
        
        return GraphResult.success_result(
            f"Graph {self.graph_id} completed successfully",
            final_state=current_state,
            node_results=node_results,
            nodes_executed=nodes_executed
        )
    
    def add_observer(self, observer: 'GraphObserver') -> None:
        """Add an observer for graph events."""
        self._observers.append(observer)
    
    def remove_observer(self, observer: 'GraphObserver') -> None:
        """Remove an observer."""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, event: str, state: Dict[str, Any],
                         result: GraphResult = None) -> None:
        """Notify all observers of an event."""
        for observer in self._observers:
            try:
                observer.on_graph_event(self, event, state, result)
            except Exception as e:
                logger.error(f"Error notifying graph observer: {e}")
    
    def get_graph_info(self) -> Dict[str, Any]:
        """Get information about this graph."""
        return {
            'graph_id': self.graph_id,
            'graph_type': self.__class__.__name__,
            'correlation_id': self.correlation_id,
            'node_count': len(self.nodes),
            'edge_count': sum(len(edges) for edges in self.edges.values()),
            'entry_points': self.entry_points,
            'exit_points': list(self.exit_points),
            'has_cycles': self.has_cycles(),
            'nodes': {node_id: node.get_node_info() for node_id, node in self.nodes.items()}
        }


class GraphObserver(ABC):
    """Observer interface for graph events."""
    
    @abstractmethod
    def on_graph_event(self, graph: WorkflowGraph, event: str,
                      state: Dict[str, Any], result: GraphResult = None) -> None:
        """Handle graph event.
        
        Args:
            graph: The graph that generated the event
            event: Event type ('start', 'success', 'error')
            state: Current workflow state
            result: Graph result (for success/error events)
        """
        pass


class LoggingGraphObserver(GraphObserver):
    """Observer that logs graph events."""
    
    def on_graph_event(self, graph: WorkflowGraph, event: str,
                      state: Dict[str, Any], result: GraphResult = None) -> None:
        """Log graph events with structured logging."""
        if event == 'start':
            logger.info(f"Graph {graph.graph_id} started [correlation_id: {graph.correlation_id}]")
        elif event == 'success':
            logger.info(f"Graph {graph.graph_id} succeeded: {result.message} "
                       f"[correlation_id: {graph.correlation_id}]")
        elif event == 'error':
            logger.error(f"Graph {graph.graph_id} failed: {result.message} "
                        f"[correlation_id: {graph.correlation_id}]")


class MetricsGraphObserver(GraphObserver):
    """Observer that collects graph metrics."""
    
    def __init__(self):
        self.executions: List[Tuple[str, GraphResult]] = []
    
    def on_graph_event(self, graph: WorkflowGraph, event: str,
                      state: Dict[str, Any], result: GraphResult = None) -> None:
        """Collect graph metrics."""
        if event in ['success', 'error']:
            self.executions.append((graph.graph_id, result))
    
    def get_metrics(self) -> List[Tuple[str, GraphResult]]:
        """Get collected metrics."""
        return self.executions.copy()
    
    def clear_metrics(self) -> None:
        """Clear collected metrics."""
        self.executions.clear()