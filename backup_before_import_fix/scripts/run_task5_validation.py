#!/usr/bin/env python3
"""
Task 5 Validation Runner

This script runs the comprehensive validation for Task 5: Knowledge Base Integration
and Pipeline Functionality validation.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from validation.comprehensive_system_validator import ComprehensiveSystemValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Run comprehensive Task 5 validation."""
    logger.info("Starting Task 5: Knowledge Base Integration and Pipeline Functionality Validation")
    
    try:
        # Initialize comprehensive validator
        validator = ComprehensiveSystemValidator()
        
        # Run complete validation
        result = await validator.run_complete_validation()
        
        # Save comprehensive report
        report_path = validator.save_comprehensive_report(result)
        
        # Print summary
        print("\n" + "="*80)
        print("TASK 5 VALIDATION SUMMARY")
        print("="*80)
        print(f"Validation ID: {result.validation_id}")
        print(f"Total Execution Time: {result.total_execution_time:.2f} seconds")
        print(f"Overall Validation: {'PASSED' if result.overall_validation_passed else 'FAILED'}")
        print(f"Performance Benchmarks: {'MET' if result.performance_benchmarks_met else 'NOT MET'}")
        print(f"Production Ready: {'YES' if result.system_ready_for_production else 'NO'}")
        
        print(f"\nSub-task Results:")
        print(f"  5.1 Knowledge Base Validation: {'PASSED' if result.knowledge_base_validation.get('validation_passed', False) else 'FAILED'}")
        print(f"  5.2 Pipeline Integration Testing: {'PASSED' if result.pipeline_integration_testing.get('testing_completed', False) else 'FAILED'}")
        print(f"  5.3 Evidence-First Validation: {'PASSED' if result.evidence_first_validation.get('validation_completed', False) else 'FAILED'}")
        print(f"  5.4 Calculation Validation: {'PASSED' if result.calculation_validation.get('validation_completed', False) else 'FAILED'}")
        print(f"  5.5 Compliance Quality Validation: {'PASSED' if result.compliance_quality_validation.get('validation_completed', False) else 'FAILED'}")
        
        if result.critical_issues:
            print(f"\nCritical Issues ({len(result.critical_issues)}):")
            for issue in result.critical_issues:
                print(f"  - {issue}")
        
        if result.major_issues:
            print(f"\nMajor Issues ({len(result.major_issues)}):")
            for issue in result.major_issues[:5]:  # Show first 5
                print(f"  - {issue}")
            if len(result.major_issues) > 5:
                print(f"  ... and {len(result.major_issues) - 5} more")
        
        if result.recommendations:
            print(f"\nRecommendations:")
            for rec in result.recommendations[:5]:  # Show first 5
                print(f"  - {rec}")
            if len(result.recommendations) > 5:
                print(f"  ... and {len(result.recommendations) - 5} more")
        
        print(f"\nDetailed report saved to: {report_path}")
        print("="*80)
        
        # Return appropriate exit code
        return 0 if result.overall_validation_passed else 1
        
    except Exception as e:
        logger.error(f"Error running Task 5 validation: {e}")
        print(f"\nERROR: Task 5 validation failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)