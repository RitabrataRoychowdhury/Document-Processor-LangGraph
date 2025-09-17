#!/usr/bin/env python3
"""
Rollback Script for QME System Migration

This script provides rollback capabilities to restore the system to its
pre-migration state if issues occur with the refactored system.
"""

import os
import sys
import shutil
import logging
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/rollback.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class QMESystemRollback:
    """Handles rollback from refactored QME system to previous version"""
    
    def __init__(self, backup_dir: str, verify_backup: bool = True):
        self.backup_dir = Path(backup_dir)
        self.verify_backup = verify_backup
        self.rollback_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Rollback tracking
        self.rollback_log = {
            'timestamp': self.rollback_timestamp,
            'backup_source': str(self.backup_dir),
            'steps_completed': [],
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        # Validate backup directory
        if not self.backup_dir.exists():
            raise ValueError(f"Backup directory does not exist: {self.backup_dir}")
    
    def run_rollback(self) -> bool:
        """Run complete rollback process"""
        logger.info(f"Starting QME system rollback from backup: {self.backup_dir}")
        
        try:
            # Step 1: Verify backup integrity
            if self.verify_backup:
                self._verify_backup_integrity()
            
            # Step 2: Create current state backup
            self._backup_current_state()
            
            # Step 3: Stop running services
            self._stop_running_services()
            
            # Step 4: Restore database
            self._restore_database()
            
            # Step 5: Restore configuration files
            self._restore_configuration_files()
            
            # Step 6: Restore service files
            self._restore_service_files()
            
            # Step 7: Restore results and data
            self._restore_results_and_data()
            
            # Step 8: Clean up refactored system files
            self._cleanup_refactored_files()
            
            # Step 9: Validate rollback
            self._validate_rollback()
            
            # Step 10: Generate rollback report
            self._generate_rollback_report()
            
            logger.info("Rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            self.rollback_log['errors'].append(f"Rollback failed: {str(e)}")
            self._generate_rollback_report()
            return False
    
    def _verify_backup_integrity(self):
        """Verify backup directory contains required files"""
        logger.info("Verifying backup integrity...")
        
        try:
            required_backups = [
                'results_backup',
                'data_backup',
                'config_backup',
                'services_backup'
            ]
            
            missing_backups = []
            for backup_name in required_backups:
                backup_path = self.backup_dir / backup_name
                if not backup_path.exists():
                    missing_backups.append(backup_name)
            
            if missing_backups:
                raise ValueError(f"Missing backup directories: {missing_backups}")
            
            # Check database backup
            db_backup = self.backup_dir / "documents_backup.db"
            if not db_backup.exists():
                self.rollback_log['warnings'].append("Database backup not found")
            
            self.rollback_log['steps_completed'].append('backup_integrity_verification')
            logger.info("Backup integrity verification completed")
            
        except Exception as e:
            error_msg = f"Error verifying backup integrity: {e}"
            logger.error(error_msg)
            self.rollback_log['errors'].append(error_msg)
            raise
    
    def _backup_current_state(self):
        """Create backup of current state before rollback"""
        logger.info("Creating backup of current state...")
        
        try:
            current_backup_dir = Path(f"rollback_backup_{self.rollback_timestamp}")
            current_backup_dir.mkdir(exist_ok=True)
            
            # Backup current directories
            backup_targets = [
                ('results', 'current_results'),
                ('config', 'current_config'),
                ('src/services', 'current_services'),
                ('data', 'current_data')
            ]
            
            for source, backup_name in backup_targets:
                source_path = Path(source)
                if source_path.exists():
                    backup_path = current_backup_dir / backup_name
                    if source_path.is_dir():
                        shutil.copytree(source_path, backup_path, ignore_errors=True)
                    else:
                        shutil.copy2(source_path, backup_path)
                    logger.info(f"Backed up current {source} to {backup_path}")
            
            self.rollback_log['statistics']['current_state_backup'] = str(current_backup_dir)
            self.rollback_log['steps_completed'].append('current_state_backup')
            logger.info("Current state backup completed")
            
        except Exception as e:
            error_msg = f"Error backing up current state: {e}"
            logger.error(error_msg)
            self.rollback_log['errors'].append(error_msg)
            raise
    
    def _stop_running_services(self):
        """Stop any running QME services"""
        logger.info("Stopping running services...")
        
        try:
            # This is a placeholder - in a real implementation, you would
            # stop specific services, kill processes, etc.
            import subprocess
            
            # Try to stop any Python processes related to QME
            try:
                subprocess.run(['pkill', '-f', 'python.*qme'], check=False)
                subprocess.run(['pkill', '-f', 'python.*main.py'], check=False)
                logger.info("Stopped QME-related processes")
            except Exception as e:
                logger.warning(f"Could not stop processes: {e}")
            
            self.rollback_log['steps_completed'].append('service_shutdown')
            logger.info("Service shutdown completed")
            
        except Exception as e:
            error_msg = f"Error stopping services: {e}"
            logger.error(error_msg)
            self.rollback_log['errors'].append(error_msg)
            # Don't raise - this is not critical for rollback
    
    def _restore_database(self):
        """Restore database from backup"""
        logger.info("Restoring database...")
        
        try:
            db_backup = self.backup_dir / "documents_backup.db"
            db_target = Path("data/database/documents.db")
            
            if db_backup.exists():
                # Ensure target directory exists
                db_target.parent.mkdir(parents=True, exist_ok=True)
                
                # Backup current database if it exists
                if db_target.exists():
                    current_db_backup = db_target.with_suffix(f".rollback_backup_{self.rollback_timestamp}.db")
                    shutil.copy2(db_target, current_db_backup)
                    logger.info(f"Current database backed up to {current_db_backup}")
                
                # Restore database
                shutil.copy2(db_backup, db_target)
                logger.info(f"Database restored from {db_backup}")
            else:
                logger.warning("No database backup found to restore")
            
            self.rollback_log['steps_completed'].append('database_restoration')
            logger.info("Database restoration completed")
            
        except Exception as e:
            error_msg = f"Error restoring database: {e}"
            logger.error(error_msg)
            self.rollback_log['errors'].append(error_msg)
            raise
    
    def _restore_configuration_files(self):
        """Restore configuration files from backup"""
        logger.info("Restoring configuration files...")
        
        try:
            config_backup = self.backup_dir / "config_backup"
            config_target = Path("config")
            
            if config_backup.exists():
                # Remove current config directory
                if config_target.exists():
                    shutil.rmtree(config_target)
                
                # Restore config from backup
                shutil.copytree(config_backup, config_target)
                logger.info(f"Configuration restored from {config_backup}")
            else:
                logger.warning("No configuration backup found to restore")
            
            self.rollback_log['steps_completed'].append('configuration_restoration')
            logger.info("Configuration restoration completed")
            
        except Exception as e:
            error_msg = f"Error restoring configuration: {e}"
            logger.error(error_msg)
            self.rollback_log['errors'].append(error_msg)
            raise
    
    def _restore_service_files(self):
        """Restore service files from backup"""
        logger.info("Restoring service files...")
        
        try:
            services_backup = self.backup_dir / "services_backup"
            services_target = Path("src/services")
            
            if services_backup.exists():
                # Backup current services
                if services_target.exists():
                    current_services_backup = Path(f"src/services_rollback_backup_{self.rollback_timestamp}")
                    shutil.copytree(services_target, current_services_backup, ignore_errors=True)
                    logger.info(f"Current services backed up to {current_services_backup}")
                    
                    # Remove current services
                    shutil.rmtree(services_target)
                
                # Restore services from backup
                shutil.copytree(services_backup, services_target)
                logger.info(f"Services restored from {services_backup}")
            else:
                logger.warning("No services backup found to restore")
            
            self.rollback_log['steps_completed'].append('services_restoration')
            logger.info("Services restoration completed")
            
        except Exception as e:
            error_msg = f"Error restoring services: {e}"
            logger.error(error_msg)
            self.rollback_log['errors'].append(error_msg)
            raise
    
    def _restore_results_and_data(self):
        """Restore results and data from backup"""
        logger.info("Restoring results and data...")
        
        try:
            # Restore results
            results_backup = self.backup_dir / "results_backup"
            results_target = Path("results")
            
            if results_backup.exists():
                # Backup current results
                if results_target.exists():
                    current_results_backup = Path(f"results_rollback_backup_{self.rollback_timestamp}")
                    shutil.copytree(results_target, current_results_backup, ignore_errors=True)
                    logger.info(f"Current results backed up to {current_results_backup}")
                    
                    # Remove current results
                    shutil.rmtree(results_target)
                
                # Restore results from backup
                shutil.copytree(results_backup, results_target)
                logger.info(f"Results restored from {results_backup}")
            
            # Restore data
            data_backup = self.backup_dir / "data_backup"
            data_target = Path("data")
            
            if data_backup.exists():
                # Restore specific data directories (preserve database which was handled separately)
                for item in data_backup.iterdir():
                    if item.name == "database":
                        continue  # Skip database - handled separately
                    
                    target_item = data_target / item.name
                    if target_item.exists():
                        if target_item.is_dir():
                            shutil.rmtree(target_item)
                        else:
                            target_item.unlink()
                    
                    if item.is_dir():
                        shutil.copytree(item, target_item)
                    else:
                        shutil.copy2(item, target_item)
                    
                    logger.info(f"Restored data item: {item.name}")
            
            self.rollback_log['steps_completed'].append('results_data_restoration')
            logger.info("Results and data restoration completed")
            
        except Exception as e:
            error_msg = f"Error restoring results and data: {e}"
            logger.error(error_msg)
            self.rollback_log['errors'].append(error_msg)
            raise
    
    def _cleanup_refactored_files(self):
        """Clean up files specific to refactored system"""
        logger.info("Cleaning up refactored system files...")
        
        try:
            # Remove refactored-specific files
            refactored_files = [
                "src/services/quality_validation_service.py",
                "src/services/performance_monitoring_service.py",
                "tests/test_end_to_end_quality_validation.py",
                "config/validation",
                "config/monitoring",
                "results/migration_reports",
                "results/validation_reports"
            ]
            
            removed_files = []
            for file_path in refactored_files:
                path = Path(file_path)
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    removed_files.append(str(path))
                    logger.info(f"Removed refactored file: {path}")
            
            self.rollback_log['statistics']['removed_refactored_files'] = removed_files
            self.rollback_log['steps_completed'].append('refactored_cleanup')
            logger.info("Refactored system cleanup completed")
            
        except Exception as e:
            error_msg = f"Error cleaning up refactored files: {e}"
            logger.error(error_msg)
            self.rollback_log['errors'].append(error_msg)
            # Don't raise - this is not critical for rollback
    
    def _validate_rollback(self):
        """Validate rollback success"""
        logger.info("Validating rollback...")
        
        try:
            validation_results = {
                'database_restored': self._validate_database_restoration(),
                'config_restored': self._validate_config_restoration(),
                'services_restored': self._validate_services_restoration(),
                'results_restored': self._validate_results_restoration()
            }
            
            all_valid = all(validation_results.values())
            
            if all_valid:
                logger.info("Rollback validation passed")
                self.rollback_log['steps_completed'].append('rollback_validation')
            else:
                logger.warning("Rollback validation found issues")
                for check, result in validation_results.items():
                    if not result:
                        self.rollback_log['warnings'].append(f"Validation failed: {check}")
            
            self.rollback_log['statistics']['validation_results'] = validation_results
            
        except Exception as e:
            error_msg = f"Error during rollback validation: {e}"
            logger.error(error_msg)
            self.rollback_log['errors'].append(error_msg)
    
    def _validate_database_restoration(self) -> bool:
        """Validate database restoration"""
        db_path = Path("data/database/documents.db")
        return db_path.exists()
    
    def _validate_config_restoration(self) -> bool:
        """Validate configuration restoration"""
        config_path = Path("config")
        return config_path.exists() and config_path.is_dir()
    
    def _validate_services_restoration(self) -> bool:
        """Validate services restoration"""
        services_path = Path("src/services")
        return services_path.exists() and len(list(services_path.glob("*.py"))) > 0
    
    def _validate_results_restoration(self) -> bool:
        """Validate results restoration"""
        results_path = Path("results")
        return results_path.exists()
    
    def _generate_rollback_report(self):
        """Generate comprehensive rollback report"""
        logger.info("Generating rollback report...")
        
        try:
            report_dir = Path("logs")
            report_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = report_dir / f"rollback_report_{self.rollback_timestamp}.json"
            
            # Add summary statistics
            self.rollback_log['summary'] = {
                'rollback_successful': len(self.rollback_log['errors']) == 0,
                'steps_completed': len(self.rollback_log['steps_completed']),
                'total_errors': len(self.rollback_log['errors']),
                'total_warnings': len(self.rollback_log['warnings']),
                'rollback_duration': 'completed',
                'backup_source': str(self.backup_dir)
            }
            
            with open(report_file, 'w') as f:
                json.dump(self.rollback_log, f, indent=2, default=str)
            
            logger.info(f"Rollback report saved to {report_file}")
            
            # Print summary
            self._print_rollback_summary()
            
        except Exception as e:
            logger.error(f"Error generating rollback report: {e}")
    
    def _print_rollback_summary(self):
        """Print rollback summary to console"""
        print("\n" + "="*80)
        print("QME SYSTEM ROLLBACK SUMMARY")
        print("="*80)
        
        summary = self.rollback_log['summary']
        print(f"Rollback Status: {'SUCCESS' if summary['rollback_successful'] else 'FAILED'}")
        print(f"Steps Completed: {summary['steps_completed']}")
        print(f"Errors: {summary['total_errors']}")
        print(f"Warnings: {summary['total_warnings']}")
        print(f"Backup Source: {summary['backup_source']}")
        
        if self.rollback_log['errors']:
            print("\nERRORS:")
            for error in self.rollback_log['errors']:
                print(f"  - {error}")
        
        if self.rollback_log['warnings']:
            print("\nWARNINGS:")
            for warning in self.rollback_log['warnings']:
                print(f"  - {warning}")
        
        print("\nCOMPLETED STEPS:")
        for step in self.rollback_log['steps_completed']:
            print(f"  ✓ {step}")
        
        print("\n" + "="*80)


def find_latest_backup() -> Optional[str]:
    """Find the latest migration backup directory"""
    backup_pattern = "migration_backup_*"
    backup_dirs = list(Path(".").glob(backup_pattern))
    
    if not backup_dirs:
        return None
    
    # Sort by timestamp in directory name
    backup_dirs.sort(key=lambda x: x.name.split("_")[-2:], reverse=True)
    return str(backup_dirs[0])


def main():
    """Main rollback function"""
    parser = argparse.ArgumentParser(description='Rollback QME system migration')
    parser.add_argument('--backup-dir', help='Backup directory to restore from')
    parser.add_argument('--no-verification', action='store_true', help='Skip backup verification')
    parser.add_argument('--list-backups', action='store_true', help='List available backup directories')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be restored without making changes')
    
    args = parser.parse_args()
    
    if args.list_backups:
        backup_dirs = list(Path(".").glob("migration_backup_*"))
        if backup_dirs:
            print("Available backup directories:")
            for backup_dir in sorted(backup_dirs, reverse=True):
                print(f"  - {backup_dir}")
        else:
            print("No backup directories found")
        return
    
    # Determine backup directory
    backup_dir = args.backup_dir
    if not backup_dir:
        backup_dir = find_latest_backup()
        if not backup_dir:
            print("No backup directory specified and no migration backups found")
            print("Use --list-backups to see available backups")
            sys.exit(1)
        print(f"Using latest backup: {backup_dir}")
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
        print(f"Rollback would restore from: {backup_dir}")
        print("Rollback would perform the following steps:")
        print("1. Verify backup integrity")
        print("2. Create current state backup")
        print("3. Stop running services")
        print("4. Restore database")
        print("5. Restore configuration files")
        print("6. Restore service files")
        print("7. Restore results and data")
        print("8. Clean up refactored system files")
        print("9. Validate rollback")
        print("10. Generate rollback report")
        return
    
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Run rollback
    rollback = QMESystemRollback(
        backup_dir=backup_dir,
        verify_backup=not args.no_verification
    )
    
    success = rollback.run_rollback()
    
    if success:
        print("\nRollback completed successfully!")
        print("The system has been restored to its pre-migration state.")
        print("You can now use the original QME system.")
    else:
        print("\nRollback failed. Check the logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()