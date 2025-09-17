#!/usr/bin/env python3
"""
Import Fixer Script for QME System
Automatically fixes import paths based on the analysis results
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
import shutil

class ImportFixer:
    def __init__(self, analysis_file: str = "import_analysis.json"):
        self.analysis_file = analysis_file
        self.root_dir = Path(".").resolve()
        self.fixes_applied = 0
        self.files_modified = 0
        
        # Define the correct import mappings based on actual file locations
        self.import_mappings = {
            # Core services that moved from src.services to src.core
            'src.services.openrouter_extraction_service': 'src.core.extraction.openrouter_extraction_service',
            'src.services.document_processor': 'src.core.extraction.document_processor',
            'src.services.structured_extractor': 'src.core.extraction.structured_extractor',
            'src.services.field_extraction_service': 'src.core.extraction.field_extraction_service',
            'src.services.ingestion_pipeline': 'src.core.extraction.ingestion_pipeline',
            'src.services.ingestion_pipeline_factory': 'src.core.extraction.ingestion_pipeline_factory',
            
            'src.services.qme_template_generator': 'src.core.generation.qme_template_generator',
            'src.services.enhanced_qme_generator': 'src.core.generation.enhanced_qme_generator',
            'src.services.intelligent_content_generator': 'src.core.generation.intelligent_content_generator',
            'src.services.template_assembly_service': 'src.core.generation.template_assembly_service',
            
            'src.services.qme_rules_engine': 'src.core.validation.qme_rules_engine',
            'src.services.advanced_qme_rules_engine': 'src.core.validation.advanced_qme_rules_engine',
            'src.services.qme_field_validator': 'src.core.validation.qme_field_validator',
            'src.services.quality_validation_service': 'src.core.validation.quality_validation_service',
            'src.services.comprehensive_quality_validation_service': 'src.core.validation.comprehensive_quality_validation_service',
            
            'src.services.impairment_calculator': 'src.core.calculation.impairment_calculator',
            'src.services.enhanced_impairment_calculator': 'src.core.calculation.enhanced_impairment_calculator',
            
            # Infrastructure services
            'src.services.vector_store': 'src.infrastructure.storage.vector_store',
            'src.services.file_handler': 'src.infrastructure.storage.file_handler',
            'src.services.database_manager': 'src.infrastructure.storage.database_manager',
            'src.services.results_storage_service': 'src.infrastructure.storage.results_storage_service',
            'src.services.metadata_tracking_service': 'src.infrastructure.storage.metadata_tracking_service',
            
            'src.services.qa_engine': 'src.infrastructure.knowledge.qa_engine',
            'src.services.ama_guidelines_engine': 'src.infrastructure.knowledge.ama_guidelines_engine',
            'src.services.knowledge_base_initializer': 'src.infrastructure.knowledge.knowledge_base_initializer',
            'src.services.enhanced_rag_pipeline': 'src.infrastructure.knowledge.enhanced_rag_pipeline',
            'src.services.evidence_rag_service': 'src.infrastructure.knowledge.evidence_rag_service',
            'src.services.comprehensive_ama_integration': 'src.infrastructure.knowledge.comprehensive_ama_integration',
            'src.services.knowledge_graph_vector_service': 'src.infrastructure.knowledge.knowledge_graph_vector_service',
            'src.services.enhanced_vector_search': 'src.infrastructure.knowledge.enhanced_vector_search',
            'src.services.qme_reference_processor': 'src.infrastructure.knowledge.qme_reference_processor',
            
            'src.services.health_checker': 'src.infrastructure.monitoring.health_checker',
            'src.services.performance_monitor': 'src.infrastructure.monitoring.performance_monitor',
            'src.services.performance_monitoring_service': 'src.infrastructure.monitoring.performance_monitoring_service',
            'src.services.system_performance_monitor': 'src.infrastructure.monitoring.system_performance_monitor',
            'src.services.comprehensive_logging_service': 'src.infrastructure.monitoring.comprehensive_logging_service',
            'src.services.component_manager': 'src.infrastructure.monitoring.component_manager',
            'src.services.api_integration_manager': 'src.infrastructure.monitoring.api_integration_manager',
            'src.services.circuit_breaker': 'src.infrastructure.monitoring.circuit_breaker',
            'src.services.retry_handler': 'src.infrastructure.monitoring.retry_handler',
            'src.services.structured_logger': 'src.infrastructure.monitoring.structured_logger',
            
            'src.services.config_manager': 'src.infrastructure.configuration.config_manager',
            'src.services.configuration_service': 'src.infrastructure.configuration.configuration_service',
            'src.services.service_registry': 'src.infrastructure.configuration.service_registry',
            'src.services.system_initializer': 'src.infrastructure.configuration.system_initializer',
            'src.services.legacy_service_registry': 'src.infrastructure.configuration.legacy_service_registry',
            
            # Services without src prefix (from examples and scripts)
            'services.openrouter_extraction_service': 'src.core.extraction.openrouter_extraction_service',
            'services.document_processor': 'src.core.extraction.document_processor',
            'services.qme_template_generator': 'src.core.generation.qme_template_generator',
            'services.intelligent_content_generator': 'src.core.generation.intelligent_content_generator',
            'services.qme_rules_engine': 'src.core.validation.qme_rules_engine',
            'services.advanced_qme_rules_engine': 'src.core.validation.advanced_qme_rules_engine',
            'services.impairment_calculator': 'src.core.calculation.impairment_calculator',
            'services.enhanced_impairment_calculator': 'src.core.calculation.enhanced_impairment_calculator',
            'services.vector_store': 'src.infrastructure.storage.vector_store',
            'services.results_storage_service': 'src.infrastructure.storage.results_storage_service',
            'services.qa_engine': 'src.infrastructure.knowledge.qa_engine',
            'services.ama_guidelines_engine': 'src.infrastructure.knowledge.ama_guidelines_engine',
            'services.knowledge_base_initializer': 'src.infrastructure.knowledge.knowledge_base_initializer',
            'services.enhanced_rag_pipeline': 'src.infrastructure.knowledge.enhanced_rag_pipeline',
            'services.comprehensive_ama_integration': 'src.infrastructure.knowledge.comprehensive_ama_integration',
            'services.knowledge_graph_vector_service': 'src.infrastructure.knowledge.knowledge_graph_vector_service',
            'services.comprehensive_logging_service': 'src.infrastructure.monitoring.comprehensive_logging_service',
            'services.professional_template_assembler': 'src.services.professional_template_assembler_simple',
            'services.professional_template_assembly_engine': 'src.core.generation.template_assembly_service',
            
            # Relative imports that need fixing
            '.qme_field_extractor': 'src.core.extraction.field_extraction_service',
            '..models.extraction_models': 'src.models.extraction_models',
            '..models.knowledge_graph': 'src.models.knowledge_graph',
            '..services.ama_guidelines_engine': 'src.infrastructure.knowledge.ama_guidelines_engine',
            '..config.openrouter_config_manager': 'src.config.openrouter_config_manager',
            '..utils.logging_config': 'src.utils.logging_config',
            '..strategies.embedding_strategy': 'src.strategies.embedding_strategy',
            
            # Test imports that need fixing
            'validation.comprehensive_system_validator': 'src.validation.comprehensive_system_validator',
            'tests.test_end_to_end_quality_validation': 'tests.end_to_end.test_end_to_end_quality_validation',
            'tests.test_end_to_end_system_comparison': 'tests.end_to_end.test_end_to_end_system_comparison',
        }
    
    def load_analysis_results(self) -> Dict:
        """Load the import analysis results"""
        try:
            with open(self.analysis_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Analysis file {self.analysis_file} not found. Run import_analyzer.py first.")
            return {}
    
    def fix_import_in_file(self, file_path: str, old_import: str, new_import: str) -> bool:
        """Fix a specific import in a file"""
        try:
            full_path = self.root_dir / file_path
            if not full_path.exists():
                return False
            
            # Read the file
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Pattern to match the import statement
            # Handle both "from X import Y" and "import X" patterns
            patterns = [
                # from old_import import ...
                (rf'from\s+{re.escape(old_import)}\s+import\s+([^\\n]+)', 
                 rf'from {new_import} import \1'),
                # import old_import
                (rf'import\s+{re.escape(old_import)}(?=\s|$)', 
                 rf'import {new_import}'),
                # import old_import as alias
                (rf'import\s+{re.escape(old_import)}\s+as\s+(\w+)', 
                 rf'import {new_import} as \1'),
            ]
            
            modified = False
            for pattern, replacement in patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    modified = True
            
            # Write back if modified
            if modified and content != original_content:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error fixing import in {file_path}: {e}")
            return False
    
    def fix_all_imports(self) -> Tuple[int, int]:
        """Fix all imports based on the analysis and mappings"""
        analysis = self.load_analysis_results()
        if not analysis:
            return 0, 0
        
        files_modified = set()
        fixes_applied = 0
        
        # Process each file with issues
        for file_path, issues in analysis.get('issues_by_file', {}).items():
            file_was_modified = False
            
            for issue in issues:
                old_module = issue['module_name']
                
                # Check if we have a mapping for this import
                new_module = self.import_mappings.get(old_module)
                if new_module:
                    success = self.fix_import_in_file(file_path, old_module, new_module)
                    if success:
                        fixes_applied += 1
                        file_was_modified = True
                        print(f"Fixed: {file_path} - {old_module} -> {new_module}")
                elif issue.get('suggested_fix'):
                    # Use the suggested fix from analysis
                    suggested_fix = issue['suggested_fix']
                    success = self.fix_import_in_file(file_path, old_module, suggested_fix)
                    if success:
                        fixes_applied += 1
                        file_was_modified = True
                        print(f"Fixed: {file_path} - {old_module} -> {suggested_fix}")
            
            if file_was_modified:
                files_modified.add(file_path)
        
        return fixes_applied, len(files_modified)
    
    def create_backup(self):
        """Create a backup of the current state"""
        backup_dir = Path("backup_before_import_fix")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        
        # Copy key directories
        for dir_name in ['src', 'tests', 'examples', 'scripts']:
            src_dir = Path(dir_name)
            if src_dir.exists():
                shutil.copytree(src_dir, backup_dir / dir_name)
        
        print(f"Backup created at: {backup_dir}")
    
    def print_summary(self, fixes_applied: int, files_modified: int):
        """Print a summary of the fixes applied"""
        print(f"\n=== Import Fix Summary ===")
        print(f"Total fixes applied: {fixes_applied}")
        print(f"Files modified: {files_modified}")
        
        if fixes_applied > 0:
            print(f"\nImport fixes have been applied successfully!")
            print(f"You can now test the system to verify the fixes work correctly.")
        else:
            print(f"\nNo import fixes were applied. This could mean:")
            print(f"- All imports are already correct")
            print(f"- The analysis file is missing or empty")
            print(f"- No mappings were found for the broken imports")

def main():
    fixer = ImportFixer()
    
    print("Creating backup before applying fixes...")
    fixer.create_backup()
    
    print("Applying import fixes...")
    fixes_applied, files_modified = fixer.fix_all_imports()
    
    fixer.print_summary(fixes_applied, files_modified)
    
    return fixes_applied > 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)