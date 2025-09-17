"""Patient repository interface and SQLite implementation."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import sqlite3

try:
    from src.models.knowledge_graph import Patient, Claim
    from src.storage.database import db_manager
    from src.utils.logging_config import get_logger
except ImportError:
    from models.knowledge_graph import Patient, Claim
    from storage.database import db_manager
    from utils.logging_config import get_logger

logger = get_logger(__name__)


class PatientRepository(ABC):
    """Abstract repository interface for patient operations."""
    
    @abstractmethod
    def save(self, patient: Patient) -> str:
        """Save patient and return ID."""
        pass
    
    @abstractmethod
    def find_by_id(self, patient_id: str) -> Optional[Patient]:
        """Find patient by ID."""
        pass
    
    @abstractmethod
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Patient]:
        """Find patients matching criteria."""
        pass
    
    @abstractmethod
    def update(self, patient_id: str, updates: Dict[str, Any]) -> bool:
        """Update patient fields."""
        pass
    
    @abstractmethod
    def delete(self, patient_id: str) -> bool:
        """Delete patient."""
        pass
    
    @abstractmethod
    def list_all(self) -> List[Patient]:
        """List all patients."""
        pass
    
    @abstractmethod
    def find_by_case_number(self, case_number: str) -> Optional[Patient]:
        """Find patient by case number."""
        pass
    
    @abstractmethod
    def find_by_medical_record_number(self, mrn: str) -> Optional[Patient]:
        """Find patient by medical record number."""
        pass


class SQLitePatientRepository(PatientRepository):
    """SQLite implementation of PatientRepository."""
    
    def __init__(self, db_manager_instance=None):
        try:
            from src.storage.database import db_manager as default_db_manager
        except ImportError:
            from storage.database import db_manager as default_db_manager
        self.db_manager = db_manager_instance or default_db_manager
    
    def save(self, patient: Patient) -> str:
        """Save patient and return ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                patient_data = patient.to_dict()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO patients (
                        id, name, age, gender, case_number, 
                        medical_record_number, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    patient_data['id'], patient_data['name'], patient_data['age'],
                    patient_data['gender'], patient_data['case_number'],
                    patient_data['medical_record_number'], patient_data['created_at'],
                    patient_data['updated_at']
                ))
                
                conn.commit()
                logger.info(f"Saved patient: {patient.id}")
                return patient.id
                
        except Exception as e:
            logger.error(f"Error saving patient: {e}")
            raise
    
    def find_by_id(self, patient_id: str) -> Optional[Patient]:
        """Find patient by ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM patients WHERE id = ?
                """, (patient_id,))
                
                row = cursor.fetchone()
                if row:
                    return Patient.from_dict(dict(row))
                
                return None
                
        except Exception as e:
            logger.error(f"Error finding patient {patient_id}: {e}")
            raise
    
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Patient]:
        """Find patients matching criteria."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic WHERE clause
                where_clauses = []
                values = []
                
                for key, value in criteria.items():
                    if key in ['name', 'gender', 'case_number', 'medical_record_number']:
                        if key == 'name' and isinstance(value, str) and '%' in value:
                            where_clauses.append("name LIKE ?")
                            values.append(value)
                        else:
                            where_clauses.append(f"{key} = ?")
                            values.append(value)
                    elif key == 'age_min':
                        where_clauses.append("age >= ?")
                        values.append(value)
                    elif key == 'age_max':
                        where_clauses.append("age <= ?")
                        values.append(value)
                    elif key == 'created_after':
                        where_clauses.append("created_at > ?")
                        values.append(value.isoformat() if isinstance(value, datetime) else value)
                    elif key == 'created_before':
                        where_clauses.append("created_at < ?")
                        values.append(value.isoformat() if isinstance(value, datetime) else value)
                
                where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                query = f"""
                    SELECT * FROM patients 
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                """
                
                cursor.execute(query, values)
                
                patients = []
                for row in cursor.fetchall():
                    patients.append(Patient.from_dict(dict(row)))
                
                return patients
                
        except Exception as e:
            logger.error(f"Error finding patients by criteria: {e}")
            raise
    
    def update(self, patient_id: str, updates: Dict[str, Any]) -> bool:
        """Update patient fields."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                set_clauses = []
                values = []
                
                for key, value in updates.items():
                    if key in ['name', 'age', 'gender', 'case_number', 'medical_record_number']:
                        set_clauses.append(f"{key} = ?")
                        values.append(value)
                    elif key in ['created_at', 'updated_at'] and isinstance(value, datetime):
                        set_clauses.append(f"{key} = ?")
                        values.append(value.isoformat())
                
                if not set_clauses:
                    return False
                
                # Always update the updated_at timestamp
                if 'updated_at' not in updates:
                    set_clauses.append("updated_at = ?")
                    values.append(datetime.now().isoformat())
                
                values.append(patient_id)
                
                query = f"""
                    UPDATE patients 
                    SET {', '.join(set_clauses)}
                    WHERE id = ?
                """
                
                cursor.execute(query, values)
                conn.commit()
                
                updated = cursor.rowcount > 0
                if updated:
                    logger.info(f"Updated patient: {patient_id}")
                
                return updated
                
        except Exception as e:
            logger.error(f"Error updating patient {patient_id}: {e}")
            raise
    
    def delete(self, patient_id: str) -> bool:
        """Delete patient."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete patient (cascading will handle related records)
                cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
                conn.commit()
                
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Deleted patient: {patient_id}")
                
                return deleted
                
        except Exception as e:
            logger.error(f"Error deleting patient {patient_id}: {e}")
            raise
    
    def list_all(self) -> List[Patient]:
        """List all patients."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM patients 
                    ORDER BY created_at DESC
                """)
                
                patients = []
                for row in cursor.fetchall():
                    patients.append(Patient.from_dict(dict(row)))
                
                return patients
                
        except Exception as e:
            logger.error(f"Error listing patients: {e}")
            raise
    
    def find_by_case_number(self, case_number: str) -> Optional[Patient]:
        """Find patient by case number."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM patients WHERE case_number = ?
                """, (case_number,))
                
                row = cursor.fetchone()
                if row:
                    return Patient.from_dict(dict(row))
                
                return None
                
        except Exception as e:
            logger.error(f"Error finding patient by case number {case_number}: {e}")
            raise
    
    def find_by_medical_record_number(self, mrn: str) -> Optional[Patient]:
        """Find patient by medical record number."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM patients WHERE medical_record_number = ?
                """, (mrn,))
                
                row = cursor.fetchone()
                if row:
                    return Patient.from_dict(dict(row))
                
                return None
                
        except Exception as e:
            logger.error(f"Error finding patient by MRN {mrn}: {e}")
            raise