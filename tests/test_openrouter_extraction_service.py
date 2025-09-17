"""
Comprehensive unit tests for OpenRouter Integration Service.

This test suite validates the OpenRouter extraction service functionality,
configuration management, error handling, and quality assessment features.
"""

import os
import json
import pytest
import tempfile
import yaml
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

from src.core.extraction.openrouter_extraction_service import (
    OpenRouterExtractionService,
    OpenRouterAPIError
)
from src.models.extraction_models import (
    ExtractionConfig,
    ExtractionResult,
    ExtractedField,
    QualityAssessment,
    ProcessingMetadata,
    VisionExtractionResult,
    ExtractionMethod
)


class TestOpenRouterExtractionService:
    """Test suite for OpenRouter extraction service"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        return {
            'api': {
                'base_url': 'https://openrouter.ai/api/v1',
                'model': 'anthropic/claude-3.5-sonnet:beta',
                'timeout': 60,
                'max_retries': 3,
                'retry_delay': 2
            },
            'extraction': {
                'max_tokens': 4000,
                'temperature': 0.1,
                'top_p': 0.9,
                'presence_penalty': 0.0,
                'frequency_penalty': 0.0
            },
            'quality_thresholds': {
                'minimum_confidence': 0.7,
                'extraction_completeness': 0.8,
                'field_accuracy': 0.85
            },
            'vision': {
                'enabled': True,
                'max_image_size': 10485760,
                'supported_formats': ['pdf', 'png', 'jpg', 'jpeg'],
                'dpi': 300
            }
        }
    
    @pytest.fixture
    def mock_prompt_config(self):
        """Mock prompt configuration for testing"""
        return {
            'system_prompt': 'You are a medical document analysis expert.',
            'extraction_prompt': 'Extract patient information from the document.',
            'validation_rules': {
                'patient_name': 'Must be present and contain first and last name',
                'date_of_birth': 'Must be valid date in MM/DD/YYYY format'
            }
        }
    
    @pytest.fixture
    def temp_config_file(self, mock_config):
        """Create temporary configuration file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(mock_config, f)
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def temp_prompt_file(self, mock_prompt_config):
        """Create temporary prompt file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(mock_prompt_config, f)
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def extraction_config(self):
        """Sample extraction configuration"""
        return ExtractionConfig(
            prompt_template="patient_info",
            extraction_method=ExtractionMethod.OPENROUTER_CLAUDE,
            quality_threshold=0.7,
            enable_vision=False,
            max_retries=3,
            timeout=60
        )
    
    @pytest.fixture
    def mock_api_response(self):
        """Mock API response from OpenRouter"""
        return {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'patient_name': {
                            'value': 'John Doe',
                            'confidence': 0.95,
                            'source_location': 'Page 1, Header'
                        },
                        'date_of_birth': {
                            'value': '01/15/1980',
                            'confidence': 0.90,
                            'source_location': 'Page 1, Demographics'
                        },
                        'age': {
                            'value': '43',
                            'confidence': 0.85,
                            'source_location': 'Page 1, Demographics'
                        }
                    })
                }
            }],
            'usage': {
                'prompt_tokens': 1000,
                'completion_tokens': 500,
                'total_tokens': 1500
            }
        }

    def test_service_initialization_success(self, temp_config_file):
        """Test successful service initialization"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            service = OpenRouterExtractionService(config_path=temp_config_file)
            
            assert service.api_key == 'test-key'
            assert service.config['api']['model'] == 'anthropic/claude-3.5-sonnet:beta'
            assert service.session is not None
    
    def test_service_initialization_missing_api_key(self, temp_config_file):
        """Test service initialization with missing API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY environment variable not set"):
                OpenRouterExtractionService(config_path=temp_config_file)
    
    def test_service_initialization_missing_config(self):
        """Test service initialization with missing configuration file"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            with pytest.raises(FileNotFoundError):
                OpenRouterExtractionService(config_path="nonexistent_config.yaml")
    
    def test_load_prompt_template_success(self, temp_config_file, temp_prompt_file):
        """Test successful prompt template loading"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            service = OpenRouterExtractionService(config_path=temp_config_file)
            
            # Mock the prompt file path
            with patch('builtins.open', mock_open_prompt_file(temp_prompt_file)):
                prompt_config = service.load_prompt_template("extraction", "patient_info")
                
                assert 'system_prompt' in prompt_config
                assert 'extraction_prompt' in prompt_config
                assert 'validation_rules' in prompt_config
    
    def test_load_prompt_template_caching(self, temp_config_file, temp_prompt_file):
        """Test prompt template caching functionality"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            service = OpenRouterExtractionService(config_path=temp_config_file)
            
            with patch('builtins.open', mock_open_prompt_file(temp_prompt_file)) as mock_open:
                # First call should read file
                service.load_prompt_template("extraction", "patient_info")
                # Second call should use cache
                service.load_prompt_template("extraction", "patient_info")
                
                # File should only be opened once due to caching
                assert mock_open.call_count == 1
    
    @patch('requests.Session.post')
    def test_extract_from_document_success(
        self, 
        mock_post, 
        temp_config_file, 
        extraction_config, 
        mock_api_response,
        mock_prompt_config
    ):
        """Test successful document extraction"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            service = OpenRouterExtractionService(config_path=temp_config_file)
            
            # Mock API response
            mock_response = Mock()
            mock_response.json.return_value = mock_api_response
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Mock prompt loading
            service.load_prompt_template = Mock(return_value=mock_prompt_config)
            
            # Create temporary document file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("Sample medical document content")
                doc_path = f.name
            
            try:
                result = service.extract_from_document(doc_path, extraction_config)
                
                assert isinstance(result, ExtractionResult)
                assert result.extraction_method == "openrouter_claude_3_5_sonnet"
                assert len(result.extracted_fields) > 0
                assert result.confidence_score > 0
                assert result.quality_assessment is not None
                assert result.processing_metadata is not None
                
                # Verify specific extracted fields
                assert 'patient_name' in result.extracted_fields
                assert result.extracted_fields['patient_name'].value == 'John Doe'
                assert result.extracted_fields['patient_name'].confidence == 0.95
                
            finally:
                os.unlink(doc_path)
    
    @patch('requests.Session.post')
    def test_extract_from_document_api_error(
        self, 
        mock_post, 
        temp_config_file, 
        extraction_config,
        mock_prompt_config
    ):
        """Test document extraction with API error"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            service = OpenRouterExtractionService(config_path=temp_config_file)
            
            # Mock API error response
            mock_response = Mock()
            mock_response.json.return_value = {'error': 'API rate limit exceeded'}
            mock_response.raise_for_status.side_effect = Exception("API Error")
            mock_post.return_value = mock_response
            
            # Mock prompt loading
            service.load_prompt_template = Mock(return_value=mock_prompt_config)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("Sample content")
                doc_path = f.name
            
            try:
                with pytest.raises(OpenRouterAPIError):
                    service.extract_from_document(doc_path, extraction_config)
            finally:
                os.unlink(doc_path)
    
    @patch('requests.Session.post')
    def test_extract_with_vision_success(
        self, 
        mock_post, 
        temp_config_file, 
        mock_prompt_config
    ):
        """Test successful vision-based extraction"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            service = OpenRouterExtractionService(config_path=temp_config_file)
            
            # Mock vision API response
            vision_response = {
                'choices': [{
                    'message': {
                        'content': json.dumps({
                            'visual_elements': [
                                {
                                    'element_type': 'table',
                                    'coordinates': {'x': 100, 'y': 200, 'width': 300, 'height': 150},
                                    'confidence': 0.9,
                                    'description': 'Patient information table'
                                }
                            ],
                            'text_regions': [
                                {
                                    'text': 'Patient: John Doe',
                                    'coordinates': {'x': 50, 'y': 50, 'width': 200, 'height': 20},
                                    'confidence': 0.95
                                }
                            ],
                            'confidence_score': 0.92
                        })
                    }
                }]
            }
            
            mock_response = Mock()
            mock_response.json.return_value = vision_response
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Mock prompt loading
            service.load_prompt_template = Mock(return_value=mock_prompt_config)
            
            # Create temporary image file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                f.write(b'fake image data')
                image_path = f.name
            
            try:
                result = service.extract_with_vision(image_path, "patient_info")
                
                assert isinstance(result, VisionExtractionResult)
                assert result.extraction_method == "openrouter_vision_claude_3_5_sonnet"
                assert len(result.visual_elements) > 0
                assert len(result.text_regions) > 0
                assert result.confidence_score == 0.92
                
            finally:
                os.unlink(image_path)
    
    def test_extract_with_vision_disabled(self, temp_config_file, mock_prompt_config):
        """Test vision extraction when vision is disabled"""
        # Modify config to disable vision
        config = {
            'api': {'base_url': 'https://openrouter.ai/api/v1', 'model': 'test', 'timeout': 60, 'max_retries': 3, 'retry_delay': 2},
            'extraction': {'max_tokens': 4000, 'temperature': 0.1, 'top_p': 0.9, 'presence_penalty': 0.0, 'frequency_penalty': 0.0},
            'quality_thresholds': {'minimum_confidence': 0.7, 'extraction_completeness': 0.8, 'field_accuracy': 0.85},
            'vision': {'enabled': False}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name
        
        try:
            with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
                service = OpenRouterExtractionService(config_path=config_path)
                
                with pytest.raises(ValueError, match="Vision extraction is not enabled"):
                    service.extract_with_vision("test.jpg", "patient_info")
        finally:
            os.unlink(config_path)
    
    def test_quality_assessment_calculation(self, temp_config_file):
        """Test quality assessment calculation"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            service = OpenRouterExtractionService(config_path=temp_config_file)
            
            # Create sample extracted fields
            extracted_fields = {
                'patient_name': ExtractedField(
                    name='patient_name',
                    value='John Doe',
                    confidence=0.95,
                    source_location='Page 1'
                ),
                'date_of_birth': ExtractedField(
                    name='date_of_birth',
                    value='01/15/1980',
                    confidence=0.90,
                    source_location='Page 1'
                ),
                'missing_field': ExtractedField(
                    name='missing_field',
                    value='NOT_FOUND',
                    confidence=0.0,
                    source_location=''
                )
            }
            
            quality_assessment = service._assess_extraction_quality(extracted_fields, {})
            
            assert isinstance(quality_assessment, QualityAssessment)
            assert 0.0 <= quality_assessment.overall_score <= 1.0
            assert 0.0 <= quality_assessment.completeness_score <= 1.0
            assert 0.0 <= quality_assessment.accuracy_score <= 1.0
            assert 0.0 <= quality_assessment.consistency_score <= 1.0
            assert 0.0 <= quality_assessment.compliance_score <= 1.0
    
    def test_confidence_intervals_calculation(self, temp_config_file):
        """Test confidence intervals calculation"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            service = OpenRouterExtractionService(config_path=temp_config_file)
            
            extracted_fields = {
                'test_field': ExtractedField(
                    name='test_field',
                    value='test_value',
                    confidence=0.8,
                    source_location='Page 1'
                )
            }
            
            intervals = service._calculate_confidence_intervals(extracted_fields)
            
            assert 'test_field' in intervals
            interval = intervals['test_field']
            assert interval.lower_bound <= 0.8 <= interval.upper_bound
            assert interval.confidence_level == 0.95
    
    def test_source_references_extraction(self, temp_config_file):
        """Test source references extraction"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            service = OpenRouterExtractionService(config_path=temp_config_file)
            
            extracted_fields = {
                'field_with_source': ExtractedField(
                    name='field_with_source',
                    value='test_value',
                    confidence=0.8,
                    source_location='Page 1, Section A'
                ),
                'field_without_source': ExtractedField(
                    name='field_without_source',
                    value='test_value',
                    confidence=0.8,
                    source_location=''
                )
            }
            
            references = service._extract_source_references(extracted_fields)
            
            # Only fields with source locations should have references
            assert len(references) == 1
            assert references[0].field_name == 'field_with_source'
            assert references[0].source_location == 'Page 1, Section A'
    
    def test_validation_results_generation(self, temp_config_file):
        """Test validation results generation"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            service = OpenRouterExtractionService(config_path=temp_config_file)
            
            extracted_fields = {
                'valid_field': ExtractedField(
                    name='valid_field',
                    value='valid_value',
                    confidence=0.8,
                    source_location='Page 1'
                ),
                'invalid_field': ExtractedField(
                    name='invalid_field',
                    value='NOT_FOUND',
                    confidence=0.0,
                    source_location=''
                )
            }
            
            validation_rules = {
                'valid_field': 'Must be present',
                'invalid_field': 'Must be present'
            }
            
            results = service._validate_extracted_data(extracted_fields, validation_rules)
            
            assert len(results) == 2
            
            # Find valid and invalid results
            valid_result = next(r for r in results if r.field_name == 'valid_field')
            invalid_result = next(r for r in results if r.field_name == 'invalid_field')
            
            assert valid_result.is_valid is True
            assert invalid_result.is_valid is False
            assert invalid_result.error_message != ""
    
    def test_document_id_generation(self, temp_config_file):
        """Test document ID generation"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            service = OpenRouterExtractionService(config_path=temp_config_file)
            
            doc_path = "/path/to/test_document.pdf"
            doc_id = service._generate_document_id(doc_path)
            
            assert doc_id.startswith("doc_")
            assert len(doc_id.split("_")) == 3  # doc_timestamp_hash
    
    def test_retry_logic_configuration(self, temp_config_file):
        """Test that retry logic is properly configured"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            service = OpenRouterExtractionService(config_path=temp_config_file)
            
            # Check that session has retry configuration
            assert service.session is not None
            
            # Verify headers are set correctly
            assert 'Authorization' in service.session.headers
            assert service.session.headers['Authorization'] == 'Bearer test-key'
            assert service.session.headers['Content-Type'] == 'application/json'
    
    def test_sonoma_sky_alpha_compatibility_validation(self, temp_config_file):
        """Test Sonoma Sky Alpha compatibility validation"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            service = OpenRouterExtractionService(config_path=temp_config_file)
            
            compatibility = service.validate_sonoma_sky_alpha_compatibility()
            
            assert isinstance(compatibility, dict)
            assert 'model_configured' in compatibility
            assert 'vision_enabled' in compatibility
            assert 'structured_output' in compatibility
            assert 'confidence_scoring' in compatibility
            assert 'api_key_present' in compatibility
            assert 'config_valid' in compatibility
            
            # API key should be present
            assert compatibility['api_key_present'] is True
    
    def test_fallback_extraction_disabled(self, temp_config_file, extraction_config):
        """Test fallback extraction when disabled"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            service = OpenRouterExtractionService(config_path=temp_config_file)
            service.enable_fallback = False
            
            result = service._perform_fallback_extraction(
                "test.txt", 
                extraction_config, 
                Exception("Test error")
            )
            
            assert result is None
    
    def test_rule_based_fallback_extraction(self, temp_config_file, extraction_config):
        """Test rule-based fallback extraction"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            service = OpenRouterExtractionService(config_path=temp_config_file)
            service.enable_fallback = True
            service.fallback_methods = ["rule_based"]
            
            # Create test document with extractable content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("Patient: John Doe\nDOB: 01/15/1980\nAge: 43")
                doc_path = f.name
            
            try:
                result = service._rule_based_extraction(doc_path, extraction_config)
                
                assert isinstance(result, ExtractionResult)
                assert result.extraction_method == "rule_based_fallback"
                assert len(result.extracted_fields) > 0
                assert result.confidence_score < 1.0  # Should be lower for fallback
                
                # Check if patient name was extracted
                if 'patient_name' in result.extracted_fields:
                    assert result.extracted_fields['patient_name'].value == 'John Doe'
                    assert result.extracted_fields['patient_name'].confidence < 1.0
                
            finally:
                os.unlink(doc_path)
    
    def test_performance_metrics_tracking(self, temp_config_file):
        """Test performance metrics tracking"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            service = OpenRouterExtractionService(config_path=temp_config_file)
            service.performance_tracking = True
            
            # Add some mock metrics
            service.request_metrics = [
                {'response_time': 1.5, 'token_usage': 1000, 'success': True},
                {'response_time': 2.0, 'token_usage': 1200, 'success': True},
                {'response_time': 3.0, 'token_usage': 800, 'success': False}
            ]
            
            metrics = service.get_performance_metrics()
            
            assert metrics['performance_tracking'] is True
            assert metrics['total_requests'] == 3
            assert metrics['average_response_time'] == 2.17  # Approximately
            assert metrics['success_rate'] == 2/3  # 2 out of 3 successful
            assert metrics['total_token_usage'] == 3000
            
            # Test clearing metrics
            service.clear_performance_metrics()
            assert len(service.request_metrics) == 0
    
    def test_enhanced_confidence_intervals(self, temp_config_file):
        """Test enhanced confidence interval calculation"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            service = OpenRouterExtractionService(config_path=temp_config_file)
            
            # Test with different field types
            extracted_fields = {
                'patient_name': ExtractedField(  # Critical field
                    name='patient_name',
                    value='John Doe',
                    confidence=0.9,
                    source_location='Page 1'
                ),
                'impairment_rating': ExtractedField(  # Important field
                    name='impairment_rating',
                    value='15%',
                    confidence=0.8,
                    source_location='Page 3'
                ),
                'notes': ExtractedField(  # Standard field
                    name='notes',
                    value='Additional notes',
                    confidence=0.7,
                    source_location='Page 4'
                )
            }
            
            intervals = service._calculate_confidence_intervals(extracted_fields)
            
            # Critical fields should have tighter intervals
            patient_interval = intervals['patient_name']
            notes_interval = intervals['notes']
            
            patient_margin = patient_interval.upper_bound - patient_interval.lower_bound
            notes_margin = notes_interval.upper_bound - notes_interval.lower_bound
            
            assert patient_margin < notes_margin  # Critical field has tighter interval


