"""
Tests for the Enhanced Document Processor.
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.services.enhanced_document_processor import (
    EnhancedDocumentProcessor, MedicalEntity, EntityRelationship, 
    ProvenanceReference, SemanticChunk, create_enhanced_document_processor
)
from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository


class TestEnhancedDocumentProcessor(unittest.TestCase):
    """Test cases for EnhancedDocumentProcessor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_kg_repo = Mock(spec=KnowledgeGraphRepository)
        # Add the missing save_section method to the mock
        self.mock_kg_repo.save_section = Mock()
        self.processor = EnhancedDocumentProcessor(kg_repository=self.mock_kg_repo)
        
        # Sample medical text for testing
        self.sample_medical_text = """
        Patient: John Smith
        Date of Injury: 01/15/2023
        Claim Number: WC-2023-001
        
        HISTORY OF PRESENT ILLNESS:
        The patient is a 45-year-old male who sustained a work-related injury to his lumbar spine.
        He was diagnosed with L4-L5 disc herniation and lumbar radiculopathy.
        
        PHYSICAL EXAMINATION:
        Examination reveals limited range of motion in the lumbar spine.
        MRI of the lumbar spine shows disc herniation at L4-L5 level.
        
        DIAGNOSIS:
        1. M51.26 - Other intervertebral disc displacement, lumbar region
        2. Lumbar radiculopathy
        
        TREATMENT:
        Physical therapy and pain management were recommended.
        
        IMPAIRMENT RATING:
        Based on AMA Table 15-3, the patient has a 12% whole person impairment.
        """
    
    def test_initialization(self):
        """Test processor initialization."""
        self.assertIsNotNone(self.processor)
        self.assertEqual(self.processor.kg_repository, self.mock_kg_repo)
        self.assertIsNotNone(self.processor.patient_patterns)
        self.assertIsNotNone(self.processor.diagnosis_patterns)
    
    def test_semantic_chunking(self):
        """Test semantic chunking functionality."""
        doc_id = "test-doc-123"
        chunks = self.processor.perform_semantic_chunking(self.sample_medical_text, doc_id)
        
        self.assertGreater(len(chunks), 0)
        
        # Check that chunks have proper structure
        for chunk in chunks:
            self.assertIsInstance(chunk, SemanticChunk)
            self.assertIsNotNone(chunk.id)
            self.assertIsNotNone(chunk.text)
            self.assertIsNotNone(chunk.chunk_type)
            self.assertEqual(chunk.metadata['doc_id'], doc_id)
        
        # Check that different section types are detected
        chunk_types = [chunk.chunk_type for chunk in chunks]
        self.assertIn('history', chunk_types)
        self.assertIn('examination', chunk_types)
        self.assertIn('diagnosis', chunk_types)
    
    def test_extract_patients(self):
        """Test patient entity extraction."""
        doc_id = "test-doc-123"
        entities = self.processor._extract_patients(self.sample_medical_text, doc_id, 1)
        
        self.assertGreater(len(entities), 0)
        
        # Check for John Smith
        patient_names = [entity.text for entity in entities]
        self.assertIn('John Smith', patient_names)
        
        # Verify entity structure
        for entity in entities:
            self.assertEqual(entity.entity_type, 'Patient')
            self.assertGreater(entity.confidence, 0)
            self.assertGreater(len(entity.provenance), 0)
    
    def test_extract_diagnoses(self):
        """Test diagnosis entity extraction."""
        doc_id = "test-doc-123"
        entities = self.processor._extract_diagnoses(self.sample_medical_text, doc_id, 1)
        
        self.assertGreater(len(entities), 0)
        
        # Check for specific diagnoses
        diagnosis_texts = [entity.text.lower() for entity in entities]
        self.assertTrue(any('m51.26' in text for text in diagnosis_texts))
        self.assertTrue(any('radiculopathy' in text for text in diagnosis_texts))
        
        # Verify ICD code detection
        icd_entities = [entity for entity in entities if entity.metadata.get('is_icd_code')]
        self.assertGreater(len(icd_entities), 0)
    
    def test_extract_imaging_studies(self):
        """Test imaging study entity extraction."""
        doc_id = "test-doc-123"
        entities = self.processor._extract_imaging_studies(self.sample_medical_text, doc_id, 1)
        
        self.assertGreater(len(entities), 0)
        
        # Check for MRI
        imaging_texts = [entity.text.lower() for entity in entities]
        self.assertTrue(any('mri' in text for text in imaging_texts))
        
        # Verify entity structure
        for entity in entities:
            self.assertEqual(entity.entity_type, 'ImagingStudy')
            self.assertIn('study_type', entity.metadata)
    
    def test_extract_impairment_ratings(self):
        """Test impairment rating entity extraction."""
        doc_id = "test-doc-123"
        entities = self.processor._extract_impairment_ratings(self.sample_medical_text, doc_id, 1)
        
        self.assertGreater(len(entities), 0)
        
        # Check for 12% impairment
        rating_entities = [entity for entity in entities if entity.metadata.get('percentage') == 12]
        self.assertGreater(len(rating_entities), 0)
        
        # Verify entity structure
        for entity in entities:
            self.assertEqual(entity.entity_type, 'ImpairmentRating')
            self.assertGreater(entity.confidence, 0)
    
    def test_extract_medical_entities(self):
        """Test comprehensive medical entity extraction."""
        doc_id = "test-doc-123"
        entities = self.processor.extract_medical_entities(self.sample_medical_text, doc_id, 1)
        
        self.assertGreater(len(entities), 0)
        
        # Check that different entity types are extracted
        entity_types = [entity.entity_type for entity in entities]
        self.assertIn('Patient', entity_types)
        self.assertIn('Diagnosis', entity_types)
        self.assertIn('ImagingStudy', entity_types)
        self.assertIn('ImpairmentRating', entity_types)
        
        # Verify all entities have proper provenance
        for entity in entities:
            self.assertGreater(len(entity.provenance), 0)
            for prov in entity.provenance:
                self.assertEqual(prov.doc_id, doc_id)
                self.assertIsNotNone(prov.snippet)
    
    def test_establish_relationships(self):
        """Test relationship establishment between entities."""
        doc_id = "test-doc-123"
        entities = self.processor.extract_medical_entities(self.sample_medical_text, doc_id, 1)
        relationships = self.processor.establish_relationships(entities)
        
        self.assertGreater(len(relationships), 0)
        
        # Verify relationship structure
        for relationship in relationships:
            self.assertIsInstance(relationship, EntityRelationship)
            self.assertIsNotNone(relationship.id)
            self.assertIsNotNone(relationship.source_entity_id)
            self.assertIsNotNone(relationship.target_entity_id)
            self.assertIsNotNone(relationship.relationship_type)
            self.assertGreater(relationship.confidence, 0)
        
        # Check for expected relationship types
        rel_types = [rel.relationship_type for rel in relationships]
        expected_types = ['HAS_DIAGNOSIS', 'RATES_IMPAIRMENT', 'TREATS', 'SHOWS']
        self.assertTrue(any(rel_type in expected_types for rel_type in rel_types))
    
    def test_process_single_document(self):
        """Test processing of a single document."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(self.sample_medical_text)
            temp_file_path = f.name
        
        try:
            doc_info = {
                'file_path': temp_file_path,
                'doc_id': 'test-doc-123'
            }
            
            result = self.processor._process_single_document(doc_info)
            
            # Verify result structure
            self.assertIn('document_id', result)
            self.assertIn('entity_count', result)
            self.assertIn('relationship_count', result)
            self.assertIn('entities_by_type', result)
            self.assertIn('chunk_count', result)
            
            # Verify counts
            self.assertGreater(result['entity_count'], 0)
            self.assertGreater(result['chunk_count'], 0)
            
            # Verify entity types
            self.assertIn('Patient', result['entities_by_type'])
            self.assertIn('Diagnosis', result['entities_by_type'])
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
    
    def test_process_patient_documents(self):
        """Test processing multiple patient documents."""
        # Create temporary test files
        temp_files = []
        documents = []
        
        try:
            for i in range(2):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(f"Patient: Test Patient {i+1}\n" + self.sample_medical_text)
                    temp_files.append(f.name)
                    documents.append({
                        'file_path': f.name,
                        'doc_id': f'test-doc-{i+1}'
                    })
            
            result = self.processor.process_patient_documents(documents)
            
            # Verify result structure
            self.assertIn('processed_documents', result)
            self.assertIn('total_entities', result)
            self.assertIn('total_relationships', result)
            self.assertIn('entities_by_type', result)
            
            # Verify processing results
            self.assertEqual(len(result['processed_documents']), 2)
            self.assertGreater(result['total_entities'], 0)
            
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
    
    def test_deduplication(self):
        """Test entity deduplication functionality."""
        # Create duplicate entities
        entity1 = MedicalEntity(
            id="1",
            entity_type="Patient",
            text="John Smith",
            normalized_text="john smith",
            confidence=0.8,
            provenance=[ProvenanceReference(doc_id="doc1")]
        )
        
        entity2 = MedicalEntity(
            id="2",
            entity_type="Patient",
            text="John Smith",
            normalized_text="john smith",
            confidence=0.9,
            provenance=[ProvenanceReference(doc_id="doc2")]
        )
        
        entity3 = MedicalEntity(
            id="3",
            entity_type="Diagnosis",
            text="Diabetes",
            normalized_text="diabetes",
            confidence=0.7,
            provenance=[ProvenanceReference(doc_id="doc1")]
        )
        
        entities = [entity1, entity2, entity3]
        deduplicated = self.processor._deduplicate_entities(entities)
        
        # Should have 2 unique entities (1 patient, 1 diagnosis)
        self.assertEqual(len(deduplicated), 2)
        
        # Patient entity should have merged provenance and higher confidence
        patient_entity = next(e for e in deduplicated if e.entity_type == "Patient")
        self.assertEqual(len(patient_entity.provenance), 2)
        self.assertEqual(patient_entity.confidence, 0.9)  # Max confidence
    
    def test_knowledge_graph_storage(self):
        """Test storage in knowledge graph."""
        # Create test entities and relationships
        entity = MedicalEntity(
            id="test-entity-1",
            entity_type="Patient",
            text="Test Patient",
            normalized_text="test patient",
            confidence=0.8,
            provenance=[ProvenanceReference(doc_id="doc1")]
        )
        
        relationship = EntityRelationship(
            id="test-rel-1",
            source_entity_id="entity1",
            target_entity_id="entity2",
            relationship_type="HAS_DIAGNOSIS",
            confidence=0.7,
            evidence="Test evidence",
            provenance=[ProvenanceReference(doc_id="doc1")]
        )
        
        chunk = SemanticChunk(
            id="test-chunk-1",
            text="Test chunk text",
            chunk_type="history",
            metadata={'doc_id': 'doc1'}
        )
        
        # Test storage
        self.processor._store_in_knowledge_graph([entity], [relationship], [chunk])
        
        # Verify repository calls
        self.mock_kg_repo.save_node.assert_called()
        self.mock_kg_repo.save_relationship.assert_called()
        self.mock_kg_repo.save_section.assert_called()
    
    def test_factory_function(self):
        """Test factory function."""
        processor = create_enhanced_document_processor()
        self.assertIsInstance(processor, EnhancedDocumentProcessor)
        self.assertIsNotNone(processor.kg_repository)
    
    @patch('os.path.exists')
    def test_process_specific_pqme_files(self, mock_exists):
        """Test processing of specific PQME files."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock the document processing
        with patch.object(self.processor, 'process_patient_documents') as mock_process:
            mock_process.return_value = {
                'processed_documents': [{'document_id': 'test'}],
                'total_entities': 10,
                'total_relationships': 5
            }
            
            result = self.processor.process_specific_pqme_files()
            
            # Verify the method was called with correct documents
            mock_process.assert_called_once()
            args = mock_process.call_args[0][0]
            self.assertEqual(len(args), 2)  # Two PQME files
            
            # Verify result
            self.assertEqual(result['total_entities'], 10)
            self.assertEqual(result['total_relationships'], 5)
    
    def test_context_snippet_extraction(self):
        """Test context snippet extraction."""
        text = "This is a test sentence with some medical content about diagnosis."
        start = 20
        end = 30
        
        snippet = self.processor._get_context_snippet(text, start, end, context_size=10)
        
        self.assertIsInstance(snippet, str)
        self.assertGreater(len(snippet), 0)
        self.assertIn("sentence", snippet)
    
    def test_relationship_confidence_calculation(self):
        """Test relationship confidence calculation."""
        entity1 = MedicalEntity(
            id="1",
            entity_type="Diagnosis",
            text="Diabetes",
            normalized_text="diabetes",
            confidence=0.8,
            provenance=[ProvenanceReference(doc_id="doc1", page=1, offset=100, snippet="patient has diabetes")]
        )
        
        entity2 = MedicalEntity(
            id="2",
            entity_type="Treatment",
            text="Insulin therapy",
            normalized_text="insulin therapy",
            confidence=0.8,
            provenance=[ProvenanceReference(doc_id="doc1", page=1, offset=150, snippet="treated with insulin")]
        )
        
        confidence = self.processor._calculate_relationship_confidence(entity1, entity2, "TREATS")
        
        self.assertGreater(confidence, 0)
        self.assertLessEqual(confidence, 1.0)


if __name__ == '__main__':
    unittest.main()