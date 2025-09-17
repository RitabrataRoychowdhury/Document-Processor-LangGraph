"""Template generation command for creating QME reports."""

from typing import Dict, Any, Optional
import os

try:
    from src.commands.base import Command, CommandResult
    from src.core.generation.qme_template_generator import QMETemplateGenerator, create_qme_template_generator
    from src.utils.logging_config import get_logger
    from src.utils.error_handling import RetryableException, NonRetryableException
except ImportError:
    from commands.base import Command, CommandResult
    from core.generation.qme_template_generator import QMETemplateGenerator, create_qme_template_generator
    from utils.logging_config import get_logger
    from utils.error_handling import RetryableException, NonRetryableException

logger = get_logger(__name__)


class TemplateCommand(Command):
    """Command for generating QME templates from patient data."""
    
    def __init__(self, patient_id: str, 
                 output_path: Optional[str] = None,
                 template_generator: Optional[QMETemplateGenerator] = None):
        """
        Initialize template generation command.
        
        Args:
            patient_id: Patient identifier
            output_path: Optional output file path
            template_generator: Optional template generator instance
        """
        self.patient_id = patient_id
        self.output_path = output_path
        self.template_generator = template_generator or create_qme_template_generator()
    
    def execute(self) -> CommandResult:
        """Execute QME template generation."""
        try:
            logger.info(f"Starting QME template generation for patient: {self.patient_id}")
            
            # Validate patient exists
            patient = self.template_generator.patient_repository.find_by_id(self.patient_id)
            if not patient:
                return CommandResult.failure_result(
                    message=f"Patient not found: {self.patient_id}",
                    error=ValueError(f"Patient not found: {self.patient_id}")
                )
            
            # Generate template
            file_path, template_data = self.template_generator.generate_qme_template(
                self.patient_id, 
                self.output_path
            )
            
            # Verify file was created
            if not os.path.exists(file_path):
                raise NonRetryableException(f"Template file was not created: {file_path}")
            
            # Prepare result data
            result_data = {
                'patient_id': self.patient_id,
                'patient_name': template_data.patient_info.name,
                'case_number': template_data.patient_info.case_number,
                'file_path': file_path,
                'diagnoses_count': len(template_data.medical_findings.diagnoses),
                'findings_count': len(template_data.medical_findings.findings),
                'impairment_ratings_count': len(template_data.medical_findings.impairment_ratings),
                'missing_sections_count': len(template_data.missing_sections),
                'missing_sections': template_data.missing_sections,
                'recommendations_count': len(template_data.recommendations),
                'ama_guidelines_count': len(template_data.ama_guidelines),
                'generated_at': template_data.generated_at.isoformat()
            }
            
            logger.info(f"Successfully generated QME template: {file_path}")
            logger.info(f"Template contains {result_data['diagnoses_count']} diagnoses, "
                       f"{result_data['findings_count']} findings, "
                       f"{result_data['impairment_ratings_count']} impairment ratings")
            
            if template_data.missing_sections:
                logger.warning(f"Template has {len(template_data.missing_sections)} missing sections: "
                             f"{', '.join(template_data.missing_sections)}")
            
            return CommandResult.success_result(
                message=f"QME template generated successfully for patient {patient.name}",
                data=result_data
            )
            
        except FileNotFoundError as e:
            error_msg = f"Required file not found during template generation: {str(e)}"
            logger.error(error_msg)
            return CommandResult.failure_result(
                message=error_msg,
                error=e
            )
            
        except PermissionError as e:
            error_msg = f"Permission denied during template generation: {str(e)}"
            logger.error(error_msg)
            return CommandResult.failure_result(
                message=error_msg,
                error=e
            )
            
        except ValueError as e:
            error_msg = f"Invalid data for template generation: {str(e)}"
            logger.error(error_msg)
            return CommandResult.failure_result(
                message=error_msg,
                error=e
            )
            
        except NonRetryableException as e:
            logger.error(f"Non-retryable error in template generation: {e}")
            return CommandResult.failure_result(
                message=str(e),
                error=e
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in template generation: {e}")
            # Most template generation errors are not retryable
            raise NonRetryableException(f"Template generation failed: {str(e)}")
    
    def can_retry(self) -> bool:
        """Check if command can be retried."""
        # Template generation is generally not retryable unless it's a temporary file system issue
        return False
    
    def get_description(self) -> str:
        """Get command description."""
        return f"Generate QME template for patient {self.patient_id}"


class BatchTemplateCommand(Command):
    """Command for generating QME templates for multiple patients."""
    
    def __init__(self, patient_ids: list, 
                 output_directory: Optional[str] = None,
                 template_generator: Optional[QMETemplateGenerator] = None):
        """
        Initialize batch template generation command.
        
        Args:
            patient_ids: List of patient identifiers
            output_directory: Optional output directory
            template_generator: Optional template generator instance
        """
        self.patient_ids = patient_ids
        self.output_directory = output_directory or "qme_templates"
        self.template_generator = template_generator or create_qme_template_generator()
    
    def execute(self) -> CommandResult:
        """Execute batch QME template generation."""
        try:
            logger.info(f"Starting batch QME template generation for {len(self.patient_ids)} patients")
            
            # Create output directory if it doesn't exist
            os.makedirs(self.output_directory, exist_ok=True)
            
            results = []
            successful_count = 0
            failed_count = 0
            
            for patient_id in self.patient_ids:
                try:
                    # Generate individual template
                    output_path = os.path.join(
                        self.output_directory, 
                        f"qme_report_{patient_id}.docx"
                    )
                    
                    template_cmd = TemplateCommand(
                        patient_id=patient_id,
                        output_path=output_path,
                        template_generator=self.template_generator
                    )
                    
                    result = template_cmd.execute()
                    results.append({
                        'patient_id': patient_id,
                        'success': result.success,
                        'file_path': result.data.get('file_path') if result.success else None,
                        'error': result.error_message if not result.success else None
                    })
                    
                    if result.success:
                        successful_count += 1
                        logger.info(f"Generated template for patient {patient_id}")
                    else:
                        failed_count += 1
                        logger.error(f"Failed to generate template for patient {patient_id}: {result.error_message}")
                        
                except Exception as e:
                    failed_count += 1
                    error_msg = f"Error generating template for patient {patient_id}: {str(e)}"
                    logger.error(error_msg)
                    results.append({
                        'patient_id': patient_id,
                        'success': False,
                        'file_path': None,
                        'error': error_msg
                    })
            
            # Prepare result data
            result_data = {
                'total_patients': len(self.patient_ids),
                'successful_count': successful_count,
                'failed_count': failed_count,
                'output_directory': self.output_directory,
                'results': results
            }
            
            success_rate = (successful_count / len(self.patient_ids)) * 100
            message = (f"Batch template generation completed: {successful_count}/{len(self.patient_ids)} "
                      f"successful ({success_rate:.1f}%)")
            
            logger.info(message)
            
            if successful_count > 0:
                return CommandResult.success_result(
                    message=message,
                    data=result_data
                )
            else:
                return CommandResult.failure_result(
                    message=message,
                    error=Exception("No templates were generated successfully")
                )
            
        except Exception as e:
            error_msg = f"Batch template generation failed: {str(e)}"
            logger.error(error_msg)
            return CommandResult.failure_result(
                message=error_msg,
                error=e
            )
    
    def can_retry(self) -> bool:
        """Check if command can be retried."""
        return False
    
    def get_description(self) -> str:
        """Get command description."""
        return f"Generate QME templates for {len(self.patient_ids)} patients"