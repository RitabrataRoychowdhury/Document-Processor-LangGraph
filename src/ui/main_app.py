"""
Main Streamlit application for the Document Q&A System.
Integrated application with comprehensive error handling and logging.
Enhanced with knowledge graph support and new repository pattern.
"""

import streamlit as st
import sys
import os
import asyncio

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.app import get_app, initialize_app
from src.startup import SystemStartup
from src.ui.upload_interface import UploadInterface
from src.ui.qa_interface import render_qa_page
from src.ui.document_manager import render_document_management_page
from src.utils.logging_config import get_logger
from src.utils.error_handling import DocumentQAError, format_error_for_ui
from src.config.app_config import app_config

logger = get_logger(__name__)

def main():
    """Main application entry point"""
    
    # Page configuration
    st.set_page_config(
        page_title="Document Q&A System",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize application if not already done
    if 'app_initialized' not in st.session_state:
        with st.spinner("Initializing application with health checks and performance monitoring..."):
            try:
                # Initialize system with startup process
                startup = SystemStartup()
                success = asyncio.run(startup.startup())
                
                if success:
                    st.session_state.app_initialized = True
                    st.session_state.startup_instance = startup
                    st.session_state.app_config = startup.config
                    logger.info("Application initialized successfully with startup system")
                else:
                    st.error("Failed to initialize application. Please check the logs and configuration.")
                    st.stop()
            except Exception as e:
                error_info = format_error_for_ui(e)
                st.error(f"Initialization error: {error_info['user_message']}")
                logger.error(f"Streamlit initialization error: {e}", exc_info=True)
                st.stop()
    
    # Get application instance and health status
    try:
        startup = st.session_state.startup_instance
        health_checker = startup.get_health_checker()
        performance_monitor = startup.get_performance_monitor()
        
        # Check system status
        if 'system_status_checked' not in st.session_state:
            health_status = health_checker.get_overall_health()
            perf_stats = performance_monitor.get_current_statistics()
            
            # Combine health and performance data
            status = {
                "initialized": True,
                "overall_healthy": health_status["overall_healthy"],
                "health_checks": health_status["checks"],
                "performance": perf_stats,
                "storage": {"total_documents": 0},  # Will be updated by legacy app if available
                "workflow": {"queue_size": 0, "active_jobs": 0, "running": True},
                "database": {"path": startup.config.database_path},
                "config": {
                    "api_key_configured": bool(startup.config.gemini_api_key or startup.config.openai_api_key),
                    "max_file_size_mb": startup.config.max_file_size_mb,
                    "allowed_file_types": startup.config.allowed_file_types,
                    "debug_mode": False
                }
            }
            
            if not health_status["overall_healthy"]:
                st.warning("⚠️ System health checks detected issues. Some features may not work properly.")
                with st.expander("Health Check Details", expanded=False):
                    for component, check in health_status["checks"].items():
                        status_icon = "✅" if check["healthy"] else "❌"
                        st.write(f"{status_icon} {component}: {check['message']}")
            
            st.session_state.system_status_checked = True
            st.session_state.system_status = status
        
        # Try to get legacy app for backward compatibility
        try:
            app = get_app()
            legacy_status = app.get_system_status()
            if not legacy_status.get("error"):
                # Update status with legacy app data
                st.session_state.system_status.update({
                    "storage": legacy_status.get("storage", {}),
                    "workflow": legacy_status.get("workflow", {}),
                    "database": legacy_status.get("database", {})
                })
        except Exception:
            # Legacy app not available, continue with new system
            pass
        
    except Exception as e:
        error_info = format_error_for_ui(e)
        st.error(f"Application error: {error_info['user_message']}")
        logger.error(f"Streamlit app error: {e}", exc_info=True)
        st.stop()
    
    # Main title
    st.title("📚 Document Q&A System")
    st.markdown("Upload and process documents for intelligent question answering")
    
    # System status indicator
    with st.sidebar:
        status = st.session_state.get('system_status', {})
        config_info = st.session_state.get('app_config', app_config)
        
        if status:
            if status.get('overall_healthy', True):
                st.success("🟢 System Healthy")
            else:
                st.warning("🟡 System Issues Detected")
            
            with st.expander("System Info", expanded=False):
                st.write(f"Documents: {status.get('storage', {}).get('total_documents', 0)}")
                st.write(f"Queue: {status.get('workflow', {}).get('queue_size', 0)} jobs")
                st.write(f"API: {'✅' if status.get('config', {}).get('api_key_configured') else '❌'}")
                
                # Show performance info
                perf_info = status.get('performance', {})
                if perf_info.get('overall_stats'):
                    stats = perf_info['overall_stats']
                    st.write(f"Processed: {stats.get('total_documents_processed', 0)}")
                    st.write(f"Success Rate: {stats.get('successful_processing', 0)}/{stats.get('total_documents_processed', 0)}")
                
                # Show new configuration info
                if hasattr(config_info, 'embedding_provider'):
                    st.write(f"Embedding: {config_info.embedding_provider}")
                    st.write(f"QA Provider: {config_info.qa_provider}")
                
                # Show health status
                health_checks = status.get('health_checks', {})
                healthy_count = sum(1 for check in health_checks.values() if check.get('healthy', False))
                total_count = len(health_checks)
                st.write(f"Health: {healthy_count}/{total_count} components")
        else:
            st.warning("🟡 System Status Unknown")
    
    # Initialize upload interface
    try:
        upload_interface = UploadInterface()
    except Exception as e:
        error_info = format_error_for_ui(e)
        st.error(f"Failed to initialize upload interface: {error_info['user_message']}")
        logger.error(f"Upload interface error: {e}", exc_info=True)
        upload_interface = None
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        
        # Add migration status if available
        if st.session_state.get('migration_needed'):
            st.warning("⚠️ Data migration available")
            if st.button("Run Migration"):
                st.session_state.switch_to_migration = True
        
        page_options = ["Upload Documents", "Document Management", "Q&A Interface", "Upload History", "System Status", "Performance Monitor", "Knowledge Base Setup", "About"]
        
        # Add migration page if needed
        if st.session_state.get('migration_needed') or st.session_state.get('show_migration'):
            page_options.insert(-1, "Data Migration")
        
        page = st.selectbox("Choose a section:", page_options)
    
    # Handle navigation switches from upload interface
    if st.session_state.get('switch_to_qa', False):
        st.session_state.switch_to_qa = False
        page = "Q&A Interface"
    elif st.session_state.get('switch_to_management', False):
        st.session_state.switch_to_management = False
        page = "Document Management"
    elif st.session_state.get('switch_to_migration', False):
        st.session_state.switch_to_migration = False
        page = "Data Migration"
    
    # Main content area with error handling
    try:
        if page == "Upload Documents":
            if upload_interface:
                render_upload_page(upload_interface)
            else:
                st.error("Upload interface not available")
        elif page == "Document Management":
            # Check if we need to show a specific document
            if st.session_state.get('view_document_id'):
                document_id = st.session_state.view_document_id
                st.session_state.view_document_id = None
                render_document_management_page(document_id)
            else:
                render_document_management_page()
        elif page == "Q&A Interface":
            # Check if we need to start Q&A with a specific document
            if st.session_state.get('qa_document_id'):
                document_id = st.session_state.qa_document_id
                st.session_state.qa_document_id = None
                render_qa_page_with_document(document_id)
            else:
                render_qa_page()
        elif page == "Upload History":
            if upload_interface:
                render_history_page(upload_interface)
            else:
                st.error("Upload interface not available")
        elif page == "System Status":
            render_system_status_page()
        elif page == "Performance Monitor":
            render_performance_monitor_page()
        elif page == "Knowledge Base Setup":
            render_knowledge_base_setup_page()
        elif page == "Data Migration":
            render_migration_page()
        elif page == "About":
            render_about_page()
    except Exception as e:
        error_info = format_error_for_ui(e)
        st.error(f"Page error: {error_info['user_message']}")
        logger.error(f"Page rendering error on {page}: {e}", exc_info=True)
        
        # Show error details in debug mode
        if st.session_state.get('system_status', {}).get('config', {}).get('debug_mode'):
            with st.expander("Error Details (Debug Mode)", expanded=False):
                st.code(str(e))
                if hasattr(e, '__traceback__'):
                    import traceback
                    st.code(traceback.format_exc())


def render_qa_page_with_document(document_id: str):
    """Render Q&A page with a specific document pre-selected."""
    from src.ui.qa_interface import render_qa_for_document
    render_qa_for_document(document_id)

def render_upload_page(upload_interface: UploadInterface):
    """Render the document upload page"""
    
    st.markdown("---")
    
    # Upload section
    file_data = upload_interface.render_upload_section()
    
    if file_data:
        st.markdown("---")
        
        # Check if document has been processed
        if file_data.get('processing_complete'):
            st.success("🎉 Document uploaded and AI processing complete!")
            
            # Show immediate Q&A access
            st.info(
                "**Your document is ready:**\n"
                "✅ Text extracted and analyzed\n"
                "🤖 AI processing complete\n"
                "💬 Ready for intelligent Q&A!"
            )
            
            # Quick access buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💬 Ask Questions Now", type="primary"):
                    st.session_state.qa_document_id = file_data['document_id']
                    st.session_state.switch_to_qa = True
                    st.rerun()
            
            with col2:
                if st.button("📄 View All Documents"):
                    st.session_state.switch_to_management = True
                    st.rerun()
        
        elif file_data.get('error'):
            st.error(f"❌ Processing failed: {file_data['error']}")
            st.info("The document was uploaded but AI processing failed. You can try uploading again.")
        
        else:
            st.success("🎉 File successfully processed!")
            st.warning("⚠️ AI processing is not available. Please configure your Gemini API key for Q&A functionality.")

def render_history_page(upload_interface: UploadInterface):
    """Render the upload history page"""
    
    st.markdown("---")
    
    uploaded_files = upload_interface.get_uploaded_files()
    
    if not uploaded_files:
        st.info("No documents uploaded yet. Go to 'Upload Documents' to get started!")
        return
    
    # Display upload history
    upload_interface.render_upload_history()
    
    # Clear history button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("🗑️ Clear All History", type="secondary"):
            upload_interface.clear_upload_history()
            st.success("Upload history cleared!")
            st.rerun()

def render_knowledge_base_setup_page():
    """Render the knowledge base setup page for canonical documents."""
    
    st.markdown("---")
    st.header("📚 Knowledge Base Setup")
    
    st.markdown("""
    This page helps you set up the knowledge base with canonical medical documents.
    The system works best when initialized with these key reference documents.
    """)
    
    # Canonical documents section
    st.subheader("🏥 Canonical Medical Documents")
    
    canonical_docs = [
        {
            "name": "AMAGuides 5th Edition.pdf",
            "description": "AMA Guides to the Evaluation of Permanent Impairment, 5th Edition",
            "purpose": "Primary reference for impairment ratings and medical evaluations"
        },
        {
            "name": "QME-Study-Guide.pdf", 
            "description": "Qualified Medical Evaluator Study Guide",
            "purpose": "Guidelines and procedures for QME evaluations"
        },
        {
            "name": "Sample3.pdf",
            "description": "Sample medical evaluation report",
            "purpose": "Example format and structure for medical reports"
        }
    ]
    
    # Check status of canonical documents
    try:
        from src.services.document_processor import get_document_status, list_processed_documents
        
        processed_docs = list_processed_documents()
        processed_names = [doc['title'] for doc in processed_docs]
        
        st.subheader("📊 Document Status")
        
        for doc in canonical_docs:
            col1, col2, col3 = st.columns([2, 3, 1])
            
            with col1:
                st.write(f"**{doc['name']}**")
            
            with col2:
                if doc['name'] in processed_names:
                    st.success("✅ Processed")
                elif os.path.exists(doc['name']):
                    st.warning("📄 Available (not processed)")
                else:
                    st.error("❌ Missing")
            
            with col3:
                if doc['name'] in processed_names:
                    if st.button("🗑️", key=f"remove_{doc['name']}", help="Remove from knowledge base"):
                        try:
                            from src.services.document_processor import remove_document
                            if remove_document(doc['name']):
                                st.success(f"Removed {doc['name']}")
                                st.rerun()
                            else:
                                st.error(f"Failed to remove {doc['name']}")
                        except Exception as e:
                            st.error(f"Error: {e}")
                elif os.path.exists(doc['name']):
                    if st.button("⚡", key=f"process_{doc['name']}", help="Process into knowledge base"):
                        try:
                            from src.services.document_processor import process_document_simple
                            with st.spinner(f"Processing {doc['name']}..."):
                                if process_document_simple(doc['name']):
                                    st.success(f"Successfully processed {doc['name']}")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to process {doc['name']}")
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            # Show description
            with st.expander(f"ℹ️ About {doc['name']}", expanded=False):
                st.write(f"**Description:** {doc['description']}")
                st.write(f"**Purpose:** {doc['purpose']}")
        
        # Bulk operations
        st.subheader("🔧 Bulk Operations")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Process All Available", type="primary"):
                processed_count = 0
                failed_count = 0
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, doc in enumerate(canonical_docs):
                    if os.path.exists(doc['name']) and doc['name'] not in processed_names:
                        status_text.text(f"Processing {doc['name']}...")
                        try:
                            from src.services.document_processor import process_document_simple
                            if process_document_simple(doc['name']):
                                processed_count += 1
                            else:
                                failed_count += 1
                        except Exception as e:
                            failed_count += 1
                            st.error(f"Error processing {doc['name']}: {e}")
                    
                    progress_bar.progress((i + 1) / len(canonical_docs))
                
                status_text.text("Processing complete!")
                
                if processed_count > 0:
                    st.success(f"✅ Successfully processed {processed_count} document(s)")
                if failed_count > 0:
                    st.error(f"❌ Failed to process {failed_count} document(s)")
                
                if processed_count > 0:
                    st.rerun()
        
        with col2:
            if st.button("🗑️ Remove All Processed"):
                if st.session_state.get('confirm_remove_all'):
                    removed_count = 0
                    for doc in canonical_docs:
                        if doc['name'] in processed_names:
                            try:
                                from src.services.document_processor import remove_document
                                if remove_document(doc['name']):
                                    removed_count += 1
                            except Exception as e:
                                st.error(f"Error removing {doc['name']}: {e}")
                    
                    if removed_count > 0:
                        st.success(f"Removed {removed_count} document(s)")
                        st.rerun()
                    
                    st.session_state.confirm_remove_all = False
                else:
                    st.warning("⚠️ This will remove all processed canonical documents!")
                    if st.button("Confirm Remove All"):
                        st.session_state.confirm_remove_all = True
                        st.rerun()
        
        with col3:
            if st.button("🔄 Refresh Status"):
                st.rerun()
        
        # File upload section
        st.subheader("📤 Upload Missing Documents")
        
        missing_docs = [doc for doc in canonical_docs if not os.path.exists(doc['name'])]
        
        if missing_docs:
            st.write("Upload the missing canonical documents:")
            
            for doc in missing_docs:
                st.write(f"**Missing:** {doc['name']}")
                uploaded_file = st.file_uploader(
                    f"Upload {doc['name']}", 
                    type=['pdf'],
                    key=f"upload_{doc['name']}"
                )
                
                if uploaded_file is not None:
                    # Save the uploaded file
                    try:
                        with open(doc['name'], 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                        
                        st.success(f"✅ Uploaded {doc['name']}")
                        
                        # Automatically process the uploaded file
                        with st.spinner(f"Processing {doc['name']}..."):
                            from src.services.document_processor import process_document_simple
                            if process_document_simple(doc['name']):
                                st.success(f"✅ Successfully processed {doc['name']}")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to process {doc['name']}")
                    
                    except Exception as e:
                        st.error(f"Error uploading {doc['name']}: {e}")
        else:
            st.success("✅ All canonical documents are available")
        
        # Knowledge base statistics
        st.subheader("📈 Knowledge Base Statistics")
        
        try:
            startup = st.session_state.get('startup_instance')
            if startup:
                health_checker = startup.get_health_checker()
                health = health_checker.get_overall_health()
                
                kg_check = health['checks'].get('knowledge_graph', {})
                kg_details = kg_check.get('details', {})
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Nodes", kg_details.get('node_count', 0))
                
                with col2:
                    st.metric("Relationships", kg_details.get('relationship_count', 0))
                
                with col3:
                    node_types = kg_details.get('node_types', {})
                    st.metric("Node Types", len(node_types))
                
                if node_types:
                    st.write("**Node Types:**")
                    for node_type, count in node_types.items():
                        st.write(f"- {node_type}: {count}")
            
        except Exception as e:
            st.warning(f"Could not load knowledge base statistics: {e}")
        
    except Exception as e:
        st.error(f"Error loading knowledge base setup: {e}")
        logger.error(f"Knowledge base setup page error: {e}", exc_info=True)


def render_performance_monitor_page():
    """Render the performance monitoring page"""
    
    st.markdown("---")
    st.header("📈 Performance Monitor")
    
    try:
        startup = st.session_state.get('startup_instance')
        if not startup:
            st.error("Performance monitor not available")
            return
        
        performance_monitor = startup.get_performance_monitor()
        
        # Get current statistics
        stats = performance_monitor.get_current_statistics()
        
        # Overall metrics
        st.subheader("📊 Overall Performance")
        
        overall_stats = stats.get('overall_stats', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Processed", overall_stats.get('total_documents_processed', 0))
        
        with col2:
            st.metric("Successful", overall_stats.get('successful_processing', 0))
        
        with col3:
            st.metric("Failed", overall_stats.get('failed_processing', 0))
        
        with col4:
            st.metric("Target Violations", overall_stats.get('target_violations', 0))
        
        # Performance targets
        st.subheader("🎯 Performance Targets")
        
        targets = stats.get('performance_targets', [])
        if targets:
            for target in targets:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{target['name']}**: {target['description']}")
                with col2:
                    st.write(f"Target: {target['target_value']} {target['unit']}")
        else:
            st.info("No performance targets configured")
        
        # Recent processing
        st.subheader("📋 Recent Processing")
        
        recent_processing = stats.get('recent_processing', [])
        if recent_processing:
            for i, proc in enumerate(recent_processing):
                with st.expander(f"📄 {proc['document']} ({'✅' if proc['success'] else '❌'})", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Processing Time**: {proc.get('processing_time', 0):.2f}s")
                        st.write(f"**File Size**: {proc.get('file_size_mb', 0):.2f} MB")
                        if proc.get('page_count'):
                            st.write(f"**Pages**: {proc['page_count']}")
                    
                    with col2:
                        st.write("**Processing Stages**:")
                        stages = proc.get('stages', {})
                        for stage, duration in stages.items():
                            st.write(f"- {stage}: {duration:.2f}s")
        else:
            st.info("No recent processing data available")
        
        # Active processing
        active_count = stats.get('active_processing_count', 0)
        if active_count > 0:
            st.subheader("⚡ Active Processing")
            st.info(f"Currently processing {active_count} document(s)")
        
        # Performance report
        st.subheader("📈 Performance Report")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Generate Overall Report"):
                report = performance_monitor.get_processing_report()
                
                if 'error' not in report:
                    st.json(report)
                else:
                    st.error(report['error'])
        
        with col2:
            if st.button("💾 Export Metrics"):
                try:
                    export_path = f"logs/performance_metrics_{int(time.time())}.json"
                    performance_monitor.export_metrics(export_path)
                    st.success(f"Metrics exported to: {export_path}")
                except Exception as e:
                    st.error(f"Export failed: {e}")
        
        # Refresh button
        if st.button("🔄 Refresh Data"):
            st.rerun()
        
    except Exception as e:
        error_info = format_error_for_ui(e)
        st.error(f"Error loading performance monitor: {error_info['user_message']}")
        logger.error(f"Performance monitor page error: {e}", exc_info=True)


def render_system_status_page():
    """Render the system status page"""
    
    st.markdown("---")
    st.header("🔧 System Status")
    
    try:
        app = get_app()
        status = app.get_system_status()
        
        if status.get("error"):
            st.error(f"System status error: {status['error']}")
            return
        
        # Overall status
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("System Status", "🟢 Online" if status['initialized'] else "🔴 Offline")
        
        with col2:
            st.metric("Total Documents", status['storage']['total_documents'])
        
        with col3:
            st.metric("Queue Size", status['workflow']['queue_size'])
        
        # Detailed information
        st.subheader("📊 Storage Statistics")
        storage_stats = status['storage']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Documents by Status:**")
            for status_name, count in storage_stats['documents_by_status'].items():
                st.write(f"- {status_name}: {count}")
        
        with col2:
            st.write("**Processing Jobs by Status:**")
            for status_name, count in storage_stats['jobs_by_status'].items():
                st.write(f"- {status_name}: {count}")
        
        # Database information
        st.subheader("🗄️ Database Information")
        db_info = status['database']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Path:** `{db_info['path']}`")
            st.write(f"**Size:** {db_info['size_bytes']:,} bytes")
        
        with col2:
            st.write("**Tables:**")
            for table, count in db_info['tables'].items():
                st.write(f"- {table}: {count} records")
        
        # Configuration
        st.subheader("⚙️ Configuration")
        config_info = status['config']
        app_config_info = st.session_state.get('app_config', app_config)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Max File Size:** {config_info['max_file_size_mb']} MB")
            st.write(f"**Debug Mode:** {'✅' if config_info['debug_mode'] else '❌'}")
            if hasattr(app_config_info, 'embedding_provider'):
                st.write(f"**Embedding Provider:** {app_config_info.embedding_provider}")
        
        with col2:
            st.write(f"**API Configured:** {'✅' if config_info['api_key_configured'] else '❌'}")
            st.write(f"**Allowed Types:** {', '.join(config_info['allowed_file_types'])}")
            if hasattr(app_config_info, 'qa_provider'):
                st.write(f"**QA Provider:** {app_config_info.qa_provider}")
                st.write(f"**Knowledge Graph:** {'✅' if app_config_info.enable_knowledge_graph else '❌'}")
        
        # Workflow status
        st.subheader("🔄 Workflow Status")
        workflow_info = status['workflow']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Queue Size", workflow_info['queue_size'])
        
        with col2:
            st.metric("Active Jobs", workflow_info['active_jobs'])
        
        with col3:
            st.metric("Manager Running", "✅" if workflow_info['running'] else "❌")
        
        # Refresh button
        if st.button("🔄 Refresh Status"):
            st.session_state.pop('system_status_checked', None)
            st.rerun()
        
    except Exception as e:
        error_info = format_error_for_ui(e)
        st.error(f"Error loading system status: {error_info['user_message']}")
        logger.error(f"System status page error: {e}", exc_info=True)


def render_migration_page():
    """Render the data migration page"""
    
    st.markdown("---")
    st.header("🔄 Data Migration")
    
    st.markdown("""
    This page helps you migrate existing data to the new knowledge graph schema while maintaining backward compatibility.
    """)
    
    try:
        # Import migration manager
        from scripts.migrate_existing_data import DataMigrationManager
        
        migration_manager = DataMigrationManager()
        
        # Show current migration status
        st.subheader("📊 Migration Status")
        
        if st.button("🔍 Analyze Current Data", type="secondary"):
            with st.spinner("Analyzing existing data..."):
                try:
                    analysis_result = migration_manager.run_migration(dry_run=True)
                    
                    if analysis_result.get('success'):
                        analysis = analysis_result['analysis']
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Total Documents", analysis['documents'])
                            st.metric("Processed Documents", analysis['processed_documents'])
                        
                        with col2:
                            st.metric("Q&A Sessions", analysis['qa_sessions'])
                            st.metric("Q&A Interactions", analysis['qa_interactions'])
                        
                        with col3:
                            st.metric("Documents with Embeddings", analysis['documents_with_embeddings'])
                            st.metric("Documents with Analysis", analysis['documents_with_analysis'])
                        
                        # Show migration recommendations
                        st.subheader("📋 Migration Recommendations")
                        
                        if analysis['processed_documents'] > 0:
                            st.success(f"✅ {analysis['processed_documents']} documents ready for migration")
                        
                        if analysis['documents_with_embeddings'] > 0:
                            st.info(f"ℹ️ {analysis['documents_with_embeddings']} documents have embeddings that will be preserved")
                        
                        if analysis['kg_tables_exist']:
                            st.warning("⚠️ Knowledge graph tables already exist. Migration will update existing data.")
                        else:
                            st.info("ℹ️ Knowledge graph tables will be created during migration.")
                        
                        # Store analysis in session state
                        st.session_state.migration_analysis = analysis_result
                        
                    else:
                        st.error(f"Analysis failed: {analysis_result.get('error')}")
                        
                except Exception as e:
                    st.error(f"Error during analysis: {e}")
        
        # Migration controls
        st.subheader("🚀 Migration Controls")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("▶️ Run Migration", type="primary"):
                with st.spinner("Running data migration..."):
                    try:
                        migration_result = migration_manager.run_migration(dry_run=False)
                        
                        if migration_result.get('success'):
                            st.success("✅ Migration completed successfully!")
                            
                            # Show migration results
                            with st.expander("Migration Results", expanded=True):
                                st.json(migration_result)
                            
                            # Clear migration needed flag
                            st.session_state.migration_needed = False
                            
                        else:
                            st.error(f"❌ Migration failed: {migration_result.get('error')}")
                            
                    except Exception as e:
                        st.error(f"Error during migration: {e}")
        
        with col2:
            if st.button("🔄 Rollback Migration", type="secondary"):
                if st.session_state.get('confirm_rollback'):
                    with st.spinner("Rolling back migration..."):
                        try:
                            rollback_result = migration_manager.rollback_migration()
                            
                            if rollback_result.get('success'):
                                st.success("✅ Migration rollback completed!")
                                st.session_state.confirm_rollback = False
                            else:
                                st.error(f"❌ Rollback failed: {rollback_result.get('error')}")
                                
                        except Exception as e:
                            st.error(f"Error during rollback: {e}")
                else:
                    st.warning("⚠️ This will remove all knowledge graph data!")
                    if st.button("Confirm Rollback"):
                        st.session_state.confirm_rollback = True
                        st.rerun()
        
        with col3:
            if st.button("📊 Check Status"):
                st.rerun()
        
        # Show migration log if available
        if st.session_state.get('migration_analysis'):
            with st.expander("Migration Log", expanded=False):
                migration_log = st.session_state.migration_analysis.get('migration_log', [])
                for log_entry in migration_log:
                    st.text(log_entry)
        
        # Migration help
        st.subheader("❓ Migration Help")
        
        with st.expander("What does migration do?", expanded=False):
            st.markdown("""
            **Data migration converts your existing documents to the new knowledge graph format:**
            
            1. **Document Nodes**: Creates knowledge graph nodes for each processed document
            2. **Section Nodes**: Extracts document sections and creates relationships
            3. **Q&A Context**: Links Q&A sessions to document nodes
            4. **Embeddings**: Preserves existing embeddings for semantic search
            5. **Relationships**: Creates connections between related entities
            
            **Your original data is preserved** - migration only adds new knowledge graph structures.
            """)
        
        with st.expander("When should I migrate?", expanded=False):
            st.markdown("""
            **You should run migration if:**
            
            - You have existing processed documents
            - You want to use the new knowledge graph features
            - You want enhanced Q&A capabilities
            - You want to generate QME templates
            
            **Migration is safe** - it doesn't modify your existing data, only adds new structures.
            """)
        
    except ImportError:
        st.error("Migration tools not available. Please ensure the migration script is properly installed.")
    except Exception as e:
        error_info = format_error_for_ui(e)
        st.error(f"Error loading migration page: {error_info['user_message']}")
        logger.error(f"Migration page error: {e}", exc_info=True)


def render_about_page():
    """Render the about page"""
    
    st.markdown("---")
    
    st.markdown("""
    ## About Document Q&A System
    
    This system allows you to upload documents and ask intelligent questions about their content using AI-powered analysis with advanced knowledge graph capabilities.
    
    ### Current Features
    - ✅ **File Upload**: Support for PDF, TXT, and DOCX formats
    - ✅ **File Validation**: Format and size validation (configurable)
    - ✅ **Text Extraction**: Intelligent text extraction from various formats
    - ✅ **Knowledge Graph**: Advanced document relationship mapping and entity extraction
    - ✅ **Multiple AI Providers**: Support for Gemini, OpenAI, and local models
    - ✅ **Hybrid Q&A**: Combines vector search with knowledge graph traversal
    - ✅ **Document Storage**: Persistent document management with SQLite
    - ✅ **Q&A Engine**: Ask intelligent questions with source citations
    - ✅ **Context Search**: Find relevant information quickly across documents
    - ✅ **Document Management**: View, organize, and delete processed documents
    - ✅ **Chat Interface**: Interactive Q&A with conversation history
    - ✅ **Real-time Processing**: Progress tracking and status updates
    - ✅ **Error Handling**: Comprehensive error handling and recovery
    - ✅ **Logging**: Detailed logging for debugging and monitoring
    - ✅ **Data Migration**: Backward compatibility with existing data
    - ✅ **Configuration Management**: Environment-based configuration
    
    ### How It Works
    1. **Upload**: Upload your documents through the web interface
    2. **Process**: Documents are analyzed using configurable AI providers (Gemini, OpenAI, or local models)
    3. **Extract**: Knowledge graph extraction identifies entities, relationships, and document structure
    4. **Store**: Processed results are stored with embeddings and knowledge graph nodes for fast retrieval
    5. **Query**: Ask questions and get intelligent answers using hybrid search with source citations
    
    ### Supported File Formats
    - **PDF**: Portable Document Format files
    - **TXT**: Plain text files (various encodings supported)
    - **DOCX**: Microsoft Word documents
    
    ### Technical Details
    - Built with Streamlit for the web interface
    - Clean architecture with Factory, Strategy, Repository, and Command patterns
    - Knowledge graph implementation with SQLite backend
    - Multiple AI provider support (Gemini, OpenAI, local models)
    - Hybrid Q&A combining vector similarity and graph traversal
    - SQLite database for document, knowledge graph, and session storage
    - Context-aware question answering with source attribution
    - Comprehensive error handling and validation
    - Centralized logging and monitoring
    - Circuit breaker pattern for API resilience
    - Retry logic with exponential backoff
    - Data migration tools for backward compatibility
    - Environment-based configuration management
    
    ### Getting Started
    1. Go to **Upload Documents** to add your first document
    2. Wait for processing to complete (you'll see progress updates)
    3. Use **Document Management** to view and manage your documents
    4. Use **Q&A Interface** to ask questions about processed documents
    5. Check **System Status** to monitor system health
    
    ### Error Handling
    The system includes comprehensive error handling:
    - File upload validation and error recovery
    - API failure handling with retry logic
    - Database transaction safety
    - Workflow error recovery
    - User-friendly error messages
    - Detailed logging for debugging
    """)

if __name__ == "__main__":
    main()