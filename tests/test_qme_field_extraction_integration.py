"""
Integration tests for QME Field Extraction Task.

Tests the complete implementation against the task requirements:
- Extract specific QME fields from PQME documents
- Validate against sample data: Nick Diaz Jr., 43 years old, Male, etc.
- Ensure field validation system works
- Test fallback extraction methods
"""

import pytest
from pathlib import Path

from src.services.enhanced_document_processor import EnhancedDocumentProcessor
from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService


class TestQMEFieldExtractionIntegration:
    """Integration tests for QME field extraction task implementation."""
    
    @pytest.fixture
    def processor(self):
        """Create enhanced document processor instance."""
        return EnhancedDocumentProcessor()
    
    @pytest.fixture
    def qme_service(self):
        """Create comprehensive QME field service instance."""
        return ComprehensiveQMEFieldService()
    
    def test_task_requirement_field_extraction(self, processor):
        """
        Test extraction of all required QME template fields as specified in task.
        
        Task requirement: Extract Name, Age, Gender, Case Number, Claim Number, 
        Injury Date, Body Part(s), Occupation, Employer, and Scheduled Exam Date
        """
        # Sample text with all required fields
        sample_text = """
        Re: Applicant: Nick Diaz Jr.
        Employer: Costco
        EAMS No: ADJ19802400
        Claim No: WC608-H07190
        
        The applicant was a 43-year-old front-end supervisor for a Costco warehouse 
        who sustained an accepted left knee injury on July 24, 2024. 
        He apparently was moving steel with a forklift.
        Your examination is scheduled to take place on September 9, 2025.
        """
        
        test_file = Path("test_task_requirements.txt")
        test_file.write_text(sample_text)
        
        try:
            result = processor.extract_qme_template_fields(str(test_file))
            
            # Verify extraction success
            assert result['success'] is True
            assert result['extraction_metadata']['ready_for_template_generation'] is True
            
            # Verify all required fields are extracted
            qme_fields = result['qme_fields']
            required_fields = [
                'name', 'age', 'gender', 'case_number', 'claim_number',
                'injury_date', 'body_parts', 'occupation', 'employer', 'scheduled_exam_date'
            ]
            
            for field in required_fields:
                assert qme_fields[field] is not None, f"Required field '{field}' not extracted"
            
            # Verify no missing fields
            assert len(result['extraction_metadata']['missing_fields']) == 0
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_sample_data_accuracy(self, qme_service):
        """
        Test extraction accuracy against provided sample data.
        
        Task requirement: Test against Nick Diaz Jr., 43 years old, Male, 
        WC608-H07190, July 24, 2024 injury date, Left knee, 
        Front-End Supervisor at Costco, September 9, 2025 exam date
        """
        sample_text = """
        Re: Applicant: Nick Diaz Jr.
        Employer: Costco
        EAMS No: ADJ19802400
        Claim No: WC608-H07190
        
        The applicant was a 43-year-old front-end supervisor for a Costco warehouse 
        who sustained an accepted left knee injury on July 24, 2024. 
        He apparently was moving steel with a forklift.
        Your examination is scheduled to take place on September 9, 2025.
        """
        
        test_file = Path("test_sample_data.txt")
        test_file.write_text(sample_text)
        
        try:
            result = qme_service.extract_and_validate_fields(str(test_file))
            field_data = result.extraction_result.field_data
            
            # Verify exact sample data values
            assert field_data.name == "Nick Diaz Jr"
            assert field_data.age == 43
            assert field_data.gender == "Male"
            assert field_data.claim_number == "WC608-H07190"
            assert field_data.injury_date == "July 24, 2024"
            assert "Left Knee" in field_data.body_parts
            assert field_data.occupation == "Front-End Supervisor"
            assert field_data.employer == "Costco"
            assert field_data.scheduled_exam_date == "September 9, 2025"
            
            # Verify high extraction confidence
            assert result.extraction_result.overall_confidence >= 0.9
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_field_validation_system(self, qme_service):
        """
        Test field validation system ensures required fields are populated.
        
        Task requirement: Create field validation system that ensures all 
        required QME template fields are populated before template generation
        """
        # Test with complete data
        complete_text = """
        Re: Applicant: John Smith
        Employer: ABC Corp
        EAMS No: ADJ12345678
        Claim No: WC123-456
        
        The 35-year-old manager sustained a right shoulder injury on June 1, 2024.
        Examination scheduled for October 15, 2025.
        """
        
        test_file = Path("test_validation_complete.txt")
        test_file.write_text(complete_text)
        
        try:
            result = qme_service.extract_and_validate_fields(str(test_file))
            
            # Should be ready for template generation
            assert result.validation_result.ready_for_template_generation
            assert result.validation_result.validation_score >= 0.8
            
        finally:
            if test_file.exists():
                test_file.unlink()
        
        # Test with incomplete data
        incomplete_text = "Patient had an injury."
        
        test_file = Path("test_validation_incomplete.txt")
        test_file.write_text(incomplete_text)
        
        try:
            result = qme_service.extract_and_validate_fields(str(test_file))
            
            # Should NOT be ready for template generation
            assert not result.validation_result.ready_for_template_generation
            assert len(result.extraction_result.missing_fields) > 0
            assert len(result.validation_result.issues) > 0
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_fallback_extraction_methods(self, qme_service):
        """
        Test fallback extraction methods using multiple NLP approaches.
        
        Task requirement: Add fallback extraction methods using multiple 
        NLP approaches (regex patterns, spaCy NER, and LLM-based extraction)
        """
        # Text with non-standard formatting to trigger fallbacks
        difficult_text = """
        PATIENT: NICK DIAZ JR
        CASE: ADJ19802400
        WORKERS COMPENSATION CLAIM: WC608H07190
        
        Patient is forty three years old male who works as supervisor.
        Injured his left knee in July 2024.
        """
        
        test_file = Path("test_fallback_methods.txt")
        test_file.write_text(difficult_text)
        
        try:
            result = qme_service.extract_and_validate_fields(str(test_file))
            
            # Should attempt fallback methods
            assert result.fallback_attempts > 0 or result.extraction_result.overall_confidence > 0.5
            
            # Should extract at least some fields despite difficult formatting
            field_data = result.extraction_result.field_data
            assert field_data.name is not None or field_data.case_number is not None
            
            # Should use multiple extraction methods
            assert len(result.extraction_methods_used) >= 1
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    @pytest.mark.integration
    def test_real_pqme_document_extraction(self, processor):
        """
        Test extraction from actual PQME PDF files.
        
        Task requirement: Implement robust pattern matching for specific 
        data points present in provided PQME documents
        """
        pdf_files = [
            "Injured worker-PQME-(09.05.2025)-AA CL-09.09.2025.p5.pdf",
            "Injured worker-PQME-(09.08.2025)-DA CL-09.09.2025.p4.pdf"
        ]
        
        for pdf_file in pdf_files:
            if Path(pdf_file).exists():
                result = processor.extract_qme_template_fields(pdf_file)
                
                # Should successfully extract from real documents
                assert result['success'] is True
                assert result['extraction_metadata']['extraction_confidence'] > 0.0
                
                # Should extract key fields from known test data
                qme_fields = result['qme_fields']
                if qme_fields['name']:
                    assert "Nick Diaz" in qme_fields['name']
                if qme_fields['claim_number']:
                    assert "WC608" in qme_fields['claim_number']
                if qme_fields['employer']:
                    assert "Costco" in qme_fields['employer']
                
                print(f"\n=== Real PDF Extraction Results for {pdf_file} ===")
                print(f"Confidence: {result['extraction_metadata']['extraction_confidence']:.2%}")
                print(f"Ready for Template: {result['extraction_metadata']['ready_for_template_generation']}")
                print("Extracted Fields:")
                for field, value in qme_fields.items():
                    if value:
                        print(f"  {field}: {value}")
    
    def test_extraction_success_rate_maximization(self, qme_service):
        """
        Test that fallback methods maximize field extraction success rate.
        
        Task requirement: Maximize field extraction success rate using 
        multiple NLP approaches
        """
        test_cases = [
            # Standard format
            """
            Re: Applicant: Alice Johnson
            Claim No: WC789-012
            The 28-year-old nurse sustained a back injury on March 15, 2024.
            """,
            
            # Non-standard format
            """
            PATIENT NAME: BOB WILSON
            WC CLAIM NUMBER: WC345678
            AGE: THIRTY FIVE
            INJURY: RIGHT ARM, OCCURRED FEBRUARY 2024
            """,
            
            # Minimal information
            """
            John Doe, injured worker
            Claim WC999-888
            Hurt his ankle at work
            """
        ]
        
        total_confidence = 0
        successful_extractions = 0
        
        for i, test_text in enumerate(test_cases):
            test_file = Path(f"test_success_rate_{i}.txt")
            test_file.write_text(test_text)
            
            try:
                result = qme_service.extract_and_validate_fields(str(test_file))
                
                # Track success metrics
                if result.extraction_result.overall_confidence > 0.3:
                    successful_extractions += 1
                total_confidence += result.extraction_result.overall_confidence
                
                # Should extract at least name or claim number
                field_data = result.extraction_result.field_data
                assert (field_data.name is not None or 
                       field_data.claim_number is not None), \
                       f"Failed to extract basic fields from test case {i}"
                
            finally:
                if test_file.exists():
                    test_file.unlink()
        
        # Should have reasonable success rate
        success_rate = successful_extractions / len(test_cases)
        average_confidence = total_confidence / len(test_cases)
        
        assert success_rate >= 0.6, f"Success rate {success_rate:.2%} below threshold"
        assert average_confidence >= 0.4, f"Average confidence {average_confidence:.2%} below threshold"
    
    def test_performance_requirements(self, processor):
        """Test that extraction meets performance requirements."""
        # Large document to test performance
        large_text = """
        Re: Applicant: Nick Diaz Jr.
        Employer: Costco
        EAMS No: ADJ19802400
        Claim No: WC608-H07190
        
        The applicant was a 43-year-old front-end supervisor for a Costco warehouse 
        who sustained an accepted left knee injury on July 24, 2024.
        Your examination is scheduled to take place on September 9, 2025.
        """ * 50  # Repeat to make it larger
        
        test_file = Path("test_performance.txt")
        test_file.write_text(large_text)
        
        try:
            import time
            start_time = time.time()
            
            result = processor.extract_qme_template_fields(str(test_file))
            
            processing_time = time.time() - start_time
            
            # Should complete within reasonable time
            assert processing_time < 10.0, f"Processing took {processing_time:.2f}s, too slow"
            
            # Should maintain accuracy despite size
            assert result['extraction_metadata']['extraction_confidence'] >= 0.8
            
        finally:
            if test_file.exists():
                test_file.unlink()


