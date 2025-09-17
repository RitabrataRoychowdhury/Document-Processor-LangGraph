"""
Pytest configuration and shared fixtures for the QME system tests.

This module provides common fixtures, test configuration, and utilities
used across all test modules in the QME system.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock
import json
from datetime import datetime

# Test configuration
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Provide test configuration."""
    return {
        "app": {
            "name": "QME System Test",
            "version": "1.0.0",
            "environment": "test",
            "debug": True,
            "log_level": "DEBUG"
        },
        "database": {
            "type": "sqlite",
            "path": ":memory:",
            "pool_size": 1,
            "timeout": 30
        },
        "storage": {
            "documents_path": "test_data/documents",
            "results_path": "test_data/results",
            "cache_path": "test_data/cache",
            "exports_path": "test_data/exports"
        },
        "validation": {
            "confidence_threshold": 0.8,
            "flagged_threshold": 0.5,
            "enable_strict_validation": False,
            "max_validation_errors": 10
        },
        "generation": {
            "template_cache_size": 10,
            "max_content_length": 10000,
            "enable_preview": True,
            "output_formats": ["docx"]
        }
    }


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_document_path(temp_dir: Path) -> Path:
    """Create a sample document file for testing."""
    doc_path = temp_dir / "sample_document.txt"
    doc_content = """
    QUALIFIED MEDICAL EVALUATOR REPORT
    
    Patient Name: John Doe
    Date of Birth: 01/15/1980
    Date of Injury: 03/20/2023
    
    HISTORY OF PRESENT ILLNESS:
    The patient is a 43-year-old male who sustained an injury to his lower back
    while lifting heavy boxes at work on March 20, 2023.
    
    PHYSICAL EXAMINATION:
    Range of Motion:
    - Flexion: 45 degrees (Normal: 90 degrees)
    - Extension: 15 degrees (Normal: 30 degrees)
    - Right Lateral Flexion: 20 degrees (Normal: 30 degrees)
    - Left Lateral Flexion: 18 degrees (Normal: 30 degrees)
    
    DIAGNOSIS:
    Lumbar strain with restricted range of motion
    
    IMPAIRMENT RATING:
    Based on AMA Guides 5th Edition, Table 15-3
    DRE Category II: 8% whole person impairment
    """
    
    doc_path.write_text(doc_content)
    return doc_path


@pytest.fixture
def sample_extracted_fields() -> Dict[str, Any]:
    """Provide sample extracted field data."""
    return {
        "patient_name": "John Doe",
        "date_of_birth": "01/15/1980",
        "date_of_injury": "03/20/2023",
        "age": 43,
        "gender": "male",
        "injury_description": "injury to his lower back while lifting heavy boxes at work",
        "rom_measurements": {
            "flexion": 45,
            "extension": 15,
            "right_lateral_flexion": 20,
            "left_lateral_flexion": 18
        },
        "diagnosis": "Lumbar strain with restricted range of motion",
        "impairment_rating": 8,
        "impairment_category": "DRE Category II"
    }


@pytest.fixture
def sample_confidence_scores() -> Dict[str, float]:
    """Provide sample confidence scores for extracted fields."""
    return {
        "patient_name": 0.95,
        "date_of_birth": 0.92,
        "date_of_injury": 0.88,
        "age": 0.90,
        "gender": 0.85,
        "injury_description": 0.82,
        "rom_measurements": 0.87,
        "diagnosis": 0.91,
        "impairment_rating": 0.94,
        "impairment_category": 0.89
    }


@pytest.fixture
def sample_evidence_snippets() -> Dict[str, list]:
    """Provide sample evidence snippets for extracted fields."""
    return {
        "patient_name": ["Patient Name: John Doe"],
        "date_of_birth": ["Date of Birth: 01/15/1980"],
        "date_of_injury": ["Date of Injury: 03/20/2023"],
        "age": ["43-year-old male"],
        "gender": ["43-year-old male"],
        "injury_description": ["sustained an injury to his lower back while lifting heavy boxes at work"],
        "rom_measurements": [
            "Flexion: 45 degrees (Normal: 90 degrees)",
            "Extension: 15 degrees (Normal: 30 degrees)",
            "Right Lateral Flexion: 20 degrees (Normal: 30 degrees)",
            "Left Lateral Flexion: 18 degrees (Normal: 30 degrees)"
        ],
        "diagnosis": ["Lumbar strain with restricted range of motion"],
        "impairment_rating": ["8% whole person impairment"],
        "impairment_category": ["DRE Category II"]
    }


