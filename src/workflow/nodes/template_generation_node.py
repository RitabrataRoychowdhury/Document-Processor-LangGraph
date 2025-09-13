"""QME template generation workflow node."""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.base.workflow_node import WorkflowNode, NodeResult
from src.services.qme_template_generator import QMETemplateGenerator
from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class TemplateGenerationNode(WorkflowNode):
    """Node for QME template generation.
    
    Implements Single Responsibility Principle - handles only template generation.
    Follows Dependency Inversion - depends on QMETemplateGenerator abstraction.
    """
    
    def __init__(self, template_generator: QMETemplateGenerator = None,
                 kg_repository: KnowledgeGraphRepository = None,
                 output_directory: str = "output/templates",
                 node_id: str = None, correlation_id: str = None):
        super().__init__(node_id, correlation_id)
        
        # Use dependency injection - don't create defaults if not provided
        if template_generator is None:
            raise ValueError("QMETemplateGenerator must be provided via dependency injection")
        if kg_repository is None:
            raise ValueError("KnowledgeGraphRepository must be provided via dependency injection")
            
        self.template_generator = template_generator
        self.kg_repository = kg_repository
        self.output_directory = output_directory
        
        # Ensure output directory exists
        os.makedirs(self.output_directory, exist_ok=True)
    
    def execute(self, state: Dict[str, Any]) -> NodeResult:
        """Execute QME template generation."""
        try:
            patient_document_id = state.get('patient_document_id') or state.get('document_id')
            patient_file_path = state.get('patient_file_path') or state.get('file_path')
            template_type = state.get('template_type', 'qme_report')
            
            logger.info(f"Starting template generation for patient document {patient_document_id} "
                       f"[correlation_id: {self.correlation_id}]")
            
            # Extract patient information from the processed document
            patient_info = self._extract_patient_information(state)
            
            # Identify diagnoses from entities or KG
            diagnoses = self._identify_diagnoses(state, patient_document_id)
            
            # Look up impairment ratings for diagnoses
            impairment_ratings = self._lookup_impairment_ratings(diagnoses)
            
            # Generate template sections
            template_sections = self._generate_template_sections(
                patient_info, diagnoses, impairment_ratings, state
            )
            
            # Identify missing information
            missing_information = self._identify_missing_information(template_sections)
            
            # Generate the actual template file
            output_file_path = self._generate_template_file(
                template_sections, patient_info, template_type, patient_document_id
            )
            
            # Calculate generation statistics
            generation_stats = {
                'patient_info_extracted': bool(patient_info),
                'diagnoses_found': len(diagnoses),
                'impairment_ratings_found': len(impairment_ratings),
                'template_sections_generated': len(template_sections),
                'missing_information_count': len(missing_information),
                'template_generated': bool(output_file_path),
                'output_file_size': os.path.getsize(output_file_path) if output_file_path and os.path.exists(output_file_path) else 0
            }
            
            result_data = {
                'patient_info': patient_info,
                'diagnoses_identified': diagnoses,
                'impairment_ratings_found': impairment_ratings,
                'template_sections': template_sections,
                'missing_information': missing_information,
                'output_file_path': output_file_path,
                'template_type': template_type,
                'generation_statistics': generation_stats,
                'template_generated': True
            }
            
            logger.info(f"Template generation completed: {output_file_path} "
                       f"({len(diagnoses)} diagnoses, {len(missing_information)} missing items) "
                       f"[correlation_id: {self.correlation_id}]")
            
            return NodeResult.success_result(
                f"Template generation completed: {os.path.basename(output_file_path) if output_file_path else 'template'}",
                data=result_data
            )
            
        except Exception as e:
            logger.error(f"Template generation failed: {e} [correlation_id: {self.correlation_id}]")
            return NodeResult.failure_result(
                f"Template generation failed: {str(e)}",
                error=e
            )
    
    def _extract_patient_information(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient information from processed document data."""
        patient_info = {}
        
        # Get entities from state
        entities = state.get('entities_extracted', [])
        
        # Extract patient names
        patient_entities = [e for e in entities if e.get('type') == 'patient']
        if patient_entities:
            patient_info['name'] = patient_entities[0].get('text', 'Unknown Patient')
        
        # Extract dates (could be DOB, injury date, etc.)
        date_entities = [e for e in entities if e.get('type') == 'date']
        if date_entities:
            patient_info['dates'] = [e.get('text') for e in date_entities]
        
        # Try to extract additional info from text
        extracted_text = state.get('extracted_text', '')
        patient_info.update(self._extract_patient_details_from_text(extracted_text))
        
        # Set defaults for missing information
        patient_info.setdefault('name', 'Unknown Patient')
        patient_info.setdefault('age', 'Unknown')
        patient_info.setdefault('gender', 'Unknown')
        patient_info.setdefault('case_number', 'Unknown')
        patient_info.setdefault('injury_date', 'Unknown')
        
        return patient_info
    
    def _extract_patient_details_from_text(self, text: str) -> Dict[str, Any]:
        """Extract additional patient details using text patterns."""
        import re
        
        details = {}
        
        # Age patterns
        age_patterns = [
            r'age[:\s]+(\d{1,3})',
            r'(\d{1,3})[- ]year[- ]old',
            r'patient.*?(\d{1,3}).*?years?'
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                age = int(match.group(1))
                if 0 < age < 120:  # Reasonable age range
                    details['age'] = age
                    break
        
        # Gender patterns
        gender_patterns = [
            r'\b(male|female|man|woman)\b',
            r'gender[:\s]+(male|female|m|f)\b'
        ]
        
        for pattern in gender_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                gender_text = match.group(1).lower()
                if gender_text in ['male', 'man', 'm']:
                    details['gender'] = 'Male'
                elif gender_text in ['female', 'woman', 'f']:
                    details['gender'] = 'Female'
                break
        
        # Case number patterns
        case_patterns = [
            r'case[:\s#]+([A-Z0-9-]+)',
            r'claim[:\s#]+([A-Z0-9-]+)',
            r'file[:\s#]+([A-Z0-9-]+)'
        ]
        
        for pattern in case_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                details['case_number'] = match.group(1)
                break
        
        return details
    
    def _identify_diagnoses(self, state: Dict[str, Any], document_id: str) -> List[Dict[str, Any]]:
        """Identify diagnoses from entities and knowledge graph."""
        diagnoses = []
        
        # Get diagnosis entities from state
        entities = state.get('entities_extracted', [])
        diagnosis_entities = [e for e in entities if e.get('type') == 'diagnosis']
        
        for entity in diagnosis_entities:
            diagnosis = {
                'description': entity.get('text', ''),
                'confidence': entity.get('confidence', 0.0),
                'source': 'entity_extraction',
                'context': entity.get('context', ''),
                'is_icd_code': entity.get('metadata', {}).get('is_icd_code', False)
            }
            diagnoses.append(diagnosis)
        
        # Try to get additional diagnoses from knowledge graph
        try:
            kg_diagnoses = self.kg_repository.get_nodes_by_type('Diagnosis')
            for kg_diagnosis in kg_diagnoses:
                if kg_diagnosis.get('properties', {}).get('document_id') == document_id:
                    diagnosis = {
                        'description': kg_diagnosis.get('properties', {}).get('description', ''),
                        'confidence': kg_diagnosis.get('properties', {}).get('confidence', 0.0),
                        'source': 'knowledge_graph',
                        'icd_code': kg_diagnosis.get('properties', {}).get('icd_code'),
                        'is_icd_code': kg_diagnosis.get('properties', {}).get('is_icd_code', False)
                    }
                    diagnoses.append(diagnosis)
        except Exception as e:
            logger.warning(f"Failed to retrieve diagnoses from knowledge graph: {e}")
        
        # Remove duplicates based on description
        unique_diagnoses = []
        seen_descriptions = set()
        
        for diagnosis in diagnoses:
            desc_key = diagnosis['description'].lower().strip()
            if desc_key not in seen_descriptions and len(desc_key) > 3:
                seen_descriptions.add(desc_key)
                unique_diagnoses.append(diagnosis)
        
        return unique_diagnoses
    
    def _lookup_impairment_ratings(self, diagnoses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Look up impairment ratings for identified diagnoses."""
        impairment_ratings = []
        
        # This is a simplified lookup - in a real system, you would have
        # a comprehensive database of AMA guidelines and impairment ratings
        
        # Sample impairment rating mappings
        rating_mappings = {
            'lumbar': {'percentage': 15, 'ama_table': '15-3', 'rationale': 'Lumbar spine impairment'},
            'cervical': {'percentage': 10, 'ama_table': '15-5', 'rationale': 'Cervical spine impairment'},
            'shoulder': {'percentage': 12, 'ama_table': '16-1', 'rationale': 'Shoulder impairment'},
            'knee': {'percentage': 8, 'ama_table': '17-2', 'rationale': 'Knee impairment'},
            'back': {'percentage': 15, 'ama_table': '15-3', 'rationale': 'Back impairment'},
            'spine': {'percentage': 15, 'ama_table': '15-3', 'rationale': 'Spine impairment'}
        }
        
        for diagnosis in diagnoses:
            description = diagnosis.get('description', '').lower()
            
            # Look for keywords in diagnosis description
            for keyword, rating_info in rating_mappings.items():
                if keyword in description:
                    impairment_rating = {
                        'diagnosis': diagnosis.get('description'),
                        'percentage': rating_info['percentage'],
                        'ama_table': rating_info['ama_table'],
                        'rationale': rating_info['rationale'],
                        'confidence': diagnosis.get('confidence', 0.0) * 0.8,  # Slightly lower confidence
                        'source': 'lookup_table'
                    }
                    impairment_ratings.append(impairment_rating)
                    break  # Only add one rating per diagnosis
        
        return impairment_ratings
    
    def _generate_template_sections(self, patient_info: Dict[str, Any], 
                                  diagnoses: List[Dict[str, Any]],
                                  impairment_ratings: List[Dict[str, Any]],
                                  state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate template sections with available information."""
        sections = {}
        
        # Header section
        sections['header'] = {
            'title': 'QUALIFIED MEDICAL EVALUATOR\'S REPORT',
            'patient_name': patient_info.get('name', '[PATIENT NAME]'),
            'case_number': patient_info.get('case_number', '[CASE NUMBER]'),
            'date_of_evaluation': datetime.now().strftime('%B %d, %Y'),
            'evaluator': '[EVALUATOR NAME]'
        }
        
        # Patient information section
        sections['patient_info'] = {
            'name': patient_info.get('name', '[PATIENT NAME]'),
            'age': patient_info.get('age', '[AGE]'),
            'gender': patient_info.get('gender', '[GENDER]'),
            'case_number': patient_info.get('case_number', '[CASE NUMBER]'),
            'injury_date': patient_info.get('injury_date', '[INJURY DATE]'),
            'dates_of_service': patient_info.get('dates', ['[DATE OF SERVICE]'])
        }
        
        # History section
        sections['history'] = {
            'chief_complaint': '[CHIEF COMPLAINT]',
            'history_of_present_illness': self._extract_history_from_text(state.get('extracted_text', '')),
            'past_medical_history': '[PAST MEDICAL HISTORY]',
            'medications': '[CURRENT MEDICATIONS]'
        }
        
        # Physical examination section
        sections['examination'] = {
            'general_appearance': '[GENERAL APPEARANCE]',
            'vital_signs': '[VITAL SIGNS]',
            'examination_findings': self._extract_examination_findings(state.get('entities_extracted', []))
        }
        
        # Diagnosis section
        sections['diagnosis'] = {
            'primary_diagnoses': [d.get('description', '[DIAGNOSIS]') for d in diagnoses[:3]],  # Top 3
            'secondary_diagnoses': [d.get('description', '[DIAGNOSIS]') for d in diagnoses[3:6]],  # Next 3
            'icd_codes': [d.get('icd_code') for d in diagnoses if d.get('icd_code')]
        }
        
        # Impairment rating section
        sections['impairment'] = {
            'ratings': impairment_ratings,
            'total_impairment': self._calculate_total_impairment(impairment_ratings),
            'ama_guidelines': 'AMA Guides to the Evaluation of Permanent Impairment, 5th Edition'
        }
        
        # Recommendations section
        sections['recommendations'] = {
            'treatment_recommendations': '[TREATMENT RECOMMENDATIONS]',
            'work_restrictions': '[WORK RESTRICTIONS]',
            'future_medical_care': '[FUTURE MEDICAL CARE]'
        }
        
        return sections
    
    def _extract_history_from_text(self, text: str) -> str:
        """Extract history information from text."""
        # Look for history-related sections
        import re
        
        history_patterns = [
            r'history[:\s]+(.*?)(?=examination|physical|diagnosis|$)',
            r'chief complaint[:\s]+(.*?)(?=history|examination|$)',
            r'present illness[:\s]+(.*?)(?=examination|physical|$)'
        ]
        
        for pattern in history_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                history_text = match.group(1).strip()
                if len(history_text) > 20:
                    return history_text[:500] + '...' if len(history_text) > 500 else history_text
        
        return '[HISTORY OF PRESENT ILLNESS]'
    
    def _extract_examination_findings(self, entities: List[Dict[str, Any]]) -> List[str]:
        """Extract examination findings from entities."""
        findings = []
        
        # Get finding entities
        finding_entities = [e for e in entities if e.get('type') == 'finding']
        for entity in finding_entities:
            finding_text = entity.get('text', '').strip()
            if len(finding_text) > 10:
                findings.append(finding_text)
        
        # Get body part entities (could indicate examination areas)
        body_part_entities = [e for e in entities if e.get('type') == 'body_part']
        for entity in body_part_entities:
            body_part = entity.get('text', '').strip()
            if body_part:
                findings.append(f"Examination of {body_part}")
        
        return findings if findings else ['[EXAMINATION FINDINGS]']
    
    def _calculate_total_impairment(self, impairment_ratings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate total impairment rating."""
        if not impairment_ratings:
            return {'percentage': 0, 'method': 'No impairments identified'}
        
        # Simple addition for demonstration (real calculation would be more complex)
        total_percentage = sum(rating.get('percentage', 0) for rating in impairment_ratings)
        
        # Cap at 100%
        total_percentage = min(total_percentage, 100)
        
        return {
            'percentage': total_percentage,
            'method': 'Combined values table' if len(impairment_ratings) > 1 else 'Direct rating',
            'component_ratings': len(impairment_ratings)
        }
    
    def _identify_missing_information(self, template_sections: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify missing information in template sections."""
        missing_info = []
        
        # Check for placeholder values that indicate missing information
        placeholders = ['[', 'UNKNOWN', 'N/A', '']
        
        def check_section(section_name: str, section_data: Any, path: str = '') -> None:
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    current_path = f"{path}.{key}" if path else key
                    check_section(section_name, value, current_path)
            elif isinstance(section_data, list):
                for i, item in enumerate(section_data):
                    current_path = f"{path}[{i}]" if path else f"[{i}]"
                    check_section(section_name, item, current_path)
            elif isinstance(section_data, str):
                if any(placeholder in section_data.upper() for placeholder in placeholders):
                    missing_info.append({
                        'section': section_name,
                        'field': path,
                        'missing_item': section_data,
                        'priority': 'high' if 'name' in path.lower() or 'diagnosis' in path.lower() else 'medium'
                    })
        
        for section_name, section_data in template_sections.items():
            check_section(section_name, section_data)
        
        return missing_info
    
    def _generate_template_file(self, template_sections: Dict[str, Any], 
                              patient_info: Dict[str, Any], 
                              template_type: str, 
                              document_id: str) -> Optional[str]:
        """Generate the actual template file."""
        try:
            # Generate filename
            patient_name = patient_info.get('name', 'Unknown').replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"QME_Report_{patient_name}_{timestamp}.docx"
            output_path = os.path.join(self.output_directory, filename)
            
            # Use the template generator to create the file
            success = self.template_generator.generate_qme_template(
                patient_info=patient_info,
                diagnoses=template_sections.get('diagnosis', {}),
                impairment_ratings=template_sections.get('impairment', {}),
                template_sections=template_sections,
                output_path=output_path
            )
            
            if success and os.path.exists(output_path):
                logger.info(f"Generated template file: {output_path}")
                return output_path
            else:
                logger.error("Template generation failed - file not created")
                return None
                
        except Exception as e:
            logger.error(f"Error generating template file: {e}")
            return None
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """Validate input state for template generation."""
        # Template generation can work with minimal input, so be flexible
        extracted_text = state.get('extracted_text')
        if not extracted_text or len(extracted_text.strip()) < 10:
            logger.error("Invalid or missing extracted_text")
            return False
        
        return True
    
    def get_required_inputs(self) -> List[str]:
        """Get required input keys."""
        return ['extracted_text']
    
    def get_output_keys(self) -> List[str]:
        """Get output keys this node adds to state."""
        return [
            'patient_info',
            'diagnoses_identified',
            'impairment_ratings_found',
            'template_sections',
            'missing_information',
            'output_file_path',
            'template_type',
            'generation_statistics',
            'template_generated'
        ]
    
    def can_retry(self, error: Exception) -> bool:
        """Determine if template generation can be retried."""
        # Template generation is generally retryable except for fundamental errors
        non_retryable_errors = (ValueError, TypeError)
        return not isinstance(error, non_retryable_errors)