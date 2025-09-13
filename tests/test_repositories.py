"""Tests for repository pattern implementations."""

import pytest
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock

from src.repositories.document_repository import SQLiteDocumentRepository
from src.repositories.patient_repository import SQLitePatientRepository
from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
from src.models.document import Document
from src.models.knowledge_graph import (
    Patient, Section, Diagnosis, Finding, ImpairmentRating,
    KnowledgeNode, KnowledgeRelationship
)
from src.storage.database import DatabaseManager
from src.storage.knowledge_graph_schema import KnowledgeGraphSchemaManager


class TestDocumentRepository:
    """Test document repository implementation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Initialize database
        db_manager = DatabaseManager(db_path)
        kg_schema = KnowledgeGraphSchemaManager(db_path)
        kg_schema.create_knowledge_graph_tables()
        
        yield db_manager
        
        # Cleanup
        os.unlink(db_path)
    
    @pytest.fixture
    def document_repo(self, temp_db):
        """Create document repository with temp database."""
        return SQLiteDocumentRepository(temp_db)
    
    @pytest.fixture
    def sample_document(self):
        """Create sample document for testing."""
        return Document(
            id="test-doc-1",
            title="Test Document",
            file_type="pdf",
            file_size=1024,
            upload_timestamp=datetime.now(),
            processing_status="completed",
            original_text="This is test content",
            document_type="medical",
            analysis="Test analysis"
        )
    
    def test_save_and_find_document(self, document_repo, sample_document):
        """Test saving and finding a document."""
        # Save document
        doc_id = document_repo.save(sample_document)
        assert doc_id == sample_document.id
        
        # Find document
        found_doc = document_repo.find_by_id(doc_id)
        assert found_doc is not None
        assert found_doc.id == sample_document.id
        assert found_doc.title == sample_document.title
        assert found_doc.processing_status == sample_document.processing_status
    
    def test_find_by_criteria(self, document_repo, sample_document):
        """Test finding documents by criteria."""
        # Save document
        document_repo.save(sample_document)
        
        # Find by status
        docs = document_repo.find_by_criteria({'processing_status': 'completed'})
        assert len(docs) == 1
        assert docs[0].id == sample_document.id
        
        # Find by file type
        docs = document_repo.find_by_criteria({'file_type': 'pdf'})
        assert len(docs) == 1
        
        # Find by non-existent criteria
        docs = document_repo.find_by_criteria({'processing_status': 'nonexistent'})
        assert len(docs) == 0
    
    def test_update_document(self, document_repo, sample_document):
        """Test updating a document."""
        # Save document
        document_repo.save(sample_document)
        
        # Update document
        updates = {
            'processing_status': 'failed',
            'analysis': 'Updated analysis'
        }
        success = document_repo.update(sample_document.id, updates)
        assert success
        
        # Verify update
        found_doc = document_repo.find_by_id(sample_document.id)
        assert found_doc.processing_status == 'failed'
        assert found_doc.analysis == 'Updated analysis'
    
    def test_delete_document(self, document_repo, sample_document):
        """Test deleting a document."""
        # Save document
        document_repo.save(sample_document)
        
        # Verify it exists
        found_doc = document_repo.find_by_id(sample_document.id)
        assert found_doc is not None
        
        # Delete document
        success = document_repo.delete(sample_document.id)
        assert success
        
        # Verify it's gone
        found_doc = document_repo.find_by_id(sample_document.id)
        assert found_doc is None


class TestPatientRepository:
    """Test patient repository implementation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Initialize database
        db_manager = DatabaseManager(db_path)
        kg_schema = KnowledgeGraphSchemaManager(db_path)
        kg_schema.create_knowledge_graph_tables()
        
        yield db_manager
        
        # Cleanup
        os.unlink(db_path)
    
    @pytest.fixture
    def patient_repo(self, temp_db):
        """Create patient repository with temp database."""
        return SQLitePatientRepository(temp_db)
    
    @pytest.fixture
    def sample_patient(self):
        """Create sample patient for testing."""
        return Patient(
            id="patient-1",
            name="John Doe",
            age=45,
            gender="M",
            case_number="CASE-001",
            medical_record_number="MRN-12345"
        )
    
    def test_save_and_find_patient(self, patient_repo, sample_patient):
        """Test saving and finding a patient."""
        # Save patient
        patient_id = patient_repo.save(sample_patient)
        assert patient_id == sample_patient.id
        
        # Find patient
        found_patient = patient_repo.find_by_id(patient_id)
        assert found_patient is not None
        assert found_patient.id == sample_patient.id
        assert found_patient.name == sample_patient.name
        assert found_patient.case_number == sample_patient.case_number
    
    def test_find_by_case_number(self, patient_repo, sample_patient):
        """Test finding patient by case number."""
        # Save patient
        patient_repo.save(sample_patient)
        
        # Find by case number
        found_patient = patient_repo.find_by_case_number(sample_patient.case_number)
        assert found_patient is not None
        assert found_patient.id == sample_patient.id
    
    def test_find_by_medical_record_number(self, patient_repo, sample_patient):
        """Test finding patient by medical record number."""
        # Save patient
        patient_repo.save(sample_patient)
        
        # Find by MRN
        found_patient = patient_repo.find_by_medical_record_number(sample_patient.medical_record_number)
        assert found_patient is not None
        assert found_patient.id == sample_patient.id


