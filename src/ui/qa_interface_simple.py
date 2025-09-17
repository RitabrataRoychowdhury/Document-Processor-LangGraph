"""Simple Q&A Interface with comprehensive error handling."""

import streamlit as st
from typing import Optional

from src.infrastructure.monitoring.ui_error_handler import (
    enhanced_ui_error_boundary, handle_component_failure
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@enhanced_ui_error_boundary(
    page="qa",
    component="qa_interface",
    show_fallback=True,
    show_recovery=True
)
def render_qa_page():
    """Render a simple Q&A page with comprehensive error handling."""
    try:
        st.title("🤖 Document Q&A")
        
        # Check if services are available
        if not _check_qa_services_available():
            st.warning("⚠️ Q&A services are not fully configured. Some features may be limited.")
            
            with st.expander("🔧 Configuration Help", expanded=False):
                st.markdown("""
                **To enable full Q&A functionality:**
                1. Configure your API keys (Gemini or OpenAI)
                2. Ensure documents are uploaded and processed
                3. Restart the application if needed
                """)
        
        st.info("Q&A interface is available. Upload documents and ask questions about them.")
        
        # Enhanced question input with validation
        question = st.text_input(
            "Ask a question:", 
            placeholder="What would you like to know about the document?",
            help="Enter your question about the uploaded documents"
        )
        
        # Document selection if multiple documents available
        available_docs = _get_available_documents()
        if available_docs:
            selected_doc = st.selectbox(
                "Select document (optional):",
                options=["All documents"] + available_docs,
                help="Choose a specific document or search all documents"
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Ask Question", type="primary", disabled=not question.strip()):
                try:
                    _process_question(question, selected_doc if available_docs else None)
                except Exception as e:
                    handle_component_failure(
                        component_name="question_processor",
                        error=e,
                        context={'page': 'qa', 'component': 'question_processing', 'question': question},
                        show_fallback=True,
                        show_recovery=True
                    )
        
        with col2:
            if st.button("Clear Question"):
                st.rerun()
        
        # Show recent questions if available
        _render_recent_questions()
        
    except Exception as e:
        logger.error(f"Error in Q&A page rendering: {e}", exc_info=True)
        handle_component_failure(
            component_name="qa_page",
            error=e,
            context={'page': 'qa', 'component': 'qa_page'},
            show_fallback=True,
            show_recovery=True
        )


@enhanced_ui_error_boundary(
    page="qa",
    component="qa_document_interface",
    show_fallback=True,
    show_recovery=True
)
def render_qa_for_document(document_id: str):
    """Render Q&A interface for a specific document with error handling."""
    try:
        st.title(f"🤖 Q&A for Document: {document_id}")
        
        # Validate document exists
        if not _validate_document_exists(document_id):
            st.error(f"❌ Document {document_id} not found or not accessible.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📄 View All Documents"):
                    st.session_state.switch_to_management = True
                    st.rerun()
            with col2:
                if st.button("📤 Upload New Document"):
                    st.session_state.current_page = "Upload Documents"
                    st.rerun()
            return
        
        # Show document info
        with st.expander(f"📄 Document Info: {document_id}", expanded=False):
            doc_info = _get_document_info(document_id)
            if doc_info:
                st.write(f"**File:** {doc_info.get('filename', 'Unknown')}")
                st.write(f"**Size:** {doc_info.get('size', 'Unknown')}")
                st.write(f"**Uploaded:** {doc_info.get('upload_date', 'Unknown')}")
            else:
                st.info("Document information not available")
        
        render_qa_page()
        
    except Exception as e:
        logger.error(f"Error in document Q&A rendering: {e}", exc_info=True)
        handle_component_failure(
            component_name="qa_document_interface",
            error=e,
            context={'page': 'qa', 'component': 'qa_document', 'document_id': document_id},
            show_fallback=True,
            show_recovery=True
        )


def render_enhanced_qa_page():
    """Render enhanced Q&A page."""
    render_qa_page()


def render_enhanced_qa_page_with_document(document_id: str):
    """Render enhanced Q&A interface for a specific document."""
    render_qa_for_document(document_id)


# Helper functions

def _check_qa_services_available() -> bool:
    """Check if Q&A services are available and configured."""
    try:
        # Check if API keys are configured
        import os
        has_gemini = bool(os.getenv('GEMINI_API_KEY'))
        has_openai = bool(os.getenv('OPENAI_API_KEY'))
        
        return has_gemini or has_openai
    except Exception as e:
        logger.error(f"Error checking Q&A services: {e}")
        return False


def _get_available_documents() -> list:
    """Get list of available documents."""
    try:
        # This would get actual documents from storage
        # For now, return mock data
        if st.session_state.get('uploaded_documents'):
            return list(st.session_state.uploaded_documents.keys())
        return []
    except Exception as e:
        logger.error(f"Error getting available documents: {e}")
        return []


def _validate_document_exists(document_id: str) -> bool:
    """Validate that a document exists and is accessible."""
    try:
        # This would check actual document storage
        available_docs = _get_available_documents()
        return document_id in available_docs
    except Exception as e:
        logger.error(f"Error validating document {document_id}: {e}")
        return False


def _get_document_info(document_id: str) -> dict:
    """Get information about a document."""
    try:
        # This would get actual document information
        # For now, return mock data
        return {
            'filename': f"{document_id}.pdf",
            'size': "2.5 MB",
            'upload_date': "2024-01-15 10:30:00"
        }
    except Exception as e:
        logger.error(f"Error getting document info for {document_id}: {e}")
        return {}


def _process_question(question: str, selected_doc: Optional[str] = None) -> None:
    """Process a user question."""
    try:
        with st.spinner("🤔 Processing your question..."):
            # Simulate processing time
            import time
            time.sleep(1)
            
            # Mock response
            st.success("✅ Question processed successfully!")
            
            # Show mock answer
            st.markdown("**Answer:**")
            st.info(f"This is a mock response to your question: '{question}'. In a full implementation, this would provide an AI-generated answer based on the document content.")
            
            # Store question in session state for recent questions
            if 'recent_questions' not in st.session_state:
                st.session_state.recent_questions = []
            
            st.session_state.recent_questions.insert(0, {
                'question': question,
                'document': selected_doc,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            })
            
            # Keep only last 5 questions
            st.session_state.recent_questions = st.session_state.recent_questions[:5]
            
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise e


def _render_recent_questions() -> None:
    """Render recent questions section."""
    try:
        recent_questions = st.session_state.get('recent_questions', [])
        
        if recent_questions:
            with st.expander("📝 Recent Questions", expanded=False):
                for i, q in enumerate(recent_questions):
                    st.write(f"**Q{i+1}:** {q['question']}")
                    if q.get('document') and q['document'] != "All documents":
                        st.write(f"*Document: {q['document']}*")
                    st.write(f"*Asked: {q['timestamp']}*")
                    st.markdown("---")
    except Exception as e:
        logger.error(f"Error rendering recent questions: {e}")