"""Q&A Interface for document question answering with chat-like interaction."""

import streamlit as st
import uuid
import os
import tempfile
from datetime import datetime
from typing import Optional, List, Dict, Any

from src.services.qa_engine import QAEngine, create_qa_engine
from src.storage.document_storage import DocumentStorage
from src.models.document import Document, QASession
from src.config.app_config import app_config
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class QAInterface:
    """Streamlit interface for document Q&A functionality."""
    
    def __init__(self):
        self.storage = DocumentStorage()
        self.qa_engine = None
        
        # Initialize session state
        if 'qa_sessions' not in st.session_state:
            st.session_state.qa_sessions = {}
        if 'current_qa_session' not in st.session_state:
            st.session_state.current_qa_session = None
        if 'selected_document' not in st.session_state:
            st.session_state.selected_document = None
    
    def render_qa_interface(self, document_id: Optional[str] = None) -> None:
        """
        Render the main Q&A interface.
        
        Args:
            document_id: Optional document ID to start Q&A with
        """
        # Get API key
        api_key = app_config.get_api_key_for_provider(app_config.qa_provider)
        if not api_key:
            st.error("⚠️ Gemini API key not configured. Please set GEMINI_API_KEY in your environment.")
            st.info("You can get an API key from: https://makersuite.google.com/app/apikey")
            return
        
        # Initialize QA engine
        if not self.qa_engine:
            try:
                # Use the hybrid QA engine factory with API key
                from src.services.qa_engine import create_hybrid_qa_engine
                self.qa_engine = create_hybrid_qa_engine(api_key, self.storage)
            except Exception as e:
                st.error(f"Failed to initialize QA engine: {str(e)}")
                return
        
        # Document selection section
        selected_doc = self._render_document_selector(document_id)
        
        if not selected_doc:
            st.info("👆 Please select a document to start asking questions.")
            return
        
        # Q&A session section
        self._render_qa_session(selected_doc)
    
    def _render_document_selector(self, preselected_doc_id: Optional[str] = None) -> Optional[Document]:
        """Render document selection interface."""
        st.subheader("📄 Select Document")
        
        # Get processed documents
        processed_docs = self.storage.list_documents(status_filter='completed')
        
        if not processed_docs:
            st.warning("No processed documents available. Please upload and process documents first.")
            return None
        
        # Create document options
        doc_options = {}
        for doc in processed_docs:
            display_name = f"{doc.title} ({doc.file_type.upper()}) - {doc.created_at.strftime('%Y-%m-%d %H:%M')}"
            doc_options[display_name] = doc
        
        # Document selection
        if preselected_doc_id:
            # Find preselected document
            preselected_doc = next((doc for doc in processed_docs if doc.id == preselected_doc_id), None)
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
            "Choose a document:",
            options=list(doc_options.keys()),
            index=default_index,
            key="document_selector"
        )
        
        selected_doc = doc_options[selected_name]
        
        # Display document info
        with st.expander("📋 Document Information", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Title:** {selected_doc.title}")
                st.write(f"**Type:** {selected_doc.document_type or 'Unknown'}")
                st.write(f"**File Format:** {selected_doc.file_type.upper()}")
                st.write(f"**Size:** {selected_doc.file_size:,} bytes")
            
            with col2:
                st.write(f"**Uploaded:** {selected_doc.upload_timestamp.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Processed:** {selected_doc.updated_at.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Status:** {selected_doc.processing_status}")
            
            if selected_doc.summary:
                st.write("**Summary:**")
                st.write(selected_doc.summary)
        
        # Store selected document in session state
        st.session_state.selected_document = selected_doc.id
        
        return selected_doc
    
    def _render_qa_session(self, document: Document) -> None:
        """Render Q&A session interface for the selected document."""
        st.subheader("💬 Ask Questions")
        
        # Get or create Q&A session
        session_id = self._get_or_create_session(document.id)
        session = self.qa_engine.get_qa_session(session_id)
        
        # Display chat history
        self._render_chat_history(session)
        
        # Question input
        self._render_question_input(document, session_id)
        
        # Session management
        self._render_session_management(document.id)
    
    def _get_or_create_session(self, document_id: str) -> str:
        """Get existing session or create new one for the document."""
        session_key = f"session_{document_id}"
        
        if session_key not in st.session_state.qa_sessions:
            # Create new session
            session_id = self.qa_engine.create_qa_session(document_id)
            st.session_state.qa_sessions[session_key] = session_id
        
        return st.session_state.qa_sessions[session_key]
    
    def _render_chat_history(self, session: Optional[QASession]) -> None:
        """Render chat history for the session."""
        if not session or not session.questions:
            st.info("💡 Start by asking a question about the document!")
            return
        
        st.write("**Conversation History:**")
        
        # Display questions and answers
        for i, interaction in enumerate(session.questions):
            # Question
            with st.chat_message("user"):
                st.write(interaction['question'])
            
            # Answer
            with st.chat_message("assistant"):
                st.write(interaction['answer'])
                
                # Show sources if available
                if interaction.get('sources'):
                    with st.expander("📚 Sources", expanded=False):
                        for source in interaction['sources']:
                            st.write(f"• {source}")
                
                # Show timestamp
                if interaction.get('timestamp'):
                    timestamp = datetime.fromisoformat(interaction['timestamp'])
                    st.caption(f"Answered at {timestamp.strftime('%H:%M:%S')}")
    
    def _render_question_input(self, document: Document, session_id: str) -> None:
        """Render question input interface."""
        # Question input form
        with st.form("question_form", clear_on_submit=True):
            question = st.text_area(
                "Ask a question about the document:",
                placeholder="e.g., What are the main points discussed in this document?",
                height=100,
                key="question_input"
            )
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                submit_button = st.form_submit_button("🤔 Ask Question", type="primary")
            
            with col2:
                example_button = st.form_submit_button("💡 Show Examples")
        
        # Handle question submission
        if submit_button and question.strip():
            self._process_question(question.strip(), document, session_id)
        
        # Handle example questions
        if example_button:
            self._show_example_questions(document)
    
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
                from src.services.qme_template_generator import QMETemplateGenerator
                
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


def render_qa_for_document(document_id: str):
    """Render Q&A interface for a specific document."""
    qa_interface = QAInterface()
    qa_interface.render_qa_interface(document_id)