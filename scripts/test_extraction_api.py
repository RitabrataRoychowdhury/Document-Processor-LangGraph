#!/usr/bin/env python3
"""
Test script for QME Document Extraction Testing API

This script validates all API endpoints and provides performance benchmarking.
"""

import os
import sys
import time
import json
import requests
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import argparse

# Add project root to path
sys.path.append('.')

def create_test_document() -> str:
    """Create a simple test document for API testing."""
    test_content = """
Patient Name: John Doe
Case Number: WC-2024-001234
Date of Injury: March 15, 2024
Date of Birth: January 10, 1980
Body Parts Affected: Lower back, left knee
Diagnosis: Lumbar strain, knee contusion
Employer: ABC Manufacturing Company
Occupation: Warehouse Worker

HISTORY OF PRESENT ILLNESS:
The patient is a 44-year-old male who sustained an injury to his lower back and left knee 
on March 15, 2024, while lifting heavy boxes at work. He reports immediate onset of pain 
in the lumbar region with radiation to the left leg.

PHYSICAL EXAMINATION:
The patient appears in mild distress. Range of motion in the lumbar spine is limited 
due to pain. Left knee shows mild swelling and tenderness over the medial aspect.

DIAGNOSIS:
1. Lumbar strain (ICD-10: M54.5)
2. Left knee contusion (ICD-10: S80.02XA)

IMPAIRMENT RATING:
Based on AMA Guides 5th Edition:
- Lumbar spine: 8% whole person impairment
- Left knee: 3% whole person impairment
- Combined: 11% whole person impairment

WORK RESTRICTIONS:
- No lifting over 25 pounds
- Avoid prolonged standing or walking
- No repetitive bending or twisting
"""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        return f.name

