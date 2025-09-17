"""
Integration tests for Enhanced RAG Pipeline with OpenRouter Integration.

This module provides comprehensive end-to-end testing for the enhanced document
processing pipeline with quality validation and performance metrics.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

from src.services.enhanced_rag_pipeline import (
    EnhancedRAGPipeline, ProcessingResult, RAGGenerationRequest, RAGGenerationResult
)
from src.services.refactored_document_processor import (
    RefactoredDocumentProcessor, DocumentProcessingConfig
)
from src.services.enhanced_vector_search import EnhancedVectorSearch, SearchQuery
from src.services.metadata_tracking_service import MetadataTrackingService
from src.models.extraction_models import (
    ExtractionConfig, ExtractionResult, ExtractedField, QualityAssessment,
    ProcessingMetadata, SourceReference
)


class TestEnhancedRAGIntegration:
    """Integration tests for enhanced RAG pipeline."""
    
    @pytest.fixture
    def mock_openrouter_service(self):
        """Mock OpenRouter extraction service."""
        service = Mock()
        
        # Mock extraction result
        extraction_result = ExtractionResult(
            document_id="test_doc_123",
            extraction_method="openrouter_claude_3_5_sonnet",
            confidence_score=0.85,
            extracted_fields={
                "patient_name": ExtractedField(
                    name="patient_name",
                    value="John Doe",
                    confidence=0.9,
                    source_location="page 1",
                    validation_status="validated",
                    notes="High confidence extraction"
                ),
                "diagnosis": ExtractedField(
                    name="diagnosis",
                    value="Lumbar spine strain",
                    confidence=0.8,
                    source_location="page 2",
                    validation_status="validated",
                    notes="Medical terminology detected"
                )
            },
            quality_assessment=QualityAssessment(
                overall_score=0.85,
                completeness_score=0.9,
                accuracy_score=0.8,
                consistency_score=0.85,
                compliance_score=0.9,
                identified_issues=[],
                improvement_suggestions=[],
                confidence_intervals={}
            ),
            processing_metadata=ProcessingMetadata(
                extraction_method="openrouter_claude_3_5_sonnet",
                processing_time=2.5,
                model_used="claude-3-5-sonnet-20241022",
                prompt_template="patient_info",
                api_version="v1"
            ),
            source_references=[
                SourceReference(
                    document_id="test_doc_123",
                    page_number=1,
                    section="patient_info",
                    text_snippet="Patient: John Doe",
                    confidence=0.9
                )
            ],
            validation_results=[]
        )
        
        service.extract_from_document.return_value = extraction_result
        service.validate_extraction_quality.return_value = extraction_result.quality_assessment
        
        return service
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store."""
        from src.services.vector_store import InMemoryVectorStore, VectorDocument
        
        store = InMemoryVectorStore()
        
        # Add some test documents
        test_docs = [
            ("doc1", "Patient John Doe has lumbar spine strain", [0.1] * 384, {"source": "medical_record"}),
            ("doc2", "Diagnosis: Lumbar spine strain with 15% impairment", [0.2] * 384, {"source": "qme_report"}),
            ("doc3", "Treatment plan for spine injury", [0.3] * 384, {"source": "treatment_plan"})
        ]
        
        for doc_id, text, embeddings, metadata in test_docs:
            store.add_document(doc_id, text, embeddings, metadata)
        
        return store
    
    @pytest.fixture
    def mock_embedding_strategy(self):
        """Mock embedding strategy."""
        strategy = Mock()
        strategy.generate_embeddings.return_value = [0.1] * 384  # Mock 384-dimensional embeddings
        return strategy
    
    @pytest.fixture
    def mock_kg_repository(self):
        """Mock knowledge graph repository."""
        repo = Mock()
        repo.find_nodes_by_type.return_value = []
        repo.find_node_by_id.return_value = None
        repo.find_relationships_by_source.return_value = []
        repo.find_relationships_by_target.return_value = []
        return repo
    
    @pytest.fixture
    def enhanced_rag_pipeline(self, mock_openrouter_service, mock_vector_store, 
                            mock_embedding_strategy, mock_kg_repository):
        """Create enhanced RAG pipeline with mocked dependencies."""
        return EnhancedRAGPipeline(
            openrouter_service=mock_openrouter_service,
            vector_store=mock_vector_store,
            embedding_strategy=mock_embedding_strategy,
            kg_repository=mock_kg_repository
        )
    
    @pytest.fixture
    def test_document_path(self):
        """Create a temporary test document."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("""
            Patient Information:
            Name: John Doe
            Age: 45
            Gender: Male
            
            Medical History:
            The patient presents with lower back pain following a work-related injury.
            Diagnosis: Lumbar spine strain
            
            Examination Findings:
            Range of motion is limited in flexion and extension.
            Pain level: 7/10
            
            Treatment Plan:
            Physical therapy recommended.
            Follow-up in 4 weeks.
            """)
            return f.name
    
    def test_enhanced_document_processing_end_to_end(self, enhanced_rag_pipeline, test_document_path):
        """Test complete document processing pipeline."""
        # Create extraction configuration
        extraction_config = ExtractionConfig(
            prompt_template="patient_info",
            extraction_type="comprehensive",
            quality_threshold=0.7,
            enable_vision=False
        )
        
        # Process document
        result = enhanced_rag_pipeline.process_document_with_enhanced_extraction(
            test_document_path, extraction_config
        )
        
        # Verify processing result
        assert result.success is True
        assert result.document_id is not None
        assert result.extraction_result is not None
        assert result.extraction_result.confidence_score >= 0.7
        assert len(result.retrieval_contexts) > 0
        assert result.quality_assessment.overall_score > 0
        
        # Verify extracted fields
        extracted_fields = result.extraction_result.extracted_fields
        assert "patient_name" in extracted_fields
        assert "diagnosis" in extracted_fields
        assert extracted_fields["patient_name"].value == "John Doe"
        assert extracted_fields["diagnosis"].value == "Lumbar spine strain"
        
        # Verify source references
        assert len(result.source_references) > 0
        assert result.source_references[0].document_id == result.document_id
        
        # Clean up
        os.unlink(test_document_path)
    
    def test_enhanced_context_retrieval(self, enhanced_rag_pipeline):
        """Test enhanced context retrieval with multiple strategies."""
        query = "lumbar spine strain diagnosis"
        document_context = {
            "document_id": "test_doc_123",
            "original_text": "Patient has lumbar spine strain with limited range of motion"
        }
        
        # Retrieve contexts
        contexts = enhanced_rag_pipeline.retrieve_enhanced_context(
            query, document_context, max_contexts=5, min_relevance_score=0.1
        )
        
        # Verify contexts
        assert len(contexts) > 0
        
        for context in contexts:
            assert context.text is not None
            assert context.source is not None
            assert context.relevance_score >= 0.1
            assert context.confidence_score > 0
            assert len(context.source_references) > 0
    
    def test_rag_content_generation(self, enhanced_rag_pipeline):
        """Test RAG-based content generation."""
        request = RAGGenerationRequest(
            query="What is the diagnosis for this patient?",
            document_context={
                "document_id": "test_doc_123",
                "patient_name": "John Doe",
                "diagnosis": "Lumbar spine strain"
            },
            max_contexts=5,
            min_relevance_score=0.3
        )
        
        # Generate content
        result = enhanced_rag_pipeline.generate_rag_content(request)
        
        # Verify generation result
        assert result.generated_content is not None
        assert len(result.generated_content) > 0
        assert result.confidence_score > 0
        assert len(result.source_contexts) > 0
        assert len(result.citations) > 0
        
        # Verify quality metrics
        assert "context_coverage" in result.quality_metrics
        assert "source_diversity" in result.quality_metrics
    
    def test_processing_statistics_tracking(self, enhanced_rag_pipeline, test_document_path):
        """Test processing statistics tracking."""
        # Get initial statistics
        initial_stats = enhanced_rag_pipeline.get_processing_statistics()
        initial_docs = initial_stats['documents_processed']
        
        # Process a document
        extraction_config = ExtractionConfig(
            prompt_template="patient_info",
            extraction_type="comprehensive"
        )
        
        result = enhanced_rag_pipeline.process_document_with_enhanced_extraction(
            test_document_path, extraction_config
        )
        
        # Get updated statistics
        updated_stats = enhanced_rag_pipeline.get_processing_statistics()
        
        # Verify statistics were updated
        assert updated_stats['documents_processed'] == initial_docs + 1
        assert updated_stats['extraction_successes'] >= initial_stats['extraction_successes']
        assert updated_stats['average_processing_time'] > 0
        
        # Clean up
        os.unlink(test_document_path)


class TestRefactoredDocumentProcessor:
    """Integration tests for refactored document processor."""
    
    @pytest.fixture
    def processor_config(self):
        """Create processor configuration."""
        return DocumentProcessingConfig(
            use_openrouter_extraction=True,
            use_vision_extraction=False,
            extraction_prompt_template="patient_info",
            max_contexts_per_document=10,
            min_confidence_threshold=0.7,
            enable_knowledge_graph_updates=True,
            enable_vector_store_updates=True,
            quality_validation_enabled=True
        )
    
    @pytest.fixture
    def refactored_processor(self, processor_config):
        """Create refactored document processor with mocked dependencies."""
        with patch('src.services.refactored_document_processor.OpenRouterExtractionService') as mock_openrouter, \
             patch('src.services.refactored_document_processor.InMemoryVectorStore') as mock_vector_store, \
             patch('src.services.refactored_document_processor.EmbeddingStrategyFactory') as mock_embedding_factory, \
             patch('src.services.refactored_document_processor.SQLiteKnowledgeGraphRepository') as mock_kg_repo:
            
            # Configure mocks
            mock_embedding_factory.create_strategy.return_value = Mock()
            
            processor = RefactoredDocumentProcessor(config=processor_config)
            return processor
    
    @pytest.fixture
    def test_document_path(self):
        """Create a temporary test document."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test document content for processing")
            return f.name
    
    def test_document_processing_with_refactored_processor(self, refactored_processor, test_document_path):
        """Test document processing with refactored processor."""
        # Mock the RAG pipeline processing
        with patch.object(refactored_processor.rag_pipeline, 'process_document_with_enhanced_extraction') as mock_process:
            # Configure mock return value
            mock_result = Mock()
            mock_result.success = True
            mock_result.document_id = "test_doc_123"
            mock_result.extraction_result = Mock()
            mock_result.extraction_result.confidence_score = 0.85
            mock_result.extraction_result.extracted_fields = {}
            mock_result.quality_assessment = Mock()
            mock_result.quality_assessment.overall_score = 0.8
            mock_result.processing_metadata = Mock()
            mock_result.processing_metadata.extraction_method = "enhanced_rag_openrouter"
            mock_result.processing_metadata.model_used = "claude-3-5-sonnet"
            mock_result.processing_metadata.processing_time = 2.5
            mock_result.retrieval_contexts = []
            mock_result.source_references = []
            mock_result.error_message = None
            
            mock_process.return_value = mock_result
            
            # Process document
            result = refactored_processor.process_document(test_document_path)
            
            # Verify result
            assert result['success'] is True
            assert result['document_id'] == "test_doc_123"
            assert result['processing_metadata']['extraction_method'] == "enhanced_rag_openrouter"
            assert result['processing_metadata']['confidence_score'] == 0.85
            assert result['error_message'] is None
        
        # Clean up
        os.unlink(test_document_path)
    
    def test_batch_document_processing(self, refactored_processor):
        """Test batch document processing."""
        # Create multiple test documents
        test_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f"Test document {i} content")
                test_files.append(f.name)
        
        try:
            # Mock the individual document processing
            with patch.object(refactored_processor, 'process_document') as mock_process:
                mock_process.return_value = {
                    'success': True,
                    'document_id': 'test_doc',
                    'processing_metadata': {'processing_time': 1.0}
                }
                
                # Process batch
                result = refactored_processor.process_multiple_documents(test_files)
                
                # Verify batch result
                assert result['total_documents'] == 3
                assert result['successful_count'] == 3
                assert result['failed_count'] == 0
                assert result['success_rate'] == 1.0
                assert len(result['results']) == 3
                
        finally:
            # Clean up
            for file_path in test_files:
                os.unlink(file_path)
    
    def test_qme_field_extraction(self, refactored_processor, test_document_path):
        """Test QME field extraction."""
        # Mock the RAG pipeline processing
        with patch.object(refactored_processor.rag_pipeline, 'process_document_with_enhanced_extraction') as mock_process:
            # Configure mock return value
            mock_result = Mock()
            mock_result.success = True
            mock_result.document_id = "test_doc_123"
            mock_result.extraction_result = Mock()
            mock_result.extraction_result.confidence_score = 0.85
            mock_result.extraction_result.extraction_method = "enhanced_rag_openrouter"
            mock_result.extraction_result.extracted_fields = {
                "patient_name": Mock(value="John Doe", confidence=0.9, source_location="page 1", validation_status="validated"),
                "diagnosis": Mock(value="Lumbar strain", confidence=0.8, source_location="page 2", validation_status="validated")
            }
            mock_result.processing_metadata = Mock()
            mock_result.processing_metadata.processing_time = 2.0
            mock_result.error_message = None
            
            mock_process.return_value = mock_result
            
            # Extract QME fields
            result = refactored_processor.extract_qme_fields(test_document_path)
            
            # Verify result
            assert result['success'] is True
            assert 'qme_fields' in result
            assert 'patient_name' in result['qme_fields']
            assert 'diagnosis' in result['qme_fields']
            assert result['qme_fields']['patient_name']['value'] == "John Doe"
            assert result['qme_fields']['diagnosis']['value'] == "Lumbar strain"
            assert result['extraction_metadata']['overall_confidence'] == 0.85
        
        # Clean up
        os.unlink(test_document_path)
    
    def test_processing_metrics_collection(self, refactored_processor):
        """Test processing metrics collection."""
        # Get initial metrics
        metrics = refactored_processor.get_processing_metrics()
        
        # Verify metrics structure
        assert 'processor_metrics' in metrics
        assert 'pipeline_metrics' in metrics
        assert 'configuration' in metrics
        
        processor_metrics = metrics['processor_metrics']
        assert 'total_documents' in processor_metrics
        assert 'successful_extractions' in processor_metrics
        assert 'failed_extractions' in processor_metrics
        assert 'success_rate' in processor_metrics
        assert 'average_processing_time' in processor_metrics
        
        config = metrics['configuration']
        assert 'use_openrouter_extraction' in config
        assert 'min_confidence_threshold' in config


