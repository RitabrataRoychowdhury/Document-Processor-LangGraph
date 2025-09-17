"""QME template generation workflow state management."""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.state.workflow_state import WorkflowState
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class TemplateState(WorkflowState):
    """State manager for QME template generation workflows.
    
    Implements Single Responsibility Principle - manages template-specific state.
    Extends WorkflowState with template generation functionality.
    """
    
    def __init__(self, state_id: str = None, correlation_id: str = None):
        super().__init__(state_id, correlation_id)
        self._workflow_type = "template"
    
    def initialize_state(self, initial_data: Dict[str, Any]) -> None:
        """Initialize template generation state."""
        # Add template-specific required data
        template_data = {
            'patient_document_id': initial_data.get('patient_document_id'),
            'patient_file_path': initial_data.get('patient_file_path'),
            'template_type': initial_data.get('template_type', 'qme_report'),
            'generation_stage': 'initialization',
            'patient_info_extracted': False,
            'diagnoses_identified': [],
            'impairment_ratings_found': [],
            'template_sections': {},
            'missing_information': [],
            'template_generated': False,
            'output_file_path': None,
            'generation_errors': [],
            **initial_data
        }
        
        super().initialize_state(template_data)
        logger.info(f"Initialized template generation state for patient document "
                   f"{template_data.get('patient_file_path')}")
    
    def validate_state(self, state_data: Dict[str, Any]) -> bool:
        """Validate template generation state."""
        if not super().validate_state(state_data):
            return False
        
        # Template-specific validations
        patient_document_id = state_data.get('patient_document_id')
        if not patient_document_id:
            logger.error("Missing patient_document_id in template state")
            return False
        
        template_type = state_data.get('template_type')
        valid_types = self.get_valid_template_types()
        if template_type not in valid_types:
            logger.error(f"Invalid template_type: {template_type}")
            return False
        
        generation_stage = state_data.get('generation_stage')
        valid_stages = self.get_valid_generation_stages()
        if generation_stage not in valid_stages:
            logger.error(f"Invalid generation_stage: {generation_stage}")
            return False
        
        return True
    
    def get_required_keys(self) -> List[str]:
        """Get required keys for template generation state."""
        base_keys = super().get_required_keys()
        template_keys = [
            'patient_document_id',
            'template_type',
            'generation_stage'
        ]
        return base_keys + template_keys
    
    def get_valid_template_types(self) -> List[str]:
        """Get valid template types."""
        return [
            'qme_report',
            'medical_evaluation',
            'impairment_assessment',
            'disability_report'
        ]
    
    def get_valid_generation_stages(self) -> List[str]:
        """Get valid generation stages for template workflow."""
        return [
            'initialization',
            'patient_info_extraction',
            'diagnosis_identification',
            'impairment_rating_lookup',
            'template_population',
            'missing_info_detection',
            'template_generation',
            'file_output',
            'completed',
            'failed'
        ]
    
    def start_patient_info_extraction(self) -> None:
        """Start patient information extraction stage."""
        self.update_state({
            'generation_stage': 'patient_info_extraction',
            'current_step': 'extracting_patient_info'
        })
        self.update_progress('patient_info_extraction', 15)
        logger.debug(f"Started patient info extraction for template {self.state_id}")
    
    def complete_patient_info_extraction(self, patient_info: Dict[str, Any]) -> None:
        """Complete patient information extraction stage."""
        self.update_state({
            'generation_stage': 'patient_info_extraction_complete',
            'patient_info_extracted': True,
            'patient_info': patient_info,
            'patient_extraction_completed_at': datetime.now().isoformat()
        })
        self.update_progress('patient_info_extraction_complete', 30)
        logger.info(f"Completed patient info extraction for template {self.state_id}")
    
    def start_diagnosis_identification(self) -> None:
        """Start diagnosis identification stage."""
        self.update_state({
            'generation_stage': 'diagnosis_identification',
            'current_step': 'identifying_diagnoses'
        })
        self.update_progress('diagnosis_identification', 45)
        logger.debug(f"Started diagnosis identification for template {self.state_id}")
    
    def complete_diagnosis_identification(self, diagnoses: List[Dict[str, Any]]) -> None:
        """Complete diagnosis identification stage."""
        self.update_state({
            'generation_stage': 'diagnosis_identification_complete',
            'diagnoses_identified': diagnoses,
            'diagnosis_count': len(diagnoses),
            'diagnosis_completed_at': datetime.now().isoformat()
        })
        self.update_progress('diagnosis_identification_complete', 60)
        logger.info(f"Completed diagnosis identification for template {self.state_id} "
                   f"({len(diagnoses)} diagnoses)")
    
    def start_impairment_rating_lookup(self) -> None:
        """Start impairment rating lookup stage."""
        self.update_state({
            'generation_stage': 'impairment_rating_lookup',
            'current_step': 'looking_up_impairment_ratings'
        })
        self.update_progress('impairment_rating_lookup', 70)
        logger.debug(f"Started impairment rating lookup for template {self.state_id}")
    
    def complete_impairment_rating_lookup(self, impairment_ratings: List[Dict[str, Any]]) -> None:
        """Complete impairment rating lookup stage."""
        self.update_state({
            'generation_stage': 'impairment_rating_lookup_complete',
            'impairment_ratings_found': impairment_ratings,
            'impairment_rating_count': len(impairment_ratings),
            'impairment_lookup_completed_at': datetime.now().isoformat()
        })
        self.update_progress('impairment_rating_lookup_complete', 80)
        logger.info(f"Completed impairment rating lookup for template {self.state_id} "
                   f"({len(impairment_ratings)} ratings)")
    
    def start_template_population(self) -> None:
        """Start template population stage."""
        self.update_state({
            'generation_stage': 'template_population',
            'current_step': 'populating_template'
        })
        self.update_progress('template_population', 85)
        logger.debug(f"Started template population for template {self.state_id}")
    
    def complete_template_population(self, template_sections: Dict[str, Any],
                                   missing_info: List[str] = None) -> None:
        """Complete template population stage."""
        self.update_state({
            'generation_stage': 'template_population_complete',
            'template_sections': template_sections,
            'missing_information': missing_info or [],
            'template_population_completed_at': datetime.now().isoformat()
        })
        self.update_progress('template_population_complete', 90)
        logger.info(f"Completed template population for template {self.state_id}")
    
    def start_template_generation(self) -> None:
        """Start template file generation stage."""
        self.update_state({
            'generation_stage': 'template_generation',
            'current_step': 'generating_template_file'
        })
        self.update_progress('template_generation', 95)
        logger.debug(f"Started template file generation for template {self.state_id}")
    
    def complete_template_generation(self, output_file_path: str, 
                                   generation_metadata: Dict[str, Any] = None) -> None:
        """Complete template file generation stage."""
        completion_data = {
            'generation_stage': 'template_generation_complete',
            'template_generated': True,
            'output_file_path': output_file_path,
            'template_generation_completed_at': datetime.now().isoformat()
        }
        
        if generation_metadata:
            completion_data['generation_metadata'] = generation_metadata
        
        self.update_state(completion_data)
        self.update_progress('template_generation_complete', 100)
        logger.info(f"Completed template generation for template {self.state_id}: {output_file_path}")
    
    def add_missing_information(self, section: str, missing_items: List[str]) -> None:
        """Add missing information for a template section."""
        current_missing = self.get_value('missing_information', [])
        
        for item in missing_items:
            missing_entry = {
                'section': section,
                'missing_item': item,
                'timestamp': datetime.now().isoformat()
            }
            current_missing.append(missing_entry)
        
        self.update_state({'missing_information': current_missing})
        logger.debug(f"Added {len(missing_items)} missing items for section '{section}' "
                    f"in template {self.state_id}")
    
    def add_generation_error(self, stage: str, error_message: str, 
                           error_details: Dict[str, Any] = None) -> None:
        """Add a generation error to the state."""
        error_entry = {
            'stage': stage,
            'error_message': error_message,
            'timestamp': datetime.now().isoformat(),
            'details': error_details or {}
        }
        
        current_errors = self.get_value('generation_errors', [])
        current_errors.append(error_entry)
        
        self.update_state({
            'generation_errors': current_errors,
            'last_error': error_entry
        })
        
        logger.error(f"Added generation error for template {self.state_id} "
                    f"at stage {stage}: {error_message}")
    
    def get_generation_summary(self) -> Dict[str, Any]:
        """Get a summary of template generation."""
        base_summary = self.get_workflow_summary()
        
        template_summary = {
            'patient_document_id': self.get_value('patient_document_id'),
            'patient_file_path': self.get_value('patient_file_path'),
            'template_type': self.get_value('template_type'),
            'generation_stage': self.get_value('generation_stage'),
            'patient_info_extracted': self.get_value('patient_info_extracted', False),
            'diagnosis_count': self.get_value('diagnosis_count', 0),
            'impairment_rating_count': self.get_value('impairment_rating_count', 0),
            'missing_info_count': len(self.get_value('missing_information', [])),
            'template_generated': self.get_value('template_generated', False),
            'output_file_path': self.get_value('output_file_path'),
            'error_count': len(self.get_value('generation_errors', [])),
            'last_error': self.get_value('last_error')
        }
        
        return {**base_summary, **template_summary}
    
    def is_patient_info_extracted(self) -> bool:
        """Check if patient information is extracted."""
        return self.get_value('patient_info_extracted', False)
    
    def is_diagnoses_identified(self) -> bool:
        """Check if diagnoses are identified."""
        return len(self.get_value('diagnoses_identified', [])) > 0
    
    def is_impairment_ratings_found(self) -> bool:
        """Check if impairment ratings are found."""
        return len(self.get_value('impairment_ratings_found', [])) > 0
    
    def is_template_generated(self) -> bool:
        """Check if template is generated."""
        return self.get_value('template_generated', False)
    
    def get_patient_info(self) -> Optional[Dict[str, Any]]:
        """Get extracted patient information."""
        return self.get_value('patient_info')
    
    def get_diagnoses(self) -> List[Dict[str, Any]]:
        """Get identified diagnoses."""
        return self.get_value('diagnoses_identified', [])
    
    def get_impairment_ratings(self) -> List[Dict[str, Any]]:
        """Get found impairment ratings."""
        return self.get_value('impairment_ratings_found', [])
    
    def get_template_sections(self) -> Dict[str, Any]:
        """Get populated template sections."""
        return self.get_value('template_sections', {})
    
    def get_missing_information(self) -> List[Dict[str, Any]]:
        """Get missing information list."""
        return self.get_value('missing_information', [])
    
    def get_generation_errors(self) -> List[Dict[str, Any]]:
        """Get generation errors."""
        return self.get_value('generation_errors', [])
    
    def has_generation_errors(self) -> bool:
        """Check if there are generation errors."""
        return len(self.get_value('generation_errors', [])) > 0
    
    def get_output_file_path(self) -> Optional[str]:
        """Get output file path."""
        return self.get_value('output_file_path')
    
    def has_missing_information(self) -> bool:
        """Check if there is missing information."""
        return len(self.get_value('missing_information', [])) > 0