"""
Gemini Integration Service for QME Document Extraction

This service provides integration with Google's Gemini API for document extraction
as a fallback option when OpenRouter is unavailable.
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import yaml

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.warning("requests library not available. Please install with: pip install requests")

from src.models.extraction_models import (
    ExtractionResult, 
    ExtractedField, 
    QualityAssessment, 
    QualityIssue,
    ProcessingMetadata,
    SourceReference,
    ValidationResult,
    ExtractionConfig,
    ConfidenceInterval
)

logger = logging.getLogger(__name__)

class GeminiAPIError(Exception):
    """Custom exception for Gemini API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}

class GeminiConfigurationError(Exception):
    """Custom exception for configuration errors"""
    pass

class GeminiExtractionService:
    """
    Service for extracting information from documents using Google's Gemini API.
    """
    
    def __init__(self, config_path: str = "config/settings/gemini_config.yaml"):
        """
        Initialize the Gemini extraction service.
        
        Args:
            config_path: Path to the Gemini configuration file
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library is required. Please install with: pip install requests")
        
        self.config = self._load_config(config_path)
        self.api_key = self._get_api_key()
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config['api']['model']}:generateContent?key={self.api_key}"
        
        logger.info(f"Gemini service initialized with model: {self.config['api']['model']}")
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load and validate configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded Gemini configuration from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {config_path}, using defaults")
            return self._get_default_config()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            raise GeminiConfigurationError(f"Invalid YAML configuration: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for Gemini service"""
        return {
            'api': {
                'model': 'gemini-2.0-flash',
                'timeout': 30,
                'max_retries': 3,
                'retry_delay': 2
            },
            'extraction': {
                'max_tokens': 2000,
                'temperature': 0.1,
                'top_p': 0.9
            },
            'quality_thresholds': {
                'minimum_confidence': 0.6,
                'extraction_completeness': 0.7,
                'field_accuracy': 0.8
            }
        }
    
    def _get_api_key(self) -> str:
        """Get API key from environment variables"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables. "
                "Please set your Gemini API key using the GEMINI_API_KEY environment variable."
            )
        
        logger.debug("Using Gemini API key from environment variable")
        return api_key
    
    def extract_from_document(
        self, 
        document_path: str, 
        extraction_config: ExtractionConfig
    ) -> ExtractionResult:
        """
        Extract information from a document using Gemini API.
        
        Args:
            document_path: Path to the document file
            extraction_config: Configuration for extraction process
            
        Returns:
            ExtractionResult with extracted data and quality assessment
        """
        start_time = time.time()
        
        try:
            # Prepare the extraction prompt
            document_text = self._read_document(document_path)
            prompt = self._prepare_extraction_prompt(document_text)
            
            # Make API call with retry logic
            response_data = self._make_api_call(prompt)
            
            # Process and validate response
            extracted_data = self._process_extraction_response(response_data)
            
            # Calculate processing metadata
            processing_time = time.time() - start_time
            metadata = ProcessingMetadata(
                extraction_method="gemini_extraction",
                processing_time=processing_time,
                model_used=self.config['api']['model'],
                prompt_template=extraction_config.prompt_template,
                api_version="v1beta"
            )
            
            # Perform quality assessment
            quality_assessment = self._assess_extraction_quality(extracted_data)
            
            return ExtractionResult(
                document_id=self._generate_document_id(document_path),
                extraction_method="gemini_extraction",
                confidence_score=quality_assessment.overall_score,
                extracted_fields=extracted_data,
                quality_assessment=quality_assessment,
                processing_metadata=metadata,
                source_references=self._extract_source_references(extracted_data),
                validation_results=[]
            )
            
        except Exception as e:
            logger.error(f"Gemini extraction failed for {document_path}: {str(e)}")
            raise GeminiAPIError(f"Document extraction failed: {str(e)}")
    
    def _read_document(self, document_path: str) -> str:
        """Read document content from file"""
        try:
            with open(document_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Handle binary files
            return f"[Binary document: {document_path}]"
        except Exception as e:
            logger.error(f"Failed to read document: {str(e)}")
            raise
    
    def _prepare_extraction_prompt(self, document_text: str) -> str:
        """Prepare extraction prompt for Gemini API"""
        prompt = f"""
