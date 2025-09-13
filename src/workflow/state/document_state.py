"""Document processing workflow state management."""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.state.workflow_state import WorkflowState
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class DocumentState(WorkflowState):
    """State manager for document processing workflows.
    
    Implements Single Responsibility Principle - manages document-specific state.
    Extends WorkflowState with document-specific functionality.
    """
    
    def __init__(self, state_id: str = None, correlation_id: str = None):
        super().__init__(state_id, correlation_id)
        self._workflow_type = "document"
    
    def initialize_state(self, initial_data: Dict[str, Any]) -> None:
        """Initialize document processing state."""
        # Add document-specific required data
        document_data = {
            'document_id': initial_data.get('document_id'),
            'file_path': initial_data.get('file_path'),
            'file_type': initial_data.get('file_type', 'unknown'),
            'file_size': initial_data.get('file_size', 0),
            'processing_stage': 'initialization',
            'extracted_text': None,
            'document_metadata': {},
            'entities_extracted': [],
            'embeddings_generated': False,
            'knowledge_graph_populated': False,
            'processing_errors': [],
            **initial_data
        }
        
        super().initialize_state(document_data)
        logger.info(f"Initialized document processing state for {document_data.get('file_path')}")
    
    def validate_state(self, state_data: Dict[str, Any]) -> bool:
        """Validate document processing state."""
        if not super().validate_state(state_data):
            return False
        
        # Document-specific validations
        document_id = state_data.get('document_id')
        if not document_id:
            logger.error("Missing document_id in document state")
            return False
        
        file_path = state_data.get('file_path')
        if not file_path:
            logger.error("Missing file_path in document state")
            return False
        
        file_size = state_data.get('file_size', 0)
        if not isinstance(file_size, (int, float)) or file_size < 0:
            logger.error(f"Invalid file_size: {file_size}")
            return False
        
        processing_stage = state_data.get('processing_stage')
        valid_stages = self.get_valid_processing_stages()
        if processing_stage not in valid_stages:
            logger.error(f"Invalid processing_stage: {processing_stage}")
            return False
        
        return True
    
    def get_required_keys(self) -> List[str]:
        """Get required keys for document processing state."""
        base_keys = super().get_required_keys()
        document_keys = [
            'document_id',
            'file_path',
            'file_type',
            'file_size',
            'processing_stage'
        ]
        return base_keys + document_keys
    
    def get_valid_processing_stages(self) -> List[str]:
        """Get valid processing stages for document workflow."""
        return [
            'initialization',
            'text_extraction',
            'section_segmentation',
            'entity_recognition',
            'embedding_generation',
            'knowledge_graph_population',
            'indexing',
            'completed',
            'failed'
        ]
    
    def start_text_extraction(self) -> None:
        """Start text extraction stage."""
        self.update_state({
            'processing_stage': 'text_extraction',
            'current_step': 'extracting_text'
        })
        self.update_progress('text_extraction', 10)
        logger.debug(f"Started text extraction for document {self.get_value('document_id')}")
    
    def complete_text_extraction(self, extracted_text: str, metadata: Dict[str, Any] = None) -> None:
        """Complete text extraction stage."""
        extraction_data = {
            'processing_stage': 'text_extraction_complete',
            'extracted_text': extracted_text,
            'text_length': len(extracted_text),
            'extraction_completed_at': datetime.now().isoformat()
        }
        
        if metadata:
            extraction_data['document_metadata'] = metadata
        
        self.update_state(extraction_data)
        self.update_progress('text_extraction_complete', 25)
        logger.info(f"Completed text extraction for document {self.get_value('document_id')} "
                   f"({len(extracted_text)} characters)")
    
    def start_entity_recognition(self) -> None:
        """Start entity recognition stage."""
        self.update_state({
            'processing_stage': 'entity_recognition',
            'current_step': 'extracting_entities'
        })
        self.update_progress('entity_recognition', 40)
        logger.debug(f"Started entity recognition for document {self.get_value('document_id')}")
    
    def complete_entity_recognition(self, entities: List[Dict[str, Any]]) -> None:
        """Complete entity recognition stage."""
        self.update_state({
            'processing_stage': 'entity_recognition_complete',
            'entities_extracted': entities,
            'entity_count': len(entities),
            'ner_completed_at': datetime.now().isoformat()
        })
        self.update_progress('entity_recognition_complete', 55)
        logger.info(f"Completed entity recognition for document {self.get_value('document_id')} "
                   f"({len(entities)} entities)")
    
    def start_embedding_generation(self) -> None:
        """Start embedding generation stage."""
        self.update_state({
            'processing_stage': 'embedding_generation',
            'current_step': 'generating_embeddings'
        })
        self.update_progress('embedding_generation', 70)
        logger.debug(f"Started embedding generation for document {self.get_value('document_id')}")
    
    def complete_embedding_generation(self, embeddings_info: Dict[str, Any]) -> None:
        """Complete embedding generation stage."""
        self.update_state({
            'processing_stage': 'embedding_generation_complete',
            'embeddings_generated': True,
            'embeddings_info': embeddings_info,
            'embedding_completed_at': datetime.now().isoformat()
        })
        self.update_progress('embedding_generation_complete', 85)
        logger.info(f"Completed embedding generation for document {self.get_value('document_id')}")
    
    def start_knowledge_graph_population(self) -> None:
        """Start knowledge graph population stage."""
        self.update_state({
            'processing_stage': 'knowledge_graph_population',
            'current_step': 'populating_knowledge_graph'
        })
        self.update_progress('knowledge_graph_population', 90)
        logger.debug(f"Started KG population for document {self.get_value('document_id')}")
    
    def complete_knowledge_graph_population(self, kg_info: Dict[str, Any]) -> None:
        """Complete knowledge graph population stage."""
        self.update_state({
            'processing_stage': 'knowledge_graph_population_complete',
            'knowledge_graph_populated': True,
            'kg_info': kg_info,
            'kg_completed_at': datetime.now().isoformat()
        })
        self.update_progress('knowledge_graph_population_complete', 95)
        logger.info(f"Completed KG population for document {self.get_value('document_id')}")
    
    def add_processing_error(self, stage: str, error_message: str, error_details: Dict[str, Any] = None) -> None:
        """Add a processing error to the state."""
        error_entry = {
            'stage': stage,
            'error_message': error_message,
            'timestamp': datetime.now().isoformat(),
            'details': error_details or {}
        }
        
        current_errors = self.get_value('processing_errors', [])
        current_errors.append(error_entry)
        
        self.update_state({
            'processing_errors': current_errors,
            'last_error': error_entry
        })
        
        logger.error(f"Added processing error for document {self.get_value('document_id')} "
                    f"at stage {stage}: {error_message}")
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get a summary of document processing."""
        base_summary = self.get_workflow_summary()
        
        document_summary = {
            'document_id': self.get_value('document_id'),
            'file_path': self.get_value('file_path'),
            'file_type': self.get_value('file_type'),
            'file_size': self.get_value('file_size'),
            'processing_stage': self.get_value('processing_stage'),
            'text_length': self.get_value('text_length', 0),
            'entity_count': self.get_value('entity_count', 0),
            'embeddings_generated': self.get_value('embeddings_generated', False),
            'knowledge_graph_populated': self.get_value('knowledge_graph_populated', False),
            'error_count': len(self.get_value('processing_errors', [])),
            'last_error': self.get_value('last_error')
        }
        
        return {**base_summary, **document_summary}
    
    def is_text_extracted(self) -> bool:
        """Check if text extraction is complete."""
        return self.get_value('extracted_text') is not None
    
    def is_entities_extracted(self) -> bool:
        """Check if entity extraction is complete."""
        return len(self.get_value('entities_extracted', [])) > 0
    
    def is_embeddings_generated(self) -> bool:
        """Check if embeddings are generated."""
        return self.get_value('embeddings_generated', False)
    
    def is_knowledge_graph_populated(self) -> bool:
        """Check if knowledge graph is populated."""
        return self.get_value('knowledge_graph_populated', False)
    
    def get_extracted_text(self) -> Optional[str]:
        """Get extracted text."""
        return self.get_value('extracted_text')
    
    def get_extracted_entities(self) -> List[Dict[str, Any]]:
        """Get extracted entities."""
        return self.get_value('entities_extracted', [])
    
    def get_processing_errors(self) -> List[Dict[str, Any]]:
        """Get processing errors."""
        return self.get_value('processing_errors', [])
    
    def has_processing_errors(self) -> bool:
        """Check if there are processing errors."""
        return len(self.get_value('processing_errors', [])) > 0