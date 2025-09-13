"""NER (Named Entity Recognition) command for extracting entities from documents."""

from typing import Dict, Any, List, Optional
import logging

from .base import Command, CommandResult, RetryableException, NonRetryableException
from src.strategies.embedding_strategy import EmbeddingStrategy, LocalEmbeddingStrategy
from src.storage.document_storage import DocumentStorage

logger = logging.getLogger(__name__)


class NERCommand(Command):
    """Command for performing Named Entity Recognition on document content."""
    
    def __init__(self, document_id: str, 
                 embedding_strategy: Optional[EmbeddingStrategy] = None,
                 storage: Optional[DocumentStorage] = None):
        super().__init__()
        self.document_id = document_id
        self.embedding_strategy = embedding_strategy or LocalEmbeddingStrategy()
        self.storage = storage or DocumentStorage()
    
    def execute(self) -> CommandResult:
        """Execute Named Entity Recognition on the document."""
        try:
            logger.info(f"Starting NER processing for document: {self.document_id}")
            
            # Retrieve document
            document = self.storage.get_document(self.document_id)
            if not document:
                return CommandResult.failure_result(
                    message=f"Document not found: {self.document_id}",
                    error=NonRetryableException("Document not found")
                )
            
            if not document.original_text:
                return CommandResult.failure_result(
                    message="Document has no text content for NER processing",
                    error=NonRetryableException("No text content")
                )
            
            # Extract entities using a simple approach for now
            # In a full implementation, this would use spaCy or similar NER library
            entities = self._extract_entities(document.original_text)
            
            # Generate embeddings for the document text
            try:
                embeddings = self.embedding_strategy.generate_embeddings(document.original_text)
            except Exception as e:
                logger.warning(f"Embedding generation failed: {e}")
                # Embedding failures are often retryable (API issues, etc.)
                raise RetryableException(f"Failed to generate embeddings: {str(e)}")
            
            # Store entities and embeddings in document metadata
            ner_data = {
                'entities': entities,
                'embeddings': embeddings,
                'ner_processed': True
            }
            
            # Update document with NER results
            updated_extracted_info = document.extracted_info.copy() if document.extracted_info else {}
            updated_extracted_info.update(ner_data)
            
            self.storage.update_document(self.document_id, {
                'extracted_info': updated_extracted_info,
                'processing_status': 'ner_completed'
            })
            
            result_data = {
                'document_id': self.document_id,
                'entities_count': len(entities),
                'entity_types': list(set(entity['type'] for entity in entities)),
                'embeddings_dimension': len(embeddings) if embeddings else 0
            }
            
            logger.info(f"Successfully completed NER for document {self.document_id}, found {len(entities)} entities")
            
            return CommandResult.success_result(
                message=f"Successfully completed NER processing for document {self.document_id}",
                data=result_data
            )
            
        except RetryableException:
            # Re-raise retryable exceptions
            raise
        except NonRetryableException as e:
            return CommandResult.failure_result(
                message=f"Non-retryable error during NER: {str(e)}",
                error=e
            )
        except Exception as e:
            logger.error(f"Unexpected error during NER processing: {e}")
            # Treat unexpected errors as retryable
            raise RetryableException(f"Unexpected NER error: {str(e)}")
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.
        
        This is a simplified implementation for the POC.
        In a full implementation, this would use spaCy or similar NER library.
        """
        entities = []
        
        # Simple pattern-based entity extraction for medical documents
        import re
        
        # Extract potential patient names (capitalized words after "Patient:" or similar)
        patient_patterns = [
            r'Patient:?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Name:?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in patient_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group(1),
                    'type': 'PATIENT',
                    'start': match.start(1),
                    'end': match.end(1),
                    'confidence': 0.8
                })
        
        # Extract potential diagnoses (words ending with common medical suffixes)
        diagnosis_patterns = [
            r'\b([A-Z][a-z]*(?:itis|osis|emia|pathy|trophy|plasia|sclerosis))\b',
            r'\b(diabetes|hypertension|arthritis|pneumonia|bronchitis)\b'
        ]
        
        for pattern in diagnosis_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group(1),
                    'type': 'DIAGNOSIS',
                    'start': match.start(1),
                    'end': match.end(1),
                    'confidence': 0.7
                })
        
        # Extract dates
        date_pattern = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b'
        matches = re.finditer(date_pattern, text)
        for match in matches:
            entities.append({
                'text': match.group(1),
                'type': 'DATE',
                'start': match.start(1),
                'end': match.end(1),
                'confidence': 0.9
            })
        
        # Extract percentages (potential impairment ratings)
        percentage_pattern = r'\b(\d{1,3}%)\b'
        matches = re.finditer(percentage_pattern, text)
        for match in matches:
            entities.append({
                'text': match.group(1),
                'type': 'PERCENTAGE',
                'start': match.start(1),
                'end': match.end(1),
                'confidence': 0.6
            })
        
        # Remove duplicates and sort by position
        unique_entities = []
        seen = set()
        for entity in sorted(entities, key=lambda x: x['start']):
            key = (entity['text'].lower(), entity['type'], entity['start'])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def can_retry(self) -> bool:
        """NER operations can be retried for certain types of failures."""
        return True
    
    def get_command_info(self) -> Dict[str, Any]:
        """Get information about this NER command."""
        info = super().get_command_info()
        info.update({
            'document_id': self.document_id,
            'embedding_strategy': self.embedding_strategy.__class__.__name__
        })
        return info