class TestEnhancedVectorSearch:
    """Integration tests for enhanced vector search."""
    
    @pytest.fixture
    def vector_search(self):
        """Create enhanced vector search with test data."""
        from src.services.vector_store import InMemoryVectorStore, VectorDocument
        
        vector_store = InMemoryVectorStore()
        
        # Add test documents
        test_docs = [
            ("doc1", "Patient John Doe diagnosed with lumbar spine strain", [0.1] * 384, 
             {"source": "medical_record", "confidence": 0.9}),
            ("doc2", "Lumbar spine impairment rating 15% based on AMA guidelines", [0.2] * 384, 
             {"source": "qme_report", "confidence": 0.8}),
            ("doc3", "Physical therapy treatment for spine injury recovery", [0.3] * 384, 
             {"source": "treatment_plan", "confidence": 0.7})
        ]
        
        for doc_id, text, embeddings, metadata in test_docs:
            vector_store.add_document(doc_id, text, embeddings, metadata)
        
        # Mock embedding strategy
        embedding_strategy = Mock()
        embedding_strategy.generate_embeddings.return_value = [0.15] * 384
        
        return EnhancedVectorSearch(vector_store, embedding_strategy)
    
    def test_semantic_search(self, vector_search):
        """Test semantic search functionality."""
        query = SearchQuery(
            text="lumbar spine diagnosis",
            query_type="semantic",
            max_results=5,
            min_relevance_score=0.1
        )
        
        results = vector_search.search(query)
        
        # Verify results
        assert len(results) > 0
        
        for result in results:
            assert result.document is not None
            assert result.semantic_score > 0
            assert result.final_score >= query.min_relevance_score
            assert result.explanation is not None
    
    def test_keyword_search(self, vector_search):
        """Test keyword search functionality."""
        query = SearchQuery(
            text="lumbar spine patient",
            query_type="keyword",
            max_results=5,
            min_relevance_score=0.1
        )
        
        results = vector_search.search(query)
        
        # Verify results
        assert len(results) > 0
        
        for result in results:
            assert result.document is not None
            assert result.keyword_score > 0
            assert result.final_score >= query.min_relevance_score
    
    def test_hybrid_search(self, vector_search):
        """Test hybrid search functionality."""
        query = SearchQuery(
            text="spine impairment rating",
            query_type="hybrid",
            max_results=5,
            min_relevance_score=0.1
        )
        
        results = vector_search.search(query)
        
        # Verify results
        assert len(results) > 0
        
        for result in results:
            assert result.document is not None
            assert result.final_score >= query.min_relevance_score
            # Hybrid search should have both semantic and keyword scores
            assert result.semantic_score >= 0 or result.keyword_score >= 0
    
    def test_search_with_filters(self, vector_search):
        """Test search with filters."""
        query = SearchQuery(
            text="spine",
            query_type="hybrid",
            filters={"source": "qme_report"},
            max_results=5,
            min_relevance_score=0.1
        )
        
        results = vector_search.search(query)
        
        # Verify filtered results
        for result in results:
            assert result.document.metadata.get("source") == "qme_report"
    
    def test_search_with_boost_factors(self, vector_search):
        """Test search with boost factors."""
        query = SearchQuery(
            text="spine",
            query_type="hybrid",
            boost_factors={"confidence": 0.5},
            max_results=5,
            min_relevance_score=0.1
        )
        
        results = vector_search.search(query)
        
        # Verify boost factors were applied
        for result in results:
            if result.document.metadata.get("confidence"):
                assert result.boost_score > 0


