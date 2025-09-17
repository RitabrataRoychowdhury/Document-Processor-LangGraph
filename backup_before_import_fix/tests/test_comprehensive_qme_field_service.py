"""
Tests for Comprehensive QME Field Service.

Tests the complete extraction and validation pipeline with real PDF files.
"""

import pytest
from pathlib import Path

from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService


class TestComprehensiveQMEFieldService:
    """Test suite for comprehensive QME field service."""
    
    @pytest.fixture
    def service(self):
        """Create comprehensive QME field service instance."""
        return ComprehensiveQMEFieldService()
    
    def test_complete_extraction_pipeline(self, service):
        """Test the complete extraction and validation pipeline."""
        # Test with sample text file
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
        
        # Create temporary test file
        test_file = Path("test_sample.txt")
        test_file.write_text(sample_text)
        
        try:
            result = service.extract_and_validate_fields(str(test_file))
            
            # Verify extraction results
            assert result.extraction_result.overall_confidence >= 0.9
            assert len(result.extraction_result.missing_fields) <= 1  # Allow for minor missing fields
            
            # Verify validation results
            assert result.validation_result.validation_score >= 0.8
            
            # Verify field values
            field_data = result.extraction_result.field_data
            assert field_data.name == "Nick Diaz Jr."
            assert field_data.age == 43
            assert field_data.gender == "Male"
            assert field_data.case_number == "ADJ19802400"
            assert field_data.claim_number == "WC608-H07190"
            assert field_data.injury_date == "July 24, 2024"
            assert "Left Knee" in field_data.body_parts
            assert field_data.occupation == "Front-End Supervisor"
            assert field_data.employer == "Costco"
            assert field_data.scheduled_exam_date == "September 9, 2025"
            
            # Verify processing metadata
            assert result.processing_time > 0
            assert 'regex_patterns' in result.extraction_methods_used
            
        finally:
            # Clean up test file
            if test_file.exists():
                test_file.unlink()
    
    @pytest.mark.integration
    def test_real_pdf_extraction(self, service):
        """Test extraction from real PQME PDF files."""
        pdf_files = [
            "Injured worker-PQME-(09.05.2025)-AA CL-09.09.2025.p5.pdf",
            "Injured worker-PQME-(09.08.2025)-DA CL-09.09.2025.p4.pdf"
        ]
        
        for pdf_file in pdf_files:
            if Path(pdf_file).exists():
                result = service.extract_and_validate_fields(pdf_file)
                
                # Should extract at least some fields
                assert result.extraction_result.overall_confidence > 0.0
                
                # Should have document info
                assert result.document_info['file_name'] == pdf_file
                assert result.document_info['file_type'] == '.pdf'
                assert result.document_info['extraction_success'] is True
                
                # Generate and print report for manual verification
                report = service.generate_comprehensive_report(result)
                print(f"\n=== Comprehensive Report for {pdf_file} ===")
                print(report)
                
                # Verify specific expected values for the known test data
                field_data = result.extraction_result.field_data
                if field_data.name:
                    assert "Nick Diaz" in field_data.name
                if field_data.claim_number:
                    assert "WC608" in field_data.claim_number
                if field_data.employer:
                    assert "Costco" in field_data.employer
    
    def test_fallback_extraction_methods(self, service):
        """Test fallback extraction methods with incomplete data."""
        # Text with some missing fields to trigger fallbacks
        incomplete_text = """
        DEFENDANT'S QME ADVOCACY LETTER
        
        Steven Bast, MD
        Re: Applicant: Nick Diaz Jr.
        EAMS No: ADJ19802400
        
        The applicant sustained an injury. He was working at the time.
        """
        
        # Create temporary test file
        test_file = Path("test_incomplete.txt")
        test_file.write_text(incomplete_text)
        
        try:
            result = service.extract_and_validate_fields(str(test_file))
            
            # Should have attempted fallback methods
            assert result.fallback_attempts > 0
            
            # Should extract available fields
            assert result.extraction_result.field_data.name == "Nick Diaz Jr."
            assert result.extraction_result.field_data.case_number == "ADJ19802400"
            
            # Should identify missing fields
            assert len(result.extraction_result.missing_fields) > 0
            
            # Should provide recommendations
            assert len(result.validation_result.recommendations) > 0
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_template_generation_readiness(self, service):
        """Test template generation readiness assessment."""
        # Complete data - should be ready
        complete_text = """
        Re: Applicant: Nick Diaz Jr.
        Employer: Costco
        EAMS No: ADJ19802400
        Claim No: WC608-H07190
        
        The 43-year-old front-end supervisor sustained a left knee injury on July 24, 2024.
        He was working for Costco warehouse. Examination scheduled for September 9, 2025.
        """
        
        test_file = Path("test_complete.txt")
        test_file.write_text(complete_text)
        
        try:
            result = service.extract_and_validate_fields(str(test_file))
            
            # Should be ready for template generation
            assert service.is_ready_for_template_generation(result)
            assert result.validation_result.ready_for_template_generation
            
        finally:
            if test_file.exists():
                test_file.unlink()
        
        # Incomplete data - should not be ready
        incomplete_text = "Patient had an injury."
        
        test_file = Path("test_minimal.txt")
        test_file.write_text(incomplete_text)
        
        try:
            result = service.extract_and_validate_fields(str(test_file))
            
            # Should not be ready for template generation
            assert not service.is_ready_for_template_generation(result)
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_comprehensive_report_generation(self, service):
        """Test comprehensive report generation."""
        sample_text = """
        Re: Applicant: John Smith
        Claim No: WC123-456
        The patient sustained an injury on January 1, 2024.
        """
        
        test_file = Path("test_report.txt")
        test_file.write_text(sample_text)
        
        try:
            result = service.extract_and_validate_fields(str(test_file))
            report = service.generate_comprehensive_report(result)
            
            # Verify report contains expected sections
            assert "Comprehensive QME Field Extraction Report" in report
            assert "Processing Time:" in report
            assert "Extraction Methods Used:" in report
            assert "Document Information:" in report
            assert "Extraction Results:" in report
            assert "Validation Results:" in report
            
            # Should contain extracted data
            assert "John Smith" in report
            assert "WC123-456" in report
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_error_handling(self, service):
        """Test error handling for invalid files."""
        # Test with non-existent file
        result = service.extract_and_validate_fields("non_existent_file.pdf")
        
        # Should handle gracefully
        assert result.document_info['extraction_success'] is False
        assert 'extraction_error' in result.document_info
        
        # Should still provide validation results
        assert result.validation_result is not None
        assert not result.validation_result.ready_for_template_generation
    
    def test_performance_benchmarks(self, service):
        """Test performance benchmarks for extraction speed."""
        sample_text = """
        Re: Applicant: Nick Diaz Jr.
        Employer: Costco
        EAMS No: ADJ19802400
        Claim No: WC608-H07190
        
        The applicant was a 43-year-old front-end supervisor for a Costco warehouse 
        who sustained an accepted left knee injury on July 24, 2024.
        Your examination is scheduled to take place on September 9, 2025.
        """ * 10  # Make it larger to test performance
        
        test_file = Path("test_performance.txt")
        test_file.write_text(sample_text)
        
        try:
            result = service.extract_and_validate_fields(str(test_file))
            
            # Should complete within reasonable time (adjust as needed)
            assert result.processing_time < 5.0  # 5 seconds max
            
            # Should still maintain accuracy
            assert result.extraction_result.overall_confidence >= 0.8
            
        finally:
            if test_file.exists():
                test_file.unlink()


if __name__ == "__main__":
    # Run basic integration test
    service = ComprehensiveQMEFieldService()
    
    # Test with sample data
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
    
    test_file = Path("test_integration.txt")
    test_file.write_text(sample_text)
    
    try:
        result = service.extract_and_validate_fields(str(test_file))
        report = service.generate_comprehensive_report(result)
        print(report)
        
        print(f"\nTemplate Generation Ready: {service.is_ready_for_template_generation(result)}")
        
    finally:
        if test_file.exists():
            test_file.unlink()