"""
QME Gold Standard Configuration.

This module defines the gold standard requirements extracted from 
AI Example QME Report Template.docx and reference materials.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class QMEGoldStandardConfig:
    """Configuration for QME gold standard requirements."""
    
    # Required sections in order (from AI Example QME Report Template.docx)
    REQUIRED_SECTIONS = [
        "patient_identification",
        "history_of_present_illness", 
        "past_medical_history",
        "social_history",
        "occupational_history",
        "review_of_systems",
        "physical_examination",
        "diagnostic_studies",
        "diagnosis",
        "impairment_rating",
        "work_restrictions",
        "future_medical_care",
        "causation_analysis",
        "apportionment"
    ]
    
    # Patient identification requirements
    PATIENT_ID_REQUIREMENTS = {
        "required_fields": [
            "full_name",
            "date_of_birth", 
            "age",
            "gender",
            "case_number",
            "claim_number",
            "date_of_injury",
            "employer",
            "occupation",
            "body_parts_injured"
        ],
        "optional_fields": [
            "medical_record_number",
            "social_security_number",
            "address",
            "phone_number"
        ],
        "validation_patterns": {
            "case_number": r"^[A-Z0-9\-]{5,20}$",
            "date_format": r"^\d{1,2}\/\d{1,2}\/\d{4}$",
            "age_range": (16, 100)
        }
    }
    
    # History section requirements
    HISTORY_REQUIREMENTS = {
        "present_illness": {
            "min_length": 500,
            "required_elements": [
                "mechanism_of_injury",
                "date_time_of_injury", 
                "initial_symptoms",
                "symptom_progression",
                "current_symptoms",
                "pain_description",
                "functional_limitations",
                "aggravating_factors",
                "relieving_factors"
            ],
            "content_patterns": [
                r"(?:injured|hurt|pain).*(?:on|date|when)",
                r"(?:describes?|reports?|states?).*(?:pain|symptoms?)",
                r"\d{1,2}\/\d{1,2}\/\d{4}",  # Date pattern
                r"(?:sharp|dull|aching|burning|stabbing|throbbing)"  # Pain descriptors
            ]
        },
        "past_medical_history": {
            "min_length": 200,
            "required_elements": [
                "prior_injuries",
                "surgeries",
                "medications",
                "allergies",
                "medical_conditions"
            ]
        },
        "social_history": {
            "required_elements": [
                "smoking_status",
                "alcohol_use",
                "recreational_activities",
                "living_situation"
            ]
        },
        "occupational_history": {
            "required_elements": [
                "current_job_duties",
                "physical_demands",
                "work_environment",
                "previous_occupations",
                "return_to_work_status"
            ]
        }
    }
    
    # Physical examination requirements
    EXAMINATION_REQUIREMENTS = {
        "general_appearance": {
            "required_elements": [
                "overall_appearance",
                "distress_level",
                "cooperation",
                "gait_observation"
            ]
        },
        "musculoskeletal": {
            "required_measurements": [
                "range_of_motion",
                "strength_testing",
                "muscle_atrophy",
                "deformities",
                "tenderness",
                "swelling"
            ],
            "measurement_standards": {
                "rom_units": "degrees",
                "strength_scale": "0-5 scale",
                "documentation": "bilateral_comparison"
            }
        },
        "neurological": {
            "required_tests": [
                "sensory_testing",
                "motor_function",
                "reflexes",
                "coordination",
                "special_tests"
            ]
        },
        "special_tests": {
            "spine": [
                "straight_leg_raise",
                "spurling_test",
                "compression_test",
                "distraction_test"
            ],
            "extremities": [
                "impingement_tests",
                "stability_tests",
                "provocative_tests"
            ]
        }
    }
    
    # Diagnostic studies requirements
    DIAGNOSTIC_REQUIREMENTS = {
        "imaging_studies": {
            "types": ["x_ray", "mri", "ct_scan", "bone_scan", "emg"],
            "required_elements": [
                "study_type",
                "date_performed",
                "findings",
                "interpretation",
                "correlation_with_symptoms"
            ]
        },
        "laboratory_tests": {
            "types": ["blood_work", "inflammatory_markers", "specific_tests"],
            "documentation": "results_and_interpretation"
        }
    }
    
    # Diagnosis requirements
    DIAGNOSIS_REQUIREMENTS = {
        "primary_diagnosis": {
            "required": True,
            "elements": [
                "condition_name",
                "icd_10_code",
                "anatomical_location",
                "severity_assessment"
            ]
        },
        "secondary_diagnoses": {
            "required": False,
            "max_count": 5
        },
        "differential_diagnoses": {
            "required": False,
            "documentation": "ruled_out_conditions"
        },
        "icd_coding": {
            "version": "ICD-10-CM",
            "format_pattern": r"^[A-Z]\d{2}(?:\.\d{1,3})?$",
            "required_specificity": "highest_level_available"
        }
    }
    
    # Impairment rating requirements (AMA Guides 5th Edition)
    IMPAIRMENT_REQUIREMENTS = {
        "methodology": {
            "guide_version": "AMA Guides to the Evaluation of Permanent Impairment, 5th Edition",
            "required_elements": [
                "body_system_chapter",
                "table_reference",
                "measurement_method",
                "calculation_steps",
                "final_percentage"
            ]
        },
        "documentation": {
            "measurements": "objective_findings_required",
            "calculations": "show_all_steps",
            "references": "specific_table_citations",
            "rationale": "explain_rating_basis"
        },
        "validation_rules": {
            "percentage_range": (0, 100),
            "whole_person_vs_regional": "specify_type",
            "combination_rules": "use_combined_values_chart",
            "rounding": "standard_ama_rounding"
        }
    }
    
    # Work restrictions requirements
    WORK_RESTRICTIONS = {
        "categories": [
            "lifting_restrictions",
            "carrying_restrictions", 
            "pushing_pulling_restrictions",
            "postural_restrictions",
            "environmental_restrictions",
            "repetitive_motion_restrictions"
        ],
        "documentation": {
            "specific_limitations": True,
            "weight_limits": "pounds_specified",
            "frequency_limits": "occasional_frequent_constant",
            "duration_limits": "time_based_restrictions"
        }
    }
    
    # Future medical care requirements
    FUTURE_CARE_REQUIREMENTS = {
        "categories": [
            "ongoing_treatment",
            "medications",
            "therapy_services",
            "diagnostic_studies",
            "surgical_interventions",
            "medical_equipment"
        ],
        "documentation": {
            "medical_necessity": "justify_each_recommendation",
            "frequency": "specify_treatment_schedule",
            "duration": "estimate_treatment_length",
            "cost_considerations": "reasonable_and_necessary"
        }
    }
    
    # Causation analysis requirements
    CAUSATION_REQUIREMENTS = {
        "elements": [
            "medical_probability_statement",
            "mechanism_analysis",
            "temporal_relationship",
            "alternative_causes_considered",
            "supporting_evidence"
        ],
        "probability_standards": {
            "language": "reasonable_medical_probability",
            "threshold": "more_likely_than_not",
            "certainty_levels": ["probable", "possible", "unlikely"]
        }
    }
    
    # Apportionment requirements
    APPORTIONMENT_REQUIREMENTS = {
        "factors": [
            "pre_existing_conditions",
            "subsequent_injuries",
            "degenerative_changes",
            "non_industrial_factors"
        ],
        "documentation": {
            "percentage_allocation": "specific_percentages",
            "rationale": "detailed_explanation",
            "medical_basis": "objective_evidence"
        }
    }
    
    # Formatting requirements (from gold standard template)
    FORMATTING_REQUIREMENTS = {
        "document_structure": {
            "header": {
                "required": True,
                "elements": ["doctor_name", "license_number", "report_date"]
            },
            "footer": {
                "required": True,
                "elements": ["page_numbers", "confidentiality_notice"]
            },
            "margins": {
                "top": 1.0,
                "bottom": 1.0, 
                "left": 1.0,
                "right": 1.0
            }
        },
        "typography": {
            "font_family": "Times New Roman",
            "font_size": 12,
            "line_spacing": 1.5,
            "paragraph_spacing": 6
        },
        "section_formatting": {
            "headers": {
                "style": "bold",
                "numbering": True,
                "spacing_before": 12,
                "spacing_after": 6
            },
            "subsections": {
                "indentation": 0.5,
                "bullet_style": "standard"
            }
        }
    }
    
    # Quality indicators
    QUALITY_INDICATORS = {
        "completeness": {
            "all_sections_present": 100,
            "required_fields_complete": 90,
            "optional_fields_complete": 70
        },
        "accuracy": {
            "measurements_documented": 95,
            "calculations_correct": 100,
            "references_accurate": 95
        },
        "compliance": {
            "ama_guidelines_followed": 100,
            "legal_requirements_met": 100,
            "formatting_standards": 85
        }
    }
    
    # Content validation patterns
    CONTENT_PATTERNS = {
        "medical_terminology": {
            "required_precision": True,
            "abbreviation_standards": "spell_out_first_use",
            "technical_accuracy": "peer_review_level"
        },
        "objective_language": {
            "avoid_subjective_terms": ["seems", "appears", "probably"],
            "use_precise_descriptors": True,
            "quantify_when_possible": True
        },
        "professional_tone": {
            "formal_language": True,
            "third_person_perspective": True,
            "clinical_objectivity": True
        }
    }


# Global configuration instance
qme_config = QMEGoldStandardConfig()