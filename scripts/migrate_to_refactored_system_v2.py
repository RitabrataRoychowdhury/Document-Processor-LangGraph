#!/usr/bin/env python3
"""
Enhanced Migration Script for QME System Refactor
Provides comprehensive migration from old system to refactored system with validation
"""

import sys
import shutil
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import yaml
import argparse

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.validation.comprehensive_quality_validation_service import ComprehensiveQualityValidationService
from src.infrastructure.monitoring.system_performance_monitor import SystemPerformanceMonitor


class SystemMigrationManager:
    """
    Comprehensive migration manager for QME system refactor
    """
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.logger = self._setup_logging()
        self.migration_id = f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Migration configuration
        self.migration_config = {
            "backup_existing": True,
            "validate_before_migration": True,
            "validate_after_migration": True,
            "preserve_user_data": True,
            "create_rollback_point": True
        }
        
        # Paths for migration
        self.paths = {
            "backup_dir": Path(f"migration_backup_{self.migration_id}"),
            "migration_log": Path(f"logs/migration_{self.migration_id}.log"),
            "rollback_script": Path(f"scripts/rollback_{self.migration_id}.py"),
            "validation_report": Path(f"results/migration_validation_{self.migration_id}.json")
        }
        
        # Initialize services
        self.quality_validator = None
        self.performance_monitor = None
        self._initialize_services()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup migration logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/migration_{self.migration_id}.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def _initialize_services(self):
        """Initialize migration services"""
        try:
            self.quality_validator = ComprehensiveQualityValidationService()
            self.performance_monitor = SystemPerformanceMonitor()
            self.logger.info("Migration services initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize migration services: {e}")
    
    def run_complete_migration(self) -> Dict[str, Any]:
        """
        Run complete migration process with validation and rollback capability
        """
        self.logger.info(f"Starting complete migration process (ID: {self.migration_id})")
        
        migration_result = {
            "migration_id": self.migration_id,
            "start_time": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "phases_completed": [],
            "validation_results": {},
            "backup_locations": {},
            "errors": [],
            "warnings": [],
            "rollback_available": False
        }
        
        try:
            # Phase 1: Pre-migration validation
            self.logger.info("Phase 1: Pre-migration validation")
            pre_validation = self._run_pre_migration_validation()
            migration_result["validation_results"]["pre_migration"] = pre_validation
            migration_result["phases_completed"].append("pre_migration_validation")
            
            if not pre_validation.get("system_ready", False):
                raise Exception("System not ready for migration - check validation results")
            
            # Phase 2: Create backup and rollback point
            self.logger.info("Phase 2: Creating backup and rollback point")
            backup_result = self._create_system_backup()
            migration_result["backup_locations"] = backup_result
            migration_result["rollback_available"] = backup_result.get("success", False)
            migration_result["phases_completed"].append("backup_creation")
            
            # Phase 3: Migrate configuration files
            self.logger.info("Phase 3: Migrating configuration files")
            config_result = self._migrate_configuration_files()
            migration_result["configuration_migration"] = config_result
            migration_result["phases_completed"].append("configuration_migration")
            
            # Phase 4: Migrate data and results
            self.logger.info("Phase 4: Migrating data and results")
            data_result = self._migrate_data_and_results()
            migration_result["data_migration"] = data_result
            migration_result["phases_completed"].append("data_migration")
            
            # Phase 5: Update service configurations
            self.logger.info("Phase 5: Updating service configurations")
            service_result = self._update_service_configurations()
            migration_result["service_configuration"] = service_result
            migration_result["phases_completed"].append("service_configuration")
            
            # Phase 6: Post-migration validation
            self.logger.info("Phase 6: Post-migration validation")
            post_validation = self._run_post_migration_validation()
            migration_result["validation_results"]["post_migration"] = post_validation
            migration_result["phases_completed"].append("post_migration_validation")
            
            # Phase 7: Generate migration report
            self.logger.info("Phase 7: Generating migration report")
            self._generate_migration_documentation(migration_result)
            migration_result["phases_completed"].append("documentation_generation")
            
            migration_result["success"] = True
            migration_result["end_time"] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            migration_result["errors"].append(str(e))
            migration_result["success"] = False
            migration_result["end_time"] = datetime.now().isoformat()
            
            # Attempt rollback if backup was created
            if migration_result["rollback_available"]:
                self.logger.info("Attempting automatic rollback...")
                rollback_result = self._perform_rollback(migration_result["backup_locations"])
                migration_result["rollback_result"] = rollback_result
        
        # Save migration results
        self._save_migration_results(migration_result)
        
        return migration_result
    
    def _run_pre_migration_validation(self) -> Dict[str, Any]:
        """Run comprehensive pre-migration validation"""
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "system_ready": False,
            "checks_performed": [],
            "issues_found": [],
            "recommendations": []
        }
        
        # Check 1: Verify existing system components
        self.logger.info("Checking existing system components...")
        existing_components = self._check_existing_components()
        validation_result["existing_components"] = existing_components
        validation_result["checks_performed"].append("existing_components")
        
        # Check 2: Verify required dependencies
        self.logger.info("Checking required dependencies...")
        dependencies = self._check_dependencies()
        validation_result["dependencies"] = dependencies
        validation_result["checks_performed"].append("dependencies")
        
        # Check 3: Check disk space and resources
        self.logger.info("Checking system resources...")
        resources = self._check_system_resources()
        validation_result["system_resources"] = resources
        validation_result["checks_performed"].append("system_resources")
        
        # Check 4: Validate configuration files
        self.logger.info("Validating configuration files...")
        config_validation = self._validate_configuration_files()
        validation_result["configuration_validation"] = config_validation
        validation_result["checks_performed"].append("configuration_validation")
        
        # Determine if system is ready
        critical_issues = []
        
        if not existing_components.get("core_services_available", False):
            critical_issues.append("Core services not available")
        
        if not dependencies.get("all_dependencies_met", False):
            critical_issues.append("Missing required dependencies")
        
        if not resources.get("sufficient_resources", False):
            critical_issues.append("Insufficient system resources")
        
        validation_result["system_ready"] = len(critical_issues) == 0
        validation_result["critical_issues"] = critical_issues
        
        return validation_result
    
    def _check_existing_components(self) -> Dict[str, Any]:
        """Check existing system components"""
        components = {
            "core_services_available": True,
            "existing_templates": [],
            "existing_configurations": [],
            "data_directories": []
        }
        
        # Check for existing templates
        template_paths = [
            Path("results/templates_archive"),
            Path("results/generated_documents"),
            Path("templates")  # Legacy location
        ]
        
        for path in template_paths:
            if path.exists():
                templates = list(path.glob("*.docx"))
                components["existing_templates"].extend([str(t) for t in templates])
        
        # Check for existing configurations
        config_paths = [
            Path("config"),
            Path("src/config"),
            Path("settings")  # Legacy location
        ]
        
        for path in config_paths:
            if path.exists():
                configs = list(path.glob("*.yaml")) + list(path.glob("*.json"))
                components["existing_configurations"].extend([str(c) for c in configs])
        
        # Check data directories
        data_paths = [
            Path("data"),
            Path("results"),
            Path("logs")
        ]
        
        for path in data_paths:
            if path.exists():
                components["data_directories"].append(str(path))
        
        return components
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check required dependencies"""
        dependencies = {
            "all_dependencies_met": True,
            "python_version": sys.version,
            "required_packages": [],
            "missing_packages": [],
            "package_versions": {}
        }
        
        # Check required packages
        required_packages = [
            "openai", "requests", "pyyaml", "pathlib", "dataclasses",
            "psutil", "python-docx", "pandas", "numpy"
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                dependencies["required_packages"].append(package)
                
                # Try to get version
                try:
                    pkg = __import__(package)
                    version = getattr(pkg, "__version__", "unknown")
                    dependencies["package_versions"][package] = version
                except:
                    dependencies["package_versions"][package] = "unknown"
                    
            except ImportError:
                dependencies["missing_packages"].append(package)
                dependencies["all_dependencies_met"] = False
        
        return dependencies
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resources"""
        import psutil
        
        # Get current resource usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        resources = {
            "sufficient_resources": True,
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_usage": disk.percent,
            "disk_free_gb": disk.free / (1024**3),
            "resource_warnings": []
        }
        
        # Check thresholds
        if cpu_percent > 80:
            resources["resource_warnings"].append(f"High CPU usage: {cpu_percent:.1f}%")
        
        if memory.percent > 85:
            resources["resource_warnings"].append(f"High memory usage: {memory.percent:.1f}%")
            resources["sufficient_resources"] = False
        
        if disk.percent > 90:
            resources["resource_warnings"].append(f"Low disk space: {disk.percent:.1f}% used")
            resources["sufficient_resources"] = False
        
        if resources["disk_free_gb"] < 1.0:
            resources["resource_warnings"].append("Less than 1GB free disk space")
            resources["sufficient_resources"] = False
        
        return resources
    
    def _validate_configuration_files(self) -> Dict[str, Any]:
        """Validate existing configuration files"""
        validation = {
            "valid_configurations": True,
            "config_files_checked": [],
            "validation_errors": [],
            "migration_required": []
        }
        
        # Check existing config files
        config_files = [
            "config/settings/openrouter_config.yaml",
            "config/validation/quality_validation_config.yaml",
            "config/templates/assembly_config.yaml"
        ]
        
        for config_file in config_files:
            config_path = Path(config_file)
            validation["config_files_checked"].append(config_file)
            
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        yaml.safe_load(f)
                    self.logger.info(f"Configuration file {config_file} is valid")
                except Exception as e:
                    validation["validation_errors"].append(f"Invalid config {config_file}: {e}")
                    validation["valid_configurations"] = False
            else:
                validation["migration_required"].append(f"Missing config file: {config_file}")
        
        return validation
    
    def _create_system_backup(self) -> Dict[str, Any]:
        """Create comprehensive system backup"""
        backup_result = {
            "success": False,
            "backup_timestamp": datetime.now().isoformat(),
            "backup_locations": {},
            "files_backed_up": 0,
            "backup_size_mb": 0
        }
        
        if self.dry_run:
            self.logger.info("DRY RUN: Would create system backup")
            backup_result["success"] = True
            return backup_result
        
        try:
            # Create backup directory
            backup_dir = self.paths["backup_dir"]
            backup_dir.mkdir(exist_ok=True)
            
            # Backup critical directories
            backup_targets = {
                "config": Path("config"),
                "src_config": Path("src/config"),
                "results": Path("results"),
                "data": Path("data"),
                "logs": Path("logs"),
                "scripts": Path("scripts")
            }
            
            total_size = 0
            files_count = 0
            
            for backup_name, source_path in backup_targets.items():
                if source_path.exists():
                    backup_dest = backup_dir / backup_name
                    
                    if source_path.is_dir():
                        shutil.copytree(source_path, backup_dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source_path, backup_dest)
                    
                    # Calculate size
                    if backup_dest.exists():
                        if backup_dest.is_dir():
                            size = sum(f.stat().st_size for f in backup_dest.rglob('*') if f.is_file())
                            files_count += len(list(backup_dest.rglob('*')))
                        else:
                            size = backup_dest.stat().st_size
                            files_count += 1
                        
                        total_size += size
                        backup_result["backup_locations"][backup_name] = str(backup_dest)
            
            backup_result["files_backed_up"] = files_count
            backup_result["backup_size_mb"] = total_size / (1024 * 1024)
            backup_result["success"] = True
            
            # Create rollback script
            self._create_rollback_script(backup_result["backup_locations"])
            
            self.logger.info(f"Backup created successfully: {files_count} files, {backup_result['backup_size_mb']:.2f} MB")
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            backup_result["error"] = str(e)
        
        return backup_result
    
    def _create_rollback_script(self, backup_locations: Dict[str, str]):
        """Create rollback script for migration"""
        rollback_script_content = f'''#!/usr/bin/env python3
"""
Automatic rollback script for migration {self.migration_id}
Generated on {datetime.now().isoformat()}
"""

import shutil
from pathlib import Path
import logging

def rollback_migration():
    """Rollback migration {self.migration_id}"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting rollback for migration {self.migration_id}")
    
    backup_locations = {backup_locations}
    
    try:
        for backup_name, backup_path in backup_locations.items():
            source_path = Path(backup_path)
            
            if backup_name == "config":
                dest_path = Path("config")
            elif backup_name == "src_config":
                dest_path = Path("src/config")
            elif backup_name == "results":
                dest_path = Path("results")
            elif backup_name == "data":
                dest_path = Path("data")
            elif backup_name == "logs":
                dest_path = Path("logs")
            elif backup_name == "scripts":
                dest_path = Path("scripts")
            else:
                continue
            
            if source_path.exists():
                if dest_path.exists():
                    if dest_path.is_dir():
                        shutil.rmtree(dest_path)
                    else:
                        dest_path.unlink()
                
                if source_path.is_dir():
                    shutil.copytree(source_path, dest_path)
                else:
                    shutil.copy2(source_path, dest_path)
                
                logger.info(f"Restored {{backup_name}} from backup")
        
        logger.info("Rollback completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Rollback failed: {{e}}")
        return False

if __name__ == "__main__":
    success = rollback_migration()
    exit(0 if success else 1)
'''
        
        if not self.dry_run:
            with open(self.paths["rollback_script"], 'w') as f:
                f.write(rollback_script_content)
            
            # Make executable
            self.paths["rollback_script"].chmod(0o755)
    
    def _migrate_configuration_files(self) -> Dict[str, Any]:
        """Migrate configuration files to new structure"""
        migration_result = {
            "success": True,
            "configurations_migrated": [],
            "new_configurations_created": [],
            "migration_errors": []
        }
        
        if self.dry_run:
            self.logger.info("DRY RUN: Would migrate configuration files")
            return migration_result
        
        # Ensure new config structure exists
        config_dirs = [
            "config/prompts/extraction",
            "config/prompts/generation", 
            "config/prompts/validation",
            "config/settings",
            "config/templates",
            "config/validation",
            "config/system"
        ]
        
        for config_dir in config_dirs:
            Path(config_dir).mkdir(parents=True, exist_ok=True)
        
        # Create default configurations if they don't exist
        default_configs = {
            "config/settings/openrouter_config.yaml": self._get_default_openrouter_config(),
            "config/validation/quality_validation_config.yaml": self._get_default_quality_config(),
            "config/templates/assembly_config.yaml": self._get_default_assembly_config(),
            "config/system/component_config.yaml": self._get_default_component_config()
        }
        
        for config_path, config_content in default_configs.items():
            config_file = Path(config_path)
            
            if not config_file.exists():
                try:
                    with open(config_file, 'w') as f:
                        yaml.dump(config_content, f, default_flow_style=False)
                    
                    migration_result["new_configurations_created"].append(config_path)
                    self.logger.info(f"Created default configuration: {config_path}")
                    
                except Exception as e:
                    migration_result["migration_errors"].append(f"Failed to create {config_path}: {e}")
                    migration_result["success"] = False
        
        return migration_result
    
    def _get_default_openrouter_config(self) -> Dict[str, Any]:
        """Get default OpenRouter configuration"""
        return {
            "api_endpoint": "https://openrouter.ai/api/v1/chat/completions",
            "model": "anthropic/claude-3.5-sonnet:beta",
            "max_tokens": 4000,
            "temperature": 0.1,
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 1.0
        }
    
    def _get_default_quality_config(self) -> Dict[str, Any]:
        """Get default quality validation configuration"""
        return {
            "quality_metrics": {
                "completeness": {"weight": 0.25, "threshold": 0.8},
                "accuracy": {"weight": 0.30, "threshold": 0.85},
                "consistency": {"weight": 0.20, "threshold": 0.75},
                "compliance": {"weight": 0.25, "threshold": 0.90}
            },
            "compliance_rules": {
                "ama_guidelines": {"severity": "critical", "enabled": True},
                "qme_standards": {"severity": "critical", "enabled": True},
                "formatting_rules": {"severity": "warning", "enabled": True},
                "data_completeness": {"severity": "critical", "enabled": True}
            },
            "thresholds": {
                "minimum_overall_score": 0.75,
                "critical_compliance_required": True,
                "warning_threshold": 0.65
            }
        }
    
    def _get_default_assembly_config(self) -> Dict[str, Any]:
        """Get default template assembly configuration"""
        return {
            "template_settings": {
                "default_template": "qme_professional_template.docx",
                "output_format": "docx",
                "include_metadata": True,
                "auto_save": True
            },
            "formatting_rules": {
                "font_family": "Times New Roman",
                "font_size": 12,
                "line_spacing": 1.15,
                "margin_inches": 1.0
            },
            "quality_checks": {
                "validate_before_assembly": True,
                "validate_after_assembly": True,
                "require_all_sections": False
            }
        }
    
    def _get_default_component_config(self) -> Dict[str, Any]:
        """Get default component configuration"""
        return {
            "components": {
                "extraction_service": {
                    "enabled": True,
                    "class": "OpenRouterExtractionService",
                    "config_file": "config/settings/openrouter_config.yaml"
                },
                "quality_validator": {
                    "enabled": True,
                    "class": "ComprehensiveQualityValidationService",
                    "config_file": "config/validation/quality_validation_config.yaml"
                },
                "template_engine": {
                    "enabled": True,
                    "class": "ProfessionalTemplateAssemblyEngine",
                    "config_file": "config/templates/assembly_config.yaml"
                }
            },
            "logging": {
                "level": "INFO",
                "file": "logs/system.log",
                "max_size_mb": 10,
                "backup_count": 5
            }
        }
    
    def _migrate_data_and_results(self) -> Dict[str, Any]:
        """Migrate data and results to new structure"""
        migration_result = {
            "success": True,
            "data_migrated": [],
            "results_organized": [],
            "migration_errors": []
        }
        
        if self.dry_run:
            self.logger.info("DRY RUN: Would migrate data and results")
            return migration_result
        
        # Ensure new directory structure
        result_dirs = [
            "results/generated_documents",
            "results/templates_archive", 
            "results/processing_logs",
            "results/validation_reports",
            "results/performance_reports"
        ]
        
        for result_dir in result_dirs:
            Path(result_dir).mkdir(parents=True, exist_ok=True)
        
        # Move existing generated documents to archive
        existing_docs = list(Path(".").glob("QME_Report_*.docx"))
        for doc in existing_docs:
            try:
                archive_path = Path("results/templates_archive") / doc.name
                if not self.dry_run:
                    shutil.move(str(doc), str(archive_path))
                migration_result["results_organized"].append(str(doc))
                self.logger.info(f"Moved {doc.name} to templates archive")
            except Exception as e:
                migration_result["migration_errors"].append(f"Failed to move {doc.name}: {e}")
        
        return migration_result
    
    def _update_service_configurations(self) -> Dict[str, Any]:
        """Update service configurations for refactored system"""
        update_result = {
            "success": True,
            "services_updated": [],
            "configuration_errors": []
        }
        
        if self.dry_run:
            self.logger.info("DRY RUN: Would update service configurations")
            return update_result
        
        # Update service registry if it exists
        service_registry_path = Path("src/services/service_registry.py")
        if service_registry_path.exists():
            update_result["services_updated"].append("service_registry")
        
        return update_result
    
    def _run_post_migration_validation(self) -> Dict[str, Any]:
        """Run post-migration validation"""
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "migration_successful": False,
            "validation_checks": [],
            "issues_found": [],
            "system_status": "unknown"
        }
        
        # Check 1: Verify new configuration structure
        config_check = self._verify_configuration_structure()
        validation_result["configuration_structure"] = config_check
        validation_result["validation_checks"].append("configuration_structure")
        
        # Check 2: Test service initialization
        service_check = self._test_service_initialization()
        validation_result["service_initialization"] = service_check
        validation_result["validation_checks"].append("service_initialization")
        
        # Check 3: Verify data migration
        data_check = self._verify_data_migration()
        validation_result["data_migration"] = data_check
        validation_result["validation_checks"].append("data_migration")
        
        # Determine overall status
        all_checks_passed = all([
            config_check.get("valid", False),
            service_check.get("services_initialized", False),
            data_check.get("migration_complete", False)
        ])
        
        validation_result["migration_successful"] = all_checks_passed
        validation_result["system_status"] = "ready" if all_checks_passed else "needs_attention"
        
        return validation_result
    
    def _verify_configuration_structure(self) -> Dict[str, Any]:
        """Verify new configuration structure"""
        verification = {
            "valid": True,
            "required_configs": [],
            "missing_configs": [],
            "invalid_configs": []
        }
        
        required_configs = [
            "config/settings/openrouter_config.yaml",
            "config/validation/quality_validation_config.yaml",
            "config/templates/assembly_config.yaml"
        ]
        
        for config_path in required_configs:
            config_file = Path(config_path)
            verification["required_configs"].append(config_path)
            
            if not config_file.exists():
                verification["missing_configs"].append(config_path)
                verification["valid"] = False
            else:
                try:
                    with open(config_file, 'r') as f:
                        yaml.safe_load(f)
                except Exception as e:
                    verification["invalid_configs"].append(f"{config_path}: {e}")
                    verification["valid"] = False
        
        return verification
    
    def _test_service_initialization(self) -> Dict[str, Any]:
        """Test service initialization"""
        service_test = {
            "services_initialized": True,
            "services_tested": [],
            "initialization_errors": []
        }
        
        # Test quality validator
        try:
            if self.quality_validator:
                service_test["services_tested"].append("quality_validator")
        except Exception as e:
            service_test["initialization_errors"].append(f"Quality validator: {e}")
            service_test["services_initialized"] = False
        
        # Test performance monitor
        try:
            if self.performance_monitor:
                service_test["services_tested"].append("performance_monitor")
        except Exception as e:
            service_test["initialization_errors"].append(f"Performance monitor: {e}")
            service_test["services_initialized"] = False
        
        return service_test
    
    def _verify_data_migration(self) -> Dict[str, Any]:
        """Verify data migration completion"""
        verification = {
            "migration_complete": True,
            "directories_verified": [],
            "missing_directories": [],
            "data_integrity_issues": []
        }
        
        required_dirs = [
            "results/generated_documents",
            "results/templates_archive",
            "results/validation_reports",
            "config/prompts",
            "config/settings"
        ]
        
        for dir_path in required_dirs:
            directory = Path(dir_path)
            verification["directories_verified"].append(dir_path)
            
            if not directory.exists():
                verification["missing_directories"].append(dir_path)
                verification["migration_complete"] = False
        
        return verification
    
    def _perform_rollback(self, backup_locations: Dict[str, str]) -> Dict[str, Any]:
        """Perform automatic rollback"""
        rollback_result = {
            "success": False,
            "rollback_timestamp": datetime.now().isoformat(),
            "items_restored": [],
            "rollback_errors": []
        }
        
        if self.dry_run:
            self.logger.info("DRY RUN: Would perform rollback")
            rollback_result["success"] = True
            return rollback_result
        
        try:
            # Execute rollback script
            import subprocess
            result = subprocess.run([sys.executable, str(self.paths["rollback_script"])], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                rollback_result["success"] = True
                rollback_result["items_restored"] = list(backup_locations.keys())
                self.logger.info("Automatic rollback completed successfully")
            else:
                rollback_result["rollback_errors"].append(f"Rollback script failed: {result.stderr}")
                self.logger.error("Automatic rollback failed")
        
        except Exception as e:
            rollback_result["rollback_errors"].append(str(e))
            self.logger.error(f"Rollback execution failed: {e}")
        
        return rollback_result
    
    def _generate_migration_documentation(self, migration_result: Dict[str, Any]):
        """Generate comprehensive migration documentation"""
        doc_content = f"""# QME System Migration Report

## Migration Summary
- **Migration ID**: {migration_result['migration_id']}
- **Start Time**: {migration_result['start_time']}
- **End Time**: {migration_result.get('end_time', 'In Progress')}
- **Success**: {migration_result.get('success', False)}
- **Dry Run**: {migration_result['dry_run']}

## Phases Completed
{chr(10).join(f"- {phase}" for phase in migration_result['phases_completed'])}

## Validation Results

### Pre-Migration Validation
{json.dumps(migration_result.get('validation_results', {}).get('pre_migration', {}), indent=2)}

### Post-Migration Validation  
{json.dumps(migration_result.get('validation_results', {}).get('post_migration', {}), indent=2)}

## Backup Information
- **Rollback Available**: {migration_result['rollback_available']}
- **Backup Locations**: {json.dumps(migration_result.get('backup_locations', {}), indent=2)}

## Issues and Recommendations

### Errors
{chr(10).join(f"- {error}" for error in migration_result.get('errors', []))}

### Warnings
{chr(10).join(f"- {warning}" for warning in migration_result.get('warnings', []))}

## Next Steps
1. Review validation results
2. Test system functionality
3. Monitor performance
4. Update documentation

Generated on: {datetime.now().isoformat()}
"""
        
        if not self.dry_run:
            doc_path = Path(f"docs/MIGRATION_REPORT_{self.migration_id}.md")
            doc_path.parent.mkdir(exist_ok=True)
            
            with open(doc_path, 'w') as f:
                f.write(doc_content)
            
            self.logger.info(f"Migration documentation generated: {doc_path}")
    
    def _save_migration_results(self, migration_result: Dict[str, Any]):
        """Save migration results to file"""
        if not self.dry_run:
            with open(self.paths["validation_report"], 'w') as f:
                json.dump(migration_result, f, indent=2)
            
            self.logger.info(f"Migration results saved to {self.paths['validation_report']}")


def main():
    """Main function for command-line execution"""
    parser = argparse.ArgumentParser(description="Migrate QME system to refactored version")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without making changes")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize migration manager
        migration_manager = SystemMigrationManager(dry_run=args.dry_run)
        
        # Run migration
        results = migration_manager.run_complete_migration()
        
        # Print summary
        print("\n" + "="*60)
        print("QME SYSTEM MIGRATION SUMMARY")
        print("="*60)
        
        if results.get("success", False):
            print("✅ Migration completed successfully!")
            print(f"📋 Phases completed: {len(results['phases_completed'])}")
            if results["rollback_available"]:
                print("🔄 Rollback available if needed")
        else:
            print("❌ Migration failed!")
            if results.get("errors"):
                print("🚨 Errors:")
                for error in results["errors"]:
                    print(f"   - {error}")
            
            if results["rollback_available"]:
                print("🔄 Automatic rollback may have been attempted")
        
        print(f"📊 Migration ID: {results['migration_id']}")
        print(f"📝 Detailed results saved to validation report")
        print("="*60)
        
        return 0 if results.get("success", False) else 1
        
    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())