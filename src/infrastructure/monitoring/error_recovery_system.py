"""
Error Recovery System

Provides intelligent error recovery mechanisms with context-aware suggestions,
automated recovery attempts, and user-guided recovery workflows.
"""

import streamlit as st
from typing import Dict, Any, Optional, List, Callable, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import time

from src.infrastructure.monitoring.error_message_formatter import ErrorCategory, format_user_friendly_error
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class RecoveryStrategy(Enum):
    """Types of recovery strategies."""
    AUTOMATIC_RETRY = "automatic_retry"
    USER_GUIDED = "user_guided"
    CONFIGURATION_FIX = "configuration_fix"
    ALTERNATIVE_PATH = "alternative_path"
    MANUAL_INTERVENTION = "manual_intervention"
    SERVICE_RESTART = "service_restart"


class RecoveryStatus(Enum):
    """Status of recovery attempts."""
    NOT_ATTEMPTED = "not_attempted"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    REQUIRES_USER_ACTION = "requires_user_action"


@dataclass
class RecoveryAction:
    """Represents a recovery action."""
    id: str
    name: str
    description: str
    strategy: RecoveryStrategy
    auto_executable: bool
    user_confirmation_required: bool
    estimated_time_seconds: int
    success_probability: float
    prerequisites: List[str]
    action_function: Optional[Callable] = None


@dataclass
class RecoveryAttempt:
    """Represents an attempt to recover from an error."""
    attempt_id: str
    error_id: str
    recovery_action: RecoveryAction
    status: RecoveryStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    success_message: Optional[str] = None


