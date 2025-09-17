"""
Advanced Performance Monitoring System for Production-Ready QME System.

This module provides comprehensive performance monitoring including:
- Processing times and success rates tracking
- Error rates and resource utilization monitoring
- Business metrics: document throughput, template generation success rates
- User activity patterns and system performance analytics
- Configurable alerting with thresholds and notification channels
- Performance trend analysis and capacity planning metrics

Designed for production monitoring and performance optimization.
"""

import time
import logging
import asyncio
import threading
import json
import statistics
import psutil
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
from collections import defaultdict, deque
from enum import Enum
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics being tracked"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Performance alert definition"""
    name: str
    metric_name: str
    threshold: float
    comparison: str  # "greater_than", "less_than", "equal_to"
    severity: AlertSeverity
    message_template: str
    enabled: bool = True
    cooldown_minutes: int = 15
    last_triggered: Optional[float] = None


@dataclass
class BusinessMetric:
    """Business-level performance metric"""
    name: str
    value: float
    unit: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceTrend:
    """Performance trend analysis"""
    metric_name: str
    current_value: float
    previous_value: float
    change_percent: float
    trend_direction: str  # "improving", "degrading", "stable"
    period_hours: int


@dataclass
class ProcessingMetrics:
    """Enhanced metrics for document processing performance."""
    processing_id: str
    document_path: str
    file_size_mb: float
    page_count: Optional[int]
    processing_start_time: float
    processing_end_time: Optional[float] = None
    total_processing_time: Optional[float] = None
    stages: Dict[str, float] = field(default_factory=dict)
    success: bool = False
    error_message: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    pipeline_type: Optional[str] = None  # "extraction", "generation", "full_workflow"
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    resource_usage: Dict[str, float] = field(default_factory=dict)
    
    def mark_stage_complete(self, stage_name: str, duration: float, metadata: Optional[Dict] = None):
        """Mark a processing stage as complete with its duration and metadata."""
        self.stages[stage_name] = duration
        if metadata:
            # Store additional stage metadata
            stage_key = f"{stage_name}_metadata"
            if not hasattr(self, 'stage_metadata'):
                self.stage_metadata = {}
            self.stage_metadata[stage_key] = metadata
    
    def complete_processing(self, success: bool = True, error_message: Optional[str] = None):
        """Mark processing as complete with resource usage capture."""
        self.processing_end_time = time.time()
        self.total_processing_time = self.processing_end_time - self.processing_start_time
        self.success = success
        self.error_message = error_message
        
        # Capture final resource usage
        try:
            process = psutil.Process()
            self.resource_usage = {
                "peak_memory_mb": process.memory_info().rss / (1024 * 1024),
                "cpu_percent": process.cpu_percent(),
                "io_read_bytes": process.io_counters().read_bytes if hasattr(process.io_counters(), 'read_bytes') else 0,
                "io_write_bytes": process.io_counters().write_bytes if hasattr(process.io_counters(), 'write_bytes') else 0
            }
        except:
            pass  # Resource usage capture is optional


@dataclass
class PerformanceTarget:
    """Performance target definition."""
    name: str
    description: str
    target_value: float
    unit: str
    comparison: str  # "less_than", "greater_than", "equal_to"


