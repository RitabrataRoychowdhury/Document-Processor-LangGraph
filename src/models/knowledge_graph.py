"""Knowledge graph domain models for the Document Q&A System."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
import json


@dataclass
class Patient:
    """Patient entity in the knowledge graph."""
    
    id: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    case_number: str = ""
    medical_record_number: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert patient to dictionary for storage."""
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'case_number': self.case_number,
            'medical_record_number': self.medical_record_number,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Patient':
        """Create patient from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            age=data.get('age'),
            gender=data.get('gender'),
            case_number=data.get('case_number', ''),
            medical_record_number=data.get('medical_record_number'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        )


@dataclass
class Section:
    """Document section entity in the knowledge graph."""
    
    id: str
    document_id: str
    section_type: str  # e.g., 'history', 'examination', 'diagnosis', 'findings'
    page_number: int
    text_content: str
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert section to dictionary for storage."""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'section_type': self.section_type,
            'page_number': self.page_number,
            'text_content': self.text_content,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Section':
        """Create section from dictionary."""
        return cls(
            id=data['id'],
            document_id=data['document_id'],
            section_type=data['section_type'],
            page_number=data['page_number'],
            text_content=data['text_content'],
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class Claim:
    """Medical claim entity in the knowledge graph."""
    
    id: str
    patient_id: str
    claim_number: str
    injury_date: Optional[datetime] = None
    body_parts: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert claim to dictionary for storage."""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'claim_number': self.claim_number,
            'injury_date': self.injury_date.isoformat() if self.injury_date else None,
            'body_parts': json.dumps(self.body_parts),
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Claim':
        """Create claim from dictionary."""
        return cls(
            id=data['id'],
            patient_id=data['patient_id'],
            claim_number=data['claim_number'],
            injury_date=datetime.fromisoformat(data['injury_date']) if data.get('injury_date') else None,
            body_parts=json.loads(data['body_parts']) if data.get('body_parts') else [],
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class Diagnosis:
    """Medical diagnosis entity in the knowledge graph."""
    
    id: str
    icd_code: str
    description: str
    severity: Optional[str] = None
    certainty: float = 1.0  # 0.0 to 1.0
    source_section_id: Optional[str] = None
    page_reference: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert diagnosis to dictionary for storage."""
        return {
            'id': self.id,
            'icd_code': self.icd_code,
            'description': self.description,
            'severity': self.severity,
            'certainty': self.certainty,
            'source_section_id': self.source_section_id,
            'page_reference': self.page_reference,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Diagnosis':
        """Create diagnosis from dictionary."""
        return cls(
            id=data['id'],
            icd_code=data['icd_code'],
            description=data['description'],
            severity=data.get('severity'),
            certainty=data.get('certainty', 1.0),
            source_section_id=data.get('source_section_id'),
            page_reference=data.get('page_reference'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class Finding:
    """Medical finding entity in the knowledge graph."""
    
    id: str
    section_id: str
    finding_type: str  # e.g., 'physical', 'imaging', 'laboratory'
    description: str
    page_reference: int
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary for storage."""
        return {
            'id': self.id,
            'section_id': self.section_id,
            'finding_type': self.finding_type,
            'description': self.description,
            'page_reference': self.page_reference,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Finding':
        """Create finding from dictionary."""
        return cls(
            id=data['id'],
            section_id=data['section_id'],
            finding_type=data['finding_type'],
            description=data['description'],
            page_reference=data['page_reference'],
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class ImagingStudy:
    """Imaging study entity in the knowledge graph."""
    
    id: str
    study_type: str  # e.g., 'MRI', 'CT', 'X-ray'
    study_date: Optional[datetime] = None
    findings: str = ""
    interpretation: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert imaging study to dictionary for storage."""
        return {
            'id': self.id,
            'study_type': self.study_type,
            'study_date': self.study_date.isoformat() if self.study_date else None,
            'findings': self.findings,
            'interpretation': self.interpretation,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImagingStudy':
        """Create imaging study from dictionary."""
        return cls(
            id=data['id'],
            study_type=data['study_type'],
            study_date=datetime.fromisoformat(data['study_date']) if data.get('study_date') else None,
            findings=data.get('findings', ''),
            interpretation=data.get('interpretation', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class ImpairmentRating:
    """Impairment rating entity in the knowledge graph."""
    
    id: str
    diagnosis_id: str
    ama_table: str
    percentage: float
    rationale: str
    source_page: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert impairment rating to dictionary for storage."""
        return {
            'id': self.id,
            'diagnosis_id': self.diagnosis_id,
            'ama_table': self.ama_table,
            'percentage': self.percentage,
            'rationale': self.rationale,
            'source_page': self.source_page,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImpairmentRating':
        """Create impairment rating from dictionary."""
        return cls(
            id=data['id'],
            diagnosis_id=data['diagnosis_id'],
            ama_table=data['ama_table'],
            percentage=data['percentage'],
            rationale=data['rationale'],
            source_page=data.get('source_page'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class KnowledgeNode:
    """Generic knowledge graph node."""
    
    id: str
    node_type: str
    properties: Dict[str, Any]
    embeddings: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert knowledge node to dictionary for storage."""
        return {
            'id': self.id,
            'node_type': self.node_type,
            'properties': json.dumps(self.properties),
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeNode':
        """Create knowledge node from dictionary."""
        return cls(
            id=data['id'],
            node_type=data['node_type'],
            properties=json.loads(data['properties']) if data.get('properties') else {},
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class KnowledgeRelationship:
    """Knowledge graph relationship."""
    
    id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert knowledge relationship to dictionary for storage."""
        return {
            'id': self.id,
            'source_node_id': self.source_node_id,
            'target_node_id': self.target_node_id,
            'relationship_type': self.relationship_type,
            'properties': json.dumps(self.properties),
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeRelationship':
        """Create knowledge relationship from dictionary."""
        return cls(
            id=data['id'],
            source_node_id=data['source_node_id'],
            target_node_id=data['target_node_id'],
            relationship_type=data['relationship_type'],
            properties=json.loads(data['properties']) if data.get('properties') else {},
            confidence=data.get('confidence', 1.0),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )