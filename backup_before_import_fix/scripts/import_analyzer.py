#!/usr/bin/env python3
"""
Import Analysis Script for QME System
Scans all Python files for import statements and identifies broken imports
"""

import os
import ast
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
import json

@dataclass
class ImportIssue:
    file_path: str
    line_number: int
    import_statement: str
    import_type: str  # 'from', 'import', 'relative'
    module_name: str
    error_type: str
    suggested_fix: Optional[str] = None

@dataclass
class PathMapping:
    old_path: str
    new_path: str
    confidence: float
    reason: str

class ImportAnalyzer:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self.python_files = []
        self.import_issues = []
        self.existing_modules = set()
        self.path_mappings = []
        
    def find_python_files(self) -> List[Path]:
        """Find all Python files in the project"""
        python_files = []
        for root, dirs, files in os.walk(self.root_dir):
            # Skip common directories that don't contain source code
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache', 'venv', '.venv', 'node_modules'}]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        return python_files
    
    def discover_existing_modules(self):
        """Discover all existing Python modules in the project"""
        for py_file in self.python_files:
            # Convert file path to module path
            rel_path = py_file.relative_to(self.root_dir)
            if rel_path.name == '__init__.py':
                # Package
                module_path = '.'.join(rel_path.parent.parts)
            else:
                # Module
                module_path = '.'.join(rel_path.with_suffix('').parts)
            
            if module_path:
                self.existing_modules.add(module_path)
    
    def parse_imports_from_file(self, file_path: Path) -> List[Tuple[int, str, str, str]]:
        """Parse import statements from a Python file"""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append((
                            node.lineno,
                            f"import {alias.name}",
                            "import",
                            alias.name
                        ))
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    level = node.level
                    
                    if level > 0:  # Relative import
                        import_type = "relative"
                        full_module = "." * level + (module if module else "")
                    else:
                        import_type = "from"
                        full_module = module
                    
                    for alias in node.names:
                        import_stmt = f"from {full_module} import {alias.name}"
                        imports.append((
                            node.lineno,
                            import_stmt,
                            import_type,
                            full_module
                        ))
        
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"Error parsing {file_path}: {e}")
        
        return imports
    
    def check_import_validity(self, module_name: str, file_path: Path) -> Tuple[bool, str]:
        """Check if an import is valid"""
        if not module_name:
            return False, "empty_module_name"
        
        # Handle relative imports
        if module_name.startswith('.'):
            # Convert relative import to absolute
            current_package = self.get_package_from_file(file_path)
            if not current_package:
                return False, "relative_import_outside_package"
            
            # Calculate absolute module name
            level = len(module_name) - len(module_name.lstrip('.'))
            relative_module = module_name[level:]
            
            package_parts = current_package.split('.')
            if level > len(package_parts):
                return False, "relative_import_too_deep"
            
            base_package = '.'.join(package_parts[:-level+1]) if level > 1 else current_package
            absolute_module = f"{base_package}.{relative_module}" if relative_module else base_package
            module_name = absolute_module
        
        # Check if module exists in our project
        if module_name in self.existing_modules:
            return True, "valid"
        
        # Check if it's a standard library or installed package
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is not None:
                return True, "external_valid"
        except (ImportError, ModuleNotFoundError, ValueError):
            pass
        
        return False, "module_not_found"
    
    def get_package_from_file(self, file_path: Path) -> str:
        """Get the package name for a file"""
        rel_path = file_path.relative_to(self.root_dir)
        if rel_path.name == '__init__.py':
            return '.'.join(rel_path.parent.parts)
        else:
            return '.'.join(rel_path.parent.parts) if rel_path.parent.parts else ""
    
    def suggest_fix(self, issue: ImportIssue) -> Optional[str]:
        """Suggest a fix for an import issue"""
        module_name = issue.module_name
        
        # Common patterns for this project
        fixes = {
            # Services moved to core or infrastructure
            'src.services.comprehensive_qme_field_service': 'src.services.comprehensive_qme_field_service',
            'src.services.professional_template_assembler_simple': 'src.services.professional_template_assembler_simple',
            
            # Core services
            'src.core.generation.qme_template_generator': 'src.core.generation.qme_template_generator',
            'src.core.extraction.document_processor': 'src.core.extraction.document_processor',
            'src.core.validation.qme_rules_engine': 'src.core.validation.qme_rules_engine',
            
            # Infrastructure services
            'src.infrastructure.storage.vector_store': 'src.infrastructure.storage.vector_store',
            'src.infrastructure.storage.file_handler': 'src.infrastructure.storage.file_handler',
            'src.infrastructure.knowledge.qa_engine': 'src.infrastructure.knowledge.qa_engine',
        }
        
        if module_name in fixes:
            return fixes[module_name]
        
        # Try to find similar module names
        for existing_module in self.existing_modules:
            if existing_module.endswith(module_name.split('.')[-1]):
                return existing_module
        
        return None
    
    def analyze_all_imports(self) -> Dict[str, List[ImportIssue]]:
        """Analyze imports in all Python files"""
        self.python_files = self.find_python_files()
        self.discover_existing_modules()
        
        issues_by_file = {}
        
        for py_file in self.python_files:
            file_issues = []
            imports = self.parse_imports_from_file(py_file)
            
            for line_no, import_stmt, import_type, module_name in imports:
                is_valid, error_type = self.check_import_validity(module_name, py_file)
                
                if not is_valid:
                    issue = ImportIssue(
                        file_path=str(py_file.relative_to(self.root_dir)),
                        line_number=line_no,
                        import_statement=import_stmt,
                        import_type=import_type,
                        module_name=module_name,
                        error_type=error_type
                    )
                    issue.suggested_fix = self.suggest_fix(issue)
                    file_issues.append(issue)
            
            if file_issues:
                issues_by_file[str(py_file.relative_to(self.root_dir))] = file_issues
        
        return issues_by_file
    
    def generate_path_mappings(self, issues_by_file: Dict[str, List[ImportIssue]]) -> List[PathMapping]:
        """Generate path mappings for fixing imports"""
        mappings = []
        
        for file_path, issues in issues_by_file.items():
            for issue in issues:
                if issue.suggested_fix:
                    mapping = PathMapping(
                        old_path=issue.module_name,
                        new_path=issue.suggested_fix,
                        confidence=0.8,
                        reason=f"Suggested fix for {issue.error_type}"
                    )
                    mappings.append(mapping)
        
        return mappings
    
    def save_analysis_results(self, issues_by_file: Dict[str, List[ImportIssue]], 
                            mappings: List[PathMapping], output_file: str = "import_analysis.json"):
        """Save analysis results to JSON file"""
        results = {
            "summary": {
                "total_files_analyzed": len(self.python_files),
                "files_with_issues": len(issues_by_file),
                "total_issues": sum(len(issues) for issues in issues_by_file.values()),
                "existing_modules_count": len(self.existing_modules)
            },
            "issues_by_file": {},
            "path_mappings": [],
            "existing_modules": sorted(list(self.existing_modules))
        }
        
        # Convert issues to dict format
        for file_path, issues in issues_by_file.items():
            results["issues_by_file"][file_path] = [
                {
                    "line_number": issue.line_number,
                    "import_statement": issue.import_statement,
                    "import_type": issue.import_type,
                    "module_name": issue.module_name,
                    "error_type": issue.error_type,
                    "suggested_fix": issue.suggested_fix
                }
                for issue in issues
            ]
        
        # Convert mappings to dict format
        results["path_mappings"] = [
            {
                "old_path": mapping.old_path,
                "new_path": mapping.new_path,
                "confidence": mapping.confidence,
                "reason": mapping.reason
            }
            for mapping in mappings
        ]
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        return results
    
    def print_summary(self, issues_by_file: Dict[str, List[ImportIssue]]):
        """Print a summary of the analysis"""
        total_issues = sum(len(issues) for issues in issues_by_file.values())
        
        print(f"\n=== Import Analysis Summary ===")
        print(f"Total Python files analyzed: {len(self.python_files)}")
        print(f"Files with import issues: {len(issues_by_file)}")
        print(f"Total import issues found: {total_issues}")
        print(f"Existing modules discovered: {len(self.existing_modules)}")
        
        if issues_by_file:
            print(f"\n=== Files with Issues ===")
            for file_path, issues in issues_by_file.items():
                print(f"\n{file_path} ({len(issues)} issues):")
                for issue in issues[:5]:  # Show first 5 issues per file
                    print(f"  Line {issue.line_number}: {issue.import_statement}")
                    print(f"    Error: {issue.error_type}")
                    if issue.suggested_fix:
                        print(f"    Suggested fix: {issue.suggested_fix}")
                if len(issues) > 5:
                    print(f"  ... and {len(issues) - 5} more issues")

def main():
    analyzer = ImportAnalyzer()
    
    print("Starting import analysis...")
    issues_by_file = analyzer.analyze_all_imports()
    
    print("Generating path mappings...")
    mappings = analyzer.generate_path_mappings(issues_by_file)
    
    print("Saving results...")
    results = analyzer.save_analysis_results(issues_by_file, mappings)
    
    analyzer.print_summary(issues_by_file)
    
    print(f"\nDetailed results saved to: import_analysis.json")
    
    return len(issues_by_file) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)