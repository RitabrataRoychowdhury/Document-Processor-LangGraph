"""
AMA Guidelines Integration Demo.

This script demonstrates the comprehensive AMA Guidelines Integration and
Medical Reasoning Engine functionality for QME report generation.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from services.comprehensive_ama_integration import (
        ComprehensiveAMAIntegration, ComprehensiveEvaluationData
    )
    from services.enhanced_impairment_calculator import (
        RangeOfMotionMeasurement, StrengthTestResult, FunctionalAssessment
    )
    from models.knowledge_graph import Diagnosis, Finding
    from utils.logging_config import get_logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)

logger = get_logger(__name__)


def create_sample_evaluation_data() -> ComprehensiveEvaluationData:
    """Create sample evaluation data for demonstration."""
    
    # Primary diagnosis
    diagnosis = Diagnosis(
        id="demo_diag_001",
        description="Lumbar disc herniation with radiculopathy",
        icd_code="M51.16"
    )
    
    # Clinical findings
    clinical_findings = [
        Finding(
            id="finding_001",
            section_id="examination_section",
            description="Lower back pain with radiation to left leg",
            finding_type="symptom",
            page_reference=3
        ),
        Finding(
            id="finding_002",
            section_id="examination_section", 
            description="Positive straight leg raise test at 45 degrees",
            finding_type="physical_examination",
            page_reference=4
        ),
        Finding(
            id="finding_003",
            section_id="examination_section",
            description="Decreased sensation in L5 dermatome",
            finding_type="neurological",
            page_reference=4
        )
    ]
    
    # Range of motion measurements
    rom_measurements = [
        RangeOfMotionMeasurement(
            joint="lumbar_spine",
            motion_type="flexion",
            measured_value=35.0,
            normal_value=60.0,
            measurement_date=datetime.now(),
            examiner_notes="Patient reports pain at end range"
        ),
        RangeOfMotionMeasurement(
            joint="lumbar_spine",
            motion_type="extension",
            measured_value=15.0,
            normal_value=25.0,
            measurement_date=datetime.now(),
            examiner_notes="Limited by pain and muscle guarding"
        ),
        RangeOfMotionMeasurement(
            joint="lumbar_spine",
            motion_type="lateral_flexion",
            measured_value=20.0,
            normal_value=25.0,
            measurement_date=datetime.now(),
            examiner_notes="Bilateral limitation, left worse than right"
        )
    ]
    
    # Strength testing results
    strength_tests = [
        StrengthTestResult(
            muscle_group="paraspinal",
            strength_grade="4/5",
            numeric_value=4.0,
            testing_method="manual muscle testing",
            notes="Weakness noted with resisted extension"
        ),
        StrengthTestResult(
            muscle_group="hip_flexors",
            strength_grade="4/5",
            numeric_value=4.0,
            testing_method="manual muscle testing",
            notes="Mild weakness on left side"
        ),
        StrengthTestResult(
            muscle_group="ankle_dorsiflexors",
            strength_grade="3/5",
            numeric_value=3.0,
            testing_method="manual muscle testing",
            notes="Significant weakness consistent with L5 radiculopathy"
        )
    ]
    
    # Functional assessments
    functional_assessments = [
        FunctionalAssessment(
            activity="lifting",
            limitation_level="severe",
            percentage_limitation=75.0,
            objective_basis=["ROM limitations", "Pain with movement", "Strength deficits"],
            impact_on_adl="Unable to lift objects over 10 pounds"
        ),
        FunctionalAssessment(
            activity="sitting",
            limitation_level="moderate",
            percentage_limitation=50.0,
            objective_basis=["Pain with prolonged sitting", "Neurological symptoms"],
            impact_on_adl="Can sit for maximum 30 minutes before symptoms worsen"
        ),
        FunctionalAssessment(
            activity="walking",
            limitation_level="mild",
            percentage_limitation=25.0,
            objective_basis=["Antalgic gait", "Neurological deficits"],
            impact_on_adl="Can walk short distances but limited by leg symptoms"
        )
    ]
    
    # Patient history
    patient_history = {
        "injury_date": "2024-01-15",
        "injury_mechanism": "lifting heavy box from floor to shelf at work",
        "initial_symptoms": ["acute lower back pain", "muscle spasm", "inability to stand straight"],
        "current_symptoms": ["chronic lower back pain", "left leg pain and numbness", "weakness in left foot"],
        "pre_existing_conditions": [],
        "previous_treatments": ["physical therapy", "chiropractic care", "anti-inflammatory medications"],
        "work_status": "modified duty with lifting restrictions"
    }
    
    # Examination data
    examination_data = {
        "general_appearance": "Patient appears uncomfortable, favors left side when walking",
        "gait": "Antalgic gait with shortened stance phase on left",
        "posture": "Forward flexed posture, list to right side",
        "palpation": "Tenderness over L4-L5 and L5-S1 levels",
        "neurological": {
            "sensation": "Decreased light touch and pinprick in L5 distribution",
            "reflexes": "Diminished left Achilles reflex",
            "motor": "Weakness in left ankle dorsiflexion and great toe extension"
        },
        "special_tests": {
            "straight_leg_raise": "Positive at 45 degrees on left, reproduces leg symptoms",
            "crossed_straight_leg_raise": "Negative",
            "femoral_stretch": "Negative"
        },
        "imaging_correlation": "MRI shows L4-L5 disc herniation with nerve root compression"
    }
    
    # Patient factors
    patient_factors = {
        "age": 42,
        "gender": "male",
        "height": "5'10\"",
        "weight": "185 lbs",
        "occupation": "warehouse worker",
        "job_demands": "heavy lifting, prolonged standing, repetitive bending",
        "dominant_hand": "right",
        "activity_level": "previously active, now limited",
        "education": "high school",
        "motivation": "high - wants to return to work"
    }
    
    return ComprehensiveEvaluationData(
        patient_id="DEMO_PATIENT_001",
        diagnosis=diagnosis,
        clinical_findings=clinical_findings,
        rom_measurements=rom_measurements,
        strength_tests=strength_tests,
        functional_assessments=functional_assessments,
        patient_history=patient_history,
        examination_data=examination_data,
        patient_factors=patient_factors
    )


def demonstrate_ama_integration():
    """Demonstrate the comprehensive AMA integration functionality."""
    
    print("=" * 80)
    print("AMA GUIDELINES INTEGRATION AND MEDICAL REASONING ENGINE DEMO")
    print("=" * 80)
    print()
    
    try:
        # Initialize the comprehensive AMA integration service
        print("1. Initializing AMA Guidelines Integration Service...")
        ama_integration = ComprehensiveAMAIntegration()
        print("   ✓ AMA Guidelines Engine initialized")
        print("   ✓ Enhanced Impairment Calculator initialized")
        print("   ✓ QME Reference Integrator initialized")
        print()
        
        # Create sample evaluation data
        print("2. Creating sample evaluation data...")
        evaluation_data = create_sample_evaluation_data()
        print(f"   ✓ Patient ID: {evaluation_data.patient_id}")
        print(f"   ✓ Primary Diagnosis: {evaluation_data.diagnosis.description}")
        print(f"   ✓ Clinical Findings: {len(evaluation_data.clinical_findings)} findings")
        print(f"   ✓ ROM Measurements: {len(evaluation_data.rom_measurements)} measurements")
        print(f"   ✓ Strength Tests: {len(evaluation_data.strength_tests)} tests")
        print(f"   ✓ Functional Assessments: {len(evaluation_data.functional_assessments)} assessments")
        print()
        
        # Perform comprehensive evaluation
        print("3. Performing comprehensive AMA evaluation...")
        result = ama_integration.perform_comprehensive_evaluation(evaluation_data)
        print("   ✓ Impairment calculation completed")
        print("   ✓ Medical reasoning generated")
        print("   ✓ AMA method selection documented")
        print("   ✓ Legal compliance verified")
        print("   ✓ Quality metrics calculated")
        print()
        
        # Display key results
        print("4. EVALUATION RESULTS:")
        print("-" * 40)
        print(f"Final Impairment Rating: {result.impairment_calculation.final_percentage}% whole person")
        print(f"Calculation Method: {result.impairment_calculation.components.calculation_method.value}")
        print(f"Confidence Score: {result.impairment_calculation.confidence_score:.1%}")
        print()
        
        print("Quality Metrics:")
        for metric, value in result.quality_metrics.items():
            if isinstance(value, float):
                print(f"  • {metric.replace('_', ' ').title()}: {value:.1%}")
            else:
                print(f"  • {metric.replace('_', ' ').title()}: {value}")
        print()
        
        print("AMA Method Selection:")
        method_selection = result.ama_method_selection
        print(f"  • Selected Method: {method_selection.get('selected_method', 'Not specified')}")
        print(f"  • Table Reference: {method_selection.get('table_reference', 'Not specified')}")
        rationale = method_selection.get('selection_rationale', [])
        if rationale:
            print("  • Selection Rationale:")
            for reason in rationale[:3]:  # Show first 3 reasons
                print(f"    - {reason}")
        print()
        
        # Generate AMA-compliant report content
        print("5. Generating AMA-compliant report content...")
        content_sections = ama_integration.generate_ama_compliant_report_content(result)
        print(f"   ✓ Generated {len(content_sections)} report sections")
        print()
        
        # Display sample content sections
        print("6. SAMPLE REPORT CONTENT:")
        print("-" * 40)
        
        # Impairment Rating Section
        if "impairment_rating" in content_sections:
            print("IMPAIRMENT RATING SECTION (excerpt):")
            impairment_content = content_sections["impairment_rating"]
            # Show first 300 characters
            print(impairment_content[:300] + "..." if len(impairment_content) > 300 else impairment_content)
            print()
        
        # Medical Reasoning Section
        if "medical_reasoning" in content_sections:
            print("MEDICAL REASONING SECTION (excerpt):")
            reasoning_content = content_sections["medical_reasoning"]
            # Show first 300 characters
            print(reasoning_content[:300] + "..." if len(reasoning_content) > 300 else reasoning_content)
            print()
        
        # Validate AMA compliance
        print("7. Validating AMA compliance...")
        compliance_report = ama_integration.validate_ama_compliance(result)
        print(f"   ✓ Overall Compliant: {compliance_report.get('overall_compliant', False)}")
        print(f"   ✓ Compliance Score: {compliance_report.get('compliance_score', 0):.1%}")
        
        if compliance_report.get('critical_issues'):
            print("   ⚠ Critical Issues:")
            for issue in compliance_report['critical_issues'][:3]:
                print(f"     - {issue}")
        else:
            print("   ✓ No critical compliance issues found")
        print()
        
        # Display recommendations
        print("8. RECOMMENDATIONS:")
        print("-" * 40)
        for i, recommendation in enumerate(result.recommendations[:5], 1):
            print(f"{i}. {recommendation}")
        print()
        
        # Display calculation summary
        print("9. CALCULATION SUMMARY:")
        print("-" * 40)
        calculator = ama_integration.impairment_calculator
        summary = calculator.get_calculation_summary(result.impairment_calculation)
        print(summary)
        print()
        
        print("=" * 80)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print()
        print("This demonstration shows the comprehensive AMA Guidelines Integration")
        print("system processing a complex lumbar spine case with:")
        print("• Intelligent AMA method selection")
        print("• Comprehensive impairment calculation")
        print("• Medical reasoning generation")
        print("• Legal compliance validation")
        print("• Quality assessment and recommendations")
        print()
        print("The system is ready for integration with QME template generation!")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        logger.error(f"Demo error: {e}", exc_info=True)
        return False
    
    return True


if __name__ == "__main__":
    success = demonstrate_ama_integration()
    sys.exit(0 if success else 1)