"""
Processing Metadata Tracking and Source Reference Management Service.

This module provides comprehensive tracking of processing metadata and source references
throughout the document processing pipeline, ensuring complete provenance and auditability.
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from src.models.extraction_models import ProcessingMetadata, SourceReference
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessingStep:
    """Individual processing step with metadata."""
    step_id: str
    step_name: str
    step_type: str  # extraction, validation, transformation, storage
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: str = "in_progress"  # in_progress, completed, failed
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class DocumentProcessingTrace:
    """Complete processing trace for a document."""
    document_id: str
    document_path: str
    processing_session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None
    status: str = "in_progress"
    processing_steps: List[ProcessingStep] = field(default_factory=list)
    source_references: List[SourceReference] = field(default_factory=list)
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    final_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceReferenceChain:
    """Chain of source references showing data lineage."""
    chain_id: str
    document_id: str
    original_source: SourceReference
    derived_references: List[SourceReference] = field(default_factory=list)
    transformation_steps: List[str] = field(default_factory=list)
    confidence_degradation: float = 0.0


class MetadataTrackingService:
    """
    Service for tracking processing metadata and source references.
    
    Features:
    - Complete processing step tracking
    - Source reference management and lineage
    - Quality metrics aggregation
    - Audit trail generation
    - Performance monitoring
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize metadata tracking service.
        
        Args:
            storage_path: Optional path for persistent storage
        """
        self.storage_path = storage_path
        self.active_traces: Dict[str, DocumentProcessingTrace] = {}
        self.completed_traces: Dict[str, DocumentProcessingTrace] = {}
        self.source_reference_chains: Dict[str, SourceReferenceChain] = {}
        
        # Performance metrics
        self.performance_metrics = {
            'total_documents_processed': 0,
            'average_processing_time': 0.0,
            'step_performance': {},
            'error_rates': {},
            'quality_trends': []
        }
        
        logger.info("Initialized MetadataTrackingService")
    
    def start_document_processing(self, document_path: str, document_id: Optional[str] = None) -> str:
        """
        Start tracking processing for a document.
        
        Args:
            document_path: Path to the document being processed
            document_id: Optional document ID, generated if not provided
            
        Returns:
            Processing session ID
        """
        if not document_id:
            document_id = self._generate_document_id(document_path)
        
        session_id = str(uuid.uuid4())
        
        trace = DocumentProcessingTrace(
            document_id=document_id,
            document_path=document_path,
            processing_session_id=session_id,
            start_time=datetime.now()
        )
        
        self.active_traces[session_id] = trace
        
        logger.info(f"Started processing trace for document {document_id}, session {session_id}")
        
        return session_id
    
    def start_processing_step(self, 
                            session_id: str,
                            step_name: str,
                            step_type: str,
                            input_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Start tracking a processing step.
        
        Args:
            session_id: Processing session ID
            step_name: Name of the processing step
            step_type: Type of processing step
            input_data: Optional input data for the step
            
        Returns:
            Step ID
        """
        if session_id not in self.active_traces:
            raise ValueError(f"No active trace found for session {session_id}")
        
        step_id = str(uuid.uuid4())
        
        step = ProcessingStep(
            step_id=step_id,
            step_name=step_name,
            step_type=step_type,
            start_time=datetime.now(),
            input_data=input_data or {}
        )
        
        self.active_traces[session_id].processing_steps.append(step)
        
        logger.debug(f"Started processing step {step_name} (ID: {step_id}) for session {session_id}")
        
        return step_id
    
    def complete_processing_step(self,
                               session_id: str,
                               step_id: str,
                               output_data: Optional[Dict[str, Any]] = None,
                               metadata: Optional[Dict[str, Any]] = None,
                               source_references: Optional[List[SourceReference]] = None) -> None:
        """
        Complete a processing step.
        
        Args:
            session_id: Processing session ID
            step_id: Step ID
            output_data: Optional output data from the step
            metadata: Optional step metadata
            source_references: Optional source references generated by the step
        """
        if session_id not in self.active_traces:
            raise ValueError(f"No active trace found for session {session_id}")
        
        trace = self.active_traces[session_id]
        step = self._find_step_by_id(trace, step_id)
        
        if not step:
            raise ValueError(f"No step found with ID {step_id}")
        
        # Update step
        step.end_time = datetime.now()
        step.duration_seconds = (step.end_time - step.start_time).total_seconds()
        step.status = "completed"
        step.output_data = output_data or {}
        step.metadata = metadata or {}
        
        # Add source references to trace
        if source_references:
            trace.source_references.extend(source_references)
            
            # Create source reference chains
            for ref in source_references:
                self._create_or_update_reference_chain(trace.document_id, ref, step.step_name)
        
        # Update performance metrics
        self._update_step_performance_metrics(step.step_name, step.duration_seconds)
        
        logger.debug(f"Completed processing step {step.step_name} in {step.duration_seconds:.2f}s")
    
    def fail_processing_step(self,
                           session_id: str,
                           step_id: str,
                           error_message: str,
                           metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark a processing step as failed.
        
        Args:
            session_id: Processing session ID
            step_id: Step ID
            error_message: Error message
            metadata: Optional error metadata
        """
        if session_id not in self.active_traces:
            raise ValueError(f"No active trace found for session {session_id}")
        
        trace = self.active_traces[session_id]
        step = self._find_step_by_id(trace, step_id)
        
        if not step:
            raise ValueError(f"No step found with ID {step_id}")
        
        # Update step
        step.end_time = datetime.now()
        step.duration_seconds = (step.end_time - step.start_time).total_seconds()
        step.status = "failed"
        step.error_message = error_message
        step.metadata = metadata or {}
        
        # Update error rate metrics
        self._update_error_rate_metrics(step.step_name)
        
        logger.error(f"Processing step {step.step_name} failed: {error_message}")
    
    def complete_document_processing(self,
                                   session_id: str,
                                   quality_metrics: Optional[Dict[str, float]] = None,
                                   final_metadata: Optional[Dict[str, Any]] = None) -> DocumentProcessingTrace:
        """
        Complete document processing and finalize trace.
        
        Args:
            session_id: Processing session ID
            quality_metrics: Optional quality metrics
            final_metadata: Optional final processing metadata
            
        Returns:
            Completed processing trace
        """
        if session_id not in self.active_traces:
            raise ValueError(f"No active trace found for session {session_id}")
        
        trace = self.active_traces[session_id]
        
        # Finalize trace
        trace.end_time = datetime.now()
        trace.total_duration_seconds = (trace.end_time - trace.start_time).total_seconds()
        trace.status = "completed"
        trace.quality_metrics = quality_metrics or {}
        trace.final_metadata = final_metadata or {}
        
        # Move to completed traces
        self.completed_traces[session_id] = trace
        del self.active_traces[session_id]
        
        # Update overall performance metrics
        self._update_overall_performance_metrics(trace)
        
        # Store trace if storage is configured
        if self.storage_path:
            self._store_trace(trace)
        
        logger.info(f"Completed document processing for session {session_id} in {trace.total_duration_seconds:.2f}s")
        
        return trace
    
    def fail_document_processing(self,
                               session_id: str,
                               error_message: str,
                               final_metadata: Optional[Dict[str, Any]] = None) -> DocumentProcessingTrace:
        """
        Mark document processing as failed.
        
        Args:
            session_id: Processing session ID
            error_message: Error message
            final_metadata: Optional final metadata
            
        Returns:
            Failed processing trace
        """
        if session_id not in self.active_traces:
            raise ValueError(f"No active trace found for session {session_id}")
        
        trace = self.active_traces[session_id]
        
        # Finalize trace
        trace.end_time = datetime.now()
        trace.total_duration_seconds = (trace.end_time - trace.start_time).total_seconds()
        trace.status = "failed"
        trace.final_metadata = final_metadata or {}
        trace.final_metadata['error_message'] = error_message
        
        # Move to completed traces
        self.completed_traces[session_id] = trace
        del self.active_traces[session_id]
        
        logger.error(f"Document processing failed for session {session_id}: {error_message}")
        
        return trace
    
    def add_source_reference(self,
                           session_id: str,
                           source_reference: SourceReference,
                           step_name: Optional[str] = None) -> None:
        """
        Add a source reference to the processing trace.
        
        Args:
            session_id: Processing session ID
            source_reference: Source reference to add
            step_name: Optional step name that generated the reference
        """
        if session_id not in self.active_traces:
            raise ValueError(f"No active trace found for session {session_id}")
        
        trace = self.active_traces[session_id]
        trace.source_references.append(source_reference)
        
        # Create or update reference chain
        self._create_or_update_reference_chain(
            trace.document_id, source_reference, step_name or "unknown"
        )
        
        logger.debug(f"Added source reference for session {session_id}")
    
    def get_processing_trace(self, session_id: str) -> Optional[DocumentProcessingTrace]:
        """Get processing trace by session ID."""
        if session_id in self.active_traces:
            return self.active_traces[session_id]
        elif session_id in self.completed_traces:
            return self.completed_traces[session_id]
        else:
            return None
    
    def get_source_reference_chain(self, document_id: str) -> List[SourceReferenceChain]:
        """Get source reference chains for a document."""
        return [
            chain for chain in self.source_reference_chains.values()
            if chain.document_id == document_id
        ]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            **self.performance_metrics,
            'active_traces': len(self.active_traces),
            'completed_traces': len(self.completed_traces),
            'total_reference_chains': len(self.source_reference_chains)
        }
    
    def generate_audit_report(self, document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate audit report for processing activities.
        
        Args:
            document_id: Optional document ID to filter by
            
        Returns:
            Audit report dictionary
        """
        report = {
            'report_generated_at': datetime.now().isoformat(),
            'summary': {
                'total_documents_processed': self.performance_metrics['total_documents_processed'],
                'active_processing_sessions': len(self.active_traces),
                'completed_processing_sessions': len(self.completed_traces)
            },
            'processing_traces': [],
            'source_reference_chains': [],
            'performance_summary': self.performance_metrics
        }
        
        # Filter traces by document ID if specified
        traces_to_include = []
        if document_id:
            traces_to_include = [
                trace for trace in self.completed_traces.values()
                if trace.document_id == document_id
            ]
        else:
            traces_to_include = list(self.completed_traces.values())
        
        # Add processing traces to report
        for trace in traces_to_include:
            report['processing_traces'].append(self._serialize_trace(trace))
        
        # Add source reference chains
        chains_to_include = self.get_source_reference_chain(document_id) if document_id else list(self.source_reference_chains.values())
        for chain in chains_to_include:
            report['source_reference_chains'].append(asdict(chain))
        
        return report
    
    def _find_step_by_id(self, trace: DocumentProcessingTrace, step_id: str) -> Optional[ProcessingStep]:
        """Find processing step by ID."""
        for step in trace.processing_steps:
            if step.step_id == step_id:
                return step
        return None
    
    def _create_or_update_reference_chain(self,
                                        document_id: str,
                                        source_reference: SourceReference,
                                        step_name: str) -> None:
        """Create or update source reference chain."""
        # Simple implementation - in production, this would be more sophisticated
        chain_id = f"{document_id}_{source_reference.section or 'unknown'}"
        
        if chain_id not in self.source_reference_chains:
            self.source_reference_chains[chain_id] = SourceReferenceChain(
                chain_id=chain_id,
                document_id=document_id,
                original_source=source_reference
            )
        else:
            chain = self.source_reference_chains[chain_id]
            chain.derived_references.append(source_reference)
            chain.transformation_steps.append(step_name)
    
    def _update_step_performance_metrics(self, step_name: str, duration: float) -> None:
        """Update performance metrics for a processing step."""
        if step_name not in self.performance_metrics['step_performance']:
            self.performance_metrics['step_performance'][step_name] = {
                'total_executions': 0,
                'total_time': 0.0,
                'average_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0
            }
        
        metrics = self.performance_metrics['step_performance'][step_name]
        metrics['total_executions'] += 1
        metrics['total_time'] += duration
        metrics['average_time'] = metrics['total_time'] / metrics['total_executions']
        metrics['min_time'] = min(metrics['min_time'], duration)
        metrics['max_time'] = max(metrics['max_time'], duration)
    
    def _update_error_rate_metrics(self, step_name: str) -> None:
        """Update error rate metrics for a processing step."""
        if step_name not in self.performance_metrics['error_rates']:
            self.performance_metrics['error_rates'][step_name] = {
                'total_attempts': 0,
                'total_errors': 0,
                'error_rate': 0.0
            }
        
        metrics = self.performance_metrics['error_rates'][step_name]
        metrics['total_attempts'] += 1
        metrics['total_errors'] += 1
        metrics['error_rate'] = metrics['total_errors'] / metrics['total_attempts']
    
    def _update_overall_performance_metrics(self, trace: DocumentProcessingTrace) -> None:
        """Update overall performance metrics."""
        self.performance_metrics['total_documents_processed'] += 1
        
        # Update average processing time
        total_docs = self.performance_metrics['total_documents_processed']
        current_avg = self.performance_metrics['average_processing_time']
        new_time = trace.total_duration_seconds or 0
        
        self.performance_metrics['average_processing_time'] = (
            (current_avg * (total_docs - 1) + new_time) / total_docs
        )
        
        # Add quality metrics to trends
        if trace.quality_metrics:
            quality_entry = {
                'timestamp': trace.end_time.isoformat() if trace.end_time else datetime.now().isoformat(),
                'document_id': trace.document_id,
                'metrics': trace.quality_metrics
            }
            self.performance_metrics['quality_trends'].append(quality_entry)
            
            # Keep only last 100 entries
            if len(self.performance_metrics['quality_trends']) > 100:
                self.performance_metrics['quality_trends'] = self.performance_metrics['quality_trends'][-100:]
    
    def _generate_document_id(self, document_path: str) -> str:
        """Generate document ID from path."""
        import hashlib
        path_hash = hashlib.md5(document_path.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"doc_{timestamp}_{path_hash}"
    
    def _serialize_trace(self, trace: DocumentProcessingTrace) -> Dict[str, Any]:
        """Serialize processing trace for storage/reporting."""
        return {
            'document_id': trace.document_id,
            'document_path': trace.document_path,
            'processing_session_id': trace.processing_session_id,
            'start_time': trace.start_time.isoformat(),
            'end_time': trace.end_time.isoformat() if trace.end_time else None,
            'total_duration_seconds': trace.total_duration_seconds,
            'status': trace.status,
            'processing_steps': [
                {
                    'step_id': step.step_id,
                    'step_name': step.step_name,
                    'step_type': step.step_type,
                    'start_time': step.start_time.isoformat(),
                    'end_time': step.end_time.isoformat() if step.end_time else None,
                    'duration_seconds': step.duration_seconds,
                    'status': step.status,
                    'metadata': step.metadata,
                    'error_message': step.error_message
                }
                for step in trace.processing_steps
            ],
            'source_references': [asdict(ref) for ref in trace.source_references],
            'quality_metrics': trace.quality_metrics,
            'final_metadata': trace.final_metadata
        }
    
    def _store_trace(self, trace: DocumentProcessingTrace) -> None:
        """Store processing trace to persistent storage."""
        try:
            if not self.storage_path:
                return
            
            storage_dir = Path(self.storage_path)
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            trace_file = storage_dir / f"trace_{trace.processing_session_id}.json"
            
            with open(trace_file, 'w') as f:
                json.dump(self._serialize_trace(trace), f, indent=2)
            
            logger.debug(f"Stored processing trace to {trace_file}")
            
        except Exception as e:
            logger.error(f"Error storing processing trace: {str(e)}")


# Global metadata tracking service instance
metadata_tracking_service = MetadataTrackingService()