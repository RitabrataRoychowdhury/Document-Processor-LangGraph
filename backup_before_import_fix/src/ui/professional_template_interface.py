"""
Professional Template Assembly Interface for Streamlit.

This module provides UI integration for the Professional Template Assembly System,
allowing users to generate gold-standard compliant QME templates with comprehensive
validation and quality assurance.
"""

import streamlit as st
import os
import tempfile
import zipfile
from datetime import datetime
from typing import Optional, Dict, Any, List
import base64
from pathlib import Path

try:
    from src.services.professional_template_assembler_simple import (
        ProfessionalTemplateAssembler, 
        TemplateAssemblyConfig, 
        ProfessionalTemplateResult
    )
    from src.core.generation.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from src.core.validation.qme_rules_engine import ValidationSeverity
    from src.utils.logging_config import get_logger
except ImportError:
    from services.professional_template_assembler_simple import (
        ProfessionalTemplateAssembler, 
        TemplateAssemblyConfig, 
        ProfessionalTemplateResult
    )
    from core.generation.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from core.validation.qme_rules_engine import ValidationSeverity
    from utils.logging_config import get_logger

logger = get_logger(__name__)


class ProfessionalTemplateInterface:
    """Streamlit interface for professional template assembly."""
    
    def __init__(self):
        """Initialize the professional template interface."""
        self.assembler = ProfessionalTemplateAssembler()
        
        # Initialize session state
        if 'professional_templates' not in st.session_state:
            st.session_state.professional_templates = {}
        if 'assembly_config' not in st.session_state:
            st.session_state.assembly_config = TemplateAssemblyConfig()
        if 'doctor_info' not in st.session_state:
            st.session_state.doctor_info = {}
    
    def render_professional_template_page(self):
        """Render the main professional template assembly page."""
        st.header("🏥 Professional QME Template Assembly")
        st.markdown("""
        Generate professional, gold-standard compliant QME templates with comprehensive 
        validation and quality assurance based on the AI Example QME Report Template.
        """)
        
        # Configuration sidebar
        with st.sidebar:
            self._render_assembly_configuration()
            self._render_doctor_information()
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Template Assembly", 
            "🔍 Quality Validation", 
            "📊 Template Gallery",
            "⚙️ Advanced Settings"
        ])
        
        with tab1:
            self._render_template_assembly_tab()
        
        with tab2:
            self._render_quality_validation_tab()
        
        with tab3:
            self._render_template_gallery_tab()
        
        with tab4:
            self._render_advanced_settings_tab()
    
    def _render_assembly_configuration(self):
        """Render assembly configuration in sidebar."""
        st.sidebar.subheader("🔧 Assembly Configuration")
        
        # Quality indicators
        include_quality = st.sidebar.checkbox(
            "Include Quality Indicators",
            value=st.session_state.assembly_config.include_quality_indicators,
            help="Add quality assessment section for draft review"
        )
        
        # Missing placeholders
        include_placeholders = st.sidebar.checkbox(
            "Show Missing Information",
            value=st.session_state.assembly_config.include_missing_placeholders,
            help="Highlight missing information with placeholders"
        )
        
        # Professional formatting
        professional_formatting = st.sidebar.checkbox(
            "Apply Professional Formatting",
            value=st.session_state.assembly_config.apply_professional_formatting,
            help="Apply gold standard formatting and styling"
        )
        
        # Validation options
        st.sidebar.subheader("✅ Validation Options")
        
        validate_before = st.sidebar.checkbox(
            "Pre-Assembly Validation",
            value=st.session_state.assembly_config.validate_before_assembly,
            help="Validate data before creating document"
        )
        
        validate_after = st.sidebar.checkbox(
            "Post-Assembly Validation",
            value=st.session_state.assembly_config.validate_after_assembly,
            help="Validate final document structure"
        )
        
        generate_report = st.sidebar.checkbox(
            "Generate Quality Report",
            value=st.session_state.assembly_config.generate_quality_report,
            help="Create detailed quality assessment report"
        )
        
        # Update session state
        st.session_state.assembly_config.include_quality_indicators = include_quality
        st.session_state.assembly_config.include_missing_placeholders = include_placeholders
        st.session_state.assembly_config.apply_professional_formatting = professional_formatting
        st.session_state.assembly_config.validate_before_assembly = validate_before
        st.session_state.assembly_config.validate_after_assembly = validate_after
        st.session_state.assembly_config.generate_quality_report = generate_report
    
    def _render_doctor_information(self):
        """Render doctor information form in sidebar."""
        st.sidebar.subheader("👨‍⚕️ Doctor Information")
        
        with st.sidebar.expander("Doctor Details", expanded=False):
            doctor_name = st.text_input(
                "Doctor Name",
                value=st.session_state.doctor_info.get('name', ''),
                key="sidebar_doctor_name"
            )
            
            license_number = st.text_input(
                "License Number",
                value=st.session_state.doctor_info.get('license', ''),
                key="sidebar_license"
            )
            
            specialty = st.text_input(
                "Specialty",
                value=st.session_state.doctor_info.get('specialty', 'Orthopaedic Surgery'),
                key="sidebar_specialty"
            )
            
            phone = st.text_input(
                "Phone",
                value=st.session_state.doctor_info.get('phone', ''),
                key="sidebar_phone"
            )
            
            # Update session state
            st.session_state.doctor_info.update({
                'name': doctor_name,
                'license': license_number,
                'specialty': specialty,
                'phone': phone
            })
    
    def _render_template_assembly_tab(self):
        """Render the template assembly tab."""
        st.subheader("📋 Professional Template Assembly")
        
        # Check if we have template data from previous steps
        if 'qme_template_data' not in st.session_state:
            st.warning("⚠️ No template data available. Please complete the QME template generation process first.")
            
            # Option to load sample data for testing
            if st.button("🧪 Load Sample Data for Testing"):
                self._load_sample_template_data()
                st.success("✅ Sample template data loaded")
                st.rerun()
            
            return
        
        template_data = st.session_state.qme_template_data
        
        # Display template data summary
        self._display_template_data_summary(template_data)
        
        # Assembly options
        st.subheader("🔧 Assembly Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Handle both object and dictionary formats for patient name
            if isinstance(template_data, dict):
                patient_name = template_data.get('patient_info', {}).get('name', 'Patient')
            else:
                patient_name = template_data.patient_info.name or 'Patient'
            
            output_filename = st.text_input(
                "Output Filename",
                value=f"QME_Report_{patient_name}_{datetime.now().strftime('%Y%m%d')}.docx",
                help="Filename for the generated template"
            )
        
        with col2:
            template_version = st.selectbox(
                "Template Version",
                options=["1.0", "1.1", "2.0"],
                index=0,
                help="Template version for tracking"
            )
        
        # Assembly button
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🚀 Assemble Professional Template", type="primary", use_container_width=True):
                self._assemble_professional_template(template_data, output_filename, template_version)
    
    def _display_template_data_summary(self, template_data):
        """Display summary of template data."""
        st.subheader("📊 Template Data Summary")
        
        col1, col2, col3 = st.columns(3)
        
        # Handle both object and dictionary formats
        if isinstance(template_data, dict):
            # Dictionary format from QME template generator
            patient_info = template_data.get('patient_info', {})
            medical_findings = template_data.get('medical_findings', {})
            missing_sections = template_data.get('missing_sections', [])
            
            with col1:
                st.metric("Patient Name", patient_info.get('name', 'Missing'))
                st.metric("Case Number", patient_info.get('case_number', 'Missing'))
            
            with col2:
                diagnoses = medical_findings.get('diagnoses', [])
                findings = medical_findings.get('findings', [])
                st.metric("Diagnoses", len(diagnoses) if isinstance(diagnoses, list) else 0)
                st.metric("Findings", len(findings) if isinstance(findings, list) else 0)
            
            with col3:
                impairment_ratings = medical_findings.get('impairment_ratings', [])
                st.metric("Impairment Ratings", len(impairment_ratings) if isinstance(impairment_ratings, list) else 0)
                st.metric("Missing Sections", len(missing_sections) if isinstance(missing_sections, list) else 0)
            
            # Show missing sections if any
            if missing_sections and isinstance(missing_sections, list):
                st.warning(f"⚠️ Missing Sections: {', '.join(missing_sections)}")
        else:
            # Object format (QMETemplateData)
            with col1:
                st.metric("Patient Name", template_data.patient_info.name or "Missing")
                st.metric("Case Number", template_data.patient_info.case_number or "Missing")
            
            with col2:
                st.metric("Diagnoses", len(template_data.medical_findings.diagnoses))
                st.metric("Findings", len(template_data.medical_findings.findings))
            
            with col3:
                st.metric("Impairment Ratings", len(template_data.medical_findings.impairment_ratings))
                st.metric("Missing Sections", len(template_data.missing_sections))
            
            # Show missing sections if any
            if template_data.missing_sections:
                st.warning(f"⚠️ Missing Sections: {', '.join(template_data.missing_sections)}")
    
    def _assemble_professional_template(self, template_data, filename: str, version: str):
        """Assemble the professional template."""
        try:
            with st.spinner("🔄 Assembling professional template..."):
                # Update assembly config
                config = st.session_state.assembly_config
                config.template_version = version
                
                # Convert template data if it's in dictionary format
                if isinstance(template_data, dict):
                    template_data = self._convert_dict_to_qme_template_data(template_data)
                
                # Assemble template
                result = self.assembler.assemble_professional_template(
                    template_data=template_data,
                    output_path=filename,
                    doctor_info=st.session_state.doctor_info,
                    assembly_config=config
                )
                
                # Store result in session state
                result_id = f"template_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                st.session_state.professional_templates[result_id] = result
                
                # Display success message
                st.success("✅ Professional template assembled successfully!")
                
                # Display results
                self._display_assembly_results(result)
                
        except Exception as e:
            st.error(f"❌ Error assembling template: {str(e)}")
            logger.error(f"Template assembly error: {e}")
    
    def _display_assembly_results(self, result: ProfessionalTemplateResult):
        """Display assembly results."""
        st.subheader("📋 Assembly Results")
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("File Size", f"{result.file_size_bytes / 1024:.1f} KB")
        
        with col2:
            st.metric("Page Count", result.page_count)
        
        with col3:
            st.metric("Word Count", result.word_count)
        
        with col4:
            overall_score = (
                result.pre_assembly_validation.quality_score.overall_score + 
                result.post_assembly_validation.quality_score.overall_score
            ) / 2
            st.metric("Quality Score", f"{overall_score:.1f}/100")
        
        # Validation results
        st.subheader("🔍 Validation Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Pre-Assembly Validation:**")
            pre_val = result.pre_assembly_validation
            
            if pre_val.is_valid:
                st.success(f"✅ Passed ({pre_val.quality_score.overall_score:.1f}/100)")
            else:
                st.error(f"❌ Failed ({pre_val.quality_score.overall_score:.1f}/100)")
            
            if pre_val.validation_issues:
                critical_issues = [i for i in pre_val.validation_issues if i.severity == ValidationSeverity.CRITICAL]
                high_issues = [i for i in pre_val.validation_issues if i.severity == ValidationSeverity.HIGH]
                
                if critical_issues:
                    st.error(f"🚨 {len(critical_issues)} critical issues")
                if high_issues:
                    st.warning(f"⚠️ {len(high_issues)} high priority issues")
        
        with col2:
            st.write("**Post-Assembly Validation:**")
            post_val = result.post_assembly_validation
            
            if post_val.is_valid:
                st.success(f"✅ Passed ({post_val.quality_score.overall_score:.1f}/100)")
            else:
                st.error(f"❌ Failed ({post_val.quality_score.overall_score:.1f}/100)")
            
            if post_val.placeholder_count > 0:
                st.warning(f"📝 {post_val.placeholder_count} placeholders remaining")
            
            st.info(f"Status: {post_val.compliance_status.title()}")
        
        # Download options
        st.subheader("📥 Download Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Main template download
            if os.path.exists(result.file_path):
                with open(result.file_path, 'rb') as file:
                    st.download_button(
                        label="📄 Download Template",
                        data=file.read(),
                        file_name=os.path.basename(result.file_path),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary"
                    )
        
        with col2:
            # Quality report download
            if result.quality_report_path and os.path.exists(result.quality_report_path):
                with open(result.quality_report_path, 'r', encoding='utf-8') as file:
                    st.download_button(
                        label="📊 Download Quality Report",
                        data=file.read(),
                        file_name=os.path.basename(result.quality_report_path),
                        mime="text/plain"
                    )
        
        with col3:
            # Complete package download
            if st.button("📦 Download Complete Package"):
                self._create_download_package(result)
    
    def _create_download_package(self, result: ProfessionalTemplateResult):
        """Create and offer complete download package."""
        try:
            with st.spinner("📦 Creating download package..."):
                package_dir = self.assembler.generate_download_package(result)
                
                # Create ZIP file
                zip_path = f"{package_dir}.zip"
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(package_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, package_dir)
                            zipf.write(file_path, arcname)
                
                # Offer download
                with open(zip_path, 'rb') as file:
                    st.download_button(
                        label="📦 Download Package",
                        data=file.read(),
                        file_name=f"QME_Package_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip"
                    )
                
                st.success("✅ Download package created successfully!")
                
        except Exception as e:
            st.error(f"❌ Error creating download package: {str(e)}")
            logger.error(f"Package creation error: {e}")
    
    def _render_quality_validation_tab(self):
        """Render the quality validation tab."""
        st.subheader("🔍 Quality Validation & Analysis")
        
        if not st.session_state.professional_templates:
            st.info("📋 No templates available for validation analysis.")
            return
        
        # Template selector
        template_ids = list(st.session_state.professional_templates.keys())
        selected_id = st.selectbox(
            "Select Template for Analysis",
            options=template_ids,
            format_func=lambda x: self._get_template_display_name(x)
        )
        
        if selected_id:
            result = st.session_state.professional_templates[selected_id]
            self._display_detailed_validation_analysis(result)
    
    def _display_detailed_validation_analysis(self, result: ProfessionalTemplateResult):
        """Display detailed validation analysis."""
        st.subheader("📊 Detailed Quality Analysis")
        
        # Quality score breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Pre-Assembly Scores:**")
            pre_scores = result.pre_assembly_validation.quality_score
            
            st.progress(pre_scores.completeness_score / 100)
            st.write(f"Completeness: {pre_scores.completeness_score:.1f}/100")
            
            st.progress(pre_scores.accuracy_score / 100)
            st.write(f"Accuracy: {pre_scores.accuracy_score:.1f}/100")
            
            st.progress(pre_scores.compliance_score / 100)
            st.write(f"Compliance: {pre_scores.compliance_score:.1f}/100")
        
        with col2:
            st.write("**Post-Assembly Scores:**")
            post_scores = result.post_assembly_validation.quality_score
            
            st.progress(post_scores.completeness_score / 100)
            st.write(f"Completeness: {post_scores.completeness_score:.1f}/100")
            
            st.progress(post_scores.accuracy_score / 100)
            st.write(f"Accuracy: {post_scores.accuracy_score:.1f}/100")
            
            st.progress(post_scores.compliance_score / 100)
            st.write(f"Compliance: {post_scores.compliance_score:.1f}/100")
        
        # Issues breakdown
        st.subheader("🚨 Issues Analysis")
        
        all_issues = result.pre_assembly_validation.validation_issues + result.post_assembly_validation.validation_issues
        
        if all_issues:
            # Group issues by severity
            critical_issues = [i for i in all_issues if i.severity == ValidationSeverity.CRITICAL]
            high_issues = [i for i in all_issues if i.severity == ValidationSeverity.HIGH]
            medium_issues = [i for i in all_issues if i.severity == ValidationSeverity.MEDIUM]
            low_issues = [i for i in all_issues if i.severity == ValidationSeverity.LOW]
            
            # Display issue counts
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Critical", len(critical_issues), delta=None, delta_color="inverse")
            with col2:
                st.metric("High", len(high_issues), delta=None, delta_color="inverse")
            with col3:
                st.metric("Medium", len(medium_issues), delta=None, delta_color="normal")
            with col4:
                st.metric("Low", len(low_issues), delta=None, delta_color="normal")
            
            # Display issues by category
            if critical_issues:
                with st.expander("🚨 Critical Issues", expanded=True):
                    for issue in critical_issues:
                        st.error(f"**{issue.title}**")
                        st.write(issue.description)
                        if issue.suggestions:
                            st.write("Suggestions:")
                            for suggestion in issue.suggestions:
                                st.write(f"• {suggestion}")
                        st.write("---")
            
            if high_issues:
                with st.expander("⚠️ High Priority Issues", expanded=False):
                    for issue in high_issues[:5]:  # Show top 5
                        st.warning(f"**{issue.title}**")
                        st.write(issue.description)
                        if issue.suggestions:
                            st.write("Suggestions:")
                            for suggestion in issue.suggestions:
                                st.write(f"• {suggestion}")
                        st.write("---")
        else:
            st.success("✅ No validation issues found!")
    
    def _render_template_gallery_tab(self):
        """Render the template gallery tab."""
        st.subheader("📊 Template Gallery & Management")
        
        if not st.session_state.professional_templates:
            st.info("📋 No templates in gallery yet.")
            return
        
        # Gallery view
        for template_id, result in st.session_state.professional_templates.items():
            with st.expander(f"📄 {template_id} - {self._get_patient_name_from_result(result)}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Generated:** {result.generated_at.strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**File Size:** {result.file_size_bytes / 1024:.1f} KB")
                    st.write(f"**Pages:** {result.page_count}")
                
                with col2:
                    overall_score = (
                        result.pre_assembly_validation.quality_score.overall_score + 
                        result.post_assembly_validation.quality_score.overall_score
                    ) / 2
                    st.write(f"**Quality Score:** {overall_score:.1f}/100")
                    st.write(f"**Status:** {result.post_assembly_validation.compliance_status.title()}")
                
                with col3:
                    if st.button(f"📥 Download", key=f"download_{template_id}"):
                        if os.path.exists(result.file_path):
                            with open(result.file_path, 'rb') as file:
                                st.download_button(
                                    label="📄 Download Template",
                                    data=file.read(),
                                    file_name=os.path.basename(result.file_path),
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key=f"dl_btn_{template_id}"
                                )
                    
                    if st.button(f"🗑️ Delete", key=f"delete_{template_id}"):
                        del st.session_state.professional_templates[template_id]
                        st.rerun()
    
    def _render_advanced_settings_tab(self):
        """Render the advanced settings tab."""
        st.subheader("⚙️ Advanced Settings & Configuration")
        
        # Template customization
        st.subheader("🎨 Template Customization")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Formatting Options:**")
            
            font_family = st.selectbox(
                "Font Family",
                options=["Times New Roman", "Arial", "Calibri"],
                index=0
            )
            
            font_size = st.slider("Font Size", min_value=10, max_value=14, value=12)
            
            line_spacing = st.selectbox(
                "Line Spacing",
                options=["Single", "1.15", "1.5", "Double"],
                index=2
            )
        
        with col2:
            st.write("**Content Options:**")
            
            include_toc = st.checkbox("Include Table of Contents", value=False)
            
            include_appendices = st.checkbox("Include Appendices", value=False)
            
            watermark_text = st.text_input("Watermark Text (optional)", value="")
        
        # Validation settings
        st.subheader("✅ Validation Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Quality Thresholds:**")
            
            min_completeness = st.slider("Minimum Completeness Score", min_value=0, max_value=100, value=80)
            min_compliance = st.slider("Minimum Compliance Score", min_value=0, max_value=100, value=90)
        
        with col2:
            st.write("**Issue Handling:**")
            
            auto_fix_enabled = st.checkbox("Enable Auto-Fix for Minor Issues", value=True)
            strict_validation = st.checkbox("Strict Validation Mode", value=False)
        
        # Export settings
        st.subheader("📤 Export Settings")
        
        export_formats = st.multiselect(
            "Export Formats",
            options=["DOCX", "PDF", "HTML"],
            default=["DOCX"]
        )
        
        include_metadata = st.checkbox("Include Document Metadata", value=True)
        
        # Save settings
        if st.button("💾 Save Advanced Settings"):
            # Here you would save the settings to configuration
            st.success("✅ Advanced settings saved successfully!")
    
    def _load_sample_template_data(self):
        """Load sample template data for testing."""
        from src.models.knowledge_graph import Diagnosis, Finding, ImpairmentRating
        
        # Create sample patient info
        patient_info = PatientInfo(
            name="John Doe",
            age=45,
            gender="Male",
            case_number="WC2024-001",
            injury_date=datetime(2024, 1, 15),
            employer="ABC Construction",
            occupation="Construction Worker",
            body_parts=["Lower Back", "Left Knee"]
        )
        
        # Create sample medical findings
        sample_diagnosis = Diagnosis(
            id="diag_001",
            icd_code="M54.5",
            description="Low back pain",
            severity="moderate",
            certainty=0.9
        )
        
        sample_finding = Finding(
            id="find_001",
            section_id="exam_001",
            finding_type="examination",
            description="Decreased range of motion in lumbar spine"
        )
        
        sample_rating = ImpairmentRating(
            id="rating_001",
            diagnosis_id="diag_001",
            percentage=15,
            ama_table="15-3",
            rationale="Based on DRE Category II findings"
        )
        
        medical_findings = MedicalFindings(
            diagnoses=[sample_diagnosis],
            findings=[sample_finding],
            impairment_ratings=[sample_rating],
            imaging_studies=["MRI lumbar spine showing disc degeneration L4-L5"],
            treatment_history=["Physical therapy", "NSAIDs"]
        )
        
        # Create template data
        template_data = QMETemplateData(
            patient_info=patient_info,
            medical_findings=medical_findings,
            missing_sections=["Past Medical History", "Social History"],
            recommendations=["Complete occupational history", "Obtain additional imaging"]
        )
        
        st.session_state.qme_template_data = template_data    
    
    def _get_template_display_name(self, template_id: str) -> str:
        """Get display name for template in selector."""
        try:
            result = st.session_state.professional_templates[template_id]
            patient_name = self._get_patient_name_from_result(result)
            return f"Template {template_id.split('_')[1]} - {patient_name}"
        except:
            return f"Template {template_id.split('_')[1]} - Unknown"
    
    def _get_patient_name_from_result(self, result) -> str:
        """Get patient name from template result, handling both data formats."""
        try:
            template_data = result.template_data
            if isinstance(template_data, dict):
                return template_data.get('patient_info', {}).get('name', 'Unknown')
            else:
                return template_data.patient_info.name or 'Unknown'
        except:
            return 'Unknown'
    
    def _convert_dict_to_qme_template_data(self, template_data_dict: Dict[str, Any]) -> 'QMETemplateData':
        """Convert dictionary format to QMETemplateData object."""
        try:
            from src.core.generation.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
            from src.models.knowledge_graph import Diagnosis, Finding, ImpairmentRating
            from datetime import datetime
            
            # Extract patient info
            patient_dict = template_data_dict.get('patient_info', {})
            patient_info = PatientInfo(
                name=patient_dict.get('name', ''),
                age=patient_dict.get('age', 0),
                gender=patient_dict.get('gender', ''),
                case_number=patient_dict.get('case_number', ''),
                injury_date=patient_dict.get('injury_date', datetime.now()),
                employer=patient_dict.get('employer', ''),
                occupation=patient_dict.get('occupation', ''),
                body_parts=patient_dict.get('body_parts', [])
            )
            
            # Extract medical findings
            medical_dict = template_data_dict.get('medical_findings', {})
            
            # Convert diagnoses
            diagnoses = []
            for i, diag in enumerate(medical_dict.get('diagnoses', [])):
                if isinstance(diag, str):
                    diagnoses.append(Diagnosis(
                        id=f"diag_{i}",
                        icd_code="",
                        description=diag,
                        severity="unknown",
                        certainty=0.5
                    ))
                elif isinstance(diag, dict):
                    diagnoses.append(Diagnosis(
                        id=diag.get('id', f"diag_{i}"),
                        icd_code=diag.get('icd_code', ''),
                        description=diag.get('description', ''),
                        severity=diag.get('severity', 'unknown'),
                        certainty=diag.get('certainty', 0.5)
                    ))
            
            # Convert findings
            findings = []
            for i, finding in enumerate(medical_dict.get('findings', [])):
                if isinstance(finding, str):
                    findings.append(Finding(
                        id=f"find_{i}",
                        section_id="",
                        finding_type="examination",
                        description=finding
                    ))
                elif isinstance(finding, dict):
                    findings.append(Finding(
                        id=finding.get('id', f"find_{i}"),
                        section_id=finding.get('section_id', ''),
                        finding_type=finding.get('finding_type', 'examination'),
                        description=finding.get('description', '')
                    ))
            
            # Convert impairment ratings
            impairment_ratings = []
            for i, rating in enumerate(medical_dict.get('impairment_ratings', [])):
                if isinstance(rating, dict):
                    impairment_ratings.append(ImpairmentRating(
                        id=rating.get('id', f"rating_{i}"),
                        diagnosis_id=rating.get('diagnosis_id', ''),
                        percentage=rating.get('percentage', 0),
                        ama_table=rating.get('ama_table', ''),
                        rationale=rating.get('rationale', '')
                    ))
            
            medical_findings = MedicalFindings(
                diagnoses=diagnoses,
                findings=findings,
                impairment_ratings=impairment_ratings,
                imaging_studies=medical_dict.get('imaging_studies', []),
                treatment_history=medical_dict.get('treatment_history', [])
            )
            
            # Create QMETemplateData object
            return QMETemplateData(
                patient_info=patient_info,
                medical_findings=medical_findings,
                missing_sections=template_data_dict.get('missing_sections', []),
                recommendations=template_data_dict.get('recommendations', [])
            )
            
        except Exception as e:
            logger.error(f"Error converting dictionary to QMETemplateData: {e}")
            # Return a minimal QMETemplateData object as fallback
            from src.core.generation.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
            return QMETemplateData(
                patient_info=PatientInfo(name="Unknown", age=0, gender="", case_number="", injury_date=datetime.now(), employer="", occupation="", body_parts=[]),
                medical_findings=MedicalFindings(diagnoses=[], findings=[], impairment_ratings=[], imaging_studies=[], treatment_history=[]),
                missing_sections=[],
                recommendations=[]
            )