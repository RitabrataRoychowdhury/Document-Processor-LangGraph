"""Tests for knowledge graph functionality."""

import pytest
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch

from src.models.knowledge_graph import (
    Patient, Section, Diagnosis, Finding, ImpairmentRating, ImagingStudy, Claim,
    KnowledgeNode, KnowledgeRelationship
)
from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
from src.infrastructure.knowledge.knowledge_graph_vector_service import KnowledgeGraphVectorService
from src.storage.database import DatabaseManager
from src.storage.knowledge_graph_schema import KnowledgeGraphSchemaManager


class TestKnowledgeGraphModels:
    """Test knowledge graph domain models."""
    
    def test_patient_model(self):
        """Test Patient model creation and serialization."""
        patient = Patient(
            id="patient-1",
            name="John Doe",
            age=45,
            gender="Male",
            case_number="WC-2024-001",
            medical_record_number="MRN-12345"
        )
        
        # Test basic properties
        assert patient.id == "patient-1"
        assert patient.name == "John Doe"
        assert patient.age == 45
        assert patient.gender == "Male"
        assert patient.case_number == "WC-2024-001"
        assert patient.medical_record_number == "MRN-12345"
        
        # Test serialization
        patient_dict = patient.to_dict()
        assert patient_dict['id'] == "patient-1"
        assert patient_dict['name'] == "John Doe"
        assert patient_dict['age'] == 45
        
        # Test deserialization
        restored_patient = Patient.from_dict(patient_dict)
        assert restored_patient.id == patient.id
        assert restored_patient.name == patient.name
        assert restored_patient.age == patient.age
    
    def test_diagnosis_model(self):
        """Test Diagnosis model creation and serialization."""
        diagnosis = Diagnosis(
            id="diag-1",
            icd_code="M54.5",
            description="Low back pain",
            severity="moderate",
            certainty=0.9,
            source_section_id="section-1",
            page_reference=2
        )
        
        # Test basic properties
        assert diagnosis.id == "diag-1"
        assert diagnosis.icd_code == "M54.5"
        assert diagnosis.description == "Low back pain"
        assert diagnosis.severity == "moderate"
        assert diagnosis.certainty == 0.9
        assert diagnosis.source_section_id == "section-1"
        assert diagnosis.page_reference == 2
        
        # Test serialization/deserialization
        diag_dict = diagnosis.to_dict()
        restored_diagnosis = Diagnosis.from_dict(diag_dict)
        assert restored_diagnosis.id == diagnosis.id
        assert restored_diagnosis.icd_code == diagnosis.icd_code
        assert restored_diagnosis.certainty == diagnosis.certainty
    
    def test_section_model(self):
        """Test Section model creation and serialization."""
        section = Section(
            id="section-1",
            document_id="doc-1",
            section_type="history",
            page_number=1,
            text_content="Patient history content"
        )
        
        # Test basic properties
        assert section.id == "section-1"
        assert section.document_id == "doc-1"
        assert section.section_type == "history"
        assert section.page_number == 1
        assert section.text_content == "Patient history content"
        
        # Test serialization/deserialization
        section_dict = section.to_dict()
        restored_section = Section.from_dict(section_dict)
        assert restored_section.id == section.id
        assert restored_section.document_id == section.document_id
        assert restored_section.section_type == section.section_type
    
    def test_finding_model(self):
        """Test Finding model creation and serialization."""
        finding = Finding(
            id="finding-1",
            section_id="section-1",
            finding_type="physical",
            description="Limited range of motion",
            page_reference=3
        )
        
        # Test basic properties
        assert finding.id == "finding-1"
        assert finding.section_id == "section-1"
        assert finding.finding_type == "physical"
        assert finding.description == "Limited range of motion"
        assert finding.page_reference == 3
        
        # Test serialization/deserialization
        finding_dict = finding.to_dict()
        restored_finding = Finding.from_dict(finding_dict)
        assert restored_finding.id == finding.id
        assert restored_finding.finding_type == finding.finding_type
        assert restored_finding.description == finding.description
    
    def test_impairment_rating_model(self):
        """Test ImpairmentRating model creation and serialization."""
        rating = ImpairmentRating(
            id="rating-1",
            diagnosis_id="diag-1",
            ama_table="15-3",
            percentage=10.0,
            rationale="Based on DRE Category II",
            source_page=45
        )
        
        # Test basic properties
        assert rating.id == "rating-1"
        assert rating.diagnosis_id == "diag-1"
        assert rating.ama_table == "15-3"
        assert rating.percentage == 10.0
        assert rating.rationale == "Based on DRE Category II"
        assert rating.source_page == 45
        
        # Test serialization/deserialization
        rating_dict = rating.to_dict()
        restored_rating = ImpairmentRating.from_dict(rating_dict)
        assert restored_rating.id == rating.id
        assert restored_rating.ama_table == rating.ama_table
        assert restored_rating.percentage == rating.percentage
    
    def test_knowledge_node_model(self):
        """Test KnowledgeNode model creation and serialization."""
        node = KnowledgeNode(
            id="node-1",
            node_type="diagnosis",
            properties={"icd_code": "M54.5", "description": "Low back pain"},
            embeddings=[0.1, 0.2, 0.3]
        )
        
        # Test basic properties
        assert node.id == "node-1"
        assert node.node_type == "diagnosis"
        assert node.properties["icd_code"] == "M54.5"
        assert node.embeddings == [0.1, 0.2, 0.3]
        
        # Test serialization/deserialization
        node_dict = node.to_dict()
        restored_node = KnowledgeNode.from_dict(node_dict)
        assert restored_node.id == node.id
        assert restored_node.node_type == node.node_type
        assert restored_node.properties == node.properties
    
    def test_knowledge_relationship_model(self):
        """Test KnowledgeRelationship model creation and serialization."""
        relationship = KnowledgeRelationship(
            id="rel-1",
            source_node_id="node-1",
            target_node_id="node-2",
            relationship_type="HAS_IMPAIRMENT",
            properties={"strength": "strong"},
            confidence=0.9
        )
        
        # Test basic properties
        assert relationship.id == "rel-1"
        assert relationship.source_node_id == "node-1"
        assert relationship.target_node_id == "node-2"
        assert relationship.relationship_type == "HAS_IMPAIRMENT"
        assert relationship.confidence == 0.9
        
        # Test serialization/deserialization
        rel_dict = relationship.to_dict()
        restored_rel = KnowledgeRelationship.from_dict(rel_dict)
        assert restored_rel.id == relationship.id
        assert restored_rel.relationship_type == relationship.relationship_type
        assert restored_rel.confidence == relationship.confidence


