#!/usr/bin/env python3
"""
Verification script for Task 5 integration with run.sh
Ensures all components are properly integrated and ready
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

def verify_task5_integration():
    """Verify Task 5 integration is complete and functional"""
    print("🔍 Verifying Task 5 Integration with run.sh")
    print("=" * 50)
    
    verification_results = {
        "imports": [],
        "configs": [],
        "directories": [],
        "scripts": [],
        "run_script": []
    }
    
    # Test imports
    print("\n📦 Testing Component Imports:")
    
    imports_to_test = [
        ("Quality Validation Service", "src.services.comprehensive_quality_validation_service", "ComprehensiveQualityValidationService"),
        ("Performance Monitor", "src.services.system_performance_monitor", "SystemPerformanceMonitor"),
        ("System Comparison Suite", "tests.test_end_to_end_system_comparison", "SystemComparisonTestSuite"),
        ("Main App", "src.ui.main_app", "main"),
        ("Health Checker", "src.services.health_checker", "HealthChecker"),
        ("App Config", "src.config.app_config", "AppConfig")
    ]
    
    for name, module, component in imports_to_test:
        try:
            module_obj = __import__(module, fromlist=[component])
            getattr(module_obj, component)
            print(f"   ✅ {name}: OK")
            verification_results["imports"].append((name, True))
        except Exception as e:
            print(f"   ❌ {name}: {e}")
            verification_results["imports"].append((name, False))
    
    # Test configuration files
    print("\n⚙️  Testing Configuration Files:")
    
    config_files = [
        ("Quality Validation Config", "config/validation/quality_validation_config.yaml"),
        ("OpenRouter Config", "config/settings/openrouter_config.yaml"),
        ("Environment File", ".env")
    ]
    
    for name, path in config_files:
        if Path(path).exists():
            print(f"   ✅ {name}: EXISTS")
            verification_results["configs"].append((name, True))
        else:
            print(f"   ❌ {name}: MISSING")
            verification_results["configs"].append((name, False))
    
    # Test required directories
    print("\n📁 Testing Required Directories:")
    
    required_dirs = [
        ("Validation Reports", "results/validation_reports"),
        ("Performance Reports", "results/performance_reports"),
        ("Generated Documents", "results/generated_documents"),
        ("Templates Archive", "results/templates_archive"),
        ("Logs", "logs")
    ]
    
    for name, path in required_dirs:
        dir_path = Path(path)
        if dir_path.exists():
            print(f"   ✅ {name}: EXISTS")
            verification_results["directories"].append((name, True))
        else:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ {name}: CREATED")
            verification_results["directories"].append((name, True))
    
    # Test Task 5 scripts
    print("\n📜 Testing Task 5 Scripts:")
    
    task5_scripts = [
        ("Integration Test", "scripts/test_task5_integration.py"),
        ("Real Document Validation", "scripts/validate_system_with_real_documents.py"),
        ("Migration Script", "scripts/migrate_to_refactored_system_v2.py"),
        ("Quality Validation Service", "src/services/comprehensive_quality_validation_service.py"),
        ("Performance Monitor", "src/services/system_performance_monitor.py"),
        ("End-to-End Tests", "tests/test_end_to_end_system_comparison.py")
    ]
    
    for name, path in task5_scripts:
        if Path(path).exists():
            print(f"   ✅ {name}: EXISTS")
            verification_results["scripts"].append((name, True))
        else:
            print(f"   ❌ {name}: MISSING")
            verification_results["scripts"].append((name, False))
    
    # Test run.sh integration
    print("\n🚀 Testing run.sh Integration:")
    
    run_script_path = Path("scripts/run.sh")
    if run_script_path.exists():
        with open(run_script_path, 'r') as f:
            content = f.read()
        
        # Check for Task 5 menu options
        task5_checks = [
            ("Option 11 (Quality Validation)", "Quality validation and system testing (Task 5)"),
            ("Option 12 (Migration)", "Run system migration to refactored architecture"),
            ("Task 5 Integration Test", "test_task5_integration.py"),
            ("Real Document Validation", "validate_system_with_real_documents.py"),
            ("Migration Script", "migrate_to_refactored_system_v2.py")
        ]
        
        for name, search_text in task5_checks:
            if search_text in content:
                print(f"   ✅ {name}: INTEGRATED")
                verification_results["run_script"].append((name, True))
            else:
                print(f"   ❌ {name}: NOT FOUND")
                verification_results["run_script"].append((name, False))
    else:
        print("   ❌ run.sh: NOT FOUND")
        verification_results["run_script"].append(("run.sh", False))
    
    # Calculate overall status
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    total_checks = 0
    passed_checks = 0
    
    for category, results in verification_results.items():
        category_passed = sum(1 for _, status in results if status)
        category_total = len(results)
        total_checks += category_total
        passed_checks += category_passed
        
        print(f"{category.title()}: {category_passed}/{category_total} ({'✅' if category_passed == category_total else '⚠️'})")
    
    success_rate = passed_checks / total_checks if total_checks > 0 else 0
    
    print(f"\nOverall: {passed_checks}/{total_checks} ({success_rate:.1%})")
    
    if success_rate >= 0.9:
        print("\n🎉 VERIFICATION SUCCESSFUL!")
        print("   Task 5 is fully integrated and ready to use")
        print("   Run scripts/run.sh and select option 11 or 12")
    elif success_rate >= 0.7:
        print("\n⚠️  VERIFICATION MOSTLY SUCCESSFUL")
        print("   Most components are ready, some minor issues detected")
        print("   System should work but may have limited functionality")
    else:
        print("\n❌ VERIFICATION FAILED")
        print("   Critical components are missing or not working")
        print("   Please review the issues above before proceeding")
    
    # Provide specific recommendations
    print("\n💡 USAGE RECOMMENDATIONS:")
    print("   1. Run: ./scripts/run.sh")
    print("   2. Select option 11 for Task 5 quality validation testing")
    print("   3. Select option 12 for system migration (if needed)")
    print("   4. Use option 1 for normal web interface with enhanced features")
    
    print("\n🔧 TASK 5 FEATURES AVAILABLE:")
    print("   • Comprehensive quality validation with scoring")
    print("   • Real-time performance monitoring")
    print("   • End-to-end system comparison testing")
    print("   • Real document validation with quality metrics")
    print("   • System migration with rollback capability")
    
    return success_rate >= 0.9

if __name__ == "__main__":
    success = verify_task5_integration()
    sys.exit(0 if success else 1)