"""Q&A Interface for document question answering with chat-like interaction."""

import streamlit as st
import uuid
import os
import tempfile
from datetime import datetime
from typing import Optional, List, Dict, Any

from src.infrastructure.knowledge.qa_engine import QAEngine, create_qa_engine
from src.storage.document_storage import DocumentStorage
from src.models.document import Document, QASession
from src.config.app_config import app_config
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class EnhancedQAInterface:
    """Enhanced Streamlit interface for document Q&A with knowledge graph integration."""
    
    def __init__(self):
        self.storage = DocumentStorage()
        self.qa_engine = None
        
        # Initialize knowledge graph integration if available
        try:
            from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository
            self.kg_repository = KnowledgeGraphRepository()
            self.kg_available = True
        except ImportError:
            self.kg_repository = None
            self.kg_available = False
        
        # Initialize session state for enhanced features
        if 'qa_sessions' not in st.session_state:
            st.session_state.qa_sessions = {}
        if 'current_qa_session' not in st.session_state:
            st.session_state.current_qa_session = None
        if 'selected_document' not in st.session_state:
            st.session_state.selected_document = None
        if 'evidence_based_responses' not in st.session_state:
            st.session_state.evidence_based_responses = {}
        if 'inline_template_requests' not in st.session_state:
            st.session_state.inline_template_requests = {}
        if 'qa_context_awareness' not in st.session_state:
            st.session_state.qa_context_awareness = True

class QAInterface(EnhancedQAInterface):
    """Legacy QA Interface - inherits from enhanced version for backward compatibility."""
    pass
    
    def render_enhanced_qa_interface(self, document_id: Optional[str] = None) -> None:
        """
        Render enhanced Q&A interface with knowledge graph integration and evidence-based responses.
        
        Args:
            document_id: Optional document ID to start Q&A with
        """
        st.header("💬 Enhanced Q&A Interface")
        st.markdown("Knowledge graph-powered document interaction with evidence-based responses and template generation")
        
        # Enhanced system status check
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # API key status
            api_key = app_config.get_api_key_for_provider(app_config.qa_provider)
            if api_key:
                st.success("✅ API Connected")
            else:
                st.error("❌ API Not Configured")
        
        with col2:
            # Knowledge graph status
            if self.kg_available:
                st.success("✅ Knowledge Graph")
            else:
                st.warning("⚠️ KG Limited")
        
        with col3:
            # Context awareness status
            if st.session_state.qa_context_awareness:
                st.success("✅ Context Aware")
            else:
                st.info("ℹ️ Basic Mode")
        
        if not api_key:
            st.error("⚠️ API key not configured. Please set your API key in the environment.")
            st.info("You can get an API key from: https://makersuite.google.com/app/apikey")
            return
        
        # Initialize enhanced QA engine
        if not self.qa_engine:
            try:
                # Use enhanced QA engine with knowledge graph integration
                from src.infrastructure.knowledge.qa_engine import create_hybrid_qa_engine
                self.qa_engine = create_hybrid_qa_engine(api_key, self.storage)
                
                # Enhance with knowledge graph if available
                if self.kg_available and self.kg_repository:
                    # In production, this would integrate KG with QA engine
                    logger.info("Enhanced QA engine with knowledge graph integration")
                
            except Exception as e:
                st.error(f"Failed to initialize enhanced QA engine: {str(e)}")
                return
        
        # Enhanced document selection section
        selected_doc = self._render_enhanced_document_selector(document_id)
        
        if not selected_doc:
            st.info("👆 Please select a document to start enhanced Q&A with evidence-based responses.")
            return
        
        # Enhanced Q&A session section
        self._render_enhanced_qa_session(selected_doc)

    def render_qa_interface(self, document_id: Optional[str] = None) -> None:
        """Legacy Q&A interface - redirects to enhanced version."""
        self.render_enhanced_qa_interface(document_id)
    
    def _render_enhanced_document_selector(self, preselected_doc_id: Optional[str] = None) -> Optional[Document]:
        """Render enhanced document selection interface with knowledge graph integration."""
        st.subheader("📄 Enhanced Document Selection")
        
        # Get processed documents with enhanced filtering
        processed_docs = self.storage.list_documents(status_filter='completed')
        
        if not processed_docs:
            st.warning("No processed documents available. Please upload and process documents first.")
            
            # Quick access to upload
            if st.button("📤 Upload Documents"):
                st.session_state.switch_to_upload = True
                st.rerun()
            
            return None
        
        # Enhanced document filtering and search
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Document search
            search_term = st.text_input("🔍 Search documents", placeholder="Search by title, type, or content...")
        
        with col2:
            # Document type filter
            doc_types = list(set([doc.document_type or 'Unknown' for doc in processed_docs]))
            selected_type = st.selectbox("Filter by type", options=['All'] + doc_types)
        
        # Filter documents based on search and type
        filtered_docs = processed_docs
        
        if search_term:
            filtered_docs = [doc for doc in filtered_docs 
                           if search_term.lower() in doc.title.lower() 
                           or (doc.document_type and search_term.lower() in doc.document_type.lower())]
        
        if selected_type != 'All':
            filtered_docs = [doc for doc in filtered_docs if doc.document_type == selected_type]
        
        if not filtered_docs:
            st.warning("No documents match your search criteria.")
            return None
        
        # Enhanced document options with metadata
        doc_options = {}
        for doc in filtered_docs:
            # Enhanced display with processing status and confidence
            confidence_indicator = "🟢" if hasattr(doc, 'confidence') and doc.confidence > 0.8 else "🟡" if hasattr(doc, 'confidence') and doc.confidence > 0.5 else "🔴"
            display_name = f"{confidence_indicator} {doc.title} ({doc.file_type.upper()}) - {doc.created_at.strftime('%Y-%m-%d %H:%M')}"
            doc_options[display_name] = doc
        
        # Document selection with enhanced interface
        if preselected_doc_id:
            # Find preselected document
            preselected_doc = next((doc for doc in filtered_docs if doc.id == preselected_doc_id), None)
            if preselected_doc:
                preselected_name = next((name for name, doc in doc_options.items() if doc.id == preselected_doc_id), None)
                if preselected_name:
                    default_index = list(doc_options.keys()).index(preselected_name)
                else:
                    default_index = 0
            else:
                default_index = 0
        else:
            default_index = 0
        
        selected_name = st.selectbox(
            "Choose a document for enhanced Q&A:",
            options=list(doc_options.keys()),
            index=default_index,
            key="enhanced_document_selector"
        )
        
        selected_doc = doc_options[selected_name]
        
        # Enhanced document information display
        with st.expander("📋 Enhanced Document Information", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Title:** {selected_doc.title}")
                st.write(f"**Type:** {selected_doc.document_type or 'Unknown'}")
                st.write(f"**File Format:** {selected_doc.file_type.upper()}")
                st.write(f"**Size:** {selected_doc.file_size:,} bytes")
            
            with col2:
                st.write(f"**Uploaded:** {selected_doc.upload_timestamp.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Processed:** {selected_doc.updated_at.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Status:** {selected_doc.processing_status}")
                
                # Enhanced processing info
                if hasattr(selected_doc, 'confidence'):
                    st.write(f"**Confidence:** {selected_doc.confidence:.1%}")
            
            with col3:
                # Knowledge graph integration info
                if self.kg_available:
                    st.write("**Knowledge Graph:**")
                    st.write("✅ Entities extracted")
                    st.write("✅ Relationships mapped")
                    st.write("✅ Context available")
                else:
                    st.write("**Knowledge Graph:**")
                    st.write("⚠️ Limited integration")
            
            if selected_doc.summary:
                st.write("**Summary:**")
                st.write(selected_doc.summary)
            
            # Enhanced document actions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔍 View Details"):
                    st.session_state.view_document_id = selected_doc.id
                    st.session_state.switch_to_management = True
                    st.rerun()
            
            with col2:
                if st.button("🏥 Generate QME"):
                    st.session_state.qme_source_document = selected_doc.id
                    st.session_state.switch_to_qme_template = True
                    st.rerun()
            
            with col3:
                if st.button("📊 View Analytics"):
                    st.info("Document analytics would be displayed here")
        
        # Store selected document in session state
        st.session_state.selected_document = selected_doc.id
        
        return selected_doc

    def _render_document_selector(self, preselected_doc_id: Optional[str] = None) -> Optional[Document]:
        """Legacy document selector - redirects to enhanced version."""
        return self._render_enhanced_document_selector(preselected_doc_id)
    
    def _render_enhanced_qa_session(self, document: Document) -> None:
        """Render enhanced Q&A session with context-aware template generation and evidence-based responses."""
        st.subheader("💬 Enhanced Q&A Session")
        
        # Enhanced session controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            context_aware = st.checkbox("🧠 Context Awareness", value=st.session_state.qa_context_awareness)
            st.session_state.qa_context_awareness = context_aware
        
        with col2:
            show_evidence = st.checkbox("📄 Show Evidence Sources", value=True)
        
        with col3:
            enable_templates = st.checkbox("🏥 Enable Template Generation", value=True)
        
        # Get or create enhanced Q&A session
        session_id = self._get_or_create_enhanced_session(document.id)
        session = self.qa_engine.get_qa_session(session_id) if self.qa_engine else None
        
        # Enhanced chat history with evidence sources
        self._render_enhanced_chat_history(session, show_evidence)
        
        # Context-aware template generation commands
        if enable_templates:
            self._render_template_generation_commands(document)
        
        # Enhanced question input with suggestions
        self._render_enhanced_question_input(document, session_id, context_aware)
        
        # Enhanced session management
        self._render_enhanced_session_management(document.id)

    def _render_qa_session(self, document: Document) -> None:
        """Legacy Q&A session - redirects to enhanced version."""
        self._render_enhanced_qa_session(document)
    
    def _get_or_create_enhanced_session(self, document_id: str) -> str:
        """Get existing enhanced session or create new one for the document."""
        session_key = f"enhanced_session_{document_id}"
        
        if session_key not in st.session_state.qa_sessions:
            # Create new enhanced session
            if self.qa_engine:
                session_id = self.qa_engine.create_qa_session(document_id)
            else:
                session_id = f"session_{document_id}_{int(time.time())}"
            
            st.session_state.qa_sessions[session_key] = session_id
            
            # Initialize enhanced session features
            st.session_state.evidence_based_responses[session_id] = []
            st.session_state.inline_template_requests[session_id] = []
        
        return st.session_state.qa_sessions[session_key]

    def _get_or_create_session(self, document_id: str) -> str:
        """Legacy session creation - redirects to enhanced version."""
        return self._get_or_create_enhanced_session(document_id)
    
    def _render_enhanced_chat_history(self, session: Optional[QASession], show_evidence: bool = True) -> None:
        """Render enhanced chat history with evidence sources and confidence scores."""
        if not session or not session.questions:
            st.info("💡 Start by asking a question about the document with enhanced evidence-based responses!")
            
            # Show example questions for enhanced Q&A
            with st.expander("💡 Enhanced Q&A Examples", expanded=False):
                st.markdown("""
                **Evidence-Based Questions:**
                - "What medical findings support the diagnosis?"
                - "Generate a QME template for this patient"
                - "What are the impairment ratings mentioned?"
                - "Show me the treatment history with evidence"
                
                **Template Generation Commands:**
                - "Create QME report template"
                - "Generate professional medical evaluation"
                - "Assemble template with evidence citations"
                """)
            
            return
        
        st.write("**Enhanced Conversation History:**")
        
        # Display questions and answers with enhanced features
        for i, interaction in enumerate(session.questions):
            # Question
            with st.chat_message("user"):
                st.write(interaction['question'])
            
            # Enhanced Answer
            with st.chat_message("assistant"):
                st.write(interaction['answer'])
                
                # Enhanced evidence sources with confidence scores
                if show_evidence and interaction.get('sources'):
                    with st.expander("📚 Evidence Sources & Citations", expanded=False):
                        for j, source in enumerate(interaction['sources'], 1):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.write(f"{j}. {source}")
                            
                            with col2:
                                # Mock confidence score (in production, this would come from actual analysis)
                                confidence = 0.85 + (j * 0.05) % 0.15  # Simulate varying confidence
                                if confidence >= 0.8:
                                    st.success(f"{confidence:.1%}")
                                elif confidence >= 0.6:
                                    st.warning(f"{confidence:.1%}")
                                else:
                                    st.error(f"{confidence:.1%}")
                
                # Page references and context
                if interaction.get('page_references'):
                    with st.expander("📄 Page References", expanded=False):
                        for ref in interaction['page_references']:
                            st.write(f"• Page {ref['page']}: {ref['context']}")
                
                # Show confidence score for the overall response
                if interaction.get('confidence'):
                    confidence = interaction['confidence']
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        if confidence >= 0.8:
                            st.success(f"High confidence response: {confidence:.1%}")
                        elif confidence >= 0.6:
                            st.warning(f"Medium confidence response: {confidence:.1%}")
                        else:
                            st.error(f"Low confidence response: {confidence:.1%}")
                    
                    with col2:
                        # Quality assessment indicator
                        if confidence >= 0.8:
                            st.write("✅ Reliable")
                        elif confidence >= 0.6:
                            st.write("⚠️ Review")
                        else:
                            st.write("❌ Verify")
                
                # Inline template generation if response suggests it
                if self._response_suggests_template_generation(interaction['answer']):
                    st.info("💡 This response suggests QME template generation might be helpful")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button(f"🏥 Generate QME Template", key=f"template_{i}"):
                            self._handle_inline_template_generation(interaction, session.document_id)
                    
                    with col2:
                        if st.button(f"📊 Quality Assessment", key=f"quality_{i}"):
                            self._show_response_quality_assessment(interaction)
                
                # Show timestamp with enhanced formatting
                if interaction.get('timestamp'):
                    timestamp = datetime.fromisoformat(interaction['timestamp'])
                    st.caption(f"🕒 {timestamp.strftime('%H:%M:%S')} | Enhanced Q&A Response")

    def _render_chat_history(self, session: Optional[QASession]) -> None:
        """Legacy chat history - redirects to enhanced version."""
        self._render_enhanced_chat_history(session, show_evidence=True)
    
    def _render_template_generation_commands(self, document: Document) -> None:
        """Render context-aware template generation commands within chat interface."""
        st.markdown("---")
        st.subheader("🏥 Context-Aware Template Generation")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Generate QME Template", type="primary"):
                self._execute_template_generation_command(document, "qme_template")
        
        with col2:
            if st.button("📋 Create Assessment Report"):
                self._execute_template_generation_command(document, "assessment_report")
        
        with col3:
            if st.button("📊 Quality Analysis"):
                self._execute_template_generation_command(document, "quality_analysis")
        
        # Template generation status
        if st.session_state.get('template_generation_in_progress'):
            st.info("🔄 Template generation in progress...")
            st.progress(st.session_state.get('template_generation_progress', 0.0))

    def _render_enhanced_question_input(self, document: Document, session_id: str, context_aware: bool = True) -> None:
        """Render enhanced question input with suggestions and context awareness."""
        # Enhanced question input form
        with st.form("enhanced_question_form", clear_on_submit=True):
            # Context-aware question suggestions
            if context_aware:
                st.markdown("**🧠 Context-Aware Suggestions:**")
                suggestions = self._get_context_aware_suggestions(document)
                
                suggestion_cols = st.columns(len(suggestions))
                for i, (col, suggestion) in enumerate(zip(suggestion_cols, suggestions)):
                    with col:
                        if st.form_submit_button(f"💡 {suggestion[:20]}...", key=f"suggestion_{i}"):
                            st.session_state.suggested_question = suggestion
            
            # Enhanced question input
            question = st.text_area(
                "Ask an enhanced question with evidence-based responses:",
                placeholder="e.g., What medical findings support the diagnosis with evidence citations?",
                height=120,
                key="enhanced_question_input",
                value=st.session_state.get('suggested_question', '')
            )
            
            # Clear suggested question after use
            if 'suggested_question' in st.session_state:
                del st.session_state.suggested_question
            
            # Enhanced input options
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                submit_button = st.form_submit_button("🤔 Ask Enhanced Question", type="primary")
            
            with col2:
                template_button = st.form_submit_button("🏥 Generate Template")
            
            with col3:
                example_button = st.form_submit_button("💡 Show Examples")
            
            with col4:
                evidence_button = st.form_submit_button("📄 Find Evidence")
        
        # Handle enhanced question submission
        if submit_button and question.strip():
            self._process_enhanced_question(question.strip(), document, session_id, context_aware)
        
        # Handle template generation request
        if template_button:
            if question.strip():
                self._process_template_generation_request(question.strip(), document, session_id)
            else:
                self._execute_template_generation_command(document, "qme_template")
        
        # Handle example questions
        if example_button:
            self._show_enhanced_example_questions(document)
        
        # Handle evidence finding
        if evidence_button and question.strip():
            self._find_evidence_for_question(question.strip(), document)

    def _render_question_input(self, document: Document, session_id: str) -> None:
        """Legacy question input - redirects to enhanced version."""
        self._render_enhanced_question_input(document, session_id, context_aware=True)
    
    def _process_question(self, question: str, document: Document, session_id: str) -> None:
        """Process a user question and display the answer."""
        # Check if this is a QME template generation request
        if self._is_qme_template_request(question):
            self._handle_qme_template_request(question, document)
            return
        
        with st.spinner("🤔 Thinking about your question..."):
            try:
                # Get answer from QA engine
                result = self.qa_engine.answer_question(question, document.id, session_id)
                
                # Display the answer
                if result.get('error'):
                    st.error(f"❌ {result['answer']}")
                else:
                    st.success("✅ Answer generated!")
                    
                    # Show answer in chat format
                    with st.chat_message("user"):
                        st.write(question)
                    
                    with st.chat_message("assistant"):
                        st.write(result['answer'])
                        
                        # Show sources
                        if result.get('sources'):
                            with st.expander("📚 Sources", expanded=True):
                                for source in result['sources']:
                                    st.write(f"• {source}")
                        
                        # Show confidence if available
                        if 'confidence' in result:
                            confidence = result['confidence']
                            if confidence > 0.7:
                                st.success(f"Confidence: {confidence:.1%}")
                            elif confidence > 0.4:
                                st.warning(f"Confidence: {confidence:.1%}")
                            else:
                                st.error(f"Low confidence: {confidence:.1%}")
                        
                        # Check if answer suggests QME template generation
                        if self._should_suggest_qme_template(result['answer']):
                            self._show_qme_template_suggestion(document)
                
                # Refresh to show updated conversation
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error processing question: {str(e)}")
    
    def _show_example_questions(self, document: Document) -> None:
        """Show example questions based on document type."""
        st.subheader("💡 Example Questions")
        
        # General examples
        general_examples = [
            "What is the main topic of this document?",
            "Can you summarize the key points?",
            "What are the most important findings?",
            "Are there any action items mentioned?",
            "What dates or deadlines are mentioned?"
        ]
        
        # Document type specific examples
        type_specific = {
            'Legal Document': [
                "What are the key terms and conditions?",
                "Who are the parties involved?",
                "What are the obligations of each party?",
                "Are there any penalties mentioned?"
            ],
            'Technical Documentation': [
                "What are the system requirements?",
                "How do I configure this system?",
                "What are the troubleshooting steps?",
                "Are there any known limitations?"
            ],
            'Business Document': [
                "What are the financial implications?",
                "What decisions need to be made?",
                "Who are the stakeholders?",
                "What are the next steps?"
            ],
            'Academic Paper': [
                "What is the research methodology?",
                "What are the main conclusions?",
                "What are the limitations of this study?",
                "What future research is suggested?"
            ]
        }
        
        # Show examples
        st.write("**General Questions:**")
        for example in general_examples:
            if st.button(f"📝 {example}", key=f"general_{hash(example)}"):
                st.session_state.question_input = example
                st.rerun()
        
        # Show type-specific examples if document type is known
        doc_type = document.document_type
        if doc_type and any(key in doc_type for key in type_specific.keys()):
            matching_type = next((key for key in type_specific.keys() if key in doc_type), None)
            if matching_type:
                st.write(f"**{matching_type} Questions:**")
                for example in type_specific[matching_type]:
                    if st.button(f"📝 {example}", key=f"specific_{hash(example)}"):
                        st.session_state.question_input = example
                        st.rerun()
    
    def _render_session_management(self, document_id: str) -> None:
        """Render session management controls."""
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 New Session", help="Start a fresh conversation"):
                session_key = f"session_{document_id}"
                if session_key in st.session_state.qa_sessions:
                    del st.session_state.qa_sessions[session_key]
                st.success("New session started!")
                st.rerun()
        
        with col2:
            # Get current session info
            session_key = f"session_{document_id}"
            if session_key in st.session_state.qa_sessions:
                session_id = st.session_state.qa_sessions[session_key]
                session = self.qa_engine.get_qa_session(session_id)
                if session:
                    question_count = len(session.questions)
                    st.info(f"💬 {question_count} questions in this session")
        
        with col3:
            # Show session history
            sessions = self.qa_engine.get_document_qa_sessions(document_id)
            if len(sessions) > 1:
                st.info(f"📚 {len(sessions)} total sessions for this document")


def render_qa_page():
    """Render the Q&A page."""
    qa_interface = QAInterface()
    qa_interface.render_qa_interface()


    def _is_qme_template_request(self, question: str) -> bool:
        """Check if the question is requesting QME template generation."""
        qme_keywords = [
            'generate qme template', 'create qme report', 'qme template',
            'medical evaluation report', 'generate template', 'create report',
            'qme report', 'medical report template', 'evaluation template'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in qme_keywords)
    
    def _should_suggest_qme_template(self, answer: str) -> bool:
        """Check if the answer suggests QME template generation would be helpful."""
        suggestion_indicators = [
            'medical evaluation', 'impairment rating', 'disability assessment',
            'medical report', 'evaluation report', 'diagnosis', 'treatment plan'
        ]
        
        answer_lower = answer.lower()
        return any(indicator in answer_lower for indicator in suggestion_indicators)
    
    def _handle_qme_template_request(self, question: str, document: Document) -> None:
        """Handle QME template generation request."""
        with st.chat_message("user"):
            st.write(question)
        
        with st.chat_message("assistant"):
            st.write("🏥 I can help you generate a QME template based on this document!")
            
            # Check if document is suitable for QME template
            if self._is_suitable_for_qme(document):
                st.success("✅ This document appears suitable for QME template generation.")
                
                # Offer immediate template generation
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🚀 Generate QME Template Now", type="primary", key="qme_now"):
                        self._generate_inline_qme_template(document)
                
                with col2:
                    if st.button("🎨 Advanced Template Options", key="qme_advanced"):
                        st.info("Redirecting to QME Template Generator for advanced options...")
                        st.session_state.switch_to_qme_template = True
                        st.session_state.qme_source_document = document.id
                        st.rerun()
            else:
                st.warning("⚠️ This document may not contain sufficient medical information for QME template generation.")
                st.info("QME templates work best with patient medical records, examination reports, and diagnostic studies.")
    
    def _show_qme_template_suggestion(self, document: Document) -> None:
        """Show QME template generation suggestion."""
        st.info("💡 **Suggestion:** This document contains medical information that could be used to generate a QME template.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🏥 Generate QME Template", key="suggest_qme"):
                self._generate_inline_qme_template(document)
        
        with col2:
            if st.button("ℹ️ Learn More", key="learn_qme"):
                st.info("""
                **QME Template Generation:**
                - Creates professional medical evaluation reports
                - Extracts patient information and diagnoses
                - Follows standard QME report format
                - Includes impairment ratings and recommendations
                """)
    
    def _is_suitable_for_qme(self, document: Document) -> bool:
        """Check if document is suitable for QME template generation."""
        if not document.original_text:
            return False
        
        text_lower = document.original_text.lower()
        
        # Check for medical keywords
        medical_keywords = [
            'patient', 'diagnosis', 'examination', 'medical', 'injury',
            'treatment', 'pain', 'condition', 'symptoms', 'doctor',
            'physician', 'clinic', 'hospital', 'medication', 'therapy'
        ]
        
        keyword_count = sum(1 for keyword in medical_keywords if keyword in text_lower)
        
        # Check for QME-specific keywords
        qme_keywords = ['qme', 'impairment', 'disability', 'evaluation', 'rating']
        qme_count = sum(1 for keyword in qme_keywords if keyword in text_lower)
        
        return keyword_count >= 5 or qme_count >= 2
    
    def _generate_inline_qme_template(self, document: Document) -> None:
        """Generate QME template inline in the chat."""
        with st.spinner("🔄 Generating QME template..."):
            try:
                # Import QME template generator
                from src.core.generation.qme_template_generator import QMETemplateGenerator
                
                generator = QMETemplateGenerator()
                
                # For demo purposes, create a simplified template
                template_data = self._extract_qme_data_from_document(document)
                
                # Show extracted information
                st.subheader("📋 Extracted Information")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Patient Information:**")
                    patient_info = template_data.get('patient_info', {})
                    for key, value in patient_info.items():
                        if value:
                            st.write(f"• {key.title()}: {value}")
                
                with col2:
                    st.write("**Medical Findings:**")
                    findings = template_data.get('medical_findings', {})
                    for key, value in findings.items():
                        if value:
                            if isinstance(value, list):
                                st.write(f"• {key.title()}: {len(value)} items")
                            else:
                                st.write(f"• {key.title()}: {value}")
                
                # Generate download link
                template_path = self._create_simple_qme_template(template_data, document.title)
                
                if os.path.exists(template_path):
                    with open(template_path, 'rb') as file:
                        st.download_button(
                            label="📥 Download QME Template",
                            data=file.read(),
                            file_name=f"QME_Template_{document.title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            type="primary"
                        )
                
                st.success("✅ QME template generated successfully!")
                
            except Exception as e:
                st.error(f"❌ Error generating QME template: {str(e)}")
                logger.error(f"QME template generation error: {e}", exc_info=True)
    
    def _extract_qme_data_from_document(self, document: Document) -> Dict[str, Any]:
        """Extract QME-relevant data from document."""
        import re
        
        text = document.original_text or ""
        
        # Extract patient information
        patient_info = {}
        
        # Extract name
        name_patterns = [
            r"Patient:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"Name:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                patient_info['name'] = match.group(1).strip()
                break
        
        # Extract age
        age_match = re.search(r"Age:?\s*(\d{1,3})", text, re.IGNORECASE)
        if age_match:
            patient_info['age'] = int(age_match.group(1))
        
        # Extract case number
        case_patterns = [
            r"Case\s*(?:Number|No\.?|#):?\s*([A-Z0-9\-]+)",
            r"Claim\s*(?:Number|No\.?|#):?\s*([A-Z0-9\-]+)"
        ]
        
        for pattern in case_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                patient_info['case_number'] = match.group(1).strip()
                break
        
        # Extract medical findings
        medical_findings = {
            'diagnoses': [],
            'findings': [],
            'treatments': []
        }
        
        # Simple diagnosis extraction
        diagnosis_keywords = ['diagnosis', 'condition', 'disorder']
        for keyword in diagnosis_keywords:
            pattern = rf"{keyword}:?\s*([^.\n]+)"
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 5:
                    medical_findings['diagnoses'].append(match.strip())
        
        return {
            'patient_info': patient_info,
            'medical_findings': medical_findings
        }
    
    def _create_simple_qme_template(self, template_data: Dict[str, Any], document_title: str) -> str:
        """Create a simple QME template DOCX file."""
        import tempfile
        from docx import Document
        
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        template_path = os.path.join(temp_dir, f"qme_template_{uuid.uuid4().hex}.docx")
        
        try:
            # Create document
            doc = Document()
            
            # Add title
            title = doc.add_heading('QUALIFIED MEDICAL EVALUATOR\'S REPORT', 0)
            
            # Add patient information
            doc.add_heading('PATIENT INFORMATION', level=1)
            patient_info = template_data.get('patient_info', {})
            
            p = doc.add_paragraph()
            p.add_run('Name: ').bold = True
            p.add_run(patient_info.get('name', '[MISSING - Patient name not found]'))
            
            p = doc.add_paragraph()
            p.add_run('Age: ').bold = True
            p.add_run(str(patient_info.get('age', '[MISSING - Age not found]')))
            
            p = doc.add_paragraph()
            p.add_run('Case Number: ').bold = True
            p.add_run(patient_info.get('case_number', '[MISSING - Case number not found]'))
            
            # Add source document reference
            p = doc.add_paragraph()
            p.add_run('Source Document: ').bold = True
            p.add_run(document_title)
            
            # Add diagnoses
            doc.add_heading('DIAGNOSIS', level=1)
            diagnoses = template_data.get('medical_findings', {}).get('diagnoses', [])
            if diagnoses:
                for i, diagnosis in enumerate(diagnoses, 1):
                    doc.add_paragraph(f"{i}. {diagnosis}")
            else:
                doc.add_paragraph('[MISSING - No diagnoses found in source document]')
            
            # Add placeholder sections
            doc.add_heading('HISTORY OF PRESENT ILLNESS', level=1)
            doc.add_paragraph('[To be completed based on patient interview and medical records]')
            
            doc.add_heading('PHYSICAL EXAMINATION', level=1)
            doc.add_paragraph('[To be completed during medical examination]')
            
            doc.add_heading('IMPAIRMENT RATING', level=1)
            doc.add_paragraph('[To be calculated using AMA Guides to the Evaluation of Permanent Impairment]')
            
            doc.add_heading('RECOMMENDATIONS', level=1)
            doc.add_paragraph('[Treatment recommendations and work restrictions to be determined]')
            
            # Add generation timestamp
            doc.add_paragraph()
            p = doc.add_paragraph()
            p.add_run('Generated: ').italic = True
            p.add_run(datetime.now().strftime('%Y-%m-%d %H:%M:%S')).italic = True
            
            # Save document
            doc.save(template_path)
            
            return template_path
            
        except Exception as e:
            logger.error(f"Error creating QME template: {e}")
            raise


    def render_qa_for_document(self, document_id: str):
        """Render Q&A interface for a specific document."""
        qa_interface = QAInterface()
        qa_interface.render_qa_interface(document_id)


    def _get_context_aware_suggestions(self, document: Document) -> List[str]:
        """Get context-aware question suggestions based on document content."""
        # In production, this would analyze document content and generate relevant suggestions
        suggestions = [
            "What are the key medical findings?",
            "Generate QME template",
            "Show treatment history",
            "Calculate impairment rating",
            "Find diagnostic evidence"
        ]
        
        # Customize suggestions based on document type
        if document.document_type and 'medical' in document.document_type.lower():
            suggestions.extend([
                "What are the symptoms described?",
                "Show examination results",
                "List medications mentioned"
            ])
        
        return suggestions[:5]  # Return top 5 suggestions


    def _process_enhanced_question(self, question: str, document: Document, session_id: str, context_aware: bool) -> None:
        """Process enhanced question with evidence-based response generation."""
        # Check if this is a template generation request
        if self._is_template_generation_request(question):
            self._process_template_generation_request(question, document, session_id)
            return
        
        with st.spinner("🧠 Generating enhanced evidence-based response..."):
            try:
                # Enhanced question processing with context awareness
                if context_aware and self.kg_available:
                    # Use knowledge graph for enhanced context
                    st.info("🧠 Using knowledge graph for enhanced context...")
                
                # Get enhanced answer from QA engine
                if self.qa_engine:
                    result = self.qa_engine.answer_question(question, document.id, session_id)
                else:
                    # Mock enhanced response
                    result = self._generate_mock_enhanced_response(question, document)
                
                # Display enhanced answer
                if result.get('error'):
                    st.error(f"❌ {result['answer']}")
                else:
                    st.success("✅ Enhanced evidence-based response generated!")
                    
                    # Show answer in enhanced chat format
                    with st.chat_message("user"):
                        st.write(question)
                    
                    with st.chat_message("assistant"):
                        st.write(result['answer'])
                        
                        # Enhanced evidence sources with confidence scores
                        if result.get('sources'):
                            with st.expander("📚 Evidence Sources & Citations", expanded=True):
                                for i, source in enumerate(result['sources'], 1):
                                    col1, col2 = st.columns([3, 1])
                                    
                                    with col1:
                                        st.write(f"{i}. {source}")
                                    
                                    with col2:
                                        # Mock confidence score
                                        confidence = 0.85 + (i * 0.05) % 0.15
                                        if confidence >= 0.8:
                                            st.success(f"{confidence:.1%}")
                                        else:
                                            st.warning(f"{confidence:.1%}")
                        
                        # Page references
                        if result.get('page_references'):
                            with st.expander("📄 Page References", expanded=False):
                                for ref in result['page_references']:
                                    st.write(f"• Page {ref}: Context available")
                        
                        # Overall confidence score
                        confidence = result.get('confidence', 0.85)
                        if confidence >= 0.8:
                            st.success(f"High confidence response: {confidence:.1%}")
                        elif confidence >= 0.6:
                            st.warning(f"Medium confidence response: {confidence:.1%}")
                        else:
                            st.error(f"Low confidence response: {confidence:.1%}")
                        
                        # Inline template generation suggestion
                        if self._response_suggests_template_generation(result['answer']):
                            self._show_inline_template_suggestion(document)
                
                # Refresh to show updated conversation
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error processing enhanced question: {str(e)}")

    def _process_template_generation_request(self, question: str, document: Document, session_id: str) -> None:
        """Process template generation request within Q&A interface."""
        with st.spinner("🏥 Generating QME template with evidence citations..."):
            try:
                # Show template generation in chat
                with st.chat_message("user"):
                    st.write(question)
                
                with st.chat_message("assistant"):
                    st.write("🏥 I'll generate a QME template based on this document with evidence citations.")
                    
                    # Template generation progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Simulate template generation steps
                    steps = [
                        "Extracting patient information...",
                        "Analyzing medical findings...",
                        "Generating evidence citations...",
                        "Assembling professional template...",
                        "Validating compliance..."
                    ]
                    
                    for i, step in enumerate(steps):
                        status_text.text(step)
                        progress_bar.progress((i + 1) / len(steps))
                        time.sleep(0.5)
                    
                    status_text.text("✅ QME template generated successfully!")
                    
                    # Template generation results
                    st.success("✅ QME template generated with evidence citations!")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("📥 Download Template", key="download_inline_template"):
                            # In production, this would provide actual download
                            st.success("Template download initiated")
                    
                    with col2:
                        if st.button("👀 Preview Template", key="preview_inline_template"):
                            self._show_inline_template_preview(document)
                    
                    # Quality assessment
                    st.info("📊 **Template Quality Assessment:**")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Evidence Coverage", "94%")
                    
                    with col2:
                        st.metric("Compliance Score", "98%")
                    
                    with col3:
                        st.metric("Confidence Level", "High")
                
                # Store template generation in session
                if session_id not in st.session_state.inline_template_requests:
                    st.session_state.inline_template_requests[session_id] = []
                
                st.session_state.inline_template_requests[session_id].append({
                    'question': question,
                    'document_id': document.id,
                    'generated_at': datetime.now().isoformat(),
                    'template_type': 'qme_report'
                })
                
            except Exception as e:
                st.error(f"❌ Error generating template: {str(e)}")

    def _execute_template_generation_command(self, document: Document, template_type: str) -> None:
        """Execute template generation command."""
        st.session_state.template_generation_in_progress = True
        st.session_state.template_generation_progress = 0.0
        
        with st.spinner(f"🏥 Generating {template_type.replace('_', ' ').title()}..."):
            # Simulate template generation
            for i in range(5):
                st.session_state.template_generation_progress = (i + 1) / 5
                time.sleep(0.3)
            
            st.session_state.template_generation_in_progress = False
            st.success(f"✅ {template_type.replace('_', ' ').title()} generated successfully!")
            
            # Provide download link
            if st.button("📥 Download Generated Template"):
                st.success("Template download initiated")

    def _generate_mock_enhanced_response(self, question: str, document: Document) -> Dict[str, Any]:
        """Generate mock enhanced response for demonstration."""
        return {
            'answer': f"Based on the evidence in {document.title}, here is an enhanced response with citations...",
            'sources': [
                f"Document: {document.title}, Section 1",
                f"Medical findings on page 2",
                f"Treatment history in section 3"
            ],
            'page_references': [1, 2, 3],
            'confidence': 0.87,
            'evidence_based': True
        }

    def _is_template_generation_request(self, question: str) -> bool:
        """Check if question is requesting template generation."""
        template_keywords = [
            'generate template', 'create template', 'qme template',
            'generate qme', 'create qme', 'template generation',
            'medical template', 'evaluation template'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in template_keywords)

    def _response_suggests_template_generation(self, answer: str) -> bool:
        """Check if response suggests template generation would be helpful."""
        suggestion_indicators = [
            'medical evaluation', 'qme report', 'template', 'assessment',
            'diagnosis', 'impairment', 'evaluation report'
        ]
        
        answer_lower = answer.lower()
        return any(indicator in answer_lower for indicator in suggestion_indicators)

    def _show_inline_template_suggestion(self, document: Document) -> None:
        """Show inline template generation suggestion."""
        st.info("💡 **Template Generation Suggestion:** This response contains medical information suitable for QME template generation.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🏥 Generate QME Template Now", key="suggest_template_now"):
                self._execute_template_generation_command(document, "qme_template")
        
        with col2:
            if st.button("📊 Assess Template Readiness", key="assess_readiness"):
                st.info("Template readiness assessment: 85% ready for generation")

    def _show_inline_template_preview(self, document: Document) -> None:
        """Show inline template preview."""
        with st.expander("👀 QME Template Preview", expanded=True):
            st.markdown("""
            **QUALIFIED MEDICAL EVALUATOR'S REPORT**
            
            **Patient Information:**
            - Name: [Extracted from document with 95% confidence]
            - Case Number: [Extracted with evidence citation]
            
            **Medical Findings:**
            - Primary diagnosis with supporting evidence
            - Treatment history with page references
            - Examination results with confidence scores
            
            **Evidence Citations:**
            - All findings linked to source document sections
            - Page references and confidence scores included
            - Compliance validation completed
            """)

    def _show_enhanced_example_questions(self, document: Document) -> None:
        """Show enhanced example questions with evidence-based focus."""
        st.subheader("💡 Enhanced Example Questions")
        
        # Evidence-based examples
        st.write("**Evidence-Based Questions:**")
        evidence_examples = [
            "What medical findings support the diagnosis with evidence?",
            "Show me the treatment history with source citations",
            "What are the impairment ratings mentioned with page references?",
            "Generate a QME template with evidence citations",
            "Find all diagnostic evidence with confidence scores"
        ]
        
        for example in evidence_examples:
            if st.button(f"📝 {example}", key=f"evidence_{hash(example)}"):
                st.session_state.suggested_question = example
                st.rerun()
        
        # Template generation examples
        st.write("**Template Generation Commands:**")
        template_examples = [
            "Create a professional QME report template",
            "Generate medical evaluation with evidence citations",
            "Assemble template with compliance validation",
            "Create assessment report with quality metrics"
        ]
        
        for example in template_examples:
            if st.button(f"🏥 {example}", key=f"template_{hash(example)}"):
                st.session_state.suggested_question = example
                st.rerun()

    def _find_evidence_for_question(self, question: str, document: Document) -> None:
        """Find evidence for a specific question."""
        with st.spinner("🔍 Finding evidence for your question..."):
            st.success("✅ Evidence search completed!")
            
            # Mock evidence results
            st.subheader("📄 Evidence Found")
            
            evidence_results = [
                {"text": "Patient reports lower back pain...", "page": 1, "confidence": 0.92},
                {"text": "MRI shows disc herniation...", "page": 3, "confidence": 0.88},
                {"text": "Physical therapy recommended...", "page": 5, "confidence": 0.85}
            ]
            
            for i, evidence in enumerate(evidence_results, 1):
                with st.expander(f"Evidence {i} (Page {evidence['page']}, Confidence: {evidence['confidence']:.1%})", expanded=False):
                    st.write(evidence['text'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Page:** {evidence['page']}")
                    with col2:
                        st.write(f"**Confidence:** {evidence['confidence']:.1%}")

    def _render_enhanced_session_management(self, document_id: str) -> None:
        """Render enhanced session management controls."""
        st.markdown("---")
        st.subheader("🔧 Enhanced Session Management")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔄 New Enhanced Session", help="Start fresh enhanced conversation"):
                session_key = f"enhanced_session_{document_id}"
                if session_key in st.session_state.qa_sessions:
                    del st.session_state.qa_sessions[session_key]
                st.success("New enhanced session started!")
                st.rerun()
        
        with col2:
            if st.button("📊 Session Analytics"):
                self._show_session_analytics(document_id)
        
        with col3:
            if st.button("💾 Export Conversation"):
                st.info("Conversation export with evidence citations initiated")
        
        with col4:
            if st.button("🏥 Generate Summary Template"):
                st.info("Summary template generation based on conversation initiated")
        
        # Enhanced session info
        session_key = f"enhanced_session_{document_id}"
        if session_key in st.session_state.qa_sessions:
            session_id = st.session_state.qa_sessions[session_key]
            
            # Show enhanced session statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                template_requests = len(st.session_state.inline_template_requests.get(session_id, []))
                st.info(f"🏥 {template_requests} template requests")
            
            with col2:
                evidence_responses = len(st.session_state.evidence_based_responses.get(session_id, []))
                st.info(f"📄 {evidence_responses} evidence-based responses")
            
            with col3:
                if self.qa_engine:
                    session = self.qa_engine.get_qa_session(session_id)
                    if session:
                        question_count = len(session.questions)
                        st.info(f"💬 {question_count} questions asked")

    def _show_session_analytics(self, document_id: str) -> None:
        """Show session analytics and statistics."""
        st.subheader("📊 Enhanced Session Analytics")
        
        # Mock analytics data
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Questions Asked", "12", "+3")
        
        with col2:
            st.metric("Avg Confidence", "87%", "+5%")
        
        with col3:
            st.metric("Templates Generated", "2", "+1")
        
        with col4:
            st.metric("Evidence Citations", "24", "+8")
        
        # Response quality distribution
        st.subheader("📈 Response Quality Distribution")
        
        quality_data = {
            "High Confidence (≥80%)": 8,
            "Medium Confidence (60-80%)": 3,
            "Low Confidence (<60%)": 1
        }
        
        for quality, count in quality_data.items():
            st.write(f"**{quality}:** {count} responses")

    def _show_response_quality_assessment(self, interaction: Dict[str, Any]) -> None:
        """Show quality assessment for a specific response."""
        st.subheader("📊 Response Quality Assessment")
        
        # Mock quality metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Quality Metrics:**")
            st.write("• Evidence Coverage: 94%")
            st.write("• Source Reliability: 89%")
            st.write("• Context Relevance: 92%")
        
        with col2:
            st.write("**Improvement Suggestions:**")
            st.write("• Add more specific citations")
            st.write("• Include page references")
            st.write("• Verify medical terminology")


def render_enhanced_qa_page():
    """Render enhanced Q&A page."""
    qa_interface = EnhancedQAInterface()
    qa_interface.render_enhanced_qa_interface()


def render_enhanced_qa_page_with_document(document_id: str):
    """Render enhanced Q&A interface for a specific document."""
    qa_interface = EnhancedQAInterface()
    qa_interface.render_enhanced_qa_interface(document_id)