#!/usr/bin/env python3
"""
QME Template Generation Demo

This script demonstrates the QME template generation system by:
1. Creating a sample patient with medical data
2. Processing patient documents to extract information
3. Generating a QME template in DOCX format
4. Showing missing information detection
"""

import os
import sys
import tempfile
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from services.qme_template_generator import (
        QMETemplateGenerator, PatientInfo, MedicalFindings, QMETemplateData,
        PatientDocumentProcessor, KnowledgeGraphMatcher, MissingInformationDetector
    )
    from models.knowledge_graph import Patient, Diagnosis, Finding, Section, ImpairmentRating
    from repositories.patient_repository import SQLitePatientRepository
    from repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
    from commands.template_command import TemplateCommand
    from utils.logging_config import get_logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the project root directory with PYTHONPATH=src")
    sys.exit(1)

logger = get_logger(__name__)


def create_sample_patient() -> Patient:
    """Create a sample patient for demonstration."""
    patient = Patient(
        id="demo_patient_001",
        name="John Smith",
        age=45,
        gender="Male",
        case_number="WC-2024-001234",
        medical_record_number="MRN-789456"
    )
    return patient


def create_sample_medical_data() -> tuple:
    """Create sample medical data for demonstration."""
    # Sample sections
    sections = [
        Section(
            id="sec_001",
            document_id="doc_001",
            section_type="history",
            page_number=1,
            text_content="Patient is a 45-year-old male who sustained a work-related injury to his lower back on 03/15/2024 while lifting heavy boxes. He reports constant lower back pain radiating to his left leg."
        ),
        Section(
            id="sec_002",
            document_id="doc_001",
            section_type="examination",
            page_number=2,
            text_content="Physical examination reveals limited range of motion in lumbar spine. Straight leg raise test positive on the left at 45 degrees. Muscle strength 4/5 in left lower extremity."
        ),
        Section(
            id="sec_003",
            document_id="doc_001",
            section_type="diagnostic",
            page_number=3,
            text_content="MRI of lumbar spine shows L4-L5 disc herniation with nerve root compression. No evidence of spinal stenosis."
        )
    ]
    
    # Sample diagnoses
    diagnoses = [
        Diagnosis(
            id="diag_001",
            icd_code="M51.26",
            description="Lumbar disc herniation with radiculopathy",
            severity="moderate",
            certainty=0.9,
            source_section_id="sec_001",
            page_reference=1
        )
    ]
    
    # Sample findings
    findings = [
        Finding(
            id="find_001",
            section_id="sec_002",
            finding_type="physical",
            description="Limited lumbar range of motion",
            page_reference=2
        ),
        Finding(
            id="find_002",
            section_id="sec_002",
            finding_type="neurological",
            description="Positive straight leg raise test",
            page_reference=2
        )
    ]
    
    # Sample impairment rating
    impairment_ratings = [
        ImpairmentRating(
            id="rating_001",
            diagnosis_id="diag_001",
            ama_table="15-3",
            percentage=12.0,
            rationale="Based on DRE Category III - radiculopathy with objective neurological findings",
            source_page=150
        )
    ]
    
    return sections, diagnoses, findings, impairment_ratings


def demonstrate_patient_info_extraction():
    """Demonstrate patient information extraction."""
    print("\n" + "="*60)
    print("PATIENT INFORMATION EXTRACTION DEMO")
    print("="*60)
    
    processor = PatientDocumentProcessor()
    
    # Sample document text
    sample_text = """
    QUALIFIED MEDICAL EVALUATOR'S REPORT
    
    Patient: John Smith
    Age: 45 years old
    Gender: Male
    Case Number: WC-2024-001234
    Medical Record Number: MRN-789456
    Date of Injury: 03/15/2024
    
    The patient is a 45-year-old male construction worker who injured his back 
    while lifting heavy boxes at work. He works for ABC Construction Company.
    The injury affected his lower back and left leg.
    """
    
    patient_info = processor.extract_patient_info(sample_text, "demo_doc")
    
    print(f"Extracted Patient Information:")
    print(f"  Name: {patient_info.name}")
    print(f"  Age: {patient_info.age}")
    print(f"  Gender: {patient_info.gender}")
    print(f"  Case Number: {patient_info.case_number}")
    print(f"  MRN: {patient_info.medical_record_number}")
    print(f"  Body Parts: {', '.join(patient_info.body_parts)}")
    print(f"  Occupation: {patient_info.occupation}")
    print(f"  Employer: {patient_info.employer}")
    
    return patient_info


def demonstrate_missing_information_detection():
    """Demonstrate missing information detection."""
    print("\n" + "="*60)
    print("MISSING INFORMATION DETECTION DEMO")
    print("="*60)
    
    detector = MissingInformationDetector()
    
    # Create incomplete template data
    incomplete_patient_info = PatientInfo(
        name="John Smith",
        age=None,  # Missing age
        case_number="",  # Missing case number
        injury_date=None  # Missing injury date
    )
    
    incomplete_medical_findings = MedicalFindings()  # Empty findings
    
    template_data = QMETemplateData(
        patient_info=incomplete_patient_info,
        medical_findings=incomplete_medical_findings
    )
    
    missing_info = detector.detect_missing_information(template_data)
    
    print(f"Detected {len(missing_info)} missing information items:")
    for i, info in enumerate(missing_info, 1):
        print(f"\n{i}. {info.section_name} - {info.priority.upper()} PRIORITY")
        print(f"   Issue: {info.description}")
        print(f"   Suggestions:")
        for suggestion in info.suggestions:
            print(f"     - {suggestion}")


