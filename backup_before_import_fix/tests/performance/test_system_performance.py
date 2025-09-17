"""
Performance tests for the QME system.

This module contains performance and load tests to ensure the system
meets production performance requirements.
"""

import pytest
import asyncio
import time
import psutil
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.core.interfaces import ProcessingResult
from tests.conftest import TestDataFactory


class PerformanceTestSuite:
    """Performance testing utilities and benchmarks."""
    
    def __init__(self, benchmarks: Dict[str, float]):
        self.benchmarks = benchmarks
        self.results: List[Dict[str, Any]] = []
    
    def measure_execution_time(self, func, *args, **kwargs) -> tuple:
        """Measure execution time of a function."""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        execution_time = end_time - start_time
        memory_delta = end_memory - start_memory
        
        return result, execution_time, memory_delta
    
    async def measure_async_execution_time(self, coro) -> tuple:
        """Measure execution time of an async function."""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        result = await coro
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        execution_time = end_time - start_time
        memory_delta = end_memory - start_memory
        
        return result, execution_time, memory_delta
    
    def assert_performance(self, operation: str, execution_time: float, memory_delta: float = None):
        """Assert that performance meets benchmarks."""
        benchmark_time = self.benchmarks.get(f"{operation}_max_time")
        if benchmark_time:
            assert execution_time <= benchmark_time, (
                f"{operation} took {execution_time:.2f}s, "
                f"exceeds benchmark of {benchmark_time:.2f}s"
            )
        
        if memory_delta is not None:
            benchmark_memory = self.benchmarks.get("memory_usage_max_mb", 500.0)
            assert memory_delta <= benchmark_memory, (
                f"{operation} used {memory_delta:.2f}MB additional memory, "
                f"exceeds benchmark of {benchmark_memory:.2f}MB"
            )
        
        # Record result
        self.results.append({
            "operation": operation,
            "execution_time": execution_time,
            "memory_delta": memory_delta,
            "timestamp": time.time()
        })


@pytest.fixture
def performance_suite(performance_benchmarks) -> PerformanceTestSuite:
    """Create performance test suite."""
    return PerformanceTestSuite(performance_benchmarks)


