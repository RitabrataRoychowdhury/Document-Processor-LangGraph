"""
QME Template Generation System.

This service generates DOCX templates following the AI Example QME Report Template.docx format.
It processes patient documents to extract information and generates comprehensive QME reports.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import re
import uuid
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

try:
    from src.models.knowledge_graph import Patient, Diagnosis, Finding, ImpairmentRating, Section
    from src.repositories.patient_repository import PatientRepository, SQLitePatientRepository
    from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository, SQLiteKnowledgeGraphRepository
    from src.services.ingestion_pipeline import MedicalNERExtractor, ExtractedEntity
    from src.utils.logging_config import get_logger
except ImportError:
    from models.knowledge_graph import Patient, Diagnosis, Finding, ImpairmentRating, Section
    from repositories.patient_repository import PatientRepository, SQLitePatientRepository
    from repositories.knowledge_graph_repository import KnowledgeGraphRepository, SQLiteKnowledgeGraphRepository
    from services.ingestion_pipeline import MedicalNERExtractor, ExtractedEntity
    from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PatientInfo:
    """Extracted patient information for QME template."""
    name: str = ""
    age: Optional[int] = None
    gender: Optional[str] = None
    case_number: str = ""
    medical_record_number: Optional[str] = None
    injury_date: Optional[datetime] = None
    body_parts: List[str] = field(default_factory=list)
    occupation: Optional[str] = None
    employer: Optional[str] = None


@dataclass
class MedicalFindings:
    """Medical findings extracted from patient documents."""
    diagnoses: List[Diagnosis] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    impairment_ratings: List[ImpairmentRating] = field(default_factory=list)
    imaging_studies: List[str] = field(default_factory=list)
    treatment_history: List[str] = field(default_factory=list)


@dataclass
class QMETemplateData:
    """Complete data structure for QME template generation."""
    patient_info: PatientInfo
    medical_findings: MedicalFindings
    missing_sections: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    ama_guidelines: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class MissingInformation:
    """Information about missing or incomplete sections."""
    section_name: str
    description: str
    suggestions: List[str] = field(default_factory=list)
    priority: str = "medium"  # low, medium, high


class PatientDocumentProcessor:
    """Processes patient documents to extract information using NER."""
    
    def __init__(self, ner_extractor: Optional[MedicalNERExtractor] = None):
        """Initialize the processor with NER extractor."""
        self.ner_extractor = ner_extractor or MedicalNERExtractor()
    
    def extract_patient_info(self, document_text: str, document_id: str) -> PatientInfo:
        """
        Extract patient information from document text using NER.
        
        Args:
            document_text: Raw document text
            document_id: Document identifier
            
        Returns:
            PatientInfo object with extracted information
        """
        try:
            logger.info(f"Extracting patient info from document: {document_id}")
            
            patient_info = PatientInfo()
            
            # Extract basic patient information using regex patterns
            patient_info.name = self._extract_patient_name(document_text)
            patient_info.age = self._extract_age(document_text)
            patient_info.gender = self._extract_gender(document_text)
            patient_info.case_number = self._extract_case_number(document_text)
            patient_info.medical_record_number = self._extract_mrn(document_text)
            patient_info.injury_date = self._extract_injury_date(document_text)
            patient_info.body_parts = self._extract_body_parts(document_text)
            patient_info.occupation = self._extract_occupation(document_text)
            patient_info.employer = self._extract_employer(document_text)
            
            logger.info(f"Extracted patient info: {patient_info.name}, Case: {patient_info.case_number}")
            return patient_info
            
        except Exception as e:
            logger.error(f"Error extracting patient info: {e}")
            return PatientInfo()
    
    def extract_medical_findings(self, sections: List[Section]) -> MedicalFindings:
        """
        Extract medical findings from document sections using NER.
        
        Args:
            sections: List of document sections
            
        Returns:
            MedicalFindings object with extracted medical information
        """
        try:
            logger.info(f"Extracting medical findings from {len(sections)} sections")
            
            # Use NER extractor to get entities
            entities = self.ner_extractor.extract_entities(sections)
            
            findings = MedicalFindings()
            
            # Process extracted entities
            for entity in entities:
                if entity.entity_type == 'diagnosis':
                    diagnosis = self._create_diagnosis_from_entity(entity)
                    if diagnosis:
                        findings.diagnoses.append(diagnosis)
                
                elif entity.entity_type == 'finding':
                    finding = self._create_finding_from_entity(entity)
                    if finding:
                        findings.findings.append(finding)
                
                elif entity.entity_type == 'imaging':
                    findings.imaging_studies.append(entity.text)
                
                elif entity.entity_type == 'treatment':
                    findings.treatment_history.append(entity.text)
            
            logger.info(f"Extracted {len(findings.diagnoses)} diagnoses, {len(findings.findings)} findings")
            return findings
            
        except Exception as e:
            logger.error(f"Error extracting medical findings: {e}")
            return MedicalFindings()
    
    def _extract_patient_name(self, text: str) -> str:
        """Extract patient name from text."""
        patterns = [
            r"Patient:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:\s*\n|\s*Age|\s*$)",
            r"Name:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:\s*\n|\s*Age|\s*$)",
            r"PATIENT NAME:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:\s*\n|\s*Age|\s*$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_age(self, text: str) -> Optional[int]:
        """Extract patient age from text."""
        patterns = [
            r"Age:?\s*(\d{1,3})",
            r"(\d{1,3})\s*year[s]?\s*old",
            r"(\d{1,3})\s*y\.?o\.?"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                age = int(match.group(1))
                if 0 < age < 120:  # Reasonable age range
                    return age
        
        return None
    
    def _extract_gender(self, text: str) -> Optional[str]:
        """Extract patient gender from text."""
        if re.search(r'\b(male|man|mr\.?)\b', text, re.IGNORECASE):
            return "Male"
        elif re.search(r'\b(female|woman|mrs?\.?|ms\.?)\b', text, re.IGNORECASE):
            return "Female"
        
        return None
    
    def _extract_case_number(self, text: str) -> str:
        """Extract case number from text."""
        patterns = [
            r"Case\s*(?:Number|No\.?|#):?\s*([A-Z0-9\-]+)",
            r"Claim\s*(?:Number|No\.?|#):?\s*([A-Z0-9\-]+)",
            r"File\s*(?:Number|No\.?|#):?\s*([A-Z0-9\-]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_mrn(self, text: str) -> Optional[str]:
        """Extract medical record number from text."""
        patterns = [
            r"MRN:?\s*([A-Z0-9\-]+)",
            r"Medical\s*Record\s*(?:Number|No\.?|#):?\s*([A-Z0-9\-]+)",
            r"Record\s*(?:Number|No\.?|#):?\s*([A-Z0-9\-]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_injury_date(self, text: str) -> Optional[datetime]:
        """Extract injury date from text."""
        patterns = [
            r"Injury\s*Date:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})",
            r"Date\s*of\s*Injury:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})",
            r"DOI:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1)
                    # Try different date formats
                    for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except Exception:
                    continue
        
        return None
    
    def _extract_body_parts(self, text: str) -> List[str]:
        """Extract affected body parts from text."""
        body_parts = []
        
        # Common body part patterns
        patterns = [
            r'\b(back|spine|lumbar|cervical|thoracic)\b',
            r'\b(shoulder|arm|elbow|wrist|hand|finger)\b',
            r'\b(hip|leg|knee|ankle|foot|toe)\b',
            r'\b(head|neck|jaw)\b',
            r'\b(chest|abdomen|pelvis)\b'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match.lower() not in [bp.lower() for bp in body_parts]:
                    body_parts.append(match.capitalize())
        
        return body_parts
    
    def _extract_occupation(self, text: str) -> Optional[str]:
        """Extract patient occupation from text."""
        patterns = [
            r"Occupation:?\s*([A-Za-z\s]+?)(?:\n|\.|\,)",
            r"Job:?\s*([A-Za-z\s]+?)(?:\n|\.|\,)",
            r"Works?\s*as\s*(?:a|an)?\s*([A-Za-z\s]+?)(?:\n|\.|\,)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                occupation = match.group(1).strip()
                if len(occupation) > 2 and len(occupation) < 50:
                    return occupation
        
        return None
    
    def _extract_employer(self, text: str) -> Optional[str]:
        """Extract employer information from text."""
        patterns = [
            r"Employer:?\s*([A-Za-z\s&\.,]+?)(?:\n|\.)",
            r"Works?\s*(?:at|for)\s*([A-Za-z\s&\.,]+?)(?:\n|\.)",
            r"Company:?\s*([A-Za-z\s&\.,]+?)(?:\n|\.)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                employer = match.group(1).strip()
                if len(employer) > 2 and len(employer) < 100:
                    return employer
        
        return None
    
    def _create_diagnosis_from_entity(self, entity: ExtractedEntity) -> Optional[Diagnosis]:
        """Create a Diagnosis object from an extracted entity."""
        try:
            return Diagnosis(
                id=str(uuid.uuid4()),
                icd_code=entity.metadata.get('icd_code', ''),
                description=entity.text,
                severity=entity.metadata.get('severity'),
                certainty=entity.confidence,
                source_section_id=entity.section_id,
                page_reference=entity.page_number
            )
        except Exception as e:
            logger.error(f"Error creating diagnosis from entity: {e}")
            return None
    
    def _create_finding_from_entity(self, entity: ExtractedEntity) -> Optional[Finding]:
        """Create a Finding object from an extracted entity."""
        try:
            return Finding(
                id=str(uuid.uuid4()),
                section_id=entity.section_id,
                finding_type=entity.metadata.get('finding_type', 'clinical'),
                description=entity.text,
                page_reference=entity.page_number
            )
        except Exception as e:
            logger.error(f"Error creating finding from entity: {e}")
            return None


class KnowledgeGraphMatcher:
    """Matches extracted information against knowledge graph for recommendations."""
    
    def __init__(self, kg_repository: Optional[KnowledgeGraphRepository] = None):
        """Initialize with knowledge graph repository."""
        self.kg_repository = kg_repository or SQLiteKnowledgeGraphRepository()
    
    def find_relevant_impairment_ratings(self, diagnoses: List[Diagnosis]) -> List[ImpairmentRating]:
        """
        Find relevant impairment ratings for given diagnoses.
        
        Args:
            diagnoses: List of diagnoses to match
            
        Returns:
            List of relevant impairment ratings
        """
        try:
            impairment_ratings = []
            
            for diagnosis in diagnoses:
                # Search for impairment ratings related to this diagnosis
                ratings = self._find_ratings_for_diagnosis(diagnosis)
                impairment_ratings.extend(ratings)
            
            logger.info(f"Found {len(impairment_ratings)} relevant impairment ratings")
            return impairment_ratings
            
        except Exception as e:
            logger.error(f"Error finding impairment ratings: {e}")
            return []
    
    def find_ama_guidelines(self, diagnoses: List[Diagnosis]) -> List[str]:
        """
        Find relevant AMA guidelines for given diagnoses.
        
        Args:
            diagnoses: List of diagnoses to match
            
        Returns:
            List of relevant AMA guidelines
        """
        try:
            guidelines = []
            
            for diagnosis in diagnoses:
                # Search for AMA guidelines related to this diagnosis
                diagnosis_guidelines = self._find_guidelines_for_diagnosis(diagnosis)
                guidelines.extend(diagnosis_guidelines)
            
            # Remove duplicates
            guidelines = list(set(guidelines))
            
            logger.info(f"Found {len(guidelines)} relevant AMA guidelines")
            return guidelines
            
        except Exception as e:
            logger.error(f"Error finding AMA guidelines: {e}")
            return []
    
    def _find_ratings_for_diagnosis(self, diagnosis: Diagnosis) -> List[ImpairmentRating]:
        """Find impairment ratings for a specific diagnosis."""
        try:
            # Search by ICD code first
            if diagnosis.icd_code:
                ratings = self.kg_repository.find_impairment_ratings_by_icd(diagnosis.icd_code)
                if ratings:
                    return ratings
            
            # Search by description keywords
            keywords = diagnosis.description.lower().split()
            for keyword in keywords:
                if len(keyword) > 3:  # Skip short words
                    ratings = self.kg_repository.find_impairment_ratings_by_keyword(keyword)
                    if ratings:
                        return ratings
            
            return []
            
        except Exception as e:
            logger.error(f"Error finding ratings for diagnosis {diagnosis.id}: {e}")
            return []
    
    def _find_guidelines_for_diagnosis(self, diagnosis: Diagnosis) -> List[str]:
        """Find AMA guidelines for a specific diagnosis."""
        try:
            guidelines = []
            
            # Search by body system/category
            body_system = self._determine_body_system(diagnosis.description)
            if body_system:
                system_guidelines = self.kg_repository.find_ama_guidelines_by_system(body_system)
                guidelines.extend(system_guidelines)
            
            # Search by specific condition
            condition_guidelines = self.kg_repository.find_ama_guidelines_by_condition(diagnosis.description)
            guidelines.extend(condition_guidelines)
            
            return guidelines
            
        except Exception as e:
            logger.error(f"Error finding guidelines for diagnosis {diagnosis.id}: {e}")
            return []
    
    def _determine_body_system(self, description: str) -> Optional[str]:
        """Determine body system from diagnosis description."""
        description_lower = description.lower()
        
        systems = {
            'musculoskeletal': ['back', 'spine', 'joint', 'bone', 'muscle', 'ligament', 'tendon'],
            'neurological': ['nerve', 'brain', 'spinal cord', 'neurological', 'neuropathy'],
            'cardiovascular': ['heart', 'cardiac', 'vascular', 'circulation'],
            'respiratory': ['lung', 'pulmonary', 'respiratory', 'breathing'],
            'digestive': ['stomach', 'intestinal', 'digestive', 'gastric']
        }
        
        for system, keywords in systems.items():
            if any(keyword in description_lower for keyword in keywords):
                return system
        
        return None


class MissingInformationDetector:
    """Detects missing or incomplete information in QME templates."""
    
    def __init__(self):
        """Initialize the detector."""
        self.required_sections = [
            'patient_demographics',
            'history_of_present_illness',
            'past_medical_history',
            'physical_examination',
            'diagnostic_studies',
            'diagnosis',
            'impairment_rating',
            'work_restrictions',
            'future_medical_care'
        ]
    
    def detect_missing_information(self, template_data: QMETemplateData) -> List[MissingInformation]:
        """
        Detect missing or incomplete information in template data.
        
        Args:
            template_data: QME template data to analyze
            
        Returns:
            List of missing information items
        """
        try:
            missing_info = []
            
            # Check patient demographics
            missing_info.extend(self._check_patient_demographics(template_data.patient_info))
            
            # Check medical findings
            missing_info.extend(self._check_medical_findings(template_data.medical_findings))
            
            # Check for impairment ratings
            missing_info.extend(self._check_impairment_ratings(template_data.medical_findings))
            
            logger.info(f"Detected {len(missing_info)} missing information items")
            return missing_info
            
        except Exception as e:
            logger.error(f"Error detecting missing information: {e}")
            return []
    
    def _check_patient_demographics(self, patient_info: PatientInfo) -> List[MissingInformation]:
        """Check for missing patient demographic information."""
        missing = []
        
        if not patient_info.name:
            missing.append(MissingInformation(
                section_name="Patient Demographics",
                description="Patient name is missing",
                suggestions=["Verify patient identification in source documents"],
                priority="high"
            ))
        
        if not patient_info.age:
            missing.append(MissingInformation(
                section_name="Patient Demographics",
                description="Patient age is missing",
                suggestions=["Look for birth date or age references in documents"],
                priority="medium"
            ))
        
        if not patient_info.case_number:
            missing.append(MissingInformation(
                section_name="Patient Demographics",
                description="Case number is missing",
                suggestions=["Check claim documents for case/claim number"],
                priority="high"
            ))
        
        if not patient_info.injury_date:
            missing.append(MissingInformation(
                section_name="Patient Demographics",
                description="Date of injury is missing",
                suggestions=["Review claim documents for injury date"],
                priority="high"
            ))
        
        return missing
    
    def _check_medical_findings(self, medical_findings: MedicalFindings) -> List[MissingInformation]:
        """Check for missing medical findings."""
        missing = []
        
        if not medical_findings.diagnoses:
            missing.append(MissingInformation(
                section_name="Medical Findings",
                description="No diagnoses identified",
                suggestions=["Review medical records for diagnostic information"],
                priority="high"
            ))
        
        if not medical_findings.findings:
            missing.append(MissingInformation(
                section_name="Medical Findings",
                description="No clinical findings documented",
                suggestions=["Review examination reports and clinical notes"],
                priority="medium"
            ))
        
        if not medical_findings.imaging_studies:
            missing.append(MissingInformation(
                section_name="Diagnostic Studies",
                description="No imaging studies documented",
                suggestions=["Check for X-rays, MRI, CT scans in medical records"],
                priority="medium"
            ))
        
        return missing
    
    def _check_impairment_ratings(self, medical_findings: MedicalFindings) -> List[MissingInformation]:
        """Check for missing impairment rating information."""
        missing = []
        
        if medical_findings.diagnoses and not medical_findings.impairment_ratings:
            missing.append(MissingInformation(
                section_name="Impairment Rating",
                description="No impairment ratings calculated",
                suggestions=[
                    "Calculate impairment ratings using AMA Guides",
                    "Review relevant AMA tables for each diagnosis"
                ],
                priority="high"
            ))
        
        return missing


class QMETemplateGenerator:
    """Main service for generating QME templates in DOCX format."""
    
    def __init__(self,
                 patient_repository: Optional[PatientRepository] = None,
                 kg_repository: Optional[KnowledgeGraphRepository] = None):
        """
        Initialize the QME template generator.
        
        Args:
            patient_repository: Repository for patient data
            kg_repository: Knowledge graph repository
        """
        self.patient_repository = patient_repository or SQLitePatientRepository()
        self.kg_repository = kg_repository or SQLiteKnowledgeGraphRepository()
        
        self.document_processor = PatientDocumentProcessor()
        self.kg_matcher = KnowledgeGraphMatcher(kg_repository)
        self.missing_info_detector = MissingInformationDetector()
        
        logger.info("Initialized QME Template Generator")
    
    def generate_qme_template(self, patient_id: str, output_path: Optional[str] = None) -> Tuple[str, QMETemplateData]:
        """
        Generate a QME template for a patient.
        
        Args:
            patient_id: Patient identifier
            output_path: Optional output file path
            
        Returns:
            Tuple of (file_path, template_data)
        """
        try:
            logger.info(f"Generating QME template for patient: {patient_id}")
            
            # Get patient data
            patient = self.patient_repository.find_by_id(patient_id)
            if not patient:
                raise ValueError(f"Patient not found: {patient_id}")
            
            # Get patient documents and extract information
            template_data = self._prepare_template_data(patient)
            
            # Generate DOCX document
            if not output_path:
                output_path = f"qme_report_{patient_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            
            self._create_docx_template(template_data, output_path)
            
            logger.info(f"Generated QME template: {output_path}")
            return output_path, template_data
            
        except Exception as e:
            logger.error(f"Error generating QME template: {e}")
            raise
    
    def _prepare_template_data(self, patient: Patient) -> QMETemplateData:
        """Prepare all data needed for template generation."""
        try:
            # Convert patient to PatientInfo
            patient_info = PatientInfo(
                name=patient.name,
                age=patient.age,
                gender=patient.gender,
                case_number=patient.case_number,
                medical_record_number=patient.medical_record_number
            )
            
            # Get patient documents and sections
            documents = self.kg_repository.find_documents_by_patient(patient.id)
            sections = []
            for doc in documents:
                doc_sections = self.kg_repository.find_sections_by_document(doc.id)
                sections.extend(doc_sections)
            
            # Extract medical findings
            medical_findings = self.document_processor.extract_medical_findings(sections)
            
            # Find relevant impairment ratings and guidelines
            impairment_ratings = self.kg_matcher.find_relevant_impairment_ratings(medical_findings.diagnoses)
            ama_guidelines = self.kg_matcher.find_ama_guidelines(medical_findings.diagnoses)
            
            medical_findings.impairment_ratings = impairment_ratings
            
            # Create template data
            template_data = QMETemplateData(
                patient_info=patient_info,
                medical_findings=medical_findings,
                ama_guidelines=ama_guidelines
            )
            
            # Detect missing information
            missing_info = self.missing_info_detector.detect_missing_information(template_data)
            template_data.missing_sections = [info.section_name for info in missing_info]
            template_data.recommendations = [info.description for info in missing_info]
            
            return template_data
            
        except Exception as e:
            logger.error(f"Error preparing template data: {e}")
            raise
    
    def _create_docx_template(self, template_data: QMETemplateData, output_path: str):
        """Create the DOCX template following QME report format."""
        try:
            # Create new document
            doc = Document()
            
            # Add title
            title = doc.add_heading('QUALIFIED MEDICAL EVALUATOR\'S REPORT', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Add patient information section
            self._add_patient_section(doc, template_data.patient_info)
            
            # Add history section
            self._add_history_section(doc, template_data)
            
            # Add examination section
            self._add_examination_section(doc, template_data)
            
            # Add diagnostic studies section
            self._add_diagnostic_studies_section(doc, template_data)
            
            # Add diagnosis section
            self._add_diagnosis_section(doc, template_data)
            
            # Add impairment rating section
            self._add_impairment_rating_section(doc, template_data)
            
            # Add recommendations section
            self._add_recommendations_section(doc, template_data)
            
            # Add missing information section
            if template_data.missing_sections:
                self._add_missing_information_section(doc, template_data)
            
            # Save document
            doc.save(output_path)
            
        except Exception as e:
            logger.error(f"Error creating DOCX template: {e}")
            raise
    
    def _add_patient_section(self, doc: Document, patient_info: PatientInfo):
        """Add patient information section."""
        doc.add_heading('PATIENT INFORMATION', level=1)
        
        p = doc.add_paragraph()
        p.add_run('Name: ').bold = True
        p.add_run(patient_info.name or '[MISSING - Patient name not found]')
        
        p = doc.add_paragraph()
        p.add_run('Age: ').bold = True
        p.add_run(str(patient_info.age) if patient_info.age else '[MISSING - Age not found]')
        
        p = doc.add_paragraph()
        p.add_run('Gender: ').bold = True
        p.add_run(patient_info.gender or '[MISSING - Gender not specified]')
        
        p = doc.add_paragraph()
        p.add_run('Case Number: ').bold = True
        p.add_run(patient_info.case_number or '[MISSING - Case number not found]')
        
        if patient_info.medical_record_number:
            p = doc.add_paragraph()
            p.add_run('Medical Record Number: ').bold = True
            p.add_run(patient_info.medical_record_number)
        
        if patient_info.injury_date:
            p = doc.add_paragraph()
            p.add_run('Date of Injury: ').bold = True
            p.add_run(patient_info.injury_date.strftime('%m/%d/%Y'))
        
        if patient_info.body_parts:
            p = doc.add_paragraph()
            p.add_run('Body Parts Affected: ').bold = True
            p.add_run(', '.join(patient_info.body_parts))
        
        if patient_info.occupation:
            p = doc.add_paragraph()
            p.add_run('Occupation: ').bold = True
            p.add_run(patient_info.occupation)
    
    def _add_history_section(self, doc: Document, template_data: QMETemplateData):
        """Add history of present illness section."""
        doc.add_heading('HISTORY OF PRESENT ILLNESS', level=1)
        
        if template_data.medical_findings.treatment_history:
            for treatment in template_data.medical_findings.treatment_history:
                doc.add_paragraph(treatment, style='List Bullet')
        else:
            p = doc.add_paragraph()
            p.add_run('[MISSING - Treatment history not documented. ')
            p.add_run('Please review medical records for treatment timeline.]').italic = True
    
    def _add_examination_section(self, doc: Document, template_data: QMETemplateData):
        """Add physical examination section."""
        doc.add_heading('PHYSICAL EXAMINATION', level=1)
        
        if template_data.medical_findings.findings:
            for finding in template_data.medical_findings.findings:
                p = doc.add_paragraph()
                p.add_run(f'{finding.finding_type.title()}: ').bold = True
                p.add_run(finding.description)
                if finding.page_reference:
                    p.add_run(f' (Page {finding.page_reference})').italic = True
        else:
            p = doc.add_paragraph()
            p.add_run('[MISSING - Physical examination findings not documented. ')
            p.add_run('Please review examination reports.]').italic = True
    
    def _add_diagnostic_studies_section(self, doc: Document, template_data: QMETemplateData):
        """Add diagnostic studies section."""
        doc.add_heading('DIAGNOSTIC STUDIES', level=1)
        
        if template_data.medical_findings.imaging_studies:
            for study in template_data.medical_findings.imaging_studies:
                doc.add_paragraph(study, style='List Bullet')
        else:
            p = doc.add_paragraph()
            p.add_run('[MISSING - Diagnostic studies not documented. ')
            p.add_run('Please review imaging reports and laboratory results.]').italic = True
    
    def _add_diagnosis_section(self, doc: Document, template_data: QMETemplateData):
        """Add diagnosis section."""
        doc.add_heading('DIAGNOSIS', level=1)
        
        if template_data.medical_findings.diagnoses:
            for i, diagnosis in enumerate(template_data.medical_findings.diagnoses, 1):
                p = doc.add_paragraph()
                p.add_run(f'{i}. ').bold = True
                p.add_run(diagnosis.description)
                if diagnosis.icd_code:
                    p.add_run(f' (ICD-10: {diagnosis.icd_code})')
                if diagnosis.severity:
                    p.add_run(f' - {diagnosis.severity}').italic = True
        else:
            p = doc.add_paragraph()
            p.add_run('[MISSING - Primary diagnosis not established. ')
            p.add_run('Please review medical records for diagnostic information.]').italic = True
    
    def _add_impairment_rating_section(self, doc: Document, template_data: QMETemplateData):
        """Add impairment rating section."""
        doc.add_heading('IMPAIRMENT RATING', level=1)
        
        if template_data.medical_findings.impairment_ratings:
            for rating in template_data.medical_findings.impairment_ratings:
                p = doc.add_paragraph()
                p.add_run(f'AMA Table {rating.ama_table}: ').bold = True
                p.add_run(f'{rating.percentage}% impairment')
                
                p = doc.add_paragraph()
                p.add_run('Rationale: ').bold = True
                p.add_run(rating.rationale)
                
                doc.add_paragraph()  # Add spacing
        else:
            p = doc.add_paragraph()
            p.add_run('[MISSING - Impairment rating not calculated. ')
            p.add_run('Please calculate using appropriate AMA Guides tables.]').italic = True
            
            if template_data.ama_guidelines:
                p = doc.add_paragraph()
                p.add_run('Suggested AMA Guidelines:').bold = True
                for guideline in template_data.ama_guidelines:
                    doc.add_paragraph(guideline, style='List Bullet')
    
    def _add_recommendations_section(self, doc: Document, template_data: QMETemplateData):
        """Add recommendations section."""
        doc.add_heading('RECOMMENDATIONS', level=1)
        
        doc.add_paragraph('Based on the medical evaluation, the following recommendations are made:')
        
        # Add standard recommendations
        recommendations = [
            'Continue current treatment plan as medically appropriate',
            'Follow up with treating physician as needed',
            'Consider work restrictions based on functional limitations'
        ]
        
        for rec in recommendations:
            doc.add_paragraph(rec, style='List Bullet')
    
    def _add_missing_information_section(self, doc: Document, template_data: QMETemplateData):
        """Add section highlighting missing information."""
        doc.add_heading('MISSING INFORMATION REQUIRING ATTENTION', level=1)
        
        p = doc.add_paragraph()
        p.add_run('The following information was not found in the available documents ')
        p.add_run('and may be required for a complete evaluation:').italic = True
        
        for recommendation in template_data.recommendations:
            doc.add_paragraph(recommendation, style='List Bullet')
        
        doc.add_paragraph()
        p = doc.add_paragraph()
        p.add_run('Please provide additional documentation to complete the evaluation.').bold = True


# Factory function for creating QME template generator
def create_qme_template_generator(patient_repository: Optional[PatientRepository] = None,
                                kg_repository: Optional[KnowledgeGraphRepository] = None) -> QMETemplateGenerator:
    """
    Factory function to create a QME template generator.
    
    Args:
        patient_repository: Patient repository instance
        kg_repository: Knowledge graph repository instance
        
    Returns:
        QMETemplateGenerator instance
    """
    return QMETemplateGenerator(patient_repository, kg_repository)