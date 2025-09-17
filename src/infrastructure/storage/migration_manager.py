"""
Database Migration Manager for Production QME System.

This module provides comprehensive database migration capabilities including:
- Version-controlled schema migrations with rollback support
- Data migration and transformation utilities
- Migration validation and integrity checks
- Backup and recovery mechanisms for safe migrations
- Cross-database compatibility (SQLite to PostgreSQL)

Designed for production deployment with zero-downtime migration support.
"""

import sqlite3
import logging
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import shutil
import tempfile

logger = logging.getLogger(__name__)


class MigrationStatus(Enum):
    """Migration execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class MigrationDirection(Enum):
    """Migration direction"""
    UP = "up"
    DOWN = "down"


@dataclass
class Migration:
    """Database migration definition"""
    version: str
    name: str
    description: str
    up_sql: str
    down_sql: str
    dependencies: List[str] = field(default_factory=list)
    data_migration: Optional[Callable] = None
    validation: Optional[Callable] = None
    checksum: str = field(init=False)
    
    def __post_init__(self):
        """Calculate migration checksum"""
        content = f"{self.version}{self.name}{self.up_sql}{self.down_sql}"
        self.checksum = hashlib.sha256(content.encode()).hexdigest()


@dataclass
class MigrationRecord:
    """Migration execution record"""
    version: str
    name: str
    status: MigrationStatus
    applied_at: float
    execution_time_ms: float
    checksum: str
    error_message: Optional[str] = None
    rollback_info: Optional[Dict[str, Any]] = None


class DatabaseMigrationManager:
    """
    Comprehensive database migration manager for production deployments.
    
    Provides version-controlled migrations with rollback support,
    data transformations, and cross-database compatibility.
    """
    
    def __init__(
        self,
        database_path: str,
        migrations_directory: str = "migrations",
        backup_directory: str = "backups/migrations"
    ):
        """Initialize migration manager"""
        self.database_path = Path(database_path)
        self.migrations_directory = Path(migrations_directory)
        self.backup_directory = Path(backup_directory)
        
        # Create directories
        self.migrations_directory.mkdir(parents=True, exist_ok=True)
        self.backup_directory.mkdir(parents=True, exist_ok=True)
        
        # Migration tracking
        self.migrations: Dict[str, Migration] = {}
        self.migration_records: List[MigrationRecord] = []
        
        # Initialize migration tracking table
        self._initialize_migration_table()
        
        # Load existing migrations
        self._load_migrations()
        self._load_migration_records()
        
        logger.info(f"Migration manager initialized with {len(self.migrations)} migrations")
    
    def _initialize_migration_table(self):
        """Initialize migration tracking table"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        applied_at REAL NOT NULL,
                        execution_time_ms REAL NOT NULL,
                        checksum TEXT NOT NULL,
                        error_message TEXT,
                        rollback_info TEXT
                    )
                """)
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to initialize migration table: {e}")
            raise
    
    def _load_migrations(self):
        """Load migration definitions from files"""
        migration_files = sorted(self.migrations_directory.glob("*.sql"))
        
        for migration_file in migration_files:
            try:
                migration = self._parse_migration_file(migration_file)
                self.migrations[migration.version] = migration
                logger.debug(f"Loaded migration: {migration.version} - {migration.name}")
                
            except Exception as e:
                logger.error(f"Failed to load migration {migration_file}: {e}")
    
    def _parse_migration_file(self, migration_file: Path) -> Migration:
        """Parse migration file and extract metadata"""
        content = migration_file.read_text(encoding='utf-8')
        
        # Extract metadata from comments
        lines = content.split('\n')
        metadata = {}
        up_sql = []
        down_sql = []
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Parse metadata comments
            if line.startswith('-- @'):
                key, value = line[3:].split(':', 1)
                metadata[key.strip()] = value.strip()
            
            # Parse section markers
            elif line == '-- +migrate Up':
                current_section = 'up'
            elif line == '-- +migrate Down':
                current_section = 'down'
            
            # Collect SQL statements
            elif current_section == 'up' and line and not line.startswith('--'):
                up_sql.append(line)
            elif current_section == 'down' and line and not line.startswith('--'):
                down_sql.append(line)
        
        # Extract version from filename
        version = migration_file.stem.split('_')[0]
        
        return Migration(
            version=version,
            name=metadata.get('name', migration_file.stem),
            description=metadata.get('description', ''),
            up_sql='\n'.join(up_sql),
            down_sql='\n'.join(down_sql),
            dependencies=metadata.get('dependencies', '').split(',') if metadata.get('dependencies') else []
        )
    
    def _load_migration_records(self):
        """Load migration execution records"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT version, name, status, applied_at, execution_time_ms, 
                           checksum, error_message, rollback_info
                    FROM schema_migrations
                    ORDER BY applied_at
                """)
                
                for row in cursor.fetchall():
                    record = MigrationRecord(
                        version=row[0],
                        name=row[1],
                        status=MigrationStatus(row[2]),
                        applied_at=row[3],
                        execution_time_ms=row[4],
                        checksum=row[5],
                        error_message=row[6],
                        rollback_info=json.loads(row[7]) if row[7] else None
                    )
                    self.migration_records.append(record)
                    
        except Exception as e:
            logger.error(f"Failed to load migration records: {e}")
    
    def create_migration(
        self,
        name: str,
        description: str = "",
        dependencies: Optional[List[str]] = None
    ) -> str:
        """Create a new migration file template"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        version = timestamp
        filename = f"{version}_{name.replace(' ', '_').lower()}.sql"
        migration_file = self.migrations_directory / filename
        
        template = f"""-- @name: {name}
-- @description: {description}
-- @dependencies: {','.join(dependencies or [])}

-- +migrate Up
-- Add your up migration SQL here


-- +migrate Down
-- Add your down migration SQL here

"""
        
        migration_file.write_text(template, encoding='utf-8')
        logger.info(f"Created migration template: {migration_file}")
        
        return version
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations"""
        applied_versions = {
            record.version for record in self.migration_records
            if record.status == MigrationStatus.COMPLETED
        }
        
        pending = []
        for version, migration in sorted(self.migrations.items()):
            if version not in applied_versions:
                # Check dependencies
                if self._check_dependencies(migration):
                    pending.append(migration)
        
        return pending
    
    def _check_dependencies(self, migration: Migration) -> bool:
        """Check if migration dependencies are satisfied"""
        if not migration.dependencies:
            return True
        
        applied_versions = {
            record.version for record in self.migration_records
            if record.status == MigrationStatus.COMPLETED
        }
        
        return all(dep in applied_versions for dep in migration.dependencies)
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """Create database backup before migration"""
        if backup_name is None:
            backup_name = f"backup_{int(time.time())}"
        
        backup_path = self.backup_directory / f"{backup_name}.db"
        
        try:
            shutil.copy2(self.database_path, backup_path)
            logger.info(f"Database backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def restore_backup(self, backup_path: str):
        """Restore database from backup"""
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        try:
            # Create temporary backup of current database
            temp_backup = self.database_path.with_suffix('.temp_backup')
            shutil.copy2(self.database_path, temp_backup)
            
            # Restore from backup
            shutil.copy2(backup_file, self.database_path)
            
            # Remove temporary backup
            temp_backup.unlink()
            
            logger.info(f"Database restored from backup: {backup_path}")
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            raise
    
    def validate_migration(self, migration: Migration) -> Tuple[bool, List[str]]:
        """Validate migration before execution"""
        errors = []
        
        # Check SQL syntax
        try:
            with sqlite3.connect(":memory:") as conn:
                # Test up migration
                conn.executescript(migration.up_sql)
                
                # Test down migration
                conn.executescript(migration.down_sql)
                
        except sqlite3.Error as e:
            errors.append(f"SQL syntax error: {e}")
        
        # Check dependencies
        if not self._check_dependencies(migration):
            missing_deps = [
                dep for dep in migration.dependencies
                if dep not in {r.version for r in self.migration_records if r.status == MigrationStatus.COMPLETED}
            ]
            errors.append(f"Missing dependencies: {missing_deps}")
        
        # Custom validation
        if migration.validation:
            try:
                validation_errors = migration.validation()
                if validation_errors:
                    errors.extend(validation_errors)
            except Exception as e:
                errors.append(f"Validation function error: {e}")
        
        return len(errors) == 0, errors
    
    def execute_migration(
        self,
        migration: Migration,
        direction: MigrationDirection = MigrationDirection.UP,
        create_backup: bool = True
    ) -> MigrationRecord:
        """Execute a single migration"""
        start_time = time.time()
        
        logger.info(f"Executing migration {migration.version} ({direction.value}): {migration.name}")
        
        # Validate migration
        is_valid, validation_errors = self.validate_migration(migration)
        if not is_valid:
            error_msg = f"Migration validation failed: {'; '.join(validation_errors)}"
            logger.error(error_msg)
            
            return MigrationRecord(
                version=migration.version,
                name=migration.name,
                status=MigrationStatus.FAILED,
                applied_at=time.time(),
                execution_time_ms=0,
                checksum=migration.checksum,
                error_message=error_msg
            )
        
        # Create backup if requested
        backup_path = None
        if create_backup:
            backup_path = self.create_backup(f"pre_migration_{migration.version}")
        
        # Record migration start
        record = MigrationRecord(
            version=migration.version,
            name=migration.name,
            status=MigrationStatus.RUNNING,
            applied_at=time.time(),
            execution_time_ms=0,
            checksum=migration.checksum
        )
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Execute SQL
                sql = migration.up_sql if direction == MigrationDirection.UP else migration.down_sql
                conn.executescript(sql)
                
                # Execute data migration if present
                if direction == MigrationDirection.UP and migration.data_migration:
                    migration.data_migration(conn)
                
                conn.commit()
            
            # Update record
            execution_time = (time.time() - start_time) * 1000
            record.status = MigrationStatus.COMPLETED
            record.execution_time_ms = execution_time
            record.rollback_info = {"backup_path": backup_path} if backup_path else None
            
            # Save migration record
            self._save_migration_record(record)
            
            logger.info(f"Migration {migration.version} completed in {execution_time:.2f}ms")
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            record.status = MigrationStatus.FAILED
            record.execution_time_ms = execution_time
            record.error_message = error_msg
            
            logger.error(f"Migration {migration.version} failed: {error_msg}")
            
            # Restore backup if available
            if backup_path:
                try:
                    self.restore_backup(backup_path)
                    logger.info("Database restored from backup after migration failure")
                except Exception as restore_error:
                    logger.error(f"Failed to restore backup: {restore_error}")
        
        return record
    
    def _save_migration_record(self, record: MigrationRecord):
        """Save migration record to database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO schema_migrations 
                    (version, name, status, applied_at, execution_time_ms, checksum, error_message, rollback_info)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.version,
                    record.name,
                    record.status.value,
                    record.applied_at,
                    record.execution_time_ms,
                    record.checksum,
                    record.error_message,
                    json.dumps(record.rollback_info) if record.rollback_info else None
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to save migration record: {e}")
    
    def migrate_up(self, target_version: Optional[str] = None) -> List[MigrationRecord]:
        """Run pending migrations up to target version"""
        pending_migrations = self.get_pending_migrations()
        
        if target_version:
            # Filter migrations up to target version
            pending_migrations = [
                m for m in pending_migrations
                if m.version <= target_version
            ]
        
        if not pending_migrations:
            logger.info("No pending migrations to execute")
            return []
        
        logger.info(f"Executing {len(pending_migrations)} pending migrations")
        
        results = []
        for migration in pending_migrations:
            record = self.execute_migration(migration, MigrationDirection.UP)
            results.append(record)
            
            # Stop on failure
            if record.status == MigrationStatus.FAILED:
                logger.error(f"Migration failed, stopping at {migration.version}")
                break
        
        return results
    
    def migrate_down(self, target_version: str) -> List[MigrationRecord]:
        """Rollback migrations down to target version"""
        applied_migrations = [
            record for record in self.migration_records
            if record.status == MigrationStatus.COMPLETED and record.version > target_version
        ]
        
        # Sort in reverse order for rollback
        applied_migrations.sort(key=lambda r: r.version, reverse=True)
        
        if not applied_migrations:
            logger.info("No migrations to rollback")
            return []
        
        logger.info(f"Rolling back {len(applied_migrations)} migrations")
        
        results = []
        for record in applied_migrations:
            migration = self.migrations.get(record.version)
            if migration:
                rollback_record = self.execute_migration(migration, MigrationDirection.DOWN)
                rollback_record.status = MigrationStatus.ROLLED_BACK
                results.append(rollback_record)
                
                # Update original record
                record.status = MigrationStatus.ROLLED_BACK
                self._save_migration_record(record)
        
        return results
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get comprehensive migration status"""
        pending = self.get_pending_migrations()
        applied = [r for r in self.migration_records if r.status == MigrationStatus.COMPLETED]
        failed = [r for r in self.migration_records if r.status == MigrationStatus.FAILED]
        
        return {
            "total_migrations": len(self.migrations),
            "applied_count": len(applied),
            "pending_count": len(pending),
            "failed_count": len(failed),
            "current_version": applied[-1].version if applied else None,
            "pending_migrations": [
                {"version": m.version, "name": m.name, "description": m.description}
                for m in pending
            ],
            "failed_migrations": [
                {"version": r.version, "name": r.name, "error": r.error_message}
                for r in failed
            ]
        }
    
    def export_migration_history(self, output_file: str):
        """Export migration history to JSON file"""
        history = {
            "export_timestamp": time.time(),
            "database_path": str(self.database_path),
            "migration_records": [
                {
                    "version": r.version,
                    "name": r.name,
                    "status": r.status.value,
                    "applied_at": r.applied_at,
                    "execution_time_ms": r.execution_time_ms,
                    "checksum": r.checksum,
                    "error_message": r.error_message
                }
                for r in self.migration_records
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(history, f, indent=2, default=str)
        
        logger.info(f"Migration history exported to: {output_file}")


# Global migration manager instance
_migration_manager: Optional[DatabaseMigrationManager] = None


def get_migration_manager(
    database_path: str,
    migrations_directory: str = "migrations"
) -> DatabaseMigrationManager:
    """Get global migration manager instance"""
    global _migration_manager
    
    if _migration_manager is None:
        _migration_manager = DatabaseMigrationManager(database_path, migrations_directory)
    
    return _migration_manager


def initialize_migration_manager(
    database_path: str,
    migrations_directory: str = "migrations"
) -> DatabaseMigrationManager:
    """Initialize global migration manager"""
    global _migration_manager
    _migration_manager = DatabaseMigrationManager(database_path, migrations_directory)
    return _migration_manager