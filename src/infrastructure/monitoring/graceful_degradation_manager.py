"""
Graceful Degradation Manager

This module provides graceful degradation patterns for UI components when services are unavailable.
It manages fallback functionality and provides alternative user experiences.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import streamlit as st

from .service_integration_validator import ServiceIntegrationValidator, ServiceStatus, DependencyStatus

logger = logging.getLogger(__name__)


class DegradationLevel(Enum):
    """Levels of service degradation"""
    FULL_FUNCTIONALITY = "full"
    PARTIAL_FUNCTIONALITY = "partial"
    MINIMAL_FUNCTIONALITY = "minimal"
    NO_FUNCTIONALITY = "none"


@dataclass
class DegradationPlan:
    """Plan for handling service degradation"""
    component_name: str
    degradation_level: DegradationLevel
    available_features: List[str]
    disabled_features: List[str]
    fallback_message: str
    recovery_actions: List[str]


class GracefulDegradationManager:
    """
    Manages graceful degradation for UI components when services are unavailable
    """
    
    def __init__(self, service_validator: ServiceIntegrationValidator):
        self.service_validator = service_validator
        self.degradation_plans: Dict[str, DegradationPlan] = {}
        self.fallback_components: Dict[str, Callable] = {}
        self.user_notifications: List[str] = []
        
        # Initialize default degradation plans
        self._initialize_degradation_plans()
        self._initialize_fallback_components()
    
    def _initialize_degradation_plans(self):
        """Initialize default degradation plans for components"""
        self.degradation_plans.update({
            'upload_interface': DegradationPlan(
                component_name='upload_interface',
                degradation_level=DegradationLevel.PARTIAL_FUNCTIONALITY,
                available_features=['file_selection', 'basic_validation'],
                disabled_features=['document_processing', 'metadata_extraction'],
                fallback_message="Document upload is available, but processing is temporarily disabled.",
                recovery_actions=['Check file storage service', 'Verify document processor']
            ),
            'qa_interface': DegradationPlan(
                component_name='qa_interface',
                degradation_level=DegradationLevel.MINIMAL_FUNCTIONALITY,
                available_features=['question_input', 'basic_search'],
                disabled_features=['ai_responses', 'context_retrieval', 'knowledge_graph_queries'],
                fallback_message="Q&A interface is in limited mode. AI responses are temporarily unavailable.",
                recovery_actions=['Check API connectivity', 'Verify knowledge graph service']
            ),
            'template_interface': DegradationPlan(
                component_name='template_interface',
                degradation_level=DegradationLevel.PARTIAL_FUNCTIONALITY,
                available_features=['template_selection', 'manual_input'],
                disabled_features=['auto_generation', 'ai_assistance', 'validation'],
                fallback_message="Template interface is available with manual input only.",
                recovery_actions=['Check template generator service', 'Verify AI services']
            ),
            'health_status': DegradationPlan(
                component_name='health_status',
                degradation_level=DegradationLevel.FULL_FUNCTIONALITY,
                available_features=['basic_status', 'error_reporting'],
                disabled_features=[],
                fallback_message="System status monitoring is operational.",
                recovery_actions=[]
            ),
            'document_manager': DegradationPlan(
                component_name='document_manager',
                degradation_level=DegradationLevel.PARTIAL_FUNCTIONALITY,
                available_features=['file_listing', 'basic_operations'],
                disabled_features=['metadata_display', 'advanced_search', 'processing_status'],
                fallback_message="Document management is available with limited functionality.",
                recovery_actions=['Check database connectivity', 'Verify file storage']
            )
        })
    
    def _initialize_fallback_components(self):
        """Initialize fallback UI components"""
        self.fallback_components.update({
            'upload_interface': self._render_fallback_upload,
            'qa_interface': self._render_fallback_qa,
            'template_interface': self._render_fallback_template,
            'health_status': self._render_fallback_health,
            'document_manager': self._render_fallback_document_manager
        })
    
    def assess_component_degradation(self, component_name: str) -> DegradationPlan:
        """
        Assess the degradation level for a component based on service availability
        
        Args:
            component_name: Name of the UI component
            
        Returns:
            DegradationPlan with current degradation status
        """
        dependency_status = self.service_validator.check_dependencies(component_name)
        
        if not dependency_status.can_function:
            # Component cannot function at all
            plan = DegradationPlan(
                component_name=component_name,
                degradation_level=DegradationLevel.NO_FUNCTIONALITY,
                available_features=[],
                disabled_features=dependency_status.required_services,
                fallback_message=f"{component_name} is temporarily unavailable due to service issues.",
                recovery_actions=[f"Restore {service}" for service in dependency_status.missing_services]
            )
        elif dependency_status.missing_services:
            # Partial functionality available
            base_plan = self.degradation_plans.get(component_name)
            if base_plan:
                plan = DegradationPlan(
                    component_name=component_name,
                    degradation_level=DegradationLevel.PARTIAL_FUNCTIONALITY,
                    available_features=base_plan.available_features,
                    disabled_features=base_plan.disabled_features + dependency_status.missing_services,
                    fallback_message=f"{base_plan.fallback_message} Missing services: {', '.join(dependency_status.missing_services)}",
                    recovery_actions=base_plan.recovery_actions
                )
            else:
                plan = DegradationPlan(
                    component_name=component_name,
                    degradation_level=DegradationLevel.PARTIAL_FUNCTIONALITY,
                    available_features=['basic_functionality'],
                    disabled_features=dependency_status.missing_services,
                    fallback_message=f"{component_name} is running with limited functionality.",
                    recovery_actions=[f"Restore {service}" for service in dependency_status.missing_services]
                )
        else:
            # Full functionality available
            plan = DegradationPlan(
                component_name=component_name,
                degradation_level=DegradationLevel.FULL_FUNCTIONALITY,
                available_features=dependency_status.available_services,
                disabled_features=[],
                fallback_message="All services are operational.",
                recovery_actions=[]
            )
        
        return plan
    
    def apply_degradation(self, component_name: str) -> Dict[str, Any]:
        """
        Apply graceful degradation for a component
        
        Args:
            component_name: Name of the UI component
            
        Returns:
            Dictionary with degradation status and UI modifications
        """
        degradation_plan = self.assess_component_degradation(component_name)
        
        result = {
            'component': component_name,
            'degradation_level': degradation_plan.degradation_level.value,
            'available_features': degradation_plan.available_features,
            'disabled_features': degradation_plan.disabled_features,
            'message': degradation_plan.fallback_message,
            'recovery_actions': degradation_plan.recovery_actions,
            'fallback_rendered': False
        }
        
        # Apply UI modifications based on degradation level
        if degradation_plan.degradation_level == DegradationLevel.NO_FUNCTIONALITY:
            if component_name in self.fallback_components:
                self.fallback_components[component_name](degradation_plan)
                result['fallback_rendered'] = True
        elif degradation_plan.degradation_level in [DegradationLevel.PARTIAL_FUNCTIONALITY, DegradationLevel.MINIMAL_FUNCTIONALITY]:
            self._show_degradation_warning(degradation_plan)
        
        return result
    
    def _show_degradation_warning(self, plan: DegradationPlan):
        """Show degradation warning to user"""
        if plan.degradation_level != DegradationLevel.FULL_FUNCTIONALITY:
            st.warning(f"⚠️ {plan.fallback_message}")
            
            if plan.recovery_actions:
                with st.expander("Recovery Actions"):
                    for action in plan.recovery_actions:
                        st.write(f"• {action}")
    
    def get_system_degradation_status(self) -> Dict[str, Any]:
        """Get overall system degradation status"""
        all_components = list(self.degradation_plans.keys())
        component_statuses = {}
        
        for component in all_components:
            component_statuses[component] = self.assess_component_degradation(component)
        
        # Calculate overall degradation level
        degradation_levels = [status.degradation_level for status in component_statuses.values()]
        
        if all(level == DegradationLevel.FULL_FUNCTIONALITY for level in degradation_levels):
            overall_level = DegradationLevel.FULL_FUNCTIONALITY
        elif any(level == DegradationLevel.NO_FUNCTIONALITY for level in degradation_levels):
            overall_level = DegradationLevel.MINIMAL_FUNCTIONALITY
        else:
            overall_level = DegradationLevel.PARTIAL_FUNCTIONALITY
        
        return {
            'overall_degradation': overall_level.value,
            'component_statuses': {name: {
                'level': status.degradation_level.value,
                'available_features': status.available_features,
                'disabled_features': status.disabled_features,
                'message': status.fallback_message
            } for name, status in component_statuses.items()},
            'total_components': len(all_components),
            'fully_functional': sum(1 for s in component_statuses.values() if s.degradation_level == DegradationLevel.FULL_FUNCTIONALITY),
            'degraded_components': sum(1 for s in component_statuses.values() if s.degradation_level != DegradationLevel.FULL_FUNCTIONALITY)
        }
    
    # Fallback component renderers
    def _render_fallback_upload(self, plan: DegradationPlan):
        """Render fallback upload interface"""
        st.error("📁 Document Upload Unavailable")
        st.write(plan.fallback_message)
        st.info("You can try again later or contact support if the issue persists.")
        
        if plan.recovery_actions:
            with st.expander("Troubleshooting Steps"):
                for action in plan.recovery_actions:
                    st.write(f"• {action}")
    
    def _render_fallback_qa(self, plan: DegradationPlan):
        """Render fallback Q&A interface"""
        st.error("❓ Q&A Service Unavailable")
        st.write(plan.fallback_message)
        
        # Provide basic search functionality if possible
        st.subheader("Basic Search")
        search_query = st.text_input("Search documents (basic text search only)")
        if search_query:
            st.info("Advanced AI-powered search is temporarily unavailable. Please try basic keyword search.")
        
        if plan.recovery_actions:
            with st.expander("Troubleshooting Steps"):
                for action in plan.recovery_actions:
                    st.write(f"• {action}")
    
    def _render_fallback_template(self, plan: DegradationPlan):
        """Render fallback template interface"""
        st.error("📄 Template Generation Unavailable")
        st.write(plan.fallback_message)
        
        # Provide manual template options
        st.subheader("Manual Template Options")
        st.info("You can download a blank template and fill it manually:")
        
        if st.button("Download Blank QME Template"):
            st.success("Template download would be available here")
        
        if plan.recovery_actions:
            with st.expander("Troubleshooting Steps"):
                for action in plan.recovery_actions:
                    st.write(f"• {action}")
    
    def _render_fallback_health(self, plan: DegradationPlan):
        """Render fallback health status"""
        st.error("🏥 System Health Monitoring Limited")
        st.write(plan.fallback_message)
        
        # Show basic system info
        st.subheader("Basic System Information")
        st.write("• Application is running")
        st.write("• Some services may be unavailable")
        
        if plan.recovery_actions:
            with st.expander("Troubleshooting Steps"):
                for action in plan.recovery_actions:
                    st.write(f"• {action}")
    
    def _render_fallback_document_manager(self, plan: DegradationPlan):
        """Render fallback document manager"""
        st.error("📋 Document Management Limited")
        st.write(plan.fallback_message)
        
        # Provide basic file operations
        st.subheader("Basic File Operations")
        st.info("Advanced document management features are temporarily unavailable.")
        
        if plan.recovery_actions:
            with st.expander("Troubleshooting Steps"):
                for action in plan.recovery_actions:
                    st.write(f"• {action}")


# Utility functions for easy integration
def check_component_health(component_name: str, service_validator: ServiceIntegrationValidator) -> bool:
    """Quick health check for a component"""
    dependency_status = service_validator.check_dependencies(component_name)
    return dependency_status.can_function


def apply_graceful_degradation(component_name: str, service_validator: ServiceIntegrationValidator) -> Dict[str, Any]:
    """Apply graceful degradation for a component"""
    degradation_manager = GracefulDegradationManager(service_validator)
    return degradation_manager.apply_degradation(component_name)


def show_service_status_banner(service_validator: ServiceIntegrationValidator):
    """Show system-wide service status banner"""
    degradation_manager = GracefulDegradationManager(service_validator)
    system_status = degradation_manager.get_system_degradation_status()
    
    if system_status['overall_degradation'] != 'full':
        degraded_count = system_status['degraded_components']
        total_count = system_status['total_components']
        
        st.warning(f"⚠️ System Status: {degraded_count}/{total_count} components have limited functionality")
        
        with st.expander("View Component Status"):
            for component, status in system_status['component_statuses'].items():
                if status['level'] != 'full':
                    st.write(f"**{component}**: {status['message']}")