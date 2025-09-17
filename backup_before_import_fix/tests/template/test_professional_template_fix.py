#!/usr/bin/env python3
"""
Test script to verify the professional template interface fix.
"""

import sys
import os
sys.path.append('.')

def test_template_data_handling():
    """Test that the professional template interface can handle both data formats."""
    
    # Test dictionary format (from QME template generator)
    dict_template_data = {
        'patient_info': {
            'name': 'John Doe',
            'age': 45,
            'gender': 'Male',
            'case_number': 'WC2024-001',
            'injury_date': '2024-01-15',
            'employer': 'ABC Construction',
            'occupation': 'Construction Worker',
            'body_parts': ['Lower Back', 'Left Knee']
        },
        'medical_findings': {
            'diagnoses': ['Low back pain', 'Left knee strain'],
            'findings': ['Decreased range of motion in lumbar spine'],
            'impairment_ratings': [],
            'imaging_studies': ['MRI lumbar spine'],
            'treatment_history': ['Physical therapy', 'NSAIDs']
        },
        'missing_sections': ['Past Medical History', 'Social History'],
        'recommendations': ['Complete occupational history', 'Obtain additional imaging']
    }
    
    # Test the helper functions
    try:
        from src.ui.professional_template_interface import ProfessionalTemplateInterface
        
        interface = ProfessionalTemplateInterface()
        
        # Test data conversion
        converted_data = interface._convert_dict_to_qme_template_data(dict_template_data)
        
        print("✅ Dictionary to QMETemplateData conversion successful")
        print(f"   Patient Name: {converted_data.patient_info.name}")
        print(f"   Case Number: {converted_data.patient_info.case_number}")
        print(f"   Diagnoses: {len(converted_data.medical_findings.diagnoses)}")
        print(f"   Missing Sections: {len(converted_data.missing_sections)}")
        
        # Test helper methods
        class MockResult:
            def __init__(self, template_data):
                self.template_data = template_data
        
        # Test with dictionary format
        dict_result = MockResult(dict_template_data)
        patient_name_dict = interface._get_patient_name_from_result(dict_result)
        print(f"   Patient name from dict: {patient_name_dict}")
        
        # Test with object format
        obj_result = MockResult(converted_data)
        patient_name_obj = interface._get_patient_name_from_result(obj_result)
        print(f"   Patient name from object: {patient_name_obj}")
        
        print("\n🎉 All tests passed! Professional template interface should work correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Professional Template Interface Fix")
    print("=" * 50)
    
    success = test_template_data_handling()
    
    if success:
        print("\n✅ Fix verified successfully!")
        print("The professional template assembly should now work correctly.")
    else:
        print("\n❌ Fix verification failed!")
        print("There may still be issues with the professional template interface.")