@pytest.fixture
def mock_extraction_service() -> Mock:
    """Create a mock extraction service."""
    service = AsyncMock()
    service.extract_fields.return_value = Mock(
        success=True,
        extracted_fields={"patient_name": "John Doe", "age": 43},
        confidence_scores={"patient_name": 0.95, "age": 0.90},
        evidence_snippets={"patient_name": ["Patient Name: John Doe"], "age": ["43-year-old"]},
        processing_time=2.5
    )
    service.calculate_confidence.return_value = {"patient_name": 0.95, "age": 0.90}
    service.collect_evidence.return_value = {
        "patient_name": ["Patient Name: John Doe"],
        "age": ["43-year-old"]
    }
    return service


@pytest.fixture
def mock_validation_service() -> Mock:
    """Create a mock validation service."""
    service = AsyncMock()
    service.validate_extraction.return_value = Mock(
        success=True,
        is_valid=True,
        accepted_fields={"patient_name": "John Doe"},
        flagged_fields={"age": 43},
        missing_fields=[],
        validation_errors=[]
    )
    service.check_compliance.return_value = Mock(
        success=True,
        is_valid=True,
        compliance_issues=[]
    )
    service.validate_quality.return_value = Mock(
        success=True,
        is_valid=True,
        quality_score=0.92
    )
    return service


@pytest.fixture
def mock_generation_service() -> Mock:
    """Create a mock generation service."""
    service = AsyncMock()
    service.generate_content.return_value = Mock(
        success=True,
        generated_content={"sections": {"history": "Sample history", "examination": "Sample exam"}},
        processing_time=3.2
    )
    service.assemble_template.return_value = Mock(
        success=True,
        template_data=b"mock docx content",
        quality_score=0.95
    )
    service.customize_output.return_value = Mock(
        success=True,
        template_data=b"customized docx content"
    )
    return service


@pytest.fixture
def mock_knowledge_service() -> Mock:
    """Create a mock knowledge service."""
    service = AsyncMock()
    service.query_knowledge_base.return_value = {
        "answer": "Sample answer from knowledge base",
        "sources": [
            {"title": "AMA Guides", "page": 123, "confidence": 0.92},
            {"title": "QME Study Guide", "page": 45, "confidence": 0.88}
        ],
        "confidence": 0.90
    }
    service.update_knowledge_base.return_value = True
    service.get_references.return_value = [
        {"title": "Reference 1", "content": "Sample content", "type": "guideline"},
        {"title": "Reference 2", "content": "Sample content", "type": "regulation"}
    ]
    return service


@pytest.fixture
def mock_storage_service() -> Mock:
    """Create a mock storage service."""
    service = AsyncMock()
    service.store_document.return_value = "doc_123"
    service.retrieve_document.return_value = b"mock document content"
    service.store_results.return_value = "result_456"
    service.get_audit_trail.return_value = [
        {
            "timestamp": datetime.now().isoformat(),
            "event": "document_uploaded",
            "user": "test_user",
            "data": {"document_id": "doc_123"}
        }
    ]
    return service


@pytest.fixture
def mock_monitoring_service() -> Mock:
    """Create a mock monitoring service."""
    service = AsyncMock()
    service.log_event.return_value = None
    service.track_performance.return_value = None
    service.check_health.return_value = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": {"status": "up", "response_time_ms": 5.2},
            "knowledge_base": {"status": "up", "response_time_ms": 12.8}
        }
    }
    service.get_metrics.return_value = {
        "requests_total": 1234,
        "requests_per_second": 5.6,
        "average_response_time": 245.7,
        "error_rate": 0.02
    }
    return service


@pytest.fixture
def sample_workflow_state() -> Dict[str, Any]:
    """Provide sample workflow state data."""
    return {
        "workflow_id": "workflow_123",
        "document_id": "doc_123",
        "status": "in_progress",
        "current_stage": "extraction",
        "progress": 45,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "pipeline_1_result": {
            "extraction_completed": True,
            "validation_completed": False,
            "extracted_fields": {"patient_name": "John Doe"},
            "confidence_scores": {"patient_name": 0.95}
        },
        "pipeline_2_result": None,
        "metadata": {
            "user_id": "user_123",
            "document_type": "pqme",
            "processing_options": {"strict_validation": False}
        }
    }


