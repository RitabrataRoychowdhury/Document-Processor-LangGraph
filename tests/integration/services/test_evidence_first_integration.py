"""
Evidence-First QME System Integration Tests.

Comprehensive integration tests for the complete evidence-first workflow
from document upload through final QME report generation with audit trail validation.

Requirements tested: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.4, 5.5
"""

import pytest
import tempfile
import os
import shutil
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch

# Core system imports
from src.repositories.document_repository import SQLiteDocumentRepository
from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
from src.storage.database import DatabaseManager
from src.storage.knowledge_graph_schema import KnowledgeGraphSchemaManager

# Evidence-first system imports
try:
    from src.workflow.evidence_first_workflow_manager import EvidenceFirstWorkflowManager
    from src.core.extraction.structured_extractor import StructuredExtractor, ExtractionContext
    from src.core.validation.qme_field_validator import EvidenceFirstValidator, ValidationReport
    from src.core.calculation.impairment_calculator import ImpairmentCalculator, ROMMeasurement
    from src.infrastructure.knowledge.evidence_rag_service import EvidenceRAGService
    from src.core.generation.intelligent_content_generator import IntelligentContentGenerator
    from tests.template.test_enhanced_professional_template_assembler import ProfessionalTemplateAssembler
    from src.core.validation.qme_rules_engine import QMERulesEngine
    EVIDENCE_FIRST_INTEGRATION_AVAILABLE = True
except ImportError as e:
    EVIDENCE_FIRST_INTEGRATION_AVAILABLE = False
    print(f"Evidence-first integration components not available: {e}")


