"""Data models for the Document Q&A System."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
import json


@dataclass
class Document:
    """Document model representing a processed document."""
    
    id: str
    title: str
    file_type: str
    file_size: int
    upload_timestamp: datetime
    processing_status: str = "pending"
    original_text: Optional[str] = None
    document_type: Optional[str] = None
    extracted_info: Optional[Dict[str, Any]] = None
    analysis: Optional[str] = None
    summary: Optional[str] = None
    embeddings: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary for storage."""
        return {
            'id': self.id,
            'title': self.title,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'upload_timestamp': self.upload_timestamp.isoformat(),
            'processing_status': self.processing_status,
            'original_text': self.original_text,
            'document_type': self.document_type,
            'extracted_info': json.dumps(self.extracted_info) if self.extracted_info else None,
            'analysis': self.analysis,
            'summary': self.summary,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Create document from dictionary."""
        return cls(
            id=data['id'],
            title=data['title'],
            file_type=data['file_type'],
            file_size=data['file_size'],
            upload_timestamp=datetime.fromisoformat(data['upload_timestamp']),
            processing_status=data.get('processing_status', 'pending'),
            original_text=data.get('original_text'),
            document_type=data.get('document_type'),
            extracted_info=json.loads(data['extracted_info']) if data.get('extracted_info') else None,
            analysis=data.get('analysis'),
            summary=data.get('summary'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        )


@dataclass
class ProcessingJob:
    """Processing job model for tracking document processing."""
    
    job_id: str
    document_id: str
    status: str = "pending"  # pending, processing, completed, failed
    current_step: Optional[str] = None
    progress_percentage: int = 0
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert processing job to dictionary for storage."""
        return {
            'job_id': self.job_id,
            'document_id': self.document_id,
            'status': self.status,
            'current_step': self.current_step,
            'progress_percentage': self.progress_percentage,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingJob':
        """Create processing job from dictionary."""
        return cls(
            job_id=data['job_id'],
            document_id=data['document_id'],
            status=data.get('status', 'pending'),
            current_step=data.get('current_step'),
            progress_percentage=data.get('progress_percentage', 0),
            error_message=data.get('error_message'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None
        )


@dataclass
class QASession:
    """Q&A session model for managing document queries."""
    
    session_id: str
    document_id: str
    questions: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_interaction(self, question: str, answer: str, sources: Optional[List[str]] = None):
        """Add a question-answer interaction to the session."""
        interaction = {
            'question': question,
            'answer': answer,
            'sources': sources or [],
            'timestamp': datetime.now().isoformat()
        }
        self.questions.append(interaction)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Q&A session to dictionary for storage."""
        return {
            'session_id': self.session_id,
            'document_id': self.document_id,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QASession':
        """Create Q&A session from dictionary."""
        return cls(
            session_id=data['session_id'],
            document_id=data['document_id'],
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class QAInteraction:
    """Individual Q&A interaction model."""
    
    id: Optional[int]
    session_id: str
    question: str
    answer: str
    sources: Optional[List[str]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Q&A interaction to dictionary for storage."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'question': self.question,
            'answer': self.answer,
            'sources': json.dumps(self.sources) if self.sources else None,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QAInteraction':
        """Create Q&A interaction from dictionary."""
        return cls(
            id=data.get('id'),
            session_id=data['session_id'],
            question=data['question'],
            answer=data['answer'],
            sources=json.loads(data['sources']) if data.get('sources') else None,
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.now()
        )