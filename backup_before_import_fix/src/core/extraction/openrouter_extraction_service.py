"""
OpenRouter Integration Service for QME Document Extraction

This service provides integration with OpenRouter's API for advanced document extraction
using vision-capable models like Claude 3.5 Sonnet (Sonoma Sky Alpha equivalent).
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI library not available. Please install with: pip install openai")

from ..models.extraction_models import (
    ExtractionResult, 
    ExtractedField, 
    QualityAssessment, 
    QualityIssue,
    ProcessingMetadata,
    SourceReference,
    ValidationResult,
    VisionExtractionResult,
    ExtractionConfig,
    ConfidenceInterval
)


logger = logging.getLogger(__name__)


class OpenRouterAPIError(Exception):
    """Custom exception for OpenRouter API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class OpenRouterConfigurationError(Exception):
    """Custom exception for configuration errors"""
    pass


class OpenRouterValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class OpenRouterExtractionService:
    """
    Service for extracting information from documents using OpenRouter's API
    with vision-capable models for superior accuracy.
    """
    
    def __init__(self, config_path: str = "config/settings/openrouter_config.yaml"):
        """
        Initialize the OpenRouter extraction service with Sonoma Sky Alpha integration.
        
        Args:
            config_path: Path to the OpenRouter configuration file
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library is required. Please install with: pip install openai")
        
        self.config = self._load_config(config_path)
        self.api_key = self._get_api_key()
        self.client = self._create_openai_client()
        self.prompt_cache = {}
        
        # Enhanced features for Sonoma Sky Alpha
        self.vision_enabled = self.config.get('vision', {}).get('enabled', False)
        self.structured_output = self.config.get('extraction', {}).get('structured_output', True)
        self.confidence_scoring = self.config.get('extraction', {}).get('confidence_scoring', True)
        
        # Performance monitoring
        self.performance_tracking = self.config.get('performance', {}).get('enable_monitoring', False)
        self.request_metrics = []
        
        # Error handling configuration
        self.enable_fallback = self.config.get('error_handling', {}).get('enable_fallback_extraction', True)
        self.fallback_methods = self.config.get('error_handling', {}).get('fallback_methods', [])
        
        logger.info(f"OpenRouter service initialized with Sonoma Sky Alpha model: {self.config['api']['model']}")
        logger.info(f"Vision enabled: {self.vision_enabled}, Structured output: {self.structured_output}")
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load and validate configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded OpenRouter configuration from {config_path}")
            
            # Validate configuration structure
            self._validate_config(config)
            
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            raise OpenRouterConfigurationError(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            raise OpenRouterConfigurationError(f"Invalid YAML configuration: {e}")
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration structure and values"""
        required_sections = ['api', 'extraction', 'quality_thresholds']
        
        for section in required_sections:
            if section not in config:
                raise OpenRouterConfigurationError(f"Missing required configuration section: {section}")
        
        # Validate API configuration
        api_config = config['api']
        required_api_fields = ['base_url', 'model', 'timeout', 'max_retries', 'retry_delay']
        
        for field in required_api_fields:
            if field not in api_config:
                raise OpenRouterConfigurationError(f"Missing required API configuration field: {field}")
        
        # Validate numeric values
        if api_config['timeout'] <= 0:
            raise OpenRouterConfigurationError("API timeout must be positive")
        
        if api_config['max_retries'] < 0:
            raise OpenRouterConfigurationError("Max retries must be non-negative")
        
        if api_config['retry_delay'] <= 0:
            raise OpenRouterConfigurationError("Retry delay must be positive")
        
        # Validate extraction configuration
        extraction_config = config['extraction']
        required_extraction_fields = ['max_tokens', 'temperature', 'top_p']
        
        for field in required_extraction_fields:
            if field not in extraction_config:
                raise OpenRouterConfigurationError(f"Missing required extraction configuration field: {field}")
        
        # Validate temperature and top_p ranges
        if not 0.0 <= extraction_config['temperature'] <= 2.0:
            raise OpenRouterConfigurationError("Temperature must be between 0.0 and 2.0")
        
        if not 0.0 <= extraction_config['top_p'] <= 1.0:
            raise OpenRouterConfigurationError("Top_p must be between 0.0 and 1.0")
        
        # Validate quality thresholds
        quality_config = config['quality_thresholds']
        required_quality_fields = ['minimum_confidence', 'extraction_completeness', 'field_accuracy']
        
        for field in required_quality_fields:
            if field not in quality_config:
                raise OpenRouterConfigurationError(f"Missing required quality threshold field: {field}")
            
            if not 0.0 <= quality_config[field] <= 1.0:
                raise OpenRouterConfigurationError(f"Quality threshold {field} must be between 0.0 and 1.0")
        
        logger.debug("Configuration validation successful")
            
    def _get_api_key(self) -> str:
        """Get API key from secure storage or environment variables"""
        # Try secure key manager first
        try:
            from ..config.secure_api_key_manager import get_openrouter_api_key
            api_key = get_openrouter_api_key()
            if api_key:
                logger.debug("Using API key from secure storage")
                return api_key
        except ImportError:
            logger.warning("Secure API key manager not available, falling back to environment variable")
        except Exception as e:
            logger.warning(f"Failed to retrieve API key from secure storage: {str(e)}")
        
        # Fallback to environment variable
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found in secure storage or environment variables. "
                "Please set your OpenRouter API key using the secure key manager or "
                "OPENROUTER_API_KEY environment variable."
            )
        
        logger.debug("Using API key from environment variable")
        return api_key
        
    def _create_openai_client(self) -> OpenAI:
        """Create OpenAI client configured for OpenRouter."""
        return OpenAI(
            base_url=self.config['api']['base_url'],
            api_key=self.api_key
        )

        
    def load_prompt_template(self, prompt_type: str, prompt_name: str) -> Dict[str, str]:
        """
        Load prompt template from configuration files.
        
        Args:
            prompt_type: Type of prompt (extraction, generation, validation)
            prompt_name: Name of the specific prompt file
            
        Returns:
            Dictionary containing prompt templates
        """
        cache_key = f"{prompt_type}_{prompt_name}"
        
        if cache_key in self.prompt_cache:
            return self.prompt_cache[cache_key]
            
        prompt_path = f"config/prompts/{prompt_type}/{prompt_name}.yaml"
        
        try:
            with open(prompt_path, 'r') as f:
                prompt_config = yaml.safe_load(f)
            
            self.prompt_cache[cache_key] = prompt_config
            logger.debug(f"Loaded prompt template: {prompt_path}")
            return prompt_config
            
        except FileNotFoundError:
            logger.error(f"Prompt template not found: {prompt_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing prompt template: {e}")
            raise
            
    def extract_from_document(
        self, 
        document_path: str, 
        extraction_config: ExtractionConfig
    ) -> ExtractionResult:
        """
        Extract information from a document using OpenRouter API.
        
        Args:
            document_path: Path to the document file
            extraction_config: Configuration for extraction process
            
        Returns:
            ExtractionResult with extracted data and quality assessment
        """
        start_time = time.time()
        
        try:
            # Load appropriate prompt template
            prompt_config = self.load_prompt_template(
                "extraction", 
                extraction_config.prompt_template
            )
            
            # Prepare the API request
            messages = [
                {
                    "role": "system",
                    "content": prompt_config["system_prompt"]
                },
                {
                    "role": "user", 
                    "content": self._prepare_extraction_content(
                        document_path, 
                        prompt_config["extraction_prompt"]
                    )
                }
            ]
            
            # Make API call with retry logic
            response_data = self._make_api_call(messages)
            
            # Process and validate response
            extracted_data = self._process_extraction_response(
                response_data, 
                prompt_config.get("validation_rules", {})
            )
            
            # Calculate processing metadata
            processing_time = time.time() - start_time
            metadata = ProcessingMetadata(
                extraction_method="openrouter_claude_3_5_sonnet",
                processing_time=processing_time,
                model_used=self.config['api']['model'],
                prompt_template=extraction_config.prompt_template,
                api_version="v1"
            )
            
            # Perform quality assessment
            quality_assessment = self._assess_extraction_quality(
                extracted_data, 
                prompt_config.get("validation_rules", {})
            )
            
            return ExtractionResult(
                document_id=self._generate_document_id(document_path),
                extraction_method="openrouter_claude_3_5_sonnet",
                confidence_score=quality_assessment.overall_score,
                extracted_fields=extracted_data,
                quality_assessment=quality_assessment,
                processing_metadata=metadata,
                source_references=self._extract_source_references(extracted_data),
                validation_results=self._validate_extracted_data(
                    extracted_data, 
                    prompt_config.get("validation_rules", {})
                )
            )
            
        except Exception as e:
            logger.error(f"Primary extraction failed for {document_path}: {str(e)}")
            
            # Attempt fallback extraction if enabled
            fallback_result = self._perform_fallback_extraction(document_path, extraction_config, e)
            if fallback_result:
                logger.info("Fallback extraction successful")
                return fallback_result
            
            # If fallback also fails, raise the original error
            raise OpenRouterAPIError(f"Document extraction failed: {str(e)}")
            
    def extract_with_vision(
        self, 
        document_path: str, 
        prompt_template: str
    ) -> VisionExtractionResult:
        """
        Extract information from document using vision capabilities.
        
        Args:
            document_path: Path to the document (PDF, image)
            prompt_template: Template for vision extraction
            
        Returns:
            VisionExtractionResult with visual analysis results
        """
        if not self.config['vision']['enabled']:
            raise ValueError("Vision extraction is not enabled in configuration")
            
        try:
            # Convert document to image if needed
            image_data = self._prepare_document_for_vision(document_path)
            
            # Load vision prompt template
            prompt_config = self.load_prompt_template("extraction", prompt_template)
            
            # Prepare vision API request
            messages = [
                {
                    "role": "system",
                    "content": prompt_config["system_prompt"]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt_config["extraction_prompt"]
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]
            
            # Make vision API call
            response_data = self._make_api_call(messages)
            
            # Process vision response
            vision_results = self._process_vision_response(response_data)
            
            return VisionExtractionResult(
                document_id=self._generate_document_id(document_path),
                extraction_method="openrouter_vision_claude_3_5_sonnet",
                visual_elements=vision_results.get("visual_elements", []),
                text_regions=vision_results.get("text_regions", []),
                confidence_score=vision_results.get("confidence_score", 0.0),
                processing_metadata=ProcessingMetadata(
                    extraction_method="openrouter_vision_claude_3_5_sonnet",
                    processing_time=vision_results.get("processing_time", 0.0),
                    model_used=self.config['api']['model'],
                    prompt_template=prompt_template,
                    api_version="v1"
                )
            )
            
        except Exception as e:
            logger.error(f"Vision extraction failed for {document_path}: {str(e)}")
            raise OpenRouterAPIError(f"Vision extraction failed: {str(e)}")
            
    def validate_extraction_quality(self, result: ExtractionResult) -> QualityAssessment:
        """
        Validate the quality of extraction results against configured thresholds.
        
        Args:
            result: ExtractionResult to validate
            
        Returns:
            QualityAssessment with detailed quality metrics and validation status
        """
        quality_assessment = self._assess_extraction_quality(
            result.extracted_fields,
            {}  # Use default validation rules
        )
        
        # Check against configured thresholds
        thresholds = self.config['quality_thresholds']
        
        # Add threshold validation issues
        if quality_assessment.overall_score < thresholds['minimum_confidence']:
            quality_assessment.identified_issues.append(
                QualityIssue(
                    issue_type="low_overall_quality",
                    severity="high",
                    description=f"Overall quality score {quality_assessment.overall_score:.2f} below threshold {thresholds['minimum_confidence']}",
                    affected_fields=list(result.extracted_fields.keys()),
                    suggested_fix="Review extraction prompts and consider using different model or approach"
                )
            )
        
        if quality_assessment.completeness_score < thresholds['extraction_completeness']:
            quality_assessment.identified_issues.append(
                QualityIssue(
                    issue_type="low_completeness",
                    severity="medium",
                    description=f"Completeness score {quality_assessment.completeness_score:.2f} below threshold {thresholds['extraction_completeness']}",
                    affected_fields=[name for name, field in result.extracted_fields.items() if not field.value or field.value == "NOT_FOUND"],
                    suggested_fix="Review document quality and extraction prompts for missing fields"
                )
            )
        
        if quality_assessment.accuracy_score < thresholds['field_accuracy']:
            quality_assessment.identified_issues.append(
                QualityIssue(
                    issue_type="low_accuracy",
                    severity="high",
                    description=f"Accuracy score {quality_assessment.accuracy_score:.2f} below threshold {thresholds['field_accuracy']}",
                    affected_fields=[name for name, field in result.extracted_fields.items() if field.confidence < thresholds['minimum_confidence']],
                    suggested_fix="Review low-confidence fields and consider manual validation"
                )
            )
        
        return quality_assessment
        
    def _make_api_call(self, messages: List[Dict[str, Any]], retry_count: int = 0) -> Dict[str, Any]:
        """Make API call to OpenRouter using OpenAI client format"""
        max_retries = self.config['api']['max_retries']
        
        try:
            logger.debug(f"Making API call to Sonoma Sky Alpha (attempt {retry_count + 1}/{max_retries + 1})")
            
            # Use OpenAI client format as specified by OpenRouter
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://qme-system.local",  # Site URL for rankings
                    "X-Title": "QME Document Extraction System",  # Site title for rankings
                },
                model=self.config['api']['model'],  # "openrouter/sonoma-sky-alpha"
                messages=messages,
                max_tokens=self.config['extraction']['max_tokens'],
                temperature=self.config['extraction']['temperature'],
                top_p=self.config['extraction']['top_p']
            )
            
            # Convert OpenAI response to dictionary format for compatibility
            response_data = {
                "choices": [
                    {
                        "message": {
                            "content": completion.choices[0].message.content,
                            "role": completion.choices[0].message.role
                        },
                        "finish_reason": completion.choices[0].finish_reason
                    }
                ],
                "usage": {
                    "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                    "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                    "total_tokens": completion.usage.total_tokens if completion.usage else 0
                },
                "model": completion.model,
                "id": completion.id
            }
            
            logger.debug("Sonoma Sky Alpha API call successful")
            return response_data
            
            # Handle different HTTP status codes
            if response.status_code == 429:  # Rate limit
                if retry_count < max_retries:
                    wait_time = self.config['api']['retry_delay'] * (2 ** retry_count)  # Exponential backoff
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    return self._make_api_call(messages, retry_count + 1)
                else:
                    raise OpenRouterAPIError(
                        "Rate limit exceeded and max retries reached",
                        status_code=429
                    )
            
            response.raise_for_status()
            
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse API response: {str(e)}")
                raise OpenRouterAPIError(
                    f"Invalid API response format: {str(e)}",
                    status_code=response.status_code,
                    response_data={"raw_response": response.text[:1000]}
                )
            
            # Check for API-level errors in response
            if 'error' in response_data:
                error_info = response_data['error']
                error_message = error_info.get('message', 'Unknown API error') if isinstance(error_info, dict) else str(error_info)
                
                # Determine if error is retryable
                retryable_errors = ['server_error', 'timeout', 'service_unavailable']
                error_type = error_info.get('type', '') if isinstance(error_info, dict) else ''
                
                if error_type in retryable_errors and retry_count < max_retries:
                    wait_time = self.config['api']['retry_delay'] * (2 ** retry_count)
                    logger.warning(f"Retryable API error: {error_message}. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    return self._make_api_call(messages, retry_count + 1)
                else:
                    raise OpenRouterAPIError(
                        f"API Error: {error_message}",
                        status_code=response.status_code,
                        response_data=response_data
                    )
            
            # Validate response structure
            if 'choices' not in response_data or not response_data['choices']:
                raise OpenRouterAPIError(
                    "Invalid API response: missing choices",
                    status_code=response.status_code,
                    response_data=response_data
                )
            
            logger.debug("API call successful")
            return response_data
            
        except Exception as e:
            error_message = str(e)
            
            # Handle rate limiting
            if "rate limit" in error_message.lower() or "429" in error_message:
                if retry_count < max_retries:
                    wait_time = self.config['api']['retry_delay'] * (2 ** retry_count)
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    return self._make_api_call(messages, retry_count + 1)
                else:
                    raise OpenRouterAPIError(
                        "Rate limit exceeded and max retries reached",
                        status_code=429
                    )
            
            # Handle timeout errors
            elif "timeout" in error_message.lower():
                if retry_count < max_retries:
                    wait_time = self.config['api']['retry_delay'] * (2 ** retry_count)
                    logger.warning(f"Request timeout. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    return self._make_api_call(messages, retry_count + 1)
                else:
                    logger.error(f"Request timeout after {max_retries} retries: {error_message}")
                    raise OpenRouterAPIError(f"Request timeout after {max_retries} retries: {error_message}")
            
            # Handle connection errors
            elif "connection" in error_message.lower():
                if retry_count < max_retries:
                    wait_time = self.config['api']['retry_delay'] * (2 ** retry_count)
                    logger.warning(f"Connection error. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    return self._make_api_call(messages, retry_count + 1)
                else:
                    logger.error(f"Connection error after {max_retries} retries: {error_message}")
                    raise OpenRouterAPIError(f"Connection error after {max_retries} retries: {error_message}")
            
            # Handle other API errors
            else:
                logger.error(f"Sonoma Sky Alpha API call failed: {error_message}")
                raise OpenRouterAPIError(f"API call failed: {error_message}")
            
    def _prepare_extraction_content(self, document_path: str, prompt: str) -> str:
        """Prepare content for extraction API call"""
        # For now, we'll assume text extraction from PDF
        # In a full implementation, this would handle various document types
        try:
            # This is a placeholder - in real implementation, would extract text from PDF
            with open(document_path, 'r', encoding='utf-8') as f:
                document_text = f.read()
        except UnicodeDecodeError:
            # Handle binary files (PDFs, images)
            document_text = f"[Binary document: {document_path}]"
            
        return f"{prompt}\n\nDocument Content:\n{document_text}"
        
    def _prepare_document_for_vision(self, document_path: str) -> str:
        """Prepare document for vision API (convert to base64 image)"""
        import base64
        
        # This is a placeholder implementation
        # In real implementation, would convert PDF pages to images
        try:
            with open(document_path, 'rb') as f:
                file_data = f.read()
            return base64.b64encode(file_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to prepare document for vision: {str(e)}")
            raise
            
    def _process_extraction_response(
        self, 
        response_data: Dict[str, Any], 
        validation_rules: Dict[str, str]
    ) -> Dict[str, ExtractedField]:
        """Process API response and convert to ExtractedField objects"""
        try:
            content = response_data['choices'][0]['message']['content']
            
            # Try to parse as JSON first
            try:
                extracted_json = json.loads(content)
            except json.JSONDecodeError:
                # If not JSON, create a simple structure
                extracted_json = {"raw_content": content}
                
            extracted_fields = {}
            
            for field_name, field_value in extracted_json.items():
                if isinstance(field_value, dict):
                    # Structured field with metadata
                    extracted_fields[field_name] = ExtractedField(
                        name=field_name,
                        value=field_value.get('value', ''),
                        confidence=field_value.get('confidence', 0.5),
                        source_location=field_value.get('source_location', ''),
                        validation_status='pending',
                        notes=field_value.get('notes', '')
                    )
                else:
                    # Simple field value
                    extracted_fields[field_name] = ExtractedField(
                        name=field_name,
                        value=str(field_value),
                        confidence=0.8,  # Default confidence
                        source_location='',
                        validation_status='pending',
                        notes=''
                    )
                    
            return extracted_fields
            
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected API response format: {str(e)}")
            raise OpenRouterAPIError(f"Invalid API response format: {str(e)}")
            
    def _process_vision_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process vision API response"""
        try:
            content = response_data['choices'][0]['message']['content']
            
            # Parse vision response
            try:
                vision_data = json.loads(content)
            except json.JSONDecodeError:
                vision_data = {
                    "visual_elements": [],
                    "text_regions": [],
                    "confidence_score": 0.5,
                    "raw_content": content
                }
                
            return vision_data
            
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected vision API response format: {str(e)}")
            raise OpenRouterAPIError(f"Invalid vision API response format: {str(e)}")
            
    def _assess_extraction_quality(
        self, 
        extracted_fields: Dict[str, ExtractedField], 
        validation_rules: Dict[str, str]
    ) -> QualityAssessment:
        """Assess the quality of extracted data"""
        total_fields = len(extracted_fields)
        if total_fields == 0:
            return QualityAssessment(
                overall_score=0.0,
                completeness_score=0.0,
                accuracy_score=0.0,
                consistency_score=0.0,
                compliance_score=0.0,
                identified_issues=[],
                improvement_suggestions=[],
                confidence_intervals={}
            )
            
        # Calculate completeness (fields with values)
        completed_fields = sum(
            1 for field in extracted_fields.values() 
            if field.value and field.value != "NOT_FOUND"
        )
        completeness_score = completed_fields / total_fields
        
        # Calculate average confidence
        total_confidence = sum(field.confidence for field in extracted_fields.values())
        accuracy_score = total_confidence / total_fields
        
        # Calculate consistency (fields with high confidence)
        high_confidence_fields = sum(
            1 for field in extracted_fields.values() 
            if field.confidence >= self.config['quality_thresholds']['minimum_confidence']
        )
        consistency_score = high_confidence_fields / total_fields
        
        # Compliance score based on validation rules
        compliance_score = self._calculate_compliance_score(extracted_fields, validation_rules)
        
        # Overall score (weighted average)
        overall_score = (
            completeness_score * 0.3 +
            accuracy_score * 0.3 +
            consistency_score * 0.2 +
            compliance_score * 0.2
        )
        
        # Identify issues
        issues = []
        if completeness_score < self.config['quality_thresholds']['extraction_completeness']:
            issues.append("Low completeness: Many fields are missing or empty")
        if accuracy_score < self.config['quality_thresholds']['field_accuracy']:
            issues.append("Low accuracy: Many fields have low confidence scores")
            
        # Generate improvement suggestions
        suggestions = []
        if completeness_score < 0.8:
            suggestions.append("Review document quality and prompt templates")
        if accuracy_score < 0.8:
            suggestions.append("Consider using different extraction prompts or models")
            
        return QualityAssessment(
            overall_score=overall_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            compliance_score=compliance_score,
            identified_issues=issues,
            improvement_suggestions=suggestions,
            confidence_intervals=self._calculate_confidence_intervals(extracted_fields)
        )
        
    def _calculate_compliance_score(
        self, 
        extracted_fields: Dict[str, ExtractedField], 
        validation_rules: Dict[str, str]
    ) -> float:
        """Calculate compliance score based on validation rules"""
        if not validation_rules:
            return 1.0
            
        compliant_fields = 0
        total_rules = len(validation_rules)
        
        for field_name, rule in validation_rules.items():
            if field_name in extracted_fields:
                field = extracted_fields[field_name]
                # Simple validation - in real implementation, would use more sophisticated rules
                if field.value and field.value != "NOT_FOUND":
                    compliant_fields += 1
                    
        return compliant_fields / total_rules if total_rules > 0 else 1.0
        
    def _calculate_confidence_intervals(
        self, 
        extracted_fields: Dict[str, ExtractedField]
    ) -> Dict[str, ConfidenceInterval]:
        """Calculate confidence intervals for extracted fields"""
        intervals = {}
        
        for field_name, field in extracted_fields.items():
            # Simple confidence interval calculation
            confidence = field.confidence
            margin = 0.1  # 10% margin
            
            intervals[field_name] = ConfidenceInterval(
                lower_bound=max(0.0, confidence - margin),
                upper_bound=min(1.0, confidence + margin),
                confidence_level=0.95
            )
            
        return intervals
        
    def _extract_source_references(
        self, 
        extracted_fields: Dict[str, ExtractedField]
    ) -> List[SourceReference]:
        """Extract source references from fields"""
        references = []
        
        for field in extracted_fields.values():
            if field.source_location:
                references.append(SourceReference(
                    field_name=field.name,
                    source_location=field.source_location,
                    confidence=field.confidence,
                    extraction_method="openrouter_claude_3_5_sonnet"
                ))
                
        return references
        
    def _validate_extracted_data(
        self, 
        extracted_fields: Dict[str, ExtractedField], 
        validation_rules: Dict[str, str]
    ) -> List[ValidationResult]:
        """Validate extracted data against rules"""
        results = []
        
        for field_name, field in extracted_fields.items():
            validation_rule = validation_rules.get(field_name, "")
            
            # Simple validation - in real implementation, would use more sophisticated validation
            is_valid = bool(field.value and field.value != "NOT_FOUND")
            
            results.append(ValidationResult(
                field_name=field_name,
                is_valid=is_valid,
                validation_rule=validation_rule,
                error_message="" if is_valid else f"Field {field_name} is missing or invalid",
                confidence=field.confidence
            ))
            
        return results
        
    def _generate_document_id(self, document_path: str) -> str:
        """Generate unique document ID"""
        import hashlib
        
        path_hash = hashlib.md5(document_path.encode()).hexdigest()[:8]
        timestamp = int(time.time())
        
        return f"doc_{timestamp}_{path_hash}"
    
    def _perform_fallback_extraction(
        self, 
        document_path: str, 
        extraction_config: ExtractionConfig,
        primary_error: Exception
    ) -> Optional[ExtractionResult]:
        """
        Perform fallback extraction when primary method fails.
        
        Args:
            document_path: Path to the document
            extraction_config: Original extraction configuration
            primary_error: The error that caused fallback to be triggered
            
        Returns:
            ExtractionResult from fallback method or None if all methods fail
        """
        if not self.enable_fallback:
            logger.warning("Fallback extraction disabled, returning None")
            return None
            
        logger.warning(f"Primary extraction failed: {str(primary_error)}")
        logger.info("Attempting fallback extraction methods")
        
        for fallback_method in self.fallback_methods:
            try:
                logger.info(f"Trying fallback method: {fallback_method}")
                
                if fallback_method == "rule_based":
                    return self._rule_based_extraction(document_path, extraction_config)
                elif fallback_method == "template_matching":
                    return self._template_matching_extraction(document_path, extraction_config)
                else:
                    logger.warning(f"Unknown fallback method: {fallback_method}")
                    continue
                    
            except Exception as fallback_error:
                logger.error(f"Fallback method {fallback_method} failed: {str(fallback_error)}")
                continue
        
        logger.error("All fallback methods failed")
        return None
    
    def _rule_based_extraction(
        self, 
        document_path: str, 
        extraction_config: ExtractionConfig
    ) -> ExtractionResult:
        """
        Perform rule-based extraction as fallback method.
        
        Args:
            document_path: Path to the document
            extraction_config: Extraction configuration
            
        Returns:
            ExtractionResult with rule-based extraction
        """
        logger.info("Performing rule-based extraction")
        
        # This is a simplified implementation
        # In a real system, this would use regex patterns and document structure analysis
        extracted_fields = {}
        
        try:
            with open(document_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Handle binary files
            content = f"[Binary document: {document_path}]"
        
        # Simple rule-based extraction patterns
        import re
        
        # Patient name pattern
        name_pattern = r'Patient:?\s*([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        name_match = re.search(name_pattern, content)
        if name_match:
            extracted_fields['patient_name'] = ExtractedField(
                name='patient_name',
                value=name_match.group(1),
                confidence=0.6,  # Lower confidence for rule-based
                source_location='Rule-based extraction',
                validation_status='needs_review',
                notes='Extracted using rule-based fallback method'
            )
        
        # Date of birth pattern
        dob_pattern = r'(?:DOB|Date of Birth):?\s*(\d{1,2}/\d{1,2}/\d{4})'
        dob_match = re.search(dob_pattern, content)
        if dob_match:
            extracted_fields['date_of_birth'] = ExtractedField(
                name='date_of_birth',
                value=dob_match.group(1),
                confidence=0.7,
                source_location='Rule-based extraction',
                validation_status='needs_review',
                notes='Extracted using rule-based fallback method'
            )
        
        # Create basic quality assessment
        quality_assessment = QualityAssessment(
            overall_score=0.5,  # Lower score for fallback method
            completeness_score=len(extracted_fields) / 10,  # Assume 10 expected fields
            accuracy_score=0.6,
            consistency_score=0.5,
            compliance_score=0.4,
            identified_issues=["Fallback extraction method used", "Lower confidence scores"],
            improvement_suggestions=["Retry with primary extraction method", "Manual review recommended"],
            confidence_intervals=self._calculate_confidence_intervals(extracted_fields)
        )
        
        # Create processing metadata
        metadata = ProcessingMetadata(
            extraction_method="rule_based_fallback",
            processing_time=1.0,  # Estimated
            model_used="rule_based_patterns",
            prompt_template=extraction_config.prompt_template,
            api_version="fallback_v1",
            error_count=1,
            retry_count=0
        )
        
        return ExtractionResult(
            document_id=self._generate_document_id(document_path),
            extraction_method="rule_based_fallback",
            confidence_score=quality_assessment.overall_score,
            extracted_fields=extracted_fields,
            quality_assessment=quality_assessment,
            processing_metadata=metadata,
            source_references=self._extract_source_references(extracted_fields),
            validation_results=[]
        )
    
    def _template_matching_extraction(
        self, 
        document_path: str, 
        extraction_config: ExtractionConfig
    ) -> ExtractionResult:
        """
        Perform template matching extraction as fallback method.
        
        Args:
            document_path: Path to the document
            extraction_config: Extraction configuration
            
        Returns:
            ExtractionResult with template-based extraction
        """
        logger.info("Performing template matching extraction")
        
        # This is a simplified implementation
        # In a real system, this would use document templates and structure matching
        extracted_fields = {}
        
        # Template matching would analyze document structure and match against known templates
        # For now, return minimal extraction result
        extracted_fields['extraction_method'] = ExtractedField(
            name='extraction_method',
            value='template_matching_fallback',
            confidence=0.5,
            source_location='Template matching analysis',
            validation_status='needs_review',
            notes='Extracted using template matching fallback method'
        )
        
        quality_assessment = QualityAssessment(
            overall_score=0.4,
            completeness_score=0.1,
            accuracy_score=0.5,
            consistency_score=0.4,
            compliance_score=0.3,
            identified_issues=["Template matching fallback used", "Limited extraction capability"],
            improvement_suggestions=["Manual extraction recommended", "Document template analysis needed"],
            confidence_intervals=self._calculate_confidence_intervals(extracted_fields)
        )
        
        metadata = ProcessingMetadata(
            extraction_method="template_matching_fallback",
            processing_time=0.5,
            model_used="template_matching_engine",
            prompt_template=extraction_config.prompt_template,
            api_version="fallback_v1",
            error_count=1,
            retry_count=0
        )
        
        return ExtractionResult(
            document_id=self._generate_document_id(document_path),
            extraction_method="template_matching_fallback",
            confidence_score=quality_assessment.overall_score,
            extracted_fields=extracted_fields,
            quality_assessment=quality_assessment,
            processing_metadata=metadata,
            source_references=self._extract_source_references(extracted_fields),
            validation_results=[]
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the extraction service.
        
        Returns:
            Dictionary containing performance metrics
        """
        if not self.performance_tracking or not self.request_metrics:
            return {"performance_tracking": False, "metrics": None}
        
        # Calculate metrics from request history
        response_times = [m.get('response_time', 0) for m in self.request_metrics]
        token_usage = [m.get('token_usage', 0) for m in self.request_metrics]
        success_rate = sum(1 for m in self.request_metrics if m.get('success', False)) / len(self.request_metrics)
        
        return {
            "performance_tracking": True,
            "total_requests": len(self.request_metrics),
            "average_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "total_token_usage": sum(token_usage),
            "average_token_usage": sum(token_usage) / len(token_usage) if token_usage else 0,
            "success_rate": success_rate,
            "error_rate": 1 - success_rate
        }
    
    def clear_performance_metrics(self) -> None:
        """Clear stored performance metrics"""
        self.request_metrics.clear()
        logger.info("Performance metrics cleared")
    
    def validate_sonoma_sky_alpha_compatibility(self) -> Dict[str, bool]:
        """
        Validate that the service is properly configured for Sonoma Sky Alpha model.
        
        Returns:
            Dictionary with compatibility check results
        """
        compatibility = {
            "model_configured": False,
            "vision_enabled": False,
            "structured_output": False,
            "confidence_scoring": False,
            "api_key_present": False,
            "config_valid": False
        }
        
        try:
            # Check model configuration
            model = self.config.get('api', {}).get('model', '')
            compatibility["model_configured"] = 'claude-3.5-sonnet' in model or 'sonoma' in model.lower()
            
            # Check vision capabilities
            compatibility["vision_enabled"] = self.vision_enabled
            
            # Check structured output
            compatibility["structured_output"] = self.structured_output
            
            # Check confidence scoring
            compatibility["confidence_scoring"] = self.confidence_scoring
            
            # Check API key
            compatibility["api_key_present"] = bool(self.api_key)
            
            # Check overall config validity
            compatibility["config_valid"] = all([
                compatibility["model_configured"],
                compatibility["api_key_present"],
                self.config.get('api', {}).get('base_url'),
                self.config.get('extraction', {}).get('max_tokens')
            ])
            
        except Exception as e:
            logger.error(f"Error validating Sonoma Sky Alpha compatibility: {str(e)}")
        
        return compatibility