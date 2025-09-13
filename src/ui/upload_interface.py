"""
Streamlit-based web interface for file upload and processing.
Provides user-friendly interface with real-time feedback and validation.
"""

import streamlit as st
from typing import Optional, Dict, Any
import time
from src.services.file_handler import FileUploadHandler, FileMetadata

class UploadInterface:
    """Streamlit interface for file upload and processing"""
    
    def __init__(self):
        """Initialize the upload interface"""
        self.file_handler = FileUploadHandler()
        
        # Initialize session state
        if 'uploaded_files' not in st.session_state:
            st.session_state.uploaded_files = {}
        if 'processing_status' not in st.session_state:
            st.session_state.processing_status = {}
    
    def render_upload_section(self) -> Optional[Dict[str, Any]]:
        """
        Render the file upload section with validation and feedback
        
        Returns:
            Optional[Dict[str, Any]]: File data if successfully uploaded and validated
        """
        st.header("📄 Document Upload")
        
        # Display supported formats
        st.info(
            "**Supported formats:** PDF, TXT, DOCX  \n"
            "**Maximum file size:** 10MB"
        )
        
        # File upload widget
        uploaded_file = st.file_uploader(
            "Choose a document to upload",
            type=['pdf', 'txt', 'docx'],
            help="Select a PDF, TXT, or DOCX file to process"
        )
        
        if uploaded_file is not None:
            return self._handle_file_upload(uploaded_file)
        
        return None
    
    def _handle_file_upload(self, uploaded_file) -> Optional[Dict[str, Any]]:
        """
        Handle file upload with validation and text extraction
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            Optional[Dict[str, Any]]: File data if successful
        """
        # Create columns for layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Display file information
            st.subheader("📋 File Information")
            
            # Get file metadata
            metadata = self.file_handler.get_file_metadata(uploaded_file)
            
            # Display file details
            st.write(f"**Filename:** {metadata['filename']}")
            st.write(f"**File Type:** {metadata['file_type']}")
            st.write(f"**File Size:** {metadata['file_size_mb']} MB")
        
        with col2:
            # Validation status
            if metadata['is_valid']:
                st.success("✅ File Valid")
            else:
                st.error("❌ File Invalid")
                st.error(metadata['error_message'])
                return None
        
        # Process file if valid
        if metadata['is_valid']:
            return self._process_valid_file(uploaded_file, metadata)
        
        return None
    
    def _process_valid_file(self, uploaded_file, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a valid file with text extraction and progress feedback
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            metadata: File metadata dictionary
            
        Returns:
            Optional[Dict[str, Any]]: Processed file data
        """
        st.subheader("🔄 Processing File")
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: File validation (already done)
            progress_bar.progress(25)
            status_text.text("✅ File validation complete")
            time.sleep(0.5)
            
            # Step 2: Text extraction
            progress_bar.progress(50)
            status_text.text("📖 Extracting text content...")
            
            extracted_text, error_message = self.file_handler.extract_text(uploaded_file)
            
            if error_message:
                progress_bar.progress(0)
                status_text.empty()
                st.error(f"❌ Text extraction failed: {error_message}")
                return None
            
            progress_bar.progress(75)
            status_text.text("✅ Text extraction complete")
            time.sleep(0.5)
            
            # Step 3: Process document immediately with Gemini
            progress_bar.progress(80)
            status_text.text("🤖 Processing with AI...")
            
            from src.config.app_config import app_config
            api_key = app_config.get_api_key_for_provider(app_config.qa_provider)
            
            if api_key:
                try:
                    # Use simple processor for immediate results
                    from src.services.simple_processor import SimpleDocumentProcessor
                    processor = SimpleDocumentProcessor(api_key)
                    
                    # Process document immediately
                    document = processor.process_document_immediately(
                        filename=metadata['filename'],
                        file_type=metadata['file_type'].lstrip('.'),
                        file_size=metadata['file_size'],
                        extracted_text=extracted_text
                    )
                    
                    progress_bar.progress(100)
                    status_text.text("✅ AI processing complete!")
                    
                    # Display success message based on processing status
                    if document.processing_status == 'completed':
                        st.success(f"🎉 Successfully processed '{metadata['filename']}'")
                        st.success("🤖 AI analysis complete! Your document is ready for Q&A!")
                    elif document.processing_status == 'partial':
                        st.success(f"🎉 Successfully processed '{metadata['filename']}'")
                        st.warning("⚠️ AI analysis partially completed. Some features may be limited, but Q&A is available!")
                    elif document.processing_status == 'minimal':
                        st.success(f"🎉 Successfully uploaded '{metadata['filename']}'")
                        st.info("ℹ️ AI analysis unavailable, but basic Q&A is ready!")
                    
                    # Show immediate Q&A access
                    self._display_immediate_qa_access(document.id, document.processing_status)
                    
                    # Prepare file data for return
                    file_data = {
                        'filename': metadata['filename'],
                        'file_type': metadata['file_type'],
                        'file_size': metadata['file_size'],
                        'extracted_text': extracted_text,
                        'metadata': metadata,
                        'document_id': document.id,
                        'processing_complete': True
                    }
                    
                except Exception as e:
                    progress_bar.progress(0)
                    status_text.empty()
                    st.error(f"❌ AI processing failed: {str(e)}")
                    
                    # Still show text preview for basic functionality
                    self._display_text_preview(extracted_text)
                    
                    file_data = {
                        'filename': metadata['filename'],
                        'file_type': metadata['file_type'],
                        'file_size': metadata['file_size'],
                        'extracted_text': extracted_text,
                        'metadata': metadata,
                        'processing_complete': False,
                        'error': str(e)
                    }
            else:
                progress_bar.progress(100)
                status_text.text("✅ File processing complete (AI analysis disabled)")
                st.warning("⚠️ Gemini API key not configured. Basic text extraction completed, but AI analysis and Q&A are not available.")
                
                # Show text preview
                self._display_text_preview(extracted_text)
                
                file_data = {
                    'filename': metadata['filename'],
                    'file_type': metadata['file_type'],
                    'file_size': metadata['file_size'],
                    'extracted_text': extracted_text,
                    'metadata': metadata,
                    'processing_complete': False
                }
            
            # Store in session state
            file_id = f"{metadata['filename']}_{int(time.time())}"
            st.session_state.uploaded_files[file_id] = file_data
            
            return file_data
            
        except Exception as e:
            progress_bar.progress(0)
            status_text.empty()
            st.error(f"❌ Processing failed: {str(e)}")
            return None
    
    def _display_text_preview(self, extracted_text: str):
        """
        Display a preview of the extracted text
        
        Args:
            extracted_text: The extracted text content
        """
        st.subheader("👀 Text Preview")
        
        # Show text statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Characters", len(extracted_text))
        
        with col2:
            word_count = len(extracted_text.split())
            st.metric("Words", word_count)
        
        with col3:
            line_count = len(extracted_text.split('\n'))
            st.metric("Lines", line_count)
        
        # Show text preview (first 500 characters)
        preview_text = extracted_text[:500]
        if len(extracted_text) > 500:
            preview_text += "..."
        
        st.text_area(
            "Text Content (Preview)",
            value=preview_text,
            height=200,
            disabled=True,
            help="This is a preview of the extracted text content"
        )
        
        # Option to show full text
        if st.checkbox("Show full text"):
            st.text_area(
                "Full Text Content",
                value=extracted_text,
                height=400,
                disabled=True
            )
    
    def render_upload_history(self):
        """Render the upload history section"""
        if st.session_state.uploaded_files:
            st.subheader("📚 Upload History")
            
            for file_id, file_data in st.session_state.uploaded_files.items():
                with st.expander(f"📄 {file_data['filename']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Type:** {file_data['file_type']}")
                        st.write(f"**Size:** {file_data['file_size'] / (1024*1024):.2f} MB")
                        st.write(f"**Characters:** {len(file_data['extracted_text'])}")
                    
                    with col2:
                        if st.button(f"Remove", key=f"remove_{file_id}"):
                            del st.session_state.uploaded_files[file_id]
                            st.rerun()
    
    def get_uploaded_files(self) -> Dict[str, Any]:
        """
        Get all uploaded files from session state
        
        Returns:
            Dict[str, Any]: Dictionary of uploaded files
        """
        return st.session_state.uploaded_files
    
    def clear_upload_history(self):
        """Clear all uploaded files from session state"""
        st.session_state.uploaded_files = {}
        st.session_state.processing_status = {}
    
    def _display_immediate_qa_access(self, document_id: str, processing_status: str = 'completed'):
        """Display immediate Q&A access for processed document."""
        st.markdown("---")
        st.subheader("💬 Ready for Q&A!")
        
        if processing_status == 'completed':
            st.info("Your document has been fully processed and is ready for intelligent question answering!")
        elif processing_status == 'partial':
            st.info("Your document has been processed with some limitations. Q&A is available but some AI features may be reduced.")
        elif processing_status == 'minimal':
            st.info("Your document is ready for basic Q&A! AI analysis was unavailable, but you can still ask questions about the content.")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💬 Ask Questions Now", type="primary", key=f"qa_{document_id}"):
                # Switch to Q&A interface with this document
                st.session_state.qa_document_id = document_id
                st.session_state.switch_to_qa = True
                st.rerun()
        
        with col2:
            if st.button("📄 View Document Details", key=f"details_{document_id}"):
                st.session_state.view_document_id = document_id
                st.session_state.switch_to_management = True
                st.rerun()
        
        with col3:
            if st.button("📚 All Documents", key=f"all_docs_{document_id}"):
                st.session_state.switch_to_management = True
                st.rerun()
        
        # Show quick preview of what was processed
        with st.expander("📊 Processing Results Preview", expanded=False):
            try:
                from src.storage.document_storage import DocumentStorage
                storage = DocumentStorage()
                document = storage.get_document(document_id)
                
                if document:
                    if document.document_type:
                        st.write(f"**Document Type:** {document.document_type}")
                    
                    if document.summary:
                        st.write("**Summary:**")
                        st.write(document.summary[:300] + "..." if len(document.summary) > 300 else document.summary)
                    
                    if document.extracted_info:
                        st.write("**Key Information Extracted:**")
                        for key, value in document.extracted_info.items():
                            if key != "Raw Extraction" and value:
                                st.write(f"- **{key}:** {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
                
            except Exception as e:
                st.write("Could not load processing results preview.")
    
    def _display_text_preview(self, extracted_text: str):
        """Display a preview of the extracted text."""
        st.markdown("---")
        st.subheader("📄 Text Preview")
        
        # Show text statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Characters", f"{len(extracted_text):,}")
        
        with col2:
            word_count = len(extracted_text.split())
            st.metric("Words", f"{word_count:,}")
        
        with col3:
            line_count = len(extracted_text.split('\n'))
            st.metric("Lines", f"{line_count:,}")
        
        # Show text preview
        preview_text = extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
        st.text_area(
            "Text Preview (first 500 characters)",
            value=preview_text,
            height=150,
            disabled=True
        )
        
        # Option to show full text
        if st.checkbox("Show full text"):
            st.text_area(
                "Full Text Content",
                value=extracted_text,
                height=400,
                disabled=True
            )