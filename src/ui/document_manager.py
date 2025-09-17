"""Document Management Interface for viewing, selecting, and managing processed documents."""

import streamlit as st
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.storage.document_storage import DocumentStorage
from src.models.document import Document, ProcessingJob
from src.ui.qa_interface_simple import render_qa_for_document
from src.infrastructure.monitoring.ui_error_handler import (
    enhanced_ui_error_boundary, handle_component_failure
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class DocumentManager:
    """Document management interface for Streamlit."""
    
    def __init__(self):
        try:
            self.storage = DocumentStorage()
        except Exception as e:
            logger.error(f"Error initializing document storage: {e}")
            self.storage = None
        
        # Initialize session state
        if 'selected_doc_for_qa' not in st.session_state:
            st.session_state.selected_doc_for_qa = None
        if 'show_delete_confirmation' not in st.session_state:
            st.session_state.show_delete_confirmation = {}
    
    @enhanced_ui_error_boundary(
        page="document_management",
        component="document_manager",
        show_fallback=True,
        show_recovery=True
    )
    def render_document_management(self) -> None:
        """Render the main document management interface with comprehensive error handling."""
        try:
            st.subheader("📚 Document Management")
            
            # Check if storage is available
            if not self.storage:
                handle_component_failure(
                    component_name="document_storage",
                    error=Exception("Document storage not available"),
                    context={'page': 'document_management', 'component': 'storage_init'},
                    show_fallback=True,
                    show_recovery=True
                )
                return
            
            # Get all documents with error handling
            try:
                documents = self.storage.list_documents()
            except Exception as storage_error:
                handle_component_failure(
                    component_name="document_list",
                    error=storage_error,
                    context={'page': 'document_management', 'component': 'document_listing'},
                    show_fallback=True,
                    show_recovery=True
                )
                return
            
            if not documents:
                st.info("📄 No documents found. Upload some documents to get started!")
                
                # Show helpful actions
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📤 Upload Documents"):
                        st.session_state.current_page = "Upload Documents"
                        st.rerun()
                with col2:
                    if st.button("🔄 Refresh"):
                        st.rerun()
                return
            
            # Document statistics with error handling
            try:
                self._render_document_stats(documents)
            except Exception as stats_error:
                logger.error(f"Error rendering document stats: {stats_error}")
                st.warning("⚠️ Unable to load document statistics")
            
            # Document list with error handling
            try:
                self._render_document_list(documents)
            except Exception as list_error:
                handle_component_failure(
                    component_name="document_list_renderer",
                    error=list_error,
                    context={'page': 'document_management', 'component': 'document_list'},
                    show_fallback=True,
                    show_recovery=True
                )
                
        except Exception as e:
            logger.error(f"Error in document management rendering: {e}", exc_info=True)
            handle_component_failure(
                component_name="document_management",
                error=e,
                context={'page': 'document_management', 'component': 'main_interface'},
                show_fallback=True,
                show_recovery=True
            )
    
    def _render_document_stats(self, documents: List[Document]) -> None:
        """Render document statistics."""
        # Calculate stats
        total_docs = len(documents)
        completed_docs = len([d for d in documents if d.processing_status == 'completed'])
        processing_docs = len([d for d in documents if d.processing_status in ['pending', 'processing']])
        failed_docs = len([d for d in documents if d.processing_status == 'failed'])
        
        # Display stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📄 Total Documents", total_docs)
        
        with col2:
            st.metric("✅ Completed", completed_docs)
        
        with col3:
            st.metric("⏳ Processing", processing_docs)
        
        with col4:
            st.metric("❌ Failed", failed_docs)
        
        st.markdown("---")
    
    def _render_document_list(self, documents: List[Document]) -> None:
        """Render the list of documents with management options."""
        # Filter options
        col1, col2 = st.columns([2, 1])
        
        with col1:
            status_filter = st.selectbox(
                "Filter by status:",
                options=["All", "Completed", "Processing", "Failed", "Pending"],
                key="status_filter"
            )
        
        with col2:
            sort_by = st.selectbox(
                "Sort by:",
                options=["Upload Date (Newest)", "Upload Date (Oldest)", "Title (A-Z)", "Title (Z-A)"],
                key="sort_by"
            )
        
        # Apply filters and sorting
        filtered_docs = self._filter_and_sort_documents(documents, status_filter, sort_by)
        
        if not filtered_docs:
            st.info(f"No documents found with status: {status_filter}")
            return
        
        # Display documents
        for doc in filtered_docs:
            self._render_document_card(doc)
    
    def _filter_and_sort_documents(self, documents: List[Document], status_filter: str, sort_by: str) -> List[Document]:
        """Filter and sort documents based on user selection."""
        # Apply status filter
        if status_filter != "All":
            status_map = {
                "Completed": "completed",
                "Processing": ["pending", "processing"],
                "Failed": "failed",
                "Pending": "pending"
            }
            
            filter_status = status_map[status_filter]
            if isinstance(filter_status, list):
                filtered_docs = [d for d in documents if d.processing_status in filter_status]
            else:
                filtered_docs = [d for d in documents if d.processing_status == filter_status]
        else:
            filtered_docs = documents.copy()
        
        # Apply sorting
        if sort_by == "Upload Date (Newest)":
            filtered_docs.sort(key=lambda d: d.upload_timestamp, reverse=True)
        elif sort_by == "Upload Date (Oldest)":
            filtered_docs.sort(key=lambda d: d.upload_timestamp)
        elif sort_by == "Title (A-Z)":
            filtered_docs.sort(key=lambda d: d.title.lower())
        elif sort_by == "Title (Z-A)":
            filtered_docs.sort(key=lambda d: d.title.lower(), reverse=True)
        
        return filtered_docs
    
    def _render_document_card(self, document: Document) -> None:
        """Render a single document card with management options."""
        # Status styling
        status_colors = {
            'completed': '🟢',
            'processing': '🟡',
            'pending': '🟡',
            'failed': '🔴'
        }
        
        status_icon = status_colors.get(document.processing_status, '⚪')
        
        # Document card
        with st.container():
            # Header row
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{status_icon} {document.title}**")
                st.caption(f"{document.file_type.upper()} • {document.file_size:,} bytes • Uploaded: {document.upload_timestamp.strftime('%Y-%m-%d %H:%M')}")
            
            with col2:
                # Q&A button (only for completed documents)
                if document.processing_status == 'completed':
                    if st.button("💬 Q&A", key=f"qa_{document.id}", help="Ask questions about this document"):
                        st.session_state.selected_doc_for_qa = document.id
                        st.rerun()
                else:
                    st.write(f"Status: {document.processing_status.title()}")
            
            with col3:
                # Delete button
                if st.button("🗑️ Delete", key=f"delete_{document.id}", help="Delete this document"):
                    st.session_state.show_delete_confirmation[document.id] = True
                    st.rerun()
            
            # Document details (expandable)
            with st.expander("📋 Document Details", expanded=False):
                self._render_document_details(document)
            
            # Delete confirmation dialog
            if st.session_state.show_delete_confirmation.get(document.id, False):
                self._render_delete_confirmation(document)
            
            st.markdown("---")
    
    def _render_document_details(self, document: Document) -> None:
        """Render detailed document information."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Basic Information:**")
            st.write(f"• **ID:** `{document.id}`")
            st.write(f"• **Title:** {document.title}")
            st.write(f"• **Type:** {document.document_type or 'Unknown'}")
            st.write(f"• **File Format:** {document.file_type.upper()}")
            st.write(f"• **File Size:** {document.file_size:,} bytes")
            st.write(f"• **Status:** {document.processing_status.title()}")
        
        with col2:
            st.write("**Timestamps:**")
            st.write(f"• **Uploaded:** {document.upload_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"• **Created:** {document.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"• **Updated:** {document.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Processing information
        if document.processing_status in ['processing', 'failed']:
            st.write("**Processing Information:**")
            jobs = self.storage.list_processing_jobs(document.id)
            if jobs:
                latest_job = jobs[0]  # Most recent job
                st.write(f"• **Current Step:** {latest_job.current_step or 'Unknown'}")
                st.write(f"• **Progress:** {latest_job.progress_percentage}%")
                if latest_job.error_message:
                    st.error(f"**Error:** {latest_job.error_message}")
        
        # Extracted information
        if document.extracted_info:
            st.write("**Extracted Information:**")
            with st.expander("View Extracted Data", expanded=False):
                st.json(document.extracted_info)
        
        # Analysis
        if document.analysis:
            st.write("**Analysis:**")
            with st.expander("View Analysis", expanded=False):
                st.write(document.analysis)
        
        # Summary
        if document.summary:
            st.write("**Summary:**")
            with st.expander("View Summary", expanded=False):
                st.write(document.summary)
        
        # Original text preview
        if document.original_text:
            st.write("**Original Text Preview:**")
            with st.expander("View Text Preview", expanded=False):
                preview_text = document.original_text[:1000]
                if len(document.original_text) > 1000:
                    preview_text += "..."
                st.text(preview_text)
    
    def _render_delete_confirmation(self, document: Document) -> None:
        """Render delete confirmation dialog."""
        st.warning(f"⚠️ Are you sure you want to delete '{document.title}'?")
        st.write("This action cannot be undone. All associated Q&A sessions will also be deleted.")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("✅ Yes, Delete", key=f"confirm_delete_{document.id}", type="primary"):
                self._delete_document(document)
        
        with col2:
            if st.button("❌ Cancel", key=f"cancel_delete_{document.id}"):
                st.session_state.show_delete_confirmation[document.id] = False
                st.rerun()
    
    def _delete_document(self, document: Document) -> None:
        """Delete a document and show result."""
        try:
            success = self.storage.delete_document(document.id)
            
            if success:
                st.success(f"✅ Document '{document.title}' has been deleted successfully!")
                # Clear confirmation state
                if document.id in st.session_state.show_delete_confirmation:
                    del st.session_state.show_delete_confirmation[document.id]
                st.rerun()
            else:
                st.error("❌ Failed to delete document. Please try again.")
                
        except Exception as e:
            st.error(f"❌ Error deleting document: {str(e)}")
    
    def render_qa_mode(self) -> None:
        """Render Q&A mode for selected document."""
        if not st.session_state.selected_doc_for_qa:
            return
        
        document_id = st.session_state.selected_doc_for_qa
        document = self.storage.get_document(document_id)
        
        if not document:
            st.error("Document not found!")
            st.session_state.selected_doc_for_qa = None
            return
        
        # Back button
        if st.button("← Back to Document List"):
            st.session_state.selected_doc_for_qa = None
            st.rerun()
        
        st.markdown("---")
        
        # Render Q&A interface
        render_qa_for_document(document_id)
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get storage statistics for dashboard."""
        return self.storage.get_storage_stats()
    
    def render_document_details(self, document_id: str) -> None:
        """Render detailed view of a specific document."""
        # Get document
        document = self.storage.get_document(document_id)
        if not document:
            st.error("Document not found!")
            return
        
        # Header
        st.subheader(f"📄 Document Details: {document.title}")
        
        # Document info
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Title:** {document.title}")
            st.write(f"**Type:** {document.document_type or 'Unknown'}")
            st.write(f"**File Format:** {document.file_type.upper()}")
            st.write(f"**Size:** {document.file_size:,} bytes")
        
        with col2:
            st.write(f"**Uploaded:** {document.upload_timestamp.strftime('%Y-%m-%d %H:%M')}")
            st.write(f"**Status:** {document.processing_status}")
            if document.updated_at:
                st.write(f"**Last Updated:** {document.updated_at.strftime('%Y-%m-%d %H:%M')}")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if document.processing_status == 'completed':
                if st.button("💬 Ask Questions", type="primary"):
                    st.session_state.selected_doc_for_qa = document_id
                    st.rerun()
        
        with col2:
            if st.button("📚 Back to All Documents"):
                st.rerun()
        
        # Show document content and analysis if available
        if document.processing_status == 'completed':
            # Summary
            if document.summary:
                st.subheader("📝 Summary")
                st.write(document.summary)
            
            # Analysis
            if document.analysis:
                with st.expander("📊 Detailed Analysis", expanded=False):
                    st.write(document.analysis)
            
            # Extracted Information
            if document.extracted_info:
                with st.expander("🔍 Extracted Information", expanded=False):
                    st.json(document.extracted_info)
            
            # Original Text
            with st.expander("📄 Original Text", expanded=False):
                st.text_area(
                    "Full Text Content",
                    value=document.original_text,
                    height=400,
                    disabled=True
                )
        
        elif document.processing_status in ['pending', 'processing']:
            st.info("⏳ Document is still being processed. Please check back later.")
            
            # Show processing status if available
            jobs = self.storage.list_processing_jobs(document_id)
            if jobs:
                latest_job = jobs[0]
                st.write(f"**Current Step:** {latest_job.current_step or 'Initializing'}")
                if latest_job.progress_percentage:
                    st.progress(latest_job.progress_percentage / 100)
                    st.write(f"Progress: {latest_job.progress_percentage}%")
        
        elif document.processing_status == 'failed':
            st.error("❌ Document processing failed.")
            
            # Show error details if available
            jobs = self.storage.list_processing_jobs(document_id)
            if jobs and jobs[0].error_message:
                with st.expander("Error Details"):
                    st.code(jobs[0].error_message)


def render_document_management_page(document_id: Optional[str] = None):
    """Render the document management page."""
    doc_manager = DocumentManager()
    
    # Check if we should show Q&A mode or specific document
    if document_id:
        doc_manager.render_document_details(document_id)
    elif st.session_state.get('selected_doc_for_qa'):
        doc_manager.render_qa_mode()
    else:
        doc_manager.render_document_management()


def render_document_management_page(document_id: Optional[str] = None):
    """Render the document management page with comprehensive error handling."""
    try:
        manager = DocumentManager()
        
        if document_id:
            # Show specific document
            st.subheader(f"📄 Document: {document_id}")
            
            # Try to get document details
            try:
                if manager.storage:
                    document = manager.storage.get_document(document_id)
                    if document:
                        # Show document details
                        st.write(f"**Filename:** {document.filename}")
                        st.write(f"**Status:** {document.processing_status}")
                        st.write(f"**Uploaded:** {document.created_at}")
                        
                        # Action buttons
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("💬 Ask Questions"):
                                render_qa_for_document(document_id)
                        
                        with col2:
                            if st.button("📋 Generate Template"):
                                st.session_state.template_document_id = document_id
                                st.session_state.current_page = "Generate QME Template"
                                st.rerun()
                        
                        with col3:
                            if st.button("📚 Back to All Documents"):
                                st.rerun()
                    else:
                        st.error(f"❌ Document {document_id} not found")
                else:
                    st.error("❌ Document storage not available")
                    
            except Exception as doc_error:
                handle_component_failure(
                    component_name="document_details",
                    error=doc_error,
                    context={'page': 'document_management', 'component': 'document_details', 'document_id': document_id},
                    show_fallback=True,
                    show_recovery=True
                )
        else:
            # Show all documents
            manager.render_document_management()
            
    except Exception as e:
        logger.error(f"Error rendering document management page: {e}", exc_info=True)
        handle_component_failure(
            component_name="document_management_page",
            error=e,
            context={'page': 'document_management', 'component': 'page_render', 'document_id': document_id},
            show_fallback=True,
            show_recovery=True
        )