@pytest.fixture
def expected_template_structure() -> Dict[str, Any]:
    """Provide expected template structure for validation."""
    return {
        "header": {
            "title": "QUALIFIED MEDICAL EVALUATOR REPORT",
            "doctor_info": {
                "name": "Dr. Test Doctor",
                "license": "12345",
                "address": "123 Test St, Test City, CA 90210"
            },
            "patient_info": {
                "name": "John Doe",
                "dob": "01/15/1980",
                "date_of_injury": "03/20/2023"
            }
        },
        "sections": {
            "history": {"required": True, "min_length": 100},
            "examination": {"required": True, "min_length": 200},
            "diagnosis": {"required": True, "min_length": 50},
            "impairment_rating": {"required": True, "min_length": 100},
            "work_restrictions": {"required": False, "min_length": 50},
            "future_medical_care": {"required": False, "min_length": 50}
        },
        "footer": {
            "signature_block": {"required": True},
            "date": {"required": True},
            "declaration": {"required": True, "text": "Labor Code 4062.3"}
        }
    }


@pytest.fixture
def performance_benchmarks() -> Dict[str, float]:
    """Provide performance benchmarks for testing."""
    return {
        "document_extraction_max_time": 30.0,  # seconds
        "validation_max_time": 10.0,  # seconds
        "template_generation_max_time": 45.0,  # seconds
        "knowledge_base_query_max_time": 5.0,  # seconds
        "end_to_end_max_time": 120.0,  # seconds
        "memory_usage_max_mb": 500.0,  # MB
        "cpu_usage_max_percent": 80.0  # percent
    }


@pytest.fixture
def test_database_url() -> str:
    """Provide test database URL."""
    return "sqlite:///:memory:"


@pytest.fixture
async def async_client():
    """Create an async HTTP client for API testing."""
    from httpx import AsyncClient
    async with AsyncClient() as client:
        yield client


class TestDataFactory:
    """Factory for creating test data objects."""
    
    @staticmethod
    def create_document_metadata(**kwargs) -> Dict[str, Any]:
        """Create document metadata for testing."""
        defaults = {
            "document_id": "test_doc_123",
            "filename": "test_document.pdf",
            "file_size": 1024000,
            "upload_time": datetime.now().isoformat(),
            "document_type": "pqme",
            "patient_name": "Test Patient",
            "user_id": "test_user"
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_extraction_result(**kwargs) -> Dict[str, Any]:
        """Create extraction result for testing."""
        defaults = {
            "success": True,
            "document_id": "test_doc_123",
            "extracted_fields": {"patient_name": "Test Patient", "age": 35},
            "confidence_scores": {"patient_name": 0.95, "age": 0.88},
            "evidence_snippets": {
                "patient_name": ["Patient Name: Test Patient"],
                "age": ["35-year-old patient"]
            },
            "processing_time": 15.5,
            "metadata": {"extractor_version": "1.0.0", "model_used": "test_model"}
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_validation_result(**kwargs) -> Dict[str, Any]:
        """Create validation result for testing."""
        defaults = {
            "success": True,
            "document_id": "test_doc_123",
            "is_valid": True,
            "accepted_fields": {"patient_name": "Test Patient"},
            "flagged_fields": {"age": 35},
            "missing_fields": [],
            "validation_errors": [],
            "compliance_status": {
                "legal_compliance": True,
                "ama_compliance": True,
                "quality_score": 0.92
            }
        }
        defaults.update(kwargs)
        return defaults


@pytest.fixture
def test_data_factory() -> TestDataFactory:
    """Provide test data factory."""
    return TestDataFactory()


# Pytest markers for test categorization
pytestmark = [
    pytest.mark.asyncio,
]


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "benchmark: mark test as benchmark test")
    config.addinivalue_line("markers", "requires_api_key: mark test as requiring API key")
    config.addinivalue_line("markers", "requires_database: mark test as requiring database")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "end_to_end" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.benchmark)
        
        # Add slow marker for tests that take longer than expected
        if "test_end_to_end" in item.name or "test_performance" in item.name:
            item.add_marker(pytest.mark.slow)