#!/usr/bin/env python3
"""
Test script for evidence-driven content generation enhancement.

This script tests the enhanced intelligent content generator with evidence-constrained
narrative generation using validated fields and source citation management.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.core.generation.intelligent_content_generator import IntelligentContentGenerator
    from src.infrastructure.knowledge.evidence_rag_service import EvidenceRAGService
    from src.infrastructure.knowledge.ama_guidelines_engine import AMAGuidelinesEngine
    from src.core.validation.qme_field_validator import ValidationReport, ValidationStatus, ConfidenceThresholds
    from src.models.knowledge_graph import KnowledgeGraph
    from src.config.qme_gold_standard_config import QMEGoldStandardConfig
    from src.utils.logging_config import get_logger
except ImportError as e:
    print(f"Import error: {e}")
    print("This test requires the full QME system to be available.")
    sys.exit(1)

def test_evidence_constrained_content_generation():
    """Test evidence-constrained content generation."""
    logger = get_logger(__name__)
    
    try:
        # Initialize components
        knowledge_graph = KnowledgeGraph()
        ama_engine = AMAGuidelinesEngine()
        config = QMEGoldStandardConfig()
        
        # Initialize enhanced content generator
        content_generator = IntelligentContentGenerator(
            ama_engine=ama_engine,
            knowledge_graph=knowledge_graph,
            config=config,
            logger=logger
        )
        
        # Create mock validation report with accepted fields
        validation_report = ValidationReport(
            accepted_fields={
                'patient_name': 'John Doe',
                'case_number': 'WC12345',
                'injury_date': '2023-01-15',
                'injury_mechanism': 'lifting heavy box at work',
                'body_part': 'lumbar spine',
                'primary_diagnosis': 'lumbar strain',
                'rom_measurements': {
                    'flexion': {'degrees': 45, 'normal': 60},
                    'extension': {'degrees': 15, 'normal': 25}
                },
                'current_symptoms': ['lower back pain', 'stiffness', 'limited mobility']
            },
            flagged_fields={
                'treatment_history': ['physical therapy', 'medications']
            },
            missing_fields=['mri_results'],
            overall_confidence=0.75,
            evidence_completeness=0.80,
            critical_field_coverage=0.90,
            can_generate_report=True,
            validation_status=ValidationStatus.ACCEPTED,
            thresholds_used=ConfidenceThresholds()
        )
        
        print("=== Testing Evidence-Constrained Content Generation ===")
        print(f"Validation Status: {validation_report.validation_status.value}")
        print(f"Can Generate Report: {validation_report.can_generate_report}")
        print(f"Accepted Fields: {len(validation_report.accepted_fields)}")
        print(f"Overall Confidence: {validation_report.overall_confidence:.2%}")
        print()
        
        # Test individual section generation
        sections_to_test = [
            'History of Present Illness',
            'Physical Examination', 
            'Diagnostic Studies',
            'Causation Analysis',
            'Future Medical Care'
        ]
        
        for section in sections_to_test:
            print(f"--- Testing {section} ---")
            
            try:
                narrative = content_generator.generate_evidence_constrained_section_content(
                    section_name=section,
                    validation_report=validation_report,
                    context={'case_type': 'workers_compensation'}
                )
                
                print(f"Section: {narrative.section_name}")
                print(f"Confidence: {narrative.confidence_score:.2%}")
                print(f"Content Length: {len(narrative.content)} characters")
                print(f"Validated Fields Used: {len(narrative.validated_fields_used)}")
                print(f"Evidence Snippets: {len(narrative.evidence_snippets)}")
                print(f"Source Citations: {len(narrative.source_citations)}")
                print(f"Placeholder Text Removed: {narrative.placeholder_text_removed}")
                print(f"Evidence Backing Complete: {narrative.evidence_backing_complete}")
                print(f"Content Preview: {narrative.content[:200]}...")
                print()
                
            except Exception as e:
                print(f"Error testing {section}: {str(e)}")
                print()
        
        # Test comprehensive report generation
        print("--- Testing Comprehensive Evidence Report Generation ---")
        
        try:
            comprehensive_content = content_generator.generate_comprehensive_evidence_report_content(
                validation_report=validation_report,
                sections=sections_to_test,
                context={'case_type': 'workers_compensation'}
            )
            
            print(f"Generated {len(comprehensive_content)} sections")
            
            total_confidence = sum(narrative.confidence_score for narrative in comprehensive_content.values())
            avg_confidence = total_confidence / len(comprehensive_content) if comprehensive_content else 0
            
            print(f"Average Confidence: {avg_confidence:.2%}")
            
            # Check evidence backing completeness
            complete_backing = sum(1 for narrative in comprehensive_content.values() 
                                 if narrative.evidence_backing_complete)
            print(f"Sections with Complete Evidence Backing: {complete_backing}/{len(comprehensive_content)}")
            
            # Check placeholder text removal
            placeholder_free = sum(1 for narrative in comprehensive_content.values() 
                                 if narrative.placeholder_text_removed)
            print(f"Sections with Placeholder Text Removed: {placeholder_free}/{len(comprehensive_content)}")
            
            print()
            
        except Exception as e:
            print(f"Error testing comprehensive report generation: {str(e)}")
            print()
        
        # Test insufficient evidence scenario
        print("--- Testing Insufficient Evidence Scenario ---")
        
        insufficient_validation = ValidationReport(
            accepted_fields={'patient_name': 'Jane Doe'},
            flagged_fields={},
            missing_fields=['case_number', 'injury_date', 'primary_diagnosis'],
            overall_confidence=0.25,
            evidence_completeness=0.30,
            critical_field_coverage=0.20,
            can_generate_report=False,
            validation_status=ValidationStatus.MISSING,
            thresholds_used=ConfidenceThresholds()
        )
        
        try:
            insufficient_content = content_generator.generate_comprehensive_evidence_report_content(
                validation_report=insufficient_validation,
                sections=['History of Present Illness'],
                context={}
            )
            
            if insufficient_content:
                narrative = list(insufficient_content.values())[0]
                print(f"Insufficient Evidence Content: {narrative.content[:200]}...")
                print(f"Confidence: {narrative.confidence_score:.2%}")
            
        except Exception as e:
            print(f"Error testing insufficient evidence scenario: {str(e)}")
        
        print("\n=== Evidence-Constrained Content Generation Test Complete ===")
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_evidence_constrained_content_generation()