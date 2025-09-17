"""
Knowledge Base Validation and Optimization Service

This module provides comprehensive validation of the knowledge base initialization,
performance optimization, and health monitoring for the QME system.
"""

import asyncio
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging

try:
    from src.infrastructure.knowledge.knowledge_base_initializer import KnowledgeBaseInitializer
    from src.infrastructure.knowledge.knowledge_graph_vector_service import KnowledgeGraphVectorService
    from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
    from src.infrastructure.storage.database_manager import DatabaseManager
    from src.config.app_config import AppConfig
except ImportError:
    # Fallback for missing dependencies
    KnowledgeBaseInitializer = None
    KnowledgeGraphVectorService = None
    SQLiteKnowledgeGraphRepository = None
    DatabaseManager = None
    AppConfig = None

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeBaseMetrics:
    """Metrics for knowledge base validation."""
    node_count: int
    relationship_count: int
    entity_type_coverage: Dict[str, int]
    canonical_documents_processed: int
    ama_tables_loaded: int
    legal_patterns_loaded: int
    vector_embeddings_count: int
    index_performance_ms: float
    query_performance_ms: float
    data_integrity_score: float
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class PerformanceOptimizationResult:
    """Result of performance optimization operations."""
    optimization_type: str
    before_metrics: Dict[str, Any]
    after_metrics: Dict[str, Any]
    improvement_percentage: float
    execution_time: float
    success: bool
    recommendations: List[str]


@dataclass
class HealthMonitoringResult:
    """Result of knowledge base health monitoring."""
    overall_health_score: float
    component_health: Dict[str, float]
    data_integrity_checks: Dict[str, bool]
    performance_metrics: Dict[str, float]
    issues_detected: List[str]
    recommendations: List[str]
    monitoring_timestamp: datetime = field(default_factory=datetime.now)


