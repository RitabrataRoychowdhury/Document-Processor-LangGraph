"""
Performance monitoring service for document processing and system metrics.

This module tracks processing times, system performance, and ensures
performance targets are met (e.g., 50-page PDF processing within 30 seconds).
"""

import time
import logging
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict, deque
import threading
import json

logger = logging.getLogger(__name__)


@dataclass
class ProcessingMetrics:
    """Metrics for document processing performance."""
    document_path: str
    file_size_mb: float
    page_count: Optional[int]
    processing_start_time: float
    processing_end_time: Optional[float] = None
    total_processing_time: Optional[float] = None
    stages: Dict[str, float] = field(default_factory=dict)
    success: bool = False
    error_message: Optional[str] = None
    
    def mark_stage_complete(self, stage_name: str, duration: float):
        """Mark a processing stage as complete with its duration."""
        self.stages[stage_name] = duration
    
    def complete_processing(self, success: bool = True, error_message: Optional[str] = None):
        """Mark processing as complete."""
        self.processing_end_time = time.time()
        self.total_processing_time = self.processing_end_time - self.processing_start_time
        self.success = success
        self.error_message = error_message


@dataclass
class PerformanceTarget:
    """Performance target definition."""
    name: str
    description: str
    target_value: float
    unit: str
    comparison: str  # "less_than", "greater_than", "equal_to"