You are a medical document extraction specialist. Extract the following information from the medical document below and return it as a JSON object.

Extract these fields if present:
- patient_name: Full name of the patient
- date_of_birth: Patient's date of birth
- injury_date: Date of injury or accident
- case_number: Workers' compensation case number
- body_parts: Affected body parts or areas
- diagnosis: Medical diagnosis or condition
- employer: Patient's employer

Return the result as a JSON object with the field names as keys. If a field is not found, omit it from the JSON. Include confidence scores for each field (0.0 to 1.0).

Document content:
{document_text[:4000]}  # Limit content to avoid token limits

Return only the JSON object, no additional text.
"""
        return prompt
    
    def _make_api_call(self, prompt: str, retry_count: int = 0) -> Dict[str, Any]:
        """Make API call to Gemini"""
        max_retries = self.config['api']['max_retries']
        
        try:
            logger.debug(f"Making Gemini API call (attempt {retry_count + 1}/{max_retries + 1})")
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": self.config['extraction']['temperature'],
                    "topP": self.config['extraction']['top_p'],
                    "maxOutputTokens": self.config['extraction']['max_tokens']
                }
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=self.config['api']['timeout']
            )
            
            if response.status_code == 429:  # Rate limit
                if retry_count < max_retries:
                    wait_time = self.config['api']['retry_delay'] * (2 ** retry_count)
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    return self._make_api_call(prompt, retry_count + 1)
                else:
                    raise GeminiAPIError("Rate limit exceeded and max retries reached", status_code=429)
            
            response.raise_for_status()
            response_data = response.json()
            
            logger.debug("Gemini API call successful")
            return response_data
            
        except requests.exceptions.RequestException as e:
            if retry_count < max_retries:
                wait_time = self.config['api']['retry_delay'] * (2 ** retry_count)
                logger.warning(f"Request failed. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                return self._make_api_call(prompt, retry_count + 1)
            else:
                logger.error(f"Gemini API call failed after {max_retries} retries: {str(e)}")
                raise GeminiAPIError(f"API call failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Gemini API call: {str(e)}")
            raise GeminiAPIError(f"Unexpected API error: {str(e)}")
    
    def _process_extraction_response(self, response_data: Dict[str, Any]) -> Dict[str, ExtractedField]:
        """Process Gemini API response and convert to ExtractedField objects"""
        try:
            # Extract content from Gemini response
            if 'candidates' not in response_data or not response_data['candidates']:
                logger.error("No candidates in Gemini response")
                return self._create_error_field("No candidates in API response")
            
            candidate = response_data['candidates'][0]
            if 'content' not in candidate or 'parts' not in candidate['content']:
                logger.error("Invalid candidate structure in Gemini response")
                return self._create_error_field("Invalid response structure")
            
            parts = candidate['content']['parts']
            if not parts or 'text' not in parts[0]:
                logger.error("No text content in Gemini response")
                return self._create_error_field("No text content in response")
            
            content = parts[0]['text']
            
            # Try to parse as JSON
            try:
                extracted_json = json.loads(content)
                logger.debug(f"Parsed Gemini JSON response type: {type(extracted_json)}")
                
                # Ensure we have a dictionary
                if not isinstance(extracted_json, dict):
                    logger.warning(f"Gemini returned non-dict response: {type(extracted_json)}")
                    if isinstance(extracted_json, list) and len(extracted_json) > 0:
                        if isinstance(extracted_json[0], dict):
                            extracted_json = extracted_json[0]
                        else:
                            return self._create_error_field("List response without dict items")
                    else:
                        return self._create_error_field("Non-dict response format")
                        
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse Gemini JSON response: {e}")
                # Try to extract fields from text response
                return self._extract_from_text_response(content)
            
            # Convert to ExtractedField objects
            extracted_fields = {}
            
            for field_name, field_value in extracted_json.items():
                if isinstance(field_value, dict) and 'value' in field_value:
                    # Structured field with metadata
                    extracted_fields[field_name] = ExtractedField(
                        name=field_name,
                        value=str(field_value['value']),
                        confidence=field_value.get('confidence', 0.7),
                        source_location='Gemini API extraction',
                        validation_status='pending',
                        notes='Extracted using Gemini API'
                    )
                else:
                    # Simple field value
                    extracted_fields[field_name] = ExtractedField(
                        name=field_name,
                        value=str(field_value),
                        confidence=0.7,  # Default confidence for Gemini
                        source_location='Gemini API extraction',
                        validation_status='pending',
                        notes='Extracted using Gemini API'
                    )
            
            return extracted_fields
            
        except Exception as e:
            logger.error(f"Error processing Gemini response: {str(e)}")
            return self._create_error_field(f"Response processing error: {str(e)}")
    
    def _create_error_field(self, error_message: str) -> Dict[str, ExtractedField]:
        """Create an error field for failed extractions"""
        return {
            'error': ExtractedField(
                name='error',
                value=error_message,
                confidence=0.0,
                source_location='',
                validation_status='error',
                notes=f'Gemini extraction error: {error_message}'
            )
        }
    
    def _extract_from_text_response(self, content: str) -> Dict[str, ExtractedField]:
        """Extract fields from text response when JSON parsing fails"""
        extracted_fields = {}
        
        # Simple pattern matching for common fields
        import re
        
        patterns = {
            'patient_name': r'(?:patient[_\s]*name|name)[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            'date_of_birth': r'(?:date[_\s]*of[_\s]*birth|dob)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            'injury_date': r'(?:injury[_\s]*date|accident[_\s]*date)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            'case_number': r'(?:case[_\s]*number|claim[_\s]*number)[:\s]*([A-Z0-9-]+)',
        }
        
        for field_name, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                extracted_fields[field_name] = ExtractedField(
                    name=field_name,
                    value=match.group(1).strip(),
                    confidence=0.6,  # Lower confidence for pattern matching
                    source_location='Text pattern matching',
                    validation_status='pending',
                    notes='Extracted from text response using pattern matching'
                )
        
        return extracted_fields
    
    def _assess_extraction_quality(self, extracted_fields: Dict[str, ExtractedField]) -> QualityAssessment:
        """Assess the quality of extracted data"""
        if not extracted_fields or 'error' in extracted_fields:
            return QualityAssessment(
                overall_score=0.0,
                completeness_score=0.0,
                accuracy_score=0.0,
                consistency_score=0.0,
                compliance_score=0.0,
                identified_issues=["Extraction failed or returned errors"],
                improvement_suggestions=["Retry extraction or use alternative method"],
                confidence_intervals={}
            )
        
        # Calculate quality metrics
        total_fields = len(extracted_fields)
        high_confidence_fields = sum(1 for field in extracted_fields.values() if field.confidence >= 0.8)
        
        completeness_score = min(100.0, (total_fields / 7) * 100)  # Assume 7 expected fields
        accuracy_score = (high_confidence_fields / total_fields) * 100 if total_fields > 0 else 0
        consistency_score = 75.0  # Gemini is reasonably consistent
        compliance_score = 80.0   # Good compliance for Gemini extraction
        
        overall_score = (completeness_score + accuracy_score + consistency_score + compliance_score) / 4
        
        return QualityAssessment(
            overall_score=overall_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            compliance_score=compliance_score,
            identified_issues=[],
            improvement_suggestions=[],
            confidence_intervals={}
        )
    
    def _extract_source_references(self, extracted_fields: Dict[str, ExtractedField]) -> List[SourceReference]:
        """Extract source references from extracted fields"""
        # Gemini doesn't provide specific source references, so return empty list
        return []
    
    def _generate_document_id(self, document_path: str) -> str:
        """Generate a unique document ID"""
        import hashlib
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path_hash = hashlib.md5(document_path.encode()).hexdigest()[:8]
        return f"doc_{timestamp}_{path_hash}"