class TestEvidenceFirstIntegration:
    """Comprehensive integration tests for evidence-first QME system."""
    
    @pytest.fixture
    def integration_workspace(self):
        """Create comprehensive workspace for integration testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create full directory structure
        directories = [
            'data/documents',
            'data/database', 
            'data/ama_guidelines',
            'data/qme_references',
            'canonical_docs',
            'output',
            'logs'
        ]
        
        for directory in directories:
            os.makedirs(os.path.join(temp_dir, directory), exist_ok=True)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def integration_database(self, integration_workspace):
        """Create comprehensive database for integration testing."""
        db_path = os.path.join(integration_workspace, 'data', 'database', 'integration_test.db')
        
        # Initialize database with full schema
        db_manager = DatabaseManager(db_path)
        kg_schema = KnowledgeGraphSchemaManager(db_path)
        kg_schema.create_knowledge_graph_tables()
        
        return db_manager
    
    @pytest.fixture
    def complete_test_data(self, integration_workspace):
        """Create complete test data for integration testing."""
        test_data = {}
        
        # Sample3.pdf content
        test_data['sample3_content'] = """
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
        
        # PQME document content
        test_data['pqme_content'] = """
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
        - Positive McMurray test indicating meniscus tear
        - Negative anterior drawer test
        
        DIAGNOSIS:
        Left knee medial meniscus tear, ICD-10: S83.242A
        
        IMPAIRMENT RATING:
        Based on AMA Guides 5th Edition Table 17-5, the patient's condition
        corresponds to 12% lower extremity impairment, which converts to
        5% whole person impairment (12% × 0.4 = 4.8%, rounded to 5%).
        
        Your examination is scheduled to take place on September 9, 2025.
        """
        
        # Comprehensive AMA tables
        test_data['ama_tables'] = {
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
                "title": "Upper Extremity Shoulder Range of Motion Impairment",
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
                "conversion_factor": 0.6,
                "page_reference": 436
            },
            "17-5": {
                "table_id": "17-5",
                "chapter": 17,
                "title": "Lower Extremity Knee Impairment",
                "body_system": "lower_extremity",
                "method_type": "functional_assessment",
                "data_structure": {
                    "type": "functional_assessment",
                    "conditions": {
                        "meniscus_tear": {"impairment_range": [8, 15], "units": "percent_le"}
                    }
                },
                "conversion_factor": 0.4,
                "page_reference": 523
            },
            "COMBINED_VALUES": {
                "table_id": "COMBINED_VALUES",
                "chapter": 1,
                "title": "Combined Values Chart",
                "formula": "A + B(100-A)/100",
                "page_reference": 10
            }
        }
        
        # QME reference patterns
        test_data['qme_patterns'] = {
            "legal_patterns": {
                "labor_code_4062_3": {
                    "pattern": r"Labor Code 4062\.3|penalty of perjury",
                    "description": "Labor Code 4062.3 declaration requirement",
                    "mandatory": True
                }
            },
            "quality_standards": {
                "no_placeholder_text": {
                    "pattern": r"\[.*\]|TODO|PLACEHOLDER",
                    "description": "No placeholder text allowed",
                    "validation_type": "negative"
                }
            }
        }
        
        # Create test files
        sample3_file = os.path.join(integration_workspace, 'canonical_docs', 'Sample3.pdf')
        with open(sample3_file, 'w') as f:
            f.write(test_data['sample3_content'])
        test_data['sample3_file'] = sample3_file
        
        pqme_file = os.path.join(integration_workspace, 'data', 'documents', 'pqme_test.txt')
        with open(pqme_file, 'w') as f:
            f.write(test_data['pqme_content'])
        test_data['pqme_file'] = pqme_file
        
        ama_tables_file = os.path.join(integration_workspace, 'data', 'ama_guidelines', 'tables.json')
        with open(ama_tables_file, 'w') as f:
            json.dump(test_data['ama_tables'], f)
        test_data['ama_tables_file'] = ama_tables_file
        
        patterns_file = os.path.join(integration_workspace, 'data', 'qme_references', 'patterns.json')
        with open(patterns_file, 'w') as f:
            json.dump(test_data['qme_patterns'], f)
        test_data['patterns_file'] = patterns_file
        
        return test_data
    
    @pytest.mark.skipif(not EVIDENCE_FIRST_INTEGRATION_AVAILABLE, reason="Evidence-first integration not available")
    def test_complete_sample3_workflow_integration(self, integration_workspace, integration_database, complete_test_data):
        """
        Test complete workflow integration using Sample3.pdf from document upload 
        through final QME report generation.
        
        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
        """
        # Setup repositories
        doc_repo = SQLiteDocumentRepository(integration_database)
        kg_repo = SQLiteKnowledgeGraphRepository(integration_database)
        
        # Initialize workflow manager
        workflow_manager = EvidenceFirstWorkflowManager(
            document_repository=doc_repo,
            knowledge_graph_repository=kg_repo,
            ama_tables_path=complete_test_data['ama_tables_file']
        )
        
        # Execute complete workflow
        start_time = time.time()
        workflow_result = workflow_manager.execute_complete_workflow(complete_test_data['sample3_file'])
        execution_time = time.time() - start_time
        
        # Verify workflow success
        assert workflow_result.success, f"Workflow failed: {workflow_result.error_message}"
        assert workflow_result.pipeline1_result.success, "Pipeline 1 failed"
        assert workflow_result.pipeline2_result.success, "Pipeline 2 failed"
        
        # Verify performance (should complete within 5 minutes)
        assert execution_time < 300, f"Workflow took {execution_time:.1f}s, exceeding 5-minute limit"
        
        # Verify Pipeline 1 results (Structured Extraction & Validation)
        pipeline1 = workflow_result.pipeline1_result
        
        # Check field extraction
        assert pipeline1.validation_report.overall_confidence >= 0.8
        accepted_fields = pipeline1.validation_report.accepted_fields
        
        # Verify critical fields extracted
        assert accepted_fields['patient_name'] == 'Jane Doe'
        assert accepted_fields['age'] == 52
        assert accepted_fields['case_number'] == 'WC-2024-005678'
        assert accepted_fields['injury_date'] == 'March 10, 2024'
        
        # Verify evidence provenance
        assert len(pipeline1.evidence_snippets) > 0
        for snippet in pipeline1.evidence_snippets:
            assert snippet.source_document == 'Sample3.pdf'
            assert snippet.confidence >= 0.5
            assert snippet.page_number is not None
        
        # Verify Pipeline 2 results (Evidence-Driven Generation & Compliance)
        pipeline2 = workflow_result.pipeline2_result
        
        # Check programmatic calculations
        assert len(pipeline2.calculation_results) >= 2  # Shoulder + cervical
        
        shoulder_calc = None
        cervical_calc = None
        combined_calc = None
        
        for calc in pipeline2.calculation_results:
            if 'shoulder' in calc.body_system.lower():
                shoulder_calc = calc
            elif 'cervical' in calc.body_system.lower() or 'spine' in calc.body_system.lower():
                cervical_calc = calc
            elif calc.calculation_method == "COMBINED_VALUES_PROGRAMMATIC":
                combined_calc = calc
        
        # Verify shoulder calculation
        assert shoulder_calc is not None, "Shoulder calculation not found"
        assert shoulder_calc.calculation_method == "ROM_BASED_PROGRAMMATIC"
        assert shoulder_calc.impairment_percentage > 0
        assert any(ref.table_id == "16-3" for ref in shoulder_calc.ama_table_references)
        
        # Verify cervical calculation
        assert cervical_calc is not None, "Cervical calculation not found"
        assert cervical_calc.calculation_method == "ROM_BASED_PROGRAMMATIC"
        assert cervical_calc.impairment_percentage > 0
        assert any(ref.table_id == "15-5" for ref in cervical_calc.ama_table_references)
        
        # Verify combined calculation
        assert combined_calc is not None, "Combined calculation not found"
        assert combined_calc.calculation_method == "COMBINED_VALUES_PROGRAMMATIC"
        assert any(ref.table_id == "COMBINED_VALUES" for ref in combined_calc.ama_table_references)
        
        # Verify legal compliance
        compliance = pipeline2.compliance_validation
        assert compliance.overall_compliance >= 0.9
        assert compliance.labor_code_4062_3_present
        assert compliance.no_placeholder_text
        
        # Verify final report generation
        final_report = workflow_result.final_report
        assert final_report.patient_name == 'Jane Doe'
        assert final_report.total_impairment_percentage > 0
        assert len(final_report.evidence_citations) > 0
        assert final_report.legal_compliance_verified
        
        print(f"✓ Complete Sample3 workflow integration passed:")
        print(f"  Execution time: {execution_time:.2f}s")
        print(f"  Pipeline 1 confidence: {pipeline1.validation_report.overall_confidence:.2%}")
        print(f"  Pipeline 2 compliance: {compliance.overall_compliance:.2%}")
        print(f"  Final impairment: {final_report.total_impairment_percentage}%")
    
    @pytest.mark.skipif(not EVIDENCE_FIRST_INTEGRATION_AVAILABLE, reason="Evidence-first integration not available")
    def test_pqme_document_workflow_integration(self, integration_workspace, integration_database, complete_test_data):
        """
        Test workflow integration with PQME document (Nick Diaz Jr. case).
        
        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
        """
        # Setup repositories
        doc_repo = SQLiteDocumentRepository(integration_database)
        kg_repo = SQLiteKnowledgeGraphRepository(integration_database)
        
        # Initialize workflow manager
        workflow_manager = EvidenceFirstWorkflowManager(
            document_repository=doc_repo,
            knowledge_graph_repository=kg_repo,
            ama_tables_path=complete_test_data['ama_tables_file']
        )
        
        # Execute workflow with PQME document
        workflow_result = workflow_manager.execute_complete_workflow(complete_test_data['pqme_file'])
        
        # Verify workflow success
        assert workflow_result.success, f"PQME workflow failed: {workflow_result.error_message}"
        
        # Verify PQME-specific field extraction
        pipeline1 = workflow_result.pipeline1_result
        accepted_fields = pipeline1.validation_report.accepted_fields
        
        # Check Nick Diaz Jr. specific data
        assert accepted_fields['patient_name'] == 'Nick Diaz Jr'
        assert accepted_fields['age'] == 43
        assert accepted_fields['employer'] == 'Costco'
        assert accepted_fields['case_number'] == 'ADJ19802400'
        assert accepted_fields['claim_number'] == 'WC608-H07190'
        assert accepted_fields['occupation'] == 'front-end supervisor'
        assert 'left knee' in accepted_fields['body_parts'].lower()
        assert accepted_fields['injury_date'] == 'July 24, 2024'
        assert accepted_fields['scheduled_exam_date'] == 'September 9, 2025'
        
        # Verify knee-specific calculation
        pipeline2 = workflow_result.pipeline2_result
        knee_calc = None
        
        for calc in pipeline2.calculation_results:
            if 'knee' in calc.body_system.lower() or 'lower' in calc.body_system.lower():
                knee_calc = calc
                break
        
        assert knee_calc is not None, "Knee calculation not found"
        assert knee_calc.calculation_method in ["FUNCTIONAL_ASSESSMENT_PROGRAMMATIC", "ROM_BASED_PROGRAMMATIC"]
        assert any(ref.table_id == "17-5" for ref in knee_calc.ama_table_references)
        
        # Verify expected impairment range (should be around 5% WP)
        expected_range = (4, 6)  # 12% LE * 0.4 = 4.8% WP
        assert expected_range[0] <= knee_calc.impairment_percentage <= expected_range[1], \
            f"Knee impairment {knee_calc.impairment_percentage}% outside expected range {expected_range}"
        
        print(f"✓ PQME document workflow integration passed:")
        print(f"  Patient: {accepted_fields['patient_name']}")
        print(f"  Knee impairment: {knee_calc.impairment_percentage}% WP")
        print(f"  Confidence: {pipeline1.validation_report.overall_confidence:.2%}")
    
    @pytest.mark.skipif(not EVIDENCE_FIRST_INTEGRATION_AVAILABLE, reason="Evidence-first integration not available")
    def test_audit_trail_completeness_validation(self, integration_workspace, integration_database, complete_test_data):
        """
        Test comprehensive audit trail validation for complete traceability.
        
        Requirements: 4.5, 5.5
        """
        # Setup repositories
        doc_repo = SQLiteDocumentRepository(integration_database)
        kg_repo = SQLiteKnowledgeGraphRepository(integration_database)
        
        # Initialize workflow manager
        workflow_manager = EvidenceFirstWorkflowManager(
            document_repository=doc_repo,
            knowledge_graph_repository=kg_repo,
            ama_tables_path=complete_test_data['ama_tables_file']
        )
        
        # Execute workflow
        workflow_result = workflow_manager.execute_complete_workflow(complete_test_data['sample3_file'])
        
        # Verify audit trail exists
        audit_trail = workflow_result.audit_trail
        assert audit_trail is not None, "Audit trail not generated"
        
        # Verify evidence sources audit
        assert len(audit_trail.evidence_sources) > 0, "No evidence sources in audit trail"
        
        for source in audit_trail.evidence_sources:
            assert source.document_id, "Missing document ID in evidence source"
            assert source.field_name, "Missing field name in evidence source"
            assert source.extracted_value, "Missing extracted value in evidence source"
            assert source.confidence >= 0.0, "Invalid confidence in evidence source"
            assert source.extraction_method, "Missing extraction method in evidence source"
            assert source.page_reference, "Missing page reference in evidence source"
            
            # Verify source coordinates if available
            if source.coordinates:
                assert source.coordinates.start_position >= 0, "Invalid start position"
                assert source.coordinates.end_position > source.coordinates.start_position, "Invalid end position"
        
        # Verify calculation methods audit
        assert len(audit_trail.calculation_steps) > 0, "No calculation steps in audit trail"
        
        for step in audit_trail.calculation_steps:
            assert step.step_number > 0, "Invalid step number"
            assert step.calculation_type in ["ROM_CALCULATION", "COMBINED_VALUES", "CONVERSION"], \
                f"Invalid calculation type: {step.calculation_type}"
            assert step.method == "PROGRAMMATIC", f"Non-programmatic method found: {step.method}"
            assert step.ama_table_reference, "Missing AMA table reference"
            assert step.input_values, "Missing input values"
            assert step.result is not None, "Missing calculation result"
            assert step.validation_status, "Missing validation status"
        
        # Verify validation results audit
        assert len(audit_trail.validation_results) > 0, "No validation results in audit trail"
        
        validation_types = set()
        for validation in audit_trail.validation_results:
            assert validation.validation_type in ['FIELD_EXTRACTION', 'CALCULATION', 'COMPLIANCE'], \
                f"Invalid validation type: {validation.validation_type}"
            assert validation.validator_name, "Missing validator name"
            assert validation.passed is not None, "Missing validation result"
            assert validation.confidence >= 0.0, "Invalid validation confidence"
            
            validation_types.add(validation.validation_type)
        
        # Verify all validation types are present
        expected_types = {'FIELD_EXTRACTION', 'CALCULATION', 'COMPLIANCE'}
        assert validation_types >= expected_types, f"Missing validation types: {expected_types - validation_types}"
        
        # Verify compliance status audit
        compliance_audit = audit_trail.compliance_status
        assert compliance_audit.labor_code_4062_3_present is not None, "Missing Labor Code 4062.3 status"
        assert compliance_audit.page_count_accurate is not None, "Missing page count status"
        assert compliance_audit.signature_blocks_present is not None, "Missing signature block status"
        assert compliance_audit.no_placeholder_text is not None, "Missing placeholder text status"
        assert compliance_audit.ama_citations_accurate is not None, "Missing AMA citation status"
        
        # Verify traceability - each populated field should have evidence source
        final_report = workflow_result.final_report
        
        for field_name, field_value in final_report.populated_fields.items():
            if field_value:  # Only check populated fields
                evidence_found = any(
                    source.field_name == field_name 
                    for source in audit_trail.evidence_sources
                )
                assert evidence_found, f"No evidence source found for populated field: {field_name}"
        
        # Verify calculation traceability
        for calc_result in workflow_result.pipeline2_result.calculation_results:
            calc_steps_found = any(
                step.calculation_id == calc_result.calculation_id
                for step in audit_trail.calculation_steps
            )
            assert calc_steps_found, f"No audit trail found for calculation: {calc_result.calculation_id}"
        
        print(f"✓ Audit trail completeness validation passed:")
        print(f"  Evidence sources: {len(audit_trail.evidence_sources)}")
        print(f"  Calculation steps: {len(audit_trail.calculation_steps)}")
        print(f"  Validation results: {len(audit_trail.validation_results)}")
        print(f"  Compliance checks: {len([k for k, v in compliance_audit.__dict__.items() if v is not None])}")
    
    @pytest.mark.skipif(not EVIDENCE_FIRST_INTEGRATION_AVAILABLE, reason="Evidence-first integration not available")
    def test_legal_compliance_validation_integration(self, integration_workspace, integration_database, complete_test_data):
        """
        Test legal compliance validation integration.
        
        Requirements: 5.1, 5.2, 5.4, 5.5
        """
        # Setup repositories
        doc_repo = SQLiteDocumentRepository(integration_database)
        kg_repo = SQLiteKnowledgeGraphRepository(integration_database)
        
        # Initialize workflow manager with compliance validation
        workflow_manager = EvidenceFirstWorkflowManager(
            document_repository=doc_repo,
            knowledge_graph_repository=kg_repo,
            ama_tables_path=complete_test_data['ama_tables_file'],
            compliance_patterns_path=complete_test_data['patterns_file']
        )
        
        # Execute workflow
        workflow_result = workflow_manager.execute_complete_workflow(complete_test_data['sample3_file'])
        
        # Verify compliance validation
        compliance = workflow_result.pipeline2_result.compliance_validation
        
        # Test mandatory sections validation
        assert compliance.mandatory_sections_present, "Mandatory sections validation failed"
        required_sections = [
            'patient_demographics', 'records_reviewed', 'physical_examination',
            'diagnosis', 'impairment_rating', 'recommendations'
        ]
        
        for section in required_sections:
            assert section in compliance.section_completeness, f"Missing section validation: {section}"
            assert compliance.section_completeness[section], f"Section not complete: {section}"
        
        # Test Labor Code 4062.3 declaration
        assert compliance.labor_code_4062_3_present, "Labor Code 4062.3 declaration missing"
        assert compliance.legal_declarations['labor_code_4062_3']['present'], "Labor Code declaration not found"
        assert compliance.legal_declarations['labor_code_4062_3']['text_accurate'], "Labor Code text inaccurate"
        
        # Test page count and billing validation
        assert compliance.page_count_accurate, "Page count validation failed"
        assert compliance.billing_compliance['mlprr_units_calculated'], "MLPRR units not calculated"
        assert compliance.billing_compliance['page_count_matches'], "Page count mismatch"
        
        # Test signature block validation
        assert compliance.signature_blocks_present, "Signature blocks validation failed"
        signature_reqs = compliance.signature_requirements
        assert signature_reqs['physician_signature_present'], "Physician signature missing"
        assert signature_reqs['date_present'], "Signature date missing"
        assert signature_reqs['license_number_present'], "License number missing"
        
        # Test placeholder text validation
        assert compliance.no_placeholder_text, "Placeholder text found in report"
        placeholder_check = compliance.content_validation['placeholder_text_check']
        assert placeholder_check['passed'], "Placeholder text validation failed"
        assert len(placeholder_check['violations']) == 0, f"Placeholder violations: {placeholder_check['violations']}"
        
        # Test programmatic calculation validation
        assert compliance.calculations_programmatic, "Non-programmatic calculations found"
        calc_validation = compliance.calculation_validation
        assert calc_validation['all_calculations_programmatic'], "Some calculations not programmatic"
        assert calc_validation['ama_table_citations_accurate'], "AMA table citations inaccurate"
        assert len(calc_validation['calculation_errors']) == 0, f"Calculation errors: {calc_validation['calculation_errors']}"
        
        # Test overall compliance score
        assert compliance.overall_compliance >= 0.9, f"Overall compliance {compliance.overall_compliance:.2%} below 90%"
        
        # Generate compliance report
        compliance_report = workflow_manager.generate_compliance_report(compliance)
        
        # Verify compliance report structure
        assert "LEGAL COMPLIANCE VALIDATION REPORT" in compliance_report
        assert "PASS/FAIL STATUS" in compliance_report
        assert "REMEDIATION STEPS" in compliance_report
        
        # Verify pass/fail status for each requirement
        assert "Labor Code 4062.3: PASS" in compliance_report
        assert "Page Count Attestation: PASS" in compliance_report
        assert "Signature Blocks: PASS" in compliance_report
        assert "No Placeholder Text: PASS" in compliance_report
        assert "Programmatic Calculations: PASS" in compliance_report
        
        print(f"✓ Legal compliance validation integration passed:")
        print(f"  Overall compliance: {compliance.overall_compliance:.2%}")
        print(f"  Mandatory sections: {sum(compliance.section_completeness.values())}/{len(compliance.section_completeness)}")
        print(f"  Legal declarations: {'✓' if compliance.labor_code_4062_3_present else '✗'}")
        print(f"  Signature blocks: {'✓' if compliance.signature_blocks_present else '✗'}")
    
    def test_integration_performance_benchmarks(self, integration_workspace, integration_database, complete_test_data):
        """Test integration performance benchmarks."""
        if not EVIDENCE_FIRST_INTEGRATION_AVAILABLE:
            pytest.skip("Evidence-first integration not available")
        
        # Create large test document
        large_content = complete_test_data['sample3_content'] + "\n" + "Additional content line.\n" * 1000
        large_file = os.path.join(integration_workspace, 'large_test.txt')
        with open(large_file, 'w') as f:
            f.write(large_content)
        
        # Setup repositories
        doc_repo = SQLiteDocumentRepository(integration_database)
        kg_repo = SQLiteKnowledgeGraphRepository(integration_database)
        
        # Initialize workflow manager
        workflow_manager = EvidenceFirstWorkflowManager(
            document_repository=doc_repo,
            knowledge_graph_repository=kg_repo,
            ama_tables_path=complete_test_data['ama_tables_file']
        )
        
        # Measure performance
        start_time = time.time()
        workflow_result = workflow_manager.execute_complete_workflow(large_file)
        execution_time = time.time() - start_time
        
        # Performance benchmarks
        assert execution_time < 300, f"Large document processing took {execution_time:.1f}s, exceeding 5-minute limit"
        
        # Should maintain accuracy despite size
        if workflow_result.success:
            assert workflow_result.pipeline1_result.validation_report.overall_confidence > 0.5
            assert workflow_result.pipeline2_result.compliance_validation.overall_compliance > 0.7
        
        print(f"Performance benchmark: {execution_time:.2f}s for large document")
    
    def test_integration_error_handling_and_recovery(self, integration_workspace, integration_database, complete_test_data):
        """Test integration error handling and recovery mechanisms."""
        if not EVIDENCE_FIRST_INTEGRATION_AVAILABLE:
            pytest.skip("Evidence-first integration not available")
        
        # Setup repositories
        doc_repo = SQLiteDocumentRepository(integration_database)
        kg_repo = SQLiteKnowledgeGraphRepository(integration_database)
        
        # Test with malformed document
        malformed_content = "Invalid content with no medical structure"
        malformed_file = os.path.join(integration_workspace, 'malformed.txt')
        with open(malformed_file, 'w') as f:
            f.write(malformed_content)
        
        # Initialize workflow manager
        workflow_manager = EvidenceFirstWorkflowManager(
            document_repository=doc_repo,
            knowledge_graph_repository=kg_repo,
            ama_tables_path=complete_test_data['ama_tables_file']
        )
        
        # Should handle gracefully
        workflow_result = workflow_manager.execute_complete_workflow(malformed_file)
        
        # Should not crash but may fail gracefully
        if not workflow_result.success:
            assert workflow_result.error_message, "Should provide error message"
            assert len(workflow_result.processing_errors) > 0, "Should report processing errors"
        
        # Test with missing AMA tables
        workflow_manager_no_tables = EvidenceFirstWorkflowManager(
            document_repository=doc_repo,
            knowledge_graph_repository=kg_repo,
            ama_tables_path="nonexistent_tables.json"
        )
        
        # Should handle missing tables gracefully
        result_no_tables = workflow_manager_no_tables.execute_complete_workflow(complete_test_data['sample3_file'])
        
        # Should fail but not crash
        assert not result_no_tables.success, "Should fail with missing AMA tables"
        assert "AMA tables" in result_no_tables.error_message.lower() or "tables" in result_no_tables.error_message.lower()


