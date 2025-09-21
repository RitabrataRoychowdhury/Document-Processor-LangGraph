#!/usr/bin/env python3
"""
QME Document Extraction API Usage Demo

This script demonstrates how to use the QME Document Extraction Testing API
for various extraction and template generation tasks.
"""

import os
import sys
import time
import requests
import tempfile
from pathlib import Path

def create_sample_document():
    """Create a sample QME document for testing."""
    sample_content = """
QUALIFIED MEDICAL EVALUATOR REPORT

Patient Information:
Name: Jane Smith
Case Number: WC-2024-005678
Date of Birth: June 15, 1985
Date of Injury: August 10, 2024
Employer: Tech Solutions Inc.
Occupation: Software Developer

Body Parts Affected:
- Right wrist
- Cervical spine

HISTORY OF PRESENT ILLNESS:
The patient is a 39-year-old female software developer who developed right wrist pain 
and cervical spine discomfort due to repetitive computer use and poor ergonomics. 
Symptoms began gradually in August 2024 and have progressively worsened.

PHYSICAL EXAMINATION:
Right wrist shows tenderness over the carpal tunnel area with positive Tinel's sign.
Cervical spine demonstrates reduced range of motion with muscle spasm in the 
upper trapezius region.

DIAGNOSTIC STUDIES:
- EMG/NCV study: Consistent with mild carpal tunnel syndrome
- Cervical spine MRI: Mild disc bulging at C5-C6

DIAGNOSIS:
1. Carpal tunnel syndrome, right wrist (ICD-10: G56.01)
2. Cervical strain with muscle spasm (ICD-10: M54.2)

CAUSATION ANALYSIS:
The patient's conditions are directly related to her work activities involving 
prolonged computer use with inadequate ergonomic setup.

IMPAIRMENT RATING:
Based on AMA Guides 5th Edition:
- Right wrist (carpal tunnel): 5% upper extremity impairment = 3% whole person
- Cervical spine: 8% whole person impairment
- Combined impairment: 11% whole person impairment

WORK RESTRICTIONS:
- Limit continuous typing to 30 minutes with 5-minute breaks
- Use ergonomic keyboard and mouse
- Adjust workstation for proper posture
- No lifting over 15 pounds

FUTURE MEDICAL CARE:
- Ergonomic assessment and equipment
- Physical therapy for cervical spine
- Possible carpal tunnel release if conservative treatment fails

CONCLUSIONS:
The patient has work-related carpal tunnel syndrome and cervical strain that 
require ongoing medical management and workplace modifications.

Dr. Michael Johnson, MD
QME License #12345
Date: September 18, 2025
"""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_content)
        return f.name

