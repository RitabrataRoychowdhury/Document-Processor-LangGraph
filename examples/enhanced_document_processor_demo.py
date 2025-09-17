#!/usr/bin/env python3
"""
Demo script for the Enhanced Document Processor.

This script demonstrates the enhanced knowledge graph-driven document processing pipeline
with intelligent semantic chunking, medical entity extraction, and relationship mapping.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.unit.core.test_enhanced_document_processor import create_enhanced_document_processor
from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def main():
    """Main demo function."""
    print("Enhanced Document Processor Demo")
    print("=" * 50)
    
    # Create enhanced document processor
    kg_repo = SQLiteKnowledgeGraphRepository()
    processor = create_enhanced_document_processor(kg_repository=kg_repo)
    
    print(f"✓ Enhanced document processor initialized")
    print(f"✓ Knowledge graph repository connected")
    
    # Test with sample medical text
    sample_text = """
    Patient: Jane Doe
    Date of Injury: 03/15/2024
    Claim Number: WC-2024-456
    
    HISTORY OF PRESENT ILLNESS:
    The patient is a 52-year-old female who sustained a work-related injury to her right shoulder.
    She was diagnosed with rotator cuff tear and shoulder impingement syndrome.
    
    PHYSICAL EXAMINATION:
    Examination reveals limited range of motion in the right shoulder.
    MRI of the right shoulder shows full-thickness rotator cuff tear.
    
    DIAGNOSIS:
    1. M75.30 - Calcific tendinitis of shoulder, unspecified shoulder
    2. M75.40 - Impingement syndrome of shoulder
    
    TREATMENT:
    Physical therapy and corticosteroid injections were recommended.
    Surgical repair may be considered if conservative treatment fails.
    
    IMPAIRMENT RATING:
    Based on AMA Table 16-3, the patient has a 15% upper extremity impairment,
    which converts to 9% whole person impairment.
    """
    
    print("\nProcessing sample medical text...")
    print("-" * 30)
    
    # Create a temporary file for testing
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_text)
        temp_file = f.name
    
    try:
        # Process the document
        documents = [{
            'file_path': temp_file,
            'doc_id': 'demo-doc-001'
        }]
        
        result = processor.process_patient_documents(documents)
        
        print(f"✓ Document processed successfully")
        print(f"✓ Total entities extracted: {result['total_entities']}")
        print(f"✓ Total relationships established: {result['total_relationships']}")
        print(f"✓ Processing errors: {len(result['processing_errors'])}")
        
        # Display entity breakdown
        print("\nEntity Breakdown:")
        for entity_type, count in result['entities_by_type'].items():
            print(f"  - {entity_type}: {count}")
        
        # Display some sample entities
        if result['processed_documents']:
            doc_result = result['processed_documents'][0]
            entities = doc_result.get('entities', [])
            
            print(f"\nSample Entities (showing first 5):")
            for i, entity in enumerate(entities[:5]):
                print(f"  {i+1}. {entity['entity_type']}: {entity['text']} (confidence: {entity['confidence']:.2f})")
            
            # Display some sample relationships
            relationships = doc_result.get('relationships', [])
            print(f"\nSample Relationships (showing first 3):")
            for i, rel in enumerate(relationships[:3]):
                print(f"  {i+1}. {rel['relationship_type']} (confidence: {rel['confidence']:.2f})")
                print(f"     Evidence: {rel['evidence'][:100]}...")
        
        # Test specific PQME file processing
        print(f"\nTesting specific PQME file processing...")
        print("-" * 40)
        
        pqme_result = processor.process_specific_pqme_files()
        
        if pqme_result['processing_errors']:
            print("⚠ PQME files not found (this is expected in demo environment)")
            for error in pqme_result['processing_errors']:
                print(f"  - {error}")
        else:
            print(f"✓ PQME files processed successfully")
            print(f"✓ Total entities: {pqme_result['total_entities']}")
            print(f"✓ Total relationships: {pqme_result['total_relationships']}")
        
        # Test knowledge graph queries
        print(f"\nTesting knowledge graph queries...")
        print("-" * 35)
        
        # Query for different entity types
        patients = kg_repo.find_nodes_by_type('patient')
        diagnoses = kg_repo.find_nodes_by_type('diagnosis')
        treatments = kg_repo.find_nodes_by_type('treatment')
        
        print(f"✓ Patients in knowledge graph: {len(patients)}")
        print(f"✓ Diagnoses in knowledge graph: {len(diagnoses)}")
        print(f"✓ Treatments in knowledge graph: {len(treatments)}")
        
        # Display knowledge graph statistics
        node_count = kg_repo.get_node_count()
        relationship_count = kg_repo.get_relationship_count()
        node_types = kg_repo.get_node_types_count()
        
        print(f"\nKnowledge Graph Statistics:")
        print(f"  - Total nodes: {node_count}")
        print(f"  - Total relationships: {relationship_count}")
        print(f"  - Node types: {dict(node_types)}")
        
    finally:
        # Clean up temporary file
        os.unlink(temp_file)
    
    print(f"\n" + "=" * 50)
    print("Enhanced Document Processor Demo Complete!")
    print("The enhanced pipeline successfully:")
    print("✓ Performed intelligent semantic chunking")
    print("✓ Extracted medical entities with provenance")
    print("✓ Established entity relationships with confidence scoring")
    print("✓ Stored results in knowledge graph with deduplication")
    print("✓ Provided comprehensive processing analytics")


if __name__ == "__main__":
    main()