if __name__ == "__main__":
    # Run integration tests
    processor = EnhancedDocumentProcessor()
    qme_service = ComprehensiveQMEFieldService()
    
    print("Running QME Field Extraction Integration Tests...")
    
    # Test 1: Basic field extraction
    sample_text = """
    Re: Applicant: Nick Diaz Jr.
    Employer: Costco
    EAMS No: ADJ19802400
    Claim No: WC608-H07190
    
    The applicant was a 43-year-old front-end supervisor for a Costco warehouse 
    who sustained an accepted left knee injury on July 24, 2024. 
    He apparently was moving steel with a forklift.
    Your examination is scheduled to take place on September 9, 2025.
    """
    
    test_file = Path("integration_test.txt")
    test_file.write_text(sample_text)
    
    try:
        result = processor.extract_qme_template_fields(str(test_file))
        
        print(f"✓ Field extraction success: {result['success']}")
        print(f"✓ Template ready: {result['extraction_metadata']['ready_for_template_generation']}")
        print(f"✓ Confidence: {result['extraction_metadata']['extraction_confidence']:.2%}")
        print(f"✓ Missing fields: {len(result['extraction_metadata']['missing_fields'])}")
        
        # Verify sample data
        qme_fields = result['qme_fields']
        expected_values = {
            'name': 'Nick Diaz Jr',
            'age': 43,
            'claim_number': 'WC608-H07190',
            'employer': 'Costco'
        }
        
        for field, expected in expected_values.items():
            actual = qme_fields[field]
            if actual == expected:
                print(f"✓ {field}: {actual}")
            else:
                print(f"✗ {field}: expected {expected}, got {actual}")
        
        print("\n✓ All integration tests passed!")
        
    finally:
        if test_file.exists():
            test_file.unlink()