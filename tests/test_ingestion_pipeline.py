"""
Tests for the ingestion pipeline functionality.
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch

try:
    from src.core.extraction.ingestion_pipeline import (
        IngestionPipeline, MedicalSectionSegmenter, MedicalNERExtractor,
        KnowledgeGraphService, ProcessingResult, ExtractedEntity
    )
    from src.core.extraction.ingestion_pipeline_factory import IngestionPipelineFactory
    from src.infrastructure.storage.vector_store import InMemoryVectorStore
    from src.factories.processor_factory import ProcessorFactory
    from src.strategies.embedding_strategy import LocalEmbeddingStrategy
    from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
    from src.models.knowledge_graph import Section, Diagnosis, Finding
except ImportError:
    from tests.test_ingestion_pipeline import (
        IngestionPipeline, MedicalSectionSegmenter, MedicalNERExtractor,
        KnowledgeGraphService, ProcessingResult, ExtractedEntity
    )
    from src.core.extraction.ingestion_pipeline_factory import IngestionPipelineFactory
    from src.infrastructure.storage.vector_store import InMemoryVectorStore
    from factories.processor_factory import ProcessorFactory
    from strategies.embedding_strategy import LocalEmbeddingStrategy
    from repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
    from models.knowledge_graph import Section, Diagnosis, Finding


class TestMedicalSectionSegmenter(unittest.TestCase):
    """Test medical section segmentation."""
    
    def setUp(self):
        self.segmenter = MedicalSectionSegmenter()
    
    def test_segment_medical_document(self):
        """Test segmentation of medical document."""
        text = """
        HISTORY OF PRESENT ILLNESS
        Patient presents with lower back pain following a work-related injury.
        
        PHYSICAL EXAMINATION
        Patient appears in mild distress. Range of motion is limited.
        
        DIAGNOSIS
        L5-S1 disc herniation with radiculopathy.
        """
        
        sections = self.segmenter.segment_document(text, "test_doc_1")
        
        self.assertGreater(len(sections), 0)
        
        # Check that sections have expected types
        section_types = [s.section_type for s in sections]
        self.assertIn('history', section_types)
        self.assertIn('examination', section_types)
        self.assertIn('diagnosis', section_types)
    
    def test_identify_section_type(self):
        """Test section type identification."""
        test_cases = [
            ("HISTORY OF PRESENT ILLNESS", "history"),
            ("Physical Examination", "examination"),
            ("DIAGNOSIS:", "diagnosis"),
            ("Clinical Findings", "findings"),
            ("Some random text", None)
        ]
        
        for text, expected_type in test_cases:
            result = self.segmenter._identify_section_type(text)
            self.assertEqual(result, expected_type, f"Failed for text: {text}")


class TestMedicalNERExtractor(unittest.TestCase):
    """Test medical named entity recognition."""
    
    def setUp(self):
        self.extractor = MedicalNERExtractor()
    
    def test_extract_diagnosis_entities(self):
        """Test extraction of diagnosis entities."""
        section = Section(
            id="test_section",
            document_id="test_doc",
            section_type="diagnosis",
            page_number=1,
            text_content="Diagnosis: L5-S1 disc herniation with radiculopathy. ICD-10: M51.16"
        )
        
        entities = self.extractor._extract_from_section(section)
        
        # Should find diagnosis entities
        diagnosis_entities = [e for e in entities if e.entity_type == 'diagnosis']
        self.assertGreater(len(diagnosis_entities), 0)
        
        # Check that ICD code is captured
        icd_found = any('M51.16' in e.text for e in diagnosis_entities)
        self.assertTrue(icd_found)
    
    def test_extract_finding_entities(self):
        """Test extraction of finding entities."""
        section = Section(
            id="test_section",
            document_id="test_doc",
            section_type="examination",
            page_number=1,
            text_content="Examination reveals limited range of motion and positive straight leg raise test."
        )
        
        entities = self.extractor._extract_from_section(section)
        
        # Should find finding entities
        finding_entities = [e for e in entities if e.entity_type == 'finding']
        self.assertGreater(len(finding_entities), 0)
    
    def test_extract_impairment_rating(self):
        """Test extraction of impairment rating entities."""
        section = Section(
            id="test_section",
            document_id="test_doc",
            section_type="impairment",
            page_number=1,
            text_content="Based on AMA Table 15-3, the patient has 15% whole person impairment."
        )
        
        entities = self.extractor._extract_from_section(section)
        
        # Should find impairment rating entities
        impairment_entities = [e for e in entities if e.entity_type == 'impairment_rating']
        self.assertGreater(len(impairment_entities), 0)


class TestKnowledgeGraphService(unittest.TestCase):
    """Test knowledge graph service."""
    
    def setUp(self):
        self.mock_repository = Mock()
        self.kg_service = KnowledgeGraphService(self.mock_repository)
    
    def test_extract_icd_code(self):
        """Test ICD code extraction."""
        test_cases = [
            ("L5-S1 disc herniation M51.16", "M51.16"),
            ("Diagnosis with ICD code S72.001A", "S72.001A"),
            ("No ICD code here", "UNKNOWN")
        ]
        
        for text, expected in test_cases:
            result = self.kg_service._extract_icd_code(text)
            self.assertEqual(result, expected)
    
    def test_extract_percentage(self):
        """Test percentage extraction from impairment text."""
        test_cases = [
            ("15% whole person impairment", 15.0),
            ("Patient has 7.5% disability", 7.5),
            ("No percentage here", 0.0)
        ]
        
        for text, expected in test_cases:
            result = self.kg_service._extract_percentage(text)
            self.assertEqual(result, expected)
    
    def test_extract_ama_table(self):
        """Test AMA table extraction."""
        test_cases = [
            ("Based on AMA Table 15-3", "15-3"),
            ("Using Table 17-2 from AMA guidelines", "17-2"),
            ("No table reference", "UNKNOWN")
        ]
        
        for text, expected in test_cases:
            result = self.kg_service._extract_ama_table(text)
            self.assertEqual(result, expected)


class TestIngestionPipelineFactory(unittest.TestCase):
    """Test ingestion pipeline factory."""
    
    def test_create_default_pipeline(self):
        """Test creation of default pipeline."""
        pipeline = IngestionPipelineFactory.create_default_pipeline()
        
        self.assertIsInstance(pipeline, IngestionPipeline)
        self.assertIsInstance(pipeline.processor_factory, ProcessorFactory)
        self.assertIsInstance(pipeline.embedding_strategy, LocalEmbeddingStrategy)
    
    def test_create_pipeline_from_config(self):
        """Test creation of pipeline from configuration."""
        config = {
            "embedding_strategy_type": "local",
            "embedding_model": "all-MiniLM-L6-v2",
            "vector_store_name": "test_store"
        }
        
        pipeline = IngestionPipelineFactory.create_pipeline_from_config(config)
        
        self.assertIsInstance(pipeline, IngestionPipeline)


class TestIngestionPipelineIntegration(unittest.TestCase):
    """Integration tests for the complete ingestion pipeline."""
    
    def setUp(self):
        self.pipeline = IngestionPipelineFactory.create_default_pipeline(
            vector_store_name="test_integration"
        )
    
    def test_process_sample_medical_document(self):
        """Test processing of a sample medical document."""
        # Create a temporary test document
        sample_content = """
        QUALIFIED MEDICAL EVALUATOR'S REPORT
        
        HISTORY OF PRESENT ILLNESS
        The patient is a 45-year-old male who sustained a work-related injury to his lower back
        on January 15, 2024. He reports constant lower back pain with radiation to the left leg.
        
        PHYSICAL EXAMINATION
        The patient appears in mild distress. Range of motion testing reveals:
        - Flexion: 45 degrees (normal 90 degrees)
        - Extension: 15 degrees (normal 30 degrees)
        Straight leg raise test is positive on the left at 30 degrees.
        
        DIAGNOSIS
        Primary diagnosis: L5-S1 disc herniation with left L5 radiculopathy (ICD-10: M51.16)
        Secondary diagnosis: Chronic lower back pain (ICD-10: M54.5)
        
        IMPAIRMENT RATING
        Based on AMA Guides Table 15-3, the patient has 12% whole person impairment
        due to the disc herniation and associated radiculopathy.
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_content)
            temp_file = f.name
        
        try:
            # Process the document
            result = self.pipeline._process_document_sync(temp_file, "test_doc_integration")
            
            # Verify processing was successful
            self.assertTrue(result.success)
            self.assertEqual(result.document_id, "test_doc_integration")
            self.assertGreater(len(result.sections), 0)
            self.assertGreater(len(result.entities), 0)
            self.assertGreater(result.embeddings_generated, 0)
            
            # Verify sections were created
            section_types = [s.section_type for s in result.sections]
            self.assertIn('history', section_types)
            self.assertIn('examination', section_types)
            self.assertIn('diagnosis', section_types)
            
            # Verify entities were extracted
            entity_types = [e.entity_type for e in result.entities]
            self.assertIn('diagnosis', entity_types)
            self.assertIn('impairment_rating', entity_types)
            
            # Check for specific content
            diagnosis_entities = [e for e in result.entities if e.entity_type == 'diagnosis']
            self.assertTrue(any('M51.16' in e.text for e in diagnosis_entities))
            
            impairment_entities = [e for e in result.entities if e.entity_type == 'impairment_rating']
            # Check that we found impairment entities (either percentage or table reference)
            self.assertTrue(len(impairment_entities) > 0)
            # Check that at least one contains either percentage or table reference
            has_percentage = any('12%' in e.text for e in impairment_entities)
            has_table = any('15-3' in e.text for e in impairment_entities)
            self.assertTrue(has_percentage or has_table, 
                          f"Expected impairment entities with percentage or table, got: {[e.text for e in impairment_entities]}")
            
        finally:
            # Clean up
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()