class AdvancedPerformanceMonitor:
    """
    Advanced performance monitoring system for production QME system.
    
    Provides comprehensive metrics collection, business analytics, alerting,
    and performance trend analysis for production monitoring and optimization.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize advanced performance monitor."""
        self.config = config or {}
        self.max_processing_time = self.config.get('max_processing_time', 30.0)
        self.max_history_size = self.config.get('max_history_size', 10000)
        
        # Core tracking data structures
        self.active_processing: Dict[str, ProcessingMetrics] = {}
        self.completed_processing: deque = deque(maxlen=self.max_history_size)
        self.business_metrics: deque = deque(maxlen=self.max_history_size)
        self.system_metrics: deque = deque(maxlen=1000)  # System resource snapshots
        
        # Performance targets and alerts
        self.performance_targets = self._initialize_targets()
        self.alerts = self._initialize_alerts()
        self.alert_handlers: List[Callable] = []
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Enhanced statistics
        self.stats = {
            # Processing statistics
            "total_documents_processed": 0,
            "successful_processing": 0,
            "failed_processing": 0,
            "average_processing_time": 0.0,
            "target_violations": 0,
            
            # Business metrics
            "documents_per_hour": 0.0,
            "templates_generated_per_hour": 0.0,
            "average_confidence_score": 0.0,
            "user_sessions_active": 0,
            
            # System metrics
            "average_memory_usage_mb": 0.0,
            "average_cpu_usage_percent": 0.0,
            "error_rate_percent": 0.0,
            "uptime_hours": 0.0
        }
        
        # Metric collectors
        self.metric_collectors: Dict[str, Callable] = {
            "system_resources": self._collect_system_metrics,
            "business_metrics": self._collect_business_metrics,
            "error_rates": self._collect_error_metrics
        }
        
        # Start background monitoring
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._background_monitoring, daemon=True)
        self.monitoring_thread.start()
        
        # Performance trend tracking
        self.trend_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=24))  # 24 hours of hourly data
        
        logger.info("Advanced Performance Monitor initialized")
    
    def _initialize_targets(self) -> List[PerformanceTarget]:
        """Initialize comprehensive performance targets."""
        return [
            # Processing time targets
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
            
            # Quality and accuracy targets
            PerformanceTarget(
                name="qme_field_extraction_accuracy",
                description="QME field extraction accuracy should be above 90%",
                target_value=90.0,
                unit="percent",
                comparison="greater_than"
            ),
            PerformanceTarget(
                name="template_generation_success_rate",
                description="Template generation success rate should be above 95%",
                target_value=95.0,
                unit="percent",
                comparison="greater_than"
            ),
            PerformanceTarget(
                name="average_confidence_score",
                description="Average confidence score should be above 80%",
                target_value=80.0,
                unit="percent",
                comparison="greater_than"
            ),
            
            # Throughput targets
            PerformanceTarget(
                name="documents_per_hour",
                description="System should process at least 10 documents per hour",
                target_value=10.0,
                unit="documents/hour",
                comparison="greater_than"
            ),
            PerformanceTarget(
                name="concurrent_users",
                description="System should support at least 5 concurrent users",
                target_value=5.0,
                unit="users",
                comparison="greater_than"
            ),
            
            # System resource targets
            PerformanceTarget(
                name="memory_usage",
                description="Memory usage should stay below 80%",
                target_value=80.0,
                unit="percent",
                comparison="less_than"
            ),
            PerformanceTarget(
                name="cpu_usage",
                description="CPU usage should stay below 70%",
                target_value=70.0,
                unit="percent",
                comparison="less_than"
            ),
            PerformanceTarget(
                name="error_rate",
                description="Error rate should stay below 5%",
                target_value=5.0,
                unit="percent",
                comparison="less_than"
            )
        ]
    
    def _initialize_alerts(self) -> List[Alert]:
        """Initialize performance alerts with configurable thresholds."""
        return [
            Alert(
                name="high_processing_time",
                metric_name="average_processing_time",
                threshold=45.0,
                comparison="greater_than",
                severity=AlertSeverity.WARNING,
                message_template="Average processing time ({value:.1f}s) exceeds threshold ({threshold}s)"
            ),
            Alert(
                name="critical_processing_time",
                metric_name="average_processing_time",
                threshold=60.0,
                comparison="greater_than",
                severity=AlertSeverity.CRITICAL,
                message_template="Critical: Average processing time ({value:.1f}s) critically high"
            ),
            Alert(
                name="high_error_rate",
                metric_name="error_rate_percent",
                threshold=10.0,
                comparison="greater_than",
                severity=AlertSeverity.WARNING,
                message_template="Error rate ({value:.1f}%) exceeds acceptable threshold"
            ),
            Alert(
                name="low_success_rate",
                metric_name="template_generation_success_rate",
                threshold=90.0,
                comparison="less_than",
                severity=AlertSeverity.WARNING,
                message_template="Template generation success rate ({value:.1f}%) below target"
            ),
            Alert(
                name="high_memory_usage",
                metric_name="average_memory_usage_mb",
                threshold=1000.0,  # 1GB
                comparison="greater_than",
                severity=AlertSeverity.WARNING,
                message_template="High memory usage detected: {value:.1f}MB"
            ),
            Alert(
                name="low_throughput",
                metric_name="documents_per_hour",
                threshold=5.0,
                comparison="less_than",
                severity=AlertSeverity.WARNING,
                message_template="Document processing throughput low: {value:.1f} docs/hour"
            )
        ]
    
    def start_processing(
        self, 
        document_path: str, 
        file_size_mb: float, 
        page_count: Optional[int] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        pipeline_type: Optional[str] = None
    ) -> str:
        """Start monitoring document processing with enhanced tracking."""
        processing_id = f"{Path(document_path).stem}_{int(time.time() * 1000)}"
        
        metrics = ProcessingMetrics(
            processing_id=processing_id,
            document_path=document_path,
            file_size_mb=file_size_mb,
            page_count=page_count,
            processing_start_time=time.time(),
            user_id=user_id,
            session_id=session_id,
            pipeline_type=pipeline_type or "unknown"
        )
        
        with self._lock:
            self.active_processing[processing_id] = metrics
        
        logger.info(f"Started monitoring processing: {document_path} (ID: {processing_id}, Pipeline: {pipeline_type})")
        
        # Record business metric
        self._record_business_metric("processing_started", 1, "count", {
            "pipeline_type": pipeline_type,
            "file_size_mb": file_size_mb,
            "user_id": user_id
        })
        
        return processing_id
    
    def mark_stage_complete(
        self, 
        processing_id: str, 
        stage_name: str, 
        duration: float,
        metadata: Optional[Dict] = None
    ):
        """Mark a processing stage as complete with enhanced metadata."""
        with self._lock:
            if processing_id in self.active_processing:
                self.active_processing[processing_id].mark_stage_complete(stage_name, duration, metadata)
                logger.debug(f"Stage '{stage_name}' completed in {duration:.2f}s for {processing_id}")
                
                # Record stage performance metric
                self._record_business_metric(f"stage_{stage_name}_duration", duration, "seconds", {
                    "processing_id": processing_id,
                    "stage": stage_name
                })
                
                # Check stage-specific performance targets
                self._check_stage_performance(stage_name, duration)
            else:
                logger.warning(f"Processing ID not found for stage completion: {processing_id}")
    
    def complete_processing(
        self, 
        processing_id: str, 
        success: bool = True, 
        error_message: Optional[str] = None,
        confidence_scores: Optional[Dict[str, float]] = None,
        quality_metrics: Optional[Dict[str, float]] = None
    ):
        """Complete processing monitoring with enhanced metrics."""
        with self._lock:
            if processing_id not in self.active_processing:
                logger.warning(f"Processing ID not found: {processing_id}")
                return
            
            metrics = self.active_processing[processing_id]
            
            # Add additional metrics
            if confidence_scores:
                metrics.confidence_scores = confidence_scores
            if quality_metrics:
                metrics.quality_metrics = quality_metrics
            
            metrics.complete_processing(success, error_message)
            
            # Move to completed processing
            self.completed_processing.append(metrics)
            del self.active_processing[processing_id]
            
            # Update statistics
            self._update_processing_statistics(metrics)
            
            # Check performance targets
            self._check_performance_targets(metrics)
            
            # Record business metrics
            self._record_processing_completion(metrics)
            
            logger.info(f"Completed monitoring for {metrics.document_path}: "
                       f"{metrics.total_processing_time:.2f}s (Success: {success})")
            
            return metrics
    
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


