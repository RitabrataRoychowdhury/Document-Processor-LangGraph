"""
Fallback Renderer

Provides fallback UI components when primary components fail to load,
ensuring graceful degradation and maintaining user experience.
"""

import streamlit as st
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass

from src.infrastructure.monitoring.error_message_formatter import format_user_friendly_error, ErrorCategory
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class FallbackType(Enum):
    """Types of fallback components."""
    SIMPLE_MESSAGE = "simple_message"
    BASIC_FUNCTIONALITY = "basic_functionality"
    ALTERNATIVE_COMPONENT = "alternative_component"
    OFFLINE_MODE = "offline_mode"
    MAINTENANCE_MODE = "maintenance_mode"


@dataclass
class FallbackConfig:
    """Configuration for fallback rendering."""
    fallback_type: FallbackType
    title: str
    message: str
    show_retry_button: bool = True
    show_alternative_actions: bool = True
    alternative_actions: Optional[List[Dict[str, Any]]] = None
    custom_content: Optional[Callable] = None


class FallbackRenderer:
    """
    Renders fallback UI components when primary components fail.
    
    Provides graceful degradation with user-friendly error messages,
    retry options, and alternative functionality when available.
    """
    
    def __init__(self):
        """Initialize the fallback renderer."""
        self.fallback_configs = self._initialize_fallback_configs()
    
    def render_fallback(self, 
                       component_name: str,
                       error: Exception,
                       context: Optional[Dict[str, Any]] = None,
                       custom_config: Optional[FallbackConfig] = None) -> None:
        """
        Render a fallback component when the primary component fails.
        
        Args:
            component_name: Name of the failed component
            error: The exception that caused the failure
            context: Additional context about the failure
            custom_config: Custom fallback configuration
        """
        # Format the error for user display
        user_error = format_user_friendly_error(error, context)
        
        # Get fallback configuration
        config = custom_config or self._get_fallback_config(component_name, user_error.category)
        
        # Render the fallback UI
        self._render_fallback_ui(component_name, user_error, config, context)
    
    def _initialize_fallback_configs(self) -> Dict[str, Dict[ErrorCategory, FallbackConfig]]:
        """Initialize fallback configurations for different components and error types."""
        return {
            "upload_interface": {
                ErrorCategory.SERVICE_UNAVAILABLE: FallbackConfig(
                    fallback_type=FallbackType.BASIC_FUNCTIONALITY,
                    title="Basic Upload Available",
                    message="Advanced upload features are unavailable, but you can still upload files using basic functionality.",
                    alternative_actions=[
                        {"label": "📁 Basic File Upload", "action": "basic_upload"},
                        {"label": "📄 View Uploaded Files", "action": "view_files"}
                    ]
                ),
                ErrorCategory.CONFIGURATION: FallbackConfig(
                    fallback_type=FallbackType.OFFLINE_MODE,
                    title="Upload Service Configuration Issue",
                    message="The upload service needs configuration. You can still view existing documents.",
                    alternative_actions=[
                        {"label": "📄 View Documents", "action": "view_documents"},
                        {"label": "🔧 Configuration Help", "action": "config_help"}
                    ]
                )
            },
            "qa_interface": {
                ErrorCategory.SERVICE_UNAVAILABLE: FallbackConfig(
                    fallback_type=FallbackType.ALTERNATIVE_COMPONENT,
                    title="Q&A Service Unavailable",
                    message="The AI-powered Q&A service is unavailable. You can still browse documents and use basic search.",
                    alternative_actions=[
                        {"label": "🔍 Search Documents", "action": "search_documents"},
                        {"label": "📄 Browse Documents", "action": "browse_documents"}
                    ]
                ),
                ErrorCategory.AUTHENTICATION: FallbackConfig(
                    fallback_type=FallbackType.OFFLINE_MODE,
                    title="API Authentication Required",
                    message="Q&A features require API authentication. Please configure your API keys.",
                    alternative_actions=[
                        {"label": "🔧 Configure API Keys", "action": "configure_api"},
                        {"label": "📖 View Documentation", "action": "view_docs"}
                    ]
                )
            },
            "template_generator": {
                ErrorCategory.SERVICE_UNAVAILABLE: FallbackConfig(
                    fallback_type=FallbackType.BASIC_FUNCTIONALITY,
                    title="Basic Template Generation Available",
                    message="Advanced template features are unavailable. You can still generate basic templates.",
                    alternative_actions=[
                        {"label": "📋 Basic Template", "action": "basic_template"},
                        {"label": "📄 Template Library", "action": "template_library"}
                    ]
                ),
                ErrorCategory.FILE_PROCESSING: FallbackConfig(
                    fallback_type=FallbackType.ALTERNATIVE_COMPONENT,
                    title="Document Processing Issue",
                    message="There was an issue processing your document. You can try with a different file or use manual input.",
                    alternative_actions=[
                        {"label": "📤 Try Different File", "action": "retry_upload"},
                        {"label": "✏️ Manual Input", "action": "manual_input"}
                    ]
                )
            },
            "system_status": {
                ErrorCategory.SERVICE_UNAVAILABLE: FallbackConfig(
                    fallback_type=FallbackType.SIMPLE_MESSAGE,
                    title="System Status Unavailable",
                    message="Unable to retrieve system status. The application may still be functional.",
                    show_alternative_actions=False
                )
            },
            "document_management": {
                ErrorCategory.SERVICE_UNAVAILABLE: FallbackConfig(
                    fallback_type=FallbackType.BASIC_FUNCTIONALITY,
                    title="Basic Document Management",
                    message="Advanced document management features are unavailable. Basic file operations are still available.",
                    alternative_actions=[
                        {"label": "📁 List Files", "action": "list_files"},
                        {"label": "📤 Upload New", "action": "upload_new"}
                    ]
                )
            }
        }
    
    def _get_fallback_config(self, component_name: str, error_category: ErrorCategory) -> FallbackConfig:
        """Get fallback configuration for a component and error category."""
        component_configs = self.fallback_configs.get(component_name, {})
        
        # Try to get specific config for this error category
        config = component_configs.get(error_category)
        
        if config:
            return config
        
        # Fall back to generic config based on error category
        return self._get_generic_fallback_config(component_name, error_category)
    
    def _get_generic_fallback_config(self, component_name: str, error_category: ErrorCategory) -> FallbackConfig:
        """Get generic fallback configuration based on error category."""
        generic_configs = {
            ErrorCategory.SERVICE_UNAVAILABLE: FallbackConfig(
                fallback_type=FallbackType.SIMPLE_MESSAGE,
                title="Service Unavailable",
                message=f"The {component_name.replace('_', ' ').title()} service is temporarily unavailable.",
                alternative_actions=[
                    {"label": "🔄 Retry", "action": "retry"},
                    {"label": "🏠 Go Home", "action": "go_home"}
                ]
            ),
            ErrorCategory.CONFIGURATION: FallbackConfig(
                fallback_type=FallbackType.MAINTENANCE_MODE,
                title="Configuration Required",
                message=f"The {component_name.replace('_', ' ').title()} requires configuration before it can be used.",
                alternative_actions=[
                    {"label": "🔧 Configuration", "action": "configure"},
                    {"label": "📖 Help", "action": "help"}
                ]
            ),
            ErrorCategory.AUTHENTICATION: FallbackConfig(
                fallback_type=FallbackType.OFFLINE_MODE,
                title="Authentication Required",
                message="This feature requires authentication. Please configure your credentials.",
                alternative_actions=[
                    {"label": "🔑 Configure Auth", "action": "configure_auth"},
                    {"label": "📖 Documentation", "action": "docs"}
                ]
            ),
            ErrorCategory.NETWORK: FallbackConfig(
                fallback_type=FallbackType.OFFLINE_MODE,
                title="Network Issue",
                message="Unable to connect to required services. Some features may be limited.",
                alternative_actions=[
                    {"label": "🔄 Retry Connection", "action": "retry"},
                    {"label": "📱 Offline Mode", "action": "offline_mode"}
                ]
            )
        }
        
        return generic_configs.get(error_category, FallbackConfig(
            fallback_type=FallbackType.SIMPLE_MESSAGE,
            title="Component Unavailable",
            message=f"The {component_name.replace('_', ' ').title()} is temporarily unavailable.",
            alternative_actions=[
                {"label": "🔄 Retry", "action": "retry"},
                {"label": "🏠 Home", "action": "home"}
            ]
        ))
    
    def _render_fallback_ui(self, 
                           component_name: str,
                           user_error: Any,
                           config: FallbackConfig,
                           context: Optional[Dict[str, Any]]) -> None:
        """Render the fallback UI based on configuration."""
        # Create a container for the fallback content
        with st.container():
            # Render based on fallback type
            if config.fallback_type == FallbackType.SIMPLE_MESSAGE:
                self._render_simple_message_fallback(config, user_error)
            
            elif config.fallback_type == FallbackType.BASIC_FUNCTIONALITY:
                self._render_basic_functionality_fallback(component_name, config, user_error)
            
            elif config.fallback_type == FallbackType.ALTERNATIVE_COMPONENT:
                self._render_alternative_component_fallback(component_name, config, user_error)
            
            elif config.fallback_type == FallbackType.OFFLINE_MODE:
                self._render_offline_mode_fallback(config, user_error)
            
            elif config.fallback_type == FallbackType.MAINTENANCE_MODE:
                self._render_maintenance_mode_fallback(config, user_error)
            
            # Render custom content if provided
            if config.custom_content:
                try:
                    config.custom_content()
                except Exception as e:
                    logger.error(f"Error rendering custom fallback content: {e}")
                    st.error("Unable to render custom content")
    
    def _render_simple_message_fallback(self, config: FallbackConfig, user_error: Any) -> None:
        """Render a simple message fallback."""
        st.warning(f"⚠️ {config.title}")
        st.info(config.message)
        
        # Show error details in expandable section
        with st.expander("🔍 Error Details", expanded=False):
            st.write(f"**Error Type:** {user_error.category.value.title()}")
            st.write(f"**Message:** {user_error.message}")
            if user_error.technical_details:
                st.code(user_error.technical_details)
        
        # Show recovery suggestions
        if user_error.recovery_suggestions:
            st.markdown("**💡 Suggested Solutions:**")
            for i, suggestion in enumerate(user_error.recovery_suggestions, 1):
                st.write(f"{i}. {suggestion}")
        
        # Render action buttons
        if config.show_retry_button or config.show_alternative_actions:
            self._render_action_buttons(config)
    
    def _render_basic_functionality_fallback(self, component_name: str, config: FallbackConfig, user_error: Any) -> None:
        """Render basic functionality fallback."""
        st.info(f"🔧 {config.title}")
        st.write(config.message)
        
        # Render basic version of the component
        if component_name == "upload_interface":
            self._render_basic_upload_interface()
        elif component_name == "template_generator":
            self._render_basic_template_generator()
        elif component_name == "document_management":
            self._render_basic_document_management()
        
        # Render action buttons
        if config.show_alternative_actions:
            self._render_action_buttons(config)
    
    def _render_alternative_component_fallback(self, component_name: str, config: FallbackConfig, user_error: Any) -> None:
        """Render alternative component fallback."""
        st.warning(f"⚠️ {config.title}")
        st.write(config.message)
        
        # Render alternative functionality
        if component_name == "qa_interface":
            self._render_basic_search_interface()
        elif component_name == "template_generator":
            self._render_template_library()
        
        # Render action buttons
        self._render_action_buttons(config)
    
    def _render_offline_mode_fallback(self, config: FallbackConfig, user_error: Any) -> None:
        """Render offline mode fallback."""
        st.error(f"🔌 {config.title}")
        st.write(config.message)
        
        st.markdown("**📱 Offline Mode Features:**")
        st.write("• View previously uploaded documents")
        st.write("• Access cached templates")
        st.write("• Basic file operations")
        
        # Render action buttons
        self._render_action_buttons(config)
    
    def _render_maintenance_mode_fallback(self, config: FallbackConfig, user_error: Any) -> None:
        """Render maintenance mode fallback."""
        st.warning(f"🚧 {config.title}")
        st.write(config.message)
        
        st.markdown("**🔧 Configuration Steps:**")
        if user_error.category == ErrorCategory.AUTHENTICATION:
            st.write("1. Set up your API keys in the .env file")
            st.write("2. Restart the application")
            st.write("3. Verify the configuration in System Status")
        else:
            st.write("1. Check the configuration documentation")
            st.write("2. Verify all required settings")
            st.write("3. Restart the application")
        
        # Render action buttons
        self._render_action_buttons(config)
    
    def _render_action_buttons(self, config: FallbackConfig) -> None:
        """Render action buttons for fallback UI."""
        if not (config.show_retry_button or config.show_alternative_actions):
            return
        
        st.markdown("---")
        
        # Calculate number of columns needed
        num_actions = 0
        if config.show_retry_button:
            num_actions += 1
        if config.alternative_actions:
            num_actions += len(config.alternative_actions)
        
        if num_actions == 0:
            return
        
        # Create columns for buttons
        cols = st.columns(min(num_actions, 4))  # Max 4 columns
        col_index = 0
        
        # Retry button
        if config.show_retry_button:
            with cols[col_index]:
                if st.button("🔄 Retry", key=f"retry_{id(config)}"):
                    st.rerun()
            col_index += 1
        
        # Alternative action buttons
        if config.alternative_actions:
            for action in config.alternative_actions:
                if col_index >= len(cols):
                    break
                
                with cols[col_index]:
                    if st.button(action["label"], key=f"action_{action['action']}_{id(config)}"):
                        self._handle_action(action["action"])
                col_index += 1
    
    def _handle_action(self, action: str) -> None:
        """Handle fallback action button clicks."""
        if action == "retry":
            st.rerun()
        elif action == "go_home" or action == "home":
            st.session_state.current_page = "Upload Documents"
            st.rerun()
        elif action == "configure":
            st.session_state.current_page = "System Status"
            st.rerun()
        elif action == "configure_api" or action == "configure_auth":
            st.info("Please configure your API keys in the .env file and restart the application.")
        elif action == "help" or action == "docs":
            st.info("Please refer to the documentation for configuration instructions.")
        elif action == "view_documents":
            st.session_state.current_page = "Document Management"
            st.rerun()
        else:
            st.info(f"Action '{action}' would be handled here in a full implementation.")
    
    # Basic component implementations for fallback functionality
    
    def _render_basic_upload_interface(self) -> None:
        """Render basic upload interface."""
        st.subheader("📤 Basic File Upload")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['pdf', 'docx', 'txt'],
            help="Upload a document for processing"
        )
        
        if uploaded_file:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            st.info("Advanced processing features are unavailable. The file has been uploaded successfully.")
    
    def _render_basic_template_generator(self) -> None:
        """Render basic template generator."""
        st.subheader("📋 Basic Template Generator")
        
        st.write("**Patient Information:**")
        col1, col2 = st.columns(2)
        
        with col1:
            patient_name = st.text_input("Patient Name")
            case_number = st.text_input("Case Number")
        
        with col2:
            exam_date = st.date_input("Examination Date")
            doctor_name = st.text_input("Doctor Name")
        
        if st.button("Generate Basic Template"):
            if patient_name and case_number:
                st.success("✅ Basic template would be generated with the provided information.")
                st.info("Advanced AI-powered features are unavailable in basic mode.")
            else:
                st.warning("Please fill in required fields: Patient Name and Case Number")
    
    def _render_basic_document_management(self) -> None:
        """Render basic document management."""
        st.subheader("📄 Basic Document Management")
        
        st.info("Advanced document management features are unavailable. Basic operations:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📁 List Files"):
                st.info("File listing functionality would be available here.")
        
        with col2:
            if st.button("📤 Upload New"):
                st.info("Basic upload functionality would be available here.")
    
    def _render_basic_search_interface(self) -> None:
        """Render basic search interface."""
        st.subheader("🔍 Basic Document Search")
        
        search_query = st.text_input("Search documents", placeholder="Enter search terms...")
        
        if st.button("Search") and search_query:
            st.info(f"Searching for: '{search_query}'")
            st.write("Basic search functionality would return results here.")
    
    def _render_template_library(self) -> None:
        """Render template library."""
        st.subheader("📚 Template Library")
        
        templates = [
            "Basic QME Report Template",
            "Simple Medical Evaluation",
            "Standard Assessment Form"
        ]
        
        selected_template = st.selectbox("Choose a template:", templates)
        
        if st.button("Use Template"):
            st.success(f"✅ Using template: {selected_template}")
            st.info("Template would be loaded for customization.")


# Global fallback renderer instance
fallback_renderer = FallbackRenderer()


def render_component_fallback(component_name: str, 
                            error: Exception,
                            context: Optional[Dict[str, Any]] = None,
                            custom_config: Optional[FallbackConfig] = None) -> None:
    """Convenience function to render a component fallback."""
    fallback_renderer.render_fallback(component_name, error, context, custom_config)