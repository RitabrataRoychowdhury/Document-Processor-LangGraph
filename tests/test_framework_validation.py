#!/usr/bin/env python3
"""
Test Framework Validation Script.

This script validates that the test framework components are properly structured
and can be imported without syntax errors.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


def validate_test_files():
    """Validate test framework files for syntax and structure."""
    test_files = [
        'tests/ui/test_ui_components.py',
        'tests/api/test_backend_endpoints.py', 
        'tests/integration/test_end_to_end_workflows.py',
        'tests/performance/test_ui_performance.py',
        'tests/test_comprehensive_suite.py',
        'tests/run_comprehensive_tests.py'
    ]
    
    results = []
    
    for test_file in test_files:
        result = {
            'file': test_file,
            'exists': False,
            'syntax_valid': False,
            'size_bytes': 0,
            'error': None
        }
        
        try:
            # Check if file exists
            if os.path.exists(test_file):
                result['exists'] = True
                result['size_bytes'] = os.path.getsize(test_file)
                
                # Check syntax by compiling
                with open(test_file, 'r') as f:
                    content = f.read()
                
                compile(content, test_file, 'exec')
                result['syntax_valid'] = True
                
            else:
                result['error'] = 'File not found'
                
        except SyntaxError as e:
            result['error'] = f'Syntax error: {e}'
        except Exception as e:
            result['error'] = f'Error: {e}'
        
        results.append(result)
    
    return results


def validate_test_structure():
    """Validate test directory structure."""
    expected_dirs = [
        'tests',
        'tests/ui',
        'tests/api', 
        'tests/integration',
        'tests/performance'
    ]
    
    expected_files = [
        'tests/README.md',
        'tests/test_config.json',
        'tests/run_comprehensive_tests.py',
        'tests/test_comprehensive_suite.py'
    ]
    
    structure_results = {
        'directories': {},
        'files': {}
    }
    
    # Check directories
    for dir_path in expected_dirs:
        structure_results['directories'][dir_path] = os.path.isdir(dir_path)
    
    # Check files
    for file_path in expected_files:
        structure_results['files'][file_path] = os.path.isfile(file_path)
    
    return structure_results


def validate_test_configuration():
    """Validate test configuration file."""
    config_file = 'tests/test_config.json'
    
    config_result = {
        'file_exists': False,
        'valid_json': False,
        'has_required_sections': False,
        'required_sections': [],
        'error': None
    }
    
    try:
        if os.path.exists(config_file):
            config_result['file_exists'] = True
            
            import json
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            config_result['valid_json'] = True
            
            # Check for required sections
            required_sections = [
                'ui_tests',
                'api_tests', 
                'integration_tests',
                'performance_tests',
                'reporting'
            ]
            
            found_sections = []
            for section in required_sections:
                if section in config_data:
                    found_sections.append(section)
            
            config_result['required_sections'] = found_sections
            config_result['has_required_sections'] = len(found_sections) == len(required_sections)
            
        else:
            config_result['error'] = 'Configuration file not found'
            
    except json.JSONDecodeError as e:
        config_result['error'] = f'Invalid JSON: {e}'
    except Exception as e:
        config_result['error'] = f'Error: {e}'
    
    return config_result


def generate_validation_report(file_results, structure_results, config_result):
    """Generate validation report."""
    report = []
    report.append("=" * 80)
    report.append("TEST FRAMEWORK VALIDATION REPORT")
    report.append("=" * 80)
    report.append("")
    
    # File validation results
    report.append("FILE VALIDATION:")
    total_files = len(file_results)
    valid_files = sum(1 for r in file_results if r['syntax_valid'])
    existing_files = sum(1 for r in file_results if r['exists'])
    
    report.append(f"  Total Files: {total_files}")
    report.append(f"  Existing Files: {existing_files}")
    report.append(f"  Syntax Valid Files: {valid_files}")
    report.append(f"  Success Rate: {(valid_files/total_files)*100:.1f}%")
    report.append("")
    
    # Individual file results
    for result in file_results:
        status = "✅" if result['syntax_valid'] else "❌"
        size_kb = result['size_bytes'] / 1024 if result['size_bytes'] > 0 else 0
        report.append(f"  {status} {result['file']} ({size_kb:.1f}KB)")
        if result['error']:
            report.append(f"      Error: {result['error']}")
    
    report.append("")
    
    # Structure validation results
    report.append("DIRECTORY STRUCTURE:")
    for dir_path, exists in structure_results['directories'].items():
        status = "✅" if exists else "❌"
        report.append(f"  {status} {dir_path}/")
    
    report.append("")
    report.append("REQUIRED FILES:")
    for file_path, exists in structure_results['files'].items():
        status = "✅" if exists else "❌"
        report.append(f"  {status} {file_path}")
    
    report.append("")
    
    # Configuration validation results
    report.append("CONFIGURATION VALIDATION:")
    report.append(f"  File Exists: {'✅' if config_result['file_exists'] else '❌'}")
    report.append(f"  Valid JSON: {'✅' if config_result['valid_json'] else '❌'}")
    report.append(f"  Required Sections: {'✅' if config_result['has_required_sections'] else '❌'}")
    
    if config_result['required_sections']:
        report.append(f"  Found Sections: {', '.join(config_result['required_sections'])}")
    
    if config_result['error']:
        report.append(f"  Error: {config_result['error']}")
    
    report.append("")
    
    # Overall assessment
    overall_success = (
        valid_files == total_files and
        all(structure_results['directories'].values()) and
        all(structure_results['files'].values()) and
        config_result['has_required_sections']
    )
    
    report.append("OVERALL ASSESSMENT:")
    if overall_success:
        report.append("  ✅ Test framework is properly structured and ready for use")
    else:
        report.append("  ⚠️  Test framework has issues that should be addressed")
        
        # Provide recommendations
        report.append("")
        report.append("RECOMMENDATIONS:")
        
        if valid_files < total_files:
            report.append("  - Fix syntax errors in test files")
        
        if not all(structure_results['directories'].values()):
            report.append("  - Create missing directories")
        
        if not all(structure_results['files'].values()):
            report.append("  - Create missing required files")
        
        if not config_result['has_required_sections']:
            report.append("  - Update configuration file with required sections")
    
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    """Main validation function."""
    print("Validating test framework...")
    
    # Run validations
    file_results = validate_test_files()
    structure_results = validate_test_structure()
    config_result = validate_test_configuration()
    
    # Generate and display report
    report = generate_validation_report(file_results, structure_results, config_result)
    print(report)
    
    # Determine exit code
    total_files = len(file_results)
    valid_files = sum(1 for r in file_results if r['syntax_valid'])
    
    if valid_files == total_files and config_result['has_required_sections']:
        print("\n🎉 Test framework validation successful!")
        return 0
    else:
        print("\n⚠️  Test framework validation found issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())