class TestKnowledgeGraphRepository:
    """Test knowledge graph repository implementation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Initialize database
        db_manager = DatabaseManager(db_path)
        kg_schema = KnowledgeGraphSchemaManager(db_path)
        kg_schema.create_knowledge_graph_tables()
        
        yield db_manager
        
        # Cleanup
        os.unlink(db_path)
    
    @pytest.fixture
    def kg_repo(self, temp_db):
        """Create knowledge graph repository with temp database."""
        return SQLiteKnowledgeGraphRepository(temp_db)
    
    @pytest.fixture
    def sample_node(self):
        """Create sample knowledge node for testing."""
        return KnowledgeNode(
            id="node-1",
            node_type="diagnosis",
            properties={"icd_code": "M54.5", "description": "Low back pain"}
        )
    
    @pytest.fixture
    def sample_relationship(self):
        """Create sample knowledge relationship for testing."""
        return KnowledgeRelationship(
            id="rel-1",
            source_node_id="node-1",
            target_node_id="node-2",
            relationship_type="HAS_IMPAIRMENT",
            confidence=0.9
        )
    
    def test_save_and_find_node(self, kg_repo, sample_node):
        """Test saving and finding a knowledge node."""
        # Save node
        node_id = kg_repo.save_node(sample_node)
        assert node_id == sample_node.id
        
        # Find node
        found_node = kg_repo.find_node_by_id(node_id)
        assert found_node is not None
        assert found_node.id == sample_node.id
        assert found_node.node_type == sample_node.node_type
        assert found_node.properties == sample_node.properties
    
    def test_find_nodes_by_type(self, kg_repo, sample_node):
        """Test finding nodes by type."""
        # Save node
        kg_repo.save_node(sample_node)
        
        # Find by type
        nodes = kg_repo.find_nodes_by_type("diagnosis")
        assert len(nodes) == 1
        assert nodes[0].id == sample_node.id
        
        # Find by non-existent type
        nodes = kg_repo.find_nodes_by_type("nonexistent")
        assert len(nodes) == 0
    
    def test_save_and_find_relationship(self, kg_repo, sample_relationship):
        """Test saving and finding a knowledge relationship."""
        # Save relationship
        rel_id = kg_repo.save_relationship(sample_relationship)
        assert rel_id == sample_relationship.id
        
        # Find by source
        relationships = kg_repo.find_relationships_by_source(sample_relationship.source_node_id)
        assert len(relationships) == 1
        assert relationships[0].id == sample_relationship.id
        
        # Find by target
        relationships = kg_repo.find_relationships_by_target(sample_relationship.target_node_id)
        assert len(relationships) == 1
        assert relationships[0].id == sample_relationship.id
    
    def test_save_section(self, kg_repo):
        """Test saving a document section."""
        section = Section(
            id="section-1",
            document_id="doc-1",
            section_type="history",
            page_number=1,
            text_content="Patient history content"
        )
        
        # Save section
        section_id = kg_repo.save_section(section)
        assert section_id == section.id
        
        # Find sections by document
        sections = kg_repo.find_sections_by_document("doc-1")
        assert len(sections) == 1
        assert sections[0].id == section.id
    
    def test_save_diagnosis(self, kg_repo):
        """Test saving a diagnosis."""
        diagnosis = Diagnosis(
            id="diag-1",
            icd_code="M54.5",
            description="Low back pain",
            severity="moderate",
            certainty=0.8,
            page_reference=2
        )
        
        # Save diagnosis
        diag_id = kg_repo.save_diagnosis(diagnosis)
        assert diag_id == diagnosis.id