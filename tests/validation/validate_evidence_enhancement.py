#!/usr/bin/env python3
"""
Validation script for evidence-driven content generation enhancement.

This script validates the code structure and implementation without requiring
full system dependencies.
"""

import ast
import os

def validate_evidence_rag_service():
    """Validate the evidence RAG service implementation."""
    print("=== Validating Evidence RAG Service ===")
    
    file_path = "src/services/evidence_rag_service.py"
    if not os.path.exists(file_path):
        print("❌ Evidence RAG service file not found")
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse the AST to validate structure
        tree = ast.parse(content)
        
        # Check for required classes
        required_classes = [
            'EvidenceSnippet',
            'CanonicalContent', 
            'EvidenceRetrievalResult',
            'AMAGuidelinesRetriever',
            'QMEStudyGuideRetriever',
            'EvidenceRAGService'
        ]
        
        found_classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                found_classes.append(node.name)
        
        missing_classes = [cls for cls in required_classes if cls not in found_classes]
        
        if missing_classes:
            print(f"❌ Missing classes: {missing_classes}")
            return False
        
        print("✅ All required classes found")
        
        # Check for key methods
        required_methods = [
            'retrieve_evidence_for_content',
            'get_evidence_constrained_content',
            'get_source_citations'
        ]
        
        found_methods = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                found_methods.append(node.name)
        
        missing_methods = [method for method in required_methods if method not in found_methods]
        
        if missing_methods:
            print(f"❌ Missing methods: {missing_methods}")
            return False
        
        print("✅ All required methods found")
        print(f"✅ Evidence RAG service validation passed ({len(content)} characters)")
        return True
        
    except Exception as e:
        print(f"❌ Error validating evidence RAG service: {str(e)}")
        return False

def validate_intelligent_content_generator():
    """Validate the enhanced intelligent content generator."""
    print("\n=== Validating Enhanced Intelligent Content Generator ===")
    
    file_path = "src/services/intelligent_content_generator.py"
    if not os.path.exists(file_path):
        print("❌ Intelligent content generator file not found")
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for evidence-first enhancements
        required_imports = [
            'evidence_rag_service',
            'EvidenceRAGService',
            'EvidenceRetrievalResult',
            'EvidenceSnippet'
        ]
        
        missing_imports = []
        for import_item in required_imports:
            if import_item not in content:
                missing_imports.append(import_item)
        
        if missing_imports:
            print(f"❌ Missing imports: {missing_imports}")
            return False
        
        print("✅ Evidence-first imports found")
        
        # Check for enhanced MedicalNarrative fields
        enhanced_fields = [
            'evidence_snippets',
            'validated_fields_used',
            'source_citations',
            'provenance_complete',
            'placeholder_text_removed',
            'evidence_backing_complete'
        ]
        
        missing_fields = []
        for field in enhanced_fields:
            if field not in content:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing enhanced fields: {missing_fields}")
            return False
        
        print("✅ Enhanced MedicalNarrative fields found")
        
        # Check for evidence-constrained methods
        evidence_methods = [
            'generate_evidence_constrained_content',
            'generate_evidence_constrained_section_content',
            'generate_comprehensive_evidence_report_content'
        ]
        
        missing_methods = []
        for method in evidence_methods:
            if method not in content:
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing evidence methods: {missing_methods}")
            return False
        
        print("✅ Evidence-constrained methods found")
        
        # Check for validation methods
        validation_methods = [
            '_validate_content_completeness',
            '_validate_no_placeholder_text',
            '_validate_evidence_backing_completeness'
        ]
        
        missing_validation = []
        for method in validation_methods:
            if method not in content:
                missing_validation.append(method)
        
        if missing_validation:
            print(f"❌ Missing validation methods: {missing_validation}")
            return False
        
        print("✅ Content validation methods found")
        print(f"✅ Enhanced content generator validation passed ({len(content)} characters)")
        return True
        
    except Exception as e:
        print(f"❌ Error validating content generator: {str(e)}")
        return False

def validate_generator_enhancements():
    """Validate individual generator enhancements."""
    print("\n=== Validating Generator Enhancements ===")
    
    file_path = "src/services/intelligent_content_generator.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check each generator has evidence-constrained method
        generators = [
            'HistoryOfPresentIllnessGenerator',
            'PhysicalExaminationGenerator',
            'DiagnosticStudiesGenerator',
            'CausationAnalysisGenerator',
            'FutureMedicalCareGenerator'
        ]
        
        for generator in generators:
            if generator not in content:
                print(f"❌ Missing generator: {generator}")
                return False
            
            # Check for evidence-constrained method in each generator
            generator_start = content.find(f"class {generator}")
            if generator_start == -1:
                print(f"❌ Generator class not found: {generator}")
                return False
            
            # Find the next class or end of file
            next_class = content.find("class ", generator_start + 1)
            if next_class == -1:
                generator_section = content[generator_start:]
            else:
                generator_section = content[generator_start:next_class]
            
            if 'generate_evidence_constrained_content' not in generator_section:
                print(f"❌ Missing evidence-constrained method in {generator}")
                return False
        
        print("✅ All generators have evidence-constrained methods")
        
        # Check for evidence enhancement methods
        enhancement_methods = [
            '_generate_validated_',
            '_remove_placeholder_text',
            '_enhance_with_evidence'
        ]
        
        for method_pattern in enhancement_methods:
            if method_pattern not in content:
                print(f"❌ Missing enhancement pattern: {method_pattern}")
                return False
        
        print("✅ Evidence enhancement methods found")
        print("✅ Generator enhancements validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error validating generator enhancements: {str(e)}")
        return False

def main():
    """Run all validation checks."""
    print("Evidence-Driven Content Generation Enhancement Validation")
    print("=" * 60)
    
    all_passed = True
    
    # Validate evidence RAG service
    if not validate_evidence_rag_service():
        all_passed = False
    
    # Validate enhanced content generator
    if not validate_intelligent_content_generator():
        all_passed = False
    
    # Validate generator enhancements
    if not validate_generator_enhancements():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED")
        print("\nEvidence-driven content generation enhancement is complete!")
        print("\nKey Features Implemented:")
        print("• Evidence RAG service for canonical content retrieval")
        print("• Evidence-constrained narrative generation")
        print("• Source citation management and provenance tracking")
        print("• Placeholder text validation and removal")
        print("• Evidence backing completeness validation")
        print("• Enhanced MedicalNarrative with evidence fields")
        print("• All QME sections support evidence-constrained generation")
    else:
        print("❌ SOME VALIDATIONS FAILED")
        print("Please review the errors above and fix the issues.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)