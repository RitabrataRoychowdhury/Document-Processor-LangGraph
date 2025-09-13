#!/usr/bin/env python3
"""
Demonstration of the Command Pattern implementation for document processing.

This script shows how to use the command pattern to process documents
with retry logic and comprehensive logging.
"""

import os
import sys
import tempfile
import logging

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.commands.ingest_command import IngestCommand
from src.commands.ner_command import NERCommand
from src.commands.kg_populate_command import KGPopulateCommand
from src.workflow.workflow_manager import WorkflowManager

# Set up logging to see the command execution details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_sample_document():
    """Create a sample document for testing."""
    content = """
    Patient: John Doe
    Date of Birth: 01/15/1980
    Date of Examination: 09/13/2025
    
    HISTORY OF PRESENT ILLNESS:
    The patient is a 45-year-old male who sustained a work-related injury to his lower back
    on 03/15/2024. He reports chronic lower back pain with radiation to the left leg.
    
    PHYSICAL EXAMINATION:
    The patient appears in mild distress. Range of motion in the lumbar spine is limited.
    Straight leg raise test is positive on the left at 45 degrees.
    
    DIAGNOSIS:
    1. Lumbar disc herniation at L4-L5
    2. Chronic lower back pain
    3. Left-sided sciatica
    
    IMPAIRMENT RATING:
    Based on the AMA Guides 5th Edition, the patient has a 15% whole person impairment
    rating for the lumbar spine condition.
    
    RECOMMENDATIONS:
    Continue physical therapy and consider epidural steroid injection.
    """
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    temp_file.write(content)
    temp_file.close()
    
    return temp_file.name


def demonstrate_individual_commands():
    """Demonstrate executing individual commands."""
    logger.info("=== Demonstrating Individual Commands ===")
    
    # Create sample document
    file_path = create_sample_document()
    logger.info(f"Created sample document: {file_path}")
    
    try:
        # 1. Ingest Command
        logger.info("\n1. Executing Ingest Command...")
        ingest_command = IngestCommand(file_path=file_path)
        ingest_result = ingest_command.execute_with_retry(max_attempts=2)
        
        if ingest_result.success:
            logger.info(f"✓ Ingest successful: {ingest_result.message}")
            document_id = ingest_result.data.get('document_id')
            logger.info(f"  Document ID: {document_id}")
            logger.info(f"  Text length: {ingest_result.data.get('text_length')} characters")
        else:
            logger.error(f"✗ Ingest failed: {ingest_result.message}")
            return
        
        # 2. NER Command
        logger.info("\n2. Executing NER Command...")
        ner_command = NERCommand(document_id=document_id)
        ner_result = ner_command.execute_with_retry(max_attempts=2)
        
        if ner_result.success:
            logger.info(f"✓ NER successful: {ner_result.message}")
            logger.info(f"  Entities found: {ner_result.data.get('entities_count')}")
            logger.info(f"  Entity types: {ner_result.data.get('entity_types')}")
        else:
            logger.error(f"✗ NER failed: {ner_result.message}")
            return
        
        # 3. KG Populate Command
        logger.info("\n3. Executing KG Populate Command...")
        kg_command = KGPopulateCommand(document_id=document_id)
        kg_result = kg_command.execute_with_retry(max_attempts=2)
        
        if kg_result.success:
            logger.info(f"✓ KG Population successful: {kg_result.message}")
            logger.info(f"  Nodes created: {kg_result.data.get('nodes_created')}")
            logger.info(f"  Relationships created: {kg_result.data.get('relationships_created')}")
        else:
            logger.error(f"✗ KG Population failed: {kg_result.message}")
        
    finally:
        # Clean up
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")


def demonstrate_workflow_manager():
    """Demonstrate using the workflow manager with command pattern."""
    logger.info("\n=== Demonstrating Workflow Manager ===")
    
    # Create sample document
    file_path = create_sample_document()
    logger.info(f"Created sample document: {file_path}")
    
    try:
        # Create workflow manager
        workflow_manager = WorkflowManager()
        
        # Submit document for processing
        logger.info("\nSubmitting document for processing...")
        job_id = workflow_manager.submit_document_for_processing(file_path)
        logger.info(f"Job submitted with ID: {job_id}")
        
        # Check queue status
        status = workflow_manager.get_queue_status()
        logger.info(f"Queue status: {status}")
        
        # Note: In a real scenario, you would start the workflow manager
        # and let it process jobs asynchronously. For this demo, we'll
        # show how to create and execute commands manually.
        
        logger.info("\nDemonstrating manual command execution...")
        
        # Create commands manually
        ingest_cmd = workflow_manager._create_command('ingest', file_path=file_path)
        logger.info(f"Created ingest command: {ingest_cmd.command_id}")
        
        # Execute with logging
        result = workflow_manager.execute_single_command(ingest_cmd)
        logger.info(f"Command result: Success={result.success}, Message={result.message}")
        
        if result.success and 'document_id' in result.data:
            document_id = result.data['document_id']
            
            # Create and execute NER command
            ner_cmd = workflow_manager._create_command('ner', document_id=document_id)
            ner_result = workflow_manager.execute_single_command(ner_cmd)
            logger.info(f"NER result: Success={ner_result.success}")
            
            if ner_result.success:
                # Create and execute KG populate command
                kg_cmd = workflow_manager._create_command('kg_populate', document_id=document_id)
                kg_result = workflow_manager.execute_single_command(kg_cmd)
                logger.info(f"KG result: Success={kg_result.success}")
        
        # Show command history
        history = workflow_manager.get_command_history()
        logger.info(f"Command history contains {len(history)} entries")
        
    finally:
        # Clean up
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")


def demonstrate_retry_logic():
    """Demonstrate retry logic with a failing command."""
    logger.info("\n=== Demonstrating Retry Logic ===")
    
    # Create a command that will fail (non-existent file)
    logger.info("Creating command with non-existent file to demonstrate retry...")
    
    try:
        ingest_command = IngestCommand(file_path="/nonexistent/file.txt")
    except Exception as e:
        logger.info(f"✓ Command creation failed as expected: {e}")
        logger.info("This demonstrates non-retryable errors (file not found)")
    
    # For retryable errors, we would need to mock the underlying services
    # to simulate temporary failures. This is covered in the unit tests.
    logger.info("Retryable error scenarios are covered in unit tests")


def main():
    """Main demonstration function."""
    logger.info("Command Pattern Implementation Demonstration")
    logger.info("=" * 50)
    
    try:
        demonstrate_individual_commands()
        demonstrate_workflow_manager()
        demonstrate_retry_logic()
        
        logger.info("\n" + "=" * 50)
        logger.info("✓ Command pattern demonstration completed successfully!")
        logger.info("\nKey features demonstrated:")
        logger.info("- Command pattern with base Command interface")
        logger.info("- Concrete command implementations (Ingest, NER, KG Populate)")
        logger.info("- Retry logic with exponential backoff")
        logger.info("- Comprehensive logging and error handling")
        logger.info("- Workflow manager integration")
        logger.info("- Command result standardization")
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())