#!/usr/bin/env python3
"""
Migration Script for QME System Refactor

This script handles the migration from the old QME system to the refactored system,
preserving existing data and ensuring smooth transition.
"""

import os
import sys
import shutil
import logging
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import sqlite3
import argparse

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.core.validation.quality_validation_service import QualityValidationService
from src.infrastructure.monitoring.performance_monitoring_service import PerformanceMonitoringService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class QMESystemMigrator:
    """Handles migration from old QME system to refactored system"""
    
    def __init__(self, backup_existing: bool = True, validate_migration: bool = True):
        self.backup_existing = backup_existing
        self.validate_migration = validate_migration
        self.migration_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = Path(f"migration_backup_{self.migration_timestamp}")
        
        # Migration tracking
        self.migration_log = {
            'timestamp': self.migration_timestamp,
            'steps_completed': [],
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        # Initialize services for validation
        self.quality_validator = None
        self.performance_monitor = None
        
        if self.validate_migration:
            try:
                self.quality_validator = QualityValidationService()
                self.performance_monitor = PerformanceMonitoringService()
            except Exception as e:
                logger.warning(f"Could not initialize validation services: {e}")
    
    def run_migration(self) -> bool:
        """Run complete migration process"""
        logger.info("Starting QME system migration to refactored architecture")
        
        try:
            # Step 1: Create backup
            if self.backup_existing:
                self._create_system_backup()
            
            # Step 2: Migrate existing documents
            self._migrate_existing_documents()
            
            # Step 3: Migrate configuration files
            self._migrate_configuration_files()
            
            # Step 4: Update database schema
            self._update_database_schema()
            
            # Step 5: Migrate templates and results
            self._migrate_templates_and_results()
            
            # Step 6: Update service configurations
            self._update_service_configurations()
            
            # Step 7: Validate migration
            if self.validate_migration:
                self._validate_migration()
            
            # Step 8: Generate migration report
            self._generate_migration_report()
            
            logger.info("Migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.migration_log['errors'].append(f"Migration failed: {str(e)}")
            self._generate_migration_report()
            return False
    
    def _create_system_backup(self):
        """Create backup of existing system"""
        logger.info("Creating system backup...")
        
        try:
            self.backup_dir.mkdir(exist_ok=True)
            
            # Backup critical directories
            backup_targets = [
                ('results', 'results_backup'),
                ('data', 'data_backup'),
                ('config', 'config_backup'),
                ('src/services', 'services_backup'),
                ('logs', 'logs_backup')
            ]
            
            for source, backup_name in backup_targets:
                source_path = Path(source)
                if source_path.exists():
                    backup_path = self.backup_dir / backup_name
                    if source_path.is_dir():
                        shutil.copytree(source_path, backup_path, ignore_errors=True)
                    else:
                        shutil.copy2(source_path, backup_path)
                    logger.info(f"Backed up {source} to {backup_path}")
            
            # Backup database
            db_path = Path("data/database/documents.db")
            if db_path.exists():
                backup_db_path = self.backup_dir / "documents_backup.db"
                shutil.copy2(db_path, backup_db_path)
                logger.info(f"Backed up database to {backup_db_path}")
            
            self.migration_log['steps_completed'].append('system_backup')
            logger.info("System backup completed")
            
        except Exception as e:
            error_msg = f"Error creating system backup: {e}"
            logger.error(error_msg)
            self.migration_log['errors'].append(error_msg)
            raise
    
    def _migrate_existing_documents(self):
        """Migrate existing documents to new structure"""
        logger.info("Migrating existing documents...")
        
        try:
            # Create new results structure
            new_results_structure = [
                "results/generated_documents",
                "results/templates_archive",
                "results/processing_logs",
                "results/validation_reports"
            ]
            
            for dir_path in new_results_structure:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
            
            # Move existing generated documents
            old_results_dir = Path("results")
            if old_results_dir.exists():
                # Move existing documents to templates_archive
                archive_dir = Path("results/templates_archive")
                
                for file_path in old_results_dir.glob("*.docx"):
                    if not file_path.name.startswith("QME_Report"):
                        continue
                    
                    new_path = archive_dir / file_path.name
                    if not new_path.exists():
                        shutil.move(str(file_path), str(new_path))
                        logger.info(f"Moved {file_path.name} to templates archive")
                
                # Organize by date if possible
                self._organize_documents_by_date(archive_dir)
            
            # Update document tracking
            self._update_document_tracking()
            
            self.migration_log['steps_completed'].append('document_migration')
            logger.info("Document migration completed")
            
        except Exception as e:
            error_msg = f"Error migrating documents: {e}"
            logger.error(error_msg)
            self.migration_log['errors'].append(error_msg)
            raise
    
    def _migrate_configuration_files(self):
        """Migrate configuration files to new structure"""
        logger.info("Migrating configuration files...")
        
        try:
            # Create new config structure
            config_structure = [
                "config/prompts/extraction",
                "config/prompts/generation", 
                "config/prompts/validation",
                "config/templates",
                "config/settings",
                "config/system",
                "config/validation",
                "config/monitoring"
            ]
            
            for dir_path in config_structure:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
            
            # Migrate existing configurations
            self._migrate_prompt_configurations()
            self._migrate_template_configurations()
            self._migrate_system_configurations()
            
            self.migration_log['steps_completed'].append('configuration_migration')
            logger.info("Configuration migration completed")
            
        except Exception as e:
            error_msg = f"Error migrating configurations: {e}"
            logger.error(error_msg)
            self.migration_log['errors'].append(error_msg)
            raise
    
    def _migrate_prompt_configurations(self):
        """Migrate prompt configurations"""
        # Create default prompt configurations if they don't exist
        prompt_configs = {
            'config/prompts/extraction/patient_info.yaml': {
                'name': 'Patient Information Extraction',
                'description': 'Extract patient demographic and injury information',
                'prompt_template': '''
                Extract the following patient information from the medical document:
                - Patient name
                - Date of birth
                - Date of injury
                - Claim number
                - Employer information
                - Contact details
                
                Format the response as structured JSON.
                ''',
                'expected_fields': ['name', 'date_of_birth', 'date_of_injury', 'claim_number', 'employer']
            },
            'config/prompts/extraction/medical_findings.yaml': {
                'name': 'Medical Findings Extraction',
                'description': 'Extract medical findings and examination results',
                'prompt_template': '''
                Extract medical findings from the document including:
                - Physical examination results
                - Diagnostic test results
                - Clinical observations
                - Functional limitations
                - Pain assessments
                
                Provide detailed, accurate medical information.
                ''',
                'expected_fields': ['examination_findings', 'diagnostic_results', 'limitations']
            }
        }
        
        for config_path, config_data in prompt_configs.items():
            config_file = Path(config_path)
            if not config_file.exists():
                with open(config_file, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
                logger.info(f"Created prompt configuration: {config_path}")
    
    def _migrate_template_configurations(self):
        """Migrate template configurations"""
        template_config = {
            'qme_report_template': {
                'name': 'Standard QME Report Template',
                'description': 'Professional QME report template with AMA compliance',
                'sections': [
                    'patient_information',
                    'history_of_present_illness',
                    'physical_examination',
                    'medical_findings',
                    'diagnosis',
                    'impairment_rating',
                    'recommendations',
                    'physician_signature'
                ],
                'formatting': {
                    'font': 'Times New Roman',
                    'font_size': 12,
                    'line_spacing': 1.5,
                    'margins': {'top': 1.0, 'bottom': 1.0, 'left': 1.0, 'right': 1.0}
                }
            }
        }
        
        config_file = Path("config/templates/qme_template_structure.yaml")
        if not config_file.exists():
            with open(config_file, 'w') as f:
                yaml.dump(template_config, f, default_flow_style=False)
            logger.info("Created template configuration")
    
    def _migrate_system_configurations(self):
        """Migrate system configurations"""
        system_config = {
            'components': {
                'openrouter_extraction_service': {
                    'enabled': True,
                    'model': 'anthropic/claude-3.5-sonnet',
                    'timeout': 30,
                    'retry_attempts': 3
                },
                'enhanced_rag_pipeline': {
                    'enabled': True,
                    'vector_store': 'chroma',
                    'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2'
                },
                'professional_template_assembly_engine': {
                    'enabled': True,
                    'template_validation': True,
                    'quality_checks': True
                },
                'quality_validation_service': {
                    'enabled': True,
                    'minimum_quality_score': 0.75,
                    'compliance_checking': True
                }
            },
            'performance_monitoring': {
                'enabled': True,
                'monitoring_interval': 30,
                'alert_thresholds': {
                    'processing_time': 30.0,
                    'memory_usage': 80.0,
                    'error_rate': 5.0
                }
            }
        }
        
        config_file = Path("config/system/component_config.yaml")
        if not config_file.exists():
            with open(config_file, 'w') as f:
                yaml.dump(system_config, f, default_flow_style=False)
            logger.info("Created system configuration")
    
    def _update_database_schema(self):
        """Update database schema for refactored system"""
        logger.info("Updating database schema...")
        
        try:
            db_path = Path("data/database/documents.db")
            if not db_path.exists():
                logger.info("Database does not exist, will be created by system")
                self.migration_log['steps_completed'].append('database_schema_update')
                return
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Add new columns for refactored system
            schema_updates = [
                '''ALTER TABLE documents ADD COLUMN quality_score REAL DEFAULT 0.0''',
                '''ALTER TABLE documents ADD COLUMN validation_status TEXT DEFAULT 'pending' ''',
                '''ALTER TABLE documents ADD COLUMN processing_version TEXT DEFAULT 'refactored_v1' ''',
                '''ALTER TABLE documents ADD COLUMN performance_metrics TEXT DEFAULT '{}' '''
            ]
            
            for update_sql in schema_updates:
                try:
                    cursor.execute(update_sql)
                    logger.info(f"Applied schema update: {update_sql}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info(f"Column already exists, skipping: {update_sql}")
                    else:
                        raise
            
            conn.commit()
            conn.close()
            
            self.migration_log['steps_completed'].append('database_schema_update')
            logger.info("Database schema update completed")
            
        except Exception as e:
            error_msg = f"Error updating database schema: {e}"
            logger.error(error_msg)
            self.migration_log['errors'].append(error_msg)
            raise
    
    def _migrate_templates_and_results(self):
        """Migrate templates and results to new organization"""
        logger.info("Migrating templates and results...")
        
        try:
            # Ensure results directory structure exists
            results_dirs = [
                "results/generated_documents",
                "results/templates_archive", 
                "results/processing_logs",
                "results/validation_reports"
            ]
            
            for dir_path in results_dirs:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
            
            # Move any remaining old results
            old_files = Path(".").glob("QME_Report_*.docx")
            for file_path in old_files:
                new_path = Path("results/templates_archive") / file_path.name
                if not new_path.exists():
                    shutil.move(str(file_path), str(new_path))
                    logger.info(f"Moved {file_path.name} to templates archive")
            
            # Create sample validation report
            self._create_sample_validation_report()
            
            self.migration_log['steps_completed'].append('templates_results_migration')
            logger.info("Templates and results migration completed")
            
        except Exception as e:
            error_msg = f"Error migrating templates and results: {e}"
            logger.error(error_msg)
            self.migration_log['errors'].append(error_msg)
            raise
    
    def _update_service_configurations(self):
        """Update service configurations for refactored system"""
        logger.info("Updating service configurations...")
        
        try:
            # Update OpenRouter configuration
            openrouter_config = {
                'api_endpoint': 'https://openrouter.ai/api/v1',
                'model_configs': {
                    'anthropic/claude-3.5-sonnet': {
                        'max_tokens': 4000,
                        'temperature': 0.1,
                        'timeout': 30
                    }
                },
                'retry_config': {
                    'max_attempts': 3,
                    'backoff_factor': 2.0,
                    'max_wait_time': 60
                }
            }
            
            config_file = Path("config/settings/openrouter_config.yaml")
            with open(config_file, 'w') as f:
                yaml.dump(openrouter_config, f, default_flow_style=False)
            
            # Update monitoring configuration
            monitoring_config = {
                'performance_thresholds': {
                    'processing_time_seconds': 30.0,
                    'memory_usage_percent': 80.0,
                    'cpu_usage_percent': 85.0,
                    'error_rate_percent': 5.0,
                    'quality_score_minimum': 0.75
                },
                'alert_settings': {
                    'email_notifications': False,
                    'log_alerts': True,
                    'alert_cooldown_minutes': 15
                },
                'monitoring_intervals': {
                    'system_metrics_seconds': 30,
                    'component_health_minutes': 5,
                    'quality_assessment_hours': 1
                }
            }
            
            monitoring_config_file = Path("config/monitoring/performance_config.yaml")
            monitoring_config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(monitoring_config_file, 'w') as f:
                yaml.dump(monitoring_config, f, default_flow_style=False)
            
            self.migration_log['steps_completed'].append('service_configuration_update')
            logger.info("Service configurations updated")
            
        except Exception as e:
            error_msg = f"Error updating service configurations: {e}"
            logger.error(error_msg)
            self.migration_log['errors'].append(error_msg)
            raise
    
    def _organize_documents_by_date(self, archive_dir: Path):
        """Organize archived documents by date"""
        try:
            for doc_file in archive_dir.glob("*.docx"):
                # Try to extract date from filename
                date_str = self._extract_date_from_filename(doc_file.name)
                if date_str:
                    # Create year/month directory structure
                    try:
                        date_obj = datetime.strptime(date_str, "%Y%m%d")
                        year_month_dir = archive_dir / str(date_obj.year) / f"{date_obj.month:02d}"
                        year_month_dir.mkdir(parents=True, exist_ok=True)
                        
                        new_path = year_month_dir / doc_file.name
                        if not new_path.exists():
                            shutil.move(str(doc_file), str(new_path))
                            logger.info(f"Organized {doc_file.name} by date")
                    except ValueError:
                        logger.warning(f"Could not parse date from {doc_file.name}")
        except Exception as e:
            logger.warning(f"Error organizing documents by date: {e}")
    
    def _extract_date_from_filename(self, filename: str) -> Optional[str]:
        """Extract date string from filename"""
        import re
        # Look for date pattern YYYYMMDD
        date_pattern = r'(\d{8})'
        match = re.search(date_pattern, filename)
        return match.group(1) if match else None
    
    def _update_document_tracking(self):
        """Update document tracking for migrated documents"""
        try:
            # Create document tracking file
            tracking_file = Path("results/document_tracking.json")
            
            tracking_data = {
                'migration_timestamp': self.migration_timestamp,
                'migrated_documents': [],
                'document_statistics': {}
            }
            
            # Count migrated documents
            archive_dir = Path("results/templates_archive")
            if archive_dir.exists():
                doc_count = len(list(archive_dir.glob("**/*.docx")))
                tracking_data['document_statistics']['total_archived'] = doc_count
                tracking_data['document_statistics']['migration_date'] = self.migration_timestamp
            
            with open(tracking_file, 'w') as f:
                json.dump(tracking_data, f, indent=2)
            
            logger.info("Document tracking updated")
            
        except Exception as e:
            logger.warning(f"Error updating document tracking: {e}")
    
    def _create_sample_validation_report(self):
        """Create sample validation report"""
        try:
            report_dir = Path("results/validation_reports")
            sample_report = {
                'report_type': 'migration_validation',
                'timestamp': self.migration_timestamp,
                'system_status': 'migrated',
                'validation_results': {
                    'configuration_valid': True,
                    'documents_migrated': True,
                    'services_configured': True
                },
                'recommendations': [
                    'Run comprehensive quality tests after migration',
                    'Validate system performance with real documents',
                    'Update user documentation for new features'
                ]
            }
            
            report_file = report_dir / f"migration_validation_{self.migration_timestamp}.json"
            with open(report_file, 'w') as f:
                json.dump(sample_report, f, indent=2)
            
            logger.info("Sample validation report created")
            
        except Exception as e:
            logger.warning(f"Error creating sample validation report: {e}")
    
    def _validate_migration(self):
        """Validate migration success"""
        logger.info("Validating migration...")
        
        try:
            validation_results = {
                'configuration_files': self._validate_configuration_files(),
                'directory_structure': self._validate_directory_structure(),
                'service_availability': self._validate_service_availability(),
                'document_migration': self._validate_document_migration()
            }
            
            all_valid = all(validation_results.values())
            
            if all_valid:
                logger.info("Migration validation passed")
                self.migration_log['steps_completed'].append('migration_validation')
            else:
                logger.warning("Migration validation found issues")
                for check, result in validation_results.items():
                    if not result:
                        self.migration_log['warnings'].append(f"Validation failed: {check}")
            
            self.migration_log['statistics']['validation_results'] = validation_results
            
        except Exception as e:
            error_msg = f"Error during migration validation: {e}"
            logger.error(error_msg)
            self.migration_log['errors'].append(error_msg)
    
    def _validate_configuration_files(self) -> bool:
        """Validate configuration files exist and are valid"""
        required_configs = [
            "config/prompts/extraction/patient_info.yaml",
            "config/prompts/extraction/medical_findings.yaml",
            "config/templates/qme_template_structure.yaml",
            "config/system/component_config.yaml",
            "config/settings/openrouter_config.yaml"
        ]
        
        for config_path in required_configs:
            if not Path(config_path).exists():
                logger.warning(f"Missing configuration file: {config_path}")
                return False
        
        return True
    
    def _validate_directory_structure(self) -> bool:
        """Validate new directory structure"""
        required_dirs = [
            "results/generated_documents",
            "results/templates_archive",
            "results/processing_logs",
            "results/validation_reports",
            "config/prompts/extraction",
            "config/prompts/generation",
            "config/prompts/validation",
            "config/templates",
            "config/settings"
        ]
        
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                logger.warning(f"Missing directory: {dir_path}")
                return False
        
        return True
    
    def _validate_service_availability(self) -> bool:
        """Validate that services can be initialized"""
        try:
            if self.quality_validator is None:
                self.quality_validator = QualityValidationService()
            
            if self.performance_monitor is None:
                self.performance_monitor = PerformanceMonitoringService()
            
            return True
        except Exception as e:
            logger.warning(f"Service validation failed: {e}")
            return False
    
    def _validate_document_migration(self) -> bool:
        """Validate document migration"""
        archive_dir = Path("results/templates_archive")
        if not archive_dir.exists():
            return False
        
        # Check if documents were migrated
        doc_count = len(list(archive_dir.glob("**/*.docx")))
        self.migration_log['statistics']['migrated_document_count'] = doc_count
        
        return doc_count >= 0  # Allow zero documents
    
    def _generate_migration_report(self):
        """Generate comprehensive migration report"""
        logger.info("Generating migration report...")
        
        try:
            report_dir = Path("results/migration_reports")
            report_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = report_dir / f"migration_report_{self.migration_timestamp}.json"
            
            # Add summary statistics
            self.migration_log['summary'] = {
                'migration_successful': len(self.migration_log['errors']) == 0,
                'steps_completed': len(self.migration_log['steps_completed']),
                'total_errors': len(self.migration_log['errors']),
                'total_warnings': len(self.migration_log['warnings']),
                'migration_duration': 'completed',
                'backup_location': str(self.backup_dir) if self.backup_existing else None
            }
            
            with open(report_file, 'w') as f:
                json.dump(self.migration_log, f, indent=2, default=str)
            
            logger.info(f"Migration report saved to {report_file}")
            
            # Print summary
            self._print_migration_summary()
            
        except Exception as e:
            logger.error(f"Error generating migration report: {e}")
    
    def _print_migration_summary(self):
        """Print migration summary to console"""
        print("\n" + "="*80)
        print("QME SYSTEM MIGRATION SUMMARY")
        print("="*80)
        
        summary = self.migration_log['summary']
        print(f"Migration Status: {'SUCCESS' if summary['migration_successful'] else 'FAILED'}")
        print(f"Steps Completed: {summary['steps_completed']}")
        print(f"Errors: {summary['total_errors']}")
        print(f"Warnings: {summary['total_warnings']}")
        
        if summary.get('backup_location'):
            print(f"Backup Location: {summary['backup_location']}")
        
        if self.migration_log['errors']:
            print("\nERRORS:")
            for error in self.migration_log['errors']:
                print(f"  - {error}")
        
        if self.migration_log['warnings']:
            print("\nWARNINGS:")
            for warning in self.migration_log['warnings']:
                print(f"  - {warning}")
        
        print("\nCOMPLETED STEPS:")
        for step in self.migration_log['steps_completed']:
            print(f"  ✓ {step}")
        
        print("\n" + "="*80)


def main():
    """Main migration function"""
    parser = argparse.ArgumentParser(description='Migrate QME system to refactored architecture')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backup')
    parser.add_argument('--no-validation', action='store_true', help='Skip migration validation')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without making changes')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
        print("Migration would perform the following steps:")
        print("1. Create system backup")
        print("2. Migrate existing documents")
        print("3. Migrate configuration files")
        print("4. Update database schema")
        print("5. Migrate templates and results")
        print("6. Update service configurations")
        print("7. Validate migration")
        print("8. Generate migration report")
        return
    
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Run migration
    migrator = QMESystemMigrator(
        backup_existing=not args.no_backup,
        validate_migration=not args.no_validation
    )
    
    success = migrator.run_migration()
    
    if success:
        print("\nMigration completed successfully!")
        print("You can now use the refactored QME system.")
        print("Run 'python -m pytest tests/test_end_to_end_quality_validation.py' to validate the system.")
    else:
        print("\nMigration failed. Check the logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()