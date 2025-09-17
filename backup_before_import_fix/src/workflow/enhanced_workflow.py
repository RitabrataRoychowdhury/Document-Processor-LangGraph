"""Enhanced LangGraph workflow for document processing with storage capabilities."""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, TypedDict
import requests
import pickle

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    # Fallback for environments without LangGraph
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = "END"

from src.models.document import Document, ProcessingJob
from src.storage.document_storage import DocumentStorage
from src.config import config

from src.utils.logging_config import get_logger
from src.utils.error_handling import WorkflowError, APIError, handle_errors

logger = get_logger(__name__)


class WorkflowState(TypedDict):
    """Type definition for workflow state."""
    document_id: str
    job_id: str
    api_key: str
    document: str
    document_length: int
    processing_status: str
    document_type: str
    extracted_info: Dict[str, Any]
    analysis: str
    final_summary: str
    embeddings: List[float]
    error: Optional[str]
    next: str


class GeminiDocumentProcessor:
    """Gemini API integration for document processing."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    def call_gemini(self, prompt: str, max_tokens: int = 1000) -> str:
        """Make API call to Gemini."""
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.7
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise Exception(f"Gemini API error: {str(e)}")
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected response format: {e}")
            raise Exception(f"Unexpected API response format: {str(e)}")


class EnhancedDocumentWorkflow:
    """Enhanced document processing workflow with LangGraph and storage."""
    
    def __init__(self, storage: DocumentStorage):
        self.storage = storage
        self.nodes = {
            "document_intake": self.document_intake_node,
            "classification": self.classification_node,
            "extraction": self.extraction_node,
            "analysis": self.analysis_node,
            "embedding_generation": self.embedding_generation_node,
            "storage": self.storage_node,
            "summary_generation": self.summary_generation_node,
            "error_handler": self.error_handler_node
        }
        self.workflow = self._create_langgraph_workflow() if LANGGRAPH_AVAILABLE else None
        
    def document_intake_node(self, state: WorkflowState) -> WorkflowState:
        """Initial document intake and validation."""
        logger.info(f"Processing document intake for job {state['job_id']}")
        
        try:
            # Update job status
            self.storage.update_processing_job(
                state["job_id"], 
                status="processing", 
                current_step="document_intake",
                progress_percentage=10
            )
            
            document = state.get("document", "")
            if not document or len(document.strip()) < 10:
                state["error"] = "Document is too short or empty"
                state["next"] = "error_handler"
                return state

            state["document_length"] = len(document)
            state["processing_status"] = "intake_complete"
            state["next"] = "classification"

            logger.info(f"Document intake complete. Length: {state['document_length']} characters")
            return state
            
        except Exception as e:
            logger.error(f"Error in document intake: {e}")
            state["error"] = f"Document intake failed: {str(e)}"
            state["next"] = "error_handler"
            return state

    def classification_node(self, state: WorkflowState) -> WorkflowState:
        """Classify the document type and determine processing approach."""
        logger.info(f"Classifying document for job {state['job_id']}")
        
        try:
            # Update job status
            self.storage.update_processing_job(
                state["job_id"], 
                current_step="classification",
                progress_percentage=25
            )
            
            processor = GeminiDocumentProcessor(state["api_key"])
            document = state["document"]

            classification_prompt = f"""
            Classify the following document into one of these categories:
            1. Legal Document (contracts, agreements, legal text)
            2. Technical Documentation (manuals, specifications, code documentation)
            3. Business Document (reports, proposals, memos)
            4. Academic Paper (research, thesis, academic writing)
            5. Personal Document (letters, diary entries, personal notes)
            6. News Article (journalism, news reports)
            7. Other

            Document to classify (first 1000 chars):
            {document[:1000]}...

            Respond with just the category name and a brief 1-sentence explanation.
            """

            classification_result = processor.call_gemini(classification_prompt, max_tokens=100)

            state["document_type"] = classification_result.strip()
            state["processing_status"] = "classified"
            state["next"] = "extraction"

            logger.info(f"Document classified as: {classification_result.strip()}")
            return state
            
        except Exception as e:
            logger.error(f"Error in classification: {e}")
            state["error"] = f"Classification failed: {str(e)}"
            state["next"] = "error_handler"
            return state

    def extraction_node(self, state: WorkflowState) -> WorkflowState:
        """Extract key information from the document."""
        logger.info(f"Extracting key information for job {state['job_id']}")
        
        try:
            # Update job status
            self.storage.update_processing_job(
                state["job_id"], 
                current_step="extraction",
                progress_percentage=40
            )
            
            processor = GeminiDocumentProcessor(state["api_key"])
            document = state["document"]
            doc_type = state.get("document_type", "Unknown")

            extraction_prompt = f"""
            Extract the following key information from this document:

            1. Main Topic/Subject
            2. Key Entities (people, organizations, places)
            3. Important Dates
            4. Key Numbers/Statistics
            5. Action Items or Requirements
            6. Summary (2-3 sentences)

            Document Type: {doc_type}

            Document:
            {document}

            Format your response as JSON with the above fields as keys. Use clear, descriptive values.
            """

            extraction_result = processor.call_gemini(extraction_prompt, max_tokens=800)

            try:
                # Clean up the response to extract JSON
                json_start = extraction_result.find('{')
                json_end = extraction_result.rfind('}') + 1

                if json_start >= 0 and json_end > json_start:
                    json_str = extraction_result[json_start:json_end]
                    extracted_info = json.loads(json_str)
                else:
                    raise json.JSONDecodeError("No JSON found", extraction_result, 0)

            except json.JSONDecodeError:
                # Fallback to structured text parsing
                extracted_info = {
                    "Main Topic": "Could not parse structured data",
                    "Raw Extraction": extraction_result
                }

            state["extracted_info"] = extracted_info
            state["processing_status"] = "extracted"
            state["next"] = "analysis"

            logger.info("Information extraction complete")
            return state
            
        except Exception as e:
            logger.error(f"Error in extraction: {e}")
            state["error"] = f"Extraction failed: {str(e)}"
            state["next"] = "error_handler"
            return state

    def analysis_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze the document for insights and recommendations."""
        logger.info(f"Analyzing document for job {state['job_id']}")
        
        try:
            # Update job status
            self.storage.update_processing_job(
                state["job_id"], 
                current_step="analysis",
                progress_percentage=55
            )
            
            processor = GeminiDocumentProcessor(state["api_key"])
            document = state["document"]
            extracted_info = state.get("extracted_info", {})

            analysis_prompt = f"""
            Based on the following document and extracted information, provide:

            1. Key Insights (3-5 bullet points)
            2. Potential Issues or Concerns
            3. Recommendations or Next Steps
            4. Risk Assessment (Low/Medium/High) with reasoning
            5. Priority Level (Low/Medium/High/Urgent)

            Document Type: {state.get('document_type', 'Unknown')}

            Extracted Information:
            {json.dumps(extracted_info, indent=2)}

            Original Document:
            {document}

            Provide a structured analysis with clear sections.
            """

            analysis_result = processor.call_gemini(analysis_prompt, max_tokens=1000)

            state["analysis"] = analysis_result
            state["processing_status"] = "analyzed"
            state["next"] = "embedding_generation"

            logger.info("Document analysis complete")
            return state
            
        except Exception as e:
            logger.error(f"Error in analysis: {e}")
            state["error"] = f"Analysis failed: {str(e)}"
            state["next"] = "error_handler"
            return state

    def embedding_generation_node(self, state: WorkflowState) -> WorkflowState:
        """Generate embeddings for the document for Q&A purposes."""
        logger.info(f"Generating embeddings for job {state['job_id']}")
        
        try:
            # Update job status
            self.storage.update_processing_job(
                state["job_id"], 
                current_step="embedding_generation",
                progress_percentage=70
            )
            
            # For now, create a simple text-based embedding using document content
            # In a production system, you would use a proper embedding model
            document_text = state["document"]
            extracted_info = state.get("extracted_info", {})
            analysis = state.get("analysis", "")
            
            # Create a combined text for embedding
            combined_text = f"""
            Document: {document_text}
            
            Extracted Information: {json.dumps(extracted_info, indent=2)}
            
            Analysis: {analysis}
            """
            
            # Simple hash-based embedding (in production, use proper embedding models)
            # This is a placeholder - you would typically use models like sentence-transformers
            import hashlib
            text_hash = hashlib.sha256(combined_text.encode()).hexdigest()
            
            # Convert hash to a list of floats (mock embedding)
            embeddings = [float(int(text_hash[i:i+2], 16)) / 255.0 for i in range(0, min(len(text_hash), 128), 2)]
            
            state["embeddings"] = embeddings
            state["processing_status"] = "embeddings_generated"
            state["next"] = "storage"

            logger.info("Embedding generation complete")
            return state
            
        except Exception as e:
            logger.error(f"Error in embedding generation: {e}")
            state["error"] = f"Embedding generation failed: {str(e)}"
            state["next"] = "error_handler"
            return state

    def storage_node(self, state: WorkflowState) -> WorkflowState:
        """Store processed document data and results."""
        logger.info(f"Storing document data for job {state['job_id']}")
        
        try:
            # Update job status
            self.storage.update_processing_job(
                state["job_id"], 
                current_step="storage",
                progress_percentage=85
            )
            
            # Update document with processed results
            document_updates = {
                'processing_status': 'processed',
                'document_type': state.get('document_type'),
                'extracted_info': state.get('extracted_info'),
                'analysis': state.get('analysis'),
                'updated_at': datetime.now()
            }
            
            # Store embeddings if available
            if 'embeddings' in state:
                document_updates['embeddings'] = state['embeddings']
            
            self.storage.update_document(state["document_id"], document_updates)
            
            state["processing_status"] = "stored"
            state["next"] = "summary_generation"

            logger.info("Document storage complete")
            return state
            
        except Exception as e:
            logger.error(f"Error in storage: {e}")
            state["error"] = f"Storage failed: {str(e)}"
            state["next"] = "error_handler"
            return state

    def summary_generation_node(self, state: WorkflowState) -> WorkflowState:
        """Generate a comprehensive summary."""
        logger.info(f"Generating final summary for job {state['job_id']}")
        
        try:
            # Update job status
            self.storage.update_processing_job(
                state["job_id"], 
                current_step="summary_generation",
                progress_percentage=95
            )
            
            processor = GeminiDocumentProcessor(state["api_key"])

            summary_prompt = f"""
            Create a comprehensive executive summary based on the following processing results:

            Document Type: {state.get('document_type', 'Unknown')}
            Document Length: {state.get('document_length', 0)} characters

            Extracted Information:
            {json.dumps(state.get('extracted_info', {}), indent=2)}

            Analysis:
            {state.get('analysis', 'No analysis available')}

            Create a clear, actionable executive summary that includes:
            1. Document Overview
            2. Key Findings
            3. Critical Information
            4. Recommended Actions
            5. Executive Recommendation

            Keep it concise but comprehensive. Use clear headings and bullet points where appropriate.
            """

            summary = processor.call_gemini(summary_prompt, max_tokens=800)

            state["final_summary"] = summary
            state["processing_status"] = "complete"
            state["next"] = "END"
            
            # Update document with final summary
            self.storage.update_document(state["document_id"], {
                'summary': summary,
                'processing_status': 'completed',
                'updated_at': datetime.now()
            })
            
            # Complete the processing job
            self.storage.update_processing_job(
                state["job_id"], 
                status="completed",
                current_step="completed",
                progress_percentage=100,
                completed_at=datetime.now()
            )

            logger.info("Summary generation complete")
            return state
            
        except Exception as e:
            logger.error(f"Error in summary generation: {e}")
            state["error"] = f"Summary generation failed: {str(e)}"
            state["next"] = "error_handler"
            return state

    def error_handler_node(self, state: WorkflowState) -> WorkflowState:
        """Handle errors in processing."""
        error_msg = state.get('error', 'Unknown error')
        logger.error(f"Error in processing job {state['job_id']}: {error_msg}")

        try:
            # Update processing job with error
            self.storage.update_processing_job(
                state["job_id"], 
                status="failed",
                error_message=error_msg,
                completed_at=datetime.now()
            )
            
            # Update document status
            self.storage.update_document(state["document_id"], {
                'processing_status': 'failed',
                'updated_at': datetime.now()
            })
            
        except Exception as e:
            logger.error(f"Error updating job status: {e}")

        state["processing_status"] = "error"
        state["next"] = "END"
        return state

    def _create_langgraph_workflow(self):
        """Create a proper LangGraph StateGraph workflow."""
        if not LANGGRAPH_AVAILABLE:
            return None
            
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("document_intake", self.document_intake_node)
        workflow.add_node("classification", self.classification_node)
        workflow.add_node("extraction", self.extraction_node)
        workflow.add_node("analysis", self.analysis_node)
        workflow.add_node("embedding_generation", self.embedding_generation_node)
        workflow.add_node("storage", self.storage_node)
        workflow.add_node("summary_generation", self.summary_generation_node)
        workflow.add_node("error_handler", self.error_handler_node)
        
        # Set entry point
        workflow.set_entry_point("document_intake")
        
        # Add edges based on the next field in state
        workflow.add_conditional_edges(
            "document_intake",
            lambda state: state.get("next", END),
            {
                "classification": "classification",
                "error_handler": "error_handler",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "classification",
            lambda state: state.get("next", END),
            {
                "extraction": "extraction",
                "error_handler": "error_handler",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "extraction",
            lambda state: state.get("next", END),
            {
                "analysis": "analysis",
                "error_handler": "error_handler",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "analysis",
            lambda state: state.get("next", END),
            {
                "embedding_generation": "embedding_generation",
                "error_handler": "error_handler",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "embedding_generation",
            lambda state: state.get("next", END),
            {
                "storage": "storage",
                "error_handler": "error_handler",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "storage",
            lambda state: state.get("next", END),
            {
                "summary_generation": "summary_generation",
                "error_handler": "error_handler",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "summary_generation",
            lambda state: state.get("next", END),
            {
                "error_handler": "error_handler",
                END: END
            }
        )
        
        workflow.add_edge("error_handler", END)
        
        return workflow.compile()

    def run_workflow(self, initial_state: WorkflowState) -> WorkflowState:
        """Run the complete workflow."""
        if LANGGRAPH_AVAILABLE and self.workflow:
            # Use proper LangGraph execution
            try:
                result = self.workflow.invoke(initial_state)
                return result
            except Exception as e:
                logger.error(f"LangGraph workflow execution failed: {e}")
                # Fallback to simple execution
                return self._run_simple_workflow(initial_state)
        else:
            # Fallback to simple workflow execution
            return self._run_simple_workflow(initial_state)
    
    def _run_simple_workflow(self, initial_state: WorkflowState) -> WorkflowState:
        """Fallback simple workflow execution."""
        current_node = "document_intake"
        state = initial_state.copy()

        max_iterations = 10  # Prevent infinite loops
        iterations = 0

        while current_node != "END" and iterations < max_iterations:
            iterations += 1

            if current_node in self.nodes:
                logger.info(f"Executing workflow node: {current_node}")
                state = self.nodes[current_node](state)
                current_node = state.get("next", "END")
            else:
                logger.error(f"Unknown workflow node: {current_node}")
                state["error"] = f"Unknown workflow node: {current_node}"
                state = self.error_handler_node(state)
                break

        return state

    def process_document(self, document_id: str, document_text: str, api_key: str) -> str:
        """Process a document through the complete workflow."""
        # Create processing job
        job_id = str(uuid.uuid4())
        
        processing_job = ProcessingJob(
            job_id=job_id,
            document_id=document_id,
            status="pending",
            current_step="initializing"
        )
        
        self.storage.create_processing_job(processing_job)
        
        # Initial workflow state
        initial_state: WorkflowState = {
            "document_id": document_id,
            "job_id": job_id,
            "api_key": api_key,
            "document": document_text,
            "document_length": 0,
            "processing_status": "initialized",
            "document_type": "",
            "extracted_info": {},
            "analysis": "",
            "final_summary": "",
            "embeddings": [],
            "error": None,
            "next": "document_intake"
        }

        try:
            # Run the workflow
            result = self.run_workflow(initial_state)
            logger.info(f"Workflow completed for job {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error in document processing workflow: {e}")
            # Update job with error
            self.storage.update_processing_job(
                job_id, 
                status="failed",
                error_message=str(e),
                completed_at=datetime.now()
            )
            raise

    def get_processing_status(self, job_id: str) -> Optional[ProcessingJob]:
        """Get the current processing status of a job."""
        return self.storage.get_processing_job(job_id)


def create_enhanced_workflow(storage: Optional[DocumentStorage] = None) -> EnhancedDocumentWorkflow:
    """Factory function to create an enhanced document workflow."""
    if storage is None:
        from src.storage.document_storage import DocumentStorage
        storage = DocumentStorage()
    
    return EnhancedDocumentWorkflow(storage)


def process_document_with_enhanced_workflow(document_id: str, document_text: str, api_key: str) -> str:
    """Convenience function to process a document with the enhanced workflow."""
    storage = DocumentStorage()
    workflow = EnhancedDocumentWorkflow(storage)
    
    return workflow.process_document(document_id, document_text, api_key)