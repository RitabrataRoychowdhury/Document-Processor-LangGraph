"""Comprehensive integration tests for refactored workflow components."""

import pytest
import tempfile
import os
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.workflow.workflow_manager import RefactoredWorkflowManager, WorkflowManager
from src.workflow.base.workflow_graph import WorkflowGraph, GraphResult
from src.workflow.base.workflow_node import WorkflowNode, NodeResult
from src.workflow.base.state_manager import StateManager
from src.workflow.state.workflow_state import WorkflowStateFactory
from src.workflow.state.document_state import DocumentState
from src.workflow.state.template_state import TemplateState
from src.workflow.nodes.extraction_node import ExtractionNode
from src.workflow.nodes.ner_node import NERNode
from src.workflow.nodes.embedding_node import EmbeddingNode
from src.workflow.nodes.kg_population_node import KGPopulationNode
from src.workflow.nodes.template_generation_node import TemplateGenerationNode
from src.workflow.graphs.document_processing_graph import DocumentProcessingGraph
from src.workflow.graphs.qme_generation_graph import QMEGenerationGraph
from src.workflow.graphs.knowledge_graph_population_graph import KnowledgeGraphPopulationGraph
from src.workflow.factories.node_factory import NodeFactory
from src.factories.processor_factory import ProcessorFactory
from src.strategies.embedding_strategy import LocalEmbeddingStrategy
from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository
from src.storage.document_storage import DocumentStorage
from src.services.qme_template_generator import QMETemplateGenerator