class QMEAPIDemo:
    """Demo class for QME API usage."""
    
    def __init__(self, api_base_url="http://localhost:8000"):
        self.api_base_url = api_base_url
        self.sample_file = None
        
    def setup(self):
        """Set up demo environment."""
        print("🔧 Setting up demo environment...")
        self.sample_file = create_sample_document()
        print(f"   Created sample document: {self.sample_file}")
        
    def cleanup(self):
        """Clean up demo environment."""
        if self.sample_file and os.path.exists(self.sample_file):
            os.unlink(self.sample_file)
            print(f"   Cleaned up sample document: {self.sample_file}")
    
    def check_api_health(self):
        """Check API health and service availability."""
        print("\n1️⃣ Checking API Health")
        print("-" * 40)
        
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API Status: {data.get('status', 'unknown')}")
                
                services = data.get('services', {})
                print("📊 Service Status:")
                for service, status in services.items():
                    status_icon = "✅" if status else "❌"
                    print(f"   {status_icon} {service.replace('_', ' ').title()}")
                
                capabilities = data.get('capabilities', {})
                print("🚀 Available Capabilities:")
                for capability, available in capabilities.items():
                    cap_icon = "✅" if available else "❌"
                    print(f"   {cap_icon} {capability.replace('_', ' ').title()}")
                
                return True
            else:
                print(f"❌ API Health Check Failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to connect to API: {e}")
            print(f"   Make sure the API server is running at {self.api_base_url}")
            return False
    
    def demo_openrouter_extraction(self):
        """Demonstrate OpenRouter extraction."""
        print("\n2️⃣ OpenRouter Extraction Demo")
        print("-" * 40)
        
        try:
            with open(self.sample_file, 'rb') as f:
                files = {'file': ('sample_qme.txt', f, 'text/plain')}
                params = {'prompt_template': 'patient_info'}
                
                print("🔄 Sending document to OpenRouter...")
                start_time = time.time()
                
                response = requests.post(
                    f"{self.api_base_url}/api/v1/extract/openrouter",
                    files=files,
                    params=params,
                    timeout=30
                )
                
                processing_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Extraction completed in {processing_time:.2f}s")
                    print(f"📄 Document ID: {data.get('document_id', 'unknown')}")
                    
                    extracted_fields = data.get('extracted_fields', {})
                    print(f"📊 Extracted {len(extracted_fields)} fields:")
                    
                    for field_name, field_value in list(extracted_fields.items())[:5]:
                        confidence = data.get('confidence_scores', {}).get(field_name, 0)
                        print(f"   • {field_name}: {field_value} (confidence: {confidence:.2f})")
                    
                    if len(extracted_fields) > 5:
                        print(f"   ... and {len(extracted_fields) - 5} more fields")
                    
                    quality = data.get('quality_assessment', {})
                    if quality:
                        print(f"🎯 Quality Score: {quality.get('overall_score', 0):.1f}%")
                    
                    return data
                else:
                    print(f"❌ OpenRouter extraction failed: {response.status_code}")
                    print(f"   Error: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ OpenRouter extraction error: {e}")
            return None
    
    def demo_multi_layer_extraction(self):
        """Demonstrate multi-layer extraction with fallback."""
        print("\n3️⃣ Multi-Layer Extraction Demo")
        print("-" * 40)
        
        try:
            with open(self.sample_file, 'rb') as f:
                files = {'file': ('sample_qme.txt', f, 'text/plain')}
                params = {
                    'extraction_strategy': 'hybrid',
                    'confidence_threshold': 0.7
                }
                
                print("🔄 Testing multi-layer fallback system...")
                print("   Strategy: OpenRouter → Gemini → Rule-based")
                start_time = time.time()
                
                response = requests.post(
                    f"{self.api_base_url}/api/v1/extract/multi-layer",
                    files=files,
                    params=params,
                    timeout=45
                )
                
                processing_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Multi-layer extraction completed in {processing_time:.2f}s")
                    
                    strategy_used = data.get('file_info', {}).get('strategy_used', 'unknown')
                    print(f"🎯 Strategy used: {strategy_used}")
                    
                    extracted_fields = data.get('extracted_fields', {})
                    print(f"📊 Extracted {len(extracted_fields)} fields:")
                    
                    # Show top fields with confidence scores
                    confidence_scores = data.get('confidence_scores', {})
                    sorted_fields = sorted(
                        extracted_fields.items(),
                        key=lambda x: confidence_scores.get(x[0], 0),
                        reverse=True
                    )
                    
                    for field_name, field_value in sorted_fields[:6]:
                        confidence = confidence_scores.get(field_name, 0)
                        print(f"   • {field_name}: {field_value} (confidence: {confidence:.2f})")
                    
                    quality = data.get('quality_assessment', {})
                    if quality:
                        print(f"🎯 Quality Metrics:")
                        print(f"   Overall: {quality.get('overall_score', 0):.1f}%")
                        print(f"   Completeness: {quality.get('completeness_score', 0):.1f}%")
                        print(f"   Accuracy: {quality.get('accuracy_score', 0):.1f}%")
                    
                    return data
                else:
                    print(f"❌ Multi-layer extraction failed: {response.status_code}")
                    print(f"   Error: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Multi-layer extraction error: {e}")
            return None
    
    def demo_extraction_comparison(self):
        """Demonstrate extraction method comparison."""
        print("\n4️⃣ Extraction Method Comparison Demo")
        print("-" * 40)
        
        try:
            with open(self.sample_file, 'rb') as f:
                files = {'file': ('sample_qme.txt', f, 'text/plain')}
                params = {
                    'include_openrouter': True,
                    'include_gemini': True,
                    'include_multi_layer': True
                }
                
                print("🔄 Comparing all extraction methods...")
                start_time = time.time()
                
                response = requests.post(
                    f"{self.api_base_url}/api/v1/extract/compare",
                    files=files,
                    params=params,
                    timeout=60
                )
                
                processing_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Comparison completed in {processing_time:.2f}s")
                    
                    results = data.get('extraction_results', {})
                    successful_methods = [method for method, result in results.items() if result.get('success', False)]
                    
                    print(f"📊 Methods tested: {len(results)}")
                    print(f"✅ Successful methods: {len(successful_methods)}")
                    print(f"🏆 Best method: {data.get('best_method', 'unknown')}")
                    
                    # Show comparison analysis
                    analysis = data.get('comparison_analysis', {})
                    
                    if 'quality_comparison' in analysis:
                        print("\n🎯 Quality Comparison:")
                        for method, score in analysis['quality_comparison'].items():
                            print(f"   {method}: {score:.1f}%")
                    
                    if 'performance_comparison' in analysis:
                        print("\n⚡ Performance Comparison:")
                        for method, time_taken in analysis['performance_comparison'].items():
                            print(f"   {method}: {time_taken:.2f}s")
                    
                    if 'field_coverage' in analysis:
                        print("\n📋 Field Coverage:")
                        for method, field_count in analysis['field_coverage'].items():
                            print(f"   {method}: {field_count} fields")
                    
                    # Show consensus fields
                    consensus_fields = analysis.get('consensus_fields', {})
                    if consensus_fields:
                        print(f"\n🤝 Consensus fields ({len(consensus_fields)}):")
                        for field_name in list(consensus_fields.keys())[:3]:
                            print(f"   • {field_name}")
                    
                    # Show discrepancies
                    discrepancies = analysis.get('discrepancies', [])
                    if discrepancies:
                        print(f"\n⚠️ Discrepancies found: {len(discrepancies)}")
                        for disc in discrepancies[:2]:
                            print(f"   • {disc.get('field', 'unknown')}: {disc.get('methods_disagreeing', 0)} methods disagree")
                    
                    return data
                else:
                    print(f"❌ Comparison failed: {response.status_code}")
                    print(f"   Error: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Comparison error: {e}")
            return None
    
    def demo_qme_generation(self):
        """Demonstrate QME template generation."""
        print("\n5️⃣ QME Template Generation Demo")
        print("-" * 40)
        
        try:
            with open(self.sample_file, 'rb') as f:
                files = {'file': ('sample_qme.txt', f, 'text/plain')}
                params = {
                    'output_format': 'docx',
                    'apply_professional_formatting': True,
                    'quality_threshold': 70.0
                }
                
                print("🔄 Generating QME template...")
                print("   Format: DOCX with professional formatting")
                start_time = time.time()
                
                response = requests.post(
                    f"{self.api_base_url}/api/v1/qme/generate",
                    files=files,
                    params=params,
                    timeout=90
                )
                
                processing_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Template generation completed in {processing_time:.2f}s")
                    
                    if data.get('success', False):
                        template_path = data.get('template_path')
                        if template_path:
                            print(f"📄 Template saved to: {template_path}")
                        
                        # Show extraction results
                        extraction_results = data.get('extraction_results', {})
                        if extraction_results:
                            extracted_fields = extraction_results.get('extracted_fields', {})
                            print(f"📊 Used {len(extracted_fields)} extracted fields")
                        
                        # Show quality assessment
                        quality = data.get('quality_assessment', {})
                        if quality:
                            print(f"🎯 Template Quality:")
                            print(f"   Overall: {quality.get('overall_score', 0):.1f}%")
                            print(f"   Assembly Strategy: {quality.get('assembly_strategy', 'unknown')}")
                            print(f"   Format: {quality.get('format_used', 'unknown')}")
                        
                        # Show validation issues
                        validation_issues = data.get('validation_issues', [])
                        if validation_issues:
                            print(f"⚠️ Validation Issues ({len(validation_issues)}):")
                            for issue in validation_issues[:3]:
                                severity = issue.get('severity', 'unknown')
                                description = issue.get('description', 'No description')
                                print(f"   • {severity.upper()}: {description}")
                        else:
                            print("✅ No validation issues found")
                    else:
                        print("❌ Template generation failed")
                        print(f"   Error: {data.get('error_message', 'Unknown error')}")
                    
                    return data
                else:
                    print(f"❌ QME generation failed: {response.status_code}")
                    print(f"   Error: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ QME generation error: {e}")
            return None
    
    def demo_template_validation(self):
        """Demonstrate template validation."""
        print("\n6️⃣ Template Validation Demo")
        print("-" * 40)
        
        try:
            with open(self.sample_file, 'rb') as f:
                files = {'file': ('sample_qme.txt', f, 'text/plain')}
                params = {'validation_level': 'comprehensive'}
                
                print("🔄 Validating template quality...")
                start_time = time.time()
                
                response = requests.post(
                    f"{self.api_base_url}/api/v1/qme/validate",
                    files=files,
                    params=params,
                    timeout=30
                )
                
                processing_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Validation completed in {processing_time:.2f}s")
                    
                    validation_score = data.get('validation_score', 0)
                    print(f"🎯 Validation Score: {validation_score:.1f}%")
                    
                    # Show quality metrics
                    quality_metrics = data.get('quality_metrics', {})
                    if quality_metrics:
                        print("📊 Quality Metrics:")
                        for metric, score in quality_metrics.items():
                            print(f"   {metric.replace('_', ' ').title()}: {score:.1f}%")
                    
                    # Show validation issues
                    validation_issues = data.get('validation_issues', [])
                    if validation_issues:
                        print(f"\n⚠️ Validation Issues ({len(validation_issues)}):")
                        
                        # Group by severity
                        severity_groups = {}
                        for issue in validation_issues:
                            severity = issue.get('severity', 'unknown')
                            if severity not in severity_groups:
                                severity_groups[severity] = []
                            severity_groups[severity].append(issue)
                        
                        for severity, issues in severity_groups.items():
                            print(f"   {severity.upper()} ({len(issues)}):")
                            for issue in issues[:2]:  # Show first 2 of each severity
                                print(f"     • {issue.get('message', 'No message')}")
                    else:
                        print("✅ No validation issues found")
                    
                    # Show recommendations
                    recommendations = data.get('recommendations', [])
                    if recommendations:
                        print(f"\n💡 Recommendations ({len(recommendations)}):")
                        for rec in recommendations[:3]:
                            print(f"   • {rec}")
                    
                    return data
                else:
                    print(f"❌ Validation failed: {response.status_code}")
                    print(f"   Error: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return None
    
    def run_complete_demo(self):
        """Run the complete API demonstration."""
        print("🚀 QME Document Extraction API Demo")
        print("=" * 60)
        print("This demo will test all major API endpoints with a sample QME document.")
        print("=" * 60)
        
        self.setup()
        
        try:
            # Check API health first
            if not self.check_api_health():
                print("\n❌ API is not available. Please start the server first:")
                print("   python scripts/start_extraction_api.py")
                return False
            
            # Run all demos
            results = {}
            
            print("\n" + "="*60)
            results['openrouter'] = self.demo_openrouter_extraction()
            
            print("\n" + "="*60)
            results['multi_layer'] = self.demo_multi_layer_extraction()
            
            print("\n" + "="*60)
            results['comparison'] = self.demo_extraction_comparison()
            
            print("\n" + "="*60)
            results['qme_generation'] = self.demo_qme_generation()
            
            print("\n" + "="*60)
            results['validation'] = self.demo_template_validation()
            
            # Print summary
            self.print_demo_summary(results)
            
            return True
            
        finally:
            self.cleanup()
    
    def print_demo_summary(self, results):
        """Print demo summary."""
        print("\n" + "="*60)
        print("📊 DEMO SUMMARY")
        print("="*60)
        
        successful_demos = sum(1 for result in results.values() if result is not None)
        total_demos = len(results)
        
        print(f"Total demos: {total_demos}")
        print(f"Successful: {successful_demos}")
        print(f"Failed: {total_demos - successful_demos}")
        print(f"Success rate: {(successful_demos / total_demos * 100):.1f}%")
        
        print("\nDemo Results:")
        for demo_name, result in results.items():
            status = "✅ SUCCESS" if result is not None else "❌ FAILED"
            print(f"  {status} {demo_name.replace('_', ' ').title()}")
        
        print("\n💡 Next Steps:")
        print("  • Explore the interactive API docs at /docs")
        print("  • Try uploading your own documents")
        print("  • Experiment with different extraction strategies")
        print("  • Test with various file formats (PDF, DOCX, TXT)")
        print("  • Use the comparison endpoint to find the best method for your documents")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="QME Document Extraction API Demo")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--demo",
        choices=['health', 'openrouter', 'multi-layer', 'compare', 'generate', 'validate', 'all'],
        default='all',
        help="Specific demo to run (default: all)"
    )
    
    args = parser.parse_args()
    
    demo = QMEAPIDemo(api_base_url=args.url)
    
    if args.demo == 'all':
        success = demo.run_complete_demo()
    else:
        demo.setup()
        try:
            if args.demo == 'health':
                success = demo.check_api_health()
            elif args.demo == 'openrouter':
                success = demo.demo_openrouter_extraction() is not None
            elif args.demo == 'multi-layer':
                success = demo.demo_multi_layer_extraction() is not None
            elif args.demo == 'compare':
                success = demo.demo_extraction_comparison() is not None
            elif args.demo == 'generate':
                success = demo.demo_qme_generation() is not None
            elif args.demo == 'validate':
                success = demo.demo_template_validation() is not None
            else:
                success = False
        finally:
            demo.cleanup()
    
    if success:
        print("\n🎉 Demo completed successfully!")
    else:
        print("\n❌ Demo failed. Check the API server and try again.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)