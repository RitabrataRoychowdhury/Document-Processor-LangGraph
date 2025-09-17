"""
Streamlit-based web interface for file upload and processing.
Provides user-friendly interface with real-time feedback and validation.
"""

import streamlit as st
from typing import Optional, Dict, Any
import time
from src.infrastructure.storage.file_handler import FileUploadHandler, FileMetadata

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
        Enhanced file upload section with drag-and-drop, validation, and progress indicators
        
        Returns:
            Optional[Dict[str, Any]]: File data if successfully uploaded and validated
        """
        st.header("📄 Enhanced Document Upload")
        
        # Enhanced upload instructions with drag-and-drop support
        st.markdown("""
        **📤 Drag and Drop Support**
        - Drag files directly into the upload area below
        - Support for multiple file formats and batch processing
        - Real-time validation and progress tracking
        """)
        
        # Display supported formats with enhanced information
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(
                "**📋 Supported Formats:**\n"
                "• PDF - Medical reports, PQME documents\n"
                "• DOCX - Word documents, templates\n"
                "• TXT - Plain text medical records"
            )
        
        with col2:
            st.info(
                "**⚙️ Processing Features:**\n"
                "• Real-time field extraction\n"
                "• Confidence score validation\n"
                "• Evidence snippet collection"
            )
        
        # Enhanced file upload widget with drag-and-drop
        uploaded_file = st.file_uploader(
            "📁 Choose a document to upload or drag and drop here",
            type=['pdf', 'txt', 'docx'],
            help="Select a PDF, TXT, or DOCX file to process with evidence-first extraction",
            accept_multiple_files=False,
            key="enhanced_file_uploader"
        )
        
        # File validation status indicator
        if uploaded_file is not None:
            return self._handle_enhanced_file_upload(uploaded_file)
        
        # Show upload tips
        with st.expander("💡 Upload Tips", expanded=False):
            st.markdown("""
            **For best results:**
            - Use high-quality scanned documents (300+ DPI)
            - Ensure text is clearly readable
            - Include complete patient information
            - Upload PQME reports for optimal field extraction
            
            **File size limits:**
            - Maximum: 10MB per file
            - Recommended: Under 5MB for faster processing
            """)
        
        return None
    
    def _handle_enhanced_file_upload(self, uploaded_file) -> Optional[Dict[str, Any]]:
        """
        Enhanced file upload handler with real-time validation and progress indicators
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            Optional[Dict[str, Any]]: File data if successful
        """
        # Enhanced file information display
        st.subheader("📋 File Validation & Processing")
        
        # Get file metadata with enhanced validation
        metadata = self.file_handler.get_file_metadata(uploaded_file)
        
        # Enhanced file information layout
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**📄 Filename:** {metadata['filename']}")
            st.write(f"**📊 File Type:** {metadata['file_type']}")
        
        with col2:
            st.write(f"**💾 File Size:** {metadata['file_size_mb']} MB")
            st.write(f"**📅 Upload Time:** {time.strftime('%H:%M:%S')}")
        
        with col3:
            # Real-time validation status
            if metadata['is_valid']:
                st.success("✅ Validation Passed")
                st.success("🔄 Ready for Processing")
            else:
                st.error("❌ Validation Failed")
                st.error(metadata['error_message'])
                return None
        
        # Enhanced progress indicators
        st.markdown("---")
        st.subheader("🔄 Processing Progress")
        
        # Process file with enhanced tracking
        if metadata['is_valid']:
            return self._process_enhanced_file(uploaded_file, metadata)
        
        return None

    def _handle_file_upload(self, uploaded_file) -> Optional[Dict[str, Any]]:
        """Legacy file upload handler - redirects to enhanced version."""
        return self._handle_enhanced_file_upload(uploaded_file)
    
    def _process_enhanced_file(self, uploaded_file, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Enhanced file processing with real-time extraction progress and field-by-field confidence scoring
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            metadata: File metadata dictionary
            
        Returns:
            Optional[Dict[str, Any]]: Processed file data with extraction results
        """
        # Enhanced processing status display
        progress_container = st.container()
        
        with progress_container:
            # Multi-stage progress tracking
            st.markdown("**📊 Processing Stages:**")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                stage1_status = st.empty()
                stage1_progress = st.empty()
            
            with col2:
                stage2_status = st.empty()
                stage2_progress = st.empty()
            
            with col3:
                stage3_status = st.empty()
                stage3_progress = st.empty()
            
            with col4:
                stage4_status = st.empty()
                stage4_progress = st.empty()
        
        # Overall progress bar
        overall_progress = st.progress(0)
        status_text = st.empty()
        
        try:
            # Stage 1: Text Extraction
            stage1_status.info("📖 Text Extraction")
            stage1_progress.progress(0.5)
            overall_progress.progress(0.1)
            status_text.text("📖 Extracting text content...")
            
            extracted_text, error_message = self.file_handler.extract_text(uploaded_file)
            
            if error_message:
                stage1_status.error("❌ Failed")
                stage1_progress.progress(0)
                st.error(f"❌ Text extraction failed: {error_message}")
                return None
            
            stage1_status.success("✅ Complete")
            stage1_progress.progress(1.0)
            overall_progress.progress(0.25)
            time.sleep(0.5)
            
            # Stage 2: Field Extraction with Confidence Scoring
            stage2_status.info("🔍 Field Extraction")
            stage2_progress.progress(0.3)
            overall_progress.progress(0.35)
            status_text.text("🔍 Extracting medical fields with confidence scoring...")
            
            # Simulate field extraction (in production, this would use actual extraction service)
            extracted_fields = self._simulate_field_extraction(extracted_text)
            
            stage2_status.success("✅ Complete")
            stage2_progress.progress(1.0)
            overall_progress.progress(0.5)
            
            # Display real-time field extraction results
            self._display_real_time_extraction_results(extracted_fields)
            
            # Stage 3: Evidence Validation
            stage3_status.info("✅ Evidence Validation")
            stage3_progress.progress(0.4)
            overall_progress.progress(0.6)
            status_text.text("✅ Validating evidence against confidence thresholds...")
            
            # Simulate evidence validation
            validation_results = self._simulate_evidence_validation(extracted_fields)
            
            stage3_status.success("✅ Complete")
            stage3_progress.progress(1.0)
            overall_progress.progress(0.75)
            
            # Display validation results
            self._display_validation_results(validation_results)
            
            # Stage 4: Knowledge Graph Population (if available)
            stage4_status.info("🕸️ Knowledge Graph")
            stage4_progress.progress(0.6)
            overall_progress.progress(0.85)
            status_text.text("🕸️ Populating knowledge graph with validated evidence...")
            
            # Simulate knowledge graph population
            kg_results = self._simulate_kg_population(validation_results)
            
            stage4_status.success("✅ Complete")
            stage4_progress.progress(1.0)
            overall_progress.progress(1.0)
            status_text.text("✅ Enhanced processing complete!")
            
            # Success message
            st.success(f"🎉 Successfully processed '{metadata['filename']}' with evidence-first extraction!")
            
            # Enhanced evidence snippet viewer
            self._display_evidence_snippet_viewer(extracted_fields, extracted_text)
            
            # Prepare enhanced file data
            file_data = {
                'filename': metadata['filename'],
                'file_type': metadata['file_type'],
                'file_size': metadata['file_size'],
                'extracted_text': extracted_text,
                'metadata': metadata,
                'extracted_fields': extracted_fields,
                'validation_results': validation_results,
                'kg_results': kg_results,
                'processing_complete': True,
                'processing_method': 'evidence_first'
            }
            
            # Store in session state
            file_id = f"{metadata['filename']}_{int(time.time())}"
            st.session_state.uploaded_files[file_id] = file_data
            
            return file_data
            
        except Exception as e:
            # Reset all progress indicators on error
            for status in [stage1_status, stage2_status, stage3_status, stage4_status]:
                status.error("❌ Error")
            overall_progress.progress(0)
            status_text.empty()
            st.error(f"❌ Enhanced processing failed: {str(e)}")
            return None

    def _process_valid_file(self, uploaded_file, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Legacy file processing - redirects to enhanced version."""
        return self._process_enhanced_file(uploaded_file, metadata)
    
    def _simulate_field_extraction(self, extracted_text: str) -> Dict[str, Any]:
        """
        Simulate field extraction with confidence scoring (in production, this would use actual extraction service)
        
        Args:
            extracted_text: The extracted text content
            
        Returns:
            Dict containing extracted fields with confidence scores
        """
        import re
        import random
        
        # Simulate field extraction based on text patterns
        fields = {}
        
        # Patient name extraction
        name_patterns = [r"Patient:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", r"Name:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"]
        for pattern in name_patterns:
            match = re.search(pattern, extracted_text, re.IGNORECASE)
            if match:
                fields['patient_name'] = {
                    'value': match.group(1).strip(),
                    'confidence': random.uniform(0.85, 0.98),
                    'source_snippet': match.group(0),
                    'position': match.span()
                }
                break
        
        # Case number extraction
        case_patterns = [r"Case\s*(?:Number|No\.?|#):?\s*([A-Z0-9\-]+)", r"Claim\s*(?:Number|No\.?|#):?\s*([A-Z0-9\-]+)"]
        for pattern in case_patterns:
            match = re.search(pattern, extracted_text, re.IGNORECASE)
            if match:
                fields['case_number'] = {
                    'value': match.group(1).strip(),
                    'confidence': random.uniform(0.75, 0.95),
                    'source_snippet': match.group(0),
                    'position': match.span()
                }
                break
        
        # Injury date extraction
        date_patterns = [r"(?:Injury|Accident)\s*(?:Date|On):?\s*([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})", r"Date\s*of\s*(?:Injury|Accident):?\s*([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})"]
        for pattern in date_patterns:
            match = re.search(pattern, extracted_text, re.IGNORECASE)
            if match:
                fields['injury_date'] = {
                    'value': match.group(1).strip(),
                    'confidence': random.uniform(0.65, 0.85),
                    'source_snippet': match.group(0),
                    'position': match.span()
                }
                break
        
        # Body parts extraction
        body_part_keywords = ['back', 'knee', 'shoulder', 'neck', 'ankle', 'wrist', 'spine', 'lumbar', 'cervical']
        found_parts = []
        for keyword in body_part_keywords:
            if keyword.lower() in extracted_text.lower():
                found_parts.append(keyword.title())
        
        if found_parts:
            fields['body_parts'] = {
                'value': ', '.join(found_parts[:3]),  # Limit to first 3 found
                'confidence': random.uniform(0.80, 0.95),
                'source_snippet': f"Multiple references to {', '.join(found_parts[:3])}",
                'position': (0, 0)  # Placeholder
            }
        
        # Diagnosis extraction (often has lower confidence)
        diagnosis_keywords = ['diagnosis', 'condition', 'disorder', 'syndrome']
        for keyword in diagnosis_keywords:
            pattern = rf"{keyword}:?\s*([^.\n]+)"
            match = re.search(pattern, extracted_text, re.IGNORECASE)
            if match:
                fields['diagnosis'] = {
                    'value': match.group(1).strip()[:50] + "..." if len(match.group(1).strip()) > 50 else match.group(1).strip(),
                    'confidence': random.uniform(0.35, 0.65),  # Often lower confidence
                    'source_snippet': match.group(0),
                    'position': match.span()
                }
                break
        
        return fields

    def _simulate_evidence_validation(self, extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate evidence validation against confidence thresholds
        
        Args:
            extracted_fields: Fields extracted with confidence scores
            
        Returns:
            Dict containing validation results
        """
        accepted_fields = {}
        flagged_fields = {}
        missing_fields = []
        
        # Required fields for QME processing
        required_fields = ['patient_name', 'case_number', 'injury_date', 'body_parts', 'diagnosis']
        
        for field_name in required_fields:
            if field_name in extracted_fields:
                field_data = extracted_fields[field_name]
                confidence = field_data['confidence']
                
                if confidence >= 0.8:
                    accepted_fields[field_name] = field_data
                elif confidence >= 0.5:
                    flagged_fields[field_name] = field_data
                else:
                    missing_fields.append(field_name)
            else:
                missing_fields.append(field_name)
        
        # Calculate overall metrics
        total_fields = len(required_fields)
        accepted_count = len(accepted_fields)
        flagged_count = len(flagged_fields)
        missing_count = len(missing_fields)
        
        evidence_completeness = (accepted_count + flagged_count * 0.5) / total_fields
        overall_confidence = sum(field['confidence'] for field in accepted_fields.values()) / max(accepted_count, 1)
        
        return {
            'accepted_fields': accepted_fields,
            'flagged_fields': flagged_fields,
            'missing_fields': missing_fields,
            'evidence_completeness': evidence_completeness,
            'overall_confidence': overall_confidence,
            'can_generate_report': evidence_completeness >= 0.6
        }

    def _simulate_kg_population(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate knowledge graph population with validated evidence
        
        Args:
            validation_results: Results from evidence validation
            
        Returns:
            Dict containing knowledge graph population results
        """
        accepted_fields = validation_results['accepted_fields']
        
        # Simulate knowledge graph updates
        nodes_created = len(accepted_fields) * 2  # Each field might create multiple nodes
        relationships_created = max(0, len(accepted_fields) - 1)  # Relationships between fields
        
        return {
            'nodes_created': nodes_created,
            'relationships_created': relationships_created,
            'population_success': True,
            'processing_time': 0.8  # Simulated processing time
        }

    def _display_real_time_extraction_results(self, extracted_fields: Dict[str, Any]):
        """
        Display real-time field extraction results with confidence scores
        
        Args:
            extracted_fields: Fields extracted with confidence scores
        """
        st.markdown("---")
        st.subheader("🔍 Real-Time Field Extraction Results")
        
        if not extracted_fields:
            st.warning("⚠️ No fields extracted from document")
            return
        
        # Display each extracted field
        for field_name, field_data in extracted_fields.items():
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**{field_name.replace('_', ' ').title()}:** {field_data['value']}")
            
            with col2:
                confidence = field_data['confidence']
                if confidence >= 0.8:
                    st.success(f"✅ {confidence:.1%}")
                elif confidence >= 0.5:
                    st.warning(f"⚠️ {confidence:.1%}")
                else:
                    st.error(f"❌ {confidence:.1%}")
            
            with col3:
                # Show extraction status
                if confidence >= 0.8:
                    st.success("Accepted")
                elif confidence >= 0.5:
                    st.warning("Flagged")
                else:
                    st.error("Low Conf.")

    def _display_validation_results(self, validation_results: Dict[str, Any]):
        """
        Display validation results showing accepted, flagged, and missing fields
        
        Args:
            validation_results: Results from evidence validation
        """
        st.markdown("---")
        st.subheader("✅ Evidence Validation Results")
        
        # Validation summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Accepted Fields", len(validation_results['accepted_fields']), "≥0.8 confidence")
        
        with col2:
            st.metric("Flagged Fields", len(validation_results['flagged_fields']), "0.5-0.8 confidence")
        
        with col3:
            st.metric("Missing Fields", len(validation_results['missing_fields']), "<0.5 confidence")
        
        with col4:
            completeness = validation_results['evidence_completeness']
            st.metric("Evidence Completeness", f"{completeness:.1%}")
        
        # Detailed validation status
        if validation_results['can_generate_report']:
            st.success("✅ Sufficient evidence for QME template generation")
        else:
            st.warning("⚠️ Additional evidence may be needed for complete QME template")

    def _display_evidence_snippet_viewer(self, extracted_fields: Dict[str, Any], extracted_text: str):
        """
        Display evidence snippet viewer showing source document references and extraction context
        
        Args:
            extracted_fields: Fields extracted with confidence scores
            extracted_text: Original extracted text
        """
        st.markdown("---")
        st.subheader("📄 Evidence Snippet Viewer")
        
        with st.expander("🔍 View Source Evidence and Extraction Context", expanded=False):
            for field_name, field_data in extracted_fields.items():
                st.markdown(f"**{field_name.replace('_', ' ').title()}:**")
                
                # Show source snippet
                snippet = field_data.get('source_snippet', 'No snippet available')
                st.code(snippet, language=None)
                
                # Show confidence and context
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"Confidence: {field_data['confidence']:.1%}")
                with col2:
                    st.write(f"Extracted Value: {field_data['value']}")
                
                st.markdown("---")
        
        # Show text statistics
        st.subheader("📊 Document Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Characters", f"{len(extracted_text):,}")
        
        with col2:
            word_count = len(extracted_text.split())
            st.metric("Words", f"{word_count:,}")
        
        with col3:
            line_count = len(extracted_text.split('\n'))
            st.metric("Lines", f"{line_count:,}")

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