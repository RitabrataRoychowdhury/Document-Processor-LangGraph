#!/usr/bin/env python3
"""
Minimal test for Evidence-First QME Workflow Manager imports

This script tests only the core imports without dependencies that may not be available.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_core_imports():
    """Test core imports without external dependencies."""
    try:
        print("Testing core Evidence-First QME Workflow Manager imports...")
        
        # Test enum imports first
        print("1. Testing enum imports...")
        from src.workflow.evidence_first_workflow_manager import (
            PipelineStatus,
            WorkflowPhase
        )
        print("   ✓ Enum imports successful")
        
        # Test dataclass imports
        print("2. Testing dataclass imports...")
        from src.workflow.evidence_first_workflow_manager import (
            PipelineResult,
            WorkflowProgress,
            EvidenceFirstWorkflowResult
        )
        print("   ✓ Dataclass imports successful")
        
        # Test enum values
        print("3. Testing enum values...")
        assert PipelineStatus.NOT_STARTED.value == "not_started"
        assert PipelineStatus.RUNNING.value == "running"
        assert PipelineStatus.COMPLETED.value == "completed"
        assert PipelineStatus.FAILED.value == "failed"
        assert PipelineStatus.SKIPPED.value == "skipped"
        
        assert WorkflowPhase.INITIALIZATION.value == "initialization"
        assert WorkflowPhase.PIPELINE_1_EXTRACTION.value == "pipeline_1_extraction"
        assert WorkflowPhase.PIPELINE_1_VALIDATION.value == "pipeline_1_validation"
        assert WorkflowPhase.PIPELINE_2_CALCULATION.value == "pipeline_2_calculation"
        assert WorkflowPhase.PIPELINE_2_GENERATION.value == "pipeline_2_generation"
        assert WorkflowPhase.PIPELINE_2_COMPLIANCE.value == "pipeline_2_compliance"
        assert WorkflowPhase.FINALIZATION.value == "finalization"
        print("   ✓ Enum values correct")
        
        # Test dataclass creation
        print("4. Testing dataclass creation...")
        pipeline_result = PipelineResult(
            pipeline_name="test_pipeline",
            status=PipelineStatus.COMPLETED,
            execution_time=1.5
        )
        assert pipeline_result.pipeline_name == "test_pipeline"
        assert pipeline_result.status == PipelineStatus.COMPLETED
        assert pipeline_result.execution_time == 1.5
        print("   ✓ PipelineResult creation works")
        
        workflow_progress = WorkflowProgress(
            current_phase=WorkflowPhase.INITIALIZATION,
            phase_progress=0.5,
            overall_progress=0.1,
            pipeline_1_status=PipelineStatus.NOT_STARTED,
            pipeline_2_status=PipelineStatus.NOT_STARTED,
            evidence_completeness=0.0
        )
        assert workflow_progress.current_phase == WorkflowPhase.INITIALIZATION
        assert workflow_progress.phase_progress == 0.5
        print("   ✓ WorkflowProgress creation works")
        
        # Test workflow manager creation with conditional imports
        print("5. Testing workflow manager creation...")
        from src.workflow.evidence_first_workflow_manager import (
            EvidenceFirstWorkflowManager,
            create_evidence_first_workflow_manager
        )
        
        # This should work even without dependencies
        workflow_manager = EvidenceFirstWorkflowManager()
        print("   ✓ EvidenceFirstWorkflowManager created")
        
        # Test service availability check
        availability = workflow_manager.check_service_availability()
        assert isinstance(availability, dict), "check_service_availability should return dict"
        print(f"   ✓ Service availability: {availability}")
        
        # Test basic methods that don't require services
        active_workflows = workflow_manager.get_active_workflows()
        assert isinstance(active_workflows, list), "get_active_workflows should return a list"
        print("   ✓ get_active_workflows() works")
        
        metrics = workflow_manager.get_workflow_metrics()
        assert isinstance(metrics, dict), "get_workflow_metrics should return a dict"
        print("   ✓ get_workflow_metrics() works")
        
        print("\n✅ Core imports, data structures, and workflow manager work correctly!")
        print("Note: Full workflow execution requires additional dependencies (spacy, etc.)")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_core_imports()
    sys.exit(0 if success else 1)