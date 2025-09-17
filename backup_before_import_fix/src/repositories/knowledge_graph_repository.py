"""Knowledge graph repository for managing nodes and relationships."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import sqlite3
import json
import pickle

try:
    from src.models.knowledge_graph import (
        KnowledgeNode, KnowledgeRelationship, Section, Diagnosis, 
        Finding, ImagingStudy, ImpairmentRating
    )
    from src.storage.database import db_manager
    from src.utils.logging_config import get_logger
except ImportError:
    from models.knowledge_graph import (
        KnowledgeNode, KnowledgeRelationship, Section, Diagnosis, 
        Finding, ImagingStudy, ImpairmentRating
    )
    from storage.database import db_manager
    from utils.logging_config import get_logger

logger = get_logger(__name__)


class KnowledgeGraphRepository(ABC):
    """Abstract repository interface for knowledge graph operations."""
    
    @abstractmethod
    def save_node(self, node: KnowledgeNode) -> str:
        """Save knowledge graph node."""
        pass
    
    @abstractmethod
    def save_relationship(self, relationship: KnowledgeRelationship) -> str:
        """Save knowledge graph relationship."""
        pass
    
    @abstractmethod
    def find_node_by_id(self, node_id: str) -> Optional[KnowledgeNode]:
        """Find node by ID."""
        pass
    
    @abstractmethod
    def find_nodes_by_type(self, node_type: str) -> List[KnowledgeNode]:
        """Find nodes by type."""
        pass
    
    @abstractmethod
    def find_relationships_by_source(self, source_node_id: str) -> List[KnowledgeRelationship]:
        """Find relationships by source node."""
        pass
    
    @abstractmethod
    def find_relationships_by_target(self, target_node_id: str) -> List[KnowledgeRelationship]:
        """Find relationships by target node."""
        pass
    
    @abstractmethod
    def find_relationships_by_type(self, relationship_type: str) -> List[KnowledgeRelationship]:
        """Find relationships by type."""
        pass


class SQLiteKnowledgeGraphRepository(KnowledgeGraphRepository):
    """SQLite implementation of KnowledgeGraphRepository."""
    
    def __init__(self, db_manager_instance=None):
        try:
            from src.storage.database import db_manager as default_db_manager
        except ImportError:
            from storage.database import db_manager as default_db_manager
        self.db_manager = db_manager_instance or default_db_manager
    
    def save_node(self, node: KnowledgeNode) -> str:
        """Save knowledge graph node."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                node_data = node.to_dict()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO knowledge_nodes (
                        id, node_type, properties, created_at
                    ) VALUES (?, ?, ?, ?)
                """, (
                    node_data['id'], node_data['node_type'], 
                    node_data['properties'], node_data['created_at']
                ))
                
                # Handle embeddings separately
                if node.embeddings:
                    cursor.execute("""
                        UPDATE knowledge_nodes SET embeddings = ? WHERE id = ?
                    """, (pickle.dumps(node.embeddings), node.id))
                
                conn.commit()
                logger.info(f"Saved knowledge node: {node.id}")
                return node.id
                
        except Exception as e:
            logger.error(f"Error saving knowledge node: {e}")
            raise
    
    def save_relationship(self, relationship: KnowledgeRelationship) -> str:
        """Save knowledge graph relationship."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                rel_data = relationship.to_dict()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO knowledge_relationships (
                        id, source_node_id, target_node_id, relationship_type,
                        properties, confidence, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    rel_data['id'], rel_data['source_node_id'], rel_data['target_node_id'],
                    rel_data['relationship_type'], rel_data['properties'], 
                    rel_data['confidence'], rel_data['created_at']
                ))
                
                conn.commit()
                logger.info(f"Saved knowledge relationship: {relationship.id}")
                return relationship.id
                
        except Exception as e:
            logger.error(f"Error saving knowledge relationship: {e}")
            raise
    
    def find_node_by_id(self, node_id: str) -> Optional[KnowledgeNode]:
        """Find node by ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM knowledge_nodes WHERE id = ?
                """, (node_id,))
                
                row = cursor.fetchone()
                if row:
                    node_dict = dict(row)
                    
                    # Handle embeddings separately if they exist
                    if node_dict.get('embeddings'):
                        try:
                            node_dict['embeddings'] = pickle.loads(node_dict['embeddings'])
                        except:
                            node_dict['embeddings'] = None
                    
                    return KnowledgeNode.from_dict(node_dict)
                
                return None
                
        except Exception as e:
            logger.error(f"Error finding knowledge node {node_id}: {e}")
            raise
    
    def find_nodes_by_type(self, node_type: str) -> List[KnowledgeNode]:
        """Find nodes by type."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM knowledge_nodes 
                    WHERE node_type = ?
                    ORDER BY created_at DESC
                """, (node_type,))
                
                nodes = []
                for row in cursor.fetchall():
                    node_dict = dict(row)
                    
                    # Handle embeddings separately if they exist
                    if node_dict.get('embeddings'):
                        try:
                            node_dict['embeddings'] = pickle.loads(node_dict['embeddings'])
                        except:
                            node_dict['embeddings'] = None
                    
                    nodes.append(KnowledgeNode.from_dict(node_dict))
                
                return nodes
                
        except Exception as e:
            logger.error(f"Error finding nodes by type {node_type}: {e}")
            raise
    
    def find_relationships_by_source(self, source_node_id: str) -> List[KnowledgeRelationship]:
        """Find relationships by source node."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM knowledge_relationships 
                    WHERE source_node_id = ?
                    ORDER BY created_at DESC
                """, (source_node_id,))
                
                relationships = []
                for row in cursor.fetchall():
                    relationships.append(KnowledgeRelationship.from_dict(dict(row)))
                
                return relationships
                
        except Exception as e:
            logger.error(f"Error finding relationships by source {source_node_id}: {e}")
            raise
    
    def find_relationships_by_target(self, target_node_id: str) -> List[KnowledgeRelationship]:
        """Find relationships by target node."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM knowledge_relationships 
                    WHERE target_node_id = ?
                    ORDER BY created_at DESC
                """, (target_node_id,))
                
                relationships = []
                for row in cursor.fetchall():
                    relationships.append(KnowledgeRelationship.from_dict(dict(row)))
                
                return relationships
                
        except Exception as e:
            logger.error(f"Error finding relationships by target {target_node_id}: {e}")
            raise
    
    def find_relationships_by_type(self, relationship_type: str) -> List[KnowledgeRelationship]:
        """Find relationships by type."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM knowledge_relationships 
                    WHERE relationship_type = ?
                    ORDER BY created_at DESC
                """, (relationship_type,))
                
                relationships = []
                for row in cursor.fetchall():
                    relationships.append(KnowledgeRelationship.from_dict(dict(row)))
                
                return relationships
                
        except Exception as e:
            logger.error(f"Error finding relationships by type {relationship_type}: {e}")
            raise
    
    # Specialized methods for medical entities
    
    def save_section(self, section: Section) -> str:
        """Save document section."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                section_data = section.to_dict()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO sections (
                        id, document_id, section_type, page_number, 
                        text_content, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    section_data['id'], section_data['document_id'], 
                    section_data['section_type'], section_data['page_number'],
                    section_data['text_content'], section_data['created_at']
                ))
                
                conn.commit()
                logger.info(f"Saved section: {section.id}")
                return section.id
                
        except Exception as e:
            logger.error(f"Error saving section: {e}")
            raise
    
    def save_diagnosis(self, diagnosis: Diagnosis) -> str:
        """Save diagnosis."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                diag_data = diagnosis.to_dict()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO diagnoses (
                        id, icd_code, description, severity, certainty,
                        source_section_id, page_reference, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    diag_data['id'], diag_data['icd_code'], diag_data['description'],
                    diag_data['severity'], diag_data['certainty'], 
                    diag_data['source_section_id'], diag_data['page_reference'],
                    diag_data['created_at']
                ))
                
                conn.commit()
                logger.info(f"Saved diagnosis: {diagnosis.id}")
                return diagnosis.id
                
        except Exception as e:
            logger.error(f"Error saving diagnosis: {e}")
            raise
    
    def save_finding(self, finding: Finding) -> str:
        """Save medical finding."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                finding_data = finding.to_dict()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO findings (
                        id, section_id, finding_type, description, 
                        page_reference, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    finding_data['id'], finding_data['section_id'], 
                    finding_data['finding_type'], finding_data['description'],
                    finding_data['page_reference'], finding_data['created_at']
                ))
                
                conn.commit()
                logger.info(f"Saved finding: {finding.id}")
                return finding.id
                
        except Exception as e:
            logger.error(f"Error saving finding: {e}")
            raise
    
    def save_impairment_rating(self, rating: ImpairmentRating) -> str:
        """Save impairment rating."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                rating_data = rating.to_dict()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO impairment_ratings (
                        id, diagnosis_id, ama_table, percentage, 
                        rationale, source_page, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    rating_data['id'], rating_data['diagnosis_id'], 
                    rating_data['ama_table'], rating_data['percentage'],
                    rating_data['rationale'], rating_data['source_page'],
                    rating_data['created_at']
                ))
                
                conn.commit()
                logger.info(f"Saved impairment rating: {rating.id}")
                return rating.id
                
        except Exception as e:
            logger.error(f"Error saving impairment rating: {e}")
            raise
    
    def find_sections_by_document(self, document_id: str) -> List[Section]:
        """Find sections by document ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM sections 
                    WHERE document_id = ?
                    ORDER BY page_number ASC
                """, (document_id,))
                
                sections = []
                for row in cursor.fetchall():
                    sections.append(Section.from_dict(dict(row)))
                
                return sections
                
        except Exception as e:
            logger.error(f"Error finding sections by document {document_id}: {e}")
            raise
    
    def find_diagnoses_by_section(self, section_id: str) -> List[Diagnosis]:
        """Find diagnoses by section ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM diagnoses 
                    WHERE source_section_id = ?
                    ORDER BY created_at DESC
                """, (section_id,))
                
                diagnoses = []
                for row in cursor.fetchall():
                    diagnoses.append(Diagnosis.from_dict(dict(row)))
                
                return diagnoses
                
        except Exception as e:
            logger.error(f"Error finding diagnoses by section {section_id}: {e}")
            raise
    
    def find_documents_by_patient(self, patient_id: str) -> List:
        """Find documents associated with a patient."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Find documents through patient relationships or metadata
                cursor.execute("""
                    SELECT DISTINCT d.* FROM documents d
                    LEFT JOIN knowledge_relationships kr ON d.id = kr.target_node_id
                    WHERE kr.source_node_id = ? AND kr.relationship_type = 'HAS_DOCUMENT'
                    OR d.extracted_info LIKE ?
                    ORDER BY d.created_at DESC
                """, (patient_id, f'%{patient_id}%'))
                
                documents = []
                for row in cursor.fetchall():
                    # Convert to document object - simplified for now
                    doc_dict = dict(row)
                    documents.append(type('Document', (), doc_dict)())
                
                return documents
                
        except Exception as e:
            logger.error(f"Error finding documents by patient {patient_id}: {e}")
            return []
    
    def find_impairment_ratings_by_icd(self, icd_code: str) -> List[ImpairmentRating]:
        """Find impairment ratings by ICD code."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT ir.* FROM impairment_ratings ir
                    JOIN diagnoses d ON ir.diagnosis_id = d.id
                    WHERE d.icd_code = ?
                    ORDER BY ir.percentage DESC
                """, (icd_code,))
                
                ratings = []
                for row in cursor.fetchall():
                    ratings.append(ImpairmentRating.from_dict(dict(row)))
                
                return ratings
                
        except Exception as e:
            logger.error(f"Error finding impairment ratings by ICD {icd_code}: {e}")
            return []
    
    def find_impairment_ratings_by_keyword(self, keyword: str) -> List[ImpairmentRating]:
        """Find impairment ratings by keyword in diagnosis description."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT ir.* FROM impairment_ratings ir
                    JOIN diagnoses d ON ir.diagnosis_id = d.id
                    WHERE d.description LIKE ?
                    ORDER BY ir.percentage DESC
                """, (f'%{keyword}%',))
                
                ratings = []
                for row in cursor.fetchall():
                    ratings.append(ImpairmentRating.from_dict(dict(row)))
                
                return ratings
                
        except Exception as e:
            logger.error(f"Error finding impairment ratings by keyword {keyword}: {e}")
            return []
    
    def find_ama_guidelines_by_system(self, body_system: str) -> List[str]:
        """Find AMA guidelines by body system."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Search in knowledge nodes for AMA guidelines
                cursor.execute("""
                    SELECT properties FROM knowledge_nodes 
                    WHERE node_type = 'ama_guideline' 
                    AND properties LIKE ?
                """, (f'%{body_system}%',))
                
                guidelines = []
                for row in cursor.fetchall():
                    try:
                        props = json.loads(row[0])
                        if 'guideline_text' in props:
                            guidelines.append(props['guideline_text'])
                    except:
                        continue
                
                return guidelines
                
        except Exception as e:
            logger.error(f"Error finding AMA guidelines by system {body_system}: {e}")
            return []
    
    def find_ama_guidelines_by_condition(self, condition: str) -> List[str]:
        """Find AMA guidelines by medical condition."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Search in knowledge nodes for AMA guidelines
                cursor.execute("""
                    SELECT properties FROM knowledge_nodes 
                    WHERE node_type = 'ama_guideline' 
                    AND properties LIKE ?
                """, (f'%{condition}%',))
                
                guidelines = []
                for row in cursor.fetchall():
                    try:
                        props = json.loads(row[0])
                        if 'guideline_text' in props:
                            guidelines.append(props['guideline_text'])
                    except:
                        continue
                
                return guidelines
                
        except Exception as e:
            logger.error(f"Error finding AMA guidelines by condition {condition}: {e}")
            return []    

    # Health check methods
    
    def get_node_count(self) -> int:
        """Get total count of knowledge graph nodes."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM knowledge_nodes")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting node count: {e}")
            return 0
    
    def get_relationship_count(self) -> int:
        """Get total count of knowledge graph relationships."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM knowledge_relationships")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting relationship count: {e}")
            return 0
    
    def get_node_types_count(self) -> Dict[str, int]:
        """Get count of nodes by type."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT node_type, COUNT(*) 
                    FROM knowledge_nodes 
                    GROUP BY node_type
                """)
                
                return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Error getting node types count: {e}")
            return {}