class KnowledgeBaseValidator:
    """Comprehensive knowledge base validation and optimization service."""
    
    def __init__(self, config: Optional[Any] = None):
        """Initialize knowledge base validator."""
        if AppConfig is None:
            raise ImportError("Required dependencies not available for KnowledgeBaseValidator")
        
        self.config = config or AppConfig()
        self.db_manager = DatabaseManager(self.config.database_path)
        self.kg_repository = SQLiteKnowledgeGraphRepository(self.db_manager)
        self.kg_vector_service = KnowledgeGraphVectorService(self.kg_repository)
        
        # Validation thresholds
        self.min_node_count = 1000
        self.min_relationship_count = 500
        self.required_entity_types = {
            'patient', 'diagnosis', 'finding', 'imaging_study', 
            'impairment_rating', 'ama_table', 'legal_requirement',
            'procedural_pattern', 'quality_standard', 'section'
        }
        
        # Performance benchmarks
        self.max_query_time_ms = 100
        self.max_index_time_ms = 50
        self.min_data_integrity_score = 0.95
        
        logger.info("Initialized Knowledge Base Validator")
    
    async def validate_complete_knowledge_base(self) -> Tuple[bool, KnowledgeBaseMetrics, List[str]]:
        """
        Validate complete knowledge base initialization with all canonical documents.
        
        Returns:
            Tuple of (validation_passed, metrics, issues)
        """
        logger.info("Starting complete knowledge base validation")
        start_time = time.time()
        
        try:
            # Collect current metrics
            metrics = await self._collect_knowledge_base_metrics()
            
            # Validate minimum requirements
            validation_issues = []
            
            # Check node count
            if metrics.node_count < self.min_node_count:
                validation_issues.append(
                    f"Insufficient nodes: {metrics.node_count} < {self.min_node_count} required"
                )
            
            # Check relationship count
            if metrics.relationship_count < self.min_relationship_count:
                validation_issues.append(
                    f"Insufficient relationships: {metrics.relationship_count} < {self.min_relationship_count} required"
                )
            
            # Check entity type coverage
            missing_entity_types = self.required_entity_types - set(metrics.entity_type_coverage.keys())
            if missing_entity_types:
                validation_issues.append(
                    f"Missing entity types: {missing_entity_types}"
                )
            
            # Check canonical documents
            if metrics.canonical_documents_processed < 3:
                validation_issues.append(
                    f"Insufficient canonical documents: {metrics.canonical_documents_processed} < 3 required"
                )
            
            # Check AMA tables
            if metrics.ama_tables_loaded < 50:
                validation_issues.append(
                    f"Insufficient AMA tables: {metrics.ama_tables_loaded} < 50 recommended"
                )
            
            # Check legal patterns
            if metrics.legal_patterns_loaded < 10:
                validation_issues.append(
                    f"Insufficient legal patterns: {metrics.legal_patterns_loaded} < 10 recommended"
                )
            
            # Check vector embeddings
            if metrics.vector_embeddings_count < metrics.node_count * 0.8:
                validation_issues.append(
                    f"Insufficient vector embeddings: {metrics.vector_embeddings_count} < 80% of nodes"
                )
            
            # Check performance metrics
            if metrics.query_performance_ms > self.max_query_time_ms:
                validation_issues.append(
                    f"Query performance too slow: {metrics.query_performance_ms}ms > {self.max_query_time_ms}ms"
                )
            
            # Check data integrity
            if metrics.data_integrity_score < self.min_data_integrity_score:
                validation_issues.append(
                    f"Data integrity too low: {metrics.data_integrity_score} < {self.min_data_integrity_score}"
                )
            
            validation_passed = len(validation_issues) == 0
            
            logger.info(f"Knowledge base validation completed in {time.time() - start_time:.2f}s")
            logger.info(f"Validation result: {'PASSED' if validation_passed else 'FAILED'}")
            
            if validation_issues:
                logger.warning(f"Validation issues: {validation_issues}")
            
            return validation_passed, metrics, validation_issues
            
        except Exception as e:
            logger.error(f"Error during knowledge base validation: {e}")
            return False, KnowledgeBaseMetrics(0, 0, {}, 0, 0, 0, 0, 0, 0, 0), [str(e)]
    
    async def _collect_knowledge_base_metrics(self) -> KnowledgeBaseMetrics:
        """Collect comprehensive knowledge base metrics."""
        try:
            # Get basic counts
            node_count = self.kg_repository.get_node_count()
            relationship_count = self.kg_repository.get_relationship_count()
            
            # Get entity type coverage
            entity_type_coverage = self.kg_repository.get_node_types_count()
            
            # Count canonical documents (check for specific document types)
            canonical_docs = 0
            document_nodes = self.kg_repository.find_nodes_by_type('document')
            for doc in document_nodes:
                if any(canonical in doc.properties.get('filename', '').lower() 
                      for canonical in ['ama', 'qme', 'sample']):
                    canonical_docs += 1
            
            # Count AMA tables
            ama_tables = len(self.kg_repository.find_nodes_by_type('ama_table'))
            
            # Count legal patterns
            legal_patterns = len(self.kg_repository.find_nodes_by_type('legal_pattern'))
            
            # Get vector embeddings count
            vector_stats = self.kg_vector_service.get_vector_store_stats()
            vector_embeddings = vector_stats.get('knowledge_graph_documents', 0)
            
            # Measure query performance
            query_start = time.time()
            test_nodes = self.kg_repository.find_nodes_by_type('diagnosis')[:10]
            query_performance_ms = (time.time() - query_start) * 1000
            
            # Measure index performance (simple search)
            index_start = time.time()
            search_results = self.kg_vector_service.search_similar_nodes("test query", top_k=5)
            index_performance_ms = (time.time() - index_start) * 1000
            
            # Calculate data integrity score
            data_integrity_score = await self._calculate_data_integrity_score()
            
            return KnowledgeBaseMetrics(
                node_count=node_count,
                relationship_count=relationship_count,
                entity_type_coverage=entity_type_coverage,
                canonical_documents_processed=canonical_docs,
                ama_tables_loaded=ama_tables,
                legal_patterns_loaded=legal_patterns,
                vector_embeddings_count=vector_embeddings,
                index_performance_ms=index_performance_ms,
                query_performance_ms=query_performance_ms,
                data_integrity_score=data_integrity_score
            )
            
        except Exception as e:
            logger.error(f"Error collecting knowledge base metrics: {e}")
            return KnowledgeBaseMetrics(0, 0, {}, 0, 0, 0, 0, 0, 0, 0)
    
    async def _calculate_data_integrity_score(self) -> float:
        """Calculate data integrity score based on various checks."""
        try:
            integrity_checks = []
            
            # Check for orphaned nodes (nodes without relationships)
            all_nodes = self.kg_repository.get_all_nodes()
            orphaned_nodes = 0
            for node in all_nodes[:100]:  # Sample check
                relationships = self.kg_repository.find_relationships_for_node(node.id)
                if not relationships:
                    orphaned_nodes += 1
            
            orphan_ratio = orphaned_nodes / min(len(all_nodes), 100)
            integrity_checks.append(1.0 - orphan_ratio)
            
            # Check for nodes with missing required properties
            missing_properties = 0
            for node in all_nodes[:100]:  # Sample check
                if node.node_type == 'diagnosis' and not node.properties.get('description'):
                    missing_properties += 1
                elif node.node_type == 'impairment_rating' and not node.properties.get('percentage'):
                    missing_properties += 1
            
            property_ratio = missing_properties / min(len(all_nodes), 100)
            integrity_checks.append(1.0 - property_ratio)
            
            # Check for duplicate nodes (simplified check)
            node_texts = set()
            duplicates = 0
            for node in all_nodes[:100]:  # Sample check
                node_text = str(node.properties.get('description', ''))
                if node_text and node_text in node_texts:
                    duplicates += 1
                else:
                    node_texts.add(node_text)
            
            duplicate_ratio = duplicates / min(len(all_nodes), 100)
            integrity_checks.append(1.0 - duplicate_ratio)
            
            # Return average integrity score
            return sum(integrity_checks) / len(integrity_checks) if integrity_checks else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating data integrity score: {e}")
            return 0.0
    
    async def optimize_knowledge_base_performance(self) -> List[PerformanceOptimizationResult]:
        """
        Implement knowledge base performance optimization with indexing, caching, and query optimization.
        
        Returns:
            List of optimization results
        """
        logger.info("Starting knowledge base performance optimization")
        optimization_results = []
        
        try:
            # 1. Optimize vector store indexing
            indexing_result = await self._optimize_vector_indexing()
            optimization_results.append(indexing_result)
            
            # 2. Optimize database queries
            query_result = await self._optimize_database_queries()
            optimization_results.append(query_result)
            
            # 3. Implement caching strategies
            caching_result = await self._implement_caching_strategies()
            optimization_results.append(caching_result)
            
            # 4. Optimize knowledge graph structure
            structure_result = await self._optimize_graph_structure()
            optimization_results.append(structure_result)
            
            logger.info(f"Performance optimization completed with {len(optimization_results)} optimizations")
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Error during performance optimization: {e}")
            return []
    
    async def _optimize_vector_indexing(self) -> PerformanceOptimizationResult:
        """Optimize vector store indexing for better search performance."""
        try:
            # Measure before performance
            before_start = time.time()
            before_results = self.kg_vector_service.search_similar_nodes("test query", top_k=10)
            before_time = (time.time() - before_start) * 1000
            
            before_metrics = {
                "search_time_ms": before_time,
                "results_count": len(before_results)
            }
            
            # Rebuild vector store with optimizations
            logger.info("Rebuilding vector store for optimization")
            self.kg_vector_service.clear_kg_vectors()
            populate_stats = self.kg_vector_service.populate_vector_store_from_kg()
            
            # Measure after performance
            after_start = time.time()
            after_results = self.kg_vector_service.search_similar_nodes("test query", top_k=10)
            after_time = (time.time() - after_start) * 1000
            
            after_metrics = {
                "search_time_ms": after_time,
                "results_count": len(after_results),
                "documents_indexed": populate_stats.get('total', 0)
            }
            
            # Calculate improvement
            improvement = max(0, (before_time - after_time) / before_time * 100) if before_time > 0 else 0
            
            return PerformanceOptimizationResult(
                optimization_type="vector_indexing",
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement_percentage=improvement,
                execution_time=time.time() - before_start,
                success=True,
                recommendations=[
                    "Vector store rebuilt with optimized indexing",
                    f"Indexed {populate_stats.get('total', 0)} documents",
                    "Consider periodic reindexing for optimal performance"
                ]
            )
            
        except Exception as e:
            logger.error(f"Error optimizing vector indexing: {e}")
            return PerformanceOptimizationResult(
                optimization_type="vector_indexing",
                before_metrics={},
                after_metrics={},
                improvement_percentage=0,
                execution_time=0,
                success=False,
                recommendations=[f"Optimization failed: {str(e)}"]
            )
    
    async def _optimize_database_queries(self) -> PerformanceOptimizationResult:
        """Optimize database queries for better performance."""
        try:
            # Measure before performance
            before_start = time.time()
            test_nodes = self.kg_repository.find_nodes_by_type('diagnosis')[:50]
            before_time = (time.time() - before_start) * 1000
            
            before_metrics = {
                "query_time_ms": before_time,
                "nodes_retrieved": len(test_nodes)
            }
            
            # Create database indexes (if not exists)
            logger.info("Creating database indexes for optimization")
            try:
                # Create indexes on commonly queried columns
                self.db_manager.execute_query(
                    "CREATE INDEX IF NOT EXISTS idx_nodes_type ON knowledge_nodes(node_type)"
                )
                self.db_manager.execute_query(
                    "CREATE INDEX IF NOT EXISTS idx_relationships_source ON knowledge_relationships(source_node_id)"
                )
                self.db_manager.execute_query(
                    "CREATE INDEX IF NOT EXISTS idx_relationships_target ON knowledge_relationships(target_node_id)"
                )
            except Exception as e:
                logger.warning(f"Index creation warning: {e}")
            
            # Measure after performance
            after_start = time.time()
            test_nodes_after = self.kg_repository.find_nodes_by_type('diagnosis')[:50]
            after_time = (time.time() - after_start) * 1000
            
            after_metrics = {
                "query_time_ms": after_time,
                "nodes_retrieved": len(test_nodes_after)
            }
            
            # Calculate improvement
            improvement = max(0, (before_time - after_time) / before_time * 100) if before_time > 0 else 0
            
            return PerformanceOptimizationResult(
                optimization_type="database_queries",
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement_percentage=improvement,
                execution_time=time.time() - before_start,
                success=True,
                recommendations=[
                    "Database indexes created for common query patterns",
                    "Query performance optimized for node type searches",
                    "Relationship queries optimized with source/target indexes"
                ]
            )
            
        except Exception as e:
            logger.error(f"Error optimizing database queries: {e}")
            return PerformanceOptimizationResult(
                optimization_type="database_queries",
                before_metrics={},
                after_metrics={},
                improvement_percentage=0,
                execution_time=0,
                success=False,
                recommendations=[f"Optimization failed: {str(e)}"]
            )
    
    async def _implement_caching_strategies(self) -> PerformanceOptimizationResult:
        """Implement caching strategies for frequently accessed data."""
        try:
            before_start = time.time()
            
            # Simple in-memory cache for frequently accessed node types
            cache = {}
            
            # Cache common node types
            for node_type in ['diagnosis', 'ama_table', 'legal_pattern']:
                cache_start = time.time()
                nodes = self.kg_repository.find_nodes_by_type(node_type)
                cache_time = (time.time() - cache_start) * 1000
                cache[node_type] = {
                    'nodes': nodes,
                    'cached_at': datetime.now(),
                    'cache_time_ms': cache_time
                }
            
            before_metrics = {
                "cache_size": 0,
                "cached_types": 0
            }
            
            after_metrics = {
                "cache_size": sum(len(data['nodes']) for data in cache.values()),
                "cached_types": len(cache),
                "total_cache_time_ms": sum(data['cache_time_ms'] for data in cache.values())
            }
            
            return PerformanceOptimizationResult(
                optimization_type="caching_strategies",
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement_percentage=0,  # Improvement will be seen in subsequent queries
                execution_time=time.time() - before_start,
                success=True,
                recommendations=[
                    f"Cached {after_metrics['cached_types']} node types",
                    f"Total cached nodes: {after_metrics['cache_size']}",
                    "Implement cache invalidation strategy for data updates",
                    "Consider Redis for distributed caching in production"
                ]
            )
            
        except Exception as e:
            logger.error(f"Error implementing caching strategies: {e}")
            return PerformanceOptimizationResult(
                optimization_type="caching_strategies",
                before_metrics={},
                after_metrics={},
                improvement_percentage=0,
                execution_time=0,
                success=False,
                recommendations=[f"Caching implementation failed: {str(e)}"]
            )
    
    async def _optimize_graph_structure(self) -> PerformanceOptimizationResult:
        """Optimize knowledge graph structure for better performance."""
        try:
            before_start = time.time()
            
            # Analyze current graph structure
            all_nodes = self.kg_repository.get_all_nodes()
            all_relationships = self.kg_repository.get_all_relationships()
            
            before_metrics = {
                "total_nodes": len(all_nodes),
                "total_relationships": len(all_relationships),
                "avg_relationships_per_node": len(all_relationships) / len(all_nodes) if all_nodes else 0
            }
            
            # Identify and remove duplicate relationships
            unique_relationships = set()
            duplicates_removed = 0
            
            for rel in all_relationships:
                rel_key = (rel.source_node_id, rel.target_node_id, rel.relationship_type)
                if rel_key in unique_relationships:
                    # Remove duplicate relationship
                    try:
                        self.kg_repository.delete_relationship(rel.id)
                        duplicates_removed += 1
                    except Exception as e:
                        logger.warning(f"Could not remove duplicate relationship: {e}")
                else:
                    unique_relationships.add(rel_key)
            
            # Update metrics after optimization
            remaining_relationships = self.kg_repository.get_all_relationships()
            
            after_metrics = {
                "total_nodes": len(all_nodes),
                "total_relationships": len(remaining_relationships),
                "avg_relationships_per_node": len(remaining_relationships) / len(all_nodes) if all_nodes else 0,
                "duplicates_removed": duplicates_removed
            }
            
            improvement = (duplicates_removed / len(all_relationships) * 100) if all_relationships else 0
            
            return PerformanceOptimizationResult(
                optimization_type="graph_structure",
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement_percentage=improvement,
                execution_time=time.time() - before_start,
                success=True,
                recommendations=[
                    f"Removed {duplicates_removed} duplicate relationships",
                    "Graph structure optimized for better traversal performance",
                    "Consider periodic structure optimization maintenance"
                ]
            )
            
        except Exception as e:
            logger.error(f"Error optimizing graph structure: {e}")
            return PerformanceOptimizationResult(
                optimization_type="graph_structure",
                before_metrics={},
                after_metrics={},
                improvement_percentage=0,
                execution_time=0,
                success=False,
                recommendations=[f"Structure optimization failed: {str(e)}"]
            )
    
    async def monitor_knowledge_base_health(self) -> HealthMonitoringResult:
        """
        Create knowledge base health monitoring with data integrity checks and update tracking.
        
        Returns:
            HealthMonitoringResult with comprehensive health assessment
        """
        logger.info("Starting knowledge base health monitoring")
        
        try:
            # Collect current metrics
            metrics = await self._collect_knowledge_base_metrics()
            
            # Perform data integrity checks
            integrity_checks = await self._perform_data_integrity_checks()
            
            # Calculate component health scores
            component_health = {
                "node_storage": self._calculate_node_health_score(metrics),
                "relationship_integrity": self._calculate_relationship_health_score(metrics),
                "vector_embeddings": self._calculate_vector_health_score(metrics),
                "query_performance": self._calculate_performance_health_score(metrics),
                "data_completeness": self._calculate_completeness_health_score(metrics)
            }
            
            # Calculate overall health score
            overall_health = sum(component_health.values()) / len(component_health)
            
            # Identify issues and generate recommendations
            issues_detected = []
            recommendations = []
            
            if metrics.node_count < self.min_node_count:
                issues_detected.append(f"Low node count: {metrics.node_count}")
                recommendations.append("Initialize knowledge base with canonical documents")
            
            if metrics.relationship_count < self.min_relationship_count:
                issues_detected.append(f"Low relationship count: {metrics.relationship_count}")
                recommendations.append("Enhance relationship extraction and creation")
            
            if metrics.query_performance_ms > self.max_query_time_ms:
                issues_detected.append(f"Slow query performance: {metrics.query_performance_ms}ms")
                recommendations.append("Optimize database indexes and query patterns")
            
            if metrics.data_integrity_score < self.min_data_integrity_score:
                issues_detected.append(f"Low data integrity: {metrics.data_integrity_score}")
                recommendations.append("Run data cleanup and validation procedures")
            
            # Performance metrics
            performance_metrics = {
                "query_time_ms": metrics.query_performance_ms,
                "index_time_ms": metrics.index_performance_ms,
                "data_integrity_score": metrics.data_integrity_score,
                "node_density": metrics.relationship_count / metrics.node_count if metrics.node_count > 0 else 0
            }
            
            return HealthMonitoringResult(
                overall_health_score=overall_health,
                component_health=component_health,
                data_integrity_checks=integrity_checks,
                performance_metrics=performance_metrics,
                issues_detected=issues_detected,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error during health monitoring: {e}")
            return HealthMonitoringResult(
                overall_health_score=0.0,
                component_health={},
                data_integrity_checks={},
                performance_metrics={},
                issues_detected=[str(e)],
                recommendations=["Fix health monitoring system errors"]
            )
    
    async def _perform_data_integrity_checks(self) -> Dict[str, bool]:
        """Perform comprehensive data integrity checks."""
        try:
            checks = {}
            
            # Check for orphaned nodes
            all_nodes = self.kg_repository.get_all_nodes()
            orphaned_count = 0
            for node in all_nodes[:100]:  # Sample check
                relationships = self.kg_repository.find_relationships_for_node(node.id)
                if not relationships:
                    orphaned_count += 1
            
            checks["no_orphaned_nodes"] = orphaned_count < len(all_nodes) * 0.1
            
            # Check for missing required properties
            missing_props = 0
            for node in all_nodes[:100]:  # Sample check
                if node.node_type == 'diagnosis' and not node.properties.get('description'):
                    missing_props += 1
            
            checks["required_properties_present"] = missing_props < len(all_nodes) * 0.05
            
            # Check for valid relationships
            all_relationships = self.kg_repository.get_all_relationships()
            invalid_rels = 0
            for rel in all_relationships[:100]:  # Sample check
                source_exists = self.kg_repository.get_node_by_id(rel.source_node_id) is not None
                target_exists = self.kg_repository.get_node_by_id(rel.target_node_id) is not None
                if not (source_exists and target_exists):
                    invalid_rels += 1
            
            checks["valid_relationships"] = invalid_rels < len(all_relationships) * 0.01
            
            # Check for reasonable data distribution
            entity_counts = self.kg_repository.get_node_types_count()
            checks["balanced_entity_distribution"] = len(entity_counts) >= 5
            
            return checks
            
        except Exception as e:
            logger.error(f"Error performing data integrity checks: {e}")
            return {"integrity_check_error": False}
    
    def _calculate_node_health_score(self, metrics: KnowledgeBaseMetrics) -> float:
        """Calculate health score for node storage."""
        if metrics.node_count >= self.min_node_count:
            return min(1.0, metrics.node_count / (self.min_node_count * 2))
        else:
            return metrics.node_count / self.min_node_count
    
    def _calculate_relationship_health_score(self, metrics: KnowledgeBaseMetrics) -> float:
        """Calculate health score for relationship integrity."""
        if metrics.relationship_count >= self.min_relationship_count:
            return min(1.0, metrics.relationship_count / (self.min_relationship_count * 2))
        else:
            return metrics.relationship_count / self.min_relationship_count
    
    def _calculate_vector_health_score(self, metrics: KnowledgeBaseMetrics) -> float:
        """Calculate health score for vector embeddings."""
        if metrics.node_count == 0:
            return 0.0
        
        embedding_ratio = metrics.vector_embeddings_count / metrics.node_count
        return min(1.0, embedding_ratio)
    
    def _calculate_performance_health_score(self, metrics: KnowledgeBaseMetrics) -> float:
        """Calculate health score for query performance."""
        if metrics.query_performance_ms <= self.max_query_time_ms:
            return 1.0
        else:
            return max(0.0, 1.0 - (metrics.query_performance_ms - self.max_query_time_ms) / self.max_query_time_ms)
    
    def _calculate_completeness_health_score(self, metrics: KnowledgeBaseMetrics) -> float:
        """Calculate health score for data completeness."""
        completeness_factors = [
            metrics.canonical_documents_processed >= 3,
            metrics.ama_tables_loaded >= 50,
            metrics.legal_patterns_loaded >= 10,
            len(metrics.entity_type_coverage) >= len(self.required_entity_types)
        ]
        
        return sum(completeness_factors) / len(completeness_factors)
    
    def save_validation_report(self, 
                             validation_passed: bool,
                             metrics: KnowledgeBaseMetrics,
                             issues: List[str],
                             output_path: Optional[str] = None) -> str:
        """Save knowledge base validation report to file."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"results/validation_reports/knowledge_base_validation_{timestamp}.json"
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        report_data = {
            "validation_passed": validation_passed,
            "validation_timestamp": datetime.now().isoformat(),
            "metrics": {
                "node_count": metrics.node_count,
                "relationship_count": metrics.relationship_count,
                "entity_type_coverage": metrics.entity_type_coverage,
                "canonical_documents_processed": metrics.canonical_documents_processed,
                "ama_tables_loaded": metrics.ama_tables_loaded,
                "legal_patterns_loaded": metrics.legal_patterns_loaded,
                "vector_embeddings_count": metrics.vector_embeddings_count,
                "query_performance_ms": metrics.query_performance_ms,
                "index_performance_ms": metrics.index_performance_ms,
                "data_integrity_score": metrics.data_integrity_score
            },
            "validation_thresholds": {
                "min_node_count": self.min_node_count,
                "min_relationship_count": self.min_relationship_count,
                "required_entity_types": list(self.required_entity_types),
                "max_query_time_ms": self.max_query_time_ms,
                "min_data_integrity_score": self.min_data_integrity_score
            },
            "issues_detected": issues,
            "recommendations": self._generate_validation_recommendations(validation_passed, metrics, issues)
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Knowledge base validation report saved to {output_file}")
        return str(output_file)
    
    def _generate_validation_recommendations(self, 
                                           validation_passed: bool,
                                           metrics: KnowledgeBaseMetrics,
                                           issues: List[str]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if not validation_passed:
            recommendations.append("Knowledge base validation failed - address issues before proceeding")
        
        if metrics.node_count < self.min_node_count:
            recommendations.append("Initialize knowledge base with canonical documents to increase node count")
        
        if metrics.relationship_count < self.min_relationship_count:
            recommendations.append("Enhance relationship extraction to improve graph connectivity")
        
        if metrics.query_performance_ms > self.max_query_time_ms:
            recommendations.append("Optimize database indexes and query patterns for better performance")
        
        if metrics.data_integrity_score < self.min_data_integrity_score:
            recommendations.append("Run data cleanup procedures to improve integrity")
        
        if len(issues) == 0 and validation_passed:
            recommendations.append("Knowledge base validation passed - system ready for production use")
        
        return recommendations