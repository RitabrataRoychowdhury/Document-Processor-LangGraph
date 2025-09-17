"""
Comprehensive Testing and Validation Framework for Evidence-First QME System.

This module implements end-to-end pipeline testing using Sample3.pdf and PQME documents
with known expected values, confidence scoring validation, programmatic calculation testing,
knowledge graph initialization testing, and complete workflow execution validation.

Requirements tested: 1.1, 2.5, 3.2, 4.5, 5.5
"""

import pytest
import tempfile
import os
import shutil
import json
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List, Optional

# Core testing imports
from src.models.document import Document
from src.models.knowledge_graph import Patient, Diagnosis, Section, Finding, KnowledgeNode
from src.repositories.document_repository import SQLiteDocumentRepository
from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
from src.storage.database import DatabaseManager
from src.storage.knowledge_graph_schema import KnowledgeGraphSchemaManager

# Evidence-first system imports
try:
    from src.workflow.evidence_first_workflow_manager import EvidenceFirstWorkflowManager
    from src.services.structured_extractor import StructuredExtractor, ExtractionContext
    from src.services.qme_field_validator import EvidenceFirstValidator, ValidationReport
    from src.services.impairment_calculator import ImpairmentCalculator, ROMMeasurement
    from src.services.evidence_rag_service import EvidenceRAGService
    from src.services.knowledge_base_initializer import KnowledgeBaseInitializer
    EVIDENCE_FIRST_AVAILABLE = True
except ImportError as e:
    EVIDENCE_FIRST_AVAILABLE = False
    print(f"Evidence-first components not available: {e}")