if __name__ == "__main__":
    # Run integration tests
    print("Running Evidence-First Integration Tests...")
    
    if not EVIDENCE_FIRST_INTEGRATION_AVAILABLE:
        print("⚠️  Evidence-first integration components not available")
        exit(1)
    
    # Create temporary test environment
    temp_dir = tempfile.mkdtemp()
    try:
        # Setup test database
        db_path = os.path.join(temp_dir, 'integration_test.db')
        db_manager = DatabaseManager(db_path)
        kg_schema = KnowledgeGraphSchemaManager(db_path)
        kg_schema.create_knowledge_graph_tables()
        
        # Create test content
        test_content = """
        Patient: Test Patient
        Age: 45
        Case: WC-2024-001
        Diagnosis: Test condition
        """
        
        test_file = os.path.join(temp_dir, 'integration_test.txt')
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Create minimal AMA tables
        ama_tables = {
            "15-5": {
                "table_id": "15-5",
                "chapter": 15,
                "title": "Test Table",
                "body_system": "spine"
            }
        }
        
        ama_file = os.path.join(temp_dir, 'ama_tables.json')
        with open(ama_file, 'w') as f:
            json.dump(ama_tables, f)
        
        print(f"✓ Test environment created: {temp_dir}")
        print(f"✓ Test file: {test_file}")
        print(f"✓ AMA tables: {ama_file}")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("✓ Evidence-First Integration Tests Ready")