def demonstrate_qme_template_generation():
    """Demonstrate complete QME template generation."""
    print("\n" + "="*60)
    print("QME TEMPLATE GENERATION DEMO")
    print("="*60)
    
    try:
        # Create repositories (using in-memory for demo)
        patient_repo = SQLitePatientRepository()
        kg_repo = SQLiteKnowledgeGraphRepository()
        
        # Create sample patient
        patient = create_sample_patient()
        patient_repo.save(patient)
        print(f"Created sample patient: {patient.name} (ID: {patient.id})")
        
        # Create sample medical data
        sections, diagnoses, findings, impairment_ratings = create_sample_medical_data()
        
        # Save sample data to knowledge graph
        for section in sections:
            kg_repo.save_section(section)
        
        for diagnosis in diagnoses:
            kg_repo.save_diagnosis(diagnosis)
        
        for finding in findings:
            kg_repo.save_finding(finding)
        
        for rating in impairment_ratings:
            kg_repo.save_impairment_rating(rating)
        
        print(f"Created sample medical data:")
        print(f"  - {len(sections)} sections")
        print(f"  - {len(diagnoses)} diagnoses")
        print(f"  - {len(findings)} findings")
        print(f"  - {len(impairment_ratings)} impairment ratings")
        
        # Generate QME template
        generator = QMETemplateGenerator(patient_repo, kg_repo)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "demo_qme_report.docx")
            
            print(f"\nGenerating QME template...")
            file_path, template_data = generator.generate_qme_template(
                patient.id, 
                output_path
            )
            
            print(f"✓ QME template generated successfully!")
            print(f"  File: {file_path}")
            print(f"  Size: {os.path.getsize(file_path)} bytes")
            
            # Show template data summary
            print(f"\nTemplate Data Summary:")
            print(f"  Patient: {template_data.patient_info.name}")
            print(f"  Case: {template_data.patient_info.case_number}")
            print(f"  Diagnoses: {len(template_data.medical_findings.diagnoses)}")
            print(f"  Findings: {len(template_data.medical_findings.findings)}")
            print(f"  Impairment Ratings: {len(template_data.medical_findings.impairment_ratings)}")
            print(f"  Missing Sections: {len(template_data.missing_sections)}")
            
            if template_data.missing_sections:
                print(f"  Missing: {', '.join(template_data.missing_sections)}")
            
            # Copy file to current directory for inspection
            import shutil
            final_path = "demo_qme_report.docx"
            shutil.copy2(file_path, final_path)
            print(f"\n✓ Template copied to: {final_path}")
            print("  You can open this file in Microsoft Word to review the generated template.")
            
            return template_data
            
    except Exception as e:
        print(f"Error during template generation: {e}")
        logger.error(f"Template generation error: {e}", exc_info=True)
        return None


def demonstrate_template_command():
    """Demonstrate using the template command."""
    print("\n" + "="*60)
    print("TEMPLATE COMMAND DEMO")
    print("="*60)
    
    try:
        # Create a mock template generator for demo
        from unittest.mock import Mock
        
        mock_generator = Mock()
        mock_patient = create_sample_patient()
        mock_generator.patient_repository.find_by_id.return_value = mock_patient
        
        # Create sample template data
        template_data = QMETemplateData(
            patient_info=PatientInfo(
                name=mock_patient.name,
                case_number=mock_patient.case_number,
                age=mock_patient.age
            ),
            medical_findings=MedicalFindings()
        )
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            mock_generator.generate_qme_template.return_value = (temp_path, template_data)
            
            # Create and execute command
            command = TemplateCommand(
                patient_id=mock_patient.id,
                template_generator=mock_generator
            )
            
            print(f"Executing template command for patient: {mock_patient.id}")
            result = command.execute()
            
            print(f"Command Result:")
            print(f"  Success: {result.success}")
            print(f"  Message: {result.message}")
            print(f"  Status: {result.status.value}")
            
            if result.success:
                print(f"  Patient ID: {result.data.get('patient_id')}")
                print(f"  File Path: {result.data.get('file_path')}")
                print(f"  Diagnoses: {result.data.get('diagnoses_count', 0)}")
                print(f"  Findings: {result.data.get('findings_count', 0)}")
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        print(f"Error during command demo: {e}")
        logger.error(f"Command demo error: {e}", exc_info=True)


def main():
    """Run all demonstrations."""
    print("QME TEMPLATE GENERATION SYSTEM DEMO")
    print("This demo shows the complete QME template generation workflow")
    
    try:
        # 1. Patient information extraction
        patient_info = demonstrate_patient_info_extraction()
        
        # 2. Missing information detection
        demonstrate_missing_information_detection()
        
        # 3. Complete template generation
        template_data = demonstrate_qme_template_generation()
        
        # 4. Template command usage
        demonstrate_template_command()
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nKey Features Demonstrated:")
        print("✓ Patient information extraction from text")
        print("✓ Medical findings processing with NER")
        print("✓ Knowledge graph matching for impairment ratings")
        print("✓ Missing information detection and suggestions")
        print("✓ DOCX template generation following QME format")
        print("✓ Command pattern implementation")
        
        if os.path.exists("demo_qme_report.docx"):
            print(f"\n📄 Generated template saved as: demo_qme_report.docx")
            print("   Open this file in Microsoft Word to review the QME report structure.")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        logger.error(f"Demo error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()