@pytest.mark.benchmark
@pytest.mark.slow
class TestDocumentExtractionPerformance:
    """Performance tests for document extraction."""
    
    @pytest.mark.asyncio
    async def test_single_document_extraction_performance(
        self, 
        performance_suite: PerformanceTestSuite,
        mock_extraction_service,
        sample_document_path: Path
    ):
        """Test single document extraction performance."""
        
        result, execution_time, memory_delta = await performance_suite.measure_async_execution_time(
            mock_extraction_service.extract_fields(str(sample_document_path))
        )
        
        performance_suite.assert_performance("document_extraction", execution_time, memory_delta)
        
        assert result.success
        assert len(result.extracted_fields) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_document_extraction_performance(
        self,
        performance_suite: PerformanceTestSuite,
        mock_extraction_service,
        sample_document_path: Path
    ):
        """Test concurrent document extraction performance."""
        num_concurrent = 5
        
        async def extract_document():
            return await mock_extraction_service.extract_fields(str(sample_document_path))
        
        start_time = time.time()
        
        # Run concurrent extractions
        tasks = [extract_document() for _ in range(num_concurrent)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete all extractions faster than sequential processing
        sequential_time_estimate = performance_suite.benchmarks["document_extraction_max_time"] * num_concurrent
        assert total_time < sequential_time_estimate * 0.8, (
            f"Concurrent extraction took {total_time:.2f}s, "
            f"expected less than {sequential_time_estimate * 0.8:.2f}s"
        )
        
        # All extractions should succeed
        assert all(result.success for result in results)
    
    @pytest.mark.asyncio
    async def test_large_document_extraction_performance(
        self,
        performance_suite: PerformanceTestSuite,
        mock_extraction_service,
        temp_dir: Path
    ):
        """Test extraction performance with large documents."""
        
        # Create a large document (simulate 50-page document)
        large_doc_path = temp_dir / "large_document.txt"
        content = "Sample medical content. " * 10000  # Simulate large document
        large_doc_path.write_text(content)
        
        result, execution_time, memory_delta = await performance_suite.measure_async_execution_time(
            mock_extraction_service.extract_fields(str(large_doc_path))
        )
        
        # Large documents may take longer, but should still be reasonable
        performance_suite.assert_performance("document_extraction", execution_time, memory_delta)
        
        assert result.success


@pytest.mark.benchmark
@pytest.mark.slow
class TestValidationPerformance:
    """Performance tests for validation services."""
    
    @pytest.mark.asyncio
    async def test_validation_performance(
        self,
        performance_suite: PerformanceTestSuite,
        mock_validation_service,
        sample_extracted_fields: Dict[str, Any]
    ):
        """Test validation performance."""
        
        # Create mock extraction result
        extraction_result = type('ExtractionResult', (), {
            'success': True,
            'extracted_fields': sample_extracted_fields,
            'confidence_scores': {k: 0.9 for k in sample_extracted_fields.keys()}
        })()
        
        result, execution_time, memory_delta = await performance_suite.measure_async_execution_time(
            mock_validation_service.validate_extraction(extraction_result)
        )
        
        performance_suite.assert_performance("validation", execution_time, memory_delta)
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_batch_validation_performance(
        self,
        performance_suite: PerformanceTestSuite,
        mock_validation_service,
        sample_extracted_fields: Dict[str, Any]
    ):
        """Test batch validation performance."""
        
        batch_size = 10
        
        # Create multiple extraction results
        extraction_results = []
        for i in range(batch_size):
            result = type('ExtractionResult', (), {
                'success': True,
                'extracted_fields': {**sample_extracted_fields, 'id': i},
                'confidence_scores': {k: 0.9 for k in sample_extracted_fields.keys()}
            })()
            extraction_results.append(result)
        
        start_time = time.time()
        
        # Validate all results
        validation_tasks = [
            mock_validation_service.validate_extraction(result)
            for result in extraction_results
        ]
        results = await asyncio.gather(*validation_tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Batch validation should be efficient
        max_batch_time = performance_suite.benchmarks["validation_max_time"] * batch_size * 0.5
        assert total_time <= max_batch_time, (
            f"Batch validation took {total_time:.2f}s, "
            f"expected less than {max_batch_time:.2f}s"
        )
        
        assert all(result.success for result in results)


@pytest.mark.benchmark
@pytest.mark.slow
class TestTemplateGenerationPerformance:
    """Performance tests for template generation."""
    
    @pytest.mark.asyncio
    async def test_template_generation_performance(
        self,
        performance_suite: PerformanceTestSuite,
        mock_generation_service,
        sample_extracted_fields: Dict[str, Any]
    ):
        """Test template generation performance."""
        
        result, execution_time, memory_delta = await performance_suite.measure_async_execution_time(
            mock_generation_service.generate_content(sample_extracted_fields)
        )
        
        performance_suite.assert_performance("template_generation", execution_time, memory_delta)
        
        assert result.success
        assert result.generated_content is not None
    
    @pytest.mark.asyncio
    async def test_template_assembly_performance(
        self,
        performance_suite: PerformanceTestSuite,
        mock_generation_service,
        sample_extracted_fields: Dict[str, Any]
    ):
        """Test template assembly performance."""
        
        template_config = {
            "doctor_info": {
                "name": "Dr. Test",
                "license": "12345",
                "address": "123 Test St"
            },
            "formatting": {
                "font_family": "Times New Roman",
                "font_size": 12
            }
        }
        
        result, execution_time, memory_delta = await performance_suite.measure_async_execution_time(
            mock_generation_service.assemble_template(sample_extracted_fields, template_config)
        )
        
        performance_suite.assert_performance("template_generation", execution_time, memory_delta)
        
        assert result.success
        assert result.template_data is not None


@pytest.mark.benchmark
@pytest.mark.slow
class TestKnowledgeBasePerformance:
    """Performance tests for knowledge base queries."""
    
    @pytest.mark.asyncio
    async def test_knowledge_base_query_performance(
        self,
        performance_suite: PerformanceTestSuite,
        mock_knowledge_service
    ):
        """Test knowledge base query performance."""
        
        query = "What is the impairment rating for lumbar spine DRE Category II?"
        
        result, execution_time, memory_delta = await performance_suite.measure_async_execution_time(
            mock_knowledge_service.query_knowledge_base(query)
        )
        
        performance_suite.assert_performance("knowledge_base_query", execution_time, memory_delta)
        
        assert "answer" in result
        assert "sources" in result
    
    @pytest.mark.asyncio
    async def test_concurrent_knowledge_base_queries(
        self,
        performance_suite: PerformanceTestSuite,
        mock_knowledge_service
    ):
        """Test concurrent knowledge base query performance."""
        
        queries = [
            "What is DRE Category II?",
            "How to calculate ROM impairment?",
            "What are the AMA table requirements?",
            "How to determine work restrictions?",
            "What is the combined values chart?"
        ]
        
        start_time = time.time()
        
        # Run concurrent queries
        query_tasks = [
            mock_knowledge_service.query_knowledge_base(query)
            for query in queries
        ]
        results = await asyncio.gather(*query_tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Concurrent queries should be efficient
        max_concurrent_time = performance_suite.benchmarks["knowledge_base_query_max_time"] * len(queries) * 0.6
        assert total_time <= max_concurrent_time, (
            f"Concurrent queries took {total_time:.2f}s, "
            f"expected less than {max_concurrent_time:.2f}s"
        )
        
        assert all("answer" in result for result in results)


@pytest.mark.benchmark
@pytest.mark.slow
class TestEndToEndPerformance:
    """End-to-end performance tests."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_performance(
        self,
        performance_suite: PerformanceTestSuite,
        mock_extraction_service,
        mock_validation_service,
        mock_generation_service,
        sample_document_path: Path
    ):
        """Test complete workflow performance."""
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Step 1: Extract fields
        extraction_result = await mock_extraction_service.extract_fields(str(sample_document_path))
        assert extraction_result.success
        
        # Step 2: Validate extraction
        validation_result = await mock_validation_service.validate_extraction(extraction_result)
        assert validation_result.success
        
        # Step 3: Generate template
        generation_result = await mock_generation_service.generate_content(
            validation_result.accepted_fields
        )
        assert generation_result.success
        
        # Step 4: Assemble final template
        template_result = await mock_generation_service.assemble_template(
            generation_result.generated_content, {}
        )
        assert template_result.success
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        total_time = end_time - start_time
        memory_delta = end_memory - start_memory
        
        performance_suite.assert_performance("end_to_end", total_time, memory_delta)


@pytest.mark.benchmark
class TestLoadTesting:
    """Load testing for system scalability."""
    
    def test_concurrent_user_simulation(
        self,
        performance_suite: PerformanceTestSuite,
        mock_extraction_service,
        sample_document_path: Path
    ):
        """Simulate concurrent users processing documents."""
        
        num_users = 10
        documents_per_user = 3
        
        def simulate_user():
            """Simulate a single user's workflow."""
            user_results = []
            for _ in range(documents_per_user):
                start_time = time.time()
                
                # Simulate document processing (using sync version for threading)
                result = asyncio.run(mock_extraction_service.extract_fields(str(sample_document_path)))
                
                end_time = time.time()
                user_results.append({
                    'success': result.success,
                    'processing_time': end_time - start_time
                })
            
            return user_results
        
        start_time = time.time()
        
        # Run concurrent users
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(simulate_user) for _ in range(num_users)]
            all_results = []
            
            for future in as_completed(futures):
                user_results = future.result()
                all_results.extend(user_results)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate statistics
        processing_times = [r['processing_time'] for r in all_results]
        success_rate = sum(1 for r in all_results if r['success']) / len(all_results)
        
        avg_processing_time = statistics.mean(processing_times)
        p95_processing_time = statistics.quantiles(processing_times, n=20)[18]  # 95th percentile
        
        # Assertions
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95%"
        assert avg_processing_time <= performance_suite.benchmarks["document_extraction_max_time"], (
            f"Average processing time {avg_processing_time:.2f}s exceeds benchmark"
        )
        assert p95_processing_time <= performance_suite.benchmarks["document_extraction_max_time"] * 1.5, (
            f"95th percentile processing time {p95_processing_time:.2f}s too high"
        )
        
        print(f"\nLoad Test Results:")
        print(f"Total Users: {num_users}")
        print(f"Documents per User: {documents_per_user}")
        print(f"Total Processing Time: {total_time:.2f}s")
        print(f"Success Rate: {success_rate:.2%}")
        print(f"Average Processing Time: {avg_processing_time:.2f}s")
        print(f"95th Percentile Processing Time: {p95_processing_time:.2f}s")


@pytest.mark.benchmark
class TestMemoryUsage:
    """Memory usage and leak detection tests."""
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(
        self,
        mock_extraction_service,
        sample_document_path: Path
    ):
        """Test memory usage stability over multiple operations."""
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_readings = [initial_memory]
        
        # Perform multiple operations
        for i in range(20):
            await mock_extraction_service.extract_fields(str(sample_document_path))
            
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_readings.append(current_memory)
            
            # Force garbage collection periodically
            if i % 5 == 0:
                import gc
                gc.collect()
        
        final_memory = memory_readings[-1]
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 100MB for 20 operations)
        assert memory_growth <= 100, (
            f"Memory grew by {memory_growth:.2f}MB over 20 operations, "
            f"possible memory leak"
        )
        
        # Check for consistent memory usage (no continuous growth)
        recent_readings = memory_readings[-5:]
        memory_variance = statistics.variance(recent_readings)
        
        assert memory_variance <= 25, (
            f"Memory usage variance {memory_variance:.2f} too high, "
            f"indicates unstable memory usage"
        )


if __name__ == "__main__":
    # Run performance tests
    pytest.main([
        __file__,
        "-v",
        "--benchmark-only",
        "--benchmark-sort=mean",
        "--benchmark-columns=min,max,mean,stddev,median,iqr,outliers,ops,rounds,iterations"
    ])