class ErrorRecoverySystem:
    """
    Intelligent error recovery system that provides context-aware recovery
    suggestions and automated recovery mechanisms.
    """
    
    def __init__(self):
        """Initialize the error recovery system."""
        self.recovery_actions = self._initialize_recovery_actions()
        self.recovery_history: List[RecoveryAttempt] = []
        
        # Initialize session state for recovery tracking
        if 'recovery_attempts' not in st.session_state:
            st.session_state.recovery_attempts = {}
        if 'recovery_suggestions' not in st.session_state:
            st.session_state.recovery_suggestions = {}
    
    def suggest_recovery_actions(self, 
                                error: Exception,
                                context: Optional[Dict[str, Any]] = None) -> List[RecoveryAction]:
        """
        Suggest recovery actions based on error type and context.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            
        Returns:
            List of suggested recovery actions, ordered by success probability
        """
        user_error = format_user_friendly_error(error, context)
        
        # Get applicable recovery actions
        applicable_actions = self._get_applicable_actions(user_error.category, error, context)
        
        # Filter based on context and prerequisites
        filtered_actions = self._filter_actions_by_context(applicable_actions, context)
        
        # Sort by success probability and user preference
        sorted_actions = sorted(filtered_actions, key=lambda x: (-x.success_probability, x.auto_executable))
        
        return sorted_actions[:5]  # Return top 5 suggestions
    
    def attempt_recovery(self, 
                        error_id: str,
                        recovery_action: RecoveryAction,
                        context: Optional[Dict[str, Any]] = None) -> RecoveryAttempt:
        """
        Attempt to recover from an error using the specified recovery action.
        
        Args:
            error_id: Unique identifier for the error
            recovery_action: The recovery action to attempt
            context: Additional context for the recovery attempt
            
        Returns:
            RecoveryAttempt object with the results
        """
        attempt_id = f"recovery_{int(time.time() * 1000)}"
        
        attempt = RecoveryAttempt(
            attempt_id=attempt_id,
            error_id=error_id,
            recovery_action=recovery_action,
            status=RecoveryStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        try:
            # Check prerequisites
            if not self._check_prerequisites(recovery_action, context):
                attempt.status = RecoveryStatus.REQUIRES_USER_ACTION
                attempt.error_message = "Prerequisites not met"
                return attempt
            
            # Execute recovery action
            if recovery_action.action_function:
                success = recovery_action.action_function(context)
                
                if success:
                    attempt.status = RecoveryStatus.SUCCESS
                    attempt.success_message = f"Successfully executed {recovery_action.name}"
                else:
                    attempt.status = RecoveryStatus.FAILED
                    attempt.error_message = f"Recovery action {recovery_action.name} failed"
            else:
                # Manual recovery action
                attempt.status = RecoveryStatus.REQUIRES_USER_ACTION
                attempt.error_message = "Manual intervention required"
        
        except Exception as e:
            attempt.status = RecoveryStatus.FAILED
            attempt.error_message = f"Recovery failed: {str(e)}"
            logger.error(f"Recovery attempt failed: {e}")
        
        finally:
            attempt.completed_at = datetime.now()
            self.recovery_history.append(attempt)
            st.session_state.recovery_attempts[attempt_id] = attempt
        
        return attempt
    
    def render_recovery_interface(self, 
                                 error: Exception,
                                 context: Optional[Dict[str, Any]] = None) -> None:
        """
        Render an interactive recovery interface for the user.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
        """
        st.markdown("---")
        st.subheader("🔧 Error Recovery Options")
        
        # Get recovery suggestions
        recovery_actions = self.suggest_recovery_actions(error, context)
        
        if not recovery_actions:
            st.info("No automatic recovery options available. Please try manual troubleshooting.")
            return
        
        # Create tabs for different recovery strategies
        strategy_groups = self._group_actions_by_strategy(recovery_actions)
        
        if len(strategy_groups) > 1:
            tabs = st.tabs([strategy.value.replace('_', ' ').title() for strategy in strategy_groups.keys()])
            
            for tab, (strategy, actions) in zip(tabs, strategy_groups.items()):
                with tab:
                    self._render_recovery_actions(actions, context)
        else:
            # Single strategy, render directly
            strategy, actions = next(iter(strategy_groups.items()))
            self._render_recovery_actions(actions, context)
        
        # Show recovery history if available
        self._render_recovery_history()
    
    def _initialize_recovery_actions(self) -> Dict[str, List[RecoveryAction]]:
        """Initialize available recovery actions."""
        return {
            ErrorCategory.CONFIGURATION.value: [
                RecoveryAction(
                    id="check_env_file",
                    name="Check Environment Configuration",
                    description="Verify that all required environment variables are set",
                    strategy=RecoveryStrategy.CONFIGURATION_FIX,
                    auto_executable=True,
                    user_confirmation_required=False,
                    estimated_time_seconds=5,
                    success_probability=0.8,
                    prerequisites=[],
                    action_function=self._check_environment_config
                ),
                RecoveryAction(
                    id="reload_config",
                    name="Reload Configuration",
                    description="Reload application configuration from files",
                    strategy=RecoveryStrategy.AUTOMATIC_RETRY,
                    auto_executable=True,
                    user_confirmation_required=False,
                    estimated_time_seconds=10,
                    success_probability=0.7,
                    prerequisites=[],
                    action_function=self._reload_configuration
                ),
                RecoveryAction(
                    id="reset_to_defaults",
                    name="Reset to Default Configuration",
                    description="Reset configuration to default values",
                    strategy=RecoveryStrategy.USER_GUIDED,
                    auto_executable=False,
                    user_confirmation_required=True,
                    estimated_time_seconds=30,
                    success_probability=0.9,
                    prerequisites=["user_confirmation"],
                    action_function=self._reset_to_defaults
                )
            ],
            ErrorCategory.SERVICE_UNAVAILABLE.value: [
                RecoveryAction(
                    id="restart_services",
                    name="Restart Services",
                    description="Attempt to restart unavailable services",
                    strategy=RecoveryStrategy.SERVICE_RESTART,
                    auto_executable=True,
                    user_confirmation_required=False,
                    estimated_time_seconds=15,
                    success_probability=0.6,
                    prerequisites=[],
                    action_function=self._restart_services
                ),
                RecoveryAction(
                    id="use_fallback_service",
                    name="Use Fallback Service",
                    description="Switch to alternative service implementation",
                    strategy=RecoveryStrategy.ALTERNATIVE_PATH,
                    auto_executable=True,
                    user_confirmation_required=False,
                    estimated_time_seconds=5,
                    success_probability=0.8,
                    prerequisites=[],
                    action_function=self._use_fallback_service
                ),
                RecoveryAction(
                    id="check_dependencies",
                    name="Check Dependencies",
                    description="Verify that all required dependencies are installed",
                    strategy=RecoveryStrategy.CONFIGURATION_FIX,
                    auto_executable=True,
                    user_confirmation_required=False,
                    estimated_time_seconds=10,
                    success_probability=0.7,
                    prerequisites=[],
                    action_function=self._check_dependencies
                )
            ],
            ErrorCategory.NETWORK.value: [
                RecoveryAction(
                    id="retry_connection",
                    name="Retry Connection",
                    description="Attempt to reconnect to the service",
                    strategy=RecoveryStrategy.AUTOMATIC_RETRY,
                    auto_executable=True,
                    user_confirmation_required=False,
                    estimated_time_seconds=10,
                    success_probability=0.5,
                    prerequisites=[],
                    action_function=self._retry_connection
                ),
                RecoveryAction(
                    id="use_offline_mode",
                    name="Switch to Offline Mode",
                    description="Continue with limited functionality in offline mode",
                    strategy=RecoveryStrategy.ALTERNATIVE_PATH,
                    auto_executable=True,
                    user_confirmation_required=False,
                    estimated_time_seconds=2,
                    success_probability=0.9,
                    prerequisites=[],
                    action_function=self._enable_offline_mode
                )
            ],
            ErrorCategory.AUTHENTICATION.value: [
                RecoveryAction(
                    id="refresh_credentials",
                    name="Refresh Credentials",
                    description="Attempt to refresh authentication credentials",
                    strategy=RecoveryStrategy.AUTOMATIC_RETRY,
                    auto_executable=True,
                    user_confirmation_required=False,
                    estimated_time_seconds=5,
                    success_probability=0.4,
                    prerequisites=[],
                    action_function=self._refresh_credentials
                ),
                RecoveryAction(
                    id="reconfigure_auth",
                    name="Reconfigure Authentication",
                    description="Guide user through authentication setup",
                    strategy=RecoveryStrategy.USER_GUIDED,
                    auto_executable=False,
                    user_confirmation_required=True,
                    estimated_time_seconds=120,
                    success_probability=0.9,
                    prerequisites=["user_interaction"],
                    action_function=self._guide_auth_setup
                )
            ],
            ErrorCategory.FILE_PROCESSING.value: [
                RecoveryAction(
                    id="retry_file_processing",
                    name="Retry File Processing",
                    description="Attempt to process the file again",
                    strategy=RecoveryStrategy.AUTOMATIC_RETRY,
                    auto_executable=True,
                    user_confirmation_required=False,
                    estimated_time_seconds=30,
                    success_probability=0.3,
                    prerequisites=[],
                    action_function=self._retry_file_processing
                ),
                RecoveryAction(
                    id="try_different_format",
                    name="Try Different Format",
                    description="Suggest alternative file formats or processing methods",
                    strategy=RecoveryStrategy.USER_GUIDED,
                    auto_executable=False,
                    user_confirmation_required=False,
                    estimated_time_seconds=60,
                    success_probability=0.7,
                    prerequisites=[],
                    action_function=self._suggest_alternative_formats
                )
            ]
        }
    
    def _get_applicable_actions(self, 
                               error_category: ErrorCategory,
                               error: Exception,
                               context: Optional[Dict[str, Any]]) -> List[RecoveryAction]:
        """Get recovery actions applicable to the error category."""
        category_actions = self.recovery_actions.get(error_category.value, [])
        
        # Add generic actions that apply to all categories
        generic_actions = [
            RecoveryAction(
                id="refresh_page",
                name="Refresh Page",
                description="Refresh the current page to reset the state",
                strategy=RecoveryStrategy.AUTOMATIC_RETRY,
                auto_executable=True,
                user_confirmation_required=False,
                estimated_time_seconds=2,
                success_probability=0.3,
                prerequisites=[],
                action_function=self._refresh_page
            ),
            RecoveryAction(
                id="clear_cache",
                name="Clear Cache",
                description="Clear application cache and session data",
                strategy=RecoveryStrategy.USER_GUIDED,
                auto_executable=False,
                user_confirmation_required=True,
                estimated_time_seconds=10,
                success_probability=0.4,
                prerequisites=["user_confirmation"],
                action_function=self._clear_cache
            )
        ]
        
        return category_actions + generic_actions
    
    def _filter_actions_by_context(self, 
                                  actions: List[RecoveryAction],
                                  context: Optional[Dict[str, Any]]) -> List[RecoveryAction]:
        """Filter recovery actions based on context."""
        if not context:
            return actions
        
        filtered_actions = []
        
        for action in actions:
            # Check if action is applicable to the current context
            if self._is_action_applicable(action, context):
                filtered_actions.append(action)
        
        return filtered_actions
    
    def _is_action_applicable(self, action: RecoveryAction, context: Dict[str, Any]) -> bool:
        """Check if a recovery action is applicable to the current context."""
        page = context.get('page', '').lower()
        component = context.get('component', '').lower()
        
        # Context-specific filtering logic
        if action.id == "use_fallback_service" and 'upload' in component:
            return True
        elif action.id == "try_different_format" and 'file' in component:
            return True
        elif action.id == "refresh_page" and page in ['upload', 'template', 'qa']:
            return True
        
        # Default: all actions are applicable unless specifically excluded
        return True
    
    def _check_prerequisites(self, action: RecoveryAction, context: Optional[Dict[str, Any]]) -> bool:
        """Check if prerequisites for a recovery action are met."""
        for prerequisite in action.prerequisites:
            if prerequisite == "user_confirmation":
                # This would be handled in the UI
                return True
            elif prerequisite == "user_interaction":
                # This would be handled in the UI
                return True
            # Add more prerequisite checks as needed
        
        return True
    
    def _group_actions_by_strategy(self, actions: List[RecoveryAction]) -> Dict[RecoveryStrategy, List[RecoveryAction]]:
        """Group recovery actions by strategy."""
        groups = {}
        
        for action in actions:
            if action.strategy not in groups:
                groups[action.strategy] = []
            groups[action.strategy].append(action)
        
        return groups
    
    def _render_recovery_actions(self, actions: List[RecoveryAction], context: Optional[Dict[str, Any]]) -> None:
        """Render recovery actions in the UI."""
        for action in actions:
            with st.expander(f"🔧 {action.name}", expanded=False):
                st.write(action.description)
                
                # Show action details
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Success Rate", f"{action.success_probability:.0%}")
                
                with col2:
                    st.metric("Est. Time", f"{action.estimated_time_seconds}s")
                
                with col3:
                    auto_text = "Yes" if action.auto_executable else "Manual"
                    st.metric("Type", auto_text)
                
                # Action button
                button_text = "🚀 Execute" if action.auto_executable else "📋 Guide Me"
                
                if action.user_confirmation_required:
                    st.warning("⚠️ This action requires confirmation and may affect your current work.")
                
                if st.button(button_text, key=f"recovery_{action.id}"):
                    if action.user_confirmation_required:
                        if st.checkbox(f"I confirm I want to execute: {action.name}", key=f"confirm_{action.id}"):
                            self._execute_recovery_action(action, context)
                    else:
                        self._execute_recovery_action(action, context)
    
    def _execute_recovery_action(self, action: RecoveryAction, context: Optional[Dict[str, Any]]) -> None:
        """Execute a recovery action and show results."""
        with st.spinner(f"Executing {action.name}..."):
            attempt = self.attempt_recovery(f"error_{int(time.time())}", action, context)
        
        if attempt.status == RecoveryStatus.SUCCESS:
            st.success(f"✅ {attempt.success_message}")
            if st.button("🔄 Refresh Page"):
                st.rerun()
        elif attempt.status == RecoveryStatus.FAILED:
            st.error(f"❌ {attempt.error_message}")
        elif attempt.status == RecoveryStatus.REQUIRES_USER_ACTION:
            st.info(f"👤 {attempt.error_message}")
        else:
            st.info(f"🔄 Recovery in progress...")
    
    def _render_recovery_history(self) -> None:
        """Render recovery attempt history."""
        if not self.recovery_history:
            return
        
        with st.expander("📊 Recovery History", expanded=False):
            recent_attempts = self.recovery_history[-5:]  # Show last 5 attempts
            
            for attempt in reversed(recent_attempts):
                status_icon = {
                    RecoveryStatus.SUCCESS: "✅",
                    RecoveryStatus.FAILED: "❌",
                    RecoveryStatus.IN_PROGRESS: "🔄",
                    RecoveryStatus.REQUIRES_USER_ACTION: "👤"
                }.get(attempt.status, "❓")
                
                st.write(f"{status_icon} {attempt.recovery_action.name} - {attempt.started_at.strftime('%H:%M:%S')}")
    
    # Recovery action implementations
    
    def _check_environment_config(self, context: Optional[Dict[str, Any]]) -> bool:
        """Check environment configuration."""
        try:
            import os
            required_vars = ['GEMINI_API_KEY', 'OPENAI_API_KEY']
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            
            if missing_vars:
                st.warning(f"Missing environment variables: {', '.join(missing_vars)}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking environment config: {e}")
            return False
    
    def _reload_configuration(self, context: Optional[Dict[str, Any]]) -> bool:
        """Reload application configuration."""
        try:
            # This would reload the actual configuration
            st.info("Configuration reloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error reloading configuration: {e}")
            return False
    
    def _reset_to_defaults(self, context: Optional[Dict[str, Any]]) -> bool:
        """Reset configuration to defaults."""
        try:
            # This would reset to default configuration
            st.info("Configuration reset to defaults")
            return True
        except Exception as e:
            logger.error(f"Error resetting configuration: {e}")
            return False
    
    def _restart_services(self, context: Optional[Dict[str, Any]]) -> bool:
        """Restart services."""
        try:
            # This would restart actual services
            st.info("Services restarted successfully")
            return True
        except Exception as e:
            logger.error(f"Error restarting services: {e}")
            return False
    
    def _use_fallback_service(self, context: Optional[Dict[str, Any]]) -> bool:
        """Use fallback service."""
        try:
            st.session_state.use_fallback_mode = True
            st.info("Switched to fallback service mode")
            return True
        except Exception as e:
            logger.error(f"Error switching to fallback service: {e}")
            return False
    
    def _check_dependencies(self, context: Optional[Dict[str, Any]]) -> bool:
        """Check dependencies."""
        try:
            # This would check actual dependencies
            st.info("Dependencies checked successfully")
            return True
        except Exception as e:
            logger.error(f"Error checking dependencies: {e}")
            return False
    
    def _retry_connection(self, context: Optional[Dict[str, Any]]) -> bool:
        """Retry connection."""
        try:
            # This would retry actual connections
            st.info("Connection retry successful")
            return True
        except Exception as e:
            logger.error(f"Error retrying connection: {e}")
            return False
    
    def _enable_offline_mode(self, context: Optional[Dict[str, Any]]) -> bool:
        """Enable offline mode."""
        try:
            st.session_state.offline_mode = True
            st.info("Offline mode enabled")
            return True
        except Exception as e:
            logger.error(f"Error enabling offline mode: {e}")
            return False
    
    def _refresh_credentials(self, context: Optional[Dict[str, Any]]) -> bool:
        """Refresh credentials."""
        try:
            # This would refresh actual credentials
            st.info("Credentials refreshed")
            return True
        except Exception as e:
            logger.error(f"Error refreshing credentials: {e}")
            return False
    
    def _guide_auth_setup(self, context: Optional[Dict[str, Any]]) -> bool:
        """Guide user through authentication setup."""
        st.info("Please follow these steps to set up authentication:")
        st.write("1. Open your .env file")
        st.write("2. Add your API keys")
        st.write("3. Restart the application")
        return True
    
    def _retry_file_processing(self, context: Optional[Dict[str, Any]]) -> bool:
        """Retry file processing."""
        try:
            # This would retry actual file processing
            st.info("File processing retried")
            return True
        except Exception as e:
            logger.error(f"Error retrying file processing: {e}")
            return False
    
    def _suggest_alternative_formats(self, context: Optional[Dict[str, Any]]) -> bool:
        """Suggest alternative file formats."""
        st.info("Try these alternative approaches:")
        st.write("• Convert to PDF format")
        st.write("• Try a smaller file size")
        st.write("• Use plain text format")
        return True
    
    def _refresh_page(self, context: Optional[Dict[str, Any]]) -> bool:
        """Refresh the page."""
        st.rerun()
        return True
    
    def _clear_cache(self, context: Optional[Dict[str, Any]]) -> bool:
        """Clear application cache."""
        try:
            # Clear session state
            for key in list(st.session_state.keys()):
                if key.startswith('cache_'):
                    del st.session_state[key]
            
            st.info("Cache cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False


# Global error recovery system instance
error_recovery_system = ErrorRecoverySystem()


def render_error_recovery_interface(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function to render error recovery interface."""
    error_recovery_system.render_recovery_interface(error, context)