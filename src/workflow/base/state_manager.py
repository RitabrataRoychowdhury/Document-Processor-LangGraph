"""Abstract base class for workflow state management following LLD principles."""

import uuid
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type, TypeVar, Generic
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from copy import deepcopy

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class StateStatus(Enum):
    """Status of workflow state."""
    INITIALIZED = "initialized"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StateSnapshot:
    """Snapshot of workflow state at a point in time."""
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    state_data: Dict[str, Any] = field(default_factory=dict)
    status: StateStatus = StateStatus.INITIALIZED
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            'snapshot_id': self.snapshot_id,
            'timestamp': self.timestamp.isoformat(),
            'state_data': self.state_data,
            'status': self.status.value,
            'correlation_id': self.correlation_id,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateSnapshot':
        """Create snapshot from dictionary."""
        return cls(
            snapshot_id=data.get('snapshot_id', str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            state_data=data.get('state_data', {}),
            status=StateStatus(data.get('status', StateStatus.INITIALIZED.value)),
            correlation_id=data.get('correlation_id', str(uuid.uuid4())),
            metadata=data.get('metadata', {})
        )


class StateManager(ABC, Generic[T]):
    """Abstract base class for workflow state management.
    
    Implements Single Responsibility Principle - manages state lifecycle.
    Follows Open/Closed Principle - easy to extend with new state types.
    Implements Interface Segregation - specific interfaces for different state operations.
    """
    
    def __init__(self, state_id: str = None, correlation_id: str = None):
        self.state_id = state_id or str(uuid.uuid4())
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self._current_state: Dict[str, Any] = {}
        self._snapshots: List[StateSnapshot] = []
        self._status = StateStatus.INITIALIZED
        self._observers: List['StateObserver'] = []
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
    
    @abstractmethod
    def initialize_state(self, initial_data: Dict[str, Any]) -> None:
        """Initialize the workflow state.
        
        Args:
            initial_data: Initial state data
        """
        pass
    
    @abstractmethod
    def validate_state(self, state_data: Dict[str, Any]) -> bool:
        """Validate state data.
        
        Args:
            state_data: State data to validate
            
        Returns:
            True if state is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_required_keys(self) -> List[str]:
        """Get list of required state keys.
        
        Returns:
            List of required state keys
        """
        pass
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state data."""
        return deepcopy(self._current_state)
    
    def update_state(self, updates: Dict[str, Any], create_snapshot: bool = True) -> None:
        """Update state with new data.
        
        Args:
            updates: State updates to apply
            create_snapshot: Whether to create a snapshot before updating
        """
        if create_snapshot:
            self.create_snapshot()
        
        old_state = deepcopy(self._current_state)
        self._current_state.update(updates)
        self._updated_at = datetime.now()
        
        # Validate updated state
        if not self.validate_state(self._current_state):
            logger.warning(f"State validation failed after update for {self.state_id}")
            # Optionally revert changes
            # self._current_state = old_state
        
        # Notify observers
        self._notify_observers('update', old_state, self._current_state)
        
        logger.debug(f"State updated for {self.state_id} [correlation_id: {self.correlation_id}]")
    
    def set_state(self, new_state: Dict[str, Any], create_snapshot: bool = True) -> None:
        """Set complete state data.
        
        Args:
            new_state: New state data
            create_snapshot: Whether to create a snapshot before setting
        """
        if create_snapshot:
            self.create_snapshot()
        
        old_state = deepcopy(self._current_state)
        self._current_state = deepcopy(new_state)
        self._updated_at = datetime.now()
        
        # Validate new state
        if not self.validate_state(self._current_state):
            logger.error(f"State validation failed for new state in {self.state_id}")
            raise ValueError("Invalid state data")
        
        # Notify observers
        self._notify_observers('set', old_state, self._current_state)
        
        logger.debug(f"State set for {self.state_id} [correlation_id: {self.correlation_id}]")
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a specific value from state.
        
        Args:
            key: State key to retrieve
            default: Default value if key not found
            
        Returns:
            State value or default
        """
        return self._current_state.get(key, default)
    
    def set_value(self, key: str, value: Any, create_snapshot: bool = False) -> None:
        """Set a specific value in state.
        
        Args:
            key: State key to set
            value: Value to set
            create_snapshot: Whether to create a snapshot before setting
        """
        self.update_state({key: value}, create_snapshot)
    
    def has_key(self, key: str) -> bool:
        """Check if state has a specific key.
        
        Args:
            key: Key to check
            
        Returns:
            True if key exists, False otherwise
        """
        return key in self._current_state
    
    def remove_key(self, key: str, create_snapshot: bool = False) -> Any:
        """Remove a key from state.
        
        Args:
            key: Key to remove
            create_snapshot: Whether to create a snapshot before removing
            
        Returns:
            Removed value or None
        """
        if create_snapshot:
            self.create_snapshot()
        
        removed_value = self._current_state.pop(key, None)
        self._updated_at = datetime.now()
        
        if removed_value is not None:
            self._notify_observers('remove', {key: removed_value}, self._current_state)
            logger.debug(f"Removed key '{key}' from state {self.state_id}")
        
        return removed_value
    
    def create_snapshot(self, metadata: Dict[str, Any] = None) -> str:
        """Create a snapshot of current state.
        
        Args:
            metadata: Optional metadata for the snapshot
            
        Returns:
            Snapshot ID
        """
        snapshot = StateSnapshot(
            state_data=deepcopy(self._current_state),
            status=self._status,
            correlation_id=self.correlation_id,
            metadata=metadata or {}
        )
        
        self._snapshots.append(snapshot)
        
        # Limit number of snapshots to prevent memory issues
        max_snapshots = 50
        if len(self._snapshots) > max_snapshots:
            self._snapshots = self._snapshots[-max_snapshots:]
        
        logger.debug(f"Created snapshot {snapshot.snapshot_id} for state {self.state_id}")
        return snapshot.snapshot_id
    
    def restore_snapshot(self, snapshot_id: str) -> bool:
        """Restore state from a snapshot.
        
        Args:
            snapshot_id: ID of snapshot to restore
            
        Returns:
            True if restored successfully, False otherwise
        """
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            logger.error(f"Snapshot {snapshot_id} not found for state {self.state_id}")
            return False
        
        old_state = deepcopy(self._current_state)
        self._current_state = deepcopy(snapshot.state_data)
        self._status = snapshot.status
        self._updated_at = datetime.now()
        
        # Notify observers
        self._notify_observers('restore', old_state, self._current_state)
        
        logger.info(f"Restored state {self.state_id} from snapshot {snapshot_id}")
        return True
    
    def get_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """Get a specific snapshot.
        
        Args:
            snapshot_id: ID of snapshot to retrieve
            
        Returns:
            StateSnapshot or None if not found
        """
        for snapshot in self._snapshots:
            if snapshot.snapshot_id == snapshot_id:
                return snapshot
        return None
    
    def get_snapshots(self) -> List[StateSnapshot]:
        """Get all snapshots.
        
        Returns:
            List of all snapshots
        """
        return self._snapshots.copy()
    
    def clear_snapshots(self) -> None:
        """Clear all snapshots."""
        self._snapshots.clear()
        logger.debug(f"Cleared all snapshots for state {self.state_id}")
    
    def get_status(self) -> StateStatus:
        """Get current state status."""
        return self._status
    
    def set_status(self, status: StateStatus) -> None:
        """Set state status.
        
        Args:
            status: New status
        """
        old_status = self._status
        self._status = status
        self._updated_at = datetime.now()
        
        # Notify observers
        self._notify_observers('status_change', {'old_status': old_status.value}, 
                             {'new_status': status.value})
        
        logger.debug(f"State {self.state_id} status changed from {old_status.value} to {status.value}")
    
    def is_complete(self) -> bool:
        """Check if state is complete."""
        return self._status == StateStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if state is failed."""
        return self._status == StateStatus.FAILED
    
    def is_active(self) -> bool:
        """Check if state is active."""
        return self._status == StateStatus.ACTIVE
    
    def add_observer(self, observer: 'StateObserver') -> None:
        """Add an observer for state events."""
        self._observers.append(observer)
    
    def remove_observer(self, observer: 'StateObserver') -> None:
        """Remove an observer."""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, event: str, old_data: Dict[str, Any],
                         new_data: Dict[str, Any]) -> None:
        """Notify all observers of a state event."""
        for observer in self._observers:
            try:
                observer.on_state_event(self, event, old_data, new_data)
            except Exception as e:
                logger.error(f"Error notifying state observer: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state manager to dictionary."""
        return {
            'state_id': self.state_id,
            'correlation_id': self.correlation_id,
            'current_state': self._current_state,
            'status': self._status.value,
            'created_at': self._created_at.isoformat(),
            'updated_at': self._updated_at.isoformat(),
            'snapshots': [snapshot.to_dict() for snapshot in self._snapshots]
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load state manager from dictionary."""
        self.state_id = data.get('state_id', self.state_id)
        self.correlation_id = data.get('correlation_id', self.correlation_id)
        self._current_state = data.get('current_state', {})
        self._status = StateStatus(data.get('status', StateStatus.INITIALIZED.value))
        self._created_at = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
        self._updated_at = datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat()))
        
        # Load snapshots
        self._snapshots = []
        for snapshot_data in data.get('snapshots', []):
            self._snapshots.append(StateSnapshot.from_dict(snapshot_data))
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get information about this state manager."""
        return {
            'state_id': self.state_id,
            'correlation_id': self.correlation_id,
            'status': self._status.value,
            'created_at': self._created_at.isoformat(),
            'updated_at': self._updated_at.isoformat(),
            'state_size': len(self._current_state),
            'snapshot_count': len(self._snapshots),
            'required_keys': self.get_required_keys(),
            'has_required_keys': all(self.has_key(key) for key in self.get_required_keys())
        }


class StateObserver(ABC):
    """Observer interface for state events."""
    
    @abstractmethod
    def on_state_event(self, state_manager: StateManager, event: str,
                      old_data: Dict[str, Any], new_data: Dict[str, Any]) -> None:
        """Handle state event.
        
        Args:
            state_manager: The state manager that generated the event
            event: Event type ('update', 'set', 'remove', 'restore', 'status_change')
            old_data: Previous state data
            new_data: New state data
        """
        pass


class LoggingStateObserver(StateObserver):
    """Observer that logs state events."""
    
    def on_state_event(self, state_manager: StateManager, event: str,
                      old_data: Dict[str, Any], new_data: Dict[str, Any]) -> None:
        """Log state events with structured logging."""
        logger.debug(f"State {state_manager.state_id} event '{event}' "
                    f"[correlation_id: {state_manager.correlation_id}]")


class PersistentStateManager(StateManager):
    """State manager with persistence capabilities."""
    
    def __init__(self, state_id: str = None, correlation_id: str = None,
                 persistence_path: str = None):
        super().__init__(state_id, correlation_id)
        self.persistence_path = persistence_path
    
    def save_to_file(self, file_path: str = None) -> None:
        """Save state to file.
        
        Args:
            file_path: Path to save file (optional)
        """
        path = file_path or self.persistence_path
        if not path:
            raise ValueError("No persistence path specified")
        
        try:
            with open(path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            logger.debug(f"Saved state {self.state_id} to {path}")
        except Exception as e:
            logger.error(f"Error saving state to file: {e}")
            raise
    
    def load_from_file(self, file_path: str = None) -> None:
        """Load state from file.
        
        Args:
            file_path: Path to load file (optional)
        """
        path = file_path or self.persistence_path
        if not path:
            raise ValueError("No persistence path specified")
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            self.from_dict(data)
            logger.debug(f"Loaded state {self.state_id} from {path}")
        except Exception as e:
            logger.error(f"Error loading state from file: {e}")
            raise