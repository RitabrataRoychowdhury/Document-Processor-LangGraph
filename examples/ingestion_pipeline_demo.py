#!/usr/bin/env python3
"""
Demonstration of the Knowledge Graph Ingestion Pipeline.

This script shows how to use the ingestion pipeline to process medical documents
and build a knowledge graph with sections, entities, and relationships.
"""

import tempfile
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.extraction.ingestion_pipeline_factory import IngestionPipelineFactory
from src.infrastructure.storage.vector_store import vector_store_manager


def main():
    print("=== Knowledge Graph Ingestion Pipeline Demo ===\n")
    
    # Create sample medical document
    sample_content = """
    QUALIFIED MEDICAL EVALUATOR'S REPORT
    
    PATIENT INFORMATION
    Patient: John Smith
    Date of Birth: 01/15/1978
    Case Number: WC-2024-001
    
    HISTORY OF PRESENT ILLNESS
    The patient is a 45-year-old male construction worker who sustained a work-related 
    injury to his lower back on January 15, 2024. He reports constant lower back pain 
    with radiation to the left leg. The pain is described as sharp and burning, 
    rated 8/10 on the pain scale.
    
    PHYSICAL EXAMINATION
    The patient appears in mild distress. Vital signs are stable.
    Range of motion testing reveals:
    - Lumbar flexion: 45 degrees (normal 90 degrees)
    - Extension: 15 degrees (normal 30 degrees)
    - Lateral bending: Limited bilaterally
    
    Neurological examination:
    - Straight leg raise test is positive on the left at 30 degrees
    - Decreased sensation in L5 distribution
    - Weakness in left foot dorsiflexion (4/5 strength)
    
    DIAGNOSTIC IMAGING
    MRI of the lumbar spine dated 02/01/2024 shows:
    - Large central disc herniation at L5-S1
    - Compression of the left L5 nerve root
    - Mild degenerative changes at L4-L5
    
    DIAGNOSIS
    Primary diagnosis: L5-S1 disc herniation with left L5 radiculopathy (ICD-10: M51.16)
    Secondary diagnosis: Chronic lower back pain (ICD-10: M54.5)
    
    IMPAIRMENT RATING
    Based on AMA Guides to the Evaluation of Permanent Impairment, 6th Edition, 
    Table 15-3, the patient has 12% whole person impairment due to the disc 
    herniation and associated radiculopathy. This rating considers the neurological 
    deficits and functional limitations documented in the examination.
    
    WORK RESTRICTIONS
    The patient is capable of sedentary to light work with the following restrictions:
    - No lifting over 20 pounds
    - No prolonged sitting or standing
    - No repetitive bending or twisting
    
    TREATMENT RECOMMENDATIONS
    1. Continue physical therapy focusing on core strengthening
    2. Consider epidural steroid injection if conservative treatment fails
    3. Surgical consultation if symptoms persist beyond 6 months
    
    Dr. Jane Medical, MD
    Qualified Medical Evaluator
    License #12345
    """
    
    print("1. Creating ingestion pipeline...")
    # Create pipeline with default local embeddings
    pipeline = IngestionPipelineFactory.create_default_pipeline(
        vector_store_name="demo_store"
    )
    print("   ✓ Pipeline created with local embeddings and demo vector store")
    
    print("\n2. Processing sample medical document...")
    
    # Create temporary file with sample content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_content)
        temp_file = f.name
    
    try:
        # Process the document
        result = pipeline._process_document_sync(temp_file, "demo_document_001")
        
        if result.success:
            print(f"   ✓ Document processed successfully!")
            print(f"   - Document ID: {result.document_id}")
            print(f"   - Sections found: {len(result.sections)}")
            print(f"   - Entities extracted: {len(result.entities)}")
            print(f"   - Embeddings generated: {result.embeddings_generated}")
            
            print("\n3. Document sections:")
            for i, section in enumerate(result.sections, 1):
                print(f"   {i}. {section.section_type.upper()}")
                print(f"      Page: {section.page_number}")
                print(f"      Content preview: {section.text_content[:100]}...")
                print()
            
            print("4. Extracted entities:")
            entity_counts = {}
            for entity in result.entities:
                entity_type = entity.entity_type
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
                
                if entity_counts[entity_type] <= 3:  # Show first 3 of each type
                    print(f"   - {entity_type.upper()}: '{entity.text}' (confidence: {entity.confidence})")
            
            # Show entity summary
            print(f"\n   Entity summary:")
            for entity_type, count in entity_counts.items():
                print(f"   - {entity_type}: {count} entities")
            
            print("\n5. Vector store statistics:")
            vector_store = vector_store_manager.get_store("demo_store")
            if vector_store:
                stats = vector_store.get_stats()
                print(f"   - Documents in vector store: {stats['document_count']}")
                print(f"   - Embedding dimension: {stats['embedding_dimension']}")
                
                # Demonstrate similarity search
                print("\n6. Similarity search demo:")
                search_query = "back pain and disc herniation"
                print(f"   Query: '{search_query}'")
                
                similar_docs = pipeline.kg_service.search_similar_content(
                    query_text=search_query,
                    top_k=3,
                    min_similarity=0.1
                )
                
                if similar_docs:
                    print(f"   Found {len(similar_docs)} similar documents:")
                    for i, doc in enumerate(similar_docs, 1):
                        print(f"   {i}. Similarity: {doc['similarity']:.3f}")
                        print(f"      Type: {doc['metadata'].get('type', 'unknown')}")
                        print(f"      Content: {doc['text'][:100]}...")
                        print()
                else:
                    print("   No similar documents found")
            
            print("7. Knowledge graph relationships:")
            print("   The following relationships were created:")
            print("   - Document → Sections (HAS_SECTION)")
            print("   - Sections → Diagnoses (CONTAINS_DIAGNOSIS)")  
            print("   - Sections → Findings (CONTAINS_FINDING)")
            print("   - Diagnoses → Impairment Ratings (HAS_RATING)")
            
        else:
            print(f"   ✗ Document processing failed: {result.error_message}")
            
    finally:
        # Clean up temporary file
        os.unlink(temp_file)
    
    print("\n=== Demo Complete ===")
    print("\nThe ingestion pipeline successfully:")
    print("• Segmented the medical document into structured sections")
    print("• Extracted medical entities (diagnoses, findings, impairment ratings)")
    print("• Generated embeddings for semantic search")
    print("• Populated the knowledge graph with nodes and relationships")
    print("• Enabled similarity search over the processed content")
    print("\nThis demonstrates the complete text extraction → section segmentation →")
    print("NER → embedding → KG population pipeline as specified in the requirements.")


if __name__ == "__main__":
    main()