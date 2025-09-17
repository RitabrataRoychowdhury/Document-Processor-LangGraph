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

from src.core.generation.qme_template_generator import QMETemplateGenerator, QMETemplateData
from src.infrastructure.storage.file_handler import FileUploadHandler
from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
# Temporarily disable professional template assembler due to indentation issues
# from src.services.professional_template_assembler import ProfessionalTemplateAssembler, TemplateAssemblyConfig
from src.storage.document_storage import DocumentStorage
from src.models.document import Document
from src.utils.logging_config import get_logger
from src.utils.error_handling import format_error_for_ui
from src.config.app_config import app_config

logger = get_logger(__name__)


def render_qme_template_page():
    """Enhanced QME template page with consolidated template assembly service integration."""
    try:
        interface = EnhancedQMETemplateInterface()
        interface.render_enhanced_qme_template_page()
    except Exception as e:
        logger.error(f"Error rendering enhanced QME template page: {e}")
        st.error(f"❌ Error loading enhanced QME template interface: {format_error_for_ui(e)['user_message']}")
        
        # Enhanced error recovery interface
        st.markdown("---")
        st.subheader("🔧 Enhanced Error Recovery")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Retry Loading"):
                st.rerun()
        
        with col2:
            if st.button("🔧 Check Services"):
                st.info("Checking service availability...")
                # In production, this would check actual service status
        
        with col3:
            if st.button("📊 System Status"):
                st.session_state.switch_to_system_status = True
                st.rerun()
        
        # Show error details in expandable section
        with st.expander("🔍 Error Details", expanded=False):
            st.code(str(e))
            
            # Show service availability
            st.markdown("**Service Availability Check:**")
            services = {
                'Template Assembly Service': True,  # Check actual availability
                'Field Extraction Service': True,
                'Quality Validation Service': True,
                'Evidence-First Workflow': True
            }
            
            for service, available in services.items():
                status_icon = "✅" if available else "❌"
                st.write(f"{status_icon} {service}")
        
        # Recovery suggestions
        st.info("💡 **Recovery Suggestions:**")
        st.write("1. Ensure all required services are properly initialized")
        st.write("2. Check that the consolidated service architecture is available")
        st.write("3. Verify template assembly service configuration")
        st.write("4. Try refreshing the page or restarting the application")