class TestKnowledgeGraphRepository:
    """Test knowledge graph repository functionality."""
    
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
    
    def test_node_creation_and_retrieval(self, kg_repo):
        """Test creating and retrieving knowledge graph nodes."""
        # Create a diagnosis node
        diagnosis_node = KnowledgeNode(
            id="diag-node-1",
            node_type="diagnosis",
            properties={
                "icd_code": "M54.5",
                "description": "Low back pain",
                "severity": "moderate"
            }
        )
        
        # Save node
        node_id = kg_repo.save_node(diagnosis_node)
        assert node_id == diagnosis_node.id
        
        # Retrieve node
        retrieved_node = kg_repo.find_node_by_id(node_id)
        assert retrieved_node is not None
        assert retrieved_node.id == diagnosis_node.id
        assert retrieved_node.node_type == diagnosis_node.node_type
        assert retrieved_node.properties == diagnosis_node.properties
    
    def test_relationship_creation_and_retrieval(self, kg_repo):
        """Test creating and retrieving knowledge graph relationships."""
        # Create two nodes first
        node1 = KnowledgeNode(
            id="node-1",
            node_type="diagnosis",
            properties={"description": "Low back pain"}
        )
        node2 = KnowledgeNode(
            id="node-2",
            node_type="impairment_rating",
            properties={"percentage": 10.0}
        )
        
        kg_repo.save_node(node1)
        kg_repo.save_node(node2)
        
        # Create relationship
        relationship = KnowledgeRelationship(
            id="rel-1",
            source_node_id="node-1",
            target_node_id="node-2",
            relationship_type="HAS_IMPAIRMENT",
            confidence=0.9
        )
        
        # Save relationship
        rel_id = kg_repo.save_relationship(relationship)
        assert rel_id == relationship.id
        
        # Retrieve relationships
        source_rels = kg_repo.find_relationships_by_source("node-1")
        assert len(source_rels) == 1
        assert source_rels[0].id == relationship.id
        assert source_rels[0].relationship_type == "HAS_IMPAIRMENT"
        
        target_rels = kg_repo.find_relationships_by_target("node-2")
        assert len(target_rels) == 1
        assert target_rels[0].id == relationship.id
    
    def test_specialized_entity_storage(self, kg_repo):
        """Test storing specialized medical entities."""
        # Test section storage
        section = Section(
            id="section-1",
            document_id="doc-1",
            section_type="history",
            page_number=1,
            text_content="Patient history content"
        )
        
        section_id = kg_repo.save_section(section)
        assert section_id == section.id
        
        # Test diagnosis storage
        diagnosis = Diagnosis(
            id="diag-1",
            icd_code="M54.5",
            description="Low back pain",
            certainty=0.9
        )
        
        diag_id = kg_repo.save_diagnosis(diagnosis)
        assert diag_id == diagnosis.id
        
        # Test finding storage
        finding = Finding(
            id="finding-1",
            section_id="section-1",
            finding_type="physical",
            description="Limited range of motion",
            page_reference=2
        )
        
        finding_id = kg_repo.save_finding(finding)
        assert finding_id == finding.id
        
        # Test impairment rating storage
        rating = ImpairmentRating(
            id="rating-1",
            diagnosis_id="diag-1",
            ama_table="15-3",
            percentage=10.0,
            rationale="DRE Category II"
        )
        
        rating_id = kg_repo.save_impairment_rating(rating)
        assert rating_id == rating.id
    
    def test_data_integrity_constraints(self, kg_repo):
        """Test data integrity and constraint validation."""
        # Test duplicate ID handling
        node1 = KnowledgeNode(
            id="duplicate-id",
            node_type="diagnosis",
            properties={"description": "First diagnosis"}
        )
        
        node2 = KnowledgeNode(
            id="duplicate-id",
            node_type="finding",
            properties={"description": "Second finding"}
        )
        
        # Save first node
        kg_repo.save_node(node1)
        
        # Save second node with same ID (should update)
        kg_repo.save_node(node2)
        
        # Retrieve and verify it was updated
        retrieved = kg_repo.find_node_by_id("duplicate-id")
        assert retrieved.node_type == "finding"
        assert retrieved.properties["description"] == "Second finding"
    
    def test_complex_relationship_patterns(self, kg_repo):
        """Test complex relationship patterns in knowledge graph."""
        # Create patient as knowledge node
        patient_node = KnowledgeNode(
            id="patient-1",
            node_type="patient",
            properties={"name": "John Doe", "case_number": "WC-001"}
        )
        kg_repo.save_node(patient_node)
        
        # Create diagnoses
        diag1 = Diagnosis(id="diag-1", icd_code="M54.5", description="Low back pain")
        diag2 = Diagnosis(id="diag-2", icd_code="M25.511", description="Knee pain")
        kg_repo.save_diagnosis(diag1)
        kg_repo.save_diagnosis(diag2)
        
        # Create impairment ratings
        rating1 = ImpairmentRating(id="rating-1", diagnosis_id="diag-1", ama_table="15-3", percentage=10.0, rationale="DRE Category II")
        rating2 = ImpairmentRating(id="rating-2", diagnosis_id="diag-2", ama_table="17-2", percentage=5.0, rationale="Knee impairment")
        kg_repo.save_impairment_rating(rating1)
        kg_repo.save_impairment_rating(rating2)
        
        # Create relationships
        patient_diag1_rel = KnowledgeRelationship(
            id="rel-1", source_node_id="patient-1", target_node_id="diag-1",
            relationship_type="HAS_DIAGNOSIS", confidence=1.0
        )
        patient_diag2_rel = KnowledgeRelationship(
            id="rel-2", source_node_id="patient-1", target_node_id="diag-2",
            relationship_type="HAS_DIAGNOSIS", confidence=1.0
        )
        diag1_rating_rel = KnowledgeRelationship(
            id="rel-3", source_node_id="diag-1", target_node_id="rating-1",
            relationship_type="HAS_IMPAIRMENT", confidence=0.9
        )
        diag2_rating_rel = KnowledgeRelationship(
            id="rel-4", source_node_id="diag-2", target_node_id="rating-2",
            relationship_type="HAS_IMPAIRMENT", confidence=0.8
        )
        
        kg_repo.save_relationship(patient_diag1_rel)
        kg_repo.save_relationship(patient_diag2_rel)
        kg_repo.save_relationship(diag1_rating_rel)
        kg_repo.save_relationship(diag2_rating_rel)
        
        # Verify complex queries
        patient_diagnoses = kg_repo.find_relationships_by_source("patient-1")
        assert len(patient_diagnoses) == 2
        
        diagnosis_impairments = kg_repo.find_relationships_by_source("diag-1")
        assert len(diagnosis_impairments) == 1
        assert diagnosis_impairments[0].relationship_type == "HAS_IMPAIRMENT"