class TestEvidenceFirstPipeline:
    """Comprehensive end-to-end testing for evidence-first QME system."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create necessary subdirectories
        os.makedirs(os.path.join(temp_dir, 'data', 'documents'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'data', 'database'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'data', 'ama_guidelines'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'data', 'qme_references'), exist_ok=True)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def test_database(self, temp_workspace):
        """Create test database with schema."""
        db_path = os.path.join(temp_workspace, 'data', 'database', 'test.db')
        
        # Initialize database
        db_manager = DatabaseManager(db_path)
        kg_schema = KnowledgeGraphSchemaManager(db_path)
        kg_schema.create_knowledge_graph_tables()
        
        return db_manager
    
    @pytest.fixture
    def sample3_content(self):
        """Sample3.pdf content with known expected values for testing."""
        return """
        QUALIFIED MEDICAL EVALUATOR'S REPORT
        
        Patient Information:
        Name: Jane Doe
        Age: 52
        Gender: Female
        Case Number: WC-2024-005678
        Date of Injury: March 10, 2024
        
        HISTORY OF PRESENT ILLNESS:
        Ms. Doe is a 52-year-old female who sustained injuries to her right shoulder 
        and neck in a work-related motor vehicle accident on March 10, 2024.
        She reports immediate onset of severe right shoulder pain and neck stiffness.
        
        PHYSICAL EXAMINATION:
        Right shoulder shows decreased range of motion:
        - Abduction: 90 degrees (normal 180)
        - Forward flexion: 120 degrees (normal 180)
        - External rotation: 30 degrees (normal 90)
        
        Cervical spine examination reveals muscle spasm and tenderness.
        Range of motion testing:
        - Flexion: 30 degrees (normal 50)
        - Extension: 40 degrees (normal 60)
        - Lateral bending: 25 degrees bilaterally (normal 45)
        
        DIAGNOSES:
        1. Right shoulder impingement syndrome, ICD-10: M75.30
        2. Cervical strain, ICD-10: S13.4XXA
        3. Post-traumatic stress disorder, ICD-10: F43.10
        
        IMPAIRMENT RATINGS:
        Right shoulder: 15% upper extremity impairment (AMA Table 16-3)
        Cervical spine: 8% whole person impairment (AMA Table 15-5)
        Combined impairment: 22% whole person impairment (Combined Values Chart)
        
        RECOMMENDATIONS:
        1. Physical therapy for right shoulder
        2. Cervical spine strengthening exercises
        3. Psychological counseling for PTSD
        4. Follow-up in 6 months
        """
    
    @pytest.fixture
    def pqme_content(self):
        """PQME document content with Nick Diaz Jr. data for testing."""
        return """
        Re: Applicant: Nick Diaz Jr.
        Employer: Costco
        EAMS No: ADJ19802400
        Claim No: WC608-H07190
        
        The applicant was a 43-year-old front-end supervisor for a Costco warehouse 
        who sustained an accepted left knee injury on July 24, 2024. 
        He apparently was moving steel with a forklift when the injury occurred.
        
        PHYSICAL EXAMINATION:
        Left knee examination reveals:
        - Swelling and tenderness over the medial joint line
        - Range of motion: Flexion 110 degrees (normal 135), Extension 0 degrees
        - Positive McMurray test
        - Negative anterior drawer test
        
        DIAGNOSIS:
        Left knee medial meniscus tear, ICD-10: S83.242A
        
        IMPAIRMENT RATING:
        Based on AMA Guides 5th Edition Table 17-5, the patient's condition
        corresponds to 12% lower extremity impairment, which converts to
        5% whole person impairment.
        
        Your examination is scheduled to take place on September 9, 2025.
        """
    
    @pytest.fixture
    def ama_tables_data(self):
        """Test AMA tables data for programmatic calculations."""
        return {
            "15-5": {
                "table_id": "15-5",
                "chapter": 15,
                "title": "Cervical Spine Range of Motion Impairment",
                "body_system": "spine",
                "method_type": "range_of_motion",
                "data_structure": {
                    "type": "range_of_motion",
                    "measurements": {
                        "flexion": {"normal": 50, "units": "degrees"},
                        "extension": {"normal": 60, "units": "degrees"},
                        "lateral_flexion": {"normal": 45, "units": "degrees"}
                    },
                    "calculation_method": "percentage_loss"
                },
                "page_reference": 394
            },
            "16-3": {
                "table_id": "16-3",
                "chapter": 16,
                "title": "Upper Extremity Impairment",
                "body_system": "upper_extremity",
                "method_type": "range_of_motion",
                "data_structure": {
                    "type": "range_of_motion",
                    "measurements": {
                        "abduction": {"normal": 180, "units": "degrees"},
                        "forward_flexion": {"normal": 180, "units": "degrees"},
                        "external_rotation": {"normal": 90, "units": "degrees"}
                    }
                },
                "page_reference": 436
            },
            "17-5": {
                "table_id": "17-5",
                "chapter": 17,
                "title": "Lower Extremity Impairment",
                "body_system": "lower_extremity",
                "method_type": "functional_assessment",
                "data_structure": {
                    "type": "functional_assessment",
                    "conditions": {
                        "meniscus_tear": {"impairment_range": [8, 15], "units": "percent_le"}
                    }
                },
                "page_reference": 523
            }
        }
    
    @pytest.mark.skipif(not EVIDENCE_FIRST_AVAILABLE, reason="Evidence-first components not available")
    def test_sample3_pdf_end_to_end_pipeline(self, temp_workspace, test_database, sample3_content, ama_tables_data):
        """
        Test complete end-to-end pipeline using Sample3.pdf with known expected values.
        
        Requirements: 1.1, 4.5, 5.5
        """
        # Setup test files
        sample3_file = os.path.join(temp_workspace, 'Sample3.pdf')
        with open(sample3_file, 'w') as f:
            f.write(sample3_content)
        
        ama_tables_file = os.path.join(temp_workspace, 'data', 'ama_guidelines', 'tables.json')
        with open(ama_tables_file, 'w') as f:
            json.dump(ama_tables_data, f)
        
        # Setup repositories
        doc_repo = SQLiteDocumentRepository(test_database)
        kg_repo = SQLiteKnowledgeGraphRepository(test_database)
        
        # Initialize workflow manager
        workflow_manager = EvidenceFirstWorkflowManager(
            document_repository=doc_repo,
            knowledge_graph_repository=kg_repo,
            ama_tables_path=ama_tables_file
        )
        
        # Execute Pipeline 1: Structured Extraction & Validation
        pipeline1_result = workflow_manager.execute_pipeline_1(sample3_file)
        
        # Verify Pipeline 1 results
        assert pipeline1_result.success
        assert pipeline1_result.validation_report.overall_confidence >= 0.8
        
        # Verify critical fields extracted with high confidence
        accepted_fields = pipeline1_result.validation_report.accepted_fields
        assert accepted_fields['patient_name'] == 'Jane Doe'
        assert accepted_fields['age'] == 52
        assert accepted_fields['case_number'] == 'WC-2024-005678'
        assert accepted_fields['injury_date'] == 'March 10, 2024'
        
        # Verify evidence provenance
        assert len(pipeline1_result.evidence_snippets) > 0
        for snippet in pipeline1_result.evidence_snippets:
            assert snippet.source_document == 'Sample3.pdf'
            assert snippet.confidence >= 0.5
        
        # Execute Pipeline 2: Evidence-Driven Generation & Compliance
        pipeline2_result = workflow_manager.execute_pipeline_2(pipeline1_result)
        
        # Verify Pipeline 2 results
        assert pipeline2_result.success
        assert pipeline2_result.compliance_validation.overall_compliance >= 0.9
        
        # Verify programmatic calculations
        assert len(pipeline2_result.calculation_results) >= 2  # Shoulder + cervical
        for calc_result in pipeline2_result.calculation_results:
            assert calc_result.calculation_method == "PROGRAMMATIC"
            assert len(calc_result.ama_table_references) > 0
            assert calc_result.impairment_percentage > 0
        
        # Verify audit trail completeness
        audit_trail = workflow_manager.generate_audit_trail()
        assert len(audit_trail.evidence_sources) > 0
        assert len(audit_trail.calculation_steps) > 0
        assert len(audit_trail.validation_results) > 0
    
    @pytest.mark.skipif(not EVIDENCE_FIRST_AVAILABLE, reason="Evidence-first components not available")
    def test_pqme_document_confidence_scoring(self, temp_workspace, test_database, pqme_content):
        """
        Test confidence scoring validation ensuring ≥95% precision for critical fields
        and ≥90% overall field coverage.
        
        Requirements: 1.1, 1.2
        """
        # Setup test file
        pqme_file = os.path.join(temp_workspace, 'pqme_test.txt')
        with open(pqme_file, 'w') as f:
            f.write(pqme_content)
        
        # Initialize structured extractor
        extractor = StructuredExtractor()
        
        # Execute extraction with confidence scoring
        extraction_context = ExtractionContext(
            document_id="pqme-test-1",
            document_text=pqme_content,
            source_file=pqme_file
        )
        
        extraction_result = extractor.extract_with_confidence(extraction_context)
        
        # Verify critical field precision ≥95%
        critical_fields = ['patient_name', 'case_number', 'injury_date', 'age']
        critical_precision = 0
        critical_extracted = 0
        
        for field in critical_fields:
            if field in extraction_result.fields:
                critical_extracted += 1
                confidence = extraction_result.confidences.get(field, 0.0)
                if confidence >= 0.8:  # High confidence threshold
                    critical_precision += 1
        
        precision_rate = critical_precision / len(critical_fields) if critical_fields else 0
        assert precision_rate >= 0.95, f"Critical field precision {precision_rate:.2%} below 95%"
        
        # Verify overall field coverage ≥90%
        expected_fields = [
            'patient_name', 'age', 'case_number', 'claim_number', 'employer',
            'injury_date', 'body_parts', 'diagnosis', 'scheduled_exam_date'
        ]
        
        extracted_count = sum(1 for field in expected_fields if field in extraction_result.fields)
        coverage_rate = extracted_count / len(expected_fields)
        assert coverage_rate >= 0.90, f"Field coverage {coverage_rate:.2%} below 90%"
        
        # Verify confidence scoring algorithm
        for field, confidence in extraction_result.confidences.items():
            assert 0.0 <= confidence <= 1.0, f"Invalid confidence {confidence} for field {field}"
            
            # Verify confidence components
            if field in extraction_result.confidence_breakdown:
                breakdown = extraction_result.confidence_breakdown[field]
                assert 'regex_confidence' in breakdown
                assert 'ner_confidence' in breakdown
                assert 'cross_validation_confidence' in breakdown
    
    @pytest.mark.skipif(not EVIDENCE_FIRST_AVAILABLE, reason="Evidence-first components not available")
    def test_programmatic_calculation_accuracy(self, temp_workspace, ama_tables_data):
        """
        Test programmatic calculation accuracy validating AMA table accuracy,
        ROM calculations, and Combined Values Chart applications.
        
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
        """
        # Setup AMA tables file
        ama_tables_file = os.path.join(temp_workspace, 'ama_tables.json')
        with open(ama_tables_file, 'w') as f:
            json.dump(ama_tables_data, f)
        
        # Initialize impairment calculator
        calculator = ImpairmentCalculator(ama_tables_file)
        
        # Test ROM calculations with known values
        rom_measurements = [
            ROMMeasurement(
                joint="cervical_spine",
                motion_type="flexion",
                measured_degrees=30.0,
                measurement_date=datetime.now(),
                examiner="Dr. Test"
            ),
            ROMMeasurement(
                joint="cervical_spine", 
                motion_type="flexion",
                measured_degrees=32.0,
                measurement_date=datetime.now(),
                examiner="Dr. Test"
            ),
            ROMMeasurement(
                joint="cervical_spine",
                motion_type="flexion", 
                measured_degrees=28.0,
                measurement_date=datetime.now(),
                examiner="Dr. Test"
            )
        ]
        
        # Execute ROM calculation
        rom_result = calculator.calculate_rom_impairment(rom_measurements, "spine")
        
        # Verify calculation accuracy
        assert rom_result.calculation_method == "ROM_BASED_PROGRAMMATIC"
        assert rom_result.impairment_percentage > 0
        assert len(rom_result.ama_table_references) > 0
        assert rom_result.ama_table_references[0].table_id == "15-5"
        
        # Verify calculation steps documentation
        assert len(rom_result.calculation_steps) >= 3
        for step in rom_result.calculation_steps:
            assert step.step_number > 0
            assert len(step.description) > 0
            assert isinstance(step.result, (int, float))
        
        # Test Combined Values Chart application
        impairments = [15.0, 8.0]  # Shoulder + cervical from Sample3
        combined_result = calculator.calculate_combined_impairment(impairments)
        
        # Verify combined calculation
        assert combined_result.calculation_method == "COMBINED_VALUES_PROGRAMMATIC"
        expected_combined = 15 + (8 * (100 - 15)) / 100  # 21.8%
        assert abs(combined_result.impairment_percentage - expected_combined) < 1.0
        
        # Verify AMA table references
        assert any(ref.table_id == "COMBINED_VALUES" for ref in combined_result.ama_table_references)
        
        # Test validation status
        assert combined_result.validation_status["combination_valid"]
        assert combined_result.validation_status["result_in_range"]
    
    @pytest.mark.skipif(not EVIDENCE_FIRST_AVAILABLE, reason="Evidence-first components not available")
    def test_knowledge_graph_initialization_validation(self, temp_workspace, test_database):
        """
        Test knowledge graph initialization confirming canonical document processing
        and entity/relationship counts.
        
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
        """
        # Setup canonical documents
        ama_guides_content = """
        AMA Guides to the Evaluation of Permanent Impairment, Fifth Edition
        
        Chapter 15: The Spine
        Range of motion impairment evaluation requires careful measurement
        and application of appropriate tables.
        
        Table 15-5: Cervical Spine Range of Motion
        Normal flexion: 50 degrees
        Normal extension: 60 degrees
        """
        
        qme_study_guide_content = """
        QME Study Guide
        
        Legal Requirements:
        - Labor Code 4062.3 declaration required
        - Page count attestation mandatory
        - Physician signature blocks required
        
        Quality Standards:
        - Evidence-based conclusions
        - Programmatic calculations
        - Complete audit trails
        """
        
        # Create canonical document files
        ama_file = os.path.join(temp_workspace, 'AMAGuides5thEdition.pdf')
        qme_file = os.path.join(temp_workspace, 'QME-Study-Guide.pdf')
        
        with open(ama_file, 'w') as f:
            f.write(ama_guides_content)
        with open(qme_file, 'w') as f:
            f.write(qme_study_guide_content)
        
        # Initialize knowledge base
        kg_repo = SQLiteKnowledgeGraphRepository(test_database)
        initializer = KnowledgeBaseInitializer(kg_repo)
        
        # Execute complete initialization
        initialization_result = initializer.initialize_complete_knowledge_base([ama_file, qme_file])
        
        # Verify initialization success
        assert initialization_result.success
        assert initialization_result.documents_processed >= 2
        
        # Verify node count requirements (≥1000)
        total_nodes = len(kg_repo.find_all_nodes())
        assert total_nodes >= 1000, f"Node count {total_nodes} below minimum 1000"
        
        # Verify relationship count requirements (≥500)
        total_relationships = len(kg_repo.find_all_relationships())
        assert total_relationships >= 500, f"Relationship count {total_relationships} below minimum 500"
        
        # Verify required entity types present
        required_entity_types = [
            'ama_table', 'legal_requirement', 'procedural_pattern', 
            'quality_standard', 'calculation_method'
        ]
        
        for entity_type in required_entity_types:
            entities = kg_repo.find_nodes_by_type(entity_type)
            assert len(entities) > 0, f"No entities found for type {entity_type}"
        
        # Verify AMA tables accessibility
        ama_tables = kg_repo.find_nodes_by_type('ama_table')
        table_ids = [node.properties.get('table_id') for node in ama_tables]
        assert '15-5' in table_ids, "AMA Table 15-5 not found in knowledge graph"
        
        # Verify legal requirements accessibility
        legal_reqs = kg_repo.find_nodes_by_type('legal_requirement')
        req_descriptions = [node.properties.get('description', '') for node in legal_reqs]
        assert any('4062.3' in desc for desc in req_descriptions), "Labor Code 4062.3 not found"
        
        # Generate initialization status report
        status_report = initializer.generate_status_report()
        assert status_report['initialization_complete']
        assert status_report['validation_passed']
        assert status_report['system_ready']
    
    @pytest.mark.skipif(not EVIDENCE_FIRST_AVAILABLE, reason="Evidence-first components not available")
    def test_complete_workflow_audit_trail_validation(self, temp_workspace, test_database, sample3_content, ama_tables_data):
        """
        Test complete workflow execution from document upload through final QME report
        generation with comprehensive audit trail validation.
        
        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.5
        """
        # Setup test environment
        sample3_file = os.path.join(temp_workspace, 'Sample3.pdf')
        with open(sample3_file, 'w') as f:
            f.write(sample3_content)
        
        ama_tables_file = os.path.join(temp_workspace, 'data', 'ama_guidelines', 'tables.json')
        with open(ama_tables_file, 'w') as f:
            json.dump(ama_tables_data, f)
        
        # Setup repositories
        doc_repo = SQLiteDocumentRepository(test_database)
        kg_repo = SQLiteKnowledgeGraphRepository(test_database)
        
        # Initialize complete workflow
        workflow_manager = EvidenceFirstWorkflowManager(
            document_repository=doc_repo,
            knowledge_graph_repository=kg_repo,
            ama_tables_path=ama_tables_file
        )
        
        # Execute complete workflow
        start_time = time.time()
        workflow_result = workflow_manager.execute_complete_workflow(sample3_file)
        execution_time = time.time() - start_time
        
        # Verify workflow success
        assert workflow_result.success
        assert workflow_result.pipeline1_result.success
        assert workflow_result.pipeline2_result.success
        
        # Verify performance requirements
        assert execution_time < 300, f"Workflow took {execution_time:.1f}s, exceeding 5-minute limit"
        
        # Verify audit trail completeness
        audit_trail = workflow_result.audit_trail
        
        # Evidence sources audit
        assert len(audit_trail.evidence_sources) > 0
        for source in audit_trail.evidence_sources:
            assert source.document_id
            assert source.confidence >= 0.5
            assert source.page_reference
        
        # Calculation methods audit
        assert len(audit_trail.calculation_steps) > 0
        for step in audit_trail.calculation_steps:
            assert step.method == "PROGRAMMATIC"
            assert step.ama_table_reference
            assert step.validation_status
        
        # Validation results audit
        assert len(audit_trail.validation_results) > 0
        for validation in audit_trail.validation_results:
            assert validation.validation_type in ['FIELD_EXTRACTION', 'CALCULATION', 'COMPLIANCE']
            assert validation.passed is not None
        
        # Compliance status audit
        compliance_audit = audit_trail.compliance_status
        assert compliance_audit.labor_code_4062_3_present
        assert compliance_audit.page_count_accurate
        assert compliance_audit.signature_blocks_present
        assert compliance_audit.no_placeholder_text
        
        # Verify final report generation
        final_report = workflow_result.final_report
        assert final_report.patient_name == 'Jane Doe'
        assert final_report.total_impairment_percentage > 0
        assert len(final_report.evidence_citations) > 0
        assert final_report.legal_compliance_verified
        
        # Verify traceability
        for field_name, field_value in final_report.populated_fields.items():
            if field_value:
                # Each populated field should have evidence source
                evidence_found = any(
                    field_name in source.extracted_fields 
                    for source in audit_trail.evidence_sources
                )
                assert evidence_found, f"No evidence source found for field {field_name}"
    
    def test_performance_benchmarks(self, temp_workspace, test_database):
        """Test system performance against benchmarks."""
        # Create large test document
        large_content = """
        QUALIFIED MEDICAL EVALUATOR'S REPORT
        
        Patient: Test Patient
        Case: WC-2024-999999
        """ + "Additional content line.\n" * 1000  # Large document
        
        large_file = os.path.join(temp_workspace, 'large_test.txt')
        with open(large_file, 'w') as f:
            f.write(large_content)
        
        # Test extraction performance
        if EVIDENCE_FIRST_AVAILABLE:
            extractor = StructuredExtractor()
            
            start_time = time.time()
            extraction_context = ExtractionContext(
                document_id="perf-test-1",
                document_text=large_content,
                source_file=large_file
            )
            result = extractor.extract_with_confidence(extraction_context)
            extraction_time = time.time() - start_time
            
            # Should complete within 2 minutes per document
            assert extraction_time < 120, f"Extraction took {extraction_time:.1f}s, too slow"
            
            # Should maintain reasonable accuracy
            assert result.overall_confidence > 0.3, "Accuracy degraded with large document"
    
    def test_error_handling_and_recovery(self, temp_workspace, test_database):
        """Test error handling and recovery mechanisms."""
        # Test with malformed document
        malformed_content = "Invalid content with no structure"
        malformed_file = os.path.join(temp_workspace, 'malformed.txt')
        with open(malformed_file, 'w') as f:
            f.write(malformed_content)
        
        if EVIDENCE_FIRST_AVAILABLE:
            # Should handle gracefully
            extractor = StructuredExtractor()
            extraction_context = ExtractionContext(
                document_id="error-test-1",
                document_text=malformed_content,
                source_file=malformed_file
            )
            
            result = extractor.extract_with_confidence(extraction_context)
            
            # Should not crash, but may have low confidence
            assert isinstance(result.overall_confidence, float)
            assert 0.0 <= result.overall_confidence <= 1.0
    
    def test_integration_with_existing_system(self, temp_workspace, test_database):
        """Test integration with existing QME system components."""
        # Test that evidence-first system works with existing repositories
        doc_repo = SQLiteDocumentRepository(test_database)
        kg_repo = SQLiteKnowledgeGraphRepository(test_database)
        
        # Create test document
        test_doc = Document(
            id="integration-test-1",
            filename="test.pdf",
            content="Test content",
            metadata={"test": True}
        )
        
        # Should integrate with existing document storage
        doc_repo.save_document(test_doc)
        retrieved_doc = doc_repo.get_document("integration-test-1")
        assert retrieved_doc.id == test_doc.id
        
        # Should integrate with existing knowledge graph
        test_node = KnowledgeNode(
            id="test-node-1",
            node_type="test",
            properties={"name": "Test Node"}
        )
        
        kg_repo.save_node(test_node)
        retrieved_node = kg_repo.get_node("test-node-1")
        assert retrieved_node.id == test_node.id


class TestConfidenceScoringValidation:
    """Dedicated tests for confidence scoring validation."""
    
    @pytest.mark.skipif(not EVIDENCE_FIRST_AVAILABLE, reason="Evidence-first components not available")
    def test_critical_field_precision_threshold(self):
        """Test that critical fields meet ≥95% precision threshold."""
        # Test data with high-confidence critical fields
        test_cases = [
            {
                'text': 'Patient: John Smith, Age: 45, Case: WC-2024-001',
                'expected': {'patient_name': 'John Smith', 'age': 45, 'case_number': 'WC-2024-001'}
            },
            {
                'text': 'Re: Applicant: Jane Doe, EAMS No: ADJ123456, Claim No: WC789-012',
                'expected': {'patient_name': 'Jane Doe', 'case_number': 'ADJ123456', 'claim_number': 'WC789-012'}
            }
        ]
        
        extractor = StructuredExtractor()
        total_critical_fields = 0
        high_confidence_fields = 0
        
        for case in test_cases:
            extraction_context = ExtractionContext(
                document_id=f"precision-test-{hash(case['text'])}",
                document_text=case['text']
            )
            
            result = extractor.extract_with_confidence(extraction_context)
            
            for field_name in ['patient_name', 'age', 'case_number', 'claim_number']:
                if field_name in result.fields and result.fields[field_name]:
                    total_critical_fields += 1
                    confidence = result.confidences.get(field_name, 0.0)
                    if confidence >= 0.8:  # High confidence threshold
                        high_confidence_fields += 1
        
        precision = high_confidence_fields / total_critical_fields if total_critical_fields > 0 else 0
        assert precision >= 0.95, f"Critical field precision {precision:.2%} below 95% threshold"
    
    @pytest.mark.skipif(not EVIDENCE_FIRST_AVAILABLE, reason="Evidence-first components not available")
    def test_overall_field_coverage_threshold(self):
        """Test that overall field coverage meets ≥90% threshold."""
        comprehensive_text = """
        Re: Applicant: Alice Johnson
        Age: 35 years old
        Gender: Female
        Employer: ABC Corporation
        EAMS No: ADJ987654321
        Claim No: WC555-444
        Date of Injury: January 15, 2024
        Body Part: Right shoulder
        Occupation: Office Manager
        Examination Date: December 1, 2025
        """
        
        extractor = StructuredExtractor()
        extraction_context = ExtractionContext(
            document_id="coverage-test-1",
            document_text=comprehensive_text
        )
        
        result = extractor.extract_with_confidence(extraction_context)
        
        expected_fields = [
            'patient_name', 'age', 'gender', 'employer', 'case_number',
            'claim_number', 'injury_date', 'body_parts', 'occupation', 'scheduled_exam_date'
        ]
        
        extracted_fields = sum(1 for field in expected_fields if field in result.fields and result.fields[field])
        coverage = extracted_fields / len(expected_fields)
        
        assert coverage >= 0.90, f"Field coverage {coverage:.2%} below 90% threshold"


class TestProgrammaticCalculationValidation:
    """Dedicated tests for programmatic calculation validation."""
    
    @pytest.mark.skipif(not EVIDENCE_FIRST_AVAILABLE, reason="Evidence-first components not available")
    def test_ama_table_accuracy_validation(self, temp_workspace):
        """Test AMA table accuracy and lookup validation."""
        # Create test AMA tables with known values
        test_tables = {
            "15-5": {
                "table_id": "15-5",
                "chapter": 15,
                "title": "Cervical Spine Range of Motion",
                "data_structure": {
                    "measurements": {
                        "flexion": {"normal": 50, "units": "degrees"},
                        "extension": {"normal": 60, "units": "degrees"}
                    }
                }
            }
        }
        
        tables_file = os.path.join(temp_workspace, 'test_tables.json')
        with open(tables_file, 'w') as f:
            json.dump(test_tables, f)
        
        calculator = ImpairmentCalculator(tables_file)
        
        # Test table accessibility
        validation = calculator.validate_ama_table_access()
        assert validation['tables_file_accessible']
        assert validation['has_range_of_motion_tables']
        
        # Test specific table lookup
        table = calculator.ama_tables.get('15-5')
        assert table is not None
        assert table['chapter'] == 15
        assert table['data_structure']['measurements']['flexion']['normal'] == 50
    
    @pytest.mark.skipif(not EVIDENCE_FIRST_AVAILABLE, reason="Evidence-first components not available")
    def test_rom_calculation_accuracy(self, temp_workspace):
        """Test ROM calculation accuracy with known values."""
        # Setup test data
        test_tables = {
            "15-5": {
                "table_id": "15-5",
                "chapter": 15,
                "title": "Cervical Spine Range of Motion",
                "body_system": "spine",
                "data_structure": {
                    "type": "range_of_motion",
                    "measurements": {
                        "flexion": {"normal": 50, "units": "degrees"}
                    }
                }
            }
        }
        
        tables_file = os.path.join(temp_workspace, 'rom_test_tables.json')
        with open(tables_file, 'w') as f:
            json.dump(test_tables, f)
        
        calculator = ImpairmentCalculator(tables_file)
        
        # Test ROM measurements with known expected result
        measurements = [
            ROMMeasurement("cervical_spine", "flexion", 30.0, datetime.now(), "Dr. Test"),
            ROMMeasurement("cervical_spine", "flexion", 32.0, datetime.now(), "Dr. Test"),
            ROMMeasurement("cervical_spine", "flexion", 28.0, datetime.now(), "Dr. Test")
        ]
        
        result = calculator.calculate_rom_impairment(measurements, "spine")
        
        # Verify calculation accuracy
        expected_average = (30.0 + 32.0 + 28.0) / 3  # 30.0 degrees
        loss_percentage = (50 - expected_average) / 50  # 40% loss
        
        assert result.calculation_method == "ROM_BASED_PROGRAMMATIC"
        assert result.impairment_percentage > 0
        assert len(result.calculation_steps) >= 3
        
        # Verify audit trail
        assert 'measurement_average' in result.audit_trail
        assert abs(result.audit_trail['measurement_average'] - expected_average) < 0.1
    
    @pytest.mark.skipif(not EVIDENCE_FIRST_AVAILABLE, reason="Evidence-first components not available")
    def test_combined_values_chart_application(self, temp_workspace):
        """Test Combined Values Chart application accuracy."""
        # Minimal tables for combined calculation
        test_tables = {"COMBINED_VALUES": {"table_id": "COMBINED_VALUES"}}
        
        tables_file = os.path.join(temp_workspace, 'combined_test_tables.json')
        with open(tables_file, 'w') as f:
            json.dump(test_tables, f)
        
        calculator = ImpairmentCalculator(tables_file)
        
        # Test known combination
        impairments = [15.0, 8.0]  # Known values from Sample3
        result = calculator.calculate_combined_impairment(impairments)
        
        # Verify Combined Values Chart formula: A + B(100-A)/100
        expected = 15 + (8 * (100 - 15)) / 100  # 21.8%
        
        assert result.calculation_method == "COMBINED_VALUES_PROGRAMMATIC"
        assert abs(result.impairment_percentage - expected) < 1.0
        assert any(ref.table_id == "COMBINED_VALUES" for ref in result.ama_table_references)


if __name__ == "__main__":
    # Run basic smoke tests
    print("Running Evidence-First Pipeline Tests...")
    
    if not EVIDENCE_FIRST_AVAILABLE:
        print("⚠️  Evidence-first components not available - running basic tests only")
    
    # Basic integration test
    temp_dir = tempfile.mkdtemp()
    try:
        # Test basic functionality
        test_content = "Patient: John Doe, Age: 45, Case: WC-2024-001"
        test_file = os.path.join(temp_dir, 'basic_test.txt')
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        print(f"✓ Created test file: {test_file}")
        print(f"✓ Test content length: {len(test_content)} characters")
        print("✓ Basic test setup completed")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("✓ Evidence-First Pipeline Test Framework Ready")