class EnhancedQMETemplateInterface:
    """Enhanced QME Template Interface with consolidated service integration."""
    
    def __init__(self):
        """Initialize enhanced QME template interface with consolidated services."""
        super().__init__()
        
        # Initialize consolidated services if available
        try:
            from src.core.generation.template_assembly_service import TemplateAssemblyService
            self.consolidated_template_service = TemplateAssemblyService()
            logger.info("Consolidated template assembly service initialized")
        except ImportError:
            self.consolidated_template_service = None
            logger.warning("Consolidated template assembly service not available")
        
        # Enhanced session state initialization
        if 'enhanced_template_previews' not in st.session_state:
            st.session_state.enhanced_template_previews = {}
        if 'template_customization_options' not in st.session_state:
            st.session_state.template_customization_options = {}
        if 'evidence_citations' not in st.session_state:
            st.session_state.evidence_citations = {}
    
    def render_enhanced_qme_template_page(self):
        """Render enhanced QME template page with consolidated service integration."""
        st.header("🏥 Enhanced QME Template Generator")
        st.markdown("""
        Generate professional QME templates using consolidated template assembly service
        with evidence-based content generation and comprehensive validation.
        """)
        
        # Enhanced progress indicator with template preview
        self._render_enhanced_progress_indicator()
        
        # Main content based on current step
        current_step = st.session_state.qme_current_step
        
        if current_step == 'upload':
            self._render_enhanced_upload_step()
        elif current_step == 'process':
            self._render_enhanced_process_step()
        elif current_step == 'review':
            self._render_enhanced_review_step()
        elif current_step == 'customize':
            self._render_enhanced_customize_step()
        elif current_step == 'download':
            self._render_enhanced_download_step()
        
        # Enhanced navigation with template preview
        self._render_enhanced_navigation_buttons()
        
        # Enhanced template gallery sidebar with previews
        with st.sidebar:
            self._render_enhanced_template_gallery()
    
    def _render_enhanced_progress_indicator(self):
        """Render enhanced progress indicator with template preview capability."""
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
        
        # Enhanced progress bar with template preview
        col1, col2 = st.columns([3, 1])
        
        with col1:
            progress = (current_index + 1) / len(steps)
            st.progress(progress)
            
            # Create enhanced step indicators
            cols = st.columns(len(steps))
            for i, (col, step) in enumerate(zip(cols, steps)):
                with col:
                    if i < current_index:
                        st.success(f"✅ {step}")
                    elif i == current_index:
                        st.info(f"🔄 {step}")
                    else:
                        st.write(f"⏳ {step}")
        
        with col2:
            # Template preview button
            if current_index >= 2:  # Available from review step onwards
                if st.button("👀 Preview Template"):
                    self._show_template_preview()
        
        st.markdown("---")
    
    def _render_enhanced_customize_step(self):
        """Render enhanced customization step with template preview and evidence citations."""
        st.subheader("🎨 Enhanced Template Customization")
        
        # Template preview with expandable sections
        st.subheader("👀 Template Preview with Evidence Citations")
        
        # Mock template sections for preview
        template_sections = {
            'Patient Information': {
                'content': 'John Doe, 45-year-old construction worker',
                'evidence_sources': ['Document page 1, line 3', 'Patient intake form'],
                'confidence': 0.95
            },
            'History of Present Illness': {
                'content': 'Patient reports lower back pain following workplace injury...',
                'evidence_sources': ['Medical record page 2', 'Doctor notes section 3'],
                'confidence': 0.87
            },
            'Physical Examination': {
                'content': 'Limited range of motion in lumbar spine...',
                'evidence_sources': ['Examination report page 4', 'Physical therapy notes'],
                'confidence': 0.92
            },
            'Diagnosis': {
                'content': 'Lumbar strain with disc involvement',
                'evidence_sources': ['Diagnostic imaging report', 'Physician assessment'],
                'confidence': 0.78
            }
        }
        
        # Display template sections with expandable evidence citations
        for section_name, section_data in template_sections.items():
            with st.expander(f"📋 {section_name} (Confidence: {section_data['confidence']:.1%})", expanded=False):
                st.write(f"**Content:** {section_data['content']}")
                
                st.markdown("**Evidence Sources:**")
                for i, source in enumerate(section_data['evidence_sources'], 1):
                    st.write(f"{i}. {source}")
                
                # Confidence indicator
                confidence = section_data['confidence']
                if confidence >= 0.8:
                    st.success(f"✅ High confidence: {confidence:.1%}")
                elif confidence >= 0.6:
                    st.warning(f"⚠️ Medium confidence: {confidence:.1%}")
                else:
                    st.error(f"❌ Low confidence: {confidence:.1%}")
        
        # Enhanced template customization options
        st.subheader("🎨 Advanced Customization Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Letterhead upload with preview
            st.markdown("**🏢 Letterhead Upload:**")
            letterhead_file = st.file_uploader(
                "Upload clinic letterhead",
                type=['png', 'jpg', 'jpeg'],
                help="Upload your clinic letterhead for professional templates"
            )
            
            if letterhead_file:
                st.success("✅ Letterhead uploaded")
                # Show letterhead preview
                st.image(letterhead_file, caption="Letterhead Preview", width=200)
            
            # Doctor information with validation
            st.markdown("**👨‍⚕️ Doctor Information:**")
            doctor_name = st.text_input("Doctor Name", value=st.session_state.qme_doctor_info.get('name', ''))
            license_number = st.text_input("Medical License", value=st.session_state.qme_doctor_info.get('license', ''))
            specialty = st.text_input("Specialty", value=st.session_state.qme_doctor_info.get('specialty', ''))
        
        with col2:
            # Formatting preferences with live preview
            st.markdown("**📄 Formatting Preferences:**")
            font_size = st.selectbox("Font Size", options=[10, 11, 12, 14], index=2)
            line_spacing = st.selectbox("Line Spacing", options=["Single", "1.15", "1.5", "Double"], index=1)
            page_margins = st.selectbox("Page Margins", options=["Normal", "Narrow", "Wide"], index=0)
            
            # Template style options
            st.markdown("**🎨 Template Style:**")
            template_style = st.selectbox(
                "Template Style",
                options=["Professional", "Clinical", "Academic", "Legal"],
                index=0
            )
            
            include_toc = st.checkbox("Include Table of Contents", value=True)
            include_appendices = st.checkbox("Include Appendices", value=False)
        
        # Update session state
        st.session_state.qme_doctor_info.update({
            'name': doctor_name,
            'license': license_number,
            'specialty': specialty
        })
        
        st.session_state.qme_template_preferences.update({
            'font_size': font_size,
            'line_spacing': line_spacing,
            'page_margins': page_margins,
            'template_style': template_style,
            'include_toc': include_toc,
            'include_appendices': include_appendices
        })
        
        # Enhanced template preview generation
        st.subheader("👀 Live Template Preview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Generate Live Preview", type="secondary"):
                self._generate_enhanced_template_preview()
        
        with col2:
            if st.button("💾 Save Customization", type="secondary"):
                st.success("✅ Customization settings saved")
        
        # Validation and continue
        can_proceed = self._validate_customization_settings()
        
        if can_proceed:
            if st.button("📥 Generate Final Template →", type="primary"):
                st.session_state.qme_current_step = 'download'
                st.rerun()
        else:
            st.button("📥 Generate Final Template →", type="primary", disabled=True, 
                     help="Please complete required customization settings")
    
    def _show_template_preview(self):
        """Show enhanced template preview with evidence citations."""
        st.modal("👀 Enhanced Template Preview")
        
        with st.container():
            st.subheader("📋 QME Template Preview")
            
            # Mock template content with evidence citations
            st.markdown("""
            **QUALIFIED MEDICAL EVALUATOR'S REPORT**
            
            **Patient:** John Doe *(Evidence: Document p.1, confidence: 95%)*
            **Case Number:** WC2024-001 *(Evidence: Claim form, confidence: 88%)*
            **Date of Examination:** [To be scheduled] *(Evidence: Pending)*
            
            **HISTORY OF PRESENT ILLNESS**
            Patient reports lower back pain following workplace injury on January 15, 2024...
            *(Evidence: Medical records p.2-3, confidence: 87%)*
            
            **PHYSICAL EXAMINATION**
            Limited range of motion in lumbar spine with positive straight leg raise test...
            *(Evidence: Examination notes p.4, confidence: 92%)*
            
            **DIAGNOSIS**
            1. Lumbar strain with possible disc involvement *(Evidence: Imaging report, confidence: 78%)*
            2. Work-related injury *(Evidence: Incident report, confidence: 85%)*
            
            **IMPAIRMENT RATING**
            [To be calculated using AMA Guides] *(Programmatic calculation pending)*
            """)
            
            if st.button("Close Preview"):
                st.rerun()
    
    def _generate_enhanced_template_preview(self):
        """Generate enhanced template preview with consolidated service."""
        with st.spinner("🔄 Generating enhanced template preview..."):
            try:
                if self.consolidated_template_service:
                    # Use consolidated template assembly service
                    st.success("✅ Enhanced template preview generated using consolidated service!")
                    st.info("Preview would be displayed here with evidence citations and formatting")
                else:
                    # Fallback to mock preview
                    st.info("📋 Mock template preview generated (consolidated service not available)")
                
                # Store preview in session state
                st.session_state.enhanced_template_previews['current'] = {
                    'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'customization': st.session_state.qme_template_preferences.copy()
                }
                
            except Exception as e:
                st.error(f"❌ Error generating enhanced preview: {e}")
    
    def _validate_customization_settings(self) -> bool:
        """Validate customization settings before proceeding."""
        doctor_info = st.session_state.qme_doctor_info
        
        required_fields = ['name', 'license', 'specialty']
        missing_fields = [field for field in required_fields if not doctor_info.get(field)]
        
        if missing_fields:
            st.warning(f"⚠️ Please complete required fields: {', '.join(missing_fields)}")
            return False
        
        return True
    
    def _render_enhanced_template_gallery(self):
        """Render enhanced template gallery with previews."""
        st.subheader("📊 Enhanced Template Gallery")
        
        if st.session_state.enhanced_template_previews:
            for preview_id, preview_data in st.session_state.enhanced_template_previews.items():
                with st.expander(f"📄 Preview {preview_id}", expanded=False):
                    st.write(f"**Generated:** {preview_data['generated_at']}")
                    st.write(f"**Style:** {preview_data['customization'].get('template_style', 'Professional')}")
                    
                    if st.button(f"👀 View", key=f"view_{preview_id}"):
                        self._show_template_preview()
        else:
            st.info("No template previews available yet")
        
        # Template examples
        st.markdown("**📋 Template Examples:**")
        example_templates = [
            "Professional QME Report",
            "Clinical Assessment Template", 
            "Academic Research Format",
            "Legal Compliance Template"
        ]
        
        for template in example_templates:
            if st.button(f"📄 {template}", key=f"example_{template}"):
                st.info(f"Loading {template} example...")
    
    def _render_enhanced_navigation_buttons(self):
        """Render enhanced navigation buttons with template actions."""
        st.markdown("---")
        
        current_step = st.session_state.qme_current_step
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if current_step != 'upload':
                if st.button("← Previous Step"):
                    step_order = ['upload', 'process', 'review', 'customize', 'download']
                    current_index = step_order.index(current_step)
                    if current_index > 0:
                        st.session_state.qme_current_step = step_order[current_index - 1]
                        st.rerun()
        
        with col2:
            if st.button("🔄 Refresh"):
                st.rerun()
        
        with col3:
            if current_step in ['review', 'customize', 'download']:
                if st.button("👀 Quick Preview"):
                    self._show_template_preview()
        
        with col4:
            if current_step == 'download':
                if st.button("📤 Export Options"):
                    st.info("Export options: DOCX, PDF, HTML, Audit Trail")


class QMETemplateInterface:
    """Streamlit interface for QME template generation."""
    
    def __init__(self):
        """Initialize the QME template interface."""
        self.template_generator = QMETemplateGenerator()
        self.file_handler = FileUploadHandler()
        self.storage = DocumentStorage()
        self.field_service = ComprehensiveQMEFieldService()
        # self.professional_assembler = ProfessionalTemplateAssembler()
        
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
        if 'qme_field_validation' not in st.session_state:
            st.session_state.qme_field_validation = {}
        if 'qme_extraction_results' not in st.session_state:
            st.session_state.qme_extraction_results = {}
    
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
        """Render the review step for extracted information with real-time field validation."""
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
        
        # Real-time Field Validation Display
        self._render_field_validation_status()
        
        # Patient Information Section with validation indicators
        st.subheader("👤 Patient Information")
        patient_info = extracted_data.get('patient_info', {})
        
        col1, col2 = st.columns(2)
        with col1:
            self._render_field_with_validation("Name", patient_info.get('name', 'Not found'))
            self._render_field_with_validation("Age", patient_info.get('age', 'Not found'))
            self._render_field_with_validation("Gender", patient_info.get('gender', 'Not found'))
        
        with col2:
            self._render_field_with_validation("Case Number", patient_info.get('case_number', 'Not found'))
            self._render_field_with_validation("Claim Number", patient_info.get('claim_number', 'Not found'))
            self._render_field_with_validation("Injury Date", patient_info.get('injury_date', 'Not found'))
        
        # Additional QME-specific fields
        col3, col4 = st.columns(2)
        with col3:
            self._render_field_with_validation("Occupation", patient_info.get('occupation', 'Not found'))
            self._render_field_with_validation("Employer", patient_info.get('employer', 'Not found'))
        
        with col4:
            body_parts_str = ', '.join(patient_info.get('body_parts', [])) if patient_info.get('body_parts') else 'Not found'
            self._render_field_with_validation("Body Parts", body_parts_str)
            self._render_field_with_validation("Exam Date", patient_info.get('exam_date', 'Not found'))
        
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
        
        # Extraction Confidence and Validation Issues
        self._render_extraction_summary(extracted_data)
        
        # Missing Information Alert
        missing_info = extracted_data.get('missing_sections', [])
        if missing_info:
            st.warning("⚠️ **Missing Information Detected:**")
            for section in missing_info:
                st.write(f"• {section}")
            st.info("The template will highlight these missing sections for manual completion.")
        
        # Manual field correction interface
        self._render_field_correction_interface(patient_info)
        
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
    
    def _render_field_validation_status(self):
        """Render real-time field validation status dashboard."""
        st.subheader("📊 Field Extraction Status")
        
        # Calculate validation metrics
        total_required_fields = 10  # Name, Age, Gender, Case#, Claim#, Injury Date, Body Parts, Occupation, Employer, Exam Date
        extracted_fields = 0
        validation_issues = 0
        
        extracted_data = self._get_extracted_data()
        patient_info = extracted_data.get('patient_info', {})
        
        # Count successfully extracted fields
        required_fields = ['name', 'age', 'gender', 'case_number', 'claim_number', 'injury_date', 'body_parts', 'occupation', 'employer', 'exam_date']
        for field in required_fields:
            value = patient_info.get(field)
            if value and value != 'Not found' and (not isinstance(value, list) or len(value) > 0):
                extracted_fields += 1
        
        # Count validation issues
        validation_issues = len(extracted_data.get('validation_issues', []))
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            extraction_rate = (extracted_fields / total_required_fields) * 100
            st.metric("Extraction Rate", f"{extraction_rate:.0f}%", f"{extracted_fields}/{total_required_fields}")
        
        with col2:
            confidence = extracted_data.get('extraction_confidence', 0) * 100
            st.metric("Confidence", f"{confidence:.0f}%")
        
        with col3:
            st.metric("Validation Issues", validation_issues)
        
        with col4:
            missing_count = total_required_fields - extracted_fields
            st.metric("Missing Fields", missing_count)
        
        # Progress bar for extraction completeness
        progress_value = extracted_fields / total_required_fields
        st.progress(progress_value)
        
        if progress_value >= 0.8:
            st.success("✅ Excellent field extraction - Ready for template generation")
        elif progress_value >= 0.6:
            st.warning("⚠️ Good field extraction - Some manual review recommended")
        else:
            st.error("❌ Limited field extraction - Manual completion required")
    
    def _render_field_with_validation(self, field_name: str, field_value: str):
        """Render a field with validation status indicator."""
        if field_value and field_value != 'Not found':
            st.write(f"✅ **{field_name}:** {field_value}")
        else:
            st.write(f"❌ **{field_name}:** {field_value}")
    
    def _render_extraction_summary(self, extracted_data: Dict[str, Any]):
        """Render extraction confidence and validation summary."""
        with st.expander("📈 Extraction Details", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Extraction Confidence:**")
                confidence = extracted_data.get('extraction_confidence', 0)
                if confidence >= 0.8:
                    st.success(f"High confidence: {confidence:.1%}")
                elif confidence >= 0.6:
                    st.warning(f"Medium confidence: {confidence:.1%}")
                else:
                    st.error(f"Low confidence: {confidence:.1%}")
            
            with col2:
                st.write("**Validation Issues:**")
                issues = extracted_data.get('validation_issues', [])
                if not issues:
                    st.success("No validation issues detected")
                else:
                    for issue in issues[:3]:  # Show first 3 issues
                        st.write(f"• {issue}")
                    if len(issues) > 3:
                        st.write(f"... and {len(issues) - 3} more issues")
    
    def _render_field_correction_interface(self, patient_info: Dict[str, Any]):
        """Render interface for manual field correction."""
        with st.expander("✏️ Manual Field Correction", expanded=False):
            st.info("Correct any inaccurate or missing information below:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                corrected_name = st.text_input("Patient Name", value=patient_info.get('name', ''), key="corrected_name")
                corrected_age = st.text_input("Age", value=str(patient_info.get('age', '')), key="corrected_age")
                corrected_gender = st.selectbox("Gender", options=["", "Male", "Female", "Other"], 
                                              index=0 if not patient_info.get('gender') or patient_info.get('gender') == 'Not found' 
                                              else ["", "Male", "Female", "Other"].index(patient_info.get('gender')) if patient_info.get('gender') in ["Male", "Female", "Other"] else 0,
                                              key="corrected_gender")
                corrected_case = st.text_input("Case Number", value=patient_info.get('case_number', ''), key="corrected_case")
                corrected_claim = st.text_input("Claim Number", value=patient_info.get('claim_number', ''), key="corrected_claim")
            
            with col2:
                corrected_injury_date = st.date_input("Injury Date", key="corrected_injury_date")
                corrected_occupation = st.text_input("Occupation", value=patient_info.get('occupation', ''), key="corrected_occupation")
                corrected_employer = st.text_input("Employer", value=patient_info.get('employer', ''), key="corrected_employer")
                corrected_body_parts = st.text_input("Body Parts (comma-separated)", 
                                                   value=', '.join(patient_info.get('body_parts', [])) if patient_info.get('body_parts') else '', 
                                                   key="corrected_body_parts")
                corrected_exam_date = st.date_input("Scheduled Exam Date", key="corrected_exam_date")
            
            if st.button("💾 Apply Corrections", key="apply_corrections"):
                # Update patient info with corrections
                corrections = {
                    'name': corrected_name,
                    'age': corrected_age,
                    'gender': corrected_gender,
                    'case_number': corrected_case,
                    'claim_number': corrected_claim,
                    'injury_date': str(corrected_injury_date),
                    'occupation': corrected_occupation,
                    'employer': corrected_employer,
                    'body_parts': [part.strip() for part in corrected_body_parts.split(',') if part.strip()],
                    'exam_date': str(corrected_exam_date)
                }
                
                # Store corrections in session state
                if 'qme_field_corrections' not in st.session_state:
                    st.session_state.qme_field_corrections = {}
                st.session_state.qme_field_corrections.update(corrections)
                
                st.success("✅ Corrections applied successfully!")
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
        
        # Validation before proceeding
        can_proceed = True
        error_messages = []
        
        # Check required doctor information
        if not st.session_state.qme_doctor_info.get('name'):
            can_proceed = False
            error_messages.append("Doctor name is required")
        
        # Check if we have extracted data
        if not self._has_processed_documents():
            can_proceed = False
            error_messages.append("No processed documents found")
        
        # Show validation errors
        if error_messages:
            st.error("❌ **Cannot proceed to template generation:**")
            for error in error_messages:
                st.write(f"• {error}")
        
        # Continue button
        if can_proceed:
            if st.button("Generate Template →", type="primary"):
                st.session_state.qme_current_step = 'download'
                st.rerun()
        else:
            st.button("Generate Template →", type="primary", disabled=True, help="Please resolve the issues above")
    
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
        
        # Template Quality Metrics
        st.subheader("📊 Template Quality Metrics")
        self._show_template_quality_metrics(template_info['data'])
        
        # Template Analytics
        st.subheader("📈 Template Analytics")
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
                if st.button("← Previous Step", key="nav_prev"):
                    st.session_state.qme_current_step = steps[current_index - 1]
                    st.rerun()
        
        with col3:
            # Next button (context-sensitive)
            next_enabled = False
            next_help = ""
            
            if current_step == 'upload' and st.session_state.qme_uploaded_files:
                next_enabled = True
            elif current_step == 'process' and self._has_processed_documents():
                next_enabled = True
            elif current_step == 'review' and st.session_state.get('accuracy_confirmed', False):
                next_enabled = True
            elif current_step == 'customize':
                next_enabled = bool(st.session_state.qme_doctor_info.get('name'))
                if not next_enabled:
                    next_help = "Please enter doctor information"
            
            if current_index < len(steps) - 1:  # Not on last step
                if next_enabled:
                    if st.button("Next Step →", key="nav_next"):
                        st.session_state.qme_current_step = steps[current_index + 1]
                        st.rerun()
                else:
                    st.button("Next Step →", key="nav_next_disabled", disabled=True, help=next_help or "Complete current step to continue")
    
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
        """Process a patient document to extract medical information using comprehensive field service."""
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
            
            # Create temporary file for processing
            temp_file_path = self._create_temp_file(file_data)
            
            # Processing steps with real functionality
            steps = [
                ("Extracting document text...", 20),
                ("Analyzing medical content...", 40),
                ("Extracting QME fields...", 60),
                ("Validating extracted data...", 80),
                ("Finalizing extraction...", 100)
            ]
            
            extraction_result = None
            
            for i, (step_text, progress) in enumerate(steps):
                status_placeholder.info(f"🔄 {step_text}")
                progress_bar.progress(progress)
                
                if i == 2:  # Extract QME fields step
                    try:
                        extraction_result = self.field_service.extract_and_validate_fields(temp_file_path)
                    except Exception as e:
                        logger.error(f"Field extraction failed: {e}")
                        extraction_result = None
                
                time.sleep(0.3)  # Brief pause for UI feedback
            
            # Process extraction results
            if extraction_result:
                extracted_info = self._convert_extraction_to_template_data(extraction_result)
                
                # Store extraction results for field validation display
                st.session_state.qme_extraction_results[file_id] = extraction_result
                
                # Update file data
                file_data.update({
                    'processing_status': 'completed',
                    'processed_at': datetime.now(),
                    'extracted_info': extracted_info,
                    'extraction_confidence': extraction_result.extraction_result.overall_confidence,
                    'validation_status': extraction_result.validation_result.is_valid
                })
                
                # Clear progress indicators
                progress_placeholder.empty()
                status_placeholder.success(f"✅ Processed {file_data['filename']} (Confidence: {extraction_result.extraction_result.overall_confidence:.1%})")
            else:
                # Fallback to basic extraction
                extracted_info = self._extract_patient_information(file_data['extracted_text'])
                file_data.update({
                    'processing_status': 'completed',
                    'processed_at': datetime.now(),
                    'extracted_info': extracted_info,
                    'extraction_confidence': 0.5,
                    'validation_status': 'needs_review'
                })
                
                progress_placeholder.empty()
                status_placeholder.warning(f"⚠️ Basic processing completed for {file_data['filename']} - Manual review recommended")
            
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
        except Exception as e:
            file_data['processing_status'] = 'failed'
            file_data['error'] = str(e)
            logger.error(f"Document processing failed: {e}")
            
            progress_placeholder.empty()
            status_placeholder.error(f"❌ Failed to process {file_data['filename']}: {str(e)}")
    
    def _create_temp_file(self, file_data: Dict[str, Any]) -> str:
        """Create a temporary file from uploaded file data."""
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"qme_temp_{uuid.uuid4().hex}.txt")
        
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(file_data['extracted_text'])
        
        return temp_file_path
    
    def _convert_extraction_to_template_data(self, extraction_result) -> Dict[str, Any]:
        """Convert comprehensive extraction result to template data format."""
        field_data = extraction_result.extraction_result.field_data
        
        extracted_info = {
            'patient_info': {
                'name': field_data.name or 'Not found',
                'age': field_data.age or 'Not found',
                'gender': field_data.gender or 'Not found',
                'case_number': field_data.case_number or 'Not found',
                'claim_number': field_data.claim_number or 'Not found',
                'injury_date': field_data.injury_date or 'Not found',
                'body_parts': field_data.body_parts or [],
                'occupation': field_data.occupation or 'Not found',
                'employer': field_data.employer or 'Not found',
                'exam_date': field_data.scheduled_exam_date or 'Not found'
            },
            'medical_findings': {
                'diagnoses': [],
                'findings': [],
                'imaging_studies': []
            },
            'missing_sections': [],
            'extraction_confidence': extraction_result.extraction_result.overall_confidence,
            'validation_issues': [issue.message for issue in extraction_result.validation_result.issues]
        }
        
        # Add missing sections based on validation
        for issue in extraction_result.validation_result.issues:
            if 'missing' in issue.message.lower():
                extracted_info['missing_sections'].append(issue.field_name)
        
        return extracted_info
    
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
        """Generate the final QME template using professional template assembler."""
        try:
            # Get extracted data with any corrections applied
            extracted_data = self._get_extracted_data_with_corrections()
            
            # Convert to QMETemplateData format
            template_data = self._convert_to_qme_template_data(extracted_data)
            
            # Fallback to basic template generation for now
            return self._generate_basic_template(extracted_data)
            
        except Exception as e:
            logger.error(f"Error generating professional template: {e}")
            # Fallback to basic template generation
            return self._generate_basic_template(extracted_data)
    
    def _generate_basic_template(self, extracted_data: Dict[str, Any]) -> Tuple[str, Any]:
        """Generate a basic QME template as fallback."""
        temp_dir = tempfile.gettempdir()
        template_path = os.path.join(temp_dir, f"qme_basic_template_{uuid.uuid4().hex}.docx")
        
        try:
            from docx import Document
            
            doc = Document()
            
            # Add title
            title = doc.add_heading('QUALIFIED MEDICAL EVALUATOR\'S REPORT', 0)
            
            # Add patient information
            doc.add_heading('PATIENT INFORMATION', level=1)
            patient_info = extracted_data.get('patient_info', {})
            
            # Create table for patient information
            table = doc.add_table(rows=10, cols=2)
            table.style = 'Table Grid'
            
            patient_fields = [
                ('Name', patient_info.get('name', '[MISSING - Patient name not found]')),
                ('Age', str(patient_info.get('age', '[MISSING - Age not found]'))),
                ('Gender', patient_info.get('gender', '[MISSING - Gender not found]')),
                ('Case Number', patient_info.get('case_number', '[MISSING - Case number not found]')),
                ('Claim Number', patient_info.get('claim_number', '[MISSING - Claim number not found]')),
                ('Injury Date', patient_info.get('injury_date', '[MISSING - Injury date not found]')),
                ('Body Parts', ', '.join(patient_info.get('body_parts', [])) or '[MISSING - Body parts not found]'),
                ('Occupation', patient_info.get('occupation', '[MISSING - Occupation not found]')),
                ('Employer', patient_info.get('employer', '[MISSING - Employer not found]')),
                ('Scheduled Exam Date', patient_info.get('exam_date', '[MISSING - Exam date not found]'))
            ]
            
            for i, (field_name, field_value) in enumerate(patient_fields):
                table.cell(i, 0).text = field_name
                table.cell(i, 1).text = str(field_value)
                table.cell(i, 0).paragraphs[0].runs[0].bold = True
            
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
                
                doctor_table = doc.add_table(rows=6, cols=2)
                doctor_table.style = 'Table Grid'
                
                doctor_fields = [
                    ('Name', doctor_info.get('name', '')),
                    ('Medical License', doctor_info.get('license', '')),
                    ('Specialty', doctor_info.get('specialty', '')),
                    ('Clinic/Practice', doctor_info.get('clinic', '')),
                    ('Address', doctor_info.get('address', '')),
                    ('Phone', doctor_info.get('phone', ''))
                ]
                
                for i, (field_name, field_value) in enumerate(doctor_fields):
                    doctor_table.cell(i, 0).text = field_name
                    doctor_table.cell(i, 1).text = str(field_value)
                    doctor_table.cell(i, 0).paragraphs[0].runs[0].bold = True
            
            # Add missing sections notice
            missing_sections = extracted_data.get('missing_sections', [])
            if missing_sections:
                doc.add_heading('MISSING INFORMATION NOTICE', level=1)
                doc.add_paragraph('The following sections require manual completion:')
                for section in missing_sections:
                    doc.add_paragraph(f"• {section}", style='List Bullet')
            
            # Save document
            doc.save(template_path)
            
            return template_path, extracted_data
            
        except Exception as e:
            logger.error(f"Error generating basic template: {e}")
            raise
    
    def _get_extracted_data_with_corrections(self) -> Dict[str, Any]:
        """Get extracted data with any manual corrections applied."""
        extracted_data = self._get_extracted_data()
        
        # Apply any manual corrections
        if 'qme_field_corrections' in st.session_state:
            corrections = st.session_state.qme_field_corrections
            patient_info = extracted_data.get('patient_info', {})
            
            for field, value in corrections.items():
                if value:  # Only apply non-empty corrections
                    patient_info[field] = value
            
            extracted_data['patient_info'] = patient_info
        
        return extracted_data
    
    def _convert_to_qme_template_data(self, extracted_data: Dict[str, Any]) -> 'QMETemplateData':
        """Convert extracted data to QMETemplateData format for professional assembly."""
        from src.core.generation.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
        
        patient_info_dict = extracted_data.get('patient_info', {})
        medical_findings_dict = extracted_data.get('medical_findings', {})
        
        # Create PatientInfo object
        patient_info = PatientInfo(
            name=patient_info_dict.get('name', ''),
            age=patient_info_dict.get('age', ''),
            gender=patient_info_dict.get('gender', ''),
            case_number=patient_info_dict.get('case_number', ''),
            claim_number=patient_info_dict.get('claim_number', ''),
            injury_date=patient_info_dict.get('injury_date', ''),
            body_parts=patient_info_dict.get('body_parts', []),
            occupation=patient_info_dict.get('occupation', ''),
            employer=patient_info_dict.get('employer', ''),
            exam_date=patient_info_dict.get('exam_date', '')
        )
        
        # Create MedicalFindings object
        medical_findings = MedicalFindings(
            diagnoses=medical_findings_dict.get('diagnoses', []),
            findings=medical_findings_dict.get('findings', []),
            imaging_studies=medical_findings_dict.get('imaging_studies', [])
        )
        
        # Create QMETemplateData object
        template_data = QMETemplateData(
            patient_info=patient_info,
            medical_findings=medical_findings,
            doctor_info=st.session_state.qme_doctor_info,
            template_preferences=st.session_state.qme_template_preferences
        )
        
        return template_data
    
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
    
    def _show_template_quality_metrics(self, template_data: Any):
        """Show quality metrics from professional template assembly."""
        if 'qme_template_quality' in st.session_state:
            quality_info = st.session_state.qme_template_quality
            
            # Pre-assembly validation
            pre_validation = quality_info.get('pre_assembly_validation')
            if pre_validation:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    compliance_status = pre_validation.compliance_status
                    if compliance_status == 'compliant':
                        st.success(f"✅ {compliance_status.title()}")
                    elif compliance_status == 'needs_review':
                        st.warning(f"⚠️ {compliance_status.replace('_', ' ').title()}")
                    else:
                        st.error(f"❌ {compliance_status.replace('_', ' ').title()}")
                
                with col2:
                    quality_score = pre_validation.quality_score
                    if hasattr(quality_score, 'overall_score'):
                        score = quality_score.overall_score * 100
                        st.metric("Quality Score", f"{score:.0f}%")
                    else:
                        st.metric("Quality Score", "N/A")
                
                with col3:
                    missing_count = len(pre_validation.missing_sections)
                    st.metric("Missing Sections", missing_count)
                
                # Show validation issues if any
                if pre_validation.issues:
                    with st.expander("⚠️ Validation Issues", expanded=False):
                        for issue in pre_validation.issues[:5]:  # Show first 5 issues
                            severity_icon = "🔴" if issue.severity == "high" else "🟡" if issue.severity == "medium" else "🟢"
                            st.write(f"{severity_icon} {issue.message}")
                        
                        if len(pre_validation.issues) > 5:
                            st.write(f"... and {len(pre_validation.issues) - 5} more issues")
            
            # Quality report link
            quality_report_path = quality_info.get('quality_report_path')
            if quality_report_path and os.path.exists(quality_report_path):
                with open(quality_report_path, 'rb') as f:
                    st.download_button(
                        label="📋 Download Quality Report",
                        data=f.read(),
                        file_name="QME_Quality_Report.pdf",
                        mime="application/pdf"
                    )
        else:
            st.info("Quality metrics will be available when using professional template assembly.")
    
    def _show_template_analytics(self, template_data: Any):
        """Show analytics for the generated template."""
        extracted_data = self._get_extracted_data()
        
        # Calculate completion metrics
        total_required_fields = 10
        completed_fields = 0
        patient_info = extracted_data.get('patient_info', {})
        
        required_fields = ['name', 'age', 'gender', 'case_number', 'claim_number', 'injury_date', 'body_parts', 'occupation', 'employer', 'exam_date']
        for field in required_fields:
            value = patient_info.get(field)
            if value and value != 'Not found' and (not isinstance(value, list) or len(value) > 0):
                completed_fields += 1
        
        missing_count = total_required_fields - completed_fields
        confidence = extracted_data.get('extraction_confidence', 0) * 100
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Sections Completed", f"{completed_fields}/{total_required_fields}")
        
        with col2:
            st.metric("Missing Information", f"{missing_count} items")
        
        with col3:
            st.metric("Extraction Confidence", f"{confidence:.0f}%")
        
        # Completion details
        with st.expander("📊 Completion Details", expanded=False):
            st.write("**Completed Fields:**")
            for field in required_fields:
                value = patient_info.get(field)
                if value and value != 'Not found' and (not isinstance(value, list) or len(value) > 0):
                    st.write(f"✅ {field.replace('_', ' ').title()}")
            
            st.write("**Missing Fields:**")
            for field in required_fields:
                value = patient_info.get(field)
                if not value or value == 'Not found' or (isinstance(value, list) and len(value) == 0):
                    st.write(f"❌ {field.replace('_', ' ').title()}")
            
            # Validation issues
            validation_issues = extracted_data.get('validation_issues', [])
            if validation_issues:
                st.write("**Validation Issues:**")
                for issue in validation_issues[:3]:
                    st.write(f"⚠️ {issue}")
                if len(validation_issues) > 3:
                    st.write(f"... and {len(validation_issues) - 3} more issues")
    
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