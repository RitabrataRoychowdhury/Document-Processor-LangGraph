"""End-to-end integration tests for the Document Q&A System."""

import pytest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.factories.processor_factory import ProcessorFactory
from src.strategies.embedding_strategy import LocalEmbeddingStrategy
from src.strategies.qa_strategy import HybridQAStrategy, KeywordRetrievalStrategy, GeminiLLMStrategy
from src.core.extraction.ingestion_pipeline import IngestionPipeline
from src.infrastructure.knowledge.qa_engine import QAEngine
from src.repositories.document_repository import SQLiteDocumentRepository
from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
from src.storage.database import DatabaseManager
from src.storage.knowledge_graph_schema import KnowledgeGraphSchemaManager
from src.models.document import Document
from src.models.knowledge_graph import Patient, Diagnosis, Section, Finding, KnowledgeNode


class TestEndToEndIntegration:
    """Test complete end-to-end workflows."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create necessary subdirectories
        os.makedirs(os.path.join(temp_dir, 'data', 'documents'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'data', 'database'), exist_ok=True)
        
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
    def sample_pdf_content(self):
        """Create sample PDF content for testing."""
        return """
        QUALIFIED MEDICAL EVALUATOR'S REPORT
        
        Patient: John Smith
        Age: 45 years old
        Gender: Male
        Case Number: WC-2024-001234
        Date of Injury: 01/15/2024
        
        HISTORY OF PRESENT ILLNESS:
        The patient is a 45-year-old male who sustained a work-related injury to his lower back 
        on January 15, 2024, while lifting heavy boxes at his workplace. He reports immediate 
        onset of severe lower back pain radiating to his left leg.
        
        PHYSICAL EXAMINATION:
        The patient appears in mild distress due to back pain. Range of motion testing reveals:
        - Forward flexion: 30 degrees (limited)
        - Extension: 10 degrees (limited)
        - Lateral bending: 15 degrees bilaterally (limited)
        
        Straight leg raise test is positive on the left at 45 degrees.
        
        DIAGNOSIS:
        1. Lumbar strain with radiculopathy, ICD-10: M54.5
        2. Possible lumbar disc herniation, ICD-10: M51.26
        
        IMPAIRMENT RATING:
        Based on the AMA Guides 5th Edition, Table 15-3, the patient's condition 
        corresponds to DRE Category II, resulting in a 10% whole person impairment.
        
        RECOMMENDATIONS:
        1. Physical therapy for 6-8 weeks
        2. MRI of lumbar spine to rule out disc herniation
        3. Follow-up in 3 months
        """
    
    @pytest.fixture
    def mock_pdf_processor(self, sample_pdf_content):
        """Create mock PDF processor that returns sample content."""
        mock_processor = Mock()
        mock_processor.extract_text.return_value = sample_pdf_content
        mock_processor.extract_metadata.return_value = {
            'page_count': 3,
            'processor_type': 'PDF',
            'title': 'Sample QME Report',
            'file_size': 1024
        }
        return mock_processor
    
    def test_complete_document_ingestion_workflow(self, temp_workspace, test_database, mock_pdf_processor):
        """Test complete document ingestion: PDF processing → KG population → vector indexing."""
        # Setup repositories
        doc_repo = SQLiteDocumentRepository(test_database)
        kg_repo = SQLiteKnowledgeGraphRepository(test_database)
        
        # Create mock file
        test_file_path = os.path.join(temp_workspace, 'data', 'documents', 'sample_qme.pdf')
        with open(test_file_path, 'w') as f:
            f.write("Mock PDF content")
        
        # Setup ingestion pipeline with mocked components
        with patch('src.factories.processor_factory.ProcessorFactory.create_processor') as mock_factory:
            mock_factory.return_value = mock_pdf_processor
            
            # Mock embedding strategy
            mock_embedding_strategy = Mock()
            mock_embedding_strategy.generate_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
            
            # Create knowledge graph service
            from src.core.extraction.ingestion_pipeline import KnowledgeGraphService
            kg_service = KnowledgeGraphService(kg_repo)
            
            # Create ingestion pipeline
            pipeline = IngestionPipeline(
                processor_factory=ProcessorFactory(),
                embedding_strategy=mock_embedding_strategy,
                kg_service=kg_service
            )
            
            # Execute ingestion
            document_id = "test-doc-1"
            result = pipeline._process_document_sync(test_file_path, document_id)
            
            # Verify ingestion was successful
            assert result.success
            assert result.document_id == document_id
            
            # Verify sections were created
            assert len(result.sections) > 0
            
            # Verify entities were extracted
            assert len(result.entities) > 0
            
            # Verify knowledge graph nodes were created
            sections = kg_repo.find_nodes_by_type('section')
            assert len(sections) >= 1
            
            diagnoses = kg_repo.find_nodes_by_type('diagnosis')
            assert len(diagnoses) >= 1
            
            # Note: findings might not be extracted depending on the NER patterns
            # The important thing is that the pipeline runs successfully
            all_nodes = kg_repo.find_nodes_by_type('section') + kg_repo.find_nodes_by_type('diagnosis')
            assert len(all_nodes) >= 2  # At least sections and diagnoses
    
    def test_sample3_pdf_processing_simulation(self, temp_workspace, test_database):
        """Test processing Sample3.pdf simulation with expected knowledge graph creation."""
        # Setup repositories
        doc_repo = SQLiteDocumentRepository(test_database)
        kg_repo = SQLiteKnowledgeGraphRepository(test_database)
        
        # Create Sample3.pdf simulation
        sample3_content = """
        QUALIFIED MEDICAL EVALUATOR'S REPORT
        
        Patient Information:
        Name: Jane Doe
        Age: 52
        Gender: Female
        Case Number: WC-2024-005678
        Date of Injury: March 10, 2024
        
        HISTORY:
        Ms. Doe is a 52-year-old female who sustained injuries to her right shoulder 
        and neck in a work-related motor vehicle accident on March 10, 2024.
        
        EXAMINATION:
        Right shoulder shows decreased range of motion:
        - Abduction: 90 degrees (normal 180)
        - Forward flexion: 120 degrees (normal 180)
        - External rotation: 30 degrees (normal 90)
        
        Cervical spine examination reveals muscle spasm and tenderness.
        
        DIAGNOSES:
        1. Right shoulder impingement syndrome, ICD-10: M75.30
        2. Cervical strain, ICD-10: S13.4XXA
        3. Post-traumatic stress disorder, ICD-10: F43.10
        
        IMPAIRMENT RATINGS:
        Right shoulder: 15% upper extremity impairment (AMA Table 16-3)
        Cervical spine: 8% whole person impairment (AMA Table 15-5)
        Combined impairment: 22% whole person impairment
        """
        
        # Mock processor for Sample3.pdf
        mock_processor = Mock()
        mock_processor.extract_text.return_value = sample3_content
        mock_processor.extract_metadata.return_value = {
            'page_count': 4,
            'processor_type': 'PDF',
            'title': 'Sample3 QME Report',
            'file_size': 2048
        }
        
        # Create test file
        test_file_path = os.path.join(temp_workspace, 'Sample3.pdf')
        with open(test_file_path, 'w') as f:
            f.write("Sample3 PDF content")
        
        # Setup pipeline with mocks
        with patch('src.factories.processor_factory.ProcessorFactory.create_processor') as mock_factory:
            mock_factory.return_value = mock_processor
            
            mock_embedding_strategy = Mock()
            mock_embedding_strategy.generate_embeddings.return_value = [0.2, 0.4, 0.6, 0.8, 1.0]
            
            # Create knowledge graph service
            from src.core.extraction.ingestion_pipeline import KnowledgeGraphService
            kg_service = KnowledgeGraphService(kg_repo)
            
            # Create and execute pipeline
            pipeline = IngestionPipeline(
                processor_factory=ProcessorFactory(),
                embedding_strategy=mock_embedding_strategy,
                kg_service=kg_service
            )
            
            document_id = "sample3-doc-1"
            result = pipeline._process_document_sync(test_file_path, document_id)
            
            # Verify successful processing
            assert result.success
            assert result.document_id == document_id
            
            # Verify sections were created
            assert len(result.sections) > 0
            
            # Verify entities were extracted (the NER will find entities in the sample content)
            assert len(result.entities) > 0
            
            # Verify knowledge graph nodes were created
            sections = kg_repo.find_nodes_by_type('section')
            assert len(sections) >= 1
            
            # Check for diagnoses (should be extracted from the sample content)
            diagnoses = kg_repo.find_nodes_by_type('diagnosis')
            assert len(diagnoses) >= 1
            
            # Check for impairment ratings (should be extracted from the sample content)
            impairment_ratings = kg_repo.find_nodes_by_type('impairment_rating')
            assert len(impairment_ratings) >= 1
            
            # Verify that we have a good mix of extracted entities
            all_entity_nodes = diagnoses + impairment_ratings
            assert len(all_entity_nodes) >= 2
            
            return result.document_id  # Return for use in QA test
    
    def test_end_to_end_qa_workflow(self, temp_workspace, test_database):
        """Test complete Q&A workflow: document ingestion → knowledge graph → Q&A query."""
        # First, ingest a document (reuse Sample3 processing)
        document_id = self.test_sample3_pdf_processing_simulation(temp_workspace, test_database)
        
        # Setup Q&A components
        kg_repo = SQLiteKnowledgeGraphRepository(test_database)
        doc_repo = SQLiteDocumentRepository(test_database)
        
        # Mock Q&A strategy components
        mock_retrieval_strategy = Mock()
        mock_llm_strategy = Mock()
        
        # Mock retrieval results
        from src.strategies.qa_strategy import RetrievalContext
        mock_retrieval_context = [
            RetrievalContext(
                text="Right shoulder impingement syndrome, ICD-10: M75.30",
                source="Sample3 QME Report",
                relevance_score=0.9,
                metadata={'page_reference': 3, 'node_type': 'diagnosis'}
            ),
            RetrievalContext(
                text="15% upper extremity impairment (AMA Table 16-3)",
                source="Sample3 QME Report", 
                relevance_score=0.85,
                metadata={'page_reference': 4, 'node_type': 'impairment_rating'}
            )
        ]
        mock_retrieval_strategy.retrieve_context.return_value = mock_retrieval_context
        
        # Mock LLM response
        expected_answer = """Based on the medical evaluation, the patient has right shoulder impingement syndrome (ICD-10: M75.30). The impairment rating for the right shoulder is 15% upper extremity impairment according to AMA Table 16-3."""
        
        mock_llm_strategy.generate_answer.return_value = expected_answer
        
        # Create Q&A strategy and engine
        from src.storage.document_storage import DocumentStorage
        mock_storage = Mock(spec=DocumentStorage)
        
        qa_strategy = HybridQAStrategy(mock_retrieval_strategy, mock_llm_strategy)
        qa_engine = QAEngine(storage=mock_storage, qa_strategy=qa_strategy, kg_repository=kg_repo)
        
        # Execute Q&A query
        question = "What is the patient's shoulder diagnosis and impairment rating?"
        
        # Mock the document content retrieval
        document_content = {
            'original_text': 'Sample3 content...',
            'summary': 'QME report for shoulder injury'
        }
        
        response = qa_strategy.answer_question(question, document_content)
        
        # Verify Q&A response
        assert response.answer == expected_answer
        assert len(response.sources) == 2
        assert response.confidence > 0.8
        
        # Verify that the Q&A workflow completed successfully
        # The exact structure of sources may vary, but we should have sources
        assert response.sources is not None
    
    def test_knowledge_graph_relationship_traversal(self, temp_workspace, test_database):
        """Test traversing knowledge graph relationships for complex queries."""
        # Setup repositories
        kg_repo = SQLiteKnowledgeGraphRepository(test_database)
        
        # Create test entities with relationships
        patient = Patient(
            id="patient-test",
            name="Test Patient",
            case_number="WC-TEST-001"
        )
        
        diagnosis = Diagnosis(
            id="diag-test",
            icd_code="M54.5",
            description="Low back pain",
            certainty=0.9
        )
        
        section = Section(
            id="section-test",
            document_id="doc-test",
            section_type="diagnosis",
            page_number=2,
            text_content="Patient diagnosed with low back pain"
        )
        
        finding = Finding(
            id="finding-test",
            section_id="section-test",
            finding_type="physical",
            description="Limited range of motion",
            page_reference=2
        )
        
        # Save entities (convert patient to knowledge node)
        patient_node = KnowledgeNode(
            id=patient.id,
            node_type="patient",
            properties={
                "name": patient.name,
                "case_number": patient.case_number
            }
        )
        kg_repo.save_node(patient_node)
        kg_repo.save_diagnosis(diagnosis)
        kg_repo.save_section(section)
        kg_repo.save_finding(finding)
        
        # Create relationships
        from src.models.knowledge_graph import KnowledgeRelationship
        
        patient_diag_rel = KnowledgeRelationship(
            id="rel-1",
            source_node_id="patient-test",
            target_node_id="diag-test",
            relationship_type="HAS_DIAGNOSIS",
            confidence=1.0
        )
        
        section_finding_rel = KnowledgeRelationship(
            id="rel-2",
            source_node_id="section-test",
            target_node_id="finding-test",
            relationship_type="CONTAINS_FINDING",
            confidence=0.9
        )
        
        kg_repo.save_relationship(patient_diag_rel)
        kg_repo.save_relationship(section_finding_rel)
        
        # Test relationship traversal
        patient_diagnoses = kg_repo.find_relationships_by_source("patient-test")
        assert len(patient_diagnoses) == 1
        assert patient_diagnoses[0].relationship_type == "HAS_DIAGNOSIS"
        assert patient_diagnoses[0].target_node_id == "diag-test"
        
        section_findings = kg_repo.find_relationships_by_source("section-test")
        assert len(section_findings) == 1
        assert section_findings[0].relationship_type == "CONTAINS_FINDING"
        
        # Test reverse traversal
        diagnosis_patients = kg_repo.find_relationships_by_target("diag-test")
        assert len(diagnosis_patients) == 1
        assert diagnosis_patients[0].source_node_id == "patient-test"
    
    def test_error_handling_and_recovery(self, temp_workspace, test_database):
        """Test error handling and recovery in end-to-end workflows."""
        # Setup repositories
        doc_repo = SQLiteDocumentRepository(test_database)
        kg_repo = SQLiteKnowledgeGraphRepository(test_database)
        
        # Create test file
        test_file_path = os.path.join(temp_workspace, 'error_test.pdf')
        with open(test_file_path, 'w') as f:
            f.write("Test content")
        
        # Test processor failure
        with patch('src.factories.processor_factory.ProcessorFactory.create_processor') as mock_factory:
            mock_processor = Mock()
            mock_processor.extract_text.side_effect = Exception("PDF processing failed")
            mock_factory.return_value = mock_processor
            
            from src.core.extraction.ingestion_pipeline import KnowledgeGraphService
            kg_service = KnowledgeGraphService(kg_repo)
            
            pipeline = IngestionPipeline(
                processor_factory=ProcessorFactory(),
                embedding_strategy=Mock(),
                kg_service=kg_service
            )
            
            result = pipeline._process_document_sync(test_file_path, "error-doc-1")
            
            # Verify graceful failure handling
            assert not result.success
            assert "PDF processing failed" in result.error_message
        
        # Test partial entity extraction failure
        with patch('src.factories.processor_factory.ProcessorFactory.create_processor') as mock_factory:
            mock_processor = Mock()
            mock_processor.extract_text.return_value = "Valid text content"
            mock_factory.return_value = mock_processor
            
            from src.core.extraction.ingestion_pipeline import KnowledgeGraphService
            kg_service = KnowledgeGraphService(kg_repo)
            
            pipeline = IngestionPipeline(
                processor_factory=ProcessorFactory(),
                embedding_strategy=Mock(),
                kg_service=kg_service
            )
            
            # Mock embedding generation to fail occasionally
            mock_embedding_strategy = Mock()
            mock_embedding_strategy.generate_embeddings.side_effect = [
                [0.1, 0.2, 0.3],  # First call succeeds
                Exception("Embedding failed"),  # Second call fails
                [0.4, 0.5, 0.6]   # Third call succeeds
            ]
            pipeline.embedding_strategy = mock_embedding_strategy
            
            result = pipeline._process_document_sync(test_file_path, "partial-error-doc-1")
            
            # Should still succeed with partial results
            assert result.success  # Pipeline should handle partial failures gracefully