class APITester:
    """Test class for QME Extraction API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_file = None
        self.results = {}
        
    def setup(self):
        """Set up test environment."""
        print("Setting up test environment...")
        self.test_file = create_test_document()
        print(f"Created test document: {self.test_file}")
        
    def cleanup(self):
        """Clean up test environment."""
        if self.test_file and os.path.exists(self.test_file):
            os.unlink(self.test_file)
            print(f"Cleaned up test document: {self.test_file}")
    
    def test_health_check(self) -> Dict[str, Any]:
        """Test health check endpoint."""
        print("\n1. Testing health check endpoint...")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health")
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Health check passed ({processing_time:.2f}s)")
                print(f"   Status: {data.get('status', 'unknown')}")
                
                services = data.get('services', {})
                for service, status in services.items():
                    status_icon = "✅" if status else "❌"
                    print(f"   {status_icon} {service}: {status}")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "processing_time": processing_time,
                    "data": data
                }
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "processing_time": processing_time,
                    "error": response.text
                }
                
        except Exception as e:
            print(f"   ❌ Health check error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": 0.0
            }
    
    def test_openrouter_extraction(self) -> Dict[str, Any]:
        """Test OpenRouter extraction endpoint."""
        print("\n2. Testing OpenRouter extraction...")
        
        try:
            start_time = time.time()
            
            with open(self.test_file, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                params = {'prompt_template': 'patient_info'}
                
                response = requests.post(
                    f"{self.base_url}/api/v1/extract/openrouter",
                    files=files,
                    params=params
                )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ OpenRouter extraction passed ({processing_time:.2f}s)")
                print(f"   Extracted {len(data.get('extracted_fields', {}))} fields")
                print(f"   Quality score: {data.get('quality_assessment', {}).get('overall_score', 0):.1f}%")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "processing_time": processing_time,
                    "data": data
                }
            else:
                print(f"   ❌ OpenRouter extraction failed: {response.status_code}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "processing_time": processing_time,
                    "error": response.text
                }
                
        except Exception as e:
            print(f"   ❌ OpenRouter extraction error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": 0.0
            }
    
    def test_gemini_extraction(self) -> Dict[str, Any]:
        """Test Gemini extraction endpoint."""
        print("\n3. Testing Gemini extraction...")
        
        try:
            start_time = time.time()
            
            with open(self.test_file, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                params = {'prompt_template': 'patient_info'}
                
                response = requests.post(
                    f"{self.base_url}/api/v1/extract/gemini",
                    files=files,
                    params=params
                )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Gemini extraction passed ({processing_time:.2f}s)")
                print(f"   Extracted {len(data.get('extracted_fields', {}))} fields")
                print(f"   Quality score: {data.get('quality_assessment', {}).get('overall_score', 0):.1f}%")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "processing_time": processing_time,
                    "data": data
                }
            else:
                print(f"   ⚠️ Gemini extraction failed: {response.status_code}")
                print(f"   This may be expected if Gemini API is not configured")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "processing_time": processing_time,
                    "error": response.text
                }
                
        except Exception as e:
            print(f"   ❌ Gemini extraction error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": 0.0
            }
    
    def test_multi_layer_extraction(self) -> Dict[str, Any]:
        """Test multi-layer extraction endpoint."""
        print("\n4. Testing multi-layer extraction...")
        
        try:
            start_time = time.time()
            
            with open(self.test_file, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                params = {
                    'extraction_strategy': 'hybrid',
                    'confidence_threshold': 0.7
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/extract/multi-layer",
                    files=files,
                    params=params
                )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Multi-layer extraction passed ({processing_time:.2f}s)")
                print(f"   Extracted {len(data.get('extracted_fields', {}))} fields")
                print(f"   Quality score: {data.get('quality_assessment', {}).get('overall_score', 0):.1f}%")
                print(f"   Strategy used: {data.get('file_info', {}).get('strategy_used', 'unknown')}")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "processing_time": processing_time,
                    "data": data
                }
            else:
                print(f"   ❌ Multi-layer extraction failed: {response.status_code}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "processing_time": processing_time,
                    "error": response.text
                }
                
        except Exception as e:
            print(f"   ❌ Multi-layer extraction error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": 0.0
            }
    
    def test_extraction_comparison(self) -> Dict[str, Any]:
        """Test extraction comparison endpoint."""
        print("\n5. Testing extraction comparison...")
        
        try:
            start_time = time.time()
            
            with open(self.test_file, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                params = {
                    'include_openrouter': True,
                    'include_gemini': True,
                    'include_multi_layer': True
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/extract/compare",
                    files=files,
                    params=params
                )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Extraction comparison passed ({processing_time:.2f}s)")
                
                results = data.get('extraction_results', {})
                successful_methods = [method for method, result in results.items() if result.get('success', False)]
                print(f"   Successful methods: {', '.join(successful_methods)}")
                print(f"   Best method: {data.get('best_method', 'unknown')}")
                
                # Show comparison analysis
                analysis = data.get('comparison_analysis', {})
                if 'quality_comparison' in analysis:
                    print("   Quality comparison:")
                    for method, score in analysis['quality_comparison'].items():
                        print(f"     {method}: {score:.1f}%")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "processing_time": processing_time,
                    "data": data
                }
            else:
                print(f"   ❌ Extraction comparison failed: {response.status_code}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "processing_time": processing_time,
                    "error": response.text
                }
                
        except Exception as e:
            print(f"   ❌ Extraction comparison error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": 0.0
            }
    
    def test_qme_generation(self) -> Dict[str, Any]:
        """Test QME template generation endpoint."""
        print("\n6. Testing QME template generation...")
        
        try:
            start_time = time.time()
            
            with open(self.test_file, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                params = {
                    'output_format': 'docx',
                    'apply_professional_formatting': True,
                    'quality_threshold': 70.0
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/qme/generate",
                    files=files,
                    params=params
                )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ QME generation passed ({processing_time:.2f}s)")
                print(f"   Template generated: {data.get('success', False)}")
                
                if data.get('template_path'):
                    print(f"   Template path: {data['template_path']}")
                
                quality = data.get('quality_assessment', {})
                if quality:
                    print(f"   Quality score: {quality.get('overall_score', 0):.1f}%")
                
                validation_issues = data.get('validation_issues', [])
                if validation_issues:
                    print(f"   Validation issues: {len(validation_issues)}")
                    for issue in validation_issues[:3]:  # Show first 3 issues
                        print(f"     - {issue.get('description', 'Unknown issue')}")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "processing_time": processing_time,
                    "data": data
                }
            else:
                print(f"   ❌ QME generation failed: {response.status_code}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "processing_time": processing_time,
                    "error": response.text
                }
                
        except Exception as e:
            print(f"   ❌ QME generation error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": 0.0
            }
    
    def test_qme_validation(self) -> Dict[str, Any]:
        """Test QME template validation endpoint."""
        print("\n7. Testing QME template validation...")
        
        try:
            start_time = time.time()
            
            with open(self.test_file, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                params = {'validation_level': 'comprehensive'}
                
                response = requests.post(
                    f"{self.base_url}/api/v1/qme/validate",
                    files=files,
                    params=params
                )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ QME validation passed ({processing_time:.2f}s)")
                print(f"   Validation score: {data.get('validation_score', 0):.1f}%")
                
                validation_issues = data.get('validation_issues', [])
                print(f"   Validation issues: {len(validation_issues)}")
                
                # Show issue breakdown by severity
                severity_counts = {}
                for issue in validation_issues:
                    severity = issue.get('severity', 'unknown')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                for severity, count in severity_counts.items():
                    print(f"     {severity}: {count}")
                
                recommendations = data.get('recommendations', [])
                if recommendations:
                    print(f"   Recommendations: {len(recommendations)}")
                    for rec in recommendations[:2]:  # Show first 2 recommendations
                        print(f"     - {rec}")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "processing_time": processing_time,
                    "data": data
                }
            else:
                print(f"   ❌ QME validation failed: {response.status_code}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "processing_time": processing_time,
                    "error": response.text
                }
                
        except Exception as e:
            print(f"   ❌ QME validation error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": 0.0
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all API tests."""
        print("🚀 Starting QME Document Extraction API Tests")
        print("=" * 60)
        
        self.setup()
        
        try:
            # Run all tests
            self.results['health_check'] = self.test_health_check()
            self.results['openrouter_extraction'] = self.test_openrouter_extraction()
            self.results['gemini_extraction'] = self.test_gemini_extraction()
            self.results['multi_layer_extraction'] = self.test_multi_layer_extraction()
            self.results['extraction_comparison'] = self.test_extraction_comparison()
            self.results['qme_generation'] = self.test_qme_generation()
            self.results['qme_validation'] = self.test_qme_validation()
            
            # Generate summary
            self.print_summary()
            
            return self.results
            
        finally:
            self.cleanup()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for result in self.results.values() if result.get('success', False))
        
        print(f"Total tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success rate: {(successful_tests / total_tests * 100):.1f}%")
        
        print("\nTest Results:")
        for test_name, result in self.results.items():
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            processing_time = result.get('processing_time', 0)
            print(f"  {status} {test_name.replace('_', ' ').title()}: {processing_time:.2f}s")
        
        # Performance summary
        total_time = sum(result.get('processing_time', 0) for result in self.results.values())
        avg_time = total_time / total_tests if total_tests > 0 else 0
        
        print(f"\nPerformance Summary:")
        print(f"  Total processing time: {total_time:.2f}s")
        print(f"  Average per test: {avg_time:.2f}s")
        
        # Identify slowest test
        slowest_test = max(self.results.items(), key=lambda x: x[1].get('processing_time', 0))
        print(f"  Slowest test: {slowest_test[0]} ({slowest_test[1].get('processing_time', 0):.2f}s)")
    
    def save_results(self, output_file: str = "api_test_results.json"):
        """Save test results to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n💾 Test results saved to: {output_file}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test QME Document Extraction API")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000",
        help="Base URL for the API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--output",
        default="api_test_results.json",
        help="Output file for test results (default: api_test_results.json)"
    )
    parser.add_argument(
        "--test",
        choices=['health', 'openrouter', 'gemini', 'multi-layer', 'compare', 'generate', 'validate', 'all'],
        default='all',
        help="Specific test to run (default: all)"
    )
    
    args = parser.parse_args()
    
    tester = APITester(base_url=args.url)
    
    if args.test == 'all':
        results = tester.run_all_tests()
    else:
        tester.setup()
        try:
            if args.test == 'health':
                results = {'health_check': tester.test_health_check()}
            elif args.test == 'openrouter':
                results = {'openrouter_extraction': tester.test_openrouter_extraction()}
            elif args.test == 'gemini':
                results = {'gemini_extraction': tester.test_gemini_extraction()}
            elif args.test == 'multi-layer':
                results = {'multi_layer_extraction': tester.test_multi_layer_extraction()}
            elif args.test == 'compare':
                results = {'extraction_comparison': tester.test_extraction_comparison()}
            elif args.test == 'generate':
                results = {'qme_generation': tester.test_qme_generation()}
            elif args.test == 'validate':
                results = {'qme_validation': tester.test_qme_validation()}
            
            tester.results = results
            tester.print_summary()
        finally:
            tester.cleanup()
    
    tester.save_results(args.output)

if __name__ == "__main__":
    main()