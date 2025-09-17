#!/usr/bin/env python3
"""
Test script for enhanced knowledge base initialization.

This script tests the complete knowledge base initialization system
for the evidence-first QME workflow.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.knowledge.knowledge_base_initializer import KnowledgeBaseInitializer, initialize_complete_system_for_option_2
from src.config.app_config import AppConfig


class MockIngestionPipeline:
    """Mock ingestion pipeline for testing."""
    
    def __init__(self, config):
        self.config = config
        from src.storage.database import DatabaseManager
        from src.repositories.document_repository import SQLiteDocumentRepository
        self.db_manager = DatabaseManager(config.database_path)
        self.doc_repository = SQLiteDocumentRepository(self.db_manager)
    
    async def process_document(self, doc_path):
        """Mock document processing that creates actual document records."""
        try:
            from src.models.document import Document
            from pathlib import Path
            import uuid
            from datetime import datetime
            
            # Create a mock document record
            file_path = Path(doc_path)
            doc = Document(
                id=str(uuid.uuid4()),
                title=file_path.name,
                file_type=file_path.suffix.lower(),
                file_size=file_path.stat().st_size if file_path.exists() else 1000,
                upload_timestamp=datetime.now(),
                processing_status='completed',
                original_text=f"Mock processed content for {file_path.name}",
                document_type='medical',
                extracted_info={"mock": "data", "processed": True},
                analysis=f"Mock analysis for {file_path.name}",
                summary=f"Mock summary for {file_path.name}"
            )
            
            # Save the document
            self.doc_repository.save(doc)
            
            return type('Result', (), {
                'success': True,
                'error_message': None
            })()
            
        except Exception as e:
            return type('Result', (), {
                'success': False,
                'error_message': str(e)
            })()


async def test_complete_initialization():
    """Test complete knowledge base initialization."""
    print("🧪 Testing Complete Knowledge Base Initialization")
    print("=" * 60)
    
    try:
        # Initialize configuration
        print("🔧 Loading configuration...")
        config = AppConfig.from_env()
        
        # Initialize ingestion pipeline
        print("🔧 Setting up ingestion pipeline...")
        pipeline = MockIngestionPipeline(config)
        
        # Create initializer
        print("🔧 Creating knowledge base initializer...")
        initializer = KnowledgeBaseInitializer(config, pipeline)
        
        # Test initialization progress before
        print("\n📊 Initial Status:")
        progress = initializer.get_initialization_progress()
        print(f"  Node count: {progress['node_count']}")
        print(f"  Relationship count: {progress['relationship_count']}")
        print(f"  Overall progress: {progress['overall_progress_percentage']:.1f}%")
        
        # Run complete initialization
        print("\n🚀 Running complete initialization...")
        result = await initializer.initialize_complete_knowledge_base()
        
        # Display results
        print("\n📊 Initialization Results:")
        print("=" * 40)
        print(f"Success: {'✅ YES' if result.success else '❌ NO'}")
        print(f"Processing Time: {result.total_processing_time:.2f} seconds")
        print(f"Processed Documents: {len(result.processed_documents)}")
        print(f"Failed Documents: {len(result.failed_documents)}")
        print(f"Knowledge Graph Nodes: {result.node_count}")
        print(f"Knowledge Graph Relationships: {result.relationship_count}")
        print(f"Entity Types: {len(result.entity_types) if result.entity_types else 0}")
        print(f"AMA Tables Loaded: {result.ama_tables_loaded}")
        print(f"Legal Patterns Loaded: {result.legal_patterns_loaded}")
        print(f"Validation Passed: {'✅ YES' if result.validation_passed else '❌ NO'}")
        print(f"System Ready: {'✅ YES' if result.system_ready else '❌ NO'}")
        
        if result.processed_documents:
            print(f"\n📄 Processed Documents:")
            for doc in result.processed_documents:
                print(f"  ✅ {doc}")
        
        if result.failed_documents:
            print(f"\n❌ Failed Documents:")
            for doc in result.failed_documents:
                print(f"  ❌ {doc}")
        
        if result.error_messages:
            print(f"\n⚠️  Issues Found:")
            for error in result.error_messages:
                print(f"  - {error}")
        
        # Test status reporting
        print("\n📋 Getting status report...")
        status_report = await initializer.get_initialization_status_report()
        
        print(f"\n📊 Status Report:")
        print("=" * 40)
        print(f"Overall Status: {status_report['overall_status']}")
        print(f"System Ready: {status_report['system_readiness']['ready']}")
        print(f"Confidence: {status_report['system_readiness']['confidence']}")
        
        # Knowledge graph stats
        kg_stats = status_report['knowledge_graph']
        print(f"\n🔗 Knowledge Graph:")
        print(f"  Nodes: {kg_stats['total_nodes']} ({kg_stats['node_count_status']})")
        print(f"  Relationships: {kg_stats['total_relationships']} ({kg_stats['relationship_count_status']})")
        print(f"  Node Types: {len(kg_stats['node_types'])}")
        
        # AMA components
        ama_stats = status_report['ama_components']
        print(f"\n📚 AMA Components:")
        print(f"  Tables: {ama_stats['tables_loaded']} ({ama_stats['tables_status']})")
        
        # QME patterns
        qme_stats = status_report['qme_patterns']
        print(f"\n⚖️  QME Patterns:")
        print(f"  Legal Patterns: {qme_stats['legal_patterns']}")
        print(f"  Structure Patterns: {qme_stats['structure_patterns']}")
        print(f"  Quality Standards: {qme_stats['quality_standards']}")
        print(f"  Status: {qme_stats['patterns_status']}")
        
        # Validation details
        validation = status_report['validation']
        print(f"\n✅ Validation:")
        print(f"  Overall Valid: {'✅ YES' if validation['overall_valid'] else '❌ NO'}")
        if validation['issues']:
            print(f"  Issues: {len(validation['issues'])}")
            for issue in validation['issues'][:3]:  # Show first 3 issues
                print(f"    - {issue}")
        
        # Next steps
        next_steps = status_report['system_readiness']['next_steps']
        print(f"\n🎯 Next Steps:")
        for step in next_steps[:3]:  # Show first 3 steps
            print(f"  • {step}")
        
        print("\n" + "=" * 60)
        if result.system_ready:
            print("🎉 Knowledge base initialization test completed successfully!")
            print("   System is ready for evidence-first QME processing.")
        else:
            print("⚠️  Knowledge base initialization test completed with issues.")
            print("   Please review the issues above.")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_validation_thresholds():
    """Test validation threshold checking."""
    print("\n🧪 Testing Validation Thresholds")
    print("=" * 40)
    
    try:
        config = AppConfig.from_env()
        pipeline = MockIngestionPipeline(config)
        initializer = KnowledgeBaseInitializer(config, pipeline)
        
        # Test validation
        validation_result = await initializer._validate_complete_initialization()
        
        print(f"Node Count Valid: {'✅' if validation_result.node_count_valid else '❌'}")
        print(f"Relationship Count Valid: {'✅' if validation_result.relationship_count_valid else '❌'}")
        print(f"Required Entities Present: {'✅' if validation_result.required_entities_present else '❌'}")
        print(f"AMA Tables Accessible: {'✅' if validation_result.ama_tables_accessible else '❌'}")
        print(f"Legal Patterns Accessible: {'✅' if validation_result.legal_patterns_accessible else '❌'}")
        print(f"Canonical Documents Processed: {'✅' if validation_result.canonical_documents_processed else '❌'}")
        print(f"Overall Valid: {'✅' if validation_result.overall_valid else '❌'}")
        
        if validation_result.issues:
            print(f"\nIssues ({len(validation_result.issues)}):")
            for issue in validation_result.issues:
                print(f"  - {issue}")
        
        if validation_result.recommendations:
            print(f"\nRecommendations ({len(validation_result.recommendations)}):")
            for rec in validation_result.recommendations:
                print(f"  • {rec}")
        
        return validation_result.overall_valid
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🧪 Knowledge Base Initialization Test Suite")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("src/services/knowledge_base_initializer.py").exists():
        print("❌ Please run this script from the project root directory")
        return False
    
    # Check for canonical documents
    canonical_docs = [
        "AMAGuides 5th Edition.pdf",
        "QME-Study-Guide.pdf", 
        "Sample3.pdf"
    ]
    
    found_docs = []
    missing_docs = []
    
    for doc in canonical_docs:
        if Path(doc).exists():
            found_docs.append(doc)
        else:
            missing_docs.append(doc)
    
    print(f"\n📚 Canonical Documents Check:")
    for doc in found_docs:
        print(f"  ✅ {doc}")
    for doc in missing_docs:
        print(f"  ❌ {doc} (missing)")
    
    if len(found_docs) == 0:
        print("\n⚠️  No canonical documents found.")
        print("   The test will still run but may show limited results.")
    
    # Run tests
    async def run_tests():
        success = True
        
        # Test complete initialization
        init_success = await test_complete_initialization()
        success = success and init_success
        
        # Test validation thresholds
        validation_success = await test_validation_thresholds()
        success = success and validation_success
        
        return success
    
    # Run async tests
    test_success = asyncio.run(run_tests())
    
    print("\n" + "=" * 60)
    if test_success:
        print("🎉 All tests passed! Knowledge base initialization is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the output above.")
    
    return test_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)