class PerformanceMonitor:
    """Monitor and track system performance metrics."""
    
    def __init__(self, config_max_processing_time: float = 30.0):
        """Initialize performance monitor."""
        self.max_processing_time = config_max_processing_time
        self.active_processing: Dict[str, ProcessingMetrics] = {}
        self.completed_processing: deque = deque(maxlen=1000)  # Keep last 1000 records
        self.performance_targets = self._initialize_targets()
        self._lock = threading.Lock()
        
        # Performance statistics
        self.stats = {
            "total_documents_processed": 0,
            "successful_processing": 0,
            "failed_processing": 0,
            "average_processing_time": 0.0,
            "target_violations": 0
        }
    
    def _initialize_targets(self) -> List[PerformanceTarget]:
        """Initialize performance targets."""
        return [
            PerformanceTarget(
                name="pdf_processing_time",
                description="50-page PDF should process within 30 seconds",
                target_value=30.0,
                unit="seconds",
                comparison="less_than"
            ),
            PerformanceTarget(
                name="text_extraction_time",
                description="Text extraction should complete within 10 seconds",
                target_value=10.0,
                unit="seconds",
                comparison="less_than"
            ),
            PerformanceTarget(
                name="embedding_generation_time",
                description="Embedding generation should complete within 15 seconds",
                target_value=15.0,
                unit="seconds",
                comparison="less_than"
            ),
            PerformanceTarget(
                name="qme_field_extraction_time",
                description="QME field extraction should complete within 10 seconds",
                target_value=10.0,
                unit="seconds",
                comparison="less_than"
            ),
            PerformanceTarget(
                name="qme_template_generation_time",
                description="QME template generation should complete within 30 seconds",
                target_value=30.0,
                unit="seconds",
                comparison="less_than"
            ),
            PerformanceTarget(
                name="qme_end_to_end_workflow_time",
                description="Complete QME workflow should finish within 60 seconds",
                target_value=60.0,
                unit="seconds",
                comparison="less_than"
            ),
            PerformanceTarget(
                name="qme_field_extraction_accuracy",
                description="QME field extraction accuracy should be above 90%",
                target_value=90.0,
                unit="percent",
                comparison="greater_than"
            ),
            PerformanceTarget(
                name="kg_population_time",
                description="Knowledge graph population should complete within 5 seconds",
                target_value=5.0,
                unit="seconds",
                comparison="less_than"
            )
        ]
    
    def start_processing(self, document_path: str, file_size_mb: float, page_count: Optional[int] = None) -> str:
        """Start monitoring document processing."""
        processing_id = f"{document_path}_{int(time.time())}"
        
        metrics = ProcessingMetrics(
            document_path=document_path,
            file_size_mb=file_size_mb,
            page_count=page_count,
            processing_start_time=time.time()
        )
        
        with self._lock:
            self.active_processing[processing_id] = metrics
        
        logger.info(f"Started monitoring processing for: {document_path} (ID: {processing_id})")
        return processing_id
    
    def mark_stage_complete(self, processing_id: str, stage_name: str, duration: float):
        """Mark a processing stage as complete."""
        with self._lock:
            if processing_id in self.active_processing:
                self.active_processing[processing_id].mark_stage_complete(stage_name, duration)
                logger.debug(f"Stage '{stage_name}' completed in {duration:.2f}s for {processing_id}")
    
    def complete_processing(self, processing_id: str, success: bool = True, error_message: Optional[str] = None):
        """Complete processing monitoring."""
        with self._lock:
            if processing_id not in self.active_processing:
                logger.warning(f"Processing ID not found: {processing_id}")
                return
            
            metrics = self.active_processing[processing_id]
            metrics.complete_processing(success, error_message)
            
            # Move to completed processing
            self.completed_processing.append(metrics)
            del self.active_processing[processing_id]
            
            # Update statistics
            self._update_statistics(metrics)
            
            # Check performance targets
            self._check_performance_targets(metrics)
            
            logger.info(f"Completed monitoring for {metrics.document_path}: "
                       f"{metrics.total_processing_time:.2f}s (Success: {success})")
    
    def _update_statistics(self, metrics: ProcessingMetrics):
        """Update performance statistics."""
        self.stats["total_documents_processed"] += 1
        
        if metrics.success:
            self.stats["successful_processing"] += 1
        else:
            self.stats["failed_processing"] += 1
        
        # Update average processing time
        if metrics.total_processing_time:
            total_time = sum(m.total_processing_time for m in self.completed_processing 
                           if m.total_processing_time is not None)
            count = len([m for m in self.completed_processing if m.total_processing_time is not None])
            self.stats["average_processing_time"] = total_time / count if count > 0 else 0.0
    
    def _check_performance_targets(self, metrics: ProcessingMetrics):
        """Check if processing meets performance targets."""
        violations = []
        
        # Check overall processing time target
        if metrics.total_processing_time and metrics.page_count:
            # Estimate if this would meet the 50-page/30-second target
            estimated_time_for_50_pages = (metrics.total_processing_time / metrics.page_count) * 50
            
            if estimated_time_for_50_pages > self.max_processing_time:
                violations.append(f"Estimated 50-page processing time: {estimated_time_for_50_pages:.2f}s "
                                f"exceeds target of {self.max_processing_time}s")
                self.stats["target_violations"] += 1
        
        # Check individual stage targets
        for target in self.performance_targets:
            stage_time = metrics.stages.get(target.name.replace("_time", ""))
            if stage_time and target.comparison == "less_than" and stage_time > target.target_value:
                violations.append(f"Stage '{target.name}' took {stage_time:.2f}s, "
                                f"exceeds target of {target.target_value}s")
        
        if violations:
            logger.warning(f"Performance target violations for {metrics.document_path}: {violations}")
    
    def get_current_statistics(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        with self._lock:
            recent_processing = list(self.completed_processing)[-10:]  # Last 10 documents
            
            return {
                "overall_stats": self.stats.copy(),
                "active_processing_count": len(self.active_processing),
                "recent_processing": [
                    {
                        "document": Path(m.document_path).name,
                        "processing_time": m.total_processing_time,
                        "file_size_mb": m.file_size_mb,
                        "page_count": m.page_count,
                        "success": m.success,
                        "stages": m.stages
                    }
                    for m in recent_processing
                ],
                "performance_targets": [
                    {
                        "name": target.name,
                        "description": target.description,
                        "target_value": target.target_value,
                        "unit": target.unit
                    }
                    for target in self.performance_targets
                ]
            }
    
    def get_processing_report(self, document_path: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed processing report."""
        with self._lock:
            if document_path:
                # Report for specific document
                matching_metrics = [m for m in self.completed_processing 
                                  if m.document_path == document_path]
                if not matching_metrics:
                    return {"error": f"No processing data found for {document_path}"}
                
                metrics = matching_metrics[-1]  # Most recent
                return {
                    "document_path": metrics.document_path,
                    "file_size_mb": metrics.file_size_mb,
                    "page_count": metrics.page_count,
                    "total_processing_time": metrics.total_processing_time,
                    "success": metrics.success,
                    "error_message": metrics.error_message,
                    "stages": metrics.stages,
                    "meets_targets": self._evaluate_targets(metrics)
                }
            else:
                # Overall report
                successful_docs = [m for m in self.completed_processing if m.success]
                failed_docs = [m for m in self.completed_processing if not m.success]
                
                return {
                    "summary": {
                        "total_processed": len(self.completed_processing),
                        "successful": len(successful_docs),
                        "failed": len(failed_docs),
                        "success_rate": len(successful_docs) / len(self.completed_processing) * 100 
                                      if self.completed_processing else 0
                    },
                    "performance": {
                        "average_processing_time": self.stats["average_processing_time"],
                        "target_violations": self.stats["target_violations"],
                        "fastest_processing": min((m.total_processing_time for m in successful_docs 
                                                 if m.total_processing_time), default=0),
                        "slowest_processing": max((m.total_processing_time for m in successful_docs 
                                                 if m.total_processing_time), default=0)
                    }
                }
    
    def _evaluate_targets(self, metrics: ProcessingMetrics) -> Dict[str, bool]:
        """Evaluate if metrics meet performance targets."""
        results = {}
        
        # Overall processing time target
        if metrics.total_processing_time and metrics.page_count:
            estimated_50_page_time = (metrics.total_processing_time / metrics.page_count) * 50
            results["50_page_target"] = estimated_50_page_time <= self.max_processing_time
        
        # Stage-specific targets
        for target in self.performance_targets:
            stage_name = target.name.replace("_time", "")
            stage_time = metrics.stages.get(stage_name)
            
            if stage_time:
                if target.comparison == "less_than":
                    results[target.name] = stage_time <= target.target_value
                elif target.comparison == "greater_than":
                    results[target.name] = stage_time >= target.target_value
                else:
                    results[target.name] = stage_time == target.target_value
        
        return results
    
    def export_metrics(self, file_path: str):
        """Export performance metrics to JSON file."""
        try:
            with self._lock:
                data = {
                    "statistics": self.stats,
                    "completed_processing": [
                        {
                            "document_path": m.document_path,
                            "file_size_mb": m.file_size_mb,
                            "page_count": m.page_count,
                            "processing_start_time": m.processing_start_time,
                            "processing_end_time": m.processing_end_time,
                            "total_processing_time": m.total_processing_time,
                            "stages": m.stages,
                            "success": m.success,
                            "error_message": m.error_message
                        }
                        for m in self.completed_processing
                    ],
                    "performance_targets": [
                        {
                            "name": target.name,
                            "description": target.description,
                            "target_value": target.target_value,
                            "unit": target.unit,
                            "comparison": target.comparison
                        }
                        for target in self.performance_targets
                    ]
                }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Performance metrics exported to: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}", exc_info=True)


# Global performance monitor instance
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def monitor_processing(func):
    """Decorator to monitor processing performance."""
    def wrapper(*args, **kwargs):
        monitor = get_performance_monitor()
        
        # Try to extract document path from arguments
        doc_path = None
        file_size = 0.0
        
        if args and hasattr(args[0], '__dict__'):
            # Look for document path in first argument
            if hasattr(args[0], 'document_path'):
                doc_path = args[0].document_path
            elif hasattr(args[0], 'file_path'):
                doc_path = args[0].file_path
        
        if doc_path and Path(doc_path).exists():
            file_size = Path(doc_path).stat().st_size / (1024 * 1024)  # MB
        
        processing_id = monitor.start_processing(
            doc_path or f"unknown_{int(time.time())}", 
            file_size
        )
        
        try:
            result = func(*args, **kwargs)
            monitor.complete_processing(processing_id, success=True)
            return result
        except Exception as e:
            monitor.complete_processing(processing_id, success=False, error_message=str(e))
            raise
    
    return wrapper