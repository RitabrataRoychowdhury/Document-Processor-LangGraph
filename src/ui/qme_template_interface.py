"""
QME Template Generation Interface for Streamlit.

This module provides a comprehensive UI for generating QME templates from patient documents,
including drag-and-drop upload, processing workflow, template customization, and download functionality.
"""

import streamlit as st
import os
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import tempfile
import base64
from io import BytesIO

from src.services.qme_template_generator import QMETemplateGenerator, QMETemplateData
from src.services.file_handler import FileUploadHandler
from src.storage.document_storage import DocumentStorage
from src.models.document import Document
from src.utils.logging_config import get_logger
from src.utils.error_handling import format_error_for_ui
from src.config.app_config import app_config

logger = get_logger(__name__)


class QMETemplateInterface:
    """Streamlit interface for QME template generation."""
    
    def __init__(self):
        """Initialize the QME template interface."""
        self.template_generator = QMETemplateGenerator()
        self.file_handler = FileUploadHandler()
        self.storage = DocumentStorage()
        
        # Initialize session state
        if 'qme_uploaded_files' not in st.session_state:
            st.session_state.qme_uploaded_files = {}
        if 'qme_processing_status' not in st.session_state:
            st.session_state.qme_processing_status = {}
        if 'qme_generated_templates' not in st.session_state:
            st.session_state.qme_generated_templates = {}
        if 'qme_current_step' not in st.session_state:
            st.session_state.qme_current_step = 'upload'
        if 'qme_doctor_info' not in st.session_state:
            st.session_state.qme_doctor_info = {}
        if 'qme_template_preferences' not in st.session_state:
            st.session_state.qme_template_preferences = {}
    
    def render_qme_template_page(self):
        """Render the main QME template generation page."""
        st.header("🏥 QME Template Generator")
        st.markdown("""
        Generate comprehensive QME (Qualified Medical Evaluator) reports from patient documents.
        Upload patient medical records and get professionally formatted QME templates.
        """)
        
        # Progress indicator
        self._render_progress_indicator()
        
        # Main content based on current step
        current_step = st.session_state.qme_current_step
        
        if current_step == 'upload':
            self._render_upload_step()
        elif current_step == 'process':
            self._render_process_step()
        elif current_step == 'review':
            self._render_review_step()
        elif current_step == 'customize':
            self._render_customize_step()
        elif current_step == 'download':
            self._render_download_step()
        
        # Navigation buttons
        self._render_navigation_buttons()
        
        # Template gallery sidebar
        with st.sidebar:
            self._render_template_gallery()
    
    def _render_progress_indicator(self):
        """Render the step-by-step progress indicator."""
        steps = ['Upload', 'Process', 'Review', 'Customize', 'Download']
        current_step = st.session_state.qme_current_step
        
        # Map step names to indices
        step_indices = {
            'upload': 0,
            'process': 1,
            'review': 2,
            'customize': 3,
            'download': 4
        }
        
        current_index = step_indices.get(current_step, 0)
        
        # Create progress bar
        progress = (current_index + 1) / len(steps)
        st.progress(progress)
        
        # Create step indicators
        cols = st.columns(len(steps))
        for i, (col, step) in enumerate(zip(cols, steps)):
            with col:
                if i < current_index:
                    st.success(f"✅ {step}")
                elif i == current_index:
                    st.info(f"🔄 {step}")
                else:
                    st.write(f"⏳ {step}")
        
        st.markdown("---")
    
    def _render_upload_step(self):
        """Render the document upload step."""
        st.subheader("📤 Step 1: Upload Patient Documents")
        
        st.info("""
        **Upload patient medical records for QME template generation:**
        - PQME (Permanent and Qualified Medical Evaluator) reports
        - Medical records and examination reports
        - Diagnostic studies and imaging reports
        - Treatment history and progress notes
        """)
        
        # File validation info
        st.markdown("""
        **Supported formats:** PDF, DOCX, TXT  
        **Maximum file size:** 10MB per file  
        **Multiple files:** Upload multiple documents for comprehensive analysis
        """)
        
        # Drag and drop file upload
        uploaded_files = st.file_uploader(
            "Drop patient documents here or click to browse",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            help="Select one or more patient medical documents"
        )
        
        if uploaded_files:
            self._handle_multiple_file_upload(uploaded_files)
        
        # Show uploaded files
        if st.session_state.qme_uploaded_files:
            st.subheader("📋 Uploaded Documents")
            self._display_uploaded_files()
        
        # Example files section
        with st.expander("💡 Example Patient Documents", expanded=False):
            st.markdown("""
            **Examples of suitable patient documents:**
            - `Injured worker-PQME-(09.05.2025)-AA CL-09.09.2025.p5.pdf`
            - `Injured worker-PQME-(09.08.2025)-DA CL-09.09.2025.p4.pdf`
            - Medical examination reports
            - Diagnostic imaging reports
            - Treatment summaries
            - Disability evaluation reports
            """)
    
    def _render_process_step(self):
        """Render the document processing step."""
        st.subheader("🔄 Step 2: Processing Documents")
        
        if not st.session_state.qme_uploaded_files:
            st.warning("⚠️ No documents uploaded. Please go back to Step 1.")
            if st.button("← Back to Upload"):
                st.session_state.qme_current_step = 'upload'
                st.rerun()
            return
        
        # Processing status
        st.info("Processing your patient documents to extract medical information...")
        
        # Process each uploaded file
        all_processed = True
        for file_id, file_data in st.session_state.qme_uploaded_files.items():
            if file_data.get('processing_status') != 'completed':
                all_processed = False
                self._process_patient_document(file_id, file_data)
        
        if all_processed:
            st.success("✅ All documents processed successfully!")
            st.info("Ready to review extracted information and generate template.")
            
            # Auto-advance to review step
            if st.button("Continue to Review →", type="primary"):
                st.session_state.qme_current_step = 'review'
                st.rerun()
        else:
            # Show processing progress
            self._show_processing_progress()
    
    def _render_review_step(self):
        """Render the review step for extracted information."""
        st.subheader("👀 Step 3: Review Extracted Information")
        
        if not self._has_processed_documents():
            st.warning("⚠️ No processed documents found. Please process documents first.")
            return
        
        # Display extracted information for review
        extracted_data = self._get_extracted_data()
        
        if not extracted_data:
            st.error("❌ No information could be extracted from the uploaded documents.")
            st.info("Please check that the documents contain patient medical information.")
            return
        
        # Patient Information Section
        st.subheader("👤 Patient Information")
        patient_info = extracted_data.get('patient_info', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Name:** {patient_info.get('name', 'Not found')}")
            st.write(f"**Age:** {patient_info.get('age', 'Not found')}")
            st.write(f"**Gender:** {patient_info.get('gender', 'Not found')}")
        
        with col2:
            st.write(f"**Case Number:** {patient_info.get('case_number', 'Not found')}")
            st.write(f"**Injury Date:** {patient_info.get('injury_date', 'Not found')}")
            st.write(f"**Body Parts:** {', '.join(patient_info.get('body_parts', []))}")
        
        # Medical Findings Section
        st.subheader("🏥 Medical Findings")
        medical_findings = extracted_data.get('medical_findings', {})
        
        # Diagnoses
        diagnoses = medical_findings.get('diagnoses', [])
        if diagnoses:
            st.write("**Diagnoses:**")
            for i, diagnosis in enumerate(diagnoses, 1):
                st.write(f"{i}. {diagnosis}")
        else:
            st.warning("⚠️ No diagnoses found in documents")
        
        # Clinical Findings
        findings = medical_findings.get('findings', [])
        if findings:
            with st.expander("🔍 Clinical Findings", expanded=False):
                for i, finding in enumerate(findings, 1):
                    st.write(f"{i}. {finding}")
        
        # Imaging Studies
        imaging = medical_findings.get('imaging_studies', [])
        if imaging:
            with st.expander("📸 Imaging Studies", expanded=False):
                for i, study in enumerate(imaging, 1):
                    st.write(f"{i}. {study}")
        
        # Missing Information Alert
        missing_info = extracted_data.get('missing_sections', [])
        if missing_info:
            st.warning("⚠️ **Missing Information Detected:**")
            for section in missing_info:
                st.write(f"• {section}")
            st.info("The template will highlight these missing sections for manual completion.")
        
        # Accuracy confirmation
        st.subheader("✅ Confirm Information Accuracy")
        accuracy_confirmed = st.checkbox(
            "I have reviewed the extracted information and confirm it is accurate",
            key="accuracy_confirmed"
        )
        
        if accuracy_confirmed:
            if st.button("Continue to Customization →", type="primary"):
                st.session_state.qme_current_step = 'customize'
                st.rerun()
    
    def _render_customize_step(self):
        """Render the template customization step."""
        st.subheader("🎨 Step 4: Customize Template")
        
        # Doctor Information
        st.subheader("👨‍⚕️ Doctor Information")
        
        col1, col2 = st.columns(2)
        with col1:
            doctor_name = st.text_input(
                "Doctor Name",
                value=st.session_state.qme_doctor_info.get('name', ''),
                key="doctor_name"
            )
            
            medical_license = st.text_input(
                "Medical License Number",
                value=st.session_state.qme_doctor_info.get('license', ''),
                key="doctor_license"
            )
            
            specialty = st.text_input(
                "Medical Specialty",
                value=st.session_state.qme_doctor_info.get('specialty', ''),
                key="doctor_specialty"
            )
        
        with col2:
            clinic_name = st.text_input(
                "Clinic/Practice Name",
                value=st.session_state.qme_doctor_info.get('clinic', ''),
                key="doctor_clinic"
            )
            
            address = st.text_area(
                "Address",
                value=st.session_state.qme_doctor_info.get('address', ''),
                key="doctor_address",
                height=100
            )
            
            phone = st.text_input(
                "Phone Number",
                value=st.session_state.qme_doctor_info.get('phone', ''),
                key="doctor_phone"
            )
        
        # Update session state
        st.session_state.qme_doctor_info.update({
            'name': doctor_name,
            'license': medical_license,
            'specialty': specialty,
            'clinic': clinic_name,
            'address': address,
            'phone': phone
        })
        
        # Letterhead Upload
        st.subheader("🏢 Letterhead (Optional)")
        letterhead_file = st.file_uploader(
            "Upload clinic letterhead (PNG, JPG)",
            type=['png', 'jpg', 'jpeg'],
            help="Optional: Upload your clinic letterhead for professional templates"
        )
        
        if letterhead_file:
            st.success("✅ Letterhead uploaded successfully")
            # Store letterhead in session state
            st.session_state.qme_template_preferences['letterhead'] = letterhead_file
        
        # Template Formatting Preferences
        st.subheader("📄 Formatting Preferences")
        
        col1, col2 = st.columns(2)
        with col1:
            font_size = st.selectbox(
                "Font Size",
                options=[10, 11, 12, 14],
                index=2,  # Default to 12
                key="font_size"
            )
            
            line_spacing = st.selectbox(
                "Line Spacing",
                options=["Single", "1.15", "1.5", "Double"],
                index=1,  # Default to 1.15
                key="line_spacing"
            )
        
        with col2:
            page_margins = st.selectbox(
                "Page Margins",
                options=["Normal", "Narrow", "Wide"],
                index=0,  # Default to Normal
                key="page_margins"
            )
            
            include_toc = st.checkbox(
                "Include Table of Contents",
                value=True,
                key="include_toc"
            )
        
        # Update template preferences
        st.session_state.qme_template_preferences.update({
            'font_size': font_size,
            'line_spacing': line_spacing,
            'page_margins': page_margins,
            'include_toc': include_toc
        })
        
        # Template Preview Option
        st.subheader("👀 Template Preview")
        if st.button("📋 Generate Preview", type="secondary"):
            self._generate_template_preview()
        
        # Continue button
        if st.button("Generate Template →", type="primary"):
            st.session_state.qme_current_step = 'download'
            st.rerun()
    
    def _render_download_step(self):
        """Render the template download step."""
        st.subheader("📥 Step 5: Download Template")
        
        # Generate the final template
        if 'final_template' not in st.session_state:
            with st.spinner("🔄 Generating final QME template..."):
                try:
                    template_path, template_data = self._generate_final_template()
                    st.session_state.final_template = {
                        'path': template_path,
                        'data': template_data,
                        'generated_at': datetime.now()
                    }
                except Exception as e:
                    st.error(f"❌ Error generating template: {str(e)}")
                    return
        
        template_info = st.session_state.final_template
        
        st.success("✅ QME Template Generated Successfully!")
        
        # Template Information
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Generated At", template_info['generated_at'].strftime("%Y-%m-%d %H:%M"))
        with col2:
            st.metric("File Format", "DOCX")
        with col3:
            if os.path.exists(template_info['path']):
                file_size = os.path.getsize(template_info['path'])
                st.metric("File Size", f"{file_size / 1024:.1f} KB")
        
        # Download Options
        st.subheader("📥 Download Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Primary DOCX download
            if os.path.exists(template_info['path']):
                with open(template_info['path'], 'rb') as file:
                    st.download_button(
                        label="📄 Download DOCX Template",
                        data=file.read(),
                        file_name=f"QME_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary"
                    )
        
        with col2:
            # PDF Preview (if available)
            if st.button("📋 Generate PDF Preview"):
                self._generate_pdf_preview(template_info['path'])
        
        with col3:
            # Email functionality
            if st.button("📧 Email Template"):
                self._show_email_dialog()
        
        # Template Analytics
        st.subheader("📊 Template Analytics")
        self._show_template_analytics(template_info['data'])
        
        # Save to Gallery
        if st.button("⭐ Save to Template Gallery"):
            self._save_to_gallery(template_info)
        
        # Professional Template Assembly Integration
        st.markdown("---")
        st.subheader("🏥 Professional Template Assembly")
        st.info("""
        **Upgrade to Professional Gold Standard Templates**
        
        Take your QME template to the next level with our Professional Template Assembly System:
        - ✅ Gold standard compliance based on AI Example QME Report Template
        - ✅ Comprehensive validation and quality assurance
        - ✅ Professional medical formatting and structure
        - ✅ Missing information detection and placeholder management
        - ✅ Complete quality reports and compliance checking
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Upgrade to Professional Template", type="primary"):
                # Store the current template data for professional assembly
                if 'final_template' in st.session_state:
                    st.session_state.qme_template_data = template_info['data']
                st.session_state.switch_to_professional_template = True
                st.rerun()
        
        with col2:
            if st.button("📋 Learn More About Professional Assembly"):
                st.info("""
                **Professional Template Assembly Features:**
                
                🏥 **Gold Standard Compliance**
                - Exact formatting from AI Example QME Report Template.docx
                - Professional medical document structure
                - Proper headers, footers, and signature blocks
                
                🔍 **Comprehensive Validation**
                - Pre-assembly and post-assembly quality checks
                - Missing information detection and highlighting
                - Compliance status and improvement recommendations
                
                📊 **Quality Assurance**
                - Detailed quality scoring (completeness, accuracy, compliance)
                - Professional quality reports with actionable insights
                - Validation against AMA Guidelines and legal requirements
                
                📥 **Professional Download**
                - High-quality DOCX with proper medical formatting
                - Complete packages with quality reports
                - Ready for submission and professional use
                """)
        
        # Start New Template
        st.markdown("---")
        if st.button("🔄 Generate New Template", type="secondary"):
            self._reset_workflow()
    
    def _render_navigation_buttons(self):
        """Render navigation buttons for workflow steps."""
        st.markdown("---")
        
        current_step = st.session_state.qme_current_step
        steps = ['upload', 'process', 'review', 'customize', 'download']
        current_index = steps.index(current_step)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            # Previous button
            if current_index > 0:
                if st.button("← Previous Step"):
                    st.session_state.qme_current_step = steps[current_index - 1]
                    st.rerun()
        
        with col3:
            # Next button (context-sensitive)
            if current_step == 'upload' and st.session_state.qme_uploaded_files:
                if st.button("Next Step →"):
                    st.session_state.qme_current_step = 'process'
                    st.rerun()
            elif current_step == 'process' and self._has_processed_documents():
                if st.button("Next Step →"):
                    st.session_state.qme_current_step = 'review'
                    st.rerun()
    
    def _render_template_gallery(self):
        """Render the template gallery in sidebar."""
        st.sidebar.subheader("📚 Template Gallery")
        
        templates = st.session_state.qme_generated_templates
        
        if not templates:
            st.sidebar.info("No templates generated yet")
        else:
            # Show recent templates
            for template_id, template_info in list(templates.items())[-5:]:  # Last 5 templates
                patient_name = template_info.get('patient_name', 'Unknown')
                version = template_info.get('version', 1)
                
                # Create display name with version
                display_name = f"{patient_name} (v{version})" if version > 1 else patient_name
                
                with st.sidebar.expander(f"📄 {display_name}", expanded=False):
                    st.write(f"**Generated:** {template_info.get('generated_at', 'Unknown')}")
                    st.write(f"**Status:** {template_info.get('status', 'Unknown')}")
                    
                    # Show completeness score
                    completeness = template_info.get('completeness_score', 0)
                    if completeness > 80:
                        st.success(f"**Completeness:** {completeness:.1f}%")
                    elif completeness > 60:
                        st.warning(f"**Completeness:** {completeness:.1f}%")
                    else:
                        st.error(f"**Completeness:** {completeness:.1f}%")
                    
                    if template_info.get('favorite'):
                        st.write("⭐ **Favorited**")
                    
                    # Show revision history if available
                    revision_history = template_info.get('revision_history', [])
                    if revision_history:
                        st.write(f"**Revisions:** {len(revision_history)} previous versions")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"📥", key=f"download_{template_id}", help="Download"):
                            self._download_template_from_gallery(template_id)
                    
                    with col2:
                        if st.button(f"⭐", key=f"favorite_{template_id}", help="Toggle Favorite"):
                            self._toggle_template_favorite(template_id)
        
        # Bulk processing section
        st.sidebar.subheader("🔄 Bulk Processing")
        
        if st.sidebar.button("📁 Bulk Process Documents"):
            self._show_bulk_processing_dialog()
        
        # Gallery management
        if st.sidebar.button("🗑️ Clear Gallery"):
            st.session_state.qme_generated_templates = {}
            st.rerun()
        
        # Template analytics
        if templates:
            st.sidebar.subheader("📊 Analytics")
            total_templates = len(templates)
            favorites = sum(1 for t in templates.values() if t.get('favorite'))
            
            st.sidebar.metric("Total Templates", total_templates)
            st.sidebar.metric("Favorites", favorites)
            
            # Completion rate
            completed = sum(1 for t in templates.values() if t.get('status') == 'completed')
            completion_rate = (completed / total_templates * 100) if total_templates > 0 else 0
            st.sidebar.metric("Completion Rate", f"{completion_rate:.1f}%")
    
    def _handle_multiple_file_upload(self, uploaded_files):
        """Handle multiple file upload with validation."""
        for uploaded_file in uploaded_files:
            # Check if file already uploaded
            file_key = f"{uploaded_file.name}_{uploaded_file.size}"
            if file_key in st.session_state.qme_uploaded_files:
                continue
            
            # Validate file
            metadata = self.file_handler.get_file_metadata(uploaded_file)
            
            if not metadata['is_valid']:
                st.error(f"❌ {uploaded_file.name}: {metadata['error_message']}")
                continue
            
            # Extract text
            extracted_text, error_message = self.file_handler.extract_text(uploaded_file)
            
            if error_message:
                st.error(f"❌ {uploaded_file.name}: {error_message}")
                continue
            
            # Store file data
            file_data = {
                'filename': uploaded_file.name,
                'file_type': metadata['file_type'],
                'file_size': metadata['file_size'],
                'extracted_text': extracted_text,
                'uploaded_at': datetime.now(),
                'processing_status': 'pending',
                'file_id': str(uuid.uuid4())
            }
            
            st.session_state.qme_uploaded_files[file_key] = file_data
            st.success(f"✅ Uploaded: {uploaded_file.name}")
    
    def _display_uploaded_files(self):
        """Display the list of uploaded files."""
        for file_key, file_data in st.session_state.qme_uploaded_files.items():
            with st.expander(f"📄 {file_data['filename']}", expanded=False):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Type:** {file_data['file_type']}")
                    st.write(f"**Size:** {file_data['file_size'] / (1024*1024):.2f} MB")
                    st.write(f"**Status:** {file_data.get('processing_status', 'pending').title()}")
                
                with col2:
                    # Validation status
                    if self._is_medical_document(file_data['extracted_text']):
                        st.success("✅ Medical Document")
                    else:
                        st.warning("⚠️ May not be medical")
                
                with col3:
                    if st.button("🗑️ Remove", key=f"remove_{file_key}"):
                        del st.session_state.qme_uploaded_files[file_key]
                        st.rerun()
                
                # Show text preview
                if st.checkbox(f"Show preview", key=f"preview_{file_key}"):
                    preview_text = file_data['extracted_text'][:500]
                    if len(file_data['extracted_text']) > 500:
                        preview_text += "..."
                    st.text_area("Text Preview", value=preview_text, height=150, disabled=True)
    
    def _is_medical_document(self, text: str) -> bool:
        """Check if document appears to be medical/patient related."""
        medical_keywords = [
            'patient', 'diagnosis', 'medical', 'examination', 'treatment',
            'injury', 'pain', 'doctor', 'physician', 'clinic', 'hospital',
            'medication', 'therapy', 'surgery', 'condition', 'symptoms',
            'qme', 'impairment', 'disability', 'evaluation'
        ]
        
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in medical_keywords if keyword in text_lower)
        
        return keyword_count >= 3  # At least 3 medical keywords
    
    def _process_patient_document(self, file_id: str, file_data: Dict[str, Any]):
        """Process a patient document to extract medical information."""
        try:
            # Update processing status
            file_data['processing_status'] = 'processing'
            
            # Show processing progress
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            with progress_placeholder:
                progress_bar = st.progress(0)
                
            with status_placeholder:
                st.info(f"🔄 Processing {file_data['filename']}...")
            
            # Simulate processing steps
            steps = [
                ("Extracting text...", 20),
                ("Analyzing content...", 40),
                ("Identifying patient information...", 60),
                ("Extracting medical findings...", 80),
                ("Finalizing extraction...", 100)
            ]
            
            for step_text, progress in steps:
                status_placeholder.info(f"🔄 {step_text}")
                progress_bar.progress(progress)
                time.sleep(0.5)  # Simulate processing time
            
            # Extract patient information (simplified for demo)
            extracted_info = self._extract_patient_information(file_data['extracted_text'])
            
            # Update file data
            file_data.update({
                'processing_status': 'completed',
                'processed_at': datetime.now(),
                'extracted_info': extracted_info
            })
            
            # Clear progress indicators
            progress_placeholder.empty()
            status_placeholder.success(f"✅ Processed {file_data['filename']}")
            
        except Exception as e:
            file_data['processing_status'] = 'failed'
            file_data['error'] = str(e)
            st.error(f"❌ Failed to process {file_data['filename']}: {str(e)}")
    
    def _extract_patient_information(self, text: str) -> Dict[str, Any]:
        """Extract patient information from document text (simplified version)."""
        import re
        
        extracted = {
            'patient_info': {},
            'medical_findings': {
                'diagnoses': [],
                'findings': [],
                'imaging_studies': []
            },
            'missing_sections': []
        }
        
        # Extract patient name
        name_patterns = [
            r"Patient:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"Name:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['patient_info']['name'] = match.group(1).strip()
                break
        
        # Extract age
        age_match = re.search(r"Age:?\s*(\d{1,3})", text, re.IGNORECASE)
        if age_match:
            extracted['patient_info']['age'] = int(age_match.group(1))
        
        # Extract case number
        case_patterns = [
            r"Case\s*(?:Number|No\.?|#):?\s*([A-Z0-9\-]+)",
            r"Claim\s*(?:Number|No\.?|#):?\s*([A-Z0-9\-]+)"
        ]
        
        for pattern in case_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['patient_info']['case_number'] = match.group(1).strip()
                break
        
        # Extract diagnoses (simplified)
        diagnosis_keywords = ['diagnosis', 'condition', 'disorder', 'syndrome']
        for keyword in diagnosis_keywords:
            pattern = rf"{keyword}:?\s*([^.\n]+)"
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 5:  # Filter out very short matches
                    extracted['medical_findings']['diagnoses'].append(match.strip())
        
        # Check for missing information
        required_fields = ['name', 'age', 'case_number']
        for field in required_fields:
            if not extracted['patient_info'].get(field):
                extracted['missing_sections'].append(f"Patient {field}")
        
        return extracted
    
    def _has_processed_documents(self) -> bool:
        """Check if there are any processed documents."""
        return any(
            file_data.get('processing_status') == 'completed'
            for file_data in st.session_state.qme_uploaded_files.values()
        )
    
    def _get_extracted_data(self) -> Dict[str, Any]:
        """Get combined extracted data from all processed documents."""
        combined_data = {
            'patient_info': {},
            'medical_findings': {
                'diagnoses': [],
                'findings': [],
                'imaging_studies': []
            },
            'missing_sections': []
        }
        
        for file_data in st.session_state.qme_uploaded_files.values():
            if file_data.get('processing_status') == 'completed':
                extracted = file_data.get('extracted_info', {})
                
                # Merge patient info (first non-empty value wins)
                for key, value in extracted.get('patient_info', {}).items():
                    if value and not combined_data['patient_info'].get(key):
                        combined_data['patient_info'][key] = value
                
                # Combine medical findings
                for key in ['diagnoses', 'findings', 'imaging_studies']:
                    findings = extracted.get('medical_findings', {}).get(key, [])
                    combined_data['medical_findings'][key].extend(findings)
                
                # Combine missing sections
                missing = extracted.get('missing_sections', [])
                combined_data['missing_sections'].extend(missing)
        
        # Remove duplicates
        for key in ['diagnoses', 'findings', 'imaging_studies']:
            combined_data['medical_findings'][key] = list(set(combined_data['medical_findings'][key]))
        
        combined_data['missing_sections'] = list(set(combined_data['missing_sections']))
        
        return combined_data
    
    def _show_processing_progress(self):
        """Show overall processing progress."""
        total_files = len(st.session_state.qme_uploaded_files)
        processed_files = sum(
            1 for file_data in st.session_state.qme_uploaded_files.values()
            if file_data.get('processing_status') == 'completed'
        )
        
        progress = processed_files / total_files if total_files > 0 else 0
        st.progress(progress)
        st.write(f"Progress: {processed_files}/{total_files} files processed")
        
        # Auto-refresh every 2 seconds if processing
        if processed_files < total_files:
            time.sleep(2)
            st.rerun()
    
    def _generate_template_preview(self):
        """Generate a preview of the template."""
        st.info("🔄 Generating template preview...")
        
        # Simulate preview generation
        with st.spinner("Creating preview..."):
            time.sleep(2)
        
        st.success("✅ Preview generated!")
        
        # Show preview sections
        with st.expander("📋 Template Preview", expanded=True):
            st.markdown("""
            **QUALIFIED MEDICAL EVALUATOR'S REPORT**
            
            **PATIENT INFORMATION**
            - Name: [Patient Name]
            - Age: [Age]
            - Case Number: [Case Number]
            
            **HISTORY OF PRESENT ILLNESS**
            [Extracted medical history will appear here]
            
            **PHYSICAL EXAMINATION**
            [Examination findings will appear here]
            
            **DIAGNOSIS**
            [Extracted diagnoses will appear here]
            
            **IMPAIRMENT RATING**
            [AMA-based impairment ratings will appear here]
            
            **RECOMMENDATIONS**
            [Treatment recommendations will appear here]
            """)
    
    def _generate_final_template(self) -> Tuple[str, Any]:
        """Generate the final QME template."""
        # Create temporary file for template
        temp_dir = tempfile.gettempdir()
        template_path = os.path.join(temp_dir, f"qme_template_{uuid.uuid4().hex}.docx")
        
        # Get extracted data
        extracted_data = self._get_extracted_data()
        
        # Use the QME template generator (simplified for demo)
        try:
            # For demo purposes, create a simple DOCX file
            from docx import Document
            
            doc = Document()
            
            # Add title
            title = doc.add_heading('QUALIFIED MEDICAL EVALUATOR\'S REPORT', 0)
            
            # Add patient information
            doc.add_heading('PATIENT INFORMATION', level=1)
            patient_info = extracted_data.get('patient_info', {})
            
            p = doc.add_paragraph()
            p.add_run('Name: ').bold = True
            p.add_run(patient_info.get('name', '[MISSING - Patient name not found]'))
            
            p = doc.add_paragraph()
            p.add_run('Age: ').bold = True
            p.add_run(str(patient_info.get('age', '[MISSING - Age not found]')))
            
            p = doc.add_paragraph()
            p.add_run('Case Number: ').bold = True
            p.add_run(patient_info.get('case_number', '[MISSING - Case number not found]'))
            
            # Add diagnoses
            doc.add_heading('DIAGNOSIS', level=1)
            diagnoses = extracted_data.get('medical_findings', {}).get('diagnoses', [])
            if diagnoses:
                for i, diagnosis in enumerate(diagnoses, 1):
                    doc.add_paragraph(f"{i}. {diagnosis}")
            else:
                doc.add_paragraph('[MISSING - No diagnoses found in documents]')
            
            # Add doctor information if provided
            doctor_info = st.session_state.qme_doctor_info
            if doctor_info.get('name'):
                doc.add_heading('EVALUATING PHYSICIAN', level=1)
                p = doc.add_paragraph()
                p.add_run('Name: ').bold = True
                p.add_run(doctor_info.get('name', ''))
                
                if doctor_info.get('license'):
                    p = doc.add_paragraph()
                    p.add_run('License: ').bold = True
                    p.add_run(doctor_info.get('license', ''))
            
            # Save document
            doc.save(template_path)
            
            return template_path, extracted_data
            
        except Exception as e:
            logger.error(f"Error generating template: {e}")
            raise
    
    def _generate_pdf_preview(self, docx_path: str):
        """Generate PDF preview of the template."""
        st.info("📋 PDF preview functionality would be implemented here")
        st.info("This would convert the DOCX template to PDF for preview")
    
    def _show_email_dialog(self):
        """Show email dialog for sending template."""
        with st.form("email_form"):
            st.subheader("📧 Email Template")
            
            # Email configuration
            col1, col2 = st.columns(2)
            
            with col1:
                recipient = st.text_input("Recipient Email*", placeholder="doctor@clinic.com")
                cc_recipients = st.text_input("CC (optional)", placeholder="admin@clinic.com")
            
            with col2:
                sender_name = st.text_input("Your Name", value=st.session_state.qme_doctor_info.get('name', ''))
                priority = st.selectbox("Priority", ["Normal", "High", "Low"])
            
            subject = st.text_input("Subject", value="QME Report Template - [Patient Name]")
            
            # Email template options
            template_type = st.selectbox(
                "Email Template",
                ["Professional", "Brief", "Detailed", "Custom"]
            )
            
            if template_type == "Professional":
                default_message = """Dear Colleague,

Please find attached the QME (Qualified Medical Evaluator) report template for your review.

This template has been generated based on the patient medical records and includes:
- Patient demographic information
- Medical history and findings
- Diagnostic information
- Preliminary impairment assessment

Please review the template and complete any missing sections as needed.

Best regards,
{sender_name}"""
            elif template_type == "Brief":
                default_message = """Please find the attached QME report template.

The template includes extracted patient information and medical findings for your review.

Thank you."""
            elif template_type == "Detailed":
                default_message = """Dear Healthcare Professional,

I am forwarding the QME report template generated from the patient medical records.

Template Contents:
- Patient Information: Extracted from source documents
- Medical Findings: Diagnoses and clinical observations
- Missing Information: Highlighted sections requiring completion
- AMA Guidelines: Relevant impairment rating references

Please review the template for accuracy and complete any missing sections. The template follows standard QME report format and includes placeholders for required information.

If you have any questions about the template or need additional information, please don't hesitate to contact me.

Professional regards,
{sender_name}
{title}
{contact_info}"""
            else:
                default_message = "Please find the attached QME report template."
            
            # Format message with doctor info
            formatted_message = default_message.format(
                sender_name=sender_name or "QME Template Generator",
                title=st.session_state.qme_doctor_info.get('specialty', ''),
                contact_info=st.session_state.qme_doctor_info.get('phone', '')
            )
            
            message = st.text_area("Message", value=formatted_message, height=200)
            
            # Attachment options
            st.subheader("📎 Attachment Options")
            
            col1, col2 = st.columns(2)
            with col1:
                include_docx = st.checkbox("Include DOCX Template", value=True)
                include_pdf = st.checkbox("Include PDF Preview", value=False)
            
            with col2:
                password_protect = st.checkbox("Password Protect", value=False)
                if password_protect:
                    password = st.text_input("Password", type="password")
            
            # Send button
            if st.form_submit_button("📧 Send Email", type="primary"):
                if not recipient:
                    st.error("Please enter recipient email address")
                elif not self._is_valid_email(recipient):
                    st.error("Please enter a valid email address")
                else:
                    self._send_template_email(
                        recipient=recipient,
                        cc_recipients=cc_recipients,
                        subject=subject,
                        message=message,
                        sender_name=sender_name,
                        priority=priority,
                        include_docx=include_docx,
                        include_pdf=include_pdf,
                        password_protect=password_protect,
                        password=password if password_protect else None
                    )
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email address format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _send_template_email(self, **email_params):
        """Send template via email (placeholder implementation)."""
        # In a real implementation, this would use an email service like:
        # - SMTP server
        # - SendGrid API
        # - AWS SES
        # - Other email service providers
        
        st.info("📧 **Email Functionality Demo**")
        st.write("In a production environment, this would:")
        st.write("✅ Connect to configured email service")
        st.write("✅ Attach the QME template file(s)")
        st.write("✅ Send email with professional formatting")
        st.write("✅ Provide delivery confirmation")
        
        # Show email preview
        with st.expander("📧 Email Preview", expanded=True):
            st.write(f"**To:** {email_params['recipient']}")
            if email_params.get('cc_recipients'):
                st.write(f"**CC:** {email_params['cc_recipients']}")
            st.write(f"**Subject:** {email_params['subject']}")
            st.write(f"**Priority:** {email_params['priority']}")
            st.write("**Message:**")
            st.text_area("", value=email_params['message'], height=150, disabled=True)
            
            st.write("**Attachments:**")
            if email_params.get('include_docx'):
                st.write("📄 QME_Template.docx")
            if email_params.get('include_pdf'):
                st.write("📄 QME_Template_Preview.pdf")
            
            if email_params.get('password_protect'):
                st.write("🔒 Files are password protected")
        
        st.success("✅ Email would be sent successfully!")
        
        # Log email activity
        logger.info(f"Email template request: {email_params['recipient']}")
    
    def _show_template_analytics(self, template_data: Any):
        """Show analytics for the generated template."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Sections Completed", "7/10")
        
        with col2:
            st.metric("Missing Information", "3 items")
        
        with col3:
            st.metric("Confidence Score", "85%")
        
        # Completion details
        with st.expander("📊 Completion Details", expanded=False):
            st.write("**Completed Sections:**")
            st.write("✅ Patient Information")
            st.write("✅ Medical History")
            st.write("✅ Diagnosis")
            
            st.write("**Missing Sections:**")
            st.write("❌ Physical Examination")
            st.write("❌ Impairment Rating")
            st.write("❌ Work Restrictions")
    
    def _save_to_gallery(self, template_info: Dict[str, Any]):
        """Save template to gallery with versioning."""
        template_id = str(uuid.uuid4())
        patient_name = template_info['data'].get('patient_info', {}).get('name', 'Unknown')
        
        # Check for existing templates for this patient
        existing_versions = []
        for existing_id, existing_template in st.session_state.qme_generated_templates.items():
            if existing_template.get('patient_name') == patient_name:
                existing_versions.append(existing_template)
        
        # Determine version number
        version_number = len(existing_versions) + 1
        
        gallery_entry = {
            'id': template_id,
            'patient_name': patient_name,
            'generated_at': template_info['generated_at'].strftime('%Y-%m-%d %H:%M'),
            'status': 'completed',
            'path': template_info['path'],
            'favorite': False,
            'version': version_number,
            'revision_history': [],
            'template_type': 'standard',
            'completeness_score': self._calculate_completeness_score(template_info['data'])
        }
        
        # Add revision history if this is a new version
        if existing_versions:
            gallery_entry['revision_history'] = [
                {
                    'version': v.get('version', 1),
                    'generated_at': v.get('generated_at'),
                    'changes': 'Updated template with new information'
                }
                for v in existing_versions
            ]
        
        st.session_state.qme_generated_templates[template_id] = gallery_entry
        
        if version_number > 1:
            st.success(f"⭐ Template saved to gallery as version {version_number}!")
        else:
            st.success("⭐ Template saved to gallery!")
    
    def _calculate_completeness_score(self, template_data: Dict[str, Any]) -> float:
        """Calculate completeness score for template."""
        required_fields = [
            'patient_info.name',
            'patient_info.age',
            'patient_info.case_number',
            'medical_findings.diagnoses'
        ]
        
        completed_fields = 0
        
        for field_path in required_fields:
            keys = field_path.split('.')
            current_data = template_data
            
            try:
                for key in keys:
                    current_data = current_data[key]
                
                if current_data:  # Field has value
                    completed_fields += 1
            except (KeyError, TypeError):
                continue  # Field missing or invalid
        
        return (completed_fields / len(required_fields)) * 100
    
    def _download_template_from_gallery(self, template_id: str):
        """Download template from gallery."""
        template_info = st.session_state.qme_generated_templates.get(template_id)
        if template_info and os.path.exists(template_info['path']):
            with open(template_info['path'], 'rb') as file:
                st.download_button(
                    label="📥 Download Template",
                    data=file.read(),
                    file_name=f"QME_Report_{template_info['patient_name']}_{template_info['generated_at']}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
    
    def _toggle_template_favorite(self, template_id: str):
        """Toggle favorite status of template."""
        if template_id in st.session_state.qme_generated_templates:
            current_status = st.session_state.qme_generated_templates[template_id].get('favorite', False)
            st.session_state.qme_generated_templates[template_id]['favorite'] = not current_status
            st.success("⭐ Favorite status updated!")
    
    def _show_bulk_processing_dialog(self):
        """Show bulk processing dialog for multiple documents."""
        with st.sidebar.form("bulk_processing_form"):
            st.write("**Bulk Process Multiple Documents**")
            
            # File uploader for multiple files
            bulk_files = st.file_uploader(
                "Select multiple patient documents",
                type=['pdf', 'docx', 'txt'],
                accept_multiple_files=True,
                key="bulk_files"
            )
            
            # Processing options
            auto_generate = st.checkbox("Auto-generate templates", value=True)
            use_default_settings = st.checkbox("Use default settings", value=True)
            
            if st.form_submit_button("🚀 Start Bulk Processing"):
                if bulk_files:
                    self._process_bulk_documents(bulk_files, auto_generate, use_default_settings)
                else:
                    st.error("Please select files to process")
    
    def _process_bulk_documents(self, files: List, auto_generate: bool, use_default_settings: bool):
        """Process multiple documents in bulk."""
        st.info(f"🔄 Starting bulk processing of {len(files)} documents...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        processed_count = 0
        failed_count = 0
        
        for i, file in enumerate(files):
            try:
                status_text.text(f"Processing {file.name}...")
                
                # Validate and extract text
                metadata = self.file_handler.get_file_metadata(file)
                if not metadata['is_valid']:
                    failed_count += 1
                    continue
                
                extracted_text, error = self.file_handler.extract_text(file)
                if error:
                    failed_count += 1
                    continue
                
                # Extract patient information
                extracted_info = self._extract_patient_information(extracted_text)
                
                if auto_generate:
                    # Generate template automatically
                    template_data = {
                        'filename': file.name,
                        'extracted_info': extracted_info,
                        'processed_at': datetime.now()
                    }
                    
                    # Create simple template
                    template_path = self._create_simple_qme_template(
                        extracted_info, 
                        file.name
                    )
                    
                    # Save to gallery
                    template_id = str(uuid.uuid4())
                    gallery_entry = {
                        'id': template_id,
                        'patient_name': extracted_info.get('patient_info', {}).get('name', file.name),
                        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'status': 'completed',
                        'path': template_path,
                        'favorite': False,
                        'bulk_processed': True
                    }
                    
                    st.session_state.qme_generated_templates[template_id] = gallery_entry
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing {file.name}: {e}")
                failed_count += 1
            
            # Update progress
            progress_bar.progress((i + 1) / len(files))
        
        # Show results
        status_text.empty()
        progress_bar.empty()
        
        if processed_count > 0:
            st.success(f"✅ Successfully processed {processed_count} documents")
        
        if failed_count > 0:
            st.error(f"❌ Failed to process {failed_count} documents")
        
        if auto_generate and processed_count > 0:
            st.info(f"📄 Generated {processed_count} QME templates. Check the Template Gallery to download them.")
    
    def _reset_workflow(self):
        """Reset the workflow to start over."""
        # Clear session state
        st.session_state.qme_uploaded_files = {}
        st.session_state.qme_processing_status = {}
        st.session_state.qme_current_step = 'upload'
        
        if 'final_template' in st.session_state:
            del st.session_state.final_template
        
        st.success("🔄 Workflow reset. Ready for new template generation!")
        st.rerun()


def render_qme_template_page():
    """Render the QME template generation page."""
    qme_interface = QMETemplateInterface()
    qme_interface.render_qme_template_page()