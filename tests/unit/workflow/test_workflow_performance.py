"""Performance tests for refactored workflow components."""

import pytest
import time
import tempfile
import os
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.workflow.workflow_manager import RefactoredWorkflowManager, WorkflowManager
from src.workflow.base.workflow_graph import GraphResult
from src.workflow.state.document_state import DocumentState
from src.workflow.nodes.extraction_node import ExtractionNode
from src.workflow.nodes.ner_node import NERNode
from src.workflow.nodes.embedding_node import EmbeddingNode
from src.factories.processor_factory import ProcessorFactory
from src.strategies.embedding_strategy import LocalEmbeddingStrategy


class TestWorkflowPerformance:
    """Performance tests for workflow components."""
    
    @pytest.fixture
    def sample_text(self):
        """Generate sample medical text for testing."""
        return """
        QUALIFIED MEDICAL EVALUATOR'S REPORT
        
        Patient: John Doe
        Date of Birth: 01/15/1980
        Case Number: WC-2023-001234
        Date of Injury: 03/20/2023
        
        HISTORY OF PRESENT ILLNESS:
        The patient is a 43-year-old male who sustained an injury to his lumbar spine 
        while lifting heavy boxes at work on March 20, 2023. He reports immediate onset 
        of lower back pain radiating down his left leg. The pain is described as sharp 
        and burning, rated 8/10 in intensity.
        
        PHYSICAL EXAMINATION:
        General appearance: The patient appears in mild distress due to pain.
        Vital signs: BP 130/80, HR 72, RR 16, Temp 98.6°F
        
        Lumbar spine examination reveals:
        - Limited range of motion in flexion and extension
        - Positive straight leg raise test on the left at 45 degrees
        - Tenderness over L4-L5 region
        - Muscle spasm in paraspinal muscles
        
        DIAGNOSIS:
        1. Lumbar disc herniation at L4-L5 level
        2. Lumbar radiculopathy, left-sided
        3. Chronic lower back pain
        
        IMPAIRMENT RATING:
        Based on AMA Guides 5th Edition, Table 15-3, the patient has a 15% whole person 
        impairment rating for lumbar spine dysfunction.
        
        RECOMMENDATIONS:
        1. Continue physical therapy
        2. Consider epidural steroid injection
        3. Work restrictions: No lifting over 20 pounds
        """ * 10  # Multiply to create larger text for performance testing
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies optimized for performance testing."""
        processor_factory = Mock(spec=ProcessorFactory)
        embedding_strategy = Mock(spec=LocalEmbeddingStrategy)
        kg_repository = Mock()
        storage = Mock()
        template_generator = Mock()
        
        # Configure mocks for fast responses
        mock_processor = Mock()
        mock_processor.extract_text.return_value = "Fast extracted text"
        mock_processor.extract_metadata.return_value = {'pages': 1}
        processor_factory.create_processor.return_value = mock_processor
        
        embedding_strategy.generate_embeddings.return_value = [0.1] * 384  # Typical embedding size
        
        kg_repository.create_node.return_value = "node_123"
        kg_repository.create_relationship.return_value = "rel_123"
        
        return {
            'processor_factory': processor_factory,
            'embedding_strategy': embedding_strategy,
            'kg_repository': kg_repository,
            'storage': storage,
            'template_generator': template_generator
        }
    
    def test_state_manager_performance(self, sample_text):
        """Test state manager performance with large state data."""
        state = DocumentState()
        
        # Test initialization performance
        start_time = time.time()
        
        initial_data = {
            'document_id': 'perf_test_doc',
            'file_path': '/test/large_document.pdf',
            'file_type': 'pdf',
            'file_size': len(sample_text),
            'extracted_text': sample_text
        }
        
        state.initialize_state(initial_data)
        init_time = time.time() - start_time
        
        # Should initialize quickly even with large text
        assert init_time < 0.1, f"State initialization took {init_time:.3f}s, expected < 0.1s"
        
        # Test multiple state updates performance
        start_time = time.time()
        
        for i in range(100):
            state.update_state({f'update_{i}': f'value_{i}'}, create_snapshot=False)
        
        update_time = time.time() - start_time
        
        # Should handle 100 updates quickly
        assert update_time < 0.5, f"100 state updates took {update_time:.3f}s, expected < 0.5s"
        
        # Test snapshot creation performance
        start_time = time.time()
        
        for i in range(10):
            state.create_snapshot({'iteration': i})
        
        snapshot_time = time.time() - start_time
        
        # Should create 10 snapshots quickly
        assert snapshot_time < 0.2, f"10 snapshots took {snapshot_time:.3f}s, expected < 0.2s"
    
    def test_node_execution_performance(self, mock_dependencies, sample_text):
        """Test individual node execution performance."""
        # Test NER Node performance
        ner_node = NERNode()
        
        state = {
            'extracted_text': sample_text,
            'correlation_id': 'perf_test'
        }
        
        start_time = time.time()
        result = ner_node.execute(state)
        ner_time = time.time() - start_time
        
        assert result.success
        # NER should complete within reasonable time for large text
        assert ner_time < 2.0, f"NER took {ner_time:.3f}s, expected < 2.0s"
        
        # Test Embedding Node performance
        embedding_node = EmbeddingNode(
            embedding_strategy=mock_dependencies['embedding_strategy']
        )
        
        # Add entities to state
        state['entities_extracted'] = result.data.get('entities_extracted', [])
        
        start_time = time.time()
        result = embedding_node.execute(state)
        embedding_time = time.time() - start_time
        
        assert result.success
        # Embedding generation should be fast with mocked strategy
        assert embedding_time < 1.0, f"Embedding took {embedding_time:.3f}s, expected < 1.0s"
    
    def test_graph_execution_performance(self, mock_dependencies):
        """Test graph execution performance."""
        manager = RefactoredWorkflowManager(**mock_dependencies)
        
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Performance test document content")
            temp_path = f.name
        
        try:
            # Mock the graph execution to return quickly
            with patch('src.workflow.graphs.document_processing_graph.DocumentProcessingGraph') as mock_graph_class:
                mock_graph = Mock()
                mock_graph.graph_id = "perf_graph"
                
                # Simulate realistic execution time
                def mock_execute(state):
                    time.sleep(0.1)  # Simulate some processing time
                    return GraphResult.success_result(
                        "Performance test completed",
                        final_state={'processed': True},
                        execution_time=0.1,
                        nodes_executed=4
                    )
                
                mock_graph.execute = mock_execute
                mock_graph_class.return_value = mock_graph
                
                # Test single execution performance
                start_time = time.time()
                result = manager.execute_document_processing_graph(temp_path)
                single_execution_time = time.time() - start_time
                
                assert result.success
                # Should complete quickly with mocked components
                assert single_execution_time < 1.0, f"Single execution took {single_execution_time:.3f}s"
                
                # Test concurrent execution performance
                start_time = time.time()
                
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = []
                    for i in range(10):
                        future = executor.submit(manager.execute_document_processing_graph, temp_path)
                        futures.append(future)
                    
                    results = []
                    for future in as_completed(futures):
                        results.append(future.result())
                
                concurrent_execution_time = time.time() - start_time
                
                # All executions should succeed
                assert all(r.success for r in results)
                assert len(results) == 10
                
                # Concurrent execution should be faster than sequential
                expected_sequential_time = single_execution_time * 10
                assert concurrent_execution_time < expected_sequential_time * 0.8, \
                    f"Concurrent execution took {concurrent_execution_time:.3f}s, " \
                    f"expected < {expected_sequential_time * 0.8:.3f}s"
        
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_memory_usage_performance(self, mock_dependencies, sample_text):
        """Test memory usage during workflow execution."""
        import psutil
        import gc
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        manager = RefactoredWorkflowManager(**mock_dependencies)
        
        # Execute multiple workflows to test memory usage
        for i in range(20):
            state = DocumentState()
            state.initialize_state({
                'document_id': f'mem_test_{i}',
                'file_path': f'/test/doc_{i}.pdf',
                'file_type': 'pdf',
                'file_size': len(sample_text),
                'extracted_text': sample_text
            })
            
            # Simulate processing
            state.start_text_extraction()
            state.complete_text_extraction(sample_text)
            
            entities = [{'type': 'test', 'text': f'entity_{j}'} for j in range(50)]
            state.start_entity_recognition()
            state.complete_entity_recognition(entities)
            
            # Force garbage collection
            if i % 5 == 0:
                gc.collect()
        
        # Check final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100, f"Memory increased by {memory_increase:.1f}MB, expected < 100MB"
    
    def test_backward_compatibility_performance(self, mock_dependencies):
        """Test that backward compatibility wrapper doesn't significantly impact performance."""
        # Test new refactored manager
        refactored_manager = RefactoredWorkflowManager(**mock_dependencies)
        
        # Test backward compatible manager
        compatible_manager = WorkflowManager(
            storage=mock_dependencies['storage'],
            processor_factory=mock_dependencies['processor_factory'],
            kg_repository=mock_dependencies['kg_repository']
        )
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Compatibility test document")
            temp_path = f.name
        
        try:
            # Mock graph execution for both managers
            with patch('src.workflow.graphs.document_processing_graph.DocumentProcessingGraph') as mock_graph_class:
                mock_graph = Mock()
                mock_graph.graph_id = "compat_graph"
                mock_graph.execute.return_value = GraphResult.success_result(
                    "Compatibility test completed",
                    execution_time=0.05
                )
                mock_graph_class.return_value = mock_graph
                
                # Test refactored manager performance
                start_time = time.time()
                refactored_result = refactored_manager.execute_document_processing_graph(temp_path)
                refactored_time = time.time() - start_time
                
                # Test compatible manager performance (using graph execution internally)
                with patch.object(compatible_manager, 'execute_document_processing_graph') as mock_execute:
                    mock_execute.return_value = GraphResult.success_result("Success")
                    
                    start_time = time.time()
                    job_id = compatible_manager.submit_document_for_processing(temp_path)
                    compatible_time = time.time() - start_time
                
                # Both should succeed
                assert refactored_result.success
                assert job_id is not None
                
                # Performance should be similar (compatible wrapper shouldn't add significant overhead)
                # Note: This test might need adjustment based on threading implementation
                assert compatible_time < refactored_time * 2, \
                    f"Compatible wrapper took {compatible_time:.3f}s vs refactored {refactored_time:.3f}s"
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_large_document_processing_performance(self, mock_dependencies):
        """Test performance with large documents (simulating 50-page PDF)."""
        # Create large sample text (simulating 50-page document)
        large_text = """
        This is a sample page of medical documentation. It contains patient information,
        medical history, examination findings, diagnoses, and treatment recommendations.
        The document includes various medical entities such as patient names, dates,
        body parts, diagnoses, and impairment ratings that need to be extracted and
        processed by the workflow system.
        """ * 1000  # Simulate large document
        
        # Test NER performance on large document
        ner_node = NERNode()
        
        state = {
            'extracted_text': large_text,
            'correlation_id': 'large_doc_test'
        }
        
        start_time = time.time()
        result = ner_node.execute(state)
        ner_time = time.time() - start_time
        
        assert result.success
        # Should process large document within target time (30 seconds as per requirements)
        assert ner_time < 30.0, f"Large document NER took {ner_time:.3f}s, expected < 30.0s"
        
        # Test embedding performance on large document
        embedding_node = EmbeddingNode(
            embedding_strategy=mock_dependencies['embedding_strategy']
        )
        
        state['entities_extracted'] = result.data.get('entities_extracted', [])
        
        start_time = time.time()
        embedding_result = embedding_node.execute(state)
        embedding_time = time.time() - start_time
        
        assert embedding_result.success
        # Embedding should also complete within reasonable time
        assert embedding_time < 10.0, f"Large document embedding took {embedding_time:.3f}s, expected < 10.0s"
        
        # Test total processing time
        total_time = ner_time + embedding_time
        assert total_time < 30.0, f"Total large document processing took {total_time:.3f}s, expected < 30.0s"
    
    def test_concurrent_workflow_performance(self, mock_dependencies):
        """Test performance under concurrent workflow execution."""
        manager = RefactoredWorkflowManager(**mock_dependencies)
        
        # Create multiple test files
        test_files = []
        for i in range(10):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f"Concurrent test document {i}")
                test_files.append(f.name)
        
        try:
            # Mock graph execution
            with patch('src.workflow.graphs.document_processing_graph.DocumentProcessingGraph') as mock_graph_class:
                def create_mock_graph():
                    mock_graph = Mock()
                    mock_graph.graph_id = f"concurrent_graph_{time.time()}"
                    mock_graph.execute.return_value = GraphResult.success_result(
                        "Concurrent test completed",
                        execution_time=0.1,
                        nodes_executed=3
                    )
                    return mock_graph
                
                mock_graph_class.side_effect = create_mock_graph
                
                # Test concurrent execution
                start_time = time.time()
                
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = []
                    for file_path in test_files:
                        future = executor.submit(manager.execute_document_processing_graph, file_path)
                        futures.append(future)
                    
                    results = []
                    for future in as_completed(futures):
                        results.append(future.result())
                
                concurrent_time = time.time() - start_time
                
                # All executions should succeed
                assert all(r.success for r in results)
                assert len(results) == 10
                
                # Concurrent execution should complete within reasonable time
                assert concurrent_time < 5.0, f"Concurrent execution took {concurrent_time:.3f}s, expected < 5.0s"
                
                # Check that metrics were properly updated
                metrics = manager.get_execution_metrics()
                assert metrics['graphs_executed'] >= 10
                assert metrics['successful_executions'] >= 10
        
        finally:
            # Cleanup
            for file_path in test_files:
                if os.path.exists(file_path):
                    os.unlink(file_path)
    
    @pytest.mark.benchmark
    def test_workflow_benchmark(self, mock_dependencies, benchmark):
        """Benchmark test for workflow execution (requires pytest-benchmark)."""
        manager = RefactoredWorkflowManager(**mock_dependencies)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Benchmark test document")
            temp_path = f.name
        
        try:
            with patch('src.workflow.graphs.document_processing_graph.DocumentProcessingGraph') as mock_graph_class:
                mock_graph = Mock()
                mock_graph.graph_id = "benchmark_graph"
                mock_graph.execute.return_value = GraphResult.success_result(
                    "Benchmark completed",
                    execution_time=0.05
                )
                mock_graph_class.return_value = mock_graph
                
                # Benchmark the execution
                result = benchmark(manager.execute_document_processing_graph, temp_path)
                assert result.success
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])