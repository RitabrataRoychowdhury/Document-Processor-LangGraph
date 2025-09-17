"""
Knowledge Graph Initialization Testing.

Tests complete knowledge graph initialization with canonical documents,
entity/relationship count validation, and system readiness confirmation
as required by the evidence-first QME system.

Requirements tested: 3.1, 3.2, 3.3, 3.4, 3.5
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

# Core imports
from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
from src.storage.database import DatabaseManager
from src.storage.knowledge_graph_schema import KnowledgeGraphSchemaManager
from src.models.knowledge_graph import KnowledgeNode, KnowledgeRelationship

# Knowledge base initialization imports
try:
    from src.services.knowledge_base_initializer import KnowledgeBaseInitializer, InitializationResult
    KNOWLEDGE_BASE_INITIALIZER_AVAILABLE = True
except ImportError:
    KNOWLEDGE_BASE_INITIALIZER_AVAILABLE = False
    KnowledgeBaseInitializer = None
    InitializationResult = None

# AMA Guidelines imports
try:
    from src.services.ama_guidelines_engine import AMAGuidelinesEngine
    AMA_GUIDELINES_AVAILABLE = True
except ImportError:
    AMA_GUIDELINES_AVAILABLE = False
    AMAGuidelinesEngine = None


class TestKnowledgeGraphInitialization:
    """Comprehensive knowledge graph initialization testing."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create necessary subdirectories
        os.makedirs(os.path.join(temp_dir, 'data', 'database'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'data', 'ama_guidelines'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'data', 'qme_references'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'canonical_docs'), exist_ok=True)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def test_database(self, temp_workspace):
        """Create test database with knowledge graph schema."""
        db_path = os.path.join(temp_workspace, 'data', 'database', 'test_kg.db')
        
        # Initialize database
        db_manager = DatabaseManager(db_path)
        kg_schema = KnowledgeGraphSchemaManager(db_path)
        kg_schema.create_knowledge_graph_tables()
        
        return db_manager
    
    @pytest.fixture
    def ama_guides_content(self):
        """AMA Guides 5th Edition test content."""
        return """
        AMA Guides to the Evaluation of Permanent Impairment, Fifth Edition
        
        Chapter 15: The Spine
        
        Range of motion impairment evaluation requires careful measurement
        and application of appropriate tables for accurate impairment rating.
        
        Table 15-5: Cervical Spine Range of Motion Impairment
        Normal cervical flexion: 50 degrees
        Normal cervical extension: 60 degrees
        Normal lateral flexion: 45 degrees bilaterally
        Normal rotation: 80 degrees bilaterally
        
        Calculation Method:
        1. Measure range of motion in degrees
        2. Calculate percentage loss from normal
        3. Apply impairment percentage from table
        4. Document all measurements and calculations
        
        Chapter 16: The Upper Extremities
        
        Table 16-3: Shoulder Range of Motion Impairment
        Normal shoulder abduction: 180 degrees
        Normal shoulder forward flexion: 180 degrees
        Normal shoulder external rotation: 90 degrees
        
        Impairment Rating Guidelines:
        - Minimum 3 measurements required per motion
        - Average measurements for calculation
        - Apply Combined Values Chart for multiple impairments
        
        Chapter 17: The Lower Extremities
        
        Table 17-5: Knee Impairment Ratings
        Meniscus tears: 8-15% lower extremity impairment
        Ligament injuries: 5-20% lower extremity impairment
        Conversion to whole person: multiply by 0.4
        
        Combined Values Chart Application:
        Formula: A + B(100-A)/100
        Where A is larger impairment, B is smaller impairment
        """
    
    @pytest.fixture
    def qme_study_guide_content(self):
        """QME Study Guide test content."""
        return """
        QME Study Guide - Legal and Procedural Requirements
        
        Legal Requirements:
        
        Labor Code 4062.3 Declaration:
        "I declare under penalty of perjury that the information contained 
        in this report and its attachments, if any, is true and correct to 
        the best of my knowledge."
        
        Page Count Requirements:
        - Accurate page count attestation required
        - MLPRR billing units calculation based on page count
        - Maximum 2000 pages for comprehensive evaluation
        
        Mandatory Signature Blocks:
        - Physician signature required
        - Date of signature required
        - Medical license number required
        - Board certification information required
        
        Procedural Requirements:
        
        Evidence-Based Conclusions:
        - All conclusions must be supported by medical evidence
        - Source citations required for all medical opinions
        - Objective findings must support subjective complaints
        
        Quality Standards:
        
        Report Completeness:
        - Patient demographics section required
        - Records reviewed section required
        - Physical examination section required
        - Diagnosis section required
        - Impairment rating section required
        - Recommendations section required
        
        Professional Standards:
        - Use of appropriate medical terminology
        - Logical organization and flow
        - Clear and concise language
        - Professional formatting and presentation
        
        Compliance Validation:
        - No placeholder text allowed
        - All calculations must be programmatic
        - AMA table citations must be accurate
        - Complete audit trail required
        """
    
    @pytest.fixture
    def sample3_content(self):
        """Sample3.pdf content for gold standard validation."""
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
        
        PHYSICAL EXAMINATION:
        Right shoulder shows decreased range of motion:
        - Abduction: 90 degrees (normal 180)
        - Forward flexion: 120 degrees (normal 180)
        - External rotation: 30 degrees (normal 90)
        
        Cervical spine examination reveals:
        - Flexion: 30 degrees (normal 50)
        - Extension: 40 degrees (normal 60)
        
        DIAGNOSES:
        1. Right shoulder impingement syndrome, ICD-10: M75.30
        2. Cervical strain, ICD-10: S13.4XXA
        
        IMPAIRMENT RATINGS:
        Right shoulder: 15% upper extremity impairment (AMA Table 16-3)
        Cervical spine: 8% whole person impairment (AMA Table 15-5)
        Combined impairment: 22% whole person impairment (Combined Values Chart)
        """
    
    @pytest.fixture
    def qme_reference_patterns(self):
        """QME reference patterns for knowledge graph population."""
        return {
            "legal_patterns": {
                "labor_code_4062_3": {
                    "pattern": r"Labor Code 4062\.3|penalty of perjury",
                    "description": "Labor Code 4062.3 declaration requirement",
                    "mandatory": True,
                    "category": "legal_compliance"
                },
                "page_count_attestation": {
                    "pattern": r"page count|MLPRR|billing units",
                    "description": "Page count attestation requirement",
                    "mandatory": True,
                    "category": "billing_compliance"
                }
            },
            "procedural_patterns": {
                "evidence_based_conclusions": {
                    "pattern": r"supported by.*evidence|medical evidence",
                    "description": "Evidence-based conclusion requirement",
                    "mandatory": True,
                    "category": "quality_standard"
                },
                "source_citations": {
                    "pattern": r"AMA.*Table|Guides.*Edition",
                    "description": "Source citation requirement",
                    "mandatory": True,
                    "category": "documentation"
                }
            },
            "quality_standards": {
                "no_placeholder_text": {
                    "pattern": r"\[.*\]|TODO|PLACEHOLDER",
                    "description": "No placeholder text allowed",
                    "mandatory": True,
                    "category": "completeness",
                    "validation_type": "negative"
                },
                "programmatic_calculations": {
                    "pattern": r"programmatic|calculated|AMA.*formula",
                    "description": "Programmatic calculation requirement",
                    "mandatory": True,
                    "category": "accuracy"
                }
            }
        }
    
    @pytest.mark.skipif(not KNOWLEDGE_BASE_INITIALIZER_AVAILABLE, reason="Knowledge base initializer not available")
    def test_canonical_document_processing(self, temp_workspace, test_database, ama_guides_content, qme_study_guide_content, sample3_content):
        """
        Test canonical document processing for AMA Guides, QME Study Guide, and Sample3.pdf.
        
        Requirements: 3.1, 3.2
        """
        # Create canonical document files
        ama_file = os.path.join(temp_workspace, 'canonical_docs', 'AMAGuides5thEdition.pdf')
        qme_file = os.path.join(temp_workspace, 'canonical_docs', 'QME-Study-Guide.pdf')
        sample3_file = os.path.join(temp_workspace, 'canonical_docs', 'Sample3.pdf')
        
        with open(ama_file, 'w') as f:
            f.write(ama_guides_content)
        with open(qme_file, 'w') as f:
            f.write(qme_study_guide_content)
        with open(sample3_file, 'w') as f:
            f.write(sample3_content)
        
        # Initialize knowledge graph repository
        kg_repo = SQLiteKnowledgeGraphRepository(test_database)
        
        # Initialize knowledge base
        initializer = KnowledgeBaseInitializer(kg_repo)
        
        # Execute canonical document processing
        canonical_docs = [ama_file, qme_file, sample3_file]
        result = initializer.process_canonical_documents(canonical_docs)
        
        # Verify processing success
        assert result.success, f"Canonical document processing failed: {result.error_message}"
        assert result.documents_processed == 3
        assert len(result.processing_errors) == 0
        
        # Verify AMA Guides processing
        ama_entities = kg_repo.find_nodes_by_type('ama_table')
        assert len(ama_entities) >= 3, f"Expected at least 3 AMA tables, found {len(ama_entities)}"
        
        # Verify specific AMA tables
        table_ids = [node.properties.get('table_id') for node in ama_entities]
        expected_tables = ['15-5', '16-3', '17-5']
        for table_id in expected_tables:
            assert table_id in table_ids, f"AMA Table {table_id} not found in knowledge graph"
        
        # Verify QME Study Guide processing
        legal_reqs = kg_repo.find_nodes_by_type('legal_requirement')
        assert len(legal_reqs) >= 2, f"Expected at least 2 legal requirements, found {len(legal_reqs)}"
        
        # Verify specific legal requirements
        req_descriptions = [node.properties.get('description', '') for node in legal_reqs]
        assert any('4062.3' in desc for desc in req_descriptions), "Labor Code 4062.3 not found"
        assert any('page count' in desc.lower() for desc in req_descriptions), "Page count requirement not found"
        
        # Verify Sample3 processing
        sample_entities = kg_repo.find_nodes_by_type('gold_standard_template')
        assert len(sample_entities) >= 1, "Sample3 gold standard template not found"
        
        print(f"✓ Canonical document processing completed:")
        print(f"  AMA tables: {len(ama_entities)}")
        print(f"  Legal requirements: {len(legal_reqs)}")
        print(f"  Gold standard templates: {len(sample_entities)}")
    
    @pytest.mark.skipif(not KNOWLEDGE_BASE_INITIALIZER_AVAILABLE, reason="Knowledge base initializer not available")
    def test_entity_relationship_count_validation(self, temp_workspace, test_database, ama_guides_content, qme_study_guide_content, qme_reference_patterns):
        """
        Test entity and relationship count validation (≥1000 nodes, ≥500 relationships).
        
        Requirements: 3.2, 3.3
        """
        # Setup test files
        ama_file = os.path.join(temp_workspace, 'canonical_docs', 'AMAGuides5thEdition.pdf')
        qme_file = os.path.join(temp_workspace, 'canonical_docs', 'QME-Study-Guide.pdf')
        patterns_file = os.path.join(temp_workspace, 'data', 'qme_references', 'all_patterns.json')
        
        with open(ama_file, 'w') as f:
            f.write(ama_guides_content)
        with open(qme_file, 'w') as f:
            f.write(qme_study_guide_content)
        with open(patterns_file, 'w') as f:
            json.dump(qme_reference_patterns, f)
        
        # Initialize knowledge graph
        kg_repo = SQLiteKnowledgeGraphRepository(test_database)
        initializer = KnowledgeBaseInitializer(kg_repo)
        
        # Execute complete initialization with entity generation
        result = initializer.initialize_complete_knowledge_base([ama_file, qme_file], patterns_file)
        
        # Verify initialization success
        assert result.success, f"Knowledge base initialization failed: {result.error_message}"
        
        # Count all nodes
        all_nodes = kg_repo.find_all_nodes()
        total_node_count = len(all_nodes)
        
        print(f"Total nodes created: {total_node_count}")
        
        # Verify minimum node count (≥1000)
        assert total_node_count >= 1000, f"Node count {total_node_count} below minimum 1000"
        
        # Count all relationships
        all_relationships = kg_repo.find_all_relationships()
        total_relationship_count = len(all_relationships)
        
        print(f"Total relationships created: {total_relationship_count}")
        
        # Verify minimum relationship count (≥500)
        assert total_relationship_count >= 500, f"Relationship count {total_relationship_count} below minimum 500"
        
        # Verify entity type distribution
        entity_type_counts = {}
        for node in all_nodes:
            node_type = node.node_type
            entity_type_counts[node_type] = entity_type_counts.get(node_type, 0) + 1
        
        print("Entity type distribution:")
        for entity_type, count in entity_type_counts.items():
            print(f"  {entity_type}: {count}")
        
        # Verify required entity types are present
        required_types = [
            'ama_table', 'legal_requirement', 'procedural_pattern',
            'quality_standard', 'calculation_method'
        ]
        
        for required_type in required_types:
            assert required_type in entity_type_counts, f"Required entity type {required_type} not found"
            assert entity_type_counts[required_type] > 0, f"No entities of type {required_type}"
        
        # Verify relationship type distribution
        relationship_type_counts = {}
        for rel in all_relationships:
            rel_type = rel.relationship_type
            relationship_type_counts[rel_type] = relationship_type_counts.get(rel_type, 0) + 1
        
        print("Relationship type distribution:")
        for rel_type, count in relationship_type_counts.items():
            print(f"  {rel_type}: {count}")
    
    @pytest.mark.skipif(not KNOWLEDGE_BASE_INITIALIZER_AVAILABLE, reason="Knowledge base initializer not available")
    def test_ama_table_accessibility_validation(self, temp_workspace, test_database, ama_guides_content):
        """
        Test AMA table accessibility for programmatic calculations.
        
        Requirements: 3.4, 3.5
        """
        # Setup AMA Guides file
        ama_file = os.path.join(temp_workspace, 'canonical_docs', 'AMAGuides5thEdition.pdf')
        with open(ama_file, 'w') as f:
            f.write(ama_guides_content)
        
        # Initialize knowledge graph
        kg_repo = SQLiteKnowledgeGraphRepository(test_database)
        initializer = KnowledgeBaseInitializer(kg_repo)
        
        # Process AMA Guides
        result = initializer.process_canonical_documents([ama_file])
        assert result.success
        
        # Test AMA table accessibility
        ama_tables = kg_repo.find_nodes_by_type('ama_table')
        
        # Verify specific tables are accessible
        table_15_5 = None
        table_16_3 = None
        table_17_5 = None
        
        for table in ama_tables:
            table_id = table.properties.get('table_id')
            if table_id == '15-5':
                table_15_5 = table
            elif table_id == '16-3':
                table_16_3 = table
            elif table_id == '17-5':
                table_17_5 = table
        
        # Verify Table 15-5 (Cervical Spine)
        assert table_15_5 is not None, "AMA Table 15-5 not accessible"
        assert table_15_5.properties.get('chapter') == 15
        assert 'cervical' in table_15_5.properties.get('title', '').lower()
        assert 'normal_flexion' in table_15_5.properties or 'flexion' in str(table_15_5.properties)
        
        # Verify Table 16-3 (Upper Extremity)
        assert table_16_3 is not None, "AMA Table 16-3 not accessible"
        assert table_16_3.properties.get('chapter') == 16
        assert 'shoulder' in table_16_3.properties.get('title', '').lower() or 'upper' in table_16_3.properties.get('title', '').lower()
        
        # Verify Table 17-5 (Lower Extremity)
        assert table_17_5 is not None, "AMA Table 17-5 not accessible"
        assert table_17_5.properties.get('chapter') == 17
        assert 'knee' in table_17_5.properties.get('title', '').lower() or 'lower' in table_17_5.properties.get('title', '').lower()
        
        # Test calculation method accessibility
        calc_methods = kg_repo.find_nodes_by_type('calculation_method')
        assert len(calc_methods) > 0, "No calculation methods found"
        
        # Verify Combined Values Chart accessibility
        combined_values_chart = None
        for method in calc_methods:
            if 'combined' in method.properties.get('name', '').lower():
                combined_values_chart = method
                break
        
        assert combined_values_chart is not None, "Combined Values Chart not accessible"
        assert 'formula' in combined_values_chart.properties, "Combined Values Chart formula not found"
        
        print(f"✓ AMA table accessibility validated:")
        print(f"  Total AMA tables: {len(ama_tables)}")
        print(f"  Calculation methods: {len(calc_methods)}")
        print(f"  Combined Values Chart: {'✓' if combined_values_chart else '✗'}")
    
    @pytest.mark.skipif(not KNOWLEDGE_BASE_INITIALIZER_AVAILABLE, reason="Knowledge base initializer not available")
    def test_legal_compliance_template_accessibility(self, temp_workspace, test_database, qme_study_guide_content):
        """
        Test legal compliance template accessibility.
        
        Requirements: 3.4, 3.5
        """
        # Setup QME Study Guide file
        qme_file = os.path.join(temp_workspace, 'canonical_docs', 'QME-Study-Guide.pdf')
        with open(qme_file, 'w') as f:
            f.write(qme_study_guide_content)
        
        # Initialize knowledge graph
        kg_repo = SQLiteKnowledgeGraphRepository(test_database)
        initializer = KnowledgeBaseInitializer(kg_repo)
        
        # Process QME Study Guide
        result = initializer.process_canonical_documents([qme_file])
        assert result.success
        
        # Test legal requirement accessibility
        legal_reqs = kg_repo.find_nodes_by_type('legal_requirement')
        assert len(legal_reqs) > 0, "No legal requirements found"
        
        # Verify Labor Code 4062.3 accessibility
        labor_code_4062_3 = None
        for req in legal_reqs:
            if '4062.3' in req.properties.get('description', ''):
                labor_code_4062_3 = req
                break
        
        assert labor_code_4062_3 is not None, "Labor Code 4062.3 not accessible"
        assert 'penalty of perjury' in labor_code_4062_3.properties.get('template_text', '').lower()
        
        # Verify page count requirement accessibility
        page_count_req = None
        for req in legal_reqs:
            if 'page count' in req.properties.get('description', '').lower():
                page_count_req = req
                break
        
        assert page_count_req is not None, "Page count requirement not accessible"
        
        # Test quality standard accessibility
        quality_standards = kg_repo.find_nodes_by_type('quality_standard')
        assert len(quality_standards) > 0, "No quality standards found"
        
        # Verify evidence-based conclusion standard
        evidence_standard = None
        for standard in quality_standards:
            if 'evidence' in standard.properties.get('description', '').lower():
                evidence_standard = standard
                break
        
        assert evidence_standard is not None, "Evidence-based conclusion standard not accessible"
        
        # Test procedural pattern accessibility
        procedural_patterns = kg_repo.find_nodes_by_type('procedural_pattern')
        assert len(procedural_patterns) > 0, "No procedural patterns found"
        
        print(f"✓ Legal compliance template accessibility validated:")
        print(f"  Legal requirements: {len(legal_reqs)}")
        print(f"  Quality standards: {len(quality_standards)}")
        print(f"  Procedural patterns: {len(procedural_patterns)}")
    
    @pytest.mark.skipif(not KNOWLEDGE_BASE_INITIALIZER_AVAILABLE, reason="Knowledge base initializer not available")
    def test_initialization_status_reporting(self, temp_workspace, test_database, ama_guides_content, qme_study_guide_content):
        """
        Test initialization status reporting and system readiness confirmation.
        
        Requirements: 3.5
        """
        # Setup test files
        ama_file = os.path.join(temp_workspace, 'canonical_docs', 'AMAGuides5thEdition.pdf')
        qme_file = os.path.join(temp_workspace, 'canonical_docs', 'QME-Study-Guide.pdf')
        
        with open(ama_file, 'w') as f:
            f.write(ama_guides_content)
        with open(qme_file, 'w') as f:
            f.write(qme_study_guide_content)
        
        # Initialize knowledge graph
        kg_repo = SQLiteKnowledgeGraphRepository(test_database)
        initializer = KnowledgeBaseInitializer(kg_repo)
        
        # Execute complete initialization
        result = initializer.initialize_complete_knowledge_base([ama_file, qme_file])
        
        # Generate status report
        status_report = initializer.generate_status_report()
        
        # Verify status report structure
        assert isinstance(status_report, dict), "Status report should be a dictionary"
        
        # Verify required status fields
        required_fields = [
            'initialization_complete',
            'validation_passed',
            'system_ready',
            'documents_processed',
            'entity_counts',
            'relationship_counts',
            'validation_results'
        ]
        
        for field in required_fields:
            assert field in status_report, f"Missing required status field: {field}"
        
        # Verify initialization completion
        assert status_report['initialization_complete'], "Initialization not marked as complete"
        assert status_report['validation_passed'], "Validation not passed"
        assert status_report['system_ready'], "System not marked as ready"
        
        # Verify document processing counts
        assert status_report['documents_processed'] >= 2, "Insufficient documents processed"
        
        # Verify entity counts
        entity_counts = status_report['entity_counts']
        assert isinstance(entity_counts, dict), "Entity counts should be a dictionary"
        assert sum(entity_counts.values()) >= 1000, "Total entity count below minimum"
        
        # Verify relationship counts
        relationship_counts = status_report['relationship_counts']
        assert isinstance(relationship_counts, dict), "Relationship counts should be a dictionary"
        assert sum(relationship_counts.values()) >= 500, "Total relationship count below minimum"
        
        # Verify validation results
        validation_results = status_report['validation_results']
        assert isinstance(validation_results, dict), "Validation results should be a dictionary"
        
        # Check specific validation results
        assert validation_results.get('ama_tables_accessible', False), "AMA tables not accessible"
        assert validation_results.get('legal_requirements_loaded', False), "Legal requirements not loaded"
        assert validation_results.get('calculation_methods_available', False), "Calculation methods not available"
        
        # Print status report for verification
        print("\n=== Knowledge Graph Initialization Status Report ===")
        print(f"Initialization Complete: {status_report['initialization_complete']}")
        print(f"Validation Passed: {status_report['validation_passed']}")
        print(f"System Ready: {status_report['system_ready']}")
        print(f"Documents Processed: {status_report['documents_processed']}")
        print(f"Total Entities: {sum(entity_counts.values())}")
        print(f"Total Relationships: {sum(relationship_counts.values())}")
        print("Entity Distribution:")
        for entity_type, count in entity_counts.items():
            print(f"  {entity_type}: {count}")
        print("Validation Results:")
        for validation, passed in validation_results.items():
            print(f"  {validation}: {'✓' if passed else '✗'}")
    
    def test_initialization_performance(self, temp_workspace, test_database):
        """Test knowledge graph initialization performance."""
        # Create large test content
        large_ama_content = """
        AMA Guides to the Evaluation of Permanent Impairment, Fifth Edition
        
        Chapter 15: The Spine
        """ + "\nAdditional content line for performance testing." * 100
        
        large_qme_content = """
        QME Study Guide - Legal and Procedural Requirements
        """ + "\nAdditional legal requirement for performance testing." * 100
        
        # Setup test files
        ama_file = os.path.join(temp_workspace, 'canonical_docs', 'LargeAMAGuides.pdf')
        qme_file = os.path.join(temp_workspace, 'canonical_docs', 'LargeQMEGuide.pdf')
        
        with open(ama_file, 'w') as f:
            f.write(large_ama_content)
        with open(qme_file, 'w') as f:
            f.write(large_qme_content)
        
        if KNOWLEDGE_BASE_INITIALIZER_AVAILABLE:
            # Initialize knowledge graph
            kg_repo = SQLiteKnowledgeGraphRepository(test_database)
            initializer = KnowledgeBaseInitializer(kg_repo)
            
            # Measure initialization time
            start_time = time.time()
            result = initializer.initialize_complete_knowledge_base([ama_file, qme_file])
            initialization_time = time.time() - start_time
            
            # Should complete within reasonable time (5 minutes for large documents)
            assert initialization_time < 300, f"Initialization took {initialization_time:.1f}s, too slow"
            
            # Should still be successful
            assert result.success, "Initialization failed with large documents"
            
            print(f"Performance test: {initialization_time:.2f}s for large document initialization")
    
    def test_initialization_error_handling(self, temp_workspace, test_database):
        """Test error handling during knowledge graph initialization."""
        # Test with missing files
        missing_file = os.path.join(temp_workspace, 'nonexistent.pdf')
        
        if KNOWLEDGE_BASE_INITIALIZER_AVAILABLE:
            kg_repo = SQLiteKnowledgeGraphRepository(test_database)
            initializer = KnowledgeBaseInitializer(kg_repo)
            
            # Should handle missing files gracefully
            result = initializer.initialize_complete_knowledge_base([missing_file])
            
            # Should not crash but should report failure
            assert not result.success, "Should fail with missing files"
            assert len(result.processing_errors) > 0, "Should report processing errors"
            
            # Test with malformed content
            malformed_file = os.path.join(temp_workspace, 'malformed.pdf')
            with open(malformed_file, 'w') as f:
                f.write("Invalid content with no structure")
            
            result = initializer.initialize_complete_knowledge_base([malformed_file])
            
            # Should handle gracefully (may succeed with low entity count)
            if not result.success:
                assert len(result.processing_errors) > 0, "Should report processing errors"


if __name__ == "__main__":
    # Run knowledge graph initialization tests
    print("Running Knowledge Graph Initialization Tests...")
    
    if not KNOWLEDGE_BASE_INITIALIZER_AVAILABLE:
        print("⚠️  Knowledge base initializer not available")
        exit(1)
    
    # Create temporary test environment
    temp_dir = tempfile.mkdtemp()
    try:
        # Setup test database
        db_path = os.path.join(temp_dir, 'test_kg.db')
        db_manager = DatabaseManager(db_path)
        kg_schema = KnowledgeGraphSchemaManager(db_path)
        kg_schema.create_knowledge_graph_tables()
        
        # Initialize knowledge graph repository
        kg_repo = SQLiteKnowledgeGraphRepository(db_manager)
        
        # Test basic initialization
        initializer = KnowledgeBaseInitializer(kg_repo)
        
        # Create test content
        test_content = """
        AMA Guides Test Content
        Table 15-5: Test table
        Legal Requirement: Test requirement
        """
        
        test_file = os.path.join(temp_dir, 'test.pdf')
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Test initialization
        result = initializer.process_canonical_documents([test_file])
        
        print(f"✓ Basic initialization test: success={result.success}")
        print(f"✓ Documents processed: {result.documents_processed}")
        
        # Test status reporting
        status_report = initializer.generate_status_report()
        print(f"✓ Status report generated: {len(status_report)} fields")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("✓ Knowledge Graph Initialization Tests Ready")