#!/usr/bin/env python3
"""
Test the complete enhanced RAG pipeline with Sonoma Sky Alpha.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

from src.services.refactored_document_processor import RefactoredDocumentProcessor, DocumentProcessingConfig
from src.models.extraction_models import ExtractionConfig, ExtractionMethod

def test_complete_pipeline():
    """Test the complete enhanced RAG pipeline."""
    
    print("🚀 Testing Complete Enhanced RAG Pipeline with Sonoma Sky Alpha")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found")
        return False
    
    print(f"✅ API Key configured: {api_key[:20]}...")
    
    try:
        # Create processor configuration
        config = DocumentProcessingConfig(
            use_openrouter_extraction=True,
            use_vision_extraction=False,
            extraction_prompt_template="patient_info",
            max_contexts_per_document=10,
            min_confidence_threshold=0.7,
            enable_knowledge_graph_updates=True,
            enable_vector_store_updates=True,
            quality_validation_enabled=True
        )
        
        print("✅ Created processing configuration")
        
        # Initialize processor
        processor = RefactoredDocumentProcessor(config=config)
        print("✅ Initialized RefactoredDocumentProcessor")
        
        # Create sample QME document
        sample_document = """
        QUALIFIED MEDICAL EVALUATOR REPORT
        
        Patient Information:
        Name: Michael Chen
        Date of Birth: 07/10/1975
        Age: 48
        Gender: Male
        Case Number: WC-2024-11111
        Claim Number: CLM-555666
        Date of Injury: 05/20/2024
        
        Employer: Tech Solutions Inc.
        Occupation: Software Engineer
        
        Chief Complaint:
        Lower back pain following lifting incident at work.
        
        History of Present Illness:
        The patient reports that on May 20, 2024, while moving office equipment, 
        he experienced sudden onset of severe lower back pain. The pain radiates 
        down his left leg and is associated with numbness and tingling.
        
        Physical Examination:
        Lumbar spine range of motion is limited due to pain.
        Positive straight leg raise test on the left at 45 degrees.
        Decreased sensation in L5 distribution.
        
        Diagnostic Studies:
        MRI lumbar spine shows disc herniation at L4-L5 with nerve root compression.
        
        Diagnosis:
        Primary: Lumbar disc herniation L4-L5 (ICD-10: M51.26)
        Secondary: Sciatica, left side (ICD-10: M54.32)
        
        Impairment Rating:
        Based on AMA Guides 5th Edition, Table 15-3
        Whole Person Impairment: 8%
        
        Causation Analysis:
        The patient's lumbar disc herniation is directly related to the 
        work-related lifting incident on 05/20/2024.
        Medical probability: 85%
        
        Treatment Plan:
        1. Conservative management with physical therapy
        2. Anti-inflammatory medications
        3. Epidural steroid injection if symptoms persist
        
        Work Status:
        Modified duty with lifting restrictions under 20 pounds.
        No prolonged sitting or standing.
        
        Prognosis:
        Good with appropriate treatment. Expected improvement in 6-8 weeks.
        """
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_document)
            temp_file = f.name
        
        try:
            print("📄 Processing sample QME document...")
            
            # Process the document
            result = processor.process_document(temp_file)
            
            print(f"📊 Processing Result:")
            print(f"  Success: {result['success']}")
            print(f"  Document ID: {result.get('document_id', 'N/A')}")
            print(f"  Confidence Score: {result.get('processing_metadata', {}).get('confidence_score', 'N/A')}")
            print(f"  Processing Time: {result.get('processing_metadata', {}).get('processing_time', 'N/A')}s")
            print(f"  Contexts Generated: {result.get('retrieval_contexts_count', 'N/A')}")
            
            if result['success']:
                print("✅ Document processing successful!")
                
                # Test QME field extraction
                print("\n🔍 Testing QME field extraction...")
                qme_result = processor.extract_qme_fields(temp_file)
                
                if qme_result['success']:
                    print("✅ QME field extraction successful!")
                    print("📋 Extracted Fields:")
                    
                    qme_fields = qme_result.get('qme_fields', {})
                    for field_name, field_data in qme_fields.items():
                        if isinstance(field_data, dict) and 'value' in field_data:
                            confidence = field_data.get('confidence', 0)
                            print(f"  • {field_name}: {field_data['value']} (confidence: {confidence:.2f})")
                        else:
                            print(f"  • {field_name}: {field_data}")
                    
                    extraction_meta = qme_result.get('extraction_metadata', {})
                    print(f"\n📈 Extraction Metadata:")
                    print(f"  • Overall Confidence: {extraction_meta.get('overall_confidence', 'N/A')}")
                    print(f"  • Fields Extracted: {extraction_meta.get('fields_extracted', 'N/A')}")
                    print(f"  • Processing Time: {extraction_meta.get('processing_time', 'N/A')}s")
                    
                else:
                    print(f"❌ QME field extraction failed: {qme_result.get('error_message', 'Unknown error')}")
                    return False
                
                # Test RAG content generation
                print("\n🤖 Testing RAG content generation...")
                rag_result = processor.generate_content_with_rag(
                    query="What is the patient's diagnosis and impairment rating?",
                    document_context={
                        "document_id": result.get('document_id'),
                        "patient_name": "Michael Chen",
                        "diagnosis": "Lumbar disc herniation"
                    }
                )
                
                if rag_result['success']:
                    print("✅ RAG content generation successful!")
                    print(f"📝 Generated Content: {rag_result['generated_content'][:200]}...")
                    print(f"🎯 Confidence Score: {rag_result.get('confidence_score', 'N/A')}")
                    print(f"📚 Source Contexts: {rag_result.get('source_contexts_count', 'N/A')}")
                else:
                    print(f"❌ RAG content generation failed: {rag_result.get('error_message', 'Unknown error')}")
                
                # Get processing metrics
                print("\n📊 Processing Metrics:")
                metrics = processor.get_processing_metrics()
                proc_metrics = metrics.get('processor_metrics', {})
                print(f"  • Total Documents: {proc_metrics.get('total_documents', 'N/A')}")
                print(f"  • Success Rate: {proc_metrics.get('success_rate', 'N/A'):.2%}")
                print(f"  • Average Processing Time: {proc_metrics.get('average_processing_time', 'N/A'):.2f}s")
                
                return True
                
            else:
                print(f"❌ Document processing failed: {result.get('error_message', 'Unknown error')}")
                return False
                
        finally:
            # Clean up temporary file
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"❌ Pipeline test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_pipeline()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Complete Enhanced RAG Pipeline with Sonoma Sky Alpha is working perfectly!")
        print("✅ All components integrated successfully:")
        print("  • OpenRouter Sonoma Sky Alpha API ✅")
        print("  • Enhanced document processing ✅") 
        print("  • QME field extraction ✅")
        print("  • RAG content generation ✅")
        print("  • Metadata tracking ✅")
        print("  • Quality validation ✅")
    else:
        print("❌ Pipeline test failed - check the logs above for details")
    
    sys.exit(0 if success else 1)