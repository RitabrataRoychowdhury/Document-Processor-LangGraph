#!/usr/bin/env python3
"""
Demo script showing how to use the hybrid Q&A system with knowledge graph.
"""

import os
import sys
sys.path.append('../src')

from src.infrastructure.knowledge.qa_engine import create_hybrid_qa_engine
from storage.document_storage import DocumentStorage
from repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
from src.infrastructure.knowledge.knowledge_graph_vector_service import create_kg_vector_service


def demo_hybrid_qa():
    """Demonstrate the hybrid Q&A system capabilities."""
    print("Hybrid Q&A System Demo")
    print("=" * 50)
    
    # Set up environment (you need to provide a real API key)
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        print("⚠ Please set GEMINI_API_KEY environment variable")
        print("Example: export GEMINI_API_KEY='your-api-key-here'")
        return
    
    try:
        # Initialize components
        print("1. Initializing components...")
        storage = DocumentStorage()
        kg_repo = SQLiteKnowledgeGraphRepository()
        
        # Set up vector store with knowledge graph
        print("2. Setting up vector store...")
        kg_vector_service = create_kg_vector_service(kg_repo)
        stats = kg_vector_service.populate_vector_store_from_kg()
        print(f"   Vector store populated: {stats}")
        
        # Create hybrid QA engine
        print("3. Creating hybrid QA engine...")
        qa_engine = create_hybrid_qa_engine(gemini_api_key, storage, kg_repo)
        print("   ✓ Hybrid QA engine ready")
        
        # Example questions
        questions = [
            "What is the impairment rating for lumbar disc herniation?",
            "What findings support a diagnosis of radiculopathy?",
            "What AMA table is used for spine impairment ratings?",
            "What are the typical symptoms of disc herniation?"
        ]
        
        print("\n4. Testing Q&A with knowledge graph...")
        for i, question in enumerate(questions, 1):
            print(f"\nQuestion {i}: {question}")
            
            try:
                # Regular Q&A
                response = qa_engine.answer_question(question)
                print(f"Answer: {response['answer'][:200]}...")
                print(f"Sources: {response['sources'][:2]}")  # Show first 2 sources
                print(f"Confidence: {response['confidence']:.2f}")
                
                # Graph traversal Q&A
                if i == 2:  # Try graph traversal for one question
                    print("\n   Trying graph traversal...")
                    traversal_response = qa_engine.answer_question_with_graph_traversal(question)
                    print(f"   Traversal paths: {traversal_response['metadata'].get('traversal_paths', 0)}")
                
            except Exception as e:
                print(f"   Error: {e}")
        
        print("\n✓ Demo completed successfully!")
        
    except Exception as e:
        print(f"✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_hybrid_qa()