class TestMetadataTrackingService:
    """Integration tests for metadata tracking service."""
    
    @pytest.fixture
    def metadata_service(self):
        """Create metadata tracking service."""
        return MetadataTrackingService()
    
    def test_complete_processing_trace(self, metadata_service):
        """Test complete processing trace lifecycle."""
        # Start document processing
        session_id = metadata_service.start_document_processing("/test/document.pdf")
        
        # Start processing steps
        step1_id = metadata_service.start_processing_step(
            session_id, "extraction", "extraction", {"input": "document_content"}
        )
        
        step2_id = metadata_service.start_processing_step(
            session_id, "validation", "validation", {"extracted_fields": "data"}
        )
        
        # Complete processing steps
        metadata_service.complete_processing_step(
            session_id, step1_id, 
            output_data={"extracted_fields": "test_data"},
            source_references=[
                SourceReference(
                    document_id="test_doc",
                    page_number=1,
                    section="extraction",
                    text_snippet="test snippet",
                    confidence=0.9
                )
            ]
        )
        
        metadata_service.complete_processing_step(
            session_id, step2_id,
            output_data={"validation_result": "passed"}
        )
        
        # Complete document processing
        trace = metadata_service.complete_document_processing(
            session_id,
            quality_metrics={"overall_score": 0.85},
            final_metadata={"processing_method": "enhanced_rag"}
        )
        
        # Verify trace
        assert trace.document_id is not None
        assert trace.status == "completed"
        assert len(trace.processing_steps) == 2
        assert len(trace.source_references) == 1
        assert trace.quality_metrics["overall_score"] == 0.85
        assert trace.total_duration_seconds > 0
    
    def test_processing_step_failure(self, metadata_service):
        """Test processing step failure handling."""
        session_id = metadata_service.start_document_processing("/test/document.pdf")
        step_id = metadata_service.start_processing_step(
            session_id, "extraction", "extraction"
        )
        
        # Fail the step
        metadata_service.fail_processing_step(
            session_id, step_id, "Extraction failed due to invalid format"
        )
        
        # Get trace
        trace = metadata_service.get_processing_trace(session_id)
        
        # Verify failed step
        failed_step = trace.processing_steps[0]
        assert failed_step.status == "failed"
        assert failed_step.error_message == "Extraction failed due to invalid format"
        assert failed_step.duration_seconds > 0
    
    def test_audit_report_generation(self, metadata_service):
        """Test audit report generation."""
        # Create and complete a processing trace
        session_id = metadata_service.start_document_processing("/test/document.pdf", "test_doc_123")
        step_id = metadata_service.start_processing_step(session_id, "test_step", "extraction")
        metadata_service.complete_processing_step(session_id, step_id)
        metadata_service.complete_document_processing(session_id)
        
        # Generate audit report
        report = metadata_service.generate_audit_report("test_doc_123")
        
        # Verify report structure
        assert 'report_generated_at' in report
        assert 'summary' in report
        assert 'processing_traces' in report
        assert 'source_reference_chains' in report
        assert 'performance_summary' in report
        
        # Verify report content
        assert len(report['processing_traces']) == 1
        assert report['processing_traces'][0]['document_id'] == "test_doc_123"
    
    def test_performance_metrics_tracking(self, metadata_service):
        """Test performance metrics tracking."""
        # Process multiple documents to generate metrics
        for i in range(3):
            session_id = metadata_service.start_document_processing(f"/test/doc_{i}.pdf")
            step_id = metadata_service.start_processing_step(session_id, "extraction", "extraction")
            metadata_service.complete_processing_step(session_id, step_id)
            metadata_service.complete_document_processing(session_id)
        
        # Get performance metrics
        metrics = metadata_service.get_performance_metrics()
        
        # Verify metrics
        assert metrics['total_documents_processed'] == 3
        assert metrics['average_processing_time'] > 0
        assert 'step_performance' in metrics
        assert 'extraction' in metrics['step_performance']
        assert metrics['step_performance']['extraction']['total_executions'] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])