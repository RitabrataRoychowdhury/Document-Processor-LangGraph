"""
UI Error Handler Service

Provides comprehensive error handling for Streamlit UI components with user-friendly
error messages, error recovery suggestions, and error tracking.
"""

import streamlit as st
import traceback
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from src.utils.error_handling import DocumentQAError, ErrorType, format_error_for_ui
from src.utils.logging_config import get_logger
from src.infrastructure.monitoring.error_message_formatter import format_user_friendly_error
from src.infrastructure.monitoring.fallback_renderer import render_component_fallback
from src.infrastructure.monitoring.error_recovery_system import render_error_recovery_interface

logger = get_logger(__name__)


class UIErrorSeverity(Enum):
    """UI error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class UIErrorContext:
    """Context information for UI errors."""
    page: str
    component: str
    user_action: str
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    additional_context: Optional[Dict[str, Any]] = None


class UIErrorHandler:
    """
    Comprehensive error handler for Streamlit UI components.
    
    Features:
    - User-friendly error messages
    - Error recovery suggestions
    - Error tracking and analytics
    - Graceful degradation
    - Error notification system
    """
    
    def __init__(self):
        """Initialize the UI error handler."""
        self.error_history: List[Dict[str, Any]] = []
        self.error_counts: Dict[str, int] = {}
        
        # Initialize session state for error tracking
        if 'ui_errors' not in st.session_state:
            st.session_state.ui_errors = []
        if 'error_notifications' not in st.session_state:
            st.session_state.error_notifications = []
    
    def handle_error(self, 
                    error: Exception,
                    context: UIErrorContext,
                    severity: UIErrorSeverity = UIErrorSeverity.ERROR,
                    show_to_user: bool = True,
                    recovery_suggestions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Handle an error with comprehensive logging and user notification.
        
        Args:
            error: The exception that occurred
            context: Context information about where the error occurred
            severity: Severity level of the error
            show_to_user: Whether to show the error to the user
            recovery_suggestions: List of recovery suggestions for the user
            
        Returns:
            Dict containing error information and handling results
        """
        # Format error for UI display
        error_info = format_error_for_ui(error)
        
        # Create comprehensive error record
        error_record = {
            "error_id": f"ui_error_{int(datetime.now().timestamp() * 1000)}",
            "timestamp": datetime.now().isoformat(),
            "severity": severity.value,
            "error_type": error_info.get("type", "unknown"),
            "message": error_info["message"],
            "user_message": error_info["user_message"],
            "context": {
                "page": context.page,
                "component": context.component,
                "user_action": context.user_action,
                "session_id": context.session_id,
                "additional_context": context.additional_context or {}
            },
            "recovery_suggestions": recovery_suggestions or [],
            "stack_trace": traceback.format_exc() if hasattr(error, '__traceback__') else None
        }
        
        # Log the error
        self._log_error(error_record)
        
        # Track error statistics
        self._track_error_stats(error_record)
        
        # Show error to user if requested
        if show_to_user:
            self._display_error_to_user(error_record)
        
        # Store in session state for error analytics
        st.session_state.ui_errors.append(error_record)
        
        return error_record
    
    def _log_error(self, error_record: Dict[str, Any]) -> None:
        """Log error with appropriate level."""
        severity = error_record["severity"]
        message = f"UI Error in {error_record['context']['page']}/{error_record['context']['component']}: {error_record['message']}"
        
        extra_data = {
            "error_id": error_record["error_id"],
            "context": error_record["context"],
            "user_message": error_record["user_message"]
        }
        
        if severity == UIErrorSeverity.CRITICAL.value:
            logger.critical(message, extra=extra_data)
        elif severity == UIErrorSeverity.ERROR.value:
            logger.error(message, extra=extra_data)
        elif severity == UIErrorSeverity.WARNING.value:
            logger.warning(message, extra=extra_data)
        else:
            logger.info(message, extra=extra_data)
    
    def _track_error_stats(self, error_record: Dict[str, Any]) -> None:
        """Track error statistics."""
        error_key = f"{error_record['context']['page']}_{error_record['error_type']}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.error_history.append(error_record)
        
        # Keep only last 100 errors in memory
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
    
    def _display_error_to_user(self, error_record: Dict[str, Any]) -> None:
        """Display error to user with appropriate styling and enhanced recovery options."""
        severity = error_record["severity"]
        user_message = error_record["user_message"]
        recovery_suggestions = error_record["recovery_suggestions"]
        
        # Choose appropriate Streamlit display method based on severity
        if severity == UIErrorSeverity.CRITICAL.value:
            st.error(f"🚨 Critical Error: {user_message}")
        elif severity == UIErrorSeverity.ERROR.value:
            st.error(f"❌ Error: {user_message}")
        elif severity == UIErrorSeverity.WARNING.value:
            st.warning(f"⚠️ Warning: {user_message}")
        else:
            st.info(f"ℹ️ {user_message}")
        
        # Show recovery suggestions if available
        if recovery_suggestions:
            with st.expander("💡 Suggested Solutions", expanded=False):
                for i, suggestion in enumerate(recovery_suggestions, 1):
                    st.write(f"{i}. {suggestion}")
        
        # Add error to notifications for persistent display
        notification = {
            "id": error_record["error_id"],
            "message": user_message,
            "severity": severity,
            "timestamp": error_record["timestamp"],
            "dismissed": False
        }
        st.session_state.error_notifications.append(notification)
    
    def safe_execute(self, 
                    func: Callable,
                    context: UIErrorContext,
                    fallback_result: Any = None,
                    recovery_suggestions: Optional[List[str]] = None,
                    *args, **kwargs) -> Any:
        """
        Safely execute a function with error handling.
        
        Args:
            func: Function to execute
            context: Error context information
            fallback_result: Result to return if function fails
            recovery_suggestions: Recovery suggestions for user
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result or fallback_result if error occurs
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.handle_error(
                error=e,
                context=context,
                recovery_suggestions=recovery_suggestions
            )
            return fallback_result
    
    def create_error_boundary(self, 
                             page: str, 
                             component: str,
                             recovery_suggestions: Optional[List[str]] = None):
        """
        Create an error boundary decorator for UI components.
        
        Args:
            page: Page name where component is located
            component: Component name
            recovery_suggestions: Default recovery suggestions
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                context = UIErrorContext(
                    page=page,
                    component=component,
                    user_action=func.__name__,
                    session_id=st.session_state.get('session_id'),
                    timestamp=datetime.now()
                )
                
                return self.safe_execute(
                    func=func,
                    context=context,
                    recovery_suggestions=recovery_suggestions,
                    *args, **kwargs
                )
            
            return wrapper
        return decorator
    
    def render_error_notifications(self) -> None:
        """Render persistent error notifications."""
        if not st.session_state.error_notifications:
            return
        
        # Filter out dismissed notifications
        active_notifications = [
            n for n in st.session_state.error_notifications 
            if not n.get("dismissed", False)
        ]
        
        if not active_notifications:
            return
        
        # Show notifications in sidebar
        with st.sidebar:
            st.subheader("🔔 Notifications")
            
            for notification in active_notifications[-5:]:  # Show last 5 notifications
                severity = notification["severity"]
                message = notification["message"]
                timestamp = notification["timestamp"]
                
                # Format timestamp
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = "Unknown"
                
                # Display notification with dismiss button
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    if severity == UIErrorSeverity.CRITICAL.value:
                        st.error(f"🚨 {message} ({time_str})")
                    elif severity == UIErrorSeverity.ERROR.value:
                        st.error(f"❌ {message} ({time_str})")
                    elif severity == UIErrorSeverity.WARNING.value:
                        st.warning(f"⚠️ {message} ({time_str})")
                    else:
                        st.info(f"ℹ️ {message} ({time_str})")
                
                with col2:
                    if st.button("✕", key=f"dismiss_{notification['id']}", help="Dismiss"):
                        notification["dismissed"] = True
                        st.rerun()
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        total_errors = len(self.error_history)
        
        if total_errors == 0:
            return {"total_errors": 0, "error_rate": 0.0}
        
        # Calculate error rates by type
        error_types = {}
        severity_counts = {}
        page_errors = {}
        
        for error in self.error_history:
            error_type = error["error_type"]
            severity = error["severity"]
            page = error["context"]["page"]
            
            error_types[error_type] = error_types.get(error_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            page_errors[page] = page_errors.get(page, 0) + 1
        
        # Calculate recent error rate (last hour)
        recent_errors = [
            e for e in self.error_history
            if (datetime.now() - datetime.fromisoformat(e["timestamp"])).total_seconds() < 3600
        ]
        
        return {
            "total_errors": total_errors,
            "recent_errors": len(recent_errors),
            "error_rate": len(recent_errors) / 60,  # Errors per minute in last hour
            "error_types": error_types,
            "severity_counts": severity_counts,
            "page_errors": page_errors,
            "most_common_error": max(error_types.items(), key=lambda x: x[1])[0] if error_types else None
        }
    
    def clear_error_history(self) -> None:
        """Clear error history and notifications."""
        self.error_history.clear()
        self.error_counts.clear()
        st.session_state.ui_errors.clear()
        st.session_state.error_notifications.clear()
    
    def export_error_report(self) -> Dict[str, Any]:
        """Export comprehensive error report."""
        return {
            "export_timestamp": datetime.now().isoformat(),
            "statistics": self.get_error_statistics(),
            "error_history": self.error_history[-50:],  # Last 50 errors
            "session_errors": st.session_state.ui_errors[-20:],  # Last 20 session errors
            "active_notifications": [
                n for n in st.session_state.error_notifications 
                if not n.get("dismissed", False)
            ]
        }
    
    def handle_component_failure(self, 
                                component_name: str,
                                error: Exception,
                                context: Optional[Dict[str, Any]] = None,
                                show_fallback: bool = True,
                                show_recovery: bool = True) -> None:
        """
        Handle component failure with comprehensive error handling, fallback rendering, and recovery options.
        
        Args:
            component_name: Name of the failed component
            error: The exception that caused the failure
            context: Additional context about the failure
            show_fallback: Whether to show fallback component
            show_recovery: Whether to show recovery options
        """
        # Create error context
        error_context = UIErrorContext(
            page=context.get('page', 'unknown') if context else 'unknown',
            component=component_name,
            user_action=context.get('user_action', 'component_load') if context else 'component_load',
            session_id=st.session_state.get('session_id'),
            timestamp=datetime.now(),
            additional_context=context
        )
        
        # Handle the error
        error_record = self.handle_error(
            error=error,
            context=error_context,
            severity=UIErrorSeverity.ERROR,
            show_to_user=True
        )
        
        # Show fallback component if requested
        if show_fallback:
            try:
                render_component_fallback(component_name, error, context)
            except Exception as fallback_error:
                logger.error(f"Fallback rendering failed for {component_name}: {fallback_error}")
                st.error("❌ Component and fallback both failed. Please refresh the page.")
        
        # Show recovery options if requested
        if show_recovery:
            try:
                render_error_recovery_interface(error, context)
            except Exception as recovery_error:
                logger.error(f"Recovery interface failed for {component_name}: {recovery_error}")
    
    def create_enhanced_error_boundary(self, 
                                     page: str, 
                                     component: str,
                                     recovery_suggestions: Optional[List[str]] = None,
                                     show_fallback: bool = True,
                                     show_recovery: bool = True):
        """
        Create an enhanced error boundary decorator with fallback and recovery options.
        
        Args:
            page: Page name where component is located
            component: Component name
            recovery_suggestions: Default recovery suggestions
            show_fallback: Whether to show fallback component on error
            show_recovery: Whether to show recovery options on error
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    context = {
                        'page': page,
                        'component': component,
                        'user_action': func.__name__,
                        'session_id': st.session_state.get('session_id'),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Handle component failure with enhanced options
                    self.handle_component_failure(
                        component_name=component,
                        error=e,
                        context=context,
                        show_fallback=show_fallback,
                        show_recovery=show_recovery
                    )
                    
                    # Return None to indicate failure
                    return None
            
            return wrapper
        return decorator


# Global UI error handler instance
ui_error_handler = UIErrorHandler()


# Convenience functions for common error handling patterns
def handle_ui_error(error: Exception, 
                   page: str, 
                   component: str, 
                   user_action: str = "unknown",
                   recovery_suggestions: Optional[List[str]] = None) -> Dict[str, Any]:
    """Convenience function for handling UI errors."""
    context = UIErrorContext(
        page=page,
        component=component,
        user_action=user_action,
        session_id=st.session_state.get('session_id'),
        timestamp=datetime.now()
    )
    
    return ui_error_handler.handle_error(
        error=error,
        context=context,
        recovery_suggestions=recovery_suggestions
    )


def safe_ui_operation(func: Callable, 
                     page: str, 
                     component: str,
                     fallback_result: Any = None,
                     recovery_suggestions: Optional[List[str]] = None,
                     *args, **kwargs) -> Any:
    """Safely execute a UI operation with error handling."""
    context = UIErrorContext(
        page=page,
        component=component,
        user_action=func.__name__,
        session_id=st.session_state.get('session_id'),
        timestamp=datetime.now()
    )
    
    return ui_error_handler.safe_execute(
        func=func,
        context=context,
        fallback_result=fallback_result,
        recovery_suggestions=recovery_suggestions,
        *args, **kwargs
    )


def ui_error_boundary(page: str, component: str, recovery_suggestions: Optional[List[str]] = None):
    """Decorator for creating error boundaries around UI components."""
    return ui_error_handler.create_error_boundary(
        page=page,
        component=component,
        recovery_suggestions=recovery_suggestions
    )


def enhanced_ui_error_boundary(page: str, 
                              component: str, 
                              recovery_suggestions: Optional[List[str]] = None,
                              show_fallback: bool = True,
                              show_recovery: bool = True):
    """Decorator for creating enhanced error boundaries with fallback and recovery options."""
    return ui_error_handler.create_enhanced_error_boundary(
        page=page,
        component=component,
        recovery_suggestions=recovery_suggestions,
        show_fallback=show_fallback,
        show_recovery=show_recovery
    )


def handle_component_failure(component_name: str,
                           error: Exception,
                           context: Optional[Dict[str, Any]] = None,
                           show_fallback: bool = True,
                           show_recovery: bool = True) -> None:
    """Convenience function for handling component failures with enhanced options."""
    ui_error_handler.handle_component_failure(
        component_name=component_name,
        error=error,
        context=context,
        show_fallback=show_fallback,
        show_recovery=show_recovery
    )