def get_performance_monitor() -> AdvancedPerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = AdvancedPerformanceMonitor()
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

    def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect current system resource metrics."""
        try:
            # System-wide metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Process-specific metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            
            # Disk usage for data directory
            try:
                disk_usage = psutil.disk_usage("data")
                disk_percent = (disk_usage.used / disk_usage.total) * 100
            except:
                disk_percent = 0.0
            
            return {
                "memory_usage_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "cpu_usage_percent": cpu_percent,
                "process_memory_mb": process_memory.rss / (1024**2),
                "disk_usage_percent": disk_percent,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
            return {"timestamp": time.time()}
    
    def _collect_business_metrics(self) -> Dict[str, float]:
        """Collect business-level performance metrics."""
        with self._lock:
            current_time = time.time()
            hour_ago = current_time - 3600  # 1 hour ago
            
            # Get recent processing data
            recent_processing = [
                p for p in self.completed_processing 
                if p.processing_end_time and p.processing_end_time > hour_ago
            ]
            
            if not recent_processing:
                return {
                    "documents_per_hour": 0.0,
                    "templates_generated_per_hour": 0.0,
                    "average_confidence_score": 0.0,
                    "success_rate_percent": 0.0,
                    "timestamp": current_time
                }
            
            # Calculate business metrics
            successful_processing = [p for p in recent_processing if p.success]
            
            # Documents per hour
            documents_per_hour = len(recent_processing)
            
            # Templates generated per hour (successful processing)
            templates_per_hour = len(successful_processing)
            
            # Average confidence score
            confidence_scores = []
            for p in successful_processing:
                if p.confidence_scores:
                    avg_confidence = sum(p.confidence_scores.values()) / len(p.confidence_scores)
                    confidence_scores.append(avg_confidence)
            
            avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.0
            
            # Success rate
            success_rate = (len(successful_processing) / len(recent_processing)) * 100
            
            return {
                "documents_per_hour": documents_per_hour,
                "templates_generated_per_hour": templates_per_hour,
                "average_confidence_score": avg_confidence,
                "success_rate_percent": success_rate,
                "active_processing_count": len(self.active_processing),
                "timestamp": current_time
            }
    
    def _collect_error_metrics(self) -> Dict[str, float]:
        """Collect error rate and failure metrics."""
        with self._lock:
            current_time = time.time()
            hour_ago = current_time - 3600
            
            recent_processing = [
                p for p in self.completed_processing 
                if p.processing_end_time and p.processing_end_time > hour_ago
            ]
            
            if not recent_processing:
                return {"error_rate_percent": 0.0, "timestamp": current_time}
            
            failed_processing = [p for p in recent_processing if not p.success]
            error_rate = (len(failed_processing) / len(recent_processing)) * 100
            
            # Categorize errors
            error_categories = defaultdict(int)
            for p in failed_processing:
                if p.error_message:
                    # Simple error categorization
                    if "timeout" in p.error_message.lower():
                        error_categories["timeout"] += 1
                    elif "memory" in p.error_message.lower():
                        error_categories["memory"] += 1
                    elif "api" in p.error_message.lower():
                        error_categories["api"] += 1
                    else:
                        error_categories["other"] += 1
            
            return {
                "error_rate_percent": error_rate,
                "total_errors": len(failed_processing),
                "timeout_errors": error_categories["timeout"],
                "memory_errors": error_categories["memory"],
                "api_errors": error_categories["api"],
                "other_errors": error_categories["other"],
                "timestamp": current_time
            }
    
    def _background_monitoring(self):
        """Background thread for continuous monitoring."""
        logger.info("Background monitoring started")
        
        while self.monitoring_active:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self.system_metrics.append(system_metrics)
                
                # Collect business metrics
                business_metrics = self._collect_business_metrics()
                
                # Update statistics
                self._update_statistics(business_metrics, system_metrics)
                
                # Check alerts
                self._check_alerts()
                
                # Update trend data (every hour)
                current_hour = int(time.time() // 3600)
                if not hasattr(self, '_last_trend_hour') or self._last_trend_hour != current_hour:
                    self._update_trend_data()
                    self._last_trend_hour = current_hour
                
                # Sleep for monitoring interval
                time.sleep(self.config.get('monitoring_interval_seconds', 60))
                
            except Exception as e:
                logger.error(f"Error in background monitoring: {e}", exc_info=True)
                time.sleep(60)  # Wait before retrying
        
        logger.info("Background monitoring stopped")
    
    def _update_statistics(self, business_metrics: Dict, system_metrics: Dict):
        """Update internal statistics with latest metrics."""
        with self._lock:
            # Update business statistics
            self.stats["documents_per_hour"] = business_metrics.get("documents_per_hour", 0.0)
            self.stats["templates_generated_per_hour"] = business_metrics.get("templates_generated_per_hour", 0.0)
            self.stats["average_confidence_score"] = business_metrics.get("average_confidence_score", 0.0)
            self.stats["error_rate_percent"] = business_metrics.get("error_rate_percent", 0.0)
            
            # Update system statistics
            self.stats["average_memory_usage_mb"] = system_metrics.get("process_memory_mb", 0.0)
            self.stats["average_cpu_usage_percent"] = system_metrics.get("cpu_usage_percent", 0.0)
            
            # Calculate uptime
            if not hasattr(self, '_start_time'):
                self._start_time = time.time()
            self.stats["uptime_hours"] = (time.time() - self._start_time) / 3600
    
    def _check_alerts(self):
        """Check performance metrics against alert thresholds."""
        current_time = time.time()
        
        for alert in self.alerts:
            if not alert.enabled:
                continue
            
            # Check cooldown period
            if (alert.last_triggered and 
                current_time - alert.last_triggered < alert.cooldown_minutes * 60):
                continue
            
            # Get current metric value
            metric_value = self.stats.get(alert.metric_name)
            if metric_value is None:
                continue
            
            # Check threshold
            should_trigger = False
            if alert.comparison == "greater_than" and metric_value > alert.threshold:
                should_trigger = True
            elif alert.comparison == "less_than" and metric_value < alert.threshold:
                should_trigger = True
            elif alert.comparison == "equal_to" and metric_value == alert.threshold:
                should_trigger = True
            
            if should_trigger:
                self._trigger_alert(alert, metric_value)
    
    def _trigger_alert(self, alert: Alert, current_value: float):
        """Trigger a performance alert."""
        alert.last_triggered = time.time()
        
        message = alert.message_template.format(
            value=current_value,
            threshold=alert.threshold,
            metric=alert.metric_name
        )
        
        alert_data = {
            "alert_name": alert.name,
            "severity": alert.severity.value,
            "message": message,
            "metric_name": alert.metric_name,
            "current_value": current_value,
            "threshold": alert.threshold,
            "timestamp": time.time()
        }
        
        logger.warning(f"Performance Alert: {message}")
        
        # Call registered alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert_data)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    def _update_trend_data(self):
        """Update hourly trend data for performance analysis."""
        current_metrics = {
            "documents_per_hour": self.stats["documents_per_hour"],
            "templates_generated_per_hour": self.stats["templates_generated_per_hour"],
            "average_confidence_score": self.stats["average_confidence_score"],
            "error_rate_percent": self.stats["error_rate_percent"],
            "average_memory_usage_mb": self.stats["average_memory_usage_mb"],
            "average_cpu_usage_percent": self.stats["average_cpu_usage_percent"]
        }
        
        timestamp = time.time()
        
        for metric_name, value in current_metrics.items():
            self.trend_history[metric_name].append({
                "timestamp": timestamp,
                "value": value
            })
    
    def add_alert_handler(self, handler: Callable[[Dict], None]):
        """Add a custom alert handler function."""
        self.alert_handlers.append(handler)
        logger.info(f"Added alert handler: {handler.__name__}")
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, PerformanceTrend]:
        """Get performance trends for the specified time period."""
        trends = {}
        cutoff_time = time.time() - (hours * 3600)
        
        for metric_name, history in self.trend_history.items():
            if len(history) < 2:
                continue
            
            # Filter to requested time period
            recent_data = [
                point for point in history 
                if point["timestamp"] > cutoff_time
            ]
            
            if len(recent_data) < 2:
                continue
            
            # Calculate trend
            current_value = recent_data[-1]["value"]
            previous_value = recent_data[0]["value"]
            
            if previous_value == 0:
                change_percent = 0.0
            else:
                change_percent = ((current_value - previous_value) / previous_value) * 100
            
            # Determine trend direction
            if abs(change_percent) < 5:  # Less than 5% change
                trend_direction = "stable"
            elif change_percent > 0:
                # For metrics where higher is better
                if metric_name in ["documents_per_hour", "templates_generated_per_hour", "average_confidence_score"]:
                    trend_direction = "improving"
                else:
                    trend_direction = "degrading"
            else:
                # For metrics where lower is better
                if metric_name in ["error_rate_percent", "average_memory_usage_mb", "average_cpu_usage_percent"]:
                    trend_direction = "improving"
                else:
                    trend_direction = "degrading"
            
            trends[metric_name] = PerformanceTrend(
                metric_name=metric_name,
                current_value=current_value,
                previous_value=previous_value,
                change_percent=change_percent,
                trend_direction=trend_direction,
                period_hours=hours
            )
        
        return trends
    
    def _record_business_metric(self, name: str, value: float, unit: str, metadata: Optional[Dict] = None):
        """Record a business metric."""
        metric = BusinessMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        self.business_metrics.append(metric)
    
    def _record_processing_completion(self, metrics: ProcessingMetrics):
        """Record business metrics for completed processing."""
        # Processing completion
        self._record_business_metric("processing_completed", 1, "count", {
            "success": metrics.success,
            "pipeline_type": metrics.pipeline_type,
            "file_size_mb": metrics.file_size_mb,
            "processing_time": metrics.total_processing_time
        })
        
        # Success/failure metrics
        if metrics.success:
            self._record_business_metric("processing_success", 1, "count")
            
            # Template generation success
            if metrics.pipeline_type in ["generation", "full_workflow"]:
                self._record_business_metric("template_generated", 1, "count")
            
            # Confidence score metrics
            if metrics.confidence_scores:
                avg_confidence = sum(metrics.confidence_scores.values()) / len(metrics.confidence_scores)
                self._record_business_metric("confidence_score", avg_confidence, "percent")
        else:
            self._record_business_metric("processing_failure", 1, "count", {
                "error_message": metrics.error_message
            })
    
    def _check_stage_performance(self, stage_name: str, duration: float):
        """Check individual stage performance against targets."""
        stage_targets = {
            "text_extraction": 10.0,
            "embedding_generation": 15.0,
            "qme_field_extraction": 10.0,
            "template_generation": 30.0,
            "kg_population": 5.0
        }
        
        if stage_name in stage_targets:
            target = stage_targets[stage_name]
            if duration > target:
                logger.warning(f"Stage '{stage_name}' exceeded target: {duration:.2f}s > {target}s")
                
                # Record performance violation
                self._record_business_metric("performance_violation", 1, "count", {
                    "stage": stage_name,
                    "duration": duration,
                    "target": target
                })
    
    def _update_processing_statistics(self, metrics: ProcessingMetrics):
        """Update processing statistics with completed metrics."""
        self.stats["total_documents_processed"] += 1
        
        if metrics.success:
            self.stats["successful_processing"] += 1
        else:
            self.stats["failed_processing"] += 1
        
        # Update average processing time
        if metrics.total_processing_time:
            successful_times = [
                m.total_processing_time for m in self.completed_processing 
                if m.success and m.total_processing_time
            ]
            if successful_times:
                self.stats["average_processing_time"] = statistics.mean(successful_times)
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report with all metrics."""
        with self._lock:
            current_time = time.time()
            
            # Basic statistics
            report = {
                "report_metadata": {
                    "generated_at": current_time,
                    "uptime_hours": self.stats["uptime_hours"],
                    "monitoring_active": self.monitoring_active
                },
                "processing_statistics": {
                    "total_processed": self.stats["total_documents_processed"],
                    "successful": self.stats["successful_processing"],
                    "failed": self.stats["failed_processing"],
                    "success_rate_percent": (
                        (self.stats["successful_processing"] / self.stats["total_documents_processed"]) * 100
                        if self.stats["total_documents_processed"] > 0 else 0
                    ),
                    "average_processing_time": self.stats["average_processing_time"],
                    "active_processing": len(self.active_processing)
                },
                "business_metrics": {
                    "documents_per_hour": self.stats["documents_per_hour"],
                    "templates_per_hour": self.stats["templates_generated_per_hour"],
                    "average_confidence_score": self.stats["average_confidence_score"],
                    "error_rate_percent": self.stats["error_rate_percent"]
                },
                "system_metrics": {
                    "memory_usage_mb": self.stats["average_memory_usage_mb"],
                    "cpu_usage_percent": self.stats["average_cpu_usage_percent"]
                },
                "performance_targets": [asdict(target) for target in self.performance_targets],
                "active_alerts": [
                    {
                        "name": alert.name,
                        "severity": alert.severity.value,
                        "last_triggered": alert.last_triggered
                    }
                    for alert in self.alerts 
                    if alert.last_triggered and (current_time - alert.last_triggered) < 3600
                ]
            }
            
            # Recent processing details
            recent_processing = list(self.completed_processing)[-10:]  # Last 10
            report["recent_processing"] = [
                {
                    "document": Path(m.document_path).name,
                    "processing_time": m.total_processing_time,
                    "success": m.success,
                    "pipeline_type": m.pipeline_type,
                    "confidence_scores": m.confidence_scores,
                    "stages": m.stages
                }
                for m in recent_processing
            ]
            
            # Performance trends
            trends = self.get_performance_trends(24)
            report["performance_trends"] = {
                name: asdict(trend) for name, trend in trends.items()
            }
            
            return report
    
    def export_metrics_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        metrics = []
        timestamp = int(time.time() * 1000)
        
        # Processing metrics
        metrics.append(f"qme_documents_processed_total {self.stats['total_documents_processed']} {timestamp}")
        metrics.append(f"qme_processing_success_total {self.stats['successful_processing']} {timestamp}")
        metrics.append(f"qme_processing_failures_total {self.stats['failed_processing']} {timestamp}")
        metrics.append(f"qme_average_processing_time_seconds {self.stats['average_processing_time']} {timestamp}")
        
        # Business metrics
        metrics.append(f"qme_documents_per_hour {self.stats['documents_per_hour']} {timestamp}")
        metrics.append(f"qme_templates_per_hour {self.stats['templates_generated_per_hour']} {timestamp}")
        metrics.append(f"qme_average_confidence_score {self.stats['average_confidence_score']} {timestamp}")
        metrics.append(f"qme_error_rate_percent {self.stats['error_rate_percent']} {timestamp}")
        
        # System metrics
        metrics.append(f"qme_memory_usage_mb {self.stats['average_memory_usage_mb']} {timestamp}")
        metrics.append(f"qme_cpu_usage_percent {self.stats['average_cpu_usage_percent']} {timestamp}")
        metrics.append(f"qme_uptime_hours {self.stats['uptime_hours']} {timestamp}")
        
        # Active processing
        metrics.append(f"qme_active_processing_count {len(self.active_processing)} {timestamp}")
        
        return "\n".join(metrics)
    
    def get_user_activity_patterns(self) -> Dict[str, Any]:
        """Analyze user activity patterns for capacity planning."""
        with self._lock:
            current_time = time.time()
            day_ago = current_time - 86400  # 24 hours
            
            recent_processing = [
                p for p in self.completed_processing 
                if p.processing_end_time and p.processing_end_time > day_ago
            ]
            
            if not recent_processing:
                return {"message": "No recent activity data available"}
            
            # Activity by hour
            hourly_activity = defaultdict(int)
            for p in recent_processing:
                hour = datetime.fromtimestamp(p.processing_start_time).hour
                hourly_activity[hour] += 1
            
            # User session analysis
            user_sessions = defaultdict(list)
            for p in recent_processing:
                if p.user_id:
                    user_sessions[p.user_id].append(p)
            
            # Peak usage analysis
            peak_hour = max(hourly_activity.items(), key=lambda x: x[1]) if hourly_activity else (0, 0)
            
            return {
                "analysis_period_hours": 24,
                "total_activity": len(recent_processing),
                "unique_users": len(user_sessions),
                "hourly_distribution": dict(hourly_activity),
                "peak_hour": {
                    "hour": peak_hour[0],
                    "activity_count": peak_hour[1]
                },
                "average_documents_per_user": (
                    len(recent_processing) / len(user_sessions) 
                    if user_sessions else 0
                ),
                "concurrent_processing_peak": max(
                    len([p for p in recent_processing 
                         if abs(p.processing_start_time - ref_time) < 300])  # 5-minute window
                    for ref_time in [p.processing_start_time for p in recent_processing]
                ) if recent_processing else 0
            }
    
    def shutdown(self):
        """Shutdown the performance monitor."""
        logger.info("Shutting down performance monitor")
        self.monitoring_active = False
        
        if hasattr(self, 'monitoring_thread'):
            self.monitoring_thread.join(timeout=5)
        
        # Export final metrics
        try:
            final_report = self.get_comprehensive_report()
            export_path = f"results/performance_reports/final_performance_report_{int(time.time())}.json"
            Path(export_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w') as f:
                json.dump(final_report, f, indent=2, default=str)
            
            logger.info(f"Final performance report exported to: {export_path}")
        except Exception as e:
            logger.error(f"Failed to export final performance report: {e}")


# Global performance monitor instance
_performance_monitor: Optional[AdvancedPerformanceMonitor] = None


def get_performance_monitor(config: Optional[Dict] = None) -> AdvancedPerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    
    if _performance_monitor is None:
        _performance_monitor = AdvancedPerformanceMonitor(config)
    
    return _performance_monitor


def initialize_performance_monitor(config: Dict[str, Any]) -> AdvancedPerformanceMonitor:
    """Initialize global performance monitor with configuration."""
    global _performance_monitor
    _performance_monitor = AdvancedPerformanceMonitor(config)
    return _performance_monitor


# Decorator for automatic performance monitoring
def monitor_performance(
    pipeline_type: str = "unknown",
    include_confidence: bool = False,
    include_quality: bool = False
):
    """Decorator to automatically monitor function performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            
            # Extract document information from arguments
            doc_path = "unknown"
            file_size = 0.0
            user_id = None
            
            # Try to extract from common argument patterns
            if args and hasattr(args[0], 'document_path'):
                doc_path = args[0].document_path
            elif 'document_path' in kwargs:
                doc_path = kwargs['document_path']
            elif 'file_path' in kwargs:
                doc_path = kwargs['file_path']
            
            if 'user_id' in kwargs:
                user_id = kwargs['user_id']
            
            # Calculate file size if path exists
            if doc_path != "unknown" and Path(doc_path).exists():
                file_size = Path(doc_path).stat().st_size / (1024 * 1024)
            
            # Start monitoring
            processing_id = monitor.start_processing(
                doc_path, file_size, pipeline_type=pipeline_type, user_id=user_id
            )
            
            try:
                result = func(*args, **kwargs)
                
                # Extract metrics from result if available
                confidence_scores = None
                quality_metrics = None
                
                if include_confidence and hasattr(result, 'confidence_scores'):
                    confidence_scores = result.confidence_scores
                elif include_confidence and isinstance(result, dict) and 'confidence_scores' in result:
                    confidence_scores = result['confidence_scores']
                
                if include_quality and hasattr(result, 'quality_metrics'):
                    quality_metrics = result.quality_metrics
                elif include_quality and isinstance(result, dict) and 'quality_metrics' in result:
                    quality_metrics = result['quality_metrics']
                
                monitor.complete_processing(
                    processing_id, 
                    success=True,
                    confidence_scores=confidence_scores,
                    quality_metrics=quality_metrics
                )
                
                return result
                
            except Exception as e:
                monitor.complete_processing(
                    processing_id, 
                    success=False, 
                    error_message=str(e)
                )
                raise
        
        return wrapper
    return decorator