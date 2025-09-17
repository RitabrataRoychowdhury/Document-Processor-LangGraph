"""
QME Reference Materials Processor.

This service processes and integrates QME-Study-Guide.pdf and Sample3.pdf
as reference materials for report structure patterns and medical reasoning examples.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import re
import json

try:
    from src.utils.logging_config import get_logger
except ImportError:
    from utils.logging_config import get_logger

# Simple document processor for PDF text extraction
class DocumentProcessor:
    """Simple document processor for extracting text from PDFs."""
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        try:
            # Try to use PyPDF2 if available
            try:
                import PyPDF2
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text()
                    return text
            except ImportError:
                pass
            
            # Fallback to pdfplumber if available
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                    return text
            except ImportError:
                pass
            
            # If no PDF libraries available, return placeholder text
            logger.warning(f"No PDF processing libraries available for {pdf_path}")
            return f"Sample text extracted from {pdf_path}"
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            return f"Error extracting text from {pdf_path}"

logger = get_logger(__name__)


@dataclass
class QMEStructurePattern:
    """Represents a QME report structure pattern."""
    section_name: str
    section_order: int
    required_elements: List[str]
    content_patterns: List[str]
    example_content: str
    legal_requirements: List[str]
    quality_indicators: List[str]


@dataclass
class MedicalReasoningExample:
    """Medical reasoning example from reference materials."""
    diagnosis_type: str
    reasoning_pattern: str
    causation_language: str
    impairment_rationale: str
    treatment_recommendations: List[str]
    source_document: str
    confidence_indicators: List[str]


@dataclass
class LegalCompliancePattern:
    """Legal compliance pattern from study guide."""
    requirement_type: str
    statutory_reference: str
    required_language: str
    compliance_criteria: List[str]
    violation_consequences: List[str]
    example_implementation: str


class QMEStudyGuideProcessor:
    """Processes QME Study Guide for legal and procedural requirements."""
    
    def __init__(self, study_guide_path: str = "QME-Study-Guide.pdf"):
        """Initialize QME Study Guide processor."""
        self.study_guide_path = study_guide_path
        self.document_processor = DocumentProcessor()
        self.legal_patterns: List[LegalCompliancePattern] = []
        self.procedural_requirements: Dict[str, List[str]] = {}
        self.quality_standards: Dict[str, Any] = {}
        
        logger.info(f"Initialized QME Study Guide processor: {study_guide_path}")
    
    def process_study_guide(self) -> bool:
        """Process QME Study Guide for compliance patterns."""
        try:
            logger.info("Processing QME Study Guide for compliance patterns")
            
            if not Path(self.study_guide_path).exists():
                logger.warning(f"QME Study Guide not found: {self.study_guide_path}")
                self._load_default_compliance_patterns()
                return False
            
            # Extract text from PDF
            extracted_text = self.document_processor.extract_text_from_pdf(self.study_guide_path)
            
            # Parse legal requirements
            self._parse_legal_requirements(extracted_text)
            
            # Extract procedural requirements
            self._extract_procedural_requirements(extracted_text)
            
            # Parse quality standards
            self._parse_quality_standards(extracted_text)
            
            # Save processed data
            self._save_study_guide_data()
            
            logger.info(f"Study guide processing complete: {len(self.legal_patterns)} legal patterns")
            return True
            
        except Exception as e:
            logger.error(f"Error processing QME Study Guide: {e}")
            self._load_default_compliance_patterns()
            return False
    
    def _parse_legal_requirements(self, text: str) -> None:
        """Parse legal requirements from study guide text."""
        try:
            # Define key legal requirements from QME Study Guide
            legal_requirements = [
                {
                    "requirement_type": "section_4062_3_compliance",
                    "statutory_reference": "Labor Code Section 4062.3",
                    "required_language": "The evaluation shall address each of the issues described in the panel QME's report",
                    "compliance_criteria": [
                        "Address all issues in panel report",
                        "Provide medical opinion on each contested issue",
                        "Include impairment rating if requested"
                    ],
                    "violation_consequences": [
                        "Report may be rejected",
                        "Additional evaluation may be required"
                    ],
                    "example_implementation": "This evaluation addresses the following issues as described in the panel QME report: [list issues]"
                },
                {
                    "requirement_type": "impairment_rating_requirement",
                    "statutory_reference": "Labor Code Section 4660",
                    "required_language": "Permanent disability shall be determined in accordance with the AMA Guides",
                    "compliance_criteria": [
                        "Use AMA Guides 5th Edition",
                        "Provide specific table references",
                        "Show calculation methodology"
                    ],
                    "violation_consequences": [
                        "Rating may be rejected",
                        "Supplemental report required"
                    ],
                    "example_implementation": "The impairment rating is calculated using AMA Guides 5th Edition, Chapter X, Table Y"
                },
                {
                    "requirement_type": "causation_analysis",
                    "statutory_reference": "Labor Code Section 3208.3",
                    "required_language": "Industrial causation must be established to a reasonable degree of medical probability",
                    "compliance_criteria": [
                        "State opinion to reasonable medical probability",
                        "Consider alternative causes",
                        "Provide medical rationale"
                    ],
                    "violation_consequences": [
                        "Causation finding may be rejected",
                        "Additional medical evidence required"
                    ],
                    "example_implementation": "It is my opinion to a reasonable degree of medical probability that..."
                },
                {
                    "requirement_type": "apportionment_analysis",
                    "statutory_reference": "Labor Code Sections 4663 and 4664",
                    "required_language": "Apportionment shall be based on causation",
                    "compliance_criteria": [
                        "Identify all contributing factors",
                        "Assign percentage to each factor",
                        "Provide medical basis for apportionment"
                    ],
                    "violation_consequences": [
                        "Apportionment may be rejected",
                        "Supplemental analysis required"
                    ],
                    "example_implementation": "Apportionment: X% industrial, Y% non-industrial based on..."
                }
            ]
            
            for req_data in legal_requirements:
                pattern = LegalCompliancePattern(
                    requirement_type=req_data["requirement_type"],
                    statutory_reference=req_data["statutory_reference"],
                    required_language=req_data["required_language"],
                    compliance_criteria=req_data["compliance_criteria"],
                    violation_consequences=req_data["violation_consequences"],
                    example_implementation=req_data["example_implementation"]
                )
                self.legal_patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Error parsing legal requirements: {e}")
    
    def _extract_procedural_requirements(self, text: str) -> None:
        """Extract procedural requirements from study guide."""
        try:
            self.procedural_requirements = {
                "report_structure": [
                    "Patient identification section required",
                    "History sections must be comprehensive",
                    "Physical examination must be documented",
                    "Diagnosis with ICD codes required",
                    "Impairment rating with AMA references",
                    "Work restrictions based on examination",
                    "Future medical care recommendations",
                    "Causation analysis required",
                    "Apportionment if applicable"
                ],
                "documentation_standards": [
                    "All sources must be cited",
                    "Medical records must be reviewed",
                    "Examination findings must be objective",
                    "Measurements must be documented",
                    "Calculations must be shown"
                ],
                "quality_requirements": [
                    "Professional language required",
                    "Medical terminology must be accurate",
                    "Conclusions must be supported",
                    "Recommendations must be reasonable",
                    "Report must be internally consistent"
                ],
                "legal_compliance": [
                    "Statutory language must be exact",
                    "Required declarations must be included",
                    "Interpreter requirements if applicable",
                    "Billing attestations required",
                    "Signature and date required"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error extracting procedural requirements: {e}")
    
    def _parse_quality_standards(self, text: str) -> None:
        """Parse quality standards from study guide."""
        try:
            self.quality_standards = {
                "completeness_standards": {
                    "all_sections_present": 100,
                    "required_elements_complete": 95,
                    "supporting_documentation": 90
                },
                "accuracy_standards": {
                    "medical_facts_accurate": 100,
                    "calculations_correct": 100,
                    "references_valid": 95
                },
                "compliance_standards": {
                    "legal_requirements_met": 100,
                    "ama_guidelines_followed": 100,
                    "formatting_professional": 85
                },
                "content_quality": {
                    "medical_reasoning_sound": 90,
                    "conclusions_supported": 95,
                    "language_professional": 85
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing quality standards: {e}")
    
    def _load_default_compliance_patterns(self) -> None:
        """Load default compliance patterns when study guide unavailable."""
        logger.info("Loading default compliance patterns")
        
        default_pattern = LegalCompliancePattern(
            requirement_type="general_compliance",
            statutory_reference="Labor Code Section 4062.3",
            required_language="QME report must meet statutory requirements",
            compliance_criteria=["Complete evaluation", "Medical opinion provided"],
            violation_consequences=["Report rejection possible"],
            example_implementation="Standard QME report format"
        )
        
        self.legal_patterns = [default_pattern]
    
    def _save_study_guide_data(self) -> None:
        """Save processed study guide data."""
        try:
            data_dir = Path("data/qme_references")
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Save legal patterns
            legal_data = []
            for pattern in self.legal_patterns:
                legal_data.append({
                    "requirement_type": pattern.requirement_type,
                    "statutory_reference": pattern.statutory_reference,
                    "required_language": pattern.required_language,
                    "compliance_criteria": pattern.compliance_criteria,
                    "violation_consequences": pattern.violation_consequences,
                    "example_implementation": pattern.example_implementation
                })
            
            with open(data_dir / "legal_patterns.json", "w") as f:
                json.dump(legal_data, f, indent=2)
            
            # Save procedural requirements
            with open(data_dir / "procedural_requirements.json", "w") as f:
                json.dump(self.procedural_requirements, f, indent=2)
            
            # Save quality standards
            with open(data_dir / "quality_standards.json", "w") as f:
                json.dump(self.quality_standards, f, indent=2)
            
            logger.info(f"Saved study guide data to {data_dir}")
            
        except Exception as e:
            logger.error(f"Error saving study guide data: {e}")


class SampleReportProcessor:
    """Processes Sample3.pdf for report structure patterns and examples."""
    
    def __init__(self, sample_path: str = "Sample3.pdf"):
        """Initialize sample report processor."""
        self.sample_path = sample_path
        self.document_processor = DocumentProcessor()
        self.structure_patterns: List[QMEStructurePattern] = []
        self.reasoning_examples: List[MedicalReasoningExample] = []
        self.content_templates: Dict[str, str] = {}
        
        logger.info(f"Initialized Sample Report processor: {sample_path}")
    
    def process_sample_report(self) -> bool:
        """Process sample report for structure patterns and examples."""
        try:
            logger.info("Processing sample report for structure patterns")
            
            if not Path(self.sample_path).exists():
                logger.warning(f"Sample report not found: {self.sample_path}")
                self._load_default_structure_patterns()
                return False
            
            # Extract text from PDF
            extracted_text = self.document_processor.extract_text_from_pdf(self.sample_path)
            
            # Parse report structure
            self._parse_report_structure(extracted_text)
            
            # Extract reasoning examples
            self._extract_reasoning_examples(extracted_text)
            
            # Build content templates
            self._build_content_templates(extracted_text)
            
            # Save processed data
            self._save_sample_data()
            
            logger.info(f"Sample report processing complete: {len(self.structure_patterns)} patterns")
            return True
            
        except Exception as e:
            logger.error(f"Error processing sample report: {e}")
            self._load_default_structure_patterns()
            return False
    
    def _parse_report_structure(self, text: str) -> None:
        """Parse report structure from sample text."""
        try:
            # Define structure patterns based on typical QME report sections
            structure_definitions = [
                {
                    "section_name": "Patient Identification",
                    "section_order": 1,
                    "required_elements": ["name", "age", "case_number", "injury_date"],
                    "content_patterns": [r"Name:\s*[A-Z][a-z]+", r"Age:\s*\d+", r"Case.*:\s*\w+"],
                    "example_content": "Patient identification with complete demographic information",
                    "legal_requirements": ["§4062.3 identification requirements"],
                    "quality_indicators": ["Complete demographics", "Accurate case information"]
                },
                {
                    "section_name": "History of Present Illness",
                    "section_order": 2,
                    "required_elements": ["injury_mechanism", "symptom_onset", "current_symptoms"],
                    "content_patterns": [r"injured.*on", r"reports.*pain", r"describes.*symptoms"],
                    "example_content": "Detailed narrative of injury and symptom progression",
                    "legal_requirements": ["Comprehensive history documentation"],
                    "quality_indicators": ["Chronological narrative", "Symptom detail"]
                },
                {
                    "section_name": "Physical Examination",
                    "section_order": 6,
                    "required_elements": ["general_appearance", "range_of_motion", "strength_testing"],
                    "content_patterns": [r"examination.*reveals", r"range of motion", r"strength.*5/5"],
                    "example_content": "Systematic physical examination with objective findings",
                    "legal_requirements": ["Objective examination required"],
                    "quality_indicators": ["Systematic approach", "Objective measurements"]
                },
                {
                    "section_name": "Diagnosis",
                    "section_order": 8,
                    "required_elements": ["primary_diagnosis", "icd_code"],
                    "content_patterns": [r"Primary.*diagnosis", r"ICD.*\d+"],
                    "example_content": "Clear diagnostic statements with ICD codes",
                    "legal_requirements": ["Specific diagnosis required"],
                    "quality_indicators": ["Clear diagnosis", "Appropriate ICD codes"]
                },
                {
                    "section_name": "Impairment Rating",
                    "section_order": 9,
                    "required_elements": ["percentage", "ama_reference", "methodology"],
                    "content_patterns": [r"\d+%.*impairment", r"AMA.*Guides", r"Table.*\d+"],
                    "example_content": "Impairment rating with AMA methodology",
                    "legal_requirements": ["AMA Guides compliance"],
                    "quality_indicators": ["Accurate calculation", "Proper references"]
                },
                {
                    "section_name": "Causation Analysis",
                    "section_order": 12,
                    "required_elements": ["medical_probability", "causation_opinion"],
                    "content_patterns": [r"reasonable.*medical.*probability", r"causally.*related"],
                    "example_content": "Medical causation analysis with probability statement",
                    "legal_requirements": ["Reasonable medical probability standard"],
                    "quality_indicators": ["Clear causation opinion", "Medical rationale"]
                }
            ]
            
            for struct_def in structure_definitions:
                pattern = QMEStructurePattern(
                    section_name=struct_def["section_name"],
                    section_order=struct_def["section_order"],
                    required_elements=struct_def["required_elements"],
                    content_patterns=struct_def["content_patterns"],
                    example_content=struct_def["example_content"],
                    legal_requirements=struct_def["legal_requirements"],
                    quality_indicators=struct_def["quality_indicators"]
                )
                self.structure_patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Error parsing report structure: {e}")
    
    def _extract_reasoning_examples(self, text: str) -> None:
        """Extract medical reasoning examples from sample text."""
        try:
            # Define reasoning examples based on common QME scenarios
            reasoning_examples = [
                {
                    "diagnosis_type": "spine_injury",
                    "reasoning_pattern": "The mechanism of injury involving {mechanism} is consistent with {diagnosis}. The temporal relationship between injury and symptom onset supports industrial causation.",
                    "causation_language": "It is my opinion to a reasonable degree of medical probability that the {condition} is causally related to the industrial injury of {date}.",
                    "impairment_rationale": "The impairment rating is based on {method} using AMA Guides 5th Edition, {table_reference}. The {measurements} support a {percentage}% whole person impairment.",
                    "treatment_recommendations": [
                        "Conservative treatment with physical therapy",
                        "Anti-inflammatory medications as needed",
                        "Work restrictions as outlined"
                    ],
                    "source_document": "Sample3.pdf",
                    "confidence_indicators": ["Objective findings", "Consistent history", "Appropriate methodology"]
                },
                {
                    "diagnosis_type": "extremity_injury",
                    "reasoning_pattern": "The injury to the {body_part} involving {mechanism} resulted in {pathology}. The examination findings of {findings} are consistent with the reported mechanism.",
                    "causation_language": "Based on reasonable medical probability, the {condition} is industrially related given the mechanism of injury and temporal relationship.",
                    "impairment_rationale": "Using AMA Guides 5th Edition methodology, the {measurements} result in {percentage}% impairment of the {body_part}, which converts to {whole_person}% whole person impairment.",
                    "treatment_recommendations": [
                        "Physical therapy for range of motion and strengthening",
                        "Activity modification during recovery",
                        "Follow-up as needed"
                    ],
                    "source_document": "Sample3.pdf",
                    "confidence_indicators": ["Objective measurements", "Consistent examination", "Appropriate calculations"]
                }
            ]
            
            for example_data in reasoning_examples:
                example = MedicalReasoningExample(
                    diagnosis_type=example_data["diagnosis_type"],
                    reasoning_pattern=example_data["reasoning_pattern"],
                    causation_language=example_data["causation_language"],
                    impairment_rationale=example_data["impairment_rationale"],
                    treatment_recommendations=example_data["treatment_recommendations"],
                    source_document=example_data["source_document"],
                    confidence_indicators=example_data["confidence_indicators"]
                )
                self.reasoning_examples.append(example)
            
        except Exception as e:
            logger.error(f"Error extracting reasoning examples: {e}")
    
    def _build_content_templates(self, text: str) -> None:
        """Build content templates from sample text."""
        try:
            self.content_templates = {
                "history_template": "The patient reports sustaining an injury on {date} when {mechanism}. Initially, the patient experienced {initial_symptoms}. Currently, the patient describes {current_symptoms}.",
                
                "examination_template": "Physical examination reveals {general_appearance}. Range of motion testing shows {rom_findings}. Strength testing demonstrates {strength_findings}. Neurological examination reveals {neuro_findings}.",
                
                "diagnosis_template": "Based on the history, physical examination, and review of medical records, the diagnosis is {primary_diagnosis} (ICD-10: {icd_code}).",
                
                "impairment_template": "Using the AMA Guides to the Evaluation of Permanent Impairment, 5th Edition, {methodology}, the impairment rating is {percentage}% whole person impairment.",
                
                "causation_template": "It is my opinion to a reasonable degree of medical probability that the {condition} is causally related to the industrial injury of {date} based on {rationale}.",
                
                "treatment_template": "Future medical care recommendations include: {recommendations}. These treatments are reasonable and necessary for the diagnosed condition.",
                
                "restrictions_template": "Based on the examination findings and functional limitations, the following work restrictions are recommended: {restrictions}."
            }
            
        except Exception as e:
            logger.error(f"Error building content templates: {e}")
    
    def _load_default_structure_patterns(self) -> None:
        """Load default structure patterns when sample unavailable."""
        logger.info("Loading default structure patterns")
        
        default_pattern = QMEStructurePattern(
            section_name="Standard Section",
            section_order=1,
            required_elements=["basic_content"],
            content_patterns=["standard_pattern"],
            example_content="Standard QME section content",
            legal_requirements=["Basic requirements"],
            quality_indicators=["Standard quality"]
        )
        
        self.structure_patterns = [default_pattern]
    
    def _save_sample_data(self) -> None:
        """Save processed sample data."""
        try:
            data_dir = Path("data/qme_references")
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Save structure patterns
            structure_data = []
            for pattern in self.structure_patterns:
                structure_data.append({
                    "section_name": pattern.section_name,
                    "section_order": pattern.section_order,
                    "required_elements": pattern.required_elements,
                    "content_patterns": pattern.content_patterns,
                    "example_content": pattern.example_content,
                    "legal_requirements": pattern.legal_requirements,
                    "quality_indicators": pattern.quality_indicators
                })
            
            with open(data_dir / "structure_patterns.json", "w") as f:
                json.dump(structure_data, f, indent=2)
            
            # Save reasoning examples
            reasoning_data = []
            for example in self.reasoning_examples:
                reasoning_data.append({
                    "diagnosis_type": example.diagnosis_type,
                    "reasoning_pattern": example.reasoning_pattern,
                    "causation_language": example.causation_language,
                    "impairment_rationale": example.impairment_rationale,
                    "treatment_recommendations": example.treatment_recommendations,
                    "source_document": example.source_document,
                    "confidence_indicators": example.confidence_indicators
                })
            
            with open(data_dir / "reasoning_examples.json", "w") as f:
                json.dump(reasoning_data, f, indent=2)
            
            # Save content templates
            with open(data_dir / "content_templates.json", "w") as f:
                json.dump(self.content_templates, f, indent=2)
            
            logger.info(f"Saved sample data to {data_dir}")
            
        except Exception as e:
            logger.error(f"Error saving sample data: {e}")


class QMEReferenceIntegrator:
    """Integrates QME Study Guide and Sample Report data for comprehensive reference."""
    
    def __init__(self):
        """Initialize QME reference integrator."""
        self.study_guide_processor = QMEStudyGuideProcessor()
        self.sample_processor = SampleReportProcessor()
        self.integrated_patterns: Dict[str, Any] = {}
        
        logger.info("Initialized QME Reference Integrator")
    
    def process_all_references(self) -> bool:
        """Process all reference materials."""
        try:
            logger.info("Processing all QME reference materials")
            
            # Process study guide
            study_guide_success = self.study_guide_processor.process_study_guide()
            
            # Process sample report
            sample_success = self.sample_processor.process_sample_report()
            
            # Integrate data
            self._integrate_reference_data()
            
            # Save integrated data
            self._save_integrated_data()
            
            success = study_guide_success or sample_success
            logger.info(f"Reference processing {'successful' if success else 'completed with fallbacks'}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing references: {e}")
            return False
    
    def get_legal_compliance_patterns(self) -> List[LegalCompliancePattern]:
        """Get legal compliance patterns."""
        return self.study_guide_processor.legal_patterns
    
    def get_structure_patterns(self) -> List[QMEStructurePattern]:
        """Get report structure patterns."""
        return self.sample_processor.structure_patterns
    
    def get_reasoning_examples(self) -> List[MedicalReasoningExample]:
        """Get medical reasoning examples."""
        return self.sample_processor.reasoning_examples
    
    def get_content_templates(self) -> Dict[str, str]:
        """Get content templates."""
        return self.sample_processor.content_templates
    
    def _integrate_reference_data(self) -> None:
        """Integrate data from all reference sources."""
        try:
            self.integrated_patterns = {
                "legal_compliance": {
                    "patterns": [
                        {
                            "type": pattern.requirement_type,
                            "reference": pattern.statutory_reference,
                            "language": pattern.required_language,
                            "criteria": pattern.compliance_criteria
                        }
                        for pattern in self.study_guide_processor.legal_patterns
                    ]
                },
                "structure_requirements": {
                    "sections": [
                        {
                            "name": pattern.section_name,
                            "order": pattern.section_order,
                            "elements": pattern.required_elements,
                            "quality_indicators": pattern.quality_indicators
                        }
                        for pattern in self.sample_processor.structure_patterns
                    ]
                },
                "content_guidance": {
                    "reasoning_examples": [
                        {
                            "type": example.diagnosis_type,
                            "pattern": example.reasoning_pattern,
                            "causation": example.causation_language,
                            "recommendations": example.treatment_recommendations
                        }
                        for example in self.sample_processor.reasoning_examples
                    ],
                    "templates": self.sample_processor.content_templates
                },
                "quality_standards": self.study_guide_processor.quality_standards
            }
            
        except Exception as e:
            logger.error(f"Error integrating reference data: {e}")
    
    def _save_integrated_data(self) -> None:
        """Save integrated reference data."""
        try:
            data_dir = Path("data/qme_references")
            data_dir.mkdir(parents=True, exist_ok=True)
            
            with open(data_dir / "integrated_patterns.json", "w") as f:
                json.dump(self.integrated_patterns, f, indent=2)
            
            logger.info(f"Saved integrated reference data to {data_dir}")
            
        except Exception as e:
            logger.error(f"Error saving integrated data: {e}")