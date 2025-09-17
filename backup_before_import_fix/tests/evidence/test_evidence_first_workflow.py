#!/usr/bin/env python3
"""
Test script for Evidence-First QME Workflow Manager

This script tests the basic functionality of the evidence-first workflow manager
to ensure it can be imported and initialized correctly.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_evidence_first_workflow_manager():
    """Test basic functionality of the evidence-first workflow manager."""
    try:
        print("Testing Evidence-First QME Workflow Manager...")
        
        # Test imports
        print("1. Testing imports...")
        from src.workflow.evidence_first_workflow_manager import (
            EvidenceFirstWorkflowManager,
            PipelineStatus,
            WorkflowPhase,
            create_evidence_first_workflow_manager
        )
        print("   ✓ Imports successful")
        
        # Test initialization
        print("2. Testing initialization...")
        workflow_manager = create_evidence_first_workflow_manager()
        print("   ✓ Workflow manager created successfully")
        
        # Test basic methods
        print("3. Testing basic methods...")
        
        # Test get_active_workflows (should be empty initially)
        active_workflows = workflow_manager.get_active_workflows()
        assert isinstance(active_workflows, list), "get_active_workflows should return a list"
        assert len(active_workflows) == 0, "Should have no active workflows initially"
        print("   ✓ get_active_workflows() works")
        
        # Test get_workflow_metrics
        metrics = workflow_manager.get_workflow_metrics()
        assert isinstance(metrics, dict), "get_workflow_metrics should return a dict"
        assert 'total_workflows' in metrics, "Metrics should include total_workflows"
        assert metrics['total_workflows'] == 0, "Should have 0 total workflows initially"
        print("   ✓ get_workflow_metrics() works")
        
        # Test get_workflow_status for non-existent workflow
        status = workflow_manager.get_workflow_status("non-existent-id")
        assert status is None, "Should return None for non-existent workflow"
        print("   ✓ get_workflow_status() works")
        
        # Test enum values
        print("4. Testing enum values...")
        assert PipelineStatus.NOT_STARTED.value == "not_started"
        assert WorkflowPhase.INITIALIZATION.value == "initialization"
        print("   ✓ Enum values correct")
        
        print("\n✅ All tests passed! Evidence-First QME Workflow Manager is working correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_evidence_first_workflow_manager()
    sys.exit(0 if success else 1)