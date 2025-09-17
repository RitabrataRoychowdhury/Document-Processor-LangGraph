#!/usr/bin/env python3
"""Script to initialize knowledge base with canonical medical documents."""

import os
import sys
import argparse
from datetime import datetime

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.infrastructure.knowledge.knowledge_base_initializer import KnowledgeBaseInitializer
from utils.logging_config import get_logger

logger = get_logger(__name__)


def main():
    """Main initialization function."""
    parser = argparse.ArgumentParser(description='Initialize knowledge base with canonical documents')
    parser.add_argument('--base-path', help='Base path for documents', default='.')
    parser.add_argument('--force', action='store_true', help='Force re-processing of existing documents')
    parser.add_argument('--status-only', action='store_true', help='Show initialization status only')
    
    args = parser.parse_args()
    
    try:
        # Create initializer
        initializer = KnowledgeBaseInitializer(args.base_path)
        
        if args.status_only:
            # Show current status
            status = initializer.get_initialization_status()
            print(f"\n📊 Knowledge Base Initialization Status")
            print(f"{'='*50}")
            print(f"Overall Status: {'✅ Initialized' if status['initialized'] else '❌ Not Initialized'}")
            
            print(f"\n📋 Document Status:")
            for doc_key, doc_status in status['documents'].items():
                status_icon = {
                    'completed': '✅',
                    'processing': '🔄', 
                    'failed': '❌',
                    'not_processed': '⏳'
                }.get(doc_status['status'], '❓')
                
                print(f"  {status_icon} {doc_status['title']}")
                print(f"     Status: {doc_status['status']}")
                if doc_status['document_id']:
                    print(f"     Document ID: {doc_status['document_id']}")
                print()
            
            return 0
        
        # Check if already initialized (unless force flag is used)
        if not args.force and initializer.is_knowledge_base_initialized():
            logger.info("Knowledge base already initialized. Use --force to re-process.")
            print("✅ Knowledge base already initialized!")
            print("Use --status-only to see details or --force to re-process.")
            return 0
        
        # Initialize knowledge base
        print("🚀 Starting knowledge base initialization...")
        print("This may take several minutes depending on document size.")
        
        start_time = datetime.now()
        results = initializer.initialize_knowledge_base()
        end_time = datetime.now()
        
        # Display results
        print(f"\n📊 Initialization Results")
        print(f"{'='*50}")
        print(f"Processing Time: {end_time - start_time}")
        print(f"Documents Processed: {len(results['processed_documents'])}")
        print(f"Total Sections Created: {results['total_sections']}")
        print(f"Total Entities Extracted: {results['total_entities']}")
        
        if results['errors']:
            print(f"\n❌ Errors ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"  • {error}")
        
        print(f"\n📋 Document Details:")
        for doc_result in results['processed_documents']:
            status_icon = '✅' if doc_result['status'] == 'processed' else '⏭️'
            print(f"  {status_icon} Document ID: {doc_result['document_id']}")
            print(f"     Status: {doc_result['status']}")
            print(f"     Sections: {doc_result['sections_created']}")
            print(f"     Entities: {doc_result['entities_extracted']}")
            print()
        
        if len(results['processed_documents']) > 0 and not results['errors']:
            print("✅ Knowledge base initialization completed successfully!")
        elif results['errors']:
            print("⚠️  Knowledge base initialization completed with errors.")
            return 1
        else:
            print("❌ Knowledge base initialization failed.")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)