class TestRefactoredWorkflowComponents:
    """Test suite for refactored workflow components."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for testing."""
        return {
            'processor_factory': Mock(spec=ProcessorFactory),
            'embedding_strategy': Mock(spec=LocalEmbeddingStrategy),
            'kg_repository': Mock(spec=KnowledgeGraphRepository),
            'storage': Mock(spec=DocumentStorage),
            'template_generator': Mock(spec=QMETemplateGenerator),
            'node_factory': Mock(spec=NodeFactory)
        }
    
    @pytest.fixture
    def temp_file(self):
        """Create a temporary test file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document with medical content. Patient John Doe has lumbar spine issues.")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    def test_workflow_state_factory(self):
        """Test workflow state factory creates correct state types."""
        # Test general workflow state
        general_state = WorkflowStateFactory.create_workflow_state("general")
        assert isinstance(general_state, WorkflowStateFactory.create_workflow_state("general").__class__)
        
        # Test document workflow state
        document_state = WorkflowStateFactory.create_workflow_state("document")
        assert isinstance(document_state, DocumentState)
        
        # Test template workflow state
        template_state = WorkflowStateFactory.create_workflow_state("template")
        assert isinstance(template_state, TemplateState)
        
        # Test supported types
        supported_types = WorkflowStateFactory.get_supported_types()
        assert "general" in supported_types
        assert "document" in supported_types
        assert "template" in supported_types
    
    def test_document_state_lifecycle(self):
        """Test document state management lifecycle."""
        state = DocumentState()
        
        # Test initialization
        initial_data = {
            'document_id': 'test_doc_123',
            'file_path': '/test/path.pdf',
            'file_type': 'pdf',
            'file_size': 1024
        }
        
        state.initialize_state(initial_data)
        
        assert state.get_value('document_id') == 'test_doc_123'
        assert state.get_value('file_path') == '/test/path.pdf'
        assert state.get_value('processing_stage') == 'initialization'
        
        # Test text extraction stage
        state.start_text_extraction()
        assert state.get_value('processing_stage') == 'text_extraction'
        
        state.complete_text_extraction("Extracted text content", {'pages': 5})
        assert state.get_value('processing_stage') == 'text_extraction_complete'
        assert state.get_value('extracted_text') == "Extracted text content"
        assert state.is_text_extracted()
        
        # Test entity recognition stage
        state.start_entity_recognition()
        entities = [{'type': 'patient', 'text': 'John Doe'}]
        state.complete_entity_recognition(entities)
        assert state.is_entities_extracted()
        assert len(state.get_extracted_entities()) == 1
        
        # Test error handling
        state.add_processing_error('test_stage', 'Test error message')
        assert state.has_processing_errors()
        errors = state.get_processing_errors()
        assert len(errors) == 1
        assert errors[0]['error_message'] == 'Test error message'
    
    def test_template_state_lifecycle(self):
        """Test template state management lifecycle."""
        state = TemplateState()
        
        # Test initialization
        initial_data = {
            'patient_document_id': 'patient_doc_123',
            'patient_file_path': '/test/patient.pdf',
            'template_type': 'qme_report'
        }
        
        state.initialize_state(initial_data)
        
        assert state.get_value('patient_document_id') == 'patient_doc_123'
        assert state.get_value('template_type') == 'qme_report'
        
        # Test patient info extraction
        state.start_patient_info_extraction()
        patient_info = {'name': 'John Doe', 'age': 45}
        state.complete_patient_info_extraction(patient_info)
        assert state.is_patient_info_extracted()
        assert state.get_patient_info()['name'] == 'John Doe'
        
        # Test diagnosis identification
        state.start_diagnosis_identification()
        diagnoses = [{'description': 'Lumbar spine injury', 'confidence': 0.9}]
        state.complete_diagnosis_identification(diagnoses)
        assert state.is_diagnoses_identified()
        assert len(state.get_diagnoses()) == 1
        
        # Test missing information tracking
        state.add_missing_information('patient_info', ['date_of_birth', 'insurance'])
        assert state.has_missing_information()
        missing = state.get_missing_information()
        assert len(missing) == 2
    
    def test_node_dependency_injection(self, mock_dependencies):
        """Test that nodes properly use dependency injection."""
        # Test ExtractionNode requires ProcessorFactory
        with pytest.raises(ValueError, match="ProcessorFactory must be provided"):
            ExtractionNode()
        
        # Test with proper dependency injection
        extraction_node = ExtractionNode(
            processor_factory=mock_dependencies['processor_factory']
        )
        assert extraction_node.processor_factory == mock_dependencies['processor_factory']
        
        # Test EmbeddingNode requires EmbeddingStrategy
        with pytest.raises(ValueError, match="EmbeddingStrategy must be provided"):
            EmbeddingNode()
        
        embedding_node = EmbeddingNode(
            embedding_strategy=mock_dependencies['embedding_strategy']
        )
        assert embedding_node.embedding_strategy == mock_dependencies['embedding_strategy']
        
        # Test KGPopulationNode requires KnowledgeGraphRepository
        with pytest.raises(ValueError, match="KnowledgeGraphRepository must be provided"):
            KGPopulationNode()
        
        kg_node = KGPopulationNode(
            kg_repository=mock_dependencies['kg_repository']
        )
        assert kg_node.kg_repository == mock_dependencies['kg_repository']
        
        # Test TemplateGenerationNode requires both dependencies
        with pytest.raises(ValueError, match="QMETemplateGenerator must be provided"):
            TemplateGenerationNode()
        
        with pytest.raises(ValueError, match="KnowledgeGraphRepository must be provided"):
            TemplateGenerationNode(template_generator=mock_dependencies['template_generator'])
        
        template_node = TemplateGenerationNode(
            template_generator=mock_dependencies['template_generator'],
            kg_repository=mock_dependencies['kg_repository']
        )
        assert template_node.template_generator == mock_dependencies['template_generator']
        assert template_node.kg_repository == mock_dependencies['kg_repository']
    
    def test_node_execution_with_retry(self, mock_dependencies):
        """Test node execution with retry logic."""
        # Create a mock node that fails first time, succeeds second time
        class TestNode(WorkflowNode):
            def __init__(self):
                super().__init__()
                self.attempt_count = 0
            
            def execute(self, state):
                self.attempt_count += 1
                if self.attempt_count == 1:
                    raise Exception("Temporary failure")
                return NodeResult.success_result("Success on retry")
            
            def validate_input(self, state):
                return True
            
            def get_required_inputs(self):
                return []
            
            def get_output_keys(self):
                return ['test_output']
        
        node = TestNode()
        result = node.execute_with_retry({'test': 'data'}, max_attempts=3)
        
        assert result.success
        assert result.retry_count == 1
        assert "Success on retry" in result.message
    
    def test_graph_execution_flow(self, mock_dependencies):
        """Test graph execution with proper flow control."""
        # Create a simple test graph
        class TestGraph(WorkflowGraph):
            def build_graph(self):
                # Create mock nodes
                node1 = Mock(spec=WorkflowNode)
                node1.node_id = "node1"
                node1.execute_with_retry.return_value = NodeResult.success_result(
                    "Node 1 success", {'node1_output': 'data1'}
                )
                
                node2 = Mock(spec=WorkflowNode)
                node2.node_id = "node2"
                node2.execute_with_retry.return_value = NodeResult.success_result(
                    "Node 2 success", {'node2_output': 'data2'}
                )
                
                self.add_node(node1)
                self.add_node(node2)
                self.add_edge("node1", "node2")
                self.set_entry_point("node1")
                self.set_exit_point("node2")
            
            def validate_graph(self):
                return True
        
        graph = TestGraph()
        result = graph.execute({'initial': 'state'})
        
        assert result.success
        assert result.nodes_executed == 2
        assert 'node1_output' in result.final_state
        assert 'node2_output' in result.final_state
    
    def test_refactored_workflow_manager_document_processing(self, mock_dependencies, temp_file):
        """Test refactored workflow manager document processing."""
        manager = RefactoredWorkflowManager(
            storage=mock_dependencies['storage'],
            processor_factory=mock_dependencies['processor_factory'],
            kg_repository=mock_dependencies['kg_repository'],
            node_factory=mock_dependencies['node_factory']
        )
        
        # Mock the graph execution
        with patch('src.workflow.graphs.document_processing_graph.DocumentProcessingGraph') as mock_graph_class:
            mock_graph = Mock()
            mock_graph.graph_id = "test_graph_123"
            mock_graph.execute.return_value = GraphResult.success_result(
                "Document processing completed",
                final_state={'document_id': 'doc_123', 'processed': True},
                execution_time=5.0,
                nodes_executed=4
            )
            mock_graph_class.return_value = mock_graph
            
            result = manager.execute_document_processing_graph(temp_file)
            
            assert result.success
            assert result.nodes_executed == 4
            assert 'document_id' in result.final_state
            
            # Check that observers were added
            assert mock_graph.add_observer.call_count == len(manager.graph_observers)
    
    def test_refactored_workflow_manager_qme_generation(self, mock_dependencies):
        """Test refactored workflow manager QME generation."""
        manager = RefactoredWorkflowManager(
            storage=mock_dependencies['storage'],
            processor_factory=mock_dependencies['processor_factory'],
            kg_repository=mock_dependencies['kg_repository'],
            node_factory=mock_dependencies['node_factory']
        )
        
        # Mock the graph execution
        with patch('src.workflow.graphs.qme_generation_graph.QMEGenerationGraph') as mock_graph_class:
            mock_graph = Mock()
            mock_graph.graph_id = "qme_graph_123"
            mock_graph.execute.return_value = GraphResult.success_result(
                "QME generation completed",
                final_state={'template_path': '/output/template.docx', 'generated': True},
                execution_time=3.0,
                nodes_executed=3
            )
            mock_graph_class.return_value = mock_graph
            
            result = manager.execute_qme_generation_graph("patient_doc_123")
            
            assert result.success
            assert result.nodes_executed == 3
            assert 'template_path' in result.final_state
    
    def test_backward_compatibility_wrapper(self, mock_dependencies, temp_file):
        """Test that the backward compatibility wrapper works correctly."""
        manager = WorkflowManager(
            storage=mock_dependencies['storage'],
            processor_factory=mock_dependencies['processor_factory'],
            kg_repository=mock_dependencies['kg_repository']
        )
        
        # Mock the graph execution in the parent class
        with patch.object(manager, 'execute_document_processing_graph') as mock_execute:
            mock_execute.return_value = GraphResult.success_result("Success")
            
            job_id = manager.submit_document_for_processing(temp_file)
            
            assert job_id is not None
            assert len(job_id) > 0
            
            # Should have called the graph-based execution
            # (Note: This test might need adjustment based on threading implementation)
    
    def test_execution_metrics_tracking(self, mock_dependencies):
        """Test that execution metrics are properly tracked."""
        manager = RefactoredWorkflowManager(
            storage=mock_dependencies['storage'],
            processor_factory=mock_dependencies['processor_factory'],
            kg_repository=mock_dependencies['kg_repository'],
            node_factory=mock_dependencies['node_factory']
        )
        
        # Simulate successful execution
        success_result = GraphResult.success_result("Success", execution_time=2.5)
        manager._update_execution_metrics(success_result)
        
        # Simulate failed execution
        failure_result = GraphResult.failure_result("Failure", execution_time=1.0)
        manager._update_execution_metrics(failure_result)
        
        metrics = manager.get_execution_metrics()
        
        assert metrics['graphs_executed'] == 2
        assert metrics['successful_executions'] == 1
        assert metrics['failed_executions'] == 1
        assert metrics['average_execution_time'] == 1.75  # (2.5 + 1.0) / 2
    
    def test_graph_status_monitoring(self, mock_dependencies):
        """Test graph status monitoring capabilities."""
        manager = RefactoredWorkflowManager(
            storage=mock_dependencies['storage'],
            processor_factory=mock_dependencies['processor_factory'],
            kg_repository=mock_dependencies['kg_repository'],
            node_factory=mock_dependencies['node_factory']
        )
        
        # Create a mock active graph
        mock_graph = Mock()
        mock_graph.graph_id = "active_graph_123"
        mock_graph.__class__.__name__ = "TestGraph"
        mock_graph.get_graph_info.return_value = {'nodes': {}, 'edges': {}}
        
        mock_state = Mock()
        mock_state.get_state_info.return_value = {'state_id': 'state_123'}
        mock_state.get_workflow_summary.return_value = {'status': 'active'}
        
        manager.active_graphs["active_graph_123"] = mock_graph
        manager.state_managers["active_graph_123"] = mock_state
        
        # Test active graph status
        status = manager.get_graph_status("active_graph_123")
        assert status is not None
        assert status['graph_id'] == "active_graph_123"
        assert status['status'] == 'running'
        assert 'graph_info' in status
        assert 'state_info' in status
        
        # Test completed graph status
        completed_result = GraphResult.success_result("Completed", execution_time=5.0)
        manager.graph_results["completed_graph_456"] = completed_result
        
        status = manager.get_graph_status("completed_graph_456")
        assert status is not None
        assert status['status'] == 'completed'
        assert status['result']['success'] is True
        
        # Test non-existent graph
        status = manager.get_graph_status("non_existent")
        assert status is None
    
    def test_workflow_visualization_data(self, mock_dependencies):
        """Test workflow visualization data generation."""
        manager = RefactoredWorkflowManager(
            storage=mock_dependencies['storage'],
            processor_factory=mock_dependencies['processor_factory'],
            kg_repository=mock_dependencies['kg_repository'],
            node_factory=mock_dependencies['node_factory']
        )
        
        # Create a mock graph with visualization data
        mock_graph = Mock()
        mock_graph.graph_id = "viz_graph_123"
        mock_graph.__class__.__name__ = "DocumentProcessingGraph"
        mock_graph.edges = {"node1": ["node2"], "node2": ["node3"]}
        mock_graph.entry_points = ["node1"]
        mock_graph.exit_points = {"node3"}
        mock_graph.get_graph_info.return_value = {
            'nodes': {
                'node1': {'type': 'ExtractionNode'},
                'node2': {'type': 'NERNode'},
                'node3': {'type': 'EmbeddingNode'}
            }
        }
        
        manager.active_graphs["viz_graph_123"] = mock_graph
        
        viz_data = manager.get_workflow_visualization("viz_graph_123")
        
        assert viz_data is not None
        assert viz_data['graph_id'] == "viz_graph_123"
        assert viz_data['graph_type'] == "DocumentProcessingGraph"
        assert 'nodes' in viz_data
        assert 'edges' in viz_data
        assert viz_data['entry_points'] == ["node1"]
        assert viz_data['exit_points'] == ["node3"]
    
    def test_error_handling_and_recovery(self, mock_dependencies):
        """Test error handling and recovery mechanisms."""
        manager = RefactoredWorkflowManager(
            storage=mock_dependencies['storage'],
            processor_factory=mock_dependencies['processor_factory'],
            kg_repository=mock_dependencies['kg_repository'],
            node_factory=mock_dependencies['node_factory']
        )
        
        # Test graph execution error handling
        with patch('src.workflow.graphs.document_processing_graph.DocumentProcessingGraph') as mock_graph_class:
            mock_graph_class.side_effect = Exception("Graph creation failed")
            
            result = manager.execute_document_processing_graph("/test/file.pdf")
            
            assert not result.success
            assert "Graph execution error" in result.message
            
            # Check that metrics were updated for the failure
            metrics = manager.get_execution_metrics()
            assert metrics['failed_executions'] >= 1
    
    def test_performance_monitoring(self, mock_dependencies):
        """Test performance monitoring capabilities."""
        manager = RefactoredWorkflowManager(
            storage=mock_dependencies['storage'],
            processor_factory=mock_dependencies['processor_factory'],
            kg_repository=mock_dependencies['kg_repository'],
            node_factory=mock_dependencies['node_factory']
        )
        
        # Simulate multiple executions with different performance characteristics
        fast_result = GraphResult.success_result("Fast execution", execution_time=1.0)
        slow_result = GraphResult.success_result("Slow execution", execution_time=10.0)
        failed_result = GraphResult.failure_result("Failed execution", execution_time=5.0)
        
        manager._update_execution_metrics(fast_result)
        manager._update_execution_metrics(slow_result)
        manager._update_execution_metrics(failed_result)
        
        metrics = manager.get_execution_metrics()
        
        assert metrics['graphs_executed'] == 3
        assert metrics['successful_executions'] == 2
        assert metrics['failed_executions'] == 1
        
        # Average should be (1.0 + 10.0 + 5.0) / 3 = 5.33...
        assert abs(metrics['average_execution_time'] - 5.333333333333333) < 0.001
    
    def test_state_persistence_and_recovery(self):
        """Test state persistence and recovery mechanisms."""
        # Test state snapshot creation and restoration
        state = DocumentState()
        
        initial_data = {
            'document_id': 'test_doc',
            'file_path': '/test/path.pdf',
            'file_type': 'pdf',
            'file_size': 1024
        }
        
        state.initialize_state(initial_data)
        
        # Create a snapshot
        snapshot_id = state.create_snapshot({'reason': 'before_processing'})
        assert snapshot_id is not None
        
        # Modify state
        state.update_state({'processing_stage': 'modified', 'new_field': 'new_value'})
        assert state.get_value('processing_stage') == 'modified'
        assert state.get_value('new_field') == 'new_value'
        
        # Restore from snapshot
        restored = state.restore_snapshot(snapshot_id)
        assert restored is True
        assert state.get_value('processing_stage') == 'initialization'
        assert state.get_value('new_field') is None
        
        # Test snapshot retrieval
        snapshot = state.get_snapshot(snapshot_id)
        assert snapshot is not None
        assert snapshot.snapshot_id == snapshot_id
        assert 'reason' in snapshot.metadata
    
    @pytest.mark.integration
    def test_end_to_end_document_processing_workflow(self, mock_dependencies, temp_file):
        """Integration test for complete document processing workflow."""
        # This test requires more setup and mocking of the entire pipeline
        # It's marked as integration test and can be run separately
        
        # Setup mocks for the entire pipeline
        mock_processor = Mock()
        mock_processor.extract_text.return_value = "Sample medical text with patient John Doe"
        mock_processor.extract_metadata.return_value = {'pages': 1}
        
        mock_dependencies['processor_factory'].create_processor.return_value = mock_processor
        mock_dependencies['embedding_strategy'].generate_embeddings.return_value = [0.1, 0.2, 0.3]
        mock_dependencies['kg_repository'].create_node.return_value = "node_123"
        mock_dependencies['kg_repository'].create_relationship.return_value = "rel_123"
        
        manager = RefactoredWorkflowManager(**mock_dependencies)
        
        # This would be a full integration test with real graph execution
        # For now, we'll test the setup and basic flow
        assert manager.processor_factory == mock_dependencies['processor_factory']
        assert manager.embedding_strategy == mock_dependencies['embedding_strategy']
        assert manager.kg_repository == mock_dependencies['kg_repository']
        
        # Test queue status
        status = manager.get_queue_status()
        assert 'active_graphs' in status
        assert 'execution_metrics' in status
        assert status['running'] is False  # Not started yet


if __name__ == "__main__":
    pytest.main([__file__, "-v"])