def mock_open_prompt_file(file_path):
    """Helper function to mock opening prompt files"""
    def mock_open(*args, **kwargs):
        if args[0] == file_path or args[0].endswith('patient_info.yaml'):
            return open(file_path, *args[1:], **kwargs)
        else:
            # For other files, return the original open
            return open(*args, **kwargs)
    return mock_open


class TestOpenRouterConfigurationManagement:
    """Test suite for configuration management functionality"""
    
    def test_config_validation_success(self):
        """Test successful configuration validation"""
        valid_config = {
            'api': {
                'base_url': 'https://openrouter.ai/api/v1',
                'model': 'anthropic/claude-3.5-sonnet:beta',
                'timeout': 60,
                'max_retries': 3,
                'retry_delay': 2
            },
            'extraction': {
                'max_tokens': 4000,
                'temperature': 0.1,
                'top_p': 0.9,
                'presence_penalty': 0.0,
                'frequency_penalty': 0.0
            },
            'quality_thresholds': {
                'minimum_confidence': 0.7,
                'extraction_completeness': 0.8,
                'field_accuracy': 0.85
            },
            'vision': {
                'enabled': True,
                'max_image_size': 10485760,
                'supported_formats': ['pdf', 'png', 'jpg', 'jpeg'],
                'dpi': 300
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_config, f)
            config_path = f.name
        
        try:
            with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
                service = OpenRouterExtractionService(config_path=config_path)
                assert service.config == valid_config
        finally:
            os.unlink(config_path)
    
    def test_config_validation_invalid_yaml(self):
        """Test configuration validation with invalid YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = f.name
        
        try:
            with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
                with pytest.raises(yaml.YAMLError):
                    OpenRouterExtractionService(config_path=config_path)
        finally:
            os.unlink(config_path)


class TestEnhancedConfigurationManager:
    """Test suite for enhanced configuration manager functionality"""
    
    def test_sonoma_sky_alpha_optimization(self):
        """Test configuration optimization for Sonoma Sky Alpha"""
        from src.config.openrouter_config_manager import OpenRouterConfigManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_manager = OpenRouterConfigManager(config_root=temp_dir)
            
            # Create basic config
            basic_config = {
                'api': {'base_url': 'https://openrouter.ai/api/v1', 'model': 'old-model'},
                'extraction': {'max_tokens': 2000},
                'quality_thresholds': {'minimum_confidence': 0.5}
            }
            
            config_manager.api_config = basic_config
            
            # Optimize for Sonoma Sky Alpha
            config_manager.optimize_configuration_for_sonoma_sky_alpha()
            
            # Verify optimizations
            assert config_manager.api_config['api']['model'] == 'anthropic/claude-3.5-sonnet:beta'
            assert config_manager.api_config['extraction']['max_tokens'] == 8000
            assert config_manager.api_config['extraction']['vision_enabled'] is True
            assert config_manager.api_config['quality_thresholds']['minimum_confidence'] == 0.75
            assert config_manager.api_config['vision']['enabled'] is True
    
    def test_configuration_export_import(self):
        """Test configuration export and import functionality"""
        from src.config.openrouter_config_manager import OpenRouterConfigManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_manager = OpenRouterConfigManager(config_root=temp_dir)
            
            # Set up test configuration
            test_config = {
                'api': {'model': 'test-model', 'base_url': 'https://test.com'},
                'extraction': {'max_tokens': 4000},
                'quality_thresholds': {'minimum_confidence': 0.8}
            }
            config_manager.api_config = test_config
            
            # Create a test prompt template
            config_manager.create_prompt_template(
                prompt_type="extraction",
                template_name="test_template",
                system_prompt="Test system prompt",
                main_prompt="Test main prompt",
                description="Test template"
            )
            
            # Export configuration
            export_path = os.path.join(temp_dir, "exported_config.yaml")
            config_manager.export_configuration(export_path)
            
            assert os.path.exists(export_path)
            
            # Create new config manager and import
            new_temp_dir = tempfile.mkdtemp()
            try:
                new_config_manager = OpenRouterConfigManager(config_root=new_temp_dir)
                new_config_manager.import_configuration(export_path, overwrite=True)
                
                # Verify import
                assert new_config_manager.api_config['api']['model'] == 'test-model'
                assert new_config_manager.api_config['extraction']['max_tokens'] == 4000
                
                # Verify template was imported
                template_path = Path(new_temp_dir) / "prompts" / "extraction" / "test_template.yaml"
                assert template_path.exists()
                
            finally:
                import shutil
                shutil.rmtree(new_temp_dir)
    
    def test_enhanced_configuration_summary(self):
        """Test enhanced configuration summary with new fields"""
        from src.config.openrouter_config_manager import OpenRouterConfigManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_manager = OpenRouterConfigManager(config_root=temp_dir)
            
            # Set up test configuration with enhanced features
            test_config = {
                'api': {'model': 'anthropic/claude-3.5-sonnet:beta'},
                'vision': {'enabled': True},
                'error_handling': {'enable_fallback_extraction': True},
                'performance': {'enable_monitoring': True},
                'quality_thresholds': {'minimum_confidence': 0.8}
            }
            config_manager.api_config = test_config
            
            summary = config_manager.get_configuration_summary()
            
            assert 'vision_enabled' in summary
            assert summary['vision_enabled'] is True
            assert 'error_handling' in summary
            assert 'performance_monitoring' in summary
            assert summary['performance_monitoring'] is True


if __name__ == "__main__":
    pytest.main([__file__])