class TestKnowledgeGraphVectorService:
    """Test knowledge graph vector service functionality."""
    
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
    def kg_vector_service(self, temp_db):
        """Create knowledge graph vector service with temp database."""
        kg_repo = SQLiteKnowledgeGraphRepository(temp_db)
        
        # Mock embedding strategy to avoid external dependencies
        mock_embedding_strategy = Mock()
        mock_embedding_strategy.generate_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        return KnowledgeGraphVectorService(
            kg_repository=kg_repo,
            embedding_strategy=mock_embedding_strategy,
            vector_store_name="test_kg_store"
        )
    
    def test_node_text_creation(self, kg_vector_service):
        """Test creating text representations of knowledge graph nodes."""
        # Test diagnosis node
        diagnosis_node = KnowledgeNode(
            id="diag-1",
            node_type="diagnosis",
            properties={
                "description": "Low back pain",
                "icd_code": "M54.5",
                "severity": "moderate"
            }
        )
        
        text = kg_vector_service._create_node_text(diagnosis_node)
        assert "Diagnosis: Low back pain" in text
        assert "ICD Code: M54.5" in text
        assert "Severity: moderate" in text
        
        # Test finding node
        finding_node = KnowledgeNode(
            id="finding-1",
            node_type="finding",
            properties={
                "description": "Limited range of motion",
                "finding_type": "physical",
                "page_reference": 3
            }
        )
        
        text = kg_vector_service._create_node_text(finding_node)
        assert "Finding: Limited range of motion" in text
        assert "Type: physical" in text
        assert "Page: 3" in text
    
    def test_add_node_to_vector_store(self, kg_vector_service):
        """Test adding individual nodes to vector store."""
        diagnosis_node = KnowledgeNode(
            id="diag-1",
            node_type="diagnosis",
            properties={
                "description": "Low back pain",
                "icd_code": "M54.5"
            }
        )
        
        # Add node to vector store
        success = kg_vector_service.add_node_to_vector_store(diagnosis_node)
        assert success
        
        # Verify embeddings were generated and stored
        assert diagnosis_node.embeddings is not None
        assert len(diagnosis_node.embeddings) == 5  # Mock returns 5 values
    
    def test_search_similar_nodes(self, kg_vector_service):
        """Test searching for similar nodes using vector similarity."""
        # Add some test nodes
        nodes = [
            KnowledgeNode(
                id="diag-1",
                node_type="diagnosis",
                properties={"description": "Low back pain", "icd_code": "M54.5"}
            ),
            KnowledgeNode(
                id="diag-2",
                node_type="diagnosis",
                properties={"description": "Knee pain", "icd_code": "M25.511"}
            ),
            KnowledgeNode(
                id="finding-1",
                node_type="finding",
                properties={"description": "Limited range of motion", "finding_type": "physical"}
            )
        ]
        
        for node in nodes:
            kg_vector_service.add_node_to_vector_store(node)
        
        # Mock vector store search results
        with patch.object(kg_vector_service.vector_store, 'search_by_text') as mock_search:
            mock_doc = Mock()
            mock_doc.text = "Diagnosis: Low back pain. ICD Code: M54.5"
            mock_doc.metadata = {
                'node_id': 'diag-1',
                'node_type': 'diagnosis',
                'description': 'Low back pain'
            }
            mock_search.return_value = [(mock_doc, 0.85)]
            
            results = kg_vector_service.search_similar_nodes("back pain", top_k=5)
            
            assert len(results) == 1
            assert results[0]['node_id'] == 'diag-1'
            assert results[0]['node_type'] == 'diagnosis'
            assert results[0]['similarity'] == 0.85
    
    def test_vector_store_stats(self, kg_vector_service):
        """Test getting vector store statistics."""
        # Add some test nodes
        diagnosis_node = KnowledgeNode(
            id="diag-1",
            node_type="diagnosis",
            properties={"description": "Low back pain"}
        )
        finding_node = KnowledgeNode(
            id="finding-1",
            node_type="finding",
            properties={"description": "Limited ROM"}
        )
        
        kg_vector_service.add_node_to_vector_store(diagnosis_node)
        kg_vector_service.add_node_to_vector_store(finding_node)
        
        # Mock vector store stats
        with patch.object(kg_vector_service.vector_store, 'get_stats') as mock_stats:
            mock_stats.return_value = {'total_documents': 2}
            
            stats = kg_vector_service.get_vector_store_stats()
            
            assert 'total_documents' in stats
            assert 'knowledge_graph_documents' in stats
            assert 'node_type_counts' in stats